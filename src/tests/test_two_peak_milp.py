"""Test two common charging windows against independent bus-indexed MILPs.

Every feasible subset of buses that can be plugged in together receives a
continuous duration. This models preemption and the site limit without using
count layers, aggregate energy intervals, or discretized time steps.
"""
from dataclasses import replace
from itertools import combinations
from pathlib import Path
import sys
import unittest
import warnings

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab.two_peak import ChargeWindow, TwoPeakDepot


def bus_milp(depot, prices, *, fixed_pairs=None, early_target=None):
    costs, upper, integer = [], [], []
    constraints, lb, ub = [], [], []

    def var(limit, cost=0, binary=False):
        idx = len(costs)
        costs.append(float(cost))
        upper.append(float(limit))
        integer.append(int(binary))
        return idx

    def row(terms, low, high):
        constraints.append(terms)
        lb.append(float(low))
        ub.append(float(high))

    n_a, n_b = depot.n_morning, depot.n_afternoon
    bus = range(min(n_a + n_b, depot.max_buses if depot.max_buses is not None else n_a + n_b))
    used = [var(1, depot.bus_fee_eur, binary=True) for _ in bus]
    a = [[var(1, binary=True) for _ in range(n_a)] for _ in bus]
    b = [[var(1, binary=True) for _ in range(n_b)] for _ in bus]
    for batch, size in ((a, n_a), (b, n_b)):
        for j in range(size):
            row([(batch[i][j], 1) for i in bus], 1, 1)
    for i in bus:
        for batch in (a[i], b[i]):
            row([(j, 1) for j in batch] + [(used[i], -1)], -np.inf, 0)
        row([(used[i], 1)] + [(j, -1) for j in a[i] + b[i]], -np.inf, 0)
        if depot.allowed_pairs is not None:
            for j, k in ((j, k) for j in range(n_a) for k in range(n_b)):
                if (j, k) not in depot.allowed_pairs:
                    row([(a[i][j], 1), (b[i][k], 1)], -np.inf, 1)
    if fixed_pairs is not None:
        count = n_a + n_b - fixed_pairs
        row([(idx, 1) for idx in used], count, count)

    grid = []
    for window, price in zip((depot.early, depot.terminal), prices):
        energy = [var(np.inf, float(price) / 1000) for _ in bus]
        grid.append(energy)
        times, delivered = [], [[] for _ in bus]
        for count in range(1, min(len(bus), window.plugs) + 1):
            for plugged in combinations(bus, count):
                duration = var(window.hours)
                times.append(duration)
                portions = []
                for i in plugged:
                    portion = var(np.inf)
                    delivered[i].append(portion)
                    portions.append(portion)
                    row([(portion, 1), (duration, -window.plug_kw)], -np.inf, 0)
                if window.site_kw is not None:
                    row([(idx, 1) for idx in portions] + [(duration, -window.site_kw)], -np.inf, 0)
        row([(idx, 1) for idx in times], 0, window.hours)
        for i in bus:
            row([(energy[i], 1)] + [(idx, -1) for idx in delivered[i]], 0, 0)

    cap, eta = depot.usable_kwh, depot.efficiency
    for i in bus:
        # Battery states after the morning drive, early charge and afternoon drive.
        # A bus starts and must end full iff used. Unused buses start/end empty.
        after_a, before_b, after_b = [var(cap) for _ in range(3)]
        row([(after_a, 1), (used[i], -cap)] + [(j, depot.morning_kwh) for j in a[i]], 0, 0)
        row([(before_b, 1), (after_a, -1), (grid[0][i], -eta)], 0, 0)
        row([(after_b, 1), (before_b, -1)] + [(j, depot.afternoon_kwh) for j in b[i]], 0, 0)
        row([(after_b, 1), (grid[1][i], eta), (used[i], -cap)], 0, 0)
    if early_target is not None:
        row([(idx, 1) for idx in grid[0]], early_target, early_target)
    matrix = np.zeros((len(constraints), len(costs)))
    for i, terms in enumerate(constraints):
        for j, coefficient in terms:
            matrix[i, j] += float(coefficient)
    # SciPy 1.13 passes the native threads option through to HiGHS.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected:.*threads.*", category=RuntimeWarning)
        return milp(costs, integrality=integer, bounds=Bounds(0, upper),
                    constraints=LinearConstraint(matrix, lb, ub),
                    options={"threads": 1, "mip_rel_gap": 0.0, "time_limit": 5.0})


class BusIndexedCrossCheck(unittest.TestCase):
    def compare(self, inst, prices, *, expected_early=None, expected_pairs=None, fixed_pairs=None):
        plan = inst.respond(prices, fixed_pairs=fixed_pairs)
        native = bus_milp(inst, prices, fixed_pairs=fixed_pairs)
        self.assertEqual(native.status, 0, native.message)
        self.assertAlmostEqual(native.fun, native.mip_dual_bound, places=7)
        self.assertIsNotNone(plan)
        self.assertAlmostEqual(float(plan.posted_cost_eur), native.fun, places=7)
        self.assertEqual(plan.fleet_kwh[0], expected_early)
        self.assertEqual(plan.pairs, expected_pairs)
        # An equal scalar objective need not imply the chosen physical point is
        # present: demand the same fleet count and early energy in the MILP.
        fixed = bus_milp(inst, prices, fixed_pairs=plan.pairs, early_target=float(plan.fleet_kwh[0]))
        self.assertEqual(fixed.status, 0, fixed.message)
        self.assertAlmostEqual(fixed.fun, native.fun, places=7)

    def infeasible(self, inst):
        self.assertIsNone(inst.respond((0, 0)))
        native = bus_milp(inst, (0, 0))
        self.assertEqual(native.status, 2, native.message)

    def test_exact_switch_and_price_signs(self):
        inst = TwoPeakDepot(1, 1, 70, 70, 100, 4, ChargeWindow(1, 1, 70), ChargeWindow(2, 2, 100))
        for prices, pairs, early in (((-50, 50), 1, 70), ((250, 50), 0, 0), ((50, 50), 1, 40)):
            with self.subTest(prices=prices):
                self.compare(inst, prices, expected_early=early, expected_pairs=pairs)
        # The second bus costs EUR 4, exactly the premium for 40 kWh at +100 EUR/MWh.
        for fixed, selected, early in ((None, 0, 0), (0, 0, 0), (1, 1, 40)):
            with self.subTest(fixed=fixed):
                self.compare(inst, (150, 50), expected_early=early, expected_pairs=selected, fixed_pairs=fixed)

    def test_lossy_sparse_shared_depot(self):
        inst = TwoPeakDepot(3, 2, 60, 70, 100, 3, ChargeWindow("0.75", 2, 75, site_kw=120),
                            ChargeWindow("2.5", 2, 70, site_kw=126), efficiency="0.8",
                            allowed_pairs=((0, 0), (0, 1), (1, 0)), max_buses=3)
        self.compare(inst, (-10, 110), expected_early=90, expected_pairs=2)
        self.compare(inst, (125, 25), expected_early=85, expected_pairs=2)
        self.infeasible(replace(inst, early=ChargeWindow("0.75", 2, 75, site_kw=100)))

    def test_physical_infeasibility(self):
        full = ChargeWindow(2, 2, 100)
        # Two plugs do not double the charging rate of one bus.
        self.infeasible(TwoPeakDepot(1, 1, 70, 70, 100, 3, ChargeWindow(1, 2, 39), full, max_buses=1))
        # Both possible pairings require the same afternoon trip.
        self.infeasible(TwoPeakDepot(2, 2, 30, 30, 100, 3, full, full,
                                     allowed_pairs=((0, 0), (1, 0)), max_buses=2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
