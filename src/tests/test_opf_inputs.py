"""Transport and zone guards using local responses only."""
from datetime import timedelta, datetime, timezone
import json
from pathlib import Path
from subprocess import CompletedProcess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
import pin_opf_inputs as inputs


class InputChecks(unittest.TestCase):
    def test_rate_limit_waits_once_and_keeps_tls(self):
        limited = CompletedProcess([], 22, b"", b"status=429 retry_after=182")
        success = CompletedProcess([], 0, b"data", b"status=200 retry_after=")
        attempts = []
        with patch.object(inputs.subprocess, "run", side_effect=[limited, success]) as run, \
                patch.object(inputs.clock, "sleep") as wait:
            self.assertEqual(inputs.fetch("https://example.test", 100, 30, attempts), b"data")
        wait.assert_called_once_with(183)
        self.assertEqual(len(attempts), 2)
        command = run.call_args.args[0]
        self.assertEqual(command[1], "--disable")
        self.assertNotIn("--insecure", command)
        self.assertIn("=https", command)

    def test_tls_failure_is_final(self):
        with patch.object(inputs.subprocess, "run", return_value=CompletedProcess(
                [], 60, b"", b"certificate validation failed\nstatus=000 retry_after=")) as run:
            with self.assertRaisesRegex(OSError, "certificate"):
                inputs.fetch("https://example.test", 100, 30, [])
            self.assertEqual(run.call_count, 1)

    def test_one_danish_record_invalidates_a_complete_day(self):
        start = datetime(2024, 1, 16, 23, tzinfo=timezone.utc)
        rows = [dict(PriceArea="DE", HourUTC=(start + timedelta(hours=i)).isoformat(),
                     SpotPriceEUR=0.0) for i in range(24)]
        day = inputs.PRICE_DAYS[0]
        data = dict(total=24, records=rows)
        self.assertEqual(inputs.check_day(json.dumps(data), day)["observed_price_areas"], ["DE"])
        rows[-1]["PriceArea"] = "DK1"
        with self.assertRaisesRegex(ValueError, "zone"):
            inputs.check_day(json.dumps(data), day)


if __name__ == "__main__":
    unittest.main()
