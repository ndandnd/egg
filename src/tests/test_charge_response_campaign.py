"""Pure prospective split, learning, and controller-guard checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math

import pytest

from egglab import charge_response_model as crm
from experiments import charge_response_campaign as campaign
from experiments import learning_campaign_stage2 as prior


def test_profile_order_and_reservations():
    cells = campaign.cells()
    assert len(cells) == 44 == len(set(cells))
    assert all(stage in campaign.SOURCES for _, stage in cells[:20])
    assert all(campaign.PROFILE[seed][0] == "train" and stage.endswith("_charge")
               for seed, stage in cells[20:32])
    assert all(campaign.PROFILE[seed][0] == "dev" and stage.endswith("_charge")
               for seed, stage in cells[32:40])
    assert all(campaign.PROFILE[seed][0] == "dev" and stage == "cold"
               for seed, stage in cells[40:])
    assert not set(campaign.RESERVED) & set(campaign.PROFILE)
    with pytest.raises(ValueError):
        campaign.case_for(2020)


def test_all_six_complete_pairs_required_before_fit():
    expected = [{"row_id": campaign.case_for(seed).name + "/" + source + "_charge",
                 "group": f"learning_s{seed}"}
                for seed in range(2022, 2028) for source in campaign.SOURCES]
    coverage = campaign.training_coverage(expected)
    assert coverage["complete_six_pairs"] and not coverage["missing_rows"]
    missing = campaign.training_coverage(expected[:-1])
    assert not missing["complete_six_pairs"]
    assert missing["missing_rows"] == [expected[-1]["row_id"]]
    duplicate = campaign.training_coverage(expected + expected[:1])
    assert not duplicate["complete_six_pairs"]


def test_ridge_uses_only_declared_train_samples():
    # Predicts a response residual, not a direct target solver objective.
    samples = []
    for group in range(6):
        for source in (0, 1):
            features = (1., 30.+group, 20.+group, 4.+source, 2.,
                        1.+source, float(source), (12.+4*group)/28.)
            samples.append({"split": "train", "group": f"g{group}",
                            "row_id": f"g{group}/s{source}", "features": features,
                            "residual_per_trip": float(source)-group/10.})
    model = crm.fit(samples)
    assert model.training_groups == tuple(f"g{k}" for k in range(6))
    assert len(model.weights) == len(crm.FEATURES)
    assert all(math.isfinite(x) for x in model.weights)
    with pytest.raises(ValueError, match="Nontraining"):
        crm.fit(samples + [{**samples[0], "split": "dev", "row_id": "dev/s0"}])
    with pytest.raises(ValueError, match="Duplicate"):
        crm.fit(samples + [samples[0]])


def test_old_projection_precedes_opposing_model_score():
    case = campaign.case_for(2028)
    target = prior.market(case, "target")
    @dataclass
    class Old:
        def propose_topology(self, _case, _prices):
            return ("edge_a",)
        def score(self, _case, _prices, plan):
            return 100.0 if plan["vehicles"][0]["movements"] == ["edge_b"] else -100.0
    candidates = [
        {"source": "source0", "row_id": "case/source0",
         "plan": {"vehicles": [{"movements": ["edge_a"]}]}},
        {"source": "source1", "row_id": "case/source1",
         "plan": {"vehicles": [{"movements": ["edge_b"]}]}}]
    chosen, raw = campaign.old_prior_choice(case, target, candidates, Old())
    assert chosen["source"] == "source0"
    assert raw == ["edge_a"]
    assert candidates[0]["old_topology_distance"] == 0
    assert candidates[1]["old_score"] > candidates[0]["old_score"]


def test_inference_rejects_dev_target_label_in_catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(campaign, "attempt", lambda _: tmp_path)
    monkeypatch.setattr(campaign, "frozen", lambda _: {})
    (tmp_path / "inference_launch.json").write_text("{}")
    rows = []
    for seed in campaign.PROFILE:
        for source in campaign.SOURCES:
            rows.append({"row_id": campaign.case_for(seed).name + "/" + source})
        if campaign.PROFILE[seed][0] == "train":
            for source in campaign.SOURCES:
                rows.append({"row_id": campaign.case_for(seed).name + "/" + source + "_charge"})
    rows.append({"row_id": campaign.case_for(2028).name + "/cold"})
    (tmp_path / "catalog.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="missing or target development labels"):
        campaign.infer_worker(tmp_path)


def test_dev_charge_worker_rejects_before_inference(tmp_path, monkeypatch):
    case = campaign.case_for(2028)
    market = prior.market(case, "target")
    monkeypatch.setattr(campaign, "attempt", lambda _: tmp_path)
    monkeypatch.setattr(campaign, "frozen", lambda _: {"design": {"groups": {
        case.name: {"case_identity": case.identity(),
                    "market_identities": {"target": market.identity()}}}}})
    dest = campaign.folder(tmp_path, 2028, "source0_charge")
    dest.mkdir(parents=True)
    (dest / "launch.json").write_text("{}")
    assert campaign.worker(tmp_path, 2028, "source0_charge") == 2
    failure = json.loads((dest / "exception.json").read_text())
    assert "before prospective inference" in failure["message"]


def test_failed_inference_receipt_is_not_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(campaign, "attempt", lambda _: tmp_path)
    receipt = {"status": "failed", "returncode": 1,
               "before_all_dev_target_cells": True, "elapsed_seconds": 2.0}
    (tmp_path / "inference_receipt.json").write_text(json.dumps(receipt))
    assert campaign.train_before_dev(tmp_path) == receipt
    assert not (tmp_path / "inference_launch.json").exists()


def test_resource_and_source_freeze_scope():
    design = campaign.design()
    assert design["declared_cells"] == 44
    assert 44*design["child_hard_seconds"] + design["trainer_hard_seconds"] < design[
        "controller_hard_seconds"] < 5700 < 6000
    assert design["charging_budget"]["threads"] == 1
    assert design["all_dev_choices_frozen_before_dev_lp_or_cold"]
    for required in ("src/egglab/charge_response_model.py",
                     "src/experiments/charge_response_campaign.py",
                     "src/tests/test_charge_response_campaign.py",
                     "src/cluster/charge_response.sbatch",
                     "research-20260930/learning-campaign/PROTOCOL_CHARGE_RESPONSE_LEARNING.md"):
        assert required in campaign.SOURCE_FILES
