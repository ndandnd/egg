"""Small synthetic guards for the prospective optimization-budget extension."""
from __future__ import annotations

import json

import numpy as np
import pytest

from egglab import physical_route_model_budget_v4 as budget
from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous
from experiments import train_physical_route_model_budget_v4 as cli
from experiments import computational_benchmark as base


def fixture_arrays():
    rng = np.random.default_rng(9)
    x = rng.normal(size=(36, 17))
    y = (x[:, 4] + .5*x[:, 5] > 0).astype(float)
    w = np.ones(len(y))/len(y)
    return x, y, w


def test_first_300_epoch_trajectory_matches_frozen_implementation():
    x, y, w = fixture_arrays()
    old = frozen._mlp_fit(x, y, w, x, y, w, 17)
    assert old["stopped_epoch"] == 300 and old["selected_epoch"] == 300

    class StopAtAnchor(Exception):
        pass

    class Recorder:
        anchor = None
        curve = []
        def mlp_curve_point(self, row):
            self.curve.append(row)
        def mlp_anchor(self, row):
            self.anchor = row
            raise StopAtAnchor
        def mlp_best(self, row):
            assert row["epoch"] % 10 == 0 and row["epoch"] <= 300
        def mlp_selection(self, row):
            raise AssertionError("No selection should run before interrupted anchor")

    recorder = Recorder()
    with pytest.raises(StopAtAnchor):
        budget.fit_mlp(x, y, w, x, y, w, 17, recorder)
    assert recorder.anchor["epoch"] == 300
    assert len(recorder.curve) == 30
    for old_row, new_row in zip(old["curve"], recorder.curve):
        assert old_row["epoch"] == new_row["epoch"]
        assert old_row["inner"]["weighted_log_loss"] == pytest.approx(
            new_row["inner"]["weighted_log_loss"], abs=1e-14)
    for key in ("W1", "b1", "W2", "b2"):
        assert np.allclose(np.asarray(recorder.anchor["params"][key]),
                           np.asarray(old["params"][key]), atol=1e-14, rtol=0)


def test_inner_patience_can_select_earlier_checkpoint_and_report_missing_anchor():
    x, y, w = fixture_arrays()
    result = budget.fit_mlp(x, y, w, x, 1-y, w, 29)
    assert result["selected_epoch"] < result["stopped_epoch"] < budget.MLP_MAX_EPOCHS
    assert result["anchor_at_300"] is None
    assert budget.choose_inner(result["curve"], index="epoch",
        min_improvement=1e-8)["epoch"] == result["selected_epoch"]
    assert budget.MLP_MAX_EPOCHS == 1200
    assert budget.TREE_ITERATIONS == (100, 200, 400, 800)
    assert frozen.MLP_MAX_EPOCHS == 300 and frozen.TREE_ITERATIONS[-1] == 200
    curve = [{"iterations": i, "inner": {"weighted_log_loss": loss}}
             for i, loss in ((100, .3), (200, .2), (400, .21), (800, .22))]
    assert budget.choose_inner(curve, index="iterations")["iterations"] == 200


def test_outer_rows_remain_unread_until_both_inner_selections(monkeypatch):
    groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10128))
    _, _, outer_groups = previous.grouped_split(groups, 0)
    stage = {"inner_done": False, "outer_reads": 0}

    class Guarded(dict):
        def __getitem__(self, key):
            if key in ("x", "y", "movement_ids", "trip_count"):
                if not stage["inner_done"]:
                    raise AssertionError("Outer source read before inner checkpoint selection")
                stage["outer_reads"] += 1
            return super().__getitem__(key)

    samples = []
    for group in groups:
        x = np.zeros((4, 17))
        x[:, :4] = np.eye(4)
        sample = {"group": group, "source": "source0", "x": x,
            "y": np.array([1., 0., 0., 0.]), "movement_ids": [0, 1, 2, 3],
            "trip_count": 1}
        samples.append(Guarded(sample) if group in outer_groups else sample)
    eligibility = [{"base_group": group, "observed_source_count": 1,
        "eligible_for_observed_source_supervision": True,
        "eligible_for_full_pair_supervision": False}
        for group in groups]

    def fake_mlp(*args):
        return {"selected_epoch": 300, "stopped_epoch": 300,
            "params": {"W1": np.zeros((17, 32)).tolist(), "b1": np.zeros(32).tolist(),
                "W2": np.zeros(32).tolist(), "b2": 0.0},
            "curve": [], "selected_inner_log_loss": .5, "anchor_at_300": {}}

    class FakeTree:
        def predict_proba(self, x):
            return np.column_stack((np.full(len(x), .75), np.full(len(x), .25)))

    def fake_tree(*args):
        stage["inner_done"] = True
        return FakeTree(), {"selected_iterations": 200,
            "selected_inner_log_loss": .5, "curve": [], "anchor_at_200": {}}

    monkeypatch.setattr(budget, "fit_mlp", fake_mlp)
    monkeypatch.setattr(budget, "fit_tree", fake_tree)
    result, _ = budget.run_fold({"groups": groups, "samples": samples,
        "group_eligibility": eligibility, "manifest_sha256": "x",
        "table_hashes": {}}, 0)
    assert stage["outer_reads"] > 0
    assert result["no_outer_selection"] is True
    assert result["outer_groups"] == outer_groups


def test_failed_task_preserves_launch_and_progress_without_retry(tmp_path, monkeypatch):
    from egglab import physical_route_model_v3 as admitted
    monkeypatch.setattr(cli, "versions", lambda: {"sklearn": cli.EXPECTED_SKLEARN,
        "joblib": cli.EXPECTED_JOBLIB, "numpy": cli.EXPECTED_NUMPY,
        "scipy": cli.EXPECTED_SCIPY})
    monkeypatch.setattr(admitted, "load_pool", lambda *args, **kwargs: {})
    def fail_after_inner_progress(dataset, task_id, progress):
        progress.mlp_curve_point({"epoch": 10, "inner": {"weighted_log_loss": .2}})
        raise RuntimeError("synthetic stopped fit")
    monkeypatch.setattr(cli.model, "run_fold", fail_after_inner_progress)
    with pytest.raises(RuntimeError, match="synthetic stopped fit"):
        cli.run(0, cli.POOL_SHA, tmp_path)
    folder = tmp_path / "task00"
    receipt = json.loads((folder / "receipt.json").read_text())
    assert (folder / "launch.json").exists()
    assert receipt["status"] == "failed"
    assert "mlp_curve_epoch0010.json" in receipt["inner_progress_hashes"]
    assert json.loads((folder / "failure.json").read_text())["type"] == "RuntimeError"
    with pytest.raises(ValueError, match="immutable"):
        cli.run(0, cli.POOL_SHA, tmp_path)


def test_completed_inner_tree_candidate_has_saved_model_hash(tmp_path):
    progress = cli.Progress(tmp_path)
    row = {"iterations": 200, "fit": {"weighted_log_loss": .1},
        "inner": {"weighted_log_loss": .2}, "fit_and_inner_seconds": .3}
    progress.tree_candidate(200, {"synthetic_tree": True}, row)
    checkpoint = progress.path / "tree_candidate_0200.json"
    model_file = progress.path / "tree_candidate_0200.joblib"
    assert json.loads(checkpoint.read_text())["model_sha256"] == base.sha(model_file)
    assert progress.hashes()[model_file.name] == base.sha(model_file)
