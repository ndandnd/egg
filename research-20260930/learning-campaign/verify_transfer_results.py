"""Replay the 18 saved independent-transfer cells without running an optimizer.

Reads compact catalog/receipts and saved candidate plans. Raw native result files
are parsed only to check the selected column and certificate provenance.
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
from egglab import route_fixed_repair as route_repair  # noqa: E402


ATTEMPT = ROOT / "result/learning_campaign/20260930-transfer-attempt1"
OUTPUT = Path(__file__).resolve().parent / "INDEPENDENT_REPLAY_TRANSFER.json"
SEEDS = (2018, 2019)
STAGES = ("source0", "source1", "cold", "retained", "nearest_price",
          "cheapest_bill", "learned", "shared_cost_only", "shared_cost_learned")
REPAIRS = STAGES[-2:]
TOL = 1e-6


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def shared_witness(case, cover):
    compiled = nr.compile_case(case)
    caps, rows, keys = route_repair._shared_charging_rows(case, compiled)
    assert len(caps) == cover["shared_charge_variable_count"]
    selected = set(cover["selected_movements"])
    q = {}
    for entry in cover["shared_charge_witness"]:
        key = (entry["movement"], entry["interval"])
        assert key not in q and entry["grid_kwh"] > 0
        interval = compiled["intervals"][entry["interval"]]
        assert (entry["start_min"], entry["end_min"]) == (interval["start"], interval["end"])
        q[key] = entry["grid_kwh"]
    assert set(q).issubset(set(keys))
    vector = ([float(mode.id in selected) for mode in case.movements]
              + [cover["soc_after_trip_witness_kwh"][trip.id] for trip in case.trips]
              + [q.get(key, 0.0) for key in keys])
    assert all(math.isfinite(value) for value in vector)
    violation = max((max(0.0, value - cap) for value, cap in
                     zip(vector[-len(caps):], caps)), default=0.0)
    for coefficients, lower, upper in rows:
        lhs = math.fsum(coefficient * vector[index]
                        for index, coefficient in coefficients.items())
        if math.isfinite(lower):
            violation = max(violation, lower - lhs)
        if math.isfinite(upper):
            violation = max(violation, lhs - upper)
    assert violation <= TOL, violation
    unselected = max((value for (movement, _), value in q.items()
                      if movement not in selected), default=0.0)
    assert unselected <= TOL
    return {"checked": True, "positive_grid_entries": len(q),
            "variable_count": len(caps), "max_row_or_bound_violation_kwh": violation,
            "max_unselected_grid_kwh": unselected, "tolerance_kwh": TOL}


def physical_pool(name, group, group_rows, best_lower):
    """Reprice only saved physical columns at target; no new search."""
    case = lp.case_from_dict(group["case"])
    market = nh.Market(**group["markets"]["target"])
    distinct = {}
    inputs = []
    raw_count = 0
    for row in group_rows:
        stage = row["row_id"].rsplit("/", 1)[-1]
        dest = ATTEMPT / name / "state0" / stage
        path = dest / ("raw_hull.json" if stage in REPAIRS else "raw_result.json")
        if path.is_file():
            raw = read(path)["result"]
            assert raw["physical_identity"] == case.identity()
            inputs.append({"path": rel(path), "sha256": sha(path)})
            plans = [(str(index), column["plan"], column)
                     for index, column in enumerate(raw["columns"])]
        else:
            plans = []
        plans.append(("catalog_plan", row["label"]["plan"], None))
        for index, plan, column in plans:
            replay = nr.replay_native(case, plan)
            pf._checked_pricing_start(case, plan)
            assert replay["replay_ok"] is True
            if column is not None:
                assert column["load"] == replay["load"]
                assert column["ops_cost"] == replay["ops_cost"]
                raw_count += 1
            digest = nr.digest(plan)
            cost = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
            candidate = {"origin": row["row_id"] + "/" + index,
                         "plan_hash": digest, "bus_count": len(plan["vehicles"]),
                         "ops_cost": replay["ops_cost"], "load_kwh": replay["load"],
                         "exact_target_cost": str(cost), "target_cost": float(cost)}
            if digest in distinct:
                assert distinct[digest]["exact_target_cost"] == str(cost)
            else:
                distinct[digest] = candidate
    plans = list(distinct.values())
    best = min(plans, key=lambda item: (Fraction(item["exact_target_cost"]), item["plan_hash"]))
    prices = [Fraction(a) + Fraction(b) * Fraction(load)
              for a, b, load in zip(market.a, market.b, best["load_kwh"])]
    for candidate in plans:
        bill = sum((price * Fraction(load) for price, load in
                    zip(prices, candidate["load_kwh"])), Fraction(0))
        candidate["own_price_energy_bill_exact"] = str(bill)
        candidate["linearized_cost_exact"] = str(Fraction(candidate["ops_cost"]) + bill)
    response = min(plans, key=lambda item: (Fraction(item["linearized_cost_exact"]), item["plan_hash"]))
    regret = Fraction(best["linearized_cost_exact"]) - Fraction(response["linearized_cost_exact"])
    assert regret >= 0
    gap = Fraction(best["exact_target_cost"]) - best_lower if best_lower is not None else None
    assert gap is None or gap >= 0
    return {"raw_columns_replayed": raw_count, "unique_physical_plans": len(plans),
            "input_raw_result_files": inputs,
            "best_physical_plan": best, "best_response_at_own_gradient": response,
            "own_load_gradient_prices_exact": [str(price) for price in prices],
            "witnessed_regret_lower_bound_exact": str(regret),
            "witnessed_regret_lower_bound": float(regret),
            "best_physical_minus_saved_lower_exact": str(gap) if gap is not None else None,
            "best_physical_minus_saved_lower": float(gap) if gap is not None else None,
            "scope": "Price response searches only replayed saved physical plans. Positive regret is a lower bound at this incumbent, not a claim about the unknown physical optimum."}


def verify():
    frozen = read(ATTEMPT / "frozen.json")
    design = frozen["design"]
    assert design["declared_cells"] == 18
    assert design["no_refit"] and design["source_cells_before_inference"]
    assert design["inference_before_all_target_cells"]
    assert set(map(int, design["profile"])) == set(SEEDS)
    assert set(SEEDS).isdisjoint(design["reserved_test_seeds"])
    catalog_path = ATTEMPT / "catalog.jsonl"
    lines = catalog_path.read_bytes().splitlines(keepends=True)
    catalog = [json.loads(line) for line in lines]
    expected_order = ([f"learning_s{seed}_n{design['profile'][str(seed)]['services']}/{stage}"
                       for seed in SEEDS for stage in STAGES[:2]]
                      + [f"learning_s{seed}_n{design['profile'][str(seed)]['services']}/{stage}"
                         for seed in SEEDS for stage in STAGES[2:]])
    assert [row["row_id"] for row in catalog] == expected_order
    inference = read(ATTEMPT / "inference_receipt.json")
    launch = read(ATTEMPT / "inference_launch.json")
    source_prefix = b"".join(lines[:4])
    source_prefix_sha = hashlib.sha256(source_prefix).hexdigest()
    assert source_prefix_sha == launch["catalog_sha256"] == inference["catalog_sha256"]
    assert inference["returncode"] == 0 and inference["before_all_target_cells"] is True
    assert inference["frozen_model_sha256"] == launch["frozen_model_sha256"]
    proposal_path = ATTEMPT / "learned/proposals.jsonl"
    assert inference["output_hashes"]["proposals.jsonl"] == sha(proposal_path)
    proposals = [json.loads(line) for line in proposal_path.read_text().splitlines()]
    assert len(proposals) == 2
    assert all(row["arm"] == "source" and row["split"] == "dev" for row in catalog[:4])
    assert all(row["arm"] != "source" for row in catalog[4:])
    source_by_id = {row["row_id"]: row for row in catalog[:4]}
    for proposal in proposals:
        source = source_by_id[proposal["source_row_id"]]
        assert proposal["replay_ok"] is True
        assert proposal["case_identity"] == source["case_identity"]
        assert proposal["plan"] == source["label"]["plan"]
        assert nr.digest(proposal["plan"]) == source["label"]["plan_hash"]

    cells, same_market = [], {}
    for row in catalog:
        name, stage = row["row_id"].split("/")
        group = design["groups"][name]
        case = lp.case_from_dict(group["case"])
        market_name = stage if stage in STAGES[:2] else "target"
        market = nh.Market(**group["markets"][market_name])
        assert case.identity() == row["case_identity"] == group["case_identity"]
        assert market.identity() == row["market_identity"] == group["market_identities"][market_name]
        assert row["market_role"] == ("source" if stage in STAGES[:2] else "target")
        dest = ATTEMPT / name / "state0" / stage
        receipt = read(dest / "receipt.json")
        assert receipt == row["label"]["receipt"]
        assert receipt["returncode"] == 0 and not receipt.get("hard_timeout")
        label = row["label"]
        assert label["status"] == "returned" and label["feasible"] is True
        assert label["plan"] is not None
        plan = label["plan"]
        kind = None
        witness = None
        hull_lower = None
        hull_status = None
        if stage in REPAIRS:
            repair = read(dest / "repair.json")["result"]
            result = read(dest / "result.json")
            saved = read(dest / "independent_replay.json")
            kind = result["candidate_kind"]
            assert kind == saved["candidate_kind"] == label["candidate_kind"]
            assert kind in ("repaired", "source_fallback")
            assert all(repair[flag] is True for flag in
                       ("energy_relaxation", "charging_caps", "shared_charging"))
            assert repair["case_identity"] == case.identity()
            assert repair["market_identity"] == market.identity()
            if kind == "repaired":
                assert repair["repair_status"] == "replayed"
                assert plan == repair["plan"]
                envelope = read(dest / "import_envelope.json")
                assert envelope["physical_identity"] == case.identity()
                assert len(envelope["columns"]) == 1
                assert envelope["columns"][0]["plan"] == plan
                assert envelope["lineage"]["kind"] == "repaired"
                assert envelope["lineage"]["plan_hash"] == nr.digest(plan)
                cover = repair["cover"]
                assert cover["shared_charging"] is True
                pf.recover_paths(case, cover["selected_movements"])
                actual = {mid for vehicle in plan["vehicles"]
                          for mid in vehicle["movements"]}
                assert actual == set(cover["selected_movements"])
                witness = shared_witness(case, cover)
            else:
                fallback = read(dest / "fallback.json")
                assert plan == fallback["plan"]
                assert result["fallback_provenance"] == saved["fallback_provenance"]
                assert fallback["provenance"]["source_plan_hash"] == nr.digest(plan)
            assert saved["case_identity"] == case.identity()
            assert saved["market_identity"] == market.identity()
            assert result["candidate_plan_hash"] == saved["plan_hash"] == nr.digest(plan)
            if (dest / "raw_hull.json").is_file():
                raw_hull = read(dest / "raw_hull.json")["result"]
                assessment = result["hull_assessment"]
                assert raw_hull["physical_identity"] == case.identity()
                assert raw_hull["market_identity"] == market.identity()
                assert raw_hull["status"] == assessment["status"]
                hull_status = raw_hull["status"]
                if raw_hull.get("lower_certificate") is not None:
                    assert assessment["global_certificate_replayed"] is True
                    hull_lower = Fraction(raw_hull["lower_certificate"]["lower_exact"])
        replay = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        assert replay["replay_ok"] is True
        exact = Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])
        assert label["plan_hash"] == nr.digest(plan)
        assert Fraction(label["objective_exact"]) == exact
        assert Fraction(label["upper_exact"]) == exact
        if stage in REPAIRS:
            assert saved["replay"] == replay
            assert Fraction(saved["objective_exact"]) == exact
            assert Fraction(result["candidate_objective_exact"]) == exact
            if kind == "repaired":
                assert repair["replay"] == replay
                assert Fraction(repair["true_cost_exact"]) == exact
        else:
            raw = read(dest / "raw_result.json")["result"]
            assert raw["physical_identity"] == case.identity()
            assert raw["market_identity"] == market.identity()
            assert any(column["plan"] == plan for column in raw["columns"])
            if label.get("lower_exact") is not None:
                assert label["bounds_replay"]["global_certificate_replayed"] is True
            if label.get("native_mixture_upper_exact") is not None:
                assert label["bounds_replay"]["mixture_replayed"] is True
        lower = Fraction(label["lower_exact"]) if label.get("lower_exact") else None
        if lower is not None:
            assert lower <= exact
        if hull_lower is not None:
            assert hull_lower <= exact
        same_market.setdefault((name, market_name), {"costs": [], "lowers": []})
        same_market[(name, market_name)]["costs"].append((stage, exact))
        if lower is not None:
            same_market[(name, market_name)]["lowers"].append((stage, lower))
        if hull_lower is not None:
            same_market[(name, market_name)]["lowers"].append((stage + "/hull", hull_lower))
        cells.append({"row_id": row["row_id"], "market": market_name,
                      "candidate_kind": kind, "native_status": label.get("native_status"),
                      "optimality": label["optimality"], "plan_hash": nr.digest(plan),
                      "bus_count": len(plan["vehicles"]),
                      "exact_cost": str(exact), "cost": float(exact),
                      "lower_exact": str(lower) if lower is not None else None,
                      "repair_hull_lower_exact": str(hull_lower) if hull_lower is not None else None,
                      "repair_hull_status": hull_status,
                      "receipt_sha256": sha(dest / "receipt.json"),
                      "shared_cover_witness": witness})

    bounds = []
    for (name, market_name), pool in same_market.items():
        best_stage, best_cost = min(pool["costs"], key=lambda item: (item[1], item[0]))
        best_lower = max((value for _, value in pool["lowers"]), default=None)
        if best_lower is not None:
            assert best_lower <= best_cost
            assert all(lower <= cost for _, lower in pool["lowers"]
                       for _, cost in pool["costs"])
        bounds.append({"case": name, "market": market_name,
                       "saved_plan_count": len(pool["costs"]),
                       "best_saved_plan_stage": best_stage,
                       "best_saved_cost_exact": str(best_cost),
                       "best_replayed_lower_exact": str(best_lower) if best_lower is not None else None,
                       "best_saved_cost": float(best_cost),
                       "best_replayed_lower": float(best_lower) if best_lower is not None else None,
                       "saved_pool_gap_exact": str(best_cost - best_lower) if best_lower is not None else None})

    own_price = []
    for name, group in design["groups"].items():
        matching = [row for row in catalog if row["row_id"].startswith(name + "/")]
        target_bound = next(item for item in bounds if item["case"] == name and item["market"] == "target")
        lower = (Fraction(target_bound["best_replayed_lower_exact"])
                 if target_bound["best_replayed_lower_exact"] is not None else None)
        own_price.append({"case": name, **physical_pool(name, group, matching, lower)})

    summary = read(ATTEMPT / "summary.json")
    assert summary["declared_cells"] == summary["accounted_cells"] == len(cells) == 18
    assert summary["feasible_cells"] == 18
    assert summary["inference_receipt"] == inference
    assert summary["test_groups_unobserved"] is True
    return {"schema": "egg-independent-transfer-replay-v1",
            "attempt_frozen_json": rel(ATTEMPT / "frozen.json"),
            "attempt_frozen_sha256": sha(ATTEMPT / "frozen.json"),
            "catalog_jsonl": rel(catalog_path), "catalog_sha256": sha(catalog_path),
            "inference": {"returncode": inference["returncode"],
                          "elapsed_seconds": inference["elapsed_seconds"],
                          "before_all_target_cells": inference["before_all_target_cells"],
                          "source_only_catalog_prefix_sha256": source_prefix_sha,
                          "source_rows": [row["row_id"] for row in catalog[:4]],
                          "model_sha256": inference["frozen_model_sha256"],
                          "proposals_sha256": sha(proposal_path),
                          "proposals": [{"case_identity": p["case_identity"],
                                         "source_row_id": p["source_row_id"],
                                         "plan_hash": nr.digest(p["plan"])} for p in proposals]},
            "heldout_scope": {"observed_case_seeds": list(SEEDS),
                              "reserved_test_seeds": design["reserved_test_seeds"],
                              "summary_claim_test_groups_unobserved": summary["test_groups_unobserved"],
                              "verification_limit": "Catalog and frozen design contain only transfer case rows; this file-level review does not prove absence of all external access."},
            "method": "Reconstruct frozen physical cases and markets; replay all saved plans and pricing starts; compare exact Fraction cost/hash/receipt and native selected-column provenance; check saved repair SOC/shared-charge rows without optimization.",
            "scope": "The 18 saved development cell candidates and saved same-market certificates only. Solver statuses and global optimality are not independently recomputed.",
            "same_market_bounds": bounds, "physical_pool_own_price_review": own_price,
            "cells": cells}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify()
    content = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.check:
        assert OUTPUT.read_text() == content
    else:
        OUTPUT.write_text(content)
    print("Verified 18 saved transfer plans, four shared-charge witnesses, and source-only inference receipts")


if __name__ == "__main__":
    main()
