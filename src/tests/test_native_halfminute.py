"""Exact source-time extension checks; no optimizer execution."""
from dataclasses import asdict, replace
from fractions import Fraction
import json
from pathlib import Path

import pytest

from egglab import native_recharge as nr
from experiments import native_recharge_qualification as q


from experiments.native_halfminute_qualification import halve_time, tiny_case, coincidence_case, controls


def test_frozen_integer_controls_are_byte_semantically_unchanged():
    root = Path(__file__).resolve().parents[2]
    saved = json.loads((root/'result/native_recharge/20260927-attempt2/frozen.json').read_text())
    current = [{**c, 'case': asdict(c['case']), 'case_identity': c['case'].identity()} for c in q.controls()]
    assert json.loads(json.dumps(current)) == saved['controls']


@pytest.mark.parametrize('bad', [True, False, -0.5, 0.25, 0.5000000000000001,
    float('nan'), float('inf'), float('-inf'), nr.MAX_TIMESTAMP_MIN+0.5, 10**500])
def test_source_timestamp_rejects_without_rounding_or_overflow(bad):
    assert not nr._timestamp(bad)
    with pytest.raises(ValueError):
        nr.validate_case(replace(q.single_case(), terminal_open_min=bad))


def test_timestamp_exact_representability_ceiling():
    for t in (0, 0.5, 1800, 1800.5, nr.MAX_TIMESTAMP_MIN-0.5, nr.MAX_TIMESTAMP_MIN):
        assert nr._timestamp(t)
        assert Fraction(float(t)) == Fraction(t)
    assert not nr._minute(1.0)


def test_source_times_allow_half_minutes_but_discrete_counts_do_not():
    c = halve_time(q.multileg_case())
    nr.validate_case(c)
    assert c.movements[0].legs[0].arrive_min == 2.5
    for bad in (replace(c, max_vehicles=2.5), replace(c, max_vehicles=2.0),
                replace(c, resources=(replace(c.resources[0], connectors=0.5),)+c.resources[1:])):
        with pytest.raises(ValueError):
            nr.validate_case(bad)
    cy = q.cyclic_case()
    modes = tuple(replace(m, depot_split=1.0) if m.kind == 'depot' else m for m in cy.movements)
    with pytest.raises(ValueError):
        nr.validate_case(replace(cy, movements=modes))


def single_plan(case, start, end, energy):
    loads = [energy*max(0,min(b,end)-max(a,start))/(end-start)
             for a,b in zip(case.market_edges_min,case.market_edges_min[1:])]
    ops = case.vehicle_cost + case.deadhead_cost_per_min*sum(
        l.arrive_min-l.depart_min for m in case.movements for l in m.legs)
    return {'schema':nr.SCHEMA, 'case_identity':case.identity(),
        'vehicles':[{'vehicle':0, 'trips':['A'], 'movements':['out_A','in_A']}],
        'charges':[{'vehicle':0,'movement':'in_A','connector':0,
                    'start_min':start,'end_min':end,'grid_kwh':energy}],
        'load':loads, 'ops_cost':ops}


def test_half_time_double_power_multileg_preserves_energy_and_objective():
    c, h = q.multileg_case(), halve_time(q.multileg_case())
    a = nr.replay_native(c, single_plan(c,75,103,14), [1,1])
    b = nr.replay_native(h, single_plan(h,37.5,51.5,14), [1,1])
    assert a['load'] == b['load'] and a['pricing_objective'] == b['pricing_objective'] == 36
    ca, ch = nr.compile_case(c)['intervals'], nr.compile_case(h)['intervals']
    assert [(i['start']/2,i['end']/2) for i in ca] == [(i['start'],i['end']) for i in ch]
    assert [i['hours']*i['rate_kw'] for i in ca] == [i['hours']*i['rate_kw'] for i in ch]


def test_actual_half_minute_capacity_and_fractional_resource_market_boundaries():
    c = tiny_case()
    grid = nr.compile_case(c)
    assert grid['intervals'][-1]['hours']*grid['intervals'][-1]['rate_kw'] == 0.5
    assert nr.replay_native(c,single_plan(c,0.5,1,0.5),[1,1])['pricing_objective'] == 7.5
    bad = tiny_case(59)
    with pytest.raises(ValueError,match='power'):
        nr.replay_native(bad,single_plan(bad,0.5,1,0.5))


def test_fractional_charge_end_precedes_positive_outbound_energy():
    c = coincidence_case()
    charges = [{'vehicle':0,'movement':mid,'connector':0,'start_min':a,'end_min':b,'grid_kwh':1}
               for mid,a,b in [('depot_AB',0.5,1.5),('in_B',2,2.5)]]
    p = {'schema':nr.SCHEMA,'case_identity':c.identity(),
         'vehicles':[{'vehicle':0,'trips':['A','B'],'movements':['out_A','depot_AB','in_B']}],
         'charges':charges,'load':[0,1,0,1],'ops_cost':7}
    report = nr.replay_native(c,p)
    assert [e['kind'] for e in report['soc_trajectories'][0] if e['time_min']==1.5] == ['charge','movement']
    for key in ('vehicle','connector'):
        p['charges'][0][key] = 0.0
        with pytest.raises(ValueError,match='ownership'):
            nr.replay_native(c,p)
        p['charges'][0][key] = 0


def test_timing_gate_retains_all_old_controls_then_four_new_ones():
    cells = controls()
    assert len(cells) == 19
    assert [c['id'] for c in cells[:15]] == [c['id'] for c in q.controls()]
    assert sum(c['expected_status']=='infeasible' for c in cells) == 4
    for c in cells:
        nr.validate_case(c['case'])
