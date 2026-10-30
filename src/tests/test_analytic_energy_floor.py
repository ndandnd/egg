"""Focused pure checks for the opt-in ideal energy-floor reporting baseline."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from egglab.analytic_energy_floor import (  # noqa: E402
    PINNED, UnsupportedBaseline, _lower_decimal, evaluate,
)
from experiments.computational_benchmark_report import (  # noqa: E402
    outward_decimal, with_analytic_energy_floor,
)


class AnalyticBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(REPO / "research-20260928/computational-results/attempt1/scientific_evidence.zip") as z:
            cls.frozen = json.loads(z.read("frozen.json"))
        cls.screen = json.loads((REPO / "research-20260928/computational-results/attempt1/analysis.json").read_text())

    def public(self, depot="public_depot15", state=0):
        item = self.frozen["cases"][depot]
        return deepcopy(item["case"]), item["case_identity"], deepcopy(item["markets"][state])

    def test_reviewed_values_and_price_only_change(self):
        expected = {
            ("public_depot15", 0): "424.365880667204",
            ("public_depot15", 1): "418.965880667204",
            ("public_depot16", 0): "435.674556453752",
            ("public_depot16", 1): "430.274556453752",
        }
        for key, decimal_prefix in expected.items():
            case, identity, market = self.public(*key)
            result = evaluate(case, identity, market, repo=REPO)
            self.assertTrue(str(result["ch_lower_decimal"]).startswith(decimal_prefix))
            self.assertEqual(result["scope"], "ideal_stored_input_CH_lower_only")
        case, identity, market = self.public()
        old = Fraction(evaluate(case, identity, market, repo=REPO)["ch_lower_exact"])
        market["a"] = [0.21] * 30
        new = Fraction(evaluate(case, identity, market, repo=REPO)["ch_lower_exact"])
        self.assertGreater(new, old)

    def test_reject_scope_and_bad_markets(self):
        case, identity, market = self.public()
        changed = deepcopy(case)
        changed["battery_kwh"] = 401.0
        for physical, case_id, prices in (
            (changed, identity, market),
            (case, "0" * 64, market),
        ):
            with self.assertRaises(UnsupportedBaseline):
                evaluate(physical, case_id, prices, repo=REPO)
        variants = []
        wrong = deepcopy(market); wrong["b"][0] = -0.1; variants.append(wrong)
        wrong = deepcopy(market); wrong["b"][0] = 0; variants.append(wrong)
        wrong = deepcopy(market); wrong["b"][0] *= 2; variants.append(wrong)
        wrong = deepcopy(market); wrong["a"][0] = -0.1; variants.append(wrong)
        wrong = deepcopy(market); wrong["a"] = [1000.0] + [0.0] * 29; variants.append(wrong)
        wrong = deepcopy(market); wrong["a"] = [1000.0] * 30; variants.append(wrong)
        wrong = deepcopy(market); wrong["a"].pop(); variants.append(wrong)
        wrong = deepcopy(market); wrong["a"][0] = 1 << 2048; variants.append(wrong)
        for prices in variants:
            with self.assertRaises(UnsupportedBaseline):
                evaluate(case, identity, prices, repo=REPO)

    def test_stale_certificate_rejected(self):
        case, identity, market = self.public()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative, _ in PINNED.values():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / relative, target)
            target = root / PINNED["flow_summary"][0]
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(UnsupportedBaseline, "stale or changed"):
                evaluate(case, identity, market, repo=root)

    def test_opt_in_keeps_native_rows_and_failures(self):
        original = {"rows": deepcopy(self.screen["rows"]), "scope": "existing",
                    "supervisor_integrity_ok": self.screen["supervisor_integrity_ok"]}
        encoded = json.dumps(original["rows"], sort_keys=True)
        augmented = with_analytic_energy_floor(original, self.frozen, repo=REPO)
        self.assertEqual(json.dumps(augmented["rows"], sort_keys=True), encoded)
        self.assertNotIn("analytic_energy_floor_baseline", original)
        appendix = augmented["analytic_energy_floor_baseline"]
        self.assertFalse(appendix["native_certification"])
        self.assertEqual(appendix["cases"]["synthetic_cyclic"]["status"], "unavailable")
        supported = appendix["cases"]["public_depot15"]["1"]
        self.assertEqual(supported["ideal_ch_lower"]["status"], "supported")
        self.assertEqual(supported["conditional_mixed_enclosures"]["cold_hull"]["status"],
                         "conditional_mixed_enclosure")
        self.assertEqual(supported["conditional_mixed_enclosures"]["retained_hull"]["status"],
                         "unavailable")

        failed = deepcopy(original)
        row = next(r for r in failed["rows"] if (r["case"], r["state"], r["stage"]) ==
                   ("public_depot15", 1, "cold_hull"))
        row["outcome"], row["complete_evidence"] = "failed", False
        checked = with_analytic_energy_floor(failed, self.frozen, repo=REPO)
        self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                         ["conditional_mixed_enclosures"]["cold_hull"]["status"], "unavailable")
        self.assertEqual(row["outcome"], "failed")

        for integrity in (False, None, "missing"):
            drifted = deepcopy(original)
            if integrity == "missing":
                del drifted["supervisor_integrity_ok"]
            else:
                drifted["supervisor_integrity_ok"] = integrity
            checked = with_analytic_energy_floor(drifted, self.frozen, repo=REPO)
            self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                             ["ideal_ch_lower"]["status"], "supported")
            self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                             ["conditional_mixed_enclosures"]["cold_hull"]["status"], "unavailable")

        unknown = deepcopy(original)
        row = next(r for r in unknown["rows"] if (r["case"], r["state"], r["stage"]) ==
                   ("public_depot15", 1, "cold_hull"))
        row["outcome"] = "new_unreviewed_state"
        checked = with_analytic_energy_floor(unknown, self.frozen, repo=REPO)
        self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                         ["conditional_mixed_enclosures"]["cold_hull"]["status"], "unavailable")

        inverted = deepcopy(original)
        row = next(r for r in inverted["rows"] if (r["case"], r["state"], r["stage"]) ==
                   ("public_depot15", 1, "planner"))
        row["upper_exact"] = "1"
        checked = with_analytic_energy_floor(inverted, self.frozen, repo=REPO)
        self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                         ["conditional_mixed_enclosures"]["cold_hull"]["status"],
                         "inconsistent_unavailable")

        contradictory = deepcopy(original)
        planner = next(r for r in contradictory["rows"] if (r["case"], r["state"], r["stage"]) ==
                       ("public_depot15", 1, "planner"))
        hull = next(r for r in contradictory["rows"] if (r["case"], r["state"], r["stage"]) ==
                    ("public_depot15", 1, "cold_hull"))
        planner_upper = Fraction(planner["upper_exact"])
        hull["lower_exact"] = str(planner_upper + 1)
        hull["upper_exact"] = str(planner_upper + 2)
        checked = with_analytic_energy_floor(contradictory, self.frozen, repo=REPO)
        self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                         ["conditional_mixed_enclosures"]["cold_hull"]["status"],
                         "inconsistent_unavailable")

        for stage, endpoint in (("planner", "upper_exact"), ("cold_hull", "lower_exact")):
            malformed = deepcopy(original)
            row = next(r for r in malformed["rows"] if (r["case"], r["state"], r["stage"]) ==
                       ("public_depot15", 1, stage))
            row[endpoint] = True
            checked = with_analytic_energy_floor(malformed, self.frozen, repo=REPO)
            self.assertEqual(checked["analytic_energy_floor_baseline"]["cases"]["public_depot15"]["1"]
                             ["conditional_mixed_enclosures"]["cold_hull"]["status"], "unavailable")

    def test_directed_decimal_display(self):
        self.assertEqual(outward_decimal(Fraction("424.365880667204")), "424.3658")
        self.assertEqual(outward_decimal(Fraction("98.36107419350077"), upper=True), "98.3611")
        self.assertEqual(_lower_decimal(Fraction(10 ** 400), digits=2), f"{10 ** 400}.00")


if __name__ == "__main__":
    unittest.main()
