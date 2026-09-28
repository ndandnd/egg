"""Prospective development-only whole-fleet retrieval comparison.

Import is inert. A frozen, exclusive attempt is required before any worker runs.
The derived pool envelope is an API adapter, not a source certificate.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
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
from experiments import native_scaling_cases as scaling
from experiments import sistig_native_case as intake

ROOT = base.ROOT
ATTEMPT = ROOT / "result/retrieval_comparison/20260928-attempt1"
PROTOCOL = "egg-retrieval-comparison-development-20260928-v1"
PUBLIC_PAYLOAD = "data/public/sistig_26088190_v1/eberbach_native_case.json"
PUBLIC_SHA = "5ffb2f3a322b40c9c6c56972607fd0c4b21130cd35cd08e0a465f34fba67dc19"
PUBLIC_CASE = "sistig_eberbach_single_depot_36_eb3"
PUBLIC_ID = "9dc30e1034953808e0c98cd467ae02272eaf6ddde2428a326d26b08b6db94c48"
SYNTHETIC_CASES = (
    "native_scale_dev_s1006_n08", "native_scale_dev_s1006_n16",
    "native_scale_dev_s1006_n24", "native_scale_dev_s1012_n16",
    "native_scale_dev_s1009_n16",
)
CASES = (*SYNTHETIC_CASES, PUBLIC_CASE)
SOURCES = ("source0", "source1")
ARMS = ("cold", "retained", "nearest_price", "cheapest_bill")
STAGES = (*SOURCES, "planner", "response", *ARMS)
CONTROLLER_CAP = 6900
SUPERVISOR_CAP = 7100
CHILD_MARGIN = 30
SOURCE_FILES = ("events.jsonl", "raw_result.json", "result.json", "receipt.json")
HASHED_SOURCES = (
    "src/experiments/retrieval_comparison.py",
    "src/tests/test_retrieval_comparison.py",
    "src/cluster/retrieval_comparison.sbatch",
    "research-20260928/retrieval-comparison/RUNNER.md",
    "doc/RETRIEVAL_COMPARISON_PROTOCOL_20260928.md",
    "src/experiments/native_scaling_cases.py",
    "research-20260928/retrieval-comparison/SYNTHETIC_PREFLIGHT.json",
    "src/experiments/sistig_native_case.py",
    "src/experiments/computational_benchmark.py",
    "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py",
    "src/egglab/native_pathflow.py", "src/egglab/native_recharge.py",
    "src/egglab/restricted_qp_proposal.py", "src/cluster/unicorn_env.sh",
    PUBLIC_PAYLOAD,
)
HULL_CONTROLS = dict(reuse_policy="feasible_pool", pricing_reserve_seconds=10.0,
                     master_policy="numerical_qp_proposal", bound_cache_policy="none")


def _attempt(path):
    target = Path(path).resolve()
    if target != ATTEMPT.resolve():
        raise ValueError("Only the exclusive prospective attempt is permitted")
    return target


def save_new(path, obj):
    base.save_new(path, obj)


def canonical(obj):
    return base.canonical(obj)


def source_hashes():
    return {name: base.sha(ROOT / name) for name in HASHED_SOURCES}


def cases():
    built = scaling.cases()
    if tuple(built) != SYNTHETIC_CASES:
        raise ValueError("Synthetic case order changed")
    preflight = json.loads((ROOT / "research-20260928/retrieval-comparison/SYNTHETIC_PREFLIGHT.json").read_text())
    if ([row["name"] for row in preflight.get("cases", [])] != list(SYNTHETIC_CASES)
            or preflight.get("generator_source_sha256") != base.sha(ROOT / "src/experiments/native_scaling_cases.py")
            or any(built[row["name"]].identity() != row["case_identity"] for row in preflight["cases"])):
        raise ValueError("Synthetic preflight identity changed")
    raw = (ROOT / PUBLIC_PAYLOAD).read_bytes()
    if base.sha(ROOT / PUBLIC_PAYLOAD) != PUBLIC_SHA:
        raise ValueError("Public payload changed")
    variants = json.loads(raw)["native_cases"]
    if len(variants) != 1:
        raise ValueError("Expected one selected Eberbach depot")
    public = intake.native_case_from_payload(variants[0])
    if public.name != PUBLIC_CASE or public.identity() != PUBLIC_ID:
        raise ValueError("Public physical identity changed")
    built[PUBLIC_CASE] = public
    for name, case in built.items():
        nr.validate_case(case)
        if len(case.market_edges_min) != 31 or tuple(case.market_edges_min) != tuple(range(0, 1801, 60)):
            raise ValueError("Expected exactly 30 hourly market periods: " + name)
    return built


def market(case_name, kind):
    if case_name not in CASES or kind not in (*SOURCES, "target"):
        raise ValueError("Unknown case/market")
    if kind == "source0":
        a = (0.20,) * 30
    elif kind == "source1":
        a = tuple(0.10 if 18 <= t < 22 else 0.30 for t in range(30))
    else:
        a = tuple(0.10 if 22 <= t < 26 else 0.30 for t in range(30))
    return nh.Market(case_name + "-" + kind, a, (1 / 900,) * 30)


def budget(case_name, stage):
    if case_name not in CASES or stage not in STAGES:
        raise ValueError("Unknown case/stage")
    public = case_name == PUBLIC_CASE
    wall = (240 if public else 60) if stage in (*SOURCES, "planner", "response") else (300 if public else 90)
    phase = min(wall, 200 if public else 50)
    if stage in (*SOURCES, *ARMS):
        return nh.Budget(backend="GRB", threads=1, phase_seconds=phase,
                         wall_seconds=wall, pricing_calls=4, master_calls=6,
                         pool_cap=32, epsilon=1e-4, pool_tolerance=1e-6,
                         polish_steps=64, rational_bits=4096, polish_seconds=20)
    return nr.Budget(backend="GRB", threads=1, phase_seconds=phase,
                     wall_seconds=wall, max_rounds=8 if stage == "planner" else 1,
                     epsilon=1e-4)


def arm_order(case_index):
    shift = case_index % len(ARMS)
    return ARMS[shift:] + ARMS[:shift]


def stage_order(case_index):
    return (*SOURCES, "planner", "response", *arm_order(case_index))


def design():
    built = cases()
    rows = {}
    for index, name in enumerate(CASES):
        case = built[name]
        rows[name] = {
            "case": asdict(case), "case_identity": case.identity(),
            "base_group": (name.split("_n")[0] if name in SYNTHETIC_CASES else "eberbach_105"),
            "markets": {kind: asdict(market(name, kind)) for kind in (*SOURCES, "target")},
            "market_identities": {kind: market(name, kind).identity() for kind in (*SOURCES, "target")},
            "budgets": {stage: asdict(budget(name, stage)) for stage in STAGES},
            "stage_order": list(stage_order(index)),
            "hard_child_seconds": {stage: budget(name, stage).wall_seconds + CHILD_MARGIN for stage in STAGES},
        }
    return rows


def native_probe():
    """Check effective GRB backend/seed without optimizing a model."""
    import mip
    model = mip.Model(name="retrieval-comparison-preflight", sense=mip.MINIMIZE, solver_name="GRB")
    identity = nr._backend_identity(model, "GRB")
    seed = model.seed
    if type(seed) is not int:
        raise ValueError("Native model seed is not an integer")
    return {"backend_identity": identity, "model_seed": seed}


def freeze(path):
    target = _attempt(path)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
        raise ValueError("Tracked execution source is not clean")
    spec = {"protocol": PROTOCOL, "source_commit": commit,
            "source_hashes": source_hashes(), "environment": base.environment(),
            "native_probe": native_probe(), "cases": design(),
            "hull_controls": HULL_CONTROLS,
            "controller_cap_seconds": CONTROLLER_CAP,
            "supervisor_cap_seconds": SUPERVISOR_CAP,
            "children_declared": 48, "development_only": True,
            "rng": "fixed model seed observed in native_probe"}
    target.mkdir(parents=True, exist_ok=False)
    save_new(target / "frozen.json", spec)
    return spec


def frozen(path, *, check_sources=True):
    target = _attempt(path)
    spec = json.loads((target / "frozen.json").read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (spec.get("protocol") != PROTOCOL or spec.get("source_commit") != commit
            or spec.get("environment") != base.environment()
            or canonical(spec.get("cases")) != canonical(design())
            or spec.get("hull_controls") != HULL_CONTROLS
            or spec.get("controller_cap_seconds") != CONTROLLER_CAP
            or spec.get("supervisor_cap_seconds") != SUPERVISOR_CAP
            or spec.get("children_declared") != 48
            or (check_sources and spec.get("source_hashes") != source_hashes())):
        raise ValueError("Frozen prospective design/source differs")
    return spec


def cell_dir(path, case_name, stage):
    return Path(path) / case_name / stage


def file_hashes(folder, names):
    return {name: {"sha256": base.sha(folder / name), "bytes": (folder / name).stat().st_size}
            for name in names if (folder / name).is_file()}


def read_events(folder):
    file = folder / "events.jsonl"
    if not file.is_file():
        return []
    return [json.loads(line) for line in file.read_text().splitlines()]


def finite_bounds(result):
    lower, upper = result.get("lower"), result.get("upper")
    if (type(lower) not in (int, float) or type(upper) not in (int, float)
            or not math.isfinite(lower) or not math.isfinite(upper) or lower > upper):
        return None
    return [str(Fraction(lower)), str(Fraction(upper))]


def _event_index(events, kind):
    indexed = {}
    for event in events:
        if event.get("event") != kind:
            continue
        call = event.get("call")
        if type(call) is not int or call < 0 or call in indexed:
            raise ValueError("Duplicate/malformed " + kind + " call")
        indexed[call] = event
    return indexed


def _candidate(case, source_market, source_identity, source_name, request, priced, bound):
    """Admit a source fleet only through its native pricing call and replay."""
    call = request["call"]
    prices, result, column = request.get("prices"), priced.get("result"), bound.get("column")
    if (not isinstance(prices, list) or len(prices) != 30
            or any(type(p) not in (int, float) or not math.isfinite(p) for p in prices)
            or not isinstance(result, dict) or not isinstance(column, dict)
            or result.get("case_identity") != case.identity()
            or result.get("prices") != prices
            or result.get("formulation") != compact.ORACLE_ID
            or result.get("extraction_policy") != compact.EXTRACTION_POLICY
            or result.get("status") not in ("certified", "bounded")
            or result.get("plan") != column.get("plan")
            or column.get("source", {}).get("state_identity") != source_identity
            or column.get("source", {}).get("pricing_call") != call
            or column.get("source", {}).get("pricing_oracle") != compact.ORACLE_ID):
        raise ValueError("Source pricing request/result/column lineage differs")
    nh.replay_column(case, column, compact.EXTRACTION_POLICY)
    objective = Fraction(column["ops_cost"]) + sum(
        (Fraction(p) * Fraction(x) for p, x in zip(prices, column["load"])), Fraction(0))
    native_objective = column["ops_cost"] + sum(p*x for p, x in zip(prices, column["load"]))
    if abs(float(objective) - native_objective) > nr.OBJECTIVE_TOL:
        raise ValueError("Source stored-number bill differs from native bill")
    lo, hi = nr.admit_bound(result["stats"], native_objective)
    if (result.get("lower") != lo
            or type(result.get("upper")) not in (int, float)
            or abs(result["upper"] - hi) > nr.OBJECTIVE_TOL
            or bound.get("certificate") != nh.fenchel_bound(source_market, prices, lo)):
        raise ValueError("Source price/native bound/global event differs")
    return {"source": source_name, "source_state_identity": source_identity,
            "call": call, "prices": prices, "key": column["key"],
            "witness_hash": column["witness_hash"], "column": column,
            "pricing_status": result["status"]}


def admit_source(path, case_name, source_name, pinned_files=None):
    """A failed source may still yield checked feasible columns; its failure stays visible."""
    folder = cell_dir(path, case_name, source_name)
    case, m, cfg = cases()[case_name], market(case_name, source_name), budget(case_name, source_name)
    files = file_hashes(folder, SOURCE_FILES)
    if pinned_files is not None and files != pinned_files:
        raise ValueError("Source files changed after pool admission")
    receipt = json.loads((folder / "receipt.json").read_text())
    paid = receipt.get("elapsed_seconds")
    if (receipt.get("hard_seconds") != cfg.wall_seconds + CHILD_MARGIN
            or type(paid) not in (int, float) or not math.isfinite(paid)
            or paid < 0):
        raise ValueError("Source receipt invalid")
    events = read_events(folder)
    requests = _event_index(events, "pricing_request")
    results = _event_index(events, "pricing_result")
    bounds = _event_index(events, "global_bound")
    identity = compact.state_identity(case, m, "retained", 0, cfg, **HULL_CONTROLS)
    if not requests or not bounds or not set(bounds) <= set(results) <= set(requests):
        raise ValueError("No complete source pricing evidence")
    candidates = [_candidate(case, m, identity, source_name,
                             requests[call], results[call], bounds[call]) for call in sorted(bounds)]
    raw_path = folder / "raw_result.json"
    raw_status = None
    if raw_path.is_file():
        wrapped = json.loads(raw_path.read_text())
        prior = wrapped["result"]
        raw_status = prior.get("status")
        if (wrapped.get("case") != case_name or wrapped.get("stage") != source_name
                or prior.get("schema") != nh.SCHEMA
                or prior.get("physical_identity") != case.identity()
                or prior.get("market_identity") != m.identity()
                or prior.get("state_identity") != identity
                or prior.get("arm") != "retained" or prior.get("state_index") != 0
                or prior.get("pricing_oracle") != compact.ORACLE_ID
                or prior.get("extraction_policy") != compact.EXTRACTION_POLICY
                or prior.get("reuse_policy") != HULL_CONTROLS["reuse_policy"]
                or prior.get("master_policy") != HULL_CONTROLS["master_policy"]
                or prior.get("pricing_reserve_seconds") != HULL_CONTROLS["pricing_reserve_seconds"]
                or prior.get("bound_cache_policy", "none") != "none"
                or raw_status not in ("certified", "bounded", "budget_exhausted", "stalled_bounded",
                                      "proposal_failed", "unresolved")):
            raise ValueError("Returned source result identity/policy differs")
        final_keys = [col["key"] for col in prior.get("columns", [])]
        if len(final_keys) != len(set(final_keys)) or not set(final_keys) <= {c["key"] for c in candidates}:
            raise ValueError("Returned source pool lacks matched pricing events")
        for col in prior.get("columns", []):
            if col not in [candidate["column"] for candidate in candidates]:
                raise ValueError("Returned source column differs from source event")
    return {"source": source_name, "files": files, "receipt": receipt,
            "raw_status": raw_status, "source_state_identity": identity,
            "source_market_identity": m.identity(), "candidates": candidates,
            "unused_request_calls": sorted(set(requests)-set(results)),
            "unused_result_calls": sorted(set(results)-set(bounds)),
            "paid_source_seconds": paid,
            "complete_source_return": receipt.get("on_time") is True and receipt.get("returncode") == 0}


def collect_pool(path, case_name):
    sources, candidates = {}, []
    for name in SOURCES:
        try:
            row = admit_source(path, case_name, name)
            sources[name] = {key: value for key, value in row.items() if key != "candidates"}
            sources[name]["eligible"] = True
            candidates.extend(row["candidates"])
        except (OSError, ValueError, KeyError, TypeError, IndexError, ArithmeticError, AttributeError) as exc:
            folder = cell_dir(path, case_name, name)
            receipt = None
            if (folder / "receipt.json").is_file():
                try:
                    receipt = json.loads((folder / "receipt.json").read_text())
                except ValueError:
                    pass
            sources[name] = {"source": name, "eligible": False,
                             "reason": f"{type(exc).__name__}: {exc}", "receipt": receipt,
                             "files": file_hashes(folder, SOURCE_FILES),
                             "paid_source_seconds": receipt.get("elapsed_seconds") if receipt else None}
    ties = {}
    for candidate in candidates:
        ties.setdefault(candidate["key"], []).append(
            {"source": candidate["source"], "call": candidate["call"], "prices": candidate["prices"]})
    return {"case": case_name, "physical_identity": cases()[case_name].identity(),
            "sources": sources, "candidates": candidates,
            "projection_price_label_ties": {key: labels for key, labels in ties.items() if len(labels) > 1},
            "unique_keys": list(ties), "eligible": bool(candidates)}


def checked_pool(path, case_name):
    saved = json.loads((Path(path) / case_name / "pool.json").read_text())
    for name in SOURCES:
        expected = saved["sources"][name]
        if file_hashes(cell_dir(path, case_name, name), SOURCE_FILES) != expected["files"]:
            raise ValueError("Source files changed after pool construction")
    rebuilt = collect_pool(path, case_name)
    if canonical(saved) != canonical(rebuilt):
        raise ValueError("Frozen per-case pool differs from source evidence")
    return saved


def exact_bill(column, prices):
    if len(prices) != len(column["load"]):
        raise ValueError("Price/load dimension mismatch")
    return Fraction(column["ops_cost"]) + sum(
        (Fraction(p) * Fraction(load) for p, load in zip(prices, column["load"])), Fraction(0))


def _candidate_tie(candidate):
    return (SOURCES.index(candidate["source"]), candidate["call"], candidate["key"])


def select(pool, m, arm):
    if arm not in ARMS or not pool["eligible"]:
        raise ValueError("No admitted retrieval pool")
    candidates = pool["candidates"]
    if arm == "retained":
        selected = []
        seen = set()
        for candidate in candidates:
            if candidate["key"] not in seen:
                selected.append(candidate)
                seen.add(candidate["key"])
        return selected
    if arm == "nearest_price":
        return [min(candidates, key=lambda c: (
            sum((Fraction(p)-Fraction(a))**2 for p, a in zip(c["prices"], m.a)),
            _candidate_tie(c)))]
    if arm == "cheapest_bill":
        return [min(candidates, key=lambda c: (exact_bill(c["column"], m.a), _candidate_tie(c)))]
    raise ValueError("Cold has no retrieved proposal")


def direct_proposals(case, m, selected):
    proposals = []
    for candidate in selected:
        column = candidate["column"]
        nh.replay_column(case, column, compact.EXTRACTION_POLICY)
        replay = nr.replay_native(case, column["plan"])
        if replay["load"] != column["load"] or replay["ops_cost"] != column["ops_cost"]:
            raise ValueError("Retrieved plan physical replay changed")
        nonlinear = Fraction(column["ops_cost"]) + nh.supply(m, column["load"])
        proposals.append({"key": candidate["key"], "source": candidate["source"],
                          "source_call": candidate["call"], "source_prices": candidate["prices"],
                          "repair": "identity/no repair: same physical case",
                          "bill_exact": str(exact_bill(column, m.a)),
                          "nonlinear_cost_exact": str(nonlinear),
                          "nonlinear_cost": float(nonlinear),
                          "physical_replay": replay,
                          "witness_hash": column["witness_hash"]})
    return proposals


def import_envelope(case, m, cfg, pool, selected):
    """Construct a replayed feasible-pool adapter; it carries no old lower bound."""
    if not selected or len(selected) > cfg.pool_cap:
        raise ValueError("Empty/oversized adapter selection")
    canonical_candidates = {(c["source"], c["call"], c["key"], c["witness_hash"]): c
                            for c in pool["candidates"]}
    for candidate in selected:
        key = (candidate["source"], candidate["call"], candidate["key"], candidate["witness_hash"])
        if key not in canonical_candidates or canonical(candidate) != canonical(canonical_candidates[key]):
            raise ValueError("Selected subset differs from admitted source column")
    if len({c["key"] for c in selected}) != len(selected):
        raise ValueError("Adapter selection contains duplicate projection")
    lineage = {"kind": "derived_feasible_pool_import", "physical_identity": case.identity(),
               "source_files": {name: pool["sources"][name]["files"] for name in SOURCES},
               "source_state_ids": {name: pool["sources"][name].get("source_state_identity") for name in SOURCES},
               "source_price_labels": [{"source": c["source"], "call": c["call"],
                                        "prices": c["prices"], "key": c["key"],
                                        "witness_hash": c["witness_hash"]} for c in pool["candidates"]],
               "selected_keys": [c["key"] for c in selected], "policy": HULL_CONTROLS}
    digest = nr.digest(lineage)
    bridge_market = nh.Market("derived-feasible-pool-" + digest, m.a, m.b)
    identity = compact.state_identity(case, bridge_market, "retained", 0, cfg, **HULL_CONTROLS)
    columns = []
    for candidate in selected:
        original = candidate["column"]
        nh.replay_column(case, original, compact.EXTRACTION_POLICY)
        copied = json.loads(canonical(original))
        copied["source"] = {"state_identity": identity, "pricing_oracle": compact.ORACLE_ID,
                            "original_source": original["source"],
                            "original_source_name": candidate["source"],
                            "original_pricing_call": candidate["call"],
                            "original_source_prices": candidate["prices"]}
        columns.append(copied)
    envelope = {"schema": nh.SCHEMA, "kind": "derived_feasible_pool_import",
                "status": "bounded", "arm": "retained", "state_index": 0,
                "state_identity": identity, "physical_identity": case.identity(),
                "market_identity": bridge_market.identity(),
                "pricing_oracle": compact.ORACLE_ID,
                "extraction_policy": compact.EXTRACTION_POLICY,
                "reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10.0,
                "master_policy": "numerical_qp_proposal", "qp_denominator": 1_000_000_000,
                "qp_maxiter": 500, "lineage": lineage, "lineage_digest": digest,
                "columns": columns}
    feasible = [nh.replay_mixture(case, m, [column], [1.0], compact.EXTRACTION_POLICY)
                for column in columns]
    best = min(feasible, key=lambda mixture: Fraction(mixture["objective_exact"]))
    envelope.update(mixture=best, upper=best["upper"])
    for column in nh.import_pool(case, envelope, identity, cfg, previous_index=0,
                                 extraction_policy=compact.EXTRACTION_POLICY,
                                 reuse_policy="feasible_pool", oracle_id=compact.ORACLE_ID,
                                 pricing_reserve_seconds=10.0):
        if column["source"].get("original_source") is None:
            raise ValueError("Adapter lost source provenance")
    return envelope, identity


def assess_hull(case, m, result):
    if (result.get("schema") != nh.SCHEMA or result.get("physical_identity") != case.identity()
            or result.get("market_identity") != m.identity()
            or result.get("pricing_oracle") != compact.ORACLE_ID
            or result.get("extraction_policy") != compact.EXTRACTION_POLICY
            or result.get("reuse_policy") != "feasible_pool"
            or result.get("master_policy") != "numerical_qp_proposal"
            or result.get("pricing_reserve_seconds") != 10.0
            or result.get("bound_cache_policy", "none") != "none"):
        raise ValueError("Target hull policy/identity differs")
    columns = result.get("columns", [])
    if len({col["key"] for col in columns}) != len(columns):
        raise ValueError("Duplicate target hull projection")
    for col in columns:
        nh.replay_column(case, col, compact.EXTRACTION_POLICY)
    assessment = {"status": result.get("status"), "bounds": finite_bounds(result),
                  "columns": len(columns), "counts": result.get("counts"),
                  "global_certificate_replayed": False,
                  "mixture_replayed": False}
    cert = result.get("lower_certificate")
    if (cert is None) != (result.get("lower") is None):
        raise ValueError("Target global lower and certificate presence differ")
    if cert is not None:
        if nh.fenchel_bound(m, cert["prices"], cert["pricing_lower"]) != cert:
            raise ValueError("Target global lower did not replay")
        if result["lower"] != cert["lower"]:
            raise ValueError("Target reported lower differs from checked certificate")
        assessment["global_certificate_replayed"] = True
    mix = result.get("mixture")
    if (mix is None) != (result.get("upper") is None):
        raise ValueError("Target feasible upper and mixture presence differ")
    if mix is not None:
        selected = {col["key"]: col for col in columns}
        chosen = [selected[key] for key in mix["column_keys"]]
        weights = [Fraction(x) for x in mix["simplex"]["weights_exact"]]
        rebuilt = nh.replay_exact_mixture(case, m, chosen, weights,
                                          extraction_policy=compact.EXTRACTION_POLICY)
        if (rebuilt["objective_exact"] != mix["objective_exact"]
                or rebuilt["load_exact"] != mix["load_exact"]
                or rebuilt["upper"] != mix["upper"]):
            raise ValueError("Target hull mixture did not replay")
        if result["upper"] != mix["upper"]:
            raise ValueError("Target reported upper differs from checked mixture")
        assessment["mixture_replayed"] = True
    if result.get("status") == "certified" and not (
            assessment["bounds"] and assessment["global_certificate_replayed"]
            and assessment["mixture_replayed"]):
        raise ValueError("Certified target omitted replayable global enclosure")
    return assessment


def assess_physical(case, m, stage, result, prices=None):
    if (result.get("case_identity") != case.identity()
            or result.get("formulation") != pf.FORMULATION
            or result.get("extraction_policy") != pf.EXTRACTION_POLICY):
        raise ValueError("Physical planner/response identity differs")
    if stage == "planner" and (result.get("a") != list(m.a) or result.get("b") != list(m.b)):
        raise ValueError("Planner market differs")
    if stage == "response" and result.get("prices") != prices:
        raise ValueError("Response price differs")
    out = {"status": result.get("status"), "bounds": finite_bounds(result),
           "plan_replayed": False}
    plan = result.get("plan")
    if plan is not None:
        replay = nr.replay_native(case, plan, prices)
        out.update(plan_replayed=True, plan_hash=nr.digest(plan), replay=replay)
        if stage == "planner":
            exact = Fraction(replay["ops_cost"]) + nh.supply(m, replay["load"])
            out.update(executable_cost_exact=str(exact), executable_cost=float(exact))
    if result.get("status") == "certified" and not (out["bounds"] and out["plan_replayed"]):
        raise ValueError("Certified physical solve omitted replayed bounds/plan")
    return out


def complete_planner(path, case_name):
    folder = cell_dir(path, case_name, "planner")
    try:
        receipt = json.loads((folder / "receipt.json").read_text())
        assessed = json.loads((folder / "result.json").read_text())["assessment"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return (receipt.get("on_time") is True and receipt.get("returncode") == 0
            and assessed.get("plan_replayed") is True and assessed.get("bounds") is not None)


def worker(path, case_name, stage):
    target = _attempt(path)
    folder = cell_dir(target, case_name, stage)
    started = time.monotonic()
    core_started = None
    try:
        spec = frozen(target, check_sources=False)
        if (case_name not in CASES or stage not in STAGES or not (folder / "launch.json").is_file()):
            raise ValueError("Child launch/case/stage missing")
        case = cases()[case_name]
        cfg = budget(case_name, stage)
        declared = spec["cases"][case_name]
        if (declared["case_identity"] != case.identity()
                or declared["budgets"][stage] != asdict(cfg)):
            raise ValueError("Child differs from frozen case/budget")
        m = market(case_name, stage if stage in SOURCES else "target")

        def record(event):
            stamped = {**event, "worker_elapsed_before_serialization_s": time.monotonic()-started}
            with (folder / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(stamped, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())

        preparation = {}
        prices = None
        if stage in SOURCES:
            core_started = time.monotonic()
            result = compact.certify(case, m, cfg, arm="retained", state_index=0,
                                     record=record, **HULL_CONTROLS)
            core_seconds = time.monotonic() - core_started
            save_new(folder / "raw_result.json", {"case": case_name, "stage": stage, "result": result})
            assessment = assess_hull(case, m, result)
        elif stage in ARMS:
            predecessor = identity = None
            if stage != "cold":
                proposal_at = time.monotonic()
                checked_at = time.monotonic()
                pool = checked_pool(target, case_name)
                preparation["pool_check_seconds"] = time.monotonic()-checked_at
                if not pool["eligible"]:
                    raise ValueError("Target retrieval source pool is empty")
                selected_at = time.monotonic()
                selected = select(pool, m, stage)
                preparation["lookup_seconds"] = time.monotonic()-selected_at
                replay_at = time.monotonic()
                preparation["direct_proposals"] = direct_proposals(case, m, selected)
                preparation["direct_replay_seconds"] = time.monotonic()-replay_at
                preparation["direct_proposal_wall_seconds"] = time.monotonic()-proposal_at
                save_new(folder / "proposal.json", {"case": case_name, "stage": stage,
                         "physical_identity": case.identity(),
                         "selected_keys": [candidate["key"] for candidate in selected],
                         "direct_proposals": preparation["direct_proposals"],
                         "pool_check_seconds": preparation["pool_check_seconds"],
                         "lookup_seconds": preparation["lookup_seconds"],
                         "direct_replay_seconds": preparation["direct_replay_seconds"],
                         "direct_proposal_wall_seconds": preparation["direct_proposal_wall_seconds"],
                         "worker_elapsed_before_serialization_s": time.monotonic()-started})
                adapter_at = time.monotonic()
                predecessor, identity = import_envelope(case, m, cfg, pool, selected)
                preparation["adapter_seconds"] = time.monotonic()-adapter_at
                save_new(folder / "import_envelope.json", predecessor)
                preparation["pool_lineage_digest"] = predecessor["lineage_digest"]
                preparation["selected_keys"] = [candidate["key"] for candidate in selected]
            preparation["pre_core_seconds"] = time.monotonic()-started
            save_new(folder / "preparation.json", preparation)
            core_started = time.monotonic()
            result = compact.certify(case, m, cfg, arm="cold" if stage == "cold" else "retained",
                                     state_index=0 if stage == "cold" else 1,
                                     previous=predecessor, expected_previous=identity,
                                     record=record, **HULL_CONTROLS)
            core_seconds = time.monotonic()-core_started
            save_new(folder / "raw_result.json", {"case": case_name, "stage": stage, "result": result})
            assessment = assess_hull(case, m, result)
            if stage != "cold":
                if result.get("state_index") != 1 or result.get("arm") != "retained":
                    raise ValueError("Target did not use retained import")
                start_events = [event for event in read_events(folder) if event.get("event") == "state_start"]
                if len(start_events) != 1 or start_events[0].get("imported_column_keys") != preparation["selected_keys"]:
                    raise ValueError("Target imported keys differ from selected pool")
        elif stage == "planner":
            core_started = time.monotonic()
            result = pf.solve_planner(case, m.a, m.b, cfg, record=record)
            core_seconds = time.monotonic()-core_started
            save_new(folder / "raw_result.json", {"case": case_name, "stage": stage, "result": result})
            assessment = assess_physical(case, m, stage, result)
        else:
            if not complete_planner(target, case_name):
                raise ValueError("Own-price response requires on-time replayed planner")
            planner = json.loads((cell_dir(target, case_name, "planner") / "result.json").read_text())
            load = planner["assessment"]["replay"]["load"]
            prices = [float(Fraction(a) + Fraction(b)*Fraction(e))
                      for a, b, e in zip(m.a, m.b, load)]
            save_new(folder / "prices.json", prices)
            core_started = time.monotonic()
            result = pf.solve_pricing(case, prices, cfg, record=record)
            core_seconds = time.monotonic()-core_started
            save_new(folder / "raw_result.json", {"case": case_name, "stage": stage, "result": result})
            assessment = assess_physical(case, m, stage, result, prices)
            planner_replay = planner["assessment"]["replay"]
            planner_bill = Fraction(planner_replay["ops_cost"]) + sum(
                (Fraction(p)*Fraction(x) for p, x in zip(prices, planner_replay["load"])), Fraction(0))
            assessment["planner_own_price_bill_exact"] = str(planner_bill)
            if assessment["bounds"]:
                lower, upper = map(Fraction, assessment["bounds"])
                assessment["own_price_regret_interval_exact"] = [str(planner_bill-upper),
                                                                  str(planner_bill-lower)]
            else:
                assessment["own_price_regret_interval_exact"] = None
        save_new(folder / "result.json", {"case": case_name, "stage": stage,
                   "assessment": assessment, "preparation": preparation,
                   "core_call_seconds": core_seconds,
                   "child_work_seconds": time.monotonic()-started,
                   "actual_environment": {"hostname": platform.node(), **base.environment()}})
        return 0
    except Exception as exc:
        save_new(folder / "exception.json", {"type": type(exc).__name__, "message": str(exc),
                 "traceback": traceback.format_exc(),
                 "core_elapsed_seconds": time.monotonic()-core_started if core_started else None,
                 "child_work_seconds": time.monotonic()-started})
        return 2


def launch_child(path, case_name, stage, hard_seconds):
    folder = cell_dir(path, case_name, stage)
    command = [sys.executable, "-m", "experiments.retrieval_comparison", "worker",
               "--attempt", str(path), "--case", case_name, "--stage", stage]
    save_new(folder / "launch.json", {"command": command, "hard_seconds": hard_seconds,
                                      "started_utc": time.time()})
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    started, returncode, hard_timeout, error = time.monotonic(), None, False, None
    try:
        with (folder / "stdout.txt").open("xb") as out, (folder / "stderr.txt").open("xb") as err:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err)
            try:
                returncode = process.wait(timeout=hard_seconds)
            except subprocess.TimeoutExpired:
                hard_timeout = True
                for stop, grace in ((process.terminate, 10), (process.kill, 2)):
                    if process.poll() is not None:
                        break
                    stop()
                    try:
                        returncode = process.wait(timeout=grace)
                        break
                    except subprocess.TimeoutExpired:
                        continue
                if returncode is None:
                    returncode = process.wait()
    except Exception as exc:
        returncode, error = 1, repr(exc)
    elapsed = time.monotonic()-started
    receipt = {"returncode": returncode, "hard_timeout": hard_timeout,
               "on_time": returncode == 0 and not hard_timeout and elapsed <= hard_seconds,
               "elapsed_seconds": elapsed, "hard_seconds": hard_seconds, "error": error}
    save_new(folder / "receipt.json", receipt)
    return receipt


def result_row(path, case_name, stage, receipt):
    folder = cell_dir(path, case_name, stage)
    row = {"case": case_name, "stage": stage, "receipt": receipt,
           "status": "hard_timeout" if receipt["hard_timeout"] else
                     "failed" if receipt["returncode"] != 0 else
                     "late" if not receipt["on_time"] else "returned",
           "online_child_seconds": receipt["elapsed_seconds"]}
    if (folder / "result.json").is_file():
        try:
            result = json.loads((folder / "result.json").read_text())
            if result.get("case") != case_name or result.get("stage") != stage:
                raise ValueError("Result wrapper identity differs")
            row.update(native_status=result["assessment"].get("status"),
                       assessment=result["assessment"],
                       preparation=result.get("preparation"),
                       core_call_seconds=result.get("core_call_seconds"),
                       child_work_seconds=result.get("child_work_seconds"))
            if receipt["on_time"]:
                row["status"] = result["assessment"].get("status", "returned")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            row["result_read_error"] = repr(exc)
            if row["status"] == "returned":
                row["status"] = "partial_result"
    if (folder / "exception.json").is_file():
        try:
            error = json.loads((folder / "exception.json").read_text())
            row["exception"] = {key: error.get(key) for key in ("type", "message")}
        except (OSError, ValueError, TypeError) as exc:
            row["exception_read_error"] = repr(exc)
    _attach_preparation_artifacts(row, folder)
    return row


def _attach_preparation_artifacts(row, folder):
    for filename, key in (("proposal.json", "direct_proposal"),
                          ("preparation.json", "preparation_artifact")):
        file = folder / filename
        if file.is_file():
            try:
                row[key] = json.loads(file.read_text())
            except (OSError, ValueError, TypeError) as exc:
                row[key + "_read_error"] = repr(exc)


def _paid_source_seconds(pool):
    values = [pool["sources"][name].get("paid_source_seconds") for name in SOURCES]
    return sum(values) if all(type(x) in (int, float) and math.isfinite(x) for x in values) else None


def paid_pool_costs(pool, pool_preparation_seconds):
    generation = _paid_source_seconds(pool)
    return {"source_generation_child_seconds": generation,
            "pool_preparation_seconds": pool_preparation_seconds,
            "paid_source_pool_seconds": generation + pool_preparation_seconds
            if generation is not None else None}


def admitted_assessment(row):
    receipt = row.get("receipt") or {}
    if receipt.get("on_time") is True and receipt.get("returncode") == 0:
        return row.get("assessment") or {}
    return {}


def comparison_metrics(rows):
    by_stage = {row["stage"]: row for row in rows}
    planner = admitted_assessment(by_stage["planner"])
    response = admitted_assessment(by_stage["response"])
    d_bounds = planner.get("bounds")
    output = {"physical_planner_D_interval": d_bounds,
              "executable_D_cost_exact": planner.get("executable_cost_exact"),
              "own_price_regret_interval_exact": response.get("own_price_regret_interval_exact"),
              "own_price_response_interval": response.get("bounds"),
              "hull_by_arm": {}}
    for arm in ARMS:
        row = by_stage[arm]
        assessed = admitted_assessment(row)
        ch_bounds = assessed.get("bounds")
        gap = None
        if d_bounds is not None and ch_bounds is not None:
            d_low, d_high = map(Fraction, d_bounds)
            ch_low, ch_high = map(Fraction, ch_bounds)
            gap = [str(d_low-ch_high), str(d_high-ch_low)]
        output["hull_by_arm"][arm] = {"CH_interval": ch_bounds,
                                      "D_minus_CH_interval": gap,
                                      "status": row["status"]}
    return output


def controller(path):
    target = _attempt(path)
    spec = frozen(target)
    save_new(target / "controller_started.json", {"protocol": PROTOCOL, "utc": time.time()})
    rows = []
    for index, case_name in enumerate(CASES):
        case_dir = target / case_name
        case_dir.mkdir(parents=True, exist_ok=False)
        local = []
        pool = None
        for stage in stage_order(index):
            folder = cell_dir(target, case_name, stage)
            folder.mkdir(parents=True, exist_ok=False)
            if stage not in SOURCES and pool is None:
                pool_started = time.monotonic()
                pool = collect_pool(target, case_name)
                save_new(case_dir / "pool.json", pool)
                pool_preparation_seconds = time.monotonic()-pool_started
                save_new(case_dir / "pool_preparation_receipt.json", {
                    "case": case_name, "elapsed_seconds": pool_preparation_seconds,
                    "scope": "controller source admission, event/physical replay, candidate extraction and pool.json write"})
            ineligible = None
            if stage in ARMS and stage != "cold" and not pool["eligible"]:
                ineligible = "No admissible replayed source column"
            elif stage == "response" and not complete_planner(target, case_name):
                ineligible = "No on-time replayed planner witness and bounds"
            if ineligible is not None:
                save_new(folder / "ineligible.json", {"reason": ineligible})
                row = {"case": case_name, "stage": stage, "status": "ineligible",
                       "reason": ineligible, "online_child_seconds": None}
            else:
                receipt = launch_child(target, case_name, stage,
                                       spec["cases"][case_name]["hard_child_seconds"][stage])
                row = result_row(target, case_name, stage, receipt)
            if stage in ARMS and stage != "cold":
                row.update(paid_pool_costs(pool, pool_preparation_seconds))
                row["paid_source_plus_target_seconds"] = (
                    row["paid_source_pool_seconds"] + row["online_child_seconds"]
                    if row.get("paid_source_pool_seconds") is not None
                    and row.get("online_child_seconds") is not None else None)
                row["amortized_online_plus_source_seconds_by_reuses"] = (
                    {str(n): row["online_child_seconds"] + row["paid_source_pool_seconds"]/n
                     for n in (1, 2, 4, 8)}
                    if row.get("paid_source_pool_seconds") is not None
                    and row.get("online_child_seconds") is not None else None)
            rows.append(row)
            local.append(row)
        save_new(case_dir / "case_summary.json", {"case": case_name,
                  "source_pool": {key: value for key, value in pool.items() if key != "candidates"},
                  **paid_pool_costs(pool, pool_preparation_seconds),
                  "rows": local, "comparison_metrics": comparison_metrics(local)})
    save_new(target / "summary.json", {"protocol": PROTOCOL, "rows": rows,
             "declared_cells": 48, "accounted_cells": len(rows),
             "all_declared_cells_accounted": len(rows) == 48,
             "scientific_admission": "pending independent result review",
             "source_work_paid_once_per_case": True,
             "amortization_reuses": [1, 2, 4, 8],
             "hull_columns_are_complete_fleets": True})
    return 0 if len(rows) == 48 else 2


def reconcile_partial(path):
    target = Path(path)
    if (target / "summary.json").is_file():
        try:
            if json.loads((target / "summary.json").read_text()).get("accounted_cells") == 48:
                return None
        except ValueError:
            pass
    rows = []
    for index, case_name in enumerate(CASES):
        for stage in stage_order(index):
            folder = cell_dir(target, case_name, stage)
            if (folder / "receipt.json").is_file():
                try:
                    row = result_row(target, case_name, stage,
                                     json.loads((folder / "receipt.json").read_text()))
                except (ValueError, KeyError, TypeError) as exc:
                    row = {"case": case_name, "stage": stage,
                           "status": "receipt_unreadable", "error": repr(exc)}
            elif (folder / "ineligible.json").is_file():
                row = {"case": case_name, "stage": stage, "status": "ineligible"}
            elif (folder / "launch.json").is_file():
                row = {"case": case_name, "stage": stage, "status": "interrupted_unreceipted"}
            else:
                row = {"case": case_name, "stage": stage, "status": "unstarted"}
            _attach_preparation_artifacts(row, folder)
            rows.append(row)
    save_new(target / "postmortem_summary.json", {"protocol": PROTOCOL, "rows": rows,
             "declared_cells": 48, "accounted_cells": len(rows),
             "scientific_admission": "none; abnormal controller termination"})
    return rows


def seal_manifest(path):
    target = Path(path)
    files = {str(p.relative_to(target)): {"bytes": p.stat().st_size, "sha256": base.sha(p)}
             for p in sorted(target.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    save_new(target / "MANIFEST.json", {"protocol": PROTOCOL, "files": files})


def supervise(path):
    target = _attempt(path)
    source_error, child_rc, hard_timeout, launch_error, quiescent = None, None, False, None, True
    try:
        frozen(target)
    except Exception as exc:
        source_error = repr(exc)
    started = time.monotonic()
    if source_error is None:
        command = [sys.executable, "-m", "experiments.retrieval_comparison", "controller",
                   "--attempt", str(target)]
        save_new(target / "supervisor_launch.json", {"command": command,
                                                    "controller_hard_seconds": CONTROLLER_CAP,
                                                    "supervisor_outer_seconds": SUPERVISOR_CAP})
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        try:
            with (target / "controller_stdout.txt").open("xb") as out, (
                    target / "controller_stderr.txt").open("xb") as err:
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                           start_new_session=True)
                child_rc, hard_timeout, quiescent = base.wait_process_group(process, CONTROLLER_CAP)
        except Exception as exc:
            launch_error, child_rc = repr(exc), 1
    else:
        save_new(target / "supervisor_launch.json", {"command": None, "blocked_before_child": True})
    try:
        source_unchanged = source_hashes() == json.loads((target / "frozen.json").read_text())["source_hashes"]
    except Exception as exc:
        source_unchanged = False
        source_error = repr(exc)
    if quiescent and (hard_timeout or child_rc != 0 or source_error or launch_error):
        reconcile_partial(target)
    rc = 124 if hard_timeout else 1 if source_error or not source_unchanged or launch_error or not quiescent else child_rc or 0
    save_new(target / "supervisor_receipt.json", {"protocol": PROTOCOL,
             "child_returncode": child_rc, "returncode": rc, "hard_timeout": hard_timeout,
             "process_group_quiescent": quiescent, "stable_seal": quiescent,
             "source_hashes_unchanged": source_unchanged,
             "source_check_error": source_error, "launch_error": launch_error,
             "elapsed_seconds": time.monotonic()-started})
    if quiescent:
        seal_manifest(target)
    return rc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("design", "freeze", "preflight", "supervise", "controller", "worker"))
    parser.add_argument("--attempt", type=Path, default=ATTEMPT)
    parser.add_argument("--case", choices=CASES)
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
        if native_probe() != json.loads((args.attempt / "frozen.json").read_text())["native_probe"]:
            raise ValueError("Effective native backend or model seed differs from freeze")
        return 0
    if args.mode == "supervise":
        return supervise(args.attempt)
    if args.mode == "controller":
        return controller(args.attempt)
    if args.case is None or args.stage is None:
        parser.error("worker requires --case and --stage")
    return worker(args.attempt, args.case, args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
