"""Pure scope and cap guards for the 28-service shared-cover budget study."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from experiments import learning_campaign_stage2 as stage2  # noqa: E402
from experiments import shared_budget_repair_pilot as pilot  # noqa: E402
from egglab import route_fixed_repair  # noqa: E402


class SharedBudgetPilotTests(unittest.TestCase):
    def test_two_cell_budget_is_explicit_and_historical_profiles_keep_defaults(self):
        self.assertEqual(pilot.CELLS, (
            ("learning_s2017_n28", "cost_learned"),
            ("learning_s2017_n28", "cost_only")))
        self.assertEqual(pilot.PATH_SECONDS, 30.0)
        self.assertNotEqual(pilot.ATTEMPT, pilot.prior.ATTEMPT)
        with self.assertRaises(ValueError):
            pilot.shared.attempt(pilot.prior.ATTEMPT, pilot.PROFILE)
        design = pilot.shared.design(pilot.PROFILE)
        self.assertEqual([(row["case"], row["mode"]) for row in design["cells"]],
                         list(pilot.CELLS))
        self.assertEqual(design["path_seconds"], 30.0)
        self.assertTrue(design["shared_charging"])
        self.assertTrue(design["no_refit"])
        self.assertEqual(len(pilot.shared.design()["cells"]), 4)
        self.assertEqual(pilot.shared.design()["path_seconds"], 5.0)
        self.assertEqual(len(pilot.shared.design(pilot.prior.PROFILE)["cells"]), 4)
        self.assertEqual(pilot.shared.design(pilot.prior.PROFILE)["path_seconds"], 5.0)
        hashes = pilot.shared.source_hashes(pilot.PROFILE)
        self.assertEqual(len(hashes), len(pilot.SOURCE_FILES))
        self.assertIn("research-20260930/learning-campaign/RESULT_MANIFEST_SHARED_INTERVAL.json", hashes)
        self.assertIn("src/experiments/route_repair_pilot.py", hashes)

    def test_worker_forwards_thirty_seconds_without_other_change(self):
        case = stage2.make_case(2017)
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
                    "shared_charging": True, "path_seconds": 30.0})

    def test_result_cap_and_profile_cell_guard(self):
        name, mode = pilot.CELLS[0]
        with tempfile.TemporaryDirectory() as temporary:
            dest = pilot.shared.folder(temporary, name, mode)
            dest.mkdir(parents=True)
            (dest / "result.json").write_text(json.dumps({
                "cover_policy": mode, "energy_relaxation": True,
                "charging_caps": True, "shared_charging": True,
                "path_seconds": 5.0,
                "outcome": "fallback_replayed_no_new_hull"}))
            with self.assertRaisesRegex(ValueError, "route-cover cap differs"):
                pilot.shared.result_row(temporary, name, mode, pilot.PROFILE)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            with mock.patch.object(pilot.shared, "attempt", return_value=path), \
                 mock.patch.object(pilot.shared, "frozen", return_value={}), \
                 mock.patch.object(pilot.shared.common, "_stage2_inputs") as prior_inputs:
                out = pilot.shared.worker(path, "learning_s2016_n20", "cost_only",
                                          pilot.PROFILE)
            self.assertEqual(out, 2)
            prior_inputs.assert_not_called()

    def test_evaluator_forwards_thirty_second_cover_cap_and_receipts_it(self):
        case = mock.Mock()
        case.identity.return_value = "case-id"
        market = mock.Mock()
        market.identity.return_value = "market-id"
        plan = {"vehicles": []}
        replay = {"ops_cost": 12, "load": []}
        provenance = {"objective_exact": "12", "source_row_id": "source0"}
        spec = {"design": {"stage2_input_hashes": {}}, "source_commit": "frozen"}
        with tempfile.TemporaryDirectory() as temporary:
            dest = Path(temporary)
            with mock.patch.object(route_fixed_repair, "repair_target", return_value={
                    "repair_status": "fallback", "failure": {"stage": "cover"}}) as repair, \
                 mock.patch.object(pilot.shared.common, "source_fallback",
                                   return_value=(plan, replay, provenance)), \
                 mock.patch.object(pilot.shared.common.nr, "replay_native", return_value=replay), \
                 mock.patch.object(pilot.shared.common.nr, "digest", return_value="plan-hash"), \
                 mock.patch.object(pilot.shared.common.pf, "_checked_pricing_start"), \
                 mock.patch.object(pilot.shared.common.nh, "supply", return_value=0), \
                 mock.patch.object(pilot.shared.common.compact, "certify") as hull:
                self.assertEqual(pilot.shared.common.evaluate_case(
                    dest, "learning_s2017_n28", case, market, None, spec, {},
                    time.monotonic(), cover_policy="cost_only", energy_relaxation=True,
                    charging_caps=True, shared_charging=True,
                    skip_hull_for_fallback=True, path_seconds=30.0), 0)
            self.assertEqual(repair.call_args.kwargs["path_seconds"], 30.0)
            hull.assert_not_called()
            self.assertEqual(json.loads((dest / "repair.json").read_text())["path_seconds"], 30.0)
            self.assertEqual(json.loads((dest / "result.json").read_text())["path_seconds"], 30.0)


if __name__ == "__main__":
    unittest.main()
