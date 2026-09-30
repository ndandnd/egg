"""One immutable prospective exact128 graph-model CPU task; no automatic retry."""
from __future__ import annotations

import argparse
import json
import importlib.metadata
from pathlib import Path
import platform
import subprocess
import time
import traceback

import numpy as np
import scipy
import sklearn
import torch

from egglab import physical_route_graph_v6 as model
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool

OUTPUT_ROOT = base.ROOT / "result/physical_learning/20260930-route-model128-graph-v6"
EXPECTED_RUNTIME = {"numpy": "1.26.4", "scipy": "1.13.1", "sklearn": "1.7.2", "torch": "2.4.1+cpu", "joblib": "1.5.2"}
SOURCE_FILES = (
    "src/cluster/physical_route_graph_v6.sbatch",
    "src/experiments/probe_physical_route_graph_v6.py",
    "research-20260930/learning-campaign/ROUTE_GRAPH_ENVIRONMENT.json",
    "research-20260930/learning-campaign/route-graph-requirements-frozen.txt",
    "src/egglab/physical_route_graph_v6.py",
    "src/experiments/train_physical_route_graph_v6.py",
    "src/tests/test_physical_route_graph_v6.py",
    "research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_V6_PROTOCOL.md",
    "src/egglab/physical_route_model_v3.py", "src/egglab/physical_route_model_v2.py",
    "src/experiments/pool_physical_route_training_v3.py",
    "src/egglab/learned_proposals.py", "src/egglab/physical_learning_cases.py",
    "src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
    "src/experiments/computational_benchmark.py",
)


def versions():
    return {"numpy": np.__version__, "scipy": scipy.__version__,
            "sklearn": sklearn.__version__, "torch": str(torch.__version__),
            "joblib": importlib.metadata.version("joblib")}


def prediction_rows(samples, probabilities):
    rows, cursor = [], 0
    for sample in samples:
        n = len(sample["movement_ids"])
        rows.extend({"base_group": sample["group"], "source": sample["source"],
            "movement_id": mid, "observed_selected": bool(sample["y"][i]),
            "probability": float(probabilities[cursor+i])}
            for i, mid in enumerate(sample["movement_ids"]))
        cursor += n
    if cursor != len(probabilities):
        raise ValueError("Saved predictions and movement IDs differ")
    return rows


class Progress:
    def __init__(self, destination):
        self.path = Path(destination) / "inner_progress"
        self.path.mkdir(exist_ok=False)
        self.persistence_seconds = 0.

    def _save(self, path, row):
        started = time.monotonic()
        try:
            base.save_new(path, row)
        finally:
            self.persistence_seconds += time.monotonic()-started

    def _model(self, fitted, path):
        started = time.monotonic()
        try:
            model.save_model(fitted, path)
        finally:
            self.persistence_seconds += time.monotonic()-started

    def preprocessing(self, row):
        self._save(self.path / "fit_only_preprocessing_and_groups.json", row)

    def start_candidate(self, family, config):
        self._save(self.path / f"{family}_start.json", {"family": family,
            "config": config, "started_unix": time.time()})

    def epoch(self, family, epoch, fitted, row):
        name = f"{family}_epoch{epoch:04d}"
        checkpoint = None
        if fitted is not None:
            path = self.path / (name+".npz")
            self._model(fitted, path)
            checkpoint = {"path": str(path.relative_to(self.path.parent)), "sha256": base.sha(path)}
        self._save(self.path / (name+".json"), {**row, "checkpoint": checkpoint})

    def candidate(self, family, fitted, row, fit, fit_p, inner, inner_p):
        path = self.path / f"{family}_selected.npz"
        self._model(fitted, path)
        evidence = {"path": str(path.relative_to(self.path.parent)), "sha256": base.sha(path),
                    "format": "numeric npz; allow_pickle=False"}
        self._save(self.path / f"{family}_selected_inner.json", {**row, "saved_model": evidence})
        self._save(self.path / f"{family}_fit_predictions.json", prediction_rows(fit, fit_p))
        self._save(self.path / f"{family}_inner_predictions.json", prediction_rows(inner, inner_p))
        return evidence

    def promotion(self, row):
        self._save(self.path / "inner_architecture_promotion.json", row)

    def hashes(self):
        return {p.name: base.sha(p) for p in sorted(self.path.iterdir()) if p.is_file()}


def run(task_id, pool_manifest_sha256, output_root=None):
    if pool_manifest_sha256 != model.POOL_SHA or task_id not in range(model.FOLDS*len(model.SEEDS)):
        raise ValueError("Only pinned exact128 TRAIN and frozen12 tasks are declared")
    destination = Path(output_root or OUTPUT_ROOT).resolve() / f"task{task_id:02d}"
    if destination.exists():
        raise ValueError("Graph task output is immutable; no retry")
    started = time.monotonic(); destination.mkdir(parents=True, exist_ok=False)
    progress, identity = None, None
    try:
        base.save_new(destination / "launch.json", {"policy": model.POLICY, "task_id": task_id,
            "pool_manifest_sha256": pool_manifest_sha256, "started_unix": time.time(),
            "launch_before_source_hash_and_data_load": True})
        progress = Progress(destination)
        identity = {"source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
                cwd=base.ROOT, text=True).strip(),
            "source_hashes": {name: base.sha(base.ROOT / name) for name in SOURCE_FILES},
            "runtime_versions": versions(), "platform": platform.platform(),
            "torch_build": torch.__config__.show(), "pool_manifest_sha256": pool_manifest_sha256}
        base.save_new(destination / "source_identity.json", identity)
        if versions() != EXPECTED_RUNTIME:
            raise ValueError("Pinned Linux CPU graph runtime versions differ")
        model.configure_cpu()
        data = model.load_pool(pool.OUTPUTS[model.PREFIX], expected_manifest_sha256=pool_manifest_sha256)
        result = model.run_fold(data, task_id, progress)
        result.update({"wall_seconds": time.monotonic()-started, "source_identity": identity})
        base.save_new(destination / "result.json", result)
        base.save_new(destination / "receipt.json", {"policy": model.POLICY, "task_id": task_id,
            "status": "completed", "pool_manifest_sha256": pool_manifest_sha256,
            "source_identity_sha256": base.sha(destination / "source_identity.json"),
            "result_sha256": base.sha(destination / "result.json"),
            "inner_progress_hashes": progress.hashes(), "wall_seconds": result["wall_seconds"]})
        return {"task_id": task_id, "output": str(destination), "wall_seconds": result["wall_seconds"]}
    except BaseException as exc:
        base.save_new(destination / "failure.json", {"type": type(exc).__name__,
            "message": str(exc), "traceback": traceback.format_exc(),
            "wall_seconds": time.monotonic()-started})
        base.save_new(destination / "receipt.json", {"policy": model.POLICY, "task_id": task_id,
            "status": "failed", "pool_manifest_sha256": pool_manifest_sha256,
            "source_identity": identity, "failure_sha256": base.sha(destination / "failure.json"),
            "inner_progress_hashes": progress.hashes() if progress else {},
            "wall_seconds": time.monotonic()-started})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--pool-manifest-sha256", required=True)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.task_id, args.pool_manifest_sha256, args.output_root), sort_keys=True))


if __name__ == "__main__":
    main()
