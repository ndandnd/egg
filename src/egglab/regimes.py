"""The four economic regimes over one EVSP oracle (handoff Section 8.2).

- uncontrolled : flat-price schedule + charge-on-arrival timing (policy)
- taker        : EVSP at posted prices (EVSP-DR limit)
- strategic    : minimize own bill sum p_t(U+L) L_t  (B9; convex PWL epigraph)
- dictator     : minimize true system cost delta      (convex PWL epigraph)

evaluate() reports every economic lens for any load vector so regimes are
always compared on identical accounting.
"""
from __future__ import annotations

import numpy as np

from .evsp import Solution, solve_evsp
from .instance import Instance
from .market import AffineMarket


def _l_max(inst: Instance) -> float:
    return inst.charge_power_kw * inst.slot_min / 60.0 * inst.max_vehicles


def solve_taker(inst: Instance, prices, **kw) -> Solution:
    sol = solve_evsp(inst, ("linear", np.asarray(prices, dtype=float)), **kw)
    sol.oracle_tier = "exact-milp/taker"
    sol.obj_true = sol.obj_model  # linear objective is exact
    return sol


def _solve_convex_adaptive(
    inst: Instance,
    seg0: list,
    tangents_at,
    true_energy_cost,
    label: str,
    tol_abs: float = 1e-2,
    max_rounds: int = 25,
    **kw,
) -> Solution:
    """Certified adaptive outer approximation for a convex separable energy
    objective (reviewer-specified): solve the tangent-relaxed MILP (its value
    is a LOWER bound on the true optimum), evaluate the true objective at the
    incumbent load (a feasible UPPER bound), add tangents at the incumbent,
    repeat until ub - lb <= tol_abs. Records lb/ub/gap/rounds; obj_true is
    the certified feasible value."""
    segs = [list(rows) for rows in seg0]
    best_sol, best_ub = None, float("inf")
    lb = -float("inf")
    rounds = 0
    total_wall = 0.0
    while rounds < max_rounds:
        rounds += 1
        sol = solve_evsp(inst, ("pwl", segs), **kw)
        total_wall += sol.stats.wall_s + sol.stats.lp_wall_s
        lb = sol.obj_model  # lower bound on true optimum
        L = np.asarray(sol.load, dtype=float)
        ub = sol.ops_cost + true_energy_cost(L)
        if ub < best_ub - 1e-12:
            best_ub, best_sol = ub, sol
        if best_ub - lb <= tol_abs:
            break
        for t, seg in enumerate(tangents_at(L)):
            segs[t].append(seg)
    sol = best_sol
    sol.obj_true = best_ub
    sol.oracle_tier = f"exact-milp/{label}-adaptive"
    sol.stats.extra.update(
        {
            "adaptive_rounds": rounds,
            "adaptive_lb": lb,
            "adaptive_ub": best_ub,
            "adaptive_gap_abs": best_ub - lb,
            "adaptive_tol_abs": tol_abs,
            "adaptive_converged": bool(best_ub - lb <= tol_abs),
            "adaptive_total_wall_s": total_wall,
        }
    )
    return sol


def solve_strategic(
    inst: Instance,
    market: AffineMarket,
    n_seg: int = 16,
    tol_abs: float = 1e-2,
    max_rounds: int = 25,
    **kw,
) -> Solution:
    return _solve_convex_adaptive(
        inst,
        market.bill_segments(_l_max(inst), n_seg),
        market.bill_tangents_at,
        market.bill_true,
        "strategic",
        tol_abs=tol_abs,
        max_rounds=max_rounds,
        **kw,
    )


def solve_dictator(
    inst: Instance,
    market: AffineMarket,
    n_seg: int = 16,
    tol_abs: float = 1e-2,
    max_rounds: int = 25,
    **kw,
) -> Solution:
    return _solve_convex_adaptive(
        inst,
        market.system_delta_segments(_l_max(inst), n_seg),
        market.system_delta_tangents_at,
        market.system_delta_true,
        "dictator",
        tol_abs=tol_abs,
        max_rounds=max_rounds,
        **kw,
    )


def solve_uncontrolled(inst: Instance, market: AffineMarket, **kw) -> Solution:
    """Policy baseline: schedule chosen against a flat price (price-oblivious
    operations), then every depot dwell charges as early as possible at full
    power ("charge on arrival"). Documented modeling choice, not an optimum."""
    flat = np.full(market.n_slots, float(np.mean(market.a)))
    sol = solve_taker(inst, flat, **kw)
    tripmap = {t.id: t for t in inst.trips}
    D = inst.depot
    new_load = np.zeros(inst.n_slots)
    new_charges = []
    by_arc = {}
    for c in sol.charges:
        key = (c["after_trip"], c["before_trip"], c["vehicle"])
        by_arc.setdefault(key, 0.0)
        by_arc[key] += c["kwh"]
    for (after, before, veh), total in by_arc.items():
        ta, tb = tripmap[after], tripmap[before]
        arrive = ta.end_min + inst.dhm(ta.end_loc, D)
        depart = tb.start_min - inst.dhm(D, tb.start_loc)
        remaining = total
        for t in range(inst.n_slots):
            lo, hi = t * inst.slot_min, (t + 1) * inst.slot_min
            ov = min(hi, depart) - max(lo, arrive)
            if ov <= 0 or remaining <= 1e-9:
                continue
            amt = min(remaining, inst.charge_power_kw * ov / 60.0)
            if amt > 1e-9:
                new_charges.append(
                    {
                        "vehicle": veh,
                        "after_trip": after,
                        "before_trip": before,
                        "slot": t,
                        "kwh": round(amt, 6),
                    }
                )
                new_load[t] += amt
                remaining -= amt
    sol.charges = new_charges
    sol.load = [round(x, 6) for x in new_load]
    sol.oracle_tier = "policy/uncontrolled-charge-on-arrival"
    return sol


def evaluate(inst: Instance, sol: Solution, market: AffineMarket) -> dict:
    """All economic lenses for a given solution (transfers kept separate from
    real costs, per the honest-accounting rules)."""
    L = np.asarray(sol.load, dtype=float)
    clearing = market.price(L)
    return {
        "ops_cost": sol.ops_cost,
        "energy_kwh": float(L.sum()),
        "bill": market.bill(L),
        "system_cost_delta": market.system_cost_delta(L),
        "total_private": sol.ops_cost + market.bill(L),
        "total_system": sol.ops_cost + market.system_cost_delta(L),
        "clearing_prices": [round(float(p), 6) for p in clearing],
        "fleet": sol.fleet,
        "dh_min_total": sol.dh_min_total,
    }
