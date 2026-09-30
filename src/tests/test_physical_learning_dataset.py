"""Synthetic completed-shard fixtures; no native optimizer or live outcomes."""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
import json

import pytest

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import physical_learning_dataset as adapter
from experiments import computational_benchmark as base
from experiments import physical_learning_campaign as campaign
from experiments import physical_learning_dataset as cli


@pytest.fixture
def completed_shard(tmp_path):
    attempt = tmp_path / "physical_learning/20260930-shard00-attempt1"
    attempt.mkdir(parents=True)
    manifest = campaign.manifest(0)
    base.save_new(attempt / "manifest.json", manifest)
    base.save_new(attempt / "frozen.json", {"protocol": campaign.PROTOCOL,
        "source_commit": "synthetic-fixture-commit",
        "source_hashes": {name: "a"*64 for name in campaign.SOURCE_FILES},
        "manifest_sha256": base.sha(attempt / "manifest.json")})
    rows = []
    for base_id, stage in campaign.cells(0):
        case = physical.make_case(base_id)
        source = stage if stage in campaign.SOURCES else stage.split("_charge_", 1)[0]
        kind = stage if stage in campaign.SOURCES else stage.rsplit("_", 1)[-1]
        market = physical.market(case, kind)
        plan = physical.make_witness(case, base_id)
        plan.update(formulation=pf.FORMULATION, native_matrix=pf.NATIVE_MATRIX,
                    extraction_policy=pf.EXTRACTION_POLICY)
        replay = nr.replay_native(case, plan)
        exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
        receipt = {"returncode": 0, "hard_timeout": False, "elapsed_seconds": 1.5}
        dest = attempt / case.name / "state0" / stage
        dest.mkdir(parents=True)
        base.save_new(dest / "receipt.json", receipt)
        if stage in campaign.SOURCES:
            base.save_new(dest / "raw_result.json", {"result": {
                "status": "budget_exhausted", "columns": [{"plan": plan}]}})
            base.save_new(dest / "result.json", {"assessment": {}})
        else:
            base.save_new(dest / "direct_rescore.json", {
                "source_row_id": case.name + "/" + source,
                "source_plan_hash": nr.digest(plan), "case_identity": case.identity(),
                "market_identity": market.identity(), "objective_exact": exact})
            base.save_new(dest / "fixed_charge.json", {"status": "replayed",
                "source_plan_hash": nr.digest(plan), "case_identity": case.identity(),
                "market_identity": market.identity(), "selected_movements": sorted(
                    mid for v in plan["vehicles"] for mid in v["movements"]),
                "plan": plan, "plan_hash": nr.digest(plan), "replay": replay,
                "objective_exact": exact, "native_stats": {"status": "OPTIMAL"}})
        label = {"status": "returned", "receipt": receipt, "feasible": True,
            "optimality": "unknown", "plan": plan, "plan_hash": nr.digest(plan),
            "ops_cost": replay["ops_cost"], "load": replay["load"],
            "objective_exact": exact, "upper_exact": exact, "lower_exact": None,
            "elapsed_seconds": 1.5,
            "native_status": "budget_exhausted" if stage in campaign.SOURCES else "OPTIMAL"}
        if stage in campaign.SOURCES:
            label["bounds_replay"] = {"global_certificate_replayed": False,
                                       "mixture_replayed": False}
        else:
            label["source_plan_hash"] = nr.digest(plan)
        rows.append({"row_id": case.name + "/" + stage,
            "base_group": f"physical_v2_s{base_id}", "base_id": base_id,
            "split": "train", "physical_profile": physical.assignment(base_id),
            "case": asdict(case), "case_identity": case.identity(),
            "market": asdict(market), "market_identity": market.identity(),
            "market_name": kind, "market_role": "source" if stage in campaign.SOURCES else "target",
            "arm": "source" if stage in campaign.SOURCES else "fixed_source_charge",
            "source_market": None if stage in campaign.SOURCES else source,
            "label": label})
    (attempt / "catalog.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    base.save_new(attempt / "summary.json", {"declared_cells": 64,
        "accounted_cells": 64, "shard": 0})
    base.save_new(attempt.with_name(attempt.name + ".slurm_wrapper_receipt.123.json"), {
        "shard": 0, "returncode": 0, "freeze_returncode": 0,
        "preflight_returncode": 0, "controller_returncode": 0})
    return attempt


def test_completed_fixture_ingests_and_compiles_without_training(completed_shard, tmp_path):
    data = adapter.ingest_attempt(completed_shard)
    assert len(data["cases"]) == 8
    assert len(data["source_inputs"]) == len(data["source_outcomes"]) == 16
    assert len(data["target_inputs"]) == len(data["target_outcomes"]) == 48
    assert all(row["curved_optimality_uncertified"] and not row["certified_for_reported_objective"]
               for row in data["target_outcomes"])
    assert all(not row["provisional_after_native_limit"] for row in data["target_outcomes"])
    assert all(row["source_market_lower_exact"] is None for row in data["source_outcomes"])
    health = adapter.health(data)
    assert health["independent_train_groups"] == 8
    assert len(health["eligible_complete_pairs"]) == 24
    assert not health["pair_exclusions"]
    assert all(row["winner"] == "tie" for row in health["eligible_complete_pairs"])
    out = tmp_path / "dataset"
    receipt = cli.compile_dataset([completed_shard], out)
    assert receipt["independent_training_groups"] == 8
    assert receipt["pre_target_input_containers"]["future_numeric_projection_required"]
    assert (out / "target_outcomes.jsonl").is_file()
    with pytest.raises(ValueError, match="already exists"):
        cli.compile_dataset([completed_shard], out)


def test_incomplete_or_cross_shard_catalog_rejected(completed_shard):
    file = completed_shard / "catalog.jsonl"
    rows = file.read_text().splitlines()
    file.write_text("\n".join(rows[:-1]) + "\n")
    with pytest.raises(adapter.ExcludedShard, match="64 cells"):
        adapter.ingest_attempt(completed_shard)


def test_source_lineage_and_wrapper_phases_rejected(completed_shard):
    wrapper = next(completed_shard.parent.glob(completed_shard.name + ".slurm_wrapper_receipt.*.json"))
    data = json.loads(wrapper.read_text())
    data["preflight_returncode"] = 2
    wrapper.write_text(json.dumps(data))
    with pytest.raises(adapter.ExcludedShard, match="Wrapper receipt"):
        adapter.ingest_attempt(completed_shard)
    data["preflight_returncode"] = 0
    wrapper.write_text(json.dumps(data))
    extra = wrapper.with_name(wrapper.name.replace(".123.json", ".124.json"))
    extra.write_text(json.dumps({**data, "returncode": 1}))
    with pytest.raises(adapter.ExcludedShard, match="Wrapper receipt"):
        adapter.ingest_attempt(completed_shard)


def test_mixed_replayed_and_censored_labels_compile_with_typed_missing_status(completed_shard, tmp_path):
    catalog = completed_shard / "catalog.jsonl"
    rows = [json.loads(line) for line in catalog.read_text().splitlines()]
    target = next(row for row in rows if row["row_id"].endswith("/source1_charge_day"))
    label = target["label"]
    label.update(feasible=False, plan=None, plan_hash=None, ops_cost=None, load=None,
                 objective_exact=None, upper_exact=None, native_status=None)
    evidence = completed_shard / target["case"]["name"] / "state0/source1_charge_day/fixed_charge.json"
    evidence.unlink()
    catalog.write_text("".join(json.dumps(row) + "\n" for row in rows))
    out = tmp_path / "mixed_dataset"
    cli.compile_dataset([completed_shard], out)
    health = json.loads((out / "health.json").read_text())
    assert len(health["pair_exclusions"]) == 1
    assert len(health["eligible_complete_pairs"]) == 23
    assert any("not_reported" in stratum["target_native_status_counts"]
               for stratum in health["by_regime_and_size"].values())
