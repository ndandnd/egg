"""Pure and explicitly fake-oracle hull qualification; no native solves."""
import copy
from dataclasses import replace
from fractions import Fraction as Q
import importlib.abc
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from egglab import native_hull as nh
from experiments import native_hull_qualification as hq
from experiments import native_recharge_qualification as nq


@pytest.fixture(autouse=True)
def forbid_native_imports():
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in ('mip', 'gurobipy'):
                raise AssertionError('Native optimizer import forbidden in pure tests')
    guard = Guard()
    sys.meta_path.insert(0, guard)
    yield
    sys.meta_path.remove(guard)


def physical(case, fleet, early):
    total = 30/case.efficiency
    if fleet == 1:
        vehicles = [{"vehicle": 0, "trips": ["A", "B"], "movements": ["out_A", "depot_AB", "in_B"]}]
        energy = {(0, "depot_AB", 1): early, (0, "in_B", 3): total-early}
    else:
        vehicles = [{"vehicle": i, "trips": [t], "movements": ["out_"+t, "in_"+t]} for i, t in enumerate(("A", "B"))]
        energy = {(0, "in_A", 1): early, (0, "in_A", 3): 15/case.efficiency-early,
                  (1, "in_B", 3): 15/case.efficiency}
    charges = nh.nr.decode_serial(case, nh.nr.compile_case(case), energy)
    load = [0.0]*4
    for c in charges:
        for t, (a, b) in enumerate(zip(case.market_edges_min, case.market_edges_min[1:])):
            load[t] += c['grid_kwh']*max(0, min(b, c['end_min'])-max(a, c['start_min']))/(c['end_min']-c['start_min'])
    plan = {"schema": nh.nr.SCHEMA, "case_identity": case.identity(), "vehicles": vehicles,
            "charges": charges, "load": load, "ops_cost": fleet*case.vehicle_cost}
    nh.nr.replay_native(case, plan)
    return plan


def supports(case):
    low, high = max(0, 30/case.efficiency-30), min(case.resources[1].per_bus_kw, 15/case.efficiency)
    plans = [physical(case, 2, low), physical(case, 2, high)]
    one = max(low, (30+case.reserve_kwh-case.battery_kwh)/case.efficiency)
    if one <= high:
        plans += [physical(case, 1, one), physical(case, 1, high)]
    return plans


def columns(case):
    return [nh.native_column(case, physical(case, fleet, early), {"kind": "analytical-pure-test"})
            for fleet, early in ((2, 0), (1, 10))]


def fake_master_weights(market, pool):
    # Pure analytical minimization over pool pairs for these one-dimensional
    # controls. This is a fake solver, not evidence about a native LP solve.
    choices = []
    for i, left in enumerate(pool):
        for j, right in enumerate(pool):
            delta = [nh.rational(y)-nh.rational(x) for x, y in zip(left['load'], right['load'])]
            derivative = nh.rational(right['ops_cost'])-nh.rational(left['ops_cost'])+sum(
                ((nh.rational(a)+nh.rational(b)*nh.rational(e))*d
                 for a, b, e, d in zip(market.a, market.b, left['load'], delta)), Q(0))
            curvature = sum((nh.rational(b)*d*d for b, d in zip(market.b, delta)), Q(0))
            weight = min(Q(1), max(Q(0), -derivative/curvature)) if curvature else Q(int(derivative < 0))
            raw = [0.0]*len(pool)
            raw[i] += float(1-weight)
            raw[j] += float(weight)
            loads = [nh.rational(e)+weight*d for e, d in zip(left['load'], delta)]
            cost = nh.rational(left['ops_cost'])+weight*(nh.rational(right['ops_cost'])-nh.rational(left['ops_cost']))+nh.supply(market, loads)
            choices.append((cost, raw))
    return min(choices, key=lambda x: x[0])[1]


def raw_master(market, pool, points, weights):
    rows = nh.tangent_rows(market, points, pool)
    load = [sum(w*c['load'][t] for w, c in zip(weights, pool)) for t in range(len(market.a))]
    epi = [max(r['slope']*v+r['intercept'] for r in cuts) for v, cuts in zip(load, rows)]
    objective = sum(w*c['ops_cost'] for w, c in zip(weights, pool))+sum(epi)
    return {'lambda': weights, 'load': load, 'epigraph': epi, 'tangent_rows': rows,
            'tangent_points': copy.deepcopy(points), 'stats': {'status': 'OPTIMAL', 'n_int': 0,
                'incumbent': objective, 'lower_bound': objective, 'wall_s': 0.0}}


def install_fakes(monkeypatch, pricing_gap=0.0, pricing_status='OPTIMAL'):
    def pricing(case, prices, budget, record=None):
        plans = supports(case)
        values = [p['ops_cost']+sum(x*y for x, y in zip(prices, nh.nr.replay_native(case, p)['load'])) for p in plans]
        index = min(range(len(plans)), key=values.__getitem__)
        stats = {'status': pricing_status, 'incumbent': values[index], 'lower_bound': values[index]-pricing_gap, 'wall_s': 0.0}
        if record:
            record({'event': 'native_start', 'round': 0})
            record({'event': 'native_status', 'round': 0, 'stats': stats})
        lo, hi = nh.nr.admit_bound(stats, values[index])
        return {'case_identity': case.identity(), 'prices': list(prices), 'stats': stats,
                'status': 'certified' if hi-lo <= budget.epsilon else 'bounded',
                'plan': plans[index], 'lower': lo, 'upper': hi}
    def master(case, market, pool, points, budget, deadline, index, record):
        nh.emit(record, {'event': 'master_start', 'call': index, 'tangent_points': points,
                         'column_keys': [c['key'] for c in pool]})
        raw = raw_master(market, pool, points, fake_master_weights(market, pool))
        nh.emit(record, {'event': 'master_status', 'call': index, 'stats': raw['stats']})
        return raw
    monkeypatch.setattr(nh.nr, 'solve_pricing', pricing)
    monkeypatch.setattr(nh, '_master_once', master)


def test_frozen_eight_controls_and_dependency_graph():
    cells = hq.controls()
    assert len(cells) == len({c['id'] for c in cells}) == 8
    assert sum(c['predecessor'] is not None for c in cells) == 2
    assert [c['market'].a[1] for c in cells[:3]] == [4, 4.2, 4]
    assert cells[0]['case'].identity() == cells[1]['case'].identity() == cells[2]['case'].identity()
    assert 'src/egglab/native_recharge.py' in hq.SOURCES
    assert 'src/experiments/native_recharge_qualification.py' in hq.SOURCES
    for cell in cells:
        nh.validate_market(cell['case'], cell['market'])


@pytest.mark.parametrize('prices,expected', [([3, -2], Q(0)), ([5, -2], Q(1)), ([4, -1], None)])
def test_nonnegative_domain_conjugate_including_negative_linear_supply(prices, expected):
    market = nh.Market('domain', (4, -2), (.5, 0))
    assert nh.conjugate(market, prices) == expected
    if expected is None:
        with pytest.raises(ValueError, match='conjugate domain'):
            nh.fenchel_bound(market, prices, 10)


def test_simplex_retains_arbitrarily_tiny_positive_exact_weight():
    weights, correction = nh.simplex([1.0, 1e-300])
    assert weights[1] > 0 and sum(weights) == 1
    assert Q(correction['weights_exact'][1]) > 0
    weights, correction = nh.simplex([-1e-12, 1+1e-12])
    assert weights == [0, 1] and Q(correction['negative_mass_exact']) > 0
    for raw in ([0, 0], [-1e-8, 1], [1.001], [float('nan')], [float('inf')]):
        with pytest.raises(ValueError):
            nh.simplex(raw)


def test_mixture_uses_cost_of_aggregate_not_average_supply_cost():
    case = nq.cyclic_case()
    market = hq.controls()[0]['market']
    pool = columns(case)
    mix = nh.replay_mixture(case, market, pool, [13/40, 27/40])
    assert abs(float(Q(mix['objective_exact']))-7591/80) < 1e-12
    separate = Q(13, 40)*(14+nh.supply(market, pool[0]['load']))+Q(27, 40)*(7+nh.supply(market, pool[1]['load']))
    assert separate > Q(mix['objective_exact'])
    assert sum(map(Q, mix['simplex']['weights_exact'])) == 1
    assert nh.pool_certificate(market, pool, mix, nh.mixture_price(market, mix))['pool_gap'] < 1e-12


def test_tiny_positive_weight_is_not_divided_into_physical_plan():
    case = nq.cyclic_case()
    pool = columns(case)
    mix = nh.replay_mixture(case, hq.controls()[0]['market'], pool, [1, 1e-300])
    assert Q(mix['load_exact'][1]) > 0
    assert mix['replayed_columns'] == 2
    assert pool[1]['plan']['load'][1] == 10


@pytest.mark.parametrize('mutate', [
    lambda c: c.update(physical_identity='wrong'),
    lambda c: c.update(extraction_policy='unknown'),
    lambda c: c['load'].__setitem__(1, 1e-12),
    lambda c: c.update(ops_cost=0),
    lambda c: c['plan']['charges'][0].update(connector=1),
])
def test_column_corruption_fails_closed(mutate):
    case = nq.cyclic_case()
    c = columns(case)[0]
    mutate(c)
    with pytest.raises(ValueError):
        nh.replay_column(case, c)


def test_fenchel_uses_global_pricing_lower_not_incumbent():
    market = hq.controls()[0]['market']
    p = [0, 5.35, 0, 4.65]
    bound = nh.fenchel_bound(market, p, 150)
    assert float(Q(bound['lower_exact'])) < 7591/80-3
    exact = nh.rational(150)-nh.conjugate(market, p)
    assert nh.rational(bound['lower']) <= exact
    assert nh.rational(nh.outward(exact, True)) >= exact


def test_float_tangent_rounding_cannot_raise_lower_line_on_pool_box():
    case = nq.cyclic_case()
    pool = columns(case)
    market = nh.Market('rounding', (.1, -.3, .7, -.9), (.2, .3, .4, .7))
    rows = nh.tangent_rows(market, [[0]*4, [.1, 6.75, .2, 23.25]], pool)
    for t, cuts in enumerate(rows):
        maximum = max(c['load'][t] for c in pool)
        for row in cuts:
            for load in (0.0, maximum/3, maximum):
                line = nh.rational(row['slope'])*nh.rational(load)+nh.rational(row['intercept'])
                true = nh.rational(market.a[t])*nh.rational(load)+nh.rational(market.b[t])*nh.rational(load)**2/2
                assert line <= true


def test_all_eight_fake_controls_certify_and_reset_retained_bounds(monkeypatch):
    install_fakes(monkeypatch)
    previous = {}
    for cell in hq.controls():
        predecessor = copy.deepcopy(previous.get(cell['predecessor']))
        expected = predecessor['state_identity'] if predecessor else None
        if predecessor:
            predecessor['lower'] = 1e300
            predecessor['upper'] = -1e300
            predecessor['lower_certificate'] = {'lower_exact': str(10**300)}
        result = nh.certify(cell['case'], cell['market'], arm=cell['arm'], state_index=cell['state_index'],
                            previous=predecessor, expected_previous=expected)
        assert result['status'] == 'certified'
        assert hq.assess(cell, result)['pass']
        assert result['counts']['seed_requests'] == (0 if predecessor else 1)
        assert 0 <= result['gap'] <= 1e-4
        previous[cell['id']] = result


def test_pricing_feasible_admission_distinct_from_master_optimal_policy(monkeypatch):
    install_fakes(monkeypatch, pricing_status='FEASIBLE')
    cell = hq.controls()[0]
    result = nh.certify(cell['case'], cell['market'])
    assert result['status'] == 'certified'
    pool = columns(cell['case'])
    raw = raw_master(cell['market'], pool, [[0]*4], [.5, .5])
    raw['stats']['status'] = 'FEASIBLE'
    with pytest.raises(ValueError, match='OPTIMAL LP'):
        nh.check_master_primal(pool, raw)


def test_duplicate_with_open_bound_stalls_and_never_declares_exhaustion(monkeypatch):
    install_fakes(monkeypatch, pricing_gap=1)
    cell = hq.controls()[0]
    result = nh.certify(cell['case'], cell['market'])
    assert result['status'] == 'stalled_bounded'
    assert result['gap'] > .99 and result['counts']['pricing_requests'] == 3


def test_retained_import_rejects_changed_physics_or_expected_state(monkeypatch):
    install_fakes(monkeypatch)
    cell = hq.controls()[3]
    previous = nh.certify(cell['case'], cell['market'], arm='retained')
    with pytest.raises(ValueError, match='predecessor'):
        nh.import_pool(replace(cell['case'], reserve_kwh=1), previous, previous['state_identity'], nh.Budget())
    with pytest.raises(ValueError, match='predecessor'):
        nh.import_pool(cell['case'], previous, 'wrong', nh.Budget())
    wrong_arm = copy.deepcopy(previous)
    wrong_arm['arm'] = 'cold'
    with pytest.raises(ValueError, match='predecessor'):
        nh.import_pool(cell['case'], wrong_arm, previous['state_identity'], nh.Budget())
    with pytest.raises(ValueError, match='predecessor'):
        nh.import_pool(cell['case'], previous, previous['state_identity'], nh.Budget(), previous_index=5)


@pytest.mark.parametrize('mutation', [
    lambda r: r['load'].__setitem__(1, r['load'][1]+1),
    lambda r: r['epigraph'].__setitem__(1, r['epigraph'][1]-1),
    lambda r: r['stats'].update(incumbent=r['stats']['incumbent']+1),
    lambda r: r['stats'].update(lower_bound=r['stats']['incumbent']+1),
])
def test_master_primal_and_objective_corruption_is_rejected(mutation):
    cell = hq.controls()[0]
    pool = columns(cell['case'])
    raw = raw_master(cell['market'], pool, [[0]*4], [.5, .5])
    mutation(raw)
    with pytest.raises(ValueError):
        nh.check_master_primal(pool, raw)


def test_master_call_cap_is_cumulative_across_pool_expansions(monkeypatch):
    install_fakes(monkeypatch)
    cell = hq.controls()[0]
    result = nh.certify(cell['case'], cell['market'], nh.Budget(master_calls=1))
    assert result['status'] == 'budget_exhausted'
    assert result['counts']['master_calls'] == 1
    assert result['counts']['pricing_requests'] == 2


def test_pricing_bound_tampering_is_rejected_after_replay(monkeypatch):
    install_fakes(monkeypatch)
    original = nh.nr.solve_pricing
    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        result['lower'] += 1
        return result
    monkeypatch.setattr(nh.nr, 'solve_pricing', corrupt)
    cell = hq.controls()[0]
    with pytest.raises(ValueError, match='enclosure changed'):
        nh.certify(cell['case'], cell['market'])


def test_cumulative_pricing_budget_counts_seed(monkeypatch):
    install_fakes(monkeypatch)
    cell = hq.controls()[0]
    result = nh.certify(cell['case'], cell['market'], nh.Budget(pricing_calls=1))
    assert result['status'] == 'budget_exhausted'
    assert result['counts']['pricing_requests'] == result['counts']['seed_requests'] == 1
    assert result['lower'] <= result['upper']


def test_master_refinement_records_do_not_mutate_solved_tangents(monkeypatch):
    cell = hq.controls()[0]
    pool = columns(cell['case'])
    records, calls = [], []
    def fake(case, market, columns, points, budget, deadline, index, record):
        calls.append(copy.deepcopy(points))
        nh.emit(record, {'event': 'master_start', 'call': index, 'tangent_points': points})
        return raw_master(market, columns, points, [.5, .5] if index == 0 else fake_master_weights(market, columns))
    monkeypatch.setattr(nh, '_master_once', fake)
    points = [[0.0]*4]
    mix, pool_certificate = nh.solve_native_rmp(cell['case'], cell['market'], pool, points, nh.Budget(),
        nh.time.monotonic()+10, {'master_calls': 0}, records.append)
    assert len(calls) == 1 and len(calls[0]) == 1 and len(points) == 2
    assert len(records[0]['tangent_points']) == 1
    assert pool_certificate['pool_gap'] <= 1e-6


@pytest.mark.parametrize('budget', [nh.Budget(threads=2), nh.Budget(wall_seconds=0), nh.Budget(master_calls=0),
    nh.Budget(phase_seconds=float('inf')), nh.Budget(epsilon=float('nan')), nh.Budget(pool_tolerance=1)])
def test_bad_budget_fails_before_oracle(monkeypatch, budget):
    monkeypatch.setattr(nh.nr, 'solve_pricing', lambda *a, **k: pytest.fail('oracle reached'))
    cell = hq.controls()[0]
    with pytest.raises(ValueError):
        nh.certify(cell['case'], cell['market'], budget)


def test_truncated_trace_has_prefix_and_complete_call_ids_are_required(tmp_path):
    good = {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_start'}}
    (tmp_path/'events.jsonl').write_text(json.dumps(good)+'\n{"event":')
    (tmp_path/'result.json').write_text('{"result":')
    events, result, issues = hq.read_evidence(tmp_path)
    assert events == [good] and result is None and len(issues) == 2
    assert not hq.accounting(events)['native_accounting_complete']
    duplicate = [good, good, {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_status', 'stats': {'wall_s': 0}}}]
    assert not hq.accounting(duplicate)['native_accounting_complete']


def test_controller_continues_all_eight_after_truncated_timeout(tmp_path, monkeypatch):
    cells, calls = hq.controls(), []
    monkeypatch.setattr(hq, 'source_hashes', lambda: {'pure': 'fixed'})
    monkeypatch.setattr(nq, 'environment', lambda: {'runtime': 'fake'})
    def fake_run(cmd, **kw):
        cell_id = cmd[cmd.index('--worker')+1]
        folder = Path(cmd[cmd.index('--output')+1])
        calls.append(cell_id)
        start = {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_start'}}
        if len(calls) == 1:
            (folder/'events.jsonl').write_text(json.dumps(start)+'\n{"event":')
            (folder/'result.json').write_text('{"result":')
            raise hq.subprocess.TimeoutExpired(cmd, kw['timeout'])
        end = {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_status', 'stats': {'wall_s': 0}}}
        (folder/'events.jsonl').write_text(json.dumps(start)+'\n'+json.dumps(end)+'\n')
        nq._json(folder/'result.json', {'result': {'status': 'certified'}, 'assessment': {'pass': True}})
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(hq.subprocess, 'run', fake_run)
    assert hq.controller(tmp_path, 'pure-fake-controller') == 1
    summary = json.loads((tmp_path/'summary.json').read_text())
    assert calls == [c['id'] for c in cells] and len(summary['cells']) == 8
    assert len(summary['cells'][0]['evidence_issues']) == 2
    assert all(c['pass'] for c in summary['cells'][1:])


def test_failed_predecessor_blocks_without_oracle(tmp_path, monkeypatch):
    cell = hq.controls()[4]
    folder = tmp_path/cell['id']
    folder.mkdir()
    predecessor = tmp_path/cell['predecessor']
    predecessor.mkdir()
    nq._json(predecessor/'result.json', {'result': {'status': 'budget_exhausted'}, 'assessment': {'pass': False}})
    monkeypatch.setattr(hq, 'source_hashes', lambda: {'pure': 'fixed'})
    monkeypatch.setattr(nh, 'certify', lambda *a, **k: pytest.fail('blocked oracle reached'))
    assert hq.worker(cell['id'], folder, nh.Budget(), {'source_hashes': {'pure': 'fixed'}}) == 3
    result = json.loads((folder/'result.json').read_text())
    assert result['result']['status'] == 'blocked_by_predecessor'


@pytest.mark.parametrize('damage', ['missing', 'malformed', 'failed', 'wrong-cell', 'nonzero',
    'timeout', 'incomplete-trace', 'empty-trace', 'mismatched-count', 'malformed-accounting'])
def test_certified_result_cannot_override_failed_predecessor_receipt(tmp_path, monkeypatch, damage):
    cell = hq.controls()[4]
    folder, predecessor = tmp_path/cell['id'], tmp_path/cell['predecessor']
    folder.mkdir(); predecessor.mkdir()
    events = [
        {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_start'}},
        {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_status', 'stats': {'wall_s': 0.0}}}]
    receipt = {'cell': cell['predecessor'], 'pass': True, 'returncode': 0, 'timeout': False,
               'status': 'certified', 'evidence_issues': [], **hq.accounting(events)}
    if damage == 'failed': receipt['pass'] = False
    if damage == 'wrong-cell': receipt['cell'] = 'other-cell'
    if damage == 'nonzero': receipt['returncode'] = 1
    if damage == 'timeout': receipt['timeout'] = True
    if damage == 'mismatched-count': receipt['native_starts'] += 1
    if damage == 'incomplete-trace': events.pop()
    if damage == 'empty-trace': events = []
    if damage == 'malformed-accounting': events[1]['detail']['stats']['wall_s'] = None
    (predecessor/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    nq._json(predecessor/'result.json', {'result': {'status': 'certified'}, 'assessment': {'pass': True}})
    if damage == 'malformed': (predecessor/'receipt.json').write_text('{"pass":')
    elif damage != 'missing': nq._json(predecessor/'receipt.json', receipt)
    monkeypatch.setattr(hq, 'source_hashes', lambda: {'pure': 'fixed'})
    monkeypatch.setattr(nh, 'certify', lambda *a, **k: pytest.fail('failed predecessor reached oracle'))
    assert hq.worker(cell['id'], folder, nh.Budget(), {'source_hashes': {'pure': 'fixed'}}) == 3
    package = json.loads((folder/'result.json').read_text())
    assert package['result']['status'] == 'blocked_by_predecessor'


def test_admitted_predecessor_requires_matching_complete_receipt(tmp_path):
    events = [
        {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_start'}},
        {'event': 'pricing_native', 'call': 0, 'detail': {'event': 'native_status', 'stats': {'wall_s': 0.0}}}]
    (tmp_path/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    package = {'result': {'status': 'certified'}, 'assessment': {'pass': True}}
    nq._json(tmp_path/'result.json', package)
    nq._json(tmp_path/'receipt.json', {'cell': 'prior', 'pass': True, 'returncode': 0,
        'timeout': False, 'status': 'certified', 'evidence_issues': [], **hq.accounting(events)})
    assert hq.admitted_predecessor(tmp_path, 'prior') == (package, [])


def test_polishing_repairs_repeated_lp_plateau_without_another_native_call(monkeypatch):
    cell = hq.controls()[0]
    pool = columns(cell['case'])
    calls, records = [], []
    def plateau(case, market, cols, points, budget, deadline, index, record):
        calls.append(index)
        return raw_master(market, cols, points, [.3249816894616279, .6750183105383719])
    monkeypatch.setattr(nh, '_master_once', plateau)
    counts = {'master_calls': 0}
    mix, cert = nh.solve_native_rmp(cell['case'], cell['market'], pool, [[0.]*4], nh.Budget(),
        nh.time.monotonic()+10, counts, records.append)
    assert calls == [0] and counts['polish_steps'] == 1
    assert cert['pool_gap'] <= 1e-6 and abs(mix['upper']-7591/80) < 1e-12
    event = next(e for e in records if e['event'] == 'pool_polish_step')
    before, after = Q(event['objective_before_exact']), Q(event['objective_after_exact'])
    gamma, decrease, curvature = map(Q, [event['gamma_exact'], event['directional_decrease_exact'], event['curvature_exact']])
    assert after == before-gamma*decrease+curvature*gamma**2/2 < before
    assert sum(map(Q, event['weights_after_exact'])) == 1
    assert all(Q(w) >= 0 for w in event['weights_after_exact'])


def test_zero_curvature_polishing_moves_full_positive_away_mass():
    c = nq.cyclic_case(); pool = columns(c)
    m = nh.Market('linear',(1,1,1,1),(0,0,0,0))
    mix = nh.replay_mixture(c,m,pool,[.5,.5]); events=[]; counts={}
    result,cert = nh.polish_pool(c,m,pool,mix,nh.Budget(),nh.time.monotonic()+10,counts,events.append)
    step=next(e for e in events if e['event']=='pool_polish_step')
    assert Q(step['curvature_exact'])==0 and Q(step['gamma_exact'])==Q(1,2)
    assert result['simplex']['weights_exact']==['0','1'] and cert['pool_gap']==0


def test_exact_polished_weights_below_float_range_are_preserved_in_json():
    c=nq.cyclic_case(); pool=columns(c); tiny=Q(1,10**1000)
    mix=nh.replay_exact_mixture(c,hq.controls()[0]['market'],pool,[1-tiny,tiny])
    decoded=json.loads(json.dumps(mix,allow_nan=False))
    assert Q(decoded['simplex']['weights_exact'][1])==tiny
    assert Q(decoded['load_exact'][1])==10*tiny>0
    assert decoded['load'][1]==0.0  # display underflows; authoritative exact value survives.
    assert decoded['replayed_columns']==2


def test_polishing_step_cap_preserves_last_exact_feasible_improvement():
    c=nq.cyclic_case(); m=hq.controls()[0]['market']
    pool=columns(c)
    pool.insert(1,nh.native_column(c,physical(c,2,5),{'source':'pure-third-column'}))
    mix=nh.replay_mixture(c,m,pool,[1/3]*3)
    seen=[];events=[];counts={}
    with pytest.raises(nh.LimitReached,match='step budget'):
        nh.polish_pool(c,m,pool,mix,nh.Budget(polish_steps=1),nh.time.monotonic()+10,
                       counts,events.append,seen.append)
    assert counts['polish_steps']==1
    assert Q(seen[-1]['objective_exact'])<Q(mix['objective_exact'])
    assert sum(map(Q,seen[-1]['simplex']['weights_exact']))==1
    assert events[-1]['event']=='pool_polish_finish' and events[-1]['outcome']=='LimitReached'
    assert hq.accounting(events)['polish_accounting_complete']


def test_polishing_bit_budget_fails_instead_of_rounding_weights():
    c=nq.cyclic_case();m=hq.controls()[0]['market'];pool=columns(c)
    mix=nh.replay_mixture(c,m,pool,[.5,.5]);counts={}
    with pytest.raises(nh.LimitReached,match='bit-size'):
        nh.polish_pool(c,m,pool,mix,nh.Budget(rational_bits=8),nh.time.monotonic()+10,counts,None)
    assert counts['polish_steps']==0


def test_polishing_time_budget_fails_closed(monkeypatch):
    c=nq.cyclic_case();m=hq.controls()[0]['market'];pool=columns(c)
    mix=nh.replay_mixture(c,m,pool,[.5,.5]);times=iter([0.,6.,7.]);counts={};events=[]
    monkeypatch.setattr(nh.time,'monotonic',lambda:next(times))
    with pytest.raises(nh.LimitReached,match='time budget'):
        nh.polish_pool(c,m,pool,mix,nh.Budget(polish_seconds=5),100.,counts,events.append)
    assert counts['polish_steps']==0 and counts['polish_wall_s']==7
    assert events[-1]['outcome']=='LimitReached'


def test_state_streams_master_upper_before_inner_budget_failure(monkeypatch):
    install_fakes(monkeypatch)
    polish=nh.polish_pool
    def capped(case,market,cols,mix,budget,deadline,counts,record,consider=None,master_call=0):
        if len(cols)>1:raise nh.LimitReached('pure forced inner cap')
        return polish(case,market,cols,mix,budget,deadline,counts,record,consider,master_call)
    monkeypatch.setattr(nh,'polish_pool',capped)
    cell=hq.controls()[0];result=nh.certify(cell['case'],cell['market'])
    assert result['status']=='budget_exhausted' and result['upper']<95
    assert abs(result['upper']-7591/80)<1e-12
    assert result['upper']>result['lower'] and result['gap']>result['epsilon']


def test_incomplete_polishing_trace_is_not_complete_accounting():
    events=[{'event':'pool_polish_start','master_call':0}]
    assert not hq.accounting(events)['polish_accounting_complete']
    events.append({'event':'pool_polish_finish','master_call':0,'elapsed_s':.1,
                   'steps_completed':1,'checks_completed':0})
    assert not hq.accounting(events)['polish_accounting_complete']


@pytest.mark.parametrize('budget',[nh.Budget(polish_steps=0),nh.Budget(rational_bits=0),
                                  nh.Budget(polish_seconds=float('inf'))])
def test_invalid_polishing_budget_fails(budget):
    with pytest.raises(ValueError,match='policy'):nh.validate_budget(budget)


def test_already_stationary_pool_cannot_qualify_after_polishing_deadline(monkeypatch):
    c=nq.cyclic_case();m=hq.controls()[0]['market'];pool=columns(c)[:1]
    mix=nh.replay_mixture(c,m,pool,[1.]);times=iter([0.,1.,6.,7.,8.]);counts={};seen=[]
    monkeypatch.setattr(nh.time,'monotonic',lambda:next(times,8.))
    with pytest.raises(nh.LimitReached,match='after pool check'):
        nh.polish_pool(c,m,pool,mix,nh.Budget(polish_seconds=5),100.,counts,None,seen.append)
    assert seen and seen[-1]['objective_exact']==mix['objective_exact']
    assert counts['polish_steps']==0


@pytest.mark.parametrize('damage',['wrong-phase','duplicate-step','wrong-step','phase-counts','after-finish','missing-check'])
def test_polishing_accounting_rejects_per_phase_misattribution_and_bad_order(damage):
    events=[{'event':'pool_polish_start','master_call':0,'cumulative_steps':0},
            {'event':'pool_polish_check','master_call':0,'step':0},
            {'event':'pool_polish_step','master_call':0,'step':1},
            {'event':'pool_polish_finish','master_call':0,'steps_completed':1,'checks_completed':1,
             'elapsed_s':.1,'outcome':'LimitReached'}]
    assert hq.accounting(events)['polish_accounting_complete']
    if damage=='wrong-phase':events[2]['master_call']=999
    if damage=='duplicate-step':events.insert(3,copy.deepcopy(events[2]));events[-1]['steps_completed']=2
    if damage=='wrong-step':events[2]['step']=7
    if damage=='phase-counts':events[-1]['steps_completed']=0
    if damage=='after-finish':events[2],events[3]=events[3],events[2]
    if damage=='missing-check':events.pop(1);events[-1]['checks_completed']=0
    assert not hq.accounting(events)['polish_accounting_complete']
