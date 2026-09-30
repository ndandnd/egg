"""Replay all saved exact-128 v4 budget models against frozen v3, without fitting.

Refuses a partial array. Only the predeclared selected outer predictions are
evaluated; 300-epoch MLP and 200-tree anchors are checked on fit/inner data and
matched prediction identity, never selected by an outer outcome.
Run with the pinned scikit-learn 1.7.2 interpreter and PYTHONPATH=src.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics

import joblib
import numpy as np
import sklearn

from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous
from egglab import physical_route_model_budget_v4 as budget
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool
import replay_route_model128 as replay3

ROOT = base.ROOT
RESULTS = ROOT / "result/physical_learning/20260930-route-model128-budget-v4"
OLD_RESULTS = replay3.RESULTS
OLD_REPLAY = replay3.OUTPUT
OLD_REPLAY_SHA = "9f274bd9106bc0fa8035dc381e6b698bcf5c3ba6ae19179ea11ecd0767c92192"
OUTPUT = ROOT / "research-20260930/learning-campaign/ROUTE_MODEL128_BUDGET_V4_REPLAY.json"
NAMES = replay3.NAMES
METRICS = replay3.METRICS
HIGH = replay3.HIGH
TOL = 1e-8


def read(path):
    return json.loads(Path(path).read_text())


def near(a, b, label, *, atol=TOL):
    if a is None or b is None:
        if a is not b:
            raise ValueError(f"{label}: null mismatch")
    elif not np.isclose(a, b, atol=atol, rtol=atol):
        raise ValueError(f"{label}: numeric mismatch")


def same_metrics(a, b, label):
    for metric in METRICS:
        near(a[metric], b[metric], f"{label}/{metric}")


def same_parameters(a, b, label):
    for name in ("W1", "b1", "W2", "b2"):
        if not np.allclose(np.asarray(a[name]), np.asarray(b[name]), atol=1e-9, rtol=1e-9):
            raise ValueError(f"{label}/{name}: MLP parameter mismatch")


def metric_summary(values):
    values = [float(v) for v in values if v is not None]
    return {"n": len(values), "mean": statistics.mean(values) if values else None,
            "median": statistics.median(values) if values else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None}


def paired(new, old, groups):
    answer = {}
    for name in NAMES:
        answer[name] = {}
        for metric in METRICS:
            differences = []
            for group in groups:
                a, b = new[group][name][metric], old[group][name][metric]
                if a is not None and b is not None:
                    differences.append((a-b) if metric in HIGH else (b-a))
            answer[name][metric] = {**metric_summary(differences),
                "positive_groups": sum(d > 1e-9 for d in differences),
                "negative_groups": sum(d < -1e-9 for d in differences),
                "near_tie_groups": sum(abs(d) <= 1e-9 for d in differences),
                "direction": "positive favors v4 over frozen v3 on the same timetable"}
    return answer


def _progress(folder, receipt, result, old):
    progress = folder / "inner_progress"
    claimed = receipt["inner_progress_hashes"]
    actual = {p.name: base.sha(p) for p in sorted(progress.iterdir()) if p.is_file()}
    if claimed != actual or not claimed:
        raise ValueError("Append-only inner progress set/hash mismatch")
    mlp = result["mlp32"]
    curve = mlp["curve"]
    if (not curve or curve[-1]["epoch"] != mlp["stopped_epoch"]
            or any(r["epoch"] != (i+1)*budget.CHECK_EVERY for i, r in enumerate(curve))
            or mlp["stopped_epoch"] > budget.MLP_MAX_EPOCHS):
        raise ValueError("MLP inner-curve checkpoint registry changed")
    chosen = budget.choose_inner(curve, index="epoch", min_improvement=1e-8)
    if (chosen["epoch"] != mlp["selected_epoch"]
            or mlp["selected_inner_log_loss"] != chosen["inner"]["weighted_log_loss"]):
        raise ValueError("MLP checkpoint was not chosen by frozen inner rule")
    selection = read(progress / "mlp_inner_selection.json")
    if (selection["selected_epoch"] != mlp["selected_epoch"]
            or selection["stopped_epoch"] != mlp["stopped_epoch"]):
        raise ValueError("Persisted pre-outer MLP selection changed")
    near(selection["selected_inner_log_loss"], mlp["selected_inner_log_loss"], "MLP selection loss")
    same_parameters(selection["params"], mlp["params"], "MLP selection")
    for row in curve:
        p = read(progress / f"mlp_curve_epoch{row['epoch']:04d}.json")
        if p["epoch"] != row["epoch"]:
            raise ValueError("MLP progress epoch changed")
        same_metrics(p["fit"], row["fit"], "MLP fit curve")
        same_metrics(p["inner"], row["inner"], "MLP inner curve")
    old_curve = {r["epoch"]: r for r in old["mlp32"]["curve"]}
    for row in curve:
        if row["epoch"] > 300:
            break
        previous_row = old_curve.get(row["epoch"])
        if previous_row is None:
            raise ValueError("Frozen v3 lacks a shared MLP inner checkpoint")
        same_metrics(row["fit"], previous_row["fit"], "shared v3/v4 MLP fit curve")
        same_metrics(row["inner"], previous_row["inner"], "shared v3/v4 MLP inner curve")
    improved = [p for p in progress.glob("mlp_best_epoch*.json")]
    if not improved or f"mlp_best_epoch{mlp['selected_epoch']:04d}.json" not in claimed:
        raise ValueError("Selected MLP best parameters not persisted before outer read")
    selected_best = read(progress / f"mlp_best_epoch{mlp['selected_epoch']:04d}.json")
    same_parameters(selected_best["params"], mlp["params"], "selected MLP best")
    anchor = mlp["anchor_at_300"]
    if mlp["stopped_epoch"] >= budget.MLP_ANCHOR_EPOCH:
        if anchor is None or anchor["epoch"] != 300:
            raise ValueError("Reached MLP epoch 300 without anchor")
        if old["mlp32"]["selected_epoch"] != 300:
            raise ValueError("Frozen v3 selected state is not its 300-epoch anchor")
        persisted = read(progress / "mlp_anchor_300.json")
        if persisted != anchor:
            raise ValueError("Saved MLP anchor differs from pre-outer progress")
        same_parameters(anchor["params"], old["mlp32"]["params"], "300-epoch v3/v4 anchor")
        old_point = next(r for r in old["mlp32"]["curve"] if r["epoch"] == 300)
        same_metrics(anchor["fit"], old_point["fit"], "300-epoch v3/v4 fit")
        same_metrics(anchor["inner"], old_point["inner"], "300-epoch v3/v4 inner")
    elif anchor is not None or "mlp_anchor_300.json" in claimed:
        raise ValueError("Unreached MLP anchor was fabricated")
    tree = result["hist_boosted"]
    if ([r["iterations"] for r in tree["curve"]] != list(budget.TREE_ITERATIONS)
            or tree["anchor_at_200"] != tree["curve"][1]):
        raise ValueError("Tree candidate grid/anchor changed")
    tree_chosen = budget.choose_inner(tree["curve"], index="iterations")
    if (tree_chosen["iterations"] != tree["selected_iterations"]
            or tree["selected_inner_log_loss"] != tree_chosen["inner"]["weighted_log_loss"]):
        raise ValueError("Tree candidate not chosen by inner loss")
    tree_selection = read(progress / "tree_inner_selection.json")
    if tree_selection["selected_iterations"] != tree["selected_iterations"]:
        raise ValueError("Persisted pre-outer tree selection changed")
    near(tree_selection["selected_inner_log_loss"], tree["selected_inner_log_loss"],
         "tree selection loss")
    for row in tree["curve"]:
        count = row["iterations"]
        candidate = progress / f"tree_candidate_{count:04d}.joblib"
        metadata = read(progress / f"tree_candidate_{count:04d}.json")
        if metadata["iterations"] != count or metadata["model_sha256"] != base.sha(candidate):
            raise ValueError("Persisted tree candidate hash changed")
        same_metrics(metadata["fit"], row["fit"], "tree candidate fit")
        same_metrics(metadata["inner"], row["inner"], "tree candidate inner")
    old_tree_point = next(r for r in old["hist_boosted"]["curve"] if r["iterations"] == 200)
    same_metrics(tree["anchor_at_200"]["fit"], old_tree_point["fit"], "200-tree v3/v4 fit")
    same_metrics(tree["anchor_at_200"]["inner"], old_tree_point["inner"], "200-tree v3/v4 inner")
    return {"mlp_selected_epoch": mlp["selected_epoch"],
            "mlp_stopped_epoch": mlp["stopped_epoch"],
            "mlp_anchor_300_reached": anchor is not None,
            "mlp_anchor_matches_v3": anchor is not None,
            "mlp_selected_inner_minus_fit_log_loss":
                chosen["inner"]["weighted_log_loss"]-chosen["fit"]["weighted_log_loss"],
            "mlp_300_inner_minus_fit_log_loss":
                anchor["inner"]["weighted_log_loss"]-anchor["fit"]["weighted_log_loss"]
                if anchor is not None else None,
            "tree_selected_iterations": tree["selected_iterations"],
            "tree_200_inner_minus_fit_log_loss":
                tree["anchor_at_200"]["inner"]["weighted_log_loss"]-
                tree["anchor_at_200"]["fit"]["weighted_log_loss"],
            "tree_selected_inner_minus_fit_log_loss":
                tree_chosen["inner"]["weighted_log_loss"]-
                tree_chosen["fit"]["weighted_log_loss"]}


def replay(output=OUTPUT):
    if sklearn.__version__ != "1.7.2":
        raise ValueError("Pinned scikit-learn 1.7.2 required")
    if base.sha(OLD_REPLAY) != OLD_REPLAY_SHA:
        raise ValueError("Frozen v3 replay changed")
    old_replay = read(OLD_REPLAY)
    replay3.verify_common32_lineage()
    if not RESULTS.is_dir():
        raise ValueError("Complete v4 collection is not present")
    folders = sorted(p.name for p in RESULTS.glob("task[0-9][0-9]") if p.is_dir())
    if folders != [f"task{i:02d}" for i in range(12)]:
        raise ValueError("Refusing a partial or extra v4 task set")
    # Read only completion controls first; no model or outer result from a
    # partially collected array is inspected.
    for task_id in range(12):
        folder = RESULTS / f"task{task_id:02d}"
        receipt_path = folder / "receipt.json"
        result_path = folder / "result.json"
        tree_path = folder / "hist_boosted.joblib"
        wrappers = list(RESULTS.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
        if (not receipt_path.is_file() or not result_path.is_file()
                or not tree_path.is_file() or len(wrappers) != 1):
            raise ValueError("Refusing incomplete v4 collection before outcome read")
        receipt, wrapper = read(receipt_path), read(wrappers[0])
        if (receipt.get("status") != "completed" or receipt.get("task_id") != task_id
                or wrapper.get("returncode") != 0 or wrapper.get("timeout_exit") is not False):
            raise ValueError("Refusing failed/incomplete v4 array before outcome read")
    dataset = previous.load_pool(pool.OUTPUTS[128],
        expected_manifest_sha256=replay3.POOL_SHA, prefix=128)
    eligibility = {r["base_group"]: r for r in dataset["group_eligibility"]}
    observations = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    task_checks = []
    for task_id in range(12):
        folder = RESULTS / f"task{task_id:02d}"
        result_path, receipt_path, tree_path = (folder / n for n in
            ("result.json", "receipt.json", "hist_boosted.joblib"))
        result, receipt = read(result_path), read(receipt_path)
        old_folder = OLD_RESULTS / f"task{task_id:02d}"
        old_result_path = old_folder / "result.json"
        old_receipt, old = read(old_folder / "receipt.json"), read(old_result_path)
        wrappers = list(RESULTS.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
        if len(wrappers) != 1:
            raise ValueError(f"Task {task_id} lacks unique completed wrapper")
        wrapper = read(wrappers[0])
        identity = read(folder / "source_identity.json")
        if (receipt.get("status") != "completed" or receipt.get("task_id") != task_id
                or result.get("task_id") != task_id or result.get("policy") != budget.POLICY
                or receipt.get("policy") != budget.POLICY
                or result.get("prefix_groups_intended") != 128
                or receipt.get("prefix_groups_intended") != 128
                or result.get("pool_manifest_sha256") != replay3.POOL_SHA
                or receipt.get("pool_manifest_sha256") != replay3.POOL_SHA
                or receipt.get("result_sha256") != base.sha(result_path)
                or receipt.get("hist_boosted_sha256") != base.sha(tree_path)
                or receipt.get("source_identity_sha256") != base.sha(folder / "source_identity.json")
                or result.get("source_hashes") != identity.get("source_hashes")
                or receipt.get("source_hashes") != identity.get("source_hashes")
                or result.get("source_commit") != identity.get("source_commit")
                or receipt.get("source_commit") != identity.get("source_commit")
                or wrapper.get("returncode") != 0 or wrapper.get("timeout_exit") is not False
                or wrapper.get("task_id") != task_id
                or wrapper.get("pool_manifest_sha256") != replay3.POOL_SHA
                or old_receipt.get("result_sha256") != base.sha(old_result_path)
                or old_receipt.get("hist_boosted_sha256") != base.sha(old_folder / "hist_boosted.joblib")
                or old.get("policy") != previous.POLICY
                or result.get("runtime_versions") != identity.get("runtime_versions")
                or receipt.get("runtime_versions") != identity.get("runtime_versions")
                or result.get("runtime_versions") != {"sklearn": "1.7.2", "joblib": "1.5.2",
                                                      "numpy": "1.26.4", "scipy": "1.13.1"}
                or result.get("no_outer_selection") is not True
                or result.get("optimization_budget_change_only") is not True):
            raise ValueError(f"Task {task_id} receipt/identity/policy mismatch")
        for name, sha in identity["source_hashes"].items():
            if base.sha(ROOT / name) != sha:
                raise ValueError(f"Task {task_id} source changed: {name}")
        fit_g, inner_g, outer_g = previous.grouped_split(dataset["groups"], task_id//3)
        if (tuple(result["fit_groups"]) != fit_g or tuple(result["inner_groups"]) != inner_g
                or tuple(result["outer_groups"]) != outer_g or result["fold"] != task_id//3
                or result["seed"] != previous.SEEDS[task_id%3]
                or any(result[k] != old[k] for k in
                    ("fit_groups", "inner_groups", "outer_groups", "seed", "features",
                     "fit_weights", "inner_weights", "outer_weights", "input_table_hashes"))):
            raise ValueError("v4/v3 fit-inner-outer split, seed, features, or weights changed")
        fit = [s for s in dataset["samples"] if s["group"] in fit_g]
        inner = [s for s in dataset["samples"] if s["group"] in inner_g]
        outer = [s for s in dataset["samples"] if s["group"] in outer_g]
        fit_x, fit_y, fit_w = previous._stack(fit)
        inner_x, inner_y, inner_w = previous._stack(inner)
        outer_x, outer_y, outer_w = previous._stack(outer)
        mean, scale = frozen._preprocess(fit_x)
        if (not np.allclose(mean, result["feature_mean_fit_only"])
                or not np.allclose(scale, result["feature_scale_fit_only"])
                or not np.allclose(mean, old["feature_mean_fit_only"])
                or not np.allclose(scale, old["feature_scale_fit_only"])):
            raise ValueError("v4/v3 preprocessing differs from same fit-only inputs")
        z, inner_z, fit_z = (outer_x-mean)/scale, (inner_x-mean)/scale, (fit_x-mean)/scale
        progress_summary = _progress(folder, receipt, result, old)
        old_tree = joblib.load(old_folder / "hist_boosted.joblib")
        if old["hist_boosted"]["selected_iterations"] != 200:
            raise ValueError("Frozen v3 tree is not its 200-iteration anchor")
        anchor_tree = joblib.load(folder / "inner_progress/tree_candidate_0200.joblib")
        for xx, label in ((fit_z, "fit"), (inner_z, "inner"), (z, "outer")):
            if not np.allclose(anchor_tree.predict_proba(xx), old_tree.predict_proba(xx),
                               atol=1e-9, rtol=1e-9):
                raise ValueError(f"200-tree v3/v4 anchor predictions differ on {label}")
        if result["mlp32"]["anchor_at_300"] is not None:
            anchor_p = frozen._mlp_predict(result["mlp32"]["anchor_at_300"], z)
            old_p = frozen._mlp_predict(old["mlp32"], z)
            if not np.allclose(anchor_p, old_p, atol=1e-9, rtol=1e-9):
                raise ValueError("300-epoch v3/v4 MLP anchor predictions differ")
        controls, prevalence, rates = frozen._controls(fit_x, fit_y, fit_w, outer_x)
        near(prevalence, result["control_prevalence_fit_only"], "fit prevalence")
        if not np.allclose(rates, result["control_kind_rates_fit_only"]):
            raise ValueError("Kind control rates changed")
        if not np.allclose(result["logistic"]["coef"], old["logistic"]["coef"], atol=1e-9, rtol=1e-9):
            raise ValueError("Unchanged logistic fit coefficients changed")
        if not np.allclose(result["logistic"]["intercept"], old["logistic"]["intercept"], atol=1e-9, rtol=1e-9):
            raise ValueError("Unchanged logistic intercept changed")
        logistic_p = frozen._sigmoid(z @ np.asarray(result["logistic"]["coef"])[0]
                                     + result["logistic"]["intercept"][0])
        tree = joblib.load(tree_path)
        predictions = {**controls, "logistic": logistic_p,
                       "mlp32": frozen._mlp_predict(result["mlp32"], z),
                       "hist_boosted": tree.predict_proba(z)[:, 1]}
        inner_controls, _, _ = frozen._controls(fit_x, fit_y, fit_w, inner_x)
        inner_predictions = {**inner_controls,
            "logistic": frozen._sigmoid(inner_z @ np.asarray(result["logistic"]["coef"])[0]
                                        + result["logistic"]["intercept"][0]),
            "mlp32": frozen._mlp_predict(result["mlp32"], inner_z),
            "hist_boosted": tree.predict_proba(inner_z)[:, 1]}
        for name in NAMES:
            inner_metrics = frozen._metrics(inner_y, inner_predictions[name], inner_w, inner)
            same_metrics(inner_metrics, result["inner_metrics"][name],
                         f"selected inner metrics/{task_id}/{name}")
        rows = result["outer_predictions"]
        old_rows = old["outer_predictions"]
        if len(rows) != len(outer_y) or len(old_rows) != len(rows):
            raise ValueError("Outer row denominator differs")
        cursor = 0
        for sample in outer:
            n = len(sample["y"])
            for j, (row, old_row, mid, y) in enumerate(zip(rows[cursor:cursor+n],
                    old_rows[cursor:cursor+n], sample["movement_ids"], sample["y"])):
                keys = ("base_group", "source", "movement_id", "observed_selected",
                        "input_trip_count_k")
                expected = (sample["group"], sample["source"], mid, bool(y),
                            min(sample["trip_count"], n))
                if tuple(row[k] for k in keys) != expected or tuple(old_row[k] for k in keys) != expected:
                    raise ValueError("v4/v3 outer row keys, labels, or ranking budget differ")
                for name in NAMES:
                    near(row["probabilities"][name], predictions[name][cursor+j],
                         f"saved outer probability/{name}", atol=1e-9)
                    if name in ("constant", "kind_frequency", "logistic"):
                        near(row["probabilities"][name], old_row["probabilities"][name],
                             f"unchanged v3/v4 outer probability/{name}", atol=1e-9)
            for name in NAMES:
                p = predictions[name][cursor:cursor+n]
                metrics = frozen._metrics(sample["y"], p, np.ones(n)/n, [sample])
                saved = result["outer_per_group_source"][sample["group"]][sample["source"]][name]
                same_metrics(metrics, saved, f"{sample['group']}/{sample['source']}/{name}")
                for metric in METRICS:
                    observations[sample["group"]][sample["source"]][name][metric].append(metrics[metric])
            cursor += n
        for group in outer_g:
            if set(result["outer_per_group_source"].get(group, {})) != set(eligibility[group]["observed_sources"]):
                raise ValueError("Observed/censored group source denominator changed")
            for name in NAMES:
                calculated = replay3.macro_sources([result["outer_per_group_source"][group][s][name]
                    for s in eligibility[group]["observed_sources"]])
                same_metrics(calculated, result["outer_per_group"][group][name],
                             f"group macro/{group}/{name}")
        for name in NAMES:
            saved_p = np.asarray([r["probabilities"][name] for r in rows])
            pooled = frozen._metrics(outer_y, saved_p, outer_w, outer)
            same_metrics(pooled, result["outer_pooled_diagnostics_secondary"][name],
                         f"pooled diagnostic/{task_id}/{name}")
            macro = replay3.macro_sources([result["outer_per_group"][g][name] for g in outer_g])
            same_metrics(macro, result["outer_metrics"][name], f"outer macro/{task_id}/{name}")
            common = tuple(g for g in outer_g if int(g.removeprefix("physical_v2_s")) < 10032)
            if tuple(result["outer_original32_common_groups"]) != common:
                raise ValueError("Common-32 outer group membership changed")
            common_macro = replay3.macro_sources([result["outer_per_group"][g][name] for g in common])
            same_metrics(common_macro, result["outer_original32_common_group_metrics"][name],
                         f"common-32 macro/{task_id}/{name}")
        task_checks.append({"task_id": task_id, "fold": result["fold"], "seed": result["seed"],
            "outer_groups": result["outer_groups"], "fit_groups_intended": len(fit_g),
            "inner_groups_intended": len(inner_g), "outer_groups_intended": len(outer_g),
            "fit_fleets_observed": len(fit), "inner_fleets_observed": len(inner),
            "outer_fleets_observed": len(outer), "outer_edges_observed": len(outer_y),
            "result_sha256": base.sha(result_path), "receipt_sha256": base.sha(receipt_path),
            "wrapper_sha256": base.sha(wrappers[0]),
            "selected_outer_metrics": result["outer_metrics"], **progress_summary})
    group_metrics = {}
    for group in dataset["groups"]:
        source_map = observations[group]
        if set(source_map) != set(eligibility[group]["observed_sources"]):
            raise ValueError(f"Missing source/seed observations: {group}")
        group_metrics[group] = {}
        for name in NAMES:
            group_metrics[group][name] = {}
            for metric in METRICS:
                per_source = []
                for source in eligibility[group]["observed_sources"]:
                    values = source_map[source][name][metric]
                    if len(values) != 3:
                        raise ValueError("Not exactly three outer seed observations")
                    valid = [v for v in values if v is not None]
                    per_source.append(statistics.mean(valid) if valid else None)
                valid = [v for v in per_source if v is not None]
                group_metrics[group][name][metric] = statistics.mean(valid) if valid else None
    earlier = old_replay["per_group_seed_and_source_averages"]
    if set(group_metrics) != set(earlier) or len(group_metrics) != 128:
        raise ValueError("v4/v3 complete group registry differs")
    common32 = tuple(f"physical_v2_s{i}" for i in range(10000, 10032))
    full128 = tuple(dataset["groups"])
    aggregate = {name: {metric: metric_summary(group_metrics[g][name][metric] for g in full128)
                       for metric in METRICS} for name in NAMES}
    common_aggregate = {name: {metric: metric_summary(group_metrics[g][name][metric] for g in common32)
                              for metric in METRICS} for name in NAMES}
    mlp_sel = [row["mlp_selected_epoch"] for row in task_checks]
    mlp_stop = [row["mlp_stopped_epoch"] for row in task_checks]
    tree_sel = [row["tree_selected_iterations"] for row in task_checks]
    artifact = {"schema": "physical-route128-budget-v4-replay-v1",
        "pool_manifest_sha256": replay3.POOL_SHA,
        "frozen_v3_replay_sha256": OLD_REPLAY_SHA,
        "sklearn_runtime_version": sklearn.__version__,
        "strict_saved_model_replay": True,
        "no_model_fit_or_outer_checkpoint_selection": True,
        "independent_groups_intended": 128,
        "groups_eligible_observed": len(group_metrics),
        "source_fleets_intended": 256,
        "source_fleets_observed": len(dataset["samples"]),
        "registered_one_source_group": "physical_v2_s10037",
        "seeds_per_group": 3,
        "task_checks": task_checks,
        "mlp32": {"selected_epoch": metric_summary(mlp_sel),
                  "stopped_epoch": metric_summary(mlp_stop),
                  "anchor_300_reached_tasks": sum(r["mlp_anchor_300_reached"] for r in task_checks),
                  "selected_inner_minus_fit_log_loss": metric_summary(
                      r["mlp_selected_inner_minus_fit_log_loss"] for r in task_checks),
                  "anchor_300_inner_minus_fit_log_loss": metric_summary(
                      r["mlp_300_inner_minus_fit_log_loss"] for r in task_checks),
                  "early_stopped_tasks": sum(v < budget.MLP_MAX_EPOCHS for v in mlp_stop)},
        "hist_boosted": {"selected_iterations": dict(Counter(tree_sel)),
                         "selected_inner_minus_fit_log_loss": metric_summary(
                             r["tree_selected_inner_minus_fit_log_loss"] for r in task_checks),
                         "anchor_200_inner_minus_fit_log_loss": metric_summary(
                             r["tree_200_inner_minus_fit_log_loss"] for r in task_checks)},
        "equal_group_aggregate_full128": aggregate,
        "equal_group_aggregate_common32": common_aggregate,
        "paired_v4_vs_v3_full128": paired(group_metrics, earlier, full128),
        "paired_v4_vs_v3_common32": paired(group_metrics, earlier, common32),
        "per_group_seed_and_source_averages": group_metrics,
        "interpretation_scope": "observed feasible source-incumbent movement classification only; no route feasibility or cost claim"}
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Replay output is immutable")
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False)+"\n")
    return artifact


if __name__ == "__main__":
    result = replay()
    print(json.dumps({"output": str(OUTPUT), "groups": result["independent_groups_intended"],
                      "source_fleets": result["source_fleets_observed"],
                      "strict_saved_model_replay": True}, sort_keys=True))
