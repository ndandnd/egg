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
    return sol


def solve_strategic(inst: Instance, market: AffineMarket, n_seg: int = 16, **kw) -> Solution:
    segs = market.bill_segments(_l_max(inst), n_seg)
    sol = solve_evsp(inst, ("pwl", segs), **kw)
    sol.oracle_tier = f"exact-milp/strategic-pwl{n_seg}"
    return sol


def solve_dictator(inst: Instance, market: AffineMarket, n_seg: int = 16, **kw) -> Solution:
    segs = market.system_delta_segments(_l_max(inst), n_seg)
    sol = solve_evsp(inst, ("pwl", segs), **kw)
    sol.oracle_tier = f"exact-milp/dictator-pwl{n_seg}"
    return sol


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
