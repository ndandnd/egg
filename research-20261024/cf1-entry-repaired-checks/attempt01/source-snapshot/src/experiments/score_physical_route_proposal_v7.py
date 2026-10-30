"""Hash-pinned saved-model inference only, in separate existing CPU runtimes."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
POOL_SHA = "d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d"
POLICY = "physical-route-proposals-heldout-train-v7"
GROUP_IDS = tuple(range(10064, 10080))
ARMS = ("tabular_v3", "families_v5", "graph_v6")
MODEL_ROOTS = {"tabular_v3": "result/physical_learning/20260930-route-model128-v3",
              "families_v5": "result/physical_learning/20260930-route-model128-families-v5-recovery1",
              "graph_v6": "result/physical_learning/20260930-route-model128-graph-v6"}
MODEL_POLICIES = {"tabular_v3": "physical-source-movement-scorer-exact-prefix-v3",
                  "families_v5": "physical-source-movement-families-exact128-v5",
                  "graph_v6": "physical-source-movement-graph-exact128-v6"}
SOURCE_FILES = (
    "src/egglab/physical_route_proposal_v7.py", "src/experiments/score_physical_route_proposal_v7.py",
    "src/experiments/physical_route_proposal_pilot_v7.py", "src/cluster/physical_route_proposal_pilot_v7.sbatch",
    "research-20260930/learning-campaign/ROUTE_PROPOSAL_TRAIN_V7_PROTOCOL.md",
    "src/egglab/physical_route_decoder_v1.py", "src/egglab/route_fixed_repair.py",
    "src/egglab/learned_proposals.py", "src/egglab/physical_learning_cases.py",
    "src/egglab/physical_route_model_v2.py", "src/egglab/physical_route_model_v3.py",
    "src/egglab/physical_route_model_families_v5.py", "src/egglab/physical_route_graph_v6.py",
    "src/egglab/native_recharge.py", "src/egglab/native_pathflow.py", "src/egglab/native_hull.py",
    "src/egglab/native_pathflow_hull.py", "src/egglab/restricted_qp_proposal.py", "src/egglab/solver.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/retrieval_comparison.py", "src/experiments/pool_physical_route_training_v3.py",
    "src/cluster/unicorn_env.sh",
)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, row):
    with Path(path).open("x") as stream:
        json.dump(row, stream, indent=2, sort_keys=True, allow_nan=False); stream.write("\n")


def checked_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise ValueError("Artifact escapes checkout")
    return path


def verify_files(hashes):
    if not hashes or any(sha(checked_path(p)) != value for p, value in hashes.items()):
        raise ValueError("Pinned artifact changed")


def validate_partition(group_id, result):
    from egglab import physical_route_model_v3 as previous
    fold = (group_id-10000) % 4
    groups = tuple(f"physical_v2_s{i}" for i in range(10000, 10128))
    expected = previous.grouped_split(groups, fold)
    if result["seed"] != 17 or result["fold"] != fold or result["task_id"] != fold*3:
        raise ValueError("Not the declared seed17 outer-fold model")
    for name, values in zip(("fit_groups", "inner_groups", "outer_groups"), expected):
        if tuple(result[name]) != values:
            raise ValueError("Frozen grouped partition differs")
    group = f"physical_v2_s{group_id}"
    if group not in result["outer_groups"] or group in result["fit_groups"] or group in result["inner_groups"]:
        raise ValueError("Proposal group leaks into fit/inner selection")


def model_folder(arm, task):
    # Preserve successful original v5 task3; never require a nonexistent recovery.
    root = ("result/physical_learning/20260930-route-model128-families-v5"
            if arm == "families_v5" and task in (2, 3, 10) else MODEL_ROOTS[arm])
    return ROOT / root / f"task{task:02d}"


def freeze(destination, graph_replay, graph_replay_sha):
    """Metadata/hashes only: no outcome metrics, source labels, fitting or scoring."""
    attestations = {}
    names = {"tabular_v3": "ROUTE_MODEL128_REPLAY.json", "families_v5": "ROUTE_FAMILIES_V5_REPLAY.json",
             "graph_v6": graph_replay}
    for arm, name in names.items():
        path = checked_path(name if "/" in name else "research-20260930/learning-campaign/"+name)
        if arm == "graph_v6" and sha(path) != graph_replay_sha:
            raise ValueError("Graph replay is not the reviewed hash")
        evidence = read(path)
        if arm == "tabular_v3" and evidence.get("strict_saved_model_replay") is not True:
            raise ValueError("Baseline replay not passed")
        if arm == "families_v5" and evidence.get("saved_model_numerical_replay_passed") is not True:
            raise ValueError("Family numerical replay not passed")
        if arm == "graph_v6" and evidence.get("passed") is not True:
            raise ValueError("Graph replay not passed")
        if evidence.get("pool_manifest_sha256") != POOL_SHA:
            raise ValueError("Replay attestation pool differs")
        attestations[arm] = {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
    models = {}
    for arm in ARMS:
        models[arm] = {}
        for task in (0, 3, 6, 9):
            folder = model_folder(arm, task)
            receipt = read(folder / "receipt.json")
            if receipt.get("status") != "completed" or receipt.get("policy") != MODEL_POLICIES[arm] or receipt["task_id"] != task or receipt["pool_manifest_sha256"] != POOL_SHA:
                raise ValueError("Incomplete frozen model")
            identity = read(folder / "source_identity.json")
            if receipt["source_identity_sha256"] != sha(folder / "source_identity.json") or not identity["source_hashes"]:
                raise ValueError("Missing native model source lineage")
            if receipt["result_sha256"] != sha(folder / "result.json"):
                raise ValueError("Model result changed")
            files = {str((folder / name).relative_to(ROOT)): sha(folder / name)
                     for name in (("receipt.json", "source_identity.json", "launch.json") if arm == "graph_v6" else ("receipt.json", "result.json", "source_identity.json"))}
            if arm == "tabular_v3":
                if receipt["hist_boosted_sha256"] != sha(folder / "hist_boosted.joblib"):
                    raise ValueError("Baseline tree changed")
                files[str((folder / "hist_boosted.joblib").relative_to(ROOT))] = receipt["hist_boosted_sha256"]
            else:
                hashes = receipt["candidate_and_inner_progress_hashes" if arm == "families_v5" else "inner_progress_hashes"]
                progress = folder / "inner_progress"
                if arm == "families_v5":
                    promotion = read(progress / "inner_family_promotion.json")
                    family = promotion["family"]
                    selection = read(progress / f"{family}_inner_selection.json")
                    index = selection["candidate_index"]
                    metadata = read(progress / f"{family}_candidate{index}_inner.json")
                    names = ["inner_family_promotion.json"] + [f"{f}_inner_selection.json" for f in ("xgboost", "catboost", "extra_trees")]
                    names += [f"{family}_candidate{i}_inner.json" for i in (0, 1)]
                else:
                    promotion = read(progress / "inner_architecture_promotion.json")
                    family = promotion["family"]
                    metadata = read(progress / f"{family}_selected_inner.json")
                    names = ["inner_architecture_promotion.json", "fit_only_preprocessing_and_groups.json",
                             "mean_message_selected_inner.json", "graph_attention_selected_inner.json"]
                model_path = checked_path(str((folder / metadata["saved_model"]["path"]).relative_to(ROOT)))
                if not model_path.is_relative_to(progress) or sha(model_path) != metadata["saved_model"]["sha256"]:
                    raise ValueError("Selected saved-model evidence differs")
                names.append(model_path.name)
                for name in names:
                    digest = hashes[name]; path = progress / name
                    if sha(path) != digest:
                        raise ValueError("Persisted inner/model evidence changed")
                    files[str(path.relative_to(ROOT))] = digest
            models[arm][str(task)] = {"folder": str(folder.relative_to(ROOT)), "files": files,
                "source_commit": identity["source_commit"], "training_source_hashes": identity["source_hashes"]}
    pool_path = "result/physical_learning/20260930-route-pool128-v3"
    if sha(ROOT / pool_path / "pool_manifest.json") != POOL_SHA:
        raise ValueError("Pool differs")
    row = {"policy": POLICY, "group_ids": GROUP_IDS, "target_kind": "day", "seed": 17,
        "pool_path": pool_path, "pool_manifest_sha256": POOL_SHA, "models": models,
        "replay_attestations": attestations, "source_hashes": {p: sha(ROOT/p) for p in SOURCE_FILES},
        "no_outcome_based_selection": True, "no_fit": True,
        "graph_replay_review_gate": "explicit reviewed graph replay SHA required by launch owner"}
    save(destination, row)
    return {"path": str(destination), "sha256": sha(destination)}


def score(arm, group_id, manifest):
    import numpy as np
    from egglab import learned_proposals as edge
    from egglab import physical_route_proposal_v7 as proposal
    if arm not in ARMS or group_id not in GROUP_IDS:
        raise ValueError("Undeclared arm/group")
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "scikit-learn", "joblib")}
    if versions != {"numpy": "1.26.4", "scipy": "1.13.1", "scikit-learn": "1.7.2", "joblib": "1.5.2"}:
        raise ValueError("Unpinned inference runtime")
    if arm == "families_v5":
        import xgboost, catboost
        if (xgboost.__version__, catboost.__version__) != ("3.0.5", "1.2.8"):
            raise ValueError("Unpinned native family runtime")
        versions.update(xgboost=xgboost.__version__, catboost=catboost.__version__)
    if arm == "graph_v6":
        import torch
        if str(torch.__version__) != "2.4.1+cpu":
            raise ValueError("Unpinned CPU graph runtime")
        versions["torch"] = str(torch.__version__)
    started = time.monotonic()
    entry = manifest["models"][arm][str(((group_id-10000)%4)*3)]
    verify_files(entry["files"])
    folder = checked_path(entry["folder"])
    if arm == "graph_v6":
        preprocess = read(folder / "inner_progress/fit_only_preprocessing_and_groups.json")
        result = {**preprocess, "policy": MODEL_POLICIES[arm], "seed": 17, "fold": (group_id-10000)%4, "task_id": ((group_id-10000)%4)*3,
            "feature_mean_fit_only": preprocess["mean_fit_only"], "feature_scale_fit_only": preprocess["scale_fit_only"],
            "pool_manifest_sha256": POOL_SHA}
    else:
        result = read(folder / "result.json")  # Access only preprocessing/partition/inner fields.
    validate_partition(group_id, result)
    if result.get("policy") != MODEL_POLICIES[arm] or result.get("pool_manifest_sha256") != POOL_SHA or tuple(result["features"]) != edge.FEATURES:
        raise ValueError("Frozen model features/pool differ")
    mean, scale = np.asarray(result["feature_mean_fit_only"]), np.asarray(result["feature_scale_fit_only"])
    if mean.shape != (len(edge.FEATURES),) or scale.shape != mean.shape or not np.isfinite(mean).all() or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("Invalid fit-only preprocessing")
    selected = "hist_boosted"
    if arm == "tabular_v3":
        import joblib
        fitted = joblib.load(folder / "hist_boosted.joblib")
        if type(fitted).__name__ != "HistGradientBoostingClassifier":
            raise ValueError("Baseline model type differs")
    elif arm == "families_v5":
        from egglab import physical_route_model_families_v5 as families
        promotion = read(folder / "inner_progress/inner_family_promotion.json")
        selections = {f: read(folder / "inner_progress" / f"{f}_inner_selection.json") for f in families.FAMILIES}
        selected = min(families.FAMILIES, key=lambda f: (selections[f]["inner_weighted_log_loss"], families.FAMILIES.index(f)))
        if promotion != result["inner_family_promotion"] or promotion["family"] != selected:
            raise ValueError("Inner family policy differs")
        choice = selections[selected]; index = choice["candidate_index"]
        row = read(folder / "inner_progress" / f"{selected}_candidate{index}_inner.json")
        candidates = [read(folder / "inner_progress" / f"{selected}_candidate{i}_inner.json") for i in (0, 1)]
        if index != families.select_candidate(candidates) or choice["saved_model"] != row["saved_model"]:
            raise ValueError("Inner candidate choice differs")
        path = folder / row["saved_model"]["path"]
        if sha(path) != row["saved_model"]["sha256"]:
            raise ValueError("Selected model changed")
        if selected == "xgboost":
            params = dict(row["fitted_parameters"])
            if params.get("missing") == "nan": params["missing"] = np.nan
            fitted = xgboost.XGBClassifier(**params); fitted.load_model(path); fitted.set_params(n_jobs=1)
            if fitted.best_iteration != row["checkpoint"]["best_iteration_zero_based"] or fitted.get_booster().num_boosted_rounds() != row["checkpoint"]["stopped_rounds"]:
                raise ValueError("XGBoost checkpoint differs")
        elif selected == "catboost":
            fitted = catboost.CatBoostClassifier(thread_count=1); fitted.load_model(str(path))
            if fitted.tree_count_ != row["checkpoint"]["selected_rounds"]:
                raise ValueError("CatBoost retained trees differ")
        else:
            import joblib
            fitted = joblib.load(path)
            if type(fitted).__name__ != "ExtraTreesClassifier" or fitted.n_jobs != 1:
                raise ValueError("ExtraTrees worker/type differs")
    else:
        from egglab import physical_route_graph_v6 as graph
        graph.configure_cpu()
        promotion = read(folder / "inner_progress/inner_architecture_promotion.json")
        rows = {f: read(folder / "inner_progress" / f"{f}_selected_inner.json") for f in graph.FAMILIES}
        selected = graph.select_family(rows)
        if promotion["family"] != selected or promotion["inner_weighted_log_losses"] != {f: rows[f]["inner_weighted_log_loss"] for f in graph.FAMILIES}:
            raise ValueError("Inner graph policy differs")
        preprocess = read(folder / "inner_progress/fit_only_preprocessing_and_groups.json")
        if not np.array_equal(mean, preprocess["mean_fit_only"]) or not np.array_equal(scale, preprocess["scale_fit_only"]):
            raise ValueError("Persisted graph preprocessing differs")
        path = folder / rows[selected]["saved_model"]["path"]
        if sha(path) != rows[selected]["saved_model"]["sha256"]:
            raise ValueError("Selected graph weights changed")
        fitted = graph.restore_model(path)
    load_seconds = time.monotonic()-started
    case, market, _, _ = proposal.inputs(group_id, manifest)
    inference = time.monotonic(); x = edge.edge_features(case, market.a)
    if arm == "graph_v6":
        sample = {"x": x, "graph": graph.topology(case), "group": f"physical_v2_s{group_id}", "source": "prospective_day",
                  "trip_count": len(case.trips)}
        with torch.no_grad():
            logits = fitted(graph.batches([sample], mean, scale, labelled=False)[0]).numpy()
    else:
        z = (x-mean)/scale
        p = families._probability(selected, fitted, z) if arm == "families_v5" else fitted.predict_proba(z)[:, 1]
        p = np.clip(p, 1e-9, 1-1e-9); logits = np.log(p)-np.log1p(-p)
    if logits.shape != (len(case.movements),) or not np.isfinite(logits).all():
        raise ValueError("Invalid saved-model logits")
    return {"arm": arm, "group_id": group_id, "case_identity": case.identity(), "market_identity": market.identity(),
        "movement_ids": [m.id for m in case.movements], "logits": logits.tolist(), "selected_model": selected,
        "model_entry": entry, "runtime_versions": versions, "artifact_load_seconds": load_seconds,
        "score_inference_seconds": time.monotonic()-inference, "seed": 17, "fold": result["fold"],
        "held_out_from_fit_and_inner": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="mode", required=True)
    frozen = sub.add_parser("freeze"); frozen.add_argument("--output", type=Path, required=True)
    frozen.add_argument("--graph-replay", required=True); frozen.add_argument("--graph-replay-sha", required=True)
    scoring = sub.add_parser("score"); scoring.add_argument("--arm", choices=ARMS, required=True)
    scoring.add_argument("--group-id", type=int, required=True); scoring.add_argument("--manifest", type=Path, required=True)
    scoring.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "freeze":
        print(json.dumps(freeze(args.output, args.graph_replay, args.graph_replay_sha)))
    else:
        save(args.output, score(args.arm, args.group_id, read(args.manifest)))


if __name__ == "__main__": main()
