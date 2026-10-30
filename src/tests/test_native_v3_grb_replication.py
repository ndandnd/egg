"""Solver-free launch and failure-evidence controls for the GRB replication."""
import json
from pathlib import Path
import subprocess

import pytest

from experiments import native_pathflow_hull_qualification as hull
from experiments import native_v3_grb_replication as gate


def test_backend_specific_hull_paths_are_exclusive(tmp_path):
    assert hull.check_output_path("CBC", hull.ATTEMPT) == hull.ATTEMPT
    assert hull.check_output_path("GRB", hull.GRB_ATTEMPT) == hull.GRB_ATTEMPT
    for backend, path in (("CBC", hull.GRB_ATTEMPT), ("GRB", hull.ATTEMPT),
                          ("GRB", tmp_path / "other"), ("OTHER", hull.GRB_ATTEMPT)):
        with pytest.raises(ValueError, match="Backend and exclusive"):
            hull.check_output_path(backend, path)


def test_wrapper_rejects_wrong_or_existing_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "PATHS", {"physical": tmp_path / "physical",
                                         "hull": tmp_path / "hull"})
    with pytest.raises(ValueError, match="exclusive"):
        gate.check_path("physical", tmp_path / "hull")
    (tmp_path / "physical.launch").mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        gate.check_path("physical", tmp_path / "physical")
    (tmp_path / "physical.launch").rmdir()
    (tmp_path / "physical").mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        gate.check_path("physical", tmp_path / "physical")


def test_hull_cannot_start_without_independent_physical_admission(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "ADMISSION", tmp_path / "absent.json")
    with pytest.raises(ValueError, match="audit/admission is absent"):
        gate.check_physical_admission({})


@pytest.mark.parametrize("mode,expected_rc,timeout,unchanged", [
    ("child_failure", 7, False, True),
    ("timeout", 124, True, True),
    ("source_drift", 1, False, False),
    ("source_check_error", 1, False, False),
    ("missing_result", 1, False, True),
])
def test_wrapper_seals_failure_evidence(tmp_path, monkeypatch, mode, expected_rc, timeout, unchanged):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    output = tmp_path / "result" / "physical"
    monkeypatch.setattr(gate, "PATHS", {"physical": output, "hull": tmp_path / "result" / "hull"})
    monkeypatch.setattr(gate, "check_published", lambda hashes, commit: None)
    values = iter(({"source": "first"}, {"source": "changed"}) if mode == "source_drift"
                  else ({"source": "first"}, {"source": "first"}))
    def hashes(stage):
        if mode == "source_check_error" and output.exists():
            raise FileNotFoundError("pinned source deleted")
        return next(values)
    monkeypatch.setattr(gate, "source_hashes", hashes)
    if mode != "missing_result":
        monkeypatch.setattr(gate, "stage_evidence", lambda *args: None)
    monkeypatch.setattr(gate.os, "killpg", lambda pid, sig: None)

    class FakeProcess:
        pid = 123
        def __init__(self):
            self.calls = 0
        def wait(self, timeout=None):
            self.calls += 1
            if mode == "timeout" and self.calls == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            return 7 if mode == "child_failure" else 0

    monkeypatch.setattr(gate.subprocess, "Popen", lambda *a, **k: FakeProcess())
    rc = gate.run("physical", output, "a" * 40)
    receipt = json.loads((output / "grb_wrapper_receipt.json").read_text())
    manifest = json.loads((output / "MANIFEST.json").read_text())
    assert rc == receipt["returncode"] == expected_rc
    assert receipt["outer_timeout"] is timeout
    assert receipt["source_hashes_unchanged"] is unchanged
    assert bool(receipt["source_check_error"]) is (mode == "source_check_error")
    assert bool(receipt["stage_evidence_error"]) is (mode == "missing_result")
    assert "grb_wrapper_receipt.json" in manifest["files"]
    assert "grb_wrapper_launch.json" in manifest["files"]
    assert "grb_wrapper_stdout.txt" in manifest["files"]
    assert "grb_wrapper_stderr.txt" in manifest["files"]
    sentinel = Path(str(output) + ".launch")
    assert (sentinel / "launch.json").is_file()
    assert (sentinel / "completion.json").is_file()
    with pytest.raises(FileExistsError):
        gate.check_path("physical", output)


def test_stage_evidence_requires_complete_control_set(tmp_path):
    attempt = tmp_path / "attempt"
    attempt.mkdir()
    gate.write_new(attempt / "frozen.json", {"protocol": gate.physical.PROTOCOL,
                   "freeze_label": "a" * 40, "budget": {"backend": "GRB"},
                   "controls": [], "source_hashes": {}})
    gate.write_new(attempt / "summary.json", {"protocol": gate.physical.PROTOCOL,
                   "cells": [], "all_pass": True, "source_hashes_unchanged": True})
    with pytest.raises(ValueError, match="Incomplete GRB"):
        gate.stage_evidence("physical", attempt, {}, "a" * 40)
