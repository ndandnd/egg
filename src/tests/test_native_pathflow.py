"""Pure path recovery, replay and fake-native admission; no optimizer."""
from dataclasses import replace
import itertools
import math
from types import SimpleNamespace as Box

import pytest
from egglab import native_recharge as nr, native_pathflow as pf
from experiments import native_recharge_qualification as q


def test_complete_cyclic_path_covers_are_recovered_without_vehicle_labels():
    case = q.cyclic_case()
    valid = []
    for flags in itertools.product((0,1), repeat=len(case.movements)):
        chosen = [m.id for m,flag in zip(case.movements,flags) if flag]
        try:
            paths,owners = pf.recover_paths(case,chosen)
        except ValueError:
            continue
        assert set(owners)==set(chosen)
        assert sorted(t for p in paths for t in p['trips'])==['A','B']
        valid.append((len(paths),tuple(sorted(chosen))))
    assert sorted(n for n,_ in valid)==[1,1,2]
    assert {n for n,ids in valid if 'depot_AB' in ids}=={1}
    assert {n for n,ids in valid if 'direct_AB' in ids}=={1}
    one = replace(case,max_vehicles=1)
    with pytest.raises(ValueError,match='path count'):
        pf.recover_paths(one,['out_A','in_A','out_B','in_B'])


@pytest.mark.parametrize('selected', [[], ['unknown'], ['out_A','in_A'],
    ['out_A','in_A','out_B','in_B','in_B'],
    ['out_A','depot_AB','direct_AB','in_B'],
    ['out_A','depot_AB','in_B','out_B']])
def test_corrupt_selected_graphs_fail(selected):
    with pytest.raises(ValueError):
        pf.recover_paths(q.cyclic_case(),selected)


def test_timestamps_preclude_disconnected_circulations():
    c = q.cyclic_case()
    bad = nr.Movement('backwards','direct','B','A',(nr.Leg('D','D',180,180,0),))
    with pytest.raises(ValueError,match='timing'):
        pf.recover_paths(replace(c,movements=c.movements+(bad,)),['backwards'])


def fake_built(case,two=False):
    selected = {'out_A','in_A','out_B','in_B'} if two else {'out_A','depot_AB','in_B'}
    compiled = nr.compile_case(case)
    ids = {m.id:j for j,m in enumerate(case.movements)}
    energy = {(ids['in_A'],1):5,(ids['in_A'],3):10,(ids['in_B'],3):15} if two else {
        (ids['depot_AB'],1):10,(ids['in_B'],3):20}
    charge = {(ids[mid],k):Box(x=energy.get((ids[mid],k),0.))
        for k,it in enumerate(compiled['intervals']) if it['rate_kw']>0 for mid in it['visits']}
    return {'x':[Box(x=float(m.id in selected)) for m in case.movements],
            'compiled':compiled,'charge':charge,
            'loads':[Box(x=l) for l in ([0,5,0,25] if two else [0,10,0,20])]}


@pytest.mark.parametrize('two',[False,True])
def test_unlabelled_charges_lift_to_replay_valid_owned_paths(two):
    c=q.cyclic_case();events=[]
    plan=pf._extract(c,fake_built(c,two),record=events.append)
    r=nr.replay_native(c,plan)
    assert r['grid_kwh']==30 and r['consumption_kwh']==30
    assert len(plan['vehicles'])==2 if two else len(plan['vehicles'])==1
    assert plan['formulation']==pf.FORMULATION
    assert [x['event'] for x in events]==['charge_normalization','serial_decoding']
    for v in r['soc_trajectories']:
        assert v[-1]['soc_kwh']==20
    assert all(a['end_min']<=b['start_min'] for a,b in zip(plan['charges'],plan['charges'][1:]))


def test_any_positive_charge_on_unused_mode_is_rejected():
    c=q.cyclic_case();b=fake_built(c)
    unused=next(j for j,m in enumerate(c.movements) if m.id=='in_A')
    b['charge'][unused,1].x=1e-14
    with pytest.raises(ValueError,match='unselected'):
        pf._extract(c,b)


def test_negative_roundoff_preserves_qualified_budget_and_raw_mapping():
    c=q.cyclic_case();b=fake_built(c)
    unused=next(j for j,m in enumerate(c.movements) if m.id=='in_A')
    b['charge'][unused,1].x=-1e-12
    plan=pf._extract(c,b)
    correction=plan['roundoff']['negative_correction']
    assert correction['negative_to_zero'][0]['key']==[unused,1]
    assert correction['negative_l1_kwh']==1e-12
    b['charge'][unused,1].x=-1e-7
    with pytest.raises(ValueError,match='roundoff'):
        pf._extract(c,b)


def test_aggregate_load_mismatch_fails():
    c=q.cyclic_case();b=fake_built(c);b['loads'][1].x=11
    with pytest.raises(ValueError,match='aggregate'):
        pf._extract(c,b)


@pytest.mark.parametrize('x',[float('nan'),float('inf'),None])
def test_raw_nonfinite_selection_fails(x):
    c=q.cyclic_case();b=fake_built(c);b['x'][0].x=x
    with pytest.raises(ValueError,match='nonfinite'):
        pf._extract(c,b)


def setup_fake(monkeypatch,stats):
    built=[]
    def builder(c,backend):
        b=fake_built(c);built.append(b);return b
    monkeypatch.setattr(pf,'build_feasible_model',builder)
    monkeypatch.setattr(pf,'attach_objective',lambda *a:None)
    monkeypatch.setattr(pf,'capture_incumbent',lambda *a:{'formulation':pf.FORMULATION,'fake':True})
    iterator=iter(stats)
    monkeypatch.setattr(pf,'_optimize_once',lambda *a:next(iterator))
    return built


def test_pricing_retains_qualified_lower_bound_not_incumbent(monkeypatch):
    setup_fake(monkeypatch,[{'status':'FEASIBLE','incumbent':37.,'lower_bound':36.}])
    result=pf.solve_pricing(q.cyclic_case(),[1]*4)
    assert result['status']=='bounded' and result['stats']['status']=='FEASIBLE'
    assert result['lower']==36-nr.BOUND_GUARD
    assert result['upper']==37+nr.BOUND_GUARD


def test_planner_keeps_true_upper_and_fresh_tangent_objective(monkeypatch):
    setup_fake(monkeypatch,[{'status':'OPTIMAL','incumbent':47.,'lower_bound':47.},
                           {'status':'OPTIMAL','incumbent':97.,'lower_bound':97.}])
    events=[]
    result=pf.solve_planner(q.cyclic_case(),[0,4,0,0],[0,.2,0,.2],record=events.append)
    assert result['status']=='certified' and len(result['rounds'])==2
    assert result['lower']==97-nr.BOUND_GUARD and result['upper']==97+nr.BOUND_GUARD
    first=next(e for e in events if e['event']=='native_start')
    assert first['tangents']==[[[0.,0.]],[[4.,0.]],[[0.,0.]],[[0.,0.]]]




def test_three_service_two_multileg_visits_lift_with_reserve_efficiency_and_cost():
    from experiments.native_pathflow_qualification import multivisit_case,controls
    c=multivisit_case();grid=nr.compile_case(c)
    chosen=['out_A','depot_AB','depot_BC','in_C']
    paths,owners=pf.recover_paths(c,chosen)
    assert len(paths)==1 and paths[0]['trips']==['A','B','C']
    charges=[]
    for mid,lo,hi in [('depot_AB',40,80),('depot_BC',120,160),('in_C',200,240)]:
        charges.append({'vehicle':0,'movement':mid,'connector':0,'start_min':lo,'end_min':hi,'grid_kwh':12/c.efficiency})
    loads=[sum(z['grid_kwh']*max(0,min(b,z['end_min'])-max(a,z['start_min']))/(z['end_min']-z['start_min'])
               for z in charges) for a,b in zip(c.market_edges_min,c.market_edges_min[1:])]
    plan={'schema':nr.SCHEMA,'case_identity':c.identity(),'vehicles':paths,'charges':charges,'load':loads,'ops_cost':37}
    replay=nr.replay_native(c,plan,[1]*4)
    assert replay['pricing_objective']==pytest.approx(1423/19)
    assert replay['grid_kwh']==pytest.approx(720/19)
    assert min(e['soc_kwh'] for e in replay['soc_trajectories'][0])>=1
    # Recover the identical physical charge allocation from compact raw keys.
    ids={m.id:j for j,m in enumerate(c.movements)}
    energy={}
    for k,it in enumerate(grid['intervals']):
        for z in charges:
            if z['start_min']<=it['start'] and it['end']<=z['end_min']:
                energy[ids[z['movement']],k]=z['grid_kwh']*(it['end']-it['start'])/(z['end_min']-z['start_min'])
    built={'x':[Box(x=float(m.id in chosen)) for m in c.movements],
           'compiled':grid,'loads':[Box(x=x) for x in loads],
           'charge':{(ids[mid],k):Box(x=energy.get((ids[mid],k),0.))
                     for k,it in enumerate(grid['intervals']) for mid in it['visits']}}
    recovered=pf._extract(c,built)
    assert nr.replay_native(c,recovered,[1]*4)['pricing_objective']==pytest.approx(1423/19)
    cells=controls();assert len(cells)==20
    assert sum(x['expected_status']=='infeasible' for x in cells)==4
    for cell in cells:nr.validate_case(cell['case'])
