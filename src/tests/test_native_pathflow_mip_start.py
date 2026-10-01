"""Pure checks for the opt-in compact physical-pricing MIP start."""
from copy import deepcopy
from dataclasses import replace
import time
from types import SimpleNamespace

import pytest

from egglab import native_pathflow as pf, native_recharge as nr
from experiments import native_recharge_qualification as q


def known_fleet(case):
    plan = {'schema':nr.SCHEMA,'case_identity':case.identity(),
        'formulation':pf.FORMULATION,'native_matrix':pf.NATIVE_MATRIX,
        'extraction_policy':pf.EXTRACTION_POLICY,
        'vehicles':[{'vehicle':0,'trips':['A','B'],
                     'movements':['out_A','depot_AB','in_B']}],
        'charges':[{'vehicle':0,'movement':'depot_AB','connector':0,
                    'start_min':60.,'end_min':120.,'grid_kwh':10.},
                   {'vehicle':0,'movement':'in_B','connector':0,
                    'start_min':180.,'end_min':220.,'grid_kwh':20.}],
        'load':[0.,10.,0.,20.],'ops_cost':7.}
    assert nr.replay_native(case,plan)['replay_ok']
    return plan


class FakeModel:
    seed = 0
    def __init__(self,vars):
        self.vars = vars
        self.start = None


def fake_native(monkeypatch,case):
    x = [SimpleNamespace(var_type='B',idx=j) for j in range(len(case.movements))]
    model = FakeModel(x)
    built = {'model':model,'x':x,'backend':'CBC','backend_runtime':{'fake':True}}
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:built)
    monkeypatch.setattr(pf,'attach_objective',lambda *args:None)
    monkeypatch.setattr(pf,'_optimize_once',lambda *args:{'status':'NO_SOLUTION_FOUND',
        'incumbent':None,'lower_bound':None})
    return model,x


def test_complete_binary_mapping_is_opt_in_and_source_is_unchanged(monkeypatch):
    case=q.cyclic_case()
    source=known_fleet(case)
    original=deepcopy(source)
    model,x=fake_native(monkeypatch,case)
    events=[]
    result=pf.solve_pricing(case,[1.]*4,start_plan=source,record=events.append)
    assert result['status']=='unresolved' and 'plan' not in result
    assert source==original
    assert model.start==[(var,int(mode.id in {'out_A','depot_AB','in_B'}))
        for var,mode in zip(x,case.movements)]
    receipt=next(e for e in events if e['event']=='mip_start_setup')
    assert receipt['status']=='submitted' and receipt['binary_count']==len(case.movements)
    assert receipt['selected_count']==3 and receipt['zero_count']==len(case.movements)-3
    assert set(receipt['timings'])=={'validation_s','model_build_s',
        'objective_attach_s','start_attach_s'}
    assert all(v>=0 for v in receipt['timings'].values())
    assert next(e for e in events if e['event']=='native_start')['model_seed']==0
    assert events[-1]['event']=='native_status'
    model.start=None
    pf.solve_pricing(case,[1.]*4)
    assert model.start is None


@pytest.mark.parametrize('change,match',[
    (lambda c,p:p.update(case_identity='wrong'),'case_identity mismatch'),
    (lambda c,p:p.update(formulation='wrong'),'formulation mismatch'),
    (lambda c,p:p.update(native_matrix='wrong'),'native_matrix mismatch'),
    (lambda c,p:p.update(extraction_policy='wrong'),'extraction_policy mismatch'),
    (lambda c,p:p.update(schema='wrong'),'schema mismatch'),
    (lambda c,p:p['vehicles'][0]['movements'].append('unknown'),'malformed or physically infeasible'),
    (lambda c,p:p['charges'][1].update(end_min=200.),'malformed or physically infeasible'),
    (lambda c,p:p['load'].__setitem__(1,9.),'malformed or physically infeasible'),
])
def test_invalid_source_rejected_before_model_build(monkeypatch,change,match):
    case=q.cyclic_case()
    source=known_fleet(case)
    change(case,source)
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:pytest.fail('cold fallback'))
    events=[]
    with pytest.raises(ValueError,match=match):
        pf.solve_pricing(case,[1.]*4,start_plan=source,record=events.append)
    assert len(events)==1 and events[0]['event']=='mip_start_setup'
    assert events[0]['status']=='rejected' and events[0]['stage']=='validation'
    assert events[0]['setup_elapsed_s']>=0


def test_same_supply_shifted_case_is_allowed_but_physical_change_is_not():
    case=q.cyclic_case()
    source=known_fleet(case)
    assert pf._checked_pricing_start(case,source)=={'out_A','depot_AB','in_B'}
    different=replace(case,battery_kwh=21.)
    with pytest.raises(ValueError,match='case_identity mismatch'):
        pf._checked_pricing_start(different,source)


def test_validation_time_is_paid_and_cannot_start_after_deadline(monkeypatch):
    case=q.cyclic_case()
    source=known_fleet(case)
    original=pf._checked_pricing_start
    def slow_check(*args):
        result=original(*args)
        time.sleep(.02)
        return result
    monkeypatch.setattr(pf,'_checked_pricing_start',slow_check)
    monkeypatch.setattr(pf,'build_feasible_model',lambda *args:pytest.fail('built after deadline'))
    events=[]
    with pytest.raises(TimeoutError,match='validation exhausted'):
        pf.solve_pricing(case,[1.]*4,budget=nr.Budget(wall_seconds=.005),
            start_plan=source,record=events.append)
    receipt=events[0]
    assert receipt['status']=='timed_out' and receipt['stage']=='validation'
    assert receipt['timings']['validation_s']>=.02
    assert receipt['setup_elapsed_s']>=receipt['timings']['validation_s']


def test_start_attachment_failure_is_recorded_and_raised(monkeypatch):
    case=q.cyclic_case()
    source=known_fleet(case)
    model,x=fake_native(monkeypatch,case)
    x[0].var_type='C'
    events=[]
    with pytest.raises(ValueError,match='binary mapping'):
        pf.solve_pricing(case,[1.]*4,start_plan=source,record=events.append)
    assert model.start is None
    assert events[0]['status']=='rejected' and events[0]['stage']=='start_attach'
    assert 'model_build_s' in events[0]['timings']


def test_unmapped_integer_variable_rejects_incomplete_start(monkeypatch):
    case=q.cyclic_case()
    source=known_fleet(case)
    model,_=fake_native(monkeypatch,case)
    model.vars.append(SimpleNamespace(var_type='I',idx=len(model.vars)))
    with pytest.raises(ValueError,match='binary mapping'):
        pf.solve_pricing(case,[1.]*4,start_plan=source)
    assert model.start is None
