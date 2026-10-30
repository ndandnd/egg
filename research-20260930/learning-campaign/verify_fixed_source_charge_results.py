"""Independently replay eight archived-source and eight fixed-route charged plans.

Reads saved development receipts and plans only. It runs no optimizer, route
search, hull solve, model fit, cluster action, or reserved-test evaluation.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from egglab import learned_proposals as lp  # noqa: E402
from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402


ATTEMPT = ROOT / "result/learning_repair/20260930-fixed-source-charge-attempt1"
OUTPUT = Path(__file__).resolve().parent / "INDEPENDENT_REPLAY_FIXED_SOURCE_CHARGE.json"
ARCHIVES = {
    2016: ROOT / "result/learning_campaign/20260930-stage2-attempt1",
    2017: ROOT / "result/learning_campaign/20260930-stage2-attempt1",
    2018: ROOT / "result/learning_campaign/20260930-transfer-attempt1",
    2019: ROOT / "result/learning_campaign/20260930-transfer-attempt1",
}
NAMES = {2016: "learning_s2016_n20", 2017: "learning_s2017_n28",
         2018: "learning_s2018_n20", 2019: "learning_s2019_n28"}
SOURCES = ("source0", "source1")
TARGET_CONTROLS = ("cold", "retained", "nearest_price", "cheapest_bill", "learned")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def exact_cost(replay, market):
    return Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])


def movements(plan):
    return {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}


def replay_plan(case, plan):
    replay = nr.replay_native(case, plan)
    pf._checked_pricing_start(case, plan)
    assert replay["replay_ok"] is True
    return replay


def archived_bounds(archive, name, market, rows):
    control_rows = {}
    lows = []
    costs = []
    for stage in TARGET_CONTROLS:
        row = next(row for row in rows if row["row_id"] == name + "/" + stage)
        assert row["market_identity"] == market.identity()
        label = row["label"]
        lower = label.get("lower_exact")
        if lower is not None:
            assert label["bounds_replay"]["global_certificate_replayed"] is True
            lows.append((stage, Fraction(lower)))
        if label.get("feasible"):
            costs.append((stage, Fraction(label["objective_exact"])))
        control_rows[stage] = {"status": label["status"],
                               "native_status": label.get("native_status"),
                               "feasible": label["feasible"],
                               "objective_exact": label.get("objective_exact"),
                               "lower_exact": lower,
                               "optimality": label["optimality"]}
    # Transfer archive includes later fresh repair hulls; these bounds are
    # same-target certified lower bounds, never a source-market transfer.
    repair_hulls = []
    for stage in ("shared_cost_only", "shared_cost_learned"):
        path = archive / name / "state0" / stage / "raw_hull.json"
        result_path = archive / name / "state0" / stage / "result.json"
        if path.is_file() and result_path.is_file():
            raw = read(path)["result"]
            assessment = read(result_path)["hull_assessment"]
            assert raw["market_identity"] == market.identity()
            if raw.get("lower_certificate") is not None:
                assert assessment["global_certificate_replayed"] is True
                lower = Fraction(raw["lower_certificate"]["lower_exact"])
                lows.append((stage + "/fresh_hull", lower))
                repair_hulls.append({"stage": stage, "path": rel(path),
                                     "sha256": sha(path), "lower_exact": str(lower),
                                     "native_status": raw["status"]})
    best_low = max(lows, key=lambda item: (item[1], item[0])) if lows else None
    best_control = min(costs, key=lambda item: (item[1], item[0])) if costs else None
    return {"controls": control_rows, "repair_hull_bounds": repair_hulls,
            "best_saved_target_lower_origin": best_low[0] if best_low else None,
            "best_saved_target_lower_exact": str(best_low[1]) if best_low else None,
            "best_saved_target_lower": float(best_low[1]) if best_low else None,
            "best_archived_target_control": best_control[0] if best_control else None,
            "best_archived_target_control_cost_exact": str(best_control[1]) if best_control else None,
            "best_archived_target_control_cost": float(best_control[1]) if best_control else None}


def verify():
    frozen = read(ATTEMPT / "frozen.json")
    summary = read(ATTEMPT / "summary.json")
    assert frozen["design"]["declared_cells"] == 8
    assert summary["declared_cells"] == summary["accounted_cells"] == 8
    assert frozen["design"]["no_route_reoptimization"] is True
    assert frozen["design"]["no_fresh_hull"] is True
    assert frozen["design"]["source_only_pre_target"] is True
    assert set(ARCHIVES).isdisjoint(frozen["design"]["test_groups_unobserved"])
    cells, cases = [], []
    for seed, archive in ARCHIVES.items():
        name = NAMES[seed]
        archive_frozen_path = archive / "frozen.json"
        archive_catalog_path = archive / "catalog.jsonl"
        group = read(archive_frozen_path)["design"]["groups"][name]
        case = lp.case_from_dict(group["case"])
        market = nh.Market(**group["markets"]["target"])
        assert case.name == name and case.identity() == group["case_identity"]
        assert market.identity() == group["market_identities"]["target"]
        rows = [json.loads(line) for line in archive_catalog_path.read_text().splitlines()]
        source_rows = {}
        for source in SOURCES:
            matched = [row for row in rows if row["row_id"] == name + "/" + source]
            assert len(matched) == 1
            row = matched[0]
            assert row["arm"] == "source" and row["split"] == "dev"
            assert row["case_identity"] == case.identity()
            assert row["market_identity"] == group["market_identities"][source]
            source_rows[source] = row
        source_index = [row["row_id"] for row in rows]
        assert max(source_index.index(name + "/" + source) for source in SOURCES) < \
               min(source_index.index(name + "/" + control) for control in TARGET_CONTROLS)
        bounds = archived_bounds(archive, name, market, rows)
        selection_path = ATTEMPT / name / "selection.json"
        selection = read(selection_path)
        assert selection == summary["selections"][name]
        assert selection["case_identity"] == case.identity()
        assert selection["market_identity"] == market.identity()
        assert selection["fresh_global_bound"] is False
        assert selection["historical_target_controls"].keys() == bounds["controls"].keys()
        per_case = []
        for source in SOURCES:
            row = source_rows[source]
            source_label = row["label"]
            assert source_label["feasible"] is True
            original = source_label["plan"]
            direct_replay = replay_plan(case, original)
            assert nr.digest(original) == source_label["plan_hash"]
            assert direct_replay["ops_cost"] == source_label["ops_cost"]
            assert direct_replay["load"] == source_label["load"]
            direct_cost = exact_cost(direct_replay, market)
            dest = ATTEMPT / name / "state0" / (source + "_charge")
            receipt_path = dest / "receipt.json"
            direct_path = dest / "direct_rescore.json"
            fixed_path = dest / "fixed_charge.json"
            result_path = dest / "result.json"
            receipt, direct, fixed, result = map(read, (receipt_path, direct_path,
                                                       fixed_path, result_path))
            assert receipt["returncode"] == 0 and not receipt.get("hard_timeout")
            assert direct["source_row_id"] == row["row_id"]
            assert direct["source_plan_hash"] == source_label["plan_hash"]
            assert direct["case_identity"] == case.identity()
            assert direct["market_identity"] == market.identity()
            assert direct["replay"] == direct_replay
            assert Fraction(direct["objective_exact"]) == direct_cost
            plan = fixed["plan"]
            charged_replay = replay_plan(case, plan)
            charged_cost = exact_cost(charged_replay, market)
            assert fixed["status"] == result["status"] == "replayed"
            assert fixed["case_identity"] == case.identity()
            assert fixed["market_identity"] == market.identity()
            assert fixed["source_plan_hash"] == source_label["plan_hash"]
            assert set(fixed["selected_movements"]) == movements(original) == movements(plan)
            assert len(plan["vehicles"]) == len(original["vehicles"])
            assert charged_replay == fixed["replay"]
            assert nr.digest(plan) == fixed["plan_hash"] == result["post_lp_plan_hash"]
            assert Fraction(fixed["objective_exact"]) == charged_cost
            assert Fraction(result["direct_objective_exact"]) == direct_cost
            assert Fraction(result["post_lp_objective_exact"]) == charged_cost
            assert result["native_status"] == fixed["native_stats"]["status"] == "OPTIMAL"
            assert result["target_optimality"] == "unknown"
            assert result["fresh_hull"] is False
            selection_row = next(item for item in selection["candidates"]
                                 if item["source"] == source)
            assert selection_row["receipt"] == receipt
            assert Fraction(selection_row["direct_objective_exact"]) == direct_cost
            assert Fraction(selection_row["post_lp_objective_exact"]) == charged_cost
            assert selection_row["post_lp_status"] == "replayed"
            lower = (Fraction(bounds["best_saved_target_lower_exact"])
                     if bounds["best_saved_target_lower_exact"] else None)
            assert lower is None or lower <= direct_cost and lower <= charged_cost
            cell = {"case": name, "source": source,
                    "source_row_id": row["row_id"],
                    "source_plan_hash": source_label["plan_hash"],
                    "source_bus_count": len(original["vehicles"]),
                    "source_native_status": source_label.get("native_status"),
                    "source_optimality": source_label["optimality"],
                    "direct_target_cost_exact": str(direct_cost),
                    "direct_target_cost": float(direct_cost),
                    "charged_plan_hash": nr.digest(plan),
                    "charged_bus_count": len(plan["vehicles"]),
                    "charged_target_cost_exact": str(charged_cost),
                    "charged_target_cost": float(charged_cost),
                    "charged_minus_direct_exact": str(charged_cost - direct_cost),
                    "charged_minus_direct": float(charged_cost - direct_cost),
                    "fixed_route_movement_count": len(movements(plan)),
                    "fixed_lp_native_status": fixed["native_stats"]["status"],
                    "child_returncode": receipt["returncode"],
                    "child_hard_timeout": receipt["hard_timeout"],
                    "child_elapsed_seconds": receipt["elapsed_seconds"],
                    "target_optimality": result["target_optimality"],
                    "receipt_sha256": sha(receipt_path),
                    "direct_rescore_sha256": sha(direct_path),
                    "fixed_charge_sha256": sha(fixed_path),
                    "result_sha256": sha(result_path)}
            cells.append(cell)
            per_case.append(cell)
        direct_best = min(per_case, key=lambda item: (Fraction(item["direct_target_cost_exact"]),
                                                       SOURCES.index(item["source"])))
        charged_best = min(per_case, key=lambda item: (Fraction(item["charged_target_cost_exact"]),
                                                        SOURCES.index(item["source"])))
        four = min(((Fraction(item[key]), item["source"], kind)
                    for item in per_case for key, kind in
                    (("direct_target_cost_exact", "direct"),
                     ("charged_target_cost_exact", "recharged"))),
                   key=lambda item: (item[0], SOURCES.index(item[1]),
                                     0 if item[2] == "direct" else 1))
        assert selection["best_direct_source"] == direct_best["source"]
        assert Fraction(selection["best_direct_objective_exact"]) == Fraction(direct_best["direct_target_cost_exact"])
        assert selection["best_recharged_source"] == charged_best["source"]
        assert Fraction(selection["best_recharged_objective_exact"]) == Fraction(charged_best["charged_target_cost_exact"])
        assert selection["best_of_four"] == {"source": four[1], "kind": four[2],
                                             "objective_exact": str(four[0])}
        for method, chosen in (("pre_target_cheapest_direct", direct_best["source"]),):
            assert selection["single_lp_methods"][method]["source"] == chosen
            chosen_cell = next(item for item in per_case if item["source"] == chosen)
            assert selection["single_lp_methods"][method]["post_lp_objective_exact"] == \
                   chosen_cell["charged_target_cost_exact"]
            assert selection["single_lp_methods"][method]["lp_paid_seconds"] == \
                   chosen_cell["child_elapsed_seconds"]
        proposal_path = archive / "learned/proposals.jsonl"
        proposals = [json.loads(line) for line in proposal_path.read_text().splitlines()]
        matched = [p for p in proposals if p["case_identity"] == case.identity()]
        assert len(matched) == 1 and matched[0]["replay_ok"] is True
        learned_source = matched[0]["source_row_id"].rsplit("/", 1)[-1]
        assert learned_source in SOURCES
        assert selection["single_lp_methods"]["frozen_learned_source"]["source"] == learned_source
        learned_cell = next(item for item in per_case if item["source"] == learned_source)
        assert selection["single_lp_methods"]["frozen_learned_source"]["post_lp_objective_exact"] == \
               learned_cell["charged_target_cost_exact"]
        assert selection["single_lp_methods"]["frozen_learned_source"]["lp_paid_seconds"] == \
               learned_cell["child_elapsed_seconds"]
        assert matched[0]["plan"] == source_rows[learned_source]["label"]["plan"]
        assert selection["single_lp_methods"]["frozen_learned_source"]["inference_seconds"] == \
               matched[0]["online_timing_seconds"]["total"]
        assert selection["two_lp_paid_seconds"] == sum(item["child_elapsed_seconds"] for item in per_case)
        best_lower = (Fraction(bounds["best_saved_target_lower_exact"])
                      if bounds["best_saved_target_lower_exact"] is not None else None)
        cases.append({"case": name, "archive": rel(archive),
                      "archive_frozen_sha256": sha(archive_frozen_path),
                      "archive_catalog_sha256": sha(archive_catalog_path),
                      "selection_sha256": sha(selection_path),
                      "historical_target": bounds,
                      "best_direct_source": direct_best["source"],
                      "best_direct_cost_exact": direct_best["direct_target_cost_exact"],
                      "best_direct_cost": direct_best["direct_target_cost"],
                      "best_recharged_source": charged_best["source"],
                      "best_recharged_cost_exact": charged_best["charged_target_cost_exact"],
                      "best_recharged_cost": charged_best["charged_target_cost"],
                      "best_of_four": selection["best_of_four"],
                      "best_recharged_minus_historical_lower_exact": (
                          str(Fraction(charged_best["charged_target_cost_exact"]) - best_lower)
                          if best_lower is not None else None),
                      "best_recharged_minus_historical_lower": (
                          float(Fraction(charged_best["charged_target_cost_exact"]) - best_lower)
                          if best_lower is not None else None),
                      "best_recharged_minus_best_historical_control_exact": (
                          str(Fraction(charged_best["charged_target_cost_exact"]) -
                              Fraction(bounds["best_archived_target_control_cost_exact"]))
                          if bounds["best_archived_target_control_cost_exact"] is not None else None),
                      "best_recharged_minus_best_historical_control": (
                          float(Fraction(charged_best["charged_target_cost_exact"]) -
                                Fraction(bounds["best_archived_target_control_cost_exact"]))
                          if bounds["best_archived_target_control_cost_exact"] is not None else None)})
    return {"schema": "egg-independent-fixed-source-charge-replay-v1",
            "attempt_frozen_json": rel(ATTEMPT / "frozen.json"),
            "attempt_frozen_sha256": sha(ATTEMPT / "frozen.json"),
            "summary_json": rel(ATTEMPT / "summary.json"),
            "summary_sha256": sha(ATTEMPT / "summary.json"),
            "method": "Fresh native physical replay and checked pricing start for all 16 plans; exact Fraction nonlinear target-market costs, case/market identities, source/fixed movement sets, hashes, saved receipts and same-target historical lower bounds checked without optimization.",
            "scope": "Eight archived source routes and their eight fixed-route charging LP outcomes, across four development groups. OPTIMAL refers only to the fixed-route linear-tariff charging LP. Curved target objective, fleet route choice, and global physical optimum remain uncertified. Historical target bounds are same-market archived certificates, not newly solved bounds.",
            "cells": cells, "cases": cases}


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
    print("Verified eight archived source and eight fixed-route charged plans")


if __name__ == "__main__":
    main()
