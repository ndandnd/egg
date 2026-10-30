"""Sealed-evidence reporter controls; no optimizer or archived result reads."""
import json
from pathlib import Path
import tempfile
import unittest

from experiments import computational_benchmark as screen
from experiments import computational_benchmark_report as reporter


def fixture(root, *, complete=True):
    attempt = root / "attempt"
    attempt.mkdir()
    cases = {case: {"base_timetable_group": "hildenbrand_37" if case.startswith("public_")
                    else case} for case in screen.CASES}
    screen.save_new(attempt / "frozen.json", {"protocol": screen.PROTOCOL,
        "source_commit": "example", "cases": cases, "stage_order": list(screen.STAGES),
        "states": [0, 1]})
    screen.save_new(attempt / "supervisor_receipt.json", {"stable_seal": True,
        "process_group_quiescent": True, "source_hashes_unchanged": True,
        "returncode": 124, "elapsed_seconds": 20})
    stages = [{"case": case, "state": state, "stage": stage, "status": "unstarted"}
              for case in screen.CASES for state in (0, 1) for stage in screen.STAGES]
    if not complete:
        stages.pop()
    screen.save_new(attempt / "postmortem_summary.json", {"rows": stages})
    planner = attempt / "synthetic_cyclic/state0/planner"
    screen.save_new(planner / "receipt.json", {"returncode": -15,
        "hard_timeout": True, "on_time": False, "elapsed_seconds": 91})
    screen.save_new(planner / "result.json", {"assessment": {"status": "certified",
        "bounds": ["1/3", "5/3"], "complete_evidence": True}})
    hull = attempt / "synthetic_cyclic/state0/cold_hull"
    screen.save_new(hull / "receipt.json", {"returncode": 0,
        "hard_timeout": False, "on_time": True, "elapsed_seconds": 12})
    screen.save_new(hull / "result.json", {"assessment": {"status": "budget_exhausted",
        "bounds": ["2", "4"], "complete_evidence": True,
        "counts": {"pricing_requests": 2, "master_calls": 1,
                   "polish_steps": 3, "polish_wall_s": .5}}})
    screen.save_new(attempt / "synthetic_cyclic/state1/cold_hull/ineligible.json", {})
    screen.seal_manifest(attempt)
    return attempt


class ComputationalReportTests(unittest.TestCase):
    def test_receipt_precedence_counts_and_missing_totals(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = fixture(root)
            report = reporter.build_report(attempt)
            self.assertEqual(report["declared_stage_count"], 32)
            self.assertEqual(len(report["rows"]), 32)
            planner, hull = report["rows"][:2]
            self.assertEqual((planner["outcome"], planner["native_status"]),
                             ("timed_out", "certified"))
            self.assertEqual(planner["gap_exact"], "4/3")
            self.assertEqual(hull["outcome"], "budget_exhausted")
            self.assertIsNone(hull["pricing_solver_wall_recorded_s"])
            self.assertIsNone(hull["master_solver_wall_recorded_s"])
            self.assertIsNone(report["hull_arm_totals"][0]["two_state_wall_seconds"])
            self.assertIsNone(report["slurm_elapsed_seconds"])
            out = root / "report"
            reporter.write_report(report, out)
            self.assertEqual(len((out / "stages.csv").read_text().splitlines()), 33)
            self.assertTrue((out / "comparison.md").is_file())
            self.assertIn("≈0.333333", (out / "comparison.md").read_text())
            self.assertNotIn("1/3", (out / "comparison.md").read_text())

    def test_refuses_unsealed_tampered_and_extra_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = fixture(root)
            (attempt / "MANIFEST.json").unlink()
            with self.assertRaises(ValueError):
                reporter.build_report(attempt)
            screen.seal_manifest(attempt)
            (attempt / "synthetic_cyclic/state0/planner/result.json").write_text("{}")
            with self.assertRaises(ValueError):
                reporter.build_report(attempt)
            (attempt / "MANIFEST.json").unlink()
            screen.seal_manifest(attempt)
            (attempt / "late_extra").write_text("after seal")
            with self.assertRaises(ValueError):
                reporter.build_report(attempt)

    def test_rejects_partial_declared_summary_and_unstable_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = fixture(root, complete=False)
            with self.assertRaisesRegex(ValueError, "32 declared"):
                reporter.build_report(attempt)
            (attempt / "MANIFEST.json").unlink()
            summary = attempt / "postmortem_summary.json"
            saved = json.loads(summary.read_text())
            saved["rows"].append({"case": "public_depot16", "state": 1,
                                  "stage": "response", "status": "unstarted"})
            summary.write_text(json.dumps(saved))
            receipt = attempt / "supervisor_receipt.json"
            saved = json.loads(receipt.read_text())
            saved["process_group_quiescent"] = False
            receipt.write_text(json.dumps(saved))
            screen.seal_manifest(attempt)
            with self.assertRaisesRegex(ValueError, "stable seal"):
                reporter.build_report(attempt)

    def test_corrupt_stage_receipt_and_source_drift_remain_accounted(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempt = fixture(Path(temporary))
            (attempt / "MANIFEST.json").unlink()
            (attempt / "synthetic_cyclic/state0/retained_hull/receipt.json").parent.mkdir(parents=True)
            (attempt / "synthetic_cyclic/state0/retained_hull/receipt.json").write_text("{")
            supervisor = attempt / "supervisor_receipt.json"
            saved = json.loads(supervisor.read_text())
            saved["source_hashes_unchanged"] = False
            supervisor.write_text(json.dumps(saved))
            screen.seal_manifest(attempt)
            report = reporter.build_report(attempt)
            self.assertEqual(len(report["rows"]), 32)
            self.assertEqual(report["rows"][2]["outcome"], "receipt_unreadable")
            self.assertFalse(report["supervisor_integrity_ok"])

    def test_null_or_missing_assessment_is_not_a_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            attempt = fixture(Path(temporary))
            (attempt / "MANIFEST.json").unlink()
            result = attempt / "synthetic_cyclic/state0/cold_hull/result.json"
            result.write_text('{"assessment": null}')
            screen.seal_manifest(attempt)
            self.assertEqual(reporter.build_report(attempt)["rows"][1]["outcome"],
                             "partial_result")
            (attempt / "MANIFEST.json").unlink()
            result.unlink()
            screen.seal_manifest(attempt)
            self.assertEqual(reporter.build_report(attempt)["rows"][1]["outcome"],
                             "returned_unassessed")


if __name__ == "__main__":
    unittest.main()
