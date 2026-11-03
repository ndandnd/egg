"""Prospective CPU graph imitation of observed feasible incumbent movements.

No route feasibility or optimality inference is made. Only inner groups select
checkpoints and the promoted architecture; every source graph stays disconnected.
"""
from __future__ import annotations

from collections import defaultdict
import copy
import math
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from egglab import learned_proposals as edge
from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous

POLICY = "physical-source-movement-graph-exact128-v6"
PREFIX = 128
POOL_SHA = "d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d"
FEATURES = previous.FEATURES
FOLDS, SEEDS = previous.FOLDS, previous.SEEDS
FAMILIES = ("mean_message", "graph_attention")
WIDTH, LAYERS, PARAMETER_CEILING = 32, 2, 18000
MAX_EPOCHS, PATIENCE, GRAPH_BATCH = 300, 30, 8
LEARNING_RATE, WEIGHT_DECAY = .003, .0001
CANDIDATE_SECONDS, TASK_SECONDS = 750., 1650.
DTYPE = torch.float64


def configure_cpu():
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)


def topology(case):
    """Trip vertices plus separate depot source/sink; parallel modes survive."""
    trip_ids = tuple(sorted(t.id for t in case.trips))
    if len(set(trip_ids)) != len(trip_ids) or not trip_ids:
        raise ValueError("Graph needs unique nonempty trip IDs")
    indexes = {trip_id: i+1 for i, trip_id in enumerate(trip_ids)}
    source, sink = 0, len(trip_ids)+1
    src, dst = [], []
    for movement in case.movements:
        if movement.before is None and movement.after is None:
            raise ValueError("Movement has neither endpoint")
        src.append(source if movement.before is None else indexes[movement.before])
        dst.append(sink if movement.after is None else indexes[movement.after])
    return {"src": np.asarray(src, dtype=np.int64),
            "dst": np.asarray(dst, dtype=np.int64), "nodes": len(trip_ids)+2,
            "trip_ids": trip_ids}


def load_pool(path, *, expected_manifest_sha256):
    if expected_manifest_sha256 != POOL_SHA:
        raise ValueError("Only the pinned exact128 TRAIN pool is declared")
    data = previous.load_pool(path, expected_manifest_sha256=expected_manifest_sha256,
                              prefix=PREFIX)
    cases = {r["base_group"]: edge.case_from_dict(r["case"])
             for r in frozen._rows(Path(path) / "cases.jsonl")}
    for sample in data["samples"]:
        case = cases[sample["group"]]
        if sample["movement_ids"] != [m.id for m in case.movements]:
            raise ValueError("Graph movement order differs from frozen edge rows")
        sample["graph"] = topology(case)
    return data


def batches(samples, mean, scale, *, labelled):
    """Bound memory with eight disconnected source graphs per deterministic batch."""
    if not samples:
        raise ValueError("No observed source graphs")
    counts = defaultdict(int)
    for sample in samples:
        counts[sample["group"]] += 1
    output = []
    for begin in range(0, len(samples), GRAPH_BATCH):
        chunk = samples[begin:begin+GRAPH_BATCH]
        xs, srcs, dsts, roles, ys, weights = [], [], [], [], [], []
        offset = 0
        for sample in chunk:
            x = (np.asarray(sample["x"], dtype=float)-mean)/scale
            graph = sample["graph"]
            src, dst = np.asarray(graph["src"]), np.asarray(graph["dst"])
            nodes = graph["nodes"]
            if (x.ndim != 2 or x.shape[1] != len(FEATURES) or not len(x)
                    or not np.isfinite(x).all() or nodes != sample["trip_count"]+2
                    or src.shape != (len(x),) or dst.shape != (len(x),)
                    or src.dtype.kind not in "iu" or dst.dtype.kind not in "iu"
                    or np.any(src < 0) or np.any(dst < 0)
                    or np.any(src >= nodes) or np.any(dst >= nodes)):
                raise ValueError("Malformed movement graph/features")
            xs.append(x); srcs.append(src+offset); dsts.append(dst+offset)
            role = np.zeros((nodes, 2)); role[0, 0] = 1; role[-1, 1] = 1
            roles.append(role)
            if labelled:
                y = np.asarray(sample["y"], dtype=float)
                if y.shape != (len(x),) or not np.isin(y, (0., 1.)).all():
                    raise ValueError("Invalid binary incumbent membership")
                ys.append(y)
                weights.append(np.full(len(x), 1/(len(counts)*counts[sample["group"]]*len(x))))
            offset += nodes
        batch = {"x": torch.as_tensor(np.concatenate(xs), dtype=DTYPE),
                 "src": torch.as_tensor(np.concatenate(srcs), dtype=torch.long),
                 "dst": torch.as_tensor(np.concatenate(dsts), dtype=torch.long),
                 "roles": torch.as_tensor(np.concatenate(roles), dtype=DTYPE),
                 "nodes": offset}
        if labelled:
            batch["y"] = torch.as_tensor(np.concatenate(ys), dtype=DTYPE)
            batch["w"] = torch.as_tensor(np.concatenate(weights), dtype=DTYPE)
        output.append(batch)
    return output


def _aggregate(messages, indexes, nodes, attention=None):
    if attention is None:
        count = torch.bincount(indexes, minlength=nodes).clamp_min(1)
        coefficients = 1/count[indexes].to(messages.dtype)
    else:
        scores = messages @ attention / math.sqrt(messages.shape[1])
        maximum = scores.new_full((nodes,), -torch.inf)
        maximum.scatter_reduce_(0, indexes, scores.detach(), reduce="amax", include_self=True)
        exponent = torch.exp(scores-maximum[indexes])
        denominator = exponent.new_zeros(nodes).index_add(0, indexes, exponent)
        coefficients = exponent/denominator[indexes]
    return messages.new_zeros((nodes, messages.shape[1])).index_add(
        0, indexes, messages*coefficients[:, None])


class GraphScorer(nn.Module):
    def __init__(self, family):
        super().__init__()
        if family not in FAMILIES:
            raise ValueError("Unknown graph architecture")
        self.family = family
        self.node = nn.Linear(2*len(FEATURES)+2, WIDTH)
        self.edge = nn.Linear(len(FEATURES), WIDTH)
        self.message = nn.ModuleList(nn.Linear(3*WIDTH, WIDTH) for _ in range(LAYERS))
        self.update = nn.ModuleList(nn.Linear(3*WIDTH, WIDTH) for _ in range(LAYERS))
        if family == "graph_attention":
            self.attention_in = nn.ParameterList(nn.Parameter(torch.zeros(WIDTH)) for _ in range(LAYERS))
            self.attention_out = nn.ParameterList(nn.Parameter(torch.zeros(WIDTH)) for _ in range(LAYERS))
        self.decoder = nn.Linear(3*WIDTH+len(FEATURES), WIDTH)
        self.output = nn.Linear(WIDTH, 1)
        self.to(device="cpu", dtype=DTYPE)
        self.parameter_count = sum(p.numel() for p in self.parameters())
        if self.parameter_count > PARAMETER_CEILING:
            raise ValueError("Graph parameter budget exceeded")

    def forward(self, batch):
        x, src, dst, nodes = (batch[k] for k in ("x", "src", "dst", "nodes"))
        if x.device.type != "cpu" or any(p.device.type != "cpu" for p in self.parameters()):
            raise ValueError("Only CPU graph computation is declared")
        incoming, outgoing = _aggregate(x, dst, nodes), _aggregate(x, src, nodes)
        h = torch.relu(self.node(torch.cat((incoming, outgoing, batch["roles"]), dim=1)))
        e = torch.relu(self.edge(x))
        for layer in range(LAYERS):
            message = torch.tanh(self.message[layer](torch.cat((h[src], h[dst], e), dim=1)))
            ai = self.attention_in[layer] if self.family == "graph_attention" else None
            ao = self.attention_out[layer] if self.family == "graph_attention" else None
            incoming = _aggregate(message, dst, nodes, ai)
            outgoing = _aggregate(message, src, nodes, ao)
            h = torch.relu(self.update[layer](torch.cat((h, incoming, outgoing), dim=1)))
        hidden = torch.relu(self.decoder(torch.cat((h[src], h[dst], e, x), dim=1)))
        return self.output(hidden).squeeze(1)


def save_model(model, path):
    """Portable numeric weights; no pickle or executable checkpoint objects."""
    values = {name: tensor.detach().cpu().numpy() for name, tensor in model.state_dict().items()}
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, **values, architecture=np.asarray(model.family), policy=np.asarray(POLICY))


def restore_model(path):
    with np.load(path, allow_pickle=False) as data:
        if str(data["policy"]) != POLICY:
            raise ValueError("Unknown graph model policy")
        model = GraphScorer(str(data["architecture"]))
        expected = model.state_dict()
        if set(data.files) != set(expected) | {"architecture", "policy"}:
            raise ValueError("Graph checkpoint tensor set differs")
        weights = {}
        for name, reference in expected.items():
            value = data[name]
            if value.shape != tuple(reference.shape) or not np.isfinite(value).all():
                raise ValueError("Malformed graph checkpoint tensor")
            weights[name] = torch.as_tensor(value, dtype=DTYPE)
        model.load_state_dict(weights, strict=True)
    return model.eval()


def predict(model, graph_batches):
    model.eval()
    with torch.no_grad():
        return np.concatenate([torch.sigmoid(model(batch)).numpy() for batch in graph_batches])


def _loss(model, graph_batches):
    model.eval()
    with torch.no_grad():
        return sum(float((F.binary_cross_entropy_with_logits(model(batch), batch["y"],
                       reduction="none")*batch["w"]).sum()) for batch in graph_batches)


def fit_candidate(family, fit_batches, inner_batches, seed, recorder=None, task_deadline=None):
    configure_cpu(); torch.manual_seed(seed)
    model = GraphScorer(family)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, betas=(.9, .999),
                                 eps=1e-8, weight_decay=WEIGHT_DECAY)
    started = time.monotonic()
    deadline = min(started+CANDIDATE_SECONDS, task_deadline if task_deadline is not None else float("inf"))
    best, best_state, best_epoch, stale, curve = float("inf"), None, 0, 0, []
    stop = "epoch_cap"
    timers = {"gradient_and_update_seconds": 0., "fit_evaluation_seconds": 0.,
              "inner_evaluation_seconds": 0., "epoch_persistence_seconds": 0.}
    for epoch in range(1, MAX_EPOCHS+1):
        if time.monotonic() >= deadline:
            stop = "candidate_time_cap"; break
        gradient_started = time.monotonic()
        model.train(); optimizer.zero_grad(set_to_none=True)
        # Accumulate the exact full-partition weighted gradient; one Adam step.
        # Batches partition graphs solely for memory, with no per-batch rescaling.
        interrupted = False
        for batch in fit_batches:
            if time.monotonic() >= deadline:
                interrupted = True; break
            loss = (F.binary_cross_entropy_with_logits(model(batch), batch["y"],
                    reduction="none")*batch["w"]).sum()
            if not torch.isfinite(loss):
                raise ValueError("Nonfinite graph fit loss")
            loss.backward()
        if interrupted:
            timers["gradient_and_update_seconds"] += time.monotonic()-gradient_started
            stop = "candidate_time_cap_incomplete_gradient_discarded"; break
        optimizer.step()
        timers["gradient_and_update_seconds"] += time.monotonic()-gradient_started
        evaluation_started = time.monotonic()
        fit_loss = _loss(model, fit_batches)
        timers["fit_evaluation_seconds"] += time.monotonic()-evaluation_started
        evaluation_started = time.monotonic()
        inner_loss = _loss(model, inner_batches)
        timers["inner_evaluation_seconds"] += time.monotonic()-evaluation_started
        if not np.isfinite([fit_loss, inner_loss]).all():
            raise ValueError("Nonfinite graph checkpoint loss")
        improved = inner_loss < best
        if improved:
            best, best_epoch, stale = inner_loss, epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            stale += 1
        row = {"epoch": epoch, "fit_weighted_log_loss": fit_loss,
               "inner_weighted_log_loss": inner_loss, "selected_so_far": improved,
               "elapsed_seconds": time.monotonic()-started}
        curve.append(row)
        if recorder is not None:
            persistence_started = time.monotonic()
            recorder.epoch(family, epoch, model if improved else None, row)
            timers["epoch_persistence_seconds"] += time.monotonic()-persistence_started
        if stale >= PATIENCE:
            stop = "inner_patience"; break
    if best_state is None:
        raise TimeoutError("No complete graph epoch within candidate time budget")
    model.load_state_dict(best_state)
    return model.eval(), {"family": family, "seed": seed,
        "parameter_count": model.parameter_count, "selected_epoch": best_epoch,
        "completed_epochs": len(curve), "stop_reason": stop,
        "inner_weighted_log_loss": best, "train_curves": curve,
        "fit_and_inner_seconds": time.monotonic()-started, "training_timers": timers}


def select_family(rows):
    if set(rows) != set(FAMILIES) or not all(np.isfinite(rows[f]["inner_weighted_log_loss"]) for f in FAMILIES):
        raise ValueError("Missing finite inner graph architecture losses")
    return min(FAMILIES, key=lambda f: (rows[f]["inner_weighted_log_loss"], FAMILIES.index(f)))


def run_fold(dataset, task_id, recorder):
    if (tuple(dataset["groups"]) != tuple(f"physical_v2_s{i}" for i in range(10000, 10128))
            or dataset["manifest_sha256"] != POOL_SHA or task_id not in range(FOLDS*len(SEEDS))):
        raise ValueError("Only exact128 TRAIN and frozen12 tasks are declared")
    started = time.monotonic(); deadline = started+TASK_SECONDS
    fold, seed_index = divmod(task_id, len(SEEDS)); seed = SEEDS[seed_index]
    fit_groups, inner_groups, outer_groups = previous.grouped_split(dataset["groups"], fold)
    fit = [s for s in dataset["samples"] if s["group"] in fit_groups]
    inner = [s for s in dataset["samples"] if s["group"] in inner_groups]
    fit_x, fit_y, fit_w = previous._stack(fit)
    inner_x, inner_y, inner_w = previous._stack(inner)
    mean, scale = frozen._preprocess(fit_x)
    recorder.preprocessing({"features": FEATURES, "mean_fit_only": mean.tolist(),
                            "scale_fit_only": scale.tolist(), "fit_groups": fit_groups,
                            "inner_groups": inner_groups, "outer_groups": outer_groups})
    fit_batches = batches(fit, mean, scale, labelled=True)
    inner_batches = batches(inner, mean, scale, labelled=True)
    models, rows = {}, {}
    for family in FAMILIES:
        recorder.start_candidate(family, {"width": WIDTH, "layers": LAYERS,
            "parameter_ceiling": PARAMETER_CEILING, "max_epochs": MAX_EPOCHS,
            "patience": PATIENCE, "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY, "candidate_seconds": CANDIDATE_SECONDS})
        fitted, row = fit_candidate(family, fit_batches, inner_batches, seed, recorder, deadline)
        prediction_started = time.monotonic()
        fit_p = predict(fitted, fit_batches)
        row["fit_selected_prediction_seconds"] = time.monotonic()-prediction_started
        prediction_started = time.monotonic()
        inner_p = predict(fitted, inner_batches)
        row["inner_selected_prediction_seconds"] = time.monotonic()-prediction_started
        row["fit_metrics"] = frozen._metrics(fit_y, fit_p, fit_w, fit)
        row["inner_metrics"] = frozen._metrics(inner_y, inner_p, inner_w, inner)
        row["saved_model"] = recorder.candidate(family, fitted, row, fit, fit_p, inner, inner_p)
        models[family], rows[family] = fitted, row
    promoted = select_family(rows)
    promotion = {"family": promoted, "tie_order": FAMILIES,
        "inner_weighted_log_losses": {f: rows[f]["inner_weighted_log_loss"] for f in FAMILIES}}
    recorder.promotion(promotion)
    # Outer graph/features/labels enter after both selected models and promotion persist.
    outer = [s for s in dataset["samples"] if s["group"] in outer_groups]
    outer_batches = batches(outer, mean, scale, labelled=False)
    _, outer_y, outer_w = previous._stack(outer)
    predictions, outer_inference_seconds = {}, {}
    for family in FAMILIES:
        inference_started = time.monotonic()
        predictions[family] = predict(models[family], outer_batches)
        outer_inference_seconds[family] = time.monotonic()-inference_started
    predictions["inner_promoted"] = predictions[promoted]
    per_source, per_group, prediction_rows = defaultdict(dict), {}, []
    cursor = 0
    for sample in outer:
        n = len(sample["y"])
        per_source[sample["group"]][sample["source"]] = {
            f: frozen._metrics(sample["y"], p[cursor:cursor+n], np.ones(n)/n, [sample])
            for f, p in predictions.items()}
        for i, movement_id in enumerate(sample["movement_ids"]):
            prediction_rows.append({"base_group": sample["group"], "source": sample["source"],
                "movement_id": movement_id, "observed_selected": bool(sample["y"][i]),
                "input_trip_count_k": min(n, sample["trip_count"]),
                "probabilities": {f: float(p[cursor+i]) for f, p in predictions.items()}})
        cursor += n
    for group in outer_groups:
        per_group[group] = {f: previous._macro_metrics([r[f] for r in per_source[group].values()])
                            for f in predictions}
    common32 = [g for g in outer_groups if int(g.removeprefix("physical_v2_s")) < 10032]
    return {"policy": POLICY, "task_id": task_id, "fold": fold, "seed": seed,
        "features": FEATURES, "width": WIDTH, "layers": LAYERS,
        "dtype": "float64", "device": "cpu", "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "fit_groups": fit_groups, "inner_groups": inner_groups, "outer_groups": outer_groups,
        "eligibility": {part: previous._partition_eligibility(dataset["group_eligibility"], groups)
            for part, groups in (("fit", fit_groups), ("inner", inner_groups), ("outer", outer_groups))},
        "weights": {part: previous._weight_manifest(samples)
                   for part, samples in (("fit", fit), ("inner", inner), ("outer", outer))},
        "pool_manifest_sha256": dataset["manifest_sha256"], "pool_table_hashes": dataset["table_hashes"],
        "candidates": rows, "inner_architecture_promotion": promotion,
        "outer_metrics": {f: previous._macro_metrics([per_group[g][f] for g in outer_groups])
                          for f in predictions},
        "common32_outer_metrics": {f: previous._macro_metrics([per_group[g][f] for g in common32])
                                   for f in predictions},
        "outer_pooled_diagnostics": {f: frozen._metrics(outer_y, p, outer_w, outer)
                                     for f, p in predictions.items()},
        "per_group_source_outer_metrics": dict(per_source), "per_group_outer_metrics": per_group,
        "outer_prediction_rows": prediction_rows, "no_outer_selection": True,
        "outer_inference_seconds_by_family": outer_inference_seconds,
        "progress_persistence_seconds": recorder.persistence_seconds,
        "label_scope": "observed feasible incumbent imitation; unselected is not infeasible or suboptimal",
        "wall_seconds": time.monotonic()-started}
