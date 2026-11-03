"""Pure scope and fallback checks for the energy-relaxed development pilot."""
from __future__ import annotations

from dataclasses import asdict
import inspect
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from egglab import route_fixed_repair  # noqa: E402
from experiments import energy_aware_repair_pilot as pilot  # noqa: E402
from experiments import learning_campaign_stage2 as stage2  # noqa: E402


class EnergyAwareRepairPilotTests(unittest.TestCase):
    def test_prospective_scope_and_pins(self):
        self.assertEqual(pilot.CELLS, (
            ("learning_s2016_n20", "cost_only"),
            ("learning_s2016_n20", "cost_learned"),
            ("learning_s2017_n28", "cost_learned"),
            ("learning_s2017_n28", "cost_only")))
        self.assertEqual((pilot.CHILD_HARD_SECONDS, pilot.CONTROLLER_CAP_SECONDS),
                         (240, 1500))
        with self.assertRaises(ValueError):
            pilot.attempt(pilot.cost.ATTEMPT)
        design = pilot.design()
        self.assertTrue(design["energy_relaxation"])
        self.assertTrue(design["skip_hull_for_replayed_source_fallback"])
        self.assertTrue(design["no_refit"])
        self.assertEqual(len(design["cells"]), 4)
        hashes = pilot.source_hashes()
        for name in ("src/egglab/route_fixed_repair.py",
                     "src/tests/test_energy_cover.py",
                     "src/experiments/route_repair_pilot.py",
                     "src/experiments/cost_aware_repair_pilot.py",
                     *pilot.DIAGNOSIS_FILES):
            self.assertIn(name, hashes)

    def test_worker_passes_energy_flag_and_skips_hull_only_for_fallback(self):
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
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
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
                self.assertIs(evaluate.call_args.args[4], marker if mode == "cost_learned" else None)
                self.assertEqual(evaluate.call_args.kwargs, {
                    "cover_policy": mode, "energy_relaxation": True,
                    "skip_hull_for_fallback": True})

    def test_fallback_replay_has_no_fresh_hull_or_pool(self):
        case = mock.Mock()
        case.identity.return_value = "case-id"
        market = mock.Mock()
        market.identity.return_value = "market-id"
        plan = {"vehicles": []}
        replay = {"ops_cost": 12, "load": []}
        provenance = {"objective_exact": "12", "source_row_id": "source0"}
        controls = {"learned": {"lower_exact": "10", "upper_exact": "13",
                                "native_status": "FEASIBLE"}}
        spec = {"design": {"stage2_input_hashes": {}}, "source_commit": "frozen"}
        with tempfile.TemporaryDirectory() as temporary:
            dest = Path(temporary)
            with mock.patch.object(route_fixed_repair, "repair_target", return_value={
                    "repair_status": "fallback", "failure": {"stage": "charging"}}), \
                 mock.patch.object(pilot.common, "source_fallback",
                                   return_value=(plan, replay, provenance)), \
                 mock.patch.object(pilot.common.nr, "replay_native", return_value=replay), \
                 mock.patch.object(pilot.common.nr, "digest", return_value="plan-hash"), \
                 mock.patch.object(pilot.common.pf, "_checked_pricing_start"), \
                 mock.patch.object(pilot.common.nh, "supply", return_value=0), \
                 mock.patch.object(pilot.common, "repaired_envelope") as pool, \
                 mock.patch.object(pilot.common.compact, "certify") as hull:
                result = pilot.common.evaluate_case(
                    dest, "learning_s2016_n20", case, market, None, spec,
                    controls, time.monotonic(), cover_policy="cost_only",
                    energy_relaxation=True, skip_hull_for_fallback=True)
            self.assertEqual(result, 0)
            pool.assert_not_called()
            hull.assert_not_called()
            actual = json.loads((dest / "result.json").read_text())
            self.assertEqual(actual["outcome"], "fallback_replayed_no_new_hull")
            self.assertEqual(actual["candidate_kind"], "source_fallback")
            self.assertEqual(actual["candidate_objective_exact"], "12")
            self.assertEqual(actual["hull_assessment"], {})
            self.assertEqual(actual["hull_wall_seconds"], 0)
            self.assertEqual(actual["historical_bounds_reference"]["learned"]["lower_exact"], "10")
            self.assertFalse(json.loads((dest / "hull_skipped.json").read_text())["fresh_bound"])
            self.assertFalse((dest / "pool_preparation.json").exists())

    def test_replayed_new_repair_still_gets_fresh_hull(self):
        case = mock.Mock()
        case.identity.return_value = "case-id"
        market = mock.Mock()
        market.identity.return_value = "market-id"
        plan = {"vehicles": []}
        replay = {"ops_cost": 12, "load": []}
        proposed = {"repair_status": "replayed", "plan": plan, "replay": replay,
                    "cover": {"selected_movements": []}, "true_cost_exact": "12"}
        envelope = {"lineage_digest": "lineage", "columns": [{"key": "column"}]}
        spec = {"design": {"stage2_input_hashes": {}}, "source_commit": "frozen"}
        with tempfile.TemporaryDirectory() as temporary:
            dest = Path(temporary)
            with mock.patch.object(route_fixed_repair, "repair_target", return_value=proposed), \
                 mock.patch.object(pilot.common.nr, "replay_native", return_value=replay), \
                 mock.patch.object(pilot.common.nr, "digest", return_value="plan-hash"), \
                 mock.patch.object(pilot.common.pf, "_checked_pricing_start"), \
                 mock.patch.object(pilot.common.pf, "recover_paths"), \
                 mock.patch.object(pilot.common.nh, "supply", return_value=0), \
                 mock.patch.object(pilot.common, "repaired_envelope",
                                   return_value=(envelope, {"identity": "ok"})) as pool, \
                 mock.patch.object(pilot.common.compact, "certify", return_value={"native": "ok"}) as hull, \
                 mock.patch.object(pilot.common.retrieval, "assess_hull",
                                   return_value={"status": "assessed"}):
                result = pilot.common.evaluate_case(
                    dest, "learning_s2016_n20", case, market, None, spec, {},
                    time.monotonic(), cover_policy="cost_only",
                    energy_relaxation=True, skip_hull_for_fallback=True)
            self.assertEqual(result, 0)
            pool.assert_called_once()
            hull.assert_called_once()
            actual = json.loads((dest / "result.json").read_text())
            self.assertEqual(actual["outcome"], "candidate_and_native_hull_checked")
            self.assertEqual(actual["candidate_kind"], "repaired")
            self.assertEqual(actual["hull_assessment"]["status"], "assessed")
            self.assertTrue((dest / "raw_hull.json").exists())

    def test_historical_defaults_remain_disabled(self):
        signature = inspect.signature(pilot.common.evaluate_case)
        self.assertFalse(signature.parameters["energy_relaxation"].default)
        self.assertFalse(signature.parameters["skip_hull_for_fallback"].default)


if __name__ == "__main__":
    unittest.main()
