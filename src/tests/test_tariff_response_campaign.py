"""Pure guards for the frozen-model tariff transfer batch."""
from __future__ import annotations

import json

import pytest

from experiments import tariff_response_campaign as campaign
from experiments import learning_campaign_stage2 as prior


def test_grouped_order_resource_cap_and_reservations():
    cells = campaign.cells()
    assert len(cells) == 44 == len(set(cells))
    assert all(stage in campaign.SOURCES for _, stage in cells[:8])
    assert all(stage not in campaign.SOURCES for _, stage in cells[8:])
    assert len({seed for seed, _ in cells}) == 4
    assert not set(campaign.PROFILE) & set(campaign.RESERVED)
    assert set(campaign.VARIANTS) == {"late", "day", "flat"}
    design = campaign.design()
    assert design["all_twelve_choices_before_target_outcomes"]
    assert design["declared_cells"] == 44
    assert 44*design["child_hard_seconds"] + design["inference_hard_seconds"] < \
        design["controller_hard_seconds"] < 5700 < 6000


def test_tariff_variants_have_prespecified_mean_and_distinct_availability():
    case = campaign.case_for(2032)
    markets = {v: campaign.target_market(case, v) for v in campaign.VARIANTS}
    assert len({m.identity() for m in markets.values()}) == 3
    assert all(len(m.a) == 30 and m.b == (1/900,)*30 for m in markets.values())
    assert all(abs(sum(m.a)/30 - 41/150) < 1e-12 for m in markets.values())
    assert markets["day"].a[10] == .10 and markets["day"].a[22] == .30
    assert markets["late"].a[10] == .30 and markets["late"].a[22] == .10
    assert len(set(markets["flat"].a)) == 1
    assert case.terminal_open_min == 1080
    with pytest.raises(ValueError):
        campaign.case_for(2020)


def test_majority_uses_only_archived_train_groups():
    result = campaign.train_majority()
    assert result["majority"] == "source1"
    assert result["counts"] == {"source0": 2, "source1": 4}
    assert set(result["training_group_winners"]) == {
        f"learning_s{seed}" for seed in range(2022, 2028)}
    assert "dev" not in result["source"]


def test_inference_rejects_any_target_result_in_catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(campaign, "attempt", lambda _: tmp_path)
    monkeypatch.setattr(campaign, "frozen", lambda _: {})
    (tmp_path / "inference_launch.json").write_text("{}")
    rows = [{"row_id": campaign.case_for(seed).name + "/" + source}
            for seed in campaign.PROFILE for source in campaign.SOURCES]
    rows.append({"row_id": campaign.case_for(2032).name + "/cold_late"})
    (tmp_path / "catalog.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    with pytest.raises(ValueError, match="no target outcomes"):
        campaign.infer_worker(tmp_path)


def test_failed_inference_receipt_is_not_retried(tmp_path):
    receipt = {"status": "failed", "returncode": 1,
               "before_all_target_cells": True, "elapsed_seconds": 3.0}
    (tmp_path / "inference_receipt.json").write_text(json.dumps(receipt))
    assert campaign.infer_before_targets(tmp_path) == receipt
    assert not (tmp_path / "inference_launch.json").exists()


def test_target_worker_rejects_before_inference(tmp_path, monkeypatch):
    case = campaign.case_for(2032)
    market = campaign.target_market(case, "late")
    monkeypatch.setattr(campaign, "attempt", lambda _: tmp_path)
    monkeypatch.setattr(campaign, "frozen", lambda _: {"design": {"groups": {
        case.name: {"case_identity": case.identity(),
                    "target_market_identities": {"late": market.identity()}}}}})
    dest = campaign.folder(tmp_path, 2032, "source0_charge_late")
    dest.mkdir(parents=True)
    (dest / "launch.json").write_text("{}")
    assert campaign.worker(tmp_path, 2032, "source0_charge_late") == 2
    failure = json.loads((dest / "exception.json").read_text())
    assert "before all variant inference" in failure["message"]


def test_input_freeze_pins_both_models_and_training_labels():
    paths = {str(path.relative_to(campaign.ROOT)) for path in campaign.INPUT_FILES}
    assert "result/learning_campaign/20260930-charge-response-attempt1/learned/model.json" in paths
    assert "result/learning_campaign/20260930-charge-response-attempt1/catalog.jsonl" in paths
    assert "result/learning_campaign/20260930-stage2-attempt1/learned/model.json" in paths
    hashes = campaign.input_hashes()
    assert set(hashes) == paths and all(len(value) == 64 for value in hashes.values())
