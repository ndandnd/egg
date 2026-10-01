"""Pure admission, matching, and interval guards for joint support diagnosis."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import economic_support_diagnostic as econ  # noqa: E402


class EconomicSupportTests(unittest.TestCase):
    def test_six_exact_source_identities_and_budgets(self):
        design = econ.design()
        self.assertEqual(len(econ.cells()), 6)
        self.assertEqual(len(design["hull_source"]), 6)
        self.assertEqual(design["order"], econ.qp.design()["order"])
        self.assertEqual(design["hard_child_seconds"], {"planner": 210, "response": 90})
        self.assertEqual(design["budgets"]["planner"]["max_rounds"], 16)
        self.assertEqual(design["budgets"]["response"]["phase_seconds"], 45)
        self.assertEqual(econ.CONTROLLER_CAP_SECONDS, 2100)
        self.assertEqual(len(econ.source_hashes()), len(econ.SOURCE_FILES))
        with self.assertRaises(ValueError):
            econ._attempt(ROOT / "result/qp_baseline_diagnostic/20260929-attempt1")

    def test_hull_source_hash_and_late_status_rejected(self):
        files = ("COLLECTION_RECEIPT.json", "frozen_identity.json", "summary.json",
                 "MANIFEST.json", "supervisor_receipt.json", "wrapper_receipt.json")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in files:
                shutil.copyfile(econ.HULL / name, directory / name)
            with mock.patch.object(econ, "HULL", directory):
                (directory / "summary.json").write_text("{}")
                with self.assertRaisesRegex(ValueError, "collection hash"):
                    econ.imported_hull()
                shutil.copyfile(ROOT / "research-20260929/qp-baseline-diagnostic/"
                                "results-attempt1/summary.json", directory / "summary.json")
                summary = json.loads((directory / "summary.json").read_text())
                summary["rows"][0]["on_time"] = False
                (directory / "summary.json").write_text(json.dumps(summary))
                receipt = json.loads((directory / "COLLECTION_RECEIPT.json").read_text())
                receipt["curated_file_sha256"]["summary.json"] = econ.base.sha(directory / "summary.json")
                (directory / "COLLECTION_RECEIPT.json").write_text(json.dumps(receipt))
                with self.assertRaisesRegex(ValueError, "complete on-time"):
                    econ.imported_hull()

    def test_gradient_and_independent_interval_arithmetic(self):
        name, kind = econ.cells()[0]
        m = econ.market(name, kind)
        load = [0.0] * len(m.a)
        load[0] = 10.0
        price = econ.gradient(m, load)
        self.assertEqual(price[0], float(econ.Fraction(m.a[0]) +
                                         econ.Fraction(m.b[0]) * 10))
        self.assertEqual(len(price), len(m.a))
        self.assertEqual(econ.gap_interval(["100", "110"], ["90", "105"]), ["0", "20"])
        self.assertEqual(econ.combined_intervals(["90", "110"], ["100", "120"]),
                         {"D_interval_exact": ["100", "110"],
                          "CH_interval_exact": ["100", "110"],
                          "D_minus_CH_interval_exact": ["0", "10"]})
        self.assertEqual(econ.gap_interval(["110", "120"], ["90", "100"]), ["10", "30"])
        self.assertEqual(econ.regret_interval("110", ["80", "100"]), ["10", "30"])
        with self.assertRaisesRegex(ValueError, "incompatible"):
            econ.gap_interval(["70", "80"], ["90", "100"])
        with self.assertRaisesRegex(ValueError, "lower exceeds"):
            econ.regret_interval("110", ["111", "120"])

    def test_ineligible_and_incomplete_stages_never_promote_bounds(self):
        name, kind = econ.cells()[0]
        hull = econ.imported_hull()[f"{name}/{kind}"]
        with tempfile.TemporaryDirectory() as temp:
            response = econ.folder(temp, name, kind, "response")
            response.mkdir(parents=True)
            (response / "ineligible.json").write_text("{}")
            missing = econ.stage_row(temp, name, kind, "planner")
            skipped = econ.stage_row(temp, name, kind, "response")
            self.assertEqual((missing["outcome"], skipped["outcome"]),
                             ("unstarted", "ineligible"))
            self.assertIsNone(skipped["lower_exact"])
            joint = econ.cell_summary(name, kind, missing, skipped, hull)
            self.assertIsNone(joint["D_interval_exact"])
            self.assertIsNone(joint["D_minus_CH_interval_exact"])
            self.assertIsNone(joint["incumbent_own_price_regret_interval_exact"])
            self.assertIsNone(econ.planner_admitted(temp, name, kind))

    def test_late_or_market_mismatched_planner_is_not_admitted(self):
        name, kind = econ.cells()[0]
        with tempfile.TemporaryDirectory() as temp:
            dest = econ.folder(temp, name, kind, "planner")
            dest.mkdir(parents=True)
            m = econ.market(name, kind)
            plan = {"vehicles": []}
            raw = {"case_identity": econ.cases()[name].identity(),
                   "formulation": econ.pf.FORMULATION,
                   "extraction_policy": econ.pf.EXTRACTION_POLICY,
                   "status": "bounded", "lower": 1.0, "upper": 2.0,
                   "a": [0.0], "b": [0.0], "plan": plan}
            saved = {"case": name, "market": kind, "stage": "planner",
                     "assessment": {"status": "bounded", "bounds": ["1", "2"],
                                    "plan_replayed": True,
                                    "plan_hash": econ.nr.digest(plan),
                                    "replay": {"load": [0.0] * len(m.a),
                                               "ops_cost": 1},
                                    "executable_cost_exact": "2"}}
            (dest / "raw_result.json").write_text(json.dumps({"result": raw}))
            (dest / "result.json").write_text(json.dumps(saved))
            late = {"returncode": 0, "on_time": False, "hard_timeout": False,
                    "elapsed_seconds": 211}
            (dest / "receipt.json").write_text(json.dumps(late))
            self.assertEqual(econ.stage_row(temp, name, kind, "planner", late)["outcome"], "late")
            self.assertIsNone(econ.planner_admitted(temp, name, kind))
            good = {**late, "on_time": True, "elapsed_seconds": 3}
            (dest / "receipt.json").write_text(json.dumps(good))
            self.assertEqual(econ.stage_row(temp, name, kind, "planner", good)["outcome"],
                             "partial_result")
            self.assertIsNone(econ.planner_admitted(temp, name, kind))


if __name__ == "__main__":
    unittest.main()
