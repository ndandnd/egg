"""One immutable exact-128 three-family grouped-CV CPU task."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import traceback

import joblib
import numpy as np
import scipy
import sklearn

from egglab import physical_route_model_families_v5 as model
from experiments import pool_physical_route_training_v3 as pool
from experiments import computational_benchmark as base

OUTPUT_ROOT = base.ROOT / "result/physical_learning/20260930-route-model128-families-v5"
POOL_SHA = "d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d"
EXPECTED_SKLEARN = "1.7.2"
EXPECTED_JOBLIB = "1.5.2"
EXPECTED_NUMPY = "1.26.4"
EXPECTED_SCIPY = "1.13.1"
EXPECTED_XGBOOST = "3.0.5"
EXPECTED_CATBOOST = "1.2.8"
SOURCE_FILES = (
    "src/egglab/physical_route_model_families_v5.py",
    "src/experiments/train_physical_route_model_families_v5.py",
    "src/cluster/physical_route_model_families_v5.sbatch",
    "src/cluster/unicorn_env.sh",
    "src/tests/test_physical_route_model_families_v5.py",
    "research-20260930/learning-campaign/ROUTE_MODEL_FAMILIES_V5_PROTOCOL.md",
    "research-20260930/learning-campaign/ROUTE_FAMILY_ENVIRONMENT.json",
    "research-20260930/learning-campaign/route-family-requirements-frozen.txt",
    "src/egglab/physical_route_model_v3.py",
    "src/experiments/pool_physical_route_training_v3.py",
    "research-20260930/learning-campaign/ROUTE_MODEL64_128_V3_PROTOCOL.md",
    "src/egglab/physical_route_model_v2.py",
    "research-20260930/learning-campaign/ROUTE_MODEL32_TRAINING_PROTOCOL.md",
    "src/egglab/learned_proposals.py",
    "src/egglab/physical_learning_cases.py",
    "src/egglab/native_recharge.py",
    "src/egglab/native_pathflow.py",
    "src/experiments/computational_benchmark.py",
)


def versions():
    def maybe(name):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return None
    return {"sklearn": sklearn.__version__, "joblib": joblib.__version__,
        "numpy": np.__version__, "scipy": scipy.__version__,
        "xgboost": maybe("xgboost-cpu") or maybe("xgboost"),
        "catboost": maybe("catboost")}


class Progress:
    """Append-only candidate models and inner decisions before outer scoring."""

    def __init__(self, destination: Path):
        self.path = destination / "inner_progress"
        self.path.mkdir(exist_ok=False)

    def start_candidate(self, family, index, config):
        if family not in model.FAMILIES or index not in (0, 1):
            raise ValueError("Unknown declared candidate")
        base.save_new(self.path / f"{family}_candidate{index}_start.json",
            {"family": family, "candidate_index": index,
             "config": dict(config), "started_unix": time.time()})

    def candidate(self, family, index, fitted, row):
        if family not in model.FAMILIES or index not in (0, 1):
            raise ValueError("Unknown declared candidate")
        name = f"{family}_candidate{index}"
        extension = {"xgboost": ".json", "catboost": ".cbm",
                     "extra_trees": ".joblib"}[family]
        path = self.path / (name+extension)
        if family == "extra_trees":
            with path.open("xb") as stream:
                joblib.dump(fitted, stream)
        else:
            if path.exists():
                raise ValueError("Candidate output is immutable")
            fitted.save_model(str(path))
        if not path.is_file() or not path.stat().st_size:
            raise ValueError("Candidate model was not serialized")
        evidence = {"path": str(path.relative_to(self.path.parent)),
            "sha256": base.sha(path), "format": extension.removeprefix(".")}
        base.save_new(self.path / (name+"_inner.json"), {**row, "saved_model": evidence})
        return evidence

    def selection(self, family, row):
        base.save_new(self.path / f"{family}_inner_selection.json", row)

    def promotion(self, row):
        base.save_new(self.path / "inner_family_promotion.json", row)

    def hashes(self):
        return {path.name: base.sha(path) for path in sorted(self.path.iterdir())}


def run(task_id, pool_manifest_sha256, output_root=None):
    if pool_manifest_sha256 != POOL_SHA:
        raise ValueError("Only the pinned exact-128 TRAIN pool is declared")
    output_root = output_root or OUTPUT_ROOT
    if task_id not in range(model.FOLDS*len(model.SEEDS)):
        raise ValueError("Task ID outside frozen 12-task grid")
    if len(pool_manifest_sha256) != 64 or any(c not in "0123456789abcdef" for c in pool_manifest_sha256):
        raise ValueError("Explicit pooled-manifest SHA-256 required")
    destination = Path(output_root).resolve() / f"task{task_id:02d}"
    if destination.exists():
        raise ValueError("Training task output is immutable; no retry")
    started = time.monotonic()
    destination.mkdir(parents=True, exist_ok=False)
    source_commit = None
    source_hashes = None
    progress = None
    try:
        base.save_new(destination / "launch.json", {"policy": model.POLICY,
            "task_id": task_id, "prefix_groups_intended": model.PREFIX,
            "fold": task_id // len(model.SEEDS),
            "seed": model.SEEDS[task_id % len(model.SEEDS)],
            "pool_manifest_sha256": pool_manifest_sha256,
            "started_unix": time.time(),
            "launch_before_source_hash_and_data_load": True})
        progress = Progress(destination)
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=base.ROOT, text=True).strip()
        source_hashes = {name: base.sha(base.ROOT / name) for name in SOURCE_FILES}
        base.save_new(destination / "source_identity.json", {"source_commit": source_commit,
            "source_hashes": source_hashes, "runtime_versions": versions(),
            "pool_manifest_sha256": pool_manifest_sha256})
        if versions() != {"sklearn": EXPECTED_SKLEARN, "joblib": EXPECTED_JOBLIB,
                "numpy": EXPECTED_NUMPY, "scipy": EXPECTED_SCIPY,
                "xgboost": EXPECTED_XGBOOST, "catboost": EXPECTED_CATBOOST}:
            raise ValueError("Pinned family/runtime versions differ")
        # Package metadata alone is insufficient: fail with a typed import error
        # if either native extension cannot actually load in this interpreter.
        importlib.import_module("xgboost")
        importlib.import_module("catboost")
        from egglab import physical_route_model_v3 as admitted
        dataset = admitted.load_pool(pool.OUTPUTS[model.PREFIX],
            expected_manifest_sha256=pool_manifest_sha256, prefix=model.PREFIX)
        result = model.run_fold(dataset, task_id, progress)
        result.update({"wall_seconds": time.monotonic()-started,
            "runtime_versions": versions(), "source_commit": source_commit,
            "source_hashes": source_hashes})
        base.save_new(destination / "result.json", result)
        base.save_new(destination / "receipt.json", {"policy": model.POLICY,
            "task_id": task_id, "prefix_groups_intended": model.PREFIX,
            "status": "completed", "source_commit": source_commit,
            "source_hashes": source_hashes, "pool_manifest_sha256": pool_manifest_sha256,
            "source_identity_sha256": base.sha(destination / "source_identity.json"),
            "result_sha256": base.sha(destination / "result.json"),
            "candidate_and_inner_progress_hashes": progress.hashes(),
            "all_candidate_fit_time_included_in_wall_seconds": True,
            "wall_seconds": result["wall_seconds"], "runtime_versions": versions()})
        return {"task_id": task_id, "fold": result["fold"], "seed": result["seed"],
            "outer_groups": result["outer_groups"], "wall_seconds": result["wall_seconds"],
            "output": str(destination)}
    except BaseException as exc:
        base.save_new(destination / "failure.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "wall_seconds": time.monotonic()-started})
        base.save_new(destination / "receipt.json", {"policy": model.POLICY,
            "task_id": task_id, "prefix_groups_intended": model.PREFIX,
            "status": "failed", "source_commit": source_commit,
            "source_hashes": source_hashes, "pool_manifest_sha256": pool_manifest_sha256,
            "failure_sha256": base.sha(destination / "failure.json"),
            "candidate_and_inner_progress_hashes": progress.hashes() if progress is not None else {},
            "wall_seconds": time.monotonic()-started, "runtime_versions": versions()})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--pool-manifest-sha256", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.task_id, args.pool_manifest_sha256), sort_keys=True))


if __name__ == "__main__":
    main()
