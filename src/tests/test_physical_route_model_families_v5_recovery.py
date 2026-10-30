"""Infrastructure-only recovery guards; no real TRAIN outcomes are read."""
import json
import signal
from pathlib import Path

import pytest

from experiments import recover_physical_route_model_families_v5 as recovery


def original(tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    source = checkout / "frozen.py"
    source.write_text("frozen source\n")
    monkeypatch.setattr(recovery, "ROOT", checkout)
    monkeypatch.setattr(recovery, "FROZEN_SOURCE_FILES", ("frozen.py",))
    root = tmp_path / "original"
    task = root / "task00"
    task.mkdir(parents=True)
    (task / "inner_progress").mkdir()
    (task / "launch.json").write_text(json.dumps({"task_id": 0, "pool_manifest_sha256": recovery.POOL_SHA}))
    (task / "source_identity.json").write_text(json.dumps({
        "source_commit": recovery.ORIGINAL_COMMIT, "pool_manifest_sha256": recovery.POOL_SHA,
        "source_hashes": {"frozen.py": recovery.sha(source)}}))
    (root / "task00.slurm_wrapper_receipt.720838.json").write_text(json.dumps({
        "task_id": 0, "returncode": 132, "array_job_id": "720831",
        "pool_manifest_sha256": recovery.POOL_SHA}))
    return root, task, source


def test_recovery_requires_original_sigill_empty_progress_and_frozen_source(tmp_path, monkeypatch):
    root, task, source = original(tmp_path, monkeypatch)
    evidence = recovery.original_evidence(root, 0)
    assert evidence["original_array_job_id"] == "720831"
    wrapper_path = root / "task00.slurm_wrapper_receipt.720838.json"
    wrapper = json.loads(wrapper_path.read_text())
    wrapper["returncode"] = 1
    wrapper_path.write_text(json.dumps(wrapper))
    with pytest.raises(ValueError, match="does not identify.*SIGILL"):
        recovery.original_evidence(root, 0)
    wrapper["returncode"] = 132
    wrapper_path.write_text(json.dumps(wrapper))
    with pytest.raises(ValueError, match="nine original SIGILL"):
        recovery.original_evidence(root, 2)
    source.write_text("changed\n")
    with pytest.raises(ValueError, match="Frozen training source differs"):
        recovery.original_evidence(root, 0)
    source.write_text("frozen source\n")
    marker = task / "inner_progress/xgboost_candidate0_start.json"
    marker.write_text("{}")
    with pytest.raises(ValueError, match="candidate progress"):
        recovery.original_evidence(root, 0)
    marker.unlink()
    (task / "receipt.json").write_text('{"status":"completed"}')
    with pytest.raises(ValueError, match="no training receipt/result"):
        recovery.original_evidence(root, 0)


def test_native_signal_is_saved_by_surviving_supervisor(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "ROOT", tmp_path)
    code = "import os, resource, signal; resource.setrlimit(resource.RLIMIT_CORE, (0, 0)); os.kill(os.getpid(), signal.SIGILL)"
    row = recovery.native_stage(tmp_path, "import_probe", code, timeout_seconds=10)
    assert row["returncode"] == -signal.SIGILL
    assert row["signal"] == "SIGILL"
    assert json.loads((tmp_path / "import_probe_receipt.json").read_text())["signal"] == "SIGILL"
    assert (tmp_path / "import_probe_start.json").is_file()


def test_failed_preflight_stops_training_and_retry(tmp_path, monkeypatch):
    root, task, _ = original(tmp_path, monkeypatch)
    output = tmp_path / "recovery"
    monkeypatch.setattr(recovery, "OUTPUT_ROOT", output)
    monkeypatch.setattr(recovery, "RECOVERY_SOURCES", ("frozen.py",))
    monkeypatch.setattr(recovery.socket, "gethostname", lambda: "unicorn-cpu-75")
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "1")
    monkeypatch.setenv("SLURM_JOB_CPUS_PER_NODE", "1")
    monkeypatch.setattr(recovery.platform, "platform", lambda: "synthetic-test-platform")
    monkeypatch.setattr(recovery.subprocess, "check_output", lambda *a, **k: "recoverycommit\n")
    stages = []
    def fail(directory, name, code, **kwargs):
        stages.append(name)
        return {"returncode": -signal.SIGILL, "signal": "SIGILL"}
    monkeypatch.setattr(recovery, "native_stage", fail)
    assert recovery.run(0, root) == 132
    assert stages == ["import_xgboost"]
    assert not (output / "task00").exists()
    assert not (task / "receipt.json").exists()
    row = json.loads((output / "task00.runtime/recovery_receipt.json").read_text())
    assert row["status"] == "runtime_preflight_failed"
    with pytest.raises(FileExistsError):
        recovery.run(0, root)


def test_declared_node_and_allocation_guard_before_child(tmp_path, monkeypatch):
    root, _, _ = original(tmp_path, monkeypatch)
    monkeypatch.setattr(recovery.socket, "gethostname", lambda: "snavely-cpu-01")
    with pytest.raises(ValueError, match="observed successful"):
        recovery.run(0, root)
    monkeypatch.setattr(recovery.socket, "gethostname", lambda: "unicorn-cpu-75")
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "2")
    with pytest.raises(ValueError, match="requested CPU"):
        recovery.run(0, root)


def test_native_timeout_has_distinct_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "ROOT", tmp_path)
    row = recovery.native_stage(tmp_path, "slow_probe", "import time; time.sleep(10)", timeout_seconds=.05)
    assert row["returncode"] == 124
    assert row["timeout"] is True
    assert row["signal"] is None
    assert (tmp_path / "slow_probe_receipt.json").is_file()


def test_truncated_original_source_map_is_rejected(tmp_path, monkeypatch):
    root, _, _ = original(tmp_path, monkeypatch)
    # The one-entry fixture is internally valid but incomplete for this declaration.
    monkeypatch.setattr(recovery, "FROZEN_SOURCE_FILES", ("frozen.py", "omitted.py"))
    with pytest.raises(ValueError, match="exact frozen 18-path set"):
        recovery.original_evidence(root, 0)
