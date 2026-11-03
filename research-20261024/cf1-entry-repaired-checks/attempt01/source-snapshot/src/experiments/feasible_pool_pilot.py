"""Prospective, development-only 24-cell native hull feasible-pool pilot."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow_hull as compact
from experiments import computational_benchmark as base

ROOT = base.ROOT
ATTEMPT = ROOT / "result/feasible_pool_pilot/20260928-attempt1"
PROTOCOL = "egg-feasible-pool-development-pilot-20260928-v1"
ARMS = ("legacy_cold_hull", "reserve_cold_hull", "reserve_feasible_hull")
CASES = base.CASES
STATES = (0, 1)
RESERVE_SECONDS = 10.0
TOTAL_CAP = 5400
SOURCES = (
    "src/experiments/feasible_pool_pilot.py",
    "src/tests/test_feasible_pool_pilot.py",
    "src/tests/test_native_hull_feasible_reuse.py",
    "src/cluster/feasible_pool_pilot.sbatch",
    "research-20260928/feasible-pool-pilot/IMPLEMENTATION.md",
    "doc/FEASIBLE_POOL_PILOT_PROTOCOL_20260928.md",
    "doc/FEASIBLE_POOL_PILOT_REVIEW_20260928.md",
    *base.SOURCES,
)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in dict.fromkeys(SOURCES)}


def controls(arm):
    if arm not in ARMS:
        raise ValueError("Unknown pilot arm")
    return {"reuse_policy": "feasible_pool", "pricing_reserve_seconds": RESERVE_SECONDS} if arm != ARMS[0] else {}


def hull_arm(arm):
    return "retained" if arm == "reserve_feasible_hull" else "cold"


def design():
    built = base.cases()
    rows = {}
    for name in CASES:
        case = built[name]
        cfg = base.budget(name, "cold_hull")
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
    spec = {"protocol": PROTOCOL, "source_commit": commit, "source_hashes": source_hashes(),
            "environment": base.environment(), "cases": design(), "stage_order": list(ARMS),
            "states": list(STATES), "controller_execution_cap_seconds": TOTAL_CAP,
            "backend": "GRB", "rng": "none", "split": "all development; Hildenbrand depots share one base timetable",
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
            or spec.get("environment") != base.environment()
            or base.canonical(spec.get("cases")) != base.canonical(design())
            or spec.get("stage_order") != list(ARMS) or spec.get("states") != list(STATES)
            or spec.get("controller_execution_cap_seconds") != TOTAL_CAP):
        raise ValueError("Frozen source/design differs from current implementation")
    return spec


def cell_dir(path, case_name, state, arm):
    return Path(path) / case_name / ("state" + str(state)) / arm


def predecessor(path, case_name):
    """Admit only an on-time, complete, replayable own state-0 pool."""
    folder = cell_dir(path, case_name, 0, "reserve_feasible_hull")
    receipt = json.loads((folder / "receipt.json").read_text())
    cfg = base.budget(case_name, "cold_hull")
    if (receipt.get("returncode") != 0 or receipt.get("hard_timeout") is not False
            or receipt.get("on_time") is not True
            or type(receipt.get("elapsed_seconds")) not in (int, float)
            or receipt.get("hard_seconds") != cfg.wall_seconds + 30
            or not 0 <= receipt["elapsed_seconds"] <= receipt["hard_seconds"]):
        raise ValueError("Predecessor child was not complete and on time")
    wrapped = json.loads((folder / "raw_result.json").read_text())
    if (wrapped.get("case"), wrapped.get("state"), wrapped.get("stage")) != (
            case_name, 0, "reserve_feasible_hull"):
        raise ValueError("Predecessor raw wrapper identity differs")
    prior = wrapped["result"]
    case, market = base.cases()[case_name], base.market(case_name, 0)
    identity = compact.state_identity(case, market, "retained", 0, cfg, **controls("reserve_feasible_hull"))
    if (prior.get("schema") != nh.SCHEMA or prior.get("status") not in
            ("certified", "budget_exhausted", "stalled_bounded", "bounded")
            or prior.get("arm") != "retained" or prior.get("state_index") != 0
            or prior.get("state_identity") != identity
            or prior.get("physical_identity") != case.identity()
            or prior.get("market_identity") != market.identity()
            or prior.get("pricing_oracle") != compact.ORACLE_ID
            or prior.get("extraction_policy") != compact.EXTRACTION_POLICY
            or any(prior.get(key) != value for key, value in controls("reserve_feasible_hull").items())):
        raise ValueError("Predecessor status/identity/policy differs")
    columns = prior.get("columns", [])
    if not 1 <= len(columns) <= cfg.pool_cap or len({c["key"] for c in columns}) != len(columns):
        raise ValueError("Predecessor pool is empty, oversized or duplicated")
    for col in columns:
        source = col.get("source")
        if not isinstance(source, dict) or source.get("state_identity") != identity or source.get("pricing_oracle") != compact.ORACLE_ID:
            raise ValueError("Predecessor column source identity/policy differs")
        nh.replay_column(case, col, compact.EXTRACTION_POLICY)
    result = json.loads((folder / "result.json").read_text())
    assessment = result["assessment"]
    if ((result.get("case"), result.get("state"), result.get("stage")) != (
            case_name, 0, "reserve_feasible_hull") or assessment.get("status") != prior["status"]
            or assessment.get("complete_evidence") is not True or not assessment.get("bounds")
            or not prior.get("lower_certificate") or not prior.get("mixture")):
        raise ValueError("Predecessor assessment differs")
    checked = base.assess(case, market, "reserve_feasible_hull", prior)
    if checked != assessment or not checked["complete_evidence"]:
        raise ValueError("Predecessor certificate/mixture failed replay")
    return prior, identity


def eligible(path, case_name):
    try:
        predecessor(path, case_name)
        return True, None
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        return False, str(exc)


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
        previous, identity = (predecessor(target, case_name) if arm == "reserve_feasible_hull" and state == 1
                              else (None, None))
        def record(event):
            with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        result = compact.certify(case, market, cfg, arm=hull_arm(arm), state_index=state,
                                 previous=previous, expected_previous=identity,
                                 record=record, **controls(arm))
        state_identity = compact.state_identity(case, market, hull_arm(arm), state, cfg, **controls(arm))
        if (result.get("state_identity") != state_identity or result.get("arm") != hull_arm(arm)
                or result.get("state_index") != state or result.get("physical_identity") != case.identity()
                or result.get("market_identity") != market.identity()
                or any(result.get(key) != value for key, value in controls(arm).items())):
            raise ValueError("Native result differs from frozen state and controls")
        base.save_new(folder / "raw_result.json", {"result": result, "case": case_name,
                                                   "state": state, "stage": arm})
        assessment = base.assess(case, market, arm, result)
        base.save_new(folder / "result.json", {"assessment": assessment,
                         "elapsed_seconds": time.monotonic() - started,
                         "case": case_name, "state": state, "stage": arm})
        return 0
    except Exception as exc:
        base.save_new(folder / "exception.json", {"type": type(exc).__name__,
                      "message": str(exc), "traceback": traceback.format_exc(),
                      "elapsed_seconds": time.monotonic() - started})
        return 2


def launch_child(path, case_name, state, arm, hard_seconds):
    command = [sys.executable, "-m", "experiments.feasible_pool_pilot", "worker",
               "--attempt", str(path), "--case", case_name, "--state", str(state), "--arm", arm]
    return base.launch_child(path, case_name, state, arm, hard_seconds, command)


def controller(path):
    target = _attempt(path)
    spec = frozen(target)
    base.save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    built = base.cases()
    for case_name in CASES:
        for state in STATES:
            state_dir = target / case_name / ("state" + str(state))
            base.save_new(state_dir / "features.json", base.features(built[case_name], base.market(case_name, state)))
            for arm in ARMS:
                folder = cell_dir(target, case_name, state, arm)
                if arm == "reserve_feasible_hull" and state == 1:
                    admitted, reason = eligible(target, case_name)
                    if not admitted:
                        base.save_new(folder / "ineligible.json", {"reason": reason, "stage": arm})
                        rows.append({"case": case_name, "state": state, "stage": arm,
                                     "status": "ineligible", "complete_evidence": False})
                        continue
                receipt = launch_child(target, case_name, state, arm, spec["cases"][case_name]["hard_child_seconds"])
                rows.append(base.result_row(target, case_name, state, arm, receipt))
            base.save_new(state_dir / "state_summary.json", {"rows": rows[-len(ARMS):],
                          "base_timetable_group": spec["cases"][case_name]["base_timetable_group"]})
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                  "all_declared_cells_accounted": len(rows) == 24,
                  "scientific_admission": "pending independent result review",
                  "hull_columns_are_complete_fleets": True})
    return 0 if len(rows) == 24 else 2


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if len(json.loads((target / "summary.json").read_text())["rows"]) == 24:
                return None
        except (ValueError, KeyError, TypeError):
            pass
    rows = []
    for case_name in CASES:
        for state in STATES:
            for arm in ARMS:
                folder = cell_dir(target, case_name, state, arm)
                entry = {"case": case_name, "state": state, "stage": arm, "complete_evidence": False}
                if (folder / "receipt.json").is_file():
                    try:
                        row = base.result_row(target, case_name, state, arm,
                                              json.loads((folder / "receipt.json").read_text()))
                    except (ValueError, KeyError, TypeError) as exc:
                        row = {**entry, "status": "receipt_unreadable", "error": repr(exc)}
                elif (folder / "ineligible.json").is_file():
                    row = {**entry, "status": "ineligible"}
                elif (folder / "launch.json").is_file():
                    row = {**entry, "status": "interrupted_unreceipted"}
                else:
                    row = {**entry, "status": "unstarted"}
                rows.append(row)
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
                  "all_declared_cells_accounted": len(rows) == 24,
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
        cmd = [sys.executable, "-m", "experiments.feasible_pool_pilot", "controller", "--attempt", str(target)]
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
                  "launch_error": launch_error, "elapsed_seconds": time.monotonic() - started})
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
