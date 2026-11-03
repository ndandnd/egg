"""The EVSP MILP oracle.

Model (documented in src/README.md): vehicle-indexed connection network with
two arc kinds between compatible trips — direct chaining, and chaining via the
depot with price-responsive charging in hourly slots during the depot gap.
Vehicles start the day full; charging happens only at the depot (Phase-1
physics; opportunity/terminal charging and V2G are later extensions). All
solves are MILPs solved to (near-)proven optimality; the per-solve
SolveStats carry LP root value, dual bound, and gap, so every oracle call is
certified for the stated model ("exact-milp" tier).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

import mip

from .instance import Instance
from .solver import SolveStats, new_model, optimize


# --------------------------------------------------------------------------
# arc precomputation
# --------------------------------------------------------------------------
def direct_pairs(inst: Instance):
    out = []
    for i, ti in enumerate(inst.trips):
        for j, tj in enumerate(inst.trips):
            if i == j:
                continue
            if ti.end_min + inst.dhm(ti.end_loc, tj.start_loc) <= tj.start_min:
                out.append((i, j))
    return out


def depot_pairs(inst: Instance):
    """(i, j, window_start_min, window_end_min): j after i via depot; the
    window is the depot dwell available for charging."""
    D = inst.depot
    out = []
    for i, ti in enumerate(inst.trips):
        for j, tj in enumerate(inst.trips):
            if i == j:
                continue
            arrive = ti.end_min + inst.dhm(ti.end_loc, D)
            depart = tj.start_min - inst.dhm(D, tj.start_loc)
            if depart >= arrive:
                out.append((i, j, arrive, depart))
    return out


def slot_overlaps(inst: Instance, w0: int, w1: int):
    """[(slot, overlap_minutes)] of window [w0, w1] with hourly slots."""
    out = []
    sm = inst.slot_min
    for t in range(inst.n_slots):
        lo, hi = t * sm, (t + 1) * sm
        ov = min(hi, w1) - max(lo, w0)
        if ov > 0:
            out.append((t, ov))
    return out


# --------------------------------------------------------------------------
# solution container
# --------------------------------------------------------------------------
def _norm(x: float, ndigits: int = 6) -> float:
    """Round and normalize -0.0 to 0.0. HASH/PRESENTATION USE ONLY — never
    apply to values that feed replay validation or economics (Unicorn
    incident 2026-08-15: pre-replay rounding accumulated along vehicle
    chains and produced spurious `6.00 < 6.0` terminal-SOC failures)."""
    v = round(float(x), ndigits)
    return v + 0.0 if v != 0 else 0.0


# Absolute replay tolerance (kWh). Covers MILP solver feasibility residuals
# (Gurobi/CBC default primal feasibility ~1e-6 per constraint) accumulated
# over a vehicle chain, plus float arithmetic in the independent replay.
# It does NOT weaken any MILP constraint — the model is solved exactly as
# before; this tolerance only governs the ex-post replay audit.
REPLAY_TOL_KWH = 1e-4

# Replay policy version, stamped into every record:
#   1 (implicit, pre-PR#11): extraction rounded to 6 decimals, 1e-6 kWh audit
#     tolerance — produced the Unicorn spurious-failure incident.
#   2 (PR#11 onward): full-precision extraction, REPLAY_TOL_KWH audit
#     tolerance, diagnostic messages.
# The B2/A6 column-generation pipeline applies its own versioned physical-load
# reconstruction before storing columns. Keep this global replay policy stable
# so unrelated resumable Phase-1/boundary workflows cannot mix representations.
REPLAY_POLICY_VERSION = 2
LOAD_RECONSTRUCTION_POLICY_VERSION = 1


def _physical_load_from_charges(
    inst: Instance,
    charges: list,
    raw_load: list,
    stats: SolveStats | None,
) -> list[float]:
    """Reconstruct the physical slot load and audit the solver aggregate.

    ``L`` is a redundant aggregate variable in the MILP.  Solver feasibility
    residuals can make its extracted value slightly negative even though every
    underlying charging variable is nonnegative.  The schedule's physical
    load is therefore the per-slot sum of its recorded charge events.  The raw
    aggregate remains diagnostic evidence and must agree within the frozen
    replay tolerance; larger discrepancies fail loudly.
    """
    if len(raw_load) != inst.n_slots:
        raise RuntimeError(
            f"solver aggregate load has {len(raw_load)} slots; "
            f"expected {inst.n_slots}"
        )
    raw = []
    for t, value in enumerate(raw_load):
        value = float(value)
        if not math.isfinite(value):
            raise RuntimeError(
                f"solver aggregate load is nonfinite at slot {t}: {value!r}"
            )
        raw.append(value)

    physical = [0.0] * inst.n_slots
    for i, charge in enumerate(charges):
        try:
            slot = int(charge["slot"])
            amount = float(charge["kwh"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"malformed charge event {i}: {charge!r}") from exc
        if slot != charge["slot"] or not 0 <= slot < inst.n_slots:
            raise RuntimeError(f"charge event {i} has invalid slot {charge['slot']!r}")
        if not math.isfinite(amount) or amount < 0.0:
            raise RuntimeError(
                f"charge event {i} has invalid nonnegative kWh value {amount!r}"
            )
        physical[slot] += amount

    residuals = [raw[t] - physical[t] for t in range(inst.n_slots)]
    max_abs = max((abs(value) for value in residuals), default=0.0)
    if max_abs > REPLAY_TOL_KWH:
        t = max(range(inst.n_slots), key=lambda k: abs(residuals[k]))
        raise RuntimeError(
            "solver aggregate load disagrees with physical charge events: "
            f"slot={t} raw={raw[t]:.12g} physical={physical[t]:.12g} "
            f"residual={residuals[t]:.3e} tol={REPLAY_TOL_KWH:.1e}"
        )
    if stats is not None:
        max_slot = (max(range(inst.n_slots), key=lambda k: abs(residuals[k]))
                    if inst.n_slots else None)
        stats.extra["load_reconstruction"] = {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
            "max_abs_residual_kwh": max_abs,
            "max_abs_residual_slot": max_slot,
            "raw_min_kwh": min(raw, default=0.0),
            "physical_min_kwh": min(physical, default=0.0),
            "raw_load_kwh": raw,
            "residual_kwh": residuals,
        }
    return [float(value) + 0.0 for value in physical]


@dataclass
class Solution:
    sequences: list  # list of list of trip ids (one per used vehicle)
    arc_kinds: list  # list of list of 'dir'/'dep' between consecutive trips
    charges: list  # [{vehicle, after_trip, before_trip, slot, kwh}]
    load: list  # kWh per slot
    fleet: int = 0
    dh_min_total: float = 0.0
    energy_charged_kwh: float = 0.0
    ops_cost: float = 0.0
    energy_cost_model: float = 0.0
    obj_model: float | None = None
    obj_true: float | None = None  # exact objective recomputed from loads
    stats: SolveStats | None = None
    oracle_tier: str = "exact-milp"

    def schedule_hash(self) -> str:
        canon = sorted(tuple(seq) for seq in self.sequences)
        return hashlib.sha256(json.dumps(canon).encode()).hexdigest()[:12]

    def load_hash(self) -> str:
        canon = [_norm(x, 2) for x in self.load]
        return hashlib.sha256(json.dumps(canon).encode()).hexdigest()[:12]


def canonicalize_solution_load(inst: Instance, sol: Solution) -> Solution:
    """Apply the B2/A6 physical-load policy to one solved schedule in place.

    This is deliberately opt-in. Generic EVSP, Phase-1, and boundary callers
    retain their established raw-solver representation and resume semantics.
    """
    sol.load = _physical_load_from_charges(
        inst, sol.charges, list(sol.load), sol.stats)
    sol.energy_charged_kwh = float(sum(sol.load))
    return sol


# --------------------------------------------------------------------------
# model build + solve
# --------------------------------------------------------------------------
def solve_evsp(
    inst: Instance,
    energy_cost: tuple,
    max_mip_gap: float = 1e-6,
    time_limit_s: float | None = None,
) -> Solution:
    """energy_cost: ('linear', p) with p per-kWh prices per slot, or
    ('pwl', segments) with segments[t] = [(slope, intercept), ...] describing
    a convex cost of L_t as the max of tangent lines (epigraph)."""
    n = len(inst.trips)
    V = inst.max_vehicles
    D = inst.depot
    B = inst.battery_kwh
    M = 2.0 * B
    dirp = direct_pairs(inst)
    depp = depot_pairs(inst)

    m = new_model("evsp")
    u = [[m.add_var(var_type=mip.BINARY) for _ in range(n)] for _ in range(V)]
    o = [[m.add_var(var_type=mip.BINARY) for _ in range(n)] for _ in range(V)]
    z = [[m.add_var(var_type=mip.BINARY) for _ in range(n)] for _ in range(V)]
    used = [m.add_var(var_type=mip.BINARY) for _ in range(V)]
    xd = [{(i, j): m.add_var(var_type=mip.BINARY) for (i, j) in dirp} for _ in range(V)]
    xg = [
        {(i, j): m.add_var(var_type=mip.BINARY) for (i, j, _, _) in depp}
        for _ in range(V)
    ]
    # charging vars on depot arcs
    P = inst.charge_power_kw
    e = [dict() for _ in range(V)]
    arc_slots = {}
    for (i, j, w0, w1) in depp:
        ovs = slot_overlaps(inst, w0, w1)
        arc_slots[(i, j)] = ovs
        for v in range(V):
            e[v][(i, j)] = {
                t: m.add_var(lb=0.0, ub=P * ov / 60.0) for (t, ov) in ovs
            }
    sb = [
        [m.add_var(lb=inst.soc_min_kwh, ub=B) for _ in range(n)] for _ in range(V)
    ]
    sa = [
        [m.add_var(lb=inst.soc_min_kwh, ub=B) for _ in range(n)] for _ in range(V)
    ]
    L = [m.add_var(lb=0.0) for _ in range(inst.n_slots)]

    # coverage
    for i in range(n):
        m += mip.xsum(u[v][i] for v in range(V)) == 1
    # degree / flow per vehicle
    for v in range(V):
        for i in range(n):
            m += (
                u[v][i]
                == o[v][i]
                + mip.xsum(xd[v][(j, i)] for (j, i2) in dirp if i2 == i)
                + mip.xsum(xg[v][(j, i)] for (j, i2, _, _) in depp if i2 == i)
            )
            m += (
                u[v][i]
                == z[v][i]
                + mip.xsum(xd[v][(i, j)] for (i2, j) in dirp if i2 == i)
                + mip.xsum(xg[v][(i, j)] for (i2, j, _, _) in depp if i2 == i)
            )
        m += used[v] == mip.xsum(o[v][i] for i in range(n))
    # symmetry breaking
    for v in range(V - 1):
        m += used[v] >= used[v + 1]

    # SOC dynamics
    for v in range(V):
        for i, ti in enumerate(inst.trips):
            m += sa[v][i] == sb[v][i] - ti.energy_kwh
            # pull-out from full battery
            k0 = inst.soc0_kwh - inst.dhk(D, ti.start_loc)
            m += sb[v][i] <= k0 + M * (1 - o[v][i])
            m += sb[v][i] >= k0 - M * (1 - o[v][i])
            # pull-in terminal SOC
            m += sa[v][i] - inst.dhk(ti.end_loc, D) >= inst.soc_end_kwh - M * (
                1 - z[v][i]
            )
        for (i, j) in dirp:
            ti, tj = inst.trips[i], inst.trips[j]
            dk = inst.dhk(ti.end_loc, tj.start_loc)
            m += sb[v][j] <= sa[v][i] - dk + M * (1 - xd[v][(i, j)])
            m += sb[v][j] >= sa[v][i] - dk - M * (1 - xd[v][(i, j)])
        for (i, j, w0, w1) in depp:
            ti, tj = inst.trips[i], inst.trips[j]
            d1 = inst.dhk(ti.end_loc, D)
            d2 = inst.dhk(D, tj.start_loc)
            x = xg[v][(i, j)]
            ch = mip.xsum(e[v][(i, j)][t] for t in e[v][(i, j)])
            m += sb[v][j] <= sa[v][i] - d1 - d2 + ch + M * (1 - x)
            m += sb[v][j] >= sa[v][i] - d1 - d2 + ch - M * (1 - x)
            m += sa[v][i] - d1 + ch <= B + M * (1 - x)  # battery cap at depot
            m += sa[v][i] - d1 >= inst.soc_min_kwh - M * (1 - x)  # arrival floor
            m += ch <= B * x  # no charging on unused arcs

    # aggregate load
    for t in range(inst.n_slots):
        m += L[t] == mip.xsum(
            e[v][(i, j)][t]
            for v in range(V)
            for (i, j) in e[v]
            if t in e[v][(i, j)]
        )

    # operations cost
    dh_expr = (
        mip.xsum(
            o[v][i] * inst.dhm(D, inst.trips[i].start_loc)
            + z[v][i] * inst.dhm(inst.trips[i].end_loc, D)
            for v in range(V)
            for i in range(n)
        )
        + mip.xsum(
            xd[v][(i, j)] * inst.dhm(inst.trips[i].end_loc, inst.trips[j].start_loc)
            for v in range(V)
            for (i, j) in dirp
        )
        + mip.xsum(
            xg[v][(i, j)]
            * (
                inst.dhm(inst.trips[i].end_loc, D)
                + inst.dhm(D, inst.trips[j].start_loc)
            )
            for v in range(V)
            for (i, j, _, _) in depp
        )
    )
    ops = (
        inst.vehicle_fixed_cost * mip.xsum(used[v] for v in range(V))
        + inst.dh_cost_per_min * dh_expr
    )

    kind, payload = energy_cost
    if kind == "linear":
        p = payload
        energy_expr = mip.xsum(float(p[t]) * L[t] for t in range(inst.n_slots))
        m.objective = ops + energy_expr
    elif kind == "pwl":
        segments = payload
        cost = [m.add_var(lb=0.0) for _ in range(inst.n_slots)]
        for t in range(inst.n_slots):
            for (slope, intercept) in segments[t]:
                m += cost[t] >= slope * L[t] + intercept
        m.objective = ops + mip.xsum(cost)
    else:
        raise ValueError(f"unknown energy_cost kind {kind!r}")

    stats = optimize(m, max_mip_gap=max_mip_gap, time_limit_s=time_limit_s)
    if stats.obj is None:
        raise RuntimeError(f"EVSP solve failed: status={stats.status}")

    return _extract(inst, stats, u, o, z, xd, xg, e, L, dirp, depp)


def _extract(inst, stats, u, o, z, xd, xg, e, L, dirp, depp) -> Solution:
    n = len(inst.trips)
    V = inst.max_vehicles
    sequences, arc_kinds, charges = [], [], []
    dh_min_total = 0.0
    D = inst.depot

    def val(var):
        return var.x if var.x is not None else 0.0

    for v in range(V):
        start = [i for i in range(n) if val(o[v][i]) > 0.5]
        if not start:
            continue
        i = start[0]
        seq, kinds = [inst.trips[i].id], []
        dh_min_total += inst.dhm(D, inst.trips[i].start_loc)
        while True:
            nxt = None
            for (a, b) in dirp:
                if a == i and val(xd[v][(a, b)]) > 0.5:
                    nxt, kind = b, "dir"
                    dh_min_total += inst.dhm(
                        inst.trips[a].end_loc, inst.trips[b].start_loc
                    )
                    break
            if nxt is None:
                for (a, b, _, _) in depp:
                    if a == i and val(xg[v][(a, b)]) > 0.5:
                        nxt, kind = b, "dep"
                        dh_min_total += inst.dhm(inst.trips[a].end_loc, D) + inst.dhm(
                            D, inst.trips[b].start_loc
                        )
                        for t, var in e[v][(a, b)].items():
                            if val(var) > 1e-6:
                                charges.append(
                                    {
                                        "vehicle": len(sequences),
                                        "after_trip": inst.trips[a].id,
                                        "before_trip": inst.trips[b].id,
                                        "slot": t,
                                        "kwh": float(val(var)),  # full precision (replay)
                                    }
                                )
                        break
            if nxt is None:
                dh_min_total += inst.dhm(inst.trips[i].end_loc, D)  # pull-in
                break
            seq.append(inst.trips[nxt].id)
            kinds.append(kind)
            i = nxt
        sequences.append(seq)
        arc_kinds.append(kinds)

    load = [float(val(L[t])) for t in range(inst.n_slots)]  # full precision
    sol = Solution(
        sequences=sequences,
        arc_kinds=arc_kinds,
        charges=charges,
        load=load,
        fleet=len(sequences),
        dh_min_total=dh_min_total,
        energy_charged_kwh=float(sum(load)),
        ops_cost=inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * dh_min_total,
        obj_model=stats.obj,
        stats=stats,
    )
    sol.energy_cost_model = (stats.obj or 0.0) - sol.ops_cost
    return sol


# --------------------------------------------------------------------------
# fixed-sequence re-realization oracle (margin tests, re-pricing)
# --------------------------------------------------------------------------
def solve_fixed_sequences(
    inst: Instance,
    sequences: list,
    energy_cost: tuple,
    max_mip_gap: float = 1e-6,
    time_limit_s: float | None = None,
) -> Solution | None:
    """Re-optimize arc kinds (direct vs via-depot) and charging for a FIXED
    trip partition (the re-realization oracle: EVSP-DR's rerealize_routes
    analogue). Returns None if the partition is time-infeasible. Used by the
    Phase-2 margin test: 'is schedule B economically tied with A at A's
    prices?'."""
    D = inst.depot
    B = inst.battery_kwh
    M = 2.0 * B
    tripmap = {t.id: t for t in inst.trips}
    m = new_model("evsp-fixed")
    load_terms = [[] for _ in range(inst.n_slots)]
    total_dh_fixed = 0.0
    dh_var_terms = []
    all_e = []  # (chain_idx, pair_idx, i_id, j_id, {t: var})
    chain_soc_ok = True

    chains = []
    for ci, seq in enumerate(sequences):
        trips = [tripmap[tid] for tid in seq]
        total_dh_fixed += inst.dhm(D, trips[0].start_loc) + inst.dhm(
            trips[-1].end_loc, D
        )
        pairs = []
        for k in range(len(trips) - 1):
            ti, tj = trips[k], trips[k + 1]
            dir_ok = ti.end_min + inst.dhm(ti.end_loc, tj.start_loc) <= tj.start_min
            arrive = ti.end_min + inst.dhm(ti.end_loc, D)
            depart = tj.start_min - inst.dhm(D, tj.start_loc)
            dep_ok = depart >= arrive
            if not dir_ok and not dep_ok:
                return None  # partition time-infeasible
            y = None
            if dir_ok and dep_ok:
                y = m.add_var(var_type=mip.BINARY)  # 1 = via depot
            evars = {}
            if dep_ok:
                for (t, ov) in slot_overlaps(inst, arrive, depart):
                    evars[t] = m.add_var(lb=0.0, ub=inst.charge_power_kw * ov / 60.0)
                    load_terms[t].append(evars[t])
            pairs.append(
                {"i": ti, "j": tj, "dir_ok": dir_ok, "dep_ok": dep_ok, "y": y, "e": evars}
            )
            all_e.append((ci, k, ti.id, tj.id, evars))
        chains.append((trips, pairs))

    # SOC propagation per chain (exact; kind choice enters linearly)
    for trips, pairs in chains:
        soc = [None] * len(trips)  # soc before each trip (model vars)
        s0 = inst.soc0_kwh - inst.dhk(D, trips[0].start_loc)
        prev_after = None
        for k, tr in enumerate(trips):
            sb = m.add_var(lb=inst.soc_min_kwh, ub=B)
            if k == 0:
                m += sb == s0
            else:
                p = pairs[k - 1]
                ti = p["i"]
                dirk = inst.dhk(ti.end_loc, tr.start_loc)
                d1 = inst.dhk(ti.end_loc, D)
                d2 = inst.dhk(D, tr.start_loc)
                ch = mip.xsum(p["e"].values()) if p["e"] else 0.0
                if p["y"] is not None:  # both kinds possible
                    y = p["y"]
                    m += sb == prev_after - dirk * (1 - y) - (d1 + d2) * y + ch
                    if p["e"]:
                        m += mip.xsum(p["e"].values()) <= B * y
                    m += prev_after - d1 + ch <= B + M * (1 - y)
                    m += prev_after - d1 >= inst.soc_min_kwh - M * (1 - y)
                elif p["dep_ok"]:  # depot only
                    m += sb == prev_after - d1 - d2 + ch
                    m += prev_after - d1 + ch <= B
                    m += prev_after - d1 >= inst.soc_min_kwh
                else:  # direct only
                    m += sb == prev_after - dirk
            sa = m.add_var(lb=inst.soc_min_kwh, ub=B)
            m += sa == sb - tr.energy_kwh
            prev_after = sa
            soc[k] = sb
        m += prev_after - inst.dhk(trips[-1].end_loc, D) >= inst.soc_end_kwh

    # deadhead minutes (kind-dependent parts)
    for trips, pairs in chains:
        for p in pairs:
            ti, tj = p["i"], p["j"]
            dmin_dir = inst.dhm(ti.end_loc, tj.start_loc)
            dmin_dep = inst.dhm(ti.end_loc, D) + inst.dhm(D, tj.start_loc)
            if p["y"] is not None:
                dh_var_terms.append(dmin_dir * (1 - p["y"]) + dmin_dep * p["y"])
            else:
                total_dh_fixed += dmin_dep if p["dep_ok"] else dmin_dir

    L = [m.add_var(lb=0.0) for _ in range(inst.n_slots)]
    for t in range(inst.n_slots):
        m += L[t] == mip.xsum(load_terms[t]) if load_terms[t] else L[t] == 0

    ops = inst.vehicle_fixed_cost * len(sequences) + inst.dh_cost_per_min * (
        total_dh_fixed + mip.xsum(dh_var_terms) if dh_var_terms else total_dh_fixed
    )
    kind, payload = energy_cost
    if kind == "linear":
        m.objective = ops + mip.xsum(float(payload[t]) * L[t] for t in range(inst.n_slots))
    elif kind == "pwl":
        cost = [m.add_var(lb=0.0) for _ in range(inst.n_slots)]
        for t in range(inst.n_slots):
            for (slope, intercept) in payload[t]:
                m += cost[t] >= slope * L[t] + intercept
        m.objective = ops + mip.xsum(cost)
    else:
        raise ValueError(kind)

    stats = optimize(m, max_mip_gap=max_mip_gap, time_limit_s=time_limit_s)
    if stats.obj is None:
        return None  # SOC-infeasible partition

    def val(v):
        return v.x if v.x is not None else 0.0

    charges = []
    arc_kinds = []
    dh_total = total_dh_fixed if not dh_var_terms else None
    dh_running = total_dh_fixed
    for ci, (trips, pairs) in enumerate(chains):
        kinds = []
        for p in pairs:
            via = p["dep_ok"] and (p["y"] is None or val(p["y"]) > 0.5)
            kinds.append("dep" if via else "dir")
            ti, tj = p["i"], p["j"]
            if p["y"] is not None:
                dh_running += (
                    inst.dhm(ti.end_loc, D) + inst.dhm(D, tj.start_loc)
                    if via
                    else inst.dhm(ti.end_loc, tj.start_loc)
                )
            if via:
                for t, var in p["e"].items():
                    if val(var) > 1e-6:
                        charges.append(
                            {
                                "vehicle": ci,
                                "after_trip": ti.id,
                                "before_trip": tj.id,
                                "slot": t,
                                "kwh": float(val(var)),  # full precision (replay)
                            }
                        )
        arc_kinds.append(kinds)

    load = [float(val(L[t])) for t in range(inst.n_slots)]  # full precision
    sol = Solution(
        sequences=[list(s) for s in sequences],
        arc_kinds=arc_kinds,
        charges=charges,
        load=load,
        fleet=len(sequences),
        dh_min_total=dh_running,
        energy_charged_kwh=float(sum(load)),
        ops_cost=inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * dh_running,
        obj_model=stats.obj,
        stats=stats,
        oracle_tier="exact-milp/fixed-sequences",
    )
    sol.energy_cost_model = (stats.obj or 0.0) - sol.ops_cost
    return sol


# --------------------------------------------------------------------------
# replay validation (independent of the MILP)
# --------------------------------------------------------------------------
def _bound_err(
    label: str, actual: float, bound: float, sense: str, tol: float
) -> str:
    """Uniform diagnostic: actual value, required bound, shortfall/excess,
    and the active tolerance (reviewer/incident-specified format)."""
    gap = (bound - actual) if sense == ">=" else (actual - bound)
    word = "shortfall" if sense == ">=" else "excess"
    return (
        f"{label}: actual={actual:.9f} required{sense}{bound:.9f} "
        f"{word}={gap:.3e} tol={tol:.1e}"
    )


def validate_solution(
    inst: Instance, sol: Solution, tol_kwh: float = REPLAY_TOL_KWH
) -> list:
    """Replay every vehicle sequence and charging plan against the instance
    physics, independently of the MILP; returns a list of violation strings
    (empty = valid).

    tol_kwh (default REPLAY_TOL_KWH = 1e-4 kWh = 0.1 Wh) absorbs solver
    primal-feasibility residuals and float accumulation along a chain. It is
    an audit tolerance only; the MILP constraints are unchanged. Time checks
    are integer-minute exact and take no tolerance."""
    errs = []
    tripmap = {t.id: t for t in inst.trips}
    covered = [tid for seq in sol.sequences for tid in seq]
    if sorted(covered) != sorted(t.id for t in inst.trips):
        errs.append("coverage: trips not covered exactly once")
    D = inst.depot
    charge_by_arc = {}
    for c in sol.charges:
        charge_by_arc.setdefault((c["after_trip"], c["before_trip"]), []).append(c)

    for vi, (seq, kinds) in enumerate(zip(sol.sequences, sol.arc_kinds)):
        t0 = tripmap[seq[0]]
        soc = inst.soc0_kwh - inst.dhk(D, t0.start_loc)
        prev = None
        for k, tid in enumerate(seq):
            tr = tripmap[tid]
            if prev is not None:
                kind = kinds[k - 1]
                if kind == "dir":
                    ready = prev.end_min + inst.dhm(prev.end_loc, tr.start_loc)
                    if ready > tr.start_min:
                        errs.append(
                            f"v{vi}: direct chain {prev.id}->{tid} late: "
                            f"ready={ready}min required<={tr.start_min}min "
                            f"excess={ready - tr.start_min}min tol=0 (exact)"
                        )
                    soc -= inst.dhk(prev.end_loc, tr.start_loc)
                else:
                    arrive = prev.end_min + inst.dhm(prev.end_loc, D)
                    depart = tr.start_min - inst.dhm(D, tr.start_loc)
                    if depart < arrive:
                        errs.append(
                            f"v{vi}: depot chain {prev.id}->{tid} infeasible: "
                            f"arrive={arrive}min required<=depart={depart}min "
                            f"excess={arrive - depart}min tol=0 (exact)"
                        )
                    soc -= inst.dhk(prev.end_loc, D)
                    if soc < inst.soc_min_kwh - tol_kwh:
                        errs.append(_bound_err(
                            f"v{vi}: SOC floor arriving depot before {tid} (kWh)",
                            soc, inst.soc_min_kwh, ">=", tol_kwh))
                    for c in charge_by_arc.get((prev.id, tid), []):
                        lo, hi = c["slot"] * inst.slot_min, (c["slot"] + 1) * inst.slot_min
                        ov = min(hi, depart) - max(lo, arrive)
                        cap = inst.charge_power_kw * max(ov, 0) / 60.0
                        if c["kwh"] > cap + tol_kwh:
                            errs.append(_bound_err(
                                f"v{vi}: charge in slot {c['slot']} on "
                                f"{prev.id}->{tid} exceeds window cap (kWh)",
                                c["kwh"], cap, "<=", tol_kwh))
                        soc += c["kwh"]
                    if soc > inst.battery_kwh + tol_kwh:
                        errs.append(_bound_err(
                            f"v{vi}: battery overfilled at depot before {tid} (kWh)",
                            soc, inst.battery_kwh, "<=", tol_kwh))
                    soc -= inst.dhk(D, tr.start_loc)
            if soc < inst.soc_min_kwh - tol_kwh:
                errs.append(_bound_err(
                    f"v{vi}: SOC floor before {tid} (kWh)",
                    soc, inst.soc_min_kwh, ">=", tol_kwh))
            soc -= tr.energy_kwh
            if soc < inst.soc_min_kwh - tol_kwh:
                errs.append(_bound_err(
                    f"v{vi}: SOC floor after {tid} (kWh)",
                    soc, inst.soc_min_kwh, ">=", tol_kwh))
            prev = tr
        soc -= inst.dhk(prev.end_loc, D)
        if soc < inst.soc_end_kwh - tol_kwh:
            errs.append(_bound_err(
                f"v{vi}: terminal SOC (kWh)", soc, inst.soc_end_kwh, ">=", tol_kwh))
    return errs
