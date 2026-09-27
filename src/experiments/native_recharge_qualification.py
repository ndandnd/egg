"""Prospectively fixed synthetic native-recharge qualification; no import solve.

The controller creates an exclusive attempt and launches one single-thread worker
per control, sequentially. Every declared cell is attempted even after failures.
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

PROTOCOL = "native-recharge-qualification-20260927-v1"
ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("src/egglab/native_recharge.py", "src/experiments/native_recharge_qualification.py",
           "src/tests/test_native_recharge.py", "doc/NATIVE_RECHARGE_QUALIFICATION_PROTOCOL_20260927.md")
TARGET_TOL = 2e-4


def _terminal_modes(trips, depot="D"):
    return tuple(m for t in trips for m in (
        nr.Movement("out_"+t.id, "pullout", None, t.id,
                    (nr.Leg(depot, t.start_place, t.start_min, t.start_min, 0.0),)),
        nr.Movement("in_"+t.id, "pullin", t.id, None,
                    (nr.Leg(t.end_place, depot, t.end_min, t.end_min, 0.0),))))


def cyclic_case(name="cyclic", battery=20.0, reserve=0.0, eta=1.0, early_kw=10.0, vehicles=2):
    trips = (nr.Trip("A", 0, 60, "D", "D", 15.0), nr.Trip("B", 120, 180, "D", "D", 15.0))
    modes = _terminal_modes(trips) + (
        nr.Movement("depot_AB", "depot", "A", "B",
                    (nr.Leg("D", "D", 60, 60, 0.0), nr.Leg("D", "D", 120, 120, 0.0)), 1),
        nr.Movement("direct_AB", "direct", "A", "B", (nr.Leg("D", "D", 60, 60, 0.0),)))
    return nr.NativeCase(name, trips, modes,
        (nr.Resource(0, 60, 0, 0, 0), nr.Resource(60, 120, early_kw, early_kw),
         nr.Resource(120, 180, 0, 0, 0), nr.Resource(180, 240, 30, 30)),
        (0, 60, 120, 180, 240), "D", vehicles, battery, reserve, 0, 240, 7, efficiency=eta)


def single_case(name="single", eta=1.0, power=30.0):
    trips = (nr.Trip("A", 0, 60, "D", "D", 15.0),)
    return nr.NativeCase(name, trips, _terminal_modes(trips),
        (nr.Resource(0, 60, 0, 0, 0), nr.Resource(60, 120, power, power)),
        (0, 60, 120), "D", 2, 20, 1, 0, 120, 7, efficiency=eta)


def overlap_case(deadline=60):
    trips = tuple(nr.Trip(t, 0, 30, "D", "D", 5.0) for t in ("A", "B"))
    edges = (0, 60) if deadline == 60 else (0, 60, deadline)
    return nr.NativeCase("overlap_"+str(deadline), trips, _terminal_modes(trips),
        (nr.Resource(0, deadline, 10, 10),), edges, "D", 2, 20, 1, 0, deadline, 7)


def multileg_case():
    trips = (nr.Trip("A", 30, 60, "P", "Q", 8),)
    modes = (nr.Movement("out_A", "pullout", None, "A",
                (nr.Leg("D", "X", 0, 5, 1), nr.Leg("X", "P", 5, 15, 2))),
             nr.Movement("in_A", "pullin", "A", None,
                (nr.Leg("Q", "Y", 60, 65, 1), nr.Leg("Y", "D", 65, 75, 2))))
    return nr.NativeCase("multileg", trips, modes,
        (nr.Resource(0, 75, 0, 0, 0), nr.Resource(75, 120, 30, 30)),
        (0, 60, 120), "D", 2, 20, 2, 0, 120, 7, deadhead_cost_per_min=0.5)


def controls():
    """Fixed grid. Targets are analytical claims to test, never solver seeds."""
    nominal = cyclic_case()
    reserve = cyclic_case("reserve_usable", battery=21, reserve=1)
    joint = cyclic_case("joint", reserve=1, eta=19/20, early_kw=12)
    fixed = cyclic_case("reserve_fixed", reserve=1)
    a, b = [0, 4, 0, 0], [0, 0.2, 0, 0.2]
    def cell(id, case, objective, target, **payload):
        return {"id": id, "case": case, "objective": objective,
                "expected_status": "infeasible" if target is None else "certified",
                "target": target, **payload}
    return [
        cell("single_linear", single_case(), "pricing", 22, prices=[1, 1]),
        cell("efficiency_linear", single_case("single_efficiency", eta=19/20), "pricing", 433/19, prices=[1, 1]),
        cell("cyclic_flat", nominal, "pricing", 37, prices=[1, 1, 1, 1]),
        cell("cyclic_own_price", nominal, "pricing", 134, prices=[0, 6, 0, 4]),
        cell("cyclic_hull_price", nominal, "pricing", 153.5, prices=[0, 5.35, 0, 4.65]),
        cell("cyclic_planner", nominal, "planner", 97, a=a, b=b),
        cell("preserved_reserve_planner", reserve, "planner", 97, a=a, b=b),
        cell("joint_flat", joint, "pricing", 733/19, prices=[1, 1, 1, 1]),
        cell("joint_planner", joint, "planner", 38527/361, a=a, b=b),
        cell("fixed_reserve_planner", fixed, "planner", 99, a=a, b=b),
        cell("fixed_reserve_one_bus", replace(fixed, name="fixed_one_bus", max_vehicles=1), "pricing", None, prices=[1]*4),
        cell("terminal_capacity_failure", single_case("short_terminal", power=10), "pricing", None, prices=[1, 1]),
        cell("partial_overlap_failure", overlap_case(60), "pricing", None, prices=[1]),
        cell("serial_connector", overlap_case(90), "pricing", 24, prices=[1, 1]),
        cell("directed_multileg", multileg_case(), "pricing", 36, prices=[1, 1]),
    ]


def source_hashes():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}


def _json(path, data):
    with Path(path).open("x") as f:
        json.dump(data, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def _version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def environment():
    return {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "mip_version": _version("mip"), "gurobipy_version": _version("gurobipy")}


def assess(cell, result):
    if result["status"] != cell["expected_status"]:
        return {"pass": False, "reason": "status differs from prospective target"}
    if cell["target"] is None:
        return {"pass": True, "reason": "native infeasibility status; solver-conditional"}
    target = cell["target"]
    if (not all(math.isfinite(result[k]) for k in ("lower", "upper", "gap"))
            or not result["lower"]-TARGET_TOL <= target <= result["upper"]+TARGET_TOL
            or abs(result["upper"]-target) > TARGET_TOL
            or not result["plan"]["replay"]["replay_ok"]):
        return {"pass": False, "reason": "bound enclosure/value/replay differs from analytical target"}
    return {"pass": True, "reason": "target enclosed and physical witness replayed"}


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
                        ("native_start", "native_status", "replayed_iteration")
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
        cmd = [sys.executable, "-m", "experiments.native_recharge_qualification", "--worker", cell["id"],
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
