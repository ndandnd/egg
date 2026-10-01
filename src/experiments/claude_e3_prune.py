"""E3: predict-and-prune versus cold solving at equal total wall time.

Arms (all GRB, 1 thread, curved planner with tangent rounds, same total budget T):
  cold     - full case, one budget (later tangent rounds only if time remains);
  cold4    - full case, four tangent rounds of T/4 each (the v7 cold-planner shape);
  learned  - keep the top fraction of direct/depot movements by v8 logits;
  learned4 - learned pruning with the cold4 four-round budget split;
  lp       - same, ranked by the LP-relaxation x-values of the full pricing MIP at
             the tariff's linear prices (LP time is charged to the budget);
  random   - same, ranked by a seeded random permutation (pruning-only control).
Pullout/pullin movements are always kept, and every trip keeps at least
`--min-options` incoming and outgoing direct/depot candidates (highest ranked).
The pruned plan is replayed on the FULL case (independent event replay) and its
exact curved bill is recomputed. Scoring time from the score file is charged to the
learned arm. Infeasible/failed arms are recorded, never replaced by a fallback.

Usage: python -m experiments.claude_e3_prune --case bank:10069 --arm learned \
           --keep 0.3 --seconds 30 --scores FILE --output DIR
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
import random
import time
import traceback

from egglab import claude_cases
from egglab import claude_scale_cases as scale
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as bank




_native_optimize_once = pf._optimize_once


def _optimize_or_stop(built, budget, deadline):
    """Harness fix (06:20 run analysis): when a new tangent round would start with no
    time left, ``nr._optimize_once`` raises TimeoutError and ``solve_planner`` loses the
    replayed plan of earlier rounds. Report a non-solution status instead so the
    planner's own loop stops and returns its best plan. Solver math is unchanged."""
    if deadline - time.monotonic() <= 0:
        return {"status": "HARNESS_NO_TIME_LEFT", "incumbent": None, "lower_bound": None,
                "wall_s": 0.0, "seconds_cap": 0.0}
    return _native_optimize_once(built, budget, deadline)


pf._optimize_once = _optimize_or_stop


def lp_scores(case, prices, deadline):
    built = pf.build_feasible_model(case, "GRB")
    pf.attach_objective(built, "linear", prices)
    model = built["model"]
    model.threads = 1
    status = model.optimize(relax=True, max_seconds=max(1.0, deadline-time.monotonic())).name
    xs = [float(v.x) if v.x is not None else 0.0 for v in built["x"]]
    return xs, status


def prune(case, scores, keep, min_options):
    flexible = [j for j, m in enumerate(case.movements) if m.kind in ("direct", "depot")]
    order = sorted(flexible, key=lambda j: (-scores[j], j))
    kept = set(order[:max(1, int(math.ceil(keep*len(flexible))))])
    by_after, by_before = {}, {}
    for j in order:
        m = case.movements[j]
        by_after.setdefault(m.after, []).append(j)
        by_before.setdefault(m.before, []).append(j)
    for lists in (by_after, by_before):
        for js in lists.values():
            kept.update(js[:min_options])
    keep_ids = {case.movements[j].id for j in kept} | {m.id for m in case.movements
                                                      if m.kind in ("pullout", "pullin")}
    reduced = replace(case, name=case.name + f"-pruned{len(keep_ids)}",
                      movements=tuple(m for m in case.movements if m.id in keep_ids))
    nr.validate_case(reduced)
    return reduced, len(flexible), len(keep_ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--arm", choices=("cold", "cold4", "learned", "learned4", "lp", "random"), required=True)
    ap.add_argument("--tariff", default="day")
    ap.add_argument("--keep", type=float, default=0.3)
    ap.add_argument("--min-options", type=int, default=3)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--scores", type=Path)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    case = claude_cases.make(args.case)
    market = bank.market(case, args.tariff)
    row = {"case": args.case, "case_identity": case.identity(), "arm": args.arm, "tariff": args.tariff,
           "keep": args.keep, "min_options": args.min_options, "seconds": args.seconds,
           "movements_full": len(case.movements)}
    started = time.monotonic()
    charged = 0.0
    try:
        target = case
        if args.arm not in ("cold", "cold4"):
            if args.arm in ("learned", "learned4"):
                scored = json.loads(args.scores.read_text())[args.case]
                if scored["case_identity"] != case.identity() or scored["movement_ids"] != [m.id for m in case.movements]:
                    raise ValueError("Score file does not match the case")
                scores, charged = scored["logits"], float(scored["score_seconds"])
                row["v8_task"] = scored.get("v8_task")
            elif args.arm == "lp":
                scores, row["lp_status"] = lp_scores(case, list(market.a), started + args.seconds)
            else:
                rng = random.Random(args.seed)
                scores = [rng.random() for _ in case.movements]
            target, row["flexible_full"], row["movements_kept"] = prune(case, scores, args.keep, args.min_options)
        row["preparation_seconds"] = time.monotonic() - started + charged
        remaining = args.seconds - row["preparation_seconds"]
        if remaining <= 1.0:
            raise TimeoutError("No solver time left after preparation")
        if args.arm in ("cold4", "learned4"):  # v7 cold shape: four tangent rounds of equal share
            budget = nr.Budget(backend="GRB", threads=1, phase_seconds=remaining/4, wall_seconds=remaining,
                               max_rounds=4, epsilon=1e-4)
        else:
            budget = nr.Budget(backend="GRB", threads=1, phase_seconds=remaining, wall_seconds=remaining,
                               max_rounds=8, epsilon=1e-4)
        result = pf.solve_planner(target, market.a, market.b, budget)
        row.update(status=result.get("status"), solver_lower_on_target=result.get("lower"),
                   solver_upper_on_target=result.get("upper"),
                   rounds=[{k: r.get("stats", {}).get(k) for k in ("status", "incumbent", "lower_bound", "wall_s")}
                           for r in result.get("rounds", [])])
        plan = result.get("plan")
        if plan:
            plan = {**plan, "case_identity": case.identity()}
            replay = nr.replay_native(case, plan)  # FULL case, independent replay
            bill = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            row.update(bill_exact=str(bill), bill=float(bill), vehicles=len(plan["vehicles"]), plan=plan,
                       movements=sorted({m for v in plan["vehicles"] for m in v["movements"]}))
    except Exception as exc:
        row["failure"] = {"type": type(exc).__name__, "message": str(exc),
                          "traceback": traceback.format_exc()[-3000:]}
    row["total_seconds"] = time.monotonic() - started + charged
    (args.output / "e3.json").write_text(json.dumps(row, indent=1, default=str))
    print(json.dumps({k: row.get(k) for k in ("case", "arm", "seconds", "movements_kept", "status",
                      "bill", "total_seconds", "failure")}, default=str))


if __name__ == "__main__":
    main()
