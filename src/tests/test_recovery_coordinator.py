"""Handcrafted fixtures and fake clocks/optimizers only; no native backend."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.abc
import json
from types import SimpleNamespace
import sys

import pytest

from egglab import native_pathflow as pf
from egglab import native_recharge as nr
from egglab.recovery_coordinator import (
    CompletionAllowance, DirectoryStorage, Schedule, coordinate, native_limits,
)
from egglab.recovery_lift import lift_plan


# Hand-derived from the fixture: operations 7, linear charge 2*15, and
# quadratic charge b*15**2/2. b is the stored binary float .2, not decimal 1/5.
# Keep exact string equality so bill-retention checks cannot hide rounding drift.
EXPECTED_BILL_EXACT = str(Fraction(7) + 2*15 + Fraction(.2)*225/2)


@pytest.fixture(autouse=True)
def forbid_backend_import():
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in ('mip', 'gurobipy'):
                raise AssertionError('Native backend forbidden in coordinator self-test')
    guard = Guard()
    sys.meta_path.insert(0, guard)
    yield
    sys.meta_path.remove(guard)


@pytest.fixture
def physical():
    trip = nr.Trip('A', 0, 60, 'D', 'D', 15.)
    out = nr.Movement('out', 'pullout', None, 'A', (nr.Leg('D', 'D', 0, 0, 0.),))
    home = nr.Movement('home', 'pullin', 'A', None, (nr.Leg('D', 'D', 60, 60, 0.),))
    source = nr.NativeCase('source', (trip,), (out, home),
                           (nr.Resource(0, 60, 0., 0., 0), nr.Resource(60, 120, 30., 30.)),
                           (0, 60, 120), 'D', 1, 20., 1., 0, 120, 7.)
    extra = nr.Movement('extra', 'pullin', 'A', None, (nr.Leg('D', 'D', 60, 75, 0.),))
    full = replace(source, name='full', movements=(extra, home, out))
    plan = {'schema':nr.SCHEMA, 'case_identity':source.identity(),
            'vehicles':[{'vehicle':0, 'trips':['A'], 'movements':['out', 'home']}],
            'charges':[{'vehicle':0, 'movement':'home', 'connector':0,
                        'start_min':60., 'end_min':90., 'grid_kwh':15.}],
            'load':[0., 15.], 'ops_cost':7., 'raw_solver_load':[999.]}
    return source, full, plan


class Clock:
    def __init__(self, now=0.):
        self.now = now

    def __call__(self):
        return self.now


class MemoryStorage:
    def __init__(self, clock, save_seconds=0., serialize_seconds=0., fail_save=False):
        self.clock = clock
        self.save_seconds = save_seconds
        self.serialize_seconds = serialize_seconds
        self.fail_save = fail_save
        self.witness = None
        self.result = None

    def save_fallback(self, witness):
        self.clock.now += self.save_seconds
        if self.fail_save:
            raise OSError('injected fallback fsync failure')
        self.witness = deepcopy(witness)
        return {'sha256':nr.digest(witness)}

    def materialize(self, result, *, schedule, clock):
        self.result = result
        self.clock.now += self.serialize_seconds
        return {'finished_monotonic':clock(), 'elapsed_s':clock()-schedule.parent_monotonic,
                'censored':clock() > schedule.deadline}


def run(physical, planner, clock=None, storage=None, **kwargs):
    source, full, _ = physical
    clock = Clock() if clock is None else clock
    storage = MemoryStorage(clock) if storage is None else storage
    return coordinate(source, full, [1., 2.], [0., .2], parent_monotonic=0., deadline=30.,
                      clock=clock, storage=storage, planner=planner, **kwargs)


def test_durable_lift_before_warm_full_and_changed_tariff(physical):
    source, full, plan = physical
    clock = Clock(4.)  # Interpreter/import/loading already consumed four seconds.
    store = MemoryStorage(clock, save_seconds=1.)
    calls = []

    def planner(case, a, b, budget, record, **kw):
        calls.append((case, budget, kw))
        if case is source:
            clock.now = 11.
            return {'plan':plan, 'lower':10**9, 'status':'certified'}
        assert store.witness is not None
        assert store.witness['true_bill_exact'] == '67'
        assert kw['start_plan'] == store.witness['plan']
        assert kw['start_case'] is full
        assert kw['deadline'] == 25.
        assert kw['completion'] is True
        assert budget.wall_seconds == 13.  # Save completed at12; handoff remains25, not a fresh budget.
        return {'status':'search_failed'}

    result = coordinate(source, full, [0., 4.], [0., 0.], parent_monotonic=0., deadline=30.,
                        clock=clock, storage=store, planner=planner)['result']
    assert calls[0][1].wall_seconds == 9.
    assert calls[0][2]['deadline'] == 13.
    assert result['restricted_prefix_lower'] == 10**9
    assert result['global_lower_bound'] is None
    assert result['selected']['true_bill'] == 67.
    assert result['mode'] == 'warm_full'
    assert result['fallback']['binary_start_spec'] == [
        {'movement_id':'extra', 'value':0}, {'movement_id':'home', 'value':1},
        {'movement_id':'out', 'value':1}]
    assert 'raw_solver_load' not in result['fallback']['plan']


@pytest.mark.parametrize('prefix_failure', ['exception', 'no_incumbent', 'bad_replay'])
def test_no_prefix_witness_cold_full_actual_remainder(physical, prefix_failure):
    source, full, plan = physical
    clock = Clock()
    calls = []

    def planner(case, a, b, budget, record, **kw):
        calls.append(kw)
        if case is source:
            clock.now = 12.
            if prefix_failure == 'exception':
                raise RuntimeError('extraction/completion failed')
            if prefix_failure == 'bad_replay':
                bad = deepcopy(plan)
                bad['charges'][0]['grid_kwh'] = 0.
                return {'plan':bad}
            return {'status':'NO_SOLUTION_FOUND'}
        assert case is full
        assert kw['start_plan'] is None and kw['start_case'] is None
        assert budget.wall_seconds == 13.
        assert budget.phase_seconds == 10.
        return {'status':'unresolved'}

    result = run(physical, planner, clock)['result']
    assert len(calls) == 2
    assert result['mode'] == 'cold_full_no_prefix_witness'
    assert result['selected'] is None and result['global_lower_bound'] is None


@pytest.mark.parametrize('failure', ['exception', 'start_rejected', 'start_unknown', 'timeout',
                                     'no_incumbent', 'bad_replay', 'infeasible'])
def test_admitted_fallback_survives_every_later_failure(physical, failure):
    source, full, plan = physical

    def planner(case, a, b, budget, record, **kw):
        if case is source:
            return {'plan':plan, 'lower':1e12}
        # A failing/mutating solver cannot corrupt the retained physical witness.
        kw['start_plan']['charges'][0]['grid_kwh'] = 0.
        if failure in ('exception', 'timeout'):
            raise (TimeoutError if failure == 'timeout' else RuntimeError)('injected')
        if failure == 'bad_replay':
            return {'plan':kw['start_plan'], 'lower':1e15, 'status':'certified'}
        return {'status':'infeasible' if failure == 'infeasible' else 'unresolved',
                'recovery':{'solver_start_status':failure}, 'upper':0., 'lower':1e15}

    result = run(physical, planner)['result']
    assert result['fallback']['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert result['selected']['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert result['global_lower_bound'] is None
    assert result['status'] == ('model_replay_contradiction' if failure == 'infeasible' else 'feasible')


@pytest.mark.parametrize('time_at_full_gate', [24., 27., 31.])
def test_lift_and_durable_save_costs_cannot_reopen_full_gate(physical, time_at_full_gate):
    source, _, plan = physical
    clock = Clock()
    store = MemoryStorage(clock, save_seconds=time_at_full_gate-11.)

    def planner(case, *args, **kw):
        assert case is source
        clock.now = 11.
        return {'plan':plan}

    outcome = run(physical, planner, clock, store)
    assert outcome['result']['selected'] is None and outcome['result']['fallback'] is None
    assert store.witness is not None  # Late durable evidence exists but was never admitted.
    assert outcome['result']['full_status'] is None
    assert outcome['completion']['elapsed_s'] == time_at_full_gate
    assert outcome['censored'] is (time_at_full_gate > 30.)


def test_failed_durability_blocks_full_and_is_visible(physical):
    source, _, plan = physical
    clock = Clock()
    store = MemoryStorage(clock, fail_save=True)

    def planner(case, *args, **kw):
        assert case is source
        return {'plan':plan}

    result = run(physical, planner, clock, store)['result']
    assert result['status'] == 'storage_failed'
    assert result['selected'] is None and result['fallback'] is None
    assert result['fallback_artifact'] is None
    assert result['full_status'] is None


def test_expired_import_loading_no_solver_and_initial_fallback(physical):
    source, full, plan = physical
    lifted = lift_plan(source, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    outcome = run(physical, lambda *a, **k: pytest.fail('No planner after gate'),
                  Clock(28.), physical_fallback=lifted)
    assert outcome['result']['selected']['true_bill'] == 59.5
    assert outcome['completion']['elapsed_s'] == 28.
    assert outcome['result']['events'][-1]['event'] == 'planner_gate_closed'


def test_late_prefix_replay_not_admitted_and_cold_gate_remains_closed(physical):
    _, _, plan = physical
    clock = Clock()

    def planner(*args, **kw):
        clock.now = 25.
        return {'plan':plan}

    result = run(physical, planner, clock)['result']
    assert result['fallback'] is None and result['full_status'] is None
    assert result['failures'][0]['error_type'] == 'TimeoutError'


def test_fail_closed_resource_or_parent_gate(physical):
    def dead_parent():
        raise OSError('parent disappeared or monitor unavailable')
    outcome = run(physical, lambda *a, **k: pytest.fail('gate must prevent dispatch'),
                  allowed=dead_parent)
    assert outcome['result']['selected'] is None
    assert all(row['stage'] == 'dispatch_gate' for row in outcome['result']['failures'])


def test_shared_native_integer_and_completion_caps_restore_on_failure(monkeypatch):
    clock = Clock(10.)
    calls, events = [], []
    allowance = CompletionAllowance()
    integer = {'x':[SimpleNamespace(lb=0., ub=1.)]}
    fixed = {'x':[SimpleNamespace(lb=1., ub=1.)]}

    def native(built, budget, deadline):
        calls.append((built, budget.phase_seconds, deadline))
        clock.now += budget.phase_seconds
        return {'status':'FEASIBLE'}

    monkeypatch.setattr(pf, '_optimize_once', native)
    with native_limits(integer_end=12., planner_end=15., allowance=allowance,
                       clock=clock, allowed=lambda: True, events=events):
        pf._optimize_once(integer, pf.Budget(), 30.)
        assert calls[-1][1:] == (2., 12.)
        with pytest.raises(TimeoutError):
            pf._optimize_once(integer, pf.Budget(), 30.)
        pf._optimize_once(fixed, replace(pf.Budget(), phase_seconds=2.), 30.)
        assert calls[-1][1:] == (2., 15.)
    assert pf._optimize_once is native
    assert allowance.spent == 2.
    clock.now = 20.
    with pytest.raises(TimeoutError):
        with native_limits(integer_end=24., planner_end=27., allowance=allowance,
                           clock=clock, allowed=lambda: True, events=events):
            pf._optimize_once(fixed, pf.Budget(), 30.)
            assert calls[-1][1:] == (1., 21.)
            pf._optimize_once(fixed, pf.Budget(), 30.)
    assert allowance.spent == 3.
    assert pf._optimize_once is native
    assert len(calls) == 3


def test_completion_exception_charges_elapsed_and_hook_restores(monkeypatch):
    clock = Clock()
    allowance = CompletionAllowance()

    def fail(*args):
        clock.now += 1.25
        raise RuntimeError('native completion failed')

    monkeypatch.setattr(pf, '_optimize_once', fail)
    with pytest.raises(RuntimeError):
        with native_limits(integer_end=12., planner_end=15., allowance=allowance,
                           clock=clock, allowed=lambda: True, events=[]):
            pf._optimize_once({'x':[SimpleNamespace(lb=0, ub=0)]}, pf.Budget(), 15.)
    assert allowance.spent == 1.25
    assert pf._optimize_once is fail


def test_real_planner_api_uses_shared_hook_and_attempts_completion(physical, monkeypatch):
    source, full, plan = physical
    clock = Clock(9.)
    calls = []

    def build(case, backend):
        return {'x':[SimpleNamespace(lb=0, ub=1)]}

    def native(built, budget, deadline):
        calls.append((budget.phase_seconds, deadline))
        clock.now += budget.phase_seconds
        return {'status':'FEASIBLE', 'incumbent':37., 'lower_bound':30.}

    def candidate(case, built, budget, deadline, stats, completion, record, index, objective):
        assert completion is True
        for var in built['x']:
            var.lb = var.ub = 1
        # Real planner -> candidate boundary -> native cap; no backend import.
        pf._optimize_once(built, replace(budget, phase_seconds=1.), deadline)
        raise ValueError('later physical extraction failed')

    monkeypatch.setattr(pf.time, 'monotonic', clock)
    monkeypatch.setattr(pf, 'build_feasible_model', build)
    monkeypatch.setattr(pf, 'attach_objective', lambda *a: None)
    monkeypatch.setattr(pf, 'capture_incumbent', lambda *a: {})
    monkeypatch.setattr(pf, '_optimize_once', native)
    monkeypatch.setattr(pf, '_candidate', candidate)
    outcome = coordinate(source, full, [1.,2.], [0.,.2], parent_monotonic=0., deadline=30.,
                         storage=MemoryStorage(clock), clock=clock,
                         budget=replace(pf.Budget(), max_rounds=1))
    assert calls[0] == (1., 10.)
    assert calls[1] == (1., 13.)
    assert outcome['result']['completion_spent_s'] > 0.
    assert pf._optimize_once is native


def admitted_full_result(full, plan, lower=30.):
    result_plan = lift_plan(full, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    result_plan['replay'] = nr.replay_native(full, result_plan)
    result_plan['raw_solver_load'] = [0., 15.]
    # Tangent envelope at origin is 7 + 2*15 = 37; physical true bill is 59.5.
    row = {'stats':{'status':'FEASIBLE', 'incumbent':37., 'lower_bound':lower},
           'tangents':[[[1.,0.]], [[2.,0.]]], 'plan':result_plan,
           'lower':lower-pf.BOUND_GUARD, 'upper':59.5+pf.BOUND_GUARD}
    return {'case_identity':full.identity(), 'formulation':pf.FORMULATION,
            'native_matrix':pf.NATIVE_MATRIX, 'status':'bounded', 'plan':result_plan,
            'rounds':[row], 'lower':lower-pf.BOUND_GUARD}


def test_only_unrestricted_guarded_mip_lower_survives(physical):
    source, full, plan = physical
    full_plan = lift_plan(source, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    native = admitted_full_result(full, full_plan)
    native['plan']['completion_stats'] = {'incumbent':37., 'lower_bound':10**12}
    native['rounds'][0]['plan']['completion_stats'] = native['plan']['completion_stats']

    def planner(case, *args, **kw):
        return {'plan':plan, 'lower':10**15} if case is source else native

    result = run(physical, planner)['result']
    assert result['global_lower_bound'] == 30.-pf.BOUND_GUARD
    assert result['bound_provenance'][0]['raw_lower_bound'] == 30.
    assert result['bound_provenance'][0]['guard'] == pf.BOUND_GUARD
    assert result['selected']['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert result['status'] == 'bounded'


def test_fallback_objective_not_overwritten_by_later_solver_objective(physical):
    source, full, plan = physical
    full_plan = lift_plan(source, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    native = admitted_full_result(full, full_plan)
    native['upper'] = 30.
    native['rounds'][0]['stats']['incumbent'] = 30.  # Does not match raw envelope 37.

    def planner(case, *args, **kw):
        return {'plan':plan} if case is source else native

    result = run(physical, planner)['result']
    assert result['selected']['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert result['global_lower_bound'] is None
    assert result['status'] == 'feasible'
    assert result['failures'][-1]['stage'] == 'full'


def test_directory_materialization_hash_endpoint_and_cleanup_independence(tmp_path):
    clock = Clock(29.)
    store = DirectoryStorage(tmp_path)
    receipt = store.materialize({'status':'failure'}, schedule=Schedule(0.,30.), clock=clock)
    raw = (tmp_path/'result.json').read_bytes()
    assert receipt['result_sha256'] == hashlib.sha256(raw).hexdigest()
    assert receipt['finished_monotonic'] == 29.
    clock.now = 100.  # Cleanup cannot alter an already captured materialization endpoint.
    assert receipt['elapsed_s'] == 29.
    assert json.loads((tmp_path/'completion.json').read_text())['elapsed_s'] == 29.
    with pytest.raises(FileExistsError):
        store.materialize({}, schedule=Schedule(0.,30.), clock=clock)


def test_late_serialization_is_censored_and_failure_still_charged(physical):
    clock = Clock(21.)
    store = MemoryStorage(clock, serialize_seconds=10.)

    def planner(*args, **kw):
        raise RuntimeError('failed native work')

    outcome = run(physical, planner, clock, store)
    assert outcome['censored'] is True
    assert outcome['completion']['elapsed_s'] == 31.
    assert outcome['result']['failures'][-1]['error_type'] == 'RuntimeError'


def test_invalid_clock_rejected():
    for anchor, deadline in [(0.,31.), (float('nan'),30.), (False,30.)]:
        with pytest.raises(ValueError):
            Schedule(anchor, deadline)


def test_nested_optimizer_scope_rejected_without_losing_outer_hook(monkeypatch):
    clock = Clock()
    original = lambda *a: {'status':'FEASIBLE'}
    monkeypatch.setattr(pf, '_optimize_once', original)
    with native_limits(integer_end=12., planner_end=15., allowance=CompletionAllowance(),
                       clock=clock, allowed=lambda: True, events=[]):
        outer = pf._optimize_once
        with pytest.raises(RuntimeError, match='serialized'):
            with native_limits(integer_end=24., planner_end=27., allowance=CompletionAllowance(),
                               clock=clock, allowed=lambda: True, events=[]):
                pytest.fail('Nested global hook must not be installed')
        assert pf._optimize_once is outer
    assert pf._optimize_once is original


def test_invalid_initial_fallback_rejected_then_cold_full(physical):
    source, full, plan = physical
    invalid = lift_plan(source, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    invalid['charges'][0]['grid_kwh'] = 0.
    calls = []

    def planner(case, *args, **kw):
        calls.append(case)
        assert kw['start_plan'] is None
        return {'status':'unresolved'}

    result = run(physical, planner, physical_fallback=invalid)['result']
    assert calls == [full]
    assert result['fallback'] is None and result['selected'] is None
    assert result['failures'][0]['stage'] == 'initial_fallback'


def test_more_expensive_full_witness_does_not_replace_prefix_bill(physical):
    source, full, plan = physical
    source = replace(source, deadhead_cost_per_min=1.)
    full = replace(full, deadhead_cost_per_min=1.)
    plan = deepcopy(plan)
    plan['case_identity'] = source.identity()
    alternative = lift_plan(source, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    alternative['vehicles'][0]['movements'] = ['out', 'extra']
    alternative['charges'][0].update(movement='extra', start_min=75., end_min=105.)
    alternative['ops_cost'] = 22.

    def planner(case, *args, **kw):
        return {'plan':plan} if case is source else {'plan':alternative, 'upper':74.5}

    outcome = coordinate(source, full, [1.,2.], [0.,.2], parent_monotonic=0., deadline=30.,
                         storage=MemoryStorage(Clock()), clock=Clock(), planner=planner)
    assert outcome['result']['selected']['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert outcome['result']['selected']['provenance']['selected_movement_ids'] == ['out', 'home']


def test_prefix_save_just_past_15_retains_unadmitted_evidence_and_stops_full(physical):
    source, _, plan = physical
    clock = Clock()
    store = MemoryStorage(clock, save_seconds=5.)

    def planner(case, *args, **kw):
        assert case is source
        clock.now = 11.
        return {'plan':plan}

    result = run(physical, planner, clock, store)['result']
    assert clock.now == 16.
    assert store.witness['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert result['selected'] is None and result['fallback'] is None
    assert result['fallback_artifact'] is None
    assert any(event['event']=='rejected_durable_witness' for event in result['events'])
    assert result['dispatch_stopped'] is True
    assert result['full_dispatched'] is False
    assert result['failures'][-1]['stage'] == 'prefix_cutoff'


def test_loading_past_prefix_gate_still_allows_cold_full(physical):
    _, full, _ = physical
    clock = Clock(16.)

    def planner(case, a, b, budget, record, **kw):
        assert case is full
        assert budget.wall_seconds == 9.
        assert kw['start_plan'] is None
        return {'status':'unresolved'}

    result = run(physical, planner, clock)['result']
    assert result['full_dispatched'] is True
    assert result['dispatch_stopped'] is False
    assert result['mode'] == 'cold_full_no_prefix_witness'


def test_slow_full_bound_replay_cannot_import_late_lower(physical, monkeypatch):
    source, full, plan = physical
    full_plan = lift_plan(source, full, plan, a=[1.,2.], b=[0.,.2])['plan']
    native = admitted_full_result(full, full_plan)
    clock = Clock()
    original = pf._candidate_score

    def slow_admission(*args):
        value = original(*args)
        clock.now = 28.
        return value

    monkeypatch.setattr(pf, '_candidate_score', slow_admission)

    def planner(case, *args, **kw):
        return {'plan':plan} if case is source else native

    result = run(physical, planner, clock)['result']
    assert result['global_lower_bound'] is None
    assert result['selected']['true_bill_exact'] == EXPECTED_BILL_EXACT
    assert result['failures'][-1]['error_type'] == 'TimeoutError'
    assert 'bound admission' in result['failures'][-1]['error']


def test_nonfinite_native_diagnostics_tagged_but_physical_json_strict(physical, tmp_path):
    source, _, plan = physical
    clock = Clock()
    store = DirectoryStorage(tmp_path)

    def planner(case, a, b, budget, record, **kw):
        record({'event':'native_test', 'nested':{'bound':float('inf'),
                                               'other':[float('-inf'),float('nan')]}})
        return {'plan':plan, 'lower':float('-inf')} if case is source else {'status':'unresolved'}

    outcome = run(physical, planner, clock, store)
    assert outcome['censored'] is False
    result = json.loads((tmp_path/'result.json').read_text())
    event = next(row for row in result['events'] if row['event'] == 'native_test')
    assert event['nested']['bound'] == {'nonfinite_float':'positive_infinity'}
    assert event['nested']['other'] == [{'nonfinite_float':'negative_infinity'},
                                        {'nonfinite_float':'nan'}]
    assert result['restricted_prefix_lower'] is None
    assert result['restricted_prefix_lower_diagnostic'] == {'nonfinite_float':'negative_infinity'}
    assert result['selected']['true_bill'] == 59.5
    with pytest.raises(ValueError):
        store.save_fallback({'invalid_physical_number':float('inf')})


def test_slow_gate_check_cannot_start_native_after_integer_cutoff(monkeypatch):
    clock = Clock(11.)
    monkeypatch.setattr(pf, '_optimize_once', lambda *a: pytest.fail('late native call'))

    def gate():
        clock.now = 12.
        return True

    with native_limits(integer_end=12., planner_end=15., allowance=CompletionAllowance(),
                       clock=clock, allowed=gate, events=[]):
        with pytest.raises(TimeoutError):
            pf._optimize_once({'x':[SimpleNamespace(lb=0, ub=1)]}, pf.Budget(), 15.)
