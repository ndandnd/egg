"""Pure fixed-column proposal tests; no native MIP or hull solver is called."""
from fractions import Fraction
import math
import unittest

from egglab import restricted_qp_proposal as qp


class RestrictedQPProposalTests(unittest.TestCase):
    def test_two_column_interior_optimum(self):
        result = qp.propose([0, 1], [[2], [0]], [0], [1], denominator=1_000_000)
        weights = [Fraction(v) for v in result["weights_exact"]]
        self.assertTrue(result["success"])
        self.assertAlmostEqual(float(weights[0]), .25, delta=2e-6)
        self.assertEqual(sum(weights), 1)
        self.assertEqual(sum(result["integer_units"]), 1_000_000)
        self.assertLess(result["rounded_directional_residual_diagnostic"], 1e-5)
        self.assertIn("no replay", result["scope"])
        self.assertGreaterEqual(result["numeric_seconds"], 0)
        self.assertGreaterEqual(result["rounding_seconds"], 0)

    def test_duplicate_singular_columns_still_return_simplex(self):
        result = qp.propose([1, 1, 0], [[1, 1], [1, 1], [2, 0]],
                            [0, 0], [1, 1], denominator=1000)
        self.assertEqual(sum(Fraction(v) for v in result["weights_exact"]), 1)
        self.assertTrue(all(u >= 0 for u in result["integer_units"]))
        self.assertTrue(math.isfinite(result["rounded_objective_diagnostic"]))

    def test_linear_zero_curvature(self):
        result = qp.propose([2, 1], [[0], [10]], [0], [0], denominator=100)
        self.assertEqual(result["integer_units"], [0, 100])
        self.assertEqual(result["rounded_directional_residual_diagnostic"], 0)

    def test_largest_remainder_rational_rounding(self):
        units, weights = qp._round_simplex([1/3] * 3, 10)
        self.assertEqual(units, [4, 3, 3])
        self.assertEqual(sum(weights), 1)

    def test_invalid_inputs_and_limits(self):
        cases = [([math.nan], [[0]], [0], [1]),
                 ([0], [[math.inf]], [0], [1]),
                 ([0], [[0]], [0], [-1]),
                 ([0, 1], [[0]], [0], [1]),
                 ([0], [[0, 1]], [0], [1])]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                qp.propose(*args)
        with self.assertRaises(ValueError):
            qp.propose([0], [[0]], [0], [0], denominator=0)
        with self.assertRaises(ValueError):
            qp.propose([0], [[0]], [0], [0], maxiter=0)


if __name__ == "__main__":
    unittest.main()
