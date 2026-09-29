"""Pure scope, admission, and accounting tests for the public DEV block."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import public_economic_sensitivity as public  # noqa: E402


class PublicEconomicSensitivityTests(unittest.TestCase):
    def test_eight_scoped_cases_markets_and_budgets(self):
        spec = public.design()
        self.assertEqual(len(public.cells()), 8)
        self.assertEqual(len({public.cases()[name].identity() for name, _ in public.cells()}), 8)
        self.assertEqual(len({public.market(name, kind).identity()
                              for name, kind in public.cells()}), 8)
        self.assertEqual([public.scenario(name)[1:] for name, _ in public.cells()],
                         [(fee, mult) for fee, mult in public.SCENARIOS for _ in public.DEPOTS])
        for name, kind in public.cells():
            depot, fee, mult = public.scenario(name)
            base = public.base_cases()[depot]
            changed = public.cases()[name]
            self.assertEqual(replace(changed, name=base.name,
                                     vehicle_cost=base.vehicle_cost), base)
            self.assertEqual(changed.vehicle_cost, fee)
            m = public.market(name, kind)
            self.assertEqual(m.a, (0.2,) * 30)
            self.assertEqual(m.b, (mult / 900,) * 30)
            self.assertEqual(spec["cases"][name]["case_identity"], changed.identity())
            self.assertEqual(spec["cases"][name]["market_identities"][kind], m.identity())
        self.assertEqual(spec["hard_child_seconds"], {"planner": 210,
                         "cold_hull": 210, "response": 90})
        self.assertEqual(spec["controller_cap_seconds"], 5400)
        self.assertEqual(spec["budgets"]["cold_hull"]["pricing_calls"], 16)
        self.assertEqual(spec["budgets"]["cold_hull"]["rational_bits"], 8192)
        self.assertEqual(spec["master_policy"], "numerical_qp_proposal")
        self.assertEqual(len(spec["analytical_floors"]), 8)
        with self.assertRaises(ValueError):
            public.scenario("public_depot15_f30_k1")
        with self.assertRaises(ValueError):
            public._attempt(ROOT / "result/economic_support_diagnostic/20260929-attempt1")

    def test_ideal_grid_scope_is_pinned_and_separate(self):
        original = public._read(public.ANALYTIC)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bounds.json"
            tampered = dict(original)
            tampered["analytical_sensitivity_only"] = [
                row for row in original["analytical_sensitivity_only"]
                if (row.get("case"), row.get("bus_cost"), row.get("curvature_multiplier"))
                != ("public_depot15", 40, 2)]
            path.write_text(json.dumps(tampered))
            with mock.patch.object(public, "ANALYTIC", path):
                public.analytical_floors.cache_clear()
                with self.assertRaisesRegex(ValueError, "Missing or duplicated"):
                    public.analytical_floors()
        public.analytical_floors.cache_clear()
        floors = public.analytical_floors()
        for name, kind in public.cells():
            self.assertEqual(floors[name]["modified_case_identity"],
                             public.cases()[name].identity())
            self.assertEqual(floors[name]["market_identity"],
                             public.market(name, kind).identity())
            self.assertIn("ideal", floors[name]["scope"])

    def test_independent_interval_arithmetic_and_gradient(self):
        self.assertEqual(public.combined_intervals(["90", "110"], ["100", "120"]),
                         {"D_interval_exact": ["100", "110"],
                          "CH_interval_exact": ["100", "110"],
                          "D_minus_CH_interval_exact": ["0", "10"]})
        self.assertEqual(public.combined_intervals(["110", "120"], ["90", "100"])
                         ["D_minus_CH_interval_exact"], ["10", "30"])
        with self.assertRaisesRegex(ValueError, "incompatible"):
            public.combined_intervals(["70", "80"], ["90", "100"])
        self.assertEqual(public.regret_interval("110", ["80", "100"]), ["10", "30"])
        with self.assertRaisesRegex(ValueError, "lower exceeds"):
            public.regret_interval("110", ["111", "120"])
        name, kind = public.cells()[0]
        m = public.market(name, kind)
        load = [0.] * len(m.a)
        load[0] = 9.
        self.assertEqual(public.gradient(m, load)[0],
                         float(public.Fraction(m.a[0]) +
                               public.Fraction(m.b[0]) * public.Fraction(9.)))

    def test_missing_late_or_stale_stages_do_not_promote(self):
        name, kind = public.cells()[0]
        analytic = public.analytical_floors()[name]
        with tempfile.TemporaryDirectory() as temp:
            response = public.folder(temp, name, kind, "response")
            response.mkdir(parents=True)
            (response / "ineligible.json").write_text("{}")
            planner = public.stage_row(temp, name, kind, "planner")
            hull = public.stage_row(temp, name, kind, "cold_hull")
            skipped = public.stage_row(temp, name, kind, "response")
            self.assertEqual(skipped["outcome"], "ineligible")
            combined = public.cell_summary(name, kind, planner, hull, skipped, analytic)
            self.assertIsNone(combined["D_minus_CH_interval_exact"])
            self.assertIsNone(combined["incumbent_own_price_regret_interval_exact"])
            self.assertIsNone(public.planner_admitted(temp, name, kind))
            pdir = public.folder(temp, name, kind, "planner")
            pdir.mkdir(parents=True)
            (pdir / "raw_result.json").write_text(json.dumps({"result": {
                "status": "certified", "case_identity": "stale", "lower": 1, "upper": 2}}))
            (pdir / "result.json").write_text(json.dumps({"case": name, "market": kind,
                "stage": "planner", "assessment": {"status": "certified", "bounds": ["1", "2"],
                "plan_replayed": True, "plan_hash": "stale", "replay": {"load": [0]*30,
                "ops_cost": 100}}}))
            late = {"returncode": 0, "on_time": False, "hard_timeout": False,
                    "elapsed_seconds": 211}
            (pdir / "receipt.json").write_text(json.dumps(late))
            self.assertEqual(public.stage_row(temp, name, kind, "planner")["outcome"], "late")
            self.assertIsNone(public.planner_admitted(temp, name, kind))
            (pdir / "receipt.json").write_text(json.dumps({**late, "on_time": True}))
            self.assertEqual(public.stage_row(temp, name, kind, "planner")["outcome"],
                             "partial_result")


if __name__ == "__main__":
    unittest.main()
