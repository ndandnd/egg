"""Eight-cell development diagnostic for pricing-call and rational-bit limits.

Import and design do not solve. This is a new cold-hull protocol, independent
of every frozen retrieval or feasible-pool attempt.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from fractions import Fraction
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

from egglab import native_pathflow_hull as compact
from experiments import computational_benchmark as base
from experiments import native_pathflow_qualification as fixture
from experiments.feasible_pool_pilot_report import extract_trace


ROOT = base.ROOT
ATTEMPT = ROOT / "result/budget_sizing_diagnostic/20260928-attempt1"
PROTOCOL = "egg-multivisit-budget-sizing-development-20260928-v1"
CASE = "synthetic_multivisit"
CALLS = (4, 16)
BITS = (4096, 8192)
CHILD_HARD_SECONDS = 90
CONTROLLER_CAP_SECONDS = 900
SOURCE_FILES = (
    "src/experiments/budget_sizing_diagnostic.py",
    "src/tests/test_budget_sizing_diagnostic.py",
    "src/cluster/budget_sizing_diagnostic.sbatch",
    "research-20260928/budget-sizing-diagnostic/DESIGN.md",
    "src/experiments/computational_benchmark.py",
    "src/experiments/feasible_pool_pilot_report.py",
    "src/experiments/native_pathflow_qualification.py",
    "src/egglab/native_hull.py",
    "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py",
    "src/egglab/native_recharge.py",
    "src/egglab/solver.py",
)


def cells():
    """Counterbalance factor order across the two markets."""
    first = [(0, calls, bits) for bits in BITS for calls in CALLS]
    second = [(1, calls, bits) for bits in reversed(BITS) for calls in reversed(CALLS)]
    return tuple(first + second)


def cell_name(calls, bits):
    if calls not in CALLS or bits not in BITS:
        raise ValueError("Outside declared sizing matrix")
    return f"c{calls}_b{bits}"


def budget(calls, bits):
    old = base.budget(CASE, "cold_hull")
    return replace(old, pricing_calls=calls, rational_bits=bits,
                   master_calls=64, pool_cap=64)


def case():
    item = fixture.multivisit_case()
    if item.identity() != base.CASE_IDS[CASE]:
        raise ValueError("Multivisit physical identity changed")
    return item


def design():
    item = case()
    return {"case": asdict(item), "case_identity": item.identity(),
            "markets": {str(s): asdict(base.market(CASE, s)) for s in (0, 1)},
            "market_identities": {str(s): base.market(CASE, s).identity() for s in (0, 1)},
            "cells": [{"state": s, "pricing_calls": c, "rational_bits": b,
                       "name": cell_name(c, b), "budget": asdict(budget(c, b)),
                       "hard_child_seconds": CHILD_HARD_SECONDS} for s, c, b in cells()],
            "development_only": True, "backend": "GRB", "native_threads": 1,
            "arm": "cold", "master_policy": "native_lp",
            "reuse_policy": "certified_only", "pricing_reserve_seconds": 0.0,
            "bound_cache_policy": "none"}


def software_runtime():
    """Compare portable software identity, never login versus compute hostname."""
    import gurobipy
    return {"python_version": platform.python_version(), "python_build": sys.version,
            "python_implementation": sys.implementation.name,
            "python_abi": sys.implementation.cache_tag, "machine": platform.machine(),
            "mip": importlib.metadata.version("mip"),
            "gurobipy": importlib.metadata.version("gurobipy"),
            "gurobi_runtime": ".".join(map(str, gurobipy.gurobi.version()))}


def host_environment():
    return {"hostname": platform.node(), "platform": platform.platform()}


def runtime_compatible(saved, actual):
    return saved == actual


def native_probe():
    """Construct a native model and record its seed; do not optimize it."""
    import mip
    from egglab import native_recharge as recharge
    model = mip.Model(name="budget-sizing-preflight", sense=mip.MINIMIZE, solver_name="GRB")
    seed = model.seed
    if type(seed) is not int or seed != 0:
        raise ValueError("Expected fixed native seed 0")
    return {"backend_identity": recharge._backend_identity(model, "GRB"), "model_seed": seed}


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the separate declared sizing attempt is allowed")
    return target


def freeze(path):
    target = _attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "software_runtime": software_runtime(),
            "freeze_host_environment": host_environment(), "native_probe": native_probe(),
            "design": design(), "controller_cap_seconds": CONTROLLER_CAP_SECONDS,
            "declared_cells": 8, "scientific_admission": "pending independent review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = _attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit:
        raise ValueError("Frozen protocol/commit differs")
    if spec.get("source_hashes") != source_hashes():
        raise ValueError("Frozen source hashes differ")
    if not runtime_compatible(spec.get("software_runtime"), software_runtime()):
        raise ValueError("Frozen portable software runtime differs")
    if spec.get("native_probe") != native_probe():
        raise ValueError("Frozen native backend/seed differs")
    if (base.canonical(spec.get("design")) != base.canonical(design())
            or spec.get("controller_cap_seconds") != CONTROLLER_CAP_SECONDS
            or spec.get("declared_cells") != 8):
        raise ValueError("Frozen sizing design differs")
    return spec


def folder(path, state, calls, bits):
    return Path(path) / CASE / f"state{state}" / cell_name(calls, bits)


def worker(path, state, calls, bits):
    target = _attempt(path)
    if (state, calls, bits) not in cells():
        raise ValueError("Undeclared cell")
    dest = folder(target, state, calls, bits)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if not (dest / "launch.json").is_file():
            raise ValueError("Missing child launch receipt")
        item, market, cfg = case(), base.market(CASE, state), budget(calls, bits)
        declared = next(row for row in spec["design"]["cells"]
                        if (row["state"], row["pricing_calls"], row["rational_bits"]) ==
                        (state, calls, bits))
        if (spec["design"]["case_identity"] != item.identity()
                or spec["design"]["market_identities"][str(state)] != market.identity()
                or declared["budget"] != asdict(cfg)):
            raise ValueError("Cell differs from frozen physical/market/budget design")
        def record(event):
            with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        result = compact.certify(item, market, cfg, arm="cold", state_index=state, record=record)
        if (result.get("state_identity") != compact.state_identity(item, market, "cold", state, cfg)
                or result.get("arm") != "cold" or result.get("state_index") != state):
            raise ValueError("Returned hull state/budget identity differs")
        base.save_new(dest / "raw_result.json", {"result": result, "state": state,
                                                  "pricing_calls": calls, "rational_bits": bits})
        assessment = base.assess(item, market, "cold_hull", result)
        base.save_new(dest / "result.json", {"assessment": assessment, "state": state,
                                              "pricing_calls": calls, "rational_bits": bits,
                                              "elapsed_seconds": time.monotonic() - started})
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
                                                  "message": str(exc),
                                                  "traceback": traceback.format_exc(),
                                                  "elapsed_seconds": time.monotonic() - started})
        return 2


def result_row(path, state, calls, bits, receipt=None):
    dest = folder(path, state, calls, bits)
    row = {"state": state, "pricing_call_cap": calls, "rational_bit_cap": bits,
           "cell": cell_name(calls, bits), "outcome": "unstarted",
           "native_status": None, "complete_evidence": False,
           "stop_reason": None, "lower_exact": None, "upper_exact": None,
           "gap_exact": None, "pricing_requests": None, "master_calls": None,
           "max_rational_bits": None, "polish_wall_s": None,
           "pricing_solver_wall_recorded_s": None,
           "pricing_solver_wall_complete": None,
           "master_solver_wall_recorded_s": None,
           "master_solver_wall_complete": None,
           "child_wall_s": None, "on_time": None}
    if receipt is None and (dest / "receipt.json").is_file():
        try:
            receipt = json.loads((dest / "receipt.json").read_text())
        except (OSError, ValueError, TypeError):
            row["outcome"] = "receipt_unreadable"
    if receipt is not None:
        row["on_time"], row["child_wall_s"] = receipt.get("on_time"), receipt.get("elapsed_seconds")
        row["outcome"] = ("hard_timeout" if receipt.get("hard_timeout") else
                          "failed" if receipt.get("returncode") != 0 else
                          "late" if receipt.get("on_time") is not True else "returned")
    elif row["outcome"] == "unstarted" and (dest / "launch.json").exists():
        row["outcome"] = "interrupted_unreceipted"
    raw_path = dest / "raw_result.json"
    if raw_path.is_file():
        try:
            raw = json.loads(raw_path.read_text())["result"]
            counts = raw.get("counts", {})
            row.update(native_status=raw.get("status"), stop_reason=raw.get("reason"),
                       pricing_requests=counts.get("pricing_requests"),
                       master_calls=counts.get("master_calls"),
                       max_rational_bits=counts.get("max_rational_bits"),
                       polish_wall_s=counts.get("polish_wall_s"))
        except (OSError, ValueError, TypeError, KeyError):
            row["raw_read_error"] = True
    events = dest / "events.jsonl"
    if events.is_file():
        try:
            trace = extract_trace([json.loads(line) for line in events.read_text().splitlines()])
            for key in ("pricing_solver_wall_recorded_s", "pricing_solver_wall_complete",
                        "master_solver_wall_recorded_s", "master_solver_wall_complete"):
                row[key] = trace[key]
            row["pricing_solver_wall_complete"] &= trace["pricing_results"] == row["pricing_requests"]
            row["master_solver_wall_complete"] &= trace["master_statuses"] == row["master_calls"]
            row["events_sha256"] = base.sha(events)
        except (OSError, ValueError, TypeError, KeyError):
            row["events_read_error"] = True
    assessed = dest / "result.json"
    if row["outcome"] == "returned" and assessed.is_file():
        try:
            result = json.loads(assessed.read_text())
            assessment = result["assessment"]
            if ((result["state"], result["pricing_calls"], result["rational_bits"])
                    != (state, calls, bits)):
                raise ValueError("Result identity differs")
            if assessment.get("complete_evidence") is True and assessment.get("bounds"):
                raw = json.loads(raw_path.read_text())["result"]
                if (assessment.get("status") != raw.get("status")
                        or assessment["bounds"] != base.finite_bounds(raw)):
                    raise ValueError("Assessed and raw native result differ")
                lo = Fraction(raw["lower_certificate"]["lower_exact"])
                hi = Fraction(raw["mixture"]["objective_exact"])
                if lo > hi:
                    raise ValueError("Native certificate interval inverted")
                row.update(complete_evidence=True, native_status=assessment["status"],
                           outcome=assessment["status"], lower_exact=str(lo),
                           upper_exact=str(hi), gap_exact=str(hi - lo))
            else:
                row["outcome"] = "incomplete_evidence"
        except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError):
            row["outcome"] = "partial_result"
            row["complete_evidence"] = False
    elif row["outcome"] == "returned":
        row["outcome"] = "returned_unassessed"
    return row


def controller(path):
    target = _attempt(path)
    frozen(target)
    base.save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    for state, calls, bits in cells():
        dest = folder(target, state, calls, bits)
        dest.mkdir(parents=True, exist_ok=False)
        command = [sys.executable, "-m", "experiments.budget_sizing_diagnostic", "worker",
                   "--attempt", str(target), "--state", str(state),
                   "--calls", str(calls), "--bits", str(bits)]
        receipt = base.launch_child(target, CASE, state, cell_name(calls, bits),
                                    CHILD_HARD_SECONDS, command=command)
        rows.append(result_row(target, state, calls, bits, receipt))
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                                             "declared_cells": 8, "accounted_cells": len(rows),
                                             "all_declared_cells_accounted": len(rows) == 8,
                                             "scientific_admission": "pending independent result review"})
    return 0


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if json.loads((target / "summary.json").read_text()).get("accounted_cells") == 8:
                return
        except (OSError, ValueError, TypeError):
            pass
    rows = [result_row(target, s, c, b) for s, c, b in cells()]
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
                                                       "declared_cells": 8,
                                                       "accounted_cells": len(rows),
                                                       "scientific_admission": "none; abnormal controller termination"})


def supervise(path):
    target = _attempt(path)
    source_error, child_rc, timed_out, launch_error, quiescent = None, None, False, None, True
    try:
        frozen(target)
    except Exception as exc:
        source_error = repr(exc)
    started = time.monotonic()
    if source_error is None:
        command = [sys.executable, "-m", "experiments.budget_sizing_diagnostic", "controller",
                   "--attempt", str(target)]
        base.save_new(target / "supervisor_launch.json", {"command": command,
                                                            "hard_seconds": CONTROLLER_CAP_SECONDS})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        try:
            with (target / "controller_stdout.txt").open("xb") as out, \
                    (target / "controller_stderr.txt").open("xb") as err:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                child_rc, timed_out, quiescent = base.wait_process_group(process, CONTROLLER_CAP_SECONDS)
        except Exception as exc:
            launch_error, child_rc = repr(exc), 1
    else:
        base.save_new(target / "supervisor_launch.json", {"command": None,
                                                            "blocked_before_child": True})
    try:
        unchanged = source_hashes() == json.loads((target / "frozen.json").read_text())["source_hashes"]
    except Exception as exc:
        unchanged, source_error = False, repr(exc)
    if quiescent and (timed_out or child_rc != 0 or source_error or launch_error):
        reconcile_partial(target)
    rc = 124 if timed_out else 1 if source_error or not unchanged or launch_error or not quiescent else child_rc or 0
    base.save_new(target / "supervisor_receipt.json", {"protocol": PROTOCOL,
                                                        "child_returncode": child_rc,
                                                        "returncode": rc, "hard_timeout": timed_out,
                                                        "process_group_quiescent": quiescent,
                                                        "stable_seal": quiescent,
                                                        "source_hashes_unchanged": unchanged,
                                                        "source_check_error": source_error,
                                                        "launch_error": launch_error,
                                                        "elapsed_seconds": time.monotonic() - started})
    if quiescent:
        files = {str(p.relative_to(target)): {"bytes": p.stat().st_size, "sha256": base.sha(p)}
                 for p in sorted(target.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
        base.save_new(target / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "supervise", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--state", type=int, choices=(0, 1))
    parser.add_argument("--calls", type=int, choices=CALLS)
    parser.add_argument("--bits", type=int, choices=BITS)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), indent=2, sort_keys=True))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt)
        return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": software_runtime(), "host": host_environment(),
                          "native_probe": native_probe()}, sort_keys=True))
        return 0
    if args.mode == "supervise":
        return supervise(args.attempt)
    if args.mode == "controller":
        return controller(args.attempt)
    if args.state is None or args.calls is None or args.bits is None:
        parser.error("worker requires --state, --calls and --bits")
    return worker(args.attempt, args.state, args.calls, args.bits)


if __name__ == "__main__":
    raise SystemExit(main())
