"""Handwritten accounting regressions; no native experiment imports or fixtures."""

from dataclasses import FrozenInstanceError, asdict
import json
import unittest

from egglab.launch_accounting import build_launch_accounting


class LaunchAccountingTests(unittest.TestCase):
    def test_cancellation_regression_matches_exact_consumer_component(self):
        result = build_launch_accounting(
            carried_charge_s=1512.6011370494984,
            receipt_charged_cpu_s=3.1857290000000003,
            receipt_cumulative_charge_s=1515.7868660494985,
            reconciled_total_s=1516.4011370494984,
        )
        consumer_component = 1515.7868660494985 - 1512.6011370494984
        self.assertEqual(result.freeze_charge_s, 3.1857290000000376)
        self.assertEqual(result.freeze_charge_s, consumer_component)
        self.assertNotEqual(result.freeze_charge_s, result.receipt_charged_cpu_s)
        self.assertEqual(result.receipt_charged_cpu_s, 3.1857290000000003)
        self.assertEqual(result.canonical_base_s, 1515.7868660494985)
        self.assertEqual(result.external_correction_s, 0.614270999999917)
        restored = json.loads(json.dumps(asdict(result)))
        self.assertEqual(restored["freeze_charge_s"], consumer_component)
        self.assertEqual(restored["receipt_charged_cpu_s"], 3.1857290000000003)

    def test_zero_external_correction(self):
        result = build_launch_accounting(
            carried_charge_s=1512.6011370494984,
            receipt_charged_cpu_s=3.1857290000000003,
            receipt_cumulative_charge_s=1515.7868660494985,
            reconciled_total_s=1515.7868660494985,
        )
        self.assertEqual(result.external_correction_s, 0.0)

    def test_zero_inputs(self):
        result = build_launch_accounting(
            carried_charge_s=0, receipt_charged_cpu_s=0,
            receipt_cumulative_charge_s=0, reconciled_total_s=0,
        )
        self.assertEqual(result.freeze_charge_s, 0)
        self.assertEqual(result.external_correction_s, 0)

    def test_external_correction_uses_canonical_base(self):
        result = build_launch_accounting(
            carried_charge_s=1512.6011370494984,
            receipt_charged_cpu_s=3.1857290000000003,
            receipt_cumulative_charge_s=1515.7868660494985,
            reconciled_total_s=1516.4011370494984,
        )
        self.assertEqual(result.external_correction_s,
                         result.reconciled_total_s - result.canonical_base_s)
        self.assertNotEqual(result.external_correction_s,
                            result.reconciled_total_s - result.carried_charge_s
                            - result.receipt_charged_cpu_s)

    def test_inconsistent_receipt_is_rejected_exactly(self):
        with self.assertRaises(ValueError):
            build_launch_accounting(
                carried_charge_s=10.0, receipt_charged_cpu_s=2.0,
                receipt_cumulative_charge_s=12.000000000000002,
                reconciled_total_s=13.0,
            )

    def test_underfunded_total_is_rejected_without_clamping(self):
        with self.assertRaises(ValueError):
            build_launch_accounting(
                carried_charge_s=10.0, receipt_charged_cpu_s=2.0,
                receipt_cumulative_charge_s=12.0, reconciled_total_s=11.0,
            )

    def test_invalid_scalar_in_each_input_is_rejected(self):
        inputs = dict(carried_charge_s=10.0, receipt_charged_cpu_s=2.0,
                      receipt_cumulative_charge_s=12.0, reconciled_total_s=13.0)
        for name in inputs:
            for invalid in (float("nan"), float("inf"), -float("inf"), -1,
                            True, False, "12", None, [], {}, complex(1, 0), 10**400):
                with self.subTest(name=name, invalid=invalid):
                    candidate = {**inputs, name: invalid}
                    with self.assertRaises(ValueError):
                        build_launch_accounting(**candidate)

    def test_inputs_are_unchanged_and_record_is_frozen(self):
        inputs = dict(carried_charge_s=10.0, receipt_charged_cpu_s=2.0,
                      receipt_cumulative_charge_s=12.0, reconciled_total_s=13.0)
        original = inputs.copy()
        result = build_launch_accounting(**inputs)
        self.assertEqual(inputs, original)
        with self.assertRaises(FrozenInstanceError):
            result.freeze_charge_s = 99.0
