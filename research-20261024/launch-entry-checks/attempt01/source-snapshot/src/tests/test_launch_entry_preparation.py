"""Temporary metadata integration; only the full lock verifier is mocked.

Real lock qualification would inspect fixtures/environment, outside this gate.
The actual adapter freezer, accounting builder, initializer and resume consumer
handle handwritten local metadata. These tests never run the controller.
"""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import comparison_native_preflight as adapter
from experiments import launch_entry_preparation as entry
from experiments import recovery_qualification as q


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value))


class LaunchEntryPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.output = self.root / "new-output"
        self.lock_path = self.root / "lock.json"
        self.receipt_path = self.root / "freeze.json"
        self.account_path = self.root / "accounting.json"
        self.source = self.root / "source.txt"
        self.extra = self.root / "closure.txt"
        self.source.write_text("synthetic checked source")
        self.extra.write_text("synthetic external accounting evidence")
        for name in ("stdout.log", "stderr.log"):
            (self.root / name).write_text("")
        self.lock = {"policy": adapter.POLICY, "carried_charge_s": 1400.,
                     "freeze_charge_s": 0., "tasks": [],
                     "sources": {str(self.source): digest(self.source)},
                     "prior_accounting_sha256": "a" * 64}
        write(self.lock_path, self.lock)
        self.receipt = {
            "policy": adapter.POLICY, "phase": "comparison_native_freeze",
            "passed": True, "failure": None, "monitor_failure": None,
            "source_changes": [], "returncode": 0, "secondary_errors": [],
            "primary_failure": None, "accounting_observations_complete": True,
            "accounting_unresolved": [], "charge_is_lower_bound": False,
            "artifact_hashes": {name: digest(self.root / name)
                                for name in ("stdout.log", "stderr.log")},
            "lock_sha256": digest(self.lock_path),
            "prior_accounting_sha256": self.lock["prior_accounting_sha256"],
            "source_hashes": self.lock["sources"],
            "termination": {"group_absent": True, "reaped": True,
                            "owned_pgids": [123], "surviving_pgids": [],
                            "cleanup_errors": [], "probe_diagnostics": []},
            "charged_cpu_s": 2., "supervisor_cpu_s": .5,
            "charged_allocation_s": 1.5, "elapsed_allocation_s": 1.,
            "sampled_peak_rss_bytes": 1.,
            "cumulative_qualification_charge_s": 1402.,
            "stdout_sha256": digest(self.root / "stdout.log"),
            "stderr_sha256": digest(self.root / "stderr.log")}
        write(self.receipt_path, self.receipt)
        self.account = {
            "policy": adapter.POLICY, "phase": "metadata_freeze",
            "freeze_passed": True, "metadata_freeze": True,
            "native_dispatch": False, "accounting_observations_complete": True,
            "owned_groups_absent_and_reaped": True, "owned_pgids": [123],
            "accounting_unresolved": [], "charge_is_lower_bound": False,
            "prior_charge_s": 1400., "current_charge_s": 2.,
            "charged_cpu_s": 1402., "hard_total_ceiling_s": q.CEILING,
            "dispatch_stop_s": q.DISPATCH_STOP,
            "shutdown_reserve_s": q.SHUTDOWN_RESERVE}
        self.refresh_account()
        # This sole mocked production operation avoids fixture/environment reads.
        self.verify = self.enterContext(patch.object(adapter, "verify_lock"))
        self.enterContext(adapter.bound60())

    def refresh_account(self):
        self.account["evidence_hashes"] = {
            str(path): digest(path)
            for path in (self.lock_path, self.receipt_path, self.extra)}
        write(self.account_path, self.account)
        self.args = {
            "lock_path": self.lock_path,
            "freeze_receipt_path": self.receipt_path,
            "accounting_path": self.account_path,
            "expected_lock_sha256": digest(self.lock_path),
            "expected_freeze_receipt_sha256": digest(self.receipt_path),
            "expected_accounting_sha256": digest(self.account_path),
            "expected_cumulative_charge_s": self.account["charged_cpu_s"],
            "expected_policy": adapter.POLICY}

    def reject(self, **changes):
        with self.assertRaises((ValueError, FileNotFoundError)):
            entry.prepare_new_output(self.output, **{**self.args, **changes})
        self.assertFalse(self.output.exists())

    def test_zero_and_positive_correction_reach_real_resume_consumer(self):
        for correction in (0., 3.):
            with self.subTest(correction=correction):
                self.account.update(current_charge_s=2. + correction,
                                    charged_cpu_s=1402. + correction)
                self.refresh_account()
                output = self.root / ("output-" + str(correction))
                inputs = {path: path.read_bytes() for path in self.root.iterdir()
                          if path.is_file()}
                args = self.args.copy()
                result = entry.prepare_new_output(output, **self.args)
                self.assertEqual(self.args, args)
                self.assertEqual({path: path.read_bytes() for path in inputs}, inputs)
                self.assertEqual(result["external_correction_s"], correction)
                self.assertEqual(result["resumed_total_s"], 1402. + correction)
                binding = q.read(output / "campaign.json")
                self.assertEqual(binding["freeze_receipt"], str(self.receipt_path))
                self.assertEqual(binding["freeze_receipt_sha256"], digest(self.receipt_path))
        self.assertEqual(self.verify.call_count, 2)

    def test_real_freezer_cancellation_uses_cumulative_minus_carry(self):
        self.receipt.update(charged_cpu_s=.1, charged_allocation_s=.1,
                            supervisor_cpu_s=0.,
                            cumulative_qualification_charge_s=1400.1)
        write(self.receipt_path, self.receipt)
        self.account.update(current_charge_s=.1, charged_cpu_s=1400.1)
        self.refresh_account()
        result = entry.prepare_new_output(self.output, **self.args)
        self.assertEqual(result["freeze_charge_s"], 1400.1 - 1400.)
        self.assertNotEqual(result["freeze_charge_s"], .1)
        self.assertEqual(result["resumed_total_s"], 1400.1)

    def test_relative_path_aliases_are_canonicalized_like_run(self):
        args = {**self.args, "freeze_receipt_path": self.root / ".." / self.root.name / "freeze.json",
                "accounting_path": self.root / "." / "accounting.json"}
        result = entry.prepare_new_output(self.output, **args)
        self.assertEqual(result["freeze_receipt"], str(self.receipt_path))
        self.assertEqual(result["accounting_path"], str(self.account_path))

    def test_changed_independently_rooted_bytes_leave_no_output(self):
        for path in (self.lock_path, self.receipt_path, self.account_path):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                self.reject()
                path.write_bytes(original)

    def test_missing_root_and_missing_account_evidence_leave_no_output(self):
        self.reject(lock_path=self.root / "missing.json")
        for key in (str(self.lock_path), str(self.receipt_path)):
            with self.subTest(key=key):
                self.refresh_account()
                del self.account["evidence_hashes"][key]
                write(self.account_path, self.account)
                self.args["expected_accounting_sha256"] = digest(self.account_path)
                self.reject()
        self.refresh_account()
        self.extra.unlink()
        self.reject()

    def test_wrong_total_policy_limits_and_source_only_phase_are_rejected(self):
        self.reject(expected_cumulative_charge_s=1403.)
        self.reject(expected_policy="uninstalled-policy")
        for key, value in (("phase", "metadata_initializer_integration"),
                           ("policy", "launch-prefix-source-v1"),
                           ("hard_total_ceiling_s", q.CEILING + 1),
                           ("accounting_observations_complete", False),
                           ("owned_groups_absent_and_reaped", False),
                           ("owned_pgids", []),
                           ("freeze_passed", False), ("native_dispatch", True),
                           ("metadata_freeze", False),
                           ("accounting_unresolved", ["missing observation"]),
                           ("charge_is_lower_bound", True),
                           ("prior_charge_s", 1399.), ("current_charge_s", 3.)):
            with self.subTest(key=key):
                original = self.account[key]
                self.account[key] = value
                self.refresh_account()
                self.reject()
                self.account[key] = original
        self.refresh_account()

    def test_installed_adapter_policy_is_required(self):
        original = q.POLICY
        try:
            q.POLICY = "generic-uninstalled"
            self.reject()
        finally:
            q.POLICY = original

    def test_unfunded_or_negative_correction_leaves_no_output(self):
        for total in (1401., adapter.PACKAGE_CAP - adapter.OUTER_S
                      - adapter.SUPERVISION_RESERVE_S
                      - adapter.ANALYSIS_FINAL_RESERVE_S + 1., q.DISPATCH_STOP):
            with self.subTest(total=total):
                self.account.update(charged_cpu_s=total, current_charge_s=total - 1400.)
                self.refresh_account()
                self.reject()

    def test_bad_real_freeze_receipt_leaves_no_output(self):
        self.receipt["termination"]["group_absent"] = False
        write(self.receipt_path, self.receipt)
        self.refresh_account()
        self.reject()
        self.verify.assert_called_once()

    def test_closure_is_reverified_after_the_lock_consumer(self):
        self.verify.side_effect = lambda lock: self.extra.write_text("changed during verification")
        self.reject()
        self.verify.assert_called_once()

    def test_existing_partial_output_is_exclusive_and_retained(self):
        self.output.mkdir()
        marker = self.output / "partial"
        marker.write_text("retain")
        with self.assertRaises(FileExistsError):
            entry.prepare_new_output(self.output, **self.args)
        self.assertEqual(list(self.output.iterdir()), [marker])
        self.assertEqual(marker.read_text(), "retain")


if __name__ == "__main__":
    unittest.main()
