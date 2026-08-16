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
import math
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


def _cg_sane(ck: dict, tol_mono: float = 2e-3) -> list:
    """Full sanity battery for a B2-A2 CG checkpoint; returns problem
    strings. 'Complete and sane' (this passing) is distinct from
    'certified' (outcome.certified) — budget exhaustion is a valid completed
    scientific outcome, but every bound and record must still be coherent."""
    def fin(x):
        return isinstance(x, (int, float)) and math.isfinite(x)

    errs = []
    if not ck.get("done"):
        errs.append("not done")
        return errs
    oc = ck.get("outcome") or {}
    if oc.get("type") not in ("certified", "budget_exhausted"):
        errs.append(f"bad outcome {oc.get('type')}")
        return errs
    ub = ck.get("ub_history") or []
    lb = ck.get("lb_history") or []
    # finite histories with matching lengths
    if len(ub) != len(lb):
        errs.append(f"history length mismatch: {len(ub)} UB vs {len(lb)} LB")
    if not ub:
        errs.append("empty bound histories")
        return errs
    if not all(fin(x) for x in ub) or not all(fin(x) for x in lb):
        errs.append("nonfinite bound history entries")
        return errs
    # LB <= UB throughout: every LB is valid for z_CH and every UB is an
    # exact feasible evaluation, so the inequality holds pairwise
    for i, (l, u) in enumerate(zip(lb, ub)):
        if l > u + 1e-6:
            errs.append(f"LB {l} > UB {u} at iteration {i}")
            break
    # monotonicity within documented tolerances
    for a, b in zip(ub, ub[1:]):
        if b > a + tol_mono:
            errs.append(f"UB increased {a} -> {b}")
            break
    for a, b in zip(lb, lb[1:]):
        if b < a - 1e-9:
            errs.append(f"LB decreased {a} -> {b}")
            break
    if ck.get("lb_best", -1e18) > min(ub) + tol_mono + ck.get(
            "identity", {}).get("epsilon", ck.get("epsilon", 0)):
        errs.append("LB_best exceeds best UB")
    # outcome coherence: gap equals final UB minus LB_best; certified
    # implies gap <= epsilon; final history entry matches the outcome
    eps = ck.get("identity", {}).get("epsilon", ck.get("epsilon"))
    if not (fin(oc.get("gap")) and fin(oc.get("ub_ch")) and fin(oc.get("lb_best"))):
        errs.append("nonfinite outcome fields")
        return errs
    if abs(oc["gap"] - (oc["ub_ch"] - oc["lb_best"])) > 1e-9:
        errs.append(f"outcome gap {oc['gap']} != ub_ch - lb_best "
                    f"{oc['ub_ch'] - oc['lb_best']}")
    if abs(ub[-1] - oc["ub_ch"]) > 1e-12:
        errs.append(f"final UB history {ub[-1]} != outcome ub_ch {oc['ub_ch']}")
    if abs(ck.get("lb_best", float("nan")) - oc["lb_best"]) > 1e-12:
        errs.append("state lb_best != outcome lb_best")
    if oc.get("certified") and eps is not None and oc["gap"] > eps + 1e-12:
        errs.append(f"certified but gap {oc['gap']} > epsilon {eps}")
    # committed oracle events: count agreement, unique ids, OPTIMAL + replay
    events = ck.get("oracle_events")
    if events is None:
        errs.append("checkpoint has no committed oracle events")
        return errs
    ids = [((e.get("extra") or {}).get("call_id")) for e in events]
    if len(events) != ck.get("oracle_calls"):
        errs.append(f"oracle_calls {ck.get('oracle_calls')} != "
                    f"{len(events)} committed oracle events")
    if len(set(ids)) != len(ids) or None in ids:
        errs.append("duplicate or missing oracle call_ids")
    for e in events:
        st = (e.get("solver") or {}).get("status")
        if st != "OPTIMAL":
            errs.append(f"oracle event {((e.get('extra') or {}).get('call_id'))} "
                        f"status {st} != OPTIMAL")
            break
    if any(e.get("replay_ok") is not True for e in events):
        errs.append("oracle event without replay_ok=true")
    # iteration events reference committed pricing solves
    id_set = set(ids)
    for it in ck.get("iteration_events") or []:
        if it.get("pricing_solve_id") not in id_set:
            errs.append(f"iteration {it.get('iteration_id')} references "
                        f"unknown pricing solve {it.get('pricing_solve_id')}")
            break
    return errs


def audit(
    runs_dir: str,
    out_path: str | None = None,
    expect_cells: int | None = None,
    expect_loops: int | None = None,
    expect_sweeps: int | None = None,
    expect_static: int | None = None,
    expect_cg: int | None = None,
):
    """Build the summary; returns (lines, ok, problems).

    Expected-count gates (Codex review, PR #12): completeness of the
    checkpoints that exist is not enough — an entirely absent cell must fail
    the audit. Callers state how many cell/loop/sweep checkpoints the grid
    should contain (from the launcher manifest or the driver's --list count);
    `expect_static` additionally requires that many completed static regimes
    per cell checkpoint (phase-1 full mode: 4; loop-only roots: omit)."""
    out_path = out_path or os.path.join(runs_dir, "SUMMARY.md")
    problems = []
    lines = [f"# Run summary: `{runs_dir}`", ""]

    sidecars = load_sidecars(runs_dir)
    recs = []
    cg_iter_recs = []
    raw_fail_shas = []
    for rel, i, raw in iter_record_lines(runs_dir):
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            problems.append(f"unparsable record {rel}:{i}")
            continue
        if rec.get("record_kind") == "cg-iteration":
            # CG iteration summaries reference their pricing solve by id
            # (the full record lives in the oracle log) and carry every
            # actual master solve in master_solves; counting their solver
            # blocks at the top level would double-count the pricing solve.
            cg_iter_recs.append(rec)
            for ms in rec.get("master_solves") or []:
                if ms.get("status") != "OPTIMAL":
                    problems.append(
                        f"cg master solve {ms.get('solve_id')} in {rel}:{i} "
                        f"has status {ms.get('status')} != OPTIMAL")
            if not rec.get("master_solves"):
                problems.append(f"cg iteration {rel}:{i} has no master solves")
            continue
        recs.append(rec)
        if rec.get("replay_ok") is False:
            raw_fail_shas.append(record_sha256(raw))

    lines.append(f"Total records: **{len(recs)}**"
                 + (f" (+{len(cg_iter_recs)} cg-iteration summaries, "
                    "master solves audit-checked, pricing referenced by id)"
                    if cg_iter_recs else ""))
    lines.append(f"- backends: {dict(Counter((r.get('solver') or {}).get('backend') for r in recs))}")
    statuses = Counter((r.get("solver") or {}).get("status") for r in recs)
    lines.append(f"- statuses: {dict(statuses)}")
    lines.append(f"- git commits: {dict(Counter(r.get('git_commit') for r in recs))}")
    lines.append(f"- replay_ok (raw stored): {dict(Counter(r.get('replay_ok') for r in recs))}")
    # Contract: every oracle record has status exactly "OPTIMAL". A missing
    # solver/status field is a violation, not a pass (Codex review, PR #12).
    missing_status = statuses.get(None, 0)
    non_optimal = sum(v for k, v in statuses.items() if k != "OPTIMAL")
    if missing_status:
        lines.append(f"- **records with MISSING solver status: {missing_status}**")
    if non_optimal:
        problems.append(
            f"{non_optimal} records without OPTIMAL solver status "
            f"(of which {missing_status} missing entirely)"
        )
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
    nonaccepted_kinds = Counter(
        sc.get("disposition") for sc in sidecars.values()
        if sc.get("disposition") not in ACCEPTED_DISPOSITIONS
    )
    lines.append("## Replay status (raw is never hidden)")
    lines.append(f"- raw legacy replay failures: {len(raw_fail_shas)}")
    lines.append(f"- successfully revalidated: {resolved}")
    lines.append(f"- unresolved replay failures: {unresolved}")
    lines.append(
        f"- revalidation sidecars present: {len(sidecars)} "
        f"(nonaccepted: {len(failed_sidecars)} — only certified_equivalent "
        f"resolves; alternative realizations are diagnostic and NOT accepted)"
    )
    if nonaccepted_kinds:
        lines.append(f"- nonaccepted dispositions: {dict(nonaccepted_kinds)}")
    if unresolved:
        problems.append(f"{unresolved} unresolved replay failures")
    if failed_sidecars:
        problems.append(
            f"{len(failed_sidecars)} nonaccepted revalidations "
            f"({dict(nonaccepted_kinds)}): {[s[:12] for s in failed_sidecars]}"
        )
    lines.append("")

    # --- checkpoint completeness with expected-count gates -------------------
    cell_cks = sorted(glob.glob(os.path.join(runs_dir, "**", "cell.ckpt.json"), recursive=True))
    loop_cks_all = sorted(glob.glob(os.path.join(runs_dir, "**", "loop.ckpt.json"), recursive=True))
    sweep_cks_all = sorted(glob.glob(os.path.join(runs_dir, "**", "sweep.ckpt.json"), recursive=True))
    cg_cks_all = sorted(glob.glob(os.path.join(runs_dir, "**", "*.cg.ckpt.json"), recursive=True))

    def _cell_complete(ck):
        if not ck.get("loop_done"):
            return False
        if expect_static is not None and len(ck.get("static_done") or []) < expect_static:
            return False
        return True

    completeness = []
    for label, paths, expected, is_complete in (
        ("cell", cell_cks, expect_cells, _cell_complete),
        ("loop", loop_cks_all, expect_loops, lambda ck: bool(ck.get("done"))),
        ("sweep", sweep_cks_all, expect_sweeps,
         lambda ck: bool(ck.get("done")) and bool(ck.get("margins_done"))),
        ("cg", cg_cks_all, expect_cg, lambda ck: not _cg_sane(ck)),
    ):
        found = len(paths)
        complete = 0
        incomplete_names = []
        for f in paths:
            try:
                ck = json.load(open(f))
            except (json.JSONDecodeError, OSError):
                incomplete_names.append(os.path.basename(os.path.dirname(f)))
                continue
            if is_complete(ck):
                complete += 1
            else:
                incomplete_names.append(os.path.basename(os.path.dirname(f)))
        missing = (expected - complete) if expected is not None else None
        completeness.append((label, expected, found, complete, missing, incomplete_names))
        if expected is not None:
            if found > expected:
                problems.append(f"{label}: found {found} checkpoints but expected {expected} (grid mismatch)")
            if complete != expected:
                problems.append(
                    f"{label}: {complete}/{expected} complete checkpoints "
                    f"(missing or incomplete: {expected - complete})"
                )
        elif incomplete_names:
            problems.append(f"{label}: {len(incomplete_names)} incomplete checkpoints")

    lines.append("## Checkpoint completeness (expected-count gates)")
    lines.append("")
    lines.append("| type | expected | found | complete | missing |")
    lines.append("|---|---|---|---|---|")
    for label, expected, found, complete, missing, _names in completeness:
        exp_s = expected if expected is not None else "(not gated)"
        mis_s = missing if missing is not None else "-"
        lines.append(f"| {label} | {exp_s} | {found} | {complete} | {mis_s} |")
    for label, _e, _f, _c, _m, names in completeness:
        if names:
            lines.append(f"- incomplete {label} checkpoints: {names}")
    if expect_static is not None:
        lines.append(f"- static-regime requirement per cell: >= {expect_static}")
    lines.append("")

    # --- B2-A2 CG certification details -------------------------------------
    if cg_cks_all:
        certified, exhausted, sane_n, gaps, calls = 0, 0, 0, [], []
        for f in cg_cks_all:
            ck = json.load(open(f))
            oc = ck.get("outcome") or {}
            if oc.get("certified"):
                certified += 1
            if oc.get("type") == "budget_exhausted":
                exhausted += 1
            if oc.get("gap") is not None:
                gaps.append(oc["gap"])
            calls.append(ck.get("oracle_calls"))
            sane = _cg_sane(ck)
            if sane:
                problems.append(f"cg {os.path.dirname(f)}: {sane}")
            else:
                sane_n += 1
        lines.append("## B2-A2 certification")
        lines.append(
            f"- cells: {len(cg_cks_all)}; complete and sane: {sane_n}; "
            f"CERTIFIED (gap <= epsilon): {certified}; "
            f"budget-exhausted (valid completed outcome, distinct from "
            f"certified): {exhausted}")
        if gaps:
            lines.append(f"- final gaps: max {max(gaps):.4g}, "
                         f"median {statistics.median(gaps):.4g}")
        lines.append(f"- oracle calls: {calls}")
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
    loop_cks = loop_cks_all
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
            # already gated in the completeness section; informational here
            lines.append(f"\n**INCOMPLETE loop cells: {incomplete}**")
        lines.append("")

    # --- sweeps ---------------------------------------------------------------
    sweep_cks = sweep_cks_all
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
            # already gated in the completeness section; informational here
            lines.append(f"- **INCOMPLETE sweep cells: {incomplete}**")
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
        lines.append("**PASS** — expected checkpoints all present and "
                     "complete; no unresolved replay failures; no nonaccepted "
                     "revalidations; every solve OPTIMAL and certified.")
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
    ap.add_argument("--expect-cells", dest="expect_cells", type=int, default=None,
                    help="required number of complete cell.ckpt.json files")
    ap.add_argument("--expect-loops", dest="expect_loops", type=int, default=None,
                    help="required number of complete loop.ckpt.json files")
    ap.add_argument("--expect-sweeps", dest="expect_sweeps", type=int, default=None,
                    help="required number of complete (done+margins_done) sweep.ckpt.json files")
    ap.add_argument("--expect-static", dest="expect_static", type=int, default=None,
                    help="required completed static regimes per cell checkpoint (phase-1 full mode: 4)")
    ap.add_argument("--expect-cg", dest="expect_cg", type=int, default=None,
                    help="required number of complete, bound-sane *.cg.ckpt.json files (B2-A2)")
    args = ap.parse_args()
    out_path = args.out or os.path.join(args.runs_dir, "SUMMARY.md")
    _, ok, problems = audit(
        args.runs_dir,
        out_path,
        expect_cells=args.expect_cells,
        expect_loops=args.expect_loops,
        expect_sweeps=args.expect_sweeps,
        expect_static=args.expect_static,
        expect_cg=args.expect_cg,
    )
    print(f"wrote {out_path}")
    if not ok:
        sys.exit("AUDIT FAILED: " + "; ".join(problems))


if __name__ == "__main__":
    main()
