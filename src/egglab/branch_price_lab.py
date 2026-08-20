"""Tiny, external branch-and-price exactness laboratory.

The normative formulation and proofs are in
``doc/TINY_BRANCH_PRICE_EXACTNESS_LAB.md``.  This module deliberately supports
only independently enumerable instances with at most four trips.  Gurobi
solves clean node masters and full-fleet pricing MILPs; all tree management,
branching, replay, and checkpointing remains external Python logic.
"""
from __future__ import annotations

import json
import math
import os
import time
from typing import Iterable

import numpy as np

try:  # Optional by repository policy; CBC-only installs must still import.
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:  # pragma: no cover - exercised in an isolated subprocess
    gp = None
    GRB = None

from . import checkpoint
from .b2a2 import (
    B2A2Error,
    canonicalize_pricing_solution,
    column_from_solution,
    market_hash,
)
from .evsp import (
    Solution,
    depot_pairs,
    direct_pairs,
    slot_overlaps,
    validate_solution,
)
from .instance import Instance
from .market import AffineMarket
from .records import provenance
from .regimes import _l_max
from .solver import SolveStats


SCHEMA_VERSION = "tiny-branch-price-v1"
BASE_ORIGIN_MAIN_SHA = "5b63e725d0fd85cfb0b83f462a612016e7f4321a"
MAX_TRIPS = 4
DEFAULT_EPSILON = 1e-5
DEFAULT_PWL_TOL = 1e-6
DEFAULT_RC_TOL = 1e-8
DEFAULT_INTEGRAL_TOL = 1e-8
DEFAULT_SUPPORT_TOL = 1e-9
DEFAULT_PRICING_MIP_GAP = 1e-9
DEFAULT_NODE_BUDGET = 200
MAX_REFINEMENTS = 200
MAX_DUPLICATE_RETRIES = 3

# Frozen safety gate from the spike request.  It applies to synthetic fixture
# identity, not Gurobi's deterministic internal Seed parameter (which is 0).
FORBIDDEN_FIXTURE_SEEDS = frozenset(range(16, 38))

_KIND_ORDER = {"out": 0, "in": 1, "dir": 2, "dep": 3}


class ExactnessLabError(RuntimeError):
    """A correctness invariant of the tiny laboratory failed."""


def _finite(value) -> bool:
    return value is not None and math.isfinite(float(value))


def gurobi_available() -> bool:
    """Whether the optional direct-Gurobi dependency can be imported."""
    return gp is not None and GRB is not None


def _require_gurobi() -> None:
    if not gurobi_available():
        raise ExactnessLabError(
            "the tiny branch-and-price laboratory requires the optional "
            "'gurobipy' package; the rest of egglab remains CBC-compatible"
        )


def _status_name(code: int) -> str:
    _require_gurobi()
    names = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.NUMERIC: "NUMERIC",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }
    return names.get(code, f"STATUS_{code}")


def _gurobi_version() -> str:
    _require_gurobi()
    return ".".join(str(x) for x in gp.gurobi.version())


def _new_model(name: str) -> gp.Model:
    """Create the only solver used by this laboratory."""
    _require_gurobi()
    try:
        model = gp.Model(name)
    except gp.GurobiError as exc:
        raise ExactnessLabError(
            "the tiny exactness laboratory requires a usable Gurobi license"
        ) from exc
    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.Params.Seed = 0
    model.Params.FeasibilityTol = 1e-8
    model.Params.OptimalityTol = 1e-8
    model.Params.IntFeasTol = 1e-9
    cpus = os.environ.get("SLURM_CPUS_PER_TASK")
    if cpus:
        try:
            model.Params.Threads = int(cpus)
        except (TypeError, ValueError, gp.GurobiError):
            pass
    return model


# ---------------------------------------------------------------------------
# Label-invariant structural arcs
# ---------------------------------------------------------------------------
def structural_arc(kind: str, tail: str | None, head: str | None) -> dict:
    if kind not in _KIND_ORDER:
        raise ExactnessLabError(f"unknown structural arc kind {kind!r}")
    if kind == "out" and (tail is not None or head is None):
        raise ExactnessLabError("pull-out arc must be (None, trip)")
    if kind == "in" and (tail is None or head is not None):
        raise ExactnessLabError("pull-in arc must be (trip, None)")
    if kind in {"dir", "dep"} and (tail is None or head is None):
        raise ExactnessLabError(f"{kind} arc needs two trips")
    return {"kind": kind, "tail": tail, "head": head}


def arc_key(arc: dict) -> str:
    """Stable, unambiguous JSON key for one structural arc."""
    return json.dumps(
        [arc["kind"], arc.get("tail"), arc.get("head")],
        separators=(",", ":"),
    )


def arc_from_key(key: str) -> dict:
    try:
        kind, tail, head = json.loads(key)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ExactnessLabError(f"invalid structural arc key {key!r}") from exc
    return structural_arc(kind, tail, head)


def _arc_sort_key(arc: dict):
    return (
        _KIND_ORDER[arc["kind"]],
        "" if arc.get("tail") is None else arc["tail"],
        "" if arc.get("head") is None else arc["head"],
    )


def structural_arc_catalog(inst: Instance) -> list[dict]:
    """Every label-invariant structural arc present in the full-fleet model."""
    arcs = []
    for trip in sorted(inst.trips, key=lambda tr: tr.id):
        arcs.append(structural_arc("out", None, trip.id))
        arcs.append(structural_arc("in", trip.id, None))
    for i, j in direct_pairs(inst):
        arcs.append(structural_arc("dir", inst.trips[i].id, inst.trips[j].id))
    for i, j, _w0, _w1 in depot_pairs(inst):
        arcs.append(structural_arc("dep", inst.trips[i].id, inst.trips[j].id))
    unique = {arc_key(arc): arc for arc in arcs}
    return sorted(unique.values(), key=_arc_sort_key)


def canonical_branch_constraints(
    inst: Instance, constraints: Iterable[dict] | None
) -> list[dict]:
    """Validate, deduplicate, and sort x_a in {0,1} decisions."""
    catalog = {arc_key(arc): arc for arc in structural_arc_catalog(inst)}
    values: dict[str, int] = {}
    for item in constraints or []:
        if not isinstance(item, dict) or "arc" not in item or "value" not in item:
            raise ExactnessLabError(f"malformed branch constraint {item!r}")
        key = arc_key(item["arc"])
        if key not in catalog:
            raise ExactnessLabError(
                f"branch constraint references absent structural arc {item['arc']!r}"
            )
        value = item["value"]
        if value not in (0, 1):
            raise ExactnessLabError(f"branch value must be 0/1, got {value!r}")
        if key in values and values[key] != int(value):
            raise ExactnessLabError(f"contradictory branch decisions for {key}")
        values[key] = int(value)
    return [
        {"arc": catalog[key], "value": values[key]}
        for key in sorted(values, key=lambda k: _arc_sort_key(catalog[k]))
    ]


def structural_incidence(
    inst: Instance, sequences: list, arc_kinds: list
) -> dict[str, int]:
    """Aggregate path-cover incidence, independent of vehicle labels."""
    if len(sequences) != len(arc_kinds):
        raise ExactnessLabError("sequence/arc-kind count mismatch")
    catalog = {arc_key(arc) for arc in structural_arc_catalog(inst)}
    incidence: dict[str, int] = {}
    covered = []
    for sequence, kinds in zip(sequences, arc_kinds):
        if not sequence:
            raise ExactnessLabError("empty vehicle sequence")
        if len(kinds) != len(sequence) - 1:
            raise ExactnessLabError("arc-kind length does not match sequence")
        covered.extend(sequence)
        selected = [
            structural_arc("out", None, sequence[0]),
            structural_arc("in", sequence[-1], None),
        ]
        selected.extend(
            structural_arc(kind, tail, head)
            for tail, head, kind in zip(sequence, sequence[1:], kinds)
        )
        for arc in selected:
            key = arc_key(arc)
            if key not in catalog:
                raise ExactnessLabError(f"solution uses absent structural arc {arc!r}")
            incidence[key] = incidence.get(key, 0) + 1
    trip_ids = sorted(trip.id for trip in inst.trips)
    if sorted(covered) != trip_ids:
        raise ExactnessLabError("structural incidence does not cover trips exactly once")
    if any(value != 1 for value in incidence.values()):
        raise ExactnessLabError("aggregate structural incidence is not binary")
    return incidence


def column_structural_incidence(inst: Instance, column: dict) -> dict[str, int]:
    stored = column.get("structural_incidence")
    derived = structural_incidence(
        inst, column["sequences"], column["arc_kinds"]
    )
    if stored is not None and stored != derived:
        raise ExactnessLabError("stored column incidence disagrees with replay")
    return derived


def restrictions_satisfied(
    inst: Instance, incidence: dict[str, int], constraints: Iterable[dict]
) -> bool:
    canonical = canonical_branch_constraints(inst, constraints)
    return all(
        incidence.get(arc_key(item["arc"]), 0) == item["value"]
        for item in canonical
    )


# ---------------------------------------------------------------------------
# Direct-Gurobi full-fleet MILP oracle
# ---------------------------------------------------------------------------
def _solve_full_fleet_oracle(
    inst: Instance,
    prices,
    constraints: Iterable[dict] | None,
    *,
    call_id: str,
    mip_gap: float,
) -> dict:
    """Optimize the complete vehicle-indexed fleet MILP under node decisions.

    Returns a serializable event containing either a replayed physical column
    or a certified INFEASIBLE status.
    """
    prices = np.asarray(prices, dtype=float)
    if prices.shape != (inst.n_slots,) or not np.all(np.isfinite(prices)):
        raise ExactnessLabError("pricing vector is wrong-length or nonfinite")
    branch = canonical_branch_constraints(inst, constraints)

    n = len(inst.trips)
    V = inst.max_vehicles
    D = inst.depot
    B = inst.battery_kwh
    M = 2.0 * B
    dirp = direct_pairs(inst)
    depp = depot_pairs(inst)
    dirset = {(i, j) for i, j in dirp}
    depset = {(i, j) for i, j, _w0, _w1 in depp}
    trip_index = {trip.id: i for i, trip in enumerate(inst.trips)}

    model = _new_model(f"tiny-bp-oracle-{call_id}")
    model.Params.MIPGap = float(mip_gap)
    u = model.addVars(V, n, vtype=GRB.BINARY, name="u")
    o = model.addVars(V, n, vtype=GRB.BINARY, name="o")
    z = model.addVars(V, n, vtype=GRB.BINARY, name="z")
    used = model.addVars(V, vtype=GRB.BINARY, name="used")
    xd = {
        (v, i, j): model.addVar(vtype=GRB.BINARY, name=f"xd[{v},{i},{j}]")
        for v in range(V)
        for i, j in dirp
    }
    xg = {
        (v, i, j): model.addVar(vtype=GRB.BINARY, name=f"xg[{v},{i},{j}]")
        for v in range(V)
        for i, j, _w0, _w1 in depp
    }
    e = {}
    arc_slots = {}
    for i, j, w0, w1 in depp:
        overlaps = slot_overlaps(inst, w0, w1)
        arc_slots[(i, j)] = overlaps
        for v in range(V):
            for t, overlap in overlaps:
                e[v, i, j, t] = model.addVar(
                    lb=0.0,
                    ub=inst.charge_power_kw * overlap / 60.0,
                    name=f"e[{v},{i},{j},{t}]",
                )
    sb = model.addVars(
        V, n, lb=inst.soc_min_kwh, ub=B, name="soc_before"
    )
    sa = model.addVars(
        V, n, lb=inst.soc_min_kwh, ub=B, name="soc_after"
    )
    load = model.addVars(inst.n_slots, lb=0.0, name="load")

    for i in range(n):
        model.addConstr(gp.quicksum(u[v, i] for v in range(V)) == 1)
    for v in range(V):
        for i in range(n):
            model.addConstr(
                u[v, i]
                == o[v, i]
                + gp.quicksum(
                    xd[v, j, i] for j, i2 in dirp if i2 == i
                )
                + gp.quicksum(
                    xg[v, j, i] for j, i2, _w0, _w1 in depp if i2 == i
                )
            )
            model.addConstr(
                u[v, i]
                == z[v, i]
                + gp.quicksum(
                    xd[v, i, j] for i2, j in dirp if i2 == i
                )
                + gp.quicksum(
                    xg[v, i, j] for i2, j, _w0, _w1 in depp if i2 == i
                )
            )
        model.addConstr(used[v] == gp.quicksum(o[v, i] for i in range(n)))
    for v in range(V - 1):
        model.addConstr(used[v] >= used[v + 1])

    for v in range(V):
        for i, trip in enumerate(inst.trips):
            model.addConstr(sa[v, i] == sb[v, i] - trip.energy_kwh)
            pull_out_soc = inst.soc0_kwh - inst.dhk(D, trip.start_loc)
            model.addConstr(
                sb[v, i] <= pull_out_soc + M * (1 - o[v, i])
            )
            model.addConstr(
                sb[v, i] >= pull_out_soc - M * (1 - o[v, i])
            )
            model.addConstr(
                sa[v, i] - inst.dhk(trip.end_loc, D)
                >= inst.soc_end_kwh - M * (1 - z[v, i])
            )
        for i, j in dirp:
            deadhead = inst.dhk(
                inst.trips[i].end_loc, inst.trips[j].start_loc
            )
            model.addConstr(
                sb[v, j] <= sa[v, i] - deadhead + M * (1 - xd[v, i, j])
            )
            model.addConstr(
                sb[v, j] >= sa[v, i] - deadhead - M * (1 - xd[v, i, j])
            )
        for i, j, _w0, _w1 in depp:
            d1 = inst.dhk(inst.trips[i].end_loc, D)
            d2 = inst.dhk(D, inst.trips[j].start_loc)
            x = xg[v, i, j]
            charge = gp.quicksum(
                e[v, i, j, t] for t, _overlap in arc_slots[i, j]
            )
            model.addConstr(
                sb[v, j] <= sa[v, i] - d1 - d2 + charge + M * (1 - x)
            )
            model.addConstr(
                sb[v, j] >= sa[v, i] - d1 - d2 + charge - M * (1 - x)
            )
            model.addConstr(sa[v, i] - d1 + charge <= B + M * (1 - x))
            model.addConstr(
                sa[v, i] - d1 >= inst.soc_min_kwh - M * (1 - x)
            )
            model.addConstr(charge <= B * x)

    for t in range(inst.n_slots):
        model.addConstr(
            load[t]
            == gp.quicksum(
                variable
                for (v, i, j, slot), variable in e.items()
                if slot == t
            )
        )

    # Node restrictions are equations on aggregate vehicle-indexed binaries.
    for item in branch:
        arc = item["arc"]
        value = item["value"]
        kind, tail, head = arc["kind"], arc.get("tail"), arc.get("head")
        if kind == "out":
            i = trip_index[head]
            expression = gp.quicksum(o[v, i] for v in range(V))
        elif kind == "in":
            i = trip_index[tail]
            expression = gp.quicksum(z[v, i] for v in range(V))
        elif kind == "dir":
            i, j = trip_index[tail], trip_index[head]
            if (i, j) not in dirset:
                raise ExactnessLabError(f"absent direct branch arc {arc!r}")
            expression = gp.quicksum(xd[v, i, j] for v in range(V))
        else:
            i, j = trip_index[tail], trip_index[head]
            if (i, j) not in depset:
                raise ExactnessLabError(f"absent depot branch arc {arc!r}")
            expression = gp.quicksum(xg[v, i, j] for v in range(V))
        model.addConstr(expression == value, name=f"branch[{arc_key(arc)}]")

    deadhead_expr = (
        gp.quicksum(
            o[v, i] * inst.dhm(D, inst.trips[i].start_loc)
            + z[v, i] * inst.dhm(inst.trips[i].end_loc, D)
            for v in range(V)
            for i in range(n)
        )
        + gp.quicksum(
            xd[v, i, j]
            * inst.dhm(inst.trips[i].end_loc, inst.trips[j].start_loc)
            for v in range(V)
            for i, j in dirp
        )
        + gp.quicksum(
            xg[v, i, j]
            * (
                inst.dhm(inst.trips[i].end_loc, D)
                + inst.dhm(D, inst.trips[j].start_loc)
            )
            for v in range(V)
            for i, j, _w0, _w1 in depp
        )
    )
    operations = (
        inst.vehicle_fixed_cost * gp.quicksum(used[v] for v in range(V))
        + inst.dh_cost_per_min * deadhead_expr
    )
    model.setObjective(
        operations
        + gp.quicksum(float(prices[t]) * load[t] for t in range(inst.n_slots)),
        GRB.MINIMIZE,
    )
    model.update()

    lp_model = model.relax()
    lp_model.Params.OutputFlag = 0
    lp_model.Params.LogToConsole = 0
    lp_start = time.time()
    lp_model.optimize()
    lp_wall = time.time() - lp_start
    lp_status = _status_name(lp_model.Status)
    lp_obj = float(lp_model.ObjVal) if lp_model.Status == GRB.OPTIMAL else None
    lp_model.dispose()

    solve_start = time.time()
    model.optimize()
    if model.Status == GRB.INF_OR_UNBD:
        model.Params.DualReductions = 0
        model.optimize()
    wall = time.time() - solve_start
    status = _status_name(model.Status)
    has_solution = model.SolCount > 0
    objective = float(model.ObjVal) if has_solution else None
    bound = (
        float(model.ObjBound)
        if model.Status != GRB.INFEASIBLE and _finite(model.ObjBound)
        else None
    )
    gap = float(model.MIPGap) if has_solution and _finite(model.MIPGap) else None
    n_integer = sum(
        variable.VType != GRB.CONTINUOUS for variable in model.getVars()
    )
    stats = SolveStats(
        backend="GRB",
        status=status,
        obj=objective,
        bound=bound,
        mip_gap=gap,
        lp_obj=lp_obj,
        lp_mip_gap_abs=(
            objective - lp_obj
            if objective is not None and lp_obj is not None
            else None
        ),
        wall_s=wall,
        lp_wall_s=lp_wall,
        n_vars=model.NumVars,
        n_int=n_integer,
        n_constrs=model.NumConstrs,
        max_mip_gap=mip_gap,
        extra={
            "gurobi_version": _gurobi_version(),
            "status_code": int(model.Status),
            "lp_status": lp_status,
            "node_count": float(model.NodeCount),
            "threads": int(model.Params.Threads),
            "call_id": call_id,
            "branch_constraints": branch,
        },
    )
    event = {
        "call_id": call_id,
        "kind": "seed" if call_id.endswith("-seed") else "pricing",
        "prices": [float(value) for value in prices],
        "branch_constraints": branch,
        "solver": stats.to_dict(),
        "column": None,
        "replay_ok": None,
        **provenance(),
    }

    if model.Status == GRB.INFEASIBLE:
        event["infeasibility_certified"] = True
        model.dispose()
        return event
    if model.Status != GRB.OPTIMAL or not has_solution:
        model.dispose()
        raise ExactnessLabError(
            f"full-fleet oracle {call_id} is not certified: {status}"
        )
    if bound is None:
        model.dispose()
        raise ExactnessLabError(f"oracle {call_id} has no finite bound")

    def value(variable):
        return float(variable.X)

    sequences, arc_kinds, charges = [], [], []
    total_deadhead = 0.0
    for v in range(V):
        starts = [i for i in range(n) if value(o[v, i]) > 0.5]
        if not starts:
            continue
        if len(starts) != 1:
            model.dispose()
            raise ExactnessLabError("oracle extraction found multiple pull-outs")
        i = starts[0]
        sequence = [inst.trips[i].id]
        kinds = []
        total_deadhead += inst.dhm(D, inst.trips[i].start_loc)
        while True:
            next_trip = None
            next_kind = None
            for a, b in dirp:
                if a == i and value(xd[v, a, b]) > 0.5:
                    next_trip, next_kind = b, "dir"
                    total_deadhead += inst.dhm(
                        inst.trips[a].end_loc, inst.trips[b].start_loc
                    )
                    break
            if next_trip is None:
                for a, b, _w0, _w1 in depp:
                    if a == i and value(xg[v, a, b]) > 0.5:
                        next_trip, next_kind = b, "dep"
                        total_deadhead += inst.dhm(
                            inst.trips[a].end_loc, D
                        ) + inst.dhm(D, inst.trips[b].start_loc)
                        for t, _overlap in arc_slots[a, b]:
                            amount = value(e[v, a, b, t])
                            if amount > 1e-8:
                                charges.append(
                                    {
                                        "vehicle": len(sequences),
                                        "after_trip": inst.trips[a].id,
                                        "before_trip": inst.trips[b].id,
                                        "slot": t,
                                        "kwh": amount,
                                    }
                                )
                        break
            if next_trip is None:
                total_deadhead += inst.dhm(inst.trips[i].end_loc, D)
                break
            sequence.append(inst.trips[next_trip].id)
            kinds.append(next_kind)
            i = next_trip
        sequences.append(sequence)
        arc_kinds.append(kinds)

    raw_load = [value(load[t]) for t in range(inst.n_slots)]
    solution = Solution(
        sequences=sequences,
        arc_kinds=arc_kinds,
        charges=charges,
        load=raw_load,
        fleet=len(sequences),
        dh_min_total=total_deadhead,
        energy_charged_kwh=sum(raw_load),
        ops_cost=(
            inst.vehicle_fixed_cost * len(sequences)
            + inst.dh_cost_per_min * total_deadhead
        ),
        obj_model=objective,
        stats=stats,
        oracle_tier="exact-milp/tiny-branch-price",
    )
    solution.energy_cost_model = objective - solution.ops_cost
    canonicalize_pricing_solution(inst, solution, prices)
    violations = validate_solution(inst, solution)
    if violations:
        model.dispose()
        raise ExactnessLabError(
            f"oracle {call_id} failed physical replay: {violations}"
        )
    column = column_from_solution(inst, solution)
    incidence = structural_incidence(inst, sequences, arc_kinds)
    if not restrictions_satisfied(inst, incidence, branch):
        model.dispose()
        raise ExactnessLabError(f"oracle {call_id} violates its branch decisions")
    column["structural_incidence"] = incidence
    event.update(
        column=column,
        replay_ok=True,
        infeasibility_certified=False,
        physical_objective=float(solution.obj_true),
        pricing_bound=float(bound),
    )
    model.dispose()
    return event


# ---------------------------------------------------------------------------
# Clean restricted master and node column generation
# ---------------------------------------------------------------------------
def _solve_clean_rmp(
    inst: Instance,
    market: AffineMarket,
    columns: list[dict],
    tangent_points: list,
    *,
    pwl_tol: float,
    solve_id_prefix: str,
) -> dict:
    if not columns:
        raise ExactnessLabError("clean node master needs at least one column")
    tangent_points = [list(map(float, point)) for point in tangent_points]
    solves = []
    total_wall = 0.0
    for refinement in range(MAX_REFINEMENTS):
        model = _new_model(f"tiny-bp-rmp-{solve_id_prefix}-{refinement}")
        lambdas = model.addVars(len(columns), lb=0.0, name="lambda")
        load = model.addVars(market.n_slots, lb=0.0, name="load")
        cost = model.addVars(market.n_slots, lb=0.0, name="cost")
        link = []
        for t in range(market.n_slots):
            link.append(
                model.addConstr(
                    gp.quicksum(
                        lambdas[j] * float(columns[j]["load"][t])
                        for j in range(len(columns))
                    )
                    - load[t]
                    == 0,
                    name=f"link[{t}]",
                )
            )
        convexity = model.addConstr(
            gp.quicksum(lambdas[j] for j in range(len(columns))) == 1,
            name="convexity",
        )
        for t, rows in enumerate(
            market.system_delta_segments(_l_max(inst), 8)
        ):
            for slope, intercept in rows:
                model.addConstr(cost[t] >= slope * load[t] + intercept)
        for point in tangent_points:
            for t, (slope, intercept) in enumerate(
                market.system_delta_tangents_at(np.asarray(point))
            ):
                model.addConstr(cost[t] >= slope * load[t] + intercept)
        model.setObjective(
            gp.quicksum(
                lambdas[j] * float(columns[j]["ops_cost"])
                for j in range(len(columns))
            )
            + gp.quicksum(cost[t] for t in range(market.n_slots)),
            GRB.MINIMIZE,
        )
        start = time.time()
        model.optimize()
        wall = time.time() - start
        total_wall += wall
        status = _status_name(model.Status)
        solve_record = {
            "solve_id": f"{solve_id_prefix}-r{refinement}",
            "backend": "GRB",
            "gurobi_version": _gurobi_version(),
            "status": status,
            "obj": (
                float(model.ObjVal) if model.Status == GRB.OPTIMAL else None
            ),
            "bound": (
                float(model.ObjBound) if model.Status == GRB.OPTIMAL else None
            ),
            "n_vars": model.NumVars,
            "n_int": 0,
            "n_constrs": model.NumConstrs,
            "wall_s": wall,
            "threads": int(model.Params.Threads),
        }
        solves.append(solve_record)
        if model.Status != GRB.OPTIMAL:
            model.dispose()
            raise ExactnessLabError(f"clean node RMP not OPTIMAL: {status}")
        model_value = float(model.ObjVal)
        lambda_values = [float(lambdas[j].X) for j in range(len(columns))]
        load_values = np.asarray(
            [float(load[t].X) for t in range(market.n_slots)]
        )
        operations = sum(
            lambda_values[j] * float(columns[j]["ops_cost"])
            for j in range(len(columns))
        )
        upper = operations + market.system_delta_true(load_values)
        if upper - model_value <= pwl_tol:
            pi = [float(row.Pi) for row in link]
            sigma = float(convexity.Pi)
            model.dispose()
            return {
                "z_model": model_value,
                "upper": upper,
                "lambdas": lambda_values,
                "load": [float(value) for value in load_values],
                "pi": pi,
                "sigma": sigma,
                "tangent_points": tangent_points,
                "n_refinements": refinement,
                "master_wall_s": total_wall,
                "master_solves": solves,
            }
        tangent_points.append([float(value) for value in load_values])
        model.dispose()
    raise ExactnessLabError("clean node RMP tangent refinement did not converge")


def _node_identity(
    inst: Instance,
    market: AffineMarket,
    branch_constraints: list[dict],
    *,
    epsilon: float,
    pwl_tol: float,
    rc_tol: float,
    pricing_mip_gap: float,
    budget: int,
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "base_origin_main_sha": BASE_ORIGIN_MAIN_SHA,
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "branch_constraints": branch_constraints,
        "epsilon": float(epsilon),
        "pwl_tol": float(pwl_tol),
        "rc_tol": float(rc_tol),
        "pricing_mip_gap": float(pricing_mip_gap),
        "budget": int(budget),
        "solver": {"backend": "GRB", "gurobi_version": _gurobi_version()},
    }


def _finish_node_optimal(state: dict, rmp: dict, gap: float) -> dict:
    aggregate = aggregate_structural_values(
        state["columns"], rmp["lambdas"], state["arc_keys"]
    )
    state["done"] = True
    state["phase"] = "done"
    state["pending_rmp"] = None
    state["outcome"] = {
        "status": "certified",
        "certified": True,
        "lower_bound": state["lb_best"],
        "upper_bound": rmp["upper"],
        "gap": gap,
        "z_model": rmp["z_model"],
        "lambdas": rmp["lambdas"],
        "load": rmp["load"],
        "aggregate_structural": aggregate,
        "pricing_calls": len(state["pricing_calls"]),
        "n_columns": len(state["columns"]),
    }
    return state


def solve_node_lp(
    inst: Instance,
    market: AffineMarket,
    branch_constraints: Iterable[dict] | None,
    out_dir: str,
    *,
    node_id: str,
    epsilon: float = DEFAULT_EPSILON,
    pwl_tol: float = DEFAULT_PWL_TOL,
    rc_tol: float = DEFAULT_RC_TOL,
    pricing_mip_gap: float = DEFAULT_PRICING_MIP_GAP,
    budget: int = DEFAULT_NODE_BUDGET,
    max_new_pricing_calls: int | None = None,
) -> dict:
    """Certified CG relaxation of one externally managed branch node.

    ``max_new_pricing_calls`` is an invocation-only pause hook for resume
    tests.  It is not part of mathematical identity.
    """
    _validate_fixture(inst)
    if epsilon < pwl_tol:
        raise ExactnessLabError("node epsilon must cover the PWL tolerance")
    branch = canonical_branch_constraints(inst, branch_constraints)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "node.ckpt.json")
    arc_keys = [arc_key(arc) for arc in structural_arc_catalog(inst)]
    identity = _node_identity(
        inst,
        market,
        branch,
        epsilon=epsilon,
        pwl_tol=pwl_tol,
        rc_tol=rc_tol,
        pricing_mip_gap=pricing_mip_gap,
        budget=budget,
    )
    state = checkpoint.load(path)
    if state is None:
        state = {
            "identity": identity,
            "node_id": node_id,
            "arc_keys": arc_keys,
            "columns": [],
            "column_keys": [],
            "tangent_points": [],
            "pricing_calls": [],
            "master_events": [],
            "lb_best": None,
            "lower_history": [],
            "upper_history": [],
            "duplicate_retries": 0,
            "phase": "seed",
            "pending_rmp": None,
            "done": False,
            "outcome": None,
        }
    elif state.get("identity") != identity or state.get("node_id") != node_id:
        raise ExactnessLabError(
            f"node {node_id} checkpoint identity mismatch; refusing resume"
        )
    if state["done"]:
        return state

    new_calls = 0

    def commit():
        checkpoint.save(path, state)

    def pause_due() -> bool:
        return (
            max_new_pricing_calls is not None
            and new_calls >= max_new_pricing_calls
        )

    while not state["done"]:
        if state["phase"] == "seed":
            if pause_due():
                commit()
                return state
            event = _solve_full_fleet_oracle(
                inst,
                market.price(np.zeros(market.n_slots)),
                branch,
                call_id=f"{node_id}-seed",
                mip_gap=pricing_mip_gap,
            )
            new_calls += 1
            state["pricing_calls"].append(event)
            if event["solver"]["status"] == "INFEASIBLE":
                if not event.get("infeasibility_certified"):
                    raise ExactnessLabError(
                        f"node {node_id} infeasibility lacks a certificate"
                    )
                state["done"] = True
                state["phase"] = "done"
                state["outcome"] = {
                    "status": "infeasible",
                    "certified": True,
                    "pricing_calls": len(state["pricing_calls"]),
                    "certificate_call_id": event["call_id"],
                }
                commit()
                return state
            column = event["column"]
            state["columns"].append(column)
            state["column_keys"].append(column["column_key"])
            state["phase"] = "master"
            commit()
            continue

        if state["phase"] == "master":
            if len(state["pricing_calls"]) >= budget:
                state["done"] = True
                state["phase"] = "done"
                state["outcome"] = {
                    "status": "budget_exhausted",
                    "certified": False,
                    "pricing_calls": len(state["pricing_calls"]),
                }
                commit()
                return state
            iteration = len(state["master_events"])
            rmp = _solve_clean_rmp(
                inst,
                market,
                state["columns"],
                state["tangent_points"],
                pwl_tol=pwl_tol,
                solve_id_prefix=f"{node_id}-it{iteration}",
            )
            state["tangent_points"] = rmp["tangent_points"]
            if (
                state["upper_history"]
                and rmp["upper"]
                > state["upper_history"][-1] + pwl_tol + 1e-7
            ):
                raise ExactnessLabError(
                    f"node {node_id} upper bound increased from "
                    f"{state['upper_history'][-1]} to {rmp['upper']}"
                )
            state["master_events"].append(
                {
                    "iteration_id": f"{node_id}-it{iteration}",
                    "rmp": rmp,
                    **provenance(),
                }
            )
            state["pending_rmp"] = rmp
            state["phase"] = "pricing"
            commit()
            continue

        if state["phase"] != "pricing" or state["pending_rmp"] is None:
            raise ExactnessLabError(
                f"node {node_id} has corrupt phase {state['phase']!r}"
            )
        if pause_due():
            commit()
            return state
        rmp = state["pending_rmp"]
        prices = -np.asarray(rmp["pi"], dtype=float)
        call_index = len(state["pricing_calls"])
        event = _solve_full_fleet_oracle(
            inst,
            prices,
            branch,
            call_id=f"{node_id}-price-{call_index}",
            mip_gap=pricing_mip_gap,
        )
        new_calls += 1
        if event["solver"]["status"] == "INFEASIBLE":
            raise ExactnessLabError(
                f"nonempty node {node_id} became infeasible during pricing"
            )
        column = event["column"]
        pricing_upper = float(event["physical_objective"])
        pricing_lower = float(event["pricing_bound"])
        min_rc_upper = pricing_upper - rmp["sigma"]
        min_rc_lower = pricing_lower - rmp["sigma"]
        lower = rmp["z_model"] + min(0.0, min_rc_lower)
        state["lb_best"] = (
            lower
            if state["lb_best"] is None
            else max(float(state["lb_best"]), lower)
        )
        gap = rmp["upper"] - state["lb_best"]
        novel = column["column_key"] not in state["column_keys"]
        event.update(
            min_reduced_cost_upper=min_rc_upper,
            min_reduced_cost_lower=min_rc_lower,
            lower_bound=lower,
            lower_bound_best=state["lb_best"],
            upper_bound=rmp["upper"],
            certificate_gap=gap,
            column_novel=novel,
        )
        state["pricing_calls"].append(event)
        state["lower_history"].append(state["lb_best"])
        state["upper_history"].append(rmp["upper"])

        if state["lb_best"] > rmp["upper"] + pwl_tol + 1e-7:
            raise ExactnessLabError(
                f"node {node_id} lower bound exceeds physical upper bound"
            )
        if gap <= epsilon:
            _finish_node_optimal(state, rmp, gap)
            commit()
            return state

        improving = min_rc_upper < -rc_tol
        if novel:
            state["columns"].append(column)
            state["column_keys"].append(column["column_key"])
        if novel and improving:
            state["duplicate_retries"] = 0
        elif not novel and improving:
            state["duplicate_retries"] += 1
            if state["duplicate_retries"] >= MAX_DUPLICATE_RETRIES:
                raise ExactnessLabError(
                    f"node {node_id} repeatedly priced a duplicate with "
                    f"negative reduced cost {min_rc_upper}"
                )
            state["tangent_points"].append(list(map(float, rmp["load"])))
        elif min_rc_lower < -rc_tol:
            # An optimal Gurobi solve should supply an improving incumbent
            # whenever its bound is improving.  Refuse to infer exhaustion.
            raise ExactnessLabError(
                f"node {node_id} has ambiguous pricing interval "
                f"[{min_rc_lower}, {min_rc_upper}]"
            )
        else:
            # Pricing is exhausted; only tangent-model slack can remain.
            state["tangent_points"].append(list(map(float, rmp["load"])))

        state["pending_rmp"] = None
        state["phase"] = "master"
        commit()
    return state


def aggregate_structural_values(
    columns: list[dict], lambdas: list[float], arc_keys: list[str]
) -> dict[str, float]:
    if len(columns) != len(lambdas):
        raise ExactnessLabError("lambda vector does not match column pool")
    return {
        key: float(
            sum(
                float(weight)
                * int(column.get("structural_incidence", {}).get(key, 0))
                for column, weight in zip(columns, lambdas)
            )
        )
        for key in arc_keys
    }


# ---------------------------------------------------------------------------
# Structural leaf conversion
# ---------------------------------------------------------------------------
def _chains_from_integral_incidence(
    inst: Instance, incidence: dict[str, int]
) -> tuple[list[list[str]], list[list[str]]]:
    incoming = {trip.id: [] for trip in inst.trips}
    outgoing = {trip.id: [] for trip in inst.trips}
    starts = []
    for key, selected in incidence.items():
        if not selected:
            continue
        arc = arc_from_key(key)
        kind, tail, head = arc["kind"], arc.get("tail"), arc.get("head")
        if kind == "out":
            incoming[head].append(("out", None))
            starts.append(head)
        elif kind == "in":
            outgoing[tail].append(("in", None))
        else:
            outgoing[tail].append((kind, head))
            incoming[head].append((kind, tail))
    if any(len(rows) != 1 for rows in incoming.values()):
        raise ExactnessLabError("integral incidence lacks one predecessor per trip")
    if any(len(rows) != 1 for rows in outgoing.values()):
        raise ExactnessLabError("integral incidence lacks one successor per trip")
    sequences, kinds_by_sequence, visited = [], [], set()
    for start in sorted(starts):
        sequence, kinds = [], []
        current = start
        while True:
            if current in visited:
                raise ExactnessLabError("integral incidence contains a cycle")
            visited.add(current)
            sequence.append(current)
            kind, successor = outgoing[current][0]
            if kind == "in":
                break
            kinds.append(kind)
            current = successor
        sequences.append(sequence)
        kinds_by_sequence.append(kinds)
    if visited != set(incoming):
        raise ExactnessLabError("integral incidence has a path not rooted at pull-out")
    return sequences, kinds_by_sequence


def _operations_from_structure(
    inst: Instance, sequences: list[list[str]], arc_kinds: list[list[str]]
) -> tuple[float, float]:
    tripmap = {trip.id: trip for trip in inst.trips}
    deadhead = 0.0
    for sequence, kinds in zip(sequences, arc_kinds):
        trips = [tripmap[trip_id] for trip_id in sequence]
        deadhead += inst.dhm(inst.depot, trips[0].start_loc)
        deadhead += inst.dhm(trips[-1].end_loc, inst.depot)
        for first, second, kind in zip(trips, trips[1:], kinds):
            if kind == "dir":
                deadhead += inst.dhm(first.end_loc, second.start_loc)
            else:
                deadhead += inst.dhm(first.end_loc, inst.depot)
                deadhead += inst.dhm(inst.depot, second.start_loc)
    operations = (
        inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * deadhead
    )
    return operations, deadhead


def _solution_from_record(record: dict) -> Solution:
    return Solution(
        sequences=[list(sequence) for sequence in record["sequences"]],
        arc_kinds=[list(kinds) for kinds in record["arc_kinds"]],
        charges=[dict(charge) for charge in record["charges"]],
        load=[float(value) for value in record["load"]],
        fleet=int(record["fleet"]),
        dh_min_total=float(record["dh_min_total"]),
        energy_charged_kwh=float(sum(record["load"])),
        ops_cost=float(record["ops_cost"]),
        obj_true=(
            None
            if record.get("objective") is None
            else float(record["objective"])
        ),
        oracle_tier="independent/tiny-leaf-replay",
    )


def realize_structurally_integral_leaf(
    inst: Instance,
    market: AffineMarket,
    node_state: dict,
    *,
    integral_tol: float,
    support_tol: float,
) -> dict:
    """Construct the convexly averaged fixed-structure physical schedule."""
    outcome = node_state["outcome"]
    columns = node_state["columns"]
    lambdas = [max(0.0, float(value)) for value in outcome["lambdas"]]
    if len(columns) != len(lambdas):
        raise ExactnessLabError("leaf lambda vector does not match columns")
    total = sum(lambdas)
    if abs(total - 1.0) > 10 * integral_tol:
        raise ExactnessLabError(f"leaf lambdas sum to {total}, not one")
    aggregate = outcome["aggregate_structural"]
    target = {
        key: int(value >= 0.5)
        for key, value in aggregate.items()
        if value >= 1.0 - integral_tol
    }
    if any(
        integral_tol < value < 1.0 - integral_tol
        for value in aggregate.values()
    ):
        raise ExactnessLabError("attempted to realize a fractional node")

    retained = []
    dropped_weight = 0.0
    for index, (column, weight) in enumerate(zip(columns, lambdas)):
        if weight <= support_tol:
            dropped_weight += weight
            continue
        incidence = column_structural_incidence(inst, column)
        complete = {
            key: incidence.get(key, 0) for key in node_state["arc_keys"]
        }
        target_complete = {
            key: target.get(key, 0) for key in node_state["arc_keys"]
        }
        if complete != target_complete:
            raise ExactnessLabError(
                "positive-weight leaf columns do not share one structure"
            )
        retained.append((index, column, weight))
    retained_weight = sum(weight for _index, _column, weight in retained)
    if not retained or retained_weight < 1.0 - 10 * integral_tol:
        raise ExactnessLabError(
            f"leaf support lost material lambda weight {1.0 - retained_weight}"
        )

    incidence = {key: value for key, value in target.items() if value}
    sequences, arc_kinds = _chains_from_integral_incidence(inst, incidence)
    arc_vehicle = {}
    for vehicle, (sequence, kinds) in enumerate(zip(sequences, arc_kinds)):
        for tail, head, kind in zip(sequence, sequence[1:], kinds):
            if kind == "dep":
                arc_vehicle[tail, head] = vehicle

    charge_amounts: dict[tuple[str, str, int], float] = {}
    normalized_weights = []
    for index, column, weight in retained:
        normalized = weight / retained_weight
        normalized_weights.append(
            {
                "column_index": index,
                "column_key": column["column_key"],
                "lambda": normalized,
            }
        )
        for charge in column["charges"]:
            key = (
                charge["after_trip"],
                charge["before_trip"],
                int(charge["slot"]),
            )
            charge_amounts[key] = charge_amounts.get(key, 0.0) + (
                normalized * float(charge["kwh"])
            )
    charges = []
    load = [0.0] * inst.n_slots
    for (tail, head, slot), amount in sorted(charge_amounts.items()):
        if amount <= support_tol:
            continue
        if (tail, head) not in arc_vehicle:
            raise ExactnessLabError("averaged charge is not on a depot arc")
        charges.append(
            {
                "vehicle": arc_vehicle[tail, head],
                "after_trip": tail,
                "before_trip": head,
                "slot": slot,
                "kwh": amount,
            }
        )
        load[slot] += amount
    operations, deadhead = _operations_from_structure(
        inst, sequences, arc_kinds
    )
    objective = operations + market.system_delta_true(np.asarray(load))
    record = {
        "sequences": sequences,
        "arc_kinds": arc_kinds,
        "charges": charges,
        "load": load,
        "fleet": len(sequences),
        "dh_min_total": deadhead,
        "ops_cost": operations,
        "objective": objective,
        "structural_incidence": incidence,
        "source_weights": normalized_weights,
        "dropped_lambda_weight": dropped_weight,
        "replay_ok": False,
        "replay_violations": None,
    }
    solution = _solution_from_record(record)
    violations = validate_solution(inst, solution)
    record["replay_violations"] = violations
    record["replay_ok"] = not violations
    if violations:
        raise ExactnessLabError(
            f"independent integral-leaf realization failed: {violations}"
        )
    realized_incidence = structural_incidence(
        inst, solution.sequences, solution.arc_kinds
    )
    if realized_incidence != incidence:
        raise ExactnessLabError("realized leaf structure changed")
    if not restrictions_satisfied(
        inst, realized_incidence, node_state["identity"]["branch_constraints"]
    ):
        raise ExactnessLabError("realized leaf violates branch decisions")

    rmp_load = np.asarray(outcome["load"], dtype=float)
    load_residual = float(
        np.max(np.abs(np.asarray(load) - rmp_load))
    )
    objective_residual = abs(objective - float(outcome["upper_bound"]))
    residual_tol = max(
        1e-6,
        20.0
        * (integral_tol + support_tol)
        * max(1.0, float(np.max(np.abs(rmp_load)))),
    )
    record["master_load_max_abs_residual"] = load_residual
    record["master_objective_abs_residual"] = objective_residual
    record["conversion_tolerance"] = residual_tol
    if load_residual > residual_tol or objective_residual > residual_tol:
        raise ExactnessLabError(
            "independent leaf realization does not reproduce the master point: "
            f"load residual={load_residual}, objective residual={objective_residual}"
        )
    return record


def _fractional_arc(
    inst: Instance,
    aggregate: dict[str, float],
    branch_constraints: list[dict],
    integral_tol: float,
) -> tuple[dict, float] | None:
    fixed = {arc_key(item["arc"]) for item in branch_constraints}
    candidates = []
    for index, arc in enumerate(structural_arc_catalog(inst)):
        key = arc_key(arc)
        value = float(aggregate.get(key, 0.0))
        if key in fixed:
            expected = next(
                item["value"]
                for item in branch_constraints
                if arc_key(item["arc"]) == key
            )
            if abs(value - expected) > 10 * integral_tol:
                raise ExactnessLabError(
                    f"node aggregate violates fixed branch arc {arc!r}"
                )
            continue
        if integral_tol < value < 1.0 - integral_tol:
            candidates.append((-min(value, 1.0 - value), index, arc, value))
    if not candidates:
        return None
    _score, _index, arc, value = min(candidates)
    return arc, value


# ---------------------------------------------------------------------------
# External branch-and-price tree
# ---------------------------------------------------------------------------
def _validate_fixture(inst: Instance) -> None:
    if len(inst.trips) > MAX_TRIPS:
        raise ExactnessLabError(
            f"tiny laboratory supports n <= {MAX_TRIPS}, got {len(inst.trips)}"
        )
    seed = inst.meta.get("seed") if isinstance(inst.meta, dict) else None
    if seed in FORBIDDEN_FIXTURE_SEEDS:
        raise ExactnessLabError(
            f"synthetic fixture seed {seed} is outside the permitted lab set"
        )


def _tree_identity(
    inst: Instance,
    market: AffineMarket,
    *,
    epsilon: float,
    pwl_tol: float,
    rc_tol: float,
    integral_tol: float,
    support_tol: float,
    pricing_mip_gap: float,
    node_budget: int,
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "base_origin_main_sha": BASE_ORIGIN_MAIN_SHA,
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "n_trips": len(inst.trips),
        "fixture_seed": inst.meta.get("seed"),
        "epsilon": float(epsilon),
        "pwl_tol": float(pwl_tol),
        "rc_tol": float(rc_tol),
        "integral_tol": float(integral_tol),
        "support_tol": float(support_tol),
        "pricing_mip_gap": float(pricing_mip_gap),
        "node_budget": int(node_budget),
        "solver": {"backend": "GRB", "gurobi_version": _gurobi_version()},
    }


def _terminal_global_bound(state: dict) -> float | None:
    bounds = []
    for node_id in state["terminal_nodes"]:
        node = state["nodes"][node_id]
        if node["status"] in {"integral", "bound_pruned"}:
            bounds.append(float(node["lp_outcome"]["lower_bound"]))
    return min(bounds) if bounds else None


def _refresh_frontier(state: dict) -> None:
    """Persist the deterministic work queues rather than reconstructing them
    only in memory.  This makes the exact resume point directly auditable."""
    state["frontier"] = {
        "queued": sorted(
            node_id
            for node_id, node in state["nodes"].items()
            if node["status"] == "queued"
        ),
        "open_best_bound": [
            node_id
            for _bound, node_id in sorted(
                (
                    float(node["lp_outcome"]["lower_bound"]),
                    node_id,
                )
                for node_id, node in state["nodes"].items()
                if node["status"] == "open"
            )
        ],
    }


def solve_tree(
    inst: Instance,
    market: AffineMarket,
    out_dir: str,
    *,
    epsilon: float = DEFAULT_EPSILON,
    pwl_tol: float = DEFAULT_PWL_TOL,
    rc_tol: float = DEFAULT_RC_TOL,
    integral_tol: float = DEFAULT_INTEGRAL_TOL,
    support_tol: float = DEFAULT_SUPPORT_TOL,
    pricing_mip_gap: float = DEFAULT_PRICING_MIP_GAP,
    node_budget: int = DEFAULT_NODE_BUDGET,
    max_nodes: int = 1000,
    max_work_items: int | None = None,
) -> dict:
    """Run or resume the deterministic external branch-and-price tree."""
    _validate_fixture(inst)
    if epsilon < pwl_tol:
        raise ExactnessLabError("tree epsilon must cover the PWL tolerance")
    os.makedirs(out_dir, exist_ok=True)
    nodes_dir = os.path.join(out_dir, "nodes")
    os.makedirs(nodes_dir, exist_ok=True)
    path = os.path.join(out_dir, "tree.ckpt.json")
    identity = _tree_identity(
        inst,
        market,
        epsilon=epsilon,
        pwl_tol=pwl_tol,
        rc_tol=rc_tol,
        integral_tol=integral_tol,
        support_tol=support_tol,
        pricing_mip_gap=pricing_mip_gap,
        node_budget=node_budget,
    )
    state = checkpoint.load(path)
    if state is None:
        root_id = "n0000"
        state = {
            "identity": identity,
            "nodes": {
                root_id: {
                    "node_id": root_id,
                    "parent": None,
                    "depth": 0,
                    "branch_constraints": [],
                    "status": "queued",
                    "lp_checkpoint": f"nodes/{root_id}/node.ckpt.json",
                    "lp_outcome": None,
                    "branch": None,
                    "children": [],
                    "realization": None,
                }
            },
            "next_node_index": 1,
            "terminal_nodes": [],
            "branch_history": [],
            "incumbent": None,
            "incumbent_history": [],
            "work_history": [],
            "frontier": {"queued": [root_id], "open_best_bound": []},
            "done": False,
            "outcome": None,
            "created": provenance(),
        }
        checkpoint.save(path, state)
    elif state.get("identity") != identity:
        raise ExactnessLabError("tree checkpoint identity mismatch; refusing resume")
    if state["done"]:
        return state

    work = 0

    def commit():
        _refresh_frontier(state)
        checkpoint.save(path, state)

    def pause_due() -> bool:
        return max_work_items is not None and work >= max_work_items

    while not state["done"]:
        if pause_due():
            commit()
            return state

        queued = sorted(
            node_id
            for node_id, node in state["nodes"].items()
            if node["status"] == "queued"
        )
        if queued:
            node_id = queued[0]
            node = state["nodes"][node_id]
            node_state = solve_node_lp(
                inst,
                market,
                node["branch_constraints"],
                os.path.join(nodes_dir, node_id),
                node_id=node_id,
                epsilon=epsilon,
                pwl_tol=pwl_tol,
                rc_tol=rc_tol,
                pricing_mip_gap=pricing_mip_gap,
                budget=node_budget,
            )
            outcome = node_state["outcome"]
            node["lp_outcome"] = outcome
            if outcome["status"] == "infeasible":
                node["status"] = "infeasible"
                state["terminal_nodes"].append(node_id)
            elif outcome["status"] == "certified":
                node["status"] = "open"
            else:
                raise ExactnessLabError(
                    f"node {node_id} did not certify: {outcome['status']}"
                )
            state["work_history"].append(
                {
                    "kind": "node_lp",
                    "node_id": node_id,
                    "status": node["status"],
                    **provenance(),
                }
            )
            work += 1
            commit()
            continue

        open_nodes = [
            (float(node["lp_outcome"]["lower_bound"]), node_id)
            for node_id, node in state["nodes"].items()
            if node["status"] == "open"
        ]
        if open_nodes:
            _bound, node_id = min(open_nodes)
            node = state["nodes"][node_id]
            outcome = node["lp_outcome"]
            incumbent = state["incumbent"]
            if (
                incumbent is not None
                and float(outcome["lower_bound"])
                >= float(incumbent["objective"]) - epsilon
            ):
                node["status"] = "bound_pruned"
                state["terminal_nodes"].append(node_id)
                state["work_history"].append(
                    {
                        "kind": "bound_prune",
                        "node_id": node_id,
                        "lower_bound": outcome["lower_bound"],
                        "incumbent": incumbent["objective"],
                        **provenance(),
                    }
                )
                work += 1
                commit()
                continue

            candidate = _fractional_arc(
                inst,
                outcome["aggregate_structural"],
                node["branch_constraints"],
                integral_tol,
            )
            if candidate is None:
                node_state = checkpoint.load(
                    os.path.join(nodes_dir, node_id, "node.ckpt.json")
                )
                realization = realize_structurally_integral_leaf(
                    inst,
                    market,
                    node_state,
                    integral_tol=integral_tol,
                    support_tol=support_tol,
                )
                node["realization"] = realization
                node["status"] = "integral"
                state["terminal_nodes"].append(node_id)
                if (
                    incumbent is None
                    or realization["objective"]
                    < float(incumbent["objective"]) - 1e-9
                ):
                    state["incumbent"] = {
                        "node_id": node_id,
                        "objective": realization["objective"],
                        "realization": realization,
                    }
                    state["incumbent_history"].append(
                        {
                            "node_id": node_id,
                            "objective": realization["objective"],
                            **provenance(),
                        }
                    )
                state["work_history"].append(
                    {
                        "kind": "integral_leaf",
                        "node_id": node_id,
                        "objective": realization["objective"],
                        **provenance(),
                    }
                )
                work += 1
                commit()
                continue

            arc, value = candidate
            if len(state["nodes"]) + 2 > max_nodes:
                raise ExactnessLabError(
                    f"external tree exceeded max_nodes={max_nodes}"
                )
            children = []
            for branch_value in (0, 1):
                child_id = f"n{state['next_node_index']:04d}"
                state["next_node_index"] += 1
                child_constraints = canonical_branch_constraints(
                    inst,
                    node["branch_constraints"]
                    + [{"arc": arc, "value": branch_value}],
                )
                state["nodes"][child_id] = {
                    "node_id": child_id,
                    "parent": node_id,
                    "depth": node["depth"] + 1,
                    "branch_constraints": child_constraints,
                    "status": "queued",
                    "lp_checkpoint": f"nodes/{child_id}/node.ckpt.json",
                    "lp_outcome": None,
                    "branch": {
                        "arc": arc,
                        "value": branch_value,
                        "parent_fractional_value": value,
                    },
                    "children": [],
                    "realization": None,
                }
                children.append(child_id)
            node["status"] = "branched"
            node["children"] = children
            branch_record = {
                "node_id": node_id,
                "arc": arc,
                "fractional_value": value,
                "children": children,
                **provenance(),
            }
            state["branch_history"].append(branch_record)
            state["work_history"].append({"kind": "branch", **branch_record})
            work += 1
            commit()
            continue

        # No queued or open node remains: terminal regions form the partition.
        global_bound = _terminal_global_bound(state)
        incumbent = state["incumbent"]
        if incumbent is None:
            state["outcome"] = {
                "status": "infeasible",
                "certified": True,
                "global_bound": None,
                "incumbent_objective": None,
                "gap": None,
                "nodes": len(state["nodes"]),
                "branches": len(state["branch_history"]),
            }
        else:
            if global_bound is None:
                raise ExactnessLabError("feasible tree has no terminal lower bound")
            gap = float(incumbent["objective"]) - global_bound
            if gap < -epsilon:
                raise ExactnessLabError(
                    f"global lower bound exceeds incumbent by {-gap}"
                )
            state["outcome"] = {
                "status": "optimal",
                "certified": bool(gap <= epsilon),
                "global_bound": global_bound,
                "incumbent_objective": float(incumbent["objective"]),
                "gap": gap,
                "nodes": len(state["nodes"]),
                "branches": len(state["branch_history"]),
                "max_depth": max(
                    node["depth"] for node in state["nodes"].values()
                ),
                "pricing_calls": sum(
                    int((node.get("lp_outcome") or {}).get("pricing_calls", 0))
                    for node in state["nodes"].values()
                ),
            }
        state["done"] = True
        commit()
    return state


# ---------------------------------------------------------------------------
# Independent persisted-state audit
# ---------------------------------------------------------------------------
def audit_tree(inst: Instance, state: dict, out_dir: str) -> list[str]:
    """Replay every persisted column and integral realization without solving."""
    errors = []
    for node_id, node in sorted(state["nodes"].items()):
        node_path = os.path.join(out_dir, "nodes", node_id, "node.ckpt.json")
        node_state = checkpoint.load(node_path)
        if node_state is None:
            if node["status"] != "queued":
                errors.append(f"{node_id}: missing node checkpoint")
            continue
        branch = node["branch_constraints"]
        for call in node_state["pricing_calls"]:
            column = call.get("column")
            if column is None:
                if not (
                    call["solver"]["status"] == "INFEASIBLE"
                    and call.get("infeasibility_certified")
                ):
                    errors.append(f"{node_id}/{call['call_id']}: uncertified null column")
                continue
            solution = _solution_from_record(
                {
                    **column,
                    "objective": call.get("physical_objective"),
                    "dh_min_total": (
                        float(column["ops_cost"])
                        - inst.vehicle_fixed_cost * int(column["fleet"])
                    )
                    / inst.dh_cost_per_min
                    if inst.dh_cost_per_min
                    else 0.0,
                }
            )
            violations = validate_solution(inst, solution)
            if violations:
                errors.append(
                    f"{node_id}/{call['call_id']}: replay {violations}"
                )
            incidence = structural_incidence(
                inst, solution.sequences, solution.arc_kinds
            )
            if not restrictions_satisfied(inst, incidence, branch):
                errors.append(
                    f"{node_id}/{call['call_id']}: branch restriction violation"
                )
        realization = node.get("realization")
        if realization is not None:
            solution = _solution_from_record(realization)
            violations = validate_solution(inst, solution)
            if violations:
                errors.append(f"{node_id}/leaf: replay {violations}")
            incidence = structural_incidence(
                inst, solution.sequences, solution.arc_kinds
            )
            if not restrictions_satisfied(inst, incidence, branch):
                errors.append(f"{node_id}/leaf: branch restriction violation")
    return errors
