"""Completed-shard, train-only adapter for versioned physical fleet labels."""
from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
import json
import math
from pathlib import Path
import re

from egglab import learned_proposals as edge
from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from experiments import computational_benchmark as base
from experiments import physical_learning_campaign as campaign

SCHEMA = "physical-learning-dataset-v1"
PAIR_TOLERANCE = Fraction("0.000001")
STAGES = ("source0", "source1", "source0_charge_late", "source1_charge_late",
          "source0_charge_day", "source1_charge_day",
          "source0_charge_flat", "source1_charge_flat")
TARIFFS = ("late", "day", "flat")
HEX = re.compile(r"^[0-9a-f]{64}$")


class ExcludedShard(ValueError):
    """An incomplete or malformed shard is excluded from pooled learning."""


def _load(path):
    return json.loads(Path(path).read_text())


def _receipt_status(receipt):
    return "hard_timeout" if receipt.get("hard_timeout") else (
        "failed" if receipt.get("returncode") != 0 else "returned")


def _source_topology(plan):
    return tuple(sorted(mid for vehicle in plan["vehicles"]
                        for mid in vehicle["movements"]))


def _exact(case, market, replay):
    return Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"])


def _wrapper_receipts(attempt):
    files = sorted(attempt.parent.glob(attempt.name + ".slurm_wrapper_receipt.*.json"))
    if not files:
        raise ExcludedShard("Incomplete shard: no Slurm wrapper completion receipt")
    receipts = [_load(file) for file in files]
    return files, receipts


def _validate_header(attempt):
    attempt = Path(attempt).resolve()
    match = re.fullmatch(r"20260930-shard(\d\d)-attempt1", attempt.name)
    if not match or attempt.parent.name != "physical_learning":
        raise ExcludedShard("Attempt path is not a declared physical training shard")
    shard = int(match.group(1))
    if not 0 <= shard < 16:
        raise ExcludedShard("Undeclared physical training shard index")
    required = ("manifest.json", "frozen.json", "summary.json", "catalog.jsonl")
    if any(not (attempt / name).is_file() for name in required):
        raise ExcludedShard("Incomplete shard: manifest, freeze, summary or catalog absent")
    manifest, frozen, summary = (_load(attempt / name) for name in required[:3])
    if (manifest.get("generator") != physical.GENERATOR
            or manifest.get("materialized_split") != "train"
            or manifest.get("shard") != shard
            or manifest.get("selected_base_ids") != list(physical.shard_ids(shard))
            or manifest.get("declared_cells") != 64
            or frozen.get("manifest_sha256") != base.sha(attempt / "manifest.json")
            or frozen.get("protocol") != "egg-physical-learning-training-label-shard-20260930-v1"
            or not frozen.get("source_commit")
            or not isinstance(frozen.get("source_hashes"), dict)
            or any(not HEX.fullmatch(value) for value in frozen["source_hashes"].values())
            or summary.get("declared_cells") != 64
            or summary.get("accounted_cells") != 64
            or summary.get("shard") != shard):
        raise ExcludedShard("Malformed or incomplete frozen training shard header")
    if manifest.get("cell_order") != [{"base_id": seed, "stage": stage}
                                     for seed, stage in (
                                         [(seed, stage) for seed in physical.shard_ids(shard)
                                          for stage in STAGES[:2]] +
                                         [(seed, stage) for seed in physical.shard_ids(shard)
                                          for stage in STAGES[2:]])]:
        raise ExcludedShard("Manifest cell order differs from declared training shard")
    source_hashes = frozen["source_hashes"]
    if (set(source_hashes) != set(campaign.SOURCE_FILES)
            or len(source_hashes) != 18):
        raise ExcludedShard("Frozen source-hash pin set is incomplete or unknown")
    groups = manifest.get("groups")
    if not isinstance(groups, dict) or len(groups) != 8:
        raise ExcludedShard("Training shard has missing or extra base groups")
    seen_ids = set()
    for name, group in groups.items():
        seed = group.get("assignment", {}).get("base_id")
        if (seed not in physical.shard_ids(shard) or group["assignment"].get("split") != "train"
                or group.get("case_identity") != edge.case_from_dict(group["case"]).identity()
                or group.get("case_identity") != physical.make_case(seed).identity()
                or name != group["case"]["name"]):
            raise ExcludedShard("Malformed or cross-split physical group in manifest")
        seen_ids.add(seed)
        generated = physical.make_case(seed)
        if any(group.get("market_identities", {}).get(kind) != physical.market(generated, kind).identity()
               for kind in ("source0", "source1") + TARIFFS):
            raise ExcludedShard("Frozen group market identity differs from generator")
    if seen_ids != set(physical.shard_ids(shard)):
        raise ExcludedShard("Duplicate/missing physical base ID across shard groups")
    wrapper_files, wrappers = _wrapper_receipts(attempt)
    successful = [receipt for receipt in wrappers if receipt.get("shard") == shard
                  and all(receipt.get(key) == 0 for key in (
                      "returncode", "freeze_returncode", "preflight_returncode",
                      "controller_returncode"))]
    if len(wrappers) != 1 or len(successful) != 1 or any(
            receipt.get("shard") != shard for receipt in wrappers):
        raise ExcludedShard("Wrapper receipt does not complete the declared shard")
    return shard, manifest, frozen, summary, wrapper_files


def ingest_attempt(attempt):
    """Validate one completed shard, preserving censored and provisional rows."""
    attempt = Path(attempt).resolve()
    shard, manifest, frozen, summary, wrapper_files = _validate_header(attempt)
    rows = [json.loads(line) for line in (attempt / "catalog.jsonl").read_text().splitlines()]
    if len(rows) != 64:
        raise ExcludedShard("Incomplete shard: catalog is not exactly 64 cells")
    by_id = {}
    for row in rows:
        key = row.get("row_id")
        if key in by_id:
            raise ExcludedShard("Duplicate catalog cell " + str(key))
        by_id[key] = row
    expected_ids = {name + "/" + stage for name in manifest["groups"] for stage in STAGES}
    if set(by_id) != expected_ids:
        raise ExcludedShard("Missing or extra catalog cell; cross-shard mix rejected")
    cases, source_inputs, source_outcomes, target_inputs, target_outcomes = [], [], [], [], []
    source_bank = {}
    input_files = [attempt / name for name in ("manifest.json", "frozen.json",
                                                  "summary.json", "catalog.jsonl")]
    input_files.extend(wrapper_files)
    for name, group in manifest["groups"].items():
        case = edge.case_from_dict(group["case"])
        base_id = group["assignment"]["base_id"]
        group_key = f"physical_v2_s{base_id}"
        if (name != case.name or group["case_identity"] != case.identity()
                or group["assignment"] != physical.assignment(base_id)):
            raise ExcludedShard("Physical case or assignment lineage changed")
        cases.append({"base_group": group_key, "base_id": base_id, "split": "train",
            "generator": physical.GENERATOR, "case_identity": case.identity(),
            "physical_profile": group["assignment"], "case": group["case"],
            "witness_hash": group["witness_hash"]})
        for stage in STAGES:
            row = by_id[name + "/" + stage]
            market_kind = stage if stage in STAGES[:2] else stage.rsplit("_", 1)[-1]
            market = nh.Market(**row["market"])
            receipt_file = attempt / name / "state0" / stage / "receipt.json"
            if not receipt_file.is_file():
                raise ExcludedShard("Missing per-cell receipt: " + name + "/" + stage)
            receipt = _load(receipt_file)
            input_files.append(receipt_file)
            label = row.get("label", {})
            if (row.get("base_group") != group_key or row.get("base_id") != base_id
                    or row.get("split") != "train" or row.get("case_identity") != case.identity()
                    or base.canonical(row.get("case")) != base.canonical(group["case"])
                    or row.get("physical_profile") != group["assignment"]
                    or row.get("market_identity") != market.identity()
                    or market.identity() != group["market_identities"][market_kind]
                    or row.get("market_name") != market_kind
                    or row.get("market_role") != ("source" if stage in STAGES[:2] else "target")
                    or label.get("receipt") != receipt
                    or label.get("status") != _receipt_status(receipt)
                    or label.get("elapsed_seconds") != receipt.get("elapsed_seconds")):
                raise ExcludedShard("Cell identity, market, split, profile or receipt mismatch: " + name + "/" + stage)
            is_source = stage in STAGES[:2]
            if row.get("arm") != ("source" if is_source else "fixed_source_charge"):
                raise ExcludedShard("Unexpected source/target arm")
            if is_source and row.get("source_market") is not None:
                raise ExcludedShard("Source cell has target source_market tag")
            if not is_source and row.get("source_market") != stage.split("_charge_", 1)[0]:
                raise ExcludedShard("Target/source lineage tag changed")
            plan = label.get("plan")
            replay = None
            if label.get("feasible"):
                if not isinstance(plan, dict):
                    raise ExcludedShard("Feasible label lacks a full physical plan")
                replay = nr.replay_native(case, plan)
                pf._checked_pricing_start(case, plan)
                exact = _exact(case, market, replay)
                if (label.get("plan_hash") != nr.digest(plan)
                        or label.get("ops_cost") != replay["ops_cost"]
                        or label.get("load") != replay["load"]
                        or label.get("objective_exact") != str(exact)):
                    raise ExcludedShard("Feasible label plan/hash/exact bill differs from replay")
            elif plan is not None or label.get("objective_exact") is not None:
                raise ExcludedShard("Censored label fabricates a plan or zero outcome")
            common = {"key": row["row_id"], "base_group": group_key, "base_id": base_id,
                "case_identity": case.identity(), "market_identity": market.identity(),
                "market_kind": market_kind, "source": stage if is_source else row["source_market"]}
            outcome = {**common, "status": label.get("status"),
                "native_status": label.get("native_status"), "feasible": bool(label.get("feasible")),
                "censored": not bool(label.get("feasible")),
                "feasible_after_child_failure": bool(label.get("feasible") and label.get("status") != "returned"),
                "certified_for_reported_objective": False,
                "curved_optimality_uncertified": bool(label.get("feasible")),
                "provisional_after_native_limit": bool(label.get("feasible") and (
                    label.get("status") != "returned" or
                    label.get("native_status") not in ("OPTIMAL", "optimal", "hull_certified"))),
                "reported_objective_scope": ("source-market physical incumbent; open physical gap possible"
                    if is_source else "curved cost of returned linear-tariff fixed-route LP plan"),
                "optimality_label": label.get("optimality"),
                "failure": label.get("failure"), "paid_seconds": label.get("elapsed_seconds"),
                "objective_exact": label.get("objective_exact"),
                "plan_hash": label.get("plan_hash"), "plan": plan,
                "source_market_lower_exact": label.get("lower_exact") if is_source else None,
                "source_market_upper_exact": label.get("upper_exact") if is_source else None,
                "bounds_replay": label.get("bounds_replay") if is_source else None,
                "unverified_native_lower_exact": label.get("unverified_native_lower_exact") if is_source else None,
                "source_plan_hash": label.get("source_plan_hash") if not is_source else None,
                "charge_wall_seconds": label.get("charge_wall_seconds") if not is_source else None,
                "independent_replay_wall_seconds": label.get("independent_replay_wall_seconds") if not is_source else None}
            if is_source:
                source_dir = attempt / name / "state0" / stage
                raw_file = source_dir / "raw_result.json"
                assessment_file = source_dir / "result.json"
                if raw_file.is_file():
                    raw = _load(raw_file).get("result", {})
                    input_files.append(raw_file)
                    if raw.get("status") != label.get("native_status"):
                        raise ExcludedShard("Source native status differs from saved raw solver result")
                    if replay is not None and not any(
                            column.get("plan") == plan and nr.digest(column["plan"]) == label["plan_hash"]
                            for column in raw.get("columns", [])):
                        raise ExcludedShard("Replayed source plan lacks raw native column lineage")
                elif replay is not None or label.get("native_status") is not None:
                    raise ExcludedShard("Source incumbent/status lacks raw native result")
                if assessment_file.is_file():
                    assessment = _load(assessment_file).get("assessment", {})
                    input_files.append(assessment_file)
                    if raw_file.is_file() and label.get("bounds_replay") != {
                            "global_certificate_replayed":
                                assessment.get("global_certificate_replayed") is True,
                            "mixture_replayed": assessment.get("mixture_replayed") is True}:
                        raise ExcludedShard("Imported source bound-assessment flags changed")
                source_outcomes.append(outcome)
                if replay is not None:
                    source_bank[(group_key, stage)] = (plan, replay, row)
                    source_inputs.append({**common,
                        "source_plan_hash": label["plan_hash"],
                        "selected_movements": list(_source_topology(plan)),
                        "source_plan": plan,
                        "source_replay": replay})
            else:
                source = row["source_market"]
                stored = source_bank.get((group_key, source))
                evidence_file = attempt / name / "state0" / stage / "fixed_charge.json"
                direct_file = attempt / name / "state0" / stage / "direct_rescore.json"
                if replay is None and evidence_file.is_file():
                    raise ExcludedShard("Censored target contradicts replayed fixed-charge evidence")
                # Source cells are guaranteed first in manifest/cell order.
                if stored is None:
                    if replay is not None:
                        raise ExcludedShard("Target plan replayed without a source plan")
                    if direct_file.is_file():
                        raise ExcludedShard("Direct target rescore exists without a source plan")
                    target_inputs.append({**common, "available": False,
                        "source_plan_hash": None, "direct_exact": None,
                        "selected_movements": None, "target_market": row["market"]})
                else:
                    source_plan, source_replay, source_row = stored
                    direct = _exact(case, market, source_replay)
                    source_hash = source_row["label"]["plan_hash"]
                    if replay is not None:
                        if not evidence_file.is_file():
                            raise ExcludedShard("Replayed target lacks fixed-charge evidence")
                        evidence = _load(evidence_file)
                        input_files.append(evidence_file)
                        if (label.get("source_plan_hash") != source_hash
                                or evidence.get("status") != "replayed"
                                or evidence.get("source_plan_hash") != source_hash
                                or evidence.get("case_identity") != case.identity()
                                or evidence.get("market_identity") != market.identity()
                                or evidence.get("plan") != plan
                                or evidence.get("plan_hash") != label["plan_hash"]
                                or evidence.get("objective_exact") != label["objective_exact"]
                                or evidence.get("replay") != replay
                                or evidence.get("native_stats", {}).get("status") != label.get("native_status")
                                or set(evidence.get("selected_movements", ())) != set(_source_topology(source_plan))
                                or set(_source_topology(plan)) != set(_source_topology(source_plan))):
                            raise ExcludedShard("Fixed-charge source topology/evidence mismatch")
                    if direct_file.is_file():
                        direct_evidence = _load(direct_file)
                        input_files.append(direct_file)
                        if (direct_evidence.get("source_plan_hash") != source_hash
                                or direct_evidence.get("source_row_id") != source_row["row_id"]
                                or direct_evidence.get("case_identity") != case.identity()
                                or direct_evidence.get("objective_exact") != str(direct)
                                or direct_evidence.get("market_identity") != market.identity()):
                            raise ExcludedShard("Direct target rescore/source lineage changed")
                    target_inputs.append({**common, "available": True,
                        "source_plan_hash": source_hash, "direct_exact": str(direct),
                        "selected_movements": list(_source_topology(source_plan)),
                        "target_market": row["market"]})
                target_outcomes.append(outcome)
    if len(cases) != 8 or len(source_outcomes) != 16 or len(target_outcomes) != 48:
        raise ExcludedShard("Completed shard row counts changed")
    return {"shard": shard, "attempt": str(attempt), "frozen_source_commit": frozen["source_commit"],
        "frozen_source_hashes": frozen["source_hashes"],
        "inputs": {str(file): base.sha(file) for file in sorted(set(input_files))},
        "cases": cases, "source_inputs": source_inputs,
        "source_outcomes": source_outcomes, "target_inputs": target_inputs,
        "target_outcomes": target_outcomes}


def health(dataset):
    """Compute group-unit health, retaining exclusions and censored outcomes."""
    groups = {}
    source_inputs = {(x["base_group"], x["source"]): x for x in dataset["source_inputs"]}
    source_outcomes = {(x["base_group"], x["source"]): x
                       for x in dataset["source_outcomes"]}
    target = {(x["base_group"], x["market_kind"], x["source"]): x
              for x in dataset["target_outcomes"]}
    by_regime = defaultdict(list)
    eligible_pairs, exclusions, source_pair_exclusions = [], [], []
    for case in dataset["cases"]:
        group = case["base_group"]
        spec = case["physical_profile"]
        sources = [source_inputs.get((group, source)) for source in ("source0", "source1")]
        topo_equal = (sources[0]["selected_movements"] == sources[1]["selected_movements"]
                      if all(sources) else None)
        plan_equal = (sources[0]["source_plan_hash"] == sources[1]["source_plan_hash"]
                      if all(sources) else None)
        if not all(sources):
            source_pair_exclusions.append({"base_group": group,
                "reason": "incomplete_replayed_source_pair",
                "source0_status": source_outcomes[(group, "source0")]["status"],
                "source1_status": source_outcomes[(group, "source1")]["status"]})
        tariffs = {}
        for tariff in TARIFFS:
            a = target[(group, tariff, "source0")]
            b = target[(group, tariff, "source1")]
            winner = margin = None
            if a["feasible"] and b["feasible"]:
                difference = Fraction(a["objective_exact"])-Fraction(b["objective_exact"])
                margin = str(abs(difference))
                winner = ("tie" if abs(difference) <= PAIR_TOLERANCE else
                          "source0" if difference < 0 else "source1")
                eligible_pairs.append({"base_group": group, "tariff": tariff,
                    "winner": winner, "margin_exact": margin,
                    "curved_optimality_uncertified": True,
                    "provisional_after_native_limit": bool(
                        a["provisional_after_native_limit"] or b["provisional_after_native_limit"])})
            else:
                exclusions.append({"base_group": group, "tariff": tariff,
                    "reason": "incomplete_replayed_pair",
                    "source0_status": a["status"], "source1_status": b["status"],
                    "source0_feasible": a["feasible"], "source1_feasible": b["feasible"]})
            tariffs[tariff] = {"winner": winner, "margin_exact": margin,
                "source0_feasible": a["feasible"], "source1_feasible": b["feasible"],
                "source0_status": a["status"], "source1_status": b["status"]}
        regime = spec["profile"]["name"]
        size = spec["services"]
        groups[group] = {"base_id": case["base_id"], "regime": regime, "services": size,
            "source_topology_equal": topo_equal, "source_full_plan_equal": plan_equal,
            "tariffs": tariffs,
            "complete_all_three_pairs": all(t["winner"] is not None for t in tariffs.values())}
        by_regime[(regime, size)].append(group)
    strata = {}
    for (regime, size), names in by_regime.items():
        outcomes = [target[(name, tariff, source)] for name in names
                    for tariff in TARIFFS for source in ("source0", "source1")]
        sources = [source_outcomes[(name, source)] for name in names
                   for source in ("source0", "source1")]
        winners = Counter(groups[name]["tariffs"][tariff]["winner"] for name in names
                          for tariff in TARIFFS if groups[name]["tariffs"][tariff]["winner"] is not None)
        pair_denominator = len(names)*len(TARIFFS)
        source_pair_denominator = sum(groups[name]["source_topology_equal"] is not None
                                      for name in names)
        topology_numerator = sum(groups[name]["source_topology_equal"] is True for name in names)
        full_plan_numerator = sum(groups[name]["source_full_plan_equal"] is True for name in names)
        winner_total = sum(winners.values())
        entropy = (-sum((count/winner_total)*math.log2(count/winner_total)
                        for count in winners.values()) if winner_total else None)
        margins = [groups[name]["tariffs"][tariff]["margin_exact"]
                   for name in names for tariff in TARIFFS
                   if groups[name]["tariffs"][tariff]["margin_exact"] is not None]
        strata[f"{regime}/n{size}"] = {"base_groups": len(names),
            "distinct_replayed_source_topologies": len({tuple(
                source_inputs[(name, source)]["selected_movements"])
                for name in names for source in ("source0", "source1")
                if (name, source) in source_inputs}),
            "complete_all_three_pair_groups": sum(groups[name]["complete_all_three_pairs"] for name in names),
            "source_pairs_intended": len(names),
            "source_pairs_replayed": source_pair_denominator,
            "identical_source_topology_groups": topology_numerator,
            "identical_source_topology_fraction": (topology_numerator/source_pair_denominator
                if source_pair_denominator else None),
            "identical_source_full_plan_groups": full_plan_numerator,
            "identical_source_full_plan_fraction": (full_plan_numerator/source_pair_denominator
                if source_pair_denominator else None),
            "source_status_counts": dict(Counter(row["status"] for row in sources)),
            "source_native_status_counts": dict(Counter(
                row["native_status"] or "not_reported" for row in sources)),
            "target_labels_intended": len(outcomes),
            "replayed_target_labels": sum(row["feasible"] for row in outcomes),
            "censored_target_labels": sum(row["censored"] for row in outcomes),
            "curved_optimality_uncertified_target_labels": sum(
                row["curved_optimality_uncertified"] for row in outcomes),
            "provisional_after_native_limit_target_labels": sum(
                row["provisional_after_native_limit"] for row in outcomes),
            "feasible_after_child_failure_target_labels": sum(
                row["feasible_after_child_failure"] for row in outcomes),
            "status_counts": dict(Counter(row["status"] for row in outcomes)),
            "target_native_status_counts": dict(Counter(
                row["native_status"] or "not_reported" for row in outcomes)),
            "paired_targets_intended": pair_denominator,
            "paired_targets_eligible": winner_total,
            "paired_winner_counts": dict(winners),
            "paired_winner_entropy_bits_descriptive": entropy,
            "paired_margin_exact_values": margins,
            "paired_near_ties": winners.get("tie", 0)}
    return {"schema": SCHEMA, "pair_tolerance_exact": str(PAIR_TOLERANCE),
        "independent_train_groups": len(dataset["cases"]),
        "distinct_replayed_source_topologies": len({tuple(row["selected_movements"])
            for row in dataset["source_inputs"]}),
        "groups": groups, "by_regime_and_size": strata,
        "eligible_complete_pairs": eligible_pairs, "pair_exclusions": exclusions,
        "source_pair_exclusions": source_pair_exclusions,
        "note": "Winners are observed fixed-route linear-tariff procedure outcomes, not global optima"}
