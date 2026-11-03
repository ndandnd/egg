#!/usr/bin/env python3
"""One physical and exact-cost replay of the completed tariff-transfer catalog."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from experiments import tariff_response_campaign as campaign

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "result/learning_campaign/20260930-tariff-response-attempt1"
catalog = ATTEMPT / "catalog.jsonl"
rows = [json.loads(line) for line in catalog.read_text().splitlines()]
expected = [(campaign.case_for(seed).name + "/" + stage)
            for seed, stage in campaign.cells()]
assert [r["row_id"] for r in rows] == expected
verified = []
for row in rows:
    case_name, stage = row["row_id"].split("/")
    case = campaign.case_for(campaign.seed_for(case_name))
    market = campaign.market_for(case, stage)
    assert row["case_identity"] == case.identity()
    assert row["market_identity"] == market.identity()
    label = row["label"]
    assert label["feasible"] and label["plan"] is not None
    checked = nr.replay_native(case, label["plan"])
    pf._checked_pricing_start(case, label["plan"])
    cost = Fraction(checked["ops_cost"]) + nh.supply(market, checked["load"])
    assert nr.digest(label["plan"]) == label["plan_hash"]
    assert cost == Fraction(label["objective_exact"])
    verified.append({"row_id": row["row_id"], "plan_hash": label["plan_hash"],
                     "objective_exact": str(cost)})
result = {"verified": True, "cells": len(verified),
          "catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
          "scope": "Physical feasibility, native start replay, plan hash and exact target cost; no new optimum certificate",
          "rows": verified}
output = ROOT / "research-20260930/learning-campaign/INDEPENDENT_REPLAY_TARIFF_RESPONSE.json"
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"verified": True, "cells": len(verified)}))
