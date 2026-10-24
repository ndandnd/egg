"""Handwritten symbolic cases only; CA1 ranks, never certifies feasibility."""
import builtins
from dataclasses import asdict, replace
import hashlib
import json

import pytest

_original_import = builtins.__import__
def _guard(name, *args, **kwargs):
    if name.split('.')[0] in {'mip', 'gurobipy'}:
        raise AssertionError('Native backend forbidden in classical control tests')
    return _original_import(name, *args, **kwargs)

builtins.__import__ = _guard
try:
    from egglab import classical_controls as cc
    from egglab.native_recharge import NativeCase, Trip, Leg, Movement, Resource
finally:
    builtins.__import__ = _original_import

@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins, '__import__', _guard)


def symbolic(n=12):
    trips = (Trip('A', 0, 10, 'X', 'X', 4.), Trip('B', 70, 80, 'Y', 'Y', 5.))
    boundaries = (Movement('outA','pullout',None,'A',(Leg('D','X',0,0,0.),)),
                  Movement('inA','pullin','A',None,(Leg('X','D',10,20,0.),)),
                  Movement('outB','pullout',None,'B',(Leg('D','Y',60,70,0.),)),
                  Movement('inB','pullin','B',None,(Leg('Y','D',80,90,0.),)))
    flexible = tuple(Movement(f'd{i:02}','direct','A','B',
                             (Leg('X','Y',10,11+i,2.),)) for i in range(n))
    return NativeCase('symbolic',trips,boundaries+flexible,
        (Resource(0,25,60.,30.),Resource(25,50,12.,24.),Resource(50,120,60.,30.)),
        (0,30,60,120),'D',2,10.,2.,0,120,100.,.1,.5)


def depot_case():
    base = symbolic(0)
    edge = Movement('via','depot','A','B',
                    (Leg('X','D',10,20,1.),Leg('D','Y',60,70,1.)),1)
    return replace(base,movements=base.movements+(edge,))


def feature(report, identity='via'):
    return next(row for row in report['features'] if row['movement_id']==identity)


def test_exact_cardinality_common_backbone_boundaries_and_nonmutation():
    case=symbolic(); before=asdict(case)
    low=cc.select_connections(case,[1000.]*4+list(range(12)))
    high=cc.select_connections(case,[-1000.]*4+list(reversed(range(12))))
    assert low['backbone_ids']==high['backbone_ids']==['d00','d01','d02']
    assert low['M']==12 and low['K']==high['K']==4
    assert low['exposure_slots']==1 and not low['zero_exposure']
    assert low['fill_ids']==['d11'] and high['fill_ids']==['d03']
    assert all(low['retained_mask'][:4]) and all(high['retained_mask'][:4])
    assert low['original_movement_ids']==[m.id for m in case.movements]
    assert len(low['retained_movement_ids'])==8 and asdict(case)==before
    assert low['retained_case_identity']!=low['case_identity']


def test_ties_and_input_permutation_use_ids_not_positions():
    case=symbolic(); first=cc.select_connections(case,[0.]*16)
    shuffled=replace(case,movements=tuple(reversed(case.movements)))
    second=cc.select_connections(shuffled,[0.]*16)
    assert first['fill_ids']==second['fill_ids']==['d03']
    assert first['backbone_ids']==second['backbone_ids']
    assert set(first['retained_movement_ids'])==set(second['retained_movement_ids'])
    assert second['retained_movement_ids']==[m.id for m,k in zip(shuffled.movements,second['retained_mask']) if k]


@pytest.mark.parametrize('n',[0,1,3,4,10,12])
def test_integer_ceiling_and_zero_exposure(n):
    case=symbolic(n); result=cc.select_connections(case,[0.]*(4+n))
    assert result['K']==min(n,max((3*n+9)//10,min(n,3)))
    assert result['zero_exposure'] is (result['K']==result['backbone_count'])
    assert sum(result['retained_mask'])==4+result['K']


@pytest.mark.parametrize('bad',[[0.]*15,[0.]*15+[float('nan')],[0.]*15+[float('inf')],[0.]*15+[True]])
def test_selector_rejects_invalid_score_vectors(bad):
    with pytest.raises(ValueError): cc.select_connections(symbolic(),bad)


def test_capacity_exact_resource_market_intersection_and_scalar_ledger():
    case=depot_case(); edge=case.movements[-1]
    assert cc._capacity_by_period(case,edge)==pytest.approx([3.5,9.,0.])
    row=feature(cc.ca1_score(case,[1.,2.,3.],[.5,0.,0.]))
    assert (row['window_start_min'],row['window_end_min'])==(20,60)
    assert row['total_grid_capacity_kwh']==12.5 and row['U_kwh']==6.25
    assert row['D_kwh']==3. and row['margin_kwh']==3.25
    assert row['stress_residuals_kwh']=={'predepot':-3.,'postdepot':-2.,'capacity':-3.25}
    assert not row['stress_flag'] and row['capacity_shortfall_kwh']==0.
    expected=hashlib.sha256(json.dumps([3.5,9.,0.],sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()
    assert row['capacity_by_period_sha256']==expected
    assert 'capacity_by_period' not in row
    assert row['replenishment_proxy']==pytest.approx(11.0256)
    assert row['movement_proxy']==0. and row['leg_minutes']==20.
    assert row['deadhead_proxy']==2. and row['proxy_cost']==pytest.approx(13.0256)


def test_price_shift_preserving_global_summaries_changes_local_proxy():
    case=depot_case()
    old=cc.ca1_score(case,[1.,2.,3.],[.5,0.,0.])
    shifted=cc.ca1_score(case,[2.,1.,3.],[.5,0.,0.])
    a,b=feature(old),feature(shifted)
    assert b['proxy_cost']==pytest.approx(10.3856) and a['proxy_cost']!=b['proxy_cost']
    for key in ('capacity_by_period_sha256','U_kwh','D_kwh','margin_kwh','stress_flag'):
        assert a[key]==b[key]
    assert old['tariff_sha256']!=shifted['tariff_sha256']
    # A price-aware proxy change alone need not change this single-edge ranking.
    assert old['scores']==shifted['scores']


def test_curvature_input_changes_proxy_without_changing_physical_features():
    case=depot_case()
    a=feature(cc.ca1_score(case,[1.,2.,3.],[0.,0.,0.]))
    b=feature(cc.ca1_score(case,[1.,2.,3.],[.5,0.,0.]))
    assert b['proxy_cost']-a['proxy_cost']==pytest.approx(.7056)
    assert a['margin_kwh']==b['margin_kwh'] and a['U_kwh']==b['U_kwh']


def test_zero_connector_positive_demand_is_diagnostic_not_deleted_or_certified():
    case=depot_case(); case=replace(case,resources=tuple(replace(r,connectors=0) for r in case.resources))
    report=cc.ca1_score(case,[1.,2.,3.],[0.,0.,0.]); row=feature(report)
    assert row['U_kwh']==0. and row['capacity_shortfall_kwh']==3.
    assert row['zero_capacity_positive_demand'] and row['stress_flag']
    assert row['replenishment_proxy']==0.
    assert not report['feasibility_certified'] and not report['bound_certified']
    assert 'via' in cc.select_connections(case,report['scores'])['retained_movement_ids']


def test_direct_capacity_is_zero_even_with_abundant_resources():
    case=symbolic(1)
    assert cc._capacity_by_period(case,case.movements[-1])==[0.,0.,0.]
    row=feature(cc.ca1_score(case,[1.,2.,3.],[0.,0.,0.]),'d00')
    assert row['U_kwh']==0. and row['stress_flag']
    assert row['window_start_min'] is None and row['window_end_min'] is None


@pytest.mark.parametrize('residual,stressed',[(.5e-6,False),(2e-6,True)])
def test_fixed_energy_tolerance_and_borderline_reporting(residual,stressed):
    case=symbolic(1)
    case=replace(case,trips=(replace(case.trips[0],energy_kwh=3.),replace(case.trips[1],energy_kwh=3.)),
                 movements=case.movements[:-1]+(replace(case.movements[-1],legs=(Leg('X','Y',10,11,2.+residual),)),))
    row=feature(cc.ca1_score(case,[0.,0.,0.],[0.,0.,0.]),'d00')
    assert row['stress_flag'] is stressed
    assert ('direct' in row['borderline_residuals_kwh']) is (not stressed)


def test_scores_are_original_order_integers_boundaries_unranked_and_id_ties():
    case=symbolic(2); edge=case.movements[-2]
    case=replace(case,movements=case.movements[:4]+(replace(edge,id='z'),replace(edge,id='a')))
    report=cc.ca1_score(case,[0.,0.,0.],[0.,0.,0.])
    assert report['flexible_order']==['a','z'] and report['scores']==[0,0,0,0,1,2]
    assert all(not row['ranked'] for row in report['features'][:4])
    assert report['case_identity']==case.identity()


@pytest.mark.parametrize('a,b',[([1.,2.],[0.,0.,0.]),([1.,2.,3.],[-1.,0.,0.]),
                                  ([float('nan'),2.,3.],[0.,0.,0.]),([True,2.,3.],[0.,0.,0.])])
def test_tariff_validation(a,b):
    with pytest.raises(ValueError): cc.ca1_score(depot_case(),a,b)


def test_negative_linear_prices_and_unclipped_proportional_cost():
    report=cc.ca1_score(depot_case(),[-1.,-2.,-3.],[0.,0.,0.])
    assert feature(report)['replenishment_proxy']==pytest.approx(-10.32)
    assert cc._proportional_proxy(12.,[1.,1.],[1.,1.],[0.,0.])==12.
    assert cc._proportional_proxy(0.,[0.,0.],[1.,1.],[0.,0.])==0.
    assert cc._proportional_proxy(12.,[0.,0.],[1.,1.],[0.,0.])==0.


def test_restrict_case_preserves_fields_order_and_original_case():
    case=symbolic(); before=asdict(case)
    reduced,ledger=cc.restrict_case(case,[0.]*16)
    assert asdict(case)==before
    assert reduced.movements==tuple(m for m,kept in zip(case.movements,ledger['retained_mask']) if kept)
    assert replace(reduced,movements=case.movements)==case
    assert ledger['restricted_identity']==ledger['retained_case_identity']==reduced.identity()
    assert all(m in reduced.movements for m in case.movements[:4])


def test_capacity_cannot_borrow_abundant_power_outside_verified_gap():
    case=depot_case()
    case=replace(case,resources=(Resource(0,20,1e6,1e6),Resource(20,60,0.,0.),Resource(60,120,1e6,1e6)))
    assert cc._capacity_by_period(case,case.movements[-1])==[0.,0.,0.]
    row=feature(cc.ca1_score(case,[1.,1.,1.],[0.,0.,0.]))
    assert row['zero_capacity_positive_demand'] and row['capacity_shortfall_kwh']==3.


def test_all_leg_minutes_include_stationary_leg_and_capacity_is_not_shared_certificate():
    case=depot_case(); edge=case.movements[-1]
    edge=replace(edge,legs=(Leg('X','D',10,20,1.),Leg('D','D',20,25,0.),Leg('D','Y',60,70,1.)),depot_split=2)
    case=replace(case,movements=case.movements[:-1]+(edge,replace(edge,id='via2')))
    report=cc.ca1_score(case,[0.,0.,0.],[0.,0.,0.])
    first,second=feature(report),feature(report,'via2')
    assert first['leg_minutes']==25. and first['deadhead_proxy']==2.5
    assert first['U_kwh']==second['U_kwh']  # Independent edge proxy; no contention allocation.
    assert first['capacity_by_period_sha256']==second['capacity_by_period_sha256']
    assert not report['feasibility_certified'] and not report['bound_certified']


def test_nonfinite_computed_proxy_fails_closed():
    with pytest.raises((ValueError,OverflowError)):
        cc.ca1_score(depot_case(),[1e308,1e308,1e308],[0.,0.,0.])


def test_invalid_identity_and_movement_ownership_rejected():
    case=symbolic(1)
    for bad in (replace(case,movements=case.movements+(case.movements[-1],)),
                replace(case,movements=case.movements[:-1]+(replace(case.movements[-1],before='missing'),))):
        with pytest.raises(ValueError): cc.select_connections(bad,[0.]*len(bad.movements))


def test_backbone_unions_distinct_incoming_and_outgoing_coverage_sets():
    case=symbolic()
    trip=Trip('C',90,100,'Z','Z',1.)
    boundary=(Movement('outC','pullout',None,'C',(Leg('D','Z',80,90,0.),)),
              Movement('inC','pullin','C',None,(Leg('Z','D',100,110,0.),)))
    # A's outgoing top3 are d00..02; C's incoming top3 must independently survive.
    extra=tuple(Movement(f'c{i:02}','direct','A','C',(Leg('X','Z',10,30+i,0.),)) for i in range(3))
    case=replace(case,trips=case.trips+(trip,),movements=case.movements+boundary+extra)
    first=cc.select_connections(case,list(range(len(case.movements))))
    second=cc.select_connections(case,list(reversed(range(len(case.movements)))))
    assert first['backbone_ids']==second['backbone_ids']==['c00','c01','c02','d00','d01','d02']
    assert first['M']==15 and (3*first['M']+9)//10==5
    assert first['K']==first['backbone_count']==6 and first['zero_exposure']
    assert not first['fill_ids'] and all(first['retained_mask'][:4])
