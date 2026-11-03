"""Check the reduced count layers against labeled assignments and battery traces."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from egglab.two_peak import ChargeWindow, TwoPeakDepot


def enumerated_loads(inst):
    """Grid-kWh enumeration for the integer lossless fixture, without count formulas."""
    result = {}
    for successors in product(range(-1, inst.n_afternoon), repeat=inst.n_morning):
        used = [b for b in successors if b >= 0]
        if len(set(used)) != len(used):
            continue
        if inst.allowed_pairs is not None and any(
                b >= 0 and (a, b) not in inst.allowed_pairs for a, b in enumerate(successors)):
            continue
        duties = [(int(inst.morning_kwh), int(inst.afternoon_kwh) if b >= 0 else 0)
                  for b in successors]
        duties += [(0, int(inst.afternoon_kwh)) for b in range(inst.n_afternoon) if b not in used]
        if inst.max_buses is not None and len(duties) > inst.max_buses:
            continue
        per_bus_limit = int(inst.early.plug_kw * inst.early.hours)
        for allocation in product(range(per_bus_limit + 1), repeat=len(duties)):
            if sum(allocation) > inst.early.grid_limit_kwh:
                continue
            terminal = []
            for (a, b), early in zip(duties, allocation):
                before_b = inst.usable_kwh - a + early
                if not b <= before_b <= inst.usable_kwh:
                    break
                refill = inst.usable_kwh - (before_b - b)
                if refill > inst.terminal.hours * inst.terminal.plug_kw:
                    break
                terminal.append(refill)
            else:
                if sum(terminal) <= inst.terminal.grid_limit_kwh:
                    result.setdefault(len(used), set()).add(sum(allocation))
    return result


class TestTwoPeak(unittest.TestCase):
    def setUp(self):
        self.depot = TwoPeakDepot(3, 2, 3, 3, 5, 1, ChargeWindow(1, 2, 3, 5),
                                 ChargeWindow(1, 3, 4), allowed_pairs=((0, 0), (0, 1), (1, 0)))

    def test_all_integer_loads_and_prices_match_labeled_enumeration(self):
        for inst in (self.depot, replace(self.depot, allowed_pairs=()),
                     replace(self.depot, allowed_pairs=None, max_buses=3),
                     replace(self.depot, terminal=ChargeWindow(1, 3, 1))):
            expected = enumerated_loads(inst)
            actual = {r.pairs: set(range(int(r.early_min_kwh), int(r.early_max_kwh) + 1))
                      for r in inst.layers()}
            self.assertEqual(actual, expected)
            for p1, p2 in ((-400, 30), (120, 120), (7000, 0)):
                costs = [((inst.n_morning + inst.n_afternoon - m) * inst.bus_fee_eur
                          + (p1 * e + p2 * (inst.total_grid_kwh - e)) / 1000, e, -m)
                         for m, loads in expected.items() for e in loads]
                plan = inst.respond((p1, p2))
                if costs:
                    self.assertEqual((plan.posted_cost_eur, plan.fleet_kwh[0], -plan.pairs), min(costs))
                else:
                    self.assertIsNone(plan)

    def test_fractional_soc_witness_at_midpoint_of_every_layer(self):
        inst = replace(self.depot, efficiency=Fraction(4, 5), terminal=ChargeWindow(2, 3, 3))
        self.assertEqual(len(inst.maximum_matching()), 2)
        self.assertGreater(len(inst.layers()), 1)
        for layer in inst.layers():
            e = (layer.early_min_kwh + layer.early_max_kwh) / 2
            rows = inst.service_witness(layer.pairs, e)
            self.assertEqual(len(rows), layer.buses)
            self.assertEqual(sorted(i for i, _, _, _ in rows if i is not None), [0, 1, 2])
            self.assertEqual(sorted(j for _, j, _, _ in rows if j is not None), [0, 1])
            self.assertEqual(sum(row[2] for row in rows), e)
            self.assertEqual(sum(row[3] for row in rows), inst.total_grid_kwh - e)
            self.assertLessEqual(e, inst.early.grid_limit_kwh)
            self.assertLessEqual(inst.total_grid_kwh - e, inst.terminal.grid_limit_kwh)
            for i, j, early, late in rows:
                if i is not None and j is not None:
                    self.assertIn((i, j), inst.allowed_pairs)
                self.assertTrue(0 <= early <= inst.early.hours * inst.early.plug_kw)
                self.assertTrue(0 <= late <= inst.terminal.hours * inst.terminal.plug_kw)
                soc = inst.usable_kwh - (inst.morning_kwh if i is not None else 0) + inst.efficiency * early
                self.assertLessEqual(soc, inst.usable_kwh)
                soc -= inst.afternoon_kwh if j is not None else 0
                self.assertGreaterEqual(soc, 0)
                self.assertEqual(soc + inst.efficiency * late, inst.usable_kwh)

    def test_individual_terminal_rate_excludes_pair_despite_spare_shared_plugs(self):
        inst = TwoPeakDepot(1, 1, 4, 4, 6, 5, ChargeWindow(1, 4, 2), ChargeWindow(1, 4, 4))
        self.assertIsNone(inst.respond((0, 0), fixed_pairs=1))
        self.assertEqual(inst.respond((0, 0), fixed_pairs=0).buses, 2)
        self.assertIsNone(replace(inst, max_buses=1).respond((0, 0)))

    def test_input_and_witness_guards(self):
        with self.assertRaises(ValueError):
            replace(self.depot, n_morning=2.5)
        with self.assertRaises(ValueError):
            replace(self.depot, allowed_pairs=((0, 3),))
        with self.assertRaises(ValueError):
            self.depot.service_witness(1, 10)
        with self.assertRaises(ValueError):
            ChargeWindow(0, 4, 5)
        self.assertIsNone(replace(self.depot, early=ChargeWindow(1, 0, 1)).respond((1, 1)))


if __name__ == "__main__":
    unittest.main()
