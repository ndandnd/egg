"""Independently replay two saved 2017 shared-budget candidates.

Only compact saved plans and frozen development inputs are read. No optimizer,
native solve, refit, cluster action, or reserved test case is used.
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
ATTEMPT = ROOT / "result/learning_repair/20260930-shared-budget-attempt1"
OUTPUT = Path(__file__).resolve().parent / "INDEPENDENT_REPLAY_SHARED_BUDGET.json"
CASE = "learning_s2017_n28"
POLICIES = ("cost_only", "cost_learned")
TOL = 1e-6


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def check_cover_witness(case, cover):
    compiled = nr.compile_case(case)
    caps, rows, keys = repair._shared_charging_rows(case, compiled)
    assert len(caps) == cover["shared_charge_variable_count"]
    selected = set(cover["selected_movements"])
    positive, charge = cover["shared_charge_witness"], {}
    unselected = []
    for entry in positive:
        key = (entry["movement"], entry["interval"])
        assert key not in charge and entry["grid_kwh"] > 0
        interval = compiled["intervals"][entry["interval"]]
        assert (entry["start_min"], entry["end_min"]) == (
            interval["start"], interval["end"])
        charge[key] = entry["grid_kwh"]
        if entry["movement"] not in selected:
            unselected.append(entry)
    assert set(charge).issubset(set(keys))
    witness = ([float(mode.id in selected) for mode in case.movements]
               + [cover["soc_after_trip_witness_kwh"][trip.id]
                  for trip in case.trips]
               + [charge.get(key, 0.0) for key in keys])
    assert all(math.isfinite(value) for value in witness)
    max_violation = max((max(0.0, value-cap) for value,cap in
                         zip(witness[-len(caps):], caps)), default=0.0)
    for coefficients, lower, upper in rows:
        lhs = math.fsum(value*witness[index]
                        for index,value in coefficients.items())
        if math.isfinite(lower):
            max_violation = max(max_violation, lower-lhs)
        if math.isfinite(upper):
            max_violation = max(max_violation, lhs-upper)
    max_unselected = max((entry["grid_kwh"] for entry in unselected), default=0.0)
    assert max_violation <= TOL and max_unselected <= TOL
    return {"checked": True, "positive_grid_entries": len(positive),
            "charge_variable_count": len(caps),
            "max_row_or_bound_violation_kwh": max_violation,
            "unselected_positive_entries": unselected,
            "max_unselected_grid_kwh": max_unselected,
            "tolerance_kwh": TOL,
            "meaning": "Saved cover MILP charge/SOC witness satisfies assembled shared rows within tolerance; tiny positive energy on an unselected movement is numerical dust, and the native LP reoptimizes charging."}


def verify():
    frozen = json.loads(STAGE2.read_text())
    group = frozen["design"]["groups"][CASE]
    case = lp.case_from_dict(group["case"])
    market = nh.Market(**group["markets"]["target"])
    assert case.identity() == group["case_identity"]
    assert market.identity() == group["market_identities"]["target"]
    cells = []
    for policy in POLICIES:
        folder = ATTEMPT / CASE / "state0" / policy
        repair_path = folder / "repair.json"
        result_path = folder / "result.json"
        replay_path = folder / "independent_replay.json"
        proposal = json.loads(repair_path.read_text())["result"]
        result = json.loads(result_path.read_text())
        saved = json.loads(replay_path.read_text())
        assert proposal["repair_status"] == "replayed"
        assert proposal["case_identity"] == case.identity()
        assert proposal["market_identity"] == market.identity()
        assert all(proposal[flag] is True for flag in
                   ("energy_relaxation", "charging_caps", "shared_charging"))
        cover = proposal["cover"]
        assert cover["status"] == 1  # bounded 30-second cover incumbent
        assert cover["shared_charging"] is True
        pf.recover_paths(case, cover["selected_movements"])
        plan = proposal["plan"]
        actual = {mid for vehicle in plan["vehicles"]
                  for mid in vehicle["movements"]}
        assert actual == set(cover["selected_movements"])
        charge_check = check_cover_witness(case, cover)
        replay = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        assert replay["replay_ok"] is True and replay == proposal["replay"]
        exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
        plan_hash = nr.digest(plan)
        assert plan_hash == result["candidate_plan_hash"] == saved["plan_hash"]
        assert str(exact) == proposal["true_cost_exact"]
        assert str(exact) == result["candidate_objective_exact"] == saved["objective_exact"]
        assert replay == saved["replay"]
        cells.append({"case": CASE, "policy": policy,
            "candidate_kind": "repaired", "repair_status": "replayed",
            "cover_status": cover["status"], "cover_mip_gap": cover["mip_gap"],
            "cover_pullout_count": cover["pullout_count"],
            "cover_wall_seconds": cover["wall_seconds"],
            "repair_json": rel(repair_path), "repair_sha256": sha(repair_path),
            "result_json": rel(result_path), "result_sha256": sha(result_path),
            "saved_replay_json": rel(replay_path), "saved_replay_sha256": sha(replay_path),
            "case_identity": case.identity(), "market_identity": market.identity(),
            "plan_hash": plan_hash, "replay_ok": True,
            "replay_matches_saved": True,
            "exact_target_cost": str(exact), "target_cost": float(exact),
            "cost_matches_saved": True, "ops_cost": replay["ops_cost"],
            "grid_load_kwh": replay["load"],
            "shared_cover_witness": charge_check})
    return {"schema": "egg-independent-shared-budget-replay-v1",
        "frozen_json": rel(STAGE2), "frozen_sha256": sha(STAGE2),
        "attempt_frozen_json": rel(ATTEMPT / "frozen.json"),
        "attempt_frozen_sha256": sha(ATTEMPT / "frozen.json"),
        "method": "Fresh native physical replay, checked pricing start, exact Fraction target cost, plan hash and saved receipt comparison; positive cover grid/SOC witness checked against assembled shared rows without optimization.",
        "scope": "Two 2017 development candidates only. Both 30-second cover solves stopped with feasible incumbents and open MIP gaps; neither proves minimum physical fleet count or optimality.",
        "cells": cells}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved JSON")
    args = parser.parse_args()
    report = verify()
    content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        assert OUTPUT.read_text() == content, "Saved independent replay changed"
    else:
        OUTPUT.write_text(content)
    print("Verified two saved 2017 plans and shared charging witnesses")


if __name__ == "__main__":
    main()
