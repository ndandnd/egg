"""Physical decode of day-tariff edge logits with the v7 pipeline.

For each requested bank group: v7 repair (`decode_path_cover`, cost_learned cover,
5 s, energy relaxation, charging caps, shared charging) -> fixed-route charging LP
(v7 budget: GRB, 45 s phase, 55 s wall) -> independent full-case replay -> exact
curved `day` bill. Failures are recorded per group, never replaced.

Usage: python -m experiments.claude_decode --logits FILE --label NAME \
           --group 10064 [--group ...] --output FILE
`--logits` is a JSON map {group_id: {"movement_ids": [...], "logits": [...]}} (E4
day_logits.json) or the claude_score_v8 format keyed "bank:<id>".
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import time
import traceback

from egglab import native_hull as nh
from egglab import native_recharge as nr
from egglab import physical_learning_cases as bank
from egglab import route_fixed_repair as repair

CHARGE = dict(backend="GRB", threads=1, phase_seconds=45., wall_seconds=55., max_rounds=1, epsilon=1e-4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logits", type=Path, action="append", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--group", type=int, action="append", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    table = {}
    for path in args.logits:
        for key, value in json.loads(path.read_text()).items():
            table[str(key).removeprefix("bank:")] = value
    rows = []
    for gid in args.group:
        case = bank.make_case(gid); market = bank.market(case, "day")
        row = {"label": args.label, "group_id": gid}
        started = time.monotonic()
        try:
            entry = table[str(gid)]
            if entry["movement_ids"] != [m.id for m in case.movements]:
                raise ValueError("Logit movement order differs from case")
            t0 = time.monotonic()
            cover = repair.decode_path_cover(case, entry["logits"], time_limit_seconds=5.,
                cover_policy="cost_learned", energy_relaxation=True, charging_caps=True, shared_charging=True)
            row["repair_seconds"] = time.monotonic()-t0
            selected = cover["selected_movements"]
            t1 = time.monotonic()
            plan, _, stats = repair._solve_fixed_charge(case, market, selected, nr.Budget(**CHARGE))
            row["charge_seconds"] = time.monotonic()-t1
            replay = nr.replay_native(case, plan)
            bill = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            row.update(status="replayed", bill=float(bill), bill_exact=str(bill),
                       vehicles=len(plan["vehicles"]), cheap_kwh=sum(replay["load"][10:14]),
                       grid_kwh=sum(replay["load"]))
        except Exception as exc:
            row.update(status="failed", failure={"type": type(exc).__name__, "message": str(exc)[:500],
                       "traceback": traceback.format_exc()[-1500:]})
        row["wall_seconds"] = time.monotonic()-started
        rows.append(row)
        print(json.dumps({k: row.get(k) for k in ("group_id", "status", "bill", "vehicles", "cheap_kwh")}), flush=True)
    args.output.write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
