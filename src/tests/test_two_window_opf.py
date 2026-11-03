"""Tiny engineering fixtures for the joint network master, unrelated to study days."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from egglab.two_window_opf import TwoWindowOPF, cone_screen


class TestTwoWindowOPF(unittest.TestCase):
    def test_fractional_window_and_joint_hull(self):
        engine = TwoWindowOPF(dict(parent=[0], r=[0], x=[0]), 1, [[0,0]]*3,
                              [[0,0]]*3, [.25,.5,.5], [20,70,90], 100, window_ids=[0,1,1])
        fixed = engine.fixed(50.)
        self.assertTrue(fixed["physical_pass"], fixed)
        self.assertAlmostEqual(fixed["grid_cost"], 5.)
        self.assertAlmostEqual(fixed["depot_price_per_mwh"][1], 80.)
        self.assertAlmostEqual(fixed["periods"][0]["depot_mw"], .2)
        hull = engine.optimize(0,100,[(0,0),(.1,-6)])
        self.assertTrue(hull["physical_pass"], hull)
        self.assertAlmostEqual(hull["early_kwh"], 60., places=5)
        self.assertAlmostEqual(hull["objective"], 4.4)
        if hull["native_bound"] is not None:
            self.assertAlmostEqual(hull["native_bound"], 4.4, places=6)
        engine.set_market([[0,.1]]*3,[[0,0]]*3,[100,10,30])
        self.assertAlmostEqual(engine.optimize(10,90)["early_kwh"], 10., places=5)
        self.assertAlmostEqual(engine.fixed_loads([50.,51.])["depot_price_per_mwh"][0],100.)

    def test_phasor_recovery_and_paid_backup(self):
        # Ideal tapped source and lossy feeder to a fixed load. Charge above
        # the binding import cap must come from the specified depot generator.
        z, i, v0 = .02+.04j, .15-.05j, 1.02
        v = v0-z*i
        s = v*i.conjugate()
        p_from = (v0*i.conjugate()).real
        n = dict(parent=[0,1],r=[0,z.real],x=[0,z.imag],slack_vm_pu=v0,
                 root_import_cap_mw=p_from)
        engine=TwoWindowOPF(n,2,[[0,0,s.real]]*2,[[0,0,s.imag]]*2,[1,1],[30,35],200.,
                            backup=(2,1.,120.))
        got=engine.fixed(100.)
        self.assertTrue(got["physical_pass"], got)
        for part in got["periods"]:
            self.assertAlmostEqual(part["current_sq_pu"][1],abs(i)**2,places=6)
            self.assertAlmostEqual(part["backup_mw"],.1,places=6)
            self.assertAlmostEqual(part["voltage_pu"][2],abs(v),places=6)
            self.assertAlmostEqual(part["dlmp"][2],120.,places=4)

    def test_physical_unit_tolerances(self):
        # Same physical observation on two distinct common MVA bases.
        for base in (1.,10.):
            self.assertEqual(cone_screen([1.],[0.],[1.],[1.000014/base**2],base)["cone_failed_edges"],[])
            self.assertEqual(cone_screen([1.],[0.],[1.],[1.0001/base**2],base)["cone_failed_edges"],[0])


if __name__=="__main__":
    unittest.main()
