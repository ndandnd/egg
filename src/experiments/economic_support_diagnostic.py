"""Bounded six-cell physical-planner and own-price-response diagnosis."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from experiments import computational_benchmark as base
from experiments import budget_sizing_diagnostic as sizing
from experiments import qp_baseline_diagnostic as qp
from experiments import retrieval_comparison as retrieval


ROOT = base.ROOT
ATTEMPT = ROOT / "result/economic_support_diagnostic/20260929-attempt1"
PROTOCOL = "egg-economic-support-diagnostic-development-20260929-v1"
HULL = ROOT / "research-20260929/qp-baseline-diagnostic/results-attempt1"
HULL_COMMIT = "60a66e77be18e067aee4026f0e3a31dc120ec427"
HULL_JOB = "595105"
STAGES = ("planner", "response")
HARD_SECONDS = {"planner": 210, "response": 90}
CONTROLLER_CAP_SECONDS = 2100
SOURCE_FILES = (
    "src/experiments/economic_support_diagnostic.py",
    "src/tests/test_economic_support_diagnostic.py",
    "src/cluster/economic_support_diagnostic.sbatch",
    "research-20260929/economic-support-diagnostic/DESIGN.md",
    "research-20260929/economic-support-diagnostic/README.md",
    "research-20260929/economic-support-diagnostic/IMPLEMENTATION.md",
    "research-20260929/qp-baseline-diagnostic/results-attempt1/COLLECTION_RECEIPT.json",
    "research-20260929/qp-baseline-diagnostic/results-attempt1/frozen_identity.json",
    "research-20260929/qp-baseline-diagnostic/results-attempt1/summary.json",
    "research-20260929/qp-baseline-diagnostic/results-attempt1/MANIFEST.json",
    "research-20260929/qp-baseline-diagnostic/results-attempt1/supervisor_receipt.json",
    "research-20260929/qp-baseline-diagnostic/results-attempt1/wrapper_receipt.json",
    "src/experiments/qp_baseline_diagnostic.py",
    "src/experiments/retrieval_comparison.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/experiments/native_scaling_cases.py",
    "research-20260928/retrieval-comparison/SYNTHETIC_PREFLIGHT.json",
    "src/egglab/native_pathflow.py",
    "src/egglab/native_recharge.py",
    "src/egglab/native_hull.py",
    "src/egglab/solver.py",
    "src/cluster/unicorn_env.sh",
)


def cells():
    return qp.cells()


def cases():
    return qp.cases()


def market(name, kind):
    return qp.market(name, kind)


def budget(stage):
    if stage not in STAGES:
        raise ValueError("Undeclared physical stage")
    return nr.Budget(backend="GRB", threads=1,
                     phase_seconds=160 if stage == "planner" else 45,
                     wall_seconds=180 if stage == "planner" else 60,
                     max_rounds=16 if stage == "planner" else 1,
                     epsilon=1e-4)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def _read(path):
    return json.loads(Path(path).read_text())


def imported_hull():
    """Admit only the six reviewed, on-time QP hull intervals."""
    receipt = _read(HULL / "COLLECTION_RECEIPT.json")
    expected_hashes = receipt.get("curated_file_sha256", {})
    for name in ("frozen_identity.json", "summary.json", "MANIFEST.json",
                 "supervisor_receipt.json", "wrapper_receipt.json"):
        if expected_hashes.get(name) != base.sha(HULL / name):
            raise ValueError("QP collection hash differs: " + name)
    frozen = _read(HULL / "frozen_identity.json")
    summary = _read(HULL / "summary.json")
    supervisor = _read(HULL / "supervisor_receipt.json")
    wrapper = _read(HULL / "wrapper_receipt.json")
    if (receipt.get("source_commit") != HULL_COMMIT or frozen.get("source_commit") != HULL_COMMIT
            or receipt.get("job_id") != HULL_JOB or str(wrapper.get("job_id")) != HULL_JOB
            or receipt.get("raw_frozen_sha256") != frozen.get("curation", {}).get("raw_frozen_sha256")
            or frozen.get("protocol") != summary.get("protocol")
            or supervisor.get("protocol") != summary.get("protocol")
            or supervisor.get("returncode") != 0
            or supervisor.get("stable_seal") is not True
            or supervisor.get("process_group_quiescent") is not True
            or supervisor.get("source_hashes_unchanged") is not True
            or any(wrapper.get(k) != 0 for k in
                   ("returncode", "freeze_returncode", "preflight_returncode", "supervise_returncode"))
            or summary.get("declared_cells") != 6 or summary.get("accounted_cells") != 6
            or summary.get("all_declared_cells_accounted") is not True):
        raise ValueError("QP source/receipt accounting differs")
    design = qp.design()
    earlier = frozen.get("design", {})
    for key in ("order", "budget", "hard_child_seconds", "pricing_reserve_seconds", "arm",
                "master_policy", "qp_denominator", "qp_maxiter", "bound_cache_policy"):
        if earlier.get(key) != design.get(key):
            raise ValueError("QP frozen design differs: " + key)
    if set(earlier.get("cases", {})) != set(qp.CASES):
        raise ValueError("QP cases differ")
    for name in qp.CASES:
        for key in ("case_identity", "market_identities", "markets", "base_group"):
            if base.canonical(earlier["cases"][name].get(key)) != base.canonical(design["cases"][name].get(key)):
                raise ValueError("QP physical/market identity differs")
    if (earlier.get("master_policy"), earlier.get("qp_denominator"), earlier.get("qp_maxiter")) != (
            "numerical_qp_proposal", 10**9, 500):
        raise ValueError("QP source master controls differ")
    rows = summary.get("rows", [])
    if len(rows) != 6 or {(r.get("case"), r.get("market")) for r in rows} != set(cells()):
        raise ValueError("QP summary lacks exactly six unique cells")
    imported = {}
    for row in rows:
        name, kind = row["case"], row["market"]
        if (row.get("state_index") != qp.state(kind)
                or row.get("master_policy") != "numerical_qp_proposal"
                or row.get("outcome") != "certified" or row.get("native_status") != "certified"
                or row.get("complete_evidence") is not True or row.get("on_time") is not True
                or row.get("child_wall_s") is None):
            raise ValueError("QP cell is not complete on-time certified evidence")
        lo, hi, gap = (Fraction(row[key]) for key in ("lower_exact", "upper_exact", "gap_exact"))
        if lo > hi or hi - lo != gap or gap > Fraction(1, 10_000):
            raise ValueError("QP hull interval invalid")
        imported[f"{name}/{kind}"] = {
            "case_identity": earlier["cases"][name]["case_identity"],
            "market_identity": earlier["cases"][name]["market_identities"][kind],
            "lower_exact": str(lo), "upper_exact": str(hi),
            "source_job_id": HULL_JOB, "source_commit": HULL_COMMIT}
    return imported


def design():
    built = cases()
    return {"cases": {name: {"case_identity": item.identity(),
                              "market_identities": {kind: market(name, kind).identity()
                                                    for kind in qp.KINDS}}
                      for name, item in built.items()},
            "order": [{"case": name, "market": kind, "state_index": qp.state(kind)}
                      for name, kind in cells()],
            "budgets": {stage: asdict(budget(stage)) for stage in STAGES},
            "hard_child_seconds": HARD_SECONDS,
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS,
            "hull_source": imported_hull(),
            "development_only": True, "independent_test_data": False}


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the exclusive economic-support attempt is allowed")
    return target


def freeze(path):
    target = _attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "software_runtime": qp.software_runtime(),
            "freeze_host_environment": sizing.host_environment(),
            "native_probe": sizing.native_probe(), "design": design(),
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS, "declared_cells": 6,
            "declared_stages": 12, "scientific_admission": "pending independent review"}
    target.mkdir(parents=True, exist_ok=False)
    base.save_new(target / "frozen.json", spec)
    return spec


def frozen(path):
    target = _attempt(path)
    spec = _read(target / "frozen.json")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit:
        raise ValueError("Frozen protocol/commit differs")
    if spec.get("source_hashes") != source_hashes():
        raise ValueError("Frozen source hashes differ")
    if not sizing.runtime_compatible(spec.get("software_runtime"), qp.software_runtime()):
        raise ValueError("Frozen portable runtime differs")
    if spec.get("native_probe") != sizing.native_probe():
        raise ValueError("Frozen native backend/seed differs")
    if (base.canonical(spec.get("design")) != base.canonical(design())
            or spec.get("controller_cap_seconds") != CONTROLLER_CAP_SECONDS
            or spec.get("declared_cells") != 6 or spec.get("declared_stages") != 12):
        raise ValueError("Frozen economic design differs")
    return spec


def folder(path, name, kind, stage):
    return Path(path) / name / f"state{qp.state(kind)}" / stage


def gradient(m, load):
    if len(load) != len(m.a) or len(load) != len(m.b):
        raise ValueError("Gradient load dimension differs")
    prices = [float(Fraction(a) + Fraction(b) * Fraction(e))
              for a, b, e in zip(m.a, m.b, load)]
    if any(not math.isfinite(p) for p in prices):
        raise ValueError("Nonfinite own-price gradient")
    return prices


def planner_admitted(path, name, kind):
    dest = folder(path, name, kind, "planner")
    try:
        receipt = _read(dest / "receipt.json")
        saved = _read(dest / "result.json")
        assessed = saved["assessment"]
        raw = _read(dest / "raw_result.json")["result"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if (receipt.get("returncode") != 0 or receipt.get("on_time") is not True
            or receipt.get("hard_timeout") is not False
            or (saved.get("case"), saved.get("market"), saved.get("stage")) !=
               (name, kind, "planner")
            or assessed.get("plan_replayed") is not True or not assessed.get("bounds")
            or assessed.get("status") not in ("certified", "bounded")
            or assessed.get("status") != raw.get("status")
            or assessed.get("bounds") != retrieval.finite_bounds(raw)
            or not isinstance(assessed.get("replay"), dict)
            or "load" not in assessed["replay"]
            or "ops_cost" not in assessed["replay"]
            or raw.get("case_identity") != cases()[name].identity()
            or raw.get("formulation") != pf.FORMULATION
            or raw.get("extraction_policy") != pf.EXTRACTION_POLICY
            or raw.get("a") != list(market(name, kind).a)
            or raw.get("b") != list(market(name, kind).b)
            or raw.get("plan") is None
            or assessed.get("plan_hash") != nr.digest(raw["plan"])):
        return None
    return assessed


def regret_interval(bill, response_bounds):
    lower, upper = map(Fraction, response_bounds)
    bill = Fraction(bill)
    if lower > upper or lower > bill:
        raise ValueError("Response lower exceeds feasible incumbent bill")
    return [str(max(Fraction(0), bill - upper)), str(bill - lower)]


def combined_intervals(d_bounds, ch_bounds):
    d_lo, d_hi = map(Fraction, d_bounds)
    ch_lo, ch_hi = map(Fraction, ch_bounds)
    if d_lo > d_hi or ch_lo > ch_hi or d_hi < ch_lo:
        raise ValueError("Physical/hull native intervals incompatible")
    d_lower = max(d_lo, ch_lo)
    ch_upper = min(ch_hi, d_hi)
    return {"D_interval_exact": [str(d_lower), str(d_hi)],
            "CH_interval_exact": [str(ch_lo), str(ch_upper)],
            "D_minus_CH_interval_exact": [
                str(max(Fraction(0), d_lower - ch_upper)), str(d_hi - ch_lo)]}


def gap_interval(d_bounds, ch_bounds):
    return combined_intervals(d_bounds, ch_bounds)["D_minus_CH_interval_exact"]


def worker(path, name, kind, stage):
    target = _attempt(path)
    if (name, kind) not in cells() or stage not in STAGES:
        raise ValueError("Undeclared physical cell/stage")
    dest = folder(target, name, kind, stage)
    started = time.monotonic()
    try:
        spec = frozen(target)
        if not (dest / "launch.json").is_file():
            raise ValueError("Missing child launch receipt")
        item, m, cfg = cases()[name], market(name, kind), budget(stage)
        declared = spec["design"]
        if (declared["cases"][name]["case_identity"] != item.identity()
                or declared["cases"][name]["market_identities"][kind] != m.identity()
                or declared["budgets"][stage] != asdict(cfg)):
            raise ValueError("Cell differs from frozen case/market/budget")
        def record(event):
            with (dest / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        prices = None
        parent = None
        if stage == "planner":
            result = pf.solve_planner(item, m.a, m.b, cfg, record=record)
        else:
            parent = planner_admitted(target, name, kind)
            if parent is None:
                raise ValueError("Response requires on-time bounded replayed planner")
            prices = gradient(m, parent["replay"]["load"])
            base.save_new(dest / "prices.json", {"case": name, "market": kind,
                                                  "planner_plan_hash": parent["plan_hash"],
                                                  "prices": prices})
            result = pf.solve_pricing(item, prices, cfg, record=record)
        base.save_new(dest / "raw_result.json", {"result": result, "case": name,
                                                  "market": kind, "stage": stage})
        assessment = retrieval.assess_physical(item, m, stage, result, prices)
        if stage == "response":
            replay = parent["replay"]
            bill = Fraction(replay["ops_cost"]) + sum(
                (Fraction(p) * Fraction(e) for p, e in zip(prices, replay["load"])),
                Fraction(0))
            assessment["planner_plan_hash"] = parent["plan_hash"]
            assessment["planner_own_price_bill_exact"] = str(bill)
            assessment["own_price_regret_interval_exact"] = (
                regret_interval(bill, assessment["bounds"]) if assessment["bounds"] else None)
        base.save_new(dest / "result.json", {"case": name, "market": kind, "stage": stage,
                                              "assessment": assessment,
                                              "elapsed_seconds": time.monotonic() - started})
        return 0
    except Exception as exc:
        base.save_new(dest / "exception.json", {"type": type(exc).__name__,
                                                "message": str(exc),
                                                "traceback": traceback.format_exc(),
                                                "elapsed_seconds": time.monotonic() - started})
        return 2


def stage_row(path, name, kind, stage, receipt=None):
    dest = folder(path, name, kind, stage)
    row = {"case": name, "market": kind, "state_index": qp.state(kind),
           "stage": stage, "outcome": "unstarted", "native_status": None,
           "complete_evidence": False, "on_time": None, "child_wall_s": None,
           "lower_exact": None, "upper_exact": None, "executable_cost_exact": None,
           "plan_hash": None, "planner_plan_hash": None,
           "own_price_bill_exact": None, "regret_lower_exact": None,
           "regret_upper_exact": None, "native_calls": None,
           "native_solver_wall_recorded_s": None,
           "native_solver_wall_complete": None, "model_construction_s": None}
    if receipt is None and (dest / "receipt.json").is_file():
        try:
            receipt = _read(dest / "receipt.json")
        except (OSError, ValueError, TypeError):
            row["outcome"] = "receipt_unreadable"
    if receipt is not None:
        row["on_time"], row["child_wall_s"] = receipt.get("on_time"), receipt.get("elapsed_seconds")
        row["outcome"] = ("hard_timeout" if receipt.get("hard_timeout") else
                          "failed" if receipt.get("returncode") != 0 else
                          "late" if receipt.get("on_time") is not True else "returned")
    elif row["outcome"] == "unstarted" and (dest / "ineligible.json").is_file():
        row["outcome"] = "ineligible"
    elif row["outcome"] == "unstarted" and (dest / "launch.json").exists():
        row["outcome"] = "interrupted_unreceipted"
    raw_path = dest / "raw_result.json"
    if raw_path.is_file():
        try:
            raw = _read(raw_path)["result"]
            row["native_status"] = raw.get("status")
            stats = ([item.get("stats") for item in raw.get("rounds", [])]
                     if stage == "planner" else [raw.get("stats")])
            row["native_calls"] = len([item for item in stats if item is not None])
            walls = [item.get("wall_s") for item in stats if isinstance(item, dict)]
            if walls and all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in walls):
                row["native_solver_wall_recorded_s"] = sum(walls)
                row["native_solver_wall_complete"] = len(walls) == row["native_calls"]
        except (OSError, ValueError, TypeError, KeyError):
            row["raw_read_error"] = True
    if row["outcome"] == "returned" and (dest / "result.json").is_file():
        try:
            saved = _read(dest / "result.json")
            assessment = saved["assessment"]
            raw = _read(raw_path)["result"]
            if ((saved.get("case"), saved.get("market"), saved.get("stage")) !=
                    (name, kind, stage)
                    or assessment.get("status") != raw.get("status")
                    or assessment.get("bounds") != retrieval.finite_bounds(raw)
                    or assessment.get("status") not in ("certified", "bounded")
                    or assessment.get("plan_replayed") is not True
                    or not assessment.get("bounds")
                    or not isinstance(assessment.get("replay"), dict)
                    or raw.get("case_identity") != cases()[name].identity()
                    or raw.get("formulation") != pf.FORMULATION
                    or raw.get("extraction_policy") != pf.EXTRACTION_POLICY
                    or raw.get("plan") is None
                    or assessment.get("plan_hash") != nr.digest(raw["plan"])):
                raise ValueError("Physical assessment not admissible")
            lo, hi = map(Fraction, assessment["bounds"])
            if lo > hi:
                raise ValueError("Physical interval reversed")
            row.update(outcome=assessment["status"], complete_evidence=True,
                       lower_exact=str(lo), upper_exact=str(hi),
                       plan_hash=assessment.get("plan_hash"))
            if stage == "planner":
                m = market(name, kind)
                if raw.get("a") != list(m.a) or raw.get("b") != list(m.b):
                    raise ValueError("Planner market mismatch")
                row["executable_cost_exact"] = assessment.get("executable_cost_exact")
            else:
                parent = planner_admitted(path, name, kind)
                prices = _read(dest / "prices.json")
                if (parent is None
                        or assessment.get("planner_plan_hash") != parent.get("plan_hash")
                        or (prices.get("case"), prices.get("market")) != (name, kind)
                        or prices.get("planner_plan_hash") != parent.get("plan_hash")
                        or prices.get("prices") != gradient(market(name, kind), parent["replay"]["load"])
                        or raw.get("prices") != prices["prices"]):
                    raise ValueError("Response incumbent/price lineage mismatch")
                bill = Fraction(parent["replay"]["ops_cost"]) + sum(
                    (Fraction(p) * Fraction(e) for p, e in
                     zip(prices["prices"], parent["replay"]["load"])), Fraction(0))
                if (assessment.get("planner_own_price_bill_exact") != str(bill)
                        or assessment.get("own_price_regret_interval_exact") !=
                        regret_interval(bill, assessment["bounds"])):
                    raise ValueError("Response regret arithmetic mismatch")
                row.update(planner_plan_hash=assessment.get("planner_plan_hash"),
                           own_price_bill_exact=assessment.get("planner_own_price_bill_exact"))
                if assessment.get("own_price_regret_interval_exact"):
                    reg_lo, reg_hi = map(Fraction, assessment["own_price_regret_interval_exact"])
                    if reg_lo < 0 or reg_lo > reg_hi:
                        raise ValueError("Response regret interval invalid")
                    row.update(regret_lower_exact=str(reg_lo), regret_upper_exact=str(reg_hi))
        except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError):
            row["outcome"] = "partial_result"
            row["complete_evidence"] = False
            row["lower_exact"] = row["upper_exact"] = None
            for key in ("executable_cost_exact", "plan_hash", "planner_plan_hash",
                        "own_price_bill_exact", "regret_lower_exact", "regret_upper_exact"):
                row[key] = None
    elif row["outcome"] == "returned":
        row["outcome"] = "returned_unassessed"
    return row


def cell_summary(name, kind, planner, response, hull):
    output = {"case": name, "market": kind,
              "hull_source_job_id": hull["source_job_id"],
              "hull_source_commit": hull["source_commit"],
              "CH_interval_exact": [hull["lower_exact"], hull["upper_exact"]],
              "D_interval_exact": None, "combined_D_interval_exact": None,
              "combined_CH_interval_exact": None,
              "D_minus_CH_interval_exact": None,
              "incumbent_plan_hash": None, "incumbent_own_price_regret_interval_exact": None}
    if planner.get("complete_evidence") is True:
        d = [planner["lower_exact"], planner["upper_exact"]]
        output["D_interval_exact"] = d
        output["incumbent_plan_hash"] = planner.get("plan_hash")
        try:
            combined = combined_intervals(d, output["CH_interval_exact"])
            output["combined_D_interval_exact"] = combined["D_interval_exact"]
            output["combined_CH_interval_exact"] = combined["CH_interval_exact"]
            output["D_minus_CH_interval_exact"] = combined["D_minus_CH_interval_exact"]
        except ValueError:
            output["inconsistent_native_bounds"] = True
    if (response.get("complete_evidence") is True
            and planner.get("complete_evidence") is True
            and response.get("planner_plan_hash") == planner.get("plan_hash")
            and response.get("regret_lower_exact") is not None):
        output["incumbent_own_price_regret_interval_exact"] = [
            response["regret_lower_exact"], response["regret_upper_exact"]]
    return output


def controller(path):
    target = _attempt(path)
    spec = frozen(target)
    base.save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows, comparisons = [], []
    for name, kind in cells():
        pair = {}
        for stage in STAGES:
            dest = folder(target, name, kind, stage)
            dest.mkdir(parents=True, exist_ok=False)
            if stage == "response" and planner_admitted(target, name, kind) is None:
                base.save_new(dest / "ineligible.json", {"reason": "no on-time replayed bounded planner"})
                row = stage_row(target, name, kind, stage)
            else:
                command = [sys.executable, "-m", "experiments.economic_support_diagnostic",
                           "worker", "--attempt", str(target), "--case", name,
                           "--market", kind, "--stage", stage]
                receipt = base.launch_child(target, name, qp.state(kind), stage,
                                            HARD_SECONDS[stage], command=command)
                row = stage_row(target, name, kind, stage, receipt)
            pair[stage] = row
            rows.append(row)
        comparisons.append(cell_summary(name, kind, pair["planner"], pair["response"],
                                        spec["design"]["hull_source"][f"{name}/{kind}"]))
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                                             "comparisons": comparisons,
                                             "declared_cells": 6, "accounted_cells": 6,
                                             "declared_stages": 12, "accounted_stages": len(rows),
                                             "all_declared_stages_accounted": len(rows) == 12,
                                             "scientific_admission": "pending independent result review"})
    return 0


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if _read(target / "summary.json").get("accounted_stages") == 12:
                return
        except (OSError, ValueError, TypeError):
            pass
    rows = [stage_row(target, name, kind, stage)
            for name, kind in cells() for stage in STAGES]
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL,
                                                        "rows": rows,
                                                        "declared_stages": 12,
                                                        "accounted_stages": len(rows),
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
        command = [sys.executable, "-m", "experiments.economic_support_diagnostic",
                   "controller", "--attempt", str(target)]
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
        unchanged = source_hashes() == _read(target / "frozen.json")["source_hashes"]
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
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "supervise",
                                         "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=qp.CASES)
    parser.add_argument("--market", choices=qp.KINDS)
    parser.add_argument("--stage", choices=STAGES)
    args = parser.parse_args(argv)
    if args.mode == "design":
        print(json.dumps(design(), indent=2, sort_keys=True))
        return 0
    if args.mode == "freeze":
        freeze(args.attempt)
        return 0
    if args.mode == "preflight":
        frozen(args.attempt)
        print(json.dumps({"runtime": qp.software_runtime(), "host": sizing.host_environment(),
                          "native_probe": sizing.native_probe()}, sort_keys=True))
        return 0
    if args.mode == "supervise":
        return supervise(args.attempt)
    if args.mode == "controller":
        return controller(args.attempt)
    if args.case is None or args.market is None or args.stage is None:
        parser.error("worker requires --case, --market, and --stage")
    return worker(args.attempt, args.case, args.market, args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
