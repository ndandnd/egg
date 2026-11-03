"""Symbolic CF1 contracts and fake native calls; never load a solver backend."""
import builtins
from copy import deepcopy
from dataclasses import asdict, replace
from fractions import Fraction
import math
from types import SimpleNamespace

import pytest

_original_import = builtins.__import__
def _guard(name, *args, **kwargs):
    if name.split('.')[0] in {'mip', 'gurobipy'}:
        raise AssertionError('Native backend forbidden in constructive unit checks')
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _guard
try:
    from egglab import constructive_control as cf
    from egglab import constructive_charging as ch
    from egglab.native_recharge import NativeCase, Trip, Leg, Movement, Resource, Budget
finally:
    builtins.__import__ = _original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins, '__import__', _guard)


class Clock:
    def __init__(self, now=0.): self.now = now
    def __call__(self): return self.now


def chain_case(n=3, cap=1, connectors=1, eta=.5):
    trips = tuple(Trip(chr(65+i), 10+40*i, 20+40*i, 'X', 'X', 2.) for i in range(n))
    movements = []
    for trip in trips:
        movements.extend((
            Movement('out'+trip.id, 'pullout', None, trip.id,
                     (Leg('D','X',trip.start_min-10,trip.start_min,1.),)),
            Movement('in'+trip.id, 'pullin', trip.id, None,
                     (Leg('X','D',trip.end_min,trip.end_min+10,1.),))))
    for left,right in zip(trips,trips[1:]):
        movements.append(Movement(left.id+right.id,'direct',left.id,right.id,
            (Leg('X','X',left.end_min,right.start_min,1.),)))
    return NativeCase('symbolic-CF1',trips,tuple(movements),
        (Resource(0,180,60.,60.,connectors),),(0,180),'D',cap,
        20.,2.,0,180,100.,.1,eta)


def test_greedy_merges_precede_vehicle_cap_and_preserve_input():
    case=chain_case();before=asdict(case)
    result=cf.construct_routes(case,deadline=6.,clock=Clock())
    assert result['status']=='proposal' and len(result['routes'])==1
    assert result['routes'][0]['trips']==['A','B','C']
    assert set(result['selected_ids'])=={'outA','AB','BC','inC'}
    assert len(result['merge_history'])==2 and asdict(case)==before
    assert result['selected_ids']==[m.id for m in case.movements if m.id in result['selected_ids']]


def test_merge_ties_use_ids_and_chronology_not_movement_order():
    case=chain_case(2)
    link=case.movements[-1]
    case=replace(case,movements=case.movements[:-1]+(replace(link,id='z'),replace(link,id='a')))
    first=cf.construct_routes(case,deadline=6.,clock=Clock())
    second=cf.construct_routes(replace(case,movements=tuple(reversed(case.movements))),
                               deadline=6.,clock=Clock())
    assert set(first['selected_ids'])==set(second['selected_ids'])=={'outA','a','inB'}
    assert first['routes'][0]['trips']==['A','B']


def test_optimistic_screen_cannot_borrow_charge_before_depot_arrival():
    case=chain_case(2)
    case=replace(case,battery_kwh=10.,trips=(replace(case.trips[0],energy_kwh=7.),
        replace(case.trips[1],energy_kwh=1.)))
    boundaries=tuple(replace(m,legs=tuple(replace(l,energy_kwh=0.) for l in m.legs))
                     for m in case.movements if m.kind in ('pullout','pullin'))
    depot=Movement('via','depot','A','B',(Leg('X','D',20,30,2.),Leg('D','X',40,50,0.)),1)
    case=replace(case,movements=boundaries+(depot,))
    result=cf.construct_routes(case,deadline=6.,clock=Clock())
    # Start full, serve7, then inbound2 => SOC1 below reserve2, even with abundant later power.
    assert result['status']=='no_proposal' and not result['selected_ids']
    assert not result['merge_history']


@pytest.mark.parametrize('eta,proposal',[(.5,True),(.25,False)])
def test_positive_depot_merge_uses_grid_capacity_and_battery_efficiency(eta,proposal):
    case=chain_case(2,eta=eta)
    case=replace(case,battery_kwh=10.,trips=tuple(replace(t,energy_kwh=4.) for t in case.trips))
    depot=Movement('via','depot','A','B',
                   (Leg('X','D',20,30,1.),Leg('D','X',40,50,1.)),1)
    case=replace(case,movements=case.movements+(depot,))
    grid=cf._window_capacity(case,depot,cf.cc._slices(case),lambda:None)
    assert grid==10.  # Ten minutes at60kW; eta converts this grid capacity to battery energy.
    result=cf.construct_routes(case,deadline=6.,clock=Clock())
    assert (result['status']=='proposal') is proposal
    if proposal:
        assert set(result['selected_ids'])=={'outA','via','inB'}
        assert result['routes'][0]['optimistic']['min_soc_kwh']==3.
    else:
        assert not result['selected_ids'] and not result['merge_history']


@pytest.mark.parametrize('eta,connectors,proposal',[(1.,1,True),(.5,1,False),(1.,0,False)])
def test_terminal_full_replenishment_uses_eta_and_connectors(eta,connectors,proposal):
    case=chain_case(1,eta=eta,connectors=connectors)
    trip=replace(case.trips[0],energy_kwh=4.)
    pullin=replace(case.movements[1],legs=(Leg('X','D',20,50,1.),))
    case=replace(case,trips=(trip,),movements=(case.movements[0],pullin),
                 resources=(Resource(0,60,60.,60.,connectors),),market_edges_min=(0,60),
                 recharge_deadline_min=60,battery_kwh=10.)
    result=cf.construct_routes(case,deadline=6.,clock=Clock())
    # Six battery kWh consumed; ten grid kWh available only in [50,60].
    assert (result['status']=='proposal') is proposal
    if not proposal: assert not result['selected_ids']


def test_repair_is_lifo_nonmutating_and_cumulatively_at_most_two():
    case=chain_case(cap=3);clock=Clock()
    original=cf.construct_routes(case,deadline=6.,clock=clock);before=deepcopy(original)
    once=cf.undo_merges(case,original,deadline=12.,clock=clock)
    twice=cf.undo_merges(case,once,deadline=12.,clock=clock)
    assert original==before and len(once['routes'])==2 and len(twice['routes'])==3
    assert once['undone_count']==1 and twice['undone_count']==2
    assert once['active_merge_count']==1 and twice['active_merge_count']==0
    assert once['repair_history'][-1]['removed_merge_indices']==[1]
    assert twice['repair_history'][-1]['removed_merge_indices']==[0]
    assert set(once['candidate_selected_ids'])!=set(original['candidate_selected_ids'])
    assert set(twice['candidate_selected_ids'])=={m.id for m in case.movements if m.kind in ('pullout','pullin')}
    with pytest.raises(ValueError): cf.undo_merges(case,twice,deadline=12.,clock=clock)


def test_expired_construction_and_repair_have_no_fresh_window():
    case=chain_case(cap=3)
    result=cf.construct_routes(case,deadline=6.,clock=Clock(6.))
    assert result['status']=='deadline' and not result['selected_ids']
    proposal=cf.construct_routes(case,deadline=6.,clock=Clock())
    repaired=cf.undo_merges(case,proposal,deadline=12.,clock=Clock(12.))
    assert repaired['status']=='deadline' and not repaired['selected_ids']


def test_undo_above_fleet_cap_keeps_diagnostic_routes_not_a_proposal():
    case=chain_case(cap=1)
    proposal=cf.construct_routes(case,deadline=6.,clock=Clock())
    repaired=cf.undo_merges(case,proposal,deadline=12.,clock=Clock())
    assert len(repaired['routes'])==2 and repaired['status']=='no_proposal'
    assert not repaired['selected_ids'] and repaired['candidate_selected_ids']


def test_terminal_cannot_borrow_power_before_pullin_availability():
    case=chain_case(1)
    case=replace(case,resources=(Resource(0,30,1e6,1e6),Resource(30,180,0.,0.)))
    result=cf.construct_routes(case,deadline=6.,clock=Clock())
    assert result['status']=='no_proposal' and not result['selected_ids']


def test_optimistic_separate_routes_do_not_claim_shared_connector_feasibility():
    case=chain_case(2,cap=2)
    case=replace(case,movements=tuple(m for m in case.movements if m.kind!='direct'))
    result=cf.construct_routes(case,deadline=6.,clock=Clock())
    assert result['status']=='proposal' and len(result['routes'])==2
    assert not result['shared_contention_checked'] and not result['feasibility_certified']


class Var:
    def __init__(self,idx,kind='C',lb=0.,ub=100.):
        self.idx,self.var_type,self.lb,self.ub=idx,kind,lb,ub


@pytest.fixture
def native(monkeypatch):
    def setup(*,statuses=None,loads=(3.,2.,4.),damage=None,advance=0.,deadline=10.):
        case=chain_case(2);selected=['outA','AB','inB'];clock=Clock();trace=[];calls=[]
        xs=[Var(i,'B',0.,1.) for i in range(len(case.movements))]
        continuous=Var(len(xs))
        expression=SimpleNamespace(sense='=',const=0.,expr={continuous:1.})
        row=SimpleNamespace(idx=0,name='physical',expr=expression)
        model=SimpleNamespace(vars=xs+[continuous],constrs=[row],num_rows=1,objective=None)
        built={'model':model,'x':xs,'physical_identity':case.identity(),
               'compiled':{'identity':case.identity()},'constraint_count_before_objective':1}
        if damage=='hidden_discrete':model.vars.append(Var(len(xs)+1,'I'))
        if damage=='mapping':built['x']=xs[:-1]+[xs[0]]
        if damage=='identity':built['physical_identity']='other'
        states=statuses or ['OPTIMAL']*3
        def build(*args): trace.append('build');return built
        def optimize(budgeted, budget, cutoff):
            index=len(calls);calls.append((budget,cutoff));trace.append('solve'+str(index))
            if index==0:assert model.objective==0.
            expected=[int(m.id in selected) for m in case.movements]
            assert [(v.lb,v.ub) for v in xs]==[(x,x) for x in expected]
            clock.now+=advance
            if damage=='physical_drift':expression.const=1.
            if damage=='fixed_bounds':xs[0].ub=1.-xs[0].lb
            state=states[index]
            if isinstance(state,Exception):raise state
            return {'status':state,'incumbent':100-index if state in ('OPTIMAL','FEASIBLE') else None,
                    'lower_bound':1e6}
        def capture(*args):trace.append('capture');return {'variables':[]}
        def extract(*args,**kwargs):
            trace.append('extract')
            return {'vehicles':[{'movements':list(selected)}],'load':[loads[len(calls)-1]],'round':len(calls)-1}
        def replay(case,plan):trace.append('replay');return {'replay_ok':True,'ops_cost':10.,'load':plan['load']}
        monkeypatch.setattr(ch.pf,'build_feasible_model',build)
        monkeypatch.setattr(ch.pf,'_optimize_once',optimize)
        monkeypatch.setattr(ch.pf,'capture_incumbent',capture)
        monkeypatch.setattr(ch.pf,'_extract',extract)
        monkeypatch.setattr(ch.pf,'attach_objective',lambda *args:trace.append('objective'))
        monkeypatch.setattr(ch.nr,'replay_native',replay)
        def run():return ch.complete_topology(case,selected,[1.],[0.],Budget(),deadline=deadline,clock=clock)
        return SimpleNamespace(case=case,selected=selected,built=built,clock=clock,calls=calls,trace=trace,run=run)
    return setup


def test_fixed_inventory_all_bounds_and_exact_replay_minimum_not_solver_score(native):
    h=native();before=asdict(h.case);result=h.run()
    assert result['status']=='feasible' and result['true_bill_exact']=='12'
    assert result['plan']['round']==1 and result['global_lower_bound'] is None
    assert result['inventory']['all_unfixed_continuous']
    assert not result['native_lp_certified'] and not result['reverse_repair_allowed']
    assert len(h.calls)==3 and {cutoff for _,cutoff in h.calls}=={10.}
    assert h.trace.count('build')==1 and h.trace.count('objective')==2
    assert asdict(h.case)==before
    for stage in result['stages']:
        assert 'lower_bound' not in stage['stats']
        assert stage['stats']['fixed_topology_lower_bound']==1e6
    assert h.trace.index('capture')<h.trace.index('extract')<h.trace.index('replay')


@pytest.mark.parametrize('later',[RuntimeError('objective failed'),'NO_SOLUTION_FOUND','INFEASIBLE'])
def test_feasibility_witness_survives_later_objective_failure(native,later):
    h=native(statuses=['OPTIMAL',later]);result=h.run()
    assert result['status']=='feasible' and result['true_bill_exact']=='13'
    assert result['plan']['round']==0 and not result['reverse_repair_allowed']
    assert result['global_lower_bound'] is None


@pytest.mark.parametrize('status,repair',[('INFEASIBLE',True),('NO_SOLUTION_FOUND',False),('UNBOUNDED',False)])
def test_only_qualified_initial_infeasible_allows_reverse_repair(native,status,repair):
    h=native(statuses=[status]);result=h.run()
    assert result['reverse_repair_allowed'] is repair and result['plan'] is None
    assert len(h.calls)==1 and 'capture' not in h.trace


@pytest.mark.parametrize('damage',['hidden_discrete','mapping','identity','physical_drift','fixed_bounds'])
def test_inventory_fails_closed_before_extracting_unqualified_model(native,damage):
    h=native(damage=damage);result=h.run()
    assert result['status']=='failed' and result['plan'] is None and result['failures']
    assert 'extract' not in h.trace and not result['reverse_repair_allowed']


def test_native_timeout_consumes_original_absolute_window_no_renewal(native):
    h=native(advance=2.,deadline=2.);result=h.run()
    assert result['status']=='unresolved' and result['plan'] is None
    assert len(h.calls)==1 and h.calls[0][1]==2. and not result['reverse_repair_allowed']
    again=h.run()
    assert len(h.calls)==1 and again['status']=='unresolved'


def test_replay_rejection_cannot_publish_solver_incumbent(native,monkeypatch):
    h=native()
    monkeypatch.setattr(ch.nr,'replay_native',lambda *args:{'replay_ok':False,'ops_cost':0.,'load':[0.]})
    result=h.run()
    assert result['status']=='failed' and result['plan'] is None and result['true_bill_exact'] is None


def test_capture_failure_prevents_extraction_and_admission(native,monkeypatch):
    h=native()
    def fail(*args):raise OSError('capture not durable')
    monkeypatch.setattr(ch.pf,'capture_incumbent',fail)
    result=h.run()
    assert result['status']=='failed' and 'extract' not in h.trace and result['plan'] is None


def test_exact_bill_minimum_resolves_difference_lost_by_float_total(native):
    lower=math.nextafter(.1,0.)
    assert 10.+lower==10.+.1
    h=native(loads=(.1,lower,.1));result=h.run()
    assert result['plan']['round']==1
    assert Fraction(result['true_bill_exact'])==Fraction(10.)+Fraction(lower)


def test_extraction_cannot_change_fixed_selected_topology(native,monkeypatch):
    h=native()
    monkeypatch.setattr(ch.pf,'_extract',lambda *args,**kw:
                        {'vehicles':[{'movements':['outA','inA']}],'load':[0.]})
    result=h.run()
    assert result['status']=='failed' and result['plan'] is None and 'replay' not in h.trace


def test_second_objective_tangent_uses_replay_load_and_total_cost_curvature(native,monkeypatch):
    h=native();payloads=[]
    monkeypatch.setattr(ch.pf,'attach_objective',lambda built,kind,payload:payloads.append(deepcopy(payload)))
    result=ch.complete_topology(h.case,h.selected,[1.],[2.],Budget(),deadline=10.,clock=h.clock)
    assert payloads==[[[(1.,0.)]],[[(1.,0.),(5.,-4.)]]]
    assert result['true_bill_exact']=='16'  # replay load2: ops10 +1*2 +.5*2*2².
