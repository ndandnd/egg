#!/usr/bin/env python3
"""Solver-free independent audit of the FAILED first native-hull attempt.

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
COMMIT='f549100587cdf561c978e145e73e86dbadc9f27e'
MANIFEST_SHA='1326245d395c01226d44543e6479799a997fa523e9a4d3fe84272a1cc37a73de'
SCHEMA='egg-native-hull-v1'
POLICY='native-roundoff-qualification-v2'
EXPECTED={'nominal_cold_s0':'budget_exhausted','nominal_cold_s1':'certified',
 'nominal_cold_s2':'budget_exhausted','nominal_retained_s0':'budget_exhausted',
 'nominal_retained_s1':'blocked_by_predecessor','nominal_retained_s2':'blocked_by_predecessor',
 'joint_cold':'budget_exhausted','fixed_reserve_cold':'certified'}

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

    Every actual saved master here has one or two columns. For the complete
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
    need(len(columns) in (1,2),'all executed master pools are one- or two-column')
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
    exact=exact_pair_min(cell,columns,start['tangent_rows'])[0]
    near(stats['incumbent'],float(exact),'independent exact PWL master minimum',1e-6)
    near(stats['lower_bound'],float(exact),'independent exact PWL master diagnostic lower',1e-6)
    pool_opt=exact_pair_min(cell,columns)[0]
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

def audit_cell(cell,blob,budget):
    events=blob['events'];receipt=blob['receipt'];package=blob['result'];result=package['result'];name=cell['id']
    need(result['status']==receipt['status']==EXPECTED[name],'preserve exact first-attempt disposition')
    need(receipt['cell']==name and not receipt['timeout'] and receipt['evidence_issues']==[],'saved cell accounting provenance')
    expected_pass=EXPECTED[name]=='certified';target=complete_hull(cell)
    need(receipt['pass']==package['assessment']['pass']==expected_pass,'failures remain failed')
    if result['status']=='blocked_by_predecessor':
        need(cell['predecessor'] and result['predecessor']==cell['predecessor'] and receipt['returncode']==3,'blocked retained dependency')
        need(len(events)==1 and events[0]['event']=='dependency_blocked' and events[0]['result']==result,'blocked trace has no optimizer work')
        for k in ('master_starts','native_returns','native_starts','pricing_requests','pricing_starts','seed_requests'):need(receipt[k]==0,'blocked zero calls')
        need(receipt['native_accounting_complete'] and receipt['native_wall_s']==0,'empty blocked accounting')
        return {'cell':name,'status':result['status'],'pass':False,'complete_hull':target,'pricing':[],'masters':[]}
    need(receipt['returncode']==(0 if expected_pass else 1),'certified versus exhausted exit code')
    need(events[0]['event']=='state_start' and events[-1]['event']=='state_finish' and events[-1]['result']==result,'state lifecycle immutable result')
    need(events[0]['fresh_bounds'] is True and events[0]['imported_column_keys']==[],'no retained import actually occurred')
    for k in ('state_identity','market_identity'):need(events[0][k]==cell[k] and result[k]==cell[k],'state/market identity')
    need(result['physical_identity']==cell['physical_identity'] and result['schema']==SCHEMA and result['extraction_policy']==POLICY,'final case/schema/policy')
    pool=[];all_columns={};prices=[];masters=[];certificates=[];eligible=[];all_mixtures=[]
    tangent_points=[[0.]*len(cell['market']['a'])];last_master=None;walls=[];i=1
    while i<len(events)-1:
        event=events[i];kind=event['event']
        if kind=='pricing_request':
            call=event['call'];need(call==len(prices),'sequential counted pricing requests')
            need(event['seed']==(call==0),'exactly one counted cold seed')
            if call==0:need(event['prices']==cell['market']['a'],'generic p=a seed only')
            else:
                need(last_master is not None and last_master['pool']['prices']==event['prices'],'fresh master-gradient pricing')
                need(Q(last_master['pool']['pool_gap_exact'])<=Q(budget['pool_tolerance']),'pricing only after declared restricted gap threshold')
            native_events=[];i+=1
            while events[i]['event']=='pricing_native':
                need(events[i]['call']==call,'nested native call ownership');native_events.append(events[i]['detail']);i+=1
            answer,bound=events[i:i+2]
            need(answer['event']=='pricing_result' and bound['event']=='global_bound' and answer['call']==bound['call']==call,'pricing result/global-bound order')
            prices.append(audit_pricing(cell,event,native_events,answer,bound));walls.append(native_events[1]['stats']['wall_s'])
            certificates.append(bound['certificate']);column=bound['column']
            if call==0:
                pool.append(column);all_columns[column['key']]=column
                # Reconstruct the implicit exact singleton mixture, retained as
                # the initial feasible UB by the source even without a master.
                singleton=Q(column['ops_cost'])+supply(cell['market'],list(map(Q,column['load'])))
                eligible.append(singleton)
            i+=2
            if i<len(events)-1 and events[i]['event']=='column_added':
                added=events[i];need(column['key'] not in {c['key'] for c in pool} and added['key']==column['key'] and added['size']==len(pool)+1,'new distinct whole-fleet column')
                if added.get('after_certificate'):
                    need(expected_pass,'after-certificate column only on certified state')
                pool.append(column);all_columns[column['key']]=column;i+=1
        elif kind=='master_start':
            call=event['call'];need(call==len(masters),'sequential master calls')
            need(event['column_keys']==[c['key'] for c in pool],'complete current master pool order')
            need(event['tangent_points']==tangent_points,'immutable complete tangent history')
            status,snapshot,replay=events[i+1:i+4]
            need([e['event'] for e in (status,snapshot,replay)]==['master_status','master_incumbent','master_replay'] and all(e['call']==call for e in (status,snapshot,replay)),'master raw evidence lifecycle')
            record=check_master(cell,pool,event,status,snapshot,replay);masters.append(record);walls.append(status['stats']['wall_s']);all_mixtures.append(replay['mixture']);last_master=replay
            if record['pool_gap']<=Q(budget['pool_tolerance']):eligible.append(record['objective'])
            else:tangent_points.append(replay['mixture']['load'])
            i+=4
        else:raise AssertionError('unknown/out-of-order state event '+kind)
    need(result['columns']==pool,'final retained pool provenance')
    for c in result['columns']:check_column(cell,c)
    counts={'master_calls':len(masters),'pricing_requests':len(prices),'seed_requests':sum(p['seed'] for p in prices)}
    need(result['counts']==counts and counts['master_calls']<=budget['master_calls'] and counts['pricing_requests']<=budget['pricing_calls'],'cumulative source caps')
    for key,val in [('master_starts',len(masters)),('pricing_starts',len(prices)),('pricing_requests',len(prices)),('seed_requests',sum(p['seed'] for p in prices)),('native_starts',len(masters)+len(prices)),('native_returns',len(masters)+len(prices))]:need(receipt[key]==val,'receipt '+key)
    need(receipt['native_accounting_complete'],'complete unique native phase accounting');near(receipt['native_wall_s'],math.fsum(walls),'complete native wall accounting',1e-12)
    lower=max(Q(c['lower_exact']) for c in certificates);upper=min(eligible)
    need(result['lower_certificate'] in certificates and Q(result['lower_certificate']['lower_exact'])==lower,'best fresh global lower')
    final_columns=[all_columns[key] for key in result['mixture']['column_keys']];final_mix=mixture(cell,final_columns,result['mixture'])
    need(final_mix['objective']==upper,'source retains only successfully returned inner-master upper bounds')
    gap=upper-lower
    need(result['lower']==outward(lower,False) and result['upper']==outward(upper,True) and Q(result['gap_exact'])==gap and result['gap']==outward(gap,True),'final exact enclosure/display')
    need(lower<=target['objective']+Q(1e-10) and target['objective']<=upper+Q(1e-10),'complete hull optimum inside saved interval within physical tolerance')
    need(result['epsilon']==budget['epsilon'],'unchanged final epsilon')
    if expected_pass:
        need(0<=gap<=Q(budget['epsilon']) and result['reason'] is None,'true declared certificate criterion')
    else:
        need(len(masters)==64 and result['reason']=='master/time budget exhausted' and gap>Q(budget['epsilon']),'preserved master-cap failure')
        need(masters[-1]['pool_gap']>Q(budget['pool_tolerance']),'inner gap remains open at exhaustion')
    observed=min(m['objective'] for m in masters)
    final_load=masters[-1]['load'];tail=0
    for m in reversed(masters):
        if m['load']!=final_load:break
        tail+=1
    return {'cell':name,'status':result['status'],'pass':expected_pass,'complete_hull':target,
            'saved_interval':[lower,upper],'saved_width':gap,'best_observed_master_upper':observed,
            'upper_omitted_from_summary':upper-observed,'final_repeated_master_tail':tail,
            'unique_master_mixtures':len(set(tuple(m['load']) for m in masters)),
            'pricing':prices,'masters':masters,'counts':counts}

def corruption_controls(cells,blobs,budget):
    controls=[]
    def reject(label,name,change):
        c=copy.deepcopy(cells[name]);b=copy.deepcopy(blobs[name]);change(c,b)
        try:audit_cell(c,b,budget)
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError) as exc:controls.append({'control':label,'rejected':True,'reason':str(exc)})
        else:raise AssertionError('corrupted hull copy accepted: '+label)
    event=lambda b,kind:next(e for e in b['events'] if e['event']==kind)
    reject('failed state relabelled certified','nominal_cold_s0',lambda c,b:b['result']['result'].__setitem__('status','certified'))
    reject('blocked state invents native call','nominal_retained_s1',lambda c,b:b['receipt'].__setitem__('native_starts',1))
    reject('missing master return','nominal_cold_s1',lambda c,b:b['events'].remove(event(b,'master_status')))
    reject('raw master weight','nominal_cold_s1',lambda c,b:event(b,'master_incumbent')['variables'][0]['solution'].update(value=.8,repr='0.8'))
    reject('raw master semantic mapping','nominal_cold_s1',lambda c,b:event(b,'master_incumbent')['mapping']['lambda'].__setitem__(0,1))
    reject('master lower bound','nominal_cold_s1',lambda c,b:event(b,'master_status')['stats'].__setitem__('lower_bound',999))
    reject('native CBC fallback','nominal_cold_s1',lambda c,b:event(b,'master_status')['stats']['backend_runtime'].__setitem__('requested','GRB'))
    reject('tangent intercept raised','nominal_cold_s1',lambda c,b:event(b,'master_start')['tangent_rows'][1][0].__setitem__('intercept',1))
    reject('mutated solved tangent history','nominal_cold_s1',lambda c,b:event(b,'master_start')['tangent_points'].append([0]*4))
    reject('simplex exact positive weight omitted','nominal_cold_s1',lambda c,b:event(b,'master_replay')['mixture']['simplex']['weights_exact'].__setitem__(0,'0'))
    reject('mixture supply uses wrong value','nominal_cold_s1',lambda c,b:event(b,'master_replay')['mixture'].__setitem__('supply_exact','0'))
    reject('pool gap falsely zero','nominal_cold_s1',lambda c,b:event(b,'master_replay')['pool'].__setitem__('pool_gap_exact','0'))
    reject('global conjugate omitted','nominal_cold_s1',lambda c,b:next(e for e in b['events'] if e['event']=='global_bound' and e['call']==1)['certificate'].__setitem__('conjugate_exact','0'))
    reject('global lower uses fabricated value','nominal_cold_s1',lambda c,b:event(b,'global_bound')['certificate'].__setitem__('pricing_lower',1000))
    reject('column intrinsic cost','nominal_cold_s1',lambda c,b:event(b,'global_bound')['column'].__setitem__('ops_cost',0))
    reject('physical SOC corrupted','nominal_cold_s1',lambda c,b:event(b,'pricing_result')['result']['plan']['replay']['soc_trajectories'][0][-1].__setitem__('soc_kwh',0))
    reject('master cumulative count','nominal_cold_s1',lambda c,b:b['receipt'].__setitem__('master_starts',99))
    reject('final narrower interval invented','nominal_cold_s1',lambda c,b:b['result']['result'].__setitem__('lower',96.1875))
    return controls

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None));ap.add_argument('--out',type=Path);args=ap.parse_args()
    need(args.repository is not None,'supply frozen repository');repo=args.repository.resolve()
    out=args.out or Path(tempfile.gettempdir())/('egg-native-hull-independent-'+uuid.uuid4().hex+'.json');resolved=out.resolve()
    need(repo!=resolved and repo not in resolved.parents and not any((p/'.git').exists() for p in (resolved,*resolved.parents)),'output outside every detected repository')
    need(not out.exists() and not out.is_symlink(),'exclusively new report path')
    started=time.perf_counter();attempt=args.attempt;manifest=base.read(attempt/'MANIFEST.json')
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA and manifest['source_commit']==COMMIT,'original manifest/freeze identity')
    for p,item in manifest['files'].items():
        data=(attempt/p).read_bytes();need(base.digest(data)==item['sha256'] and len(data)==item['bytes'],'raw manifest '+p)
    actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file() and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
    need(actual==set(manifest['files']),'complete original raw manifest')
    frozen=base.read(attempt/'frozen.json');budget=frozen['budget']
    need(frozen['freeze_label']==COMMIT and frozen['protocol']=='native-hull-qualification-20260927-v1','frozen prospective hull protocol')
    for p,sha in frozen['source_hashes'].items():need(base.digest(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p]))==sha,'frozen source '+p)
    cells={c['id']:c for c in frozen['controls']};need(list(cells)==list(EXPECTED),'eight prospective cells/order')
    for c in cells.values():
        need(c['physical_identity']==digest_object({'schema':'egg-native-recharge-v1','case':c['case']}),'complete physical identity')
        need(c['market_identity']==digest_object(c['market']),'market identity')
        need(c['state_identity']==digest_object({'schema':SCHEMA,'case':c['physical_identity'],'market':c['market_identity'],'arm':c['arm'],'state_index':c['state_index'],'budget':budget,'extraction_policy':POLICY}),'state identity')
    summary=base.read(attempt/'summary.json');supervisor=base.read(attempt/'supervisor_receipt.json')
    need(summary['all_pass'] is False and summary['source_hashes_unchanged'] is True,'failed unchanged first attempt preserved')
    need(supervisor['returncode']==1 and supervisor['outer_timeout'] is False,'failed supervisor exit without timeout')
    blobs={}
    for receipt in summary['cells']:
        name=receipt['cell'];folder=attempt/name;inp=base.read(folder/'input.json')
        need(inp['control']==cells[name] and inp['budget']==budget and inp['source_hashes']==frozen['source_hashes'],'frozen input equality')
        need(receipt==base.read(folder/'receipt.json'),'raw receipt equality')
        blobs[name]={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()],'receipt':receipt,'result':base.read(folder/'result.json')}
    need(list(blobs)==list(cells),'all eight declared states accounted')
    records=[audit_cell(c,blobs[n],budget) for n,c in cells.items()]
    for c in cells.values():
        if c['predecessor']:need(not blobs[c['predecessor']]['receipt']['pass'],'both retained successors block failed predecessors')
    controls=corruption_controls(cells,blobs,budget)
    pricing=[p for r in records for p in r['pricing']];masters=[m for r in records for m in r['masters']]
    report={'audit_status':'PASS reconstruction of a FAILED scientific attempt; two certificates, four cap failures, two blocked dependencies',
        'frozen_commit':COMMIT,'original_manifest_sha256':MANIFEST_SHA,'raw_files':len(manifest['files']),
        'raw_bytes':sum(x['bytes'] for x in manifest['files'].values()),
        'auditor_sources':{p.name:base.digest(p.read_bytes()) for p in (HERE/'audit_native_hull.py',HERE/'independent_native_raw.py',HERE/'independent_fixture_core.py')},
        'counts':{'cells':len(records),'certified':sum(r['pass'] for r in records),'budget_exhausted':sum(r['status']=='budget_exhausted' for r in records),'blocked':sum(r['status']=='blocked_by_predecessor' for r in records),
            'pricing_calls':len(pricing),'master_calls':len(masters),'native_calls':len(pricing)+len(masters),
            'native_raw_variables':sum(p['raw_variables'] for p in pricing),'master_raw_variables':sum(m['raw_variables'] for m in masters),
            'physical_witnesses':len(pricing),'physical_sessions':sum(p['physical_witness']['sessions'] for p in pricing),
            'SOC_events':sum(p['physical_witness']['soc_events'] for p in pricing),'independent_PWL_master_minima':len(masters),'independent_global_pricing_minima':len(pricing)},
        'max_native_constraint_residual':max(p['max_raw_constraint_residual'] for p in pricing),
        'max_master_constraint_residual':max(m['raw_LP_residual'] for m in masters),
        'max_native_PWL_objective_error':max(abs(m['native_PWL_incumbent_minus_exact']) for m in masters),
        'max_combined_physical_correction':max(p['correction']['combined_correction'] for p in pricing),
        'cells':records,'corruption_controls':controls,
        'scope':'No author imports or native solver. Exact stored-number simplex/Fenchel/tangent arithmetic, analytical complete cyclic-fleet price/hull proofs, and complete one/two-column PWL LP minima; tolerance-conditional unchanged floating physical witnesses and native evidence. Failed statuses retained.',
        'audit_wall_s':time.perf_counter()-started}
    for p,item in manifest['files'].items():need(base.digest((attempt/p).read_bytes())==item['sha256'],'raw preservation '+p)
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'raw manifest preservation')
    with out.open('x') as f:json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps({'status':report['audit_status'],'out':str(resolved),'counts':report['counts'],'corruptions_rejected':len(controls),'wall_s':report['audit_wall_s']},indent=2))

if __name__=='__main__':main()
