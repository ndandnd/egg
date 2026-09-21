"""Exact, solver-independent examples; none is an EVSP embedding or run result."""
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction as Q
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab.coordination_certificates import CostBounds, Premises, coordination_certificate


PREMISES = Premises(True, True, True, physical_minimum_attained=True)


def cost(value):
    return CostBounds(value, value, "synthetic_currency")


def dot(x, y):
    return sum(a * b for a, b in zip(x, y))


def energy(load):
    # a=(1,1), b=(1,1), U=(0,0): currency, using kWh per slot.
    return sum(load) + dot(load, load) / 2


def price(load):
    return tuple(1 + value for value in load)


class CoordinationExamples(unittest.TestCase):
    def test_two_slot_integer_example_and_supplier_accounting(self):
        # Exactly two abstract allowed schedules, both with zero intrinsic cost.
        loads = ((Q(2), Q(0)), (Q(0), Q(2)))
        z_d = min(energy(load) for load in loads)
        mean = tuple((a + b) / 2 for a, b in zip(*loads))
        z_ch = energy(mean)
        # Along the complete convex hull L=(2t,2(1-t)),
        # F(L)=3+4(t-1/2)^2, so 3 is a global lower bound attained at t=1/2.
        for t in (Q(0), Q(1, 7), Q(1, 2), Q(4, 5), Q(1)):
            self.assertEqual(energy((2*t, 2*(1-t))), 3 + 4*(t-Q(1, 2))**2)
        self.assertEqual((z_d, z_ch), (4, 3))
        certificate = coordination_certificate(cost(z_d), cost(z_ch), premises=PREMISES)
        self.assertEqual(certificate.gap, (1, 1))
        self.assertTrue(certificate.excludes_exact_equilibrium)
        for load in loads:
            own = price(load)
            regret = dot(own, load) - min(dot(own, other) for other in loads)
            self.assertEqual(regret, 4)
            self.assertGreaterEqual(regret, certificate.regret_lower)
        # At common CH price p=(2,2), the fleet is indifferent: its LOC is zero.
        # F*(p)=sum(max(0,p_t-1)^2/2)=1; supply carries the entire system gap.
        ch_price = price(mean)
        conjugate = sum(max(Q(0), p-1)**2 / 2 for p in ch_price)
        fleet_loc = dot(ch_price, loads[0]) - min(dot(ch_price, x) for x in loads)
        supply_loc = energy(loads[0]) - dot(ch_price, loads[0]) + conjugate
        self.assertEqual((fleet_loc, supply_loc), (0, 1))
        self.assertEqual(fleet_loc + supply_loc, z_d - z_ch)
        # Randomizing across days incurs F before averaging, so no gain here.
        self.assertEqual(sum(energy(x) for x in loads) / 2, z_d)
        self.assertGreater(z_d, energy(mean))

    def test_zero_gap_every_planner_optimizer_is_supported(self):
        # Affine F, equal total energy: both physical choices and every mixture
        # cost 2; at gradient (1,1) both are best responses.
        loads = ((Q(2), Q(0)), (Q(0), Q(2)))
        values = [sum(load) for load in loads]
        self.assertEqual(values, [2, 2])
        certificate = coordination_certificate(cost(2), cost(2), premises=PREMISES)
        self.assertTrue(certificate.establishes_exact_equilibrium)
        self.assertFalse(certificate.excludes_exact_equilibrium)
        for load in loads:
            self.assertEqual(dot((1, 1), load), min(values))

    def test_nonattainment_is_not_zero_gap_existence(self):
        # S=[0,1]\{1/2}, c=0, F(x)=(x-1/2)^2: both infima are zero,
        # and conv(S)=[0,1] is compact, but physical minimum is not attained.
        # For x<1/2 the own-price linear minimizer is 1; for x>1/2 it is 0.
        # No feasible x equals its best response. The sequence checks the
        # excluded-point construction, not a claim of enumerating infinite S.
        for n in (3, 10, 100, 1000):
            for x in (Q(1, 2)-Q(1, n), Q(1, 2)+Q(1, n)):
                p = 2*(x-Q(1, 2))
                best = Q(1) if p < 0 else Q(0)
                self.assertGreater(p*x - p*best, 0)
                self.assertEqual((x-Q(1, 2))**2, Q(1, n*n))
        certificate = coordination_certificate(
            cost(0), cost(0), premises=replace(PREMISES, physical_minimum_attained=False))
        self.assertFalse(certificate.establishes_exact_equilibrium)
        self.assertFalse(certificate.excludes_exact_equilibrium)

    def test_approximate_price_uses_cost_units_and_strict_exclusion(self):
        p = replace(PREMISES, price_error_at_same_physical_load=True,
                    global_load_diameter_bound=True)
        # Two-slot example has D_1=4 kWh. A cost gap of 1 excludes
        # epsilon=.1 and eta=.2 currency/kWh (.1+.2*4=.9 currency).
        args = dict(premises=p, epsilon_cost="0.1", load_diameter_kwh="4")
        cert = coordination_certificate(cost(4), cost(3), price_error_per_kwh="0.2", **args)
        self.assertEqual(cert.approximate_regret_ceiling, Q(9, 10))
        self.assertTrue(cert.excludes_approximate_equilibrium)
        boundary = coordination_certificate(cost(4), cost(3), price_error_per_kwh="0.225", **args)
        self.assertEqual(boundary.approximate_regret_ceiling, 1)
        self.assertFalse(boundary.excludes_approximate_equilibrium)
        # At physical (2,0), posted p=(2,2) is a zero-regret response but
        # eta=1 from own p=(3,1); gap=1 therefore cannot exclude it.
        admitted = coordination_certificate(cost(4), cost(3), premises=p,
                                            price_error_per_kwh=1, load_diameter_kwh=4)
        self.assertFalse(admitted.excludes_approximate_equilibrium)

    def test_rounding_allowances_can_remove_apparent_positive_gap(self):
        cert = coordination_certificate(
            CostBounds("10.001", "10.002", "SEK", "0.001"),
            CostBounds("9.999", "10", "SEK", "0.002"), premises=PREMISES)
        self.assertEqual(cert.raw_gap, (Q(-2, 1000), Q(6, 1000)))
        self.assertEqual(cert.gap, (0, Q(6, 1000)))
        self.assertFalse(cert.excludes_exact_equilibrium)
        self.assertFalse(cert.establishes_exact_equilibrium)

    def test_bound_directions_and_large_exact_cancellation(self):
        cert = coordination_certificate(CostBounds(10, 12, "SEK"),
                                        CostBounds(8, 9, "SEK"), premises=PREMISES)
        self.assertEqual(cert.raw_gap, (1, 4))
        base = 10**100
        large = coordination_certificate(cost(base + Q(1, 3)), cost(base), premises=PREMISES)
        self.assertEqual(large.gap, (Q(1, 3), Q(1, 3)))

    def test_invalid_inputs_and_unestablished_premises(self):
        for bad in (1.0, True, "NaN", Decimal("Infinity"), "1/0"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                CostBounds(bad, 2, "SEK")
        for bounds in ((2, 1, "SEK", 0), (1, 2, "", 0), (1, 2, "SEK", -1)):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                CostBounds(*bounds)
        for field in ("common_complete_schedule_model", "convex_differentiable_system_cost",
                      "certified_bounds_include_all_errors"):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "premises"):
                coordination_certificate(cost(4), cost(3), premises=replace(PREMISES, **{field: False}))
        with self.assertRaises(ValueError):
            Premises(1, True, True)
        with self.assertRaisesRegex(ValueError, "negative upper"):
            coordination_certificate(cost(2), cost(3), premises=PREMISES)
        with self.assertRaisesRegex(ValueError, "monetary units"):
            coordination_certificate(cost(4), CostBounds(3, 3, "USD"), premises=PREMISES)
        for flags in ({}, {"price_error_at_same_physical_load": True},
                      {"global_load_diameter_bound": True}):
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, "same-load"):
                coordination_certificate(cost(4), cost(3), premises=replace(PREMISES, **flags),
                                         price_error_per_kwh=1, load_diameter_kwh=4)
        for name in ("epsilon_cost", "price_error_per_kwh", "load_diameter_kwh"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                coordination_certificate(cost(4), cost(3), premises=PREMISES, **{name: -1})


if __name__ == "__main__":
    unittest.main()
