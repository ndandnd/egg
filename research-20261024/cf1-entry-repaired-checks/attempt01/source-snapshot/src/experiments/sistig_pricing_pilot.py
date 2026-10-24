"""Prospective complete public-timetable pricing pilot; no optimizer on import.

All37 services and every declared movement are retained in each of two
single-depot scenarios. Synthetic prices/costs; no operational benefit claim.
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
from experiments import sistig_native_case as intake

PROTOCOL = "sistig-pricing-pilot-20260927-v1"
ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
PAYLOAD_SHA256 = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"
SOURCES = ("src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
    "src/experiments/native_recharge_qualification.py", "src/experiments/sistig_native_case.py",
    "src/experiments/sistig_pricing_pilot.py", "src/tests/test_sistig_pricing_pilot.py",
    "doc/SISTIG_PRICING_PILOT_PROTOCOL_20260927.md", "src/cluster/sistig_pricing_pilot.sbatch",
    "src/cluster/unicorn_env.sh", "src/egglab/solver.py",
    "result/native_pathflow/20260927-attempt1/frozen.json",
    "result/native_pathflow/20260927-attempt1/MANIFEST.json",
    "result/native_pathflow/20260927-attempt1/summary.json",
    "result/native_pathflow/20260927-attempt1/review/MANIFEST.json",
    "result/native_pathflow/20260927-attempt1/review/audit-report.json",
    "result/native_pathflow/20260927-attempt1/review/REVIEW.md", PAYLOAD)
_json = original._json
environment = original.environment


def controls():
    raw = (ROOT/PAYLOAD).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("Pinned public payload changed")
    variants = json.loads(raw)["native_cases"]
    if [v["selected_depot_id"] for v in variants] != [15,16]:
        raise ValueError("Expected the two complete public depot variants")
    cells = []
    for variant in variants:
        case = intake.native_case_from_payload(variant)
        if case.identity() != variant["case_identity"] or len(case.trips) != 37:
            raise ValueError("Public case identity/coverage changed")
        compiled = nr.compile_case(case)
        # Recompute the already declared feasible reference; never a solver seed.
        witness = intake._construct_and_replay_one_trip_witness(case, compiled)
        prices = [.2]*(len(case.market_edges_min)-1)
        reference = case.vehicle_cost*37 + .2*witness["total_terminal_charge_kwh"]
        cells.append({"id":f"depot_{variant['selected_depot_id']}_flat",
            "case":case,"objective":"pricing","prices":prices,
            "reference_upper":reference,"reference_witness":witness,
            "source_payload_sha256":PAYLOAD_SHA256})
    return cells


def assess(cell, result, backend):
    """Admit a conditional interval, without mistaking a bounded solve for optimality."""
    issues = []
    if result.get("case_identity") != cell["case"].identity() or result.get("prices") != cell["prices"]:
        issues.append("Returned case identity or prices differ from frozen input")
    if result.get("status") not in ("certified", "bounded"):
        issues.append("No physically replayed finite interval; known feasible input")
    else:
        lo, hi, gap = (result.get(k) for k in ("lower", "upper", "gap"))
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
               for v in (lo,hi,gap)) or lo > hi or gap < 0:
            issues.append("Malformed finite enclosure")
        else:
            if abs(gap-(hi-lo)) > 1e-8:
                issues.append("Stored width differs from enclosure")
            if lo > cell["reference_upper"]+nr.BOUND_GUARD:
                issues.append("Native lower bound contradicts constructive reference")
            expected = "certified" if gap <= 1e-4 else "bounded"
            if result["status"] != expected:
                issues.append("Status does not match unchanged width policy")
        try:
            replay = nr.replay_native(cell["case"],result["plan"],cell["prices"])
            admitted = nr.admit_bound(result["stats"],replay["pricing_objective"])
            if (lo,hi) != admitted:
                issues.append("Endpoints differ from qualified native-bound admission")
            stats = result["stats"]
            runtime = stats["backend_runtime"]
            expected_module = "mip.gurobi" if backend == "GRB" else "mip.cbc"
            if (stats.get("backend") != backend or stats.get("threads") != 1
                    or runtime.get("requested") != backend or runtime.get("solver_module") != expected_module
                    or runtime.get("model_solver_name") != backend):
                issues.append("Returned backend/thread identity differs from request")
        except (ValueError,KeyError,TypeError) as exc:
            issues.append(f"Physical replay rejected: {type(exc).__name__}: {exc}")
    return {"pass":not issues,"issues":issues,
        "scope":"Conditional numerical pricing enclosure for declared synthetic scenario",
        "reference_upper":cell["reference_upper"],
        "optimality_certified":not issues and result.get("status")=="certified"}


def assess_runtime(assessment, elapsed_s, wall_seconds):
    verdict = {**assessment, "issues":list(assessment["issues"]),
               "routine_elapsed_s":elapsed_s, "routine_cap_s":wall_seconds}
    verdict["routine_within_budget"] = (not isinstance(elapsed_s,bool)
        and isinstance(elapsed_s,(int,float)) and math.isfinite(elapsed_s)
        and 0 <= elapsed_s <= wall_seconds)
    if not verdict["routine_within_budget"]:
        verdict["pass"] = False
        verdict["optimality_certified"] = False
        verdict["issues"].append("Scientific routine/admission exceeded wall deadline")
    return verdict


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
        assessment = assess(cell, result, budget.backend)
        elapsed = time.perf_counter()-start
        assessment = assess_runtime(assessment,elapsed,budget.wall_seconds)
        _json(out/"result.json", {"cell": cell_id, "elapsed_s": elapsed, "environment": environment(),
              "result": result, "assessment": assessment})
        return 0 if assessment["pass"] else 1
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
    expected_events = ["native_start","native_status","native_incumbent",
                       "charge_normalization","serial_decoding","objective_reconstruction"]
    finite = result and result["result"].get("status") in ("certified","bounded")
    names = [e["event"] for e in events]
    if (names != expected_events[:len(names)] or len(names)>len(expected_events)
            or any(e["round"] != 0 for e in events) or (finite and names != expected_events)):
        issues.append({"type":"LinearPhaseAccounting","message":"Expected one ordered round-zero pricing phase"})
    if result and len(events)>=2 and events[1]["event"] == "native_status":
        if events[1]["stats"] != result["result"].get("stats"):
            issues.append({"type":"NativeStatusMismatch","message":"Raw phase stats differ from saved result"})
    return events, result, issues


def qualify(output, freeze_label, backend="GRB"):
    if not freeze_label.strip():
        raise ValueError("The committed source freeze label is required")
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    budget = nr.Budget(backend=backend, threads=1, phase_seconds=180, wall_seconds=240, max_rounds=1, epsilon=1e-4)
    nr._check_budget(budget)
    hashes = source_hashes()
    gate = ROOT/"result/native_pathflow/20260927-attempt1"
    gate_frozen = json.loads((gate/"frozen.json").read_text())
    gate_summary = json.loads((gate/"summary.json").read_text())
    gate_audit = json.loads((gate/"review/audit-report.json").read_text())
    if (not gate_summary["all_pass"] or not gate_summary["source_hashes_unchanged"]
            or not gate_audit["audit_status"].startswith("PASS for all 20")):
        raise ValueError("Independent compact gate is not complete")
    for dependency in ("src/egglab/native_pathflow.py", "src/egglab/native_recharge.py"):
        if hashes[dependency] != gate_frozen["source_hashes"][dependency]:
            raise ValueError("Pilot physical dependency differs from passed gate")
    cells = controls()
    for cell in cells:
        nr.validate_case(cell["case"])
    frozen = {"protocol": PROTOCOL, "freeze_label": freeze_label, "source_hashes": hashes,
              "budget": asdict(budget), "environment": environment(),
              "compact_gate": {"attempt":"result/native_pathflow/20260927-attempt1",
                  "freeze_label":gate_frozen["freeze_label"],"independent_audit_status":gate_audit["audit_status"]},
              "dataset": {"doi":intake.DOI,"license":intake.LICENSE_URL,
                  "attribution":"Adapted from Sistig, Sinhuber, Rogge and Sauer (2025); modeled energy and single-depot EGG restrictions"},
              "controls": [{**c, "case": asdict(c["case"]), "case_identity": c["case"].identity()} for c in cells]}
    _json(out/"frozen.json", frozen)
    rows = []
    start = time.perf_counter()
    for cell in cells:
        folder = out/cell["id"]
        folder.mkdir()
        _json(folder/"input.json", {**cell, "case": asdict(cell["case"]), "budget": asdict(budget),
              "source_hashes": hashes, "case_identity": cell["case"].identity()})
        cmd = [sys.executable, "-m", "experiments.sistig_pricing_pilot", "--worker", cell["id"],
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
    parser.add_argument("--backend", choices=("CBC", "GRB"), default="GRB")
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
