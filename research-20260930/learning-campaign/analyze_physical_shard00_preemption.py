#!/usr/bin/env python3
"""Replay only receipted cells from the partial shard-00 training attempt."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from egglab import learned_proposals as edge  # noqa: E402
from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402
from egglab import physical_learning_cases as physical  # noqa: E402
from experiments import computational_benchmark as base  # noqa: E402
from experiments import physical_learning_campaign as campaign  # noqa: E402


DEFAULT_ATTEMPT = ROOT / "result/physical_learning/20260930-shard00-attempt1"
DEFAULT_OUTPUT = ROOT / "research-20260930/learning-campaign/PHYSICAL_SHARD00_PREEMPTION_REPLAY.json"
PAIR_TOLERANCE = Fraction("0.000001")


def read_json(path):
    return json.loads(Path(path).read_text())


def plan_topology(plan):
    return tuple(sorted(mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]))


def exact_bill(market, replay):
    return Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])


def summarize(attempt, output, slurm_state, slurm_wall_seconds):
    attempt = Path(attempt).resolve()
    manifest_path, frozen_path, catalog_path = (attempt / "manifest.json",
        attempt / "frozen.json", attempt / "catalog.jsonl")
    manifest, frozen = read_json(manifest_path), read_json(frozen_path)
    if (attempt.name != "20260930-shard00-attempt1"
            or manifest.get("shard") != 0
            or manifest.get("materialized_split") != "train"
            or manifest.get("declared_cells") != 64
            or frozen.get("manifest_sha256") != base.sha(manifest_path)):
        raise ValueError("Attempt is not the frozen shard-00 training design")

    rows = [json.loads(line) for line in catalog_path.read_text().splitlines() if line]
    by_id = {}
    for row in rows:
        key = row.get("row_id")
        if key in by_id:
            raise ValueError("Duplicate catalog row: " + str(key))
        by_id[key] = row
    expected = campaign.cells(0)
    expected_ids = {physical.make_case(base_id).name + "/" + stage
                    for base_id, stage in expected}
    if not set(by_id) <= expected_ids:
        raise ValueError("Catalog contains a cell outside the frozen shard")

    cell_states, receipt_paths, launch_paths = [], [], []
    for base_id, stage in expected:
        case = physical.make_case(base_id)
        cell_dir = attempt / case.name / "state0" / stage
        launched = (cell_dir / "launch.json").is_file()
        receipted = (cell_dir / "receipt.json").is_file()
        catalogued = case.name + "/" + stage in by_id
        cell_states.append({"row_id": case.name + "/" + stage,
            "base_id": base_id, "stage": stage,
            "launched": launched, "receipted": receipted, "catalogued": catalogued})
        if receipted:
            receipt_paths.append(cell_dir / "receipt.json")
        if launched:
            launch_paths.append(cell_dir / "launch.json")
        if catalogued != receipted:
            raise ValueError("Catalog and per-cell receipt coverage differ at " + case.name + "/" + stage)
        if receipted and not launched:
            raise ValueError("Receipted cell lacks launch record: " + case.name + "/" + stage)

    source = {}
    source_rows = []
    target_rows = []
    replay_started = time.monotonic()
    input_paths = set([manifest_path, frozen_path, catalog_path,
                       *receipt_paths, *launch_paths])

    for base_id, stage in expected:
        row_id = physical.make_case(base_id).name + "/" + stage
        if row_id not in by_id:
            continue
        row = by_id[row_id]
        case = edge.case_from_dict(row["case"])
        market = nh.Market(**row["market"])
        label = row["label"]
        cell_dir = attempt / case.name / "state0" / stage
        receipt = read_json(cell_dir / "receipt.json")
        expected_case = physical.make_case(base_id)
        manifest_group = manifest["groups"][expected_case.name]
        market_kind = stage if stage in campaign.SOURCES else stage.rsplit("_", 1)[-1]
        expected_market = physical.market(expected_case, market_kind)
        if (row.get("split") != "train" or row.get("base_id") != base_id
                or row.get("base_group") != f"physical_v2_s{base_id}"
                or row.get("row_id") != row_id
                or case.identity() != expected_case.identity()
                or row.get("case_identity") != case.identity()
                or row.get("case_identity") != manifest_group["case_identity"]
                or row.get("market_identity") != market.identity()
                or market.identity() != expected_market.identity()
                or market.identity() != manifest_group["market_identities"][market_kind]
                or row.get("market_name") != market_kind
                or row.get("market_role") != ("source" if stage in campaign.SOURCES else "target")
                or label.get("receipt") != receipt
                or label.get("elapsed_seconds") != receipt.get("elapsed_seconds")
                or label.get("status") != "returned"
                or receipt.get("returncode") != 0 or receipt.get("hard_timeout")
                or not label.get("feasible")):
            raise ValueError("Completed-cell identity/receipt/feasibility mismatch: " + row_id)
        plan = label["plan"]
        replay = nr.replay_native(case, plan)
        pf._checked_pricing_start(case, plan)
        bill = exact_bill(market, replay)
        plan_hash = nr.digest(plan)
        if (plan_hash != label.get("plan_hash")
                or replay.get("ops_cost") != label.get("ops_cost")
                or replay.get("load") != label.get("load")
                or str(bill) != label.get("objective_exact")):
            raise ValueError("Saved label does not match independent physical/cost replay: " + row_id)
        input_paths.add(cell_dir / "direct_rescore.json") if (cell_dir / "direct_rescore.json").is_file() else None

        if stage in campaign.SOURCES:
            raw_path = cell_dir / "raw_result.json"
            if not raw_path.is_file():
                raise ValueError("Source outcome missing raw native result: " + row_id)
            raw = read_json(raw_path).get("result", {})
            if (raw.get("status") != label.get("native_status")
                    or not any(column.get("plan") == plan
                               and nr.digest(column["plan"]) == plan_hash
                               for column in raw.get("columns", []))):
                raise ValueError("Source plan/native receipt lineage mismatch: " + row_id)
            input_paths.add(raw_path)
            assessment_path = cell_dir / "result.json"
            if assessment_path.is_file():
                input_paths.add(assessment_path)
            source[(base_id, stage)] = {"row": row, "case": case, "plan": plan,
                "plan_hash": plan_hash, "topology": plan_topology(plan),
                "market": market, "replay": replay, "cost_exact": str(bill),
                "native_status": label.get("native_status"),
                "elapsed_seconds": receipt.get("elapsed_seconds")}
            source_rows.append({"row_id": row_id, "base_id": base_id,
                "source": stage, "plan_hash": plan_hash,
                "topology_movement_count": len(plan_topology(plan)),
                "physical_cost_exact": str(bill),
                "source_lower_exact_imported": label.get("lower_exact"),
                "unverified_source_lower_exact_imported": label.get("unverified_native_lower_exact"),
                "native_status": label.get("native_status"),
                "child_elapsed_seconds": receipt.get("elapsed_seconds")})
        else:
            source_name = stage.split("_charge_", 1)[0]
            direct_path = cell_dir / "direct_rescore.json"
            evidence_path = cell_dir / "fixed_charge.json"
            if not direct_path.is_file() or not evidence_path.is_file():
                raise ValueError("Replayed charge cell lacks source/LP evidence: " + row_id)
            direct, evidence = read_json(direct_path), read_json(evidence_path)
            source_cell = source.get((base_id, source_name))
            if source_cell is None:
                raise ValueError("Charge cell lacks its earlier receipted source plan: " + row_id)
            source_hash = source_cell["plan_hash"]
            if (row.get("source_market") != source_name
                    or direct.get("source_row_id") != source_cell["row"]["row_id"]
                    or label.get("source_plan_hash") != source_hash
                    or direct.get("source_plan_hash") != source_hash
                    or direct.get("case_identity") != case.identity()
                    or direct.get("market_identity") != market.identity()
                    or evidence.get("source_plan_hash") != source_hash
                    or evidence.get("case_identity") != case.identity()
                    or evidence.get("market_identity") != market.identity()
                    or evidence.get("plan") != plan
                    or evidence.get("plan_hash") != plan_hash
                    or evidence.get("replay") != replay
                    or evidence.get("objective_exact") != str(bill)
                    or evidence.get("native_stats", {}).get("status") != label.get("native_status")
                    or set(evidence.get("selected_movements", ())) != set(source_cell["topology"])
                    or set(plan_topology(plan)) != set(source_cell["topology"])
                    or direct.get("objective_exact") != str(exact_bill(market, source_cell["replay"]))):
                raise ValueError("Charged plan/source lineage/exact bill mismatch: " + row_id)
            input_paths.update((direct_path, evidence_path))
            target_rows.append({"row_id": row_id, "base_id": base_id,
                "tariff": stage.rsplit("_", 1)[-1], "source": source_name,
                "source_plan_hash": source_hash, "plan_hash": plan_hash,
                "physical_cost_exact": str(bill),
                "direct_source_bill_exact": direct.get("objective_exact"),
                "native_status": label.get("native_status"),
                "child_elapsed_seconds": receipt.get("elapsed_seconds"),
                "charge_wall_seconds": label.get("charge_wall_seconds"),
                "independent_replay_wall_seconds": label.get("independent_replay_wall_seconds")})

    replay_elapsed = time.monotonic() - replay_started
    input_hashes = {str(path.relative_to(attempt)): base.sha(path)
                    for path in sorted(input_paths)}

    source_pairs = []
    for base_id in physical.shard_ids(0):
        left, right = source.get((base_id, "source0")), source.get((base_id, "source1"))
        if not left or not right:
            raise ValueError("Expected all eight source pairs to be receipted")
        source_pairs.append({"base_id": base_id,
            "source0_plan_hash": left["plan_hash"], "source1_plan_hash": right["plan_hash"],
            "identical_movement_topology": left["topology"] == right["topology"],
            "identical_full_plan_hash": left["plan_hash"] == right["plan_hash"]})

    paired = []
    by_target = {(row["base_id"], row["tariff"], row["source"]): row for row in target_rows}
    complete_groups = []
    for base_id in physical.shard_ids(0):
        tariffs_here = [tariff for tariff in campaign.TARIFFS
                        if (base_id, tariff, "source0") in by_target
                        and (base_id, tariff, "source1") in by_target]
        if len(tariffs_here) == len(campaign.TARIFFS):
            complete_groups.append(base_id)
        for tariff in tariffs_here:
            a, b = by_target[(base_id, tariff, "source0")], by_target[(base_id, tariff, "source1")]
            ca, cb = Fraction(a["physical_cost_exact"]), Fraction(b["physical_cost_exact"])
            delta = ca - cb
            paired.append({"base_id": base_id, "tariff": tariff,
                "source0_cost_exact": str(ca), "source1_cost_exact": str(cb),
                "source0_minus_source1_exact": str(delta),
                "absolute_margin_exact": str(abs(delta)),
                "winner": ("tie" if abs(delta) <= PAIR_TOLERANCE
                           else "source0" if delta < 0 else "source1")})

    launches = sum(state["launched"] for state in cell_states)
    receipted = sum(state["receipted"] for state in cell_states)
    first_unreceipted = next((i for i, state in enumerate(cell_states)
                              if state["launched"] and not state["receipted"]), None)
    unlaunched_after = sum(not state["launched"] for state in cell_states)
    if launches != 41 or receipted != 40 or first_unreceipted is None:
        raise ValueError(f"Unexpected partial shard accounting: launches={launches}, receipts={receipted}")
    interrupted = cell_states[first_unreceipted]
    if unlaunched_after != 23:
        raise ValueError("Unexpected number of unlaunched cells")
    if len(rows) != receipted:
        raise ValueError("Catalog does not cover exactly all receipted cells")

    def timing(values):
        vals = [float(value) for value in values if value is not None]
        return {"n": len(vals), "sum_seconds": sum(vals),
            "median_seconds": statistics.median(vals) if vals else None,
            "min_seconds": min(vals) if vals else None,
            "max_seconds": max(vals) if vals else None}

    child_times = [row["label"].get("elapsed_seconds") for row in rows]
    source_times = [item["child_elapsed_seconds"] for item in source_rows]
    target_times = [item["child_elapsed_seconds"] for item in target_rows]
    charge_times = [item["charge_wall_seconds"] for item in target_rows]
    replay_times = [item["independent_replay_wall_seconds"] for item in target_rows]
    stage_counts = Counter(item["stage"] for item in cell_states if item["receipted"])
    status_counts = Counter(by_id[item["row_id"]]["label"].get("native_status")
                            for item in cell_states if item["receipted"])
    profile_rows = []
    for base_id in physical.shard_ids(0):
        group = manifest["groups"][physical.make_case(base_id).name]
        profile_rows.append({"base_id": base_id, "services": group["assignment"]["services"],
            "battery_profile": group["assignment"]["profile"]})

    result = {"schema": "physical-shard00-preemption-replay-v1",
        "attempt": str(attempt), "frozen_source_commit": frozen.get("source_commit"),
        "manifest_sha256": frozen.get("manifest_sha256"),
        "analyzer_sha256": base.sha(Path(__file__)),
        "partial_job_accounting": {"state": slurm_state,
            "slurm_elapsed_seconds": slurm_wall_seconds,
            "wrapper_receipt_present": any(attempt.parent.glob(attempt.name + ".slurm_wrapper_receipt.*.json")),
            "summary_present": (attempt / "summary.json").is_file()},
        "coverage": {"cells_declared": len(expected), "cells_launched": launches,
            "cells_receipted_and_catalogued": receipted, "cells_unlaunched": unlaunched_after,
            "launched_without_receipt": launches-receipted,
            "interrupted_first_cell": interrupted["row_id"],
            "preemption_ordering_note": "The fixed manifest order completed all source cells, then all three tariffs for the first four base groups; the next target cell was launched without a receipt and the final 23 cells were never launched.",
            "catalog_status_counts": dict(Counter(row["label"].get("status") for row in rows)),
            "native_status_counts": dict(status_counts),
            "stage_counts_receipted": dict(stage_counts)},
        "source_plan_pairs": source_pairs,
        "source_topology_equal_groups": sum(x["identical_movement_topology"] for x in source_pairs),
        "source_full_plan_equal_groups": sum(x["identical_full_plan_hash"] for x in source_pairs),
        "observed_charging_labels": target_rows,
        "paired_tariff_comparisons": paired,
        "pair_tie_tolerance_exact": str(PAIR_TOLERANCE),
        "charging_complete_groups": complete_groups,
        "charging_complete_group_count": len(complete_groups),
        "paired_winner_counts": dict(Counter(item["winner"] for item in paired)),
        "timing_seconds": {"worker_child_all_receipted": timing(child_times),
            "source_children": timing(source_times), "target_children": timing(target_times),
            "target_charge_phase": timing(charge_times),
            "target_independent_replay_phase": timing(replay_times),
            "posthoc_physical_replay_elapsed": replay_elapsed},
        "groups": profile_rows,
        "limitations": ["This is a preempted prefix, not a completed 64-cell shard.",
            "The 24 observed charging cells cover only the first four base IDs by frozen execution order; later groups are unobserved, so the sample is ordering-biased.",
            "Source lower bounds are imported source-market campaign fields and were not independently recertified here.",
            "No model was fit; no dev/test case was read; no optimization was run."],
        "input_hashes_sha256": input_hashes}
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--slurm-state", default="PREEMPTED")
    parser.add_argument("--slurm-wall-seconds", type=float, default=713.0)
    args = parser.parse_args()
    result = summarize(args.attempt, args.output, args.slurm_state,
                       args.slurm_wall_seconds)
    print(json.dumps({"output": str(args.output),
        "receipted": result["coverage"]["cells_receipted_and_catalogued"],
        "target_labels": result["coverage"]["stage_counts_receipted"]}, sort_keys=True))


if __name__ == "__main__":
    main()
