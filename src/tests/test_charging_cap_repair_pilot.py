"""Pure profile guards for the charging-window-cap development run."""
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
from experiments import charging_cap_repair_pilot as pilot  # noqa: E402
from experiments import learning_campaign_stage2 as stage2  # noqa: E402


class ChargingCapPilotTests(unittest.TestCase):
    def test_profile_is_distinct_and_freezes_charging_diagnosis(self):
        self.assertNotEqual(pilot.ATTEMPT, pilot.shared.ATTEMPT)
        self.assertEqual(pilot.PROFILE.module, "experiments.charging_cap_repair_pilot")
        with self.assertRaises(ValueError):
            pilot.shared.attempt(pilot.shared.ATTEMPT, pilot.PROFILE)
        design = pilot.shared.design(pilot.PROFILE)
        self.assertEqual(len(design["cells"]), 4)
        self.assertEqual([(x["case"], x["mode"]) for x in design["cells"]],
                         list(pilot.shared.CELLS))
        self.assertEqual((design["path_seconds"], design["child_hard_seconds"],
                          design["controller_cap_seconds"]), (5.0, 240, 1500))
        self.assertTrue(design["energy_relaxation"])
        self.assertTrue(design["charging_caps"])
        self.assertIn("individual depot and terminal", design["energy_relaxation_meaning"])
        self.assertNotIn("optimistic full reset", design["energy_relaxation_meaning"])
        self.assertTrue(design["skip_hull_for_replayed_source_fallback"])
        self.assertTrue(design["no_refit"])
        self.assertFalse(pilot.shared.design().get("charging_caps", False))
        for name in pilot.DIAGNOSIS_FILES:
            self.assertIn(name, design["diagnosis_hashes"])
        hashes = pilot.shared.source_hashes(pilot.PROFILE)
        self.assertEqual(len(hashes), len(pilot.SOURCE_FILES))
        for name in ("src/egglab/route_fixed_repair.py",
                     "src/tests/test_charging_cap_cover.py",
                     "src/experiments/route_repair_pilot.py",
                     "src/experiments/energy_aware_repair_pilot.py",
                     "src/cluster/charging_cap_repair.sbatch"):
            self.assertIn(name, hashes)

    def test_worker_only_enables_caps_in_explicit_profile(self):
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
                    "skip_hull_for_fallback": True, "charging_caps": True})

    def test_result_guard_and_historic_evaluator_default(self):
        name, mode = pilot.shared.CELLS[0]
        with tempfile.TemporaryDirectory() as temporary:
            dest = pilot.shared.folder(temporary, name, mode)
            dest.mkdir(parents=True)
            (dest / "result.json").write_text(json.dumps({
                "cover_policy": mode, "energy_relaxation": True,
                "outcome": "fallback_replayed_no_new_hull"}))
            with self.assertRaisesRegex(ValueError, "charging-window caps"):
                pilot.shared.result_row(temporary, name, mode, pilot.PROFILE)
        signature = inspect.signature(pilot.shared.common.evaluate_case)
        self.assertFalse(signature.parameters["charging_caps"].default)


if __name__ == "__main__":
    unittest.main()
