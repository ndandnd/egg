"""One prospective infrastructure recovery task; original v5 training is unchanged.

Only stdlib is imported in this supervisor, so native child signals are recorded.
No TRAIN outcomes are opened to decide recovery eligibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_COMMIT = "75dd4cf19f1f735cc3dea559567da3b2bd32013e"
POOL_SHA = "d9aad5b5ea62fd82a8b4f6a3c20a95c57953ba12c7bf0949fa06004aa511c40d"
FAILED_TASKS = (0, 1, 4, 5, 6, 7, 8, 9, 11)
COMPLETED_TASKS = (2, 3, 10)
FROZEN_SOURCE_FILES = (
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
OUTPUT_ROOT = ROOT / "result/physical_learning/20260930-route-model128-families-v5-recovery1"
RECOVERY_SOURCES = (
    "src/experiments/recover_physical_route_model_families_v5.py",
    "src/cluster/physical_route_model_families_v5_recovery1.sbatch",
    "research-20260930/learning-campaign/ROUTE_MODEL_FAMILIES_V5_RECOVERY1_PROTOCOL.md",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, row):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(row, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def original_evidence(original_root, task_id):
    """Read launch/identity/wrapper receipts only, never result or inner metrics."""
    if task_id not in FAILED_TASKS:
        raise ValueError("Only the nine original SIGILL tasks are declared for recovery")
    original_root = Path(original_root).resolve()
    task = original_root / f"task{task_id:02d}"
    if (task / "receipt.json").exists() or (task / "result.json").exists():
        raise ValueError("Recovery requires an original task with no training receipt/result")
    launch_path = task / "launch.json"
    identity_path = task / "source_identity.json"
    launch = json.loads(launch_path.read_text())
    identity = json.loads(identity_path.read_text())
    if launch["task_id"] != task_id or launch["pool_manifest_sha256"] != POOL_SHA:
        raise ValueError("Original task identity/pool differs")
    if identity["source_commit"] != ORIGINAL_COMMIT or identity["pool_manifest_sha256"] != POOL_SHA:
        raise ValueError("Original source commit/pool differs")
    wrappers = list(original_root.glob(f"task{task_id:02d}.slurm_wrapper_receipt.*.json"))
    if len(wrappers) != 1:
        raise ValueError("Exactly one original wrapper receipt required")
    wrapper = json.loads(wrappers[0].read_text())
    if (wrapper["returncode"] != 132 or wrapper["task_id"] != task_id
            or wrapper["array_job_id"] != "720831" or wrapper["pool_manifest_sha256"] != POOL_SHA):
        raise ValueError("Original wrapper does not identify array720831 SIGILL")
    progress = task / "inner_progress"
    if progress.exists() and any(progress.iterdir()):
        raise ValueError("Original task has candidate progress; undeclared resume refused")
    hashes = identity["source_hashes"]
    if not isinstance(hashes, dict) or set(hashes) != set(FROZEN_SOURCE_FILES):
        raise ValueError("Original source hashes must contain the exact frozen 18-path set")
    for name, digest in hashes.items():
        if sha(ROOT / name) != digest:
            raise ValueError(f"Frozen training source differs: {name}")
    return {"original_attempt_root": str(original_root), "original_task_id": task_id,
        "original_array_job_id": "720831", "original_source_commit": ORIGINAL_COMMIT,
        "launch_sha256": sha(launch_path), "source_identity_sha256": sha(identity_path),
        "wrapper_receipt_sha256": sha(wrappers[0]), "original_source_hashes": hashes}


def native_stage(directory, name, code, timeout_seconds=60):
    """Child-only numerical imports; parent survives SIGILL to save its receipt."""
    save_new(directory / f"{name}_start.json", {"stage": name, "started_unix": time.time()})
    started = time.monotonic()
    timed_out = False
    with (directory / f"{name}.stdout").open("x") as out, (directory / f"{name}.stderr").open("x") as err:
        try:
            completed = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                stdout=out, stderr=err, timeout=timeout_seconds, check=False)
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = 124
    row = {"stage": name, "returncode": returncode, "timeout": timed_out,
        "signal": signal.Signals(-returncode).name if returncode < 0 else None,
        "elapsed_seconds": time.monotonic()-started,
        "stdout_sha256": sha(directory / f"{name}.stdout"),
        "stderr_sha256": sha(directory / f"{name}.stderr")}
    save_new(directory / f"{name}_receipt.json", row)
    return row


IMPORT_PROBES = (
    ("import_xgboost", "import xgboost; assert xgboost.__version__ == '3.0.5'; print(xgboost.__version__)"),
    ("import_catboost", "import catboost; assert catboost.__version__ == '1.2.8'; print(catboost.__version__)"),
)
TINY_FIT = '''
import numpy as np
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier
x = np.arange(128, dtype=float).reshape(32, 4) / 128
y = np.arange(32) % 2
for model in (XGBClassifier(n_estimators=2, max_depth=2, tree_method="hist", n_jobs=1),
              CatBoostClassifier(iterations=2, depth=2, thread_count=1, verbose=False,
                  allow_writing_files=False),
              ExtraTreesClassifier(n_estimators=2, max_depth=2, n_jobs=1, random_state=17)):
    model.fit(x, y)
    p = model.predict_proba(x)
    assert p.shape == (32, 2) and np.isfinite(p).all()
    print(type(model).__name__, "tiny synthetic fit/predict completed", flush=True)
'''


def run(task_id, original_root):
    evidence = original_evidence(original_root, task_id)
    if socket.gethostname().split(".")[0] != "unicorn-cpu-75":
        raise ValueError("Only the observed successful one-CPU node unicorn-cpu-75 is declared")
    if os.environ.get("SLURM_CPUS_PER_TASK") != "1":
        raise ValueError("Recovery requires exactly one requested CPU")
    if Path(original_root).resolve() == OUTPUT_ROOT.resolve():
        raise ValueError("Recovery output must be separate from the original attempt")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    diagnostics = OUTPUT_ROOT / f"task{task_id:02d}.runtime"
    diagnostics.mkdir(exist_ok=False)  # exclusive guard; no automatic resume/retry
    started = time.monotonic()
    save_new(diagnostics / "recovery_launch.json", {**evidence,
        "task_id": task_id, "output_root": str(OUTPUT_ROOT), "hostname": socket.gethostname(),
        "platform": platform.platform(), "python": sys.executable, "started_unix": time.time(),
        "requested_cpus_per_task": os.environ.get("SLURM_CPUS_PER_TASK"),
        "allocated_job_cpus": os.environ.get("SLURM_JOB_CPUS_PER_NODE"),
        "allocated_memory": os.environ.get("SLURM_MEM_PER_NODE"),
        "recovery_source_hashes": {name: sha(ROOT / name) for name in RECOVERY_SOURCES},
        "recovery_source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "cpuinfo": Path("/proc/cpuinfo").read_text() if Path("/proc/cpuinfo").exists() else None,
        "selection_basis": "Original SIGILL/infrastructure evidence only"})
    for name, code in (*IMPORT_PROBES, ("tiny_native_fit", TINY_FIT)):
        row = native_stage(diagnostics, name, code)
        if row["returncode"]:
            save_new(diagnostics / "recovery_receipt.json", {"task_id": task_id,
                "status": "runtime_preflight_failed", "failed_stage": name, **row})
            return 128-row["returncode"] if row["returncode"] < 0 else row["returncode"]
    # Invoke exactly the frozen runner, preserving all scientific settings.
    code = ("import json; from experiments.train_physical_route_model_families_v5 import run; "
            f"print(json.dumps(run({task_id}, {POOL_SHA!r}, output_root={str(OUTPUT_ROOT)!r}), sort_keys=True))")
    remaining = max(1, 1680-int(time.monotonic()-started))
    row = native_stage(diagnostics, "frozen_training", code, timeout_seconds=remaining)
    save_new(diagnostics / "recovery_receipt.json", {"task_id": task_id,
        "status": "completed" if row["returncode"] == 0 else "training_failed",
        "elapsed_seconds_total": time.monotonic()-started, **row})
    return 128-row["returncode"] if row["returncode"] < 0 else row["returncode"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", type=int, choices=FAILED_TASKS, required=True)
    parser.add_argument("--original-attempt-root", type=Path, required=True)
    args = parser.parse_args(argv)
    return run(args.task_id, args.original_attempt_root)


if __name__ == "__main__":
    raise SystemExit(main())
