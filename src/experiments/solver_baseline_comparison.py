"""Prospective, development-only ordered 32-cell hull solver comparison."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import computational_benchmark as base

ROOT = base.ROOT
ATTEMPT = ROOT / "result/solver_baseline_comparison/20260928-attempt1"
PROTOCOL = "egg-solver-baseline-comparison-development-20260928-v1"
ARMS = ("reserve_cold_hull", "reserve_feasible_hull", "qp_feasible_hull",
        "qp_cache_feasible_hull")
CASES = base.CASES
STATES = (0, 1)
TOTAL_CAP = 5400
SOURCES = (
    "src/experiments/solver_baseline_comparison.py",
    "src/tests/test_solver_baseline_comparison.py",
    "src/cluster/solver_baseline_comparison.sbatch",
    "doc/SOLVER_BASELINE_COMPARISON_PROTOCOL_20260928.md",
    "src/egglab/restricted_qp_proposal.py",
    "src/tests/test_native_hull_numerical_master.py",
    "src/tests/test_native_hull_pricing_cache.py",
    "src/tests/test_native_hull_feasible_reuse.py",
    *base.SOURCES,
)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in dict.fromkeys(SOURCES)}


def environment():
    import gurobipy
    return {**base.environment(), "numpy": importlib.metadata.version("numpy"),
            "gurobi_runtime": ".".join(str(x) for x in gurobipy.gurobi.version())}


def controls(arm):
    if arm not in ARMS:
        raise ValueError("Unknown comparison arm")
    result = {"reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10.0}
    if arm.startswith("qp_"):
        result.update(master_policy="numerical_qp_proposal", qp_denominator=1_000_000_000,
                      qp_maxiter=500)
    if arm == "qp_cache_feasible_hull":
        result["bound_cache_policy"] = "physical_pricing"
    return result


def hull_arm(arm):
    return "cold" if arm == ARMS[0] else "retained"


def design():
    built = base.cases()
    rows = {}
    for name in CASES:
        case, cfg = built[name], base.budget(name, "cold_hull")
        rows[name] = {
            "case": asdict(case), "case_identity": case.identity(),
            "base_timetable_group": "hildenbrand_37" if name.startswith("public_") else name,
            "development_only": True,
            "markets": [asdict(base.market(name, state)) for state in STATES],
            "market_identities": [base.market(name, state).identity() for state in STATES],
            "budget": asdict(cfg), "hard_child_seconds": cfg.wall_seconds + 30,
            "arms": {arm: {"hull_arm": hull_arm(arm), "controls": controls(arm)} for arm in ARMS},
        }
    return rows


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the exclusive prospective attempt is allowed")
    return target


def freeze(path):
    target = _attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    runtime = environment()
    if not all(runtime.get(name) for name in ("mip", "gurobipy", "scipy", "numpy")):
        raise ValueError("GRB native and SciPy runtimes are required")
    spec = {"protocol": PROTOCOL, "source_commit": commit, "source_hashes": source_hashes(),
            "environment": runtime, "cases": design(), "stage_order": list(ARMS),
            "within_arm_order": list(STATES), "controller_execution_cap_seconds": TOTAL_CAP,
            "backend": "GRB", "rng": "none",
            "split": "all development; Hildenbrand depots share one base timetable",
            "raw_provenance": "complete fleet columns; no independent route-level DW master"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = _attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or spec.get("environment") != environment()
            or base.canonical(spec.get("cases")) != base.canonical(design())
            or spec.get("stage_order") != list(ARMS)
            or spec.get("within_arm_order") != list(STATES)
            or spec.get("controller_execution_cap_seconds") != TOTAL_CAP):
        raise ValueError("Frozen source/design differs from current implementation")
    return spec


def cell_dir(path, case_name, state, arm):
    return Path(path) / case_name / ("state" + str(state)) / arm


SOURCE_FILES = ("raw_result.json", "result.json", "receipt.json", "events.jsonl")


def source_files(folder):
    return {name: {"sha256": base.sha(folder / name), "bytes": (folder / name).stat().st_size}
            for name in SOURCE_FILES}


def _cache_event_check(case, market, prior, events, identity, cfg):
    """Match every transferable native bound to its original event and projection."""
    records = prior.get("physical_pricing_evidence")
    if (not isinstance(records, list) or not records
            or prior.get("physical_pricing_evidence_digest") != nr.digest(records)
            or prior.get("source_pricing_call_cap") != cfg.pricing_calls):
        raise ValueError("Source cache evidence missing or changed")
    requests, results, bounds = {}, {}, {}
    for event in events:
        call = event.get("call")
        kind = event.get("event")
        store = ({"pricing_request": requests, "pricing_result": results,
                  "global_bound": bounds}.get(kind))
        if store is None:
            continue
        if type(call) is not int or call in store:
            raise ValueError("Duplicate or malformed source pricing event")
        store[call] = event
    if len(requests) != prior.get("counts", {}).get("pricing_requests"):
        raise ValueError("Source pricing requests/count differ")
    if len(records) != len(results) or set(results) != set(bounds):
        raise ValueError("Source pricing results/bounds/evidence differ")
    seen = set()
    for item in records:
        if (not isinstance(item, dict) or set(item) != {"record", "digest"}
                or item["digest"] != nr.digest(item["record"])):
            raise ValueError("Malformed source cache record")
        data = item["record"]
        call = data.get("pricing_call")
        if call in seen or call not in results or call not in requests:
            raise ValueError("Source cache call provenance differs")
        seen.add(call)
        raw, bound, request = results[call]["result"], bounds[call], requests[call]
        col = bound["column"]
        if (data.get("source_state_identity") != identity
                or data.get("source_market_identity") != market.identity()
                or data.get("physical_identity") != case.identity()
                or data.get("pricing_oracle") != compact.ORACLE_ID
                or data.get("extraction_policy") != compact.EXTRACTION_POLICY
                or data.get("prices") != request.get("prices")
                or raw.get("prices") != data["prices"]
                or raw.get("status") != data.get("native_result_status")
                or raw.get("case_identity") != case.identity()
                or raw.get("formulation") != compact.ORACLE_ID
                or raw.get("extraction_policy") != compact.EXTRACTION_POLICY
                or raw.get("plan") != col.get("plan")
                or raw.get("lower") != data.get("pricing_lower")
                or raw.get("upper") != data.get("pricing_upper")
                or data.get("load") != col.get("load")
                or data.get("ops_cost") != col.get("ops_cost")
                or data.get("column_key") != col.get("key")
                or data.get("witness_hash") != col.get("witness_hash")
                or col.get("source", {}).get("state_identity") != identity
                or col.get("source", {}).get("pricing_call") != call
                or col.get("source", {}).get("pricing_oracle") != compact.ORACLE_ID):
            raise ValueError("Source cache event/result/projection differs")
        nh.replay_column(case, col, compact.EXTRACTION_POLICY)
        objective = col["ops_cost"] + sum(p*e for p, e in zip(data["prices"], col["load"]))
        stats = {key: raw["stats"].get(key) for key in
                 ("status", "incumbent", "lower_bound", "wall_s", "backend", "threads")}
        lower, upper = nr.admit_bound(raw["stats"], objective)
        if (data.get("pricing_objective") != objective or data.get("native_stats") != stats
                or data.get("pricing_lower") != lower or data.get("pricing_upper") != upper
                or bound.get("certificate") != nh.fenchel_bound(market, data["prices"], lower)):
            raise ValueError("Source cache native bound differs")
    if seen != set(results):
        raise ValueError("Source cache omits a completed pricing call")


def predecessor(path, case_name, arm, pinned_files=None):
    """Admit only an on-time, complete, replayable own state-0 source."""
    if arm == ARMS[0]:
        raise ValueError("Cold arm has no predecessor")
    folder = cell_dir(path, case_name, 0, arm)
    if pinned_files is not None and source_files(folder) != pinned_files:
        raise ValueError("Source files differ from parent admission receipt")
    receipt = json.loads((folder / "receipt.json").read_text())
    cfg = base.budget(case_name, "cold_hull")
    if (receipt.get("returncode") != 0 or receipt.get("hard_timeout") is not False
            or receipt.get("on_time") is not True
            or type(receipt.get("elapsed_seconds")) not in (int, float)
            or receipt.get("hard_seconds") != cfg.wall_seconds + 30
            or not 0 <= receipt["elapsed_seconds"] <= receipt["hard_seconds"]):
        raise ValueError("Source child was not complete and on time")
    wrapped = json.loads((folder / "raw_result.json").read_text())
    if (wrapped.get("case"), wrapped.get("state"), wrapped.get("stage")) != (case_name, 0, arm):
        raise ValueError("Source raw wrapper identity differs")
    prior = wrapped["result"]
    case, market = base.cases()[case_name], base.market(case_name, 0)
    identity = compact.state_identity(case, market, "retained", 0, cfg, **controls(arm))
    if (prior.get("schema") != nh.SCHEMA or prior.get("status") not in
            ("certified", "budget_exhausted", "stalled_bounded", "bounded")
            or prior.get("arm") != "retained" or prior.get("state_index") != 0
            or prior.get("state_identity") != identity
            or prior.get("physical_identity") != case.identity()
            or prior.get("market_identity") != market.identity()
            or prior.get("pricing_oracle") != compact.ORACLE_ID
            or prior.get("extraction_policy") != compact.EXTRACTION_POLICY
            or any(prior.get(key) != value for key, value in controls(arm).items())):
        raise ValueError("Source status/identity/policy differs")
    columns = prior.get("columns", [])
    if not 1 <= len(columns) <= cfg.pool_cap or len({c["key"] for c in columns}) != len(columns):
        raise ValueError("Source pool is empty, oversized or duplicated")
    for col in columns:
        source = col.get("source")
        if (not isinstance(source, dict) or source.get("state_identity") != identity
                or source.get("pricing_oracle") != compact.ORACLE_ID):
            raise ValueError("Source column provenance differs")
        nh.replay_column(case, col, compact.EXTRACTION_POLICY)
    reviewed = json.loads((folder / "result.json").read_text())
    assessment = reviewed["assessment"]
    if ((reviewed.get("case"), reviewed.get("state"), reviewed.get("stage")) != (case_name, 0, arm)
            or assessment.get("status") != prior["status"]
            or assessment.get("complete_evidence") is not True or not assessment.get("bounds")
            or not prior.get("lower_certificate") or not prior.get("mixture")):
        raise ValueError("Source assessment differs")
    if base.assess(case, market, arm, prior) != assessment:
        raise ValueError("Source certificate/mixture failed replay")
    if arm == "qp_cache_feasible_hull":
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
        _cache_event_check(case, market, prior, events, identity, cfg)
    return prior, identity


def admission(path, case_name, arm):
    started = time.monotonic()
    folder = cell_dir(path, case_name, 0, arm)
    try:
        prior, identity = predecessor(path, case_name, arm)
        files = source_files(folder)
        return {"eligible": True, "reason": None, "source_state_identity": identity,
                "source_files": files, "source_child_elapsed_seconds":
                json.loads((folder / "receipt.json").read_text())["elapsed_seconds"],
                "parent_check_elapsed_seconds": time.monotonic()-started}
    except (OSError, ValueError, KeyError, TypeError, IndexError, ArithmeticError, AttributeError) as exc:
        return {"eligible": False, "reason": str(exc), "source_files": None,
                "parent_check_elapsed_seconds": time.monotonic()-started}


def worker(path, case_name, state, arm):
    target = _attempt(path)
    folder = cell_dir(target, case_name, state, arm)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if not (folder / "launch.json").is_file():
            raise ValueError("Child launch receipt missing")
        case, market = base.cases()[case_name], base.market(case_name, state)
        cfg = base.budget(case_name, "cold_hull")
        expected = spec["cases"][case_name]
        if (expected["case_identity"] != case.identity()
                or expected["market_identities"][state] != market.identity()
                or expected["budget"] != asdict(cfg)
                or expected["arms"][arm] != {"hull_arm": hull_arm(arm), "controls": controls(arm)}):
            raise ValueError("Child differs from frozen cell")
        previous = identity = None
        verification_seconds = None
        if state == 1 and arm != ARMS[0]:
            checked = time.monotonic()
            admitted = json.loads((folder / "admission.json").read_text())
            if admitted.get("eligible") is not True or not isinstance(admitted.get("source_files"), dict):
                raise ValueError("Parent source admission missing")
            previous, identity = predecessor(target, case_name, arm, admitted["source_files"])
            if identity != admitted.get("source_state_identity"):
                raise ValueError("Parent source identity differs")
            verification_seconds = time.monotonic()-checked
            base.save_new(folder / "child_source_check.json", {"source_state_identity": identity,
                          "source_files": admitted["source_files"],
                          "elapsed_seconds": verification_seconds})
        def record(event):
            with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        extra = controls(arm)
        if arm == "qp_cache_feasible_hull" and state == 1:
            extra = {**extra, "cached_from": previous, "expected_cached_state": identity}
        result = compact.certify(case, market, cfg, arm=hull_arm(arm), state_index=state,
                                 previous=previous, expected_previous=identity, record=record, **extra)
        state_identity = compact.state_identity(case, market, hull_arm(arm), state, cfg,
                       **controls(arm), **({"expected_cached_state": identity}
                                          if arm == "qp_cache_feasible_hull" and state == 1 else {}))
        if (result.get("state_identity") != state_identity or result.get("arm") != hull_arm(arm)
                or result.get("state_index") != state or result.get("physical_identity") != case.identity()
                or result.get("market_identity") != market.identity()
                or any(result.get(key) != value for key, value in controls(arm).items())
                or (arm == "qp_cache_feasible_hull" and state == 1
                    and result.get("cache_source_state_identity") != identity)):
            raise ValueError("Native result differs from frozen state and controls")
        base.save_new(folder / "raw_result.json", {"result": result, "case": case_name,
                                                   "state": state, "stage": arm})
        assessment = base.assess(case, market, arm, result)
        base.save_new(folder / "result.json", {"assessment": assessment,
                         "elapsed_seconds": time.monotonic()-started,
                         "child_predecessor_verification_seconds": verification_seconds,
                         "case": case_name, "state": state, "stage": arm})
        return 0
    except Exception as exc:
        base.save_new(folder / "exception.json", {"type": type(exc).__name__,
                      "message": str(exc), "traceback": traceback.format_exc(),
                      "elapsed_seconds": time.monotonic()-started})
        return 2


def launch_child(path, case_name, state, arm, hard_seconds):
    command = [sys.executable, "-m", "experiments.solver_baseline_comparison", "worker",
               "--attempt", str(path), "--case", case_name, "--state", str(state), "--arm", arm]
    return base.launch_child(path, case_name, state, arm, hard_seconds, command)


def paid_pairs(rows):
    """Receipt wall plus one parent admission; absent components stay unknown."""
    indexed = {(row["case"], row["stage"], row["state"]): row for row in rows}
    pairs = []
    for case_name in CASES:
        for arm in ARMS:
            first, second = (indexed.get((case_name, arm, state)) for state in STATES)
            first_s = first.get("receipt", {}).get("elapsed_seconds") if first else None
            second_s = second.get("receipt", {}).get("elapsed_seconds") if second else None
            admission_s = (second.get("admission", {}).get("parent_check_elapsed_seconds")
                           if second and arm != ARMS[0] else None)
            known = (type(first_s) in (int, float) and type(second_s) in (int, float)
                     and (arm == ARMS[0] or type(admission_s) in (int, float)))
            pairs.append({"case": case_name, "arm": arm,
                          "state0_child_elapsed_seconds": first_s,
                          "state1_child_elapsed_seconds": second_s,
                          "parent_admission_elapsed_seconds": admission_s,
                          "complete_two_state_paid_seconds":
                          first_s + second_s + (admission_s if arm != ARMS[0] else 0)
                          if known else None})
    return pairs


def controller(path):
    target = _attempt(path)
    spec = frozen(target)
    started = time.monotonic()
    base.save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    built = base.cases()
    for case_name in CASES:
        for arm in ARMS:
            for state in STATES:
                state_dir = target / case_name / ("state" + str(state))
                feature_file = state_dir / "features.json"
                if not feature_file.exists():
                    base.save_new(feature_file, base.features(built[case_name], base.market(case_name, state)))
                folder = cell_dir(target, case_name, state, arm)
                if state == 1 and arm != ARMS[0]:
                    checked = admission(target, case_name, arm)
                    base.save_new(folder / "admission.json", checked)
                    if not checked["eligible"]:
                        rows.append({"case": case_name, "state": state, "stage": arm,
                                     "status": "ineligible", "complete_evidence": False,
                                     "admission": checked})
                        continue
                receipt = launch_child(target, case_name, state, arm,
                                       spec["cases"][case_name]["hard_child_seconds"])
                row = base.result_row(target, case_name, state, arm, receipt)
                if state == 1 and arm != ARMS[0]:
                    row["admission"] = checked
                rows.append(row)
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                  "paid_pairs": paid_pairs(rows), "controller_elapsed_seconds": time.monotonic()-started,
                  "all_declared_cells_accounted": len(rows) == 32,
                  "scientific_admission": "pending independent result review",
                  "hull_columns_are_complete_fleets": True})
    return 0 if len(rows) == 32 else 2


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if len(json.loads((target / "summary.json").read_text())["rows"]) == 32:
                return None
        except (ValueError, KeyError, TypeError):
            pass
    rows = []
    for case_name in CASES:
        for arm in ARMS:
            for state in STATES:
                folder = cell_dir(target, case_name, state, arm)
                entry = {"case": case_name, "state": state, "stage": arm, "complete_evidence": False}
                admitted, admission_error = None, None
                if (folder / "admission.json").is_file():
                    try:
                        admitted = json.loads((folder / "admission.json").read_text())
                        if not isinstance(admitted, dict):
                            raise ValueError("Admission receipt is not an object")
                    except (OSError, ValueError, TypeError) as exc:
                        admission_error = repr(exc)
                if (folder / "receipt.json").is_file():
                    try:
                        row = base.result_row(target, case_name, state, arm,
                                              json.loads((folder / "receipt.json").read_text()))
                    except (ValueError, KeyError, TypeError) as exc:
                        row = {**entry, "status": "receipt_unreadable", "error": repr(exc)}
                elif admission_error is not None:
                    row = {**entry, "status": "admission_unreadable"}
                elif admitted is not None and admitted.get("eligible") is False:
                    row = {**entry, "status": "ineligible"}
                elif (folder / "launch.json").is_file():
                    row = {**entry, "status": "interrupted_unreceipted"}
                else:
                    row = {**entry, "status": "unstarted"}
                if admitted is not None:
                    row["admission"] = admitted
                if admission_error is not None:
                    row["admission_read_error"] = admission_error
                rows.append(row)
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
                  "paid_pairs": paid_pairs(rows),
                  "all_declared_cells_accounted": len(rows) == 32,
                  "scientific_admission": "none; abnormal controller termination"})
    return rows


def seal_manifest(path):
    target = Path(path)
    files = {str(p.relative_to(target)): {"bytes": p.stat().st_size, "sha256": base.sha(p)}
             for p in sorted(target.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    base.save_new(target / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})


def supervise(path):
    target = _attempt(path)
    source_error, child_rc, timeout, launch_error, quiescent = None, None, False, None, True
    try:
        frozen(target)
    except Exception as exc:
        source_error = repr(exc)
    started = time.monotonic()
    if source_error is None:
        cmd = [sys.executable, "-m", "experiments.solver_baseline_comparison", "controller", "--attempt", str(target)]
        base.save_new(target / "supervisor_launch.json", {"command": cmd, "hard_seconds": TOTAL_CAP})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        try:
            with (target / "controller_stdout.txt").open("xb") as out, (target / "controller_stderr.txt").open("xb") as err:
                process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                child_rc, timeout, quiescent = base.wait_process_group(process, TOTAL_CAP)
        except Exception as exc:
            launch_error, child_rc = repr(exc), 1
    else:
        base.save_new(target / "supervisor_launch.json", {"command": None, "blocked_before_child": True})
    try:
        unchanged = source_hashes() == json.loads((target / "frozen.json").read_text())["source_hashes"]
    except Exception as exc:
        unchanged = False
        source_error = repr(exc)
    if quiescent and (timeout or child_rc != 0 or source_error or launch_error):
        reconcile_partial(target)
    rc = 124 if timeout else 1 if source_error or not unchanged or launch_error or not quiescent else child_rc or 0
    base.save_new(target / "supervisor_receipt.json", {"protocol": PROTOCOL,
                  "child_returncode": child_rc, "returncode": rc, "hard_timeout": timeout,
                  "process_group_quiescent": quiescent, "stable_seal": quiescent,
                  "source_hashes_unchanged": unchanged, "source_check_error": source_error,
                  "launch_error": launch_error, "elapsed_seconds": time.monotonic()-started})
    if quiescent:
        seal_manifest(target)
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "supervise", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--state", type=int, choices=STATES)
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), indent=2, sort_keys=True))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt)
        return 0
    if args.mode == "supervise":
        return supervise(args.attempt)
    if args.mode == "controller":
        return controller(args.attempt)
    if args.case is None or args.state is None or args.arm is None:
        parser.error("worker requires --case, --state and --arm")
    return worker(args.attempt, args.case, args.state, args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
