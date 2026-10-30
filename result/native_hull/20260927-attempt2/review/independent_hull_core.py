#!/usr/bin/env python3
"""Independent stored-number hull arithmetic and native witness helpers.

Only colocated independent auditors and Python standard library are imported.
Exact arithmetic concerns stored floats; no physical witness is repaired.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
import independent_native_raw as native

base=native.base
need,near=base.need,base.near
HERE=Path(__file__).resolve().parent
SCHEMA='egg-native-hull-v2'
POLICY='native-roundoff-qualification-v2'

def digest_object(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False).encode()).hexdigest()

def outward(q,up):
    q=Q(q);f=float(q)
    if (Q(f)<q if up else Q(f)>q):f=math.nextafter(f,math.inf if up else -math.inf)
    return f

def supply(m,load):return sum((Q(a)*x+Q(b)*x*x/2 for a,b,x in zip(m['a'],m['b'],load)),Q(0))

def conjugate(m,p):
    total=Q(0)
    for a,b,v in zip(m['a'],m['b'],p):
        d=Q(v)-Q(a)
        if d>0:
            need(b>0,'finite conjugate domain');total+=d*d/(2*Q(b))
    return total

def projection_key(load,ops):
    return digest_object({'schema':SCHEMA,'load':[float(x+0.).hex() for x in load],
                          'ops_cost':float(ops+0.).hex()})

def native_cell(cell,prices):
    return {'id':cell['id'],'case':cell['case'],'case_identity':cell['physical_identity'],
            'objective':'pricing','prices':prices}

def backend(stats,master=False):
    rt=stats['backend_runtime']
    need(stats['backend']=='CBC' and stats['threads']==1 and 0<stats['seconds_cap']<=10,'explicit native caps/backend')
    need(rt['requested']==rt['model_solver_name']=='CBC' and rt['solver_class']=='SolverCbc' and rt['solver_module']=='mip.cbc','CBC native runtime, no fallback')
    need(rt['native_library_sha256']=='fe44771023b133390daf7b72790c2ce65d1ccb2e5ac77c7a04c8d8f8648aff7d','reported CBC library fingerprint')
    need(stats['status']=='OPTIMAL' and stats['wall_s']>=0,'preserve observed OPTIMAL return')
    if master:need(stats['n_int']==0,'pure LP master')

def check_column(cell,column):
    need(column['schema']==SCHEMA and column['physical_identity']==cell['physical_identity'] and column['extraction_policy']==POLICY,'column physical/policy identity')
    need(column['witness_hash']==digest_object(column['plan']),'immutable whole-fleet witness hash')
    witness=base.physical(native_cell(cell,[0]*len(cell['market']['a'])),column['plan'])
    need(column['load']==witness['load'] and column['ops_cost']==witness['ops'],'fresh exact stored column projection')
    need(column['key']==projection_key(column['load'],column['ops_cost']),'exact projection key including intrinsic cost')
    return witness

def mixture(cell,columns,saved):
    need(saved['column_keys']==[c['key'] for c in columns] and saved['replayed_columns']==len(columns),'mixture immutable column order')
    data=saved['simplex'];raw=list(map(Q,data['raw']))
    need(len(raw)==len(columns),'simplex dimension')
    negative=sum((-w for w in raw if w<0),Q(0));positive=[max(w,Q(0)) for w in raw];mass=sum(positive,Q(0))
    need(data['tolerance']==1e-10 and mass>0 and negative<=Q(1e-10) and abs(mass-1)<=Q(1e-10),'fixed simplex correction policy')
    weights=[w/mass for w in positive]
    need(list(map(Q,data['weights_exact']))==weights and Q(data['negative_mass_exact'])==negative and Q(data['positive_mass_exact'])==mass,'exact simplex and all positive weights')
    need(Q(data['l1_correction_exact'])==sum((abs(a-b) for a,b in zip(raw,weights)),Q(0)),'simplex correction L1')
    load=[sum((w*Q(c['load'][t]) for w,c in zip(weights,columns)),Q(0)) for t in range(len(cell['market']['a']))]
    ops=sum((w*Q(c['ops_cost']) for w,c in zip(weights,columns)),Q(0));F=supply(cell['market'],load);value=ops+F
    need(list(map(Q,saved['load_exact']))==load and saved['load']==list(map(float,load)),'exact aggregate load and display')
    need(Q(saved['ops_exact'])==ops and Q(saved['supply_exact'])==F and Q(saved['objective_exact'])==value,'true cost of aggregate mixture')
    need(saved['upper']==outward(value,True),'outward exact mixture upper')
    return {'weights':weights,'load':load,'ops':ops,'objective':value,'negative_mass':negative,'mass_correction':abs(mass-1)}

def pool_bound(cell,columns,mix,saved):
    market=cell['market'];p=[float(Q(a)+Q(b)*x) for a,b,x in zip(market['a'],market['b'],mix['load'])]
    need(saved['prices']==p,'actual serialized true gradient')
    conj=conjugate(market,p)
    scores=[Q(c['ops_cost'])+sum((Q(v)*Q(e) for v,e in zip(p,c['load'])),Q(0)) for c in columns]
    lower=min(scores)-conj;gap=mix['objective']-lower
    need(gap>=0 and Q(saved['conjugate_exact'])==conj and Q(saved['pool_min_score_exact'])==min(scores),'restricted score and conjugate')
    need(Q(saved['pool_lower_exact'])==lower and Q(saved['pool_gap_exact'])==gap and saved['pool_gap']==outward(gap,True),'exact restricted-pool Fenchel gap')
    return gap

def global_bound(cell,prices,lower,saved):
    conj=conjugate(cell['market'],prices);exact=Q(lower)-conj
    need(saved['prices']==prices and saved['pricing_lower']==lower and Q(saved['conjugate_exact'])==conj,'global certificate provenance')
    need(Q(saved['lower_exact'])==exact and saved['lower']==outward(exact,False),'global native-lower Fenchel arithmetic')
    return exact

def check_tangents(cell,columns,start):
    market=cell['market'];rows=start['tangent_rows'];points=start['tangent_points']
    need(len(rows)==len(market['a']) and all(len(r)==len(points) for r in rows),'saved tangent shape')
    for t,(a,b) in enumerate(zip(market['a'],market['b'])):
        maximum=max(Q(c['load'][t]) for c in columns)
        for point,row in zip(points,rows[t]):
            q=Q(point[t]);slope=Q(a)+Q(b)*q;intercept=-Q(b)*q*q/2
            need(q>=0 and Q(row['point_exact'])==q and Q(row['exact_slope'])==slope and Q(row['exact_intercept'])==intercept,'exact ideal tangent')
            need(row['slope']==float(slope),'serialized tangent slope')
            pad=max(Q(0),Q(row['slope'])-slope)*maximum
            need(Q(row['rounding_pad_exact'])==pad and row['intercept']==outward(intercept-pad,False),'pool-box conservative tangent rounding')
            for endpoint in (Q(0),maximum):
                need(Q(row['slope'])*endpoint+Q(row['intercept'])<=slope*endpoint+intercept,'rounded line below exact tangent throughout pool box')

def exact_pair_min(cell,columns,rows=None):
    """Exact one-parameter optimization over each pool pair.

    This pair helper is complete for one/two-column masters. For the complete
    physical hull, all vertices share total energy and the minimum of c+F(e)
    lies on its lower piecewise-linear (early energy,cost) boundary; each edge
    uses at most two vertices. Pair enumeration is therefore complete here.
    """
    candidates=[];m=cell['market']
    for i,j in itertools.combinations_with_replacement(range(len(columns)),2):
        left,right=columns[i],columns[j]
        load=list(map(Q,left['load']));d=[Q(y)-x for x,y in zip(load,right['load'])]
        ops=Q(left['ops_cost']);dc=Q(right['ops_cost'])-ops;xs={Q(0),Q(1)}
        if rows is None:
            derivative=dc+sum(((Q(a)+Q(b)*x)*z for a,b,x,z in zip(m['a'],m['b'],load,d)),Q(0))
            curvature=sum((Q(b)*z*z for b,z in zip(m['b'],d)),Q(0))
            if curvature:xs.add(max(Q(0),min(Q(1),-derivative/curvature)))
            def objective(w):return ops+w*dc+supply(m,[x+w*z for x,z in zip(load,d)])
        else:
            lines=[[(Q(r['slope'])*z,Q(r['slope'])*x+Q(r['intercept'])) for r in rr] for rr,x,z in zip(rows,load,d)]
            for rr in lines:
                # Duplicate tangents add no breakpoints. This is auditor work
                # reduction only; all original rows remain individually checked.
                for (a,b),(aa,bb) in itertools.combinations(set(rr),2):
                    if a!=aa:
                        w=(bb-b)/(a-aa)
                        if 0<=w<=1:xs.add(w)
            def objective(w):return ops+w*dc+sum((max(a*w+b for a,b in rr) for rr in lines),Q(0))
        candidates.extend((objective(w),i,j,w) for w in xs)
    return min(candidates)

def complete_hull(cell):
    projections=base.branches(native_cell(cell,[0]*4));vertices=[]
    for ops,intercept,slope,lo,hi in projections:
        for x in {lo,hi}:
            vertices.append({'ops_cost':ops,'load':[a+b*x for a,b in zip(intercept,slope)]})
    need(vertices,'nonempty independently complete cyclic branches')
    value,i,j,w=exact_pair_min(cell,vertices)
    target=Q(cell['target_exact']);near(float(value),float(target),'complete analytical hull target',1e-10)
    load=[Q(a)+w*(Q(b)-Q(a)) for a,b in zip(vertices[i]['load'],vertices[j]['load'])]
    for x,y in zip(load,cell['load_target_exact']):near(float(x),float(Q(y)),'complete hull aggregate-load target',1e-10)
    return {'objective':value,'analytical_decimal_target':target,'vertices':vertices,'support_vertices':[i,j],'right_weight':w,'load':load}

def check_master(cell,columns,start,status,snapshot,replay):
    need(len(columns) in (1,2,3),'all executed master pools have at most three columns')
    stats=status['stats'];backend(stats,True);check_tangents(cell,columns,start)
    records=snapshot['variables'];mapping=snapshot['mapping'];n=len(columns);T=len(cell['market']['a'])
    need([r['index'] for r in records]==list(range(n+2*T)) and len(records)==stats['n_vars'],'all raw master variables')
    need(mapping=={'lambda':list(range(n)),'load':list(range(n,n+T)),'epigraph':list(range(n+T,n+2*T))},'raw master semantic mapping')
    need(stats['master_base_constraints']==T+1 and stats['n_constraints']==T+1+sum(map(len,start['tangent_rows'])),'exact master constraint counts')
    values=[native.value_record(r['solution']) for r in records];need(all(v is not None for v in values),'finite raw master primal')
    residuals=[]
    def le(a,b):residuals.append(max(Q(0),a-b))
    for k,r in enumerate(records):
        need(r['type']=='C','continuous master variable')
        lo=native.value_record(r['lower']);hi=native.value_record(r['upper'])
        if k<n:need(lo==0 and hi==1,'simplex declared bounds')
        elif k<n+T:need(lo==0 and hi==max(Q(c['load'][k-n]) for c in columns),'current pool load box')
        else:need(lo<-Q(10)**100 and hi>Q(10)**100,'free-below epigraph')
        le(lo,values[k]);le(values[k],hi)
    weights=values[:n];loads=values[n:n+T];epi=values[n+T:]
    mass=sum(weights,Q(0));le(mass,1);le(1,mass)
    for t,x in enumerate(loads):
        target=sum((w*Q(c['load'][t]) for w,c in zip(weights,columns)),Q(0))
        le(x,target);le(target,x)
        for row in start['tangent_rows'][t]:le(Q(row['slope'])*x+Q(row['intercept']),epi[t])
    need(max(residuals,default=Q(0))<=Q(1e-6),'raw LP primal reconstruction residual')
    raw_objective=sum((w*Q(c['ops_cost']) for w,c in zip(weights,columns)),Q(0))+sum(epi,Q(0))
    near(float(raw_objective),stats['incumbent'],'raw master objective',1e-6)
    need(stats['lower_bound']<=stats['incumbent']+1e-6,'master diagnostic lower/incumbent ordering')
    need(replay['raw_tangent_objective']==stats['incumbent'] and replay['mixture']['simplex']['raw']==list(map(float,weights)),'master raw-to-mixture provenance')
    mix=mixture(cell,columns,replay['mixture']);gap=pool_bound(cell,columns,mix,replay['pool'])
    exact=master_min(cell,columns,start['tangent_rows'])[0]
    near(stats['incumbent'],float(exact),'independent exact PWL master minimum',1e-6)
    near(stats['lower_bound'],float(exact),'independent exact PWL master diagnostic lower',1e-6)
    pool_opt=master_min(cell,columns)[0]
    need(mix['objective']>=pool_opt,'restricted true minimum versus feasible mixture')
    return {'call':start['call'],'objective':mix['objective'],'load':mix['load'],'weights':mix['weights'],
            'pool_gap':gap,'pool_true_optimum':pool_opt,'true_pool_suboptimality':mix['objective']-pool_opt,
            'exact_PWL_minimum':exact,'native_PWL_incumbent_minus_exact':Q(stats['incumbent'])-exact,
            'raw_LP_residual':max(residuals,default=Q(0)),'raw_variables':len(records),
            'tangent_points':len(start['tangent_points']),'unique_tangent_points':len(set(tuple(p) for p in start['tangent_points'])),
            'positive_weights':sum(w>0 for w in mix['weights'])}

def audit_pricing(cell,request,events,result_event,bound_event):
    prices=request['prices'];nc=native_cell(cell,prices)
    need([e['event'] for e in events]==['native_start','native_status','native_incumbent','charge_normalization','serial_decoding','objective_reconstruction'],'complete native pricing evidence order')
    need(all(e['round']==0 for e in events),'one native phase per pricing request')
    start,stats=events[0],events[1]['stats'];backend(stats)
    answer=result_event['result'];plan=answer['plan'];reference=base.scalar_min(nc)[0]
    need(answer['status'] in ('certified','bounded') and answer['case_identity']==cell['physical_identity'] and answer['prices']==prices and answer['stats']==stats,'native price identity/status')
    near(stats['incumbent'],float(reference),'complete exact fleet-pricing minimum',1e-6)
    near(stats['lower_bound'],float(reference),'complete exact fleet-pricing global lower',1e-6)
    raw=native.raw_primal(nc,start,stats,events[2]);correction=native.conversion(nc,raw,events[3],events[4],events[5],plan,start,stats)
    witness=base.physical(nc,plan);objective=witness['ops']+sum(p*e for p,e in zip(prices,witness['load']))
    near(objective,stats['incumbent'],'native pricing incumbent physical objective',1e-6)
    need(answer['lower']==stats['lower_bound']-1e-6 and answer['upper']==objective+1e-6,'native single outward bound guard')
    near(answer['gap'],answer['upper']-answer['lower'],'native pricing width',1e-12)
    need(Q(answer['lower'])<=reference<=Q(answer['upper']),'independent exact pricing optimum enclosed')
    column=bound_event['column'];need(column['plan']==plan and column['source']=={'state_identity':cell['state_identity'],'pricing_call':request['call']},'column provenance from physical native pricing')
    check_column(cell,column)
    lower=global_bound(cell,prices,answer['lower'],bound_event['certificate'])
    return {'call':request['call'],'seed':request['seed'],'prices':prices,'complete_price_minimum':reference,
            'native_incumbent':stats['incumbent'],'native_lower':stats['lower_bound'],'fenchel_lower':lower,
            'raw_variables':raw['variables'],'max_raw_constraint_residual':raw['max_constraint_residual'],
            'correction':correction,'physical_witness':witness}
