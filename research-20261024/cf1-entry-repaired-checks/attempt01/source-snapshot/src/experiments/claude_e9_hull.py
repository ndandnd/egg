"""E9: do learned-pruned plans make complete-fleet hull certification feasible at scale?

For one case and the `day` tariff: (1) cold hull (no seed columns); (2) hull seeded with
the replayed physical plans of earlier E3/E6 runs (passed as e3.json paths); (3) own-
price response at the cheapest seed plan's marginal prices. Hull budget and harness as
E0 except a 600 s wall. The D upper bound is the cheapest replayed plan among the
seeds; the D lower bound is the best full-case planner lower bound among the given
cold-arm e3.json files (a pruned run's solver bound is NOT valid for the full case and
is never used). Failures are recorded, never retried.

Usage: python -m experiments.claude_e9_hull --case scale:50000:40 \
           --seed-run PATH ... --cold-run PATH ... --output DIR
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import time

from egglab import claude_cases
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as bank
from egglab import physical_route_decoder_v1 as decoder
from egglab import route_fixed_repair as repair
from experiments.claude_e0_support import RESPONSE_BUDGET, hull_bounds, stage

CHARGE = dict(backend="GRB", threads=1, phase_seconds=110., wall_seconds=120., max_rounds=1, epsilon=1e-4)
HULL = dict(backend="GRB", threads=1, phase_seconds=500.0, wall_seconds=600.0, pricing_calls=32,
            master_calls=64, pool_cap=48, epsilon=1e-4, pool_tolerance=1e-6, polish_steps=256,
            rational_bits=8192, polish_seconds=30.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--seed-run", type=Path, action="append", default=[])
    ap.add_argument("--cold-run", type=Path, action="append", default=[])
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    case = claude_cases.make(args.case)
    market = bank.market(case, "day")
    seeds, seed_meta = [], []
    for path in args.seed_run:
        r = json.loads(path.read_text())
        if r.get("case_identity") != case.identity():
            raise ValueError("Seed run is for a different case")
        if r.get("bill") is None:
            seed_meta.append({"path": str(path), "usable": False}); continue
        meta = {"path": str(path), "bill": r["bill"], "arm": r["arm"], "keep": r.get("keep"),
                "seconds": r.get("seconds")}
        if "plan" in r:
            plan = r["plan"]; meta["plan_source"] = "saved"
        else:  # E3 rows keep routes, not charges: re-optimize charging on the same routes
            t0 = time.monotonic()
            plan, _, _ = repair._solve_fixed_charge(case, market, r["movements"], nr.Budget(**CHARGE))
            meta.update(plan_source="fixed_route_charging_lp", charge_seconds=time.monotonic()-t0)
        replay = nr.replay_native(case, plan)
        meta["rebuilt_bill"] = float(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
        meta["usable"] = True
        seed_meta.append(meta); seeds.append(plan)
    lowers = []
    for path in args.cold_run:
        r = json.loads(path.read_text())
        if r.get("case_identity") == case.identity() and r.get("arm") in ("cold", "cold4") \
                and r.get("solver_lower_on_target") is not None:
            lowers.append(float(r["solver_lower_on_target"]))
    rec = {"case": args.case, "case_identity": case.identity(), "market_identity": market.identity(),
           "hull_budget": HULL, "seeds": seed_meta, "full_case_planner_lowers": lowers}
    budget = nh.Budget(**HULL)
    lineage = {"policy": "claude-e9-hull-20261001", "case": args.case}
    stage("cold_hull", lambda: decoder.verify_global(case, market, None, lineage, budget), rec)
    if seeds:
        stage("seeded_hull", lambda: decoder.verify_global(case, market, seeds,
              {**lineage, "seed_plan_hashes": [nr.digest(s) for s in seeds]}, budget), rec)
    best = None
    for plan in seeds:
        replay = nr.replay_native(case, plan)
        bill = float(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
        if best is None or bill < best[0]:
            best = (bill, plan, replay)
    if best is not None:
        load = best[2]["load"]
        prices = [float(a + b*e) for a, b, e in zip(market.a, market.b, load)]
        rec["own_prices"] = prices
        stage("response", lambda: pf.solve_pricing(case, prices, nr.Budget(**RESPONSE_BUDGET)), rec)
    hulls = [hull_bounds(rec[k]) for k in ("cold_hull", "seeded_hull") if k in rec]
    lo_ch = max([h[0] for h in hulls if h[0] is not None], default=None)
    up_d = best[0] if best else None
    up_ch = min([h[1] for h in hulls if h[1] is not None] + ([up_d] if up_d is not None else []), default=None)
    lo_d = max(lowers + ([lo_ch] if lo_ch is not None else []), default=None)
    summary = {"D": [lo_d, up_d], "CH": [lo_ch, up_ch],
               "hull_status": {k: hull_bounds(rec[k])[2] for k in ("cold_hull", "seeded_hull") if k in rec},
               "hull_bounds": {k: hull_bounds(rec[k])[:2] for k in ("cold_hull", "seeded_hull") if k in rec}}
    if None not in (lo_d, up_d, lo_ch, up_ch):
        summary["gap"] = [max(0.0, lo_d-up_ch), up_d-lo_ch]
    if best is not None and rec.get("response", {}).get("status") == "completed":
        r = rec["response"]["result"]
        private = float(best[2]["ops_cost"]) + sum(p*e for p, e in zip(rec["own_prices"], best[2]["load"]))
        if r.get("lower") is not None:
            summary["regret_of_best_seed"] = [private - r["upper"], private - r["lower"]]
    rec["summary"] = summary
    (args.output / "e9.json").write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps({"case": args.case, **summary}, default=str))


if __name__ == "__main__":
    main()
