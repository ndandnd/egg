"""Pure campaign guards; no native optimization is run."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from egglab import native_recharge as nr  # noqa: E402
from experiments import learning_campaign as campaign  # noqa: E402


class LearningCampaignTests(unittest.TestCase):
    def test_split_and_distinct_physical_groups(self):
        design = campaign.design()
        self.assertEqual(design["reserved_test_seeds"], [2004, 2005])
        self.assertEqual(len(design["groups"]), 3)
        self.assertEqual([row["split"] for row in design["groups"].values()],
                         ["train", "train", "dev"])
        self.assertEqual(len({row["case_identity"] for row in design["groups"].values()}), 3)
        for seed in campaign.ACTIVE:
            case = campaign.make_case(seed)
            nr.validate_case(case)
            self.assertEqual(len(case.trips), 8)
            self.assertEqual(len(campaign.market(case, "target").a), 30)
        with self.assertRaisesRegex(ValueError, "Reserved test"):
            campaign.make_case(2004)

    def test_cells_and_budgets(self):
        design = campaign.design()
        self.assertEqual(design["stages"]["learning_s2003"], list(campaign.STAGES))
        self.assertEqual(design["stages"]["learning_s2001"], list(campaign.STAGES[:-2]))
        self.assertEqual(design["budget"]["threads"], 1)
        self.assertEqual(design["budget"]["backend"], "GRB")
        self.assertEqual(design["child_hard_seconds"], 100)
        self.assertEqual(design["controller_hard_seconds"], 2100)
        self.assertEqual(design["policy"]["bound_cache_policy"], "none")
        self.assertEqual(design["declared_cells"], 17)

    def test_catalog_is_append_only_and_conflict_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            row = {"row_id": "case/source0", "label": {"status": "failed"}}
            campaign.append_catalog(temporary, row)
            campaign.append_catalog(temporary, row)
            lines = (Path(temporary) / "catalog.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0]), row)
            with self.assertRaisesRegex(ValueError, "conflict"):
                campaign.append_catalog(temporary, {"row_id": row["row_id"],
                                                     "label": {"status": "certified"}})

    def test_failed_child_preserves_receipt_without_feasible_label(self):
        case = campaign.make_case(2001)
        with tempfile.TemporaryDirectory() as temporary:
            dest = campaign.folder(temporary, case.name, "cold")
            dest.mkdir(parents=True)
            (dest / "receipt.json").write_text(json.dumps({"returncode": 124,
                "hard_timeout": True, "elapsed_seconds": 100.2}))
            (dest / "exception.json").write_text(json.dumps({"type": "Timeout",
                                                               "message": "cap"}))
            label = campaign.label(temporary, case, "cold")
            self.assertEqual(label["status"], "hard_timeout")
            self.assertFalse(label["feasible"])
            self.assertEqual(label["elapsed_seconds"], 100.2)
            self.assertIsNone(label["objective_exact"])

    def test_failed_assessment_does_not_promote_raw_bounds(self):
        case = campaign.make_case(2001)
        with tempfile.TemporaryDirectory() as temporary:
            dest = campaign.folder(temporary, case.name, "cold")
            dest.mkdir(parents=True)
            (dest / "receipt.json").write_text(json.dumps({"returncode": 2,
                "hard_timeout": False, "elapsed_seconds": 1.2}))
            (dest / "raw_result.json").write_text(json.dumps({"result": {
                "status": "certified", "columns": [],
                "lower_certificate": {"lower_exact": "123"},
                "mixture": {"objective_exact": "124"}}}))
            row = campaign.label(temporary, case, "cold")
            self.assertIsNone(row["lower_exact"])
            self.assertNotIn("native_mixture_upper_exact", row)
            self.assertEqual(row["unverified_native_lower_exact"], "123")
            self.assertEqual(row["unverified_native_mixture_upper_exact"], "124")
            self.assertEqual(row["status"], "failed")
            self.assertFalse(row["feasible"])

    def test_cheapest_control_uses_nonlinear_target_cost(self):
        market = campaign.nh.Market("synthetic", (0.0, 0.0), (1.0, 1.0))
        pool = {"candidates": [
            {"source": "source0", "call": 0, "key": "concentrated",
             "column": {"ops_cost": 0.0, "load": [2.0, 0.0]}},
            {"source": "source1", "call": 0, "key": "spread",
             "column": {"ops_cost": 0.0, "load": [1.0, 1.0]}}]}
        self.assertEqual(campaign.select_nonlinear_cheapest(pool, market)[0]["key"],
                         "spread")


if __name__ == "__main__":
    unittest.main()
