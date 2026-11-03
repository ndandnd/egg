"""Read-only saved-model replay of original v5 successes plus declared recovery.

No estimator fit/partial_fit API is called. Refuses incomplete collection before
opening any recovered scientific result; writes only the final verification JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import time

import catboost
import joblib
import numpy as np
import xgboost

from egglab import physical_route_model_families_v5 as families
from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool
from experiments import recover_physical_route_model_families_v5 as recovery
from experiments import train_physical_route_model_families_v5 as cli

ROOT = base.ROOT
DOC = ROOT / "research-20260930/learning-campaign"
ORIGINAL = ROOT / "result/physical_learning/20260930-route-model128-families-v5"
RECOVERED = ROOT / "result/physical_learning/20260930-route-model128-families-v5-recovery1"
OUTPUT = DOC / "ROUTE_FAMILIES_V5_REPLAY.json"
NAMES = (*families.FAMILIES, "inner_promoted")
METRICS = previous.PERFORMANCE_METRICS
COMPARE_METRICS = ("weighted_log_loss", "weighted_brier", "average_precision",
    "input_trip_count_topk_recall_mean_by_fleet", "weighted_positive_recall_at_fixed_half",
    "weighted_negative_recall_at_fixed_half")
HIGH = set(COMPARE_METRICS) - {"weighted_log_loss", "weighted_brier"}
PINNED = {"sklearn": "1.7.2", "joblib": "1.5.2", "numpy": "1.26.4", "scipy": "1.13.1",
          "xgboost": "3.0.5", "catboost": "1.2.8"}
BASELINES = {"v3": ("ROUTE_MODEL128_REPLAY.json", "9f274bd9106bc0fa8035dc381e6b698bcf5c3ba6ae19179ea11ecd0767c92192"),
    "v4": ("ROUTE_MODEL128_BUDGET_V4_REPLAY.json", "acf9d7f3d6cce9ba5be142c2ef6899cbb4eec155d6070d226889e5fc8d849053")}
TOL = 1e-8


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(a, b, label, tolerance=TOL):
    """Compare complete metric/provenance structures, including count denominators."""
    if isinstance(a, dict) and isinstance(b, dict):
        require(set(a) == set(b), f"{label}: dictionary keys differ")
        for key in a:
            same(a[key], b[key], f"{label}/{key}", tolerance)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        require(len(a) == len(b), f"{label}: sequence length differs")
        for i, (aa, bb) in enumerate(zip(a, b)):
            same(aa, bb, f"{label}/{i}", tolerance)
    elif isinstance(a, (int, float, np.number)) and isinstance(b, (int, float, np.number)):
        require(np.isclose(a, b, atol=tolerance, rtol=tolerance), f"{label}: numeric mismatch {a} vs {b}")
    else:
        require(a == b, f"{label}: value mismatch")


def summary(values):
    values = [float(v) for v in values if v is not None]
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "min": min(values) if values else None, "max": max(values) if values else None}


def probability_error(native, saved, family):
    """XGBoost probabilities are float32; bound drift by representable ULPs."""
    error = abs(float(native)-saved)
    strict = bool(np.isclose(native, saved, atol=TOL, rtol=TOL))
    if family == "xgboost":
        a, b = np.float32(native), np.float32(saved)
        require(float(a) == float(native) and float(b) == saved, "XGBoost output no longer float32-representable")
        ulps = abs(int(a.view(np.uint32))-int(b.view(np.uint32)))
        require(ulps <= 2, f"XGBoost probability differs by {ulps} float32 ULPs")
    else:
        ulps = None
        same(float(native), saved, f"{family} saved probability", 1e-9)
    return error, ulps, strict


def metric_errors(native, saved):
    return {m: abs(native[m]-saved[m]) if native.get(m) is not None and saved.get(m) is not None else None
            for m in METRICS if m in native and m in saved}


def wrapper(root, task_id, array):
    paths = list(root.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
    require(len(paths) == 1, f"Task{task_id} requires one wrapper receipt")
    row = read(paths[0])
    require(row["task_id"] == task_id and row["array_job_id"] == array
            and row["pool_manifest_sha256"] == recovery.POOL_SHA, "Wrapper task/array/pool mismatch")
    return paths[0], row


def gate():
    """Completion/source/status controls first; no recovered result is decoded here."""
    launches = {array: read(DOC / f"LAUNCH_{array}.json") for array in ("720831", "722702")}
    same(launches["722702"]["recovery_task_ids"], recovery.FAILED_TASKS, "recovered IDs")
    same(launches["722702"]["original_retained_success_task_ids"], recovery.COMPLETED_TASKS, "retained IDs")
    require(launches["722702"]["scientific_settings_changed"] is False, "Scientific settings changed")
    require(launches["720831"]["source_commit"] == recovery.ORIGINAL_COMMIT, "Original source commit differs")
    for root, ids in ((ORIGINAL, range(12)), (RECOVERED, recovery.FAILED_TASKS)):
        actual = sorted(p.name for p in root.glob("task[0-9][0-9]") if p.is_dir())
        require(actual == [f"task{i:02d}" for i in ids], "Incomplete or extra task directory set")
    failures = []
    for task_id in recovery.FAILED_TASKS:
        lineage = recovery.original_evidence(ORIGINAL, task_id)
        p, row = wrapper(ORIGINAL, task_id, "720831")
        failures.append({**lineage, "wrapper_returncode": row["returncode"],
            "wrapper_elapsed_seconds": row["elapsed_seconds"],
            "failure_artifact_hashes": {str(q.relative_to(ORIGINAL)): base.sha(q)
                for q in sorted((ORIGINAL/f"task{task_id:02d}").rglob("*")) if q.is_file()}})
    for task_id in range(12):
        root = ORIGINAL if task_id in recovery.COMPLETED_TASKS else RECOVERED
        array = "720831" if root == ORIGINAL else "722702"
        folder = root / f"task{task_id:02d}"
        receipt = read(folder / "receipt.json")
        _, w = wrapper(root, task_id, array)
        require(receipt["status"] == "completed" and receipt["task_id"] == task_id
                and (folder / "result.json").is_file() and w["returncode"] == 0
                and w["timeout_exit"] is False, "Incomplete/failed selected task collection")
        if array == "722702":
            runtime = root / f"task{task_id:02d}.runtime"
            rr = read(runtime / "recovery_receipt.json")
            require(rr["status"] == "completed" and rr["returncode"] == 0 and rr["task_id"] == task_id,
                    "Recovery runtime did not complete")
    return launches, failures


def runtime_lineage(task_id, launches):
    directory = RECOVERED / f"task{task_id:02d}.runtime"
    launch = read(directory / "recovery_launch.json")
    original = recovery.original_evidence(ORIGINAL, task_id)
    for key in ("original_task_id", "original_array_job_id", "original_source_commit", "launch_sha256",
                "source_identity_sha256", "wrapper_receipt_sha256", "original_source_hashes"):
        same(launch[key], original[key], f"recovery original linkage/{key}")
    require(launch["hostname"].split(".")[0] == "unicorn-cpu-75"
            and launch["recovery_source_commit"] == launches["722702"]["source_commit"], "Recovery source/node differs")
    require(set(launch["recovery_source_hashes"]) == set(recovery.RECOVERY_SOURCES), "Recovery source-path set differs")
    for name, digest in launch["recovery_source_hashes"].items():
        require(base.sha(ROOT/name) == digest, f"Recovery source changed: {name}")
    stages = {}
    for stage in ("import_xgboost", "import_catboost", "tiny_native_fit", "frozen_training"):
        row = read(directory / f"{stage}_receipt.json")
        require(row["stage"] == stage and row["returncode"] == 0
                and row["timeout"] is False and row["signal"] is None, f"Failed recovery stage: {stage}")
        for suffix in ("stdout", "stderr"):
            require(base.sha(directory/f"{stage}.{suffix}") == row[f"{suffix}_sha256"], "Recovery stream hash differs")
        require(read(directory/f"{stage}_start.json")["stage"] == stage, "Recovery stage marker differs")
        stages[stage] = row
    return {"recovery_launch_sha256": base.sha(directory/"recovery_launch.json"), "stages": stages,
        "recovery_receipt": read(directory/"recovery_receipt.json"),
        "runtime_artifact_hashes": {p.name: base.sha(p) for p in sorted(directory.iterdir()) if p.is_file()}}


def load_candidate(family, row, path):
    """Load trusted, hash-checked artifacts; force the declared prediction worker."""
    checkpoint = row["checkpoint"]
    require(row["thread_count"] == 1 and row["library_weight_scale"] == "mean sample weight one", "Candidate thread/weight policy differs")
    if family == "xgboost":
        config = dict(row["fitted_parameters"])
        if config.get("missing") == "nan":
            config["missing"] = np.nan
        fitted = xgboost.XGBClassifier(**config)
        fitted.load_model(path)
        fitted.set_params(n_jobs=1)
        require(fitted.best_iteration == checkpoint["best_iteration_zero_based"], "XGBoost best iteration differs")
        require(fitted.get_booster().num_boosted_rounds() == checkpoint["stopped_rounds"], "XGBoost stored rounds differ")
    elif family == "catboost":
        fitted = catboost.CatBoostClassifier(thread_count=1)
        fitted.load_model(str(path))
        require(fitted.tree_count_ == checkpoint["selected_rounds"], "CatBoost retained trees differ")
        require(fitted.get_best_iteration() == checkpoint["best_iteration_zero_based"], "CatBoost best iteration differs")
    else:
        fitted = joblib.load(path)
        require(type(fitted).__name__ == "ExtraTreesClassifier" and fitted.n_jobs == 1
                and len(fitted.estimators_) == 300, "ExtraTrees model/thread/tree count differs")
        same(families._json_safe(fitted.get_params()), row["fitted_parameters"], "ExtraTrees parameters")
    if family != "extra_trees":
        curve = np.asarray(checkpoint["inner_weighted_logloss_by_round"])
        require(len(curve) == checkpoint["stopped_rounds"] <= 800 and np.isfinite(curve).all(), "Inner curve differs")
        best = checkpoint["best_iteration_zero_based"]
        require(best == int(np.argmin(curve)) and checkpoint["selected_rounds"] == best+1,
                "Native checkpoint was not chosen by inner curve")
        require(len(curve) == 800 or len(curve) == best+1+50, "Native patience/round cap differs")
        same(float(curve[best]), row["inner_metrics"]["weighted_log_loss"], "Native inner curve vs recomputed loss", 1e-6)
    return fitted


def verify_task(task_id, dataset, launches):
    root = ORIGINAL if task_id in recovery.COMPLETED_TASKS else RECOVERED
    array = "720831" if root == ORIGINAL else "722702"
    folder = root / f"task{task_id:02d}"
    receipt, result, identity = [read(folder/name) for name in ("receipt.json", "result.json", "source_identity.json")]
    wp, w = wrapper(root, task_id, array)
    require(receipt["result_sha256"] == base.sha(folder/"result.json")
            and receipt["source_identity_sha256"] == base.sha(folder/"source_identity.json"), "Result/identity hash differs")
    for row in (receipt, result, identity):
        require(row["source_commit"] == launches[array]["source_commit"]
                and row["pool_manifest_sha256"] == recovery.POOL_SHA
                and row["runtime_versions"] == PINNED, "Task source/runtime/pool differs")
        same(row["source_hashes"], identity["source_hashes"], "Source-hash lineage")
    require(set(identity["source_hashes"]) == set(recovery.FROZEN_SOURCE_FILES), "Frozen source-path set differs")
    for name, digest in identity["source_hashes"].items():
        require(base.sha(ROOT/name) == digest, f"Frozen source changed: {name}")
    require(result["policy"] == receipt["policy"] == families.POLICY
            and result["no_outer_selection"] is True and result["task_id"] == task_id
            and result["prefix_groups_intended"] == receipt["prefix_groups_intended"] == 128
            and receipt["all_candidate_fit_time_included_in_wall_seconds"] is True, "Policy/task/time scope differs")
    launch = read(folder/"launch.json")
    require(launch["policy"] == families.POLICY and launch["task_id"] == task_id
            and launch["pool_manifest_sha256"] == recovery.POOL_SHA, "Training launch marker differs")
    same(result["candidate_menu"], families.MENU, "Frozen candidate menu")
    same(result["features"], families.FEATURES, "Frozen features")
    same(result["input_table_hashes"], dataset["table_hashes"], "Input tables")
    fit_g, inner_g, outer_g = previous.grouped_split(dataset["groups"], task_id//3)
    require(result["fold"] == task_id//3 and result["seed"] == families.SEEDS[task_id%3], "Fold/seed differs")
    partitions, arrays = {}, {}
    for part, groups in (("fit", fit_g), ("inner", inner_g), ("outer", outer_g)):
        same(result[f"{part}_groups"], groups, f"{part} groups")
        samples = [s for s in dataset["samples"] if s["group"] in groups]
        partitions[part] = samples
        arrays[part] = previous._stack(samples)
        same(result[f"{part}_weights"], previous._weight_manifest(samples), f"{part} weights")
        same(result[f"{part}_eligibility"], previous._partition_eligibility(dataset["group_eligibility"], groups), f"{part} eligibility")
        require(result[f"{part}_fleets"] == len(samples) and result[f"{part}_edges"] == len(arrays[part][1]), "Source/edge denominator differs")
    mean, scale = frozen._preprocess(arrays["fit"][0])
    same(mean.tolist(), result["feature_mean_fit_only"], "Fit-only mean")
    same(scale.tolist(), result["feature_scale_fit_only"], "Fit-only scale")
    z = {part: (values[0]-mean)/scale for part, values in arrays.items()}
    progress = folder/"inner_progress"
    claimed = receipt["candidate_and_inner_progress_hashes"]
    actual = {p.name: base.sha(p) for p in sorted(progress.iterdir()) if p.is_file()}
    expected = {"inner_family_promotion.json"}
    for family in families.FAMILIES:
        ext = {"xgboost": "json", "catboost": "cbm", "extra_trees": "joblib"}[family]
        expected.add(f"{family}_inner_selection.json")
        for index in (0, 1):
            expected.update({f"{family}_candidate{index}_start.json", f"{family}_candidate{index}_inner.json", f"{family}_candidate{index}.{ext}"})
    require(set(actual) == expected and claimed == actual, "Candidate/progress artifact set/hash differs")
    selected, selections, candidate_checks = {}, {}, []
    for family in families.FAMILIES:
        rows = result["candidate_rows"][family]
        require(len(rows) == 2, "Frozen candidate count differs")
        fitted_candidates, replayed_inner_losses = [], []
        for index, row in enumerate(rows):
            require(row["candidate_index"] == index and row["family"] == family and row["seed"] == result["seed"], "Candidate identity differs")
            same(row["config"], families.MENU[family][index], "Candidate configuration")
            start = read(progress/f"{family}_candidate{index}_start.json")
            same(start["config"], row["config"], "Candidate start configuration")
            require(start["family"] == family and start["candidate_index"] == index, "Candidate start identity differs")
            metadata = read(progress/f"{family}_candidate{index}_inner.json")
            same(metadata, row, "Saved candidate metadata")
            path = folder/row["saved_model"]["path"]
            require(base.sha(path) == row["saved_model"]["sha256"], "Candidate model hash differs")
            fitted = load_candidate(family, row, path)
            recomputed = {}
            for part in ("fit", "inner"):
                p = families._probability(family, fitted, z[part])
                require(np.isfinite(p).all() and np.all((p >= 0) & (p <= 1)), "Invalid candidate probabilities")
                recomputed[part] = frozen._metrics(arrays[part][1], p, arrays[part][2])
                same(recomputed[part], row[f"{part}_metrics"], f"Candidate {part} metrics")
            replayed_inner_losses.append(recomputed["inner"]["weighted_log_loss"])
            fitted_candidates.append(fitted)
            candidate_checks.append({"family": family, "candidate_index": index, "config": row["config"],
                "model_sha256": row["saved_model"]["sha256"],
                "checkpoint": {k: v for k, v in row["checkpoint"].items() if k != "inner_weighted_logloss_by_round"},
                "fit_and_inner_seconds": row["fit_and_inner_seconds"],
                "replayed_fit_weighted_log_loss": recomputed["fit"]["weighted_log_loss"],
                "replayed_inner_weighted_log_loss": recomputed["inner"]["weighted_log_loss"],
                "fit_metric_abs_error": metric_errors(recomputed["fit"], row["fit_metrics"]),
                "inner_metric_abs_error": metric_errors(recomputed["inner"], row["inner_metrics"]),
                "fit_inner_metric_replay": True})
        winner = families.select_candidate(rows)
        require(min(range(2), key=lambda i: (replayed_inner_losses[i], i)) == winner,
                "Native replay changes inner candidate selection")
        choice = {"candidate_index": winner, "inner_weighted_log_loss": rows[winner]["inner_metrics"]["weighted_log_loss"],
                  "selected_config": rows[winner]["config"], "saved_model": rows[winner]["saved_model"]}
        same(choice, result["family_selection"][family], "Inner candidate choice")
        same(choice, read(progress/f"{family}_inner_selection.json"), "Persisted inner candidate choice")
        selected[family], selections[family] = fitted_candidates[winner], choice
    promoted = min(families.FAMILIES, key=lambda f: (selections[f]["inner_weighted_log_loss"], families.FAMILIES.index(f)))
    promotion = {"family": promoted, "policy": "minimum selected-family inner weighted log loss",
        "tie_order": families.FAMILIES, "family_inner_losses": {f: selections[f]["inner_weighted_log_loss"] for f in families.FAMILIES}}
    same(promotion, result["inner_family_promotion"], "Inner family promotion")
    same(promotion, read(progress/"inner_family_promotion.json"), "Persisted family promotion")
    native_selected_losses = {f: next(r["replayed_inner_weighted_log_loss"] for r in candidate_checks
        if r["family"] == f and r["candidate_index"] == selections[f]["candidate_index"]) for f in families.FAMILIES}
    require(min(families.FAMILIES, key=lambda f: (native_selected_losses[f], families.FAMILIES.index(f))) == promoted,
            "Native replay changes inner family promotion")
    predictions = {f: families._probability(f, fitted, z["outer"]) for f, fitted in selected.items()}
    predictions["inner_promoted"] = predictions[promoted]
    saved = result["outer_predictions"]
    require(len(saved) == len(arrays["outer"][1]), "Outer row count differs")
    sources, saved_sources, groups, cursor, max_error = defaultdict(dict), defaultdict(dict), {}, 0, 0.
    saved_predictions = {f: np.asarray([r["probabilities"][f] for r in saved]) for f in NAMES}
    errors = {f: {"max_abs_error": 0., "max_float32_ulps": 0 if f == "xgboost" or (f == "inner_promoted" and promoted == "xgboost") else None,
                  "failed_initial_1e8_checks": 0, "first_initial_1e8_failure": None} for f in NAMES}
    source_metric_errors = {f: {m: 0. for m in METRICS} for f in NAMES}
    for sample in partitions["outer"]:
        n = len(sample["y"])
        for i, mid in enumerate(sample["movement_ids"]):
            row = saved[cursor+i]
            same([row[k] for k in ("base_group", "source", "movement_id", "observed_selected", "input_trip_count_k")],
                 [sample["group"], sample["source"], mid, bool(sample["y"][i]), min(n, sample["trip_count"])], "Outer keys/labels/ranking budget")
            require(set(row["probabilities"]) == set(NAMES), "Outer family set differs")
            for family in NAMES:
                native_family = promoted if family == "inner_promoted" else family
                error, ulps, strict = probability_error(predictions[family][cursor+i], row["probabilities"][family], native_family)
                max_error = max(max_error, error)
                diagnostic = errors[family]
                diagnostic["max_abs_error"] = max(diagnostic["max_abs_error"], error)
                if ulps is not None:
                    diagnostic["max_float32_ulps"] = max(diagnostic["max_float32_ulps"], ulps)
                if not strict:
                    diagnostic["failed_initial_1e8_checks"] += 1
                    if diagnostic["first_initial_1e8_failure"] is None:
                        diagnostic["first_initial_1e8_failure"] = {"outer_row_index": cursor+i,
                            "base_group": row["base_group"], "source": row["source"], "movement_id": row["movement_id"],
                            "saved": row["probabilities"][family], "native": float(predictions[family][cursor+i]), "absolute_error": error, "float32_ulps": ulps}
        for family in NAMES:
            native_p, saved_p = predictions[family][cursor:cursor+n], saved_predictions[family][cursor:cursor+n]
            require(np.array_equal(np.argsort(-native_p, kind="stable"), np.argsort(-saved_p, kind="stable")),
                    "Native replay changes complete source ranking; same-platform replay required")
            require(np.array_equal(native_p >= .5, saved_p >= .5), "Native replay changes fixed-half classification")
        sources[sample["group"]][sample["source"]] = {f: frozen._metrics(sample["y"], p[cursor:cursor+n], np.ones(n)/n, [sample])
            for f, p in predictions.items()}
        saved_sources[sample["group"]][sample["source"]] = {f: frozen._metrics(sample["y"], p[cursor:cursor+n], np.ones(n)/n, [sample])
            for f, p in saved_predictions.items()}
        same(sources[sample["group"]][sample["source"]], result["outer_per_group_source"][sample["group"]][sample["source"]], "Outer per-source metrics")
        same(saved_sources[sample["group"]][sample["source"]], result["outer_per_group_source"][sample["group"]][sample["source"]], "Saved-probability per-source metrics", 1e-12)
        for family in NAMES:
            delta = metric_errors(sources[sample["group"]][sample["source"]][family],
                                  saved_sources[sample["group"]][sample["source"]][family])
            for metric, error in delta.items():
                if error is not None:
                    source_metric_errors[family][metric] = max(source_metric_errors[family][metric], error)
        cursor += n
    same(dict(sources), result["outer_per_group_source"], "Outer source registry/metrics")
    same(dict(saved_sources), result["outer_per_group_source"], "Saved-probability source registry/metrics", 1e-12)
    for group in outer_g:
        groups[group] = {f: previous._macro_metrics([row[f] for row in saved_sources[group].values()]) for f in NAMES}
    same(groups, result["outer_per_group"], "Outer equal-source timetable metrics", 1e-12)
    common = tuple(g for g in outer_g if int(g.removeprefix("physical_v2_s")) < 10032)
    same(result["outer_original32_common_groups"], common, "Fixed common32 groups")
    pooled_metric_errors = {}
    for family, p in predictions.items():
        native_pooled = frozen._metrics(arrays["outer"][1], p, arrays["outer"][2], partitions["outer"])
        same(native_pooled,
             result["outer_pooled_diagnostics_secondary"][family], "Outer pooled diagnostic")
        pooled_metric_errors[family] = metric_errors(native_pooled, result["outer_pooled_diagnostics_secondary"][family])
        same(frozen._metrics(arrays["outer"][1], saved_predictions[family], arrays["outer"][2], partitions["outer"]),
             result["outer_pooled_diagnostics_secondary"][family], "Saved-probability pooled diagnostic", 1e-12)
        same(previous._macro_metrics([groups[g][family] for g in outer_g]), result["outer_metrics"][family], "Outer macro metric", 1e-12)
        same(previous._macro_metrics([groups[g][family] for g in common]), result["outer_original32_common_group_metrics"][family], "Common32 macro metric", 1e-12)
    same(receipt["wall_seconds"], result["wall_seconds"], "Training wall time")
    check = {"task_id": task_id, "array_job_id": array, "source_commit": identity["source_commit"],
        "fold": result["fold"], "seed": result["seed"], "result_sha256": base.sha(folder/"result.json"),
        "receipt_sha256": base.sha(folder/"receipt.json"), "wrapper_sha256": base.sha(wp),
        "source_identity_sha256": base.sha(folder/"source_identity.json"),
        "candidate_checks": candidate_checks, "family_selection": selections, "inner_family_promotion": promotion,
        "outer_probability_max_abs_error": max_error, "probability_replay_by_family": errors,
        "native_vs_saved_outer_source_metric_max_abs_error": source_metric_errors,
        "native_vs_saved_outer_pooled_metric_abs_error": pooled_metric_errors,
        "complete_source_rankings_and_fixed_half_classification_unchanged": True,
        "native_replayed_inner_choices_and_promotion_unchanged": True,
        "saved_probability_metrics_recomputed_at_1e12": True, "all_metrics_replayed": True,
        "training_wall_seconds": result["wall_seconds"], "wrapper_elapsed_seconds": w["elapsed_seconds"],
        "allocated_job_cpus": w["allocated_job_cpus"], "candidate_fit_inner_seconds_sum": sum(r["fit_and_inner_seconds"] for r in candidate_checks)}
    if array == "722702":
        check["recovery_runtime"] = runtime_lineage(task_id, launches)
    return check, groups


def accounting(array, launch):
    path = DOC/f"ACCOUNTING_{array}.json"
    record = read(path)
    expected_ids = list(range(12)) if array == "720831" else list(recovery.FAILED_TASKS)
    name = "egg-route-families128" if array == "720831" else "egg-route-families128-recovery1"
    submit = launch["submitted_at_utc"].removesuffix("Z")
    rows = [r for r in record["records"] if r["job_id"] in {f"{array}_{i}" for i in expected_ids}]
    require(sorted(int(r["job_id"].split("_")[-1]) for r in rows) == expected_ids, "Incomplete task-level accounting")
    for row in rows:
        require(row["job_name"] == name and row["user"] == "nc437" and row["submit_utc"] == submit, "Accounting identity mismatch")
        failed = array == "720831" and int(row["job_id"].split("_")[-1]) in recovery.FAILED_TASKS
        require(row["state"] == ("FAILED" if failed else "COMPLETED") and row["exit_code"] == ("4:0" if failed else "0:0"), "Accounting state mismatch")
    elapsed = sum(r["elapsed_seconds"] for r in rows)
    cpu = sum(r["elapsed_seconds"]*r["allocated_cpus"] for r in rows)
    failed = [r for r in rows if r["state"] == "FAILED"]
    return {"accounting_sha256": base.sha(path), "task_records": rows,
        "elapsed_task_seconds_sum": elapsed, "allocated_cpu_seconds_sum": cpu,
        "failed_task_elapsed_seconds_sum": sum(r["elapsed_seconds"] for r in failed),
        "failed_task_allocated_cpu_seconds_sum": sum(r["elapsed_seconds"]*r["allocated_cpus"] for r in failed)}


def compare(new, old, groups):
    answer = {}
    for family in NAMES:
        answer[family] = {}
        for baseline in next(iter(old.values())):
            answer[family][baseline] = {}
            for metric in COMPARE_METRICS:
                delta = [new[g][family][metric]-old[g][baseline][metric] for g in groups
                    if new[g][family][metric] is not None and old[g][baseline][metric] is not None]
                improvement = delta if metric in HIGH else [-d for d in delta]
                answer[family][baseline][metric] = {"new_minus_baseline": summary(delta),
                    "improvement_direction": summary(improvement), "improved_groups": sum(d > 1e-9 for d in improvement),
                    "worsened_groups": sum(d < -1e-9 for d in improvement), "tied_groups": sum(abs(d) <= 1e-9 for d in improvement)}
    return answer


def replay(*, check_only=False, output=OUTPUT):
    started = time.monotonic()
    require(cli.versions() == PINNED and xgboost.__version__ == "3.0.5" and catboost.__version__ == "1.2.8", "Pinned native replay runtime required")
    launches, failures = gate()
    baseline = {}
    for version, (name, digest) in BASELINES.items():
        require(base.sha(DOC/name) == digest, "Recorded baseline replay hash changed")
        row = read(DOC/name)
        require(row["strict_saved_model_replay"] is True and row["pool_manifest_sha256"] == recovery.POOL_SHA
                and row["seeds_per_group"] == 3 and row["source_fleets_observed"] == 255, "Baseline replay scope differs")
        baseline[version] = row
    dataset = previous.load_pool(pool.OUTPUTS[128], expected_manifest_sha256=recovery.POOL_SHA, prefix=128)
    checks, observations = [], defaultdict(list)
    for task_id in range(12):
        check, groups = verify_task(task_id, dataset, launches)
        checks.append(check)
        for group, metrics in groups.items():
            observations[group].append(metrics)
        print(f"replayed task{task_id:02d} array{check['array_job_id']} six candidates; max probability error {check['outer_probability_max_abs_error']:.3g}", flush=True)
    require(set(observations) == set(dataset["groups"]) and all(len(v) == 3 for v in observations.values()), "Expected three outer seeds per timetable")
    groups = {g: {f: {m: statistics.mean(v[f][m] for v in rows if v[f][m] is not None)
        if any(v[f][m] is not None for v in rows) else None for m in METRICS} for f in NAMES} for g, rows in observations.items()}
    cohorts = {"full128": tuple(dataset["groups"]), "common32": tuple(f"physical_v2_s{i}" for i in range(10000,10032))}
    for row in baseline.values():
        require(set(row["per_group_seed_and_source_averages"]) == set(groups), "Baseline timetable registry differs")
    account = {a: accounting(a, launch) for a, launch in launches.items()}
    artifact = {"schema": "physical-route-families-v5-combined-replay-v1",
        "saved_model_numerical_replay_passed": True, "exact_all_family_probability_reproduction": False,
        "saved_prediction_metrics_recomputed_within_1e12": True,
        "all_source_rankings_and_fixed_half_classifications_unchanged": True,
        "initial_strict_probability_check": {"absolute_and_relative_tolerance": 1e-8,
            "passed": False, "first_failure_preserved_in_task0_xgboost": True,
            "revision": "XGBoost only: at most two float32 ULPs; other native probabilities atol/rtol1e-9. All saved-probability metrics checked atol/rtol1e-12; native metrics atol/rtol1e-8; complete source rankings unchanged."},
        "no_fit_or_outer_promotion": True, "pool_manifest_sha256": recovery.POOL_SHA, "runtime_versions": cli.versions(),
        "independent_timetables": 128, "observed_source_fleets": 255, "seeds_per_group": 3,
        "registered_censor": "physical_v2_s10037/source0", "native_candidate_models_replayed": 72,
        "selected_native_outer_models_replayed": 36, "original_failed_tasks_preserved": failures,
        "task_checks": checks, "accounting": account,
        "combined_elapsed_task_seconds_sum": sum(r["elapsed_task_seconds_sum"] for r in account.values()),
        "combined_allocated_cpu_seconds_sum": sum(r["allocated_cpu_seconds_sum"] for r in account.values()),
        "selected_training_wall_seconds_sum": sum(r["training_wall_seconds"] for r in checks),
        "all_six_candidate_fit_inner_seconds_sum": sum(r["candidate_fit_inner_seconds_sum"] for r in checks),
        "baseline_replay_hashes": {v: sha for v, (_, sha) in BASELINES.items()},
        "per_group_seed_and_source_averages": groups,
        "equal_group_aggregate": {c: {f: {m: summary(groups[g][f][m] for g in ids) for m in METRICS} for f in NAMES} for c, ids in cohorts.items()},
        "paired_comparisons": {v: {c: compare(groups, row["per_group_seed_and_source_averages"], ids) for c, ids in cohorts.items()} for v,row in baseline.items()},
        "inner_promoted_family_counts": dict(Counter(r["inner_family_promotion"]["family"] for r in checks)),
        "candidate_selection_counts": {f: dict(Counter(str(r["family_selection"][f]["selected_config"]) for r in checks)) for f in families.FAMILIES},
        "replay_wall_seconds": time.monotonic()-started,
        "replay_script_sha256": base.sha(Path(__file__)),
        "scope": "Observed feasible incumbent edge membership; repeated folds/seeds, no outer-tuned promotion or route/cost/speedup claim"}
    if not check_only:
        with Path(output).open("x") as stream:
            json.dump(artifact, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Replay without writing an artifact")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = replay(check_only=args.check_only, output=args.output)
    print(json.dumps({"saved_model_numerical_replay_passed": True, "tasks": len(result["task_checks"]),
        "candidate_models": result["native_candidate_models_replayed"], "replay_wall_seconds": result["replay_wall_seconds"]}))
