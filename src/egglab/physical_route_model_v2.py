"""Grouped, train-only 32-group source-movement classification experiment."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

from egglab import learned_proposals as edge
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training as pool

POLICY = "physical-source-movement-scorer-grouped32-v2"
FEATURES = edge.FEATURES
FOLDS = 4
SEEDS = (17, 29, 43)
POOL = pool.OUTPUT
MLP_HIDDEN = 32
MLP_MAX_EPOCHS = 300
MLP_CHECK_EVERY = 10
MLP_PATIENCE_CHECKS = 6
MLP_LR = 0.005
MLP_RIDGE = 0.001
TREE_ITERATIONS = (25, 50, 100, 200)
TREE_MAX_LEAVES = 15
TREE_MIN_LEAF = 20
TREE_MAX_BINS = 128
TREE_LR = 0.05
TREE_L2 = 1.0
LOGISTIC_C = 1.0
LOGISTIC_MAX_ITER = 1000
LOGISTIC_TOL = 1e-6


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    return json.loads(Path(path).read_text())


def _rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def load_pool(path=POOL, *, expected_manifest_sha256):
    path = Path(path).resolve()
    if _sha(path / "pool_manifest.json") != expected_manifest_sha256:
        raise ValueError("Pinned pooled training manifest hash changed")
    manifest = _read(path / "pool_manifest.json")
    if (manifest.get("policy") != pool.POLICY or manifest.get("train_only") is not True
            or manifest.get("base_ids") != list(range(10000, 10032))
            or manifest.get("independent_groups") != 32 or manifest.get("source_fleets") != 64):
        raise ValueError("Unknown or non-TRAIN pooled dataset")
    for name in ("cases.jsonl", "source_inputs.jsonl"):
        if manifest.get("output_hashes", {}).get(name) != _sha(path / name):
            raise ValueError("Pooled input table hash changed: " + name)
    cases = _rows(path / "cases.jsonl")
    source_inputs = _rows(path / "source_inputs.jsonl")
    if len(cases) != 32 or len(source_inputs) != 64:
        raise ValueError("Expected 32 cases and 64 source fleets")
    by_group = {}
    for row in cases:
        group, base_id = row.get("base_group"), row.get("base_id")
        if (group in by_group or base_id not in range(10000, 10032)
                or group != f"physical_v2_s{base_id}" or row.get("split") != "train"
                or row.get("generator") != physical.GENERATOR
                or row.get("physical_profile") != physical.assignment(base_id)):
            raise ValueError("Duplicate/unknown/non-train pooled group")
        case = edge.case_from_dict(row["case"])
        if case.identity() != row.get("case_identity") or case.identity() != physical.make_case(base_id).identity():
            raise ValueError("Pooled case identity changed")
        by_group[group] = (row, case)
    if {row[0]["base_id"] for row in by_group.values()} != set(range(10000, 10032)):
        raise ValueError("Missing TRAIN base ID")
    samples, seen = [], set()
    for source in source_inputs:
        group, kind = source.get("base_group"), source.get("source")
        if group not in by_group or kind not in ("source0", "source1") or (group, kind) in seen:
            raise ValueError("Duplicate, foreign, or unknown source fleet")
        seen.add((group, kind))
        row, case = by_group[group]
        plan = source["source_plan"]
        if (source.get("base_id") != row["base_id"] or source.get("case_identity") != case.identity()
                or source.get("source_plan_hash") != nr.digest(plan)):
            raise ValueError("Source physical identity/hash changed")
        market = physical.market(case, kind)
        if source.get("market_identity") != market.identity():
            raise ValueError("Source market identity changed")
        selected = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
        if selected != set(source["selected_movements"]):
            raise ValueError("Source full plan/topology mismatch")
        x = edge.edge_features(case, market.a)
        y = edge.selected_vector(case, plan)
        if len(x) != len(y) or not np.isfinite(x).all():
            raise ValueError("Invalid finite source movement matrix")
        samples.append({"group": group, "source": kind, "x": x, "y": y,
            "movement_ids": [m.id for m in case.movements], "trip_count": len(case.trips)})
    if seen != {(g, s) for g in by_group for s in ("source0", "source1")}:
        raise ValueError("Pooled source pair missing")
    return {"groups": tuple(sorted(by_group)), "samples": samples,
        "manifest_sha256": expected_manifest_sha256,
        "table_hashes": {name: _sha(path / name)
                         for name in ("cases.jsonl", "source_inputs.jsonl")}}


def grouped_split(groups, fold):
    if len(groups) != 32 or len(set(groups)) != 32 or fold not in range(FOLDS):
        raise ValueError("Expected 32 unique groups and four outer folds")
    ordered = tuple(sorted(groups))
    outer = tuple(g for i, g in enumerate(ordered) if i % FOLDS == fold)
    training = tuple(g for g in ordered if g not in outer)
    inner = training[2::6]  # Four fixed validation timetables, no outcome-dependent selection.
    fit = tuple(g for g in training if g not in inner)
    if (len(fit), len(inner), len(outer)) != (20, 4, 8):
        raise ValueError("Grouped 20/4/8 split changed")
    return fit, inner, outer


def _stack(samples):
    if not samples:
        raise ValueError("Empty grouped sample split")
    x = np.concatenate([s["x"] for s in samples])
    y = np.concatenate([s["y"] for s in samples])
    w = np.concatenate([np.full(len(s["y"]), 1/(len(samples)*len(s["y"])))
                        for s in samples])
    return x, y, w


def _weight_manifest(samples):
    return [{"base_group": s["group"], "source": s["source"],
        "movement_rows": len(s["y"]), "fleet_weight": 1/len(samples),
        "per_movement_weight": 1/(len(samples)*len(s["y"]))} for s in samples]


def _preprocess(x):
    mean, scale = x.mean(axis=0), x.std(axis=0)
    mean[-1], scale[-1] = 0.0, 1.0
    scale[scale < 1e-8] = 1.0
    return mean, scale


def _sigmoid(logits):
    return 1/(1+np.exp(-np.clip(logits, -35, 35)))


def _metrics(y, p, w, samples=None):
    p = np.clip(np.asarray(p), 1e-9, 1-1e-9)
    total = w.sum()
    positive = y > 0.5
    negative = ~positive
    predicted = p >= 0.5
    outcome = {"weighted_log_loss": float(np.sum(w*(-y*np.log(p)-(1-y)*np.log1p(-p)))/total),
        "weighted_brier": float(np.sum(w*(p-y)**2)/total),
        "weighted_accuracy_at_fixed_half": float(np.sum(w*(predicted==positive))/total),
        "weighted_positive_recall_at_fixed_half": (
            float(np.sum(w[predicted & positive])/np.sum(w[positive]))
            if np.any(positive) else None),
        "weighted_negative_recall_at_fixed_half": (
            float(np.sum(w[(~predicted) & negative])/np.sum(w[negative]))
            if np.any(negative) else None),
        "positive_count": int(np.sum(positive)),
        "negative_count": int(np.sum(negative)),
        "positive_weight": float(np.sum(w[positive])),
        "negative_weight": float(np.sum(w[negative])),
        "average_precision": float(average_precision_score(y, p, sample_weight=w)),
        "positive_rate": float(np.sum(w*y)/total)}
    if samples is not None:
        cursor, recalls, diagnostic = 0, [], []
        for sample in samples:
            n = len(sample["y"])
            k = min(sample["trip_count"], n)  # Known from the case before any label.
            scores = p[cursor:cursor+n]
            top = np.argsort(-scores, kind="stable")[:k]
            denom = float(sample["y"].sum())
            recall = float(sample["y"][top].sum()/denom) if denom > 0 else None
            recalls.append(recall)
            diagnostic.append({"base_group": sample["group"], "source": sample["source"],
                "trip_count_input_k": k, "observed_positive_edges": int(denom),
                "topk_recall": recall})
            cursor += n
        outcome["input_trip_count_topk_recall_mean_by_fleet"] = float(np.mean(
            [v for v in recalls if v is not None])) if any(v is not None for v in recalls) else None
        outcome["topk_by_fleet"] = diagnostic
    return outcome


def _controls(fit_x, fit_y, fit_w, other_x):
    prevalence = float(np.dot(fit_w, fit_y)/fit_w.sum())
    kind = np.argmax(fit_x[:, :4], axis=1)
    rates = []
    for i in range(4):
        mask = kind == i
        rates.append(float(np.dot(fit_w[mask], fit_y[mask])/fit_w[mask].sum())
                     if np.any(mask) else prevalence)
    return ({"constant": np.full(len(other_x), prevalence),
        "kind_frequency": np.asarray(rates)[np.argmax(other_x[:, :4], axis=1)]},
        prevalence, rates)


def _mlp_fit(x, y, w, val_x, val_y, val_w, seed):
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, 0.05, (x.shape[1], MLP_HIDDEN)); b1 = np.zeros(MLP_HIDDEN)
    W2 = rng.normal(0, 0.05, MLP_HIDDEN); b2 = 0.0
    params = [W1, b1, W2, np.asarray(b2)]
    first = [np.zeros_like(p) for p in params]
    second = [np.zeros_like(p) for p in params]
    best, best_loss, stale, curve = None, float("inf"), 0, []
    for epoch in range(1, MLP_MAX_EPOCHS+1):
        h = np.tanh(x @ params[0] + params[1])
        p = _sigmoid(h @ params[2] + params[3])
        d = w*(p-y)/w.sum()
        gradients = [None]*4
        gradients[2] = h.T @ d + MLP_RIDGE*params[2]
        gradients[3] = np.asarray(d.sum())
        dh = (d[:, None]*params[2][None, :])*(1-h*h)
        gradients[0] = x.T @ dh + MLP_RIDGE*params[0]
        gradients[1] = dh.sum(axis=0)
        for j in range(4):
            first[j] = 0.9*first[j]+0.1*gradients[j]
            second[j] = 0.999*second[j]+0.001*gradients[j]**2
            adjusted = (first[j]/(1-0.9**epoch))/(np.sqrt(second[j]/(1-0.999**epoch))+1e-8)
            params[j] = params[j]-MLP_LR*adjusted
        if epoch % MLP_CHECK_EVERY:
            continue
        fit_p = _sigmoid(np.tanh(x @ params[0]+params[1]) @ params[2]+params[3])
        inner_p = _sigmoid(np.tanh(val_x @ params[0]+params[1]) @ params[2]+params[3])
        fit_metric = _metrics(y, fit_p, w)
        inner_metric = _metrics(val_y, inner_p, val_w)
        loss = inner_metric["weighted_log_loss"]
        curve.append({"epoch": epoch, "fit": fit_metric, "inner": inner_metric})
        if loss < best_loss-1e-8:
            best_loss, stale = loss, 0
            best = (epoch, [np.array(value, copy=True) for value in params])
        else:
            stale += 1
            if stale >= MLP_PATIENCE_CHECKS:
                break
    if best is None:
        raise ValueError("MLP failed to select an inner-group epoch")
    epoch, chosen = best
    return {"selected_epoch": epoch, "stopped_epoch": curve[-1]["epoch"],
        "params": {"W1": chosen[0].tolist(), "b1": chosen[1].tolist(),
            "W2": chosen[2].tolist(), "b2": float(chosen[3])},
        "curve": curve, "selected_inner_log_loss": best_loss}


def _mlp_predict(artifact, x):
    p = artifact["params"]
    return _sigmoid(np.tanh(x @ np.asarray(p["W1"])+np.asarray(p["b1"])) @
                    np.asarray(p["W2"])+p["b2"])


def _tree_fit(x, y, w, inner_x, inner_y, inner_w, seed):
    curve, candidates = [], {}
    # sklearn's own row-level early stopping is disabled: only entire inner groups select.
    for count in TREE_ITERATIONS:
        model = HistGradientBoostingClassifier(loss="log_loss", max_iter=count,
            max_leaf_nodes=TREE_MAX_LEAVES, min_samples_leaf=TREE_MIN_LEAF,
            max_bins=TREE_MAX_BINS, learning_rate=TREE_LR,
            l2_regularization=TREE_L2, early_stopping=False, random_state=seed)
        model.fit(x, y, sample_weight=w*len(y)/w.sum())
        fit_metric = _metrics(y, model.predict_proba(x)[:, 1], w)
        inner_metric = _metrics(inner_y, model.predict_proba(inner_x)[:, 1], inner_w)
        curve.append({"iterations": count, "fit": fit_metric, "inner": inner_metric})
        candidates[count] = model
    winner = min(curve, key=lambda row: (row["inner"]["weighted_log_loss"], row["iterations"]))
    selected = winner["iterations"]
    return candidates[selected], {"selected_iterations": selected,
        "selected_inner_log_loss": winner["inner"]["weighted_log_loss"],
        "curve": curve}


def run_fold(dataset, task_id):
    if task_id not in range(FOLDS*len(SEEDS)):
        raise ValueError("Undeclared 32-group route task")
    fold, seed_index = divmod(task_id, len(SEEDS)); seed = SEEDS[seed_index]
    fit_groups, inner_groups, outer_groups = grouped_split(dataset["groups"], fold)
    fit = [s for s in dataset["samples"] if s["group"] in fit_groups]
    inner = [s for s in dataset["samples"] if s["group"] in inner_groups]
    outer = [s for s in dataset["samples"] if s["group"] in outer_groups]
    fit_x, fit_y, fit_w = _stack(fit)
    inner_x, inner_y, inner_w = _stack(inner)
    mean, scale = _preprocess(fit_x)
    z, inner_z = (fit_x-mean)/scale, (inner_x-mean)/scale
    controls_inner, prevalence, kind_rates = _controls(fit_x, fit_y, fit_w, inner_x)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        logistic = LogisticRegression(C=LOGISTIC_C, solver="lbfgs", max_iter=LOGISTIC_MAX_ITER,
            tol=LOGISTIC_TOL, random_state=seed)
        logistic.fit(z, fit_y, sample_weight=fit_w*len(fit_y)/fit_w.sum())
    convergence = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
    logistic_inner = logistic.predict_proba(inner_z)[:, 1]
    mlp = _mlp_fit(z, fit_y, fit_w, inner_z, inner_y, inner_w, seed)
    tree, tree_artifact = _tree_fit(z, fit_y, fit_w, inner_z, inner_y, inner_w, seed)
    inner_predictions = {**controls_inner, "logistic": logistic_inner,
        "mlp32": _mlp_predict(mlp, inner_z), "hist_boosted": tree.predict_proba(inner_z)[:, 1]}
    inner_metrics = {name: _metrics(inner_y, p, inner_w, inner) for name, p in inner_predictions.items()}
    # Outer rows are first touched after every model and stopping decision is fixed.
    outer_x, outer_y, outer_w = _stack(outer)
    outer_z = (outer_x-mean)/scale
    controls_outer, _, _ = _controls(fit_x, fit_y, fit_w, outer_x)
    outer_predictions = {**controls_outer, "logistic": logistic.predict_proba(outer_z)[:, 1],
        "mlp32": _mlp_predict(mlp, outer_z), "hist_boosted": tree.predict_proba(outer_z)[:, 1]}
    outer_metrics = {name: _metrics(outer_y, p, outer_w, outer)
                     for name, p in outer_predictions.items()}
    per_group = defaultdict(dict)
    prediction_rows = []
    cursor = 0
    for sample in outer:
        n = len(sample["y"]); k = min(sample["trip_count"], n)
        each = {}
        for name, p in outer_predictions.items():
            each[name] = _metrics(sample["y"], p[cursor:cursor+n], np.ones(n)/n, [sample])
        per_group[sample["group"]][sample["source"]] = each
        for j, movement_id in enumerate(sample["movement_ids"]):
            prediction_rows.append({"base_group": sample["group"], "source": sample["source"],
                "movement_id": movement_id, "observed_selected": bool(sample["y"][j]),
                "input_trip_count_k": k,
                "probabilities": {name: float(p[cursor+j]) for name, p in outer_predictions.items()}})
        cursor += n
    return {"policy": POLICY, "task_id": task_id, "fold": fold, "seed": seed,
        "fit_groups": fit_groups, "inner_groups": inner_groups, "outer_groups": outer_groups,
        "fit_fleets": len(fit), "inner_fleets": len(inner), "outer_fleets": len(outer),
        "fit_edges": len(fit_y), "inner_edges": len(inner_y), "outer_edges": len(outer_y),
        "fit_weights": _weight_manifest(fit), "inner_weights": _weight_manifest(inner),
        "outer_weights": _weight_manifest(outer),
        "features": FEATURES, "feature_mean_fit_only": mean.tolist(),
        "feature_scale_fit_only": scale.tolist(), "control_prevalence_fit_only": prevalence,
        "control_kind_rates_fit_only": kind_rates,
        "logistic": {"coef": logistic.coef_.tolist(), "intercept": logistic.intercept_.tolist(),
            "n_iter": logistic.n_iter_.tolist(), "convergence_warnings": convergence,
            "config": {"C": LOGISTIC_C, "solver": "lbfgs", "max_iter": LOGISTIC_MAX_ITER,
                       "tol": LOGISTIC_TOL}},
        "mlp32": {**mlp, "config": {"hidden_units": MLP_HIDDEN,
            "max_epochs": MLP_MAX_EPOCHS, "check_every_epochs": MLP_CHECK_EVERY,
            "patience_checks": MLP_PATIENCE_CHECKS, "learning_rate": MLP_LR,
            "ridge": MLP_RIDGE, "optimizer": "full-batch Adam"}},
        "hist_boosted": {**tree_artifact,
            "model_serialization": "sklearn joblib companion artifact",
            "config": {"max_leaf_nodes": TREE_MAX_LEAVES, "min_samples_leaf": TREE_MIN_LEAF,
                "max_bins": TREE_MAX_BINS, "learning_rate": TREE_LR,
                "l2_regularization": TREE_L2, "candidate_iterations": TREE_ITERATIONS,
                "early_stopping": False}},
        "inner_metrics": inner_metrics, "outer_metrics": outer_metrics,
        "outer_per_group_source": dict(per_group), "outer_predictions": prediction_rows,
        "pool_manifest_sha256": dataset["manifest_sha256"],
        "input_table_hashes": dataset["table_hashes"],
        "objective_scope": "observed feasible source-incumbent movement selection; not optimal-edge truth",
        "ranking_k_scope": "case trip count known before route solving",
        "no_outer_selection": True}, tree
