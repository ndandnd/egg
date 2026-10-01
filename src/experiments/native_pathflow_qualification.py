"""Prospective compact path-flow gate; no optimizer on import.

The same nineteen prior controls plus one declared multi-visit control; own
immutable attempt and worker, unchanged objective/bound/roundoff admission.
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

from egglab import native_pathflow as pf
from experiments import native_recharge_qualification as original
from experiments import native_halfminute_qualification as timing

PROTOCOL = "native-pathflow-qualification-20260927-v3-orphan-projection"
ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
    "src/experiments/native_recharge_qualification.py",
    "src/experiments/native_halfminute_qualification.py",
    "src/experiments/native_pathflow_qualification.py", "src/tests/test_native_pathflow.py",
    "doc/NATIVE_PATHFLOW_QUALIFICATION_PROTOCOL_20260927.md",
    "src/tests/test_native_pathflow_energy_band.py",
    "src/tests/test_native_pathflow_hull.py",
    "doc/NATIVE_PATHFLOW_ENERGY_BAND_DESIGN_20260927.md",
    "doc/NATIVE_PATHFLOW_EQUIVALENCE_REVIEW_20260927.md",
    "doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_REPAIR_DESIGN_20260927.md",
    "doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_REPAIR_REVIEW_20260927.md",
    "doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_QUALIFICATION_PROTOCOL_20260927.md",
    "doc/NATIVE_PATHFLOW_ORPHAN_CHARGE_IMPLEMENTATION_REVIEW_20260927.md")
TARGET_TOL = original.TARGET_TOL
_json = original._json
environment = original.environment
assess = original.assess


def multivisit_case():
    trips=tuple(nr.Trip(t,start,start+20,'P','Q',8) for t,start in [('A',10),('B',90),('C',170)])
    modes=[]
    for t in trips:
        modes.extend((nr.Movement('out_'+t.id,'pullout',None,t.id,
            (nr.Leg('D','X',t.start_min-10,t.start_min-5,1),nr.Leg('X','P',t.start_min-5,t.start_min,1))),
            nr.Movement('in_'+t.id,'pullin',t.id,None,
            (nr.Leg('Q','X',t.end_min,t.end_min+5,1),nr.Leg('X','D',t.end_min+5,t.end_min+10,1)))))
    for before,after in zip(trips,trips[1:]):
        modes.append(nr.Movement('depot_'+before.id+after.id,'depot',before.id,after.id,
            (nr.Leg('Q','X',before.end_min,before.end_min+5,1),
             nr.Leg('X','D',before.end_min+5,before.end_min+10,1),
             nr.Leg('D','X',after.start_min-10,after.start_min-5,1),
             nr.Leg('X','P',after.start_min-5,after.start_min,1)),2))
    return nr.NativeCase('three_services_two_depot_visits',trips,tuple(modes),
        (nr.Resource(0,240,30,30),),(0,60,120,180,240),'D',1,20,1,0,240,7,
        deadhead_cost_per_min=.5,efficiency=19/20)


def controls():
    return timing.controls()+[{'id':'three_service_multivisit','case':multivisit_case(),
        'objective':'pricing','target':1423/19,'expected_status':'certified','prices':[1]*4}]


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
            result = pf.solve_pricing(case, cell["prices"], budget, record=record)
        else:
            result = pf.solve_planner(case, cell["a"], cell["b"], budget, record=record)
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
                         "charge_projection",
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
    frozen = {"protocol": PROTOCOL, "formulation": pf.FORMULATION,
              "native_matrix":pf.NATIVE_MATRIX,"extraction_policy":pf.EXTRACTION_POLICY,
              "shared_negative_normalizer_policy":nr.EXTRACTION_POLICY,
              "freeze_label": freeze_label, "source_hashes": hashes,
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
        cmd = [sys.executable, "-m", "experiments.native_pathflow_qualification", "--worker", cell["id"],
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
