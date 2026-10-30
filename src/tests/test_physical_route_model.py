import json

import numpy as np
import pytest

from egglab import physical_route_model as model
from experiments import train_physical_route_model as cli


def synthetic_dataset():
    groups = tuple(f"physical_v2_s{10000+i}" for i in range(8))
    samples = []
    for g, group in enumerate(groups):
        for source in ("source0", "source1"):
            x = np.zeros((12, len(model.FEATURES)))
            x[:, 0] = np.arange(12) % 4 == 0
            x[:, 1] = np.arange(12) % 4 == 1
            x[:, 2] = np.arange(12) % 4 == 2
            x[:, 3] = np.arange(12) % 4 == 3
            x[:, 4] = np.arange(12)/12
            x[:, 7] = (g+1)/10
            x[:, -1] = 1
            y = np.asarray([(j+g+(source == "source1")) % 3 == 0 for j in range(12)], float)
            samples.append({"group": group, "source": source,
                "x": x, "y": y, "movement_ids": [f"m{j}" for j in range(len(y))],
                "movement_count": len(y)})
    return {"groups": groups, "samples": samples,
        "receipt_sha256": "a"*64, "table_hashes": {"cases.jsonl": "b"*64}}


def test_all_outer_folds_keep_source_variants_together():
    groups = synthetic_dataset()["groups"]
    held_sets = []
    for fold in range(4):
        train, held = model.split_groups(groups, fold)
        assert len(train) == 6 and len(held) == 2
        assert not set(train) & set(held)
        held_sets.append(set(held))
    assert set.union(*held_sets) == set(groups)
    assert sum(len(s) for s in held_sets) == 8


def test_feature_policy_is_explicit_numeric_pre_source_only():
    assert len(model.FEATURES) == 17
    assert model.FEATURES[:4] == model.KINDS
    forbidden = ("id", "name", "hash", "cost", "bound", "certificate", "status", "winner")
    assert not any(token in feature for feature in model.FEATURES for token in forbidden)


def test_fold_fit_serialization_and_outer_group_evaluation(monkeypatch):
    monkeypatch.setattr(model, "EPOCHS", 20)
    result = model.run_fold(synthetic_dataset(), 4)
    assert result["fold"] == 1 and result["seed"] == 29
    assert len(result["train_groups"]) == 6 and len(result["heldout_groups"]) == 2
    assert not set(result["train_groups"]) & set(result["heldout_groups"])
    assert result["train_source_fleets"] == 12 and result["heldout_source_fleets"] == 4
    assert set(result["heldout_metrics"]) == {"constant", "kind_frequency", "linear", "mlp16"}
    assert len(result["linear_model"]["weights"]) == len(model.FEATURES)
    assert np.asarray(result["mlp16_model"]["W1"]).shape == (len(model.FEATURES), 16)
    assert set(result["heldout_per_group_source"]) == set(result["heldout_groups"])
    assert len(result["heldout_predictions"]) == result["heldout_movement_rows"]
    assert result["training_config"]["epochs"] == 20
    json.dumps(result, allow_nan=False)


def test_training_only_preprocessing_excludes_outer_group():
    d = synthetic_dataset()
    train, held = model.split_groups(d["groups"], 0)
    samples = [s for s in d["samples"] if s["group"] in train]
    x, _, _ = model._stack(samples)
    mean, scale = model.preprocessing(x)
    # The energy feature differs by group; adding an extreme held-out value
    # cannot alter a transform fitted only on training samples.
    before = mean.copy(), scale.copy()
    for sample in d["samples"]:
        if sample["group"] in held:
            sample["x"][:, 7] = 9999
    x_after, _, _ = model._stack([s for s in d["samples"] if s["group"] in train])
    after = model.preprocessing(x_after)
    assert all(np.array_equal(a, b) for a, b in zip(before, after))


def test_declared_task_grid_and_wrapper_budget():
    with pytest.raises(ValueError, match="Undeclared"):
        model.run_fold(synthetic_dataset(), 12)
    wrapper = (cli.base.ROOT / "src/cluster/physical_route_model.sbatch").read_text()
    assert "--array=0-11%4" in wrapper and "--time=00:30:00" in wrapper
    assert "--cpus-per-task=1" in wrapper and "--mem=8G" in wrapper
    assert "--no-requeue" in wrapper and "--exclude=scaglione-compute-01" in wrapper


def test_immutable_task_serialization_with_synthetic_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(model, "EPOCHS", 20)
    monkeypatch.setattr(model, "load_dataset", synthetic_dataset)
    summary = cli.run(0, output_root=tmp_path)
    result = json.loads((tmp_path / "task00/result.json").read_text())
    receipt = json.loads((tmp_path / "task00/receipt.json").read_text())
    assert summary["task_id"] == 0
    assert result["heldout_groups"] == ["physical_v2_s10000", "physical_v2_s10004"]
    assert receipt["result_sha256"] == cli.base.sha(tmp_path / "task00/result.json")
    assert receipt["dataset_receipt_sha256"] == "a"*64
    assert (tmp_path / "task00/launch.json").is_file()
    assert len(result["heldout_predictions"]) == result["heldout_movement_rows"]
    with pytest.raises(ValueError, match="immutable"):
        cli.run(0, output_root=tmp_path)


def test_failed_fit_keeps_launch_failure_and_cannot_retry(tmp_path, monkeypatch):
    def fail_load():
        raise ValueError("deliberate input failure")
    monkeypatch.setattr(model, "load_dataset", fail_load)
    with pytest.raises(ValueError, match="deliberate input failure"):
        cli.run(1, output_root=tmp_path)
    folder = tmp_path / "task01"
    assert json.loads((folder / "launch.json").read_text())["task_id"] == 1
    assert json.loads((folder / "receipt.json").read_text())["status"] == "failed"
    assert "deliberate input failure" in (folder / "failure.json").read_text()
    with pytest.raises(ValueError, match="immutable"):
        cli.run(1, output_root=tmp_path)
