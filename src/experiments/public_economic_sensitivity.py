"""Eight-cell public fee/curvature sensitivity with fresh D, CH and response."""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from fractions import Fraction
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from egglab import native_hull as nh
from egglab import native_pathflow as pf
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import computational_benchmark as base
from experiments import budget_sizing_diagnostic as sizing
from experiments import qp_baseline_diagnostic as qp
from experiments import retrieval_comparison as retrieval


ROOT = base.ROOT
ATTEMPT = ROOT / "result/public_economic_sensitivity/20260929-attempt1"
PROTOCOL = "egg-public-economic-sensitivity-development-20260929-v1"
STAGES = ("planner", "cold_hull", "response")
KINDS = ("market0",)
SCENARIOS = ((100, 1), (40, 1), (20, 1), (40, 2))
DEPOTS = ("public_depot15", "public_depot16")
CASE_IDS = tuple(f"{depot}_f{fee}_k{mult}" for fee, mult in SCENARIOS for depot in DEPOTS)
HARD_SECONDS = {"planner": 210, "cold_hull": 210, "response": 90}
CONTROLLER_CAP_SECONDS = 5400
RESERVE_SECONDS = 10.0
QP_DENOMINATOR = 1_000_000_000
QP_MAXITER = 500
ANALYTIC = ROOT / "research-20260929/charging-availability-bound/bounds.json"
SOURCE_FILES = (
    "src/experiments/public_economic_sensitivity.py",
    "src/tests/test_public_economic_sensitivity.py",
    "src/cluster/public_economic_sensitivity.sbatch",
    "research-20260929/public-economic-sensitivity/DESIGN.md",
    "research-20260929/public-economic-sensitivity/IMPLEMENTATION.md",
    "research-20260929/public-economic-sensitivity/README.md",
    "research-20260929/economic-support-diagnostic/NEXT_PUBLIC_SENSITIVITY.md",
    "research-20260929/charging-availability-bound/bounds.json",
    "research-20260929/charging-availability-bound/compute.py",
    "research-20260929/charging-availability-bound/PROOF.md",
    "src/experiments/qp_baseline_diagnostic.py",
    "src/experiments/retrieval_comparison.py",
    "src/experiments/computational_benchmark.py",
    "src/experiments/budget_sizing_diagnostic.py",
    "src/experiments/sistig_native_case.py",
    "data/public/sistig_26088190_v1/hildenbrand_native_cases.json",
    "src/egglab/native_hull.py",
    "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py",
    "src/egglab/native_recharge.py",
    "src/egglab/restricted_qp_proposal.py",
    "src/egglab/solver.py",
    "src/cluster/unicorn_env.sh",
)


def state(kind):
    if kind != "market0":
        raise ValueError("Undeclared market")
    return 0


def cells():
    return tuple((name, "market0") for name in CASE_IDS)


def scenario(name):
    for fee, mult in SCENARIOS:
        for depot in DEPOTS:
            if name == f"{depot}_f{fee}_k{mult}":
                return depot, fee, mult
    raise ValueError("Undeclared economic scenario")


@lru_cache(maxsize=1)
def base_cases():
    original = base.cases()
    return {name: original[name] for name in DEPOTS}


@lru_cache(maxsize=1)
def cases():
    original = base_cases()
    built = {}
    for name in CASE_IDS:
        depot, fee, _ = scenario(name)
        case = replace(original[depot], name=name, vehicle_cost=float(fee))
        if (case.identity() == original[depot].identity()
                or case.vehicle_cost != fee
                or replace(case, name=original[depot].name,
                           vehicle_cost=original[depot].vehicle_cost) != original[depot]):
            raise ValueError("Modified public case does not preserve physical inputs")
        nr.validate_case(case)
        built[name] = case
    return built


def market(name, kind):
    state(kind)
    _, _, mult = scenario(name)
    return nh.Market(name + "-market0", (0.2,) * 30, (mult / 900,) * 30)


def budget(stage):
    if stage not in STAGES:
        raise ValueError("Undeclared stage")
    if stage == "cold_hull":
        return nh.Budget(backend="GRB", threads=1, phase_seconds=160,
                         wall_seconds=180, pricing_calls=16, master_calls=64,
                         pool_cap=64, epsilon=1e-4, pool_tolerance=1e-6,
                         polish_steps=64, rational_bits=8192, polish_seconds=20)
    return nr.Budget(backend="GRB", threads=1,
                     phase_seconds=160 if stage == "planner" else 45,
                     wall_seconds=180 if stage == "planner" else 60,
                     max_rounds=16 if stage == "planner" else 1,
                     epsilon=1e-4)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in SOURCE_FILES}


def _read(path):
    return json.loads(Path(path).read_text())


@lru_cache(maxsize=1)
def analytical_floors():
    grid = _read(ANALYTIC)
    if grid.get("scope") != "exact ideal stored-input hull lower bounds; reporting only; no native solves":
        raise ValueError("Analytical floor scope changed")
    originals = base_cases()
    for depot in DEPOTS:
        base_rows = [r for r in grid.get("rows", []) if r.get("case") == depot and r.get("state") == 0]
        if len(base_rows) != 1 or base_rows[0].get("case_identity") != originals[depot].identity():
            raise ValueError("Analytical floor base physical identity differs")
        declared_market = base.market(depot, 0)
        if base.canonical(base_rows[0].get("market")) != base.canonical(asdict(declared_market)):
            raise ValueError("Analytical floor base market differs")
    floors = {}
    for name in CASE_IDS:
        depot, fee, mult = scenario(name)
        matches = [r for r in grid["analytical_sensitivity_only"]
                   if (r.get("case"), r.get("state"), r.get("bus_cost"),
                       r.get("curvature_multiplier")) == (depot, 0, fee, mult)]
        if len(matches) != 1:
            raise ValueError("Missing or duplicated scoped analytical floor")
        value = Fraction(matches[0]["lower_exact"])
        floors[name] = {"lower_exact": str(value),
                        "scope": "ideal stored-input model; reporting only",
                        "base_case_identity": originals[depot].identity(),
                        "modified_case_identity": cases()[name].identity(),
                        "market_identity": market(name, "market0").identity(),
                        "source_sha256": base.sha(ANALYTIC)}
    return floors


@lru_cache(maxsize=1)
def design():
    built = cases()
    return {"cases": {name: {"case_identity": item.identity(),
                              "base_case_identity": base_cases()[scenario(name)[0]].identity(),
                              "base_group": "hildenbrand_37",
                              "scenario": {"bus_fee": scenario(name)[1],
                                           "curvature_multiplier": scenario(name)[2]},
                              "market_identities": {"market0": market(name, "market0").identity()},
                              "market": asdict(market(name, "market0"))}
                      for name, item in built.items()},
            "order": [{"case": name, "market": kind, "state_index": state(kind)}
                      for name, kind in cells()],
            "budgets": {stage: asdict(budget(stage)) for stage in STAGES},
            "hard_child_seconds": HARD_SECONDS,
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS,
            "analytical_floors": analytical_floors(),
            "arm": "cold", "master_policy": "numerical_qp_proposal",
            "qp_denominator": QP_DENOMINATOR, "qp_maxiter": QP_MAXITER,
            "pricing_reserve_seconds": RESERVE_SECONDS,
            "bound_cache_policy": "none", "development_only": True,
            "independent_test_data": False}


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the exclusive public sensitivity attempt is allowed")
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
            "controller_cap_seconds": CONTROLLER_CAP_SECONDS, "declared_cells": 8,
            "declared_stages": 24, "scientific_admission": "pending independent review"}
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
            or spec.get("declared_cells") != 8 or spec.get("declared_stages") != 24):
        raise ValueError("Frozen public sensitivity design differs")
    return spec


def folder(path, name, kind, stage):
    return Path(path) / name / f"state{state(kind)}" / stage


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
        elif stage == "cold_hull":
            result = compact.certify(item, m, cfg, arm="cold", state_index=0,
                                     record=record, pricing_reserve_seconds=RESERVE_SECONDS,
                                     master_policy="numerical_qp_proposal",
                                     qp_denominator=QP_DENOMINATOR, qp_maxiter=QP_MAXITER)
            if (result.get("state_identity") != compact.state_identity(
                    item, m, "cold", 0, cfg,
                    pricing_reserve_seconds=RESERVE_SECONDS,
                    master_policy="numerical_qp_proposal",
                    qp_denominator=QP_DENOMINATOR, qp_maxiter=QP_MAXITER)
                    or result.get("physical_identity") != item.identity()
                    or result.get("market_identity") != m.identity()
                    or result.get("arm") != "cold" or result.get("state_index") != 0
                    or result.get("pricing_reserve_seconds") != RESERVE_SECONDS
                    or result.get("master_policy") != "numerical_qp_proposal"
                    or result.get("qp_denominator") != QP_DENOMINATOR
                    or result.get("qp_maxiter") != QP_MAXITER):
                raise ValueError("Fresh QP hull state/control identity differs")
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
        assessment = (base.assess(item, m, "cold_hull", result)
                      if stage == "cold_hull" else
                      retrieval.assess_physical(item, m, stage, result, prices))
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
    row = {"case": name, "market": kind, "state_index": state(kind),
           "stage": stage, "outcome": "unstarted", "native_status": None,
           "stop_reason": None,
           "complete_evidence": False, "on_time": None, "child_wall_s": None,
           "lower_exact": None, "upper_exact": None, "executable_cost_exact": None,
           "plan_hash": None, "planner_plan_hash": None,
           "own_price_bill_exact": None, "regret_lower_exact": None,
           "regret_upper_exact": None, "native_calls": None,
           "native_solver_wall_recorded_s": None,
           "native_solver_wall_complete": None, "model_construction_s": None,
           "pricing_requests": None, "master_calls": None,
           "max_rational_bits": None, "polish_wall_s": None,
           "qp_proposal_calls": None, "qp_non_success": None,
           "qp_proposal_wall_s": None, "qp_replay_wall_s": None,
           "planner_width_exact": None, "used_buses": None}
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
            row["stop_reason"] = raw.get("reason")
            if stage == "cold_hull":
                counts = raw.get("counts", {})
                for key in ("pricing_requests", "master_calls", "max_rational_bits",
                            "polish_wall_s", "qp_proposal_calls", "qp_non_success",
                            "qp_proposal_wall_s", "qp_replay_wall_s"):
                    row[key] = counts.get(key)
            else:
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
            if stage == "cold_hull":
                m = market(name, kind)
                if ((saved.get("case"), saved.get("market"), saved.get("stage")) !=
                        (name, kind, stage)
                        or assessment.get("status") != raw.get("status")
                        or assessment.get("status") not in
                        ("certified", "budget_exhausted", "stalled_bounded")
                        or assessment.get("complete_evidence") is not True
                        or not assessment.get("bounds")
                        or assessment.get("bounds") != base.finite_bounds(raw)
                        or raw.get("physical_identity") != cases()[name].identity()
                        or raw.get("market_identity") != m.identity()
                        or raw.get("master_policy") != "numerical_qp_proposal"
                        or raw.get("qp_denominator") != QP_DENOMINATOR
                        or raw.get("qp_maxiter") != QP_MAXITER
                        or raw.get("pricing_reserve_seconds") != RESERVE_SECONDS
                        or raw.get("arm") != "cold" or raw.get("state_index") != 0
                        or raw.get("state_identity") != compact.state_identity(
                            cases()[name], m, "cold", 0, budget("cold_hull"),
                            pricing_reserve_seconds=RESERVE_SECONDS,
                            master_policy="numerical_qp_proposal",
                            qp_denominator=QP_DENOMINATOR, qp_maxiter=QP_MAXITER)):
                    raise ValueError("QP hull assessment not admissible")
                lo = Fraction(raw["lower_certificate"]["lower_exact"])
                hi = Fraction(raw["mixture"]["objective_exact"])
                assessed_lo, assessed_hi = map(Fraction, assessment["bounds"])
                if lo > hi or assessed_lo > lo or assessed_hi < hi:
                    raise ValueError("QP hull enclosure invalid")
                row.update(outcome=assessment["status"], complete_evidence=True,
                           lower_exact=str(lo), upper_exact=str(hi))
                return row
            if ((saved.get("case"), saved.get("market"), saved.get("stage")) !=
                    (name, kind, stage)
                    or assessment.get("status") != raw.get("status")
                    or assessment.get("bounds") != retrieval.finite_bounds(raw)
                    or assessment.get("status") not in ("certified", "bounded")
                    or assessment.get("plan_replayed") is not True
                    or not assessment.get("bounds")
                    or not isinstance(assessment.get("replay"), dict)
                    or raw.get("case_identity") != cases()[name].identity()
                    or (stage == "planner" and
                        (raw.get("a") != list(market(name, kind).a) or
                         raw.get("b") != list(market(name, kind).b)))
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
                       plan_hash=assessment.get("plan_hash"),
                       used_buses=len(raw["plan"]["vehicles"]))
            if stage == "planner":
                m = market(name, kind)
                if raw.get("a") != list(m.a) or raw.get("b") != list(m.b):
                    raise ValueError("Planner market mismatch")
                row["executable_cost_exact"] = assessment.get("executable_cost_exact")
                row["planner_width_exact"] = str(hi - lo)
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
                        "own_price_bill_exact", "regret_lower_exact", "regret_upper_exact",
                        "planner_width_exact", "used_buses"):
                row[key] = None
    elif row["outcome"] == "returned":
        row["outcome"] = "returned_unassessed"
    return row


def cell_summary(name, kind, planner, hull, response, analytic):
    output = {"case": name, "market": kind,
              "base_group": "hildenbrand_37", "scenario": {"bus_fee": scenario(name)[1],
                  "curvature_multiplier": scenario(name)[2]},
              "case_identity": cases()[name].identity(),
              "market_identity": market(name, kind).identity(),
              "analytical_ideal_lower_exact": analytic["lower_exact"],
              "analytical_scope": analytic["scope"],
              "D_interval_exact": None, "CH_interval_exact": None,
              "combined_D_interval_exact": None, "combined_CH_interval_exact": None,
              "D_minus_CH_interval_exact": None, "planner_width_exact": None,
              "incumbent_plan_hash": None, "incumbent_used_buses": None,
              "incumbent_own_price_regret_interval_exact": None}
    if planner.get("complete_evidence") is True:
        output["D_interval_exact"] = [planner["lower_exact"], planner["upper_exact"]]
        output["planner_width_exact"] = planner["planner_width_exact"]
        output["incumbent_plan_hash"] = planner.get("plan_hash")
        output["incumbent_used_buses"] = planner.get("used_buses")
    if hull.get("complete_evidence") is True:
        output["CH_interval_exact"] = [hull["lower_exact"], hull["upper_exact"]]
    if output["D_interval_exact"] and output["CH_interval_exact"]:
        try:
            combined = combined_intervals(output["D_interval_exact"],
                                          output["CH_interval_exact"])
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
                command = [sys.executable, "-m", "experiments.public_economic_sensitivity",
                           "worker", "--attempt", str(target), "--case", name,
                           "--market", kind, "--stage", stage]
                receipt = base.launch_child(target, name, state(kind), stage,
                                            HARD_SECONDS[stage], command=command)
                row = stage_row(target, name, kind, stage, receipt)
            pair[stage] = row
            rows.append(row)
        comparisons.append(cell_summary(name, kind, pair["planner"], pair["cold_hull"],
                                        pair["response"],
                                        spec["design"]["analytical_floors"][name]))
    base.save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
                                             "comparisons": comparisons,
                                             "declared_cells": 8, "accounted_cells": 8,
                                             "declared_stages": 24, "accounted_stages": len(rows),
                                             "all_declared_stages_accounted": len(rows) == 24,
                                             "scientific_admission": "pending independent result review"})
    return 0


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if _read(target / "summary.json").get("accounted_stages") == 24:
                return
        except (OSError, ValueError, TypeError):
            pass
    rows = [stage_row(target, name, kind, stage)
            for name, kind in cells() for stage in STAGES]
    base.save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL,
                                                        "rows": rows,
                                                        "declared_stages": 24,
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
        command = [sys.executable, "-m", "experiments.public_economic_sensitivity",
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
    parser.add_argument("--case", choices=CASE_IDS)
    parser.add_argument("--market", choices=KINDS)
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
