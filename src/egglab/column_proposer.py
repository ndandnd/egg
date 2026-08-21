"""Bounded local-move column-proposer laboratory.

This module is intentionally separate from the production A2/A6 loops.  It
rebuilds clean RMPs over insertion-ordered prefixes of a certified A2 run,
prices deterministic one-trip local moves with the exact fixed-sequence MILP,
and scores only replay-valid, novel columns with strictly negative physical
reduced cost.  Fixed-sequence bounds never enter a convex-hull certificate.

The normative contract is ``doc/LOCAL_MOVE_COLUMN_PROPOSER_LAB.md``.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from .b2a2 import (
    RC_TOL,
    canonicalize_pricing_solution,
    certified_cg,
    column_from_solution,
    column_key,
    market_hash,
    pricing_incumbent,
    solve_rmp,
)
from .evsp import (
    LOAD_RECONSTRUCTION_POLICY_VERSION,
    REPLAY_POLICY_VERSION,
    REPLAY_TOL_KWH,
    Solution,
    solve_fixed_sequences,
    validate_solution,
)
from .instance import synthetic_instance
from .market import make_affine_market
from .regimes import solve_taker
from .solver import backend


SCHEMA = "local-move-column-proposer-v1"
MOVE_CATALOG_VERSION = "relocate-swap-v1"
BASE_COMMIT = "5b63e725d0fd85cfb0b83f462a612016e7f4321a"

SEEDS = (0, 11, 15)
N_TRIPS = 4
MAX_VEHICLES = 4
B_SCALES = (0.01, 0.05)
CELLS = tuple((seed, N_TRIPS, b) for seed in SEEDS for b in B_SCALES)

EPSILON = 1e-3
BUDGET = 80
PWL_TOL = 1e-4
GLOBAL_MIP_GAP = 1e-9
FIXED_MIP_GAP = 1e-9
ACTIVE_LAMBDA_TOL = 1e-8
NUMERIC_TOL = 1e-8

DISPOSITIONS = (
    "INVALID-HALT",
    "NO-OPPORTUNITY",
    "HONEST-NEGATIVE",
    "LIMITED-SIGNAL",
    "POSITIVE-SPIKE",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO_ROOT / "doc" / "LOCAL_MOVE_COLUMN_PROPOSER_LAB.md"


class ColumnProposerError(RuntimeError):
    pass


def _finite(value) -> bool:
    return value is not None and math.isfinite(float(value))


def _close(a, b, *, tol: float = NUMERIC_TOL) -> bool:
    if not (_finite(a) and _finite(b)):
        return False
    scale = max(1.0, abs(float(a)), abs(float(b)))
    return abs(float(a) - float(b)) <= tol * scale


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(document: dict) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, stderr=subprocess.DEVNULL
    ).decode().strip()


def _full_head() -> str:
    return _git("rev-parse", "HEAD")


def _verify_git_state(analysis_commit: str) -> None:
    if len(analysis_commit) != 40 or any(
            c not in "0123456789abcdef" for c in analysis_commit):
        raise ColumnProposerError("analysis commit must be a full lowercase SHA")
    if _full_head() != analysis_commit:
        raise ColumnProposerError(
            f"HEAD {_full_head()} != analysis commit {analysis_commit}")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, analysis_commit],
        cwd=REPO_ROOT,
    ).returncode != 0:
        raise ColumnProposerError(
            f"base commit {BASE_COMMIT} is not an ancestor of {analysis_commit}")
    dirty = _git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        raise ColumnProposerError(
            "tracked worktree is dirty; refusing outcome generation")
    if not SPEC_PATH.is_file():
        raise ColumnProposerError(f"normative spec is missing: {SPEC_PATH}")


def _trip_rank(inst) -> dict:
    return {t.id: (int(t.start_min), str(t.id)) for t in inst.trips}


def canonical_partition(inst, sequences) -> tuple[tuple[str, ...], ...]:
    """Canonical label-free trip partition.

    Trips are time-ordered within chains and vehicle labels are removed by
    lexicographically ordering the resulting chain tuples.
    """
    if not isinstance(sequences, (list, tuple)):
        raise ColumnProposerError("sequences must be a list/tuple")
    rank = _trip_rank(inst)
    expected = sorted(rank)
    chains = []
    for chain in sequences:
        if not isinstance(chain, (list, tuple)) or not chain:
            raise ColumnProposerError("every sequence must be nonempty")
        ids = [str(tid) for tid in chain]
        if any(tid not in rank for tid in ids):
            raise ColumnProposerError("sequence contains an unknown trip id")
        chains.append(tuple(sorted(ids, key=lambda tid: rank[tid])))
    covered = sorted(tid for chain in chains for tid in chain)
    if covered != expected:
        raise ColumnProposerError("partition does not cover every trip exactly once")
    if len(chains) > int(inst.max_vehicles):
        raise ColumnProposerError("partition exceeds max_vehicles")
    return tuple(sorted(chains))


def partition_json(partition) -> list[list[str]]:
    return [list(chain) for chain in partition]


def partition_id(partition) -> str:
    payload = json.dumps(partition_json(partition), separators=(",", ":"))
    return _sha256(payload.encode())


def _origin_key(origin: dict) -> str:
    return json.dumps(origin, sort_keys=True, separators=(",", ":"))


def local_move_catalog(inst, active_sources: list[dict],
                       prefix_columns: list[dict]) -> list[dict]:
    """Enumerate the frozen relocate/swap catalog in canonical order."""
    existing = {
        canonical_partition(inst, item["sequences"])
        for item in prefix_columns
    }
    sources = {}
    for item in active_sources:
        part = canonical_partition(inst, item["sequences"])
        sources.setdefault(part, set()).add(str(item["column_key"]))

    candidates: dict[tuple, dict] = {}

    def add_candidate(source, moved, origin):
        candidate = canonical_partition(inst, moved)
        if candidate == source or candidate in existing:
            return
        row = candidates.setdefault(candidate, {
            "candidate_id": partition_id(candidate),
            "sequences": partition_json(candidate),
            "origins": {},
        })
        row["origins"][_origin_key(origin)] = origin

    for source in sorted(sources):
        chains = [list(chain) for chain in source]
        source_id = partition_id(source)

        # Relocate one trip to another existing chain.
        for source_index, source_chain in enumerate(chains):
            for trip_id in sorted(source_chain):
                for target_index in range(len(chains)):
                    if target_index == source_index:
                        continue
                    moved = [list(chain) for chain in chains]
                    moved[source_index].remove(trip_id)
                    moved[target_index].append(trip_id)
                    moved = [chain for chain in moved if chain]
                    add_candidate(source, moved, {
                        "kind": "relocate",
                        "source_partition_id": source_id,
                        "trip": trip_id,
                        "target": "existing",
                        "target_chain": list(chains[target_index]),
                    })

                # Relocate to a new singleton chain (a local split).
                if len(chains) < int(inst.max_vehicles) and len(source_chain) > 1:
                    moved = [list(chain) for chain in chains]
                    moved[source_index].remove(trip_id)
                    moved.append([trip_id])
                    add_candidate(source, moved, {
                        "kind": "relocate",
                        "source_partition_id": source_id,
                        "trip": trip_id,
                        "target": "new-singleton",
                        "target_chain": [],
                    })

        # Swap one trip across two distinct chains.
        for left_index in range(len(chains)):
            for right_index in range(left_index + 1, len(chains)):
                for left_trip in sorted(chains[left_index]):
                    for right_trip in sorted(chains[right_index]):
                        moved = [list(chain) for chain in chains]
                        moved[left_index].remove(left_trip)
                        moved[right_index].remove(right_trip)
                        moved[left_index].append(right_trip)
                        moved[right_index].append(left_trip)
                        add_candidate(source, moved, {
                            "kind": "swap",
                            "source_partition_id": source_id,
                            "left_trip": left_trip,
                            "right_trip": right_trip,
                        })

    out = []
    for candidate in sorted(candidates):
        row = candidates[candidate]
        row["origins"] = [
            row["origins"][key] for key in sorted(row["origins"])
        ]
        out.append(row)
    return out


def classify_reduced_cost(reduced_cost: float, novel: bool) -> str:
    if not _finite(reduced_cost):
        raise ColumnProposerError("candidate reduced cost is nonfinite")
    value = float(reduced_cost)
    if not novel:
        if value < -RC_TOL:
            raise ColumnProposerError(
                "duplicate candidate has strictly negative reduced cost")
        return "DUPLICATE"
    if value < -RC_TOL:
        return "ACCEPTED"
    if abs(value) <= RC_TOL:
        return "TOLERANCE-TIE"
    return "NONIMPROVING"


def disposition(global_opportunities: int, captured_opportunities: int) -> str:
    if global_opportunities < 0 or captured_opportunities < 0:
        raise ColumnProposerError("negative aggregate count")
    if captured_opportunities > global_opportunities:
        raise ColumnProposerError("captures exceed opportunities")
    if global_opportunities == 0:
        return "NO-OPPORTUNITY"
    if captured_opportunities == 0:
        return "HONEST-NEGATIVE"
    rate = captured_opportunities / global_opportunities
    return "POSITIVE-SPIKE" if rate >= 0.5 else "LIMITED-SIGNAL"


def _solver_evidence(stats) -> dict:
    return {
        "backend": stats.backend,
        "status": stats.status,
        "obj": stats.obj,
        "bound": stats.bound,
        "mip_gap": stats.mip_gap,
        "n_vars": stats.n_vars,
        "n_int": stats.n_int,
        "n_constrs": stats.n_constrs,
        "max_mip_gap": stats.max_mip_gap,
    }


def _column_evidence(sol, col: dict, prices, sigma: float) -> dict:
    physical_obj = pricing_incumbent(col, sol, prices)
    reduced_cost = physical_obj - float(sigma)
    return {
        "sequences": [list(chain) for chain in sol.sequences],
        "arc_kinds": [list(kinds) for kinds in sol.arc_kinds],
        "charges": [
            {
                "vehicle": int(charge["vehicle"]),
                "after_trip": str(charge["after_trip"]),
                "before_trip": str(charge["before_trip"]),
                "slot": int(charge["slot"]),
                "kwh": float(charge["kwh"]),
            }
            for charge in sol.charges
        ],
        "load": [float(value) + 0.0 for value in col["load"]],
        "fleet": int(sol.fleet),
        "dh_min_total": float(sol.dh_min_total),
        "energy_charged_kwh": float(sol.energy_charged_kwh),
        "ops_cost": float(col["ops_cost"]),
        "obj_model": float(sol.obj_model),
        "obj_true": float(sol.obj_true),
        "physical_pricing_objective": physical_obj,
        "reduced_cost": reduced_cost,
        "column_key": col["column_key"],
        "schedule_hash": sol.schedule_hash(),
        "load_hash": sol.load_hash(),
        "replay_ok": True,
        "solver": _solver_evidence(sol.stats),
        "load_reconstruction": {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
        },
    }


def _price_global(inst, prices, sigma: float, prefix_keys: set[str]) -> dict:
    sol = solve_taker(inst, prices, max_mip_gap=GLOBAL_MIP_GAP)
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)
    evidence = _column_evidence(sol, col, prices, sigma)
    bound = float(sol.stats.bound)
    rc_lb = bound - float(sigma)
    rc_ub = float(evidence["reduced_cost"])
    if rc_lb > rc_ub + NUMERIC_TOL * max(1.0, abs(rc_lb), abs(rc_ub)):
        raise ColumnProposerError(
            f"global pricing bound exceeds incumbent: {rc_lb} > {rc_ub}")
    novel = col["column_key"] not in prefix_keys
    if not novel and rc_ub < -RC_TOL:
        raise ColumnProposerError(
            "global pricing returned a negative-RC duplicate")
    improving = novel and rc_ub < -RC_TOL
    if rc_lb < -RC_TOL and not improving:
        raise ColumnProposerError(
            "global pricing remains ambiguous at the frozen tolerance")
    return {
        "novel": novel,
        "reduced_cost_lb": rc_lb,
        "reduced_cost_ub": rc_ub,
        "opportunity": improving,
        "evidence": evidence,
    }


def _price_candidate(inst, candidate: dict, prices, sigma: float,
                     prefix_keys: set[str], global_rc_lb: float) -> dict:
    row = {
        "candidate_id": candidate["candidate_id"],
        "sequences": candidate["sequences"],
        "origins": candidate["origins"],
    }
    sol = solve_fixed_sequences(
        inst,
        candidate["sequences"],
        ("linear", np.asarray(prices, dtype=float)),
        max_mip_gap=FIXED_MIP_GAP,
    )
    if sol is None:
        row.update(classification="INFEASIBLE-PARTITION", evidence=None)
        return row
    if sol.stats is None or sol.stats.status != "OPTIMAL":
        raise ColumnProposerError(
            "fixed-partition solve did not return OPTIMAL")
    if not _finite(sol.stats.bound):
        raise ColumnProposerError(
            "fixed-partition solve returned no finite bound")
    canonicalize_pricing_solution(inst, sol, prices)
    col = column_from_solution(inst, sol)
    evidence = _column_evidence(sol, col, prices, sigma)
    novel = col["column_key"] not in prefix_keys
    classification = classify_reduced_cost(evidence["reduced_cost"], novel)
    if float(evidence["reduced_cost"]) < float(global_rc_lb) - NUMERIC_TOL * max(
            1.0, abs(float(evidence["reduced_cost"])),
            abs(float(global_rc_lb))):
        raise ColumnProposerError(
            "candidate objective lies below the full-fleet certified bound")
    row.update(
        classification=classification,
        novel=novel,
        evidence=evidence,
    )
    return row


def evaluate_prefix(inst, market, prefix_columns: list[dict],
                    prefix_size: int, *, tag: str) -> dict:
    rmp = solve_rmp(
        inst,
        market,
        prefix_columns,
        [],
        pwl_tol=PWL_TOL,
        solve_id_prefix=f"{tag}-prefix{prefix_size}",
    )
    prices = [-float(value) for value in rmp["pi"]]
    sigma = float(rmp["sigma"])
    prefix_min = [
        {
            "column_key": col["column_key"],
            "sequences": partition_json(canonical_partition(
                inst, col["sequences"])),
        }
        for col in prefix_columns
    ]
    prefix_keys = {row["column_key"] for row in prefix_min}
    active_sources = []
    for index, (col, lam) in enumerate(zip(prefix_columns, rmp["lambdas"])):
        if float(lam) > ACTIVE_LAMBDA_TOL:
            part = canonical_partition(inst, col["sequences"])
            active_sources.append({
                "prefix_index": index,
                "column_key": col["column_key"],
                "lambda": float(lam),
                "partition_id": partition_id(part),
                "sequences": partition_json(part),
            })
    if not active_sources:
        raise ColumnProposerError("clean RMP has no active source column")

    catalog = local_move_catalog(inst, active_sources, prefix_min)
    global_pricing = _price_global(inst, prices, sigma, prefix_keys)
    proposals = [
        _price_candidate(
            inst, candidate, prices, sigma, prefix_keys,
            global_pricing["reduced_cost_lb"])
        for candidate in catalog
    ]
    accepted = [
        proposal for proposal in proposals
        if proposal["classification"] == "ACCEPTED"
    ]
    if accepted and not global_pricing["opportunity"]:
        raise ColumnProposerError(
            "local proposer found an improving column without a global "
            "pricing opportunity")
    captured = bool(global_pricing["opportunity"] and accepted)
    classifications = {}
    for proposal in proposals:
        key = proposal["classification"]
        classifications[key] = classifications.get(key, 0) + 1
    return {
        "prefix_size": prefix_size,
        "prefix_columns": prefix_min,
        "rmp": {
            "z_model": float(rmp["z_model"]),
            "ub": float(rmp["ub"]),
            "pwl_slack": float(rmp["ub"] - rmp["z_model"]),
            "lambdas": [float(value) for value in rmp["lambdas"]],
            "load": [float(value) for value in rmp["L"]],
            "pi": [float(value) for value in rmp["pi"]],
            "sigma": sigma,
        },
        "prices": prices,
        "active_sources": active_sources,
        "move_catalog_count": len(catalog),
        "global_pricing": global_pricing,
        "proposals": proposals,
        "counts": {
            "catalog": len(catalog),
            "accepted": len(accepted),
            "classifications": classifications,
        },
        "captured": captured,
    }


def _cell_tag(cell) -> str:
    seed, n_trips, b = cell
    return f"s{seed}_n{n_trips}_b{b:g}"


def singleton_feasibility_witness(inst) -> dict:
    """Outcome-blind proof that one initially full vehicle per trip works."""
    if int(inst.max_vehicles) < len(inst.trips):
        raise ColumnProposerError(
            "singleton witness requires at least one vehicle per trip")
    rows = []
    for trip in sorted(inst.trips, key=lambda item: item.id):
        energy = (
            inst.dhk(inst.depot, trip.start_loc)
            + float(trip.energy_kwh)
            + inst.dhk(trip.end_loc, inst.depot)
        )
        terminal_soc = float(inst.soc0_kwh) - energy
        margin = terminal_soc - float(inst.soc_end_kwh)
        if margin < 0.0:
            raise ColumnProposerError(
                f"singleton witness fails for {trip.id}: terminal margin "
                f"{margin}")
        rows.append({
            "trip": trip.id,
            "round_trip_energy_kwh": energy,
            "terminal_soc_kwh": terminal_soc,
            "terminal_margin_kwh": margin,
        })
    return {
        "policy": "one-trip-per-vehicle",
        "vehicle_count": len(inst.trips),
        "max_vehicles": int(inst.max_vehicles),
        "minimum_terminal_margin_kwh": min(
            row["terminal_margin_kwh"] for row in rows),
        "trips": rows,
    }


def run_cell(cell, run_dir: str | os.PathLike) -> dict:
    seed, n_trips, b = cell
    if tuple(cell) not in CELLS:
        raise ColumnProposerError(f"cell {cell!r} is outside the frozen grid")
    inst = synthetic_instance(
        seed=seed, n_trips=n_trips, max_vehicles=MAX_VEHICLES)
    market = make_affine_market(inst, shape="duck", b_scale=b)
    feasibility = singleton_feasibility_witness(inst)
    tag = _cell_tag(cell)
    raw = Path(run_dir) / tag
    state = certified_cg(
        inst,
        market,
        epsilon=EPSILON,
        budget=BUDGET,
        out_dir=str(raw),
        tag="a2",
        experiment="local-move-column-proposer-baseline",
        pwl_tol=PWL_TOL,
        solver_kw={"max_mip_gap": GLOBAL_MIP_GAP},
        method="a2",
    )
    outcome = state.get("outcome") or {}
    if not outcome.get("certified") or outcome.get("type") != "certified":
        raise ColumnProposerError(
            f"{tag}: baseline A2 did not certify: {outcome!r}")
    columns = state["columns"]
    if not columns:
        raise ColumnProposerError(f"{tag}: baseline A2 retained no columns")
    snapshots = [
        evaluate_prefix(inst, market, columns[:prefix_size], prefix_size, tag=tag)
        for prefix_size in range(1, len(columns) + 1)
    ]
    return {
        "cell": {"seed": seed, "n_trips": n_trips, "b": b, "tag": tag},
        "instance": {
            "name": inst.name,
            "hash": inst.hash(),
            "max_vehicles": inst.max_vehicles,
        },
        "feasibility_witness": feasibility,
        "market": {
            "hash": market_hash(market),
            "name": market.name,
            "a": [float(value) for value in market.a],
            "b": [float(value) for value in market.b],
            "base_load": [float(value) for value in market.U],
        },
        "baseline": {
            "certified": True,
            "type": outcome["type"],
            "gap": float(outcome["gap"]),
            "ub_ch": float(outcome["ub_ch"]),
            "lb_best": float(outcome["lb_best"]),
            "oracle_calls": int(outcome["oracle_calls"]),
            "column_count": len(columns),
            "column_keys": [col["column_key"] for col in columns],
        },
        "snapshots": snapshots,
    }


def _design() -> dict:
    return {
        "schema": SCHEMA,
        "move_catalog_version": MOVE_CATALOG_VERSION,
        "population": {
            "seeds": list(SEEDS),
            "n_trips": N_TRIPS,
            "max_vehicles": MAX_VEHICLES,
            "b_scales": list(B_SCALES),
            "shape": "duck",
            "cell_count": len(CELLS),
            "excluded_seed_band": [16, 37],
        },
        "baseline": {
            "method": "a2",
            "epsilon": EPSILON,
            "budget": BUDGET,
            "pwl_tol": PWL_TOL,
            "max_mip_gap": GLOBAL_MIP_GAP,
        },
        "proposer": {
            "moves": ["relocate", "swap"],
            "active_lambda_tol": ACTIVE_LAMBDA_TOL,
            "fixed_partition_max_mip_gap": FIXED_MIP_GAP,
            "reduced_cost_tol": RC_TOL,
            "numeric_tol": NUMERIC_TOL,
            "replay_tol_kwh": REPLAY_TOL_KWH,
            "replay_policy_version": REPLAY_POLICY_VERSION,
            "load_reconstruction_policy_version":
                LOAD_RECONSTRUCTION_POLICY_VERSION,
            "score": "captured_opportunities/global_opportunities",
        },
        "dispositions": list(DISPOSITIONS),
    }


def summarize_cells(cells: list[dict]) -> dict:
    opportunities = 0
    captured = 0
    proposals = 0
    feasible = 0
    accepted = 0
    snapshots = 0
    per_cell = []
    for cell in cells:
        cell_opportunities = sum(
            bool(s["global_pricing"]["opportunity"])
            for s in cell["snapshots"])
        cell_captured = sum(bool(s["captured"]) for s in cell["snapshots"])
        cell_proposals = sum(s["counts"]["catalog"] for s in cell["snapshots"])
        cell_feasible = sum(
            proposal["classification"] != "INFEASIBLE-PARTITION"
            for s in cell["snapshots"] for proposal in s["proposals"])
        cell_accepted = sum(
            proposal["classification"] == "ACCEPTED"
            for s in cell["snapshots"] for proposal in s["proposals"])
        opportunities += cell_opportunities
        captured += cell_captured
        proposals += cell_proposals
        feasible += cell_feasible
        accepted += cell_accepted
        snapshots += len(cell["snapshots"])
        per_cell.append({
            "tag": cell["cell"]["tag"],
            "snapshots": len(cell["snapshots"]),
            "global_opportunities": cell_opportunities,
            "captured_opportunities": cell_captured,
            "proposals": cell_proposals,
            "feasible_proposals": cell_feasible,
            "accepted_proposals": cell_accepted,
        })
    return {
        "cells": len(cells),
        "snapshots": snapshots,
        "global_opportunities": opportunities,
        "captured_opportunities": captured,
        "capture_rate": (
            None if opportunities == 0 else captured / opportunities),
        "proposals": proposals,
        "feasible_proposals": feasible,
        "accepted_proposals": accepted,
        "disposition": disposition(opportunities, captured),
        "per_cell": per_cell,
    }


def build_report(run_root: str | os.PathLike, analysis_commit: str, *,
                 cells=CELLS) -> dict:
    cell_list = [tuple(cell) for cell in cells]
    if cell_list != list(CELLS):
        raise ColumnProposerError("outcome runs require the exact frozen grid")
    results = [run_cell(cell, run_root) for cell in cell_list]
    report = {
        "schema": SCHEMA,
        "base_commit": BASE_COMMIT,
        "analysis_commit": analysis_commit,
        "spec": {
            "path": str(SPEC_PATH.relative_to(REPO_ROOT)),
            "sha256": _sha256(SPEC_PATH.read_bytes()),
        },
        "environment": {
            "backend": backend(),
            "mip_version": importlib.metadata.version("mip"),
        },
        "design": _design(),
        "cells": results,
    }
    report["summary"] = summarize_cells(results)
    return report


def _recompute_ops(inst, sequences, arc_kinds) -> tuple[float, float]:
    if len(sequences) != len(arc_kinds):
        raise ColumnProposerError("sequence/arc-kind vehicle counts differ")
    tripmap = {trip.id: trip for trip in inst.trips}
    deadhead = 0.0
    for sequence, kinds in zip(sequences, arc_kinds):
        if not sequence or len(kinds) != len(sequence) - 1:
            raise ColumnProposerError("malformed sequence/arc-kind lengths")
        trips = [tripmap[trip_id] for trip_id in sequence]
        deadhead += inst.dhm(inst.depot, trips[0].start_loc)
        deadhead += inst.dhm(trips[-1].end_loc, inst.depot)
        for left, right, kind in zip(trips, trips[1:], kinds):
            if kind == "dir":
                deadhead += inst.dhm(left.end_loc, right.start_loc)
            elif kind == "dep":
                deadhead += (
                    inst.dhm(left.end_loc, inst.depot)
                    + inst.dhm(inst.depot, right.start_loc)
                )
            else:
                raise ColumnProposerError(f"unknown arc kind {kind!r}")
    ops = (
        inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * deadhead
    )
    return float(deadhead), float(ops)


def _audit_evidence(inst, evidence: dict, prices, sigma: float,
                    label: str) -> list[str]:
    errors = []

    def fail(message):
        errors.append(f"{label}: {message}")

    try:
        sequences = evidence["sequences"]
        arc_kinds = evidence["arc_kinds"]
        charges = evidence["charges"]
        stored_load = [float(value) for value in evidence["load"]]
        if len(stored_load) != inst.n_slots:
            fail("load length mismatch")
            return errors
        physical = [0.0] * inst.n_slots
        for charge in charges:
            slot = int(charge["slot"])
            if slot != charge["slot"] or not 0 <= slot < inst.n_slots:
                fail("invalid charge slot")
                continue
            amount = float(charge["kwh"])
            if not math.isfinite(amount) or amount < 0:
                fail("invalid charge amount")
                continue
            physical[slot] += amount
        for slot, (actual, stored) in enumerate(zip(physical, stored_load)):
            if not _close(actual, stored):
                fail(
                    f"physical load mismatch at slot {slot}: "
                    f"{actual} != {stored}")
        deadhead, ops = _recompute_ops(inst, sequences, arc_kinds)
        if not _close(deadhead, evidence["dh_min_total"]):
            fail("deadhead total mismatch")
        if not _close(ops, evidence["ops_cost"]):
            fail("operating cost mismatch")
        if int(evidence["fleet"]) != len(sequences):
            fail("fleet count mismatch")
        if not _close(sum(physical), evidence["energy_charged_kwh"]):
            fail("charged-energy total mismatch")
        sol = Solution(
            sequences=[list(sequence) for sequence in sequences],
            arc_kinds=[list(kinds) for kinds in arc_kinds],
            charges=[dict(charge) for charge in charges],
            load=stored_load,
            fleet=int(evidence["fleet"]),
            dh_min_total=float(evidence["dh_min_total"]),
            energy_charged_kwh=float(evidence["energy_charged_kwh"]),
            ops_cost=float(evidence["ops_cost"]),
            obj_model=float(evidence["obj_model"]),
            obj_true=float(evidence["obj_true"]),
            stats=None,
        )
        violations = validate_solution(inst, sol)
        if violations:
            fail(f"physical replay failed: {violations}")
        recomputed_key = column_key({"load": physical, "ops_cost": ops})
        if recomputed_key != evidence["column_key"]:
            fail("column key mismatch")
        physical_obj = ops + float(np.dot(
            np.asarray(prices, dtype=float), np.asarray(physical)))
        if not _close(physical_obj, evidence["physical_pricing_objective"]):
            fail("physical pricing objective mismatch")
        if not _close(physical_obj, evidence["obj_true"]):
            fail("stored true objective mismatch")
        rc = physical_obj - float(sigma)
        if not _close(rc, evidence["reduced_cost"]):
            fail("reduced cost mismatch")
        if evidence.get("replay_ok") is not True:
            fail("stored replay claim is not true")
        policy = evidence.get("load_reconstruction") or {}
        if policy != {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
        }:
            fail("load-reconstruction policy mismatch")
        solver = evidence.get("solver") or {}
        if solver.get("status") != "OPTIMAL":
            fail("solver status is not OPTIMAL")
        if not _finite(solver.get("bound")):
            fail("solver bound is nonfinite")
    except (KeyError, TypeError, ValueError, ColumnProposerError) as exc:
        fail(f"malformed evidence: {exc}")
    return errors


def audit_report(report: dict) -> list[str]:
    """Independent no-solver replay/arithmetic/catalog audit."""
    errors: list[str] = []

    def fail(message):
        errors.append(message)

    if report.get("schema") != SCHEMA:
        fail("report schema mismatch")
        return errors
    if report.get("base_commit") != BASE_COMMIT:
        fail("base commit mismatch")
    if report.get("design") != _design():
        fail("frozen design mismatch")
    spec = report.get("spec") or {}
    if spec.get("path") != str(SPEC_PATH.relative_to(REPO_ROOT)):
        fail("spec path mismatch")
    if spec.get("sha256") != _sha256(SPEC_PATH.read_bytes()):
        fail("spec hash mismatch")
    if len(report.get("cells") or []) != len(CELLS):
        fail("cell count mismatch")
        return errors

    expected_cells = list(CELLS)
    for cell_index, (stored, expected) in enumerate(
            zip(report["cells"], expected_cells)):
        label = f"cell[{cell_index}]"
        seed, n_trips, b = expected
        if stored.get("cell") != {
            "seed": seed, "n_trips": n_trips, "b": b,
            "tag": _cell_tag(expected),
        }:
            fail(f"{label}: cell identity mismatch")
        inst = synthetic_instance(
            seed=seed, n_trips=n_trips, max_vehicles=MAX_VEHICLES)
        market = make_affine_market(inst, shape="duck", b_scale=b)
        if (stored.get("instance") or {}).get("hash") != inst.hash():
            fail(f"{label}: instance hash mismatch")
        if stored.get("feasibility_witness") != singleton_feasibility_witness(inst):
            fail(f"{label}: singleton feasibility witness mismatch")
        market_doc = stored.get("market") or {}
        if market_doc.get("hash") != market_hash(market):
            fail(f"{label}: market hash mismatch")
        for key, actual in (
            ("a", market.a), ("b", market.b), ("base_load", market.U)
        ):
            values = market_doc.get(key)
            if not isinstance(values, list) or len(values) != len(actual):
                fail(f"{label}: market {key} mismatch")
            elif any(not _close(x, y) for x, y in zip(values, actual)):
                fail(f"{label}: market {key} values mismatch")

        baseline = stored.get("baseline") or {}
        if not baseline.get("certified") or baseline.get("type") != "certified":
            fail(f"{label}: baseline is not certified")
        column_count = baseline.get("column_count")
        snapshots = stored.get("snapshots") or []
        if column_count != len(baseline.get("column_keys") or []):
            fail(f"{label}: baseline column count/key mismatch")
        if column_count != len(snapshots):
            fail(f"{label}: snapshot count does not equal column count")

        for snapshot_index, snapshot in enumerate(snapshots, start=1):
            snap_label = f"{label}.prefix[{snapshot_index}]"
            if snapshot.get("prefix_size") != snapshot_index:
                fail(f"{snap_label}: prefix index mismatch")
            prefix = snapshot.get("prefix_columns") or []
            if len(prefix) != snapshot_index:
                fail(f"{snap_label}: prefix column count mismatch")
            if [row.get("column_key") for row in prefix] != (
                    baseline.get("column_keys") or [])[:snapshot_index]:
                fail(f"{snap_label}: prefix key order mismatch")
            rmp = snapshot.get("rmp") or {}
            prices = snapshot.get("prices") or []
            pi = rmp.get("pi") or []
            if len(prices) != inst.n_slots or len(pi) != inst.n_slots:
                fail(f"{snap_label}: price/dual length mismatch")
                continue
            if any(not _close(price, -dual)
                   for price, dual in zip(prices, pi)):
                fail(f"{snap_label}: price is not minus clean dual")
            sigma = rmp.get("sigma")
            if not _finite(sigma):
                fail(f"{snap_label}: sigma is nonfinite")
                continue
            lambdas = rmp.get("lambdas") or []
            if len(lambdas) != len(prefix):
                fail(f"{snap_label}: lambda count mismatch")
            elif not _close(sum(float(value) for value in lambdas), 1.0):
                fail(f"{snap_label}: lambdas do not sum to one")
            if not _close(
                    float(rmp.get("ub", 0)) - float(rmp.get("z_model", 0)),
                    rmp.get("pwl_slack")):
                fail(f"{snap_label}: PWL slack mismatch")
            if float(rmp.get("pwl_slack", float("inf"))) > PWL_TOL + NUMERIC_TOL:
                fail(f"{snap_label}: PWL slack exceeds tolerance")

            active = snapshot.get("active_sources") or []
            expected_active = []
            if len(lambdas) == len(prefix):
                for index, (column, lam) in enumerate(zip(prefix, lambdas)):
                    if float(lam) > ACTIVE_LAMBDA_TOL:
                        part = canonical_partition(inst, column["sequences"])
                        expected_active.append({
                            "prefix_index": index,
                            "column_key": column["column_key"],
                            "lambda": float(lam),
                            "partition_id": partition_id(part),
                            "sequences": partition_json(part),
                        })
            if active != expected_active:
                fail(f"{snap_label}: active-source derivation mismatch")

            expected_catalog = local_move_catalog(inst, active, prefix)
            proposals = snapshot.get("proposals") or []
            proposal_catalog = [
                {
                    "candidate_id": row.get("candidate_id"),
                    "sequences": row.get("sequences"),
                    "origins": row.get("origins"),
                }
                for row in proposals
            ]
            if proposal_catalog != expected_catalog:
                fail(f"{snap_label}: move catalog mismatch")
            if snapshot.get("move_catalog_count") != len(expected_catalog):
                fail(f"{snap_label}: move catalog count mismatch")

            global_doc = snapshot.get("global_pricing") or {}
            global_evidence = global_doc.get("evidence") or {}
            errors.extend(_audit_evidence(
                inst, global_evidence, prices, float(sigma),
                f"{snap_label}.global"))
            prefix_keys = {row["column_key"] for row in prefix}
            global_key = global_evidence.get("column_key")
            global_novel = global_key not in prefix_keys
            if global_doc.get("novel") != global_novel:
                fail(f"{snap_label}: global novelty mismatch")
            global_rc_ub = global_evidence.get("reduced_cost")
            if not _close(global_doc.get("reduced_cost_ub"), global_rc_ub):
                fail(f"{snap_label}: global RC upper mismatch")
            solver_bound = (global_evidence.get("solver") or {}).get("bound")
            if _finite(solver_bound):
                expected_lb = float(solver_bound) - float(sigma)
                if not _close(global_doc.get("reduced_cost_lb"), expected_lb):
                    fail(f"{snap_label}: global RC lower mismatch")
            expected_opportunity = bool(
                global_novel and _finite(global_rc_ub)
                and float(global_rc_ub) < -RC_TOL)
            if global_doc.get("opportunity") != expected_opportunity:
                fail(f"{snap_label}: global opportunity mismatch")

            accepted_count = 0
            classifications = {}
            for proposal_index, proposal in enumerate(proposals):
                proposal_label = f"{snap_label}.proposal[{proposal_index}]"
                classification = proposal.get("classification")
                if classification == "INFEASIBLE-PARTITION":
                    if proposal.get("evidence") is not None:
                        fail(f"{proposal_label}: infeasible row has evidence")
                else:
                    evidence = proposal.get("evidence") or {}
                    errors.extend(_audit_evidence(
                        inst, evidence, prices, float(sigma), proposal_label))
                    novel = evidence.get("column_key") not in prefix_keys
                    if proposal.get("novel") != novel:
                        fail(f"{proposal_label}: novelty mismatch")
                    try:
                        expected_class = classify_reduced_cost(
                            float(evidence.get("reduced_cost")), novel)
                    except (TypeError, ValueError, ColumnProposerError) as exc:
                        fail(f"{proposal_label}: classification error: {exc}")
                        expected_class = None
                    if classification != expected_class:
                        fail(f"{proposal_label}: classification mismatch")
                classifications[classification] = (
                    classifications.get(classification, 0) + 1)
                accepted_count += classification == "ACCEPTED"

            expected_captured = bool(expected_opportunity and accepted_count)
            if snapshot.get("captured") != expected_captured:
                fail(f"{snap_label}: capture label mismatch")
            expected_counts = {
                "catalog": len(proposals),
                "accepted": accepted_count,
                "classifications": classifications,
            }
            if snapshot.get("counts") != expected_counts:
                fail(f"{snap_label}: proposal counts mismatch")
            if accepted_count and not expected_opportunity:
                fail(f"{snap_label}: accepted candidate without opportunity")

    expected_summary = summarize_cells(report["cells"])
    if report.get("summary") != expected_summary:
        fail("aggregate summary/disposition mismatch")
    return errors


def summary_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Local-move column proposer — bounded tiny result",
        "",
        f"Disposition: **{summary['disposition']}**.",
        "",
        "The frozen score counts only strict negative-reduced-cost, novel "
        "columns that pass independent physical replay.",
        "",
        f"- Cells: {summary['cells']}",
        f"- Clean-prefix snapshots: {summary['snapshots']}",
        f"- Global improvement opportunities: "
        f"{summary['global_opportunities']}",
        f"- Captured opportunities: {summary['captured_opportunities']}",
        f"- Capture rate: "
        + ("undefined" if summary["capture_rate"] is None
           else f"{summary['capture_rate']:.6f}"),
        f"- Unique candidate partitions priced: {summary['proposals']}",
        f"- Feasible/replayed candidate columns: "
        f"{summary['feasible_proposals']}",
        f"- Strictly accepted candidate columns: "
        f"{summary['accepted_proposals']}",
        "",
        "| cell | snapshots | opportunities | captured | proposals | "
        "feasible | accepted |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["per_cell"]:
        lines.append(
            f"| `{row['tag']}` | {row['snapshots']} | "
            f"{row['global_opportunities']} | "
            f"{row['captured_opportunities']} | {row['proposals']} | "
            f"{row['feasible_proposals']} | {row['accepted_proposals']} |")
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "This is a four-trip synthetic mechanism spike conditional on the "
        "recorded clean-dual representatives and active supports. Structural "
        "changes, schedule hashes, wall time, and fixed-partition solver "
        "bounds are not scores. The proposer contributes no convex-hull "
        "certificate and no convergence or efficiency claim.",
        "",
    ])
    return "\n".join(lines)


def _manifest(report_bytes: bytes, summary_bytes: bytes,
              analysis_commit: str) -> dict:
    return {
        "schema": f"{SCHEMA}-manifest",
        "base_commit": BASE_COMMIT,
        "analysis_commit": analysis_commit,
        "files": {
            "REPORT.json": _sha256(report_bytes),
            "SUMMARY.md": _sha256(summary_bytes),
        },
    }


def publish(run_root: str | os.PathLike, out_dir: str | os.PathLike,
            analysis_commit: str | None = None, *,
            verify_git: bool = True) -> Path:
    """Run the frozen grid once, audit it, and atomically publish evidence."""
    analysis_commit = analysis_commit or _full_head()
    if verify_git:
        _verify_git_state(analysis_commit)
    run_root = Path(run_root).resolve()
    out_dir = Path(out_dir).resolve()
    if run_root.exists():
        raise ColumnProposerError(
            f"refusing existing raw run root: {run_root}")
    if out_dir.exists():
        raise ColumnProposerError(
            f"refusing existing output directory: {out_dir}")
    if run_root == out_dir or run_root in out_dir.parents or out_dir in run_root.parents:
        raise ColumnProposerError("raw and published output paths overlap")
    run_root.parent.mkdir(parents=True, exist_ok=True)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    run_root.mkdir()
    report = build_report(run_root, analysis_commit)
    audit_errors = audit_report(report)
    if audit_errors:
        raise ColumnProposerError(
            "independent audit failed:\n" + "\n".join(audit_errors))
    report_bytes = canonical_bytes(report)
    summary_bytes = summary_markdown(report).encode()
    manifest = _manifest(report_bytes, summary_bytes, analysis_commit)
    manifest_bytes = canonical_bytes(manifest)
    staging = Path(tempfile.mkdtemp(
        prefix=f".{out_dir.name}.staging-", dir=out_dir.parent))
    try:
        (staging / "REPORT.json").write_bytes(report_bytes)
        (staging / "SUMMARY.md").write_bytes(summary_bytes)
        (staging / "MANIFEST.json").write_bytes(manifest_bytes)
        os.rename(staging, out_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return out_dir


def audit_directory(path: str | os.PathLike) -> list[str]:
    path = Path(path)
    errors = []
    expected = {"REPORT.json", "SUMMARY.md", "MANIFEST.json"}
    if not path.is_dir():
        return [f"not a directory: {path}"]
    actual = {entry.name for entry in path.iterdir()}
    if actual != expected:
        errors.append(
            f"file set mismatch: expected {sorted(expected)}, got "
            f"{sorted(actual)}")
        return errors
    try:
        report_raw = (path / "REPORT.json").read_bytes()
        report = json.loads(report_raw)
        if report_raw != canonical_bytes(report):
            errors.append("REPORT.json is not canonical")
        summary_raw = (path / "SUMMARY.md").read_bytes()
        if summary_raw != summary_markdown(report).encode():
            errors.append("SUMMARY.md does not regenerate")
        manifest_raw = (path / "MANIFEST.json").read_bytes()
        manifest = json.loads(manifest_raw)
        if manifest_raw != canonical_bytes(manifest):
            errors.append("MANIFEST.json is not canonical")
        expected_manifest = _manifest(
            report_raw, summary_raw, report.get("analysis_commit"))
        if manifest != expected_manifest:
            errors.append("manifest identity/hash mismatch")
        errors.extend(audit_report(report))
    except (OSError, json.JSONDecodeError, KeyError, TypeError,
            ValueError, ColumnProposerError) as exc:
        errors.append(f"cannot audit artifact: {exc}")
    return errors
