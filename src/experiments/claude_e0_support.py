"""E0: price-support evidence (D, CH, gap, own-price regret) for the v7 TRAIN groups.

Reruns the two v7 hull controls that failed on the ``pool_tol`` keyword typo, with
the correct ``pool_tolerance`` keyword and a sized (not v7) budget, and adds the
own-price response of the v7 cold planner incumbent. The v7 cold planner bounds
are reused, not recomputed. Every stage failure is recorded, never retried.

Usage: python -m experiments.claude_e0_support --group-id 10064 \
           --v7-comparison PATH --v7-cold-planner PATH --output DIR
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import physical_route_decoder_v1 as decoder

HULL_BUDGET = dict(backend="GRB", threads=1, phase_seconds=150.0, wall_seconds=180.0,
                   pricing_calls=16, master_calls=64, pool_cap=48, epsilon=1e-4,
                   pool_tolerance=1e-6, polish_steps=256, rational_bits=8192,
                   polish_seconds=20.0)
RESPONSE_BUDGET = dict(backend="GRB", threads=1, phase_seconds=50.0, wall_seconds=60.0,
                       max_rounds=1, epsilon=1e-4)


def _f(x):
    return None if x is None else float(Fraction(x)) if isinstance(x, str) else float(x)


def stage(name, fn, record):
    started = time.monotonic()
    try:
        row = fn()
        record[name] = {"status": "completed", "wall_seconds": time.monotonic()-started, "result": row}
    except Exception as exc:  # recorded, never retried
        record[name] = {"status": "failed", "wall_seconds": time.monotonic()-started,
                        "failure": {"type": type(exc).__name__, "message": str(exc),
                                    "traceback": traceback.format_exc()[-4000:]}}
    return record[name]


def hull_bounds(row):
    if row["status"] != "completed" or row["result"].get("status") != "checked":
        return None, None, None
    a = row["result"]["assessment"]
    b = a.get("bounds")  # [lower, upper] as exact fraction strings, or None
    if not b:
        return None, None, a.get("status")
    return _f(b[0]), _f(b[1]), a.get("status")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--group-id", type=int, required=True)
    p.add_argument("--v7-comparison", type=Path, required=True)
    p.add_argument("--v7-cold-planner", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    case = physical.make_case(args.group_id)
    market = physical.market(case, "day")
    comp = json.loads(args.v7_comparison.read_text())
    cold_planner = json.loads(args.v7_cold_planner.read_text())["data"]
    if comp["group_id"] != args.group_id or comp["case_identity"] != case.identity():
        raise ValueError("v7 comparison does not match the regenerated case")
    if comp["market_identity"] != market.identity():
        raise ValueError("v7 market identity differs")
    record = {"group_id": args.group_id, "case_identity": case.identity(),
              "market_identity": market.identity(), "hull_budget": HULL_BUDGET,
              "response_budget": RESPONSE_BUDGET, "started_unix": time.time()}
    budget = nh.Budget(**HULL_BUDGET)
    lineage = {"policy": "claude-e0-support-20261001", "group_id": args.group_id}
    stage("cold_hull", lambda: decoder.verify_global(case, market, None, lineage, budget), record)
    sources = [c["plan"] for c in comp["direct_source_controls"]["candidates"]]
    if sources:
        stage("retained_hull", lambda: decoder.verify_global(case, market, sources,
              {**lineage, "source_plan_hashes": [nr.digest(s) for s in sources]}, budget), record)
    cold = comp["cold_physical_incumbent"]
    load = cold["replay"]["load"]
    prices = [float(a + b*e) for a, b, e in zip(market.a, market.b, load)]
    record["own_prices"] = prices
    stage("response", lambda: pf.solve_pricing(case, prices, nr.Budget(**RESPONSE_BUDGET)), record)
    # Combine bounds. D interval from v7 cold planner (native, tolerance-qualified).
    lo_d, up_d = _f(cold_planner.get("lower")), _f(cold_planner.get("upper"))
    hulls = [hull_bounds(record[k]) for k in ("cold_hull", "retained_hull") if k in record]
    lo_ch = max([h[0] for h in hulls if h[0] is not None], default=None)
    up_ch = min([h[1] for h in hulls if h[1] is not None] + ([up_d] if up_d is not None else []), default=None)
    if lo_ch is not None and lo_d is not None:
        lo_d = max(lo_d, lo_ch)  # D >= CH
    summary = {"D": [lo_d, up_d], "CH": [lo_ch, up_ch],
               "hull_status": {k: hull_bounds(record[k])[2] for k in ("cold_hull", "retained_hull") if k in record}}
    if None not in (lo_d, up_d, lo_ch, up_ch):
        summary["gap"] = [max(0.0, lo_d-up_ch), up_d-lo_ch]
    resp = record["response"]
    bill = float(Fraction(cold["replay"]["ops_cost"])) + sum(p*e for p, e in zip(prices, load))
    summary["incumbent_private_bill"] = bill
    if resp["status"] == "completed" and resp["result"].get("lower") is not None:
        r = resp["result"]
        summary["regret"] = [bill - _f(r.get("upper")), bill - _f(r.get("lower"))]
        summary["response_status"] = r.get("status")
    record["summary"] = summary
    record["finished_unix"] = time.time()
    (args.output / "e0.json").write_text(json.dumps(record, indent=1, sort_keys=True, default=str))
    print(json.dumps({"group_id": args.group_id, **summary}, default=str))


if __name__ == "__main__":
    main()
