"""Pure route-repair pilot guards; native optimization is never invoked."""
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
from egglab import native_pathflow_hull as compact  # noqa: E402
from egglab import native_pathflow as pf  # noqa: E402
from egglab import native_recharge as nr  # noqa: E402
from experiments import learning_campaign_stage2 as stage2  # noqa: E402
from experiments import route_repair_pilot as pilot  # noqa: E402


class RouteRepairPilotTests(unittest.TestCase):
    def test_scope_and_budgets(self):
        self.assertEqual(pilot.CASE_NAMES, ("learning_s2016_n20", "learning_s2017_n28"))
        self.assertEqual((pilot.repair_budget().threads, pilot.hull_budget().threads), (1, 1))
        self.assertEqual((pilot.repair_budget().wall_seconds,
                          pilot.hull_budget().wall_seconds,
                          pilot.CHILD_HARD_SECONDS), (55, 70, 240))
        self.assertEqual((pilot.CONTROLLER_CAP_SECONDS, pilot.REPAIR_PATH_SECONDS), (900, 5.0))
        with self.assertRaises(ValueError):
            pilot.attempt(ROOT / "result/learning_campaign/20260930-stage2-attempt1")

    def test_repaired_envelope_replays_one_feasible_fleet_without_old_bound(self):
        case = stage2.make_case(2016)
        market = stage2.market(case, "target")
        plan = stage2.make_witness(case)
        plan["extraction_policy"] = compact.EXTRACTION_POLICY
        envelope, identity = pilot.repaired_envelope(
            case, market, plan, {"kind": "test", "plan_hash": nr.digest(plan)})
        self.assertEqual(envelope["state_identity"], identity)
        self.assertEqual(len(envelope["columns"]), 1)
        self.assertEqual(envelope["kind"], "derived_route_repair_pool_import")
        self.assertNotIn("lower_certificate", envelope)
        self.assertEqual(envelope["columns"][0]["witness_hash"], nr.digest(plan))

    def test_historical_controls_replay_and_tampering_fails(self):
        case = stage2.make_case(2016)
        market = stage2.market(case, "target")
        plan = stage2.make_witness(case)
        replay = nr.replay_native(case, plan)
        exact = Fraction(replay["ops_cost"]) + pilot.nh.supply(market, replay["load"])
        rows = []
        for arm in ("learned", "cheapest_bill"):
            rows.append({"row_id": case.name + "/" + arm, "split": "dev",
                         "case_identity": case.identity(), "market_identity": market.identity(),
                         "label": {"status": "returned", "native_status": "bounded",
                                   "feasible": True, "plan": plan,
                                   "plan_hash": nr.digest(plan),
                                   "objective_exact": str(exact),
                                   "elapsed_seconds": 3.0}})
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "catalog.jsonl").write_text("\n".join(json.dumps(row) for row in rows)+"\n")
            with mock.patch.object(pilot, "STAGE2", path):
                controls = pilot.control_rows(case.name, case, market)
                self.assertEqual(set(controls), {"learned", "cheapest_bill"})
                rows[0]["label"]["objective_exact"] = "0"
                (path / "catalog.jsonl").write_text("\n".join(json.dumps(row) for row in rows)+"\n")
                with self.assertRaisesRegex(ValueError, "does not replay"):
                    pilot.control_rows(case.name, case, market)

    def test_partial_receipts_remain_visible(self):
        with tempfile.TemporaryDirectory() as temporary:
            dest = pilot.folder(temporary, pilot.CASE_NAMES[0])
            dest.mkdir(parents=True)
            self.assertEqual(pilot.result_row(temporary, pilot.CASE_NAMES[0])["outcome"],
                             "interrupted_unreceipted")
            (dest / "receipt.json").write_text(json.dumps({"returncode": 124,
                "hard_timeout": True, "elapsed_seconds": 240.1}))
            row = pilot.result_row(temporary, pilot.CASE_NAMES[0])
            self.assertEqual(row["outcome"], "hard_timeout")
            self.assertEqual(row["elapsed_seconds"], 240.1)

    def test_source_fallback_uses_pre_target_source_plan_and_selection(self):
        case = stage2.make_case(2016)
        market = stage2.market(case, "target")
        plan = stage2.make_witness(case)
        plan.update(formulation=pf.FORMULATION, native_matrix=pf.NATIVE_MATRIX,
                    extraction_policy=pf.EXTRACTION_POLICY)
        replay = nr.replay_native(case, plan)
        key = pilot.nh.projection_key(replay["load"], replay["ops_cost"])
        rows = [{"row_id": case.name + "/" + source, "split": "dev",
                 "arm": "source", "case_identity": case.identity(),
                 "label": {"feasible": True, "plan": plan,
                           "plan_hash": nr.digest(plan), "status": "returned",
                           "native_status": "bounded"}}
                for source in ("source0", "source1")]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "catalog.jsonl").write_text("\n".join(json.dumps(row) for row in rows)+"\n")
            selected = path / case.name / "state0/cheapest_bill/selection.json"
            selected.parent.mkdir(parents=True)
            selected.write_text(json.dumps({"selected_keys": [key],
                                            "source_paid_seconds": 12.0}))
            with mock.patch.object(pilot, "STAGE2", path):
                chosen, _, provenance = pilot.source_fallback(case.name, case, market)
                self.assertEqual(chosen, plan)
                self.assertEqual(provenance["source_row_id"], case.name + "/source0")
                self.assertEqual(provenance["source_pool_acquisition_seconds"], 12.0)
                selected.write_text(json.dumps({"selected_keys": ["wrong"]}))
                with self.assertRaisesRegex(ValueError, "differs"):
                    pilot.source_fallback(case.name, case, market)


if __name__ == "__main__":
    unittest.main()
