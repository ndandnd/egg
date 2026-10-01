"""Train-only movement scorer for observed feasible physical source fleets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from egglab import learned_proposals as edge
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from experiments import computational_benchmark as base

POLICY = "physical-source-movement-scorer-pilot-v1"
FEATURES = edge.FEATURES  # Explicit numeric case/source-price features; no IDs or outcomes.
KINDS = ("pullout", "direct", "depot", "pullin")
SEEDS = (17, 29, 43)
FOLDS = 4
EPOCHS = 240
LEARNING_RATE = 0.03
RIDGE = 0.001
HIDDEN = 16
DATASET = base.ROOT / "result/physical_learning/20260930-shard00-composite-v2"
DATASET_RECEIPT_SHA256 = "c9ed1e67356812e60a5986153227029d8eb15e98e2799a0ef87a56284be671d7"
TABLES = ("cases.jsonl", "source_inputs.jsonl")


def _jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_dataset(path=DATASET):
    """Read only admitted TRAIN case/source inputs; pin the complete receipt."""
    path = Path(path).resolve()
    if _sha(path / "dataset_receipt.json") != DATASET_RECEIPT_SHA256:
        raise ValueError("Frozen physical composite receipt hash changed")
    receipt = json.loads((path / "dataset_receipt.json").read_text())
    if receipt.get("schema") != "physical-learning-composite-v2" or receipt.get("train_only") is not True:
        raise ValueError("Only admitted train-only physical composite v2 is allowed")
    for name in TABLES:
        if receipt.get("output_hashes", {}).get(name) != _sha(path / name):
            raise ValueError("Physical training input hash changed: " + name)
    cases, source_inputs = (_jsonl(path / name) for name in TABLES)
    if len(cases) != 8 or len(source_inputs) != 16:
        raise ValueError("Pilot requires eight groups and two source fleets per group")
    by_group = {}
    for case in cases:
        group = case["base_group"]
        if (group in by_group or case.get("split") != "train"
                or case.get("generator") != physical.GENERATOR
                or case.get("base_id") not in physical.shard_ids(0)
                or case.get("physical_profile") != physical.assignment(case["base_id"])):
            raise ValueError("Duplicate/non-train/unknown physical group")
        native = edge.case_from_dict(case["case"])
        if native.identity() != case["case_identity"] or native.identity() != physical.make_case(case["base_id"]).identity():
            raise ValueError("Physical case identity differs from frozen generator")
        by_group[group] = (case, native)
    if {case["base_id"] for case in cases} != set(physical.shard_ids(0)):
        raise ValueError("Pilot group registry incomplete")
    samples = []
    seen = set()
    for source in source_inputs:
        group, kind = source.get("base_group"), source.get("source")
        if group not in by_group or kind not in ("source0", "source1") or (group, kind) in seen:
            raise ValueError("Duplicate, foreign, or unknown source input")
        seen.add((group, kind))
        case_info, case = by_group[group]
        if (source.get("base_id") != case_info["base_id"]
                or source.get("case_identity") != case.identity()
                or source.get("source_plan_hash") != nr.digest(source["source_plan"])):
            raise ValueError("Source identity differs from case")
        selected = set(source["selected_movements"])
        movement_ids = {m.id for m in case.movements}
        if (selected != {mid for vehicle in source["source_plan"]["vehicles"]
                        for mid in vehicle["movements"]}
                or not selected <= movement_ids):
            raise ValueError("Source selected movement set differs from full plan")
        market = physical.market(case, kind)
        if source.get("market_identity") != market.identity():
            raise ValueError("Source market identity changed")
        x = edge.edge_features(case, market.a)
        y = edge.selected_vector(case, source["source_plan"])
        if not np.isfinite(x).all() or len(y) != len(x):
            raise ValueError("Invalid finite edge features/labels")
        samples.append({"group": group, "source": kind, "case_identity": case.identity(),
            "source_plan_hash": source["source_plan_hash"], "x": x, "y": y,
            "movement_ids": [m.id for m in case.movements], "movement_count": len(y)})
    if seen != {(group, source) for group in by_group for source in ("source0", "source1")}:
        raise ValueError("Source fleet pair missing")
    return {"receipt_sha256": _sha(path / "dataset_receipt.json"),
        "table_hashes": {name: _sha(path / name) for name in TABLES},
        "groups": tuple(sorted(by_group)), "samples": samples}


def split_groups(groups, fold):
    if fold not in range(FOLDS) or len(groups) != 8 or len(set(groups)) != 8:
        raise ValueError("Expected four folds of eight unique train groups")
    held = tuple(group for i, group in enumerate(sorted(groups)) if i % FOLDS == fold)
    train = tuple(group for group in sorted(groups) if group not in held)
    if len(held) != 2 or len(train) != 6 or set(held) & set(train):
        raise ValueError("Grouped fold overlaps")
    return train, held


def _stack(samples):
    x = np.concatenate([s["x"] for s in samples])
    y = np.concatenate([s["y"] for s in samples])
    # Equal weight per observed full fleet; never use target costs as weights.
    w = np.concatenate([np.full(len(s["y"]), 1/(len(samples)*len(s["y"]))) for s in samples])
    return x, y, w


def preprocessing(x):
    mean, scale = x.mean(axis=0), x.std(axis=0)
    mean[-1], scale[-1] = 0.0, 1.0
    scale[scale < 1e-8] = 1.0
    return mean, scale


def _sigmoid(z):
    return 1/(1+np.exp(-np.clip(z, -35, 35)))


def _metrics(y, p, weights):
    p = np.clip(p, 1e-9, 1-1e-9)
    total = float(weights.sum())
    positive = y > 0.5
    negative = ~positive
    pred = p >= 0.5
    return {"weighted_log_loss": float(np.sum(weights*(-y*np.log(p)-(1-y)*np.log1p(-p)))/total),
        "weighted_brier": float(np.sum(weights*(p-y)**2)/total),
        "weighted_accuracy": float(np.sum(weights*(pred == positive))/total),
        "positive_recall": float(np.sum(weights*(pred & positive))/sum(weights[positive]))
            if np.any(positive) else None,
        "negative_recall": float(np.sum(weights*((~pred) & negative))/sum(weights[negative]))
            if np.any(negative) else None,
        "positive_rate": float(np.sum(weights*y)/total)}


def _controls(train_x, train_y, train_w, test_x):
    prevalence = float(np.sum(train_w*train_y)/train_w.sum())
    # First four features are one-hot movement kinds by explicit feature policy.
    kind = np.argmax(train_x[:, :4], axis=1)
    test_kind = np.argmax(test_x[:, :4], axis=1)
    rates = []
    for i in range(4):
        mask = kind == i
        rates.append(float(np.sum(train_w[mask]*train_y[mask])/train_w[mask].sum()) if np.any(mask)
                     else prevalence)
    return {"constant": np.full(len(test_x), prevalence),
        "kind_frequency": np.asarray(rates)[test_kind]}, prevalence, rates


def _curve(y, p, w, epoch):
    return {"epoch": epoch, **_metrics(y, p, w)}


def _linear(z, y, w, seed):
    theta = np.zeros(z.shape[1]); curve = []
    for epoch in range(1, EPOCHS+1):
        p = _sigmoid(z @ theta)
        reg = theta.copy(); reg[-1] = 0.0
        grad = z.T @ (w*(p-y))/w.sum() + RIDGE*reg
        theta -= LEARNING_RATE*grad
        if epoch == 1 or epoch % 20 == 0:
            curve.append(_curve(y, _sigmoid(z @ theta), w, epoch))
    return {"weights": theta.tolist(), "curve": curve, "seed": seed}


def _mlp(z, y, w, seed):
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, 0.08, (z.shape[1], HIDDEN))
    b1 = np.zeros(HIDDEN)
    W2 = rng.normal(0, 0.08, HIDDEN)
    b2 = 0.0
    curve = []
    for epoch in range(1, EPOCHS+1):
        hidden = np.tanh(z @ W1 + b1)
        p = _sigmoid(hidden @ W2 + b2)
        d = w*(p-y)/w.sum()
        gW2 = hidden.T @ d + RIDGE*W2
        gb2 = float(d.sum())
        dh = (d[:, None]*W2[None, :])*(1-hidden**2)
        gW1 = z.T @ dh + RIDGE*W1
        gb1 = dh.sum(axis=0)
        W2 -= LEARNING_RATE*gW2; b2 -= LEARNING_RATE*gb2
        W1 -= LEARNING_RATE*gW1; b1 -= LEARNING_RATE*gb1
        if epoch == 1 or epoch % 20 == 0:
            curve.append(_curve(y, _sigmoid(np.tanh(z @ W1+b1) @ W2+b2), w, epoch))
    return {"W1": W1.tolist(), "b1": b1.tolist(), "W2": W2.tolist(),
        "b2": b2, "curve": curve, "seed": seed}


def run_fold(dataset, task_id):
    if task_id not in range(FOLDS*len(SEEDS)):
        raise ValueError("Undeclared training task")
    fold, seed = divmod(task_id, len(SEEDS))
    seed = SEEDS[seed]
    train_groups, held_groups = split_groups(dataset["groups"], fold)
    train = [s for s in dataset["samples"] if s["group"] in train_groups]
    held = [s for s in dataset["samples"] if s["group"] in held_groups]
    train_x, train_y, train_w = _stack(train)
    held_x, held_y, held_w = _stack(held)
    mean, scale = preprocessing(train_x)
    z, z_held = (train_x-mean)/scale, (held_x-mean)/scale
    controls, prevalence, kind_rates = _controls(train_x, train_y, train_w, held_x)
    linear = _linear(z, train_y, train_w, seed)
    mlp = _mlp(z, train_y, train_w, seed)
    predictions = {**controls,
        "linear": _sigmoid(z_held @ np.asarray(linear["weights"])),
        "mlp16": _sigmoid(np.tanh(z_held @ np.asarray(mlp["W1"]) +
            np.asarray(mlp["b1"])) @ np.asarray(mlp["W2"]) + mlp["b2"])}
    held_metrics = {name: _metrics(held_y, p, held_w) for name, p in predictions.items()}
    per_group = {}
    heldout_predictions = []
    cursor = 0
    for sample in held:
        n = sample["movement_count"]
        weights = np.ones(n)/n
        per_group.setdefault(sample["group"], {})[sample["source"]] = {
            name: _metrics(sample["y"], pred[cursor:cursor+n], weights)
            for name, pred in predictions.items()}
        for j in range(n):
            heldout_predictions.append({"base_group": sample["group"],
                "source": sample["source"],
                "movement_id": sample["movement_ids"][j],
                "observed_selected": bool(sample["y"][j]),
                "probabilities": {name: float(pred[cursor+j])
                                  for name, pred in predictions.items()}})
        cursor += n
    return {"policy": POLICY, "task_id": task_id, "fold": fold, "seed": seed,
        "train_groups": train_groups, "heldout_groups": held_groups,
        "train_source_fleets": len(train), "heldout_source_fleets": len(held),
        "train_movement_rows": len(train_y), "heldout_movement_rows": len(held_y),
        "features": FEATURES, "feature_mean": mean.tolist(), "feature_scale": scale.tolist(),
        "training_only_control_prevalence": prevalence,
        "training_only_kind_frequencies": kind_rates,
        "linear_model": linear, "mlp16_model": mlp,
        "heldout_metrics": held_metrics, "heldout_per_group_source": per_group,
        "heldout_predictions": heldout_predictions,
        "dataset_receipt_sha256": dataset["receipt_sha256"],
        "input_table_hashes": dataset["table_hashes"],
        "objective_scope": "selected movement in observed feasible source incumbent, not edge truth or optimality",
        "fixed_epochs_no_outer_tuning": EPOCHS,
        "training_config": {"epochs": EPOCHS, "learning_rate": LEARNING_RATE,
            "ridge": RIDGE, "hidden_units": HIDDEN,
            "weighting": "equal full-fleet weight then equal movement weight within fleet"}}
