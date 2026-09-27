"""Eight fixed compact-oracle hull cells; explicit dependency, exclusive attempts."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow_hull as compact
from experiments import native_hull_qualification as indexed
from experiments import native_recharge_qualification as nq

PROTOCOL = "native-pathflow-hull-qualification-20260927-v3-orphan-projection"
ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "result/native_pathflow_hull/20260927-attempt2"
SOURCES = tuple(dict.fromkeys(indexed.SOURCES + (
    "src/egglab/native_hull.py", "src/egglab/native_pathflow.py",
    "src/egglab/native_pathflow_hull.py",
    "src/experiments/native_pathflow_hull_qualification.py",
    "src/tests/test_native_pathflow_hull_policy.py",
    "src/tests/test_native_pathflow_hull.py",
    "src/tests/test_native_pathflow_energy_band.py",
    "doc/NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md",
    "doc/NATIVE_PATHFLOW_HULL_QUALIFICATION_PROTOCOL_20260927.md",
    "doc/NATIVE_PATHFLOW_HULL_V3_QUALIFICATION_PROTOCOL_20260927.md",
    "doc/NATIVE_PATHFLOW_HULL_INTEGRATION_DESIGN_20260927.md",
    "doc/NATIVE_PATHFLOW_HULL_V3_POLICY_INTEGRATION_20260927.md",
    "doc/NATIVE_PATHFLOW_HULL_V3_IMPLEMENTATION_REVIEW_20260927.md")))
WORKER_SECONDS = indexed.WORKER_SECONDS
OUTER_SECONDS = indexed.OUTER_SECONDS
TARGET_TOL = indexed.TARGET_TOL
controls = indexed.controls
assess = indexed.assess
read_evidence = indexed.read_evidence
accounting = indexed.accounting
admitted_predecessor = indexed.admitted_predecessor


def source_hashes():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def manifest(cell, budget):
    return {**cell, "case":asdict(cell["case"]), "market":asdict(cell["market"]),
        "physical_identity":cell["case"].identity(), "market_identity":cell["market"].identity(),
        "pricing_oracle":compact.ORACLE_ID, "extraction_policy":compact.EXTRACTION_POLICY,
        "state_identity":compact.state_identity(cell["case"],cell["market"],cell["arm"],cell["state_index"],budget)}


def worker(cell_id, directory, budget, frozen):
    folder = Path(directory)
    cell = next(c for c in controls() if c["id"] == cell_id)
    def record(event):
        with (folder/"events.jsonl").open("a") as f:
            f.write(json.dumps(event, sort_keys=True, allow_nan=False)+"\n")
            f.flush()
            os.fsync(f.fileno())
    start = time.perf_counter()
    try:
        if (source_hashes() != frozen["source_hashes"] or frozen.get("protocol") != PROTOCOL
                or frozen.get("pricing_oracle") != compact.ORACLE_ID
                or frozen.get("extraction_policy") != compact.EXTRACTION_POLICY):
            raise ValueError("Hull source changed after source freeze")
        previous = expected = None
        if cell["predecessor"]:
            package, issues = admitted_predecessor(folder.parent/cell["predecessor"], cell["predecessor"])
            if not package:
                result = {"schema": nh.SCHEMA, "status": "blocked_by_predecessor", "predecessor": cell["predecessor"]}
                record({"event": "dependency_blocked", "result": result, "issues": issues})
                nq._json(folder/"result.json", {"result": result, "assessment": {"pass": False}, "elapsed_s": time.perf_counter()-start})
                return 3
            previous = package["result"]
            expected = next(c["state_identity"] for c in frozen["controls"] if c["id"] == cell["predecessor"])
        result = compact.certify(cell["case"], cell["market"], budget, arm=cell["arm"], state_index=cell["state_index"],
                            previous=previous, expected_previous=expected, record=record)
        if (result.get("extraction_policy") != compact.EXTRACTION_POLICY
                or any(column.get("extraction_policy") != compact.EXTRACTION_POLICY
                       for column in result.get("columns", []))):
            raise ValueError("Compact hull result/column extraction policy mismatch")
        assessment = assess(cell, result)
        nq._json(folder/"result.json", {"result": result, "assessment": assessment,
                "elapsed_s": time.perf_counter()-start, "environment": nq.environment()})
        return 0 if assessment["pass"] else 1
    except Exception as exc:
        nq._json(folder/"exception.json", {"type": type(exc).__name__, "message": str(exc),
                 "traceback": traceback.format_exc(), "elapsed_s": time.perf_counter()-start})
        traceback.print_exc()
        return 2


def controller(output, freeze_label, backend="CBC"):
    out = Path(output)
    if not freeze_label.strip() or not out.is_dir():
        raise ValueError("Exclusive attempt directory and source freeze required")
    budget = nh.Budget(backend=backend)
    nh.validate_budget(budget)
    cells = controls()
    hashes = source_hashes()
    for c in cells:
        nh.nr.validate_case(c["case"])
        nh.validate_market(c["case"], c["market"])
    frozen = {"protocol": PROTOCOL, "pricing_oracle": compact.ORACLE_ID,
              "extraction_policy": compact.EXTRACTION_POLICY,
              "source_hashes": hashes, "freeze_label": freeze_label,
              "budget": asdict(budget), "environment": nq.environment(), "worker_seconds": WORKER_SECONDS,
              "outer_seconds": OUTER_SECONDS, "controls": [manifest(c, budget) for c in cells]}
    nq._json(out/"frozen.json", frozen)
    for c in cells:
        folder = out/c["id"]
        folder.mkdir()
        nq._json(folder/"input.json", {"control": manifest(c, budget), "source_hashes": hashes, "budget": asdict(budget)})
    rows, started = [], time.perf_counter()
    for cell in cells:
        folder = out/cell["id"]
        cmd = [sys.executable, "-m", "experiments.native_pathflow_hull_qualification", "--worker", cell["id"],
               "--output", str(folder.resolve()), "--frozen", str((out/"frozen.json").resolve())]
        nq._json(folder/"launch.json", {"command": cmd, "worker_cap_s": WORKER_SECONDS})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT/"src")+os.pathsep+env.get("PYTHONPATH", "")
        timeout, rc, launch = False, None, time.perf_counter()
        with (folder/"stdout.txt").open("x") as stdout, (folder/"stderr.txt").open("x") as stderr:
            try:
                rc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    timeout=WORKER_SECONDS, check=False).returncode
            except subprocess.TimeoutExpired:
                timeout = True
            except Exception as exc:
                nq._json(folder/"launch_exception.json", {"type": type(exc).__name__, "message": str(exc)})
        events, package, issues = read_evidence(folder)
        try:
            counts = accounting(events)
        except (ValueError, TypeError, KeyError) as exc:
            issues.append({"file": "events.jsonl", "message": "accounting: "+str(exc)})
            counts = {"native_accounting_complete": False, "native_starts": None, "native_returns": None,
                      "polish_accounting_complete": False}
        row = {"cell": cell["id"], "returncode": rc, "timeout": timeout,
               "elapsed_s": time.perf_counter()-launch, "evidence_issues": issues, **counts,
               "status": package["result"]["status"] if package else "timeout" if timeout else "exception",
               "pass": bool(rc == 0 and not timeout and package and package["assessment"]["pass"] and not issues
                            and counts["native_accounting_complete"] and counts["polish_accounting_complete"]
                            and counts["native_starts"] >= 1)}
        nq._json(folder/"receipt.json", row)
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    summary = {"protocol": PROTOCOL, "cells": rows, "elapsed_s": time.perf_counter()-started,
               "all_pass": all(r["pass"] for r in rows), "source_hashes_unchanged": source_hashes() == hashes}
    nq._json(out/"summary.json", summary)
    return 0 if summary["all_pass"] and summary["source_hashes_unchanged"] else 1


def supervise(output, freeze_label, backend="CBC"):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    cmd = [sys.executable, "-m", "experiments.native_pathflow_hull_qualification", "--controller", "--output", str(out.resolve()),
           "--freeze-label", freeze_label, "--backend", backend]
    nq._json(out/"supervisor_launch.json", {"command": cmd, "outer_cap_s": OUTER_SECONDS, "kill_grace_s": 10})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT/"src")+os.pathsep+env.get("PYTHONPATH", "")
    start, timed_out = time.perf_counter(), False
    with (out/"controller_stdout.txt").open("x") as stdout, (out/"controller_stderr.txt").open("x") as stderr:
        process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            rc = process.wait(timeout=OUTER_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                rc = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                rc = None
            # The controller may exit before a native worker; kill any surviving
            # group member even when waiting for the controller already returned.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if rc is None:
                rc = process.wait()
    receipt = {"protocol": PROTOCOL, "returncode": rc, "outer_timeout": timed_out,
               "elapsed_s": time.perf_counter()-start}
    nq._json(out/"supervisor_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)
    return 1 if timed_out else rc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--freeze-label")
    parser.add_argument("--backend", choices=("CBC", "GRB"), default="CBC")
    parser.add_argument("--controller", action="store_true")
    parser.add_argument("--worker")
    parser.add_argument("--frozen")
    args = parser.parse_args(argv)
    if args.worker:
        frozen = json.loads(Path(args.frozen).read_text())
        return worker(args.worker, args.output, nh.Budget(**frozen["budget"]), frozen)
    if Path(args.output).resolve() != ATTEMPT.resolve():
        parser.error("Only the exclusive prospective attempt2 path is admitted")
    if not args.freeze_label:
        parser.error("--freeze-label is required before optimizer execution")
    return controller(args.output, args.freeze_label, args.backend) if args.controller else supervise(args.output, args.freeze_label, args.backend)


if __name__ == "__main__":
    raise SystemExit(main())
