"""Prospective inner-only optimization-budget extension of the frozen 128-group scorer.

Only the MLP epoch cap and tree candidate grid change. All source features,
weights, partitions, seeds, learning rates, regularization, and model sizes
come from the frozen v2/v3 implementation.
"""
from __future__ import annotations

from collections import defaultdict
import time
import warnings

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous

POLICY = "physical-source-movement-scorer-budget128-v4"
PREFIX = 128
MLP_MAX_EPOCHS = 1200
TREE_ITERATIONS = (100, 200, 400, 800)
MLP_ANCHOR_EPOCH = 300
TREE_ANCHOR_ITERATIONS = 200
CHECK_EVERY = frozen.MLP_CHECK_EVERY
PATIENCE = frozen.MLP_PATIENCE_CHECKS
FOLDS = previous.FOLDS
SEEDS = previous.SEEDS
FEATURES = previous.FEATURES


def choose_inner(curve, *, index, min_improvement=0.0):
    """Select only by inner loss, preserving the frozen MLP improvement rule."""
    if not curve:
        raise ValueError("No inner-group checkpoint exists")
    selected, best, last = None, float("inf"), None
    for row in curve:
        if last is not None and row[index] <= last:
            raise ValueError("Inner checkpoints must be strictly increasing")
        last = row[index]
        loss = row["inner"]["weighted_log_loss"]
        if loss < best-min_improvement:
            selected, best = row, loss
    return selected


def _parameters(params):
    return {"W1": params[0].tolist(), "b1": params[1].tolist(),
        "W2": params[2].tolist(), "b2": float(params[3])}


def fit_mlp(x, y, w, inner_x, inner_y, inner_w, seed, progress=None):
    """Frozen full-batch Adam with a longer prospective cap and inner-only stop."""
    rng = np.random.default_rng(seed)
    W1 = rng.normal(0, 0.05, (x.shape[1], frozen.MLP_HIDDEN))
    params = [W1, np.zeros(frozen.MLP_HIDDEN),
        rng.normal(0, 0.05, frozen.MLP_HIDDEN), np.asarray(0.0)]
    first = [np.zeros_like(p) for p in params]
    second = [np.zeros_like(p) for p in params]
    best, best_loss, stale, curve = None, float("inf"), 0, []
    anchor = None
    started = time.monotonic()
    for epoch in range(1, MLP_MAX_EPOCHS+1):
        h = np.tanh(x @ params[0] + params[1])
        p = frozen._sigmoid(h @ params[2] + params[3])
        d = w*(p-y)/w.sum()
        gradient = [None]*4
        gradient[2] = h.T @ d + frozen.MLP_RIDGE*params[2]
        gradient[3] = np.asarray(d.sum())
        dh = (d[:, None]*params[2][None, :])*(1-h*h)
        gradient[0] = x.T @ dh + frozen.MLP_RIDGE*params[0]
        gradient[1] = dh.sum(axis=0)
        for j in range(4):
            first[j] = 0.9*first[j]+0.1*gradient[j]
            second[j] = 0.999*second[j]+0.001*gradient[j]**2
            adjusted = (first[j]/(1-0.9**epoch))/(np.sqrt(second[j]/(1-0.999**epoch))+1e-8)
            params[j] = params[j]-frozen.MLP_LR*adjusted
        if epoch % CHECK_EVERY:
            continue
        fit_p = frozen._sigmoid(np.tanh(x @ params[0]+params[1]) @ params[2]+params[3])
        inner_p = frozen._sigmoid(np.tanh(inner_x @ params[0]+params[1]) @ params[2]+params[3])
        fit_metric = frozen._metrics(y, fit_p, w)
        inner_metric = frozen._metrics(inner_y, inner_p, inner_w)
        loss = inner_metric["weighted_log_loss"]
        curve.append({"epoch": epoch, "fit": fit_metric, "inner": inner_metric})
        improved = loss < best_loss-1e-8
        if improved:
            best_loss, stale = loss, 0
            best = (epoch, [np.array(value, copy=True) for value in params])
        else:
            stale += 1
        if progress is not None:
            progress.mlp_curve_point({"epoch": epoch, "fit": fit_metric,
                "inner": inner_metric, "elapsed_seconds": time.monotonic()-started,
                "best_epoch_so_far": best[0] if best else None,
                "stale_checks": stale, "improved_inner_best": improved})
        if epoch == MLP_ANCHOR_EPOCH:
            anchor = {"epoch": epoch, "params": _parameters(params),
                "fit": fit_metric, "inner": inner_metric,
                "best_epoch_so_far": best[0] if best else None}
            if progress is not None:
                progress.mlp_anchor(anchor)
        if improved and progress is not None:
            progress.mlp_best({"epoch": epoch, "params": _parameters(params),
                "fit": fit_metric, "inner": inner_metric})
        if stale >= PATIENCE:
            break
    if best is None:
        raise ValueError("MLP failed to select an inner-group epoch")
    selected = choose_inner(curve, index="epoch", min_improvement=1e-8)
    if selected["epoch"] != best[0]:
        raise ValueError("Incremental MLP selection differs from inner-only curve")
    if progress is not None:
        progress.mlp_selection({"selected_epoch": best[0],
            "stopped_epoch": curve[-1]["epoch"],
            "selected_inner_log_loss": best_loss,
            "params": _parameters(best[1])})
    return {"selected_epoch": best[0], "stopped_epoch": curve[-1]["epoch"],
        "params": _parameters(best[1]), "curve": curve,
        "selected_inner_log_loss": best_loss, "anchor_at_300": anchor}


def fit_tree(x, y, w, inner_x, inner_y, inner_w, seed, progress=None):
    """Frozen HistGBDT settings; four prospective iteration candidates."""
    curve, candidates = [], {}
    for count in TREE_ITERATIONS:
        started = time.monotonic()
        tree = HistGradientBoostingClassifier(loss="log_loss", max_iter=count,
            max_leaf_nodes=frozen.TREE_MAX_LEAVES,
            min_samples_leaf=frozen.TREE_MIN_LEAF, max_bins=frozen.TREE_MAX_BINS,
            learning_rate=frozen.TREE_LR, l2_regularization=frozen.TREE_L2,
            early_stopping=False, random_state=seed)
        tree.fit(x, y, sample_weight=w*len(y)/w.sum())
        row = {"iterations": count,
            "fit": frozen._metrics(y, tree.predict_proba(x)[:, 1], w),
            "inner": frozen._metrics(inner_y, tree.predict_proba(inner_x)[:, 1], inner_w),
            "fit_and_inner_seconds": time.monotonic()-started}
        curve.append(row)
        candidates[count] = tree
        if progress is not None:
            progress.tree_candidate(count, tree, row)
    selected = choose_inner(curve, index="iterations")
    if progress is not None:
        progress.tree_selection({"selected_iterations": selected["iterations"],
            "selected_inner_log_loss": selected["inner"]["weighted_log_loss"]})
    return candidates[selected["iterations"]], {"selected_iterations": selected["iterations"],
        "selected_inner_log_loss": selected["inner"]["weighted_log_loss"],
        "curve": curve, "anchor_at_200": next(row for row in curve
            if row["iterations"] == TREE_ANCHOR_ITERATIONS)}


def run_fold(dataset, task_id, progress=None):
    if len(dataset["groups"]) != PREFIX or task_id not in range(FOLDS*len(SEEDS)):
        raise ValueError("Only exact-128 TRAIN and the frozen 12 tasks are declared")
    fold, seed_index = divmod(task_id, len(SEEDS)); seed = SEEDS[seed_index]
    fit_groups, inner_groups, outer_groups = previous.grouped_split(dataset["groups"], fold)
    fit = [s for s in dataset["samples"] if s["group"] in fit_groups]
    inner = [s for s in dataset["samples"] if s["group"] in inner_groups]
    fit_x, fit_y, fit_w = previous._stack(fit)
    inner_x, inner_y, inner_w = previous._stack(inner)
    mean, scale = frozen._preprocess(fit_x)
    z, inner_z = (fit_x-mean)/scale, (inner_x-mean)/scale
    controls_inner, prevalence, kind_rates = frozen._controls(fit_x, fit_y, fit_w, inner_x)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        logistic = LogisticRegression(C=frozen.LOGISTIC_C, solver="lbfgs",
            max_iter=frozen.LOGISTIC_MAX_ITER, tol=frozen.LOGISTIC_TOL, random_state=seed)
        logistic.fit(z, fit_y, sample_weight=fit_w*len(fit_y)/fit_w.sum())
    convergence = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
    mlp = fit_mlp(z, fit_y, fit_w, inner_z, inner_y, inner_w, seed, progress)
    tree, tree_artifact = fit_tree(z, fit_y, fit_w, inner_z, inner_y, inner_w, seed, progress)
    inner_predictions = {**controls_inner, "logistic": logistic.predict_proba(inner_z)[:, 1],
        "mlp32": frozen._mlp_predict(mlp, inner_z), "hist_boosted": tree.predict_proba(inner_z)[:, 1]}
    inner_metrics = {name: frozen._metrics(inner_y, p, inner_w, inner)
                     for name, p in inner_predictions.items()}
    # The loader has materialized the admitted pool, but run_fold first accesses
    # outer x/y here, after both inner checkpoint decisions are persisted.
    outer = [s for s in dataset["samples"] if s["group"] in outer_groups]
    outer_x, outer_y, outer_w = previous._stack(outer)
    outer_z = (outer_x-mean)/scale
    controls_outer, _, _ = frozen._controls(fit_x, fit_y, fit_w, outer_x)
    outer_predictions = {**controls_outer, "logistic": logistic.predict_proba(outer_z)[:, 1],
        "mlp32": frozen._mlp_predict(mlp, outer_z), "hist_boosted": tree.predict_proba(outer_z)[:, 1]}
    outer_pooled_diagnostics = {name: frozen._metrics(outer_y, p, outer_w, outer)
                                for name, p in outer_predictions.items()}
    per_group_source, per_group, prediction_rows = defaultdict(dict), {}, []
    group_buffers = defaultdict(list)
    cursor = 0
    for sample in outer:
        n = len(sample["y"]); k = min(sample["trip_count"], n)
        per_group_source[sample["group"]][sample["source"]] = {
            name: frozen._metrics(sample["y"], p[cursor:cursor+n], np.ones(n)/n, [sample])
            for name, p in outer_predictions.items()}
        group_buffers[sample["group"]].append((sample, cursor, n))
        for j, movement_id in enumerate(sample["movement_ids"]):
            prediction_rows.append({"base_group": sample["group"], "source": sample["source"],
                "movement_id": movement_id, "observed_selected": bool(sample["y"][j]),
                "input_trip_count_k": k,
                "probabilities": {name: float(p[cursor+j]) for name, p in outer_predictions.items()}})
        cursor += n
    for group in outer_groups:
        chunks = group_buffers.get(group, [])
        per_group_source.setdefault(group, {})
        per_group[group] = {name: previous._macro_metrics([
            per_group_source[group][s["source"]][name] for s, _, _ in chunks])
            if chunks else None for name in outer_predictions}
    outer_metrics = {name: previous._macro_metrics([per_group[g][name] for g in outer_groups
                                           if per_group[g][name] is not None])
                     for name in outer_predictions}
    common_groups = sorted(g for g in outer_groups
                           if int(g.removeprefix("physical_v2_s")) < 10032)
    common32_metrics = {name: previous._macro_metrics([per_group[g][name] for g in common_groups])
                        for name in outer_predictions}
    eligibility = dataset["group_eligibility"]
    return {"policy": POLICY, "task_id": task_id, "fold": fold, "seed": seed,
        "prefix_groups_intended": PREFIX, "fit_groups": fit_groups,
        "inner_groups": inner_groups, "outer_groups": outer_groups,
        "fit_eligibility": previous._partition_eligibility(eligibility, fit_groups),
        "inner_eligibility": previous._partition_eligibility(eligibility, inner_groups),
        "outer_eligibility": previous._partition_eligibility(eligibility, outer_groups),
        "fit_fleets": len(fit), "inner_fleets": len(inner), "outer_fleets": len(outer),
        "fit_edges": len(fit_y), "inner_edges": len(inner_y), "outer_edges": len(outer_y),
        "fit_weights": previous._weight_manifest(fit),
        "inner_weights": previous._weight_manifest(inner),
        "outer_weights": previous._weight_manifest(outer),
        "features": FEATURES, "feature_mean_fit_only": mean.tolist(),
        "feature_scale_fit_only": scale.tolist(),
        "control_prevalence_fit_only": prevalence,
        "control_kind_rates_fit_only": kind_rates,
        "logistic": {"coef": logistic.coef_.tolist(), "intercept": logistic.intercept_.tolist(),
            "n_iter": logistic.n_iter_.tolist(), "convergence_warnings": convergence,
            "config": {"C": frozen.LOGISTIC_C, "solver": "lbfgs",
                "max_iter": frozen.LOGISTIC_MAX_ITER, "tol": frozen.LOGISTIC_TOL}},
        "mlp32": {**mlp, "config": {"hidden_units": frozen.MLP_HIDDEN,
            "max_epochs": MLP_MAX_EPOCHS, "anchor_epoch": MLP_ANCHOR_EPOCH,
            "check_every_epochs": CHECK_EVERY, "patience_checks": PATIENCE,
            "learning_rate": frozen.MLP_LR, "ridge": frozen.MLP_RIDGE,
            "optimizer": "full-batch Adam"}},
        "hist_boosted": {**tree_artifact,
            "model_serialization": "sklearn joblib companion artifact",
            "config": {"max_leaf_nodes": frozen.TREE_MAX_LEAVES,
                "min_samples_leaf": frozen.TREE_MIN_LEAF, "max_bins": frozen.TREE_MAX_BINS,
                "learning_rate": frozen.TREE_LR, "l2_regularization": frozen.TREE_L2,
                "candidate_iterations": TREE_ITERATIONS,
                "anchor_iterations": TREE_ANCHOR_ITERATIONS,
                "early_stopping": False}},
        "inner_metrics": inner_metrics, "outer_metrics": outer_metrics,
        "outer_pooled_diagnostics_secondary": outer_pooled_diagnostics,
        "outer_per_group": per_group, "outer_per_group_source": dict(per_group_source),
        "outer_predictions": prediction_rows,
        "outer_original32_common_group_metrics": common32_metrics,
        "outer_original32_common_groups": common_groups,
        "pool_manifest_sha256": dataset["manifest_sha256"],
        "input_table_hashes": dataset["table_hashes"],
        "objective_scope": "observed feasible source-incumbent movement selection; not optimal-edge truth",
        "ranking_k_scope": "case trip count known before route solving",
        "no_outer_selection": True,
        "optimization_budget_change_only": True}, tree
