"""Strictly replay saved 64-group edge models and compare the fixed common 32.

This reads fitted artifacts only. It never fits, selects a checkpoint, or changes
the predeclared outer folds. Run with the pinned scikit-learn 1.7.2 interpreter.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path
import statistics

import joblib
import numpy as np
import sklearn

from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as model
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool

ROOT = base.ROOT
RESULTS = ROOT / "result/physical_learning/20260930-route-model64-v3"
OLD = ROOT / "research-20260930/learning-campaign/ROUTE_MODEL32_REPLAY.json"
OLD_POOL = ROOT / "result/physical_learning/20260930-route-pool32-v1/pool_manifest.json"
OUTPUT = ROOT / "research-20260930/learning-campaign/ROUTE_MODEL64_REPLAY.json"
POOL_SHA = "64791ec33307612bd8ad7f3c2396c42e0ffdc44717d2c865fe268f61bdab5eb0"
OLD_POOL_SHA = "35251cbc8c81787263b51f6259820299e862fba97efa6b8d09c9b1f9c8211842"
OLD_REPLAY_SHA = "9af43721c02f30b9f35fd29a8a70655643c8f10aa94478dd42ca6e638fd46607"
NAMES = ("constant", "kind_frequency", "logistic", "mlp32", "hist_boosted")
METRICS = ("weighted_log_loss", "weighted_brier", "average_precision",
           "input_trip_count_topk_recall_mean_by_fleet",
           "weighted_positive_recall_at_fixed_half",
           "weighted_negative_recall_at_fixed_half")
HIGH = {"average_precision", "input_trip_count_topk_recall_mean_by_fleet",
        "weighted_positive_recall_at_fixed_half",
        "weighted_negative_recall_at_fixed_half"}
TOL = 1e-8


def read(path):
    return json.loads(Path(path).read_text())


def check_number(actual, saved, label):
    if actual is None or saved is None:
        if actual is not saved:
            raise ValueError(f"{label}: null mismatch")
    elif not np.isclose(actual, saved, atol=TOL, rtol=TOL):
        raise ValueError(f"{label}: {actual} != {saved}")


def summary(values):
    values = [float(v) for v in values if v is not None]
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "min": min(values) if values else None, "max": max(values) if values else None}


def macro_sources(source_metrics):
    return {key: statistics.mean(v[key] for v in source_metrics if v[key] is not None)
            if any(v[key] is not None for v in source_metrics) else None
            for key in METRICS}


def verify_common32_lineage():
    """Pin the prior replay and the exact four shard inputs shared by both pools."""
    if (base.sha(OLD) != OLD_REPLAY_SHA or base.sha(OLD_POOL) != OLD_POOL_SHA
            or base.sha(pool.OUTPUTS[64] / "pool_manifest.json") != POOL_SHA):
        raise ValueError("Frozen 32/64 replay or pool-manifest SHA-256 changed")
    earlier = read(OLD)
    older_pool = read(OLD_POOL)
    larger_pool = read(pool.OUTPUTS[64] / "pool_manifest.json")
    if (earlier.get("pool_manifest_sha256") != OLD_POOL_SHA
            or earlier.get("strict_saved_model_replay") is not True
            or earlier.get("independent_outer_groups") != 32
            or older_pool.get("base_ids") != list(range(10000, 10032))
            or larger_pool.get("base_ids") != list(range(10000, 10064))):
        raise ValueError("Prior replay or exact registry prefix differs")
    old_shards = older_pool.get("admitted_shards", ())
    new_shards = larger_pool.get("admitted_shards", ())
    if len(old_shards) != 4 or len(new_shards) != 8:
        raise ValueError("Admitted shard count differs from exact 32/64 prefix")
    keys = ("shard", "dataset_receipt_sha256", "case_table_sha256",
            "source_table_sha256")
    for index in range(4):
        if (old_shards[index].get("shard") != index
                or new_shards[index].get("shard") != index
                or any(old_shards[index].get(key) != new_shards[index].get(key)
                       for key in keys)):
            raise ValueError(f"Common-32 shard {index} input lineage changed")
    return earlier


def replay(output=OUTPUT):
    if sklearn.__version__ != "1.7.2":
        raise ValueError("Saved-model replay requires scikit-learn 1.7.2")
    dataset = model.load_pool(pool.OUTPUTS[64], expected_manifest_sha256=POOL_SHA, prefix=64)
    eligibility = {row["base_group"]: row for row in dataset["group_eligibility"]}
    old = verify_common32_lineage()
    if (old.get("independent_outer_groups") != 32
            or old.get("strict_saved_model_replay") is not True
            or old.get("sklearn_runtime_version") != "1.7.2"):
        raise ValueError("Prior 32-group comparison is not the strict frozen replay")
    old_groups = old["per_group_seed_and_source_averages"]
    common_groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10032))
    if set(old_groups) != set(common_groups):
        raise ValueError("The prior common-32 cohort changed")
    observations = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    task_checks = []
    iters, warnings, mlp_epochs, mlp_stops, mlp_gaps, tree_iters, tree_gaps = [], [], [], [], [], [], []
    for task_id in range(12):
        folder = RESULTS / f"task{task_id:02d}"
        result_path, receipt_path, tree_path = (folder / n for n in
            ("result.json", "receipt.json", "hist_boosted.joblib"))
        result, receipt = read(result_path), read(receipt_path)
        wrappers = list(RESULTS.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
        if len(wrappers) != 1:
            raise ValueError(f"Task {task_id} lacks a unique wrapper receipt")
        wrapper = read(wrappers[0])
        if (receipt.get("status") != "completed" or receipt.get("task_id") != task_id
                or result.get("task_id") != task_id
                or result.get("policy") != model.POLICY
                or result.get("prefix_groups_intended") != 64
                or result.get("pool_manifest_sha256") != POOL_SHA
                or receipt.get("pool_manifest_sha256") != POOL_SHA
                or receipt.get("result_sha256") != base.sha(result_path)
                or receipt.get("hist_boosted_sha256") != base.sha(tree_path)
                or receipt.get("source_identity_sha256") != base.sha(folder / "source_identity.json")
                or result.get("source_hashes") != receipt.get("source_hashes")
                or result.get("source_commit") != receipt.get("source_commit")
                or result.get("runtime_versions", {}).get("sklearn") != "1.7.2"
                or result.get("no_outer_selection") is not True
                or wrapper.get("task_id") != task_id or wrapper.get("returncode") != 0
                or wrapper.get("pool_manifest_sha256") != POOL_SHA
                or wrappers[0].name !=
                    f"task{task_id:02d}.slurm_wrapper_receipt.{wrapper.get('job_id')}.json"):
            raise ValueError(f"Task {task_id} result/receipt/model/wrapper lineage mismatch")
        fit_g, inner_g, outer_g = model.grouped_split(dataset["groups"], task_id // 3)
        if (tuple(result["fit_groups"]) != fit_g or tuple(result["inner_groups"]) != inner_g
                or tuple(result["outer_groups"]) != outer_g
                or result["seed"] != model.SEEDS[task_id % 3]
                or result["fold"] != task_id // 3):
            raise ValueError("Predeclared whole-timetable split changed")
        fit = [s for s in dataset["samples"] if s["group"] in fit_g]
        outer = [s for s in dataset["samples"] if s["group"] in outer_g]
        fit_x, fit_y, fit_w = model._stack(fit)
        outer_x, outer_y, outer_w = model._stack(outer)
        mean, scale = frozen._preprocess(fit_x)
        if not (np.allclose(mean, result["feature_mean_fit_only"])
                and np.allclose(scale, result["feature_scale_fit_only"])):
            raise ValueError("Saved preprocessing differs from fit-only samples")
        z = (outer_x - mean) / scale
        controls, prevalence, rates = frozen._controls(fit_x, fit_y, fit_w, outer_x)
        check_number(prevalence, result["control_prevalence_fit_only"], "fit prevalence")
        if not np.allclose(rates, result["control_kind_rates_fit_only"]):
            raise ValueError("Fit-only kind rates changed")
        logistic = result["logistic"]
        linear_p = frozen._sigmoid(z @ np.asarray(logistic["coef"])[0]
                                   + logistic["intercept"][0])
        mlp_p = frozen._mlp_predict(result["mlp32"], z)
        tree = joblib.load(tree_path)
        tree_p = tree.predict_proba(z)[:, 1]
        predictions = {**controls, "logistic": linear_p,
                       "mlp32": mlp_p, "hist_boosted": tree_p}
        saved_rows = result["outer_predictions"]
        if len(saved_rows) != len(outer_y):
            raise ValueError("Outer prediction row count changed")
        cursor = 0
        checked_by_group = defaultdict(dict)
        for sample in outer:
            n = len(sample["y"])
            rows = saved_rows[cursor:cursor+n]
            keys = [(r["base_group"], r["source"], r["movement_id"],
                     r["observed_selected"], r["input_trip_count_k"]) for r in rows]
            expected = [(sample["group"], sample["source"], mid, bool(y),
                         min(sample["trip_count"], n))
                        for mid, y in zip(sample["movement_ids"], sample["y"])]
            if keys != expected:
                raise ValueError("Saved row keys/labels/ranking budgets changed")
            for name in NAMES:
                saved_p = np.asarray([r["probabilities"][name] for r in rows])
                if not np.allclose(saved_p, predictions[name][cursor:cursor+n],
                                   atol=1e-9, rtol=1e-9):
                    raise ValueError(f"Saved {name} probabilities differ")
                metrics = frozen._metrics(sample["y"], saved_p, np.ones(n)/n, [sample])
                for metric in METRICS:
                    check_number(metrics[metric],
                        result["outer_per_group_source"][sample["group"]][sample["source"]][name][metric],
                        f"{sample['group']}/{sample['source']}/{name}/{metric}")
                    observations[sample["group"]][sample["source"]][name][metric].append(metrics[metric])
                checked_by_group[sample["group"]][sample["source"]] = True
            cursor += n
        if cursor != len(outer_y):
            raise ValueError("Outer sample traversal incomplete")
        for group in outer_g:
            if set(checked_by_group[group]) != set(eligibility[group]["observed_sources"]):
                raise ValueError("Registered censor/source membership differs")
            for name in NAMES:
                calculated = macro_sources([result["outer_per_group_source"][group][s][name]
                    for s in eligibility[group]["observed_sources"]])
                saved = result["outer_per_group"][group][name]
                for metric in METRICS:
                    check_number(calculated[metric], saved[metric],
                                 f"outer group macro {group}/{name}/{metric}")
        for name in NAMES:
            saved_probability = np.asarray([r["probabilities"][name] for r in saved_rows])
            pooled = frozen._metrics(outer_y, saved_probability, outer_w, outer)
            for metric in METRICS:
                check_number(pooled[metric],
                    result["outer_pooled_diagnostics_secondary"][name][metric],
                    f"pooled diagnostic {name}/{metric}")
                macro = statistics.mean(result["outer_per_group"][g][name][metric]
                                        for g in outer_g)
                check_number(macro, result["outer_metrics"][name][metric],
                             f"outer macro {name}/{metric}")
            common = tuple(g for g in outer_g if g in common_groups)
            if tuple(result["outer_original32_common_groups"]) != common:
                raise ValueError("Saved common-32 group set changed")
            for metric in METRICS:
                common_mean = statistics.mean(result["outer_per_group"][g][name][metric]
                                              for g in common)
                check_number(common_mean,
                    result["outer_original32_common_group_metrics"][name][metric],
                    f"common-32 macro {name}/{metric}")
        iters.extend(logistic["n_iter"])
        warnings.extend(logistic["convergence_warnings"])
        mlp_epochs.append(result["mlp32"]["selected_epoch"])
        mlp_stops.append(result["mlp32"]["stopped_epoch"])
        mlp_point = next(r for r in result["mlp32"]["curve"]
                         if r["epoch"] == result["mlp32"]["selected_epoch"])
        mlp_gaps.append(mlp_point["inner"]["weighted_log_loss"]-
                        mlp_point["fit"]["weighted_log_loss"])
        tree_iters.append(result["hist_boosted"]["selected_iterations"])
        tree_point = next(r for r in result["hist_boosted"]["curve"]
                          if r["iterations"] == result["hist_boosted"]["selected_iterations"])
        tree_gaps.append(tree_point["inner"]["weighted_log_loss"]-
                         tree_point["fit"]["weighted_log_loss"])
        task_checks.append({"task_id": task_id, "fold": result["fold"], "seed": result["seed"],
            "outer_groups": result["outer_groups"], "outer_edges": len(outer_y),
            "outer_fleets": len(outer), "logistic_n_iter": logistic["n_iter"],
            "logistic_convergence_warnings": len(logistic["convergence_warnings"]),
            "mlp_selected_epoch": result["mlp32"]["selected_epoch"],
            "mlp_stopped_epoch": result["mlp32"]["stopped_epoch"],
            "tree_selected_iterations": result["hist_boosted"]["selected_iterations"]})
    group_metrics = {}
    for group in dataset["groups"]:
        source_map = observations[group]
        if set(source_map) != set(eligibility[group]["observed_sources"]):
            raise ValueError(f"Incomplete source/seed admission for {group}")
        group_metrics[group] = {}
        for name in NAMES:
            group_metrics[group][name] = {}
            for metric in METRICS:
                per_source = []
                for source in eligibility[group]["observed_sources"]:
                    values = source_map[source][name][metric]
                    if len(values) != 3:
                        raise ValueError("Not exactly three outer seed predictions per source")
                    finite = [v for v in values if v is not None]
                    per_source.append(statistics.mean(finite) if finite else None)
                finite = [v for v in per_source if v is not None]
                group_metrics[group][name][metric] = statistics.mean(finite) if finite else None
    aggregate = {name: {metric: summary(group_metrics[g][name][metric]
                  for g in dataset["groups"]) for metric in METRICS} for name in NAMES}
    paired_kind = {}
    for name in ("logistic", "mlp32", "hist_boosted"):
        paired_kind[name] = {}
        for metric in METRICS:
            diff = [(group_metrics[g][name][metric]-group_metrics[g]["kind_frequency"][metric])
                    if metric in HIGH else
                    (group_metrics[g]["kind_frequency"][metric]-group_metrics[g][name][metric])
                    for g in dataset["groups"]]
            paired_kind[name][metric] = {**summary(diff),
                "positive_groups": sum(v > 1e-9 for v in diff),
                "negative_groups": sum(v < -1e-9 for v in diff),
                "near_tie_groups": sum(abs(v) <= 1e-9 for v in diff)}
    paired_common = {}
    for name in NAMES:
        paired_common[name] = {}
        for metric in METRICS:
            differences = []
            for group in common_groups:
                earlier = old_groups[group][name][metric]
                later = group_metrics[group][name][metric]
                if earlier is None or later is None:
                    continue
                differences.append((later-earlier) if metric in HIGH else (earlier-later))
            paired_common[name][metric] = {**summary(differences),
                "direction": "positive favors 64-group fit on same original-32 timetable",
                "positive_groups": sum(v > 1e-9 for v in differences),
                "negative_groups": sum(v < -1e-9 for v in differences),
                "near_tie_groups": sum(abs(v) <= 1e-9 for v in differences)}
    artifact = {"schema": "physical-route64-replay-v1", "pool_manifest_sha256": POOL_SHA,
        "sklearn_runtime_version": sklearn.__version__, "strict_saved_model_replay": True,
        "independent_groups_intended": 64, "groups_eligible_observed": 64,
        "source_fleets_intended": 128, "source_fleets_observed": len(dataset["samples"]),
        "registered_one_source_group": "physical_v2_s10037",
        "seeds_per_group": 3, "task_checks": task_checks,
        "equal_group_aggregate": aggregate, "paired_vs_kind_frequency": paired_kind,
        "common32_group_metrics_64fit": {g: group_metrics[g] for g in common_groups},
        "common32_group_metrics_32fit": old_groups,
        "common32_paired_64fit_vs_32fit": paired_common,
        "common32_equal_group_aggregate_32fit": old["equal_group_aggregate"],
        "common32_equal_group_aggregate_64fit": {name: {metric: summary(
            group_metrics[g][name][metric] for g in common_groups)
            for metric in METRICS} for name in NAMES},
        "logistic": {"n_iter": summary(iters), "convergence_warning_count": len(warnings),
                     "convergence_warnings": warnings},
        "mlp32": {"selected_epoch": summary(mlp_epochs), "stopped_epoch": summary(mlp_stops),
                  "selected_inner_minus_fit_log_loss": summary(mlp_gaps),
                  "early_stopped_tasks": sum(v < frozen.MLP_MAX_EPOCHS for v in mlp_stops)},
        "hist_boosted": {"selected_iterations": dict(Counter(tree_iters)),
                         "selected_inner_minus_fit_log_loss": summary(tree_gaps)},
        "per_group_seed_and_source_averages": group_metrics,
        "interpretation_scope": "observed feasible source-incumbent movement classification only; no route feasibility or cost claim"}
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Replay output is immutable")
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-lineage-only", action="store_true",
                        help="Validate pinned 32/64 pool inputs without touching replay output")
    args = parser.parse_args()
    if args.validate_lineage_only:
        verify_common32_lineage()
        print(json.dumps({"common32_lineage": "validated", "old_replay_sha256": OLD_REPLAY_SHA,
                          "old_pool_manifest_sha256": OLD_POOL_SHA,
                          "new_pool_manifest_sha256": POOL_SHA}, sort_keys=True))
    else:
        result = replay()
        print(json.dumps({"output": str(OUTPUT), "groups": result["independent_groups_intended"],
            "source_fleets": result["source_fleets_observed"],
            "strict_saved_model_replay": True}, sort_keys=True))
