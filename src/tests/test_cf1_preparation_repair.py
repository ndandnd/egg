"""Affected preparation paths only: symbolic models and fake backend calls."""
import builtins
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

_original_import = builtins.__import__
def _guard(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in preparation checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__ = _guard
try:
    from egglab import constructive_charging as ch
    from egglab import constructive_proposal as provider
    from egglab import recovery_coordinator as rc
    from experiments import comparison_native_worker as worker
    from test_constructive_controls import native, chain_case, Clock, Var
    from test_comparison_native_adapter import instrument
finally:
    builtins.__import__ = _original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guard)


def test_row_signature_can_stop_inside_coefficient_traversal():
    visits=[]
    class Coefficients:
        def items(self):
            for i in range(130):
                visits.append(i)
                yield Var(i),float(i)
    row=SimpleNamespace(idx=0,name='physical',expr=SimpleNamespace(
        sense='=',const=0.,expr=Coefficients()))
    checks=[]
    def check():
        checks.append(True)
        if len(checks)==3:raise TimeoutError('Absolute preparation deadline')
    with pytest.raises(TimeoutError):ch._row_signature(row,check=check)
    assert visits==list(range(65))  # Stops mid-row, without traversing the tail.


def test_inventory_deadline_stops_mid_variable_walk(native):
    h=native();visited=[]
    original=h.built['model'].vars
    class Variables:
        def __iter__(self):
            for i,var in enumerate(original):
                visited.append(i)
                yield var
    h.built['model'].vars=Variables()
    def check():
        if len(visited)>=2:raise TimeoutError('Absolute inventory deadline')
    with pytest.raises(TimeoutError):ch._inventory(h.case,h.built,set(h.selected),check=check)
    assert visited==[0,1] and not h.calls
    assert all((v.lb,v.ub)==(0.,1.) for v in original[:-1])


@pytest.mark.parametrize('damage',['row','bounds','hidden_discrete','mapping'])
def test_repeated_inventory_keeps_all_physical_rejections(native,damage):
    h=native();selected=set(h.selected)
    rows,before=ch._inventory(h.case,h.built,selected,check=lambda:None)
    for movement,var in zip(h.case.movements,h.built['x']):
        var.lb=var.ub=int(movement.id in selected)
    _,after=ch._inventory(h.case,h.built,selected,rows,check=lambda:None)
    assert after['mapped_binary_indices']==before['mapped_binary_indices']
    assert after['physical_rows_preserved'] and after['all_unfixed_continuous']
    if damage=='row':h.built['model'].constrs[0].expr.const=1.
    elif damage=='bounds':h.built['x'][0].ub=1.-h.built['x'][0].lb
    elif damage=='hidden_discrete':h.built['model'].vars[-1].var_type='I'
    else:h.built['x'][-1]=h.built['x'][0]
    with pytest.raises(ValueError):ch._inventory(h.case,h.built,selected,rows,check=lambda:None)
    assert not h.calls


def test_inventory_timeout_retains_compact_bound_timing_without_solver(native,monkeypatch):
    h=native(deadline=10.);original=ch._inventory
    def expired(case,built,selected,*args,check=None,measure=None):
        variables=built['model'].vars
        # Snapshot before replacing the iterable; the check stops its second item.
        snapshot=list(variables)
        class ExpiringVariables:
            def __iter__(self):
                for index,var in enumerate(snapshot):
                    if index==1:h.clock.now=10.
                    yield var
        built['model'].vars=ExpiringVariables()
        try:return original(case,built,selected,*args,check=check,measure=measure)
        finally:built['model'].vars=variables
    monkeypatch.setattr(ch,'_inventory',expired)
    result=h.run()
    assert result['plan'] is None and result['status']=='unresolved' and not h.calls
    assert len(result['failures'])==1 and result['failures'][0]['error_type']=='TimeoutError'
    timings=result['preparation_timings']
    assert {'validation','model_build','inventory0','inventory0.variables'} <= {r['stage'] for r in timings}
    failed=[r for r in timings if r['stage']=='inventory0.variables'][0]
    assert failed['started_monotonic']==0. and failed['finished_monotonic']==10.
    assert failed['elapsed_s']==10. and failed['deadline']==10.
    assert failed['completed_before_deadline'] is False and failed['error']['error_type']=='TimeoutError'
    assert not result['reverse_repair_allowed'] and result['global_lower_bound'] is None


@pytest.mark.parametrize('returned',[105.,105.25])
def test_late_helper_evidence_retained_once_without_admission_or_quota_renewal(returned):
    clock=Clock(101.);allowance=rc.CompletionAllowance(limit=6.,spent=2.);seen=[]
    failure={'stage':'inventory','error_type':'TimeoutError','error':'preparation exhausted'}
    timing={'stage':'inventory0.variables','started_monotonic':101.,
        'finished_monotonic':returned,'elapsed_s':returned-101.,'deadline':105.,
        'completed_before_deadline':False}
    helper={'status':'feasible','plan':{'tag':'earlier'},'replay':{'replay_ok':True},
        'failures':[failure],'stages':[{'stage':'feasibility','stats':{'status':'FEASIBLE'}}],
        'preparation_timings':[timing],'events':[{'raw':'must not duplicate'}],
        'true_bill_exact':'10','true_bill':10.}
    saved=deepcopy(helper)
    def complete(*args,deadline,**kwargs):
        seen.append(deadline);clock.now=returned;return helper
    result=provider.propose(chain_case(2),[1.],[0.],
        schedule=SimpleNamespace(construction_end=106.,charging_stage_end=112.),
        allowance=allowance,budget=rc.pf.Budget(),clock=clock,allowed=lambda:True,events=[],
        constructor=lambda *args,**kwargs:{'status':'proposal','selected_ids':['outA','AB','inB'],
            'active_merge_count':2,'undone_count':0},completer=complete,
        undoer=lambda *args,**kwargs:pytest.fail('No repair after helper failure/witness'))
    audits=[r for r in result['stages'] if r['stage']=='charging0']
    assert len(audits)==1 and audits[0]['result']['preparation_timings']==[timing]
    assert audits[0]['result']['stages']==helper['stages']
    assert not {'plan','replay','events','failures'} & audits[0]['result'].keys()
    assert audits[0]['timing']=={'entered_monotonic':101.,'returned_monotonic':returned,'deadline':105.}
    assert result['failures'].count(failure)==1 and helper==saved
    assert seen==[105.] and result['completion_deadline']==105. and allowance.spent==2.
    assert result['repairs']==0 and not result['durable_fallback'] and not result['start_submitted']
    assert (result['plan'] is not None) is (returned==105.)
    if returned>105.:
        assert result['status']=='unresolved' and len(result['failures'])==2
        assert result['failures'][-1]['error_type']=='TimeoutError'


def test_native_build_timestamps_bind_actual_phase_case_and_cutoff(instrument,monkeypatch):
    h=instrument;original=worker.pf.build_feasible_model
    def build(*args,**kwargs):
        value=original(*args,**kwargs);h.clock.now+=.25;return value
    monkeypatch.setattr(worker.pf,'build_feasible_model',build)
    with worker.instrument_native60(h.lock,h.task,h.folder,anchor=100.,full_case=h.full,
                                   source_case=h.source,clock=h.clock) as state:
        with worker.native_phase(state,'prefix',120.):
            worker.pf.build_feasible_model(h.source,'GRB')
    rows=[json.loads(line) for line in (h.folder/'native.jsonl').read_text().splitlines()]
    enter=next(r for r in rows if r['event']=='native_model60_build' and r['stage']=='enter')
    leave=next(r for r in rows if r['event']=='native_model60_build' and r['stage']=='return')
    model=next(r for r in rows if r['event']=='native_model60')
    assert enter['at']==101. and leave['at']==101.25
    assert leave['started_monotonic']==101. and leave['elapsed_s']==.25
    assert model['build_started_monotonic']==101. and model['build_finished_monotonic']==101.25
    assert model['build_elapsed_s']==.25 and model['at']==101.25
    assert all(r['deadline']==120. and r['phase']=='prefix' and
               r['case_identity']==h.source.identity() for r in (enter,leave,model))
    assert not h.calls
