"""Focused read-only reporting checks; no optimizer or private archive dependency."""
import json
from pathlib import Path
import tempfile
import unittest

from experiments import feasible_pool_pilot as pilot
from experiments import feasible_pool_pilot_report as report


class FeasiblePoolReportTests(unittest.TestCase):
    def test_outward_display_preserves_enclosure(self):
        self.assertEqual(report.outward("315767/1000", True), "315.76")
        self.assertEqual(report.outward("547464/1000", False), "547.47")
        self.assertEqual(report.outward("-121/100", True), "-1.21")

    def test_compact_trace_links_fresh_pricing_and_later_master(self):
        events = [
            {"event": "state_start", "imported_column_keys": ["old"], "fresh_bounds": True},
            {"event": "master_start", "call": 0, "column_keys": ["old"]},
            {"event": "master_status", "call": 0, "stats": {"status": "OPTIMAL", "wall_s": .2}},
            {"event": "pricing_request", "call": 0, "seed": False,
             "pricing_wall_allowance_seconds": 40, "remaining_total_seconds": 50, "reserve_seconds": 10},
            {"event": "pricing_result", "call": 0, "result": {"status": "bounded", "stats": {
                "status": "FEASIBLE", "incumbent": 5, "lower_bound": 3, "wall_s": 2}}},
            {"event": "global_bound", "call": 0, "certificate": {"lower_exact": "9/2"},
             "column": {"key": "fresh"}},
            {"event": "column_added", "key": "fresh"},
            {"event": "master_start", "call": 1, "column_keys": ["old", "fresh"]},
            {"event": "pricing_reserve_stop", "remaining_seconds": 9, "reserve_seconds": 10},
        ]
        trace = report.extract_trace(events)
        self.assertEqual((trace["imported_columns"], trace["imported_in_first_master"]), (1, 1))
        self.assertEqual((trace["new_columns_added"], trace["added_columns_reached_later_master"]), (1, 1))
        self.assertEqual(trace["reserve_stop_events"], 1)
        self.assertEqual(trace["pricing_trace"][0]["global_lower_exact"], "9/2")
        self.assertEqual(trace["pricing_trace"][0]["native_lower_bound"], 3)
        self.assertEqual(trace["pricing_solver_wall_recorded_s"], 2)

    def test_manifest_requires_exact_24_keys_and_unchanged_seal(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = Path(tmp)
            pilot.base.save_new(attempt / "frozen.json", {"protocol": pilot.PROTOCOL,
                "cases": {case: {"base_timetable_group": case} for case in pilot.CASES},
                "stage_order": list(pilot.ARMS), "states": list(pilot.STATES)})
            pilot.base.save_new(attempt / "supervisor_receipt.json", {"stable_seal": True,
                "process_group_quiescent": True, "returncode": 0, "source_hashes_unchanged": True})
            rows = [{"case": case, "state": state, "stage": arm} for case in pilot.CASES
                    for state in pilot.STATES for arm in pilot.ARMS]
            pilot.base.save_new(attempt / "summary.json", {"rows": rows})
            pilot.seal_manifest(attempt)
            self.assertEqual(report.verify(attempt)[3], "summary.json")
            (attempt / "MANIFEST.json").unlink()
            rows.pop()
            (attempt / "summary.json").write_text(json.dumps({"rows": rows}))
            pilot.seal_manifest(attempt)
            with self.assertRaisesRegex(ValueError, "24 cells"):
                report.verify(attempt)

    def test_timeout_status_precedes_successful_native_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = Path(tmp)
            folder = attempt / "synthetic_cyclic/state0/legacy_cold_hull"
            pilot.base.save_new(folder / "receipt.json", {"hard_timeout": True,
                "returncode": -15, "on_time": False, "elapsed_seconds": 91})
            pilot.base.save_new(folder / "result.json", {"assessment": {"status": "certified",
                "complete_evidence": True}})
            row, _ = report.cell(attempt, {"cases": {"synthetic_cyclic": {
                "base_timetable_group": "synthetic_cyclic"}}}, {"files": {}},
                "synthetic_cyclic", 0, "legacy_cold_hull")
            self.assertEqual((row["outcome"], row["native_status"]), ("timed_out", "certified"))

    def test_missing_paid_time_renders_na_without_zero_bar(self):
        totals = [{"case": case, "arm": arm, "state0_s": 2.0, "state1_s": 3.0,
                   "paid_two_state_s": 5.0} for case in pilot.CASES for arm in pilot.ARMS]
        missing = next(row for row in totals if row["case"] == "synthetic_cyclic"
                       and row["arm"] == "reserve_feasible_hull")
        missing.update(state1_s=None, paid_two_state_s=None)
        rows = [{"case": case, "state": 1, "arm": arm, "lower_exact": None,
                 "upper_exact": None} for case in pilot.CASES[2:] for arm in pilot.ARMS]
        with tempfile.TemporaryDirectory() as tmp:
            report.plot({"paid_totals": totals, "rows": rows}, Path(tmp))
            svg = (Path(tmp) / "paid_two_state_time.svg").read_text()
            self.assertIn("n/a", svg)
            self.assertTrue((Path(tmp) / "paid_two_state_time.png").is_file())
            self.assertFalse(any(line.endswith(" ") for line in svg.splitlines()))

    def test_csv_writer_uses_lf_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cells.csv"
            report.write_csv(path, [{"a": "x", "b": 1}], ("a", "b"))
            self.assertEqual(path.read_bytes(), b"a,b\nx,1\n")


if __name__ == "__main__":
    unittest.main()
