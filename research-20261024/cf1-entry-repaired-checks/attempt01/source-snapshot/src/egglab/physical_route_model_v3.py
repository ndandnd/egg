"""Exact-prefix grouped 64/128 source-movement learning curves.

Frozen architecture and fit routines are imported from v2; only admission,
registry-aware splitting, censor accounting, and timetable weights differ.
"""
from __future__ import annotations

from collections import defaultdict
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from egglab import learned_proposals as edge
from egglab import native_recharge as nr
from egglab import physical_learning_cases as physical
from egglab import physical_route_model_v2 as frozen
from experiments import pool_physical_route_training_v3 as pool

POLICY = "physical-source-movement-scorer-exact-prefix-v3"
FEATURES = frozen.FEATURES
FOLDS = frozen.FOLDS
SEEDS = frozen.SEEDS


def load_pool(path, *, expected_manifest_sha256, prefix):
    if prefix not in pool.OUTPUTS:
        raise ValueError("Undeclared exact prefix")
    path = Path(path).resolve()
    if frozen._sha(path / "pool_manifest.json") != expected_manifest_sha256:
        raise ValueError("Pinned pooled training manifest hash changed")
    manifest = frozen._read(path / "pool_manifest.json")
    if (manifest.get("policy") != pool.POLICY or manifest.get("train_only") is not True
            or manifest.get("base_ids") != list(range(10000, 10000 + prefix))
            or manifest.get("independent_groups_intended") != prefix
            or len(manifest.get("admitted_shards", ())) != prefix // 8
            or [r.get("shard") for r in manifest["admitted_shards"]] != list(range(prefix // 8))):
        raise ValueError("Unknown or non-TRAIN exact-prefix pooled dataset")
    for name in pool.TABLES:
        if manifest.get("output_hashes", {}).get(name) != frozen._sha(path / name):
            raise ValueError("Pooled input table hash changed: " + name)
    cases = frozen._rows(path / "cases.jsonl")
    source_inputs = frozen._rows(path / "source_inputs.jsonl")
    if len(cases) != prefix or len(source_inputs) != manifest.get("source_fleets_observed"):
        raise ValueError("Pooled case/source counts changed")
    by_group = {}
    for row in cases:
        group, base_id = row.get("base_group"), row.get("base_id")
        if (group in by_group or base_id not in range(10000, 10000 + prefix)
                or group != f"physical_v2_s{base_id}" or row.get("split") != "train"
                or row.get("generator") != physical.GENERATOR
                or row.get("physical_profile") != physical.assignment(base_id)):
            raise ValueError("Duplicate/unknown/non-TRAIN pooled group")
        case = edge.case_from_dict(row["case"])
        if case.identity() != row.get("case_identity") or case.identity() != physical.make_case(base_id).identity():
            raise ValueError("Pooled case identity changed")
        by_group[group] = (row, case)
    if {row[0]["base_id"] for row in by_group.values()} != set(range(10000, 10000 + prefix)):
        raise ValueError("Missing registry TRAIN base ID")
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
    eligibility = manifest.get("group_eligibility")
    if not isinstance(eligibility, list) or len(eligibility) != prefix:
        raise ValueError("Missing explicit group eligibility")
    for entry, base_id in zip(eligibility, range(10000, 10000 + prefix)):
        group = f"physical_v2_s{base_id}"
        observed = [s for s in ("source0", "source1") if (group, s) in seen]
        if (entry.get("base_id") != base_id or entry.get("base_group") != group
                or entry.get("intended_source_count") != 2
                or entry.get("observed_source_count") != len(observed)
                or entry.get("observed_sources") != observed
                or entry.get("missing_source_labels") != [s for s in ("source0", "source1") if s not in observed]
                or entry.get("eligible_for_observed_source_supervision") is not bool(observed)
                or entry.get("eligible_for_full_pair_supervision") is not (len(observed) == 2)):
            raise ValueError("Group/source eligibility inconsistent with input rows")
    if (manifest.get("groups_eligible_observed") != sum(bool(r["observed_source_count"]) for r in eligibility)
            or manifest.get("groups_eligible_full_pair") != sum(r["observed_source_count"] == 2 for r in eligibility)
            or manifest.get("source_fleets_intended") != 2*prefix):
        raise ValueError("Pooled eligibility totals changed")
    return {"groups": tuple(sorted(by_group)), "samples": samples,
        "group_eligibility": eligibility, "manifest_sha256": expected_manifest_sha256,
        "table_hashes": {name: frozen._sha(path / name) for name in pool.TABLES}}


def grouped_split(groups, fold):
    if len(groups) not in (64, 128) or len(set(groups)) != len(groups) or fold not in range(FOLDS):
        raise ValueError("Expected 64/128 unique registry groups and four folds")
    prefix = len(groups)
    ordered = tuple(sorted(groups))
    if ordered != tuple(f"physical_v2_s{i}" for i in range(10000, 10000 + prefix)):
        raise ValueError("Groups must be the exact sorted TRAIN prefix")
    outer = tuple(g for i, g in enumerate(ordered) if i % FOLDS == fold)
    training = tuple(g for g in ordered if g not in outer)
    inner = training[2::6]
    fit = tuple(g for g in training if g not in inner)
    expected = (40, 8, 16) if prefix == 64 else (80, 16, 32)
    if (len(fit), len(inner), len(outer)) != expected:
        raise ValueError("Grouped fit/inner/outer sizes changed")
    return fit, inner, outer


def _stack(samples):
    """Each eligible timetable, then each observed fleet, then each edge weighs equally."""
    if not samples:
        raise ValueError("Partition has no eligible observed source groups")
    counts = defaultdict(int)
    for sample in samples:
        counts[sample["group"]] += 1
    n_groups = len(counts)
    x = np.concatenate([s["x"] for s in samples])
    y = np.concatenate([s["y"] for s in samples])
    w = np.concatenate([np.full(len(s["y"]), 1/(n_groups*counts[s["group"]]*len(s["y"])))
                        for s in samples])
    return x, y, w


def _weight_manifest(samples):
    counts = defaultdict(int)
    for sample in samples:
        counts[sample["group"]] += 1
    n_groups = len(counts)
    return [{"base_group": s["group"], "source": s["source"],
        "movement_rows": len(s["y"]), "group_weight": 1/n_groups,
        "observed_source_count_in_group": counts[s["group"]],
        "fleet_weight": 1/(n_groups*counts[s["group"]]),
        "per_movement_weight": 1/(n_groups*counts[s["group"]]*len(s["y"]))}
        for s in samples]


def _partition_eligibility(entries, groups):
    selected = [e for e in entries if e["base_group"] in groups]
    return {"intended_groups": len(selected),
        "eligible_observed_groups": sum(e["eligible_for_observed_source_supervision"] for e in selected),
        "eligible_full_pair_groups": sum(e["eligible_for_full_pair_supervision"] for e in selected),
        "intended_source_fleets": 2*len(selected),
        "observed_source_fleets": sum(e["observed_source_count"] for e in selected),
        "per_group": selected}


PERFORMANCE_METRICS = (
    "weighted_log_loss", "weighted_brier", "weighted_accuracy_at_fixed_half",
    "weighted_positive_recall_at_fixed_half", "weighted_negative_recall_at_fixed_half",
    "average_precision", "positive_rate", "input_trip_count_topk_recall_mean_by_fleet",
)


def _macro_metrics(rows):
    """Mean sources within timetable, then mean eligible timetables."""
    output = {"eligible_units": len(rows)}
    for key in PERFORMANCE_METRICS:
        values = [r[key] for r in rows if r[key] is not None]
        output[key] = float(np.mean(values)) if values else None
        output[key + "_eligible_units"] = len(values)
    for key in ("positive_count", "negative_count"):
        output[key] = sum(r[key] for r in rows)
    return output


def run_fold(dataset, task_id):
    if task_id not in range(FOLDS*len(SEEDS)):
        raise ValueError("Undeclared 12-task grouped route experiment")
    fold, seed_index = divmod(task_id, len(SEEDS)); seed = SEEDS[seed_index]
    fit_groups, inner_groups, outer_groups = grouped_split(dataset["groups"], fold)
    fit = [s for s in dataset["samples"] if s["group"] in fit_groups]
    inner = [s for s in dataset["samples"] if s["group"] in inner_groups]
    outer = [s for s in dataset["samples"] if s["group"] in outer_groups]
    # _stack fails explicitly for any entirely censored partition.
    fit_x, fit_y, fit_w = _stack(fit)
    inner_x, inner_y, inner_w = _stack(inner)
    mean, scale = frozen._preprocess(fit_x)
    z, inner_z = (fit_x-mean)/scale, (inner_x-mean)/scale
    controls_inner, prevalence, kind_rates = frozen._controls(fit_x, fit_y, fit_w, inner_x)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        logistic = LogisticRegression(C=frozen.LOGISTIC_C, solver="lbfgs",
            max_iter=frozen.LOGISTIC_MAX_ITER, tol=frozen.LOGISTIC_TOL, random_state=seed)
        logistic.fit(z, fit_y, sample_weight=fit_w*len(fit_y)/fit_w.sum())
    convergence = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
    mlp = frozen._mlp_fit(z, fit_y, fit_w, inner_z, inner_y, inner_w, seed)
    tree, tree_artifact = frozen._tree_fit(z, fit_y, fit_w, inner_z, inner_y, inner_w, seed)
    inner_predictions = {**controls_inner, "logistic": logistic.predict_proba(inner_z)[:, 1],
        "mlp32": frozen._mlp_predict(mlp, inner_z), "hist_boosted": tree.predict_proba(inner_z)[:, 1]}
    inner_metrics = {name: frozen._metrics(inner_y, p, inner_w, inner)
                     for name, p in inner_predictions.items()}
    # Outer labels enter only after every fit and inner checkpoint choice is frozen.
    outer_x, outer_y, outer_w = _stack(outer)
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
        per_group_source.setdefault(group, {})
        chunks = group_buffers.get(group, [])
        per_group[group] = {name: _macro_metrics([
            per_group_source[group][s["source"]][name] for s, _, _ in chunks])
            if chunks else None for name in outer_predictions}
    outer_metrics = {name: _macro_metrics([per_group[g][name] for g in outer_groups
                                           if per_group[g][name] is not None])
                     for name in outer_predictions}
    common32 = [s for s in outer if int(s["group"].removeprefix("physical_v2_s")) < 10032]
    common32_metrics = {}
    common32_pooled_diagnostics = {}
    if common32:
        _, cy, cw = _stack(common32)
        common32_indexes = np.concatenate([np.arange(start, start+len(s["y"]))
            for s, start in ((s, sum(len(o["y"]) for o in outer[:i]))
                             for i, s in enumerate(outer))
            if int(s["group"].removeprefix("physical_v2_s")) < 10032])
        common32_pooled_diagnostics = {name: frozen._metrics(cy, p[common32_indexes], cw, common32)
                                       for name, p in outer_predictions.items()}
        common_groups = sorted({s["group"] for s in common32})
        common32_metrics = {name: _macro_metrics([per_group[g][name] for g in common_groups])
                            for name in outer_predictions}
    eligibility = dataset["group_eligibility"]
    return {"policy": POLICY, "task_id": task_id, "fold": fold, "seed": seed,
        "prefix_groups_intended": len(dataset["groups"]),
        "fit_groups": fit_groups, "inner_groups": inner_groups, "outer_groups": outer_groups,
        "fit_eligibility": _partition_eligibility(eligibility, fit_groups),
        "inner_eligibility": _partition_eligibility(eligibility, inner_groups),
        "outer_eligibility": _partition_eligibility(eligibility, outer_groups),
        "fit_fleets": len(fit), "inner_fleets": len(inner), "outer_fleets": len(outer),
        "fit_edges": len(fit_y), "inner_edges": len(inner_y), "outer_edges": len(outer_y),
        "fit_weights": _weight_manifest(fit), "inner_weights": _weight_manifest(inner),
        "outer_weights": _weight_manifest(outer),
        "features": FEATURES, "feature_mean_fit_only": mean.tolist(),
        "feature_scale_fit_only": scale.tolist(), "control_prevalence_fit_only": prevalence,
        "control_kind_rates_fit_only": kind_rates,
        "logistic": {"coef": logistic.coef_.tolist(), "intercept": logistic.intercept_.tolist(),
            "n_iter": logistic.n_iter_.tolist(), "convergence_warnings": convergence,
            "config": {"C": frozen.LOGISTIC_C, "solver": "lbfgs",
                "max_iter": frozen.LOGISTIC_MAX_ITER, "tol": frozen.LOGISTIC_TOL}},
        "mlp32": {**mlp, "config": {"hidden_units": frozen.MLP_HIDDEN,
            "max_epochs": frozen.MLP_MAX_EPOCHS, "check_every_epochs": frozen.MLP_CHECK_EVERY,
            "patience_checks": frozen.MLP_PATIENCE_CHECKS, "learning_rate": frozen.MLP_LR,
            "ridge": frozen.MLP_RIDGE, "optimizer": "full-batch Adam"}},
        "hist_boosted": {**tree_artifact,
            "model_serialization": "sklearn joblib companion artifact",
            "config": {"max_leaf_nodes": frozen.TREE_MAX_LEAVES,
                "min_samples_leaf": frozen.TREE_MIN_LEAF, "max_bins": frozen.TREE_MAX_BINS,
                "learning_rate": frozen.TREE_LR, "l2_regularization": frozen.TREE_L2,
                "candidate_iterations": frozen.TREE_ITERATIONS, "early_stopping": False}},
        "inner_metrics": inner_metrics, "outer_metrics": outer_metrics,
        "outer_pooled_diagnostics_secondary": outer_pooled_diagnostics,
        "outer_per_group": per_group, "outer_per_group_source": dict(per_group_source),
        "outer_predictions": prediction_rows,
        "outer_original32_common_group_metrics": common32_metrics,
        "outer_original32_pooled_diagnostics_secondary": common32_pooled_diagnostics,
        "outer_original32_common_groups": sorted({s["group"] for s in common32}),
        "pool_manifest_sha256": dataset["manifest_sha256"],
        "input_table_hashes": dataset["table_hashes"],
        "objective_scope": "observed feasible source-incumbent movement selection; not optimal-edge truth",
        "ranking_k_scope": "case trip count known before route solving",
        "no_outer_selection": True}, tree
