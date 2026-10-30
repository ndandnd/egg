"""Pure isolation, ordering, inference, and receipt guards for transfer campaign."""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from egglab import native_hull as nh  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402
from experiments import learning_campaign_stage2 as prior  # noqa: E402
from experiments import transfer_campaign as campaign  # noqa: E402


class TransferCampaignTests(unittest.TestCase):
    def test_new_groups_reserved_ids_and_source_first_order(self):
        self.assertEqual(campaign.PROFILE, {2018: ("dev", 20), 2019: ("dev", 28)})
        self.assertEqual(campaign.RESERVED_TEST_SEEDS, (2004, 2005, 2020, 2021))
        self.assertEqual(len(campaign.CELLS), 18)
        self.assertEqual(campaign.CELLS[:4], ((2018, "source0"), (2018, "source1"),
                                              (2019, "source0"), (2019, "source1")))
        self.assertEqual(campaign.CELLS[4:6], ((2018, "cold"), (2018, "retained")))
        self.assertEqual(campaign.CELLS[-2:], ((2019, "shared_cost_only"),
                                                (2019, "shared_cost_learned")))
        self.assertEqual((campaign.NATIVE_CHILD_SECONDS, campaign.REPAIR_CHILD_SECONDS,
                          campaign.INFERENCE_SECONDS, campaign.CONTROLLER_SECONDS),
                         (100, 240, 45, 3000))
        self.assertEqual(14*100+4*240, 2360)
        for seed, n in ((2018, 20), (2019, 28)):
            case = campaign.case_for(seed)
            self.assertEqual(len(case.trips), n)
            self.assertEqual(nr.replay_native(case, prior.make_witness(
                case, profile=campaign.PROFILE))["ops_cost"], n/2*100)
            self.assertNotIn(case.identity(), [prior.make_case(s).identity()
                for s in prior.ACTIVE])
        for seed in campaign.RESERVED_TEST_SEEDS:
            with self.assertRaises(ValueError):
                campaign.case_for(seed)
        with self.assertRaises(ValueError):
            campaign.seed_for("learning_s2020_n20")
        design = campaign.design()
        self.assertEqual(design["declared_cells"], 18)
        self.assertEqual(design["new_size_matched_test_reservations"],
                         {"2020": 20, "2021": 28})
        self.assertTrue(design["no_refit"])
        self.assertEqual(set(design["groups"]),
                         {"learning_s2018_n20", "learning_s2019_n28"})

    def test_infer_reads_only_sources_and_frozen_model(self):
        rows = []
        for seed in campaign.SEEDS:
            case = campaign.case_for(seed)
            for stage in campaign.SOURCE_STAGES:
                market = prior.market(case, stage)
                rows.append({"row_id": case.name+"/"+stage,
                    "base_group": f"learning_s{seed}", "split": "dev", "arm": "source",
                    "case": asdict(case), "case_identity": case.identity(),
                    "market": asdict(market), "label": {"feasible": False, "plan": None}})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "inference_launch.json").write_text("{}")
            fake_model = mock.Mock(training_groups=tuple(f"learning_s{s}" for s in range(2010, 2016)))
            with mock.patch.object(campaign, "attempt", return_value=path), \
                 mock.patch.object(campaign, "frozen"), \
                 mock.patch.object(campaign, "_catalog_rows", return_value=rows), \
                 mock.patch.object(campaign.repair, "_stage2_inputs", return_value=({}, fake_model)), \
                 mock.patch.object(campaign.lp, "rank_candidates", return_value={}) as rank, \
                 mock.patch.object(campaign.lp, "fit", side_effect=AssertionError("refit forbidden")), \
                 mock.patch.object(campaign.trainer, "_summary", return_value={"ok": True}), \
                 mock.patch.object(campaign.trainer, "_write_atomic") as write:
                self.assertEqual(campaign.infer_worker(path), 0)
            self.assertEqual(rank.call_count, 2)
            for call in rank.call_args_list:
                self.assertIs(call.args[0], fake_model)
                self.assertEqual(call.args[1]["arm"], "proposal_target")
                self.assertEqual(call.args[1]["label"], {"feasible": False, "plan": None})
                self.assertEqual(len(call.args[2]), 4)
                self.assertTrue(all(row["arm"] == "source" for row in call.args[2]))
            self.assertEqual(write.call_count, 1)

    def test_failed_inference_receipt_is_not_retried_after_target_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "catalog.jsonl").write_text("{}\n")
            rows = [{"row_id": campaign.case_for(seed).name+"/"+stage}
                    for seed in campaign.SEEDS for stage in campaign.SOURCE_STAGES]
            with mock.patch.object(campaign, "_catalog_rows", return_value=rows), \
                 mock.patch.object(campaign, "source_hashes", return_value={}), \
                 mock.patch.object(campaign.sizing, "software_runtime", return_value={}), \
                 mock.patch.object(campaign.subprocess, "run",
                                   return_value=mock.Mock(returncode=2)) as run:
                first = campaign.infer_before_targets(path)
                self.assertEqual(first["returncode"], 2)
                self.assertTrue(first["before_all_target_cells"])
                cold = campaign.folder(path, campaign.case_for(2018).name, "cold")
                cold.mkdir(parents=True)
                (cold / "launch.json").write_text("{}")
                second = campaign.infer_before_targets(path)
            self.assertEqual(first, second)
            run.assert_called_once()

    def test_cold_has_no_import_and_direct_proposal_is_separate_receipt(self):
        case = campaign.case_for(2018)
        group = campaign.design()["groups"][case.name]
        spec = {"design": {"groups": {case.name: group}}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            cold = campaign.folder(path, case.name, "cold")
            cold.mkdir(parents=True)
            (cold / "launch.json").write_text("{}")
            (path / "inference_receipt.json").write_text("{}")
            with mock.patch.object(campaign, "attempt", return_value=path), \
                 mock.patch.object(campaign, "frozen", return_value=spec), \
                 mock.patch.object(campaign.prior, "pool") as pool, \
                 mock.patch.object(campaign.compact, "certify", return_value={}) as certify, \
                 mock.patch.object(campaign.retrieval, "assess_hull", return_value={}):
                self.assertEqual(campaign.native_worker(path, 2018, "cold"), 0)
            pool.assert_not_called()
            self.assertEqual(certify.call_args.kwargs["arm"], "cold")
            self.assertIsNone(certify.call_args.kwargs["previous"])
            self.assertFalse((cold / "direct_proposals.json").exists())
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            dest = campaign.folder(path, case.name, "cheapest_bill")
            dest.mkdir(parents=True)
            (dest / "launch.json").write_text("{}")
            (path / "inference_receipt.json").write_text("{}")
            candidate = {"key": "key", "source": "source0", "call": 1,
                         "column": {"plan": {}}, "witness_hash": "hash"}
            available = {"eligible": True, "candidates": [candidate],
                         "sources": {"source0": {"paid_source_seconds": 3.0}}}
            direct = [{"key": "key", "nonlinear_cost_exact": "12", "witness_hash": "hash"}]
            with mock.patch.object(campaign, "attempt", return_value=path), \
                 mock.patch.object(campaign, "frozen", return_value=spec), \
                 mock.patch.object(campaign.prior, "pool", return_value=available), \
                 mock.patch.object(campaign.prior, "catalog_source_pool", return_value=available), \
                 mock.patch.object(campaign.prior, "select_nonlinear_cheapest",
                                   return_value=[candidate]), \
                 mock.patch.object(campaign.retrieval, "direct_proposals", return_value=direct), \
                 mock.patch.object(campaign.retrieval, "import_envelope",
                                   return_value=({"columns": []}, {})), \
                 mock.patch.object(campaign.compact, "certify", return_value={}), \
                 mock.patch.object(campaign.retrieval, "assess_hull", return_value={}):
                self.assertEqual(campaign.native_worker(path, 2018, "cheapest_bill"), 0)
            saved = json.loads((dest / "direct_proposals.json").read_text())
            self.assertEqual(saved["proposals"], direct)
            self.assertGreaterEqual(saved["direct_replay_rescoring_wall_seconds"], 0)

    def test_provisional_repair_plan_survives_later_hull_failure(self):
        case = campaign.case_for(2018)
        market = prior.market(case, "target")
        plan = prior.make_witness(case, profile=campaign.PROFILE)
        replay = nr.replay_native(case, plan)
        exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            dest = campaign.folder(path, case.name, "shared_cost_only")
            dest.mkdir(parents=True)
            (dest / "receipt.json").write_text(json.dumps({"returncode": 2,
                "hard_timeout": False, "elapsed_seconds": 17.0}))
            (dest / "repair.json").write_text(json.dumps({"result": {
                "repair_status": "replayed", "plan": plan}}))
            (dest / "independent_replay.json").write_text(json.dumps({
                "candidate_kind": "repaired", "case_identity": case.identity(),
                "market_identity": market.identity(), "plan_hash": nr.digest(plan),
                "objective_exact": exact}))
            (dest / "exception.json").write_text(json.dumps({"type": "RuntimeError",
                "message": "hull failure"}))
            label = campaign.catalog_row(path, 2018, "shared_cost_only")["label"]
            self.assertTrue(label["feasible"])
            self.assertEqual(label["status"], "failed")
            self.assertEqual(label["optimality"], "unknown")
            self.assertEqual(label["objective_exact"], exact)
            self.assertEqual(label["upper_exact"], exact)
            self.assertIsNone(label["hull_assessment"])
            self.assertEqual(label["failure"]["message"], "hull failure")

    def test_controller_preserves_interrupted_unreceipted_cell(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            first = campaign.folder(path, campaign.case_for(2018).name, "source0")
            second = campaign.folder(path, campaign.case_for(2018).name, "source1")
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "receipt.json").write_text("{}")
            with mock.patch.object(campaign, "attempt", return_value=path), \
                 mock.patch.object(campaign, "frozen"), \
                 mock.patch.object(campaign, "catalog_row", return_value={"row_id": "first"}), \
                 mock.patch.object(campaign.prior, "append_catalog") as append, \
                 mock.patch.object(campaign.base, "launch_child") as launch:
                with self.assertRaisesRegex(ValueError, "Interrupted unreceipted"):
                    campaign.controller(path)
            append.assert_called_once()
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
