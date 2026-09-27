"""Pure arithmetic/fake-expression V2 energy-band qualification; no optimizer."""
from dataclasses import asdict, replace
from fractions import Fraction as Q
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace as Box

import pytest
from egglab import native_pathflow as pf
from experiments import native_pathflow_qualification as pq
from experiments import native_pathflow_hull_qualification as hq
from egglab import native_hull as hull

ROOT=Path(__file__).resolve().parents[2]


class Expr:
    def __init__(self,coeff=None,const=0.0,sense=None):
        self.coeff=dict(coeff or {});self.const=float(const);self.sense=sense
    @property
    def expr(self):return Box(items=lambda:[(Box(idx=k),v) for k,v in self.coeff.items()])
    def __add__(self,other):
        if hasattr(other,'as_expr'):other=other.as_expr()
        other=other if isinstance(other,Expr) else Expr(const=other)
        coeff=dict(self.coeff)
        for k,v in other.coeff.items():coeff[k]=coeff.get(k,0)+v
        return Expr(coeff,self.const+other.const)
    __radd__=__add__
    def __neg__(self):return self*-1
    def __sub__(self,other):return self+-other
    def __rsub__(self,other):return other+-self
    def __mul__(self,n):return Expr({k:v*n for k,v in self.coeff.items()},self.const*n)
    __rmul__=__mul__
    def relation(self,other,sense):
        e=self-other;e.sense=sense;return e
    def __le__(self,other):return self.relation(other,'<=')
    def __ge__(self,other):return self.relation(other,'>=')
    def __eq__(self,other):return self.relation(other,'==')


class FakeModel:
    def __init__(self,**kwargs):self.vars=[];self.rows=[]
    def add_var(self,lb=0,ub=math.inf,var_type='C'):
        idx=len(self.vars);v=Expr({idx:1.0});v.idx=idx;v.lb=lb;v.ub=ub;v.var_type=var_type;v.name=str(idx);v.x=None
        self.vars.append(v);return v
    @property
    def num_rows(self):return len(self.rows)
    def __iadd__(self,row):self.rows.append(row);return self


def build_fake(monkeypatch,case):
    monkeypatch.setitem(sys.modules,'mip',Box(Model=FakeModel,MINIMIZE='MIN',BINARY='B',xsum=lambda xs:sum(xs,Expr())))
    monkeypatch.setattr(pf.nr,'_backend_identity',lambda *args:{'fake':True})
    return pf.build_feasible_model(case)


def test_all20_definitions_budgets_and8_hull_definitions_preserved():
    old=json.loads((ROOT/'result/native_pathflow/20260927-attempt1/frozen.json').read_bytes())
    now=[{**c,'case':asdict(c['case']),'case_identity':c['case'].identity()} for c in pq.controls()]
    assert json.loads(json.dumps(now))==old['controls']
    budget=pf.Budget(backend='CBC',threads=1,phase_seconds=10,wall_seconds=45,max_rounds=48,epsilon=1e-4)
    assert asdict(budget)==old['budget']
    previous=json.loads((ROOT/'result/native_pathflow_hull/20260927-attempt1/frozen.json').read_bytes())
    newer=[hq.manifest(c,hull.Budget()) for c in hq.controls()]
    strip=lambda c:{k:v for k,v in c.items() if k not in ('state_identity','pricing_oracle')}
    assert [strip(c) for c in previous['controls']]==json.loads(json.dumps([strip(c) for c in newer]))
    assert asdict(hull.Budget())==previous['budget']
    assert all(c['pricing_oracle']==pf.FORMULATION for c in newer)
    assert all(a['state_identity']!=b['state_identity'] for a,b in zip(previous['controls'],newer))


def test_all20_fixed_synthetic_bands_are_exact_equalities():
    for c in pq.controls():
        s=pf.energy_balance_spec(c['case']);expected=sum(Q(t.energy_kwh) for t in c['case'].trips)
        assert Q(s['union_lower_exact'])==Q(s['union_upper_exact'])==expected
        assert Q(s['lower_rhs'])==Q(s['upper_rhs'])==expected
        assert s['charge_coefficient']==c['case'].efficiency and s['selected_mode_cap']==2*len(c['case'].trips)


def test_archived_v1_hull_pool_cannot_cross_v2_oracle_boundary(monkeypatch):
    from egglab import native_pathflow_hull as integrated
    previous=json.loads((ROOT/'result/native_pathflow_hull/20260927-attempt1/nominal_retained_s0/result.json').read_bytes())['result']
    assert previous['pricing_oracle']=='egg-native-pathflow-v1'
    cell=next(c for c in hq.controls() if c['id']=='nominal_retained_s1')
    monkeypatch.setattr(pf,'solve_pricing',lambda *a,**k:pytest.fail('Pricing reached across version boundary'))
    with pytest.raises(ValueError,match='oracle identity'):
        integrated.certify(cell['case'],cell['market'],arm='retained',state_index=1,
            previous=previous,expected_previous=previous['state_identity'])


def test_public_profiles_match_independently_derived_band_and_outward_endpoints():
    from experiments.sistig_native_case import native_case_from_payload
    p=json.loads((ROOT/'data/public/sistig_26088190_v1/hildenbrand_native_cases.json').read_bytes())
    for v in p['native_cases']:
        s=pf.energy_balance_spec(native_case_from_payload(v))
        lo=Q(250264333071608001,281474976710656);hi=Q(250264333071609185,281474976710656)
        assert Q(s['union_lower_exact'])==lo and Q(s['union_upper_exact'])==hi
        assert Q(s['lower_rhs'])<=lo<=hi<=Q(s['upper_rhs'])
        assert Q(math.nextafter(s['lower_rhs'],math.inf))>lo
        assert Q(math.nextafter(s['upper_rhs'],-math.inf))<hi
        assert any(Q(m['energy_aggregation_defect_exact']) for m in s['modes'])
        assert any(Q(m['residual_constant_defect_exact']) for m in s['modes'])


def test_pure_fractional_witness_satisfies_v1_rows_but_is_cut(monkeypatch):
    from experiments.native_recharge_qualification import cyclic_case
    case=cyclic_case();b=build_fake(monkeypatch,case);m=b['model']
    ids={mode.id:j for j,mode in enumerate(case.movements)}
    values={v.idx:Q(0) for v in m.vars}
    for mid,x in {'out_A':1,'in_A':Q(1,4),'out_B':Q(1,4),'in_B':1,'depot_AB':Q(3,8),'direct_AB':Q(3,8)}.items():
        values[b['x'][ids[mid]].idx]=Q(x)
    for var,value in zip(b['soc_before'],[20,Q(35,2)]):values[var.idx]=Q(value)
    for var,value in zip(b['soc_after'],[5,Q(5,2)]):values[var.idx]=Q(value)
    values[b['charge'][ids['in_B'],3].idx]=Q(35,2)
    for t,L in enumerate(b['loads']):values[L.idx]=Q(35,2) if t==3 else Q(0)
    bad=[]
    for i,row in enumerate(m.rows):
        residual=sum(Q(a)*values[k] for k,a in row.coeff.items())+Q(row.const)
        ok=(residual<=0 if row.sense=='<=' else residual>=0 if row.sense=='>=' else residual==0)
        if not ok:bad.append((i,residual))
    assert bad==[(b['energy_balance_row_indices'][0],Q(-25,2))]
    assert b['energy_balance_row_indices'][1] not in [i for i,_ in bad]
    assert b['constraint_count_before_objective']==38 # V1 nominal had36 rows.


def test_actual_fake_expression_rows_and_raw_ledger_agree(monkeypatch):
    c=pq.multivisit_case();b=build_fake(monkeypatch,c)
    for v in b['model'].vars:v.x=0.0
    raw=pf.capture_incumbent(c,b)
    assert raw['energy_balance']['constraint_indices']==b['energy_balance_row_indices']
    assert raw['energy_balance']['policy']==pf.ENERGY_BALANCE_POLICY
    rows=[b['model'].rows[i] for i in b['energy_balance_row_indices']]
    assert rows[0].sense=='>=' and rows[1].sense=='<='
    for row in rows:
        for v in b['charge'].values():assert row.coeff[v.idx]==c.efficiency
        for j,entry in enumerate(b['energy_balance']['modes']):assert row.coeff.get(b['x'][j].idx,0)==-entry['energy_float']


def test_unknown_expression_constant_rounding_fails_closed(monkeypatch):
    original=pf.energy_balance_spec
    def altered(c):
        s=original(c);s['modes'][0]['normalized_minus_constant_float']+=1;return s
    monkeypatch.setattr(pf,'energy_balance_spec',altered)
    with pytest.raises(ValueError,match='normalization differs'):build_fake(monkeypatch,pq.controls()[0]['case'])


def test_hidden_tiny_service_constant_elision_fails_closed(monkeypatch):
    original=Expr.__sub__
    monkeypatch.setattr(Expr,'__sub__',lambda self,other:self if isinstance(other,(int,float)) and 0<abs(other)<1e-63 else original(self,other))
    c=pq.controls()[0]['case'];c=replace(c,trips=(replace(c.trips[0],energy_kwh=1e-70),))
    with pytest.raises(ValueError,match='service row assembly'):build_fake(monkeypatch,c)


def test_hidden_aggregate_coefficient_elision_fails_closed(monkeypatch):
    monkeypatch.setattr(Expr,'expr',property(lambda self:Box(items=lambda:[])))
    with pytest.raises(ValueError,match='aggregate coefficients'):build_fake(monkeypatch,pq.controls()[0]['case'])


def test_full_battery_pullout_zero_constant_var_alias_is_supported(monkeypatch):
    class AliasingVar:
        """Model the real Var-0 behavior: no .const attribute on a Var."""
        def __init__(self,var):self.var=var;self.idx=var.idx
        def as_expr(self):return Expr(self.var.coeff)
        def __add__(self,other):return self.as_expr()+other
        __radd__=__add__
        def __sub__(self,other):
            if isinstance(other,(int,float)) and other==0:return self
            return self.as_expr()-other
        def __rsub__(self,other):return other-self.as_expr()
        def __neg__(self):return -self.as_expr()
        def __mul__(self,n):return self.as_expr()*n
        __rmul__=__mul__
        def __le__(self,o):return self.as_expr()<=o
        def __ge__(self,o):return self.as_expr()>=o
        def __eq__(self,o):return self.as_expr()==o
    original=FakeModel.add_var
    def alias_var(self,**kwargs):
        v=AliasingVar(original(self,**kwargs));self.vars[-1]=v;return v
    monkeypatch.setattr(FakeModel,'add_var',alias_var)
    n=pf.nr
    case=n.NativeCase('full_battery_pullout',(n.Trip('A',10,20,'D','D',0),),
        (n.Movement('out','pullout',None,'A',(n.Leg('D','D',0,10,20),)),
         n.Movement('in','pullin','A',None,(n.Leg('D','D',20,20,0),))),
        (n.Resource(0,60,30,30),),(0,60),'D',1,20,0,0,60,7)
    b=build_fake(monkeypatch,case)
    assert not hasattr(b['x'][0],'const')
    assert b['energy_balance']['modes'][0]['residual_constant_float']==0
    plan={'schema':n.SCHEMA,'case_identity':case.identity(),
        'vehicles':[{'vehicle':0,'trips':['A'],'movements':['out','in']}],
        'charges':[{'vehicle':0,'movement':'in','connector':0,'start_min':20,'end_min':60,'grid_kwh':20}],
        'load':[20],'ops_cost':7}
    assert n.replay_native(case,plan,[1])['pricing_objective']==27
