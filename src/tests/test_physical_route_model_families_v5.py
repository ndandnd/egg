"""Small source-edge fixtures; no real TRAIN pool or native optimization."""
from __future__ import annotations

import json

import joblib
import numpy as np
import pytest

from egglab import physical_route_model_families_v5 as families
from egglab import physical_route_model_v3 as previous
from experiments import train_physical_route_model_families_v5 as cli
from experiments import computational_benchmark as base


def test_weight_scale_and_inner_only_tie_selection():
    w = np.array([.5, .25, .25])
    scaled = families._weighted_for_library(w)
    assert scaled.sum() == pytest.approx(3)
    assert scaled[0]/scaled[1] == pytest.approx(2)
    rows = [{"inner_metrics": {"weighted_log_loss": .2},
             "outer_metrics": {"weighted_log_loss": .8}},
            {"inner_metrics": {"weighted_log_loss": .3},
             "outer_metrics": {"weighted_log_loss": .1}}]
    assert families.select_candidate(rows) == 0
    rows[1]["inner_metrics"]["weighted_log_loss"] = .2
    assert families.select_candidate(rows) == 0  # fixed menu order
    with pytest.raises(ValueError, match="positive"):
        families._weighted_for_library(np.array([.5, 0.]))


def test_real_tiny_family_roundtrip_and_weighted_inner_checkpoint(tmp_path, monkeypatch):
    import catboost
    import xgboost
    rng = np.random.default_rng(5)
    x = rng.normal(size=(72, 17))
    inner = rng.normal(size=(28, 17))
    y = (x[:, 4]-.4*x[:, 7] > 0).astype(int)
    inner_y = (inner[:, 4]-.4*inner[:, 7] > 0).astype(int)
    w = np.linspace(1., 2., len(y)); w /= w.sum()
    iw = np.linspace(2., 1., len(inner_y)); iw /= iw.sum()
    monkeypatch.setattr(families, "MAX_ROUNDS", 80)
    monkeypatch.setattr(families, "EARLY_STOP_ROUNDS", 10)
    monkeypatch.setattr(families, "EXTRA_TREES", 20)
    for family, config in (("xgboost", {"max_depth": 3}),
                           ("catboost", {"depth": 4}),
                           ("extra_trees", {"min_samples_leaf": 5})):
        fitted, row = families.fit_candidate(family, config, x, y, w,
            inner, inner_y, iw, 17)
        assert row["thread_count"] == 1
        assert isinstance(row["fitted_parameters"], dict)
        assert row["inner_metrics"]["weighted_log_loss"] > 0
        p = families._probability(family, fitted, inner)
        if family == "xgboost":
            curve = row["checkpoint"]["inner_weighted_logloss_by_round"]
            best = row["checkpoint"]["best_iteration_zero_based"]
            assert best == int(np.argmin(curve))
            assert curve[best] == pytest.approx(
                row["inner_metrics"]["weighted_log_loss"], abs=1e-6)
            assert np.allclose(p, fitted.predict_proba(inner,
                iteration_range=(0, best+1))[:, 1])
            path = tmp_path / "xgb.json"; fitted.save_model(str(path))
            loaded = xgboost.XGBClassifier(n_jobs=1); loaded.load_model(str(path))
        elif family == "catboost":
            curve = row["checkpoint"]["inner_weighted_logloss_by_round"]
            best = row["checkpoint"]["best_iteration_zero_based"]
            assert best == int(np.argmin(curve))
            assert curve[best] == pytest.approx(
                row["inner_metrics"]["weighted_log_loss"], abs=1e-7)
            assert fitted.tree_count_ == row["checkpoint"]["selected_rounds"]
            path = tmp_path / "cat.cbm"; fitted.save_model(str(path))
            loaded = catboost.CatBoostClassifier(thread_count=1); loaded.load_model(str(path))
        else:
            path = tmp_path / "extra.joblib"; joblib.dump(fitted, path)
            loaded = joblib.load(path)
        assert path.is_file() and path.stat().st_size > 0
        assert np.allclose(p, families._probability(family, loaded, inner), atol=1e-12)


def test_outer_fields_not_used_for_fit_inner_or_family_promotion(monkeypatch):
    groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10128))
    _, _, outer_groups = previous.grouped_split(groups, 0)
    state = {"fitted_candidates": 0, "outer_accesses": 0}

    class Guarded(dict):
        def __getitem__(self, key):
            if key in ("x", "y", "movement_ids", "trip_count"):
                if state["fitted_candidates"] != 6:
                    raise AssertionError("Outer source used before all inner candidate decisions")
                state["outer_accesses"] += 1
            return super().__getitem__(key)

    samples = []
    for group in groups:
        x = np.zeros((4, 17)); x[:, :4] = np.eye(4)
        sample = {"group": group, "source": "source0", "x": x,
            "y": np.array([1., 0., 0., 0.]),
            "movement_ids": [0, 1, 2, 3], "trip_count": 1}
        samples.append(Guarded(sample) if group in outer_groups else sample)
    eligibility = [{"base_group": group, "observed_source_count": 1,
        "eligible_for_observed_source_supervision": True,
        "eligible_for_full_pair_supervision": False}
        for group in groups]

    class Dummy:
        best_iteration = 0
        tree_count_ = 1
        def predict_proba(self, x, **kwargs):
            return np.column_stack((np.full(len(x), .75), np.full(len(x), .25)))

    def fake_fit(family, config, *args):
        state["fitted_candidates"] += 1
        rank = {"xgboost": .3, "catboost": .2, "extra_trees": .1}[family]
        return Dummy(), {"family": family, "config": config,
            "inner_metrics": {"weighted_log_loss": rank},
            "fit_metrics": {"weighted_log_loss": .01},
            "fit_and_inner_seconds": 0., "thread_count": 1}

    monkeypatch.setattr(families, "fit_candidate", fake_fit)
    result = families.run_fold({"groups": groups, "samples": samples,
        "group_eligibility": eligibility, "manifest_sha256": "x",
        "table_hashes": {}}, 0)
    assert state["outer_accesses"] > 0
    assert result["inner_family_promotion"]["family"] == "extra_trees"
    assert set(result["outer_metrics"]) == set(families.FAMILIES) | {"inner_promoted"}
    assert result["no_outer_selection"] is True


def test_completed_candidate_persists_portable_model_and_hash(tmp_path):
    class FakePortable:
        def save_model(self, path):
            from pathlib import Path
            Path(path).write_text("tiny candidate")

    progress = cli.Progress(tmp_path)
    progress.start_candidate("xgboost", 0, {"max_depth": 3})
    assert json.loads((progress.path / "xgboost_candidate0_start.json").read_text())[
        "config"] == {"max_depth": 3}
    evidence = progress.candidate("xgboost", 0, FakePortable(),
        {"family": "xgboost", "config": {"max_depth": 3},
         "inner_metrics": {"weighted_log_loss": .2}})
    model_path = tmp_path / evidence["path"]
    assert evidence["sha256"] == base.sha(model_path)
    assert progress.hashes()[model_path.name] == evidence["sha256"]
    assert json.loads((progress.path / "xgboost_candidate0_inner.json").read_text())[
        "saved_model"]["sha256"] == evidence["sha256"]


def test_missing_dependency_records_typed_failure_and_no_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "versions", lambda: {"sklearn": cli.EXPECTED_SKLEARN,
        "joblib": cli.EXPECTED_JOBLIB, "numpy": cli.EXPECTED_NUMPY,
        "scipy": cli.EXPECTED_SCIPY, "xgboost": cli.EXPECTED_XGBOOST,
        "catboost": cli.EXPECTED_CATBOOST})
    actual_import = cli.importlib.import_module
    def missing(name):
        if name == "catboost":
            raise ModuleNotFoundError("synthetic missing catboost")
        return actual_import(name)
    monkeypatch.setattr(cli.importlib, "import_module", missing)
    with pytest.raises(ModuleNotFoundError, match="synthetic missing"):
        cli.run(0, cli.POOL_SHA, tmp_path)
    folder = tmp_path / "task00"
    receipt = json.loads((folder / "receipt.json").read_text())
    assert (folder / "launch.json").exists()
    assert receipt["status"] == "failed"
    assert json.loads((folder / "failure.json").read_text())["type"] == "ModuleNotFoundError"
    with pytest.raises(ValueError, match="immutable"):
        cli.run(0, cli.POOL_SHA, tmp_path)
