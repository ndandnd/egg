"""Independently replay saved outer edge scores; no fitting or model selection."""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
import statistics

import joblib
import numpy as np
import sklearn

from egglab import physical_route_model_v2 as model
from experiments import computational_benchmark as base

ROOT = base.ROOT
RESULTS = ROOT / "result/physical_learning/20260930-route-model32-v2"
OUTPUT = ROOT / "research-20260930/learning-campaign/ROUTE_MODEL32_REPLAY.json"
POOL_SHA = "35251cbc8c81787263b51f6259820299e862fba97efa6b8d09c9b1f9c8211842"
MODELS = ("constant", "kind_frequency", "logistic", "mlp32", "hist_boosted")
METRICS = ("weighted_log_loss", "weighted_brier", "average_precision",
           "input_trip_count_topk_recall_mean_by_fleet",
           "weighted_positive_recall_at_fixed_half",
           "weighted_negative_recall_at_fixed_half")
HIGHER_BETTER = {"average_precision", "input_trip_count_topk_recall_mean_by_fleet",
                 "weighted_positive_recall_at_fixed_half",
                 "weighted_negative_recall_at_fixed_half"}


def _read(path):
    return json.loads(Path(path).read_text())


def _match_number(observed, expected, *, tolerance=1e-8):
    if observed is None or expected is None:
        if observed is not expected:
            raise ValueError("Null metric mismatch")
    elif not np.isclose(observed, expected, atol=tolerance, rtol=tolerance):
        raise ValueError(f"Metric/probability mismatch: {observed} vs {expected}")


def _summarize(values):
    values = [float(v) for v in values if v is not None]
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "min": min(values) if values else None, "max": max(values) if values else None}


def replay(*, strict_models=False, output=OUTPUT):
    if strict_models and sklearn.__version__ != "1.7.2":
        raise ValueError("Strict boosted-model replay requires pinned scikit-learn 1.7.2")
    dataset = model.load_pool(expected_manifest_sha256=POOL_SHA)
    group_source_values = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    task_checks, logistic_iters, logistic_warnings = [], [], []
    mlp_selected, mlp_stopped, mlp_gaps, tree_selected, tree_gaps = [], [], [], [], []
    for task_id in range(12):
        folder = RESULTS / f"task{task_id:02d}"
        result_path, receipt_path = folder / "result.json", folder / "receipt.json"
        result, receipt = _read(result_path), _read(receipt_path)
        wrappers = sorted(RESULTS.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
        if len(wrappers) != 1:
            raise ValueError("Task lacks unique wrapper receipt")
        wrapper = _read(wrappers[0])
        tree_path = folder / "hist_boosted.joblib"
        if (receipt.get("status") != "completed" or receipt.get("task_id") != task_id
                or receipt.get("result_sha256") != base.sha(result_path)
                or receipt.get("hist_boosted_sha256") != base.sha(tree_path)
                or result.get("pool_manifest_sha256") != POOL_SHA
                or receipt.get("pool_manifest_sha256") != POOL_SHA
                or result.get("source_hashes") != receipt.get("source_hashes")
                or result.get("source_commit") != receipt.get("source_commit")
                or wrapper.get("task_id") != task_id or wrapper.get("returncode") != 0
                or wrapper.get("pool_manifest_sha256") != POOL_SHA
                or wrappers[0].name != f"task{task_id:02d}.slurm_wrapper_receipt.{wrapper.get('job_id')}.json"):
            raise ValueError("Task result/model/receipt/wrapper lineage mismatch")
        if result.get("runtime_versions", {}).get("sklearn") != "1.7.2":
            raise ValueError("Saved task used a different sklearn version")
        fit_g, inner_g, outer_g = model.grouped_split(dataset["groups"], task_id // 3)
        if (tuple(result["fit_groups"]) != fit_g or tuple(result["inner_groups"]) != inner_g
                or tuple(result["outer_groups"]) != outer_g or result.get("seed") != model.SEEDS[task_id % 3]):
            raise ValueError("Grouped fit/inner/outer split changed")
        fit = [s for s in dataset["samples"] if s["group"] in fit_g]
        outer = [s for s in dataset["samples"] if s["group"] in outer_g]
        fit_x, fit_y, fit_w = model._stack(fit)
        outer_x, outer_y, outer_w = model._stack(outer)
        mean, scale = model._preprocess(fit_x)
        if not np.allclose(mean, result["feature_mean_fit_only"]) or not np.allclose(
                scale, result["feature_scale_fit_only"]):
            raise ValueError("Saved preprocessing is not fit-only")
        z_outer = (outer_x-mean)/scale
        controls, prevalence, rates = model._controls(fit_x, fit_y, fit_w, outer_x)
        _match_number(prevalence, result["control_prevalence_fit_only"])
        if not np.allclose(rates, result["control_kind_rates_fit_only"]):
            raise ValueError("Saved frequency control differs from fit-only data")
        logistic = result["logistic"]
        logit = z_outer @ np.asarray(logistic["coef"])[0] + logistic["intercept"][0]
        mlp = result["mlp32"]["params"]
        mlp_p = model._sigmoid(np.tanh(z_outer @ np.asarray(mlp["W1"])+
            np.asarray(mlp["b1"])) @ np.asarray(mlp["W2"])+mlp["b2"])
        predictions = {**controls, "logistic": model._sigmoid(logit), "mlp32": mlp_p}
        if strict_models:
            tree = joblib.load(tree_path)
            predictions["hist_boosted"] = tree.predict_proba(z_outer)[:, 1]
        saved_rows = result["outer_predictions"]
        if len(saved_rows) != len(outer_y):
            raise ValueError("Saved outer prediction count changed")
        cursor = 0
        for sample in outer:
            n = len(sample["y"])
            subset = saved_rows[cursor:cursor+n]
            if [(r["base_group"], r["source"], r["movement_id"], r["observed_selected"])
                    for r in subset] != [(sample["group"], sample["source"], mid, bool(y))
                    for mid, y in zip(sample["movement_ids"], sample["y"])]:
                raise ValueError("Saved outer row key/label order differs from admitted source")
            for name in MODELS:
                stored = np.asarray([r["probabilities"][name] for r in subset])
                if name in predictions and not np.allclose(
                        stored, predictions[name][cursor:cursor+n], atol=1e-9, rtol=1e-9):
                    raise ValueError("Saved model probability differs: " + name)
                measured = model._metrics(sample["y"], stored, np.ones(n)/n, [sample])
                published = result["outer_per_group_source"][sample["group"]][sample["source"]][name]
                for metric in METRICS:
                    _match_number(measured[metric], published[metric])
                    group_source_values[sample["group"]][sample["source"]][name, metric].append(
                        measured[metric])
            cursor += n
        for name in MODELS:
            p = np.asarray([r["probabilities"][name] for r in saved_rows])
            measured = model._metrics(outer_y, p, outer_w, outer)
            for metric in METRICS:
                _match_number(measured[metric], result["outer_metrics"][name][metric])
        logistic_iters.extend(logistic["n_iter"])
        logistic_warnings.extend(logistic["convergence_warnings"])
        mlp_selected.append(result["mlp32"]["selected_epoch"])
        mlp_stopped.append(result["mlp32"]["stopped_epoch"])
        selected_curve = next(row for row in result["mlp32"]["curve"]
                              if row["epoch"] == result["mlp32"]["selected_epoch"])
        mlp_gaps.append(selected_curve["inner"]["weighted_log_loss"]-
                        selected_curve["fit"]["weighted_log_loss"])
        tree_selected.append(result["hist_boosted"]["selected_iterations"])
        selected_tree = next(row for row in result["hist_boosted"]["curve"]
                             if row["iterations"] == result["hist_boosted"]["selected_iterations"])
        tree_gaps.append(selected_tree["inner"]["weighted_log_loss"]-
                         selected_tree["fit"]["weighted_log_loss"])
        task_checks.append({"task_id": task_id, "fold": result["fold"], "seed": result["seed"],
            "outer_groups": result["outer_groups"], "outer_edges": len(outer_y),
            "logistic_n_iter": logistic["n_iter"],
            "logistic_convergence_warnings": len(logistic["convergence_warnings"]),
            "mlp_selected_epoch": result["mlp32"]["selected_epoch"],
            "mlp_stopped_epoch": result["mlp32"]["stopped_epoch"],
            "tree_selected_iterations": result["hist_boosted"]["selected_iterations"],
            "tree_model_replayed": strict_models})
    group_metrics = {}
    for group in sorted(group_source_values):
        group_metrics[group] = {}
        for name in MODELS:
            group_metrics[group][name] = {}
            for metric in METRICS:
                values = [v for source in ("source0", "source1")
                          for v in group_source_values[group][source][name, metric] if v is not None]
                group_metrics[group][name][metric] = statistics.mean(values) if values else None
    if len(group_metrics) != 32 or any(len(group_source_values[g]) != 2 for g in group_metrics):
        raise ValueError("Seed/group/source aggregation is incomplete")
    aggregate, paired = {}, {}
    for name in MODELS:
        aggregate[name] = {metric: _summarize(group_metrics[g][name][metric]
                           for g in group_metrics) for metric in METRICS}
        if name == "kind_frequency":
            continue
        paired[name] = {}
        for metric in METRICS:
            differences = []
            for group in group_metrics:
                value = group_metrics[group][name][metric]
                cheap = group_metrics[group]["kind_frequency"][metric]
                if value is None or cheap is None:
                    continue
                differences.append((value-cheap) if metric in HIGHER_BETTER else (cheap-value))
            paired[name][metric] = {**_summarize(differences),
                "direction": "positive favors model over kind-frequency",
                "positive_groups": sum(v > 1e-9 for v in differences),
                "negative_groups": sum(v < -1e-9 for v in differences),
                "near_tie_groups": sum(abs(v) <= 1e-9 for v in differences)}
    artifact = {"schema": "physical-route32-replay-v1", "pool_manifest_sha256": POOL_SHA,
        "strict_saved_model_replay": strict_models,
        "sklearn_runtime_version": sklearn.__version__,
        "independent_outer_groups": 32, "source_fleets_per_group": 2,
        "seeds_per_group": 3, "task_checks": task_checks,
        "equal_group_aggregate": aggregate, "paired_vs_kind_frequency": paired,
        "logistic": {"n_iter": _summarize(logistic_iters),
            "convergence_warning_count": len(logistic_warnings),
            "convergence_warnings": logistic_warnings},
        "mlp32": {"selected_epoch": _summarize(mlp_selected),
            "stopped_epoch": _summarize(mlp_stopped),
            "selected_inner_minus_fit_log_loss": _summarize(mlp_gaps),
            "early_stopped_tasks": sum(stop < model.MLP_MAX_EPOCHS for stop in mlp_stopped)},
        "hist_boosted": {"selected_iterations": dict(Counter(tree_selected)),
            "selected_inner_minus_fit_log_loss": _summarize(tree_gaps)},
        "per_group_seed_and_source_averages": group_metrics,
        "interpretation_scope": "observed source-incumbent movement classification only; no full-route feasibility or global-cost claim"}
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Replay output is immutable")
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return artifact


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-models", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    result = replay(strict_models=args.strict_models, output=args.output)
    print(json.dumps({"output": str(args.output), "strict_saved_model_replay":
        result["strict_saved_model_replay"], "groups": result["independent_outer_groups"]},
        sort_keys=True))


if __name__ == "__main__":
    main()
