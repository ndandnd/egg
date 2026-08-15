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
def _norm(x: float, ndigits: int = 6) -> float:
    """Round and normalize -0.0 to 0.0 (hash-stability)."""
    v = round(float(x), ndigits)
    return v + 0.0 if v != 0 else 0.0


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

    load = [_norm(val(L[t])) for t in range(inst.n_slots)]
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
                                "kwh": _norm(val(var)),
                            }
                        )
        arc_kinds.append(kinds)

    load = [_norm(val(L[t])) for t in range(inst.n_slots)]
    sol = Solution(
        sequences=[list(s) for s in sequences],
        arc_kinds=arc_kinds,
        charges=charges,
        load=load,
        fleet=len(sequences),
        dh_min_total=dh_running,
        energy_charged_kwh=_norm(sum(load)),
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
