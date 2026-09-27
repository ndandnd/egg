"""Prospective one-cell Sistig nonlinear pilot; import performs no optimization.

Only the supervised, independently admitted GRB attempt may execute workers.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction as Q
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
from experiments import native_pathflow_qualification as physical_gate
from experiments import native_pathflow_hull_qualification as hull_gate
from experiments import sistig_native_case as intake

ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "result/sistig_nonlinear/20260927-attempt1"
PROTOCOL = "sistig-nonlinear-one-cell-20260927-v1"
PAYLOAD = "data/public/sistig_26088190_v1/hildenbrand_native_cases.json"
PAYLOAD_SHA256 = "af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6"
CASE_ID = "1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7"
ADMISSION = "doc/SISTIG_NONLINEAR_PILOT_ADMISSION_20260927.json"
REVIEW = "doc/SISTIG_NONLINEAR_PILOT_IMPLEMENTATION_REVIEW_20260927.md"
STAGES = ("planner", "hull", "own_price")
ROUTINE_CAPS = {"planner": 240, "hull": 1440, "own_price": 240}
CHILD_CAPS = {"planner": 255, "hull": 1455, "own_price": 255}
TOTAL_CAP = 2040
RESOLUTION = Q(5)
NEGATIVE_GUARD = Q(1, 10_000)
BACKEND = "GRB"
PILOT_SOURCES = (
    "src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
    "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py",
    "src/egglab/solver.py", "src/experiments/sistig_native_case.py",
    "src/experiments/native_hull_qualification.py",
    "src/experiments/native_pathflow_hull_qualification.py",
    "src/experiments/native_recharge_qualification.py",
    "src/experiments/sistig_nonlinear_pilot.py",
    "src/tests/test_sistig_nonlinear_pilot.py",
    "src/cluster/sistig_nonlinear_pilot.sbatch",
    "src/cluster/unicorn_env.sh",
    "doc/SISTIG_NONLINEAR_PILOT_PROTOCOL_20260927.md",
    "doc/SISTIG_MINIMAL_NONLINEAR_PILOT_RECOMMENDATION_20260927.md",
    REVIEW, ADMISSION, PAYLOAD,
)
SOURCES = tuple(dict.fromkeys(PILOT_SOURCES + physical_gate.SOURCES + hull_gate.SOURCES))


class QualificationHold(ValueError):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, sort_keys=True, indent=2, allow_nan=False)
        out.write("\n")


def source_hashes():
    return {name: sha(ROOT / name) for name in SOURCES}


def environment():
    def version(name):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return None
    return {"python": sys.version, "executable": sys.executable,
            "platform": platform.platform(), "mip": version("mip"),
            "gurobipy": version("gurobipy")}


def require_admission_files():
    if not (ROOT / ADMISSION).is_file() or not (ROOT / REVIEW).is_file():
        raise QualificationHold("NOT-YET-QUALIFIED: independent admission/review absent")


def _pinned_json(item):
    if (not isinstance(item, dict) or set(item) != {"path", "sha256"}
            or type(item["path"]) is not str or type(item["sha256"]) is not str):
        raise QualificationHold("NOT-YET-QUALIFIED: malformed gate evidence pin")
    path = Path(item["path"])
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "result":
        raise QualificationHold("NOT-YET-QUALIFIED: gate path is outside results")
    full = ROOT / path
    if not full.is_file() or sha(full) != item["sha256"]:
        raise QualificationHold("NOT-YET-QUALIFIED: gate evidence hash missing or changed")
    return json.loads(full.read_text())


def check_admission(hashes):
    """No public optimizer until same-source GRB 20+8 gates and reviews pass."""
    require_admission_files()
    path = ROOT / ADMISSION
    review = ROOT / REVIEW
    receipt = json.loads(path.read_text())
    if (receipt.get("status") != "PASS" or receipt.get("backend") != BACKEND
            or "**PASS**" not in review.read_text()):
        raise QualificationHold("NOT-YET-QUALIFIED: GRB admission review has not passed")
    shared_physical = ("src/egglab/native_recharge.py", "src/egglab/native_pathflow.py")
    shared_hull = shared_physical + ("src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py")
    physical_budget = nr.Budget(backend=BACKEND, threads=1, phase_seconds=10,
                                wall_seconds=45, max_rounds=48, epsilon=1e-4)
    hull_budget = nh.Budget(backend=BACKEND)
    expected_physical = [{**control, "case": asdict(control["case"]),
                          "case_identity": control["case"].identity()}
                         for control in physical_gate.controls()]
    expected_hull = [hull_gate.manifest(control, hull_budget)
                     for control in hull_gate.controls()]
    if len(expected_physical) != 20 or len(expected_hull) != 8:
        raise QualificationHold("NOT-YET-QUALIFIED: control builders no longer declare 20+8")
    canonical = lambda value: json.loads(json.dumps(value, sort_keys=True, allow_nan=False))
    for name, expected_controls, expected_budget, dependencies, protocol in (
            ("physical", expected_physical, asdict(physical_budget), shared_physical,
             physical_gate.PROTOCOL),
            ("hull", expected_hull, asdict(hull_budget), shared_hull, hull_gate.PROTOCOL)):
        expected_count = len(expected_controls)
        gate = receipt.get(name)
        if not isinstance(gate, dict):
            raise QualificationHold(f"NOT-YET-QUALIFIED: {name} GRB gate absent")
        frozen = _pinned_json(gate.get("frozen"))
        summary = _pinned_json(gate.get("summary"))
        audit = _pinned_json(gate.get("audit"))
        rows = summary.get("cells")
        if (frozen.get("protocol") != protocol
                or canonical(frozen.get("budget")) != canonical(expected_budget)
                or not isinstance(frozen.get("source_hashes"), dict)
                or not isinstance(frozen.get("controls"), list)
                or canonical(frozen["controls"]) != canonical(expected_controls)
                or summary.get("protocol") != protocol
                or not isinstance(rows, list) or len(rows) != expected_count
                or summary.get("all_pass") is not True
                or summary.get("source_hashes_unchanged") is not True
                or any(row.get("pass") is not True for row in rows)
                or not str(audit.get("audit_status", "")).startswith("PASS")):
            raise QualificationHold(f"NOT-YET-QUALIFIED: {name} GRB gate incomplete")
        if (name == "physical" and (frozen.get("formulation") != pf.FORMULATION
                                    or frozen.get("extraction_policy") != pf.EXTRACTION_POLICY)):
            raise QualificationHold("NOT-YET-QUALIFIED: physical V3 identity mismatch")
        if (name == "hull" and (frozen.get("pricing_oracle") != compact.ORACLE_ID
                                or frozen.get("extraction_policy") != compact.EXTRACTION_POLICY)):
            raise QualificationHold("NOT-YET-QUALIFIED: hull V3 identity mismatch")
        for dependency in dependencies:
            if frozen["source_hashes"].get(dependency) != hashes.get(dependency):
                raise QualificationHold(f"NOT-YET-QUALIFIED: {name} source differs: {dependency}")
    return receipt


def public_case():
    raw = (ROOT / PAYLOAD).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("Pinned public payload changed")
    variants = json.loads(raw)["native_cases"]
    if [v["selected_depot_id"] for v in variants] != [15, 16]:
        raise ValueError("Full public case sequence changed")
    case = intake.native_case_from_payload(variants[0])
    nr.validate_case(case)
    if (case.identity() != CASE_ID or variants[0]["case_identity"] != CASE_ID
            or len(case.trips) != 37 or list(case.market_edges_min) != list(range(0, 1801, 60))
            or case.battery_kwh != 400 or case.resources[0].per_bus_kw != 360
            or case.resources[0].grid_kw != 360 or case.resources[0].connectors != 1
            or case.recharge_deadline_min != 1800):
        raise ValueError("Declared depot-15 full-recharge case changed")
    return case


def market(case):
    if len(case.market_edges_min) != 31:
        raise ValueError("Expected 30 hourly periods")
    return nh.Market("sistig-depot15-30h-high-curvature", (.2,) * 30,
                     (1 / 900,) * 30)


def budget(stage):
    if stage == "hull":
        return nh.Budget(backend=BACKEND, threads=1, phase_seconds=180,
                         wall_seconds=1440, pricing_calls=6, master_calls=8,
                         pool_cap=48, epsilon=1e-4, pool_tolerance=1e-6,
                         polish_steps=256, rational_bits=8192, polish_seconds=5)
    return nr.Budget(backend=BACKEND, threads=1, phase_seconds=180,
                     wall_seconds=240, max_rounds=48 if stage == "planner" else 1,
                     epsilon=1e-4)


def _finite_interval(result):
    lo, hi = result.get("lower"), result.get("upper")
    if (type(lo) not in (int, float) or type(hi) not in (int, float)
            or not math.isfinite(lo) or not math.isfinite(hi) or lo > hi):
        raise ValueError("Missing or reversed finite global enclosure")
    return Q(lo), Q(hi)


def _identity(result, case):
    if (result.get("case_identity") != case.identity()
            or result.get("formulation") != pf.FORMULATION
            or result.get("extraction_policy") != pf.EXTRACTION_POLICY
            or not isinstance(result.get("plan"), dict)
            or result.get("plan", {}).get("formulation") != pf.FORMULATION
            or result.get("plan", {}).get("extraction_policy") != pf.EXTRACTION_POLICY):
        raise ValueError("Physical result/plan provenance mismatch")


def _backend(stats):
    runtime = stats.get("backend_runtime", {})
    if (stats.get("backend") != BACKEND or stats.get("threads") != 1
            or runtime.get("requested") != BACKEND
            or runtime.get("model_solver_name") != BACKEND
            or runtime.get("solver_module") != "mip.gurobi"):
        raise ValueError("Backend identity differs from qualified GRB")


def assess(stage, case, m, result, prices=None):
    """Admit author-side evidence; independent post-run audit remains required."""
    if stage in ("planner", "own_price"):
        _identity(result, case)
        if result.get("status") not in ("certified", "bounded"):
            raise ValueError("No replayed physical interval")
        lo, hi = _finite_interval(result)
        replay = nr.replay_native(case, result["plan"], prices)
        if stage == "planner":
            if result.get("a") != list(m.a) or result.get("b") != list(m.b):
                raise ValueError("Planner market differs from frozen cell")
            expected = replay["ops_cost"] + pf.true_cost(m.a, m.b, replay["load"])
            if hi < Q(expected) or hi - Q(expected) > Q(1, 1000):
                raise ValueError("Planner upper endpoint differs from replay")
            if not result.get("rounds"):
                raise ValueError("Missing planner native rounds")
            for item in result["rounds"]:
                _backend(item["stats"])
        else:
            if result.get("prices") != prices:
                raise ValueError("Own-price response price vector changed")
            _backend(result["stats"])
            if (lo, hi) != tuple(map(Q, nr.admit_bound(result["stats"],
                                                        replay["pricing_objective"]))):
                raise ValueError("Response global enclosure differs from replay")
        return {"lower_exact_stored": str(lo), "upper_exact_stored": str(hi),
                "plan_hash": nr.digest(result["plan"]), "used_buses": len(result["plan"]["vehicles"]),
                "replay": replay, "status": result["status"]}
    if stage != "hull":
        raise ValueError("Unknown stage")
    if (result.get("physical_identity") != case.identity()
            or result.get("market_identity") != m.identity()
            or result.get("pricing_oracle") != compact.ORACLE_ID
            or result.get("extraction_policy") != compact.EXTRACTION_POLICY
            or result.get("status") not in ("certified", "stalled_bounded", "budget_exhausted")):
        raise ValueError("Hull identity or completion differs from frozen cell")
    lo, hi = _finite_interval(result)
    columns = result.get("columns", [])
    if not columns or not result.get("lower_certificate") or not result.get("mixture"):
        raise ValueError("Missing global hull pricing bound or feasible mixture")
    keys = [column["key"] for column in columns]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate hull column projection key")
    for column in columns:
        nh.replay_column(case, column, compact.EXTRACTION_POLICY)
    cert = result["lower_certificate"]
    rebuilt = nh.fenchel_bound(m, cert["prices"], cert["pricing_lower"])
    if rebuilt != cert or lo != Q(cert["lower"]):
        raise ValueError("Hull Fenchel lower bound differs from global pricing receipt")
    mixture = result["mixture"]
    saved_keys = mixture.get("column_keys")
    if (not isinstance(saved_keys, list) or not saved_keys
            or any(type(key) is not str for key in saved_keys)
            or len(set(saved_keys)) != len(saved_keys)):
        raise ValueError("Invalid saved hull mixture column keys")
    by_key = {column["key"]: column for column in columns}
    if any(key not in by_key for key in saved_keys):
        raise ValueError("Saved hull mixture refers to a missing final column")
    selected = [by_key[key] for key in saved_keys]
    weights = [Q(x) for x in mixture["simplex"]["weights_exact"]]
    rebuilt_mix = nh.replay_exact_mixture(case, m, selected, weights,
                                          extraction_policy=compact.EXTRACTION_POLICY)
    if (rebuilt_mix["objective_exact"] != mixture.get("objective_exact")
            or rebuilt_mix["load_exact"] != mixture.get("load_exact")
            or rebuilt_mix["ops_exact"] != mixture.get("ops_exact")
            or rebuilt_mix["supply_exact"] != mixture.get("supply_exact")
            or rebuilt_mix["upper"] != mixture.get("upper")
            or hi != Q(mixture["upper"])):
        raise ValueError("Hull mixture objective/load does not replay")
    if Q(result["gap_exact"]) != Q(mixture["objective_exact"]) - Q(cert["lower_exact"]):
        raise ValueError("Hull exact stored-number gap differs")
    return {"lower_exact_stored": str(lo), "upper_exact_stored": str(hi),
            "global_lower_exact": cert["lower_exact"], "mixture_exact": mixture["objective_exact"],
            "status": result["status"],
            "bounded_budget_limited": result["status"] == "budget_exhausted",
            "columns": len(columns)}


def own_prices(m, planner_package):
    load = planner_package["assessment"]["replay"]["load"]
    if len(load) != 30:
        raise ValueError("Planner load dimension changed")
    return [float(a + b * e) for a, b, e in zip(m.a, m.b, load)]


def report(planner, hull, response, prices):
    p, h, r = (package["assessment"] for package in (planner, hull, response))
    d_lo, d_hi = Q(p["lower_exact_stored"]), Q(p["upper_exact_stored"])
    h_lo, h_hi = Q(h["lower_exact_stored"]), Q(h["upper_exact_stored"])
    r_lo, r_hi = Q(r["lower_exact_stored"]), Q(r["upper_exact_stored"])
    gap = (d_lo - h_hi, d_hi - h_lo)
    if gap[1] < -NEGATIVE_GUARD or gap[0] > gap[1]:
        raise ValueError("Planner/hull gap enclosure is inconsistent")
    if gap[0] > RESOLUTION:
        classification = "resolvably_positive_above_five"
    elif gap[1] <= RESOLUTION and gap[0] >= -NEGATIVE_GUARD:
        classification = "gap_at_most_five_under_declared_numerical_policy"
    else:
        classification = "unresolved_at_five"
    load = p["replay"]["load"]
    own_value = Q(p["replay"]["ops_cost"]) + sum((Q(x) * Q(y) for x, y in zip(prices, load)), Q(0))
    regret = (own_value - r_hi, own_value - r_lo)
    return {"gap_interval_exact_stored": [str(x) for x in gap],
            "gap_classification": classification, "resolution": str(RESOLUTION),
            "negative_guard": str(NEGATIVE_GUARD),
            "own_price_vector": prices, "own_price_plan_value_exact_stored": str(own_value),
            "own_price_regret_interval_exact_stored": [str(x) for x in regret],
            "regret_subject": ("planner_optimum_under_declared_numerical_policy"
                               if p["status"] == "certified" else "named_planner_incumbent"),
            "planner_plan_hash": p["plan_hash"], "used_buses": p["used_buses"],
            "claim_scope": "synthetic one-cell numerical enclosure; independent result audit pending"}


def _case_and_market():
    case = public_case()
    m = market(case)
    nh.validate_market(case, m)
    return case, m


def freeze(attempt):
    if Path(attempt).resolve() != ATTEMPT.resolve():
        raise ValueError("Only the exclusive attempt1 path is admitted")
    require_admission_files()
    hashes = source_hashes()
    admission = check_admission(hashes)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for name, expected in hashes.items():
        blob = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ROOT)
        if hashlib.sha256(blob).hexdigest() != expected:
            raise QualificationHold(f"NOT-YET-QUALIFIED: uncommitted dependency {name}")
    case, m = _case_and_market()
    spec = {"protocol": PROTOCOL, "source_commit": commit, "source_hashes": hashes,
            "admission_sha256": sha(ROOT / ADMISSION), "admission": admission,
            "case": asdict(case), "case_identity": case.identity(),
            "market": asdict(m), "market_identity": m.identity(),
            "backend": BACKEND, "stages": list(STAGES), "routine_caps": ROUTINE_CAPS,
            "child_caps": CHILD_CAPS, "total_cap": TOTAL_CAP,
            "budgets": {stage: asdict(budget(stage)) for stage in STAGES},
            "resolution": str(RESOLUTION), "negative_guard": str(NEGATIVE_GUARD),
            "environment": environment()}
    Path(attempt).mkdir(parents=True, exist_ok=False)
    write_new(Path(attempt) / "frozen.json", spec)


def _frozen(attempt):
    if Path(attempt).resolve() != ATTEMPT.resolve():
        raise ValueError("Attempt path mismatch")
    path = Path(attempt) / "frozen.json"
    spec = json.loads(path.read_text())
    require_admission_files()
    hashes = source_hashes()
    check_admission(hashes)
    case, m = _case_and_market()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_hashes") != hashes
            or spec.get("admission_sha256") != sha(ROOT / ADMISSION)
            or spec.get("case") != json.loads(json.dumps(asdict(case)))
            or spec.get("case_identity") != case.identity()
            or spec.get("market") != json.loads(json.dumps(asdict(m)))
            or spec.get("market_identity") != m.identity()
            or spec.get("backend") != BACKEND or spec.get("stages") != list(STAGES)
            or spec.get("routine_caps") != ROUTINE_CAPS or spec.get("child_caps") != CHILD_CAPS
            or spec.get("total_cap") != TOTAL_CAP
            or spec.get("budgets") != {s: asdict(budget(s)) for s in STAGES}
            or spec.get("resolution") != str(RESOLUTION)
            or spec.get("negative_guard") != str(NEGATIVE_GUARD)
            or spec.get("environment") != environment()):
        raise ValueError("Frozen execution identity or budget changed")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if spec.get("source_commit") != commit:
        raise ValueError("Published source commit changed")
    return spec, case, m, sha(path)


def worker(attempt, stage):
    folder = Path(attempt) / stage
    started = time.monotonic()
    try:
        if not (Path(attempt) / "STARTED.json").is_file() or not (folder / "launch.json").is_file():
            raise ValueError("Supervisor and stage launch receipts required")
        spec, case, m, frozen_hash = _frozen(attempt)
        instruction = json.loads((folder / "input.json").read_text())
        if (instruction.get("stage") != stage or instruction.get("frozen_sha256") != frozen_hash
                or instruction.get("budget") != spec["budgets"][stage]):
            raise ValueError("Worker instruction differs from frozen stage")
        def record(event):
            with (folder / "events.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                out.flush()
                os.fsync(out.fileno())
        if stage == "planner":
            result = pf.solve_planner(case, m.a, m.b, budget(stage), record=record)
            prices = None
        elif stage == "hull":
            result = compact.certify(case, m, budget(stage), arm="cold", state_index=0,
                                     record=record)
            prices = None
        elif stage == "own_price":
            prices = instruction["prices"]
            if prices != own_prices(m, json.loads((Path(attempt) / "planner/result.json").read_text())):
                raise ValueError("Own-price instruction differs from planner replay")
            result = pf.solve_pricing(case, prices, budget(stage), record=record)
        else:
            raise ValueError("Unknown pilot stage")
        write_new(folder / "raw_result.json", {"stage": stage, "result": result,
                  "frozen_sha256": frozen_hash})
        assessment = assess(stage, case, m, result, prices)
        elapsed = time.monotonic() - started
        if elapsed > ROUTINE_CAPS[stage]:
            raise TimeoutError("Scientific routine/admission cap exceeded")
        write_new(folder / "result.json", {"stage": stage, "result": result,
                  "assessment": assessment, "elapsed_seconds": elapsed,
                  "frozen_sha256": frozen_hash})
        return 0
    except Exception as exc:
        write_new(folder / "exception.json", {"stage": stage, "type": type(exc).__name__,
                  "message": str(exc), "traceback": traceback.format_exc(),
                  "elapsed_seconds": time.monotonic() - started})
        return 2


def _events(folder, stage):
    events, issues = [], []
    path = folder / "events.jsonl"
    if path.exists():
        try:
            lines = path.read_bytes().splitlines()
        except OSError as exc:
            lines = []
            issues.append({"message": "Event read: " + str(exc)})
        for line_number, line in enumerate(lines, 1):
            try:
                event = json.loads(line)
                if type(event) is not dict or type(event.get("event")) is not str:
                    raise ValueError("Malformed event")
                events.append(event)
            except (ValueError, TypeError, UnicodeError) as exc:
                issues.append({"line": line_number, "message": str(exc),
                               "valid_prefix_events": len(events)})
                break
    if stage == "hull":
        try:
            count = hull_gate.accounting(events)
        except Exception as exc:
            issues.append({"message": "Hull accounting: " + str(exc)})
            count = {"native_accounting_complete": False,
                     "polish_accounting_complete": False, "native_starts": 0}
        if not count["native_accounting_complete"] or not count["polish_accounting_complete"] or count["native_starts"] < 1:
            issues.append({"message": "Incomplete hull native/polish accounting"})
        for event in events:
            detail = event.get("detail") if isinstance(event.get("detail"), dict) else {}
            if event.get("event") == "master_status" or (
                    event.get("event") == "pricing_native"
                    and detail.get("event") == "native_status"):
                stats = event.get("stats") if event["event"] == "master_status" else detail.get("stats")
                try:
                    _backend(stats)
                except (ValueError, AttributeError) as exc:
                    issues.append({"message": "Hull backend: " + str(exc)})
    else:
        starts = sum(e.get("event") == "native_start" for e in events)
        returns = sum(e.get("event") == "native_status" for e in events)
        count = {"native_starts": starts, "native_returns": returns,
                 "native_accounting_complete": starts > 0 and starts == returns}
        if not count["native_accounting_complete"] or (stage == "own_price" and starts != 1):
            issues.append({"message": "Incomplete physical native accounting"})
        for event in events:
            if event.get("event") == "native_status":
                try:
                    _backend(event.get("stats"))
                except (ValueError, AttributeError) as exc:
                    issues.append({"message": "Physical backend: " + str(exc)})
    return count, issues


def controller(attempt):
    spec, case, m, frozen_hash = _frozen(attempt)
    if not (Path(attempt) / "supervisor_launch.json").is_file():
        raise ValueError("Supervisor launch receipt required")
    started = time.monotonic()
    write_new(Path(attempt) / "STARTED.json", {"protocol": PROTOCOL,
              "frozen_sha256": frozen_hash, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    rows, packages, prices, stop_reason = [], {}, None, None
    for stage in STAGES:
        if time.monotonic() - started > TOTAL_CAP:
            stop_reason = "complete attempt cap reached before stage launch"
            break
        folder = Path(attempt) / stage
        folder.mkdir(exist_ok=False)
        instruction = {"stage": stage, "budget": spec["budgets"][stage],
                       "frozen_sha256": frozen_hash}
        if stage == "own_price":
            prices = own_prices(m, packages["planner"])
            instruction["prices"] = prices
        write_new(folder / "input.json", instruction)
        cmd = [sys.executable, "-m", "experiments.sistig_nonlinear_pilot", "worker",
               "--attempt", str(Path(attempt).resolve()), "--stage", stage]
        write_new(folder / "launch.json", {"command": cmd,
                  "hard_cap_seconds": CHILD_CAPS[stage], "frozen_sha256": frozen_hash})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        launched, timed_out, rc, error = time.monotonic(), False, None, None
        try:
            with (folder / "stdout.txt").open("xb") as out, (folder / "stderr.txt").open("xb") as err:
                process = subprocess.run(cmd, cwd=ROOT, env=env, stdout=out, stderr=err,
                                         timeout=CHILD_CAPS[stage], check=False)
                rc = process.returncode
        except subprocess.TimeoutExpired:
            timed_out, rc = True, 124
        except Exception as exc:
            error, rc = repr(exc), 1
        try:
            counts, issues = _events(folder, stage)
        except Exception as exc:
            counts, issues = {"native_accounting_complete": False}, [
                {"message": "Event accounting: " + repr(exc)}]
        package = None
        if (folder / "result.json").is_file():
            try:
                package = json.loads((folder / "result.json").read_text())
                if (package.get("stage") != stage or package.get("frozen_sha256") != frozen_hash
                        or type(package.get("elapsed_seconds")) not in (int, float)
                        or not 0 <= package["elapsed_seconds"] <= ROUTINE_CAPS[stage]
                        or package.get("assessment") != assess(stage, case, m,
                                                                package["result"], prices)):
                    raise ValueError("Stage result identity mismatch")
            except Exception as exc:
                issues.append({"message": "Result read: " + str(exc)})
                package = None
        accepted = bool(rc == 0 and not timed_out and not issues and package)
        row = {"stage": stage, "returncode": rc, "hard_timeout": timed_out,
               "launch_error": error, "elapsed_seconds": time.monotonic() - launched,
               "accounting": counts, "evidence_issues": issues, "pass": accepted,
               "status": package["result"].get("status") if package else "failed"}
        write_new(folder / "receipt.json", row)
        rows.append(row)
        if not accepted:
            stop_reason = f"{stage} failed or timed out"
            break
        packages[stage] = package
    complete = len(rows) == 3 and all(row["pass"] for row in rows)
    final, report_error = None, None
    if complete:
        try:
            final = report(packages["planner"], packages["hull"], packages["own_price"], prices)
        except Exception as exc:
            complete, report_error = False, repr(exc)
            stop_reason = "final interval consistency failure"
    source_error = None
    try:
        sources_unchanged = source_hashes() == spec["source_hashes"]
    except Exception as exc:
        sources_unchanged, source_error = False, repr(exc)
    summary = {"protocol": PROTOCOL, "stages": rows, "complete": complete,
               "unstarted_stages": list(STAGES[len(rows):]), "stop_reason": stop_reason,
               "elapsed_seconds": time.monotonic() - started,
               "source_hashes_unchanged": sources_unchanged,
               "source_check_error": source_error,
               "frozen_sha256": frozen_hash, "report": final,
               "report_error": report_error,
               "independent_result_audit_pending": True}
    write_new(Path(attempt) / "summary.json", summary)
    return 0 if complete and sources_unchanged else 1


def supervise(attempt):
    try:
        _frozen(attempt)
    except Exception as exc:
        if not (Path(attempt) / "frozen.json").is_file():
            raise
        write_new(Path(attempt) / "supervisor_launch.json", {"command": None,
                  "outer_cap_seconds": TOTAL_CAP, "blocked_before_child": True})
        write_new(Path(attempt) / "supervisor_receipt.json", {"protocol": PROTOCOL,
                  "child_returncode": None, "returncode": 1,
                  "outer_timeout": False, "exception": repr(exc),
                  "source_hashes_unchanged": False,
                  "source_check_error": repr(exc), "elapsed_seconds": 0})
        seal_manifest(attempt)
        return 1
    command = [sys.executable, "-m", "experiments.sistig_nonlinear_pilot", "controller",
               "--attempt", str(Path(attempt).resolve())]
    write_new(Path(attempt) / "supervisor_launch.json", {"command": command,
              "outer_cap_seconds": TOTAL_CAP, "kill_grace_seconds": 10})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started, timed_out, rc, error = time.monotonic(), False, None, None
    try:
        with (Path(attempt) / "controller_stdout.txt").open("xb") as out, (Path(attempt) / "controller_stderr.txt").open("xb") as err:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                       start_new_session=True)
            try:
                rc = process.wait(timeout=TOTAL_CAP)
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
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                if rc is None:
                    rc = process.wait()
    except Exception as exc:
        error, rc = repr(exc), 1
    source_error = None
    try:
        spec = json.loads((Path(attempt) / "frozen.json").read_text())
        sources_unchanged = source_hashes() == spec["source_hashes"]
    except Exception as exc:
        sources_unchanged, source_error = False, repr(exc)
    final_rc = 124 if timed_out else rc if type(rc) is int else 1
    if not sources_unchanged and final_rc == 0:
        final_rc = 1
    write_new(Path(attempt) / "supervisor_receipt.json", {"protocol": PROTOCOL,
              "child_returncode": rc, "returncode": final_rc,
              "outer_timeout": timed_out, "exception": error,
              "source_hashes_unchanged": sources_unchanged,
              "source_check_error": source_error,
              "elapsed_seconds": time.monotonic() - started})
    seal_manifest(attempt)
    return final_rc


def seal_manifest(attempt):
    files = {str(path.relative_to(attempt)): {"bytes": path.stat().st_size, "sha256": sha(path)}
             for path in sorted(Path(attempt).rglob("*")) if path.is_file()}
    write_new(Path(attempt) / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "supervise", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--stage", choices=STAGES)
    args = parser.parse_args(argv)
    attempt = args.attempt.resolve()
    if args.mode == "worker":
        if not args.stage:
            parser.error("Worker stage is required")
        return worker(attempt, args.stage)
    if args.stage:
        parser.error("Stage is worker-only")
    return {"freeze": freeze, "supervise": supervise,
            "controller": controller}[args.mode](attempt)


if __name__ == "__main__":
    raise SystemExit(main())
