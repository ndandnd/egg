"""E2: cold time-to-quality profile of the complete-fleet pricing MIP.

One cold Gurobi solve (1 thread) of V(p) = min c(x) + p.e(x) at the tariff's linear
prices, on a scaled development case or a TRAIN bank case. Records model size, build
time, the incumbent/bound progress log over time, the final status, and an
independent replay of the final incumbent. This is the same oracle that hull pricing
and own-price response call repeatedly.

Usage: python -m experiments.claude_e2_profile --source scale --base-id 50000 \
           --services 40 --tariff day --seconds 600 --output DIR
       python -m experiments.claude_e2_profile --source bank --base-id 10069 ...
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time
import traceback

from egglab import claude_scale_cases as scale
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as bank


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=("scale", "bank"), required=True)
    p.add_argument("--base-id", type=int, required=True)
    p.add_argument("--services", type=int)
    p.add_argument("--tariff", default="day")
    p.add_argument("--seconds", type=float, default=600.0)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    case = (scale.make_case(args.base_id, args.services) if args.source == "scale"
            else bank.make_case(args.base_id))
    market = bank.market(case, args.tariff)
    prices = list(market.a)
    row = {"source": args.source, "base_id": args.base_id, "services": len(case.trips),
           "case_name": case.name, "case_identity": case.identity(), "tariff": args.tariff,
           "market_identity": market.identity(), "seconds_cap": args.seconds,
           "movements": len(case.movements),
           "depot_movements": sum(m.kind == "depot" for m in case.movements),
           "connector_kw": case.resources[0].grid_kw, "started_unix": time.time()}
    try:
        t0 = time.monotonic()
        built = pf.build_feasible_model(case, "GRB")
        pf.attach_objective(built, "linear", prices)
        row["build_seconds"] = time.monotonic() - t0
        model = built["model"]
        row.update(n_vars=model.num_cols, n_int=model.num_int, n_constraints=model.num_rows)
        model.threads = 1
        model.max_mip_gap = 1e-9
        model.store_search_progress_log = True
        t1 = time.monotonic()
        status = model.optimize(max_seconds=args.seconds).name
        row["solve_seconds"] = time.monotonic() - t1
        row["status"] = status
        row["incumbent"] = float(model.objective_value) if model.num_solutions else None
        bound = model.objective_bound
        row["bound"] = float(bound) if bound is not None and math.isfinite(float(bound)) else None
        log = getattr(model.search_progress_log, "log", None) or []
        row["progress"] = [[float(t), [float(lb) if math.isfinite(lb) else None,
                                       float(ub) if math.isfinite(ub) else None]]
                           for t, (lb, ub) in log]
        if model.num_solutions:
            plan = pf._extract(case, built)
            replay = nr.replay_native(case, plan, prices)
            row["replay"] = {"status": "replayed", "vehicles": len(plan["vehicles"]),
                             "pricing_objective": replay["pricing_objective"],
                             "ops_cost": replay["ops_cost"], "load": replay["load"]}
            row["plan"] = plan
    except Exception as exc:
        row["failure"] = {"type": type(exc).__name__, "message": str(exc),
                          "traceback": traceback.format_exc()[-4000:]}
    row["finished_unix"] = time.time()
    (args.output / "e2.json").write_text(json.dumps(row, indent=1, sort_keys=True, default=str))
    print(json.dumps({k: row.get(k) for k in ("case_name", "movements", "n_int", "status",
                      "incumbent", "bound", "solve_seconds", "failure")}, default=str))


if __name__ == "__main__":
    main()
