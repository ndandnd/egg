"""Eight prospectively fixed native-hull cells, exclusive attempts and hard caps."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from experiments import native_recharge_qualification as nq

PROTOCOL = "native-hull-qualification-20260927-v2"
ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("src/egglab/native_hull.py", "src/experiments/native_hull_qualification.py",
           "src/tests/test_native_hull.py", "doc/NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md",
           "doc/NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md",
           "src/egglab/native_recharge.py", "src/experiments/native_recharge_qualification.py")
EVENTS = {"state_start", "pricing_request", "pricing_native", "pricing_result", "pricing_unresolved", "global_bound",
          "master_start", "master_status", "master_incumbent", "master_replay", "column_added",
          "state_finish", "dependency_blocked", "pool_polish_check", "pool_polish_step", "master_progress",
          "pool_polish_start", "pool_polish_finish"}
WORKER_SECONDS = 75.0
OUTER_SECONDS = 650.0
TARGET_TOL = 2e-4


def controls():
    cells = []
    case = nq.cyclic_case()
    for arm in ("cold", "retained"):
        for state, a in enumerate((4.0, 4.2, 4.0)):
            cells.append({"id": f"nominal_{arm}_s{state}", "case": case,
                "market": nh.Market(f"nominal-s{state}", (0, a, 0, 0), (0, .2, 0, .2)),
                "arm": arm, "state_index": state,
                "predecessor": f"nominal_retained_s{state-1}" if arm == "retained" and state else None,
                "target_exact": "1539/16" if state == 1 else "7591/80",
                "load_target_exact": ["0", "25/4", "0", "95/4"] if state == 1 else ["0", "27/4", "0", "93/4"]})
    for name, case, target, loads in (
        ("joint", nq.cyclic_case("joint", reserve=1, eta=19/20, early_kw=12), "2987911/28880", ["0", "573/76", "0", "1827/76"]),
        ("fixed_reserve", nq.cyclic_case("reserve_fixed", reserve=1), "99", ["0", "5", "0", "25"])):
        cells.append({"id": name+"_cold", "case": case, "market": nh.Market(name, (0, 4, 0, 0), (0, .2, 0, .2)),
                      "arm": "cold", "state_index": 0, "predecessor": None,
                      "target_exact": target, "load_target_exact": loads})
    return cells


def source_hashes():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def manifest(cell, budget):
    return {**cell, "case": asdict(cell["case"]), "market": asdict(cell["market"]),
            "physical_identity": cell["case"].identity(), "market_identity": cell["market"].identity(),
            "state_identity": nh.state_identity(cell["case"], cell["market"], cell["arm"], cell["state_index"], budget)}


def assess(cell, result):
    if result.get("status") != "certified":
        return {"pass": False, "reason": "no complete current-market hull certificate"}
    target = Fraction(cell["target_exact"])
    lower = Fraction(result["lower_certificate"]["lower_exact"])
    upper = Fraction(result["mixture"]["objective_exact"])
    tolerance = nh.rational(TARGET_TOL)
    passed = (0 <= upper-lower <= nh.rational(result["epsilon"])
              and lower-tolerance <= target <= upper+tolerance and abs(upper-target) <= tolerance)
    # Load errors are reported; acceptance is the objective enclosure, not an
    # unjustified demand that every equivalent decomposition has identical weights.
    load_errors = [float(Fraction(x)-Fraction(y)) for x, y in
                   zip(result["mixture"]["load_exact"], cell["load_target_exact"])]
    return {"pass": passed, "reason": "analytical target/enclosure check",
            "target_exact": str(target), "load_errors": load_errors}


def read_evidence(directory):
    folder = Path(directory)
    events, issues, result = [], [], None
    trace = folder/"events.jsonl"
    if trace.exists():
        try:
            lines = trace.read_bytes().splitlines()
        except OSError as exc:
            lines = []
            issues.append({"file": "events.jsonl", "message": str(exc)})
        for index, line in enumerate(lines):
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or event.get("event") not in EVENTS:
                    raise ValueError("Unrecognized hull trace event")
                if event["event"] == "pricing_native" and not isinstance(event.get("detail"), dict):
                    raise ValueError("Malformed nested oracle event")
                events.append(event)
            except (ValueError, TypeError, UnicodeError) as exc:
                issues.append({"file": "events.jsonl", "line": index+1, "message": str(exc),
                               "valid_prefix_events": len(events)})
                break
    if (folder/"result.json").exists():
        try:
            candidate = json.loads((folder/"result.json").read_bytes())
            if (not isinstance(candidate, dict) or not isinstance(candidate.get("assessment"), dict)
                    or type(candidate["assessment"].get("pass")) is not bool
                    or not isinstance(candidate.get("result"), dict)
                    or candidate["result"].get("status") not in
                        ("certified", "stalled_bounded", "budget_exhausted", "unresolved", "blocked_by_predecessor")):
                raise ValueError("Malformed hull result")
            result = candidate
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            issues.append({"file": "result.json", "message": str(exc)})
    return events, result, issues


def accounting(events):
    starts, returns, walls = [], [], []
    polish_starts, polish_returns, polish_walls, completed_steps, completed_checks = [], [], [], [], []
    active, cumulative_steps, phase_steps, phase_checks, last_polish = None, 0, 0, 0, None
    ordered_polish = True
    for e in events:
        if e["event"] == "pool_polish_start":
            ordered_polish &= (active is None and type(e.get("master_call")) is int
                               and e["master_call"] >= 0 and type(e.get("cumulative_steps")) is int
                               and e["cumulative_steps"] == cumulative_steps)
            active, phase_steps, phase_checks, last_polish = e.get("master_call"), 0, 0, "start"
            polish_starts.append(e["master_call"])
        if e["event"] == "pool_polish_check":
            ordered_polish &= (active is not None and e.get("master_call") == active
                               and type(e.get("step")) is int and e["step"] == cumulative_steps
                               and last_polish in ("start", "step"))
            phase_checks += 1
            last_polish = "check"
        if e["event"] == "pool_polish_step":
            ordered_polish &= (active is not None and e.get("master_call") == active
                               and type(e.get("step")) is int and e["step"] == cumulative_steps+1
                               and last_polish == "check")
            cumulative_steps += 1
            phase_steps += 1
            last_polish = "step"
        if e["event"] == "pool_polish_finish":
            ordered_polish &= (active is not None and e.get("master_call") == active
                               and e.get("steps_completed") == phase_steps
                               and e.get("checks_completed") == phase_checks
                               and (e.get("outcome") != "qualified" or last_polish == "check"))
            active, last_polish = None, None
            polish_returns.append(e["master_call"])
            if (not nh.nr._finite(e.get("elapsed_s"))
                    or any(type(e.get(k)) is not int or e[k] < 0 for k in ("steps_completed", "checks_completed"))):
                raise ValueError("Invalid exact-polishing time/call accounting")
            polish_walls.append(e["elapsed_s"])
            completed_steps.append(e["steps_completed"])
            completed_checks.append(e["checks_completed"])
        kind, item = ("pricing", e["detail"]) if e["event"] == "pricing_native" else ("master", e)
        if item.get("event") == ("native_start" if kind == "pricing" else "master_start"):
            starts.append((kind, e["call"]))
        if item.get("event") == ("native_status" if kind == "pricing" else "master_status"):
            returns.append((kind, e["call"]))
            wall = item.get("stats", {}).get("wall_s")
            if not nh.nr._finite(wall):
                raise ValueError("Invalid returned native wall time")
            walls.append(wall)
    complete = (len(starts) == len(set(starts)) and len(returns) == len(set(returns))
                and set(starts) == set(returns))
    steps = sum(e["event"] == "pool_polish_step" for e in events)
    checks = sum(e["event"] == "pool_polish_check" for e in events)
    polish_complete = (ordered_polish and active is None and len(polish_starts) == len(set(polish_starts))
                       and len(polish_returns) == len(set(polish_returns))
                       and set(polish_starts) == set(polish_returns)
                       and sum(completed_steps) == steps and sum(completed_checks) == checks)
    return {"native_starts": len(starts), "native_returns": len(returns),
            "pricing_starts": sum(k == "pricing" for k, _ in starts),
            "master_starts": sum(k == "master" for k, _ in starts),
            "seed_requests": sum(e["event"] == "pricing_request" and e.get("seed", False) for e in events),
            "pricing_requests": sum(e["event"] == "pricing_request" for e in events),
            "native_wall_s": math.fsum(walls), "native_accounting_complete": complete,
            "polish_starts": len(polish_starts), "polish_returns": len(polish_returns),
            "polish_steps": steps, "polish_checks": checks, "polish_wall_s": math.fsum(polish_walls),
            "polish_accounting_complete": polish_complete}


def admitted_predecessor(directory, expected_cell):
    """Import only a controller-accepted, independently complete prior cell."""
    folder = Path(directory)
    events, package, issues = read_evidence(folder)
    try:
        receipt = json.loads((folder/"receipt.json").read_bytes())
        if (not isinstance(receipt, dict) or receipt.get("cell") != expected_cell
                or receipt.get("pass") is not True or type(receipt.get("returncode")) is not int
                or receipt["returncode"] != 0 or receipt.get("timeout") is not False
                or receipt.get("status") != "certified" or receipt.get("evidence_issues") != []):
            raise ValueError("Predecessor controller receipt is missing, failed, or mismatched")
        counts = accounting(events)
        if (not counts["native_accounting_complete"] or not counts["polish_accounting_complete"]
                or counts["native_starts"] < 1):
            raise ValueError("Predecessor trace has no complete nonzero native accounting")
        if any(type(receipt.get(k)) is not type(v) or receipt[k] != v for k, v in counts.items()):
            raise ValueError("Predecessor receipt accounting disagrees with its saved trace")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        issues.append({"file": "receipt.json/events.jsonl", "message": str(exc)})
    if (not package or not package["assessment"]["pass"]
            or package["result"]["status"] != "certified"):
        issues.append({"file": "result.json", "message": "Predecessor result was not accepted as certified"})
    return (None if issues else package), issues


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
        if source_hashes() != frozen["source_hashes"]:
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
        result = nh.certify(cell["case"], cell["market"], budget, arm=cell["arm"], state_index=cell["state_index"],
                            previous=previous, expected_previous=expected, record=record)
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
    frozen = {"protocol": PROTOCOL, "source_hashes": hashes, "freeze_label": freeze_label,
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
        cmd = [sys.executable, "-m", "experiments.native_hull_qualification", "--worker", cell["id"],
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
    cmd = [sys.executable, "-m", "experiments.native_hull_qualification", "--controller", "--output", str(out.resolve()),
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
    if not args.freeze_label:
        parser.error("--freeze-label is required before optimizer execution")
    return controller(args.output, args.freeze_label, args.backend) if args.controller else supervise(args.output, args.freeze_label, args.backend)


if __name__ == "__main__":
    raise SystemExit(main())
