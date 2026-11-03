#!/usr/bin/env python3
"""Deterministic FULL-POPULATION B2 analysis: 64 moderate/strong instances
x methods A2-A5 = 256 method-cells, joining the certified pilots with the
208-cell matched expansion.

Inputs (raw, gitignored, never committed):
  runs/b2a2_pilot     12 A2 cells   (pilot seeds {0,11,15})
  runs/b2a345_pilot   36 A3-A5 cells (pilot seeds)
  runs/b2_expansion   208 cells      (seeds 0-15 minus pilot, all methods)

The union must be EXACT: no overlaps (a cell served by two roots), no gaps
(a missing instance/method), no extras. Every cell is identity-validated
(instance and market hashes recomputed from the generators; dictator
checkpoint identity and z_d_ub pairing), and every metric comes from
checkpoint/oracle evidence through the corrected wall partition
(wall_clean_s + wall_stab_s == total_solver_wall_s enforced per cell).

Preregistered criteria at their TRUE denominators (all labels computed):
- acc-1: each of A3/A4/A5 certifies >= 95% within 240 calls on EXACTLY 32
  b = 0.05 instances per method (96 method-cells).
- acc-3: best stabilized method beats A2 by >= 2x on median TOTAL oracle
  calls over EXACTLY 64 matched instances per method (threshold unchanged).
- kill-1: A2 certifies >= 95% on its 32 b = 0.05 cells AND acc-3 fails.
- kill-3: no cell's LB_CH exceeds z_D_ub + tol_d (halt-and-debug on
  violation, enforced during extraction).
- acc-4 (vs tatonnement) remains not-testable: no A1 cells exist.

Two-call cells (seed + one clean certification call) are LEGITIMATE
immediate-certification outcomes: they are verified (identity,
certification, coherence) and REPORTED, never filtered.

Outputs (committed): result/b2_full/<stamp>/ with MANIFEST.json (hashing
every input and output), cells.csv, matched_comparison.csv,
method_summary.csv, acceptance_status.csv, two_call_cells.csv, SUMMARY.md,
and figures. Byte-identical regeneration for identical inputs and stamp.

Two-commit protocol: commit 1 is this code; Codex regenerates artifacts
from the transferred raw data against the verified code commit.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from experiments.analyze_b2_pilot import (
    AnalysisError,
    METHODS,
    STAB_METHODS,
    default_instance_builder,
    extract_cell_from_dir,
    matched_comparison,
    method_summary,
    scan_extras,
    sha256_file,
    tree_hashes,
    validate_cell,
    verify_analysis_code_commit,
    write_csv,
)
from experiments.audit_runs import audit

PILOT_SEEDS = (0, 11, 15)
FULL_INSTANCES = tuple(
    (s, n, b) for s in range(16) for n in (8, 12) for b in (0.01, 0.05))
PILOT_INSTANCES_FULL = tuple(
    (s, n, b) for (s, n, b) in FULL_INSTANCES if s in PILOT_SEEDS)
EXPANSION_INSTANCES_FULL = tuple(
    (s, n, b) for (s, n, b) in FULL_INSTANCES if s not in PILOT_SEEDS)
CERT_RATE_BAR = 0.95
SPEEDUP_BAR = 2.0
EPS = 1e-2
BUDGET = 240
TOL_D = 1e-2
EXPECTED_EXPERIMENT = {
    "a2_pilot": "b2a2-pilot",
    "a345_pilot": "b2a345-pilot",
    "expansion": "b2-expansion",
}


# ---------------------------------------------------------------------------
# locating and validating the exact 12 + 36 + 208 union
# ---------------------------------------------------------------------------
def locate_cell_dir(roots: dict, pilot_instances, m, s, n, b) -> str:
    """Deterministic single source per cell: pilot roots for pilot
    instances (A2 pilot uses unprefixed dirs), expansion root otherwise
    (all methods prefixed)."""
    base = f"s{s}_n{n}_b{b:g}"
    if (s, n, b) in pilot_instances:
        if m == "a2":
            return os.path.join(roots["a2_pilot"], base)
        return os.path.join(roots["a345_pilot"], f"{m}_{base}")
    return os.path.join(roots["expansion"], f"{m}_{base}")


def validate_full(roots: dict, instances, pilot_instances,
                  instance_builder=default_instance_builder) -> None:
    pilot_set = set(pilot_instances)
    inst_set = set(instances)
    if not pilot_set <= inst_set:
        raise AnalysisError("pilot instances not a subset of the population")
    n_pilot = len(pilot_set)
    n_exp = len(inst_set - pilot_set)
    # programmatic effective audits with exact per-root provenance
    for key, expect, gates in (
        ("a2_pilot", n_pilot, {"a2": n_pilot}),
        ("a345_pilot", 3 * n_pilot, {m: n_pilot for m in STAB_METHODS}),
        ("expansion", 4 * n_exp, {m: n_exp for m in METHODS}),
    ):
        root = roots[key]
        if not os.path.isdir(root):
            raise AnalysisError(f"missing runs root: {root}")
        _lines, ok, problems = audit(root, out_path=os.devnull,
                                     expect_cg=expect,
                                     expect_cg_method=gates)
        if not ok:
            raise AnalysisError(
                f"effective audit FAILED for {root}: {problems}")

    seen = set()
    for (s, n, b) in instances:
        for m in METHODS:
            d = locate_cell_dir(roots, pilot_set, m, s, n, b)
            ck_path = validate_cell(d, m, s, n, b, instance_builder)
            ck = json.load(open(ck_path))
            experiments = {e.get("experiment")
                           for e in ck.get("oracle_events") or []}
            expected_experiment = (EXPECTED_EXPERIMENT["a2_pilot"]
                                   if (s, n, b) in pilot_set and m == "a2"
                                   else EXPECTED_EXPERIMENT["a345_pilot"]
                                   if (s, n, b) in pilot_set
                                   else EXPECTED_EXPERIMENT["expansion"])
            if experiments != {expected_experiment}:
                raise AnalysisError(
                    f"cell {m} seed={s} n={n} b={b}: CG experiment "
                    f"lineage {sorted(map(str, experiments))} != "
                    f"{expected_experiment!r}")
            if ck_path in seen:
                raise AnalysisError(f"duplicate/overlapping cell {ck_path}")
            seen.add(ck_path)
    scan_extras(tuple(roots.values()), seen)
    if len(seen) != 4 * len(inst_set):
        raise AnalysisError(
            f"{len(seen)} method-cells found; expected {4 * len(inst_set)}")


# ---------------------------------------------------------------------------
# denominator gates and criteria (all labels computed)
# ---------------------------------------------------------------------------
def check_denominators(cells: pd.DataFrame, expected_b005_per_method: int,
                       expected_matched_per_method: int) -> None:
    """The preregistered criteria are only meaningful at their exact
    denominators; a wrong count is a population error, not a rounding
    issue — abort."""
    for m in METHODS:
        got = len(cells[(cells.method == m) & (cells.b == 0.05)])
        if got != expected_b005_per_method:
            raise AnalysisError(
                f"denominator error: {m} has {got} b=0.05 cells; expected "
                f"{expected_b005_per_method}")
        tot = len(cells[cells.method == m])
        if tot != expected_matched_per_method:
            raise AnalysisError(
                f"denominator error: {m} has {tot} matched cells; expected "
                f"{expected_matched_per_method}")


def check_scientific_contract(cells: pd.DataFrame) -> None:
    """Reject a population assembled under settings other than the
    preregistered B2 contract. Identity coherence alone is insufficient:
    all sources must use the same epsilon, budget, and dictator tolerance."""
    expected = {"epsilon": EPS, "budget": BUDGET, "tol_d": TOL_D}
    for field, value in expected.items():
        observed = set(cells[field].tolist())
        if observed != {value}:
            raise AnalysisError(
                f"scientific-contract error: {field} values "
                f"{sorted(map(str, observed))} != {value}")


def two_call_report(cells: pd.DataFrame) -> pd.DataFrame:
    """Cells that certified after only seed + one clean call are legitimate
    immediate-certification outcomes: verify coherence explicitly
    (identity was already validated) and REPORT them — never filter them.
    The label is deliberately causal-neutral: these cases can occur at
    either tested feedback strength."""
    two = cells[cells["oracle_calls"] <= 2].copy()
    for _, r in two.iterrows():
        label = f"{r['method']} seed={r['seed']} n={r['n_trips']} b={r['b']}"
        if r["outcome"] != "certified" or not bool(r["certified"]):
            raise AnalysisError(
                f"two-call cell {label} is NOT certified — outcome "
                f"{r['outcome']!r}")
        if int(r["oracle_calls_stab"]) != 0:
            raise AnalysisError(
                f"two-call cell {label}: has stabilized calls, impossible "
                "before the first candidate phase")
        if int(r["oracle_calls"]) != 2 or int(r["oracle_calls_clean"]) != 2:
            raise AnalysisError(
                f"two-call cell {label}: expected exactly seed + one clean "
                f"pricing call (total=clean=2), got total="
                f"{r['oracle_calls']} clean={r['oracle_calls_clean']}")
        if r["final_gap"] > r["epsilon"] + 1e-12:
            raise AnalysisError(
                f"two-call cell {label}: gap {r['final_gap']} > epsilon")
    cols = ["method", "seed", "n_trips", "b", "outcome", "certified",
            "final_gap", "oracle_calls", "oracle_calls_clean",
            "oracle_calls_stab", "n_columns", "uplift_lo", "uplift_hi"]
    out = two[cols].copy()
    out["identity_verified"] = True
    out["certification_verified"] = True
    return out


def acceptance_full(cells: pd.DataFrame, summary: pd.DataFrame,
                    expected_b005: int, expected_matched: int) -> pd.DataFrame:
    """Full-population verdicts at true denominators; statuses in
    {pass, fail, not-testable}, all computed."""
    ov = summary[summary["scope"] == "overall"].set_index("method")
    a2_med = float(ov.loc["a2", "calls_median"])
    stab_meds = {m: float(ov.loc[m, "calls_median"]) for m in STAB_METHODS}
    best_stab = min(stab_meds, key=stab_meds.get)
    speedup = a2_med / stab_meds[best_stab]
    acc3_pass = speedup >= SPEEDUP_BAR

    acc1_parts, acc1_pass = [], True
    for m in STAB_METHODS:
        sub = cells[(cells.method == m) & (cells.b == 0.05)]
        rate = float(sub["certified"].mean())
        acc1_parts.append(
            f"{m}: {int(sub['certified'].sum())}/{len(sub)} "
            f"({rate:.3f})")
        acc1_pass = acc1_pass and (rate >= CERT_RATE_BAR)

    a2_b005 = cells[(cells.method == "a2") & (cells.b == 0.05)]
    a2_rate = float(a2_b005["certified"].mean())
    kill1_active = (a2_rate >= CERT_RATE_BAR) and not acc3_pass

    zd_margin_min = float(cells["zd_minus_lb"].min())
    n_contra = int((cells["zd_minus_lb"] < -1e-6).sum())

    rows = [
        {
            "criterion_id": "acc-1-cert95-b005",
            "description": ("each of A3/A4/A5 certifies >= 95% within 240 "
                            "calls on the b=0.05 population"),
            "denominator": (f"{expected_b005} b=0.05 instances per "
                            f"stabilized method ({3 * expected_b005} "
                            "method-cells) — full population"),
            "observed": "; ".join(acc1_parts),
            "status": "pass" if acc1_pass else "fail",
        },
        {
            "criterion_id": "acc-2-bound-sanity",
            "description": ("LB_CH <= UB_CH throughout; UB_CH nonincreasing; "
                            "z_CH interval consistent with dictator "
                            "interval"),
            "denominator": f"all {len(cells)} method-cells",
            "observed": (f"audits passed; min(z_D_ub + tol_d - LB_CH) = "
                         f"{zd_margin_min:.6g}"),
            "status": "pass" if zd_margin_min >= -1e-6 else "fail",
        },
        {
            "criterion_id": "acc-3-stab-beats-a2-2x",
            "description": ("best stabilized method beats plain CG (A2) by "
                            ">= 2x on median TOTAL oracle calls at b in "
                            "{0.01, 0.05}"),
            "denominator": (f"{expected_matched} matched instances per "
                            "method — full population"),
            "observed": (f"A2 median {a2_med:g}; best stabilized "
                         f"{best_stab} median {stab_meds[best_stab]:g}; "
                         f"speedup {speedup:.3f} (bar {SPEEDUP_BAR:g})"),
            "status": "pass" if acc3_pass else "fail",
        },
        {
            "criterion_id": "acc-4-vs-tatonnement",
            "description": ("budget-matched superiority over the A0/A1 "
                            "tatonnement family"),
            "denominator": "requires A1 family cells (none exist)",
            "observed": "no A0/A1 cells in the certified population",
            "status": "not-testable",
        },
        {
            "criterion_id": "kill-1-a2-meets-bar",
            "description": ("KILL: plain CG already meets the acceptance "
                            "bar and stabilization does not deliver its "
                            "preregistered speedup"),
            "denominator": (f"A2: {len(a2_b005)} b=0.05 instances (full "
                            "acceptance population); speedup: acc-3"),
            "observed": (
                f"A2 certified {int(a2_b005['certified'].sum())}"
                f"/{len(a2_b005)} on b=0.05 (rate {a2_rate:.3f}, bar "
                f"{CERT_RATE_BAR:g}); acc-3 {'passed' if acc3_pass else 'failed'}"
                f" => kill {'ACTIVE' if kill1_active else 'inactive'}"),
            "status": "pass" if kill1_active else "fail",
        },
        {
            "criterion_id": "kill-3-zch-vs-dictator",
            "description": ("KILL: certified z_CH interval must never "
                            "contradict the dictator interval"),
            "denominator": f"all {len(cells)} method-cells",
            "observed": (f"{n_contra} contradictions; min margin "
                         f"{zd_margin_min:.6g}"),
            "status": "pass" if n_contra == 0 else "fail",
        },
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# figures (full population: distributions, not per-instance bars)
# ---------------------------------------------------------------------------
COLORS = {"a2": "#264653", "a3": "#2a9d8f", "a4": "#e9c46a", "a5": "#e76f51"}


def make_figures(cells: pd.DataFrame, out_dir: str) -> list:
    made = []
    b_vals = sorted(cells["b"].unique())

    def box_by_method(col, fname, ylabel, logy=False):
        fig, axes = plt.subplots(1, len(b_vals) + 1,
                                 figsize=(4 * (len(b_vals) + 1), 4.2),
                                 sharey=True)
        panels = [("overall", cells)] + [
            (f"b={b:g}", cells[cells.b == b]) for b in b_vals]
        for ax, (name, sub) in zip(axes, panels):
            data = [sub[sub.method == m][col].tolist() for m in METHODS]
            bp = ax.boxplot(data, tick_labels=[m.upper() for m in METHODS],
                            patch_artist=True, medianprops={"color": "black"})
            for patch, m in zip(bp["boxes"], METHODS):
                patch.set_facecolor(COLORS[m])
                patch.set_alpha(0.7)
            ax.set_title(name)
            if logy:
                ax.set_yscale("log")
        axes[0].set_ylabel(ylabel)
        fig.suptitle(f"B2 full population (64 instances x 4 methods): "
                     f"{ylabel}")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, fname), dpi=150)
        plt.close(fig)
        made.append(fname)

    box_by_method("oracle_calls", "F1_total_calls_by_method.png",
                  "total oracle calls to certificate")
    box_by_method("total_solver_wall_s", "F2_solver_wall_by_method.png",
                  "total solver wall time (s)", logy=True)
    box_by_method("broadcast_tv", "F3_broadcast_tv_by_method.png",
                  "broadcast price-path total variation", logy=True)

    # F4: clean vs total calls scatter (the decomposition finding)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for m in METHODS:
        sub = cells[cells.method == m]
        ax.scatter(sub["oracle_calls_clean"], sub["oracle_calls"],
                   s=22, alpha=0.75, label=m.upper(), color=COLORS[m])
    lim = max(float(cells["oracle_calls"].max()) * 1.05, 10)
    ax.plot([0, lim], [0, lim], ls="--", lw=0.8, color="gray")
    ax.set_xlabel("clean certification calls")
    ax.set_ylabel("total oracle calls")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.legend()
    ax.set_title("Clean vs total oracle calls (diagonal: no candidate "
                 "overhead)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "F4_clean_vs_total_calls.png"), dpi=150)
    plt.close(fig)
    made.append("F4_clean_vs_total_calls.png")
    return made


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------
def write_summary_md(path, cells, matched, summary, acceptance, two_calls,
                     stamp, code_commit):
    ov = summary[summary["scope"] == "overall"].set_index("method")
    n_inst = len(cells) // 4
    lines = [
        f"# B2 full-population analysis — {n_inst} matched instances x "
        f"A2-A5 ({stamp})",
        "",
        f"Analysis code commit: `{code_commit}`. Deterministic regeneration "
        "from the certified checkpoints (MANIFEST.json has every input and "
        "output hash).",
        "",
        "## Population",
        "",
        f"- {len(cells)} method-cells: {n_inst} instances x 4 methods "
        "(pilot 12 + 36 cells joined with the 208-cell expansion; exact "
        "union verified — no overlaps, gaps, or extras);",
        f"- certified: {int(cells['certified'].sum())}/{len(cells)}; "
        f"two-call immediate-certification cells: {len(two_calls)} (verified, "
        "reported in two_call_cells.csv, never filtered).",
        "",
        "## Method summary (overall)",
        "",
        "| method | cert | median total calls | median clean | median stab "
        "| median wall (s) | W/T/L vs A2 (total) | clean W/T/L |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in METHODS:
        r = ov.loc[m]
        wtl = (f"{int(r['wins_vs_a2'])}/{int(r['ties_vs_a2'])}/"
               f"{int(r['losses_vs_a2'])}" if m != "a2" else "—")
        cwtl = (f"{int(r['clean_wins_vs_a2'])}/{int(r['clean_ties_vs_a2'])}/"
                f"{int(r['clean_losses_vs_a2'])}" if m != "a2" else "—")
        lines.append(
            f"| {m.upper()} | {int(r['certified'])}/{int(r['cells'])} | "
            f"{r['calls_median']:g} | {r['clean_calls_median']:g} | "
            f"{r['stab_calls_median']:g} | {r['wall_median_s']:.2f} | "
            f"{wtl} | {cwtl} |")
    lines += ["", "## Preregistered criteria (computed; true denominators)",
              "", "| id | status | observed |", "|---|---|---|"]
    for _, r in acceptance.iterrows():
        lines.append(f"| {r['criterion_id']} | **{r['status']}** | "
                     f"{r['observed']} |")
    lines += [
        "",
        "## b-stratified medians",
        "",
        "| scope | method | total | clean | stab | wall (s) | cert rate |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in summary.sort_values(["scope", "method"]).iterrows():
        lines.append(
            f"| {r['scope']} | {r['method'].upper()} | {r['calls_median']:g} "
            f"| {r['clean_calls_median']:g} | {r['stab_calls_median']:g} | "
            f"{r['wall_median_s']:.2f} | {r['cert_rate']:.3f} |")
    acc = acceptance.set_index("criterion_id")
    lines += [
        "",
        "## Verdict (computed)",
        "",
        f"acc-3 (2x speedup): **{acc.loc['acc-3-stab-beats-a2-2x', 'status']}**; "
        f"acc-1 (95% certification): "
        f"**{acc.loc['acc-1-cert95-b005', 'status']}**; "
        f"kill-1: **{acc.loc['kill-1-a2-meets-bar', 'status']}** "
        "(pass = kill signal active on the full population).",
        "",
        "The scientific decision (stop stabilization and reframe vs a "
        "prespecified focused continuation) is recorded in "
        "doc/DECISION_LOG.md AFTER this artifact set is reviewed — this "
        "file reports the computed evidence, not the decision.",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def analyze(roots: dict, out_base: str, stamp: str,
            analysis_code_commit: str,
            instances=FULL_INSTANCES,
            pilot_instances=PILOT_INSTANCES_FULL,
            instance_builder=default_instance_builder,
            verify_code_commit: bool = True) -> str:
    code_verified = False
    if verify_code_commit:
        analysis_code_commit = verify_analysis_code_commit(
            analysis_code_commit)
        code_verified = True
    validate_full(roots, instances, pilot_instances, instance_builder)

    pilot_set = set(pilot_instances)
    rows = []
    for (s, n, b) in instances:
        for m in METHODS:
            d = locate_cell_dir(roots, pilot_set, m, s, n, b)
            rows.append(extract_cell_from_dir(d, m, s, n, b))
    cells = pd.DataFrame(rows)
    n_inst = len(instances)
    check_denominators(
        cells,
        expected_b005_per_method=sum(1 for i in instances if i[2] == 0.05),
        expected_matched_per_method=n_inst)
    check_scientific_contract(cells)

    two_calls = two_call_report(cells)
    matched = matched_comparison(cells)
    if len(matched) != 3 * n_inst:
        raise AnalysisError("matched join produced wrong row count")
    summary = method_summary(cells, matched)
    acceptance = acceptance_full(
        cells, summary,
        expected_b005=sum(1 for i in instances if i[2] == 0.05),
        expected_matched=n_inst)

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
    write_csv(two_calls, os.path.join(out_dir, "two_call_cells.csv"),
              ["method", "b", "n_trips", "seed"])
    figures = make_figures(cells, out_dir)
    write_summary_md(os.path.join(out_dir, "SUMMARY.md"), cells, matched,
                     summary, acceptance, two_calls, stamp,
                     analysis_code_commit)

    outputs = sorted(["cells.csv", "matched_comparison.csv",
                      "method_summary.csv", "acceptance_status.csv",
                      "two_call_cells.csv", "SUMMARY.md"] + figures)
    manifest = {
        "schema": "b2-full-population-v1",
        "stamp": stamp,
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": code_verified,
        "population": {
            "instances": [list(t) for t in instances],
            "pilot_instances": [list(t) for t in pilot_instances],
            "methods": list(METHODS),
            "method_cells": len(cells),
        },
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
        "inputs": {key: {"path": roots[key],
                         "files": tree_hashes(roots[key])}
                   for key in sorted(roots)},
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
    ap.add_argument("--expansion-root", default="runs/b2_expansion")
    ap.add_argument("--out", default=os.path.join("..", "result", "b2_full"))
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--analysis-code-commit", required=True)
    args = ap.parse_args()
    stamp = args.stamp or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    roots = {"a2_pilot": args.a2_root, "a345_pilot": args.a345_root,
             "expansion": args.expansion_root}
    out_dir = analyze(roots, args.out, stamp, args.analysis_code_commit)
    print(f"[done] wrote {out_dir}")


if __name__ == "__main__":
    main()
