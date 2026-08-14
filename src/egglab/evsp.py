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
    stats: SolveStats | None = None
    oracle_tier: str = "exact-milp"

    def schedule_hash(self) -> str:
        canon = sorted(tuple(seq) for seq in self.sequences)
        return hashlib.sha256(json.dumps(canon).encode()).hexdigest()[:12]

    def load_hash(self) -> str:
        canon = [round(x, 2) for x in self.load]
        return hashlib.sha256(json.dumps(canon).encode()).hexdigest()[:12]


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
                                        "kwh": round(val(var), 6),
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

    load = [round(val(L[t]), 6) for t in range(inst.n_slots)]
    sol = Solution(
        sequences=sequences,
        arc_kinds=arc_kinds,
        charges=charges,
        load=load,
        fleet=len(sequences),
        dh_min_total=dh_min_total,
        energy_charged_kwh=round(sum(load), 6),
        ops_cost=inst.vehicle_fixed_cost * len(sequences)
        + inst.dh_cost_per_min * dh_min_total,
        obj_model=stats.obj,
        stats=stats,
    )
    sol.energy_cost_model = (stats.obj or 0.0) - sol.ops_cost
    return sol


# --------------------------------------------------------------------------
# replay validation (independent of the MILP)
# --------------------------------------------------------------------------
def validate_solution(inst: Instance, sol: Solution) -> list:
    """Replay every vehicle sequence and charging plan against the instance
    physics; returns a list of violation strings (empty = valid)."""
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
                        errs.append(f"v{vi}: direct chain {prev.id}->{tid} late")
                    soc -= inst.dhk(prev.end_loc, tr.start_loc)
                else:
                    arrive = prev.end_min + inst.dhm(prev.end_loc, D)
                    depart = tr.start_min - inst.dhm(D, tr.start_loc)
                    if depart < arrive:
                        errs.append(f"v{vi}: depot chain {prev.id}->{tid} infeasible")
                    soc -= inst.dhk(prev.end_loc, D)
                    if soc < inst.soc_min_kwh - 1e-6:
                        errs.append(f"v{vi}: SOC floor violated arriving depot")
                    for c in charge_by_arc.get((prev.id, tid), []):
                        lo, hi = c["slot"] * inst.slot_min, (c["slot"] + 1) * inst.slot_min
                        ov = min(hi, depart) - max(lo, arrive)
                        cap = inst.charge_power_kw * max(ov, 0) / 60.0
                        if c["kwh"] > cap + 1e-6:
                            errs.append(
                                f"v{vi}: charge {c['kwh']:.2f} kWh exceeds window cap "
                                f"{cap:.2f} in slot {c['slot']}"
                            )
                        soc += c["kwh"]
                    if soc > inst.battery_kwh + 1e-6:
                        errs.append(f"v{vi}: battery overfilled at depot")
                    soc -= inst.dhk(D, tr.start_loc)
            if soc < inst.soc_min_kwh - 1e-6:
                errs.append(f"v{vi}: SOC floor violated before {tid}")
            soc -= tr.energy_kwh
            if soc < inst.soc_min_kwh - 1e-6:
                errs.append(f"v{vi}: SOC floor violated after {tid}")
            prev = tr
        soc -= inst.dhk(prev.end_loc, D)
        if soc < inst.soc_end_kwh - 1e-6:
            errs.append(f"v{vi}: terminal SOC {soc:.2f} < {inst.soc_end_kwh}")
    return errs
