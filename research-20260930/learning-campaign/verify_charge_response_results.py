"""Independently replay the saved charge-response development campaign.

This verifies saved plans, training labels, prospective proposal hashes, and
paired outcomes. It does not refit a model or run any optimization.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from egglab import charge_response_model as crm  # noqa: E402
from egglab import learned_proposals as lp  # noqa: E402
from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402


ATTEMPT = ROOT / "result/learning_campaign/20260930-charge-response-attempt1"
OUTPUT = Path(__file__).resolve().parent / "INDEPENDENT_REPLAY_CHARGE_RESPONSE.json"
SEEDS = tuple(range(2022, 2032))
TRAIN = tuple(range(2022, 2028))
DEV = tuple(range(2028, 2032))
SOURCES = ("source0", "source1")
METHODS = ("cheapest_direct", "nearest_price", "frozen_edge_prior",
           "charge_response_ridge")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def cost(replay, market):
    return Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])


def replay(case, plan):
    physical = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    assert physical["replay_ok"] is True
    return physical


def movements(plan):
    return {mid for bus in plan["vehicles"] for mid in bus["movements"]}


def verify():
    frozen_path = ATTEMPT / "frozen.json"
    catalog_path = ATTEMPT / "catalog.jsonl"
    frozen = read(frozen_path)
    design = frozen["design"]
    assert design["declared_cells"] == 44
    assert design["train_groups"] == 6 and design["dev_groups"] == 4
    assert set(SEEDS).isdisjoint(design["reserved_unmaterialized"])
    lines = catalog_path.read_bytes().splitlines(keepends=True)
    rows = [json.loads(line) for line in lines]
    assert len(rows) == 44
    name_by_seed = {seed: next(name for name in design["groups"]
                               if name.startswith(f"learning_s{seed}_")) for seed in SEEDS}
    expected_order = (
        [name_by_seed[seed] + "/" + source
         for seed in SEEDS for source in SOURCES]
        + [name_by_seed[seed] + "/" + source + "_charge"
           for seed in TRAIN for source in SOURCES]
        + [name_by_seed[seed] + "/" + source + "_charge"
           for seed in DEV for source in SOURCES]
        + [name_by_seed[seed] + "/cold"
           for seed in DEV])
    assert [row["row_id"] for row in rows] == expected_order
    catalog = {row["row_id"]: row for row in rows}
    assert len(catalog) == 44

    inference_path = ATTEMPT / "inference_receipt.json"
    launch = read(ATTEMPT / "inference_launch.json")
    inference = read(inference_path)
    prefix_hash = hashlib.sha256(b"".join(lines[:32])).hexdigest()
    assert inference["returncode"] == 0 and inference["before_all_dev_target_cells"] is True
    assert inference["inputs"]["catalog_sha256"] == launch["inputs"]["catalog_sha256"] == prefix_hash
    old_model_path = ROOT / "result/learning_campaign/20260930-stage2-attempt1/learned/model.json"
    assert inference["inputs"]["old_model_sha256"] == sha(old_model_path)
    assert {row["split"] for row in rows[:32]} == {"train", "dev"}
    assert all(row["arm"] == "source" or (row["split"] == "train" and row["arm"].endswith("_charge"))
               for row in rows[:32])
    assert all(row["split"] == "dev" and row["arm"] != "source" for row in rows[32:])
    baseline_path = ATTEMPT / "baseline_choices.json"
    assert inference["inputs"]["baseline_choices_sha256"] == sha(baseline_path)
    coverage_path = ATTEMPT / "training_coverage.json"
    assert inference["training_coverage_sha256"] == sha(coverage_path)
    coverage = read(coverage_path)
    assert coverage["complete_six_pairs"] is True and not coverage["missing_rows"]
    learned = ATTEMPT / "learned"
    for filename in ("model.json", "training_rows.json", "proposals.json", "timing.json"):
        assert inference["output_hashes"][filename] == sha(learned / filename)
    model_raw = read(learned / "model.json")
    model = crm.ResponseModel.from_dict(model_raw)
    training_rows = read(learned / "training_rows.json")
    proposals = read(learned / "proposals.json")
    baseline = read(baseline_path)
    assert len(training_rows) == 12
    assert set(model.training_groups) == {f"learning_s{seed}" for seed in TRAIN}
    assert set(model.training_rows) == set(coverage["expected_rows"])
    assert set(proposals) == set(baseline) == {f"learning_s{seed}_n{20 if seed in (2028,2030) else 28}" for seed in DEV}
    feature_matrix = np.asarray([sample["features"] for sample in training_rows])
    expected_mean = feature_matrix.mean(axis=0)
    expected_scale = feature_matrix.std(axis=0)
    expected_mean[0], expected_scale[0] = 0.0, 1.0
    expected_scale[expected_scale < 1e-8] = 1.0
    assert np.allclose(model.mean, expected_mean, rtol=0, atol=1e-12)
    assert np.allclose(model.scale, expected_scale, rtol=0, atol=1e-12)

    cells, cases, training_pairs = [], {}, []
    for seed in SEEDS:
        name = name_by_seed[seed]
        group = design["groups"][name]
        case = lp.case_from_dict(group["case"])
        assert case.identity() == group["case_identity"]
        split = "train" if seed in TRAIN else "dev"
        assert group["split"] == split
        market = {kind: nh.Market(**group["markets"][kind])
                  for kind in (*SOURCES, "target")}
        assert all(market[k].identity() == group["market_identities"][k] for k in market)
        case_cells = {}
        for stage in (*SOURCES, *(source + "_charge" for source in SOURCES),
                      *(("cold",) if seed in DEV else ())):
            row = catalog[name + "/" + stage]
            label = row["label"]
            market_name = stage if stage in SOURCES else "target"
            assert row["split"] == split and row["case_identity"] == case.identity()
            assert row["market_identity"] == market[market_name].identity()
            dest = ATTEMPT / name / "state0" / stage
            receipt = read(dest / "receipt.json")
            assert label["receipt"] == receipt
            assert receipt["returncode"] == 0 and not receipt["hard_timeout"]
            assert label["feasible"] is True and label["status"] == "returned"
            plan = label["plan"]
            physical = replay(case, plan)
            exact = cost(physical, market[market_name])
            assert nr.digest(plan) == label["plan_hash"]
            assert physical["ops_cost"] == label["ops_cost"]
            assert physical["load"] == label["load"]
            assert Fraction(label["objective_exact"]) == exact
            assert Fraction(label["upper_exact"]) == exact
            native = label.get("native_status")
            if stage in SOURCES or stage == "cold":
                raw = read(dest / "raw_result.json")["result"]
                assert raw["physical_identity"] == case.identity()
                assert raw["market_identity"] == market[market_name].identity()
                assert any(column["plan"] == plan for column in raw["columns"])
                if label.get("lower_exact") is not None:
                    assert label["bounds_replay"]["global_certificate_replayed"] is True
                    assert Fraction(label["lower_exact"]) <= exact
            else:
                source = stage.removesuffix("_charge")
                source_row = catalog[name + "/" + source]
                source_plan = source_row["label"]["plan"]
                assert movements(plan) == movements(source_plan)
                assert len(plan["vehicles"]) == len(source_plan["vehicles"])
                fixed = read(dest / "fixed_charge.json")
                direct = read(dest / "direct_rescore.json")
                result = read(dest / "result.json")
                assert fixed["status"] == result["status"] == "replayed"
                assert fixed["case_identity"] == case.identity()
                assert fixed["market_identity"] == market["target"].identity()
                assert fixed["source_plan_hash"] == source_row["label"]["plan_hash"]
                assert set(fixed["selected_movements"]) == movements(plan)
                assert fixed["plan"] == plan and fixed["replay"] == physical
                assert fixed["plan_hash"] == label["plan_hash"]
                assert Fraction(fixed["objective_exact"]) == exact
                assert direct["source_plan_hash"] == source_row["label"]["plan_hash"]
                source_physical = replay(case, source_plan)
                direct_exact = cost(source_physical, market["target"])
                assert Fraction(direct["objective_exact"]) == direct_exact
                assert Fraction(result["direct_exact"]) == direct_exact
                assert Fraction(result["post_lp_exact"]) == exact
                assert native == fixed["native_stats"]["status"] == "OPTIMAL"
            cell = {"row_id": row["row_id"], "split": split, "stage": stage,
                    "market": market_name, "plan_hash": label["plan_hash"],
                    "bus_count": len(plan["vehicles"]), "native_status": native,
                    "optimality": label["optimality"], "cost_exact": str(exact),
                    "cost": float(exact), "lower_exact": label.get("lower_exact"),
                    "receipt_sha256": sha(dest / "receipt.json")}
            cells.append(cell)
            case_cells[stage] = {"cell": cell, "physical": physical, "plan": plan}
        if seed in TRAIN:
            pair = []
            for source in SOURCES:
                sample_id = name + "/" + source + "_charge"
                sample = next(item for item in training_rows if item["row_id"] == sample_id)
                direct = cost(case_cells[source]["physical"], market["target"])
                charged = Fraction(case_cells[source + "_charge"]["cell"]["cost_exact"])
                features = crm.features(case, market["target"], market[source],
                                        case_cells[source]["physical"], source)
                assert sample["group"] == f"learning_s{seed}" and sample["split"] == "train"
                assert np.allclose(sample["features"], features, rtol=0, atol=1e-12)
                assert math.isclose(sample["residual_per_trip"],
                                    float((charged-direct)/len(case.trips)), rel_tol=0, abs_tol=1e-12)
                assert sample["label_plan_hash"] == case_cells[source + "_charge"]["cell"]["plan_hash"]
                assert sample["source_plan_hash"] == case_cells[source]["cell"]["plan_hash"]
                pair.append((source, charged))
            winner = min(pair, key=lambda item: (item[1], SOURCES.index(item[0])))[0]
            training_pairs.append({"case": name, "source0_cost_exact": str(pair[0][1]),
                                   "source1_cost_exact": str(pair[1][1]), "winner": winner})
        else:
            proposal = proposals[name]
            base_choice = baseline[name]
            assert proposal["case_identity"] == base_choice["case_identity"] == case.identity()
            assert proposal["market_identity"] == base_choice["market_identity"] == market["target"].identity()
            assert set(proposal["choices"]) == set(METHODS)
            assert {key: proposal["choices"][key] for key in METHODS if key != "charge_response_ridge"} == \
                   base_choice["choices"]
            assert len(proposal["candidates"]) == 2
            for candidate in proposal["candidates"]:
                source = candidate["source"]
                assert source in SOURCES
                source_plan = case_cells[source]["plan"]
                source_physical = case_cells[source]["physical"]
                assert candidate["row_id"] == name + "/" + source
                assert candidate["plan_hash"] == nr.digest(source_plan)
                assert Fraction(candidate["direct_exact"]) == cost(source_physical, market["target"])
                expected_features = crm.features(case, market["target"], market[source],
                                                 source_physical, source)
                assert np.allclose(candidate["features"], expected_features, rtol=0, atol=1e-12)
                expected_prediction = model.predict_cost(case, market["target"], market[source],
                                                         source_physical, source)
                assert math.isclose(candidate["predicted_post_lp_cost"], expected_prediction,
                                    rel_tol=0, abs_tol=1e-9)
            ridge_choice = min(proposal["candidates"], key=lambda c: (
                c["predicted_post_lp_cost"], SOURCES.index(c["source"])))
            assert proposal["choices"]["charge_response_ridge"] == ridge_choice["source"]
            charged_costs = {source: Fraction(case_cells[source + "_charge"]["cell"]["cost_exact"])
                             for source in SOURCES}
            best_source = min(SOURCES, key=lambda s: (charged_costs[s], SOURCES.index(s)))
            best_cost = charged_costs[best_source]
            cold_cost = Fraction(case_cells["cold"]["cell"]["cost_exact"])
            chosen = {}
            for method in METHODS:
                source = proposal["choices"][method]
                assert source in SOURCES
                chosen[method] = {"source": source, "cost_exact": str(charged_costs[source]),
                                  "cost": float(charged_costs[source]),
                                  "paired_excess_exact": str(charged_costs[source]-best_cost),
                                  "paired_excess": float(charged_costs[source]-best_cost),
                                  "cold_gap_exact": str(charged_costs[source]-cold_cost),
                                  "cold_gap": float(charged_costs[source]-cold_cost)}
            physical_pool = []
            for stage in (*SOURCES, *(source + "_charge" for source in SOURCES), "cold"):
                physical = case_cells[stage]["physical"]
                true_cost = cost(physical, market["target"])
                physical_pool.append({"stage": stage,
                    "plan_hash": case_cells[stage]["cell"]["plan_hash"],
                    "bus_count": case_cells[stage]["cell"]["bus_count"],
                    "ops_cost": physical["ops_cost"], "load_kwh": physical["load"],
                    "true_target_cost_exact": str(true_cost),
                    "true_target_cost": float(true_cost)})
            best_physical = min(physical_pool, key=lambda item: (
                Fraction(item["true_target_cost_exact"]), item["stage"]))
            gradient = [Fraction(a) + Fraction(b)*Fraction(load)
                        for a, b, load in zip(market["target"].a, market["target"].b,
                                              best_physical["load_kwh"])]
            for candidate in physical_pool:
                bill = sum((p*Fraction(load) for p, load in
                            zip(gradient, candidate["load_kwh"])), Fraction(0))
                candidate["own_price_energy_bill_exact"] = str(bill)
                candidate["own_price_linearized_cost_exact"] = str(Fraction(candidate["ops_cost"])+bill)
            response = min(physical_pool, key=lambda item: (
                Fraction(item["own_price_linearized_cost_exact"]), item["stage"]))
            regret = (Fraction(best_physical["own_price_linearized_cost_exact"])-
                      Fraction(response["own_price_linearized_cost_exact"]))
            assert regret >= 0
            cold_lower = (Fraction(case_cells["cold"]["cell"]["lower_exact"])
                          if case_cells["cold"]["cell"]["lower_exact"] is not None else None)
            if cold_lower is not None:
                assert all(cold_lower <= Fraction(item["true_target_cost_exact"])
                           for item in physical_pool)
            own_price = {"pool_stages": [item["stage"] for item in physical_pool],
                "pool_count": len(physical_pool),
                "best_physical_plan": best_physical,
                "best_response_at_incumbent_own_price": response,
                "own_load_gradient_prices_exact": [str(p) for p in gradient],
                "witnessed_regret_lower_bound_exact": str(regret),
                "witnessed_regret_lower_bound": float(regret),
                "best_compatible_cold_lower_exact": str(cold_lower) if cold_lower is not None else None,
                "best_physical_minus_cold_lower_exact": (
                    str(Fraction(best_physical["true_target_cost_exact"])-cold_lower)
                    if cold_lower is not None else None),
                "best_physical_minus_cold_lower": (
                    float(Fraction(best_physical["true_target_cost_exact"])-cold_lower)
                    if cold_lower is not None else None),
                "scope": "Five already replayed physical plans (two direct source, two fixed-charge, one cold). Positive regret lower-bounds oracle regret at this saved incumbent only; no claim about support of the unknown physical optimum."}
            cases[name] = {"seed": seed, "source0_cost_exact": str(charged_costs["source0"]),
                           "source1_cost_exact": str(charged_costs["source1"]),
                           "paired_winner": best_source, "best_two_lp_cost_exact": str(best_cost),
                           "cold_cost_exact": str(cold_cost), "cold_lower_exact": case_cells["cold"]["cell"]["lower_exact"],
                           "choices": chosen,
                           "finite_pool_own_price_review": own_price,
                           "proposal_predictions": {c["source"]: c["predicted_post_lp_cost"]
                                                    for c in proposal["candidates"]}}
    summary = read(ATTEMPT / "summary.json")
    assert summary["declared_cells"] == summary["accounted_cells"] == 44
    assert summary["inference_receipt"] == inference
    assert summary["test_groups_unobserved"] is True
    for name, case in cases.items():
        saved = summary["cases"][name]
        assert saved["prospective_choices"] == {m: case["choices"][m]["source"] for m in METHODS}
        assert Fraction(saved["paid_two_lp_best"]["objective_exact"]) == \
               Fraction(case["best_two_lp_cost_exact"])
        assert saved["paid_two_lp_best"]["source"] == case["paired_winner"]
        assert Fraction(saved["cold"]["objective_exact"]) == Fraction(case["cold_cost_exact"])
    assert len(cells) == 44 and len(training_pairs) == 6 and len(cases) == 4
    assert len({c["row_id"] for c in cells}) == 44
    train_counts = Counter(pair["winner"] for pair in training_pairs)
    assert train_counts["source1"] == 4 and train_counts["source0"] == 2
    majority = max(SOURCES, key=lambda source: (train_counts[source], -SOURCES.index(source)))
    dev_wins = Counter(case["paired_winner"] for case in cases.values())
    assert dev_wins["source1"] == 3 and dev_wins["source0"] == 1
    assert all(case["choices"]["charge_response_ridge"]["source"] == "source1"
               for case in cases.values())
    posthoc = {}
    for label, source in (("always_source1", "source1"), ("training_majority", majority)):
        posthoc[label] = {"source": source,
            "same_as_ridge_in_all_four": all(case["choices"]["charge_response_ridge"]["source"] == source
                                          for case in cases.values()),
            "mean_paired_excess": sum(float(Fraction(case["source1_cost_exact"] if source == "source1"
                                           else case["source0_cost_exact"]) -
                                             Fraction(case["best_two_lp_cost_exact"]))
                                      for case in cases.values())/len(cases),
            "scope": "Post hoc diagnostic only; this constant policy was not frozen prospectively as a campaign arm."}
    aggregates = {}
    for method in METHODS:
        selected = [case["choices"][method] for case in cases.values()]
        aggregates[method] = {"source1_selections": sum(item["source"] == "source1" for item in selected),
            "mean_paired_excess": sum(item["paired_excess"] for item in selected)/4,
            "mean_cold_gap": sum(item["cold_gap"] for item in selected)/4,
            "paired_wins": sum(item["paired_excess"] == 0 for item in selected)}
    return {"schema": "egg-independent-charge-response-replay-v1",
            "attempt_frozen_json": rel(frozen_path), "attempt_frozen_sha256": sha(frozen_path),
            "catalog_jsonl": rel(catalog_path), "catalog_sha256": sha(catalog_path),
            "inference": {"returncode": inference["returncode"],
                          "elapsed_seconds": inference["elapsed_seconds"],
                          "before_all_dev_target_cells": inference["before_all_dev_target_cells"],
                          "source_train_catalog_prefix_sha256": prefix_hash,
                          "baseline_choices_sha256": sha(baseline_path),
                          "training_coverage_sha256": sha(coverage_path),
                          "model_sha256": sha(learned / "model.json"),
                          "training_rows_sha256": sha(learned / "training_rows.json"),
                          "proposals_sha256": sha(learned / "proposals.json"),
                          "training_groups": list(model.training_groups),
                          "training_row_count": len(training_rows),
                          "training_only_normalization_checked": True,
                          "all_four_dev_proposals_frozen": sorted(proposals)},
            "training_pairs": training_pairs, "training_winner_counts": dict(train_counts),
            "development_winner_counts": dict(dev_wins),
            "development_cases": cases, "prospective_method_aggregates": aggregates,
            "posthoc_constant_policy_diagnostics": posthoc,
            "cells": cells,
            "method": "Fresh native physical replay, checked pricing starts, exact Fraction curved-market costs and movement sets for all saved plans; source/train catalog-prefix and output hashes, training-only feature normalization, and all four saved dev predictions checked without fitting or solving.",
            "scope": "Forty-four saved development/train cells only. Native OPTIMAL on charging means fixed-route linear-tariff LP optimum, not curved-target or route/global optimum. Four development groups are exploratory; constant source1 comparisons are post hoc, and reserved groups were not materialized."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify()
    content = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.check:
        assert OUTPUT.read_text() == content
    else:
        OUTPUT.write_text(content)
    print("Verified 44 saved labels, six training pairs, and four prospective development choices")


if __name__ == "__main__":
    main()
