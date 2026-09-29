"""Pure guards for the six-cell cold development screen; no optimization."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import cold_baseline_viability as viability  # noqa: E402


class ColdBaselineViabilityTests(unittest.TestCase):
    def test_six_unique_pinned_development_cells_and_common_controls(self):
        plan = viability.design()
        self.assertEqual(len(plan["order"]), 6)
        self.assertEqual({(row["case"], row["market"]) for row in plan["order"]},
                         {(name, kind) for name in viability.CASES for kind in viability.KINDS})
        self.assertEqual([(row["case"], row["market"]) for row in plan["order"]], [
            (viability.CASES[0], "source0"), (viability.CASES[0], "target"),
            (viability.CASES[1], "target"), (viability.CASES[1], "source0"),
            (viability.CASES[2], "source0"), (viability.CASES[2], "target")])
        self.assertEqual(set(plan["cases"]), set(viability.CASES))
        self.assertTrue(all(row["base_group"] == "native_scale_dev_s1006"
                            for row in plan["cases"].values()))
        for name in viability.CASES:
            self.assertEqual(plan["cases"][name]["market_identities"]["source0"],
                             viability.retrieval.market(name, "source0").identity())
            self.assertEqual(plan["cases"][name]["market_identities"]["target"],
                             viability.retrieval.market(name, "target").identity())
        cfg = plan["budget"]
        self.assertEqual((cfg["pricing_calls"], cfg["rational_bits"],
                          cfg["master_calls"], cfg["pool_cap"]), (16, 8192, 64, 64))
        self.assertEqual((cfg["wall_seconds"], cfg["phase_seconds"],
                          plan["hard_child_seconds"]), (180, 160, 210))
        self.assertEqual((cfg["backend"], cfg["threads"],
                          plan["pricing_reserve_seconds"]), ("GRB", 1, 10.0))
        self.assertEqual((plan["arm"], plan["master_policy"], plan["bound_cache_policy"]),
                         ("cold", "native_lp", "none"))
        self.assertFalse(plan["independent_test_data"])

    def test_case_identity_and_old_attempt_rejected(self):
        real_make = viability.scaling.make_case
        def altered(seed, size):
            return replace(real_make(seed, size), vehicle_cost=101.0)
        with mock.patch.object(viability.scaling, "make_case", side_effect=altered):
            with self.assertRaisesRegex(ValueError, "differs from reviewed"):
                viability.cases()
        with self.assertRaises(ValueError):
            viability._attempt(ROOT / "result/retrieval_comparison/20260928-attempt1")
        with self.assertRaises(ValueError):
            viability.market("public_depot15", "target")

    def test_late_failed_and_incomplete_rows_never_promote_bounds(self):
        name, kind = viability.CASES[0], "source0"
        with tempfile.TemporaryDirectory() as temporary:
            dest = viability.folder(temporary, name, kind)
            dest.mkdir(parents=True)
            (dest / "raw_result.json").write_text(json.dumps({"result": {
                "status": "certified", "lower": 1.0, "upper": 2.0,
                "counts": {"pricing_requests": 5, "master_calls": 4},
                "lower_certificate": {"lower_exact": "1"},
                "mixture": {"objective_exact": "2"}}}))
            assessed = {"case": name, "market": kind, "assessment": {
                "status": "certified", "complete_evidence": True, "bounds": ["1", "2"]}}
            (dest / "result.json").write_text(json.dumps(assessed))
            for receipt in ({"returncode": 2, "on_time": False, "hard_timeout": False,
                             "elapsed_seconds": 3},
                            {"returncode": 0, "on_time": False, "hard_timeout": False,
                             "elapsed_seconds": 211},
                            {"returncode": 0, "on_time": 1, "hard_timeout": False,
                             "elapsed_seconds": 3}):
                row = viability.result_row(temporary, name, kind, receipt)
                self.assertFalse(row["complete_evidence"])
                self.assertIsNone(row["lower_exact"])
            good = {"returncode": 0, "on_time": True, "hard_timeout": False,
                    "elapsed_seconds": 3}
            checked = viability.result_row(temporary, name, kind, good)
            self.assertTrue(checked["complete_evidence"])
            self.assertEqual(Fraction(checked["gap_exact"]), 1)
            assessed["assessment"].update(complete_evidence=False, bounds=None)
            (dest / "result.json").write_text(json.dumps(assessed))
            incomplete = viability.result_row(temporary, name, kind, good)
            self.assertEqual(incomplete["outcome"], "incomplete_evidence")
            self.assertIsNone(incomplete["lower_exact"])
            assessed["assessment"].update(status="unreviewed_status",
                                          complete_evidence=True, bounds=["1", "2"])
            (dest / "result.json").write_text(json.dumps(assessed))
            unknown = viability.result_row(temporary, name, kind, good)
            self.assertEqual(unknown["outcome"], "incomplete_evidence")
            self.assertIsNone(unknown["lower_exact"])

    def test_postmortem_accounts_for_every_cell(self):
        with tempfile.TemporaryDirectory() as temporary:
            viability.reconcile_partial(temporary)
            saved = json.loads((Path(temporary) / "postmortem_summary.json").read_text())
            self.assertEqual(saved["accounted_cells"], 6)
            self.assertEqual(len(saved["rows"]), 6)
            self.assertEqual({(row["case"], row["market"]) for row in saved["rows"]},
                             set(viability.cells()))
            self.assertTrue(all(row["outcome"] == "unstarted" for row in saved["rows"]))


if __name__ == "__main__":
    unittest.main()
