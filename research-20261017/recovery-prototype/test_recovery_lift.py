"""Handcrafted physical cases only; no solver-generated fixtures or datasets."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import importlib.abc
import sys

import pytest

from egglab import native_hull as nh
from egglab import native_recharge as nr
from recovery_lift import lift_plan


@pytest.fixture(autouse=True)
def forbid_solver_imports():
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in ('mip','gurobipy'):
                raise AssertionError('No solver imports permitted')
    guard=Guard()
    sys.meta_path.insert(0,guard)
    yield
    sys.meta_path.remove(guard)


def fixture():
    trip=nr.Trip('A',0,60,'D','D',15.)
    out=nr.Movement('out','pullout',None,'A',(nr.Leg('D','D',0,0,0.),))
    home=nr.Movement('home','pullin','A',None,(nr.Leg('D','D',60,60,0.),))
    source=nr.NativeCase('source',(trip,),(out,home),
        (nr.Resource(0,60,0.,0.,0),nr.Resource(60,120,30.,30.)),
        (0,60,120),'D',1,20.,1.,0,120,7.)
    extra=nr.Movement('extra','pullin','A',None,(nr.Leg('D','D',60,75,0.),))
    full=replace(source,name='full',movements=(extra,home,out))
    plan={'schema':nr.SCHEMA,'case_identity':source.identity(),
          'vehicles':[{'vehicle':0,'trips':['A'],'movements':['out','home']}],
          'charges':[{'vehicle':0,'movement':'home','connector':0,
                      'start_min':60.,'end_min':90.,'grid_kwh':15.}],
          'load':[0.,15.],'ops_cost':7.,
          'raw_solver_load':[999.], 'indexed_charge':{'stale':'DO NOT COPY'}}
    return source,full,plan


def test_permuted_ids_extra_edges_and_full_interval_split():
    source,full,plan=fixture()
    saved=deepcopy(plan)
    result=lift_plan(source,full,plan,a=[1.,2.],b=[0.,.2])
    assert result['binary_start_spec']==[
        {'movement_id':'extra','value':0},{'movement_id':'home','value':1},
        {'movement_id':'out','value':1}]
    source_intervals=nr.compile_case(source)['intervals']
    full_intervals=nr.compile_case(full)['intervals']
    assert len(full_intervals)>len(source_intervals)
    assert result['replay']['replay_ok'] and result['true_bill']==59.5
    assert result['plan']['case_identity']==full.identity()
    assert 'indexed_charge' not in result['plan'] and 'raw_solver_load' not in result['plan']
    assert result['provenance']['added_full_movement_ids']==['extra']
    assert result['global_lower_bound'] is None and result['start_status']=='not_submitted'
    assert plan==saved
    result['plan']['charges'][0]['grid_kwh']=0
    assert plan==saved


@pytest.mark.parametrize('corruption',['unknown','duplicate','changed'])
def test_movement_mapping_violations(corruption):
    source,full,plan=fixture()
    if corruption=='unknown':
        full=replace(full,movements=tuple(m for m in full.movements if m.id!='home'))
    elif corruption=='duplicate':
        full=replace(full,movements=full.movements+(full.movements[0],))
    else:
        full=replace(full,movements=tuple(replace(m,legs=(nr.Leg('D','D',60,61,0.),))
            if m.id=='home' else m for m in full.movements))
    with pytest.raises(ValueError,match='Unknown|Duplicate|Changed'):
        lift_plan(source,full,plan,a=[1.,1.],b=[0.,0.])


@pytest.mark.parametrize('corruption',['energy','unknown_selected','duplicate_selected','stored_bill'])
def test_invalid_physical_source_is_rejected(corruption):
    source,full,plan=fixture()
    if corruption=='energy': plan['charges'][0]['grid_kwh']=10.
    elif corruption=='unknown_selected': plan['vehicles'][0]['movements'][1]='missing'
    elif corruption=='duplicate_selected': plan['vehicles'][0]['movements'][1]='out'
    else: plan['ops_cost']=0.
    with pytest.raises(ValueError):
        lift_plan(source,full,plan,a=[1.,1.],b=[0.,0.])


def test_no_continuous_or_bounds_api_and_target_market_recomputed():
    source,full,plan=fixture()
    original=(source,full,deepcopy(plan))
    result=lift_plan(source,full,plan,a=[0.,4.],b=[0.,0.])
    assert result['true_bill']==67.
    assert all(set(entry)=={'movement_id','value'} for entry in result['binary_start_spec'])
    assert result['provenance']['continuous_start_policy']=='omit-all-continuous-variables'
    assert (source,full,plan)==original
    with pytest.raises(TypeError):
        lift_plan(source,full,plan,a=[0.,4.],b=[0.,0.],model=object())


def test_changed_nonmovement_physics_rejected():
    source,full,plan=fixture()
    with pytest.raises(ValueError,match='Changed full-case policy/physics'):
        lift_plan(source,replace(full,battery_kwh=21.),plan,a=[1.,1.],b=[0.,0.])


def test_fractional_bill_matches_canonical_exact_witness_evaluation():
    source,full,plan=fixture()
    trip=replace(source.trips[0],energy_kwh=15.1)
    source=replace(source,trips=(trip,))
    full=replace(full,trips=(trip,))
    plan['case_identity']=source.identity()
    plan['charges'][0].update(grid_kwh=15.1,end_min=100.)
    plan['load']=[0.,15.1]
    a,b=[.1,.3],[.2,.7]
    result=lift_plan(source,full,plan,a=a,b=b)
    replay=nr.replay_native(full,result['plan'])
    canonical=Fraction(replay['ops_cost'])+nh.supply(nh.Market('target',tuple(a),tuple(b)),replay['load'])
    assert Fraction(result['true_bill_exact'])==canonical
    assert result['true_bill']==float(canonical)
    # The exact rational cannot be reconstructed from a rounded float-only bill.
    assert Fraction(result['true_bill'])!=canonical
    assert Fraction(result['provenance']['source_replay_bill_at_target_market_exact'])==canonical
