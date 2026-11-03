"""Fraction-arithmetic spot checks for the independent derivation in REVIEW.md."""

from fractions import Fraction as Q


def main() -> None:
    # Gross generator dispatches are (A_early, A_middle, A_terminal) and B.
    examples = {
        0: ((0, 5, 10), (0, 10, 20)),
        5: ((5, 10, 15), (0, 5, 10)),
        10: ((5, 10, 15), (5, 5, 5)),
    }
    incremental = {0: 110, 5: 100, 10: 105}
    for early, (a, b) in examples.items():
        assert tuple(a[t] + b[t] for t in range(3)) == (early, 15, 30 - early)
        assert a[1] - a[0] <= 5 and a[2] - a[1] <= 5
        assert Q(7) * a[0] + 5 * a[1] + a[2] + 6 * b[0] + 5 * b[1] + 5 * b[2] - 75 == incremental[early]

    # Exact global lower cut from p=(57/10,5,5), with ramp rents 13/10
    # on each hourly A ramp and 27/10 on A's terminal capacity.
    p = (Q(57, 10), Q(5), Q(5))
    mu_ramp = Q(13, 10)
    mu_capacity = Q(27, 10)
    intercept = 5 * mu_ramp + 5 * mu_ramp + 15 * mu_capacity
    assert intercept == Q(107, 2)
    assert p[0] + mu_ramp == 7  # A early
    assert p[1] - mu_ramp + mu_ramp == 5  # A middle
    assert p[2] - mu_ramp - mu_capacity == 1  # A terminal
    assert p[0] <= 6 and p[1] == 5 and p[2] == 5  # B
    assert 14 + p[2] * 30 == 7 + p[0] * 10 + p[2] * 20 == 164
    assert 164 - intercept == Q(221, 2)  # hull lower bound
    assert Q(1, 2) * 10 + Q(1, 2) * 0 == 5  # mixture mean early load
    assert Q(1, 2) * 7 + Q(1, 2) * 14 + incremental[5] == Q(221, 2)

    physical = min(7 + incremental[10], 14 + incremental[5])
    assert physical == 112
    assert physical - Q(221, 2) == Q(3, 2)
    assert 7 + 6 * 10 + 5 * 20 - (14 + 5 * 30) == 3  # own-price regret

    # The physical two-bus x=5 plan has a non-singleton generator price set.
    # Its regret falls then rises across s=57/10, attaining 7/2 there.
    selected_early_price = Q(57, 10)
    two_private = 139 + 5 * selected_early_price
    assert two_private - 164 == Q(7, 2)
    assert two_private - (107 + 10 * selected_early_price) == Q(7, 2)
    assert 32 - 5 * Q(3) > Q(7, 2)
    assert 5 * Q(6) - 25 > Q(7, 2)

    # Control with both inter-hour ramps slack has G(x)=90+x on [0,10].
    assert min(7 + 100, 14 + 90) == 104
    assert 14 + 90 == 104  # hull minimum at x=0, gap zero
    print("exact Fraction certificate checks passed")


if __name__ == "__main__":
    main()
