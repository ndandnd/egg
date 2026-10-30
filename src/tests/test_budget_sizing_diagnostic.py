"""Pure design/accounting tests; no native optimizer or cluster interaction."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import budget_sizing_diagnostic as sizing  # noqa: E402


class BudgetSizingTests(unittest.TestCase):
    def test_factorial_and_common_controls(self):
        design = sizing.design()
        rows = design["cells"]
        self.assertEqual(len(rows), 8)
        self.assertEqual({(row["state"], row["pricing_calls"], row["rational_bits"])
                          for row in rows}, {(s, c, b) for s in (0, 1)
                                              for c in (4, 16) for b in (4096, 8192)})
        self.assertEqual(design["case_identity"], sizing.base.CASE_IDS[sizing.CASE])
        for row in rows:
            self.assertEqual(row["name"], sizing.cell_name(row["pricing_calls"], row["rational_bits"]))
            self.assertEqual(row["hard_child_seconds"], 90)
            cfg = row["budget"]
            self.assertEqual((cfg["pricing_calls"], cfg["rational_bits"]),
                             (row["pricing_calls"], row["rational_bits"]))
            self.assertEqual((cfg["master_calls"], cfg["pool_cap"]), (64, 64))
            self.assertEqual((cfg["wall_seconds"], cfg["phase_seconds"]), (60, 45))
            self.assertEqual((cfg["backend"], cfg["threads"]), ("GRB", 1))
        common = []
        for row in rows:
            cfg = deepcopy(row["budget"])
            cfg.pop("pricing_calls")
            cfg.pop("rational_bits")
            common.append(cfg)
        self.assertTrue(all(item == common[0] for item in common))

    def test_failed_late_and_boolean_receipts_do_not_promote(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dest = sizing.folder(root, 1, 4, 4096)
            dest.mkdir(parents=True)
            (dest / "raw_result.json").write_text(json.dumps({"result": {
                "status": "certified", "lower": 1.0, "upper": 2.0,
                "counts": {"pricing_requests": 3, "master_calls": 3},
                "lower_certificate": {"lower_exact": "1"},
                "mixture": {"objective_exact": "2"}}}))
            (dest / "result.json").write_text(json.dumps({"state": 1, "pricing_calls": 4,
                "rational_bits": 4096, "assessment": {"status": "certified",
                                                    "complete_evidence": True, "bounds": ["1", "2"]}}))
            for receipt in ({"returncode": 2, "hard_timeout": False, "on_time": False,
                             "elapsed_seconds": 3},
                            {"returncode": 0, "hard_timeout": False, "on_time": False,
                             "elapsed_seconds": 91},
                            {"returncode": 0, "hard_timeout": False, "on_time": 1,
                             "elapsed_seconds": 3}):
                row = sizing.result_row(root, 1, 4, 4096, receipt)
                self.assertFalse(row["complete_evidence"])
                self.assertIsNone(row["lower_exact"])
            good = {"returncode": 0, "hard_timeout": False, "on_time": True,
                    "elapsed_seconds": 3}
            row = sizing.result_row(root, 1, 4, 4096, good)
            self.assertTrue(row["complete_evidence"])
            self.assertEqual(Fraction(row["gap_exact"]), 1)

            (dest / "result.json").write_text(json.dumps({"state": 1, "pricing_calls": 4,
                "rational_bits": 4096, "assessment": {"status": "certified",
                                                    "complete_evidence": False, "bounds": None}}))
            incomplete = sizing.result_row(root, 1, 4, 4096, good)
            self.assertFalse(incomplete["complete_evidence"])
            self.assertEqual(incomplete["outcome"], "incomplete_evidence")
            self.assertIsNone(incomplete["lower_exact"])

    def test_all_cell_accounting_and_runtime_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sizing.reconcile_partial(root)
            saved = json.loads((root / "postmortem_summary.json").read_text())
            self.assertEqual(saved["accounted_cells"], 8)
            self.assertEqual(len(saved["rows"]), 8)
            self.assertTrue(all(row["outcome"] == "unstarted" for row in saved["rows"]))
        software = {"python": "3.11", "solver": "same"}
        self.assertTrue(sizing.runtime_compatible(software, dict(software)))
        self.assertFalse(sizing.runtime_compatible(software, {**software, "solver": "different"}))


if __name__ == "__main__":
    unittest.main()
