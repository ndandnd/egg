"""Analytical and adversarial controls for the isolated physical adapter."""
import copy
from pathlib import Path
import sys

import mip
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.physical_qualification import fixtures, qualify, replay, validate_grid, solve


@pytest.mark.parametrize('index,d,ch,feasible', [
    (0, 8., 8., 2), (1, 13., 12.2, 2), (2, 13., 13., 1),
    (3, 14., 14., 1), (4, .5, .5, 1), (5, None, None, 0),
    (6, 36., 36., 2), (7, 36.8, 36.8, 2)])
def test_complete_continuous_structure_enclosures(index, d, ch, feasible):
    inst, market, cap = fixtures()[index]
    result = qualify(inst, market, cap)
    assert sum(v['status'] == 'OPTIMAL' for v in result['physical']) == feasible
    if not feasible:
        assert result['status'] == result['ch']['status'] == 'INFEASIBLE'
        assert 'gap_interval' not in result
        return
    assert result['d_lower'] <= d <= result['d_upper']
    assert result['ch']['lower'] <= ch <= result['ch']['upper']
    assert result['gap_interval'][0] <= d-ch <= result['gap_interval'][1]
    assert result['d_upper']-result['d_lower'] < 3e-5
    assert result['ch']['upper']-result['ch']['lower'] < 3e-5
    if index == 3:
        # An aggregate-only capacity row would incorrectly keep CH=12.2.
        assert result['ch']['lower'] > 13.99
    if index == 7:
        assert result['ch']['load'] == pytest.approx([0., 8., 12., 0.], abs=1e-5)


def physical_witness():
    inst, _, _ = fixtures()[1]
    structure = {'sequences': [['t0', 't1']], 'kinds': [['dep']], 'ops_cost': 7.}
    charges = [{'chain': 0, 'edge': 0, 'slot': 1, 'energy': 5.},
               {'chain': 0, 'edge': 0, 'slot': 2, 'energy': 5.}]
    return inst, structure, charges


@pytest.mark.parametrize('mutation', ['coverage', 'negative', 'duplicate', 'outside_window',
                                     'power', 'soc', 'ops', 'capacity', 'terminal'])
def test_independent_replay_rejects_corrupted_physical_evidence(mutation):
    inst, structure, charges = physical_witness()
    assert replay(inst, structure, charges)['load'] == [0., 5., 5., 0.]
    cap = None
    if mutation == 'coverage':
        structure['sequences'][0][1] = 't0'
    elif mutation == 'negative':
        charges[0]['energy'] = -1.
    elif mutation == 'duplicate':
        charges.append(copy.deepcopy(charges[0]))
    elif mutation == 'outside_window':
        charges[0]['slot'] = 0
    elif mutation == 'power':
        charges[0]['energy'] = 11.
    elif mutation == 'soc':
        charges[0]['energy'] = 4.
    elif mutation == 'ops':
        structure['ops_cost'] = 6.
    elif mutation == 'capacity':
        cap = [0., 4., 5., 0.]
    elif mutation == 'terminal':
        inst.soc_end_kwh = 1.
    with pytest.raises(ValueError):
        replay(inst, structure, charges, cap=cap)


def test_unresolved_structure_solve_cannot_be_skipped_as_infeasible(monkeypatch):
    calls = []
    def unfinished(self, **kwargs):
        calls.append(kwargs)
        return mip.OptimizationStatus.FEASIBLE
    monkeypatch.setattr(mip.Model, 'optimize', unfinished)
    inst, market, _ = fixtures()[1]
    _, structure, _ = physical_witness()
    import time
    with pytest.raises(RuntimeError, match='unresolved solver status: FEASIBLE'):
        solve(inst, market, [structure], None, False, time.perf_counter()+5., [])
    assert len(calls) == 1


def test_partial_slot_availability_is_outside_declared_adapter_scope():
    inst, _, _ = fixtures()[0]
    from egglab.instance import Trip
    inst.trips[0] = Trip('t0', 0, 70, 'D', 'D', 15.)
    with pytest.raises(ValueError, match='aligned'):
        validate_grid(inst, None)
