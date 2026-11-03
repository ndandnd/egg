"""First bounded computational DEVELOPMENT screen; import never solves a model.

Only the exclusive frozen attempt may launch the 32 declared child stages. Raw
native traces are evidence, not an independent audit or an ML test set.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import native_recharge_qualification as recharge_fixture
from experiments import native_pathflow_qualification as path_fixture
from experiments import sistig_native_case as intake

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "result/computational_benchmark/20260928-attempt1"
PROTOCOL = "egg-computational-development-screen-20260928-v1"
PAYLOAD = "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
PAYLOAD_SHA = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"
TOTAL_CAP = 5400
CASE_IDS = {
    "synthetic_cyclic": "f24ed85ecec207ad543878c4cb247575629026fe1259ba3226155e439905b140",
    "synthetic_multivisit": "317fb71d02f64d511688e9b5b0008002e6aceeaad20745502341f823bd9d861b",
    "public_depot15": "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7",
    "public_depot16": "216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d",
}
CASES = tuple(CASE_IDS)
STAGES = ("planner", "cold_hull", "retained_hull", "response")
SOURCES = (
    "src/experiments/computational_benchmark.py",
    "src/tests/test_computational_benchmark.py",
    "src/cluster/computational_benchmark.sbatch",
    "research-20260928/computational-design/IMPLEMENTATION.md",
    "doc/COMPUTATIONAL_SCREEN_PROTOCOL_20260928.md",
    "doc/COMPUTATIONAL_SCREEN_REVIEW_20260928.md",
    "src/cluster/unicorn_env.sh",
    "src/egglab/native_recharge.py",
    "src/egglab/native_pathflow.py",
    "src/egglab/native_hull.py",
    "src/egglab/native_pathflow_hull.py",
    "src/egglab/solver.py",
    "src/experiments/native_recharge_qualification.py",
    "src/experiments/native_halfminute_qualification.py",
    "src/experiments/native_pathflow_qualification.py",
    "src/experiments/sistig_native_case.py",
    PAYLOAD,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def source_hashes():
    return {name: sha(ROOT / name) for name in SOURCES}


def environment():
    def version(package):
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None
    return {"python": sys.version, "platform": platform.platform(),
            "mip": version("mip"), "gurobipy": version("gurobipy"),
            "scipy": version("scipy")}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def cases():
    """Return four fixed cases; the two public variants share one base group."""
    raw = (ROOT / PAYLOAD).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA:
        raise ValueError("Public payload pin changed")
    variants = json.loads(raw)["native_cases"]
    if [v["selected_depot_id"] for v in variants] != [15, 16]:
        raise ValueError("Public depot order changed")
    result = {
        "synthetic_cyclic": recharge_fixture.cyclic_case(),
        "synthetic_multivisit": path_fixture.multivisit_case(),
        "public_depot15": intake.native_case_from_payload(variants[0]),
        "public_depot16": intake.native_case_from_payload(variants[1]),
    }
    for name, case in result.items():
        nr.validate_case(case)
        if case.identity() != CASE_IDS[name]:
            raise ValueError("Case identity changed: " + name)
    return result


def market(case_name, state):
    if case_name not in CASE_IDS or state not in (0, 1):
        raise ValueError("Unknown case/state")
    if case_name == "synthetic_cyclic":
        a = (0.0, 4.0, 0.0, 0.0) if state == 0 else (0.0, 3.8, 0.0, 0.2)
        b = (0.0, 0.2, 0.0, 0.2)
    elif case_name == "synthetic_multivisit":
        a = (0.2,) * 4 if state == 0 else (0.18, 0.18, 0.22, 0.22)
        b = (0.2,) * 4
    else:
        a = (0.2,) * 30 if state == 0 else (0.18,) * 15 + (0.22,) * 15
        b = (1 / 900,) * 30
    return nh.Market(case_name + "-state" + str(state), a, b)


def budget(case_name, stage):
    if case_name not in CASE_IDS or stage not in STAGES:
        raise ValueError("Unknown case/stage")
    public = case_name.startswith("public_")
    wall = (180 if public else 60) if stage != "response" else (60 if public else 30)
    phase = min(wall, 160 if public else 45)
    if stage.endswith("hull"):
        return nh.Budget(backend="GRB", threads=1, phase_seconds=phase,
                         wall_seconds=wall, pricing_calls=4, master_calls=6,
                         pool_cap=16, epsilon=1e-4, pool_tolerance=1e-6,
                         polish_steps=64, rational_bits=4096, polish_seconds=20)
    return nr.Budget(backend="GRB", threads=1, phase_seconds=phase,
                     wall_seconds=wall, max_rounds=(1 if stage == "response" else
                                                   8 if public else 6), epsilon=1e-4)


def design():
    built = cases()
    rows = {}
    for name, case in built.items():
        rows[name] = {
            "case": asdict(case), "case_identity": case.identity(),
            "base_timetable_group": "hildenbrand_37" if name.startswith("public_") else name,
            "development_only": True,
            "markets": [asdict(market(name, state)) for state in (0, 1)],
            "market_identities": [market(name, state).identity() for state in (0, 1)],
            "budgets": {stage: asdict(budget(name, stage)) for stage in STAGES},
            "hard_child_seconds": {stage: budget(name, stage).wall_seconds + 30 for stage in STAGES},
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
            "environment": environment(),
            "source_review": "doc/COMPUTATIONAL_SCREEN_REVIEW_20260928.md",
            "cases": design(), "stage_order": list(STAGES), "states": [0, 1],
            "controller_execution_cap_seconds": TOTAL_CAP, "backend": "GRB",
            "rng": "none", "split": "all development; Hildenbrand depots share one base timetable",
            "polish_seconds_interpretation": "soft algorithm stop target; actual elapsed is recorded",
            "raw_provenance": "complete fleet columns; no independent route-level DW master"}
    target.mkdir(parents=True, exist_ok=False)
    save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = _attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("source_hashes") != source_hashes()
            or spec.get("environment") != environment()
            or canonical(spec.get("cases")) != canonical(design())
            or spec.get("stage_order") != list(STAGES)
            or spec.get("controller_execution_cap_seconds") != TOTAL_CAP):
        raise ValueError("Frozen source/design differs from current published implementation")
    return spec


def finite_bounds(result):
    lo, hi = result.get("lower"), result.get("upper")
    if (type(lo) not in (int, float) or type(hi) not in (int, float)
            or not math.isfinite(lo) or not math.isfinite(hi) or lo > hi):
        return None
    return [str(Fraction(lo)), str(Fraction(hi))]


def assess(case, m, stage, result, prices=None):
    """Light author-side replay; a future independent result audit is separate."""
    status = result.get("status", "unresolved")
    identity = case.identity()
    if stage.endswith("hull"):
        if (result.get("physical_identity") != identity or
                result.get("market_identity") != m.identity() or
                result.get("pricing_oracle") != compact.ORACLE_ID or
                result.get("extraction_policy") != compact.EXTRACTION_POLICY):
            raise ValueError("Hull policy/case/market identity mismatch")
        counts = result.get("counts", {})
        actual_polish = counts.get("polish_wall_s", 0)
        if type(actual_polish) not in (int, float) or actual_polish < 0 or not math.isfinite(actual_polish):
            raise ValueError("Invalid hull polish accounting")
        out = {"status": status, "bounds": finite_bounds(result), "complete_evidence": False,
               "counts": counts, "polish_soft_excess_seconds": max(0.0, actual_polish - 20),
               "columns": len(result.get("columns", []))}
        if not result.get("lower_certificate") or not result.get("mixture"):
            if status == "certified":
                raise ValueError("Certified hull omitted its global certificate or mixture")
            return out
        columns = result.get("columns", [])
        keys = [col["key"] for col in columns]
        if not columns or len(keys) != len(set(keys)):
            raise ValueError("Empty/duplicate hull columns")
        for col in columns:
            nh.replay_column(case, col, compact.EXTRACTION_POLICY)
        cert = result["lower_certificate"]
        if nh.fenchel_bound(m, cert["prices"], cert["pricing_lower"]) != cert:
            raise ValueError("Hull global certificate does not replay")
        mix = result["mixture"]
        selected = {col["key"]: col for col in columns}
        chosen = [selected[key] for key in mix["column_keys"]]
        weights = [Fraction(x) for x in mix["simplex"]["weights_exact"]]
        rebuilt = nh.replay_exact_mixture(case, m, chosen, weights,
                                          extraction_policy=compact.EXTRACTION_POLICY)
        if (rebuilt["objective_exact"] != mix["objective_exact"]
                or rebuilt["load_exact"] != mix["load_exact"]
                or rebuilt["upper"] != mix["upper"]
                or not out["bounds"]):
            raise ValueError("Hull mixture/bounds do not replay")
        out["complete_evidence"] = True
        return out
    if result.get("case_identity") != identity:
        raise ValueError("Physical case identity mismatch")
    out = {"status": status, "bounds": finite_bounds(result), "complete_evidence": False}
    if result.get("plan") is None:
        if status == "certified":
            raise ValueError("Certified physical solve omitted plan")
        return out
    if (result.get("formulation") != pf.FORMULATION or
            result.get("extraction_policy") != pf.EXTRACTION_POLICY):
        raise ValueError("Physical formulation/extraction mismatch")
    replay = nr.replay_native(case, result["plan"], prices)
    if stage == "planner":
        if result.get("a") != list(m.a) or result.get("b") != list(m.b):
            raise ValueError("Planner market mismatch")
    elif result.get("prices") != prices:
        raise ValueError("Own-price vector mismatch")
    if not out["bounds"]:
        return out
    out.update(complete_evidence=True, replay=replay,
               plan_hash=nr.digest(result["plan"]), used_buses=len(result["plan"]["vehicles"]),
               movement_mask=[move.id in {mid for bus in result["plan"]["vehicles"]
                                           for mid in bus["movements"]}
                              for move in case.movements])
    return out


def features(case, m):
    return {"case_identity": case.identity(), "market_identity": m.identity(),
            "trips": [asdict(t) for t in case.trips],
            "movements": [asdict(move) for move in case.movements],
            "movement_ids": [move.id for move in case.movements],
            "market": asdict(m), "base_group": "hildenbrand_37" if len(case.trips) == 37 else case.name,
            "development_only": True}


def complete_stage(path, case_name, state, stage, certified=False):
    folder = Path(path) / case_name / ("state" + str(state)) / stage
    receipt_path, result_path = folder / "receipt.json", folder / "result.json"
    if not receipt_path.is_file() or not result_path.is_file():
        return False
    try:
        receipt = json.loads(receipt_path.read_text())
        assessment = json.loads(result_path.read_text())["assessment"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return (receipt.get("returncode") == 0 and receipt.get("on_time") is True
            and receipt.get("hard_timeout") is False
            and type(receipt.get("elapsed_seconds")) in (int, float)
            and receipt["elapsed_seconds"] <= receipt.get("hard_seconds", -1)
            and assessment.get("complete_evidence") is True
            and (not certified or assessment.get("status") == "certified"))


def worker(path, case_name, state, stage):
    target = _attempt(path)
    folder = target / case_name / ("state" + str(state)) / stage
    started = time.monotonic()
    try:
        spec = frozen(target)
        if not (folder / "launch.json").is_file():
            raise ValueError("Child stage launch receipt missing")
        case = cases()[case_name]
        m = market(case_name, state)
        cfg = budget(case_name, stage)
        expected = spec["cases"][case_name]
        if (expected["case_identity"] != case.identity() or
                expected["market_identities"][state] != m.identity() or
                expected["budgets"][stage] != asdict(cfg)):
            raise ValueError("Child differs from frozen cell")
        def record(event):
            with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        prices = None
        if stage == "planner":
            result = pf.solve_planner(case, m.a, m.b, cfg, record=record)
        elif stage == "response":
            if not complete_stage(target, case_name, state, "planner"):
                raise ValueError("Own-price response requires on-time replayed planner witness")
            parent = json.loads((target / case_name / ("state" + str(state)) /
                                 "planner" / "result.json").read_text())
            if not parent["assessment"]["complete_evidence"]:
                raise ValueError("Own-price response requires replayed planner witness")
            load = parent["assessment"]["replay"]["load"]
            prices = [float(a + b * e) for a, b, e in zip(m.a, m.b, load)]
            save_new(folder / "prices.json", prices)
            result = pf.solve_pricing(case, prices, cfg, record=record)
        else:
            arm = "cold" if stage == "cold_hull" else "retained"
            predecessor = None
            identity = None
            if arm == "retained" and state == 1:
                if not complete_stage(target, case_name, 0, "retained_hull", certified=True):
                    raise ValueError("Retained predecessor lacks on-time certified evidence")
                earlier = target / case_name / "state0" / "retained_hull" / "raw_result.json"
                predecessor = json.loads(earlier.read_text())["result"]
                prior_market = market(case_name, 0)
                if (predecessor.get("status") != "certified" or
                        predecessor.get("market_identity") != prior_market.identity()):
                    raise ValueError("Retained predecessor was not certified")
                identity = compact.state_identity(case, prior_market, "retained", 0, cfg)
            result = compact.certify(case, m, cfg, arm=arm, state_index=state,
                                     previous=predecessor, expected_previous=identity,
                                     record=record)
        save_new(folder / "raw_result.json", {"result": result, "case": case_name,
                                                "state": state, "stage": stage})
        assessment = assess(case, m, stage, result, prices)
        save_new(folder / "result.json", {"assessment": assessment,
                      "elapsed_seconds": time.monotonic() - started,
                      "case": case_name, "state": state, "stage": stage})
        return 0
    except Exception as exc:
        save_new(folder / "exception.json", {"type": type(exc).__name__,
                   "message": str(exc), "traceback": traceback.format_exc(),
                   "elapsed_seconds": time.monotonic() - started})
        return 2


def launch_child(path, case_name, state, stage, hard_seconds, command=None):
    """One child, one receipt. Timeout preserves any partial raw child files."""
    folder = Path(path) / case_name / ("state" + str(state)) / stage
    command = command or [sys.executable, "-m", "experiments.computational_benchmark",
                          "worker", "--attempt", str(path), "--case", case_name,
                          "--state", str(state), "--stage", stage]
    save_new(folder / "launch.json", {"command": command, "hard_seconds": hard_seconds,
                                      "started_utc": time.time()})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started, rc, timeout, error = time.monotonic(), None, False, None
    try:
        with (folder / "stdout.txt").open("xb") as out, (folder / "stderr.txt").open("xb") as err:
            # Stay in the controller process group so its total-cap kill also
            # terminates this child. Per-stage expiry targets this child only.
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err)
            try:
                rc = process.wait(timeout=hard_seconds)
            except subprocess.TimeoutExpired:
                timeout = True
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
    receipt = {"returncode": rc, "hard_timeout": timeout, "error": error,
               "elapsed_seconds": elapsed, "hard_seconds": hard_seconds,
               "on_time": not timeout and rc == 0 and elapsed <= hard_seconds}
    save_new(folder / "receipt.json", receipt)
    return receipt


def result_row(path, case_name, state, stage, receipt):
    folder = Path(path) / case_name / ("state" + str(state)) / stage
    row = {"case": case_name, "state": state, "stage": stage,
           "receipt": receipt, "status": "timed_out" if receipt["hard_timeout"] else
           "failed" if receipt["returncode"] != 0 else
           "late" if not receipt["on_time"] else "returned"}
    result_path = folder / "result.json"
    if result_path.is_file():
        try:
            assessment = json.loads(result_path.read_text())["assessment"]
            row.update(native_status=assessment["status"], bounds=assessment["bounds"],
                       complete_evidence=assessment["complete_evidence"])
            if receipt["on_time"]:
                row["status"] = assessment["status"]
            if stage.endswith("hull"):
                row.update(counts=assessment["counts"], columns=assessment["columns"],
                           polish_soft_excess_seconds=assessment["polish_soft_excess_seconds"])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row.update(complete_evidence=False, result_read_error=repr(exc))
            if row["status"] == "returned":
                row["status"] = "partial_result"
    return row


def controller(path):
    target = _attempt(path)
    spec = frozen(target)
    save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    for case_name in CASES:
        for state in (0, 1):
            state_dir = target / case_name / ("state" + str(state))
            save_new(state_dir / "features.json", features(cases()[case_name], market(case_name, state)))
            for stage in STAGES:
                folder = target / case_name / ("state" + str(state)) / stage
                if stage == "response":
                    eligible = complete_stage(target, case_name, state, "planner")
                elif stage == "retained_hull" and state == 1:
                    eligible = complete_stage(target, case_name, 0, "retained_hull", certified=True)
                else:
                    eligible = True
                if not eligible:
                    save_new(folder / "ineligible.json", {"reason": "missing replayed planner" if stage == "response"
                             else "retained predecessor not certified", "stage": stage})
                    rows.append({"case": case_name, "state": state, "stage": stage,
                                 "status": "ineligible", "complete_evidence": False})
                    continue
                receipt = launch_child(target, case_name, state, stage,
                                       spec["cases"][case_name]["hard_child_seconds"][stage])
                rows.append(result_row(target, case_name, state, stage, receipt))
            save_new(target / case_name / ("state" + str(state)) / "state_summary.json",
                     {"rows": rows[-len(STAGES):], "base_timetable_group":
                      spec["cases"][case_name]["base_timetable_group"]})
    save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
             "all_declared_stages_accounted": len(rows) == 32,
             "scientific_admission": "pending independent result review",
             "hull_columns_are_complete_fleets": True})
    return 0 if len(rows) == 32 else 2


def seal_manifest(path):
    target = Path(path)
    files = {str(p.relative_to(target)): {"bytes": p.stat().st_size, "sha256": sha(p)}
             for p in sorted(target.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    save_new(target / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})


def group_quiescent(pgid, seconds=2):
    """Confirm no non-zombie member can still write into the attempt."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            listing = subprocess.check_output(["ps", "-eo", "pgid=,stat="], text=True)
            active = any(parts[0] == str(pgid) and not parts[1].startswith("Z")
                         for line in listing.splitlines() if len(parts := line.split()) >= 2)
        except (OSError, subprocess.CalledProcessError):
            return False
        if not active:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(.05)


def wait_process_group(process, hard_seconds):
    """Kill the controller and its in-group worker before manifest sealing."""
    timed_out = False
    try:
        rc = process.wait(timeout=hard_seconds)
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
    if timed_out or rc != 0 or not group_quiescent(process.pid, 0):
        # The worker shares the controller's fresh process group. A controller
        # exit alone does not prove its child is gone.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if rc is None:
            try:
                rc = process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                rc = -signal.SIGKILL
    return rc, timed_out, group_quiescent(process.pid)


def reconcile_partial(path):
    """Account for every declared cell after abnormal controller termination."""
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if len(json.loads((target / "summary.json").read_text())["rows"]) == 32:
                return None
        except (ValueError, KeyError, TypeError):
            pass
    rows = []
    for case_name in CASES:
        for state in (0, 1):
            for stage in STAGES:
                folder = target / case_name / ("state" + str(state)) / stage
                base = {"case": case_name, "state": state, "stage": stage,
                        "complete_evidence": False}
                if (folder / "receipt.json").is_file():
                    try:
                        row = result_row(target, case_name, state, stage,
                                         json.loads((folder / "receipt.json").read_text()))
                    except (ValueError, KeyError, TypeError) as exc:
                        row = {**base, "status": "receipt_unreadable", "error": repr(exc)}
                elif (folder / "ineligible.json").is_file():
                    row = {**base, "status": "ineligible"}
                elif (folder / "launch.json").is_file():
                    row = {**base, "status": "interrupted_unreceipted"}
                else:
                    row = {**base, "status": "unstarted"}
                rows.append(row)
    save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
             "all_declared_stages_accounted": len(rows) == 32,
             "scientific_admission": "none; abnormal controller termination"})
    return rows


def supervise(path):
    target = _attempt(path)
    source_error, child_rc, timeout, launch_error, quiescent = None, None, False, None, True
    try:
        frozen(target)
    except Exception as exc:
        source_error = repr(exc)
    started = time.monotonic()
    if source_error is None:
        cmd = [sys.executable, "-m", "experiments.computational_benchmark", "controller",
               "--attempt", str(target)]
        save_new(target / "supervisor_launch.json", {"command": cmd, "hard_seconds": TOTAL_CAP})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        try:
            with (target / "controller_stdout.txt").open("xb") as out, (target / "controller_stderr.txt").open("xb") as err:
                process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                child_rc, timeout, quiescent = wait_process_group(process, TOTAL_CAP)
        except Exception as exc:
            launch_error, child_rc = repr(exc), 1
    else:
        save_new(target / "supervisor_launch.json", {"command": None, "blocked_before_child": True})
    try:
        unchanged = source_hashes() == json.loads((target / "frozen.json").read_text())["source_hashes"]
    except Exception as exc:
        unchanged = False
        source_error = repr(exc)
    if quiescent and (timeout or child_rc != 0 or source_error or launch_error):
        reconcile_partial(target)
    rc = 124 if timeout else 1 if source_error or not unchanged or launch_error or not quiescent else child_rc or 0
    save_new(target / "supervisor_receipt.json", {"protocol": PROTOCOL,
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
    parser.add_argument("--state", type=int, choices=(0, 1))
    parser.add_argument("--stage", choices=STAGES)
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
    if args.case is None or args.state is None or args.stage is None:
        parser.error("worker requires --case, --state and --stage")
    return worker(args.attempt, args.case, args.state, args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
