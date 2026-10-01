"""Prospective, development-only 16-call compact pricing-start diagnostic."""
from __future__ import annotations

import argparse
from dataclasses import asdict
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

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import computational_benchmark as base
from experiments import solver_baseline_comparison as comparison

ROOT = base.ROOT
ATTEMPT = ROOT / "result/pricing_start_pilot/20260928-attempt1"
INVENTORY = ROOT / "research-20260928/pricing-start/SOURCE_INVENTORY.json"
PROTOCOL = "egg-pricing-start-development-20260928-v1"
SOURCE_COMMIT = "f4b342dc85799d01d9313baeaf8c9ec527759d59"
CASES = base.CASES
QUERIES = ("linear_tariff", "marginal_price")
ARMS = ("cold", "start")
CONTROLLER_CAP = 2700
SOURCE_FILES = ("raw_result.json", "receipt.json", "result.json", "events.jsonl")
SOURCES = (
    "src/experiments/pricing_start_pilot.py",
    "src/tests/test_pricing_start_pilot.py",
    "src/cluster/pricing_start_pilot.sbatch",
    "research-20260928/agent-notes/pricing-start-runner/IMPLEMENTATION.md",
    "research-20260928/pricing-start/SOURCE_INVENTORY.json",
    "doc/PRICING_START_PILOT_PROTOCOL_20260928.md",
    "src/egglab/native_pathflow.py", "src/egglab/native_recharge.py",
    "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/solver_baseline_comparison.py",
    "src/cluster/unicorn_env.sh", *base.SOURCES,
)


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the exclusive prospective pricing-start attempt is allowed")
    return target


def source_hashes():
    return {name: base.sha(ROOT / name) for name in dict.fromkeys(SOURCES)}


def runtime():
    import gurobipy
    return {"python_version": platform.python_version(),
            "mip": importlib.metadata.version("mip"),
            "gurobipy": importlib.metadata.version("gurobipy"),
            "scipy": importlib.metadata.version("scipy"),
            "numpy": importlib.metadata.version("numpy"),
            "gurobi_runtime": ".".join(map(str, gurobipy.gurobi.version()))}


def native_probe():
    """Observe the effective backend and default seed without optimizing."""
    import mip
    model = mip.Model(name="pricing-start-preflight", sense=mip.MINIMIZE, solver_name="GRB")
    identity = nr._backend_identity(model, "GRB")
    seed = model.seed
    if type(seed) is not int:
        raise ValueError("Native model seed is not an integer")
    return {"backend_identity": identity, "model_seed": seed}


def budget(case_name):
    cfg = base.budget(case_name, "cold_hull")
    return nr.Budget(backend="GRB", threads=1, phase_seconds=cfg.phase_seconds,
                     wall_seconds=cfg.wall_seconds, max_rounds=1, epsilon=cfg.epsilon)


def arm_order(case_index, query_index):
    return ARMS if (case_index + query_index) % 2 == 0 else ARMS[::-1]


def _inventory():
    inventory = json.loads(INVENTORY.read_text())
    if (inventory.get("source_commit") != SOURCE_COMMIT
            or inventory.get("sealed_attempt") != "solver_baseline_comparison/20260928-attempt1"
            or [row.get("case") for row in inventory.get("sources", [])] != list(CASES)):
        raise ValueError("Source inventory identity or order changed")
    return inventory


def _source_file_hashes(folder):
    return {name: {"sha256": base.sha(folder / name), "bytes": (folder / name).stat().st_size}
            for name in SOURCE_FILES}


def _source_case(source_root, inventory_row, case_name, case):
    """Admit only the pinned physical pool; historical bound events are not reused."""
    started = time.monotonic()
    try:
        expected_rel = f"{case_name}/state0/qp_cache_feasible_hull"
        if inventory_row.get("case") != case_name or inventory_row.get("source_relative_path") != expected_rel:
            raise ValueError("Source path/case differs from inventory")
        folder = Path(source_root) / expected_rel
        files = _source_file_hashes(folder)
        if (files["raw_result.json"]["sha256"] != inventory_row["raw_sha256"]
                or files["receipt.json"]["sha256"] != inventory_row["receipt_sha256"]):
            raise ValueError("Pinned source raw/receipt hash differs")
        receipt = json.loads((folder / "receipt.json").read_text())
        cfg = base.budget(case_name, "cold_hull")
        paid = receipt.get("elapsed_seconds")
        if (receipt.get("returncode") != 0 or receipt.get("on_time") is not True
                or receipt.get("hard_timeout") is not False
                or receipt.get("hard_seconds") != cfg.wall_seconds + 30
                or type(paid) not in (int, float) or not math.isfinite(paid)
                or not 0 <= paid <= receipt["hard_seconds"]
                or paid != inventory_row.get("source_child_elapsed_seconds")):
            raise ValueError("Source child status or paid time is ineligible")
        wrapped = json.loads((folder / "raw_result.json").read_text())
        if (wrapped.get("case"), wrapped.get("state"), wrapped.get("stage")) != (
                case_name, 0, "qp_cache_feasible_hull"):
            raise ValueError("Source wrapper identity differs")
        prior = wrapped["result"]
        original_market = base.market(case_name, 0)
        identity = compact.state_identity(case, original_market, "retained", 0, cfg,
                                           **comparison.controls("qp_cache_feasible_hull"))
        if (prior.get("schema") != nh.SCHEMA or prior.get("status") != inventory_row.get("status")
                or prior.get("status") not in ("certified", "bounded", "budget_exhausted", "stalled_bounded")
                or prior.get("state_index") != 0 or prior.get("arm") != "retained"
                or prior.get("state_identity") != identity
                or identity != inventory_row.get("source_state_identity")
                or prior.get("physical_identity") != case.identity()
                or prior.get("market_identity") != original_market.identity()
                or prior.get("pricing_oracle") != compact.ORACLE_ID
                or prior.get("extraction_policy") != compact.EXTRACTION_POLICY
                or any(prior.get(k) != v for k, v in comparison.controls("qp_cache_feasible_hull").items())):
            raise ValueError("Source status, identity or policy differs")
        columns = prior.get("columns")
        if (not isinstance(columns, list) or len(columns) != inventory_row.get("columns")
                or not 1 <= len(columns) <= cfg.pool_cap
                or len({c["key"] for c in columns}) != len(columns)):
            raise ValueError("Source pool count/keys differ")
        for col in columns:
            if (col.get("source", {}).get("state_identity") != identity
                    or col.get("source", {}).get("pricing_oracle") != compact.ORACLE_ID):
                raise ValueError("Source column provenance differs")
            nh.replay_column(case, col, compact.EXTRACTION_POLICY)
            pf._checked_pricing_start(case, col["plan"])
        return {"eligible": True, "reason": None, "source_files": files,
                "source_state_identity": identity, "source_status": prior["status"],
                "source_child_elapsed_seconds": paid, "columns": columns,
                "preparation_elapsed_seconds": time.monotonic() - started}
    except (OSError, ValueError, KeyError, TypeError, IndexError, ArithmeticError, AttributeError) as exc:
        return {"eligible": False, "reason": f"{type(exc).__name__}: {exc}",
                "source_child_elapsed_seconds": inventory_row.get("source_child_elapsed_seconds"),
                "source_status": inventory_row.get("status"),
                "preparation_elapsed_seconds": time.monotonic() - started}


def _bill(column, prices):
    return Fraction(column["ops_cost"]) + sum(
        (Fraction(p) * Fraction(load) for p, load in zip(prices, column["load"])), Fraction(0))


def _choose(columns, prices):
    return min(columns, key=lambda c: (_bill(c, prices), c["key"]))


def _queries(case_name, columns):
    market = base.market(case_name, 1)
    linear_exact = [str(Fraction(a)) for a in market.a]
    linear = [float(Fraction(a)) for a in market.a]
    anchor = _choose(columns, linear)
    marginal_fractions = [Fraction(a) + Fraction(b) * Fraction(load)
                          for a, b, load in zip(market.a, market.b, anchor["load"])]
    marginal = [float(p) for p in marginal_fractions]
    output = {}
    for name, prices, exact in ((QUERIES[0], linear, linear_exact),
                                (QUERIES[1], marginal, [str(p) for p in marginal_fractions])):
        chosen = _choose(columns, prices)
        output[name] = {"prices": prices, "prices_exact": exact,
                        "source_plan": chosen["plan"], "source_plan_hash": nr.digest(chosen["plan"]),
                        "source_column_key": chosen["key"], "source_load": chosen["load"],
                        "source_ops_cost": chosen["ops_cost"],
                        "source_pricing_objective_exact": str(_bill(chosen, prices)),
                        "source_pricing_objective": float(_bill(chosen, prices)),
                        "selected_movement_count": sum(len(v["movements"]) for v in chosen["plan"]["vehicles"]),
                        "physical_identity": chosen["physical_identity"],
                        "gradient_anchor_key": anchor["key"] if name == QUERIES[1] else None}
    output[QUERIES[1]]["duplicates_linear_prices"] = marginal == linear
    return output


def _prepared_case(source_root, inventory_row, case_name, case):
    admitted = _source_case(source_root, inventory_row, case_name, case)
    columns = admitted.pop("columns", None)
    queries = _queries(case_name, columns) if admitted["eligible"] else None
    return {"case_identity": case.identity(), "market_identity": base.market(case_name, 1).identity(),
            "base_timetable_group": "hildenbrand_37" if case_name.startswith("public_") else case_name,
            "budget": asdict(budget(case_name)), "hard_child_seconds": budget(case_name).wall_seconds + 30,
            "source": admitted, "queries": queries}


def freeze(path, source_root):
    preparation_started = time.monotonic()
    target = _attempt(path)
    if target.exists():
        raise FileExistsError(target)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    source_root = Path(source_root).resolve(strict=True)
    source_freeze = json.loads((source_root / "frozen.json").read_text())
    if source_freeze.get("source_commit") != SOURCE_COMMIT:
        raise ValueError("Sealed predecessor commit differs")
    inventory = _inventory()
    built = base.cases()
    cases = {name: _prepared_case(source_root, row, name, built[name])
             for name, row in zip(CASES, inventory["sources"])}
    env = runtime()
    if not all(env.get(k) for k in ("mip", "gurobipy", "scipy", "numpy", "gurobi_runtime")):
        raise ValueError("Native runtime/version unavailable")
    probe = native_probe()
    spec = {"protocol": PROTOCOL, "source_commit": commit, "source_hashes": source_hashes(),
            "source_root": str(source_root), "source_root_frozen_sha256": base.sha(source_root / "frozen.json"),
            "source_inventory_sha256": base.sha(INVENTORY), "source_execution_commit": SOURCE_COMMIT,
            "environment": env, "native_probe": probe,
            "cases": cases, "case_order": list(CASES), "query_order": list(QUERIES),
            "arm_orders": {name: {query: list(arm_order(i, j)) for j, query in enumerate(QUERIES)}
                           for i, name in enumerate(CASES)},
            "controller_cap_seconds": CONTROLLER_CAP, "backend": "GRB", "threads": 1,
            "all_development": True, "scientific_admission": "pending independent result review",
            "freeze_preparation_elapsed_seconds": time.monotonic() - preparation_started,
            "freeze_actual_environment": {**env, "platform": platform.platform(),
                                          "hostname": platform.node()}}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path, *, check_sources=True):
    target = _attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or spec.get("environment") != runtime()
            or spec.get("source_inventory_sha256") != base.sha(INVENTORY)
            or spec.get("source_root_frozen_sha256") != base.sha(Path(spec["source_root"]) / "frozen.json")
            or spec.get("case_order") != list(CASES) or spec.get("query_order") != list(QUERIES)
            or spec.get("controller_cap_seconds") != CONTROLLER_CAP):
        raise ValueError("Frozen source/runtime/input differs")
    if check_sources and spec.get("native_probe") != native_probe():
        raise ValueError("Frozen native backend/seed differs")
    expected_orders = {name: {query: list(arm_order(i, j)) for j, query in enumerate(QUERIES)}
                       for i, name in enumerate(CASES)}
    if spec.get("arm_orders") != expected_orders or spec.get("backend") != "GRB" or spec.get("threads") != 1:
        raise ValueError("Frozen arms/backend/threads differ")
    for name, case in base.cases().items():
        row = spec["cases"][name]
        if (row["case_identity"] != case.identity()
                or row["market_identity"] != base.market(name, 1).identity()
                or row["budget"] != asdict(budget(name))):
            raise ValueError("Frozen case/market/budget differs")
        if check_sources:
            current = _prepared_case(spec["source_root"], next(r for r in _inventory()["sources"] if r["case"] == name), name, case)
            current["source"].pop("preparation_elapsed_seconds", None)
            saved = json.loads(json.dumps(row))
            saved["source"].pop("preparation_elapsed_seconds", None)
            if base.canonical(current) != base.canonical(saved):
                raise ValueError("Frozen source admission/selection differs")
    return spec


def cell_dir(path, case_name, query, arm):
    return Path(path) / case_name / query / arm


def read_worker_evidence(folder):
    """Retain a valid event prefix and setup failures without inferring acceptance."""
    folder = Path(folder)
    events, issues = [], []
    path = folder / "events.jsonl"
    if path.exists():
        try:
            lines = path.read_bytes().splitlines()
        except OSError as exc:
            lines = []
            issues.append({"file": "events.jsonl", "error": repr(exc)})
        allowed = {"native_start", "native_status", "native_incumbent", "charge_normalization",
                   "charge_projection", "serial_decoding", "objective_reconstruction",
                   "replayed_iteration", "mip_start_setup"}
        for index, line in enumerate(lines):
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or event.get("event") not in allowed:
                    raise ValueError("Unknown native event")
                if event["event"] == "mip_start_setup":
                    if (event.get("status") not in ("submitted", "rejected", "timed_out")
                            or type(event.get("setup_elapsed_s")) not in (int, float)
                            or not math.isfinite(event["setup_elapsed_s"])
                            or event["setup_elapsed_s"] < 0 or not isinstance(event.get("timings"), dict)):
                        raise ValueError("Malformed MIP start setup event")
                elif type(event.get("round")) is not int or event["round"] < 0:
                    raise ValueError("Malformed native round")
                if event["event"] == "native_status" and (not isinstance(event.get("stats"), dict)
                        or type(event["stats"].get("wall_s")) not in (int, float)):
                    raise ValueError("Malformed native status timing")
                events.append(event)
            except (ValueError, TypeError, UnicodeError) as exc:
                issues.append({"file": "events.jsonl", "line": index + 1,
                               "error": repr(exc), "valid_prefix_events": len(events)})
                break
    return events, issues


def _assessment(case, prices, result, known_upper):
    if (result.get("case_identity") != case.identity() or result.get("prices") != prices
            or result.get("formulation") != pf.FORMULATION
            or result.get("native_matrix") != pf.NATIVE_MATRIX
            or result.get("extraction_policy") != pf.EXTRACTION_POLICY):
        raise ValueError("Native result identity/price differs")
    plan = result.get("plan")
    replay = nr.replay_native(case, plan, prices) if plan is not None else None
    lower, upper = result.get("lower"), result.get("upper")
    if replay is not None:
        admitted = nr.admit_bound(result["stats"], replay["pricing_objective"])
        if [lower, upper] != list(admitted):
            raise ValueError("Native interval differs from replayed bound admission")
    elif lower is not None or upper is not None:
        raise ValueError("No-plan raw bound cannot become admitted interval")
    return {"native_status": result.get("status"), "raw_native_stats": result.get("stats"),
            "returned_plan": plan is not None, "native_replayed_objective":
            replay["pricing_objective"] if replay else None,
            "native_admitted_interval": [lower, upper] if replay else None,
            "known_source_upper": known_upper,
            "best_feasible_upper": min(known_upper, replay["pricing_objective"]) if replay else known_upper,
            "plan_hash": nr.digest(plan) if plan else None}


def worker(path, case_name, query, arm):
    target = _attempt(path)
    folder = cell_dir(target, case_name, query, arm)
    started = time.monotonic()
    call_started = None
    try:
        spec = frozen(target, check_sources=False)
        row = spec["cases"][case_name]
        if (not (folder / "launch.json").is_file() or not row["source"]["eligible"]
                or query not in QUERIES or arm not in ARMS):
            raise ValueError("Child launch/source declaration missing")
        selected = row["queries"][query]
        case = base.cases()[case_name]
        if (selected["physical_identity"] != case.identity()
                or selected["source_plan_hash"] != nr.digest(selected["source_plan"])):
            raise ValueError("Frozen selected plan differs")
        def record(event):
            with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        call_started = time.monotonic()
        result = pf.solve_pricing(case, selected["prices"], budget(case_name),
                                  record=record, start_plan=selected["source_plan"] if arm == "start" else None)
        core_call_elapsed = time.monotonic() - call_started
        base.save_new(folder / "raw_result.json", result)
        assessment = _assessment(case, selected["prices"], result, selected["source_pricing_objective"])
        base.save_new(folder / "result.json", {"assessment": assessment,
                      "child_work_elapsed_seconds": time.monotonic() - started,
                      "core_call_elapsed_seconds": core_call_elapsed,
                      "actual_environment": {**runtime(), "platform": platform.platform(),
                                             "hostname": platform.node()}})
        return 0
    except Exception as exc:
        base.save_new(folder / "exception.json", {"type": type(exc).__name__,
                      "message": str(exc), "traceback": traceback.format_exc(),
                      "child_work_elapsed_seconds": time.monotonic() - started,
                      "core_call_elapsed_seconds": time.monotonic() - call_started if call_started is not None else None,
                      "actual_environment": {**runtime(), "platform": platform.platform(),
                                             "hostname": platform.node()}})
        return 2


def result_row(path, case_name, query, arm, receipt, selected, expected_probe=None):
    folder = cell_dir(path, case_name, query, arm)
    events, issues = read_worker_evidence(folder)
    setups = [e for e in events if e["event"] == "mip_start_setup"]
    starts = [e for e in events if e["event"] == "native_start"]
    statuses = [e for e in events if e["event"] == "native_status"]
    row = {"case": case_name, "query": query, "arm": arm,
           "status": "hard_timeout" if receipt["hard_timeout"] else
                     "failed" if receipt["returncode"] != 0 else "returned",
           "receipt": receipt, "evidence_issues": issues,
           "native_start_events": len(starts), "native_status_events": len(statuses),
           "start_requested": arm == "start", "start_setup_events": setups,
           "start_submitted": any(e["status"] == "submitted" for e in setups),
           "native_acceptance": "unknown", "selected_movement_count": selected["selected_movement_count"],
           "known_source_upper": selected["source_pricing_objective"],
           "raw_native_status_events": statuses,
           "native_seed": starts[0].get("model_seed") if len(starts) == 1 else None,
           "backend_runtime": starts[0].get("backend_runtime") if len(starts) == 1 else None}
    if receipt["returncode"] == 0 and not receipt["hard_timeout"]:
        if (len(starts) != 1 or len(statuses) != 1
                or (arm == "start" and (len(setups) != 1 or setups[0]["status"] != "submitted"))
                or (arm == "cold" and setups) or issues):
            row["evidence_issues"].append({"error": "Complete returned call has incomplete or inconsistent native events"})
            row["status"] = "evidence_mismatch"
    if expected_probe is not None and starts:
        if (len(starts) != 1 or starts[0].get("model_seed") != expected_probe["model_seed"]
                or starts[0].get("backend_runtime") != expected_probe["backend_identity"]
                or starts[0].get("backend") != "GRB"):
            row["evidence_issues"].append({"error": "Native backend or seed differs from preflight"})
            row["status"] = "evidence_mismatch"
    result_path = folder / "result.json"
    if result_path.exists():
        try:
            result = json.loads(result_path.read_text())
            row.update(result["assessment"])
            row["child_work_elapsed_seconds"] = result["child_work_elapsed_seconds"]
            row["core_call_elapsed_seconds"] = result["core_call_elapsed_seconds"]
            row["actual_environment"] = result["actual_environment"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row["result_read_error"] = repr(exc)
    exception_path = folder / "exception.json"
    if exception_path.exists():
        try:
            error = json.loads(exception_path.read_text())
            row["exception"] = {k: error.get(k) for k in ("type", "message")}
            row["core_call_elapsed_seconds"] = error.get("core_call_elapsed_seconds")
            row["child_work_elapsed_seconds"] = error.get("child_work_elapsed_seconds")
            row["actual_environment"] = error.get("actual_environment")
        except (OSError, ValueError, TypeError) as exc:
            row["exception_read_error"] = repr(exc)
    row["native_optimization_seconds"] = (statuses[0]["stats"].get("wall_s")
                                           if len(statuses) == 1 else None)
    return row


def launch_child(path, case_name, query, arm, hard_seconds, command):
    """One child process/model and one receipt, with no retry or replacement arm."""
    folder = cell_dir(path, case_name, query, arm)
    base.save_new(folder / "launch.json", {"command": command, "hard_seconds": hard_seconds,
                  "started_utc": time.time()})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started, rc, timed_out, error = time.monotonic(), None, False, None
    try:
        with (folder / "stdout.txt").open("xb") as out, (folder / "stderr.txt").open("xb") as err:
            # The child shares the controller process group, so controller expiry
            # also stops any in-flight native solve.
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err)
            try:
                rc = process.wait(timeout=hard_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                for stop, grace in ((process.terminate, 10), (process.kill, 2)):
                    if process.poll() is not None:
                        break
                    stop()
                    try:
                        rc = process.wait(timeout=grace)
                        break
                    except subprocess.TimeoutExpired:
                        continue
                if rc is None:
                    rc = process.wait()
    except Exception as exc:
        error, rc = repr(exc), 1
    elapsed = time.monotonic() - started
    receipt = {"returncode": rc, "hard_timeout": timed_out, "error": error,
               "elapsed_seconds": elapsed, "hard_seconds": hard_seconds,
               "on_time": not timed_out and rc == 0 and elapsed <= hard_seconds}
    base.save_new(folder / "receipt.json", receipt)
    return receipt


def controller(path):
    target = _attempt(path)
    spec = frozen(target)
    base.save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    for name in CASES:
        case_row = spec["cases"][name]
        for query in QUERIES:
            for arm in spec["arm_orders"][name][query]:
                if not case_row["source"]["eligible"]:
                    rows.append({"case": name, "query": query, "arm": arm, "status": "ineligible",
                                 "reason": case_row["source"]["reason"], "start_requested": arm == "start",
                                 "source_child_elapsed_seconds": case_row["source"]["source_child_elapsed_seconds"]})
                    continue
                selected = case_row["queries"][query]
                command = [sys.executable, "-m", "experiments.pricing_start_pilot", "worker",
                           "--attempt", str(target), "--case", name, "--query", query, "--arm", arm]
                receipt = launch_child(target, name, query, arm,
                                       case_row["hard_child_seconds"], command)
                rows.append(result_row(target, name, query, arm, receipt, selected,
                                       spec["native_probe"]))
    online = sum(r.get("receipt", {}).get("elapsed_seconds", 0) for r in rows)
    historic = sum(spec["cases"][name]["source"]["source_child_elapsed_seconds"] or 0
                   for name in CASES)
    preparation = spec["freeze_preparation_elapsed_seconds"]
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                  "all_declared_calls_accounted": len(rows) == 16,
                  "source_cost_by_case": {name: {"historical_once_seconds": spec["cases"][name]["source"]["source_child_elapsed_seconds"],
                     "preparation_once_seconds": spec["cases"][name]["source"]["preparation_elapsed_seconds"]}
                     for name in CASES},
                  "conditional_online_child_seconds": online,
                  "historical_source_once_seconds": historic,
                  "freeze_preparation_once_seconds": preparation,
                  "source_inclusive_seconds": historic + preparation + online,
                  "scientific_admission": "pending independent result review"})
    return 0 if len(rows) == 16 and not any(r["status"] == "evidence_mismatch" for r in rows) else 2


def reconcile_partial(path):
    target = Path(path)
    rows = []
    spec = json.loads((target / "frozen.json").read_text())
    for name in CASES:
        for query in QUERIES:
            for arm in spec["arm_orders"][name][query]:
                folder = cell_dir(target, name, query, arm)
                selected = (spec["cases"][name]["queries"] or {}).get(query)
                if (folder / "receipt.json").exists():
                    try:
                        row = result_row(target, name, query, arm,
                                         json.loads((folder / "receipt.json").read_text()), selected,
                                         spec["native_probe"])
                    except Exception as exc:
                        row = {"case": name, "query": query, "arm": arm,
                               "status": "receipt_unreadable", "error": repr(exc)}
                else:
                    row = {"case": name, "query": query, "arm": arm,
                           "status": "ineligible" if not spec["cases"][name]["source"]["eligible"] else
                                     "interrupted_unreceipted" if (folder / "launch.json").exists() else "unstarted"}
                rows.append(row)
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
                  "scientific_admission": "none; abnormal controller termination"})


def seal_manifest(path):
    target = Path(path)
    files = {str(p.relative_to(target)): {"bytes": p.stat().st_size, "sha256": base.sha(p)}
             for p in sorted(target.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    base.save_new(target / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})


def supervise(path):
    target = _attempt(path)
    preflight_error = None
    try:
        frozen(target)
    except Exception as exc:
        preflight_error = repr(exc)
    command = ([sys.executable, "-m", "experiments.pricing_start_pilot", "controller",
                "--attempt", str(target)] if preflight_error is None else None)
    base.save_new(target / "supervisor_launch.json", {"command": command, "hard_seconds": CONTROLLER_CAP,
                  "blocked_before_child": preflight_error is not None})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started, rc, timeout, quiescent, error = time.monotonic(), None, False, True, None
    if command is not None:
        try:
            with (target / "controller_stdout.txt").open("xb") as out, (target / "controller_stderr.txt").open("xb") as err:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                rc, timeout, quiescent = base.wait_process_group(process, CONTROLLER_CAP)
        except Exception as exc:
            error, rc = repr(exc), 1
    input_check_error = None
    try:
        frozen(target)
    except Exception as exc:
        input_check_error = repr(exc)
    if quiescent and (timeout or rc != 0 or error or preflight_error or input_check_error):
        reconcile_partial(target)
    result = 124 if timeout else 1 if error or preflight_error or input_check_error or not quiescent else rc or 0
    base.save_new(target / "supervisor_receipt.json", {"protocol": PROTOCOL,
                  "child_returncode": rc, "returncode": result, "hard_timeout": timeout,
                  "process_group_quiescent": quiescent, "stable_seal": quiescent,
                  "source_and_inputs_unchanged": input_check_error is None,
                  "preflight_error": preflight_error, "input_check_error": input_check_error,
                  "launch_error": error,
                  "elapsed_seconds": time.monotonic() - started})
    if quiescent:
        seal_manifest(target)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "preflight", "supervise", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--query", choices=QUERIES)
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args(argv)
    if args.mode == "freeze":
        if args.source_root is None:
            parser.error("freeze requires --source-root")
        freeze(args.attempt, args.source_root)
        return 0
    if args.mode == "supervise":
        return supervise(args.attempt)
    if args.mode == "preflight":
        frozen(args.attempt)
        return 0
    if args.mode == "controller":
        return controller(args.attempt)
    if None in (args.case, args.query, args.arm):
        parser.error("worker requires --case, --query and --arm")
    return worker(args.attempt, args.case, args.query, args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
