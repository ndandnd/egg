"""Pure lineage, LP-outcome, and interrupted-cell checks for fixed source charging."""
from __future__ import annotations

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
from egglab import route_fixed_repair as rr  # noqa: E402
from experiments import fixed_source_charge_campaign as run  # noqa: E402


class FixedSourceChargeTests(unittest.TestCase):
    def test_scope_inputs_and_exact_archived_source_replays(self):
        self.assertEqual(len(run.CELLS), 8)
        self.assertEqual(run.CELLS, tuple((seed, source) for seed in (2016, 2017, 2018, 2019)
                                          for source in ("source0", "source1")))
        self.assertEqual((run.CHILD_SECONDS, run.CONTROLLER_SECONDS), (100, 1200))
        self.assertEqual((run.budget().phase_seconds, run.budget().wall_seconds,
                          run.budget().threads), (45, 55, 1))
        design = run.design()
        self.assertEqual(design["declared_cells"], 8)
        self.assertEqual(design["test_groups_unobserved"], [2004, 2005, 2020, 2021])
        self.assertTrue(design["source_only_pre_target"])
        self.assertTrue(design["no_route_reoptimization"])
        self.assertTrue(design["no_fresh_hull"])
        self.assertEqual(len(run.input_hashes()), 18)
        self.assertEqual(len(run.source_hashes()), len(run.SOURCE_FILES))
        for seed in run.ARCHIVES:
            case, target = run.archived_case(seed)
            for source in run.SOURCES:
                row, replay = run.archived_source(seed, source, case)
                self.assertEqual(row["label"]["plan_hash"],
                                 design["groups"][case.name]["source_plan_hashes"][source])
                self.assertEqual(replay["replay_ok"], True)
                self.assertEqual(target.identity(), design["groups"][case.name]["market_identity"])
        with self.assertRaises(ValueError):
            run.archived_case(2020)

    def test_worker_records_direct_bill_and_replayed_fixed_route_lp(self):
        seed, source = run.CELLS[0]
        case, market = run.archived_case(seed)
        row, replay = run.archived_source(seed, source, case)
        plan = row["label"]["plan"]
        spec = {"design": {"groups": {case.name: {"case_identity": case.identity(),
            "market_identity": market.identity(),
            "source_plan_hashes": {source: row["label"]["plan_hash"]}}}}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            dest = run.folder(path, seed, source)
            dest.mkdir(parents=True)
            (dest / "launch.json").write_text("{}")
            with mock.patch.object(run, "attempt", return_value=path), \
                 mock.patch.object(run, "frozen", return_value=spec), \
                 mock.patch.object(rr, "_solve_fixed_charge",
                                   return_value=(plan, replay, {"status": "OPTIMAL"})) as solve:
                self.assertEqual(run.worker(path, seed, source), 0)
            selected = set(solve.call_args.args[2])
            self.assertEqual(selected, {mid for v in plan["vehicles"] for mid in v["movements"]})
            direct = json.loads((dest / "direct_rescore.json").read_text())
            fixed = json.loads((dest / "fixed_charge.json").read_text())
            result = json.loads((dest / "result.json").read_text())
            exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
            self.assertEqual((direct["objective_exact"], fixed["objective_exact"],
                              result["post_lp_objective_exact"]), (exact, exact, exact))
            self.assertEqual(fixed["target_optimality"],
                             "unknown; native LP minimizes only linear market.a")

    def test_lp_failure_retains_direct_plan_and_native_telemetry(self):
        seed, source = run.CELLS[0]
        case, market = run.archived_case(seed)
        row, _ = run.archived_source(seed, source, case)
        spec = {"design": {"groups": {case.name: {"case_identity": case.identity(),
            "market_identity": market.identity(),
            "source_plan_hashes": {source: row["label"]["plan_hash"]}}}}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            dest = run.folder(path, seed, source)
            dest.mkdir(parents=True)
            (dest / "launch.json").write_text("{}")
            with mock.patch.object(run, "attempt", return_value=path), \
                 mock.patch.object(run, "frozen", return_value=spec), \
                 mock.patch.object(rr, "_solve_fixed_charge", side_effect=rr.RepairStageFailure(
                     "infeasible", native_stats={"status": "INFEASIBLE"})):
                self.assertEqual(run.worker(path, seed, source), 0)
            self.assertTrue((dest / "direct_rescore.json").exists())
            self.assertEqual(json.loads((dest / "result.json").read_text())["status"],
                             "no_replayed_lp_plan")
            self.assertEqual(json.loads((dest / "fixed_charge_failure.json").read_text())
                             ["native_stats"]["status"], "INFEASIBLE")

    def test_selection_salvages_replayed_lp_after_worker_failure_and_missing_direct(self):
        seed = 2016
        case, market = run.archived_case(seed)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            for source in run.SOURCES:
                dest = run.folder(path, seed, source)
                dest.mkdir(parents=True)
                (dest / "receipt.json").write_text(json.dumps({
                    "returncode": 2 if source == "source0" else 0,
                    "hard_timeout": False,
                    "elapsed_seconds": 4.0 if source == "source0" else None}))
            row, replay = run.archived_source(seed, "source0", case)
            plan = row["label"]["plan"]
            exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
            dest = run.folder(path, seed, "source0")
            (dest / "fixed_charge.json").write_text(json.dumps({
                "status": "replayed", "case_identity": case.identity(),
                "market_identity": market.identity(),
                "source_plan_hash": row["label"]["plan_hash"],
                "selected_movements": sorted(mid for v in plan["vehicles"] for mid in v["movements"]),
                "native_stats": {"status": "OPTIMAL"}, "plan": plan,
                "plan_hash": nr.digest(plan), "replay": replay, "objective_exact": exact}))
            (dest / "exception.json").write_text(json.dumps({
                "type": "RuntimeError", "message": "failed after fixed charge"}))
            selection = run.select_case(path, seed)
            first = selection["candidates"][0]
            self.assertFalse(first["direct_receipt_present"])
            self.assertEqual(first["post_lp_status"],
                             "replayed_provisional_after_worker_failure")
            self.assertEqual(first["post_lp_objective_exact"], exact)
            self.assertEqual(first["receipt"]["returncode"], 2)
            self.assertEqual(selection["best_of_four"]["objective_exact"],
                             min((Fraction(x["direct_objective_exact"]) for x in selection["candidates"]),
                                 default=Fraction(exact)).__str__())
            self.assertIsNotNone(selection["archived_model_preparation_elapsed_seconds"])
            (dest / "result.json").write_text(json.dumps({
                "status": "replayed", "post_lp_objective_exact": exact}))
            (path / case.name / "selection.json").unlink()
            completed_before_failure = run.select_case(path, seed)
            self.assertEqual(completed_before_failure["candidates"][0]["post_lp_status"],
                             "replayed_provisional_after_worker_failure")
            self.assertIsNone(selection["two_lp_paid_seconds"])
            self.assertIsNone(selection["two_lp_plus_historical_acquisition_seconds"])
            self.assertIsNotNone(selection["historical_source_acquisition_seconds"])

    def test_selection_rejects_misattributed_fixed_route(self):
        seed = 2016
        case, market = run.archived_case(seed)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            for source in run.SOURCES:
                dest = run.folder(path, seed, source)
                dest.mkdir(parents=True)
                (dest / "receipt.json").write_text(json.dumps({
                    "returncode": 2, "hard_timeout": False, "elapsed_seconds": 4.0}))
            row, replay = run.archived_source(seed, "source0", case)
            plan = row["label"]["plan"]
            exact = str(Fraction(replay["ops_cost"]) + nh.supply(market, replay["load"]))
            (run.folder(path, seed, "source0") / "fixed_charge.json").write_text(json.dumps({
                "status": "replayed", "case_identity": case.identity(),
                "market_identity": market.identity(),
                "source_plan_hash": row["label"]["plan_hash"],
                "selected_movements": [], "plan": plan, "plan_hash": nr.digest(plan),
                "replay": replay, "objective_exact": exact}))
            with self.assertRaisesRegex(ValueError, "Recharged plan replay/hash"):
                run.select_case(path, seed)

    def test_interrupted_unreceipted_cell_stops_controller(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            first = run.folder(path, *run.CELLS[0])
            first.mkdir(parents=True)
            with mock.patch.object(run, "attempt", return_value=path), \
                 mock.patch.object(run, "frozen"), \
                 mock.patch.object(run.base, "launch_child") as launch:
                with self.assertRaisesRegex(ValueError, "Interrupted unreceipted"):
                    run.controller(path)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
