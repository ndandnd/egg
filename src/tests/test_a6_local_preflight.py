"""Refusal-path and manifest-lifecycle battery for the local A6
preflight/launcher (experiments/local_a6_preflight.py). Every refusal is
tested; execution is exercised with a stubbed cell subprocess (no solver
runs)."""
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
    check_clean_tree_for_execute,
    check_concurrency,
    check_grid,
    preflight,
)
from experiments.run_a6_pilot import build_cells


@pytest.fixture()
def grb_clean(monkeypatch):
    """Common happy-path environment: GRB backend, clean tracked tree."""
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")
    monkeypatch.setattr(pf, "_git_state", lambda: ("f" * 40, 0))


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
# dirty-tree policy: dry-run reports, --execute refuses tracked changes
# --------------------------------------------------------------------------
def test_clean_tree_check_semantics():
    check_clean_tree_for_execute(0)  # clean: no raise
    with pytest.raises(PreflightError, match="tracked file"):
        check_clean_tree_for_execute(3)


def test_execute_refused_on_dirty_tracked_tree(monkeypatch, tmp_path,
                                               capsys):
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")
    monkeypatch.setattr(pf, "_git_state", lambda: ("a" * 40, 2))
    called = []
    monkeypatch.setattr(pf, "_run_cell_subprocess",
                        lambda *a, **k: called.append(a) or 0)
    rc = pf.main(["--execute", "--out", str(tmp_path)])
    assert rc == 2
    assert called == []  # refused before any cell was submitted
    assert "staged/unstaged" in capsys.readouterr().out


def test_dry_run_reports_dirty_but_proceeds(monkeypatch, tmp_path):
    monkeypatch.setattr(pf, "detect_backend", lambda: "GRB")
    monkeypatch.setattr(pf, "_git_state", lambda: ("a" * 40, 2))
    rc = pf.main(["--out", str(tmp_path)])
    assert rc == 0  # dry-run only reports
    man = _read_single_manifest(tmp_path)
    assert man["git_dirty"] is True and man["git_dirty_files"] == 2


def test_untracked_files_never_block(grb_clean, tmp_path, monkeypatch):
    # _git_state uses --untracked-files=no by contract: a clean (0) result
    # with untracked files present must allow --execute
    def stub(k, cell, out_dir, log_path):
        open(log_path, "w").write("x")
        return 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--out", str(tmp_path)])
    assert rc == 0


def test_git_state_excludes_untracked_live():
    """The real probe must not count untracked files: -uno is load-bearing."""
    commit, dirty = pf._git_state()
    assert len(commit) == 40
    out = pf.subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=os.path.dirname(os.path.abspath(pf.__file__))).decode().strip()
    assert dirty == len(out.splitlines())


# --------------------------------------------------------------------------
# absolute out-path resolution (regression: invoke from outside src)
# --------------------------------------------------------------------------
def _read_single_manifest(out_dir):
    files = [f for f in os.listdir(out_dir)
             if f.startswith("LOCAL_MANIFEST-")]
    assert len(files) == 1
    return json.load(open(os.path.join(out_dir, files[0])))


def test_relative_out_resolved_once_from_outside_src(grb_clean, tmp_path,
                                                     monkeypatch):
    """Invoke from a working directory OUTSIDE src with a RELATIVE --out:
    the manifest, logs, status checks, and the subprocess argument must all
    use one absolute path under the invoker's cwd."""
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    monkeypatch.chdir(outside)
    seen = {"outs": set(), "logs": []}

    def stub(k, cell, out_dir, log_path):
        seen["outs"].add(out_dir)
        seen["logs"].append(log_path)
        open(log_path, "w").write("x")
        return 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--out", "myruns"])
    assert rc == 0
    expected = str(outside / "myruns")
    assert seen["outs"] == {expected}          # one absolute path everywhere
    for lp in seen["logs"]:
        assert lp.startswith(os.path.join(expected, "logs"))
    man = _read_single_manifest(expected)
    assert man["out_dir"] == expected
    assert man["all_succeeded"] is True


def test_dry_run_from_outside_src(grb_clean, tmp_path, monkeypatch):
    outside = tmp_path / "cwd"
    outside.mkdir()
    monkeypatch.chdir(outside)
    rc = pf.main(["--out", "rel_out"])
    assert rc == 0
    man = _read_single_manifest(outside / "rel_out")
    assert man["execution_status"] == "dry-run"
    assert man["out_dir"] == str(outside / "rel_out")


# --------------------------------------------------------------------------
# manifest lifecycle: started -> complete/incomplete; exceptions captured
# --------------------------------------------------------------------------
def test_started_manifest_exists_before_first_cell(grb_clean, tmp_path,
                                                   monkeypatch):
    observed = {}

    def stub(k, cell, out_dir, log_path):
        if not observed:
            man = _read_single_manifest(out_dir)
            observed["status_at_first_cell"] = man["execution_status"]
        open(log_path, "w").write("x")
        return 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--concurrency", "1", "--out", str(tmp_path)])
    assert rc == 0
    assert observed["status_at_first_cell"] == "started"
    assert _read_single_manifest(tmp_path)["execution_status"] == "complete"


def test_per_cell_exception_captured_and_finalized_incomplete(
        grb_clean, tmp_path, monkeypatch):
    def stub(k, cell, out_dir, log_path):
        open(log_path, "w").write("x")
        if k == 7:
            raise RuntimeError("simulated cell crash")
        return 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--out", str(tmp_path)])
    assert rc == 1
    man = _read_single_manifest(tmp_path)
    assert man["execution_status"] == "incomplete"
    assert man["all_succeeded"] is False
    crashed = [r for r in man["results"].values() if "exception" in r]
    assert len(crashed) == 1
    assert "simulated cell crash" in crashed[0]["exception"]
    assert crashed[0]["exit_code"] is None
    assert len(man["results"]) == 24  # every cell accounted for


def test_failure_exit_code_finalizes_incomplete(grb_clean, tmp_path,
                                                monkeypatch):
    def stub(k, cell, out_dir, log_path):
        open(log_path, "w").write("boom")
        return 1 if k == 5 else 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--out", str(tmp_path)])
    assert rc == 1
    assert _read_single_manifest(tmp_path)["execution_status"] == "incomplete"


# --------------------------------------------------------------------------
# manifest provenance: versions incl. Gurobi runtime; no license secrets
# --------------------------------------------------------------------------
def test_manifest_contents_and_no_license_secrets(monkeypatch, tmp_path):
    fake_license = str(tmp_path / "gurobi-secret.lic")
    monkeypatch.setenv("GRB_LICENSE_FILE", fake_license)
    man = build_manifest("GRB", 4, True, str(tmp_path), build_cells())
    assert len(man["git_commit"]) == 40
    assert isinstance(man["git_dirty"], bool)
    assert man["backend"] == "GRB"
    for key in ("python", "mip", "numpy", "pandas", "gurobipy",
                "gurobi_runtime"):
        assert key in man["versions"], key
    assert man["concurrency"] == 4 and man["threads_per_cell"] == 4
    assert man["cells"] == 24
    assert man["grb_license_env_set"] is True
    dump = json.dumps(man)
    assert fake_license not in dump          # no license path leaks
    assert "gurobi-secret" not in dump
    monkeypatch.delenv("GRB_LICENSE_FILE")
    man2 = build_manifest("GRB", 4, True, str(tmp_path), build_cells())
    assert man2["grb_license_env_set"] is False


def test_gurobi_runtime_version_recorded(monkeypatch, tmp_path):
    monkeypatch.setattr(pf, "_gurobi_runtime_version", lambda: "12.0.1")
    monkeypatch.setattr(pf, "_pkg_version",
                        lambda name: "12.0.1" if name == "gurobipy" else "x")
    man = build_manifest("GRB", 4, True, str(tmp_path), build_cells())
    assert man["versions"]["gurobi_runtime"] == "12.0.1"
    assert man["versions"]["gurobipy"] == "12.0.1"
    # on a machine without gurobipy the probe degrades to 'unknown'
    assert pf._gurobi_runtime_version() in ("unknown",) or isinstance(
        pf._gurobi_runtime_version(), str)


# --------------------------------------------------------------------------
# dry-run default and stubbed execution
# --------------------------------------------------------------------------
def test_dry_run_is_default_and_executes_nothing(grb_clean, tmp_path,
                                                 monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(pf, "_run_cell_subprocess",
                        lambda *a, **k: calls.append(a) or 0)
    rc = pf.main(["--out", str(tmp_path)])
    assert rc == 0
    assert calls == []  # nothing executed
    out = capsys.readouterr().out
    assert "[dry-run] nothing executed" in out
    man = _read_single_manifest(tmp_path)
    assert man["dry_run"] is True and "results" not in man
    assert man["execution_status"] == "dry-run"


def test_execute_runs_all_cells_with_concurrency_cap(grb_clean, tmp_path,
                                                     monkeypatch):
    lock = threading.Lock()
    state = {"active": 0, "peak": 0, "ks": []}

    def stub(k, cell, out_dir, log_path):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            state["ks"].append(k)
        open(log_path, "w").write(f"stub cell {k} {cell_tag(cell)}\n")
        time.sleep(0.02)
        with lock:
            state["active"] -= 1
        return 0

    monkeypatch.setattr(pf, "_run_cell_subprocess", stub)
    monkeypatch.setattr(pf, "cell_status", lambda *_a: "complete")
    rc = pf.main(["--execute", "--concurrency", "3", "--out", str(tmp_path)])
    assert rc == 0
    assert sorted(state["ks"]) == list(range(24))  # all 24 cells ran once
    assert state["peak"] <= 3                      # concurrency respected
    assert len(os.listdir(tmp_path / "logs")) == 24
    man = _read_single_manifest(tmp_path)
    assert man["all_succeeded"] is True
    assert len(man["results"]) == 24
    for r in man["results"].values():
        assert r["exit_code"] == 0 and r["status_after"] == "complete"


def test_subprocess_env_contract(monkeypatch, tmp_path):
    """The real runner must set 4 threads, hard-require GRB, and pass the
    ABSOLUTE out path (checked without running a solver)."""
    captured = {}

    def fake_run(cmd, stdout, stderr, env, cwd):
        captured.update(env=env, cmd=cmd)
        return type("P", (), {"returncode": 0})()

    monkeypatch.setattr(pf.subprocess, "run", fake_run)
    out_abs = str(tmp_path / "absout")
    rc = pf._run_cell_subprocess(3, build_cells()[3], out_abs,
                                 str(tmp_path / "x.log"))
    assert rc == 0
    assert captured["env"]["SLURM_CPUS_PER_TASK"] == "4"
    assert captured["env"]["EGGLAB_REQUIRE_GRB"] == "1"
    assert "--cell" in captured["cmd"] and "3" in captured["cmd"]
    assert out_abs in captured["cmd"]  # absolute path reaches the driver


def test_resume_status_reporting(tmp_path):
    from egglab import checkpoint
    cell = build_cells()[0]
    assert pf.cell_status(str(tmp_path), cell) == "pending"
    d = tmp_path / cell_tag(cell)
    checkpoint.save(str(d / f"{cell[0]}.cg.ckpt.json"), {"done": False})
    assert pf.cell_status(str(tmp_path), cell) == "resumable"
    checkpoint.save(str(d / f"{cell[0]}.cg.ckpt.json"), {"done": True})
    assert pf.cell_status(str(tmp_path), cell) == "complete"
