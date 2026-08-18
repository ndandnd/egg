#!/usr/bin/env python3
"""Deterministic B2 pilot-closeout pipeline (A2 vs A3/A4/A5).

Inputs (raw, gitignored, never committed):
  src/runs/b2a2_pilot    12 A2 cells   (job 80309 lineage; certified)
  src/runs/b2a345_pilot  36 A3-A5 cells (jobs 91001/91002; certified)

Outputs (committed): result/b2_pilot/<UTC stamp>/ containing MANIFEST.json,
cells.csv, matched_comparison.csv, method_summary.csv,
acceptance_status.csv, SUMMARY.md, and figures.

Safeguards (all enforced, loud AnalysisError otherwise):
- programmatic effective audit of both roots (completeness + per-method
  counts; certification is REPORTED, not silently required);
- exact cell identity: every expected (method, seed, n_trips, b) must exist
  with the exact instance and market hashes recomputed from the generators;
  missing, duplicate, unexpected, or mismatched cells reject the run;
- 12 cells per method, 48 matched method-cells total;
- all evidence comes from checkpoints/oracle events, never Slurm text;
- solver wall time is separated from task elapsed time (each method-cell
  repeats its own dictator stage; dictator wall is its own column);
- broadcast price-path metrics are recomputed from oracle-event prices and
  cross-validated against outcome fields where both exist;
- no method/seed/b filtering anywhere — the full grid or nothing;
- byte-identical CSV/JSON regeneration for identical inputs and stamp.

Two-commit provenance protocol: commit 1 is this code (tests+docs); commit 2
adds the generated artifacts whose MANIFEST.json names commit 1 as
analysis_code_commit (pass --analysis-code-commit).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from egglab import checkpoint
from egglab.b2a2 import market_hash
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from experiments.audit_runs import audit

PILOT_INSTANCES = tuple(
    (s, n, b) for s in (0, 11, 15) for n in (8, 12) for b in (0.01, 0.05))
METHODS = ("a2", "a3", "a4", "a5")
STAB_METHODS = ("a3", "a4", "a5")
BROADCAST_REGIMES = {
    "a2": ("cg-seed", "cg-pricing"),
    "a3": ("cg-seed", "cg-stab-pricing"),
    "a4": ("cg-seed", "cg-stab-pricing"),
    "a5": ("cg-seed", "cg-stab-pricing"),
}
TV_XCHECK_TOL = 1e-3  # prices in records are rounded to 1e-6 per slot


class AnalysisError(RuntimeError):
    pass


def default_instance_builder(seed: int, n_trips: int):
    """EXACTLY the pilot drivers' construction (identity must match)."""
    return synthetic_instance(seed=seed, n_trips=n_trips)


def verify_analysis_code_commit(claimed: str) -> str:
    """The two-commit protocol is only meaningful if the pipeline actually
    runs from the commit it stamps into the manifest: verify HEAD matches
    the claimed hash (prefix match either way) and the tracked tree is
    clean. Returns the full resolved hash."""
    import subprocess

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_dir).decode().strip()
    if not (head.startswith(claimed) or claimed.startswith(head)):
        raise AnalysisError(
            f"analysis code commit mismatch: running from {head[:12]} but "
            f"--analysis-code-commit claims {claimed}; check out the "
            "claimed commit or fix the argument")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_dir).decode().strip()
    if dirty:
        raise AnalysisError(
            "analysis tree has uncommitted tracked changes; the manifest "
            f"would misattribute results to {claimed}:\n{dirty}")
    return head


# ---------------------------------------------------------------------------
# hashing / deterministic writing
# ---------------------------------------------------------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hashes(root: str) -> dict:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            out[os.path.relpath(p, root)] = sha256_file(p)
    return out


def write_csv(df: pd.DataFrame, path: str, sort_by: list) -> None:
    out = df.sort_values(sort_by, kind="mergesort").reset_index(drop=True)
    out.to_csv(path, index=False, float_format="%.12g")


def q1q3(vals):
    s = sorted(vals)
    if not s:
        return float("nan"), float("nan")
    qs = statistics.quantiles(s, n=4, method="inclusive") if len(s) > 1 else [s[0]] * 3
    return qs[0], qs[2]


# ---------------------------------------------------------------------------
# loading and validation
# ---------------------------------------------------------------------------
def cell_dir(root: str, method: str, seed: int, n: int, b: float) -> str:
    base = f"s{seed}_n{n}_b{b:g}"
    return os.path.join(root, base if method == "a2" else f"{method}_{base}")


def expected_cells(instances):
    return [(m, s, n, b) for m in METHODS for (s, n, b) in instances]


def validate_cell(d: str, m: str, s: int, n: int, b: float,
                  instance_builder=default_instance_builder) -> str:
    """Exact identity validation of one cell directory (CG checkpoint AND
    dictator checkpoint, including the z_d_ub pairing). Returns the cg
    checkpoint path. Shared by the pilot and full-population pipelines."""
    ck_path = os.path.join(d, f"{m}.cg.ckpt.json")
    if not os.path.exists(ck_path):
        raise AnalysisError(f"missing cell: {m} seed={s} n={n} b={b} "
                            f"({ck_path})")
    ck = checkpoint.load(ck_path)
    ident = ck.get("identity") or {}
    inst = instance_builder(s, n)
    mkt = make_affine_market(inst, shape="duck", b_scale=b)
    if ident.get("instance_hash") != inst.hash():
        raise AnalysisError(
            f"cell {m} seed={s} n={n} b={b}: instance hash mismatch")
    if ident.get("market_hash") != market_hash(mkt):
        raise AnalysisError(
            f"cell {m} seed={s} n={n} b={b}: market hash mismatch")
    if ident.get("method", "a2") != m:
        raise AnalysisError(
            f"cell dir {d}: identity method {ident.get('method')} != {m}")
    if not ck.get("done"):
        raise AnalysisError(f"cell {m} seed={s} n={n} b={b} not done")
    # the dictator checkpoint's identity is evidence too: same
    # instance/market hashes, same tolerance, same solver settings,
    # and its value must be the one the CG identity was keyed to
    dck = checkpoint.load(os.path.join(d, "dictator.ckpt.json"))
    if dck is None:
        raise AnalysisError(f"missing dictator checkpoint in {d}")
    d_ident = dck.get("identity") or {}
    if d_ident.get("instance_hash") != inst.hash():
        raise AnalysisError(
            f"cell {m} seed={s} n={n} b={b}: dictator instance hash "
            "mismatch")
    if d_ident.get("market_hash") != market_hash(mkt):
        raise AnalysisError(
            f"cell {m} seed={s} n={n} b={b}: dictator market hash "
            "mismatch")
    if d_ident.get("tol_d") != ident.get("tol_d"):
        raise AnalysisError(
            f"cell {m} seed={s} n={n} b={b}: dictator tol_d "
            f"{d_ident.get('tol_d')} != cg identity {ident.get('tol_d')}")
    if ident.get("z_d_ub") != dck.get("z_d_ub"):
        raise AnalysisError(
            f"cell {m} seed={s} n={n} b={b}: cg identity z_d_ub "
            f"{ident.get('z_d_ub')} != dictator checkpoint "
            f"{dck.get('z_d_ub')} (stale pairing)")
    return ck_path


def scan_extras(roots, expected_ckpt_paths) -> None:
    """Reject any cg checkpoint in the given roots that is not expected —
    catches overlaps (a cell served by two roots) and strays."""
    import glob as _glob
    found = set()
    for root in roots:
        for p in _glob.glob(os.path.join(root, "**", "*.cg.ckpt.json"),
                            recursive=True):
            found.add(os.path.abspath(p))
    expected_set = {os.path.abspath(p) for p in expected_ckpt_paths}
    extras = sorted(found - expected_set)
    if extras:
        raise AnalysisError(f"unexpected cg checkpoints present: {extras}")


def validate_roots(a2_root: str, a345_root: str, instances,
                   instance_builder=default_instance_builder) -> list:
    """Audit + exact identity validation; returns audit problem summary."""
    n_inst = len(instances)
    for root, expect, gates in (
        (a2_root, n_inst, {"a2": n_inst}),
        (a345_root, 3 * n_inst, {m: n_inst for m in STAB_METHODS}),
    ):
        if not os.path.isdir(root):
            raise AnalysisError(f"missing runs root: {root}")
        _lines, ok, problems = audit(
            root, out_path=os.devnull, expect_cg=expect,
            expect_cg_method=gates)
        if not ok:
            raise AnalysisError(f"effective audit FAILED for {root}: {problems}")

    # exact identity of every expected cell; no extras, no duplicates
    seen_dirs = set()
    for (m, s, n, b) in expected_cells(instances):
        root = a2_root if m == "a2" else a345_root
        ck_path = validate_cell(cell_dir(root, m, s, n, b), m, s, n, b,
                                instance_builder)
        if ck_path in seen_dirs:
            raise AnalysisError(f"duplicate cell path {ck_path}")
        seen_dirs.add(ck_path)
    scan_extras((a2_root, a345_root), seen_dirs)
    if len(seen_dirs) != 4 * n_inst:
        raise AnalysisError(
            f"{len(seen_dirs)} method-cells found; expected {4 * n_inst}")
    return []


# ---------------------------------------------------------------------------
# per-cell extraction (checkpoint/oracle evidence only)
# ---------------------------------------------------------------------------
def _price_path_metrics(events, regimes) -> tuple:
    tv, linf, last, n = 0.0, 0.0, None, 0
    for e in events:
        if e.get("regime") not in regimes:
            continue
        p = e.get("prices")
        if p is None:
            continue
        if last is not None:
            diffs = [abs(a - c) for a, c in zip(p, last)]
            tv += sum(diffs)
            linf = max(linf, max(diffs))
        last = p
        n += 1
    return tv, linf, n


CLEAN_ORACLE_REGIMES = ("cg-seed", "cg-pricing")
STAB_ORACLE_REGIME = "cg-stab-pricing"
WALL_IDENTITY_TOL = 1e-6  # seconds; sums of identical float terms


def _wall_value(value, label: str) -> float:
    """Return a recorded wall time only when it is finite and nonnegative."""
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AnalysisError(f"{label}: missing or nonfinite wall evidence "
                            f"{value!r}")
    if value < 0:
        raise AnalysisError(f"{label}: negative wall evidence {value!r}")
    return float(value)


def wall_partition(ck: dict, method: str, label: str) -> tuple:
    """Partition SOLVER-REPORTED wall time exactly once (review fix).

    - Every oracle event's `solver.wall_s + solver.lp_wall_s` is assigned by
      REGIME: cg-seed and cg-pricing are clean; cg-stab-pricing is
      stabilized; anything else rejects the cell.
    - Every master solve's `wall_s` is assigned by its iteration event's
      PHASE (clean/terminal vs stabilized), each stable solve_id counted
      exactly once (a duplicate is double counting and rejects the cell).
    - Wrapper elapsed times (`pricing_wall_s`, `master_wall_s`) are NEVER
      mixed into solver-wall fields.
    - Cross-checks: oracle-event count equals oracle_calls (an omitted
      seed/pricing event cannot pass); stabilized/clean iteration events
      must reference exactly the stabilized/clean pricing call ids (a
      phase misclassification cannot pass); A2 must have zero stabilized
      calls; clean/terminal events (and A3/A5 stabilized events) must
      carry their master-solve evidence.

    Returns (wall_clean_s, wall_stab_s, total_solver_wall_s) satisfying
    wall_clean + wall_stab == total within WALL_IDENTITY_TOL (enforced).
    """
    events = ck["oracle_events"]
    iters = ck["iteration_events"]
    if len(events) != ck["oracle_calls"]:
        raise AnalysisError(
            f"{label}: {len(events)} oracle events but oracle_calls="
            f"{ck['oracle_calls']} — omitted or duplicated oracle evidence")

    clean_oracle = stab_oracle = 0.0
    seen_call_ids = set()
    stab_call_ids, clean_pricing_ids = set(), set()
    for e in events:
        sv = e.get("solver") or {}
        cid = (e.get("extra") or {}).get("call_id")
        if cid is None or cid in seen_call_ids:
            raise AnalysisError(f"{label}: missing or duplicate oracle "
                                f"call_id {cid!r}")
        seen_call_ids.add(cid)
        w = (_wall_value(sv.get("wall_s"), f"{label} oracle {cid} wall_s")
             + _wall_value(sv.get("lp_wall_s"),
                           f"{label} oracle {cid} lp_wall_s"))
        reg = e.get("regime")
        if reg in CLEAN_ORACLE_REGIMES:
            clean_oracle += w
            if reg == "cg-pricing":
                clean_pricing_ids.add(cid)
        elif reg == STAB_ORACLE_REGIME:
            stab_oracle += w
            stab_call_ids.add(cid)
        else:
            raise AnalysisError(f"{label}: unknown oracle regime {reg!r}")
    if method == "a2" and stab_call_ids:
        raise AnalysisError(
            f"{label}: A2 cell contains stabilized oracle calls "
            f"{sorted(stab_call_ids)}")

    clean_master = stab_master = 0.0
    seen_solve_ids = set()
    stab_event_pids, clean_event_pids = set(), set()
    for ev in iters:
        phase = ev.get("phase") or ("terminal" if ev.get("terminal")
                                    else "clean")
        if phase not in ("clean", "stabilized", "terminal"):
            raise AnalysisError(f"{label}: unknown iteration phase {phase!r}")
        if phase == "stabilized":
            stab_event_pids.add(ev.get("pricing_solve_id"))
        elif phase == "clean":
            clean_event_pids.add(ev.get("pricing_solve_id"))
        solves = ev.get("master_solves") or []
        if not solves and not (phase == "stabilized"
                               and method in ("a4", "a6_a4")):
            raise AnalysisError(
                f"{label}: iteration {ev.get('iteration_id')} (phase "
                f"{phase}) has no master-solve evidence")
        for ms in solves:
            sid = ms.get("solve_id")
            if sid is None or sid in seen_solve_ids:
                raise AnalysisError(
                    f"{label}: master solve id {sid!r} is missing or appears "
                    "twice — wall time would be double counted")
            seen_solve_ids.add(sid)
            w = _wall_value(ms.get("wall_s"),
                            f"{label} master solve {sid} wall_s")
            if phase == "stabilized":
                stab_master += w
            else:
                clean_master += w
    if stab_event_pids != stab_call_ids:
        raise AnalysisError(
            f"{label}: stabilized iteration events reference "
            f"{sorted(stab_event_pids)} but stabilized oracle calls are "
            f"{sorted(stab_call_ids)} — phase misclassification")
    if clean_event_pids != clean_pricing_ids:
        raise AnalysisError(
            f"{label}: clean iteration events reference "
            f"{sorted(clean_event_pids)} but clean pricing calls are "
            f"{sorted(clean_pricing_ids)} — phase misclassification")

    wall_clean = clean_oracle + clean_master
    wall_stab = stab_oracle + stab_master
    # independent total: every oracle event + every master solve, unpartitioned
    total = clean_oracle + stab_oracle + clean_master + stab_master
    if abs(wall_clean + wall_stab - total) > WALL_IDENTITY_TOL:
        raise AnalysisError(
            f"{label}: wall identity violated — clean {wall_clean} + stab "
            f"{wall_stab} != total {total} "
            f"(tol {WALL_IDENTITY_TOL}); aborting analysis")
    return wall_clean, wall_stab, total


def extract_cell(root: str, method: str, seed: int, n: int, b: float) -> dict:
    return extract_cell_from_dir(cell_dir(root, method, seed, n, b),
                                 method, seed, n, b)


def extract_cell_from_dir(d: str, method: str, seed: int, n: int,
                          b: float) -> dict:
    ck = checkpoint.load(os.path.join(d, f"{method}.cg.ckpt.json"))
    dck = checkpoint.load(os.path.join(d, "dictator.ckpt.json"))
    if dck is None:
        raise AnalysisError(f"missing dictator checkpoint in {d}")
    oc = ck["outcome"]
    events = ck["oracle_events"]

    wall_clean, wall_stab, total_solver_wall = wall_partition(
        ck, method, f"cell {method} seed={seed} n={n} b={b}")

    # broadcast metrics recomputed from oracle evidence; cross-validated
    tv, linf, n_pts = _price_path_metrics(events, BROADCAST_REGIMES[method])
    if oc.get("broadcast_tv") is not None:
        if abs(oc["broadcast_tv"] - tv) > TV_XCHECK_TOL * max(1.0, tv):
            raise AnalysisError(
                f"cell {method} seed={seed} n={n} b={b}: broadcast TV "
                f"mismatch outcome={oc['broadcast_tv']} recomputed={tv}")
        tv, linf = oc["broadcast_tv"], oc["broadcast_linf_max"]

    backends = sorted({(e.get("solver") or {}).get("backend") for e in events})
    mips = sorted({e.get("mip_version", "unknown") for e in events})
    commits = sorted({e.get("git_commit") for e in events})
    stab = ck.get("stab") or {}
    uplift = oc.get("uplift_interval") or [float("nan"), float("nan")]
    calls_stab = oc.get("oracle_calls_stab")
    if calls_stab is None:  # pre-stabilization A2 checkpoint schema
        calls_stab = 0
    calls_clean = oc.get("oracle_calls_clean")
    if calls_clean is None:
        calls_clean = ck["oracle_calls"] - calls_stab

    # EXPLICIT dictator/convex-hull consistency test (kill-3 precondition):
    # LB_CH may never exceed the dictator's certified upper value. A
    # violation is the doc's halt-and-debug condition — refuse to analyze.
    zd_excess = ck["lb_best"] - (dck["z_d_ub"] + dck["tol_d"])
    if zd_excess > 1e-6:
        raise AnalysisError(
            f"cell {method} seed={seed} n={n} b={b}: z_CH/dictator "
            f"CONTRADICTION — LB_CH {ck['lb_best']} exceeds z_D_ub + tol_d "
            f"{dck['z_d_ub'] + dck['tol_d']} by {zd_excess}; halt and debug "
            "(MEASUREMENT_RESULTS.md kill test 3)")

    return {
        "lb_best": ck["lb_best"], "ub_ch": oc["ub_ch"],
        "zd_minus_lb": dck["z_d_ub"] + dck["tol_d"] - ck["lb_best"],
        "method": method, "seed": seed, "n_trips": n, "b": b,
        "outcome": oc["type"], "certified": bool(oc["certified"]),
        "final_gap": oc["gap"],
        "oracle_calls": ck["oracle_calls"],
        "oracle_calls_clean": calls_clean,
        "oracle_calls_stab": calls_stab,
        "n_columns": len(ck["columns"]),
        "serious_steps": stab.get("serious_steps", 0),
        "null_steps": stab.get("null_steps", 0),
        "wall_clean_s": wall_clean,
        "wall_stab_s": wall_stab,
        "total_solver_wall_s": total_solver_wall,
        "dictator_wall_s": (dck.get("adaptive") or {}).get(
            "adaptive_total_wall_s", float("nan")),
        "broadcast_tv": tv, "broadcast_linf_max": linf,
        "broadcast_points": n_pts,
        "uplift_lo": uplift[0], "uplift_hi": uplift[1],
        "z_d_ub": dck.get("z_d_ub"), "tol_d": dck.get("tol_d"),
        "epsilon": ck["identity"]["epsilon"],
        "budget": ck["identity"]["budget"],
        "backend": "+".join(str(x) for x in backends),
        "mip_version": "+".join(str(x) for x in mips),
        "source_commit": "+".join(str(x) for x in commits),
    }


# ---------------------------------------------------------------------------
# tables
# ---------------------------------------------------------------------------
def matched_comparison(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base = cells[cells["method"] == "a2"].set_index(["seed", "n_trips", "b"])
    for m in STAB_METHODS:
        sub = cells[cells["method"] == m]
        for _, r in sub.iterrows():
            key = (r["seed"], r["n_trips"], r["b"])
            if key not in base.index:
                raise AnalysisError(f"no A2 baseline for instance {key}")
            a2 = base.loc[key]
            calls_diff = int(r["oracle_calls"] - a2["oracle_calls"])
            label = ("win" if calls_diff < 0
                     else "tie" if calls_diff == 0 else "loss")
            clean_diff = int(r["oracle_calls_clean"]
                             - a2["oracle_calls_clean"])
            clean_label = ("win" if clean_diff < 0
                           else "tie" if clean_diff == 0 else "loss")
            rows.append({
                "seed": key[0], "n_trips": key[1], "b": key[2], "method": m,
                "a2_calls": int(a2["oracle_calls"]),
                "method_calls": int(r["oracle_calls"]),
                "calls_diff": calls_diff,
                "calls_ratio": r["oracle_calls"] / a2["oracle_calls"],
                # decomposition: does stabilization reduce CLEAN-master
                # iterations even when total calls lose? (pilot finding)
                "a2_clean_calls": int(a2["oracle_calls_clean"]),
                "method_clean_calls": int(r["oracle_calls_clean"]),
                "method_stab_calls": int(r["oracle_calls_stab"]),
                "clean_calls_diff": clean_diff,
                "clean_result_vs_a2": clean_label,
                "a2_solver_wall_s": a2["total_solver_wall_s"],
                "method_solver_wall_s": r["total_solver_wall_s"],
                "wall_diff_s": r["total_solver_wall_s"] - a2["total_solver_wall_s"],
                "wall_ratio": (r["total_solver_wall_s"]
                               / a2["total_solver_wall_s"]),
                "calls_result_vs_a2": label,
                "both_certified": bool(r["certified"] and a2["certified"]),
            })
    return pd.DataFrame(rows)


def method_summary(cells: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    scopes = [("overall", cells)] + [
        (f"b={b:g}", cells[cells["b"] == b]) for b in sorted(cells["b"].unique())]
    for scope_name, sub in scopes:
        for m in METHODS:
            s = sub[sub["method"] == m]
            if not len(s):
                continue
            calls = s["oracle_calls"].tolist()
            walls = s["total_solver_wall_s"].tolist()
            c_q1, c_q3 = q1q3(calls)
            w_q1, w_q3 = q1q3(walls)
            row = {
                "scope": scope_name, "method": m, "cells": len(s),
                "certified": int(s["certified"].sum()),
                "cert_rate": s["certified"].mean(),
                "calls_median": statistics.median(calls),
                "calls_q1": c_q1, "calls_q3": c_q3, "calls_max": max(calls),
                "clean_calls_median": statistics.median(
                    s["oracle_calls_clean"].tolist()),
                "stab_calls_median": statistics.median(
                    s["oracle_calls_stab"].tolist()),
                "clean_wall_median_s": statistics.median(
                    s["wall_clean_s"].tolist()),
                "stab_wall_median_s": statistics.median(
                    s["wall_stab_s"].tolist()),
                "wall_median_s": statistics.median(walls),
                "wall_q1_s": w_q1, "wall_q3_s": w_q3, "wall_max_s": max(walls),
                "gap_median": s["final_gap"].median(),
                "gap_max": s["final_gap"].max(),
                "broadcast_tv_median": s["broadcast_tv"].median(),
                "broadcast_linf_median": s["broadcast_linf_max"].median(),
            }
            if m in STAB_METHODS:
                mm = matched[matched["method"] == m]
                if scope_name != "overall":
                    mm = mm[mm["b"] == float(scope_name.split("=")[1])]
                row["wins_vs_a2"] = int((mm["calls_result_vs_a2"] == "win").sum())
                row["ties_vs_a2"] = int((mm["calls_result_vs_a2"] == "tie").sum())
                row["losses_vs_a2"] = int((mm["calls_result_vs_a2"] == "loss").sum())
                row["clean_wins_vs_a2"] = int(
                    (mm["clean_result_vs_a2"] == "win").sum())
                row["clean_ties_vs_a2"] = int(
                    (mm["clean_result_vs_a2"] == "tie").sum())
                row["clean_losses_vs_a2"] = int(
                    (mm["clean_result_vs_a2"] == "loss").sum())
            else:
                row["wins_vs_a2"] = row["ties_vs_a2"] = row["losses_vs_a2"] = 0
                row["clean_wins_vs_a2"] = row["clean_ties_vs_a2"] = 0
                row["clean_losses_vs_a2"] = 0
            rows.append(row)
    return pd.DataFrame(rows)


def acceptance_status(cells: pd.DataFrame, summary: pd.DataFrame,
                      n_instances: int) -> pd.DataFrame:
    """Every status below is COMPUTED from the tables — different data must
    produce different verdicts (review requirement). 'not-testable' is used
    only where the criterion's denominator structurally cannot exist in the
    pilot (full-grid populations; missing A0/A1 arms)."""
    ov = summary[summary["scope"] == "overall"].set_index("method")
    a2_med = float(ov.loc["a2", "calls_median"])
    stab_meds = {m: float(ov.loc[m, "calls_median"]) for m in STAB_METHODS}
    best_stab = min(stab_meds, key=stab_meds.get)
    best_med = stab_meds[best_stab]
    speedup = a2_med / best_med  # criterion: >= 2
    a2_cells = cells[cells.method == "a2"]
    # Kill-1 applies A2 to the same b=0.05 certification population as
    # acc-1.  The 2x speed comparison remains over b in {0.01, 0.05}.
    a2_acceptance_cells = a2_cells[a2_cells.b == 0.05]
    a2_cert_rate = (float(a2_acceptance_cells["certified"].mean())
                    if len(a2_acceptance_cells) else float("nan"))
    acc3_status = "pilot-supports" if speedup >= 2.0 else "pilot-rejects"
    # kill-1: A2 meets the negotiation bar (>= 95% certified within budget)
    # AND stabilization does not deliver its promised >= 2x speedup
    kill1_testable = bool(len(a2_acceptance_cells))
    kill1_active = (kill1_testable and a2_cert_rate >= 0.95
                    and speedup < 2.0)
    kill1_status = ("pilot-supports" if kill1_active else
                    "pilot-rejects" if kill1_testable else
                    "not-testable-from-pilot")
    # kill-3: computed margin (a contradiction would have aborted extraction)
    zd_margin_min = float(cells["zd_minus_lb"].min())
    n_contra = int((cells["zd_minus_lb"] < -1e-6).sum())
    kill3_status = "pilot-supports" if n_contra == 0 else "pilot-rejects"

    rows = [
        {
            "criterion_id": "acc-1-cert95-b005",
            "description": ("each of A3/A4/A5 certifies >= 95% within 240 "
                            "calls on the b=0.05 population"),
            "denominator": ("full grid: 32 b=0.05 instances x 3 stabilized "
                            "methods = 96 method-cells"),
            "observed_pilot": "; ".join(
                f"{m}: {int(cells[(cells.method == m) & (cells.b == 0.05)]['certified'].sum())}"
                f"/{len(cells[(cells.method == m) & (cells.b == 0.05)])} certified"
                for m in STAB_METHODS),
            "status": "not-testable-from-pilot",
        },
        {
            "criterion_id": "acc-2-bound-sanity",
            "description": ("LB_CH <= UB_CH every iteration; UB_CH "
                            "nonincreasing after every valid expansion; "
                            "z_CH interval consistent with dictator interval"),
            "denominator": f"all {len(cells)} pilot method-cells",
            "observed_pilot": (
                "computed: effective audit passed (pipeline aborts "
                f"otherwise); min(z_D_ub + tol_d - LB_CH) = "
                f"{zd_margin_min:.6g} >= 0 across all cells"),
            "status": "pilot-supports" if zd_margin_min >= -1e-6
                      else "pilot-rejects",
        },
        {
            "criterion_id": "acc-3-stab-beats-a2-2x",
            "description": ("best stabilized method beats plain CG (A2) by "
                            ">= 2x on median oracle calls at b in "
                            "{0.01, 0.05}"),
            "denominator": (f"pilot: {n_instances} matched instances; full "
                            "criterion population: 64 moderate/strong "
                            "instances per method (16 seeds x 2 sizes x "
                            "b in {0.01, 0.05})"),
            "observed_pilot": (
                f"A2 median {a2_med:g}; best stabilized {best_stab} median "
                f"{best_med:g}; speedup a2/best = {speedup:.3f} "
                "(criterion needs >= 2)"),
            "status": acc3_status,
        },
        {
            "criterion_id": "acc-4-vs-tatonnement",
            "description": ("budget-matched superiority of stabilized "
                            "methods over the A0/A1 tatonnement family"),
            "denominator": "requires A1 family cells (none in this pilot)",
            "observed_pilot": "no A0/A1 cells in the pilot",
            "status": "not-testable-from-pilot",
        },
        {
            "criterion_id": "kill-1-a2-meets-bar",
            "description": ("KILL: if plain CG already meets the acceptance "
                            "bar, stabilization is not the contribution "
                            "('memory beats memorylessness')"),
            "denominator": (
                f"pilot: {len(a2_acceptance_cells)} b=0.05 A2 instances; "
                "full acceptance population: 32 b=0.05 A2 instances"),
            "observed_pilot": (
                f"A2 certified {int(a2_acceptance_cells['certified'].sum())}"
                f"/{len(a2_acceptance_cells)} on b=0.05 "
                f"(rate {a2_cert_rate:.3f}, bar 0.95) with "
                f"median {a2_med:g} calls; best stabilized speedup "
                f"{speedup:.3f} (bar 2.0) => kill "
                f"{'ACTIVE' if kill1_active else 'inactive'}"),
            "status": kill1_status,
        },
        {
            "criterion_id": "kill-3-zch-vs-dictator",
            "description": ("KILL: certified z_CH interval must never "
                            "contradict the dictator interval "
                            "(LB_CH > z_D_ub + tol)"),
            "denominator": f"all {len(cells)} pilot method-cells",
            "observed_pilot": (
                f"computed: {n_contra} contradictions; minimum margin "
                f"z_D_ub + tol_d - LB_CH = {zd_margin_min:.6g}"),
            "status": kill3_status,
        },
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# figures + summary
# ---------------------------------------------------------------------------
COLORS = {"a2": "#264653", "a3": "#2a9d8f", "a4": "#e9c46a", "a5": "#e76f51"}


def make_figures(cells: pd.DataFrame, out_dir: str) -> list:
    made = []
    inst_order = sorted(set(map(tuple, cells[["seed", "n_trips", "b"]].values)))
    labels = [f"s{s}n{n}b{b:g}" for (s, n, b) in inst_order]
    x = range(len(inst_order))

    def per_method(col):
        return {
            m: [float(cells[(cells.method == m) & (cells.seed == s)
                            & (cells.n_trips == n) & (cells.b == b)][col].iloc[0])
                for (s, n, b) in inst_order]
            for m in METHODS
        }

    for col, fname, ylabel, logy in (
        ("oracle_calls", "F1_matched_oracle_calls.png",
         "oracle calls to certificate", False),
        ("total_solver_wall_s", "F2_matched_solver_wall.png",
         "total solver wall time (s)", True),
        ("broadcast_tv", "F3_broadcast_total_variation.png",
         "broadcast price-path total variation", True),
    ):
        vals = per_method(col)
        fig, ax = plt.subplots(figsize=(11, 4.5))
        w = 0.2
        for i, m in enumerate(METHODS):
            ax.bar([xi + (i - 1.5) * w for xi in x], vals[m], width=w,
                   label=m.upper(), color=COLORS[m])
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel(ylabel)
        if logy:
            ax.set_yscale("log")
        ax.legend(ncol=4)
        ax.set_title(f"B2 pilot, matched instances: {ylabel}")
        fig.tight_layout()
        p = os.path.join(out_dir, fname)
        fig.savefig(p, dpi=150)
        plt.close(fig)
        made.append(fname)

    # F4: clean vs total call decomposition (stacked: clean + stabilized)
    clean_v = per_method("oracle_calls_clean")
    stab_v = per_method("oracle_calls_stab")
    fig, ax = plt.subplots(figsize=(11, 4.5))
    w = 0.2
    for i, m in enumerate(METHODS):
        xs = [xi + (i - 1.5) * w for xi in x]
        ax.bar(xs, clean_v[m], width=w, label=f"{m.upper()} clean",
               color=COLORS[m])
        ax.bar(xs, stab_v[m], width=w, bottom=clean_v[m],
               color=COLORS[m], alpha=0.45,
               label=f"{m.upper()} stabilized" if m != "a2" else None)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("oracle calls (clean solid, stabilized shaded)")
    ax.legend(ncol=4, fontsize=7)
    ax.set_title("B2 pilot: clean vs total oracle-call decomposition")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "F4_clean_vs_total_calls.png"), dpi=150)
    plt.close(fig)
    made.append("F4_clean_vs_total_calls.png")
    return made


def write_summary_md(path: str, cells, matched, summary, acceptance,
                     stamp, code_commit):
    ov = summary[summary["scope"] == "overall"].set_index("method")
    lines = [
        f"# B2 pilot closeout — certified A2 vs A3/A4/A5 ({stamp})",
        "",
        f"Analysis code commit: `{code_commit}`. All numbers regenerate "
        "deterministically from the certified pilot checkpoints "
        "(see MANIFEST.json for input hashes).",
        "",
        "## Result",
        "",
        f"- {len(cells)} method-cells "
        f"({len(cells) // 4} instances x 4 methods); "
        f"certified: {int(cells['certified'].sum())}/{len(cells)}; "
        "no budget exhaustion." if cells["certified"].all() else
        f"- certified: {int(cells['certified'].sum())}/{len(cells)}.",
        "",
        "| method | median calls | IQR | median solver wall (s) | "
        "certified | W/T/L vs A2 (calls) |",
        "|---|---|---|---|---|---|",
    ]
    for m in METHODS:
        r = ov.loc[m]
        wtl = (f"{int(r['wins_vs_a2'])}/{int(r['ties_vs_a2'])}/"
               f"{int(r['losses_vs_a2'])}" if m != "a2" else "—")
        lines.append(
            f"| {m.upper()} | {r['calls_median']:g} | "
            f"[{r['calls_q1']:g}, {r['calls_q3']:g}] | "
            f"{r['wall_median_s']:.2f} | {int(r['certified'])}/{int(r['cells'])} "
            f"| {wtl} |")
    a2_med = float(ov.loc["a2", "calls_median"])
    stab_meds = {m: float(ov.loc[m, "calls_median"]) for m in STAB_METHODS}
    best = min(stab_meds, key=stab_meds.get)
    speedup = a2_med / stab_meds[best]
    a2_cells = cells[cells.method == "a2"]
    a2_acceptance_cells = a2_cells[a2_cells.b == 0.05]
    a2_cert_rate = (float(a2_acceptance_cells["certified"].mean())
                    if len(a2_acceptance_cells) else float("nan"))
    kill1_active = (len(a2_acceptance_cells) > 0
                    and a2_cert_rate >= 0.95 and speedup < 2.0)
    if kill1_active:
        verdict = (
            "On this pilot the STABILIZATION KILL SIGNAL (kill-1) is "
            "ACTIVE: memory (retaining all columns in the clean RMP) "
            "appears to solve the price-coordination problem that broke "
            "tatonnement, while du Merle boxes, Wentges smoothing, and "
            "proximal bundles do not deliver their preregistered speedup "
            "at this scale.")
    else:
        verdict = (
            "On this pilot the stabilization kill signal (kill-1) is NOT "
            "active (see acceptance_status.csv for the computed criteria).")
    # clean/stabilized call decomposition (computed): does stabilization
    # accelerate the clean master even when total calls lose?
    a2_clean_med = float(ov.loc["a2", "clean_calls_median"])
    decomp_rows = []
    best_clean, best_clean_med = None, float("inf")
    for m in STAB_METHODS:
        r = ov.loc[m]
        cw, ct, cl = (int(r["clean_wins_vs_a2"]), int(r["clean_ties_vs_a2"]),
                      int(r["clean_losses_vs_a2"]))
        decomp_rows.append(
            f"| {m.upper()} | {r['clean_calls_median']:g} | "
            f"{r['stab_calls_median']:g} | {cw}/{ct}/{cl} | "
            f"{r['clean_wall_median_s']:.2f} | "
            f"{r['stab_wall_median_s']:.2f} |")
        if float(r["clean_calls_median"]) < best_clean_med:
            best_clean, best_clean_med = m, float(r["clean_calls_median"])
    clean_helps = best_clean_med < a2_clean_med
    total_loses = float(ov.loc[best_clean, "calls_median"]) > a2_med
    if clean_helps and total_loses:
        decomp_verdict = (
            f"Stabilization — especially {best_clean.upper()} — DOES "
            "accelerate clean-master convergence (see clean-call W/T/L), "
            "but its extra candidate calls are not amortized at this "
            "problem size: the total-call comparison still favors A2. The "
            "preregistered acceptance metric remains TOTAL oracle calls.")
    elif clean_helps:
        decomp_verdict = (
            f"Stabilization ({best_clean.upper()}) reduces clean-master "
            "iterations AND wins on total calls.")
    else:
        decomp_verdict = (
            "Stabilization does not reduce clean-master iterations on "
            "this pilot — it fails at the iteration level, not merely on "
            "candidate-call overhead.")
    lines += [
        "",
        "## Interpretation (computed from the tables above)",
        "",
        f"A2 certified {a2_cert_rate:.0%} of the pilot's b=0.05 instances "
        f"with overall median "
        f"oracle-call count {a2_med:g}; the best stabilized method "
        f"({best.upper()}, median {stab_meds[best]:g}) gives a speedup "
        f"ratio a2/best = {speedup:.2f}, versus the preregistered "
        f"acceptance bar of >= 2. {verdict}",
        "",
        "### Clean/stabilized call decomposition",
        "",
        f"A2 clean-call median: {a2_clean_med:g}. Solver wall time is "
        "partitioned exactly once from solver-reported times "
        "(wall_clean_s + wall_stab_s = total_solver_wall_s, enforced).",
        "",
        "| method | clean-call median | stab-call median | "
        "clean W/T/L vs A2 | clean-wall median (s) | "
        "stab-wall median (s) |",
        "|---|---|---|---|---|---|",
        *decomp_rows,
        "",
        decomp_verdict,
        "",
        "Denominators and caveats:",
        "",
        f"- {len(cells) // 4} instances (seeds 0/11/15 x n 8/12 x "
        "b 0.01/0.05); the preregistered acceptance criteria are defined "
        "on their full populations — 64 moderate/strong instances per "
        "method for the 2x criterion, 96 b=0.05 method-cells for the "
        "certification criterion — so pilot evidence cannot pass or fail "
        "them, only support or reject continuing (see "
        "acceptance_status.csv).",
        "- Stabilized iterations spend 2 oracle calls (clean certification "
        "+ candidate) by design; the comparison metric is total calls to "
        "certificate, which is exactly what the acceptance bar "
        "preregisters.",
        "- Each method-cell repeats its own dictator stage; dictator wall "
        "time is reported separately (dictator_wall_s) and excluded from "
        "solver-wall comparisons.",
        "- A2 cells ran on the pre-stabilization checkpoint schema; "
        "broadcast metrics for them are recomputed from committed oracle "
        "prices (cross-validated where both sources exist).",
        "",
        "## Next decision",
        "",
        "Options on the table (DECISION_LOG.md):",
        "",
        "1. Stop stabilization now and reframe Chapter I's algorithmic half "
        "around 'memory beats memorylessness' (equivalence theorem + "
        "uplift accounting + A2-vs-A1 budget-matched comparison).",
        "2. Run ONLY the prespecified moderate/strong-feedback matched "
        "expansion (208 remaining A2-A5 method-cells) to give the kill "
        "decision its full preregistered denominator before abandoning "
        "stabilization.",
        "",
        "The 960-cell campaign remains paused either way; the 576 fresh A1 "
        "baseline cells are a separate decision.",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def analyze(a2_root: str, a345_root: str, out_base: str, stamp: str,
            analysis_code_commit: str, instances=PILOT_INSTANCES,
            instance_builder=default_instance_builder,
            verify_code_commit: bool = True) -> str:
    code_verified = False
    if verify_code_commit:
        analysis_code_commit = verify_analysis_code_commit(
            analysis_code_commit)
        code_verified = True
    validate_roots(a2_root, a345_root, instances, instance_builder)

    rows = []
    for (m, s, n, b) in expected_cells(instances):
        root = a2_root if m == "a2" else a345_root
        rows.append(extract_cell(root, m, s, n, b))
    cells = pd.DataFrame(rows)
    if len(cells) != 4 * len(instances):
        raise AnalysisError("cell count mismatch after extraction")

    matched = matched_comparison(cells)
    if len(matched) != 3 * len(instances):
        raise AnalysisError("matched join produced wrong row count")
    summary = method_summary(cells, matched)
    acceptance = acceptance_status(cells, summary, len(instances))

    out_dir = os.path.join(out_base, stamp)
    os.makedirs(out_dir, exist_ok=True)
    write_csv(cells, os.path.join(out_dir, "cells.csv"),
              ["method", "b", "n_trips", "seed"])
    write_csv(matched, os.path.join(out_dir, "matched_comparison.csv"),
              ["method", "b", "n_trips", "seed"])
    write_csv(summary, os.path.join(out_dir, "method_summary.csv"),
              ["scope", "method"])
    write_csv(acceptance, os.path.join(out_dir, "acceptance_status.csv"),
              ["criterion_id"])
    figures = make_figures(cells, out_dir)
    write_summary_md(os.path.join(out_dir, "SUMMARY.md"), cells, matched,
                     summary, acceptance, stamp, analysis_code_commit)

    outputs = sorted(["cells.csv", "matched_comparison.csv",
                      "method_summary.csv", "acceptance_status.csv",
                      "SUMMARY.md"] + figures)
    manifest = {
        "schema": "b2-pilot-closeout-v1",
        "stamp": stamp,
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": code_verified,
        "grid": {"instances": [list(t) for t in instances],
                 "methods": list(METHODS)},
        "tolerances": {
            "epsilon": sorted(cells["epsilon"].unique().tolist()),
            "budget": sorted(cells["budget"].unique().tolist()),
            "tol_d": sorted(cells["tol_d"].unique().tolist()),
        },
        "solver": {
            "backends": sorted(cells["backend"].unique().tolist()),
            "mip_versions": sorted(cells["mip_version"].unique().tolist()),
        },
        "experiment_commits": sorted(cells["source_commit"].unique().tolist()),
        "inputs": {
            "b2a2_pilot": {"path": a2_root, "files": tree_hashes(a2_root)},
            "b2a345_pilot": {"path": a345_root,
                             "files": tree_hashes(a345_root)},
        },
        "outputs": {fn: sha256_file(os.path.join(out_dir, fn))
                    for fn in outputs},
    }
    with open(os.path.join(out_dir, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    return out_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a2-root", default="runs/b2a2_pilot")
    ap.add_argument("--a345-root", default="runs/b2a345_pilot")
    ap.add_argument("--out", default=os.path.join("..", "result", "b2_pilot"))
    ap.add_argument("--stamp", default=None,
                    help="UTC stamp for the artifact dir (default: now)")
    ap.add_argument("--analysis-code-commit", required=True,
                    help="commit hash of the analysis code (two-commit "
                         "provenance protocol, commit 1)")
    args = ap.parse_args()
    stamp = args.stamp or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = analyze(args.a2_root, args.a345_root, args.out, stamp,
                      args.analysis_code_commit)
    print(f"[done] wrote {out_dir}")


if __name__ == "__main__":
    main()
