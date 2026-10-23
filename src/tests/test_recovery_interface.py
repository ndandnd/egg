"""Solver-free recovery boundary tests; no native backend is imported."""
from dataclasses import replace
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest
from egglab import native_pathflow as pf
from egglab.recovery_lift import lift_plan

_spec = importlib.util.spec_from_file_location('recovery_fixture', Path(__file__).resolve().parents[2]/'research-20261017/recovery-prototype/test_recovery_lift.py')
# Load the frozen handcrafted fixture without changing its historical module import.
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research-20261017/recovery-prototype'))
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
fixture = _fixture.fixture


def test_binary_inventory_and_bounds_untouched():
    source,full,plan=fixture()
    hint=lift_plan(source,full,plan,a=[1.,2.],b=[0.,.2])
    variables=[SimpleNamespace(idx=i,var_type='B',lb=0,ub=1) for i in range(3)]
    continuous=SimpleNamespace(idx=3,var_type='C',lb=0,ub=99)
    model=SimpleNamespace(vars=variables+[continuous])
    pf._attach_pricing_start(full,{'x':variables,'model':model},set(hint['provenance']['selected_movement_ids']))
    assert [value for _,value in model.start]==[0,1,1]
    assert all(var is not continuous for var,_ in model.start)
    assert [(v.lb,v.ub) for v in variables]==[(0,1)]*3


@pytest.mark.parametrize('failure',['build','attach','optimize','no_incumbent','replay','infeasible'])
def test_fallback_retained(monkeypatch,failure):
    source,full,plan=fixture()
    def fail(*args,**kwargs): raise RuntimeError('injected failure')
    monkeypatch.setattr(pf,'build_feasible_model',fail if failure=='build' else lambda *args: {})
    monkeypatch.setattr(pf,'attach_objective',lambda *args: None)
    monkeypatch.setattr(pf,'_attach_pricing_start',fail if failure=='attach' else lambda *args: {})
    stats={'status':'INFEASIBLE' if failure=='infeasible' else 'FEASIBLE',
           'incumbent':None if failure=='no_incumbent' else 1.,'lower_bound':0.}
    monkeypatch.setattr(pf,'_optimize_once',fail if failure=='optimize' else lambda *args: stats)
    monkeypatch.setattr(pf,'_candidate',fail)
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source)
    assert result['upper']==59.5
    assert result['plan']['case_identity']==full.identity()
    assert result['lower']==-float('inf')
    assert result['status']!='certified'
    assert result['recovery']['global_lower_bound'] is None
    assert 'raw_solver_load' not in result['plan']


def test_expired_clock_never_builds(monkeypatch):
    source,full,plan=fixture()
    monkeypatch.setattr(pf.time,'monotonic',lambda:100.)
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args: pytest.fail('expired model build'))
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,deadline=99.)
    assert result['upper']==59.5 and result['status']=='feasible'
    assert result['recovery_timing']['deadline_overrun_s']==1.


def test_setup_exhaustion_prevents_native_call(monkeypatch):
    source,full,plan=fixture()
    clock=[0.]
    monkeypatch.setattr(pf.time,'monotonic',lambda:clock[0])
    def build(*args): clock[0]=3.; return {}
    monkeypatch.setattr(pf,'build_feasible_model',build)
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:pytest.fail('native phase after deadline'))
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,deadline=2.)
    assert result['upper']==59.5
    assert result['rounds'][0]['search_failure']['error_type']=='TimeoutError'


def test_invalid_start_no_fabricated_fallback(monkeypatch):
    source,full,plan=fixture()
    plan['charges'][0]['grid_kwh']=0
    monkeypatch.setattr(pf.time,'monotonic',lambda:100.)
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,deadline=99.)
    assert 'plan' not in result and 'lower' not in result
    assert result['recovery']['status']=='rejected'


def test_full_bound_separate_from_physical_fallback_objective(monkeypatch):
    source,full,plan=fixture()
    lifted=lift_plan(source,full,plan,a=[1.,2.],b=[0.,.2])['plan']
    lifted['replay']=pf.replay_native(full,lifted)
    lifted['raw_solver_load']=[0.,15.]
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:{})
    monkeypatch.setattr(pf,'attach_objective',lambda *args:None)
    monkeypatch.setattr(pf,'_attach_pricing_start',lambda *args:{})
    stats={'status':'FEASIBLE','incumbent':37.,'lower_bound':30.}
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:stats)
    monkeypatch.setattr(pf,'_candidate',lambda *args:(lifted,stats))
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,
                            budget=replace(pf.Budget(),max_rounds=1))
    assert result['upper']==59.5
    assert result['lower']==30.-pf.BOUND_GUARD
    assert result['rounds'][0]['stats']['incumbent']==37.
    assert 'raw_solver_load' not in result['plan']
    assert result['status']=='bounded'


@pytest.mark.parametrize('event',['native_status','native_incumbent','recovery_fallback_admitted','candidate_rejected'])
def test_instrumentation_sink_failure_retains_fallback(monkeypatch,event):
    source,full,plan=fixture()
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:{})
    monkeypatch.setattr(pf,'attach_objective',lambda *args:None)
    monkeypatch.setattr(pf,'_attach_pricing_start',lambda *args:{})
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:{'status':'FEASIBLE','incumbent':37.,'lower_bound':0.})
    monkeypatch.setattr(pf,'capture_incumbent',lambda *args:{})
    def fail_candidate(*args): raise RuntimeError('extraction injected')
    monkeypatch.setattr(pf,'_candidate',fail_candidate)
    def record(row):
        if row['event']==event: raise OSError('sink injected')
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,record=record)
    assert result['upper']==59.5 and result['lower']==-float('inf')
    assert result['instrumentation_failures'][0]['event']==event


def test_capture_failure_retains_fallback(monkeypatch):
    source,full,plan=fixture()
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:{})
    monkeypatch.setattr(pf,'attach_objective',lambda *args:None)
    monkeypatch.setattr(pf,'_attach_pricing_start',lambda *args:{})
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:{'status':'FEASIBLE','incumbent':37.,'lower_bound':0.})
    def capture(*args): raise RuntimeError('capture injected')
    monkeypatch.setattr(pf,'capture_incumbent',capture)
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,record=lambda row:None)
    assert result['upper']==59.5 and result['lower']==-float('inf')
    assert result['rounds'][0]['extraction_failure']['error']=='capture injected'


def test_contradictory_prior_bound_invalidated_after_early_retention(monkeypatch):
    source,full,plan=fixture()
    lifted=lift_plan(source,full,plan,a=[1.,2.],b=[0.,.2])['plan']
    lifted['replay']=pf.replay_native(full,lifted)
    lifted['raw_solver_load']=[0.,15.]
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:{})
    monkeypatch.setattr(pf,'attach_objective',lambda *args:None)
    monkeypatch.setattr(pf,'_attach_pricing_start',lambda *args:{})
    rounds=[0]
    def optimize(*args):
        rounds[0]+=1
        return {'status':'FEASIBLE','incumbent':37.,'lower_bound':30.}
    monkeypatch.setattr(pf,'_optimize_once',optimize)
    monkeypatch.setattr(pf,'_candidate',lambda *args:(lifted,{'incumbent':100.}))
    # Inject an admission boundary inconsistency: later admitted bill undercuts
    # the earlier global lower. This isolates retention/enclosure fault handling.
    monkeypatch.setattr(pf,'_candidate_score',lambda *args:0.)
    monkeypatch.setattr(pf,'true_cost',lambda *args:52.5 if rounds[0]==1 else 20.)
    monkeypatch.setattr(pf,'admit_bound',lambda *args,**kw:(50.,59.5) if rounds[0]==1 else (0.,27.))
    result=pf.solve_planner(full,[1.,2.],[0.,.2],start_plan=plan,start_case=source,
                            budget=replace(pf.Budget(),max_rounds=2))
    assert result['upper']==27. and result['lower']==-float('inf')
    assert result['gap']==float('inf') and result['status']=='bound_replay_contradiction'
    assert result['rounds'][1]['bound_contradiction']['previous_lower']==50.
