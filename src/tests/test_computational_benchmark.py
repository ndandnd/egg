"""Pure design and harmless process-control tests; never call a native solver."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from experiments import computational_benchmark as screen


class ComputationalScreenTests(unittest.TestCase):
    def test_fixed_cases_markets_and_budgets(self):
        rows = screen.design()
        self.assertEqual(list(rows), list(screen.CASES))
        self.assertEqual({rows[x]["base_timetable_group"] for x in
                          ("public_depot15", "public_depot16")}, {"hildenbrand_37"})
        for name, row in rows.items():
            self.assertEqual(row["case_identity"], screen.CASE_IDS[name])
            self.assertEqual(len(row["markets"]), 2)
            self.assertEqual(set(row["budgets"]), set(screen.STAGES))
            for stage in screen.STAGES:
                self.assertEqual(row["hard_child_seconds"][stage],
                                 row["budgets"][stage]["wall_seconds"] + 30)
                self.assertEqual(row["budgets"][stage]["threads"], 1)
        cyclic = rows["synthetic_cyclic"]["markets"]
        self.assertEqual(cyclic[0]["a"], (0, 4, 0, 0))
        self.assertEqual(cyclic[1]["a"], (0, 3.8, 0, 0.2))
        self.assertEqual(cyclic[0]["b"], (0, 0.2, 0, 0.2))
        public = rows["public_depot15"]["markets"]
        self.assertEqual(public[1]["a"], (0.18,) * 15 + (0.22,) * 15)
        self.assertEqual(public[0]["b"], (1 / 900,) * 30)
        self.assertEqual(rows["public_depot15"]["budgets"]["cold_hull"]["polish_seconds"], 20)

    def test_stage_eligibility_requires_on_time_complete_and_certified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "synthetic_cyclic/state0/retained_hull"
            screen.save_new(folder / "receipt.json", {"returncode": 0, "on_time": True,
                            "hard_timeout": False, "elapsed_seconds": 2, "hard_seconds": 90})
            screen.save_new(folder / "result.json", {"assessment": {"status": "certified",
                            "complete_evidence": True, "bounds": ["1", "2"]}})
            self.assertTrue(screen.complete_stage(root, "synthetic_cyclic", 0,
                                                   "retained_hull", certified=True))
            receipt = json.loads((folder / "receipt.json").read_text())
            receipt["elapsed_seconds"] = 91
            (folder / "receipt.json").write_text(json.dumps(receipt))
            self.assertFalse(screen.complete_stage(root, "synthetic_cyclic", 0,
                                                    "retained_hull", certified=True))
            receipt["elapsed_seconds"] = 2
            receipt["returncode"] = 2
            (folder / "receipt.json").write_text(json.dumps(receipt))
            self.assertFalse(screen.complete_stage(root, "synthetic_cyclic", 0,
                                                    "retained_hull", certified=True))
            receipt["returncode"] = 0
            (folder / "receipt.json").write_text(json.dumps(receipt))
            result = json.loads((folder / "result.json").read_text())
            result["assessment"]["status"] = "budget_exhausted"
            (folder / "result.json").write_text(json.dumps(result))
            self.assertFalse(screen.complete_stage(root, "synthetic_cyclic", 0,
                                                    "retained_hull", certified=True))
            self.assertTrue(screen.complete_stage(root, "synthetic_cyclic", 0,
                                                   "retained_hull"))

    def test_timeout_and_failure_never_become_native_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "synthetic_cyclic/state0/planner"
            screen.save_new(folder / "result.json", {"assessment": {"status": "certified",
                            "bounds": ["1", "2"], "complete_evidence": True}})
            timeout = {"returncode": -15, "hard_timeout": True, "on_time": False,
                       "elapsed_seconds": 1, "hard_seconds": 1}
            row = screen.result_row(root, "synthetic_cyclic", 0, "planner", timeout)
            self.assertEqual((row["status"], row["native_status"]), ("timed_out", "certified"))
            failed = {**timeout, "returncode": 2, "hard_timeout": False}
            self.assertEqual(screen.result_row(root, "synthetic_cyclic", 0,
                                               "planner", failed)["status"], "failed")

    def test_child_deadline_preserves_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt = screen.launch_child(Path(temporary), "synthetic_cyclic", 0, "planner",
                .15, [sys.executable, "-c", "import time; time.sleep(5)"])
            self.assertTrue(receipt["hard_timeout"])
            self.assertFalse(receipt["on_time"])
            self.assertTrue((Path(temporary) / "synthetic_cyclic/state0/planner/receipt.json").is_file())

    def test_total_deadline_kills_nested_worker_group(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child_started, marker = root / "child_started", root / "survivor"
            code = ("import subprocess,sys,time; "
                    "subprocess.Popen([sys.executable,'-c',"
                    "'import sys,time; open(sys.argv[2],\"w\").write(\"ready\"); "
                    "time.sleep(1); open(sys.argv[1],\"w\").write(\"alive\")',"
                    "sys.argv[2],sys.argv[1]]); time.sleep(5)")
            process = subprocess.Popen([sys.executable, "-c", code,
                                        str(child_started), str(marker)], start_new_session=True)
            try:
                deadline = time.monotonic() + 1
                while not child_started.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(child_started.exists())
                # The local sandbox denies ps; the later marker checks actual
                # group termination, while the quiescence parser is tested below.
                with patch.object(screen, "group_quiescent", return_value=True):
                    _, timed_out, quiescent = screen.wait_process_group(process, .1)
                self.assertTrue(timed_out)
                self.assertTrue(quiescent)
                time.sleep(1.1)
                self.assertFalse(marker.exists(), "nested worker survived total-cap cleanup")
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, 9)
                    process.wait()

    def test_group_quiescence_excludes_zombies_but_not_live_members(self):
        with patch.object(screen.subprocess, "check_output",
                          return_value="123 Z\n123 S\n456 R\n"):
            self.assertFalse(screen.group_quiescent(123, 0))
        with patch.object(screen.subprocess, "check_output",
                          return_value="123 Z\n456 R\n"):
            self.assertTrue(screen.group_quiescent(123, 0))

    def test_source_drift_seals_failure_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "attempt"
            target.mkdir()
            screen.save_new(target / "frozen.json", {"source_hashes": {"pin": "before"}})
            with (patch.object(screen, "ATTEMPT", target),
                  patch.object(screen, "frozen", return_value={}),
                  patch.object(screen, "source_hashes", return_value={"pin": "after"}),
                  patch.object(screen.subprocess, "Popen") as popen,
                  patch.object(screen, "wait_process_group", return_value=(0, False, True))):
                popen.return_value.pid = 12345
                self.assertEqual(screen.supervise(target), 1)
            receipt = json.loads((target / "supervisor_receipt.json").read_text())
            self.assertFalse(receipt["source_hashes_unchanged"])
            self.assertEqual((receipt["child_returncode"], receipt["returncode"]), (0, 1))
            self.assertTrue((target / "MANIFEST.json").is_file())

    def test_total_timeout_reconciles_partial_thirty_two_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "attempt"
            target.mkdir()
            screen.save_new(target / "frozen.json", {"source_hashes": {"pin": "same"}})
            folder = target / "synthetic_cyclic/state0/planner"
            screen.save_new(folder / "receipt.json", {"returncode": -15,
                            "hard_timeout": True, "on_time": False,
                            "elapsed_seconds": 2, "hard_seconds": 1})
            (folder / "result.json").write_text('{"assessment":')
            screen.save_new(target / "synthetic_cyclic/state0/cold_hull/launch.json",
                            {"command": ["unimportant"]})
            with (patch.object(screen, "ATTEMPT", target),
                  patch.object(screen, "frozen", return_value={}),
                  patch.object(screen, "source_hashes", return_value={"pin": "same"}),
                  patch.object(screen.subprocess, "Popen"),
                  patch.object(screen, "wait_process_group", return_value=(-15, True, True))):
                self.assertEqual(screen.supervise(target), 124)
            rows = json.loads((target / "postmortem_summary.json").read_text())["rows"]
            self.assertEqual(len(rows), 32)
            self.assertEqual(rows[0]["status"], "timed_out")
            self.assertFalse(rows[0]["complete_evidence"])
            self.assertIn("result_read_error", rows[0])
            self.assertEqual(rows[1]["status"], "interrupted_unreceipted")
            self.assertEqual(rows[2]["status"], "unstarted")
            self.assertTrue((target / "MANIFEST.json").is_file())

    def test_unconfirmed_group_does_not_claim_stable_seal(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "attempt"
            target.mkdir()
            screen.save_new(target / "frozen.json", {"source_hashes": {"pin": "same"}})
            with (patch.object(screen, "ATTEMPT", target),
                  patch.object(screen, "frozen", return_value={}),
                  patch.object(screen, "source_hashes", return_value={"pin": "same"}),
                  patch.object(screen.subprocess, "Popen"),
                  patch.object(screen, "wait_process_group", return_value=(-9, True, False))):
                self.assertEqual(screen.supervise(target), 124)
            receipt = json.loads((target / "supervisor_receipt.json").read_text())
            self.assertFalse(receipt["stable_seal"])
            self.assertFalse((target / "MANIFEST.json").exists())


if __name__ == "__main__":
    unittest.main()
