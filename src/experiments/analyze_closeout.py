#!/usr/bin/env python3
"""Definitive analysis of the certified synthetic measurement closeout.

Usage:
  python experiments/analyze_closeout.py \
      --phase1 ../result/phase1/20260816T180507Z \
      --damping ../result/damping_frontier/20260816T180507Z \
      --boundary ../result/boundary_fine/20260816T180507Z \
      --out ../result/analysis/<UTC-stamp>

Contract:
- The three input directories are IMMUTABLE; this script only reads them.
- Certified filter: replay_effective_ok == True AND solver_status == OPTIMAL.
  Raw replay information is preserved in the audit-totals table.
- Deterministic: identical inputs produce byte-identical CSV tables (sorted
  rows/columns, fixed float formatting). Figures are content-deterministic.
- Every headline number is cross-validated between records.csv and the
  checkpoints (and the audited SUMMARY.md) where both exist; any disagreement
  raises AnalysisError and no output is written.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

LOAD_TOL_KWH = 1.0  # material-load threshold, must match egglab.boundary
WELFARE_TOL = 2e-2  # dictator-dominance check tolerance (certified gap scale)


class AnalysisError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# provenance hashing
# ---------------------------------------------------------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def checkpoints_digest(root: str) -> tuple:
    """Combined SHA-256 over all checkpoint files (sorted relpath + content
    hash), plus the file count."""
    h = hashlib.sha256()
    files = sorted(glob.glob(os.path.join(root, "checkpoints", "*", "*.ckpt.json")))
    for fp in files:
        rel = os.path.relpath(fp, root)
        h.update(rel.encode())
        h.update(sha256_file(fp).encode())
    return h.hexdigest(), len(files)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def input_hashes(roots: dict) -> dict:
    out = {}
    for name, r in roots.items():
        digest, n = checkpoints_digest(r["root"])
        ap = os.path.abspath(r["root"])
        try:
            path = os.path.relpath(ap, REPO_ROOT)
        except ValueError:
            path = ap
        out[name] = {
            "path": path if not path.startswith("..") else ap,
            "records.csv": sha256_file(os.path.join(r["root"], "records.csv")),
            "SUMMARY.md": sha256_file(os.path.join(r["root"], "SUMMARY.md")),
            "checkpoints_sha256": digest,
            "n_checkpoint_files": n,
        }
    return out


def output_hashes(out_dir: str) -> dict:
    """SHA-256 of every generated file (excluding the manifest itself)."""
    hashes = {}
    for fp in sorted(glob.glob(os.path.join(out_dir, "**", "*"), recursive=True)):
        if os.path.isdir(fp) or os.path.basename(fp) == "MANIFEST.json":
            continue
        hashes[os.path.relpath(fp, out_dir)] = sha256_file(fp)
    return hashes


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
LOOP_TAG = re.compile(r"^s(\d+)_n(\d+)_([a-z_]+)_b([\d.]+)_a([\d.]+)$")
SWEEP_TAG = re.compile(r"^s(\d+)_n(\d+)_slot(\d+)$")


def parse_loop_cell(name: str) -> dict:
    m = LOOP_TAG.match(name)
    if not m:
        raise AnalysisError(f"unparsable loop cell name: {name}")
    return {
        "cell": name,
        "seed": int(m.group(1)),
        "n_trips": int(m.group(2)),
        "shape": m.group(3),
        "b": float(m.group(4)),
        "alpha": float(m.group(5)),
    }


def parse_sweep_cell(name: str) -> dict:
    m = SWEEP_TAG.match(name)
    if not m:
        raise AnalysisError(f"unparsable sweep cell name: {name}")
    return {"cell": name, "seed": int(m.group(1)), "n_trips": int(m.group(2)),
            "slot": int(m.group(3))}


def load_root(root: str) -> dict:
    df = pd.read_csv(os.path.join(root, "records.csv"), low_memory=False)
    summary = open(os.path.join(root, "SUMMARY.md")).read()
    cks = {}
    for kind in ("loop", "sweep", "cell"):
        for fp in sorted(glob.glob(os.path.join(root, "checkpoints", "*", f"{kind}.ckpt.json"))):
            cell = os.path.basename(os.path.dirname(fp))
            cks.setdefault(kind, {})[cell] = json.load(open(fp))
    return {"root": root, "df": df, "summary": summary, "ckpts": cks}


def summary_int(summary: str, pattern: str) -> int:
    m = re.search(pattern, summary)
    if not m:
        raise AnalysisError(f"pattern {pattern!r} not found in SUMMARY.md")
    return int(m.group(1).replace(",", ""))


def certified(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["replay_effective_ok"] == True)  # noqa: E712
              & (df["solver_status"] == "OPTIMAL")].copy()


# ---------------------------------------------------------------------------
# deterministic writing
# ---------------------------------------------------------------------------
def write_csv(df: pd.DataFrame, path: str, sort_by: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = df.sort_values(sort_by, kind="mergesort").reset_index(drop=True)
    out.to_csv(path, index=False, float_format="%.10g")


# ---------------------------------------------------------------------------
# audit totals (raw information preserved)
# ---------------------------------------------------------------------------
def audit_totals(roots: dict) -> pd.DataFrame:
    rows = []
    for name, r in roots.items():
        df = r["df"]
        raw_fail = int((df["replay_original_ok"] == False).sum())  # noqa: E712
        summary_fail = summary_int(r["summary"], r"raw legacy replay failures: (\d+)")
        if raw_fail != summary_fail:
            raise AnalysisError(
                f"{name}: raw replay failures disagree: records.csv={raw_fail} "
                f"SUMMARY.md={summary_fail}")
        total_summary = summary_int(r["summary"], r"Total records: \*\*([\d,]+)\*\*")
        if total_summary != len(df):
            raise AnalysisError(
                f"{name}: record count disagrees: records.csv={len(df)} "
                f"SUMMARY.md={total_summary}")
        cert = certified(df)
        rows.append({
            "campaign": name,
            "records": len(df),
            "certified_records": len(cert),
            "raw_replay_failures": raw_fail,
            "revalidated": int(((df["replay_original_ok"] == False)  # noqa: E712
                                & (df["replay_effective_ok"] == True)).sum()),  # noqa: E712
            "unresolved": int((df["replay_effective_ok"] == False).sum()),  # noqa: E712
            "non_optimal": int((df["solver_status"] != "OPTIMAL").sum()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# loop outcomes: checkpoints as source of truth, cross-validated vs records
# ---------------------------------------------------------------------------
def loop_cell_table(roots: dict) -> pd.DataFrame:
    rows = []
    for name in ("phase1", "damping"):
        r = roots[name]
        loops = r["ckpts"].get("loop", {})
        recs = certified(r["df"])
        loop_recs = recs[recs["regime"] == "taker-iteration"]
        # records-side terminal outcome per cell
        term = loop_recs[loop_recs["x_outcome_type"].notna()]
        term_by_cell = {t: (row["x_outcome_type"], row.get("x_cycle_length"))
                        for t, row in term.set_index("x_tag").iterrows()} \
            if "x_tag" in term.columns else {}
        # phase1 loop tags are 'loop' with cell dir in checkpoints; records
        # carry x_tag == cell tag for statics but loop extras carry the
        # params: group records by cell parameters instead
        for cell, ck in sorted(loops.items()):
            meta = parse_loop_cell(cell)
            if not ck.get("done"):
                raise AnalysisError(f"{name}/{cell}: loop checkpoint not done")
            oc = ck["outcome"]
            sub = loop_recs[
                (loop_recs["x_seed"] == meta["seed"])
                & (loop_recs["n_trips"] == meta["n_trips"])
                & (np.isclose(loop_recs["x_b_scale"], meta["b"]))
                & (np.isclose(loop_recs["x_alpha"], meta["alpha"]))
            ]
            if len(sub) != ck["iter"]:
                raise AnalysisError(
                    f"{name}/{cell}: {len(sub)} certified loop records but "
                    f"checkpoint ran {ck['iter']} iterations")
            rec_term = sub[sub["x_outcome_type"].notna()]
            if oc["type"] != "max_iters":
                if len(rec_term) != 1 or rec_term.iloc[0]["x_outcome_type"] != oc["type"]:
                    raise AnalysisError(
                        f"{name}/{cell}: records terminal outcome "
                        f"{list(rec_term['x_outcome_type'])} != checkpoint {oc['type']}")
                if oc["type"] == "cycle":
                    rl = rec_term.iloc[0].get("x_cycle_length")
                    if not np.isclose(float(rl), oc["length"]):
                        raise AnalysisError(f"{name}/{cell}: cycle length mismatch")
            final_resid = float(sub.sort_values("x_iter").iloc[-1]["x_price_residual"])
            rows.append({
                "campaign": name, **meta,
                "outcome": oc["type"],
                "cycle_length": oc.get("length"),
                "cycle_first_seen": oc.get("first_seen"),
                "iters_run": ck["iter"],
                "final_price_residual": final_resid,
            })
    return pd.DataFrame(rows)


def outcome_rates(cells: pd.DataFrame) -> pd.DataFrame:
    g = (cells.groupby(["campaign", "b", "alpha"])
         .agg(n_cells=("cell", "count"),
              fixed_point=("outcome", lambda s: int((s == "fixed_point").sum())),
              cycle=("outcome", lambda s: int((s == "cycle").sum())),
              max_iters=("outcome", lambda s: int((s == "max_iters").sum())),
              median_iters=("iters_run", "median"))
         .reset_index())
    for c in ("fixed_point", "cycle", "max_iters"):
        g[f"{c}_rate"] = g[c] / g["n_cells"]
    return g


# ---------------------------------------------------------------------------
# welfare ladder (phase-1 statics)
# ---------------------------------------------------------------------------
def welfare_tables(roots: dict):
    """Phase-1 static regimes. The four alpha cells re-solve identical static
    problems, giving 4 independent solver draws per (seed, n_trips, b,
    regime). Each optimizing regime's OWN certified objective (obj_true) must
    be alpha-invariant (validated); cross-lens metrics such as the taker's
    total_system may legitimately differ across draws when the regime's
    problem has degenerate optima — that selection spread is itself a
    measured degeneracy diagnostic, reported per cell."""
    df = certified(roots["phase1"]["df"])
    st = df[df["experiment"] == "phase1-static"].copy()
    key = ["x_seed", "n_trips", "x_b_scale", "regime"]
    # invariance of each optimizing regime's own certified objective
    opt = st[st["regime"].isin(["taker", "strategic", "dictator"])]
    inv = opt.groupby(key)["obj_true"].agg(["min", "max", "count"])
    bad = inv[(inv["max"] - inv["min"]) > WELFARE_TOL]
    if len(bad):
        raise AnalysisError(
            f"own-objective alpha-invariance violated: {bad.index.tolist()[:5]}")
    draws = (st.groupby(key)
             .agg(n_draws=("econ_total_system", "count"),
                  total_system_mean=("econ_total_system", "mean"),
                  total_system_min=("econ_total_system", "min"),
                  total_system_max=("econ_total_system", "max"),
                  total_private_mean=("econ_total_private", "mean"),
                  energy_kwh_mean=("econ_energy_kwh", "mean"),
                  fleet=("fleet", "max"))
             .reset_index()
             .rename(columns={"x_seed": "seed", "x_b_scale": "b"}))
    draws["selection_spread"] = draws["total_system_max"] - draws["total_system_min"]
    ladder = draws
    # dominance: the dictator minimizes total_system, so its (invariant)
    # optimum must lower-bound EVERY draw of every other regime
    piv_min = ladder.pivot_table(index=["seed", "n_trips", "b"],
                                 columns="regime", values="total_system_min")
    piv_mean = ladder.pivot_table(index=["seed", "n_trips", "b"],
                                  columns="regime", values="total_system_mean")
    for other in ("uncontrolled", "taker", "strategic"):
        viol = piv_min[piv_mean["dictator"] > piv_min[other] + WELFARE_TOL]
        if len(viol):
            raise AnalysisError(f"dictator worse than {other} in {len(viol)} cells")
    gaps = piv_mean.reset_index()
    for other in ("uncontrolled", "taker", "strategic"):
        gaps[f"gap_{other}_minus_dictator"] = gaps[other] - gaps["dictator"]
    gsum = (gaps.groupby("b")[[f"gap_{o}_minus_dictator"
                               for o in ("uncontrolled", "taker", "strategic")]]
            .agg(["mean", "max"]))
    gsum.columns = ["_".join(c) for c in gsum.columns]
    return ladder, gaps, gsum.reset_index()


# ---------------------------------------------------------------------------
# boundary switches: checkpoints as truth, reclassified from points
# ---------------------------------------------------------------------------
def switch_tables(roots: dict):
    r = roots["boundary"]
    recs = certified(r["df"])
    rows, cell_rows = [], []
    for cell, ck in sorted(r["ckpts"].get("sweep", {}).items()):
        meta = parse_sweep_cell(cell)
        if not (ck.get("done") and ck.get("margins_done")):
            raise AnalysisError(f"boundary/{cell}: incomplete checkpoint")
        pts = ck["points"]
        sub = recs[(recs["x_seed"] == meta["seed"])
                   & (recs["n_trips"] == meta["n_trips"])
                   & (recs["x_sweep_slot"] == meta["slot"])]
        if len(sub) != len(pts):
            raise AnalysisError(
                f"boundary/{cell}: {len(sub)} certified records vs {len(pts)} points")
        # reclassify from points and compare with stored switches (kinds)
        recomputed = {"degenerate_tie": 0, "charging_only": 0,
                      "duty_change": 0, "fleet_change": 0}
        for a, b_ in zip(pts, pts[1:]):
            if a["schedule_hash"] == b_["schedule_hash"] and a["load_hash"] == b_["load_hash"]:
                continue
            l1 = float(np.abs(np.asarray(a["load"]) - np.asarray(b_["load"])).sum())
            if b_["fleet"] != a["fleet"]:
                recomputed["fleet_change"] += 1
            elif l1 <= LOAD_TOL_KWH:
                recomputed["degenerate_tie"] += 1
            elif a["schedule_hash"] != b_["schedule_hash"]:
                recomputed["duty_change"] += 1
            else:
                recomputed["charging_only"] += 1
        stored = ck.get("counts_by_kind", {})
        if recomputed != {k: int(stored.get(k, 0)) for k in recomputed}:
            raise AnalysisError(
                f"boundary/{cell}: reclassification {recomputed} != stored {stored}")
        n_econ_cell = 0
        for s in ck["switches"]:
            economic = (s["kind"] in ("charging_only", "duty_change", "fleet_change")
                        and not s.get("tie_margin", False))
            n_econ_cell += int(economic)
            rows.append({
                **meta,
                "kind": s["kind"],
                "tie_margin": bool(s.get("tie_margin", False)),
                "economic": economic,
                "load_l1": s.get("load_l1"),
                "load_jump_slot": s.get("load_jump_slot"),
                "delta_lo": s["between_deltas"][0],
                "delta_hi": s["between_deltas"][1],
                "schedule_changed": s.get("schedule_changed"),
                "margin_b_at_a": s.get("margin_b_at_a"),
                "margin_a_at_b": s.get("margin_a_at_b"),
            })
        if n_econ_cell != ck.get("n_economic_switches"):
            raise AnalysisError(f"boundary/{cell}: economic count mismatch")
        cell_rows.append({**meta, "n_switches": ck["n_switches"],
                          "n_economic": n_econ_cell, **recomputed})
    sw = pd.DataFrame(rows)
    cells = pd.DataFrame(cell_rows)
    econ = sw[sw["economic"]]
    by = (econ.groupby(["n_trips", "slot"])
          .agg(n_economic=("load_l1", "count"),
               median_load_l1=("load_l1", "median"),
               max_load_l1=("load_l1", "max"))
          .reset_index())
    return sw, cells, by


# ---------------------------------------------------------------------------
# solver statistics
# ---------------------------------------------------------------------------
def solver_stats(roots: dict) -> pd.DataFrame:
    rows = []
    for name, r in roots.items():
        cert = certified(r["df"])
        for regime, sub in sorted(cert.groupby("regime")):
            w = sub["solver_wall_s"].astype(float)
            g = sub["solver_lp_mip_gap_abs"].dropna().astype(float)
            rows.append({
                "campaign": name, "regime": regime, "n": len(sub),
                "wall_s_median": w.median(), "wall_s_p90": w.quantile(0.9),
                "wall_s_max": w.max(),
                "lp_gap_median": g.median() if len(g) else None,
                "lp_gap_p90": g.quantile(0.9) if len(g) else None,
                "lp_gap_max": g.max() if len(g) else None,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
def make_figures(out: str, cells: pd.DataFrame, rates: pd.DataFrame,
                 sw: pd.DataFrame, gaps: pd.DataFrame, roots: dict) -> list:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figs = []

    def save(fig, name):
        p = os.path.join(out, "figures", name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        figs.append(p)

    # F1: outcome shares by (b, alpha), one panel per campaign
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    for ax, camp in zip(axes, ("phase1", "damping")):
        sub = rates[rates["campaign"] == camp].sort_values(["b", "alpha"])
        labels = [f"b={b:g}\na={a:g}" for b, a in zip(sub["b"], sub["alpha"])]
        x = np.arange(len(sub))
        bottom = np.zeros(len(sub))
        for key, color in (("fixed_point_rate", "#2a9d8f"),
                           ("cycle_rate", "#e76f51"),
                           ("max_iters_rate", "#e9c46a")):
            ax.bar(x, sub[key], bottom=bottom, color=color,
                   label=key.replace("_rate", ""))
            bottom += sub[key].to_numpy()
        ax.set_xticks(x, labels, fontsize=6, rotation=90)
        ax.set_title(f"{camp}: outcome shares by (b, alpha)")
        ax.set_ylabel("share of cells")
    axes[0].legend(loc="lower left", fontsize=8)
    save(fig, "F1_outcome_rates.png")

    # F2: cycle-length distribution by b
    cyc = cells[cells["outcome"] == "cycle"]
    fig, ax = plt.subplots(figsize=(7, 4))
    for b, sub in sorted(cyc.groupby("b")):
        ax.hist(sub["cycle_length"], bins=np.arange(1.5, 32.5, 1),
                alpha=0.6, label=f"b={b:g} (n={len(sub)})")
    ax.set_xlabel("certified cycle length (iterations)")
    ax.set_ylabel("cells")
    ax.set_title("Price-state cycle lengths")
    ax.legend()
    save(fig, "F2_cycle_lengths.png")

    # F3: welfare gaps vs b
    fig, ax = plt.subplots(figsize=(7, 4))
    for other, color in (("uncontrolled", "#264653"), ("taker", "#2a9d8f"),
                         ("strategic", "#e76f51")):
        col = f"gap_{other}_minus_dictator"
        s = gaps.groupby("b")[col].mean()
        ax.plot(s.index, s.values, "o-", color=color, label=f"{other} - dictator")
    ax.set_xscale("symlog", linthresh=1e-3)
    ax.set_xlabel("market slope b")
    ax.set_ylabel("mean total-system cost gap")
    ax.set_title("Welfare ladder gaps vs price impact")
    ax.legend()
    save(fig, "F3_welfare_gaps.png")

    # F4: economic switch load jumps
    econ = sw[sw["economic"]]
    fig, ax = plt.subplots(figsize=(7, 4))
    for n, sub in sorted(econ.groupby("n_trips")):
        ax.hist(sub["load_l1"], bins=20, alpha=0.6, label=f"n_trips={n} (n={len(sub)})")
    ax.set_xlabel("L1 load jump at switch (kWh)")
    ax.set_ylabel("economic switches")
    ax.set_title("Discontinuity sizes at economic boundary switches")
    ax.legend()
    save(fig, "F4_switch_jumps.png")

    # F5: solver wall time and LP gap ECDFs
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for name, r in sorted(roots.items()):
        cert = certified(r["df"])
        w = np.sort(cert["solver_wall_s"].astype(float).to_numpy())
        axes[0].plot(w, np.linspace(0, 1, len(w)), label=name)
        g = np.sort(cert["solver_lp_mip_gap_abs"].dropna().astype(float).to_numpy())
        axes[1].plot(g, np.linspace(0, 1, len(g)), label=name)
    axes[0].set_xlabel("MIP wall time (s)"); axes[0].set_ylabel("ECDF")
    axes[0].set_xscale("log"); axes[0].legend()
    axes[1].set_xlabel("LP-vs-MIP absolute gap"); axes[1].legend()
    fig.suptitle("Solver statistics (certified records)")
    save(fig, "F5_solver_stats.png")

    # F6: example residual trajectories (one per outcome type, deterministic pick)
    fig, ax = plt.subplots(figsize=(8, 4))
    dampdf = certified(roots["damping"]["df"])
    loops = dampdf[dampdf["regime"] == "taker-iteration"]
    for oc, color in (("fixed_point", "#2a9d8f"), ("cycle", "#e76f51"),
                      ("max_iters", "#e9c46a")):
        pick = cells[(cells["campaign"] == "damping") & (cells["outcome"] == oc)]
        if not len(pick):
            continue
        c = pick.sort_values(["b", "alpha", "seed"]).iloc[0]
        sub = loops[(loops["x_seed"] == c["seed"]) & (loops["n_trips"] == c["n_trips"])
                    & (np.isclose(loops["x_b_scale"], c["b"]))
                    & (np.isclose(loops["x_alpha"], c["alpha"]))].sort_values("x_iter")
        ax.semilogy(sub["x_iter"], sub["x_price_residual"].astype(float),
                    color=color, label=f"{oc}: {c['cell']}")
    ax.set_xlabel("iteration"); ax.set_ylabel("price residual (max abs)")
    ax.set_title("Example price-residual trajectories (damping frontier)")
    ax.legend(fontsize=7)
    save(fig, "F6_residual_trajectories.png")
    return figs


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def analyze(phase1: str, damping: str, boundary: str, out: str) -> dict:
    roots = {"phase1": load_root(phase1), "damping": load_root(damping),
             "boundary": load_root(boundary)}

    totals = audit_totals(roots)
    cells = loop_cell_table(roots)
    rates = outcome_rates(cells)
    ladder, gaps, gsum = welfare_tables(roots)
    sw, sw_cells, sw_by = switch_tables(roots)
    solver = solver_stats(roots)

    write_csv(totals, os.path.join(out, "T8_audit_totals.csv"), ["campaign"])
    write_csv(cells, os.path.join(out, "T1_loop_cells.csv"),
              ["campaign", "b", "alpha", "seed", "n_trips"])
    write_csv(rates, os.path.join(out, "T1b_outcome_rates.csv"),
              ["campaign", "b", "alpha"])
    cyc = cells[cells["outcome"] == "cycle"][
        ["campaign", "b", "alpha", "seed", "n_trips", "cycle_length",
         "cycle_first_seen", "iters_run"]]
    write_csv(cyc, os.path.join(out, "T2_cycle_lengths.csv"),
              ["campaign", "b", "alpha", "seed", "n_trips"])
    het = (cells.groupby(["campaign", "seed"])["outcome"]
           .value_counts().unstack(fill_value=0).reset_index())
    write_csv(het, os.path.join(out, "T4_outcomes_by_seed.csv"),
              ["campaign", "seed"])
    write_csv(ladder, os.path.join(out, "T6_welfare_ladder.csv"),
              ["b", "n_trips", "seed", "regime"])
    write_csv(gaps, os.path.join(out, "T6b_welfare_gaps.csv"),
              ["b", "n_trips", "seed"])
    write_csv(gsum, os.path.join(out, "T6c_welfare_gap_summary.csv"), ["b"])
    write_csv(sw, os.path.join(out, "T7_switches.csv"),
              ["n_trips", "seed", "slot", "delta_lo"])
    write_csv(sw_cells, os.path.join(out, "T7b_switches_by_cell.csv"),
              ["n_trips", "seed", "slot"])
    write_csv(sw_by, os.path.join(out, "T7c_switch_summary.csv"),
              ["n_trips", "slot"])
    write_csv(solver, os.path.join(out, "T5_solver_stats.csv"),
              ["campaign", "regime"])

    figs = make_figures(out, cells, rates, sw, gaps, roots)

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=os.path.dirname(__file__)
        ).decode().strip()
    except Exception:
        commit = "unknown"
    manifest = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "analysis_code_commit": commit,
        "inputs": {"phase1": phase1, "damping": damping, "boundary": boundary},
        "input_hashes": input_hashes(roots),
        "certified_filter": "replay_effective_ok == True AND solver_status == OPTIMAL",
        "figures": [os.path.basename(f) for f in figs],
        "output_hashes": output_hashes(out),
    }
    with open(os.path.join(out, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)

    return {"totals": totals, "cells": cells, "rates": rates, "ladder": ladder,
            "gaps": gaps, "gsum": gsum, "switches": sw, "sw_cells": sw_cells,
            "solver": solver}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase1", required=True)
    ap.add_argument("--damping", required=True)
    ap.add_argument("--boundary", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = analyze(args.phase1, args.damping, args.boundary, args.out)
    print(res["totals"].to_string(index=False))
    print(f"\nwrote analysis to {args.out}")


if __name__ == "__main__":
    main()
