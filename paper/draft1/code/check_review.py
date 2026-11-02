"""Targeted referee regressions and an unrestricted assignment baseline."""
from fractions import Fraction as Q
import json
import numpy as np
from scipy.optimize import linear_sum_assignment

import twobatch as tb
from study import load_ops, eligible, r_sorted


def tie_regression():
    instance = tb.Instance([1] * 3, [1] * 3, 1, 3, 6, 1)
    supply = tb.Supply(0, 1, Q(4, 3), 0)
    assert tb.gap(instance, supply) > 0
    assert {e for e, _ in tb.response_set(instance, Q(1))} == {0, 1, 2, 3}
    price = Q(1)
    for expected in [Q(1, 3), Q(1)] * 3:
        choices = tb.response_set(instance, price)
        load = Q(1) if price == 1 else choices[0][0]
        assert any(e == load for e, _ in choices)
        price = (price + supply.g(instance, load)) / 2
        assert price == expected


def generic_matching_cost(a, b, battery, m):
    # Dummy vertices impose exactly m real pairs. The bottom-right block
    # is forbidden. Every real-real edge remains available to the optimizer.
    na, nb = len(a), len(b)
    order = na + nb - m
    costs = np.zeros((order, order))
    costs[:na, :nb] = np.maximum(0, np.add.outer(a, b) - battery)
    costs[na:, nb:] = np.inf
    rows, cols = linear_sum_assignment(costs)
    assert np.count_nonzero((rows < na) & (cols < nb)) == m
    return costs[rows, cols].sum()


def main():
    tie_regression()
    ops, _ = load_ops()
    checks = []
    for battery in (300, 400):
        for op in ops:
            if not eligible(op, battery):
                continue
            a, b = op["a_kwh"], op["b_kwh"]
            thresholds = r_sorted(a, b, battery)
            maximum = min(len(a), len(b))
            for m in (maximum // 2, maximum):
                direct = generic_matching_cost(a, b, battery, m)
                error = abs(float(thresholds[m] - direct))
                assert error <= 1e-7, (op["operator"], battery, m, error)
                checks.append(error)
    print(json.dumps({"status": "PASS", "tie_counterexample": "PASS",
                      "independent_assignment_solves": len(checks),
                      "maximum_absolute_kwh_difference": max(checks)}))


if __name__ == "__main__":
    main()
