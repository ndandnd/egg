#!/usr/bin/env python3
"""Completion audit + SUMMARY.md generator for a runs directory.

Usage: python experiments/audit_runs.py runs/phase1 [-o SUMMARY.md]

Scans checkpoints and records; reports: cell completion, replay-validation
status, loop-outcome tables by (b, alpha), adaptive-approximation gap stats,
Phase-2 switch classification tables, and solver statistics. Everything the
committed CSV cannot show at a glance.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    out_path = args.out or os.path.join(args.runs_dir, "SUMMARY.md")

    lines = [f"# Run summary: `{args.runs_dir}`", ""]

    recs = []
    for fp in sorted(glob.glob(os.path.join(args.runs_dir, "**", "*.jsonl"), recursive=True)):
        recs.extend(load_jsonl(fp))
    lines.append(f"Total records: **{len(recs)}**")
    lines.append(f"- backends: {dict(Counter((r.get('solver') or {}).get('backend') for r in recs))}")
    lines.append(f"- statuses: {dict(Counter((r.get('solver') or {}).get('status') for r in recs))}")
    lines.append(f"- git commits: {dict(Counter(r.get('git_commit') for r in recs))}")
    replay = Counter(r.get("replay_ok") for r in recs)
    lines.append(f"- replay_ok: {dict(replay)}")
    bad = [r for r in recs if r.get("replay_ok") is False]
    if bad:
        lines.append(f"- **REPLAY FAILURES: {len(bad)}** (cells: "
                     f"{sorted(set((r.get('extra') or {}).get('tag') for r in bad))})")
    lines.append("")

    # adaptive approximation quality
    ad = [
        ((r.get("solver") or {}).get("extra") or {})
        for r in recs
        if ((r.get("solver") or {}).get("extra") or {}).get("adaptive_rounds")
    ]
    if ad:
        gaps = [a["adaptive_gap_abs"] for a in ad]
        lines.append("## Adaptive convex approximation (strategic/dictator)")
        lines.append(f"- solves: {len(ad)}; converged: {sum(1 for a in ad if a.get('adaptive_converged'))}")
        lines.append(f"- gap abs: max {max(gaps):.4g}, median {statistics.median(gaps):.4g}")
        lines.append(f"- rounds: max {max(a['adaptive_rounds'] for a in ad)}, "
                     f"median {statistics.median(a['adaptive_rounds'] for a in ad)}")
        lines.append("")

    # loop outcomes by (b, alpha)
    loop_cks = sorted(glob.glob(os.path.join(args.runs_dir, "**", "loop.ckpt.json"), recursive=True))
    if loop_cks:
        table = defaultdict(Counter)
        incomplete = []
        for f in loop_cks:
            ck = json.load(open(f))
            cell = os.path.basename(os.path.dirname(f))
            parts = cell.split("_")
            b = next((p[1:] for p in parts if p.startswith("b") and p != "b"), "?")
            a = next((p[1:] for p in reversed(parts) if p.startswith("a")), "?")
            if not ck.get("done"):
                incomplete.append(cell)
                continue
            table[(b, a)][ck["outcome"]["type"]] += 1
        lines.append("## Phase-1 loop outcomes (price-state detection) by (b, alpha)")
        lines.append("")
        lines.append("| b | alpha | fixed_point | cycle | max_iters |")
        lines.append("|---|---|---|---|---|")
        for (b, a) in sorted(table):
            c = table[(b, a)]
            lines.append(f"| {b} | {a} | {c.get('fixed_point',0)} | {c.get('cycle',0)} | {c.get('max_iters',0)} |")
        if incomplete:
            lines.append(f"\n**INCOMPLETE loop cells: {incomplete}**")
        lines.append("")

    # phase-2 sweeps
    sweep_cks = sorted(glob.glob(os.path.join(args.runs_dir, "**", "sweep.ckpt.json"), recursive=True))
    if sweep_cks:
        kinds = Counter()
        econ, ties, cells_with_econ, incomplete = 0, 0, 0, []
        jumps = []
        for f in sweep_cks:
            ck = json.load(open(f))
            if not ck.get("done"):
                incomplete.append(os.path.basename(os.path.dirname(f)))
                continue
            has_econ = False
            for s in ck.get("switches", []):
                kinds[s.get("kind", "unclassified")] += 1
                if s.get("tie_margin"):
                    ties += 1
                elif s.get("kind") in ("charging_only", "duty_change", "fleet_change"):
                    econ += 1
                    has_econ = True
                    jumps.append(s.get("load_l1", 0.0))
            cells_with_econ += 1 if has_econ else 0
        lines.append("## Phase-2 switch classification")
        lines.append(f"- cells: {len(sweep_cks)} ({len(incomplete)} incomplete)")
        lines.append(f"- switches by kind: {dict(kinds)}")
        lines.append(f"- economic switches: {econ} in {cells_with_econ} cells; margin-tied: {ties}")
        if jumps:
            lines.append(f"- load jumps (L1 kWh): median {statistics.median(jumps):.1f}, max {max(jumps):.1f}")
        if incomplete:
            lines.append(f"- **INCOMPLETE sweep cells: {incomplete}**")
        lines.append("")

    # solver stats
    walls = [((r.get("solver") or {}).get("wall_s") or 0.0) for r in recs]
    lpgaps = [((r.get("solver") or {}).get("lp_mip_gap_abs")) for r in recs]
    lpgaps = [g for g in lpgaps if g is not None]
    if walls:
        lines.append("## Solver statistics")
        lines.append(f"- MIP wall time (s): median {statistics.median(walls):.2f}, max {max(walls):.2f}")
        if lpgaps:
            lines.append(f"- LP-vs-MIP absolute gap: median {statistics.median(lpgaps):.3f}, max {max(lpgaps):.3f}")
        lines.append("")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out_path}")
    if bad:
        sys.exit(f"AUDIT FAILED: {len(bad)} replay failures")


if __name__ == "__main__":
    main()
