"""Deterministic candidate retention and completion accounting checks."""
from types import SimpleNamespace
import time

import pytest

from egglab import native_pathflow as pf
from experiments.native_recharge_qualification import cyclic_case
from test_route_fixed_repair import known_plan, SELECTED


def setup_planner(monkeypatch, fail_first=False):
    case = cyclic_case()
    plan = known_plan(case)
    plan['replay'] = pf.replay_native(case, plan)
    plan['raw_solver_load'] = plan['replay']['load']
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args: {})
    monkeypatch.setattr(pf,'attach_objective',lambda *args: None)
    monkeypatch.setattr(pf,'_optimize_once',lambda *args: {
        'status':'FEASIBLE','incumbent':37.,'lower_bound':0.})
    calls = []
    def extract(*args, **kwargs):
        calls.append(1)
        if fail_first or len(calls)>1:
            raise ValueError('deliberate later invalid candidate')
        return plan
    monkeypatch.setattr(pf,'_extract',extract)
    return case, plan


def test_later_invalid_retains_best(monkeypatch):
    case, plan = setup_planner(monkeypatch)
    result = pf.solve_planner(case,[1.]*4,[0.]*4,pf.Budget(max_rounds=3))
    assert result['status']=='bounded'
    assert result['plan'] is plan
    assert len(result['rounds'])==2
    assert result['rounds'][1]['extraction_failure']


def test_first_invalid_is_explicit(monkeypatch):
    case, _ = setup_planner(monkeypatch,True)
    result = pf.solve_planner(case,[1.]*4,[0.]*4)
    assert result['status']=='extraction_failed' and 'plan' not in result


def test_completion_no_time():
    with pytest.raises(TimeoutError):
        pf._complete_topology(cyclic_case(),{},pf.Budget(),time.monotonic()-1)


def test_unqualified_integrality_rejected():
    built={'model':SimpleNamespace(integer_tol=1e-6), 'x':[SimpleNamespace(x=.2)]}
    with pytest.raises(ValueError,match='Unqualified integrality'):
        pf._complete_topology(cyclic_case(),built,pf.Budget(),time.monotonic()+10)


def test_completion_keeps_original_global_bound(monkeypatch):
    case = cyclic_case()
    monkeypatch.setattr(pf,'_complete_topology',lambda *args:(known_plan(case),{
        'status':'OPTIMAL','incumbent':40.,'lower_bound':40.}))
    raw={'status':'FEASIBLE','incumbent':37.,'lower_bound':12.}
    plan, admitted=pf._candidate(case,{},pf.Budget(),time.monotonic()+10,raw,True,None,0)
    assert admitted['lower_bound']==12.
    assert admitted['incumbent']==40.
    assert plan['raw_mip_stats']==raw
    assert raw['incumbent']==37.


def test_completion_preserves_rows_and_fixes_trickle_topology(monkeypatch):
    case=cyclic_case()
    variables=[SimpleNamespace(x=1-2e-7 if m.id in SELECTED else 2e-7,lb=0,ub=1)
               for m in case.movements]
    model=SimpleNamespace(integer_tol=1e-6,objective='original objective')
    built={'model':model,'x':variables,'constraints':object()}
    calls=[]
    def optimize(*args):
        calls.append(model.objective)
        assert all(v.lb==v.ub==int(m.id in SELECTED) for m,v in zip(case.movements,variables))
        return {'status':'OPTIMAL','incumbent':37.,'lower_bound':37.}
    monkeypatch.setattr(pf,'_optimize_once',optimize)
    monkeypatch.setattr(pf,'_extract',lambda *args,**kwargs:known_plan(case))
    pf._complete_topology(case,built,pf.Budget(),time.monotonic()+10)
    assert calls==[0.,'original objective']


def test_infeasible_completion_rejected(monkeypatch):
    case=cyclic_case()
    built={'model':SimpleNamespace(integer_tol=1e-6,objective='original'),
           'x':[SimpleNamespace(x=int(m.id in SELECTED),lb=0,ub=1) for m in case.movements]}
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:{'status':'INFEASIBLE','incumbent':None})
    with pytest.raises(ValueError,match='infeasible'):
        pf._complete_topology(case,built,pf.Budget(),time.monotonic()+10)


def test_later_repair_runtime_error_retains_best(monkeypatch):
    case, plan = setup_planner(monkeypatch)
    calls=[]
    def complete(*args):
        calls.append(1)
        if len(calls)>1:
            raise RuntimeError('solver backend repair error')
        return plan, {'status':'FEASIBLE','incumbent':37.,'lower_bound':37.}
    monkeypatch.setattr(pf,'_complete_topology',complete)
    result=pf.solve_planner(case,[1.]*4,[0.]*4,pf.Budget(max_rounds=3),completion=True)
    assert result['status']=='bounded' and result['plan'] is plan
    assert 'RuntimeError' in result['rounds'][1]['extraction_failure']['error']


@pytest.mark.parametrize('error_type', [TimeoutError, RuntimeError])
@pytest.mark.parametrize('fail_first', [False, True])
def test_native_optimizer_exception_retention(monkeypatch, error_type, fail_first):
    case, plan = setup_planner(monkeypatch)
    calls=[]
    def optimize(*args):
        calls.append(1)
        if fail_first or len(calls)>1:
            raise error_type('visible native optimizer failure')
        return {'status':'FEASIBLE','incumbent':37.,'lower_bound':0.}
    monkeypatch.setattr(pf,'_optimize_once',optimize)
    events=[]
    # Avoid forensic snapshot fixture requirements; record failures explicitly.
    monkeypatch.setattr(pf,'capture_incumbent',lambda *args:{})
    result=pf.solve_planner(case,[1.]*4,[0.]*4,pf.Budget(max_rounds=3),record=events.append)
    assert result['status']==('search_failed' if fail_first else 'bounded')
    if fail_first:
        assert 'plan' not in result
    else:
        assert result['plan'] is plan
    failure=result['rounds'][-1]['search_failure']
    assert failure['stage']=='optimization' and failure['error_type']==error_type.__name__
    assert any(event['event']=='native_search_failed' for event in events)


@pytest.mark.parametrize('error_type',[TimeoutError,RuntimeError])
def test_valid_same_round_raw_survives_completion_failure(monkeypatch,error_type):
    case,plan=setup_planner(monkeypatch)
    monkeypatch.setattr(pf,'_extract',lambda *args,**kwargs:plan)
    def fail(*args):
        raise error_type('objective phase failed after feasibility')
    monkeypatch.setattr(pf,'_complete_topology',fail)
    result=pf.solve_planner(case,[1.]*4,[0.]*4,pf.Budget(max_rounds=1),completion=True)
    assert result['plan'] is plan and result['status']=='bounded'
    assert plan['candidate_failures'][0]['error_type']==error_type.__name__


def test_completed_worse_true_bill_does_not_replace_raw(monkeypatch):
    case=cyclic_case()
    raw={'ops_cost':7.,'raw_solver_load':[1.,0.,0.,0.],'physical':[1.,0.,0.,0.]}
    completed={'ops_cost':7.,'raw_solver_load':[0.,2.,0.,0.],'physical':[0.,2.,0.,0.]}
    monkeypatch.setattr(pf,'_extract',lambda *args,**kwargs:raw)
    monkeypatch.setattr(pf,'replay_native',lambda case,plan,*args:{'load':plan['physical'],'replay_ok':True})
    monkeypatch.setattr(pf,'_complete_topology',lambda *args:(completed,{
        'status':'OPTIMAL','incumbent':7.,'lower_bound':7.}))
    stats={'status':'FEASIBLE','incumbent':7.,'lower_bound':0.}
    # Identical tangent objectives; true quadratic cost is 0.5 vs 2.
    selected,_=pf._candidate(case,{},pf.Budget(),time.monotonic()+10,stats,True,None,0,
        ('tangents',([0.]*4,[1.]*4,[[(0.,0.)]]*4)))
    assert selected is raw


def test_pricing_returned_stats_admit_changed_completion_objective(monkeypatch):
    case=cyclic_case()
    completed={'ops_cost':7.,'raw_solver_load':[10.,0.,0.,0.]}
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:{})
    monkeypatch.setattr(pf,'attach_objective',lambda *args:None)
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:{
        'status':'FEASIBLE','incumbent':16.,'lower_bound':10.})
    def reject_raw(*args,**kwargs):
        raise ValueError('raw rejected')
    monkeypatch.setattr(pf,'_extract',reject_raw)
    monkeypatch.setattr(pf,'_complete_topology',lambda *args:(completed,{
        'status':'OPTIMAL','incumbent':17.,'lower_bound':17.}))
    monkeypatch.setattr(pf,'replay_native',lambda *args:{
        'load':[10.,0.,0.,0.],'pricing_objective':17.,'replay_ok':True})
    result=pf.solve_pricing(case,[1.]*4,completion=True)
    assert result['stats']['incumbent']==17.
    assert result['raw_mip_stats']['incumbent']==16.
    assert result['stats']['lower_bound']==10.
    assert pf.admit_bound(result['stats'],17.)==(result['lower'],result['upper'])
