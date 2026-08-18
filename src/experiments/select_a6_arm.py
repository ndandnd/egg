#!/usr/bin/env python3
"""One-shot A6 arm selection from the burned pilot
(doc/A6_SPARSE_STABILIZATION_SPEC.md Sections 6-7).

Deterministically produces result/a6_pilot/<stamp>/SELECTION.json from the
transferred pilot runs. Prespecified rule (frozen): select a6_a3 for the
holdout iff it beats a6_a4 on the total-call SCORE on at least
WIN_THRESHOLD = 9 of the 12 matched pilot instances, ties counted as
non-wins; otherwise select a6_a4.

Scoring (spec Section 6): a certified cell scores its calls-to-
certificate; a VALID budget-exhausted cell scores 241 (budget + 1); audit
or validity failures abort selection entirely (they are never scored).
The pilot's implementation gates additionally require 12/12 complete,
sane, CERTIFIED cells per arm (enforced through the audit gates below),
so budget-exhausted scoring is a defensive rule here and the primary one
for the holdout analysis.

This artifact (plus a DECISION_LOG entry) must be committed BEFORE any
holdout job is generated, submitted, or inspected.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab import checkpoint
from experiments.analyze_b2_pilot import (
    AnalysisError,
    default_instance_builder,
    scan_extras,
    tree_hashes,
    validate_cell,
    verify_analysis_code_commit,
)
from experiments.audit_runs import audit

ARMS = ("a6_a4", "a6_a3")
PILOT_INSTANCES = tuple(
    (s, n, b) for s in (0, 11, 15) for n in (8, 12) for b in (0.01, 0.05))
WIN_THRESHOLD = 9          # a6_a3 needs >= 9/12 score wins; ties non-wins
BUDGET_EXHAUSTED_SCORE = 241


def cell_score(ck: dict, label: str) -> int:
    """Spec Section 6 scoring; validity failures must have been rejected
    by the audit/validation gates before this is called."""
    oc = ck.get("outcome") or {}
    if oc.get("certified"):
        return int(oc["oracle_calls"])
    if oc.get("type") == "budget_exhausted":
        return BUDGET_EXHAUSTED_SCORE
    raise AnalysisError(f"{label}: unscorable outcome {oc.get('type')!r}")


def select(pilot_root: str, out_base: str, stamp: str,
           analysis_code_commit: str,
           instances=PILOT_INSTANCES,
           win_threshold: int = WIN_THRESHOLD,
           instance_builder=default_instance_builder,
           verify_code_commit: bool = True,
           require_certified: bool = True) -> str:
    code_verified = False
    if verify_code_commit:
        analysis_code_commit = verify_analysis_code_commit(
            analysis_code_commit)
        code_verified = True

    n_inst = len(instances)
    gates = {m: n_inst for m in ARMS}
    cert_gates = {m: n_inst for m in ARMS} if require_certified else None
    _lines, ok, problems = audit(
        pilot_root, out_path=os.devnull, expect_cg=2 * n_inst,
        expect_cg_method=gates, expect_cg_certified_method=cert_gates)
    if not ok:
        raise AnalysisError(
            f"pilot audit FAILED — selection aborted, nothing scored: "
            f"{problems}")

    seen = set()
    per_cell = []
    scores = {m: {} for m in ARMS}
    for (s, n, b) in instances:
        for m in ARMS:
            d = os.path.join(pilot_root, f"{m}_s{s}_n{n}_b{b:g}")
            ck_path = validate_cell(d, m, s, n, b, instance_builder)
            if ck_path in seen:
                raise AnalysisError(f"duplicate cell {ck_path}")
            seen.add(ck_path)
            ck = checkpoint.load(ck_path)
            label = f"{m} seed={s} n={n} b={b}"
            score = cell_score(ck, label)
            oc = ck["outcome"]
            scores[m][(s, n, b)] = score
            per_cell.append({
                "method": m, "seed": s, "n_trips": n, "b": b,
                "outcome": oc["type"], "certified": bool(oc["certified"]),
                "oracle_calls": int(oc["oracle_calls"]),
                "score": score,
            })
    scan_extras((pilot_root,), seen)

    matched = []
    wins_a3 = 0
    for key in instances:
        s4, s3 = scores["a6_a4"][key], scores["a6_a3"][key]
        a3_wins = s3 < s4  # ties are non-wins
        wins_a3 += int(a3_wins)
        matched.append({
            "seed": key[0], "n_trips": key[1], "b": key[2],
            "score_a6_a4": s4, "score_a6_a3": s3,
            "a6_a3_wins": bool(a3_wins),
        })
    selected = "a6_a3" if wins_a3 >= win_threshold else "a6_a4"

    out_dir = os.path.join(out_base, stamp)
    os.makedirs(out_dir, exist_ok=True)
    selection = {
        "schema": "a6-arm-selection-v1",
        "stamp": stamp,
        "analysis_code_commit": analysis_code_commit,
        "analysis_code_verified": code_verified,
        "pilot_root": pilot_root,
        "inputs": {"files": tree_hashes(pilot_root)},
        "rule": ("select a6_a3 iff it beats a6_a4 on the total-call score "
                 f"on >= {win_threshold}/{n_inst} matched pilot instances, "
                 "ties non-wins; otherwise a6_a4 "
                 "(doc/A6_SPARSE_STABILIZATION_SPEC.md Section 7)"),
        "win_threshold": win_threshold,
        "n_instances": n_inst,
        "scoring": {"certified": "calls-to-certificate",
                    "budget_exhausted": BUDGET_EXHAUSTED_SCORE},
        "per_cell": sorted(per_cell, key=lambda r: (
            r["method"], r["b"], r["n_trips"], r["seed"])),
        "matched": sorted(matched, key=lambda r: (
            r["b"], r["n_trips"], r["seed"])),
        "a6_a3_wins": wins_a3,
        "selected_arm": selected,
    }
    with open(os.path.join(out_dir, "SELECTION.json"), "w") as f:
        json.dump(selection, f, indent=2, sort_keys=True)
        f.write("\n")
    return out_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot-root", default="runs/a6_pilot")
    ap.add_argument("--out", default=os.path.join("..", "result", "a6_pilot"))
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--analysis-code-commit", required=True)
    args = ap.parse_args()
    stamp = args.stamp or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = select(args.pilot_root, args.out, stamp,
                     args.analysis_code_commit)
    sel = json.load(open(os.path.join(out_dir, "SELECTION.json")))
    print(f"[done] wrote {out_dir}/SELECTION.json — selected arm: "
          f"{sel['selected_arm']} (a6_a3 wins {sel['a6_a3_wins']}"
          f"/{sel['n_instances']})")


if __name__ == "__main__":
    main()
