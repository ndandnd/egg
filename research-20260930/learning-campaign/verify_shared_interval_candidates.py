"""Independent replay and saved shared-charge witness check for four cells.

Reads only compact frozen inputs, repair/candidate receipts and saved plans.
No optimizer, refit, native solve or reserved test case is used.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from egglab import learned_proposals as lp  # noqa: E402
from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402
from egglab import route_fixed_repair as repair  # noqa: E402


STAGE2 = ROOT / "result/learning_campaign/20260930-stage2-attempt1/frozen.json"
ATTEMPT = ROOT / "result/learning_repair/20260930-shared-interval-attempt1"
OUTPUT = Path(__file__).resolve().parent / "INDEPENDENT_REPLAY_SHARED_INTERVAL.json"
CASES = ("learning_s2016_n20", "learning_s2017_n28")
POLICIES = ("cost_only", "cost_learned")
TOL = 1e-6


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def verify_shared_witness(case, cover):
    """Check saved positive q and SOC against the decoder's actual row assembly."""
    compiled = nr.compile_case(case)
    caps, rows, keys = repair._shared_charging_rows(case, compiled)
    assert len(caps) == cover["shared_charge_variable_count"]
    selected = set(cover["selected_movements"])
    positive = cover["shared_charge_witness"]
    q = {}
    for entry in positive:
        key = (entry["movement"], entry["interval"])
        assert key not in q and entry["grid_kwh"] > 0
        assert entry["movement"] in selected
        interval = compiled["intervals"][entry["interval"]]
        assert (entry["start_min"], entry["end_min"]) == (
            interval["start"], interval["end"])
        q[key] = entry["grid_kwh"]
    assert set(q).issubset(set(keys))
    witness = ([float(mode.id in selected) for mode in case.movements]
               + [cover["soc_after_trip_witness_kwh"][trip.id] for trip in case.trips]
               + [q.get(key, 0.0) for key in keys])
    assert all(math.isfinite(value) for value in witness)
    cap_excess = max((value-cap for value,cap in zip(witness[-len(caps):],caps)),
                     default=0.0)
    max_violation = max(0.0, cap_excess)
    for coefficients, lower, upper in rows:
        lhs = math.fsum(coefficient*witness[index]
                        for index,coefficient in coefficients.items())
        if math.isfinite(lower):
            max_violation = max(max_violation, lower-lhs)
        if math.isfinite(upper):
            max_violation = max(max_violation, lhs-upper)
    assert max_violation <= TOL
    return {"checked": True, "positive_grid_entries": len(positive),
            "charge_variable_count": len(caps),
            "max_row_or_bound_violation_kwh": max_violation,
            "tolerance_kwh": TOL,
            "meaning": "Saved cover MILP charge/SOC witness satisfies its assembled shared rows; native LP later reoptimizes charges."}


def verify():
    frozen = json.loads(STAGE2.read_text())
    cells = []
    for name in CASES:
        group = frozen["design"]["groups"][name]
        case = lp.case_from_dict(group["case"])
        market = nh.Market(**group["markets"]["target"])
        assert case.identity() == group["case_identity"]
        assert market.identity() == group["market_identities"]["target"]
        for policy in POLICIES:
            folder = ATTEMPT / name / "state0" / policy
            repair_path = folder / "repair.json"
            result_path = folder / "result.json"
            replay_path = folder / "independent_replay.json"
            proposal = json.loads(repair_path.read_text())["result"]
            result = json.loads(result_path.read_text())
            saved_replay = json.loads(replay_path.read_text())
            assert proposal["case_identity"] == case.identity()
            assert proposal["market_identity"] == market.identity()
            assert proposal["energy_relaxation"] is True
            assert proposal["charging_caps"] is True
            assert proposal["shared_charging"] is True
            assert result["cover_policy"] == policy
            if proposal["repair_status"] == "replayed":
                kind = "repaired"
                plan = proposal["plan"]
                plan_source = repair_path
                cover = proposal["cover"]
                assert cover["shared_charging"] is True
                assert cover["status"] in (0, 1)
                pf.recover_paths(case, cover["selected_movements"])
                actual = {mid for vehicle in plan["vehicles"]
                          for mid in vehicle["movements"]}
                assert actual == set(cover["selected_movements"])
                shared_witness = verify_shared_witness(case, cover)
            else:
                kind = "source_fallback"
                fallback_path = folder / "fallback.json"
                plan = json.loads(fallback_path.read_text())["plan"]
                plan_source = fallback_path
                cover = proposal["cover"]
                assert proposal["failure"]["stage"] == "cover"
                assert cover["selected_movements"] is None
                shared_witness = {"checked": False,
                    "reason": "Cover solver reached time limit without an integral incumbent; saved candidate is archived fallback."}
            replay = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            assert replay["replay_ok"] is True
            exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            plan_hash = nr.digest(plan)
            assert plan_hash == result["candidate_plan_hash"] == saved_replay["plan_hash"]
            assert str(exact) == result["candidate_objective_exact"] == saved_replay["objective_exact"]
            assert replay == saved_replay["replay"]
            if kind == "repaired":
                assert replay == proposal["replay"]
                assert str(exact) == proposal["true_cost_exact"]
            cells.append({"case": name, "policy": policy, "candidate_kind": kind,
                "repair_status": proposal["repair_status"],
                "cover_status": cover["status"],
                "cover_mip_gap": cover["mip_gap"],
                "cover_pullout_count": cover.get("pullout_count"),
                "repair_json": relative(repair_path), "repair_sha256": sha(repair_path),
                "result_json": relative(result_path), "result_sha256": sha(result_path),
                "saved_replay_json": relative(replay_path), "saved_replay_sha256": sha(replay_path),
                "candidate_plan_source": relative(plan_source),
                "candidate_plan_source_sha256": sha(plan_source),
                "case_identity": case.identity(), "market_identity": market.identity(),
                "plan_hash": plan_hash, "replay_ok": True,
                "replay_matches_saved": True,
                "exact_cost": str(exact), "cost_matches_saved": True,
                "grid_load_kwh": replay["load"], "ops_cost": replay["ops_cost"],
                "shared_cover_witness": shared_witness})
    return {"schema": "egg-independent-shared-interval-replay-v1",
        "frozen_json": relative(STAGE2), "frozen_sha256": sha(STAGE2),
        "attempt_frozen_json": relative(ATTEMPT / "frozen.json"),
        "attempt_frozen_sha256": sha(ATTEMPT / "frozen.json"),
        "method": "Fresh native physical replay and checked pricing start for all saved plans; exact Fraction operations plus frozen-market supply. New covers' saved positive interval charge/SOC witnesses checked against _shared_charging_rows without optimization.",
        "scope": "Four saved development candidates only; source fallback is not a new repair, and time-limit cover incumbents are not optimality certificates.",
        "cells": cells}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare with saved JSON")
    args = parser.parse_args()
    report = verify()
    content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        assert OUTPUT.read_text() == content, "Independent replay output changed"
    else:
        OUTPUT.write_text(content)
    print("Verified four saved plans and two shared cover witnesses")


if __name__ == "__main__":
    main()
