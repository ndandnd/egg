"""Pure profile checks for the conditional shared charging development pilot."""
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
from experiments import learning_campaign_stage2 as stage2  # noqa: E402
from experiments import shared_interval_repair_pilot as pilot  # noqa: E402


class SharedIntervalPilotTests(unittest.TestCase):
    def test_distinct_immutable_profile_and_scope(self):
        self.assertNotEqual(pilot.ATTEMPT, pilot.prior.ATTEMPT)
        self.assertEqual(pilot.PROFILE.module, "experiments.shared_interval_repair_pilot")
        with self.assertRaises(ValueError):
            pilot.shared.attempt(pilot.prior.ATTEMPT, pilot.PROFILE)
        with self.assertRaises(ValueError):
            pilot.shared.PilotProfile(pilot.ATTEMPT, pilot.PROTOCOL,
                pilot.PROFILE.module, "bad", pilot.SOURCE_FILES,
                pilot.DIAGNOSIS_FILES, shared_charging=True)
        self.assertEqual(len(set(pilot.SOURCE_FILES)), len(pilot.SOURCE_FILES))
        self.assertEqual(pilot.shared.CELLS, pilot.prior.shared.CELLS)
        for filename in pilot.DIAGNOSIS_FILES:
            self.assertIn(filename, pilot.SOURCE_FILES)
        design = pilot.shared.design(pilot.PROFILE)
        self.assertEqual([(row["case"], row["mode"]) for row in design["cells"]],
                         list(pilot.shared.CELLS))
        self.assertTrue(design["energy_relaxation"])
        self.assertTrue(design["charging_caps"])
        self.assertTrue(design["shared_charging"])
        self.assertTrue(design["skip_hull_for_replayed_source_fallback"])
        self.assertTrue(design["no_refit"])
        self.assertEqual((design["path_seconds"], design["child_hard_seconds"],
                          design["controller_cap_seconds"]), (5.0, 240, 1500))
        self.assertFalse(pilot.shared.design().get("shared_charging", False))
        self.assertFalse(pilot.shared.design(pilot.prior.PROFILE).get("shared_charging", False))

    def test_worker_forwards_only_explicit_shared_profile(self):
        case = stage2.make_case(2016)
        market = stage2.market(case, "target")
        declared = {"case": asdict(case), "case_identity": case.identity(),
                    "markets": {"target": asdict(market)},
                    "market_identities": {"target": market.identity()}, "split": "dev"}
        prior_frozen = {"design": {"groups": {case.name: declared}}}
        marker = object()
        pinned = {"catalog.jsonl": "abc"}
        spec = {"design": {"stage2_input_hashes": pinned}, "source_commit": "test"}
        for mode in pilot.shared.MODES:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary)
                dest = pilot.shared.folder(path, case.name, mode)
                dest.mkdir(parents=True)
                (dest / "launch.json").write_text("{}")
                with mock.patch.object(pilot.shared, "attempt", return_value=path), \
                     mock.patch.object(pilot.shared, "frozen", return_value=spec), \
                     mock.patch.object(pilot.shared.common, "_stage2_inputs",
                                       return_value=(prior_frozen, marker)), \
                     mock.patch.object(pilot.shared.common, "input_hashes", return_value=pinned), \
                     mock.patch.object(pilot.shared.common, "control_rows", return_value={}), \
                     mock.patch.object(pilot.shared.common, "evaluate_case", return_value=0) as evaluate:
                    self.assertEqual(pilot.shared.worker(path, case.name, mode,
                                                         pilot.PROFILE), 0)
                self.assertIs(evaluate.call_args.args[4], marker if mode == "cost_learned" else None)
                self.assertEqual(evaluate.call_args.kwargs, {
                    "cover_policy": mode, "energy_relaxation": True,
                    "skip_hull_for_fallback": True, "charging_caps": True,
                    "shared_charging": True})

    def test_result_guard_and_historical_defaults(self):
        name, mode = pilot.shared.CELLS[0]
        with tempfile.TemporaryDirectory() as temporary:
            dest = pilot.shared.folder(temporary, name, mode)
            dest.mkdir(parents=True)
            (dest / "result.json").write_text(json.dumps({
                "cover_policy": mode, "energy_relaxation": True,
                "charging_caps": True, "outcome": "fallback_replayed_no_new_hull"}))
            with self.assertRaisesRegex(ValueError, "shared interval charging"):
                pilot.shared.result_row(temporary, name, mode, pilot.PROFILE)
        signature = inspect.signature(pilot.shared.common.evaluate_case)
        self.assertFalse(signature.parameters["shared_charging"].default)


if __name__ == "__main__":
    unittest.main()
