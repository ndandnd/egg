"""Exact lossless two-bus special case, with slot energy measured in kWh.

There is one unlimited, zero-impedance line, a 1 p.u. voltage slack, a
unity-power-factor load at the depot and an unconstrained signed source.
All base and fleet energy is downstream. The source is paid in the input
currency; converting between kWh and MWh does not convert currencies.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class IdealDispatch:
    source_mw: np.ndarray
    line_mw: np.ndarray
    squared_current_pu: np.ndarray
    source_cost: np.ndarray
    dlmp_per_kwh: np.ndarray
    dlmp_per_mwh: np.ndarray


def solve_ideal_feeder(a_per_kwh, b_per_kwh2, base_kwh, fleet_kwh, slot_hours=1.0):
    """Solve each slot independently. A batch of fleet trajectories is allowed.

    Bus balances force source and line real power to equal total depot MW.
    Both squared voltages equal one. With zero reactive power and 1 MVA
    base, the physical squared current equals line MW squared. Eliminate
    the redundant cone variable before differentiating the source value.
    """
    a, b, base = (np.asarray(v, dtype=float) for v in (a_per_kwh, b_per_kwh2, base_kwh))
    fleet = np.asarray(fleet_kwh, dtype=float)
    if a.ndim != 1 or not a.size or b.shape != a.shape or base.shape != a.shape:
        raise ValueError("source coefficients and base energy need matching slot vectors")
    if fleet.ndim < 1 or fleet.shape[-1] != a.size:
        raise ValueError("fleet energy has the wrong slot dimension")
    if not np.isfinite(slot_hours) or slot_hours <= 0 or np.any(b < 0):
        raise ValueError("slot hours must be positive and supply slopes nonnegative")
    if not all(np.isfinite(v).all() for v in (a, b, base, fleet)):
        raise ValueError("nonfinite energy or coefficient")

    energy = base + fleet
    source_mw = energy / (1000.0 * slot_hours)
    # Integral of the marginal source offer from zero to signed source energy.
    cost = a * energy + 0.5 * b * energy**2
    depot_price = a + b * energy
    return IdealDispatch(source_mw, source_mw, source_mw**2, cost,
                         depot_price, 1000.0 * depot_price)
