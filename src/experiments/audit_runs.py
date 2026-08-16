#!/usr/bin/env python3
"""Completion audit + SUMMARY.md generator for a runs directory.

Usage: python experiments/audit_runs.py runs/phase1 [-o SUMMARY.md]

Reports (never hiding raw counts):
- RAW stored replay failures (replay_ok=false as written in the JSONL), and
- EFFECTIVE unresolved failures after matching each failing record's exact
  SHA-256 to a successful revalidation sidecar (see egglab/revalidate.py and
  doc/MEASUREMENT_CLOSEOUT.md).

Exit code is 0 only when ALL of the following hold:
- every loop/sweep checkpoint is complete;
- every stored replay failure is absent or covered by a successful,
  exact-hash revalidation sidecar;
- no sidecar reports a failed/materially-different revalidation;
- every solver status is OPTIMAL and every adaptive certification converged.
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

from egglab.revalidate import (  # noqa: E402
    ACCEPTED_DISPOSITIONS,
    REVAL_DIR,
    iter_record_lines,
    load_sidecars,
    record_sha256,
)


def audit(runs_dir: str, out_path: str | None = None):
    """Build the summary; returns (lines, ok, problems)."""
    out_path = out_path or os.path.join(runs_dir, "SUMMARY.md")
    problems = []
    lines = [f"# Run summary: `{runs_dir}`", ""]

    sidecars = load_sidecars(runs_dir)
    recs = []
    raw_fail_shas = []
    for rel, i, raw in iter_record_lines(runs_dir):
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            problems.append(f"unparsable record {rel}:{i}")
            continue
        recs.append(rec)
        if rec.get("replay_ok") is False:
            raw_fail_shas.append(record_sha256(raw))

    lines.append(f"Total records: **{len(recs)}**")
    lines.append(f"- backends: {dict(Counter((r.get('solver') or {}).get('backend') for r in recs))}")
    statuses = Counter((r.get("solver") or {}).get("status") for r in recs)
    lines.append(f"- statuses: {dict(statuses)}")
    lines.append(f"- git commits: {dict(Counter(r.get('git_commit') for r in recs))}")
    lines.append(f"- replay_ok (raw stored): {dict(Counter(r.get('replay_ok') for r in recs))}")
    non_optimal = sum(v for k, v in statuses.items() if k not in ("OPTIMAL", None))
    if non_optimal:
        problems.append(f"{non_optimal} records with non-OPTIMAL solver status")
    lines.append("")

    # --- replay: raw vs effective (sidecar-matched) -------------------------
    resolved, unresolved = 0, 0
    for sha in raw_fail_shas:
        sc = sidecars.get(sha)
        if sc and sc.get("disposition") in ACCEPTED_DISPOSITIONS:
            resolved += 1
        else:
            unresolved += 1
    failed_sidecars = [
        sha for sha, sc in sidecars.items()
        if sc.get("disposition") not in ACCEPTED_DISPOSITIONS
    ]
    lines.append("## Replay status (raw is never hidden)")
    lines.append(f"- raw legacy replay failures: {len(raw_fail_shas)}")
    lines.append(f"- successfully revalidated: {resolved}")
    lines.append(f"- unresolved replay failures: {unresolved}")
    lines.append(f"- revalidation sidecars present: {len(sidecars)} "
                 f"(failed/materially-different: {len(failed_sidecars)})")
    if unresolved:
        problems.append(f"{unresolved} unresolved replay failures")
    if failed_sidecars:
        problems.append(
            f"{len(failed_sidecars)} failed/materially-different revalidations: "
            f"{[s[:12] for s in failed_sidecars]}"
        )
    lines.append("")

    # --- adaptive approximation quality -------------------------------------
    ad = [
        ((r.get("solver") or {}).get("extra") or {})
        for r in recs
        if ((r.get("solver") or {}).get("extra") or {}).get("adaptive_rounds")
    ]
    if ad:
        gaps = [a["adaptive_gap_abs"] for a in ad]
        unconverged = sum(1 for a in ad if not a.get("adaptive_converged"))
        lines.append("## Adaptive convex approximation (strategic/dictator)")
        lines.append(f"- solves: {len(ad)}; converged: {len(ad) - unconverged}")
        lines.append(f"- gap abs: max {max(gaps):.4g}, median {statistics.median(gaps):.4g}")
        lines.append(f"- rounds: max {max(a['adaptive_rounds'] for a in ad)}, "
                     f"median {statistics.median(a['adaptive_rounds'] for a in ad)}")
        if unconverged:
            problems.append(f"{unconverged} unconverged adaptive certifications")
        lines.append("")

    # --- loop outcomes -------------------------------------------------------
    loop_cks = sorted(glob.glob(os.path.join(runs_dir, "**", "loop.ckpt.json"), recursive=True))
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
            problems.append(f"{len(incomplete)} incomplete loop cells")
        lines.append("")

    # --- sweeps ---------------------------------------------------------------
    sweep_cks = sorted(glob.glob(os.path.join(runs_dir, "**", "sweep.ckpt.json"), recursive=True))
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
            problems.append(f"{len(incomplete)} incomplete sweep cells")
        lines.append("")

    # --- solver stats -----------------------------------------------------------
    walls = [((r.get("solver") or {}).get("wall_s") or 0.0) for r in recs]
    lpgaps = [g for g in (((r.get("solver") or {}).get("lp_mip_gap_abs")) for r in recs) if g is not None]
    if walls:
        lines.append("## Solver statistics")
        lines.append(f"- MIP wall time (s): median {statistics.median(walls):.2f}, max {max(walls):.2f}")
        if lpgaps:
            lines.append(f"- LP-vs-MIP absolute gap: median {statistics.median(lpgaps):.3f}, max {max(lpgaps):.3f}")
        lines.append("")

    ok = not problems
    lines.append("## Audit verdict")
    if ok:
        lines.append("**PASS** — checkpoints complete; no unresolved replay "
                     "failures; no failed revalidations; all solves OPTIMAL "
                     "and certified.")
    else:
        lines.append("**FAIL**:")
        for p in problems:
            lines.append(f"- {p}")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines, ok, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()
    out_path = args.out or os.path.join(args.runs_dir, "SUMMARY.md")
    _, ok, problems = audit(args.runs_dir, out_path)
    print(f"wrote {out_path}")
    if not ok:
        sys.exit("AUDIT FAILED: " + "; ".join(problems))


if __name__ == "__main__":
    main()
