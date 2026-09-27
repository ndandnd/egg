"""Exact assignment certificates versus independent finite enumeration."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as Q
from itertools import permutations, product

import pytest

from egglab import flat_energy_relaxation as er
from experiments.native_recharge_qualification import cyclic_case


def brute(matrix):
    candidates = [sum(matrix[i][j] for i, j in enumerate(p))
                  for p in permutations(range(len(matrix[0])), len(matrix))
                  if all(matrix[i][j] is not None for i, j in enumerate(p))]
    return min(candidates) if candidates else None


def test_all_small_sparse_signed_assignment_matrices():
    # Exhaust all 4^6 two-by-three matrices, including missing and negative arcs.
    for values in product((None, Q(-3, 7), Q(0), Q(5, 3)), repeat=6):
        matrix = [list(values[:3]), list(values[3:])]
        expected = brute(matrix)
        if expected is None:
            with pytest.raises(ValueError, match="No complete"):
                er.exact_assignment(matrix)
        else:
            cert = er.exact_assignment(matrix)
            assert er.verify_assignment(matrix, cert) == expected


def test_larger_augmentations_and_exact_binary_input():
    for n in (1, 3, 4, 5):
        a = [[None if (i + j) % 4 == 0 else Q((i * 7 - j * 3) % 13 - 6, 11)
              for j in range(n + 1)] for i in range(n)]
        assert er.verify_assignment(a, er.exact_assignment(a)) == brute(a)
    assert er.rational(.2) != Q(1, 5)
    assert er.rational(.2) == Q.from_float(.2)


@pytest.mark.parametrize('field,change', [
    ('assignment', [0, 0]), ('assignment', [True, 1]),
    ('assignment', [0, 2]), ('row_potentials', ['-100', '0']),
    ('column_potentials', ['1', '0', '0']),
    ('column_potentials', ['-1', '-1', '-1']), ('objective', '999'),
])
def test_corrupted_certificates_fail(field, change):
    a = [[-5, None, 0], [None, -2, 0]]
    cert = deepcopy(er.exact_assignment(a)); cert[field] = change
    with pytest.raises(ValueError):
        er.verify_assignment(a, cert)


def test_path_cover_reduction_counts_energy_and_fleet_cost_once():
    c = cyclic_case()
    r = er.solve_relaxation(c, 1)
    # Relaxed battery permits the direct arc: 30 service kWh and one bus.
    assert Q(r['lower_exact']) == Q(30 + c.vehicle_cost)
    assert r['used_paths_in_relaxation'] == 1
    assert set(r['selected_movement_ids']) in (
        {'out_A', 'direct_AB', 'in_B'}, {'out_A', 'depot_AB', 'in_B'})
    losses = er.solve_relaxation(replace(c, efficiency=.95), .2)
    assert Q(losses['lower_exact']) == Q(c.vehicle_cost) + Q(.2) * 30 / Q(.95)
    # Removing connections forces both endpoint pairs, including both bus costs.
    split = replace(c, movements=tuple(m for m in c.movements if m.kind in ('pullout', 'pullin')))
    assert Q(er.solve_relaxation(split, 1)['lower_exact']) == 30 + 2 * Q(c.vehicle_cost)


def test_relaxation_does_not_invent_missing_endpoint_or_honor_fleet_cap():
    c = cyclic_case()
    no_out = replace(c, movements=tuple(m for m in c.movements if m.id != 'out_B'))
    with pytest.raises(ValueError, match='pullout and pullin'):
        er.path_cover_problem(no_out, 1)
    split = replace(c, max_vehicles=1,
                    movements=tuple(m for m in c.movements if m.kind in ('pullout', 'pullin')))
    assert er.solve_relaxation(split, 1)['used_paths_in_relaxation'] == 2


def test_parallel_modes_use_cheapest_complete_declared_movement():
    c = cyclic_case()
    modes = tuple(replace(m, legs=tuple(replace(l, energy_kwh=1) for l in m.legs))
                  if m.kind == 'direct' else m for m in c.movements)
    result = er.solve_relaxation(replace(c, movements=modes), 1)
    assert 'depot_AB' in result['selected_movement_ids']
    assert 'direct_AB' not in result['selected_movement_ids']


@pytest.mark.parametrize('bad', [True, float('nan'), float('inf'), '0.2'])
def test_nonfinite_or_untyped_input_rejected(bad):
    with pytest.raises(ValueError):
        er.rational(bad)
