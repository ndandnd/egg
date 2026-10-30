"""Focused protocol and failure-accounting checks; never invoke a native MIP."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import feasible_pool_pilot as pilot


class FeasiblePoolPilotTests(unittest.TestCase):
    def test_design_has_exactly_twenty_four_frozen_hull_cells(self):
        design = pilot.design()
        self.assertEqual(len(design), 4)
        self.assertEqual((pilot.ARMS, pilot.STATES),
                         (("legacy_cold_hull", "reserve_cold_hull", "reserve_feasible_hull"), (0, 1)))
        for name, row in design.items():
            self.assertEqual(len(row["market_identities"]), 2)
            self.assertEqual(row["budget"], pilot.base.budget(name, "cold_hull").__dict__)
            self.assertEqual(row["hard_child_seconds"], row["budget"]["wall_seconds"] + 30)
            self.assertEqual(row["arms"]["legacy_cold_hull"]["controls"], {})
            for arm in pilot.ARMS[1:]:
                self.assertEqual(row["arms"][arm]["controls"],
                                 {"reuse_policy": "feasible_pool", "pricing_reserve_seconds": 10.0})
        self.assertEqual(design["public_depot15"]["base_timetable_group"], "hildenbrand_37")
        self.assertEqual(design["public_depot16"]["base_timetable_group"], "hildenbrand_37")

    def predecessor_fixture(self, root, *, status="budget_exhausted", receipt=None):
        name = "synthetic_cyclic"
        folder = pilot.cell_dir(root, name, 0, "reserve_feasible_hull")
        case, market = pilot.base.cases()[name], pilot.base.market(name, 0)
        cfg = pilot.base.budget(name, "cold_hull")
        identity = pilot.compact.state_identity(case, market, "retained", 0, cfg,
                                                **pilot.controls("reserve_feasible_hull"))
        raw = {"schema": pilot.nh.SCHEMA, "status": status, "arm": "retained", "state_index": 0,
               "state_identity": identity, "physical_identity": case.identity(),
               "market_identity": market.identity(), "pricing_oracle": pilot.compact.ORACLE_ID,
               "extraction_policy": pilot.compact.EXTRACTION_POLICY,
               **pilot.controls("reserve_feasible_hull"),
               "columns": [{"key": "one", "source": {"state_identity": identity,
                                                     "pricing_oracle": pilot.compact.ORACLE_ID}}],
               "lower_certificate": {"fixture": True}, "mixture": {"fixture": True}}
        pilot.base.save_new(folder / "raw_result.json", {"result": raw, "case": name,
                           "state": 0, "stage": "reserve_feasible_hull"})
        pilot.base.save_new(folder / "result.json", {"assessment": {"status": status,
                           "complete_evidence": True, "bounds": ["0", "1"]},
                           "case": name, "state": 0, "stage": "reserve_feasible_hull"})
        pilot.base.save_new(folder / "receipt.json", receipt or {"returncode": 0,
                           "hard_timeout": False, "on_time": True,
                           "elapsed_seconds": 3, "hard_seconds": cfg.wall_seconds + 30})
        return raw

    def test_bounded_ontime_replayed_predecessor_is_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            with (patch.object(pilot.nh, "replay_column") as replay,
                  patch.object(pilot.base, "assess", return_value={"status": "budget_exhausted",
                              "complete_evidence": True, "bounds": ["0", "1"]})):
                prior = self.predecessor_fixture(tmp)
                self.assertEqual(pilot.predecessor(tmp, "synthetic_cyclic")[0], prior)
                self.assertEqual(replay.call_count, 1)

    def test_late_or_failed_predecessor_is_ineligible(self):
        for receipt in ({"returncode": 0, "hard_timeout": True, "on_time": False,
                         "elapsed_seconds": 91, "hard_seconds": 90},
                        {"returncode": 2, "hard_timeout": False, "on_time": False,
                         "elapsed_seconds": 3, "hard_seconds": 90}):
            with tempfile.TemporaryDirectory() as tmp:
                self.predecessor_fixture(tmp, receipt=receipt)
                self.assertFalse(pilot.eligible(tmp, "synthetic_cyclic")[0])

    def test_wrong_predecessor_identity_and_empty_pool_are_ineligible(self):
        for change in ({"state_identity": "wrong"}, {"columns": []},
                       {"columns": [{"key": "one", "source": {}}]}):
            with tempfile.TemporaryDirectory() as tmp:
                self.predecessor_fixture(tmp)
                folder = pilot.cell_dir(tmp, "synthetic_cyclic", 0, "reserve_feasible_hull")
                wrapped = json.loads((folder / "raw_result.json").read_text())
                wrapped["result"].update(change)
                (folder / "raw_result.json").write_text(json.dumps(wrapped))
                self.assertFalse(pilot.eligible(tmp, "synthetic_cyclic")[0])

    def test_missing_complete_assessment_is_ineligible_even_with_bounded_pool(self):
        for omission in ("assessment", "mixture", "lower_certificate"):
            with tempfile.TemporaryDirectory() as tmp:
                self.predecessor_fixture(tmp)
                folder = pilot.cell_dir(tmp, "synthetic_cyclic", 0, "reserve_feasible_hull")
                file = folder / ("result.json" if omission == "assessment" else "raw_result.json")
                wrapped = json.loads(file.read_text())
                if omission == "assessment":
                    wrapped["assessment"]["complete_evidence"] = False
                else:
                    wrapped["result"].pop(omission)
                file.write_text(json.dumps(wrapped))
                with patch.object(pilot.nh, "replay_column"):
                    admitted, reason = pilot.eligible(tmp, "synthetic_cyclic")
                self.assertFalse(admitted)
                self.assertIn("assessment differs", reason)

    def test_state_zero_reserve_arm_uses_fresh_opt_in_core_controls(self):
        name, arm = "synthetic_cyclic", "reserve_feasible_hull"
        case, market = pilot.base.cases()[name], pilot.base.market(name, 0)
        cfg = pilot.base.budget(name, "cold_hull")
        identity = pilot.compact.state_identity(case, market, "retained", 0, cfg,
                                                **pilot.controls(arm))
        result = {"state_identity": identity, "arm": "retained", "state_index": 0,
                  "physical_identity": case.identity(), "market_identity": market.identity(),
                  **pilot.controls(arm)}
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            pilot.base.save_new(pilot.cell_dir(target, name, 0, arm) / "launch.json", {})
            with (patch.object(pilot, "ATTEMPT", target),
                  patch.object(pilot, "frozen", return_value={"cases": pilot.design()}),
                  patch.object(pilot.compact, "certify", return_value=result) as certify,
                  patch.object(pilot.base, "assess", return_value={"status": "budget_exhausted"})):
                self.assertEqual(pilot.worker(target, name, 0, arm), 0)
            self.assertEqual(certify.call_args.kwargs["previous"], None)
            self.assertEqual(certify.call_args.kwargs["expected_previous"], None)
            self.assertEqual(certify.call_args.kwargs["reuse_policy"], "feasible_pool")
            self.assertEqual(certify.call_args.kwargs["pricing_reserve_seconds"], 10.0)

    def test_timeout_precedence_and_partial_24_row_accounting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = pilot.cell_dir(root, "synthetic_cyclic", 0, "legacy_cold_hull")
            pilot.base.save_new(folder / "result.json", {"assessment": {"status": "certified",
                                "bounds": ["1", "2"], "complete_evidence": True,
                                "counts": {}, "columns": 1, "polish_soft_excess_seconds": 0}})
            pilot.base.save_new(folder / "receipt.json", {"returncode": -15,
                                "hard_timeout": True, "on_time": False,
                                "elapsed_seconds": 91, "hard_seconds": 90})
            pilot.base.save_new(pilot.cell_dir(root, "synthetic_cyclic", 0, "reserve_cold_hull") /
                                "launch.json", {"command": ["unimportant"]})
            rows = pilot.reconcile_partial(root)
            self.assertEqual(len(rows), 24)
            self.assertEqual((rows[0]["status"], rows[0]["native_status"]), ("timed_out", "certified"))
            self.assertEqual(rows[1]["status"], "interrupted_unreceipted")
            self.assertEqual(rows[2]["status"], "unstarted")

    def test_source_drift_fails_before_controller_and_seals_accounting(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "attempt"
            target.mkdir()
            pilot.base.save_new(target / "frozen.json", {"source_hashes": {"pin": "before"}})
            with (patch.object(pilot, "ATTEMPT", target),
                  patch.object(pilot, "frozen", side_effect=ValueError("source drift")),
                  patch.object(pilot, "source_hashes", return_value={"pin": "after"})):
                self.assertEqual(pilot.supervise(target), 1)
            self.assertEqual(len(json.loads((target / "postmortem_summary.json").read_text())["rows"]), 24)
            self.assertTrue((target / "MANIFEST.json").is_file())


if __name__ == "__main__":
    unittest.main()
