"""E4 step 1: tariff-diverse cold labels for the TRAIN bank.

For one TRAIN timetable, solve the cold curved planner (same budget as the v7 cold
planner: GRB, 1 thread, 55 s phase, 70 s wall, 4 tangent rounds) under six
deterministic training tariffs plus the bank `day` tariff (evaluation only). Training
tariffs never put two or more cheap hours inside 10:00-14:00, so `day` stays a
held-out price pattern. Each solve appends one JSON line; failures are recorded.

Usage: python -m experiments.claude_e4_labels --group-id 10000 --output DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as bank

TRAIN_TARIFFS = 6
DAY_HOURS = set(range(10, 14))
BUDGET = dict(backend="GRB", threads=1, phase_seconds=55.0, wall_seconds=70.0,
              max_rounds=4, epsilon=1e-4)


def _draw(group_id, k, field, count):
    raw = hashlib.sha256(f"claude-e4-tariff-v1|{group_id}|{k}|{field}".encode()).digest()
    return int.from_bytes(raw[:8], "big") % count


def training_tariff(group_id, k):
    """k=0 flat; k>=1 one cheap window; never >= 2 cheap hours inside 10:00-14:00."""
    if k == 0:
        level = (0.15, 0.20, 0.25, 0.30)[_draw(group_id, k, "flat", 4)]
        return {"kind": "flat", "a": [level]*30}
    for attempt in range(1000):
        width = 3 + _draw(group_id, k, f"w{attempt}", 3)
        start = 6 + _draw(group_id, k, f"s{attempt}", 30 - 6 - width + 1)
        hours = set(range(start, start+width))
        if len(hours & DAY_HOURS) < 2:
            break
    else:
        raise RuntimeError("No admissible training window")
    cheap = (0.05, 0.10, 0.15)[_draw(group_id, k, "cheap", 3)]
    base = (0.25, 0.30, 0.35)[_draw(group_id, k, "base", 3)]
    return {"kind": "window", "start_hour": start, "width": width, "cheap": cheap,
            "base": base, "a": [cheap if h in hours else base for h in range(30)]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--group-id", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.group_id not in bank.TRAIN_IDS:
        raise ValueError("E4 labels are TRAIN-only")
    args.output.mkdir(parents=True, exist_ok=False)
    case = bank.make_case(args.group_id)
    tariffs = [(f"train{k}", training_tariff(args.group_id, k)) for k in range(TRAIN_TARIFFS)]
    day = bank.market(case, "day")
    tariffs.append(("day_eval", {"kind": "bank_day", "a": list(day.a)}))
    out = args.output / "labels.jsonl"
    for name, tariff in tariffs:
        market = nh.Market(f"{case.name}-claude-e4-{name}", tuple(tariff["a"]), (1/900,)*30)
        row = {"group_id": args.group_id, "case_identity": case.identity(), "tariff_name": name,
               "tariff": tariff, "market_identity": market.identity(), "budget": BUDGET,
               "role": "evaluation_only" if name == "day_eval" else "training"}
        started = time.monotonic()
        try:
            result = pf.solve_planner(case, market.a, market.b, nr.Budget(**BUDGET))
            row.update(status=result.get("status"), lower=result.get("lower"),
                       upper=result.get("upper"), gap=result.get("gap"), plan=result.get("plan"))
            if result.get("plan"):
                replay = nr.replay_native(case, result["plan"])
                row["objective_exact"] = str(replay["ops_cost"] + nh.supply(market, replay["load"]))
                row["vehicles"] = len(result["plan"]["vehicles"])
        except Exception as exc:
            row["failure"] = {"type": type(exc).__name__, "message": str(exc),
                              "traceback": traceback.format_exc()[-3000:]}
        row["wall_seconds"] = time.monotonic() - started
        with out.open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True, default=str) + "\n")
        print(json.dumps({k: row.get(k) for k in ("tariff_name", "status", "upper", "gap",
                          "vehicles", "wall_seconds")}, default=str), flush=True)


if __name__ == "__main__":
    main()
