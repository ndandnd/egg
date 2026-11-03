"""Pure generator, split, replay and resumability guards for label shard zero."""
from __future__ import annotations

import json

import pytest

from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from experiments import physical_learning_campaign as campaign


def test_registry_and_full_factorial_are_grouped_without_old_collisions():
    assert len(physical.TRAIN_IDS) == 128
    assert len(physical.DEV_IDS) == len(physical.TEST_IDS) == 32
    assert not (set(physical.TRAIN_IDS) | set(physical.DEV_IDS) | set(physical.TEST_IDS)) \
        & set(physical.RESERVED_OLD)
    assert set(physical.shard_ids(0)) == set(range(10000, 10008))
    assert set(physical.shard_ids(15)) == set(range(10120, 10128))
    with pytest.raises(ValueError):
        physical.shard_ids(16)
    with pytest.raises(ValueError):
        physical.make_case(2004)
    crossed = {(physical.assignment(base_id)["profile"]["name"],
                physical.assignment(base_id)["services"],
                physical.assignment(base_id)["consumption_kwh_per_km"],
                physical.assignment(base_id)["depot_min_gap_minutes"])
               for base_id in physical.TRAIN_IDS[:54]}
    assert len(crossed) == 3*2*3*3


def test_first_eight_pure_witnesses_replay_and_metadata_is_explicit():
    counts = {}
    for base_id in physical.shard_ids(0):
        spec = physical.assignment(base_id)
        case = physical.make_case(base_id)
        plan = physical.make_witness(case, base_id)
        replay = nr.replay_native(case, plan)
        profile = spec["profile"]
        counts[profile["name"]] = counts.get(profile["name"], 0) + 1
        assert profile["upper_kwh"] - profile["reserve_kwh"] == pytest.approx(
            profile["operating_span_kwh"])
        assert case.battery_kwh == profile["upper_kwh"]
        assert len(plan["vehicles"]) == len(case.trips)//2
        assert replay["ops_cost"] == len(plan["vehicles"])*case.vehicle_cost
        assert physical.metadata(base_id)["case_identity"] == case.identity()
    assert sorted(counts.values()) == [2, 3, 3]


def test_motion_energy_and_depot_idle_assumptions():
    assert physical.drive_energy_kwh(30, 1.7) == pytest.approx(30*36/60*1.7)
    assert physical._travel("A", "D", 1.45) == (4, pytest.approx(4*36/60*1.45))
    assert physical.DEPOT_DWELL_IDLE_KW == 0.0
    assert physical.IDLE_KW == 1.2


def test_manifest_materializes_only_eight_train_groups_and_64_cells():
    design = campaign.manifest(0)
    assert design["materialized_split"] == "train"
    assert len(design["groups"]) == 8
    assert design["selected_base_ids"] == list(physical.shard_ids(0))
    assert len(design["cell_order"]) == 64
    assert all(stage in campaign.SOURCES for _, stage in campaign.cells(0)[:16])
    assert all(stage not in campaign.SOURCES for _, stage in campaign.cells(0)[16:])
    assert 64*design["child_hard_seconds"] < design["controller_hard_seconds"] < 6900 < 7200
    assert design["no_model_fit"] and design["no_dev_or_test_materialization"]
    assert design["target_fixed_charge_budget"]["threads"] == 1


def test_attempt_is_shard_exclusive_and_source_hash_scope():
    assert campaign.attempt(0).name == "20260930-shard00-attempt1"
    assert campaign.attempt(15).name == "20260930-shard15-attempt1"
    with pytest.raises(ValueError):
        campaign.attempt(0, campaign.ROOT / "result/physical_learning/other")
    assert len(set(campaign.SOURCE_FILES)) == len(campaign.SOURCE_FILES)
    for name in ("src/egglab/physical_learning_cases.py",
                 "src/experiments/physical_learning_campaign.py",
                 "src/tests/test_physical_learning_campaign.py",
                 "src/cluster/physical_learning.sbatch",
                 "research-20260930/learning-campaign/PROTOCOL_PHYSICAL_LEARNING.md"):
        assert name in campaign.SOURCE_FILES


def test_failed_source_receipt_preserves_status_time_without_fabricated_plan(tmp_path):
    base_id = physical.shard_ids(0)[0]
    dest = campaign.folder(tmp_path, base_id, "source0")
    dest.mkdir(parents=True)
    (dest / "receipt.json").write_text(json.dumps({"hard_timeout": True,
        "returncode": 124, "elapsed_seconds": 100.1}))
    row = campaign.label(tmp_path, base_id, "source0")
    assert row["status"] == "hard_timeout" and row["elapsed_seconds"] == 100.1
    assert not row["feasible"] and row["plan"] is None and row["lower_exact"] is None


def test_charging_cell_without_source_records_failure_and_no_hidden_solve(tmp_path, monkeypatch):
    base_id = physical.shard_ids(0)[0]
    case = physical.make_case(base_id)
    market = physical.market(case, "late")
    monkeypatch.setattr(campaign, "attempt", lambda shard, path=None: tmp_path)
    monkeypatch.setattr(campaign, "frozen", lambda shard, path=None: (None, {"groups": {
        case.name: {"case_identity": case.identity(),
                    "market_identities": {"late": market.identity()}}}}))
    dest = campaign.folder(tmp_path, base_id, "source0_charge_late")
    dest.mkdir(parents=True)
    (dest / "launch.json").write_text("{}")
    assert campaign.worker(0, tmp_path, base_id, "source0_charge_late") == 2
    failure = json.loads((dest / "exception.json").read_text())
    assert "Missing or duplicate source catalog row" in failure["message"]


def test_worker_rejects_reserved_split_before_materializing_case(tmp_path, monkeypatch):
    monkeypatch.setattr(campaign, "attempt", lambda shard, path=None: tmp_path)
    original = physical.make_case
    def guarded_make_case(base_id):
        if base_id == 30000:
            raise AssertionError("Test case was materialized")
        return original(base_id)
    monkeypatch.setattr(physical, "make_case", guarded_make_case)
    with pytest.raises(ValueError, match="outside the selected training shard"):
        campaign.worker(0, tmp_path, 30000, "source0")
