"""Complete enumeration of schedule structures on tiny instances — the
independent ground truth for the B2-A2 launch gate.

A STRUCTURE is a partition of the trips into time-ordered vehicle chains plus
a fixed arc kind (direct / via-depot) for every consecutive pair. Its
charging realizations form a polytope P_s (continuous). The convex-hull
master value is, exactly,

    z_CH_enum = min  sum_s ops_s * lambda_s + DeltaC_true(L)
                s.t. L = sum_s (charging load of structure s),
                     charging of s constrained by A_s y_s <= b_s * lambda_s
                     (the lambda-scaled polytope; all constraints homogeneous
                      in (y_s, lambda_s), so lambda_s = 0 => y_s = 0 feasible),
                     sum_s lambda_s = 1, lambda >= 0,

solved as an LP with the same exact-evaluation + tangent-refinement scheme
as the A2 master (value reported is the exact evaluation; model slack
<= pwl_tol).

The enumerated integer/dictator value is

    z_D_enum = min_s [ ops_s + min_{y in P_s} DeltaC_true(load(y)) ],

each inner problem solved as a per-structure convex program (adaptive PWL).
This must reproduce the independently solved regimes.solve_dictator value
within combined tolerances.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time

import mip
import numpy as np

from .b2a2 import B2A2Error
from .evsp import (
    Solution,
    canonicalize_solution_load,
    slot_overlaps,
    validate_solution,
)
from .instance import Instance, Trip
from .market import AffineMarket
from .solver import new_model, optimize

MAX_STRUCTURES = 2000
PWL_TOL = 1e-4
CANONICAL_DIGITS = 12


def canonical_number(value: float, digits: int = CANONICAL_DIGITS) -> float:
    """Stable JSON-facing float representation (never used in optimization)."""
    value = round(float(value), digits)
    return 0.0 if value == 0.0 else value


def canonical_structure(struct_or_sequences, kinds=None) -> dict:
    """Vehicle-label-independent representation of a discrete structure."""
    if isinstance(struct_or_sequences, dict):
        sequences = struct_or_sequences["sequences"]
        kinds = struct_or_sequences.get(
            "kinds", struct_or_sequences.get("arc_kinds"))
    else:
        sequences = struct_or_sequences
    if kinds is None or len(sequences) != len(kinds):
        raise ValueError("sequences and arc kinds must align")
    pairs = sorted(
        ((tuple(seq), tuple(arc_kinds))
         for seq, arc_kinds in zip(sequences, kinds)),
        key=lambda item: (item[0], item[1]),
    )
    return {
        "sequences": [list(seq) for seq, _ in pairs],
        "kinds": [list(arc_kinds) for _, arc_kinds in pairs],
    }


def structure_id(struct_or_sequences, kinds=None) -> str:
    payload = json.dumps(
        canonical_structure(struct_or_sequences, kinds),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_solution_record(sol: Solution) -> dict:
    """Canonical, solver-metadata-free schedule/load record for witnesses."""
    indexed = sorted(
        ((tuple(seq), tuple(kinds), old_i)
         for old_i, (seq, kinds) in enumerate(
             zip(sol.sequences, sol.arc_kinds))),
        key=lambda item: (item[0], item[1]),
    )
    remap = {old_i: new_i for new_i, (_, _, old_i) in enumerate(indexed)}
    sequences = [list(seq) for seq, _, _ in indexed]
    kinds = [list(arc_kinds) for _, arc_kinds, _ in indexed]
    charges = []
    for charge in sol.charges:
        charges.append({
            "vehicle": remap[int(charge["vehicle"])],
            "after_trip": charge["after_trip"],
            "before_trip": charge["before_trip"],
            "slot": int(charge["slot"]),
            "kwh": canonical_number(charge["kwh"]),
        })
    charges.sort(key=lambda row: (
        row["vehicle"], row["after_trip"], row["before_trip"], row["slot"]))
    return {
        "structure_id": structure_id(sequences, kinds),
        "sequences": sequences,
        "arc_kinds": kinds,
        "charges": charges,
        "load": [canonical_number(value) for value in sol.load],
        "fleet": len(sequences),
        "ops_cost": canonical_number(sol.ops_cost),
        "energy_charged_kwh": canonical_number(sum(sol.load)),
    }


# ---------------------------------------------------------------------------
# structure enumeration
# ---------------------------------------------------------------------------
def _pair_kinds(inst: Instance, ti, tj) -> list:
    kinds = []
    if ti.end_min + inst.dhm(ti.end_loc, tj.start_loc) <= tj.start_min:
        kinds.append("dir")
    arrive = ti.end_min + inst.dhm(ti.end_loc, inst.depot)
    depart = tj.start_min - inst.dhm(inst.depot, tj.start_loc)
    if depart >= arrive:
        kinds.append("dep")
    return kinds


def enumerate_structures(inst: Instance) -> list:
    """All (partition, kinds) structures; trips within a chain are ordered by
    start time. Raises if the instance is too large to enumerate."""
    trips = sorted(inst.trips, key=lambda t: (t.start_min, t.id))
    partitions = []

    def extend(idx, chains):
        if len(partitions) > MAX_STRUCTURES:
            raise B2A2Error("instance too large for complete enumeration")
        if idx == len(trips):
            partitions.append([list(c) for c in chains])
            return
        t = trips[idx]
        for c in chains:
            if _pair_kinds(inst, c[-1], t):
                c.append(t)
                extend(idx + 1, chains)
                c.pop()
        if len(chains) < inst.max_vehicles:
            chains.append([t])
            extend(idx + 1, chains)
            chains.pop()

    extend(0, [])

    structures = []
    for part in partitions:
        kind_options = []
        for chain in part:
            for a, b in zip(chain, chain[1:]):
                kind_options.append(_pair_kinds(inst, a, b))
        combos = [[]]
        for opts in kind_options:
            combos = [c + [k] for c in combos for k in opts]
        for combo in combos:
            it = iter(combo)
            kinds = [[next(it) for _ in range(len(chain) - 1)] for chain in part]
            structures.append({
                "sequences": [[t.id for t in chain] for chain in part],
                "kinds": kinds,
                "ops_cost": _ops_cost(inst, part, kinds),
            })
            if len(structures) > MAX_STRUCTURES:
                raise B2A2Error("instance too large for complete enumeration")
    return structures


def _ops_cost(inst: Instance, part, kinds) -> float:
    return (
        inst.vehicle_fixed_cost * len(part)
        + inst.dh_cost_per_min * _dh_minutes(inst, part, kinds)
    )


def _dh_minutes(inst: Instance, part, kinds) -> float:
    D = inst.depot
    dh = 0.0
    for chain, ck in zip(part, kinds):
        dh += inst.dhm(D, chain[0].start_loc) + inst.dhm(chain[-1].end_loc, D)
        for (a, b), k in zip(zip(chain, chain[1:]), ck):
            if k == "dir":
                dh += inst.dhm(a.end_loc, b.start_loc)
            else:
                dh += inst.dhm(a.end_loc, D) + inst.dhm(D, b.start_loc)
    return dh


# ---------------------------------------------------------------------------
# lambda-scaled charging polytope of one structure
# ---------------------------------------------------------------------------
def _add_structure_block(
    m, inst: Instance, struct, lam, load_terms, capture: dict | None = None
):
    """Add A_s y_s <= b_s * lam constraints (all homogeneous); accumulate the
    structure's per-slot charging into load_terms.  ``capture`` is optional
    extraction metadata used only by the independent tiny replay."""
    D = inst.depot
    tripmap = {t.id: t for t in inst.trips}
    B = inst.battery_kwh
    P = inst.charge_power_kw
    if capture is not None:
        capture.setdefault("charge_arcs", [])
        capture.setdefault("n_charge_variables", 0)
    for chain_i, (seq, ck) in enumerate(
            zip(struct["sequences"], struct["kinds"])):
        trips = [tripmap[tid] for tid in seq]
        prev_after = None
        for i, tr in enumerate(trips):
            sb = m.add_var(lb=0.0, ub=mip.INF)
            if i == 0:
                m += sb == (inst.soc0_kwh - inst.dhk(D, tr.start_loc)) * lam
            else:
                p = trips[i - 1]
                kind = ck[i - 1]
                if kind == "dir":
                    m += sb == prev_after - inst.dhk(p.end_loc, tr.start_loc) * lam
                else:
                    arrive = p.end_min + inst.dhm(p.end_loc, D)
                    depart = tr.start_min - inst.dhm(D, tr.start_loc)
                    d1 = inst.dhk(p.end_loc, D)
                    d2 = inst.dhk(D, tr.start_loc)
                    evars = {}
                    for (t, ov) in slot_overlaps(inst, arrive, depart):
                        e = m.add_var(lb=0.0)
                        m += e <= (P * ov / 60.0) * lam
                        evars[t] = e
                        load_terms[t].append(e)
                    if capture is not None:
                        capture["charge_arcs"].append({
                            "vehicle": chain_i,
                            "after_trip": p.id,
                            "before_trip": tr.id,
                            "variables": evars,
                        })
                        capture["n_charge_variables"] += len(evars)
                    ch = mip.xsum(evars.values()) if evars else 0.0
                    m += sb == prev_after - (d1 + d2) * lam + ch
                    m += prev_after - d1 * lam + ch <= B * lam
                    m += prev_after - d1 * lam >= inst.soc_min_kwh * lam
            m += sb >= inst.soc_min_kwh * lam
            m += sb <= B * lam
            sa = m.add_var(lb=0.0, ub=mip.INF)
            m += sa == sb - tr.energy_kwh * lam
            m += sa >= inst.soc_min_kwh * lam
            prev_after = sa
        m += prev_after - inst.dhk(trips[-1].end_loc, D) * lam >= (
            inst.soc_end_kwh * lam)


def _fixed_structure_model(inst: Instance, struct, name: str):
    """Build one fixed-structure charging LP and retain extraction handles."""
    struct = {
        **canonical_structure(struct),
        "ops_cost": float(struct["ops_cost"]),
    }
    m = new_model(name)
    one = m.add_var(lb=1.0, ub=1.0)
    load_terms = [[] for _ in range(inst.n_slots)]
    capture = {}
    _add_structure_block(m, inst, struct, one, load_terms, capture=capture)
    loads = [m.add_var(lb=0.0) for _ in range(inst.n_slots)]
    for slot in range(inst.n_slots):
        m += (
            loads[slot] == mip.xsum(load_terms[slot])
            if load_terms[slot]
            else loads[slot] == 0
        )
    capture["active_load_slots"] = [
        slot for slot, terms in enumerate(load_terms) if terms]
    return m, loads, capture, struct


def _materialize_structure_solution(
    inst: Instance,
    struct: dict,
    capture: dict,
    loads,
    stats,
) -> Solution:
    def value(var):
        return float(var.x or 0.0)

    charges = []
    for arc in capture["charge_arcs"]:
        for slot, var in arc["variables"].items():
            amount = value(var)
            if amount > 1e-10:
                charges.append({
                    "vehicle": arc["vehicle"],
                    "after_trip": arc["after_trip"],
                    "before_trip": arc["before_trip"],
                    "slot": int(slot),
                    "kwh": amount,
                })
    charges.sort(key=lambda row: (
        row["vehicle"], row["after_trip"], row["before_trip"], row["slot"]))
    tripmap = {trip.id: trip for trip in inst.trips}
    part = [[tripmap[trip_id] for trip_id in seq]
            for seq in struct["sequences"]]
    dh_minutes = _dh_minutes(inst, part, struct["kinds"])
    sol = Solution(
        sequences=[list(seq) for seq in struct["sequences"]],
        arc_kinds=[list(kinds) for kinds in struct["kinds"]],
        charges=charges,
        load=[value(var) for var in loads],
        fleet=len(struct["sequences"]),
        dh_min_total=dh_minutes,
        ops_cost=float(struct["ops_cost"]),
        stats=stats,
        oracle_tier="independent-enumerated-structure",
    )
    canonicalize_solution_load(inst, sol)
    violations = validate_solution(inst, sol)
    if violations:
        raise B2A2Error(
            "enumerated fixed-structure response failed replay: "
            + "; ".join(violations))
    return sol


def solve_structure_linear(
    inst: Instance,
    struct: dict,
    prices,
    max_mip_gap: float = 1e-9,
) -> dict | None:
    """Independently optimize charging for one fully fixed discrete structure."""
    prices = np.asarray(prices, dtype=float)
    if prices.shape != (inst.n_slots,) or not np.isfinite(prices).all():
        raise ValueError("prices must be a finite vector with one value per slot")
    m, loads, capture, struct = _fixed_structure_model(
        inst, struct, "enum-linear-structure")
    energy = mip.xsum(float(prices[t]) * loads[t]
                      for t in range(inst.n_slots))
    m.objective = float(struct["ops_cost"]) + energy
    stats = optimize(
        m, max_mip_gap=max_mip_gap, solve_lp_first=False)
    if stats.obj is None:
        return None
    if stats.status != "OPTIMAL":
        raise B2A2Error(
            f"enumerated structure solve status {stats.status} != OPTIMAL")
    sol = _materialize_structure_solution(
        inst, struct, capture, loads, stats)
    objective = float(struct["ops_cost"]) + float(
        np.dot(prices, np.asarray(sol.load, dtype=float)))
    sol.obj_model = stats.obj
    sol.obj_true = objective
    sol.energy_cost_model = objective - sol.ops_cost
    bound = stats.bound
    optimality_gap = (
        max(0.0, objective - float(bound))
        if bound is not None and math.isfinite(float(bound))
        else None
    )
    return {
        "structure": struct,
        "structure_id": structure_id(struct),
        "solution_object": sol,
        "solution": canonical_solution_record(sol),
        "objective": objective,
        "certified_bound": float(bound) if bound is not None else None,
        "optimality_gap_abs": optimality_gap,
        "n_charge_variables": capture["n_charge_variables"],
        "active_load_slots": list(capture["active_load_slots"]),
    }


def enumerate_price_responses(inst: Instance, prices) -> dict:
    """Exhaust every discrete structure and optimize its continuous response.

    This is deliberately stronger and more explicit than asking the compact
    MILP for one incumbent: every partition/arc-kind structure is listed as
    feasible or infeasible, and every feasible structure carries its own
    independently replayed optimal charging realization.
    """
    structures = sorted(
        enumerate_structures(inst),
        key=lambda struct: structure_id(struct),
    )
    responses = []
    feasible_raw = []
    for index, struct in enumerate(structures):
        sid = structure_id(struct)
        solved = solve_structure_linear(inst, struct, prices)
        if solved is None:
            responses.append({
                "index": index,
                "structure_id": sid,
                "structure": {
                    **canonical_structure(struct),
                    "ops_cost": canonical_number(struct["ops_cost"]),
                },
                "feasible": False,
            })
            continue
        feasible_raw.append(solved)
        responses.append({
            "index": index,
            "structure_id": sid,
            "structure": {
                **canonical_structure(struct),
                "ops_cost": canonical_number(struct["ops_cost"]),
            },
            "feasible": True,
            "objective": canonical_number(solved["objective"]),
            "certified_bound": (
                canonical_number(solved["certified_bound"])
                if solved["certified_bound"] is not None else None),
            "optimality_gap_abs": (
                canonical_number(solved["optimality_gap_abs"])
                if solved["optimality_gap_abs"] is not None else None),
            "n_charge_variables": solved["n_charge_variables"],
            "active_load_slots": solved["active_load_slots"],
            "solution": solved["solution"],
        })
    if not feasible_raw:
        raise B2A2Error("no feasible response structure")
    ranked = sorted(
        feasible_raw,
        key=lambda row: (row["objective"], row["structure_id"]),
    )
    best = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None
    best_value = best["objective"]
    for response in responses:
        if response["feasible"]:
            response["objective_gap_from_best"] = canonical_number(
                float(response["objective"]) - best_value)
    return {
        "prices": [canonical_number(value) for value in prices],
        "n_structures": len(structures),
        "n_feasible": len(feasible_raw),
        "n_infeasible": len(structures) - len(feasible_raw),
        "best_structure_id": best["structure_id"],
        "best_objective": canonical_number(best_value),
        "runner_up_structure_id": (
            runner_up["structure_id"] if runner_up is not None else None),
        "runner_up_objective": (
            canonical_number(runner_up["objective"])
            if runner_up is not None else None),
        "strict_structure_margin": (
            canonical_number(runner_up["objective"] - best_value)
            if runner_up is not None else None),
        "responses": responses,
    }


def structure_optimal_face(
    inst: Instance,
    struct: dict,
    prices,
    objective_tolerance: float = 1e-8,
) -> dict:
    """Bound load variation on a structure's near-optimal LP face.

    Linear programs have no positive objective gap to arbitrarily nearby
    feasible points.  This check therefore reports aggregate-load uniqueness,
    not a fictitious continuous-response margin.
    """
    solved = solve_structure_linear(inst, struct, prices)
    if solved is None:
        raise B2A2Error("cannot inspect the optimal face of an infeasible structure")
    prices = np.asarray(prices, dtype=float)
    m, loads, capture, _ = _fixed_structure_model(
        inst, struct, "enum-linear-optimal-face")
    energy_optimum = solved["objective"] - float(struct["ops_cost"])
    energy = mip.xsum(float(prices[t]) * loads[t]
                      for t in range(inst.n_slots))
    m += energy <= energy_optimum + objective_tolerance
    ranges = []
    for slot in capture["active_load_slots"]:
        m.objective = loads[slot]
        low_stats = optimize(m, solve_lp_first=False)
        if low_stats.status != "OPTIMAL":
            raise B2A2Error("optimal-face minimum solve failed")
        low = float(loads[slot].x or 0.0)
        m.objective = -loads[slot]
        high_stats = optimize(m, solve_lp_first=False)
        if high_stats.status != "OPTIMAL":
            raise B2A2Error("optimal-face maximum solve failed")
        high = float(loads[slot].x or 0.0)
        ranges.append({
            "slot": slot,
            "min_kwh": canonical_number(low),
            "max_kwh": canonical_number(high),
            "range_kwh": canonical_number(max(0.0, high - low)),
        })
    return {
        "objective_tolerance": objective_tolerance,
        "active_load_slots": capture["active_load_slots"],
        "slot_ranges": ranges,
        "max_load_range_kwh": canonical_number(
            max((row["range_kwh"] for row in ranges), default=0.0)),
    }


def _solve_pwl_true(m, L, cost, market: AffineMarket, base_obj_expr,
                    pwl_tol: float):
    """Shared adaptive scheme: solve, exact-evaluate, refine tangents at the
    incumbent load until slack <= pwl_tol. Returns (exact_value, model_value,
    L_values). Tangents are added to the SAME model incrementally."""
    T = market.n_slots
    lmax = max(1.0, 10 * float(np.max(market.U)) + 1e4)
    for t in range(T):
        for (sl, ic) in market.system_delta_segments(lmax, 8)[t]:
            m += cost[t] >= sl * L[t] + ic
    for _ in range(200):
        st = optimize(m, solve_lp_first=False)
        if st.status != "OPTIMAL":
            return None, None, None
        L_v = np.array([float(v.x or 0.0) for v in L])
        model = float(st.obj)
        base_val = model - sum(float(c.x or 0.0) for c in cost)
        exact = base_val + market.system_delta_true(L_v)
        if exact - model <= pwl_tol:
            return exact, model, L_v
        segs = market.system_delta_tangents_at(L_v)
        for t in range(T):
            sl, ic = segs[t]
            m += cost[t] >= sl * L[t] + ic
    raise B2A2Error("enumeration PWL refinement did not converge")


def enumerated_ch(inst: Instance, market: AffineMarket,
                  pwl_tol: float = PWL_TOL) -> dict:
    """Exact convex-hull value by complete enumeration (independent of CG)."""
    structures = enumerate_structures(inst)
    T = market.n_slots
    m = new_model("enum-ch")
    lams = [m.add_var(lb=0.0) for _ in structures]
    m += mip.xsum(lams) == 1
    load_terms = [[] for _ in range(T)]
    for struct, lam in zip(structures, lams):
        _add_structure_block(m, inst, struct, lam, load_terms)
    L = [m.add_var(lb=0.0) for _ in range(T)]
    for t in range(T):
        m += L[t] == mip.xsum(load_terms[t])
    cost = [m.add_var(lb=0.0) for _ in range(T)]
    base = mip.xsum(lams[i] * float(structures[i]["ops_cost"])
                    for i in range(len(structures)))
    m.objective = base + mip.xsum(cost)
    exact, model, L_v = _solve_pwl_true(m, L, cost, market, base, pwl_tol)
    if exact is None:
        raise B2A2Error("enumerated CH master infeasible")
    return {"z_ch": exact, "z_ch_model": model,
            "n_structures": len(structures),
            "load": [float(x) for x in L_v]}


def structure_true_value(inst: Instance, struct, market: AffineMarket,
                         pwl_tol: float = PWL_TOL):
    """min over charging in P_s of ops_s + DeltaC_true(load); None if the
    structure is SOC-infeasible at full weight."""
    T = market.n_slots
    m = new_model("enum-struct")
    one = m.add_var(lb=1.0, ub=1.0)
    load_terms = [[] for _ in range(T)]
    _add_structure_block(m, inst, struct, one, load_terms)
    L = [m.add_var(lb=0.0) for _ in range(T)]
    for t in range(T):
        m += L[t] == mip.xsum(load_terms[t]) if load_terms[t] else L[t] == 0
    cost = [m.add_var(lb=0.0) for _ in range(T)]
    m.objective = mip.xsum(cost)  # ops added as constant afterwards
    exact, _model, _L = _solve_pwl_true(m, L, cost, market, 0.0, pwl_tol)
    if exact is None:
        return None
    return float(struct["ops_cost"]) + exact


def structure_true_response(
    inst: Instance,
    struct: dict,
    market: AffineMarket,
    pwl_tol: float = PWL_TOL,
) -> dict | None:
    """Enumerated dictator subproblem with its physical response attached."""
    m, loads, capture, struct = _fixed_structure_model(
        inst, struct, "enum-dictator-structure")
    cost = [m.add_var(lb=0.0) for _ in range(inst.n_slots)]
    m.objective = mip.xsum(cost)
    exact_energy, model_energy, _ = _solve_pwl_true(
        m, loads, cost, market, 0.0, pwl_tol)
    if exact_energy is None:
        return None
    sol = _materialize_structure_solution(
        inst, struct, capture, loads, stats=None)
    exact = float(struct["ops_cost"]) + market.system_delta_true(sol.load)
    model = float(struct["ops_cost"]) + float(model_energy)
    sol.obj_true = exact
    sol.obj_model = model
    sol.energy_cost_model = model - sol.ops_cost
    return {
        "structure": struct,
        "structure_id": structure_id(struct),
        "solution_object": sol,
        "solution": canonical_solution_record(sol),
        "objective_upper": exact,
        "objective_lower": model,
        "pwl_gap_abs": max(0.0, exact - model),
        "n_charge_variables": capture["n_charge_variables"],
        "active_load_slots": capture["active_load_slots"],
    }


def enumerated_dictator_details(
    inst: Instance,
    market: AffineMarket,
    pwl_tol: float = PWL_TOL,
) -> dict:
    """Complete per-structure dictator evidence, including uniqueness margin."""
    structures = sorted(
        enumerate_structures(inst),
        key=lambda struct: structure_id(struct),
    )
    rows = []
    feasible = []
    for index, struct in enumerate(structures):
        solved = structure_true_response(inst, struct, market, pwl_tol)
        if solved is None:
            rows.append({
                "index": index,
                "structure_id": structure_id(struct),
                "structure": {
                    **canonical_structure(struct),
                    "ops_cost": canonical_number(struct["ops_cost"]),
                },
                "feasible": False,
            })
            continue
        feasible.append(solved)
        rows.append({
            "index": index,
            "structure_id": solved["structure_id"],
            "structure": {
                **canonical_structure(struct),
                "ops_cost": canonical_number(struct["ops_cost"]),
            },
            "feasible": True,
            "objective_upper": canonical_number(solved["objective_upper"]),
            "objective_lower": canonical_number(solved["objective_lower"]),
            "pwl_gap_abs": canonical_number(solved["pwl_gap_abs"]),
            "n_charge_variables": solved["n_charge_variables"],
            "active_load_slots": solved["active_load_slots"],
            "solution": solved["solution"],
        })
    if not feasible:
        raise B2A2Error("no feasible structure")
    ranked = sorted(
        feasible,
        key=lambda row: (row["objective_upper"], row["structure_id"]),
    )
    best = ranked[0]
    other_lower = min(
        (row["objective_lower"] for row in feasible
         if row["structure_id"] != best["structure_id"]),
        default=float("inf"),
    )
    separation = other_lower - best["objective_upper"]
    return {
        "pwl_tolerance": pwl_tol,
        "n_structures": len(structures),
        "n_feasible": len(feasible),
        "n_infeasible": len(structures) - len(feasible),
        "best_structure_id": best["structure_id"],
        "z_d_upper": canonical_number(best["objective_upper"]),
        "z_d_lower": canonical_number(best["objective_lower"]),
        "best_response": canonical_solution_record(best["solution_object"]),
        "other_structures_lower_bound": (
            canonical_number(other_lower)
            if math.isfinite(other_lower) else None),
        "certified_unique_structure_margin": (
            canonical_number(separation)
            if math.isfinite(separation) else None),
        "structures": rows,
    }


def enumerated_dictator(inst: Instance, market: AffineMarket,
                        pwl_tol: float = PWL_TOL) -> dict:
    structures = enumerate_structures(inst)
    best, best_struct, n_feas = None, None, 0
    for s in structures:
        v = structure_true_value(inst, s, market, pwl_tol)
        if v is None:
            continue
        n_feas += 1
        if best is None or v < best:
            best, best_struct = v, s
    if best is None:
        raise B2A2Error("no feasible structure")
    return {"z_d": best, "structure": best_struct,
            "n_structures": len(structures), "n_feasible": n_feas}


# ---------------------------------------------------------------------------
# independent strict-cycle witness replay
# ---------------------------------------------------------------------------
def _instance_from_canonical(record: dict) -> Instance:
    data = dict(record)
    data["trips"] = [Trip(**trip) for trip in data["trips"]]
    data["dh_min"] = {
        (left, right): value for left, right, value in data["dh_min"]}
    data["dh_kwh"] = {
        (left, right): value for left, right, value in data["dh_kwh"]}
    return Instance(**data)


def _market_from_record(record: dict) -> AffineMarket:
    return AffineMarket(
        record["a"],
        record["b"],
        record["base_load"],
        name=record["name"],
    )


def _solution_from_record(record: dict) -> Solution:
    return Solution(
        sequences=[list(seq) for seq in record["sequences"]],
        arc_kinds=[list(kinds) for kinds in record["arc_kinds"]],
        charges=[dict(charge) for charge in record["charges"]],
        load=[float(value) for value in record["load"]],
        fleet=int(record["fleet"]),
        ops_cost=float(record["ops_cost"]),
        energy_charged_kwh=float(record["energy_charged_kwh"]),
        oracle_tier="witness-replay-input",
    )


def _assert_witness_close(actual, expected, path: str, tolerance: float):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise B2A2Error(
                f"witness replay mismatch at {path}: dictionary keys differ")
        for key in expected:
            _assert_witness_close(
                actual[key], expected[key], f"{path}.{key}", tolerance)
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise B2A2Error(
                f"witness replay mismatch at {path}: list length differs")
        for index, (left, right) in enumerate(zip(actual, expected)):
            _assert_witness_close(
                left, right, f"{path}[{index}]", tolerance)
        return
    if (
        isinstance(expected, (int, float))
        and not isinstance(expected, bool)
    ):
        if (
            not isinstance(actual, (int, float))
            or not math.isfinite(float(actual))
            or abs(float(actual) - float(expected)) > tolerance
        ):
            raise B2A2Error(
                f"witness replay mismatch at {path}: "
                f"{actual!r} != {expected!r}")
        return
    if actual != expected:
        raise B2A2Error(
            f"witness replay mismatch at {path}: "
            f"{actual!r} != {expected!r}")


def _enumerated_strict_cycle_status(
    inst: Instance,
    market: AffineMarket,
    price_tolerance: float,
    strict_margin: float,
) -> dict:
    """Independent dynamics using only complete structure enumeration."""
    prices = market.price(np.zeros(market.n_slots))
    history = []
    rows = []
    outcome = None
    for iteration in range(8):
        enumeration = enumerate_price_responses(inst, prices)
        best = next(
            row for row in enumeration["responses"]
            if row["structure_id"] == enumeration["best_structure_id"])
        load = np.asarray(best["solution"]["load"], dtype=float)
        induced = market.price(load)
        rows.append({
            "iteration": iteration,
            "structure_id": best["structure_id"],
            "load": best["solution"]["load"],
            "margin": enumeration["strict_structure_margin"],
            "prices": [canonical_number(value) for value in prices],
            "induced": [canonical_number(value) for value in induced],
        })
        if float(np.max(np.abs(induced - prices))) <= price_tolerance:
            outcome = {"type": "fixed_point", "iteration": iteration}
        else:
            for first_seen in range(max(0, len(history) - 1)):
                if float(np.max(np.abs(
                        prices - history[first_seen]))) <= price_tolerance:
                    outcome = {
                        "type": "cycle",
                        "first_seen": first_seen,
                        "length": iteration - first_seen,
                        "iteration": iteration,
                    }
                    break
        if outcome is not None:
            break
        history.append(np.asarray(prices, dtype=float))
        prices = induced
    if outcome is None:
        outcome = {"type": "max_iters", "iteration": 8}
    strict = False
    if outcome.get("type") == "cycle" and outcome.get("length") == 2:
        first = outcome["first_seen"]
        orbit = rows[first:first + 2]
        strict = bool(
            len(orbit) == 2
            and orbit[0]["structure_id"] != orbit[1]["structure_id"]
            and all(
                row["margin"] is not None
                and float(row["margin"]) > strict_margin
                for row in orbit
            )
        )
    return {"strict": strict, "outcome": outcome, "rows": rows}


def replay_cycle_witness(
    witness: dict,
    verify_integrity: bool = True,
) -> dict:
    """Replay a canonical witness without the compact EVSP cycle oracle."""
    expected_schema = "egglab.strict-undamped-two-cycle.v1"
    if witness.get("schema") != expected_schema:
        raise B2A2Error(
            f"unsupported strict-cycle witness schema {witness.get('schema')!r}")
    if verify_integrity:
        integrity = witness.get("integrity", {})
        claimed = integrity.get("canonical_payload_sha256")
        payload = {
            key: value for key, value in witness.items()
            if key != "integrity"
        }
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode()
        actual = hashlib.sha256(encoded).hexdigest()
        if claimed != actual:
            raise B2A2Error(
                "strict-cycle witness canonical payload hash mismatch")

    inst = _instance_from_canonical(witness["instance"])
    if json.loads(json.dumps(
            inst.canonical(), sort_keys=True)) != witness["instance"]:
        raise B2A2Error("instance does not round-trip canonically")
    market = _market_from_record(witness["market"])
    evidence = witness["computational_evidence"]
    cycle = evidence["cycle"]
    tolerances = witness["tolerances"]
    price_tolerance = float(tolerances["price_state_inf"])
    load_tolerance = float(tolerances["load_match_and_replay_kwh"])
    strict_required = float(tolerances["strict_margin_required"])
    objective_ceiling = float(tolerances["objective_tolerance_ceiling"])

    trajectory = cycle["complete_iteration_trajectory"]
    if len(trajectory) != 3:
        raise B2A2Error(
            "complete strict two-cycle trajectory must contain three solves")
    replayed_enumerations = []
    margins = []
    for index, row in enumerate(trajectory):
        sol = _solution_from_record(row["response"])
        violations = validate_solution(inst, sol)
        if violations:
            raise B2A2Error(
                f"witness response {index} failed physical replay: "
                + "; ".join(violations))
        if structure_id(sol.sequences, sol.arc_kinds) != (
                row["response"]["structure_id"]):
            raise B2A2Error(
                f"witness response {index} structure id mismatch")
        posted = np.asarray(row["posted_prices"], dtype=float)
        induced = market.price(sol.load)
        if float(np.max(np.abs(
                induced - np.asarray(row["induced_prices"], dtype=float)))) > (
                    price_tolerance):
            raise B2A2Error(
                f"witness response {index} induced-price mismatch")
        if index < len(trajectory) - 1:
            next_posted = np.asarray(
                trajectory[index + 1]["posted_prices"], dtype=float)
            if float(np.max(np.abs(induced - next_posted))) > price_tolerance:
                raise B2A2Error(
                    f"trajectory transition {index}->{index + 1} is broken")
        enumeration = enumerate_price_responses(inst, posted)
        if (
            enumeration["best_structure_id"]
            != row["response"]["structure_id"]
        ):
            raise B2A2Error(
                f"response {index} is not the enumerated best structure")
        best = next(
            candidate for candidate in enumeration["responses"]
            if candidate["structure_id"] == enumeration["best_structure_id"])
        if float(np.max(np.abs(
                np.asarray(best["solution"]["load"], dtype=float)
                - np.asarray(sol.load, dtype=float)))) > load_tolerance:
            raise B2A2Error(
                f"response {index} load differs from enumerated replay")
        if index < 2:
            replayed_enumerations.append(enumeration)
            margins.append(float(enumeration["strict_structure_margin"]))

    if float(np.max(np.abs(
            np.asarray(trajectory[2]["posted_prices"], dtype=float)
            - np.asarray(trajectory[0]["posted_prices"], dtype=float)))) > (
                price_tolerance):
        raise B2A2Error("trajectory does not close after two transitions")
    if (
        trajectory[0]["response"]["structure_id"]
        == trajectory[1]["response"]["structure_id"]
    ):
        raise B2A2Error("cycle endpoints do not have distinct structures")
    if min(margins) <= strict_required:
        raise B2A2Error("independent structure margins are not strict")

    expected_states = evidence[
        "exhaustive_feasible_response_enumeration"]["states"]
    for index, enumeration in enumerate(replayed_enumerations):
        expected = dict(expected_states[index])
        expected.pop("state")
        _assert_witness_close(
            enumeration, expected, f"enumeration.state[{index}]", 1e-9)

    dictator = enumerated_dictator_details(
        inst, market, pwl_tol=float(
            evidence["convex_hull_dictator_comparison"]["pwl_tolerance"]))
    _assert_witness_close(
        dictator,
        evidence["fixed_point_absence"]["enumerated_dictator"],
        "fixed_point_absence.enumerated_dictator",
        1e-8,
    )
    best_dictator = next(
        row for row in dictator["structures"]
        if row["structure_id"] == dictator["best_structure_id"])
    candidate = dictator["best_response"]
    candidate_prices = market.price(candidate["load"])
    candidate_responses = enumerate_price_responses(inst, candidate_prices)
    candidate_objective = (
        float(candidate["ops_cost"])
        + float(np.dot(candidate_prices, candidate["load"]))
    )
    deviation = candidate_objective - float(
        candidate_responses["best_objective"])
    if not (
        float(dictator["certified_unique_structure_margin"])
        > objective_ceiling
        and best_dictator["n_charge_variables"] == 0
        and deviation > objective_ceiling
    ):
        raise B2A2Error(
            "fixed-point-absence computational preconditions failed replay")

    hull = enumerated_ch(
        inst, market, pwl_tol=float(
            evidence["convex_hull_dictator_comparison"]["pwl_tolerance"]))
    comparison = evidence["convex_hull_dictator_comparison"]
    hull_replay = {
        "z_ch_lower_model": canonical_number(hull["z_ch_model"]),
        "z_ch_upper_exact_incumbent": canonical_number(hull["z_ch"]),
        "z_ch_load": [canonical_number(value) for value in hull["load"]],
        "z_d_lower": dictator["z_d_lower"],
        "z_d_upper": dictator["z_d_upper"],
        "uplift_interval": [
            canonical_number(dictator["z_d_lower"] - hull["z_ch"]),
            canonical_number(dictator["z_d_upper"] - hull["z_ch_model"]),
        ],
        "n_structures": hull["n_structures"],
        "pwl_tolerance": comparison["pwl_tolerance"],
    }
    _assert_witness_close(
        hull_replay, comparison, "convex_hull_dictator_comparison", 1e-8)

    independent_final = _enumerated_strict_cycle_status(
        inst, market, price_tolerance, strict_required)
    if not independent_final["strict"]:
        raise B2A2Error(
            "final witness is not a strict cycle under enumerated replay")
    replayed_irreducibility = 0
    for trial in evidence["irreducibility"]["trials"]:
        if trial["axis"] == "trip":
            candidate_inst = replace(
                inst,
                trips=[
                    trip for trip in inst.trips
                    if trip.id != trial["removed"]
                ],
            )
            candidate_market = market
        elif trial["axis"] == "vehicle_capacity":
            candidate_inst = replace(
                inst, max_vehicles=inst.max_vehicles - 1)
            candidate_market = market
        elif trial["axis"] == "affine_feedback_slot":
            slopes = market.b.copy()
            slopes[int(trial["removed"])] = 0.0
            candidate_inst = inst
            candidate_market = AffineMarket(
                market.a.copy(), slopes, market.U.copy(),
                name="independent-irreducibility-replay")
        else:
            raise B2A2Error(
                f"unknown irreducibility axis {trial['axis']!r}")
        status = _enumerated_strict_cycle_status(
            candidate_inst, candidate_market,
            price_tolerance, strict_required)
        if status["strict"]:
            raise B2A2Error(
                f"irreducibility trial unexpectedly preserves strict cycle: "
                f"{trial['axis']} {trial['removed']}")
        replayed_irreducibility += 1

    report = {
        "engine": "egglab.enumerate_tiny",
        "status": "pass",
        "checks": {
            "canonical_instance_round_trip": True,
            "physical_schedule_replay": True,
            "complete_trajectory": True,
            "exhaustive_response_enumeration": True,
            "strict_structure_margins": True,
            "fixed_point_absence_preconditions": True,
            "convex_hull_dictator_comparison": True,
            "irreducibility": True,
        },
        "n_structures": replayed_enumerations[0]["n_structures"],
        "n_feasible_responses_by_state": [
            row["n_feasible"] for row in replayed_enumerations],
        "minimum_structure_margin": canonical_number(min(margins)),
        "fixed_point_profitable_deviation_margin": canonical_number(deviation),
        "irreducibility_trials_replayed": replayed_irreducibility,
    }
    if "independent_replay" in witness:
        _assert_witness_close(
            report, witness["independent_replay"],
            "independent_replay", 1e-9)
    return report


def _main(argv=None):
    parser = argparse.ArgumentParser(
        description="Independent replay for a tiny strict-cycle witness")
    parser.add_argument("--replay", required=True, help="canonical witness JSON")
    args = parser.parse_args(argv)
    with open(args.replay) as handle:
        witness = json.load(handle)
    report = replay_cycle_witness(witness)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
