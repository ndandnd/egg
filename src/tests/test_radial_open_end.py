"""Check the passive-leaf formulation against direct complex circuit laws."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from egglab.radial_opf import price_depot_day, solve_radial


class TestPassiveOpenEnd(unittest.TestCase):
    def test_energized_leaf_against_complex_circuit(self):
        slack, tap = 1.025, 1.04
        z, y_from = .035+.04j, .004+.021j
        y_to, y_bus = .0001+.00021j, .00003-.00005j
        w = slack/tap
        v = w/(1 + z*(y_to + y_bus))
        series = (w - v)/z
        i_from, i_to = (series + y_from*w)/tap, -series + y_to*v
        s_from, s_to = slack*i_from.conjugate(), v*i_to.conjugate()
        case = dict(parent=[0], r=[z.real], x=[z.imag], p_mw=[0, 0], q_mvar=[0, 0],
                    open_end_leaves=[1], slack_vm_pu=slack, tap_ratio=tap,
                    g_from_pu=y_from.real, b_from_pu=y_from.imag,
                    g_to_pu=y_to.real, b_to_pu=y_to.imag, g_bus_pu=[0, y_bus.real],
                    b_bus_pu=[0, y_bus.imag], price=-15)
        got = solve_radial(**case)
        self.assertTrue(got["point_ac_residuals_pass"])
        self.assertEqual(got["formulation"], "passive_open_end_reduction")
        self.assertEqual(got["open_end_leaves"], [1])
        self.assertIsNone(got["dlmp"][1])
        self.assertIsNone(got["dlmp_q"][1])
        self.assertAlmostEqual(got["dlmp"][0], -15, places=7)
        for field, expected in (("current_sq_pu", abs(series)**2),
                                ("current_from_pu", abs(i_from)), ("current_to_pu", abs(i_to)),
                                ("p_send_mw", s_from.real), ("q_send_mvar", s_from.imag),
                                ("p_to_mw", s_to.real), ("q_to_mvar", s_to.imag)):
            self.assertAlmostEqual(got[field][0], expected, delta=1e-8)
        self.assertAlmostEqual(got["voltage_pu"][1], abs(v), delta=1e-8)
        self.assertAlmostEqual(got["loss_mw"], s_from.real, delta=1e-8)
        self.assertEqual(solve_radial(**case, imax_from_pu=.95*abs(i_from))["status"],
                         "infeasible")

    def test_only_zero_injection_uncontrolled_leaf_is_eligible(self):
        case = dict(parent=[0, 1], r=[.01, .02], x=[.02, .03], p_mw=[0, .2, 0],
                    q_mvar=[0, .04, 0], open_end_leaves=[2])
        for override in (dict(open_end_leaves=[0]), dict(open_end_leaves=[1]),
                         dict(open_end_leaves=[2, 2]), dict(open_end_leaves=[3]),
                         dict(p_mw=[0, .2, 1e-12]), dict(q_mvar=[0, .04, -1e-12]),
                         dict(backup=(2, .1, 50)), dict(linearized=True)):
            with self.subTest(override=override), self.assertRaises(ValueError):
                solve_radial(**(case | override))
        # A zero center cannot license finite-difference perturbations at an open end.
        with self.assertRaisesRegex(ValueError, "depot"):
            price_depot_day([0], [.01], [.02], [[0, 0]], [[0, 0]], 1, [0], [1], [50],
                            open_end_leaves=[1])


if __name__ == "__main__":
    unittest.main()
