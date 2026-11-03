"""One immutable 32-group grouped-CV CPU task with nested stopping discipline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
import traceback

import joblib
import numpy as np
import scipy
import sklearn

from egglab import physical_route_model_v2 as model
from experiments import computational_benchmark as base

OUTPUT_ROOT = base.ROOT / "result/physical_learning/20260930-route-model32-v2"
EXPECTED_SKLEARN = "1.7.2"
EXPECTED_JOBLIB = "1.5.2"
EXPECTED_NUMPY = "1.26.4"
EXPECTED_SCIPY = "1.13.1"
SOURCE_FILES = (
    "src/egglab/physical_route_model_v2.py",
    "src/experiments/train_physical_route_model_v2.py",
    "src/experiments/pool_physical_route_training.py",
    "src/cluster/physical_route_model_v2.sbatch",
    "src/tests/test_physical_route_model_v2.py",
    "research-20260930/learning-campaign/ROUTE_MODEL32_TRAINING_PROTOCOL.md",
    "src/egglab/learned_proposals.py",
    "src/egglab/physical_learning_cases.py",
    "src/egglab/native_recharge.py",
    "src/egglab/native_pathflow.py",
    "src/experiments/computational_benchmark.py",
)


def versions():
    return {"sklearn": sklearn.__version__, "joblib": joblib.__version__,
        "numpy": np.__version__, "scipy": scipy.__version__}


def run(task_id, pool_manifest_sha256, output_root=OUTPUT_ROOT):
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
    try:
        base.save_new(destination / "launch.json", {"policy": model.POLICY,
            "task_id": task_id, "fold": task_id // len(model.SEEDS),
            "seed": model.SEEDS[task_id % len(model.SEEDS)],
            "pool_manifest_sha256": pool_manifest_sha256,
            "started_unix": time.time(),
            "launch_before_source_hash_and_data_load": True})
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=base.ROOT, text=True).strip()
        source_hashes = {name: base.sha(base.ROOT / name) for name in SOURCE_FILES}
        base.save_new(destination / "source_identity.json", {"source_commit": source_commit,
            "source_hashes": source_hashes, "runtime_versions": versions(),
            "pool_manifest_sha256": pool_manifest_sha256})
        if versions() != {"sklearn": EXPECTED_SKLEARN, "joblib": EXPECTED_JOBLIB,
                "numpy": EXPECTED_NUMPY, "scipy": EXPECTED_SCIPY}:
            raise ValueError("Pinned 32-group sklearn/runtime versions differ")
        dataset = model.load_pool(expected_manifest_sha256=pool_manifest_sha256)
        result, tree = model.run_fold(dataset, task_id)
        result.update({"wall_seconds": time.monotonic()-started,
            "runtime_versions": versions(), "source_commit": source_commit,
            "source_hashes": source_hashes})
        tree_path = destination / "hist_boosted.joblib"
        with tree_path.open("xb") as stream:
            joblib.dump(tree, stream)
        base.save_new(destination / "result.json", result)
        base.save_new(destination / "receipt.json", {"policy": model.POLICY,
            "task_id": task_id, "status": "completed", "source_commit": source_commit,
            "source_hashes": source_hashes, "pool_manifest_sha256": pool_manifest_sha256,
            "source_identity_sha256": base.sha(destination / "source_identity.json"),
            "result_sha256": base.sha(destination / "result.json"),
            "hist_boosted_sha256": base.sha(tree_path),
            "wall_seconds": result["wall_seconds"], "runtime_versions": versions()})
        return {"task_id": task_id, "fold": result["fold"], "seed": result["seed"],
            "outer_groups": result["outer_groups"], "wall_seconds": result["wall_seconds"],
            "output": str(destination)}
    except BaseException as exc:
        base.save_new(destination / "failure.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "wall_seconds": time.monotonic()-started})
        base.save_new(destination / "receipt.json", {"policy": model.POLICY,
            "task_id": task_id, "status": "failed", "source_commit": source_commit,
            "source_hashes": source_hashes, "pool_manifest_sha256": pool_manifest_sha256,
            "failure_sha256": base.sha(destination / "failure.json"),
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
