#!/usr/bin/env python3
"""Local A6 pilot preflight + launcher (no cluster; no holdout anywhere).

Runs the EXACT 24-cell burned-seed A6 pilot (experiments/run_a6_pilot.py,
untouched) on a local machine with Gurobi. Defaults to DRY-RUN: nothing
executes without --execute.

Hard refusals (each tested):
- solver backend is not a usable GRB (CBC is refused outright — local A6
  evidence must be backend-comparable to the cluster);
- the pilot grid is not exactly 24 cells (12 a6_a4 + 12 a6_a3);
- any holdout-range seed (>= 16) appears in the grid;
- requested concurrency is outside 1..4;
- --execute with staged or unstaged TRACKED changes in the analysis repo
  (untracked files never block; dry-run only REPORTS dirtiness so the
  manifest cannot misattribute results to a commit).

Path discipline: --out is resolved to ONE absolute path at startup and
that single path is used for every manifest, status check, log, and cell
subprocess — invoking from any working directory is safe.

Execution: at most MAX_CONCURRENCY = 4 concurrent cells, each cell run as
a subprocess with SLURM_CPUS_PER_TASK = 4 (the solver honors it for
threads) and EGGLAB_REQUIRE_GRB = 1 (a mid-run CBC fallback hard-fails).
A "started" execution manifest is written ATOMICALLY before any cell is
submitted; per-cell exceptions are captured into the results; the
manifest is always finalized as complete or incomplete. Per-cell logs
under <out>/logs/. Resume is inherited from the existing transactional
checkpoints.

The manifest records commit, dirty status, backend, package versions
(python, mip, numpy, pandas, gurobipy, and the Gurobi RUNTIME version),
host, and settings — and deliberately NO license material (only a
boolean for whether a license env var is set; never its value/contents).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import platform
import socket
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab import checkpoint
from egglab.solver import detect_backend
from experiments.run_a6_pilot import build_cells

MAX_CONCURRENCY = 4
THREADS_PER_CELL = 4
EXPECTED_CELLS = 24
BURNED_SEEDS = (0, 11, 15)
HOLDOUT_SEED_MIN = 16


class PreflightError(RuntimeError):
    pass


def cell_tag(cell) -> str:
    m, s, n, b = cell
    return f"{m}_s{s}_n{n}_b{b:g}"


# ---------------------------------------------------------------------------
# refusal checks (pure; every path unit-tested)
# ---------------------------------------------------------------------------
def check_backend(backend_name: str) -> None:
    if backend_name != "GRB":
        raise PreflightError(
            f"solver backend is {backend_name!r}; a usable GRB backend is "
            "required and CBC is refused — local A6 evidence must be "
            "backend-comparable to the cluster")


def check_grid(cells) -> None:
    if len(cells) != EXPECTED_CELLS:
        raise PreflightError(
            f"pilot grid has {len(cells)} cells; expected exactly "
            f"{EXPECTED_CELLS}")
    if len(set(cells)) != EXPECTED_CELLS:
        raise PreflightError("pilot grid contains duplicate cells")
    for m in ("a6_a4", "a6_a3"):
        got = sum(1 for c in cells if c[0] == m)
        if got != EXPECTED_CELLS // 2:
            raise PreflightError(
                f"pilot grid has {got} {m} cells; expected "
                f"{EXPECTED_CELLS // 2}")
    for (m, s, n, b) in cells:
        if s >= HOLDOUT_SEED_MIN:
            raise PreflightError(
                f"holdout-range seed {s} (>= {HOLDOUT_SEED_MIN}) in the "
                f"pilot grid ({m}, n={n}, b={b}); refusing")
        if s not in BURNED_SEEDS:
            raise PreflightError(
                f"non-burned seed {s} in the pilot grid; refusing")


def check_concurrency(concurrency: int) -> None:
    if not (1 <= concurrency <= MAX_CONCURRENCY):
        raise PreflightError(
            f"concurrency {concurrency} outside 1..{MAX_CONCURRENCY}; "
            "refusing (local machines get at most "
            f"{MAX_CONCURRENCY} x {THREADS_PER_CELL} threads)")


def check_clean_tree_for_execute(dirty_files: int) -> None:
    """Execution must be attributable to one commit: staged or unstaged
    TRACKED changes refuse --execute (untracked files never block)."""
    if dirty_files:
        raise PreflightError(
            f"{dirty_files} tracked file(s) with staged/unstaged changes; "
            "--execute requires a clean tracked tree so the manifest "
            "commit is truthful (dry-run only reports dirtiness; "
            "untracked files do not block)")


def preflight(cells, backend_name: str, concurrency: int) -> None:
    check_backend(backend_name)
    check_grid(cells)
    check_concurrency(concurrency)


# ---------------------------------------------------------------------------
# provenance (no license secrets)
# ---------------------------------------------------------------------------
def _git_state() -> tuple:
    """(full commit hash, number of tracked files with staged or unstaged
    changes). Untracked files are excluded by -uno."""
    repo = os.path.dirname(os.path.abspath(__file__))
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo).decode().strip()
    return commit, len(dirty.splitlines())


def _pkg_version(name: str) -> str:
    try:
        import importlib.metadata as md

        return md.version(name)
    except Exception:
        return "unknown"


def _gurobi_runtime_version() -> str:
    """The Gurobi RUNTIME (linked library) version via gurobipy, without
    touching any license material; 'unknown' when gurobipy is absent."""
    try:
        import gurobipy

        return ".".join(str(x) for x in gurobipy.gurobi.version())
    except Exception:
        return "unknown"


def build_manifest(backend_name: str, concurrency: int, dry_run: bool,
                   out_dir: str, cells) -> dict:
    commit, dirty_files = _git_state()
    return {
        "schema": "a6-local-preflight-v2",
        "stamp": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "git_commit": commit,
        "git_dirty": bool(dirty_files),
        "git_dirty_files": dirty_files,
        "backend": backend_name,
        "versions": {
            "python": platform.python_version(),
            "mip": _pkg_version("mip"),
            "numpy": _pkg_version("numpy"),
            "pandas": _pkg_version("pandas"),
            "gurobipy": _pkg_version("gurobipy"),
            "gurobi_runtime": _gurobi_runtime_version(),
        },
        "host": socket.gethostname(),
        "concurrency": concurrency,
        "threads_per_cell": THREADS_PER_CELL,
        "cells": len(cells),
        "dry_run": dry_run,
        "execution_status": "dry-run" if dry_run else "started",
        "out_dir": out_dir,
        # deliberately NO license paths or contents — presence only:
        "grb_license_env_set": bool(os.environ.get("GRB_LICENSE_FILE")),
    }


def write_manifest_atomic(path: str, manifest: dict) -> None:
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# ---------------------------------------------------------------------------
# execution (resume through existing checkpoints)
# ---------------------------------------------------------------------------
def cell_status(out_dir: str, cell) -> str:
    ck = checkpoint.load(os.path.join(
        out_dir, cell_tag(cell), f"{cell[0]}.cg.ckpt.json"))
    if ck is None:
        return "pending"
    if ck.get("done"):
        return "complete"
    return "resumable"


def _run_cell_subprocess(k: int, cell, out_dir: str, log_path: str) -> int:
    """One pilot cell as a subprocess (monkeypatchable in tests).
    `out_dir` is already absolute, so the subprocess cwd cannot change
    where results land."""
    env = dict(os.environ)
    env["SLURM_CPUS_PER_TASK"] = str(THREADS_PER_CELL)
    env["EGGLAB_REQUIRE_GRB"] = "1"
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "run_a6_pilot.py")
    with open(log_path, "w") as log:
        proc = subprocess.run(
            [sys.executable, script, "--cell", str(k), "--out", out_dir],
            stdout=log, stderr=subprocess.STDOUT, env=env,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return proc.returncode


def run_pilot(out_dir: str, concurrency: int, manifest: dict,
              manifest_path: str) -> dict:
    """Submit cells with the started manifest already on disk; capture
    per-cell exceptions; ALWAYS finalize the manifest."""
    cells = build_cells()
    logs_dir = os.path.join(out_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    results = {}

    def job(k, cell):
        tag = cell_tag(cell)
        log_path = os.path.join(logs_dir, f"cell_{k:02d}_{tag}.log")
        try:
            rc = _run_cell_subprocess(k, cell, out_dir, log_path)
            return tag, {"cell_index": k, "exit_code": rc,
                         "log": os.path.relpath(log_path, out_dir),
                         "status_after": cell_status(out_dir, cell)}
        except Exception as exc:  # captured, never lost
            return tag, {"cell_index": k, "exit_code": None,
                         "exception": f"{type(exc).__name__}: {exc}",
                         "log": os.path.relpath(log_path, out_dir),
                         "status_after": cell_status(out_dir, cell)}

    manifest = dict(manifest)
    try:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=concurrency) as pool:
            futures = [pool.submit(job, k, cell)
                       for k, cell in enumerate(cells)]
            for fut in concurrent.futures.as_completed(futures):
                tag, res = fut.result()
                results[tag] = res
    finally:
        manifest["results"] = {t: results[t] for t in sorted(results)}
        ok = (len(results) == len(cells) and all(
            r["exit_code"] == 0 and "exception" not in r
            and r["status_after"] == "complete" for r in results.values()))
        manifest["all_succeeded"] = ok
        manifest["execution_status"] = "complete" if ok else "incomplete"
        write_manifest_atomic(manifest_path, manifest)
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true",
                    help="actually run the 24 cells (default: dry-run)")
    ap.add_argument("--concurrency", type=int, default=MAX_CONCURRENCY)
    ap.add_argument("--out", default="runs/a6_pilot")
    args = ap.parse_args(argv)

    # ONE absolute path for everything that follows (manifests, status
    # checks, logs, subprocess arguments)
    out_dir = os.path.abspath(args.out)

    cells = build_cells()
    backend_name = detect_backend()
    try:
        preflight(cells, backend_name, args.concurrency)
        if args.execute:
            _commit, dirty_files = _git_state()
            check_clean_tree_for_execute(dirty_files)
    except PreflightError as exc:
        print(f"[REFUSED] {exc}")
        return 2

    manifest = build_manifest(backend_name, args.concurrency,
                              not args.execute, out_dir, cells)
    manifest_path = os.path.join(
        out_dir, f"LOCAL_MANIFEST-{manifest['stamp']}.json")

    print(f"[preflight OK] backend={backend_name}; {len(cells)} cells; "
          f"concurrency={args.concurrency} x {THREADS_PER_CELL} threads; "
          f"out={out_dir}")
    for k, cell in enumerate(cells):
        print(f"  {k:2d} {cell_tag(cell):24s} {cell_status(out_dir, cell)}")

    if not args.execute:
        write_manifest_atomic(manifest_path, manifest)
        print(f"[dry-run] nothing executed; manifest: {manifest_path}. "
              "Pass --execute to run.")
        return 0

    # atomically publish the STARTED manifest before any cell is submitted
    write_manifest_atomic(manifest_path, manifest)
    manifest = run_pilot(out_dir, args.concurrency, manifest, manifest_path)
    ok = manifest["all_succeeded"]
    print(f"[{'done' if ok else 'INCOMPLETE'}] manifest: {manifest_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
