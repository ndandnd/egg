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

import time

import mip
import numpy as np

from .b2a2 import B2A2Error
from .evsp import slot_overlaps
from .instance import Instance
from .market import AffineMarket
from .solver import new_model, optimize

MAX_STRUCTURES = 2000
PWL_TOL = 1e-4


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
    D = inst.depot
    dh = 0.0
    for chain, ck in zip(part, kinds):
        dh += inst.dhm(D, chain[0].start_loc) + inst.dhm(chain[-1].end_loc, D)
        for (a, b), k in zip(zip(chain, chain[1:]), ck):
            if k == "dir":
                dh += inst.dhm(a.end_loc, b.start_loc)
            else:
                dh += inst.dhm(a.end_loc, D) + inst.dhm(D, b.start_loc)
    return inst.vehicle_fixed_cost * len(part) + inst.dh_cost_per_min * dh


# ---------------------------------------------------------------------------
# lambda-scaled charging polytope of one structure
# ---------------------------------------------------------------------------
def _add_structure_block(m, inst: Instance, struct, lam, load_terms):
    """Add A_s y_s <= b_s * lam constraints (all homogeneous); accumulate the
    structure's per-slot charging into load_terms."""
    D = inst.depot
    tripmap = {t.id: t for t in inst.trips}
    B = inst.battery_kwh
    P = inst.charge_power_kw
    for seq, ck in zip(struct["sequences"], struct["kinds"]):
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
