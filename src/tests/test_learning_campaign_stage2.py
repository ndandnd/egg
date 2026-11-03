"""Pure guards for the fixed stage-2 synthetic campaign."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from egglab import native_recharge as nr  # noqa: E402
from experiments import learning_campaign_stage2 as campaign  # noqa: E402


class LearningCampaignStage2Tests(unittest.TestCase):
    def test_fixed_profile_split_sizes_and_pure_witnesses(self):
        design = campaign.design()
        self.assertEqual(design["reserved_test_seeds"], [2004, 2005])
        self.assertEqual(design["declared_cells"], 44)
        self.assertEqual(len(design["groups"]), 8)
        self.assertEqual([(row["split"], len(row["case"]["trips"]))
                          for row in design["groups"].values()],
                         [("train", 12)]*2 + [("train", 20)]*2 +
                         [("train", 28)]*2 + [("dev", 20), ("dev", 28)])
        self.assertEqual(len({row["case_identity"] for row in design["groups"].values()}), 8)
        for seed in campaign.ACTIVE:
            case = campaign.make_case(seed)
            plan = campaign.make_witness(case)
            self.assertEqual(nr.digest(plan), design["groups"][case.name]["pure_witness_hash"])
            self.assertTrue(nr.replay_native(case, plan)["replay_ok"])
            self.assertEqual(campaign.seed_from_name(case.name), seed)
        for seed in campaign.RESERVED_TEST_SEEDS:
            with self.assertRaisesRegex(ValueError, "reserved test"):
                campaign.make_case(seed)

    def test_all_dev_sources_precede_single_prospective_fit(self):
        cells = campaign.cells()
        self.assertEqual(len(cells), len(set(cells)))
        self.assertEqual(len(cells), 44)
        first_target = next(i for i, (seed, stage) in enumerate(cells)
                            if campaign.SPLITS[seed] == "dev" and stage == "cold")
        dev_sources = {(seed, stage) for seed in (2016, 2017)
                       for stage in ("source0", "source1")}
        self.assertTrue(dev_sources <= set(cells[:first_target]))
        self.assertFalse(any(seed in (2016, 2017) and stage not in ("source0", "source1")
                             for seed, stage in cells[:first_target]))
        self.assertEqual(campaign.stages(2016), campaign.STAGES)
        self.assertEqual(campaign.stages(2010), campaign.STAGES[:-2])
        self.assertEqual(campaign.budget().threads, 1)
        self.assertEqual(campaign.CHILD_SECONDS, 100)
        self.assertEqual(campaign.CONTROLLER_SECONDS, 5400)

    def test_trainer_guard_requires_both_dev_source_groups(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            rows = [{"row_id": campaign.make_case(2016).name + "/source0"},
                    {"row_id": campaign.make_case(2016).name + "/source1"}]
            (path / "catalog.jsonl").write_text("\n".join(json.dumps(row) for row in rows)+"\n")
            with self.assertRaisesRegex(ValueError, "All development source"):
                campaign.train_before_dev_cold(path)
            self.assertFalse((path / "learning_launch.json").exists())


if __name__ == "__main__":
    unittest.main()
