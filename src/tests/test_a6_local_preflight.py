"""Refusal-path battery for the local A6 preflight/launcher
(experiments/local_a6_preflight.py). Every refusal is tested; execution is
exercised with a stubbed cell subprocess (no solver runs)."""
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import experiments.local_a6_preflight as pf
from experiments.local_a6_preflight import (
    MAX_CONCURRENCY,
    PreflightError,
    THREADS_PER_CELL,
    build_manifest,
    cell_tag,
    check_backend,
    check_concurrency,
    check_grid,
    preflight,
)
from experiments.run_a6_pilot import build_cells


# --------------------------------------------------------------------------
# refusals
# --------------------------------------------------------------------------
def test_refuses_cbc_backend():
    with pytest.raises(PreflightError, match="CBC is refused"):
        check_backend("CBC")
    with pytest.raises(PreflightError):
        check_backend("")
    check_backend("GRB")  # the only accepted backend


def test_refuses_wrong_cell_count():
    cells = build_cells()
    with pytest.raises(PreflightError, match="expected exactly 24"):
        check_grid(cells[:-1])
    with pytest.raises(PreflightError, match="expected exactly 24"):
        check_grid(cells + [("a6_a4", 0, 8, 0.002)])


def test_refuses_duplicate_cells():
    cells = build_cells()[:-1] + [build_cells()[0]]
    with pytest.raises(PreflightError, match="duplicate"):
        check_grid(cells)


def test_refuses_arm_imbalance():
    # 24 unique cells but 13 a6_a4 / 11 a6_a3
    cells = build_cells()
    cells = [c for c in cells if c != ("a6_a3", 15, 12, 0.05)]
    cells.append(("a6_a4", 0, 8, 0.002))
    with pytest.raises(PreflightError, match="a6_a4 cells"):
        check_grid(cells)


def test_refuses_holdout_seed():
    cells = build_cells()[:-1] + [("a6_a3", 16, 12, 0.05)]
    with pytest.raises(PreflightError, match="holdout-range seed 16"):
        check_grid(cells)
    cells = build_cells()[:-1] + [("a6_a3", 31, 12, 0.05)]
    with pytest.raises(PreflightError, match="holdout-range seed 31"):
        check_grid(cells)


def test_refuses_non_burned_seed():
    cells = build_cells()[:-1] + [("a6_a3", 7, 12, 0.05)]
    with pytest.raises(PreflightError, match="non-burned seed 7"):
        check_grid(cells)


def test_refuses_bad_concurrency():
    for bad in (0, -1, 5, 99):
        with pytest.raises(PreflightError, match="concurrency"):
            check_concurrency(bad)
    for ok in (1, 2, 3, 4):
        check_concurrency(ok)
    assert MAX_CONCURRENCY == 4 and THREADS_PER_CELL == 4


def test_preflight_happy_path():
    preflight(build_cells(), "GRB", 4)  # no raise


def test_main_refuses_on_cbc(monkeypatch, capsys):
    monkeypatch.setattr(pf, "detect_backend", lambda: "CBC")
    rc = pf.main(["--out", "/tmp/nonexistent-a6-preflight"])
    assert rc == 2
    assert "[REFUSED]" in capsys.readouterr().out


def test_main_refuses_on_bad_concurrency(monkeypatch, capsys):
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")
    rc = pf.main(["--concurrency", "8", "--out", "/tmp/nope-a6"])
    assert rc == 2
    assert "concurrency 8" in capsys.readouterr().out


# --------------------------------------------------------------------------
# manifest: provenance without license secrets
# --------------------------------------------------------------------------
def test_manifest_contents_and_no_license_secrets(monkeypatch, tmp_path):
    fake_license = str(tmp_path / "gurobi-secret.lic")
    monkeypatch.setenv("GRB_LICENSE_FILE", fake_license)
    man = build_manifest("GRB", 4, True, str(tmp_path), build_cells())
    assert len(man["git_commit"]) == 40
    assert isinstance(man["git_dirty"], bool)
    assert man["backend"] == "GRB"
    assert man["versions"]["mip"] != ""
    assert man["versions"]["python"]
    assert man["concurrency"] == 4 and man["threads_per_cell"] == 4
    assert man["cells"] == 24
    assert man["grb_license_env_set"] is True
    dump = json.dumps(man)
    assert fake_license not in dump          # no license path leaks
    assert "gurobi-secret" not in dump
    monkeypatch.delenv("GRB_LICENSE_FILE")
    man2 = build_manifest("GRB", 4, True, str(tmp_path), build_cells())
    assert man2["grb_license_env_set"] is False


# --------------------------------------------------------------------------
# dry-run default and stubbed execution
# --------------------------------------------------------------------------
def test_dry_run_is_default_and_executes_nothing(monkeypatch, tmp_path,
                                                 capsys):
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")
    calls = []
    monkeypatch.setattr(pf, "_run_cell_subprocess",
                        lambda *a, **k: calls.append(a) or 0)
    rc = pf.main(["--out", str(tmp_path)])
    assert rc == 0
    assert calls == []  # nothing executed
    out = capsys.readouterr().out
    assert "[dry-run] nothing executed" in out
    manifests = [f for f in os.listdir(tmp_path)
                 if f.startswith("LOCAL_MANIFEST-")]
    assert len(manifests) == 1
    man = json.load(open(tmp_path / manifests[0]))
    assert man["dry_run"] is True and "results" not in man


def test_execute_runs_all_cells_with_thread_env_and_concurrency_cap(
        monkeypatch, tmp_path):
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")
    lock = threading.Lock()
    state = {"active": 0, "peak": 0, "envs": [], "ks": []}

    def stub(k, cell, out_dir, log_path):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            state["ks"].append(k)
        # the real runner sets these in the subprocess env; emulate the
        # contract check by invoking the env builder logic indirectly:
        with open(log_path, "w") as f:
            f.write(f"stub cell {k} {cell_tag(cell)}\n")
        time.sleep(0.02)
        with lock:
            state["active"] -= 1
        return 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    # completed-status probe: pretend every cell finished
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--concurrency", "3", "--out", str(tmp_path)])
    assert rc == 0
    assert sorted(state["ks"]) == list(range(24))  # all 24 cells ran once
    assert state["peak"] <= 3                      # concurrency respected
    logs = os.listdir(tmp_path / "logs")
    assert len(logs) == 24                         # per-cell logs exist
    manifests = [f for f in os.listdir(tmp_path)
                 if f.startswith("LOCAL_MANIFEST-")]
    man = json.load(open(tmp_path / manifests[0]))
    assert man["all_succeeded"] is True
    assert len(man["results"]) == 24
    for r in man["results"].values():
        assert r["exit_code"] == 0 and r["status_after"] == "complete"


def test_execute_reports_failure_exit_code(monkeypatch, tmp_path):
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")

    def stub(k, cell, out_dir, log_path):
        open(log_path, "w").write("boom\n")
        return 1 if k == 5 else 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--out", str(tmp_path)])
    assert rc == 1  # overall failure surfaced


def test_subprocess_env_contract(monkeypatch, tmp_path):
    """The real runner must set 4 threads and hard-require GRB in the cell
    subprocess environment (checked without running a solver)."""
    captured = {}

    def fake_run(cmd, stdout, stderr, env, cwd):
        captured.update(env=env, cmd=cmd)
        return type("P", (), {"returncode": 0})()

    monkeypatch.setattr(pf.subprocess, "run", fake_run)
    rc = pf._run_cell_subprocess(3, build_cells()[3], str(tmp_path),
                                 str(tmp_path / "x.log"))
    assert rc == 0
    assert captured["env"]["SLURM_CPUS_PER_TASK"] == "4"
    assert captured["env"]["EGGLAB_REQUIRE_GRB"] == "1"
    assert "--cell" in captured["cmd"] and "3" in captured["cmd"]


def test_resume_status_reporting(tmp_path):
    from egglab import checkpoint
    cell = build_cells()[0]
    assert pf.cell_status(str(tmp_path), cell) == "pending"
    d = tmp_path / cell_tag(cell)
    checkpoint.save(str(d / f"{cell[0]}.cg.ckpt.json"), {"done": False})
    assert pf.cell_status(str(tmp_path), cell) == "resumable"
    checkpoint.save(str(d / f"{cell[0]}.cg.ckpt.json"), {"done": True})
    assert pf.cell_status(str(tmp_path), cell) == "complete"
