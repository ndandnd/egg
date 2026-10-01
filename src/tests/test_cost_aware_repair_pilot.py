"""Pure guards for the four-cell crossed repair ablation."""
from __future__ import annotations

from dataclasses import asdict
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import cost_aware_repair_pilot as pilot  # noqa: E402
from experiments import learning_campaign_stage2 as stage2  # noqa: E402


class CostAwareRepairPilotTests(unittest.TestCase):
    def test_crossed_order_and_frozen_scope(self):
        self.assertEqual(pilot.CELLS, (
            ("learning_s2016_n20", "cost_only"),
            ("learning_s2016_n20", "cost_learned"),
            ("learning_s2017_n28", "cost_learned"),
            ("learning_s2017_n28", "cost_only")))
        self.assertEqual(len(set(pilot.CELLS)), 4)
        self.assertEqual((pilot.CHILD_HARD_SECONDS, pilot.CONTROLLER_CAP_SECONDS),
                         (240, 1500))
        self.assertNotEqual(pilot.ATTEMPT, pilot.common.ATTEMPT)
        with self.assertRaises(ValueError):
            pilot.attempt(pilot.common.ATTEMPT)
        self.assertIn("src/experiments/route_repair_pilot.py", pilot.source_hashes())
        self.assertIn("src/egglab/route_fixed_repair.py", pilot.source_hashes())
        self.assertEqual(len(pilot.common.input_hashes()), 9)
        self.assertEqual(len(pilot.design()["cells"]), 4)
        self.assertTrue(pilot.design()["no_refit"])

    def test_cost_only_passes_no_prior_and_cost_learned_uses_frozen_prior(self):
        case = stage2.make_case(2016)
        market = stage2.market(case, "target")
        declared = {"case": asdict(case), "case_identity": case.identity(),
                    "markets": {"target": asdict(market)},
                    "market_identities": {"target": market.identity()}, "split": "dev"}
        prior_frozen = {"design": {"groups": {case.name: declared}}}
        marker = object()
        pinned = {"catalog.jsonl": "abc"}
        spec = {"design": {"stage2_input_hashes": pinned}, "source_commit": "test"}
        for mode in pilot.MODES:
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                dest = pilot.folder(path, case.name, mode)
                dest.mkdir(parents=True)
                (dest / "launch.json").write_text("{}")
                with mock.patch.object(pilot, "attempt", return_value=path), \
                     mock.patch.object(pilot, "frozen", return_value=spec), \
                     mock.patch.object(pilot.common, "_stage2_inputs",
                                       return_value=(prior_frozen, marker)), \
                     mock.patch.object(pilot.common, "input_hashes", return_value=pinned), \
                     mock.patch.object(pilot.common, "control_rows", return_value={}), \
                     mock.patch.object(pilot.common, "evaluate_case", return_value=0) as evaluate:
                    self.assertEqual(pilot.worker(path, case.name, mode), 0)
                self.assertEqual(evaluate.call_args.args[4], marker if mode == "cost_learned" else None)
                self.assertEqual(evaluate.call_args.kwargs["cover_policy"], mode)
                self.assertTrue((dest / "controls.json").is_file())

    def test_result_mode_and_interrupted_receipts(self):
        name, mode = pilot.CELLS[0]
        with tempfile.TemporaryDirectory() as temporary:
            dest = pilot.folder(temporary, name, mode)
            dest.mkdir(parents=True)
            self.assertEqual(pilot.result_row(temporary, name, mode)["outcome"],
                             "interrupted_unreceipted")
            (dest / "receipt.json").write_text(json.dumps({"returncode": 124,
                "hard_timeout": True, "elapsed_seconds": 240.2}))
            row = pilot.result_row(temporary, name, mode)
            self.assertEqual((row["outcome"], row["elapsed_seconds"]),
                             ("hard_timeout", 240.2))
            (dest / "result.json").write_text(json.dumps({"cover_policy": "wrong",
                "outcome": "candidate_and_native_hull_checked", "repair_status": "replayed"}))
            with self.assertRaisesRegex(ValueError, "mode differs"):
                pilot.result_row(temporary, name, mode)

    def test_shared_evaluator_retains_historical_default_policy(self):
        signature = inspect.signature(pilot.common.evaluate_case)
        self.assertEqual(signature.parameters["cover_policy"].default, "score_only")


if __name__ == "__main__":
    unittest.main()
