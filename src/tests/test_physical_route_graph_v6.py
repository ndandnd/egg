"""Tiny synthetic graph/selection fixtures; no TRAIN fit or native optimizer."""
from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from egglab import physical_route_graph_v6 as graph
from egglab import physical_route_model_v3 as previous
from experiments import train_physical_route_graph_v6 as cli
from experiments import probe_physical_route_graph_v6 as probe


def sample(group="fixture", source="source0", seed=5):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(6, 17)); x[:, -1] = 1.
    return {"group": group, "source": source, "x": x,
        "y": (x[:, 0] > 0).astype(float), "movement_ids": [10, 11, 12, 13, 14, 15],
        "trip_count": 2, "graph": {"src": np.array([0, 0, 1, 1, 1, 2]),
            "dst": np.array([1, 2, 2, 2, 3, 3]), "nodes": 4, "trip_ids": (7, 19)}}


def test_declared_parallel_movements_and_separate_depot_endpoints():
    case = SimpleNamespace(trips=[SimpleNamespace(id=19), SimpleNamespace(id=7)],
        movements=[SimpleNamespace(before=None, after=7), SimpleNamespace(before=7, after=19),
                   SimpleNamespace(before=7, after=19), SimpleNamespace(before=19, after=None)])
    topology = graph.topology(case)
    assert topology["trip_ids"] == (7, 19)
    assert topology["nodes"] == 4
    assert topology["src"].tolist() == [0, 1, 1, 2]
    assert topology["dst"].tolist() == [1, 2, 2, 3]
    case.movements.append(SimpleNamespace(before=None, after=None))
    with pytest.raises(ValueError, match="neither"):
        graph.topology(case)


@pytest.mark.parametrize("family,count", [("mean_message", 17857), ("graph_attention", 17985)])
def test_disconnected_graphs_edge_permutations_and_npz_roundtrip(family, count, tmp_path):
    graph.configure_cpu(); torch.manual_seed(17)
    model = graph.GraphScorer(family)
    assert model.parameter_count == count <= graph.PARAMETER_CEILING
    first, second = sample("a"), sample("b", seed=6)
    mean, scale = np.zeros(17), np.ones(17)
    one = graph.batches([first], mean, scale, labelled=False)
    joined = graph.batches([first, second], mean, scale, labelled=False)
    reference = graph.predict(model, one)
    assert graph.predict(model, joined)[:6] == pytest.approx(reference, abs=1e-12)
    second["x"] *= 100.
    assert graph.predict(model, graph.batches([first, second], mean, scale,
        labelled=False))[:6] == pytest.approx(reference, abs=1e-12)
    shuffled = copy.deepcopy(first); permutation = np.array([4, 2, 0, 5, 1, 3])
    shuffled["x"] = shuffled["x"][permutation]
    shuffled["graph"]["src"] = shuffled["graph"]["src"][permutation]
    shuffled["graph"]["dst"] = shuffled["graph"]["dst"][permutation]
    assert graph.predict(model, graph.batches([shuffled], mean, scale,
        labelled=False)) == pytest.approx(reference[permutation], abs=1e-12)
    path = tmp_path / "weights.npz"
    graph.save_model(model, path)
    assert graph.predict(graph.restore_model(path), one) == pytest.approx(reference, abs=1e-12)
    with pytest.raises(FileExistsError):
        graph.save_model(model, path)
    with np.load(path, allow_pickle=False) as archive:
        assert str(archive["policy"]) == graph.POLICY


def test_attention_aggregation_gradients_and_equal_initial_pooling():
    graph.configure_cpu()
    messages = torch.tensor([[.2, -.4], [1.2, .3], [-.7, .9]], dtype=graph.DTYPE, requires_grad=True)
    attention = torch.tensor([.3, -.2], dtype=graph.DTYPE, requires_grad=True)
    indexes = torch.tensor([1, 1, 2])
    assert torch.autograd.gradcheck(lambda m, a: graph._aggregate(m, indexes, 4, a),
                                   (messages, attention), eps=1e-6, atol=1e-5)
    assert torch.allclose(graph._aggregate(messages, indexes, 4),
        graph._aggregate(messages, indexes, 4, torch.zeros(2, dtype=graph.DTYPE)))
    torch.manual_seed(17); mean = graph.GraphScorer("mean_message")
    torch.manual_seed(17); attention_model = graph.GraphScorer("graph_attention")
    batch = graph.batches([sample()], np.zeros(17), np.ones(17), labelled=True)
    assert torch.equal(mean(batch[0]), attention_model(batch[0]))
    loss = F.binary_cross_entropy_with_logits(attention_model(batch[0]), batch[0]["y"])
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in attention_model.parameters())
    assert any(float(p.grad.abs().sum()) > 0 for p in attention_model.attention_in)


@pytest.mark.parametrize("family", graph.FAMILIES)
def test_tiny_training_selected_checkpoint_and_saved_progress(family, tmp_path, monkeypatch):
    monkeypatch.setattr(graph, "MAX_EPOCHS", 45)
    monkeypatch.setattr(graph, "PATIENCE", 8)
    fit = [sample("fit0", "source0", 5), sample("fit0", "source1", 6), sample("fit1", seed=7)]
    inner = [sample("inner", seed=8)]
    for item in fit+inner:
        item["x"][:, 1:16] = 0.  # one clean synthetic pre-solve feature signal
    x = np.concatenate([s["x"] for s in fit])
    mean, scale = graph.frozen._preprocess(x)
    fit_batches = graph.batches(fit, mean, scale, labelled=True)
    inner_batches = graph.batches(inner, mean, scale, labelled=True)
    torch.manual_seed(17); initial = graph.GraphScorer(family)
    initial_loss = graph._loss(initial, fit_batches)
    progress = cli.Progress(tmp_path)
    progress.start_candidate(family, {"fixture": True})
    trained, row = graph.fit_candidate(family, fit_batches, inner_batches, 17, progress)
    losses = [r["inner_weighted_log_loss"] for r in row["train_curves"]]
    assert row["selected_epoch"] == int(np.argmin(losses))+1
    assert graph._loss(trained, inner_batches) == pytest.approx(min(losses), abs=1e-12)
    assert graph._loss(trained, fit_batches) < initial_loss-.03
    assert len(list(progress.path.glob(f"{family}_epoch*.json"))) == row["completed_epochs"]
    selected = progress.path / f'{family}_epoch{row["selected_epoch"]:04d}.npz'
    assert selected.exists()
    assert graph.predict(graph.restore_model(selected), inner_batches) == pytest.approx(
        graph.predict(trained, inner_batches), abs=1e-12)
    # Singleton timetable retains half partition weight; the paired sources split half.
    weights = torch.cat([b["w"] for b in fit_batches]).numpy()
    assert [weights[:6].sum(), weights[6:12].sum(), weights[12:].sum()] == pytest.approx([.25, .25, .5])


def test_inner_ties_and_expired_budget_are_explicit():
    rows = {family: {"inner_weighted_log_loss": .2, "outer_weighted_log_loss":
                   100. if family == "mean_message" else 0.} for family in graph.FAMILIES}
    assert graph.select_family(rows) == "mean_message"
    rows["graph_attention"]["inner_weighted_log_loss"] = .1
    assert graph.select_family(rows) == "graph_attention"
    batch = graph.batches([sample()], np.zeros(17), np.ones(17), labelled=True)
    with pytest.raises(TimeoutError, match="No complete"):
        graph.fit_candidate("mean_message", batch, batch, 17, task_deadline=0.01)


def test_outer_graph_and_labels_wait_for_saved_architecture_promotion(tmp_path, monkeypatch):
    groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10128))
    fit_groups, inner_groups, outer_groups = previous.grouped_split(groups, 0)
    state = {"completed": 0, "promoted": False, "outer_accesses": 0}
    class Guarded(dict):
        def __getitem__(self, key):
            if key in ("x", "y", "graph", "trip_count", "movement_ids"):
                assert state["completed"] == 2 and state["promoted"]
                state["outer_accesses"] += 1
            return super().__getitem__(key)
    samples = []
    for group in groups:
        item = sample(group, seed=5)
        if group in outer_groups:
            item["x"] += 500.
            item = Guarded(item)
        elif group in inner_groups:
            item["x"] += 20.
        samples.append(item)
    class Recorder(cli.Progress):
        def promotion(self, row):
            super().promotion(row)
            state["promoted"] = True
    def fake_fit(family, *args):
        state["completed"] += 1
        return graph.GraphScorer(family), {"family": family,
            "inner_weighted_log_loss": .1 if family == "mean_message" else .2}
    monkeypatch.setattr(graph, "fit_candidate", fake_fit)
    data = {"groups": groups, "samples": samples, "manifest_sha256": graph.POOL_SHA,
        "table_hashes": {}, "group_eligibility": [{"base_group": g, "observed_source_count": 1,
            "eligible_for_observed_source_supervision": True,
            "eligible_for_full_pair_supervision": False} for g in groups]}
    result = graph.run_fold(data, 0, Recorder(tmp_path))
    assert state["outer_accesses"] > 0 and result["no_outer_selection"]
    assert result["inner_architecture_promotion"]["family"] == "mean_message"
    preprocessing = json.loads((tmp_path / "inner_progress/fit_only_preprocessing_and_groups.json").read_text())
    assert preprocessing["mean_fit_only"][:16] == pytest.approx(sample()["x"].mean(axis=0)[:16])
    assert set(result["outer_metrics"]) == set(graph.FAMILIES) | {"inner_promoted"}


def test_runtime_mismatch_and_sigill_leave_typed_receipts(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "versions", lambda: {"torch": "wrong"})
    with pytest.raises(ValueError, match="runtime versions"):
        cli.run(0, graph.POOL_SHA, tmp_path / "train")
    receipt = json.loads((tmp_path / "train/task00/receipt.json").read_text())
    assert receipt["status"] == "failed"
    assert (tmp_path / "train/task00/launch.json").exists()
    with pytest.raises(ValueError, match="immutable"):
        cli.run(0, graph.POOL_SHA, tmp_path / "train")
    def child(argv, **kwargs):
        failing = "import torch" in argv[-1]
        return SimpleNamespace(returncode=-4 if failing else 0, stdout="", stderr="synthetic SIGILL" if failing else "")
    monkeypatch.setattr(probe.subprocess, "run", child)
    path = tmp_path / "probe.jsonl"
    assert probe.run("python-fixture", path) is False
    final = json.loads(path.read_text().splitlines()[-1])
    assert final["status"] == "failed"
    assert final["stages"][-1]["stage"] == "torch"
    assert final["stages"][-1]["returncode"] == -4
    with pytest.raises(ValueError, match="immutable"):
        probe.run("python-fixture", path)


def test_time_cap_discards_incomplete_epoch_gradient(tmp_path, monkeypatch):
    monkeypatch.setattr(graph, "GRAPH_BATCH", 1)
    monkeypatch.setattr(graph, "CANDIDATE_SECONDS", 1.)
    clock = {"now": 0., "gradient_forwards": 0}
    monkeypatch.setattr(graph, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    original = graph.GraphScorer.forward
    def forward(model, batch):
        result = original(model, batch)
        if model.training and torch.is_grad_enabled():
            clock["gradient_forwards"] += 1
            if clock["gradient_forwards"] == 3:
                clock["now"] = 2.  # second epoch: first of two gradient batches exceeds cap
        return result
    monkeypatch.setattr(graph.GraphScorer, "forward", forward)
    fit = graph.batches([sample("a"), sample("b", seed=6)],
                        np.zeros(17), np.ones(17), labelled=True)
    inner = graph.batches([sample("i", seed=7)], np.zeros(17), np.ones(17), labelled=True)
    progress = cli.Progress(tmp_path)
    trained, row = graph.fit_candidate("mean_message", fit, inner, 17, progress)
    assert row["completed_epochs"] == row["selected_epoch"] == 1
    assert row["stop_reason"] == "candidate_time_cap_incomplete_gradient_discarded"
    assert clock["gradient_forwards"] == 3
    checkpoint = progress.path / "mean_message_epoch0001.npz"
    assert graph.predict(trained, inner) == pytest.approx(
        graph.predict(graph.restore_model(checkpoint), inner), abs=1e-12)
    assert not (progress.path / "mean_message_epoch0002.json").exists()
