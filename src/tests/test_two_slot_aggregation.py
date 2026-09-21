"""Independent analytic examples for the exploratory rational laboratory."""
from fractions import Fraction as Q
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.two_slot_aggregation import Case, evaluate, shared_capacity_witness


def test_odd_even_scaling_and_distinct_regret_metrics():
    # With zero base prices: F(kE,(N-k)E) = bE^2[N^2+(2k-N)^2]/4.
    for n in range(1, 9):
        for e, b in ((Q(1), Q(1)), (Q(1), Q(1, n)), (Q(1, n), Q(1))):
            row = evaluate(Case('analytic', (e,)*n, (Q(0),)*n, (Q(0),)*n, b=b))
            assert row['zch'] == b*e*e*n*n/4
            assert row['gap'] == (b*e*e/4 if n % 2 else 0)
            assert row['minimum_joint_own_price_regret'] == (b*e*e*(n+1)/2 if n % 2 else 0)
            assert row['minimum_max_individual_unrestricted_regret'] == (b*e*e if n % 2 else 0)


def test_nonzero_menu_cost_has_interior_convexified_solution():
    # h(x)=3x/4 + [x^2+(1-x)^2]/2; minimizer x=1/8, h=31/64.
    row = evaluate(Case('interior', (Q(1),), (Q(3, 4),), (Q(0),)))
    assert row['optimal_early_energy'] == 0
    assert row['convex_early_energy'] == Q(1, 8)
    assert row['zd'] == Q(1, 2)
    assert row['zch'] == Q(31, 64)
    assert row['gap'] == Q(1, 64)
    assert row['fleet_loc_at_ch_price'] == 0
    assert row['supplier_loc_at_ch_price'] == Q(1, 64)


def test_shared_capacity_requires_declared_deviation_sets():
    row = shared_capacity_witness()
    assert row['zd'] == row['zch'] == 3
    assert row['energy_price'] == [1, 3]
    assert row['unrestricted_individual_regrets'] == [2, 0]
    assert row['capacity_priced_individual_regrets'] == [0, 0]
    assert row['residual_capacity_deviation_regrets'] == [0, 0]
    assert row['capacity_rent'] == 2
