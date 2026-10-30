import json

import joblib
import numpy as np
import pytest

from egglab import physical_route_model_v2 as model
from experiments import pool_physical_route_training as pool
from experiments import train_physical_route_model_v2 as cli


def synthetic_dataset():
    groups = tuple(f"physical_v2_s{10000+i}" for i in range(32))
    samples = []
    for g, group in enumerate(groups):
        for source in ("source0", "source1"):
            x = np.zeros((16, len(model.FEATURES)))
            kind = np.arange(16) % 4
            x[np.arange(16), kind] = 1
            x[:, 4] = np.arange(16)/16
            x[:, 7] = (g+1)/33
            x[:, 8] = 0.5
            x[:, 11] = 0.1 if source == "source0" else 0.3
            x[:, -1] = 1
            y = np.asarray([(j+g+(source == "source1")) % 3 == 0 for j in range(16)], float)
            samples.append({"group": group, "source": source, "x": x, "y": y,
                "movement_ids": [f"m{j}" for j in range(16)], "trip_count": 4})
    return {"groups": groups, "samples": samples,
        "manifest_sha256": "a"*64, "table_hashes": {"cases.jsonl": "b"*64}}


def test_grouped_outer_inner_fit_partition_all_folds():
    groups = synthetic_dataset()["groups"]
    outer_sets = []
    for fold in range(4):
        fit, inner, outer = model.grouped_split(groups, fold)
        assert (len(fit), len(inner), len(outer)) == (20, 4, 8)
        assert not (set(fit) & set(inner) or set(fit) & set(outer) or set(inner) & set(outer))
        outer_sets.append(set(outer))
    assert set.union(*outer_sets) == set(groups)


def test_feature_policy_has_no_identity_outcome_or_solver_fields():
    assert len(model.FEATURES) == 17
    forbidden = ("id", "name", "hash", "cost", "bound", "certificate", "status", "winner")
    assert not any(token in name for name in model.FEATURES for token in forbidden)


def test_input_trip_count_ranking_budget_does_not_use_positive_count():
    sample = {"group": "g", "source": "source0", "y": np.asarray([1, 1, 1, 1, 1, 0]),
        "trip_count": 2}
    metric = model._metrics(sample["y"], np.asarray([.9, .8, .7, .6, .5, .1]),
        np.ones(6)/6, [sample])
    assert metric["topk_by_fleet"][0]["trip_count_input_k"] == 2
    assert metric["topk_by_fleet"][0]["observed_positive_edges"] == 5
    assert metric["input_trip_count_topk_recall_mean_by_fleet"] == pytest.approx(0.4)
    assert metric["weighted_positive_recall_at_fixed_half"] == pytest.approx(1.0)
    assert metric["weighted_negative_recall_at_fixed_half"] == pytest.approx(1.0)
    assert metric["positive_count"] == 5 and metric["negative_count"] == 1


def test_small_synthetic_fit_serializes_models_curves_predictions(tmp_path, monkeypatch):
    monkeypatch.setattr(model, "MLP_MAX_EPOCHS", 20)
    monkeypatch.setattr(model, "MLP_PATIENCE_CHECKS", 2)
    monkeypatch.setattr(model, "TREE_ITERATIONS", (2, 4))
    result, tree = model.run_fold(synthetic_dataset(), 4)
    assert result["fold"] == 1 and result["seed"] == 29
    assert (len(result["fit_groups"]), len(result["inner_groups"]), len(result["outer_groups"])) == (20, 4, 8)
    assert result["hist_boosted"]["selected_iterations"] in (2, 4)
    assert result["mlp32"]["selected_epoch"] in (10, 20)
    assert len(result["outer_predictions"]) == result["outer_edges"]
    assert result["outer_weights"][0]["fleet_weight"] == pytest.approx(1/16)
    assert set(result["outer_metrics"]) == {
        "constant", "kind_frequency", "logistic", "mlp32", "hist_boosted"}
    json.dumps(result, allow_nan=False)
    joblib.dump(tree, tmp_path / "tree.joblib")
    loaded = joblib.load(tmp_path / "tree.joblib")
    assert np.allclose(tree.predict_proba(np.zeros((3, len(model.FEATURES)))),
                       loaded.predict_proba(np.zeros((3, len(model.FEATURES)))))


def test_pool_compiles_only_exact_train_prefix_from_admitted_datasets(tmp_path):
    result = pool.build(tmp_path / "pool")  # Hash/table read only; no native replay or fit.
    assert result["independent_groups"] == 32 and result["source_fleets"] == 64
    data = model.load_pool(tmp_path / "pool", expected_manifest_sha256=result["manifest_sha256"])
    assert len(data["groups"]) == 32 and len(data["samples"]) == 64
    with pytest.raises(ValueError, match="hash"):
        model.load_pool(tmp_path / "pool", expected_manifest_sha256="0"*64)


def test_failed_task_marks_launch_and_refuses_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "EXPECTED_SKLEARN", cli.sklearn.__version__)
    monkeypatch.setattr(cli, "EXPECTED_JOBLIB", cli.joblib.__version__)
    monkeypatch.setattr(cli, "EXPECTED_NUMPY", cli.np.__version__)
    monkeypatch.setattr(cli, "EXPECTED_SCIPY", cli.scipy.__version__)
    def fail_pool(*args, **kwargs):
        raise ValueError("synthetic pool failure")
    monkeypatch.setattr(model, "load_pool", fail_pool)
    with pytest.raises(ValueError, match="synthetic pool failure"):
        cli.run(0, "a"*64, tmp_path)
    folder = tmp_path / "task00"
    assert json.loads((folder / "launch.json").read_text())["task_id"] == 0
    assert json.loads((folder / "receipt.json").read_text())["status"] == "failed"
    with pytest.raises(ValueError, match="immutable"):
        cli.run(0, "a"*64, tmp_path)


def test_pre_source_hash_failure_still_has_launch_and_failure_receipts(tmp_path, monkeypatch):
    def fail_commit(*args, **kwargs):
        raise RuntimeError("synthetic commit lookup failure")
    monkeypatch.setattr(cli.subprocess, "check_output", fail_commit)
    with pytest.raises(RuntimeError, match="synthetic commit lookup failure"):
        cli.run(1, "a"*64, tmp_path)
    folder = tmp_path / "task01"
    assert json.loads((folder / "launch.json").read_text())["task_id"] == 1
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["status"] == "failed" and receipt["source_commit"] is None
    assert "synthetic commit lookup failure" in (folder / "failure.json").read_text()
