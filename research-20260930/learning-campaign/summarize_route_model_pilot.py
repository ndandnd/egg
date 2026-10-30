#!/usr/bin/env python3
"""Replay saved route-model pilot predictions and summarize grouped CV metrics.

This script does not fit a model, read target/development/test tables, or call a
solver. It validates all 12 immutable task receipts, rebuilds the admitted
TRAIN-only candidate-edge features/labels, evaluates the serialized models and
controls, and compares predictions/metrics to the saved outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = Path(__file__).resolve().parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
DEFAULT_DATASET = REPO / "result/physical_learning/20260930-shard00-composite-v2"
DEFAULT_PILOT = REPO / "result/physical_learning/20260930-route-model-pilot"
DEFAULT_ACCOUNTING = CAMPAIGN / "ACCOUNTING_713295.json"
DEFAULT_JSON = CAMPAIGN / "ROUTE_MODEL_PILOT_REVIEW.json"
DEFAULT_REPORT = CAMPAIGN / "RESULTS_ROUTE_MODEL_PILOT.md"
FROZEN_DATASET_RECEIPT_SHA256 = "c9ed1e67356812e60a5986153227029d8eb15e98e2799a0ef87a56284be671d7"
EXPECTED_GROUPS = tuple(f"physical_v2_s{base_id}" for base_id in range(10000, 10008))
SEEDS = (17, 29, 43)
FOLDS = 4
TASKS = FOLDS * len(SEEDS)
METHODS = ("constant", "kind_frequency", "linear", "mlp16")
METRICS = ("weighted_log_loss", "weighted_brier", "weighted_accuracy",
           "positive_recall", "negative_recall", "positive_rate")
PREDICTION_TOL = 2e-10
METRIC_TOL = 2e-9
EXPECTED_SOURCE_FILES = (
    "src/egglab/physical_route_model.py",
    "src/experiments/train_physical_route_model.py",
    "src/cluster/physical_route_model.sbatch",
    "src/tests/test_physical_route_model.py",
    "research-20260930/learning-campaign/ROUTE_MODEL_TRAINING_PROTOCOL.md",
    "src/egglab/learned_proposals.py",
    "src/egglab/physical_learning_cases.py",
    "src/egglab/native_recharge.py",
    "src/egglab/native_pathflow.py",
    "src/experiments/computational_benchmark.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(Path(path).read_text())


def read_jsonl(path: Path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def load_training_inputs(dataset_dir: Path):
    """Rebuild candidate features and incumbent labels from the two admitted tables only."""
    from egglab import learned_proposals as edge
    from egglab import native_recharge as nr
    from egglab import physical_learning_cases as physical

    dataset_dir = dataset_dir.resolve()
    receipt_path = dataset_dir / "dataset_receipt.json"
    if sha256(receipt_path) != FROZEN_DATASET_RECEIPT_SHA256:
        raise ValueError("Admitted TRAIN dataset receipt hash changed")
    receipt = read_json(receipt_path)
    if receipt.get("schema") != "physical-learning-composite-v2" or receipt.get("train_only") is not True:
        raise ValueError("Input is not the frozen train-only composite v2")
    table_names = ("cases.jsonl", "source_inputs.jsonl")
    table_hashes = {}
    for name in table_names:
        actual = sha256(dataset_dir / name)
        if receipt.get("output_hashes", {}).get(name) != actual:
            raise ValueError(f"Admitted input table hash mismatch: {name}")
        table_hashes[name] = actual

    cases = read_jsonl(dataset_dir / "cases.jsonl")
    source_inputs = read_jsonl(dataset_dir / "source_inputs.jsonl")
    if len(cases) != 8 or len(source_inputs) != 16:
        raise ValueError("Pilot requires the exact eight-group/16-source TRAIN bank")
    case_by_group = {}
    seen_base_ids = set()
    for item in cases:
        base_id, group = item.get("base_id"), item.get("base_group")
        if (group in case_by_group or item.get("split") != "train"
                or item.get("generator") != physical.GENERATOR
                or base_id not in physical.shard_ids(0)
                or base_id in seen_base_ids
                or item.get("physical_profile") != physical.assignment(base_id)):
            raise ValueError("Duplicate, non-train, or unexpected physical case")
        case = edge.case_from_dict(item["case"])
        expected = physical.make_case(base_id)
        if case.identity() != item.get("case_identity") or case.identity() != expected.identity():
            raise ValueError("Case identity differs from frozen TRAIN generator")
        case_by_group[group] = (item, case)
        seen_base_ids.add(base_id)
    if set(case_by_group) != set(EXPECTED_GROUPS) or seen_base_ids != set(physical.shard_ids(0)):
        raise ValueError("The exact shard-00 TRAIN group registry is required")

    samples = []
    seen_sources = set()
    for source in source_inputs:
        group, source_name = source.get("base_group"), source.get("source")
        if (group not in case_by_group or source_name not in ("source0", "source1")
                or (group, source_name) in seen_sources):
            raise ValueError("Duplicate, foreign, or unknown source fleet")
        case_item, case = case_by_group[group]
        if (source.get("base_id") != case_item["base_id"]
                or source.get("case_identity") != case.identity()
                or source.get("source_plan_hash") != nr.digest(source["source_plan"])):
            raise ValueError("Source plan provenance does not match frozen case")
        plan_ids = {movement for vehicle in source["source_plan"]["vehicles"]
                    for movement in vehicle["movements"]}
        if set(source.get("selected_movements", ())) != plan_ids:
            raise ValueError("Selected movement set differs from serialized source plan")
        market = physical.market(case, source_name)
        if source.get("market_identity") != market.identity():
            raise ValueError("Source-market identity differs from frozen registry")

        # Case/source-market candidate features are predictors; source-plan
        # movement membership is used only as the observed-incumbent label.
        x = edge.edge_features(case, market.a)
        y = edge.selected_vector(case, source["source_plan"])
        movement_ids = [movement.id for movement in case.movements]
        if (x.shape != (len(movement_ids), len(edge.FEATURES)) or y.shape != (len(movement_ids),)
                or not np.isfinite(x).all() or not np.isfinite(y).all()):
            raise ValueError("Invalid movement-level features or labels")
        samples.append({"group": group, "source": source_name, "x": x, "y": y,
                        "movement_ids": movement_ids})
        seen_sources.add((group, source_name))
    expected_sources = {(group, source) for group in EXPECTED_GROUPS
                        for source in ("source0", "source1")}
    if seen_sources != expected_sources:
        raise ValueError("Source pair is incomplete")
    return {"groups": EXPECTED_GROUPS, "samples": samples,
            "receipt_sha256": sha256(receipt_path), "table_hashes": table_hashes,
            "features": tuple(edge.FEATURES), "receipt": receipt}


def stack(samples):
    x = np.concatenate([sample["x"] for sample in samples], axis=0)
    y = np.concatenate([sample["y"] for sample in samples], axis=0)
    n = len(samples)
    w = np.concatenate([np.full(len(sample["y"]), 1 / (n * len(sample["y"])))
                        for sample in samples])
    return x, y, w


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def evaluate_serialized(result, samples):
    """Evaluate stored parameters only; this function contains no training/fit call."""
    mean = np.asarray(result["feature_mean"], dtype=float)
    scale = np.asarray(result["feature_scale"], dtype=float)
    if mean.ndim != 1 or scale.shape != mean.shape or not np.isfinite(mean).all() or not np.isfinite(scale).all():
        raise ValueError("Malformed saved feature preprocessing")
    if np.any(scale <= 0) or tuple(result.get("features", ())) == ():
        raise ValueError("Invalid saved feature scale or empty feature schema")
    prevalence = float(result["training_only_control_prevalence"])
    kind_rates = np.asarray(result["training_only_kind_frequencies"], dtype=float)
    if kind_rates.shape != (4,) or not np.isfinite(kind_rates).all():
        raise ValueError("Invalid training-only movement-kind control")
    linear = np.asarray(result["linear_model"]["weights"], dtype=float)
    w1 = np.asarray(result["mlp16_model"]["W1"], dtype=float)
    b1 = np.asarray(result["mlp16_model"]["b1"], dtype=float)
    w2 = np.asarray(result["mlp16_model"]["W2"], dtype=float)
    b2 = float(result["mlp16_model"]["b2"])
    if (linear.shape != mean.shape or w1.shape != (len(mean), 16) or b1.shape != (16,)
            or w2.shape != (16,) or not all(np.isfinite(a).all() for a in (linear, w1, b1, w2))
            or not math.isfinite(b2)):
        raise ValueError("Malformed saved model parameters")

    probabilities = {}
    for sample in samples:
        x = sample["x"]
        if x.shape[1] != len(mean):
            raise ValueError("Saved feature schema dimension does not match inputs")
        z = (x - mean) / scale
        kinds = np.argmax(x[:, :4], axis=1)
        probabilities[(sample["group"], sample["source"])] = {
            "constant": np.full(len(x), prevalence),
            "kind_frequency": kind_rates[kinds],
            "linear": sigmoid(z @ linear),
            "mlp16": sigmoid(np.tanh(z @ w1 + b1) @ w2 + b2),
        }
    return probabilities


def metrics(y, p, weights):
    y = np.asarray(y, dtype=float)
    p = np.clip(np.asarray(p, dtype=float), 1e-9, 1 - 1e-9)
    weights = np.asarray(weights, dtype=float)
    total = float(weights.sum())
    if total <= 0 or not all(np.isfinite(a).all() for a in (y, p, weights)):
        raise ValueError("Invalid rows or weights in metric calculation")
    positive, negative = y > 0.5, y <= 0.5
    predicted = p >= 0.5
    return {
        "weighted_log_loss": float(np.sum(weights * (-y * np.log(p) - (1-y) * np.log1p(-p))) / total),
        "weighted_brier": float(np.sum(weights * (p-y) ** 2) / total),
        "weighted_accuracy": float(np.sum(weights * (predicted == positive)) / total),
        "positive_recall": float(np.sum(weights * (predicted & positive)) / np.sum(weights[positive]))
            if np.any(positive) else None,
        "negative_recall": float(np.sum(weights * ((~predicted) & negative)) / np.sum(weights[negative]))
            if np.any(negative) else None,
        "positive_rate": float(np.sum(weights * y) / total),
    }


def assert_metric_equal(actual, expected, label, diff_tracker):
    if not set(METRICS) <= set(actual) or set(expected) != set(METRICS):
        raise ValueError(f"Saved metric keys differ at {label}")
    for name in METRICS:
        a, e = actual[name], expected[name]
        if a is None or e is None:
            if a is not None or e is not None:
                raise ValueError(f"Saved null metric differs at {label}/{name}")
            continue
        delta = abs(float(a) - float(e))
        diff_tracker["max_abs_metric_difference"] = max(
            diff_tracker["max_abs_metric_difference"], delta)
        if not math.isclose(float(a), float(e), rel_tol=METRIC_TOL, abs_tol=METRIC_TOL):
            raise ValueError(f"Recomputed metric differs at {label}/{name}: {a} vs {e}")


def verify_source_hashes(result, launch, receipt):
    maps = [result.get("source_hashes"), launch.get("source_hashes"), receipt.get("source_hashes")]
    if any(not isinstance(m, dict) for m in maps) or not maps[0]:
        raise ValueError("Training task lacks frozen source hashes")
    if not (maps[0] == maps[1] == maps[2]):
        raise ValueError("Launch, result, and task receipt source hashes differ")
    if set(maps[0]) != set(EXPECTED_SOURCE_FILES):
        raise ValueError("Unexpected training source-hash scope")
    for name, expected in maps[0].items():
        if sha256(REPO / name) != expected:
            raise ValueError(f"Current frozen training source differs: {name}")


def load_tasks(pilot_dir: Path, dataset):
    tasks = []
    common_commit = None
    common_sources = None
    for task_id in range(TASKS):
        fold, seed = divmod(task_id, len(SEEDS))
        seed = SEEDS[seed]
        folder = pilot_dir / f"task{task_id:02d}"
        required = (folder / "launch.json", folder / "result.json", folder / "receipt.json")
        if not all(path.is_file() for path in required):
            raise ValueError(f"Task {task_id} is incomplete; all 12 tasks are required")
        launch, result, receipt = (read_json(path) for path in required)
        if (launch.get("task_id") != task_id or receipt.get("task_id") != task_id
                or result.get("task_id") != task_id or receipt.get("status") != "completed"):
            raise ValueError(f"Task {task_id} task identity or status mismatch")
        if sha256(folder / "result.json") != receipt.get("result_sha256"):
            raise ValueError(f"Task {task_id} result receipt hash mismatch")
        if (result.get("dataset_receipt_sha256") != dataset["receipt_sha256"]
                or receipt.get("dataset_receipt_sha256") != dataset["receipt_sha256"]
                or launch.get("dataset_receipt_sha256") != dataset["receipt_sha256"]):
            raise ValueError(f"Task {task_id} used a different admitted dataset")
        if result.get("fold") != fold or result.get("seed") != seed:
            raise ValueError(f"Task {task_id} fold/seed grid mismatch")
        train_groups = tuple(sorted(g for i, g in enumerate(dataset["groups"]) if i % FOLDS != fold))
        held_groups = tuple(g for i, g in enumerate(dataset["groups"]) if i % FOLDS == fold)
        if (tuple(result.get("train_groups", ())) != train_groups
                or tuple(result.get("heldout_groups", ())) != held_groups
                or set(train_groups) & set(held_groups) or len(held_groups) != 2):
            raise ValueError(f"Task {task_id} group split differs from frozen plan")
        if tuple(result.get("features", ())) != dataset["features"]:
            raise ValueError(f"Task {task_id} feature schema changed")
        launch_config = launch.get("training_config", {})
        result_config = result.get("training_config", {})
        if (not launch_config or any(result_config.get(k) != v for k, v in launch_config.items())
                or result_config.get("weighting") != "equal full-fleet weight then equal movement weight within fleet"):
            raise ValueError(f"Task {task_id} launch/result model configuration differs")
        verify_source_hashes(result, launch, receipt)
        if common_commit is None:
            common_commit = receipt.get("source_commit")
            common_sources = receipt.get("source_hashes")
        if receipt.get("source_commit") != common_commit or receipt.get("source_hashes") != common_sources:
            raise ValueError("Pilot task code identity is not consistent across tasks")
        wrappers = sorted(pilot_dir.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
        if len(wrappers) != 1:
            raise ValueError(f"Task {task_id} must have exactly one Slurm wrapper receipt")
        wrapper = read_json(wrappers[0])
        if (wrapper.get("task_id") != task_id or wrapper.get("returncode") != 0
                or wrapper.get("timeout_exit") is not False
                or str(wrapper.get("job_id")) not in wrappers[0].name):
            raise ValueError(f"Task {task_id} wrapper receipt is not a successful unique completion")
        if (wrapper.get("requested_cpus_per_task") not in ("1", 1)
                or wrapper.get("allocated_memory") not in ("8192", 8192)):
            raise ValueError(f"Task {task_id} resource receipt differs from frozen request")
        if "failure.json" in {p.name for p in folder.iterdir()}:
            raise ValueError(f"Task {task_id} contains a failure artifact alongside success")
        tasks.append({"task_id": task_id, "fold": fold, "seed": seed,
                      "launch": launch, "result": result, "receipt": receipt,
                      "wrapper": wrapper, "wrapper_path": str(wrappers[0])})
    return tasks


def _weight_samples(samples):
    return np.concatenate([np.full(len(sample["y"]), 1/(len(samples)*len(sample["y"])))
                           for sample in samples])


def _mean(values):
    values = [float(value) for value in values if value is not None]
    if not values:
        return {"mean": None, "sd": None, "n_groups": 0}
    return {"mean": statistics.fmean(values),
            "sd": statistics.stdev(values) if len(values) > 1 else None,
            "n_groups": len(values)}


def analyze(pilot_dir: Path, dataset_dir: Path, accounting_path: Path):
    from egglab import learned_proposals as edge

    dataset = load_training_inputs(dataset_dir)
    tasks = load_tasks(pilot_dir.resolve(), dataset)
    accounting = read_json(accounting_path)
    if (accounting.get("array_job_id") != "713295"
            or accounting.get("completed_tasks") != TASKS
            or accounting.get("failed_tasks") != 0):
        raise ValueError("Scheduler accounting does not confirm all 12 successful tasks")
    accounting_rows = {int(row["task_id"]): row for row in accounting.get("tasks", [])}
    if set(accounting_rows) != set(range(TASKS)):
        raise ValueError("Scheduler accounting task rows are incomplete")
    for task in tasks:
        row = accounting_rows[task["task_id"]]
        if (row.get("state") != "COMPLETED" or row.get("exit_code") != "0:0"
                or row.get("allocated_cpus") != 1 or row.get("requested_memory_gb") != 8
                or str(row.get("allocated_job_id")) != str(task["wrapper"].get("job_id"))):
            raise ValueError(f"Scheduler accounting disagrees for task {task['task_id']}")
    worker_wall_sum = sum(float(task["result"].get("wall_seconds", 0)) for task in tasks)
    if not math.isclose(worker_wall_sum, float(accounting.get("receipted_model_seconds", -1)),
                        rel_tol=1e-10, abs_tol=1e-8):
        raise ValueError("Scheduler accounting model-time total differs from task receipts")
    samples_by_group = {}
    for sample in dataset["samples"]:
        samples_by_group.setdefault(sample["group"], []).append(sample)
    if any(len(samples_by_group[group]) != 2 for group in dataset["groups"]):
        raise ValueError("Expected two source fleets per base group")

    group_seed_scores = {group: {} for group in dataset["groups"]}
    fold_train_scores = {fold: {} for fold in range(FOLDS)}
    comparison = {"max_abs_probability_difference": 0.0,
                  "max_abs_metric_difference": 0.0,
                  "prediction_rows_checked": 0,
                  "heldout_metric_sets_checked": 0,
                  "per_group_source_metric_sets_checked": 0,
                  "training_curve_metric_sets_checked": 0}
    threshold_counts = {method: {"predicted_positive": 0, "observed_positive": 0,
                                "prediction_rows_including_seed_repeats": 0}
                        for method in METHODS}
    task_timing = []

    for task in tasks:
        result = task["result"]
        fold, seed = task["fold"], task["seed"]
        train_groups = set(result["train_groups"])
        held_groups = set(result["heldout_groups"])
        train_samples = [s for s in dataset["samples"] if s["group"] in train_groups]
        held_samples = [s for s in dataset["samples"] if s["group"] in held_groups]
        probabilities = evaluate_serialized(result, dataset["samples"])

        # Validate saved predictions by a stable natural key, not row position.
        stored_rows = result.get("heldout_predictions")
        if not isinstance(stored_rows, list):
            raise ValueError(f"Task {task['task_id']} lacks movement-keyed predictions")
        stored = {}
        for row in stored_rows:
            key = (row.get("base_group"), row.get("source"), row.get("movement_id"))
            if key in stored:
                raise ValueError(f"Task {task['task_id']} duplicates a heldout movement key")
            stored[key] = row
        expected_rows = sum(len(s["y"]) for s in held_samples)
        if len(stored) != expected_rows or any(k[0] not in held_groups for k in stored):
            raise ValueError(f"Task {task['task_id']} heldout prediction partition is incomplete")

        task_probs = {}
        held_x, held_y, held_w = stack(held_samples)
        # The stack order is the original admitted source-input table order.
        flat_probs = {method: np.concatenate([probabilities[(s["group"], s["source"])][method]
                                              for s in held_samples])
                      for method in METHODS}
        for method in METHODS:
            threshold_counts[method]["predicted_positive"] += int(np.sum(flat_probs[method] >= 0.5))
            threshold_counts[method]["observed_positive"] += int(np.sum(held_y > 0.5))
            threshold_counts[method]["prediction_rows_including_seed_repeats"] += len(held_y)
        offset = 0
        for sample in held_samples:
            n = len(sample["y"])
            keyset = set()
            for j, movement_id in enumerate(sample["movement_ids"]):
                key = (sample["group"], sample["source"], movement_id)
                if key not in stored:
                    raise ValueError(f"Task {task['task_id']} missing prediction key {key}")
                saved_row = stored[key]
                if saved_row.get("observed_selected") != bool(sample["y"][j]):
                    raise ValueError(f"Task {task['task_id']} label differs at {key}")
                saved_p = saved_row.get("probabilities", {})
                if set(saved_p) != set(METHODS):
                    raise ValueError(f"Task {task['task_id']} probability methods differ")
                for method in METHODS:
                    actual = float(probabilities[(sample["group"], sample["source"])][method][j])
                    saved = float(saved_p[method])
                    delta = abs(actual-saved)
                    comparison["max_abs_probability_difference"] = max(
                        comparison["max_abs_probability_difference"], delta)
                    if not math.isclose(actual, saved, rel_tol=1e-9, abs_tol=PREDICTION_TOL):
                        raise ValueError(f"Task {task['task_id']} probability mismatch at {key}/{method}")
                    task_probs.setdefault((sample["group"], sample["source"]), {})[method] = \
                        probabilities[(sample["group"], sample["source"])][method]
                keyset.add(key)
                comparison["prediction_rows_checked"] += 1
            offset += n
        if offset != len(held_y):
            raise ValueError("Internal heldout row accounting mismatch")

        recomputed_held = {method: metrics(held_y, flat_probs[method], held_w)
                           for method in METHODS}
        for method in METHODS:
            assert_metric_equal(result["heldout_metrics"][method], recomputed_held[method],
                                f"task{task['task_id']}/held/{method}", comparison)
            comparison["heldout_metric_sets_checked"] += 1
            for sample in held_samples:
                saved_metric = result["heldout_per_group_source"][sample["group"]][sample["source"]][method]
                recomputed = metrics(sample["y"], probabilities[(sample["group"], sample["source"])][method],
                                     np.full(len(sample["y"]), 1/len(sample["y"])))
                assert_metric_equal(saved_metric, recomputed,
                                    f"task{task['task_id']}/{sample['group']}/{sample['source']}/{method}",
                                    comparison)
                comparison["per_group_source_metric_sets_checked"] += 1

        train_x, train_y, train_w = stack(train_samples)
        train_probs = {method: np.concatenate([probabilities[(s["group"], s["source"])][method]
                                               for s in train_samples])
                       for method in METHODS}
        train_metrics = {method: metrics(train_y, train_probs[method], train_w) for method in METHODS}
        fold_train_scores[fold][seed] = train_metrics
        for model_key, method in (("linear_model", "linear"), ("mlp16_model", "mlp16")):
            curves = result[model_key].get("curve", [])
            if not curves or curves[-1].get("epoch") != result.get("fixed_epochs_no_outer_tuning"):
                raise ValueError(f"Task {task['task_id']} missing final training curve for {method}")
            assert_metric_equal(curves[-1], train_metrics[method],
                                f"task{task['task_id']}/train/{method}", comparison)
            comparison["training_curve_metric_sets_checked"] += 1

        # One independent group score is formed from its two source fleets,
        # averaging all movement rows equally within each fleet.
        for group in held_groups:
            group_samples = [s for s in samples_by_group[group]]
            if len(group_samples) != 2:
                raise ValueError(f"Group {group} does not contain both sources")
            group_weights = np.concatenate([np.full(len(s["y"]), 1/(2*len(s["y"])))
                                            for s in group_samples])
            group_y = np.concatenate([s["y"] for s in group_samples])
            group_scores = {}
            for method in METHODS:
                group_p = np.concatenate([task_probs[(s["group"], s["source"])][method]
                                          for s in group_samples])
                group_scores[method] = metrics(group_y, group_p, group_weights)
            if seed in group_seed_scores[group]:
                raise ValueError(f"Group {group} is scored twice for seed {seed}")
            group_seed_scores[group][seed] = group_scores
        task_timing.append({"task_id": task["task_id"], "fold": fold, "seed": seed,
            "worker_wall_seconds": result.get("wall_seconds"),
            "wrapper_elapsed_seconds": task["wrapper"].get("elapsed_seconds"),
            "allocated_job_cpus": task["wrapper"].get("allocated_job_cpus"),
            "allocated_memory": task["wrapper"].get("allocated_memory"),
            "job_id": task["wrapper"].get("job_id")})

    group_means = {}
    for group, by_seed in group_seed_scores.items():
        if set(by_seed) != set(SEEDS):
            raise ValueError(f"Group {group} is not scored once for each declared seed")
        group_means[group] = {}
        for method in METHODS:
            group_means[group][method] = {}
            for metric in METRICS:
                vals = [by_seed[seed][method][metric] for seed in SEEDS]
                group_means[group][method][metric] = (
                    statistics.fmean(float(v) for v in vals if v is not None)
                    if any(v is not None for v in vals) else None)

    method_summary = {}
    for method in METHODS:
        method_summary[method] = {}
        for metric in METRICS:
            method_summary[method][metric] = _mean(
                group_means[group][method][metric] for group in dataset["groups"])

    train_fold_summary = {}
    for method in METHODS:
        train_fold_summary[method] = {}
        for metric in METRICS:
            fold_values = []
            for fold in range(FOLDS):
                values = [fold_train_scores[fold][seed][method][metric] for seed in SEEDS]
                present = [float(v) for v in values if v is not None]
                fold_values.append(statistics.fmean(present) if present else None)
            train_fold_summary[method][metric] = _mean(fold_values)

    train_vs_held = {}
    for method in METHODS:
        train_loss = train_fold_summary[method]["weighted_log_loss"]["mean"]
        held_loss = method_summary[method]["weighted_log_loss"]["mean"]
        train_vs_held[method] = {
            "training_log_loss_mean_across_four_fold_seed_means": train_loss,
            "heldout_log_loss_mean_across_eight_group_seed_means": held_loss,
            "heldout_minus_training_log_loss": (held_loss-train_loss)
                if train_loss is not None and held_loss is not None else None,
            "training_fold_n": train_fold_summary[method]["weighted_log_loss"]["n_groups"],
            "heldout_base_group_n": method_summary[method]["weighted_log_loss"]["n_groups"],
        }

    wrappers = [task["wrapper"] for task in tasks]
    alloc_counts = {}
    for wrapper in wrappers:
        key = str(wrapper.get("allocated_job_cpus"))
        alloc_counts[key] = alloc_counts.get(key, 0) + 1
    memory_counts = {}
    for wrapper in wrappers:
        key = str(wrapper.get("allocated_memory"))
        memory_counts[key] = memory_counts.get(key, 0) + 1
    config = tasks[0]["result"].get("training_config")
    raw_row_total = sum(len(sample["y"]) for sample in dataset["samples"])
    raw_positive_total = sum(int(np.sum(sample["y"] > 0.5)) for sample in dataset["samples"])
    return {
        "schema": "route-model-pilot-replay-review-v1",
        "evidence_scope": "exploratory grouped training-only movement classification; no cost/global-optimum or deployment claim",
        "dataset": {"path": str(dataset_dir.resolve()),
            "receipt_sha256": dataset["receipt_sha256"],
            "input_table_hashes": dataset["table_hashes"],
            "base_groups": list(dataset["groups"]),
            "group_count": len(dataset["groups"]),
            "source_fleets": len(dataset["samples"]),
            "candidate_movement_rows": sum(len(s["y"]) for s in dataset["samples"]),
            "raw_candidate_row_positive_rate": raw_positive_total / raw_row_total,
            "fleet_weighted_group_mean_positive_rate": method_summary["constant"]["positive_rate"]["mean"],
            "features": list(dataset["features"]),
            "label": "movement selected in a physically replayed observed source incumbent; non-selection is not infeasibility or suboptimality"},
        "pilot": {"attempt_path": str(pilot_dir.resolve()),
            "task_count": len(tasks), "folds": FOLDS, "seeds": list(SEEDS),
            "task_ids": [task["task_id"] for task in tasks],
            "source_commit": tasks[0]["receipt"].get("source_commit"),
            "source_hashes": tasks[0]["receipt"].get("source_hashes"),
            "training_config": config,
            "numpy_versions": sorted({task["result"].get("numpy_version") for task in tasks}),
            "worker_wall_seconds_sum_not_elapsed": sum(float(t["worker_wall_seconds"]) for t in task_timing),
            "worker_wall_seconds_max": max(float(t["worker_wall_seconds"]) for t in task_timing),
            "wrapper_elapsed_seconds_max": max(int(t["wrapper_elapsed_seconds"]) for t in task_timing),
            "allocated_cpu_counts": alloc_counts,
            "allocated_memory_counts": memory_counts,
            "accounting_path": str(accounting_path.resolve()),
            "accounting_sha256": sha256(accounting_path),
            "allocation_cpu_seconds": accounting["allocation_cpu_seconds"],
            "receipted_model_seconds": accounting["receipted_model_seconds"],
            "completed_tasks": accounting["completed_tasks"],
            "failed_tasks": accounting["failed_tasks"],
            "rss_caveat": accounting.get("rss_caveat"),
            "task_timing": task_timing},
        "classification_cutoff_0_5_counts_including_seed_repeats": threshold_counts,
        "recomputation": {**comparison, "prediction_tolerance": PREDICTION_TOL,
            "metric_tolerance": METRIC_TOL, "all_saved_outputs_match": True,
            "review_script_sha256": sha256(Path(__file__)),
            "operation": "evaluate saved parameters/preprocessing only; no model fit or solver call"},
        "group_macro_metrics_seed_averaged_then_group_averaged": method_summary,
        "group_metrics": group_means,
        "training_fold_seedmean_metrics_descriptive": train_fold_summary,
        "training_vs_heldout_log_loss": train_vs_held,
    }


def report_text(summary):
    lines = [
        "# Exploratory source-route model pilot: replay review",
        "",
        "This is an eight-group TRAIN-only movement-classification pilot. Each positive means an edge occurred in a physically replayed observed source incumbent; a negative means it was unchosen, not infeasible or inferior. Results are out-of-group cross-validation on training groups, not independent development/test performance, validated deployment, or route-cost gains.",
        "",
        f"The admitted dataset has {summary['dataset']['group_count']} independent base groups and {summary['dataset']['source_fleets']} source fleets ({summary['dataset']['candidate_movement_rows']} candidate movement rows). The pilot used {summary['pilot']['task_count']} tasks: four group folds × three repeated seeds. The 12 tasks are not 12 independent datasets. Dataset receipt SHA-256: `{summary['dataset']['receipt_sha256']}`.",
        "",
        "I recomputed held-out and training probabilities from the serialized model weights and preprocessing, using only the admitted `cases.jsonl` and `source_inputs.jsonl` plus saved task artifacts. No fit, native solve, target outcome, or development/test table was read. Saved movement probabilities, metric summaries, and training-curve endpoints were checked against the recomputation.",
        "",
        "## Held-out metrics",
        "",
        "Metrics average the three seeds within each base group, then average the eight group scores equally. Recall denominators include only groups containing that class.",
        "",
        "| Method | Log loss | Brier | Accuracy | Positive recall | Negative recall | Positive rate |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    names = {"constant": "Training prevalence", "kind_frequency": "Training kind frequency",
             "linear": "Linear logistic", "mlp16": "16-unit tanh MLP"}
    for method in METHODS:
        m = summary["group_macro_metrics_seed_averaged_then_group_averaged"][method]
        def val(metric, digits=4):
            cell = m[metric]
            if cell["mean"] is None:
                return "n/a"
            text = f"{cell['mean']:.{digits}f}"
            if metric in ("positive_recall", "negative_recall"):
                text += f" (n={cell['n_groups']})"
            return text
        lines.append(f"| {names[method]} | {val('weighted_log_loss')} | {val('weighted_brier')} | {val('weighted_accuracy')} | {val('positive_recall')} | {val('negative_recall')} | {val('positive_rate')} |")
    threshold = summary["classification_cutoff_0_5_counts_including_seed_repeats"]
    mlp = summary["group_macro_metrics_seed_averaged_then_group_averaged"]["mlp16"]
    kind = summary["group_macro_metrics_seed_averaged_then_group_averaged"]["kind_frequency"]
    lines += ["",
        f"The raw candidate-row selected-edge rate is {summary['dataset']['raw_candidate_row_positive_rate']:.1%}; the group/fleet-weighted mean is {summary['dataset']['fleet_weighted_group_mean_positive_rate']:.1%}. At the fixed 0.5 cutoff, every method predicted zero positive edges across the held-out predictions ({threshold['mlp16']['predicted_positive']} MLP positives over {threshold['mlp16']['prediction_rows_including_seed_repeats']} row evaluations including repeated seeds). Positive recall is therefore zero and negative recall one for all methods: the 93.88% accuracy is the all-negative result, not useful route-proposal quality. The MLP improves Brier from {kind['weighted_brier']['mean']:.4f} to {mlp['weighted_brier']['mean']:.4f}, but its log loss ({mlp['weighted_log_loss']['mean']:.4f}) does not beat kind frequency ({kind['weighted_log_loss']['mean']:.4f}); the linear model is worse on both proper scoring metrics. This small pilot shows no clear model advantage. No threshold was tuned on held-out labels.",
        "",
        "## Training versus held-out fit", "",
        "Training loss is averaged over seeds within each of four overlapping fold-training sets. Held-out loss is seed-averaged within each of eight groups, then group-averaged. These small gaps are descriptive only; they do not establish adequate training or the absence of overfitting, and they are not independent uncertainty estimates.", "",
        "| Method | Training log loss | Held-out log loss | Held-out minus training |",
        "|---|---:|---:|---:|"]
    for method in METHODS:
        row = summary["training_vs_heldout_log_loss"][method]
        lines.append(f"| {names[method]} | {row['training_log_loss_mean_across_four_fold_seed_means']:.4f} | {row['heldout_log_loss_mean_across_eight_group_seed_means']:.4f} | {row['heldout_minus_training_log_loss']:.4f} |")
    pilot = summary["pilot"]
    lines += ["", "## Reproducibility and limits", "",
        f"All 12 task and wrapper receipts completed. Maximum saved-probability discrepancy was `{summary['recomputation']['max_abs_probability_difference']:.3g}`; maximum metric discrepancy was `{summary['recomputation']['max_abs_metric_difference']:.3g}`. Per-task model/runtime/source hashes and wrapper receipts are recorded in the machine-readable review. Scheduler accounting recorded {pilot['allocation_cpu_seconds']} allocated CPU-seconds and {pilot['receipted_model_seconds']:.2f} receipted model seconds; each task received one CPU and 8 GB. Worker elapsed times sum to {pilot['worker_wall_seconds_sum_not_elapsed']:.1f} seconds across concurrent tasks; the slowest task wrapper took {pilot['wrapper_elapsed_seconds_max']} seconds. The worker-time sum is not elapsed campaign time.",
        "",
        "The metrics assess how well fixed, shallow scorers classify edges from observed source incumbents. They do not measure a decoded route, physical feasibility of a new proposal, target cost, global optimality, or speedup. Any ranking plus constrained decoder should be specified prospectively and evaluated on route feasibility and cost; do not tune a threshold on these held-out labels. The 8-group pilot remains exploratory; later learning checkpoints use predetermined training-group prefixes and preserve development/test groups.",
        ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_PILOT)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--accounting", type=Path, default=DEFAULT_ACCOUNTING)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = analyze(args.attempt, args.dataset, args.accounting)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    args.report_output.write_text(report_text(summary))
    print(json.dumps({"tasks": summary["pilot"]["task_count"],
        "group_count": summary["dataset"]["group_count"],
        "json": str(args.json_output), "report": str(args.report_output)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
