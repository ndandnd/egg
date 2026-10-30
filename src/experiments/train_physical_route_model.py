"""One immutable CPU task: grouped source-edge scorer training and evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
import traceback

import numpy as np

from egglab import physical_route_model as model
from experiments import computational_benchmark as base

OUTPUT_ROOT = base.ROOT / "result/physical_learning/20260930-route-model-pilot"
SOURCE_FILES = (
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


def run(task_id, output_root=OUTPUT_ROOT):
    if task_id not in range(model.FOLDS*len(model.SEEDS)):
        raise ValueError("Task ID is outside the frozen 12-task grid")
    output_root = Path(output_root).resolve()
    destination = output_root / f"task{task_id:02d}"
    if destination.exists():
        raise ValueError("Training task output is immutable; task already exists")
    started = time.monotonic()
    destination.mkdir(parents=True, exist_ok=False)
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=base.ROOT, text=True).strip()
    source_hashes = {name: base.sha(base.ROOT / name) for name in SOURCE_FILES}
    base.save_new(destination / "launch.json", {"policy": model.POLICY,
        "task_id": task_id, "fold": task_id // len(model.SEEDS),
        "seed": model.SEEDS[task_id % len(model.SEEDS)],
        "source_commit": source_commit, "source_hashes": source_hashes,
        "dataset_receipt_sha256": model.DATASET_RECEIPT_SHA256,
        "training_config": {"epochs": model.EPOCHS, "learning_rate": model.LEARNING_RATE,
            "ridge": model.RIDGE, "hidden_units": model.HIDDEN}})
    try:
        dataset = model.load_dataset()
        result = model.run_fold(dataset, task_id)
        result["wall_seconds"] = time.monotonic()-started
        result["numpy_version"] = np.__version__
        result["source_commit"] = source_commit
        result["source_hashes"] = source_hashes
        base.save_new(destination / "result.json", result)
        base.save_new(destination / "receipt.json", {"policy": model.POLICY,
            "task_id": task_id, "dataset_receipt_sha256": dataset["receipt_sha256"],
            "result_sha256": base.sha(destination / "result.json"),
            "source_commit": source_commit, "source_hashes": source_hashes,
            "wall_seconds": result["wall_seconds"], "status": "completed"})
        return {"task_id": task_id, "fold": result["fold"], "seed": result["seed"],
            "heldout_groups": result["heldout_groups"], "wall_seconds": result["wall_seconds"],
            "output": str(destination)}
    except BaseException as exc:
        base.save_new(destination / "failure.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "wall_seconds": time.monotonic()-started})
        base.save_new(destination / "receipt.json", {"policy": model.POLICY,
            "task_id": task_id, "status": "failed", "source_commit": source_commit,
            "source_hashes": source_hashes,
            "dataset_receipt_sha256": model.DATASET_RECEIPT_SHA256,
            "failure_sha256": base.sha(destination / "failure.json"),
            "wall_seconds": time.monotonic()-started})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", type=int, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.task_id), sort_keys=True))


if __name__ == "__main__":
    main()
