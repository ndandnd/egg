"""Pure scope and accounting checks for the six-cell QP diagnosis."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import cold_baseline_viability as baseline  # noqa: E402
from experiments import qp_baseline_diagnostic as qp  # noqa: E402


class QPBaselineTests(unittest.TestCase):
    def test_same_six_cells_and_only_declared_master_change(self):
        before, after = baseline.design(), qp.design()
        self.assertEqual(before["cases"], after["cases"])
        self.assertEqual(before["order"], after["order"])
        self.assertEqual(before["budget"], after["budget"])
        self.assertEqual(before["hard_child_seconds"], after["hard_child_seconds"])
        self.assertEqual(before["pricing_reserve_seconds"], after["pricing_reserve_seconds"])
        self.assertEqual((after["arm"], after["bound_cache_policy"]), ("cold", "none"))
        self.assertEqual((after["master_policy"], after["qp_denominator"],
                          after["qp_maxiter"]), ("numerical_qp_proposal", 10**9, 500))
        self.assertEqual(len(qp.cells()), 6)
        self.assertEqual(qp.CONTROLLER_CAP_SECONDS, 1500)
        with self.assertRaises(ValueError):
            qp._attempt(ROOT / "result/cold_baseline_viability/20260929-attempt1")

    def test_portable_runtime_adds_qp_dependencies(self):
        with mock.patch.object(qp.sizing, "software_runtime", return_value={"core": "pinned"}), \
                mock.patch.object(qp.importlib.metadata, "version",
                                  side_effect={"numpy": "2.0", "scipy": "1.0"}.get):
            self.assertEqual(qp.software_runtime(),
                             {"core": "pinned", "numpy": "2.0", "scipy": "1.0"})
        self.assertEqual(len(qp.source_hashes()), len(qp.SOURCE_FILES))

    def test_qp_policy_and_incomplete_rows_fail_closed(self):
        name, kind = qp.CASES[0], "source0"
        with tempfile.TemporaryDirectory() as temporary:
            dest = qp.folder(temporary, name, kind)
            dest.mkdir(parents=True)
            raw = {"status": "certified", "lower": 1.0, "upper": 2.0,
                   "master_policy": "numerical_qp_proposal",
                   "qp_denominator": 10**9, "qp_maxiter": 500,
                   "pricing_reserve_seconds": 10.0,
                   "counts": {"pricing_requests": 2, "master_calls": 1,
                              "qp_proposal_calls": 1, "qp_non_success": 0,
                              "qp_proposal_wall_s": .5, "qp_replay_wall_s": .1},
                   "lower_certificate": {"lower_exact": "1"},
                   "mixture": {"objective_exact": "2"}}
            (dest / "raw_result.json").write_text(json.dumps({"result": raw}))
            assessed = {"case": name, "market": kind, "assessment": {
                "status": "certified", "complete_evidence": True, "bounds": ["1", "2"]}}
            (dest / "result.json").write_text(json.dumps(assessed))
            (dest / "events.jsonl").write_text(json.dumps({"event": "qp_proposal_result"}) + "\n")
            good = {"returncode": 0, "on_time": True, "hard_timeout": False,
                    "elapsed_seconds": 3}
            row = qp.result_row(temporary, name, kind, good)
            self.assertTrue(row["complete_evidence"])
            self.assertEqual(Fraction(row["gap_exact"]), 1)
            self.assertEqual(row["qp_proposal_calls"], 1)
            self.assertEqual(row["qp_proposal_wall_s"], .5)
            self.assertIsNone(row["master_solver_wall_recorded_s"])
            self.assertIsNone(row["master_solver_wall_complete"])
            self.assertFalse(row["native_lp_master_time_applicable"])
            self.assertIsNone(row["model_construction_s"])
            late = qp.result_row(temporary, name, kind,
                                 {**good, "on_time": False, "elapsed_seconds": 211})
            self.assertFalse(late["complete_evidence"])
            self.assertIsNone(late["lower_exact"])
            raw["master_policy"] = "native_lp"
            (dest / "raw_result.json").write_text(json.dumps({"result": raw}))
            mismatch = qp.result_row(temporary, name, kind, good)
            self.assertEqual(mismatch["outcome"], "partial_result")
            self.assertIsNone(mismatch["lower_exact"])
            assessed["assessment"].update(complete_evidence=False, bounds=None)
            (dest / "result.json").write_text(json.dumps(assessed))
            incomplete = qp.result_row(temporary, name, kind, good)
            self.assertEqual(incomplete["outcome"], "incomplete_evidence")

    def test_all_six_cells_accounted_after_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            qp.reconcile_partial(temporary)
            saved = json.loads((Path(temporary) / "postmortem_summary.json").read_text())
            self.assertEqual(saved["accounted_cells"], 6)
            self.assertEqual({(r["case"], r["market"]) for r in saved["rows"]}, set(qp.cells()))
            self.assertTrue(all(r["outcome"] == "unstarted" for r in saved["rows"]))


if __name__ == "__main__":
    unittest.main()
