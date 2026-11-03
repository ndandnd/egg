"""Prospective half-minute extension gate; exclusive attempt, no import solve.

Retains the fifteen original integer controls and adds four timing controls.
The attempt-preserving controller is copied from the V2 gate; the original
runner and its evidence remain unchanged.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

from egglab import native_recharge as nr

from experiments import native_recharge_qualification as original

PROTOCOL = "native-halfminute-qualification-20260927-v1"
ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("src/egglab/native_recharge.py", "src/experiments/native_recharge_qualification.py",
    "src/experiments/native_halfminute_qualification.py", "src/tests/test_native_recharge.py",
    "src/tests/test_native_halfminute.py", "doc/NATIVE_HALFMINUTE_QUALIFICATION_PROTOCOL_20260927.md")
TARGET_TOL = original.TARGET_TOL
_json = original._json
environment = original.environment
assess = original.assess


def halve_time(case):
    """Equivalent energy/cost problem: half duration, double kW and driving rate."""
    return replace(case,
        trips=tuple(replace(t, start_min=t.start_min/2, end_min=t.end_min/2) for t in case.trips),
        movements=tuple(replace(m, legs=tuple(replace(l, depart_min=l.depart_min/2,
            arrive_min=l.arrive_min/2) for l in m.legs)) for m in case.movements),
        resources=tuple(replace(r, start_min=r.start_min/2, end_min=r.end_min/2,
            per_bus_kw=2*r.per_bus_kw, grid_kw=2*r.grid_kw) for r in case.resources),
        market_edges_min=tuple(t/2 for t in case.market_edges_min),
        terminal_open_min=case.terminal_open_min/2,
        recharge_deadline_min=case.recharge_deadline_min/2,
        deadhead_cost_per_min=2*case.deadhead_cost_per_min)


def tiny_case(power=60):
    trips = (nr.Trip('A',0,0.5,'D','D',0.5),)
    return nr.NativeCase('half_minute_capacity',trips,original._terminal_modes(trips),
        (nr.Resource(0,0.5,0,0,0),nr.Resource(0.5,1,power,power)),
        (0,0.5,1),'D',1,1,0,0.5,1,7)


def coincidence_case():
    trips = (nr.Trip('A',0,0.5,'D','D',1), nr.Trip('B',1.5,2,'D','D',0))
    depot = nr.Movement('depot_AB','depot','A','B',
        (nr.Leg('D','D',0.5,0.5,0),nr.Leg('D','D',1.5,1.5,1)),1)
    return nr.NativeCase('fractional_coincidence',trips,original._terminal_modes(trips)+(depot,),
        (nr.Resource(0,0.5,0,0,0),nr.Resource(0.5,1.5,60,60),
         nr.Resource(1.5,2,0,0,0),nr.Resource(2,2.5,120,120)),
        (0,0.5,1.5,2,2.5),'D',1,1,0,0,2.5,7)


def controls():
    def cell(name,case,target):
        return {'id':name,'case':case,'objective':'pricing','target':target,
                'expected_status':'infeasible' if target is None else 'certified',
                'prices':[1]*(len(case.market_edges_min)-1)}
    return original.controls() + [
        cell('halfminute_multileg',halve_time(original.multileg_case()),36),
        cell('halfminute_capacity',tiny_case(),7.5),
        cell('halfminute_capacity_failure',tiny_case(59),None),
        cell('halfminute_coincidence',coincidence_case(),9),
    ]


def source_hashes():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}


def worker(cell_id, directory, budget, frozen_source):
    out = Path(directory)
    cell = next(c for c in controls() if c["id"] == cell_id)
    def record(data):
        with (out/"events.jsonl").open("a") as f:
            f.write(json.dumps(data, sort_keys=True, allow_nan=False)+"\n")
            f.flush()
            os.fsync(f.fileno())
    start = time.perf_counter()
    try:
        if source_hashes() != frozen_source:
            raise ValueError("Source changed after attempt freeze")
        case = cell["case"]
        if cell["objective"] == "pricing":
            result = nr.solve_pricing(case, cell["prices"], budget, record=record)
        else:
            result = nr.solve_planner(case, cell["a"], cell["b"], budget, record=record)
        _json(out/"result.json", {"cell": cell_id, "elapsed_s": time.perf_counter()-start, "environment": environment(),
              "result": result, "assessment": assess(cell, result)})
        return 0 if assess(cell, result)["pass"] else 1
    except Exception as exc:
        _json(out/"exception.json", {"cell": cell_id, "elapsed_s": time.perf_counter()-start,
              "type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        traceback.print_exc()
        return 2


def read_worker_evidence(directory):
    """Preserve the valid trace prefix when a killed writer leaves partial JSON."""
    folder = Path(directory)
    events, issues, result = [], [], None
    event_file = folder/"events.jsonl"
    if event_file.exists():
        try:
            lines = event_file.read_bytes().splitlines()
        except OSError as exc:
            lines = []
            issues.append({"file": "events.jsonl", "type": type(exc).__name__, "message": str(exc)})
        for index, line in enumerate(lines):
            try:
                event = json.loads(line)
                if (not isinstance(event, dict) or event.get("event") not in
                        ("native_start", "native_status", "native_incumbent", "charge_normalization",
                         "serial_decoding", "objective_reconstruction", "replayed_iteration")
                        or not nr._minute(event.get("round")) or event["round"] < 0):
                    raise ValueError("Malformed native event record")
                if event["event"] == "native_status" and (
                        not isinstance(event.get("stats"), dict)
                        or not nr._finite(event["stats"].get("wall_s"))):
                    raise ValueError("Malformed native status timing record")
                events.append(event)
            except (ValueError, TypeError, UnicodeError) as exc:
                issues.append({"file": "events.jsonl", "line": index+1,
                               "type": type(exc).__name__, "message": str(exc),
                               "valid_prefix_events": len(events)})
                break
    result_file = folder/"result.json"
    if result_file.exists():
        try:
            candidate = json.loads(result_file.read_bytes())
            if (not isinstance(candidate, dict) or not isinstance(candidate.get("assessment"), dict)
                    or not isinstance(candidate["assessment"].get("pass"), bool)
                    or not isinstance(candidate.get("result"), dict)
                    or candidate["result"].get("status") not in
                        ("certified", "bounded", "infeasible", "unresolved")):
                raise ValueError("Malformed worker result record")
            result = candidate
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            issues.append({"file": "result.json", "type": type(exc).__name__, "message": str(exc)})
    return events, result, issues


def qualify(output, freeze_label, backend="CBC"):
    if not freeze_label.strip():
        raise ValueError("The committed source freeze label is required")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    budget = nr.Budget(backend=backend, threads=1, phase_seconds=10, wall_seconds=45, max_rounds=48, epsilon=1e-4)
    nr._check_budget(budget)
    hashes = source_hashes()
    cells = controls()
    for cell in cells:
        nr.validate_case(cell["case"])
    frozen = {"protocol": PROTOCOL, "freeze_label": freeze_label, "source_hashes": hashes,
              "budget": asdict(budget), "environment": environment(), "target_tolerance": TARGET_TOL,
              "controls": [{**c, "case": asdict(c["case"]), "case_identity": c["case"].identity()} for c in cells]}
    _json(out/"frozen.json", frozen)
    rows = []
    start = time.perf_counter()
    for cell in cells:
        folder = out/cell["id"]
        folder.mkdir()
        _json(folder/"input.json", {**cell, "case": asdict(cell["case"]), "budget": asdict(budget),
              "source_hashes": hashes, "case_identity": cell["case"].identity()})
        cmd = [sys.executable, "-m", "experiments.native_halfminute_qualification", "--worker", cell["id"],
               "--output", str(folder.resolve()), "--frozen", str((out/"frozen.json").resolve())]
        _json(folder/"launch.json", {"command": cmd, "hard_timeout_s": budget.wall_seconds+15})
        launched = time.perf_counter()
        timed_out = False
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT/"src")+os.pathsep+env.get("PYTHONPATH", "")
        with (folder/"stdout.txt").open("x") as stdout, (folder/"stderr.txt").open("x") as stderr:
            try:
                run = subprocess.run(cmd, cwd=ROOT, stdout=stdout, stderr=stderr,
                                     timeout=budget.wall_seconds+15, check=False, env=env)
                rc = run.returncode
            except subprocess.TimeoutExpired:
                timed_out, rc = True, None
            except Exception as exc:
                rc = None
                _json(folder/"launch_exception.json", {"type": type(exc).__name__, "message": str(exc),
                      "traceback": traceback.format_exc()})
        events, result, evidence_issues = read_worker_evidence(folder)
        started = sum(e["event"] == "native_start" for e in events)
        returned = sum(e["event"] == "native_status" for e in events)
        row = {"cell": cell["id"], "returncode": rc, "hard_timeout": timed_out,
               "wall_s": time.perf_counter()-launched,
               "native_calls_started": started, "native_calls_returned": returned,
               "native_accounting_complete": not evidence_issues and started == returned,
               "evidence_issues": evidence_issues,
               "native_wall_s": sum(e["stats"]["wall_s"] for e in events if e["event"] == "native_status"),
               "pass": bool(rc == 0 and result and result["assessment"]["pass"]
                            and not evidence_issues and started == returned and started >= 1),
               "status": result["result"]["status"] if result else "timeout" if timed_out else "exception"}
        _json(folder/"receipt.json", row)
        rows.append(row)
        print(json.dumps(row), flush=True)
    summary = {"protocol": PROTOCOL, "elapsed_s": time.perf_counter()-start, "cells": rows,
               "all_pass": all(r["pass"] for r in rows), "source_hashes_unchanged": source_hashes() == hashes}
    _json(out/"summary.json", summary)
    return 0 if summary["all_pass"] and summary["source_hashes_unchanged"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--freeze-label")
    parser.add_argument("--backend", choices=("CBC", "GRB"), default="CBC")
    parser.add_argument("--worker")
    parser.add_argument("--frozen")
    args = parser.parse_args(argv)
    if args.worker:
        frozen = json.loads(Path(args.frozen).read_text())
        return worker(args.worker, args.output, nr.Budget(**frozen["budget"]), frozen["source_hashes"])
    if not args.freeze_label:
        parser.error("--freeze-label is required before any scientific optimizer execution")
    return qualify(args.output, args.freeze_label, args.backend)


if __name__ == "__main__":
    raise SystemExit(main())
