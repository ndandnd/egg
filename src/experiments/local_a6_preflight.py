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
- requested concurrency is outside 1..4.

Execution: at most MAX_CONCURRENCY = 4 concurrent cells, each cell run as
a subprocess with SLURM_CPUS_PER_TASK = 4 (the solver honors it for
threads) and EGGLAB_REQUIRE_GRB = 1 (a mid-run CBC fallback hard-fails).
Per-cell logs under <out>/logs/. Resume is inherited from the existing
transactional checkpoints: rerunning re-invokes every cell and completed
cells return immediately from their done checkpoints; interrupted cells
resume exactly.

The manifest records commit, dirty status, backend, package versions,
host, and settings — and deliberately NO license material (only a boolean
for whether a license env var is set; never its value or contents).
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


def preflight(cells, backend_name: str, concurrency: int) -> None:
    check_backend(backend_name)
    check_grid(cells)
    check_concurrency(concurrency)


# ---------------------------------------------------------------------------
# manifest (no license secrets)
# ---------------------------------------------------------------------------
def _pkg_version(name: str) -> str:
    try:
        import importlib.metadata as md

        return md.version(name)
    except Exception:
        return "unknown"


def build_manifest(backend_name: str, concurrency: int, dry_run: bool,
                   out_dir: str, cells) -> dict:
    repo = os.path.dirname(os.path.abspath(__file__))
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo).decode().strip()
    return {
        "schema": "a6-local-preflight-v1",
        "stamp": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "git_commit": commit,
        "git_dirty": bool(dirty),
        "git_dirty_files": len(dirty.splitlines()),
        "backend": backend_name,
        "versions": {
            "python": platform.python_version(),
            "mip": _pkg_version("mip"),
            "numpy": _pkg_version("numpy"),
            "pandas": _pkg_version("pandas"),
        },
        "host": socket.gethostname(),
        "concurrency": concurrency,
        "threads_per_cell": THREADS_PER_CELL,
        "cells": len(cells),
        "dry_run": dry_run,
        "out_dir": out_dir,
        # deliberately NO license paths or contents — presence only:
        "grb_license_env_set": bool(os.environ.get("GRB_LICENSE_FILE")),
    }


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
    """One pilot cell as a subprocess (monkeypatchable in tests)."""
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


def run_pilot(out_dir: str, concurrency: int, manifest: dict) -> dict:
    cells = build_cells()
    logs_dir = os.path.join(out_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    results = {}

    def job(k, cell):
        tag = cell_tag(cell)
        log_path = os.path.join(logs_dir, f"cell_{k:02d}_{tag}.log")
        rc = _run_cell_subprocess(k, cell, out_dir, log_path)
        return tag, {"cell_index": k, "exit_code": rc,
                     "log": os.path.relpath(log_path, out_dir),
                     "status_after": cell_status(out_dir, cell)}

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrency) as pool:
        futures = [pool.submit(job, k, cell)
                   for k, cell in enumerate(cells)]
        for fut in concurrent.futures.as_completed(futures):
            tag, res = fut.result()
            results[tag] = res

    manifest = dict(manifest)
    manifest["results"] = {t: results[t] for t in sorted(results)}
    manifest["all_succeeded"] = all(
        r["exit_code"] == 0 and r["status_after"] == "complete"
        for r in results.values())
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true",
                    help="actually run the 24 cells (default: dry-run)")
    ap.add_argument("--concurrency", type=int, default=MAX_CONCURRENCY)
    ap.add_argument("--out", default="runs/a6_pilot")
    args = ap.parse_args(argv)

    cells = build_cells()
    backend_name = detect_backend()
    try:
        preflight(cells, backend_name, args.concurrency)
    except PreflightError as exc:
        print(f"[REFUSED] {exc}")
        return 2

    manifest = build_manifest(backend_name, args.concurrency,
                              not args.execute, args.out, cells)
    os.makedirs(args.out, exist_ok=True)
    manifest_path = os.path.join(
        args.out, f"LOCAL_MANIFEST-{manifest['stamp']}.json")

    print(f"[preflight OK] backend={backend_name}; {len(cells)} cells; "
          f"concurrency={args.concurrency} x {THREADS_PER_CELL} threads")
    for k, cell in enumerate(cells):
        print(f"  {k:2d} {cell_tag(cell):24s} {cell_status(args.out, cell)}")

    if not args.execute:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"[dry-run] nothing executed; manifest: {manifest_path}. "
              "Pass --execute to run.")
        return 0

    manifest = run_pilot(args.out, args.concurrency, manifest)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    ok = manifest["all_succeeded"]
    print(f"[{'done' if ok else 'INCOMPLETE'}] manifest: {manifest_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
