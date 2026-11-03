"""Read-only matched source-topology charging attribution on four declared TRAIN/day groups.

The precommitted protocol is ROUTE_DECODER_MATCHED_SOURCE_CHARGE_V1_PROTOCOL.md.
No native solver, model fit, or reserved outcome is called or read here.
"""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from experiments import computational_benchmark as base
from experiments import physical_route_decoder_pilot_v1 as pilot

DOC = base.ROOT / "research-20260930/learning-campaign"
DATA = base.ROOT / "result/physical_learning/20260930-shard04-dataset-v1"
OUTPUT = DOC / "ROUTE_DECODER_MATCHED_SOURCE_CHARGE_V1_REPLAY.json"
PILOT = DOC / "ROUTE_DECODER_TRAIN_PILOT_V2_REPLAY.json"
PILOT_SHA = "2c8d0b177f341fccce351306ff7c88012b4076187ab8e16b60086bc9229163e5"
PROTOCOL = DOC / "ROUTE_DECODER_MATCHED_SOURCE_CHARGE_V1_PROTOCOL.md"
PROTOCOL_SHA = "174ebe2aea2f5cfcb9cd53928d02785a53d759b18e6f56cd74862d057b1a2622"
PROTOCOL_COMMIT = "b33f028d5aad63138a4f75c2df1f7d5f61c79d43"
IDS = tuple(range(10036, 10040))
SOURCES = ("source0", "source1")
LEARNED = ("32_logistic", "32_hist_boosted", "64_logistic", "64_hist_boosted")


def load(path):
    return json.loads(Path(path).read_text())


def rows(name):
    return [json.loads(line) for line in (DATA / name).read_text().splitlines()]


def selected(plan):
    return {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}


def exact_bill(market, replay):
    return Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])


def one(table, group_id, source, kind=None):
    found = [r for r in table if r.get("base_id") == group_id
             and r.get("source") == source
             and (kind is None or r.get("market_kind") == kind)]
    if len(found) != 1:
        raise ValueError(f"Expected one {group_id}/{source}/{kind}, got {len(found)}")
    return found[0]


def build():
    if base.sha(PILOT) != PILOT_SHA or base.sha(PROTOCOL) != PROTOCOL_SHA:
        raise ValueError("Frozen pilot or prospective protocol changed")
    receipt = load(DATA / "dataset_receipt.json")
    if (receipt.get("schema") != "physical-learning-dataset-v1"
            or receipt.get("status") != "complete" or receipt.get("train_only") is not True
            or len(receipt.get("shards", [])) != 1):
        raise ValueError("Unknown or non-TRAIN shard-04 dataset receipt")
    for name in ("source_inputs.jsonl", "target_inputs.jsonl", "target_outcomes.jsonl"):
        if base.sha(DATA / name) != receipt["output_hashes"][name]:
            raise ValueError(f"Dataset table hash changed: {name}")
    source_inputs = rows("source_inputs.jsonl")
    target_inputs = rows("target_inputs.jsonl")
    target_outcomes = rows("target_outcomes.jsonl")
    pilot_data = load(PILOT)
    if [g["group_id"] for g in pilot_data["groups"]] != list(IDS):
        raise ValueError("Pilot group registry changed")
    out_groups = []
    for group_id, saved in zip(IDS, pilot_data["groups"]):
        case, market, pool_sources, eligibility = pilot.case_inputs(
            group_id, pilot_data["pool64_manifest_sha256"])
        if (saved["case_identity"] != case.identity()
                or saved["market_identity"] != market.identity()
                or saved["intended_sources"] != 2
                or saved["observed_sources"] != len(pool_sources)
                or eligibility["observed_source_count"] != len(pool_sources)):
            raise ValueError(f"Pilot source registry changed: {group_id}")
        pool_by_source = {r["source"]: r for r in pool_sources}
        if len(pool_by_source) != len(pool_sources):
            raise ValueError("Duplicate pool source")
        source_records = {}
        for source in SOURCES:
            ti = one(target_inputs, group_id, source, "day")
            to = one(target_outcomes, group_id, source, "day")
            common = ("base_id", "base_group", "source", "key", "market_kind",
                      "case_identity", "market_identity", "source_plan_hash")
            if (any(ti[k] != to[k] for k in common)
                    or ti["base_group"] != f"physical_v2_s{group_id}"
                    or ti["case_identity"] != case.identity()
                    or ti["market_identity"] != market.identity()
                    or ti["source"] != source):
                raise ValueError(f"Target input/outcome identity mismatch: {group_id}/{source}")
            record = {"source": source, "target_key": ti["key"],
                      "source_plan_hash": ti["source_plan_hash"],
                      "available": ti["available"], "status": to["status"],
                      "feasible": to["feasible"], "censored": to["censored"],
                      "native_status": to["native_status"],
                      "curved_optimality_uncertified": to["curved_optimality_uncertified"],
                      "paid_seconds": to["paid_seconds"],
                      "charge_wall_seconds": to["charge_wall_seconds"],
                      "independent_replay_wall_seconds": to["independent_replay_wall_seconds"],
                      "failure": to["failure"]}
            if source not in pool_by_source:
                if (ti["available"] is not False or ti["source_plan_hash"] is not None
                        or ti["direct_exact"] is not None or ti["selected_movements"] is not None
                        or to["status"] != "failed" or to["feasible"] is not False
                        or to["censored"] is not True or to["plan"] is not None
                        or to["objective_exact"] is not None or to["plan_hash"] is not None):
                    raise ValueError("Unavailable source acquired a target label")
                record.update({"direct_bill_exact": None, "charged_bill_exact": None,
                               "charged_plan_hash": None})
            else:
                source_row = one(source_inputs, group_id, source, source)
                pool_row = pool_by_source[source]
                if (source_row != pool_row
                        or ti["available"] is not True
                        or ti["source_plan_hash"] != source_row["source_plan_hash"]
                        or ti["selected_movements"] != source_row["selected_movements"]
                        or source_row["case_identity"] != case.identity()
                        or to["status"] != "returned" or to["feasible"] is not True
                        or to["censored"] is not False or to["failure"] is not None
                        or to["native_status"] != "OPTIMAL"
                        or to["curved_optimality_uncertified"] is not True):
                    raise ValueError(f"Charged source admission/status mismatch: {group_id}/{source}")
                direct = nr.replay_native(case, source_row["source_plan"])
                pf._checked_pricing_start(case, source_row["source_plan"])
                charged = nr.replay_native(case, to["plan"])
                pf._checked_pricing_start(case, to["plan"])
                direct_bill = exact_bill(market, direct)
                charged_bill = exact_bill(market, charged)
                if (direct != source_row["source_replay"]
                        or nr.digest(source_row["source_plan"]) != ti["source_plan_hash"]
                        or nr.digest(to["plan"]) != to["plan_hash"]
                        or selected(source_row["source_plan"]) != set(ti["selected_movements"])
                        or selected(to["plan"]) != set(ti["selected_movements"])
                        or str(direct_bill) != ti["direct_exact"]
                        or str(direct_bill) != saved["source_bills_exact"][source]
                        or str(charged_bill) != to["objective_exact"]):
                    raise ValueError(f"Independent source replay/bill/topology mismatch: {group_id}/{source}")
                record.update({"direct_bill_exact": str(direct_bill),
                               "charged_bill_exact": str(charged_bill),
                               "charged_plan_hash": to["plan_hash"],
                               "charged_minus_direct_exact": str(charged_bill-direct_bill)})
            source_records[source] = record
        valid = [r for r in source_records.values() if r["charged_bill_exact"] is not None]
        if len(valid) != saved["observed_sources"]:
            raise ValueError("Observed source denominator changed")
        best_direct = min(valid, key=lambda r: (Fraction(r["direct_bill_exact"]), r["source"]))
        best_charged = min(valid, key=lambda r: (Fraction(r["charged_bill_exact"]), r["source"]))
        best_source_policy = min(
            [(Fraction(r[k]), r["source"], policy)
             for r in valid for policy, k in (("direct", "direct_bill_exact"),
                                               ("charged", "charged_bill_exact"))])
        arms = {}
        for name in (*LEARNED, "cost_only"):
            prior = saved["arms"][name]
            cost = Fraction(prior["candidate_cost_exact"]) if prior["candidate_cost_exact"] else None
            if cost is None:
                if prior["proposal_status"] != "failed":
                    raise ValueError("Missing candidate without failed status")
            elif prior["proposal_status"] != "replayed":
                raise ValueError("Candidate cost without replay")
            arm = {"status": prior["proposal_status"], "cost_exact": str(cost) if cost is not None else None,
                   "topology_novel": prior["topology_novel"],
                   "plan_hash": prior["candidate_plan_hash"],
                   "minus_best_charged_source_exact": str(cost-Fraction(best_charged["charged_bill_exact"]))
                       if cost is not None else None,
                   "minus_best_direct_or_charged_source_exact": str(cost-best_source_policy[0])
                       if cost is not None else None,
                   "equal_charged_source_plan": [r["source"] for r in valid
                       if prior["candidate_plan_hash"] == r["charged_plan_hash"]] if cost is not None else []}
            arms[name] = arm
        out_groups.append({"group_id": group_id, "intended_sources": 2,
                           "observed_sources": len(valid),
                           "missing_source_labels": saved["missing_source_labels"],
                           "sources": source_records,
                           "best_direct_source": {"source": best_direct["source"],
                                                  "cost_exact": best_direct["direct_bill_exact"]},
                           "best_charged_source": {"source": best_charged["source"],
                                                   "cost_exact": best_charged["charged_bill_exact"]},
                           "best_direct_or_charged_source": {"source": best_source_policy[1],
                                                              "policy": best_source_policy[2],
                                                              "cost_exact": str(best_source_policy[0])},
                           "arms": arms})
    return {"scope": "predeclared TRAIN groups 10036-10039, target day; read-only replay",
            "protocol_commit": PROTOCOL_COMMIT, "protocol_sha256": PROTOCOL_SHA,
            "dataset_receipt_sha256": base.sha(DATA / "dataset_receipt.json"),
            "dataset_table_sha256": {n: base.sha(DATA / n) for n in
                ("source_inputs.jsonl", "target_inputs.jsonl", "target_outcomes.jsonl")},
            "pilot_replay_sha256": PILOT_SHA, "groups": out_groups,
            "independent_timetables": len(out_groups),
            "intended_source_cells": sum(g["intended_sources"] for g in out_groups),
            "observed_source_cells": sum(g["observed_sources"] for g in out_groups),
            "verification_source_sha256": base.sha(Path(__file__))}


def main():
    output = build()
    base.save_new(OUTPUT, output)
    print(json.dumps({"output": str(OUTPUT), "independent_timetables": output["independent_timetables"],
                      "observed_source_cells": output["observed_source_cells"]}, sort_keys=True))


if __name__ == "__main__":
    main()
