"""Frozen three-family comparison on observed TRAIN source-incumbent edges.

All candidate and checkpoint decisions use grouped inner timetables. XGBoost,
CatBoost and ExtraTrees are imported lazily so a missing pinned dependency
leaves a typed task failure receipt rather than changing the model menu.
"""
from __future__ import annotations

from collections import defaultdict
import math
import time

import numpy as np

from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous

POLICY = "physical-source-movement-families-exact128-v5"
PREFIX = 128
SEEDS = previous.SEEDS
FOLDS = previous.FOLDS
FEATURES = previous.FEATURES
FAMILIES = ("xgboost", "catboost", "extra_trees")
MENU = {
    "xgboost": ({"max_depth": 3}, {"max_depth": 6}),
    "catboost": ({"depth": 4}, {"depth": 6}),
    "extra_trees": ({"min_samples_leaf": 5}, {"min_samples_leaf": 20}),
}
MAX_ROUNDS = 800
EARLY_STOP_ROUNDS = 50
LEARNING_RATE = 0.05
EXTRA_TREES = 300


def _weighted_for_library(w):
    """Preserve v3 relative timetable/source/edge weights at mean weight one."""
    w = np.asarray(w, dtype=float)
    if w.ndim != 1 or not len(w) or not np.isfinite(w).all() or np.any(w <= 0):
        raise ValueError("Invalid positive sample weights")
    return w*len(w)/w.sum()


def select_candidate(rows):
    """Strict inner weighted log loss; menu order breaks exact ties."""
    if len(rows) != 2:
        raise ValueError("The frozen menu has exactly two candidates per family")
    losses = [row["inner_metrics"]["weighted_log_loss"] for row in rows]
    if not all(np.isfinite(loss) for loss in losses):
        raise ValueError("Candidate has no finite grouped-inner log loss")
    return min(range(2), key=lambda index: (losses[index], index))


def _json_safe(value):
    """Record complete library parameters without nonfinite JSON or opaque objects."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    return {"python_type": type(value).__name__, "repr": repr(value)}


def _probability(family, fitted, x):
    if family == "xgboost":
        best = int(fitted.best_iteration)
        return np.asarray(fitted.predict_proba(x,
            iteration_range=(0, best+1))[:, 1], dtype=float)
    if family == "catboost":
        count = int(fitted.tree_count_)
        return np.asarray(fitted.predict_proba(x,
            ntree_end=count, thread_count=1)[:, 1], dtype=float)
    if family == "extra_trees":
        return np.asarray(fitted.predict_proba(x)[:, 1], dtype=float)
    raise ValueError("Unknown frozen family")


def fit_candidate(family, config, fit_x, fit_y, fit_w,
                  inner_x, inner_y, inner_w, seed):
    """Fit one menu item; native early stopping sees only weighted inner rows."""
    started = time.monotonic()
    train_weight = _weighted_for_library(fit_w)
    validation_weight = _weighted_for_library(inner_w)
    if family == "xgboost":
        from xgboost import XGBClassifier
        fitted = XGBClassifier(objective="binary:logistic", tree_method="hist",
            n_estimators=MAX_ROUNDS, learning_rate=LEARNING_RATE,
            max_depth=config["max_depth"], max_bin=256, subsample=1.0,
            colsample_bytree=1.0, reg_lambda=1.0, eval_metric="logloss",
            early_stopping_rounds=EARLY_STOP_ROUNDS, n_jobs=1,
            random_state=seed, verbosity=0)
        fitted.fit(fit_x, fit_y, sample_weight=train_weight,
            eval_set=[(inner_x, inner_y)],
            sample_weight_eval_set=[validation_weight], verbose=False)
        curve = [float(v) for v in fitted.evals_result()["validation_0"]["logloss"]]
        best = int(fitted.best_iteration)
        checkpoint = {"best_iteration_zero_based": best,
            "selected_rounds": best+1, "stopped_rounds": len(curve),
            "inner_weighted_logloss_by_round": curve}
    elif family == "catboost":
        from catboost import CatBoostClassifier, Pool
        fitted = CatBoostClassifier(iterations=MAX_ROUNDS,
            depth=config["depth"], learning_rate=LEARNING_RATE,
            loss_function="Logloss", eval_metric="Logloss",
            l2_leaf_reg=3.0, random_strength=1.0, thread_count=1,
            random_seed=seed, task_type="CPU", allow_writing_files=False,
            verbose=False)
        fitted.fit(Pool(fit_x, fit_y, weight=train_weight),
            eval_set=Pool(inner_x, inner_y, weight=validation_weight),
            use_best_model=True, early_stopping_rounds=EARLY_STOP_ROUNDS,
            verbose=False)
        evals = fitted.get_evals_result()["validation"]["Logloss"]
        curve = [float(v) for v in evals]
        best, trees = int(fitted.best_iteration_), int(fitted.tree_count_)
        if trees != best+1:
            raise ValueError("CatBoost selected tree count differs from weighted inner best")
        checkpoint = {"best_iteration_zero_based": best,
            "selected_rounds": trees, "stopped_rounds": len(curve),
            "inner_weighted_logloss_by_round": curve}
    elif family == "extra_trees":
        from sklearn.ensemble import ExtraTreesClassifier
        fitted = ExtraTreesClassifier(n_estimators=EXTRA_TREES,
            min_samples_leaf=config["min_samples_leaf"],
            max_features=1.0, bootstrap=False, n_jobs=1, random_state=seed)
        fitted.fit(fit_x, fit_y, sample_weight=train_weight)
        checkpoint = {"selected_trees": EXTRA_TREES,
            "inner_early_stopping": False}
    else:
        raise ValueError("Unknown frozen family")
    fit_p = _probability(family, fitted, fit_x)
    inner_p = _probability(family, fitted, inner_x)
    if (not np.isfinite(fit_p).all() or not np.isfinite(inner_p).all()
            or np.any((fit_p < 0) | (fit_p > 1))
            or np.any((inner_p < 0) | (inner_p > 1))):
        raise ValueError("Candidate probabilities are invalid")
    row = {"family": family, "config": dict(config), "seed": seed,
        "fitted_parameters": _json_safe(fitted.get_params()),
        "checkpoint": checkpoint,
        "fit_metrics": frozen._metrics(fit_y, fit_p, fit_w),
        "inner_metrics": frozen._metrics(inner_y, inner_p, inner_w),
        "fit_and_inner_seconds": time.monotonic()-started,
        "thread_count": 1, "library_weight_scale": "mean sample weight one",
        "grouped_inner_early_stop_only": family in ("xgboost", "catboost")}
    return fitted, row


def run_fold(dataset, task_id, recorder=None):
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
    selected_models, candidate_rows, selection = {}, {}, {}
    for family in FAMILIES:
        models, rows = [], []
        for index, config in enumerate(MENU[family]):
            if recorder is not None:
                recorder.start_candidate(family, index, config)
            fitted, row = fit_candidate(family, config, z, fit_y, fit_w,
                inner_z, inner_y, inner_w, seed)
            row["candidate_index"] = index
            if recorder is not None:
                row["saved_model"] = recorder.candidate(family, index, fitted, row)
            models.append(fitted); rows.append(row)
        winner = select_candidate(rows)
        selected_models[family] = models[winner]
        candidate_rows[family] = rows
        selection[family] = {"candidate_index": winner,
            "inner_weighted_log_loss": rows[winner]["inner_metrics"]["weighted_log_loss"],
            "selected_config": rows[winner]["config"],
            "saved_model": rows[winner].get("saved_model")}
        if recorder is not None:
            recorder.selection(family, selection[family])
    promoted = min(FAMILIES, key=lambda family: (
        selection[family]["inner_weighted_log_loss"], FAMILIES.index(family)))
    promotion = {"family": promoted, "policy": "minimum selected-family inner weighted log loss",
        "tie_order": FAMILIES,
        "family_inner_losses": {family: selection[family]["inner_weighted_log_loss"]
                                for family in FAMILIES}}
    if recorder is not None:
        recorder.promotion(promotion)
    # load_pool has materialized all rows, but no outer x/y enters preprocessing,
    # fitting, early stopping, or candidate selection above this point.
    outer = [s for s in dataset["samples"] if s["group"] in outer_groups]
    outer_x, outer_y, outer_w = previous._stack(outer)
    outer_z = (outer_x-mean)/scale
    predictions = {family: _probability(family, selected_models[family], outer_z)
                   for family in FAMILIES}
    predictions["inner_promoted"] = predictions[promoted]
    outer_pooled_diagnostics = {family: frozen._metrics(outer_y, p, outer_w, outer)
                                for family, p in predictions.items()}
    per_group_source, per_group, prediction_rows = defaultdict(dict), {}, []
    group_buffers = defaultdict(list)
    cursor = 0
    for sample in outer:
        n = len(sample["y"]); k = min(sample["trip_count"], n)
        per_group_source[sample["group"]][sample["source"]] = {
            family: frozen._metrics(sample["y"], p[cursor:cursor+n], np.ones(n)/n, [sample])
            for family, p in predictions.items()}
        group_buffers[sample["group"]].append(sample)
        for j, movement_id in enumerate(sample["movement_ids"]):
            prediction_rows.append({"base_group": sample["group"], "source": sample["source"],
                "movement_id": movement_id, "observed_selected": bool(sample["y"][j]),
                "input_trip_count_k": k,
                "probabilities": {family: float(p[cursor+j])
                    for family, p in predictions.items()}})
        cursor += n
    for group in outer_groups:
        samples = group_buffers.get(group, [])
        per_group_source.setdefault(group, {})
        per_group[group] = {family: previous._macro_metrics([
            per_group_source[group][sample["source"]][family] for sample in samples])
            if samples else None for family in predictions}
    outer_metrics = {family: previous._macro_metrics([per_group[g][family]
        for g in outer_groups if per_group[g][family] is not None]) for family in predictions}
    common32 = sorted(g for g in outer_groups
                      if int(g.removeprefix("physical_v2_s")) < 10032)
    common32_metrics = {family: previous._macro_metrics([per_group[g][family]
        for g in common32]) for family in predictions}
    eligibility = dataset["group_eligibility"]
    result = {"policy": POLICY, "task_id": task_id, "fold": fold, "seed": seed,
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
        "candidate_menu": MENU, "candidate_rows": candidate_rows,
        "family_selection": selection, "inner_family_promotion": promotion,
        "outer_metrics": outer_metrics,
        "outer_pooled_diagnostics_secondary": outer_pooled_diagnostics,
        "outer_per_group": per_group, "outer_per_group_source": dict(per_group_source),
        "outer_predictions": prediction_rows,
        "outer_original32_common_group_metrics": common32_metrics,
        "outer_original32_common_groups": common32,
        "pool_manifest_sha256": dataset["manifest_sha256"],
        "input_table_hashes": dataset["table_hashes"],
        "objective_scope": "observed feasible source-incumbent movement selection; not optimal-edge truth",
        "ranking_k_scope": "case trip count known before route solving",
        "no_outer_selection": True}
    return result
