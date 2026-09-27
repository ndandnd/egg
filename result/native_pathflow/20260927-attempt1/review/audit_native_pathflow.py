#!/usr/bin/env python3
"""Independent compact path-flow raw matrix, witness and exact fixture audit.

Imports only the colocated independent_fixture_core and Python standard library.
No author module or native optimizer is imported/executed.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
import independent_fixture_core as base

HERE=Path(__file__).resolve().parent
COMMIT='ebb146e9de01d0c6aa13b03eb2348337a1d0b3f0'
MANIFEST_SHA='2ab225a5b79cf278c5ef55c834ba835a65126f09f370b9b967e5fac8a2f5327d'
POLICY='native-roundoff-qualification-v2'
TOL=Q(1e-8)
base.FAILURES={}
CBC_V2_FROZEN_SHA='76da01c8ede9ce709e5ba5986af5820fd5a2f0c47bb51ffec9c782e65da375bc'
NEW_IDENTITIES={'halfminute_multileg':'66c639a35b6806ef2b4f9f5ed728d02f654018c3515a61a0d26fbf55f190053b','halfminute_capacity':'5080e04d419cb22921f19ecbd0071b30a49195e4cdcce0aecd4bc59a6a4027de','halfminute_capacity_failure':'99262cd3908c4814c1dfe5272e7e9dd0419d66886d50f1a1d482c464cf08ce03','halfminute_coincidence':'b884844d2d9b59b8216edf34524ae643336f251b26d3e8b24060ce463329aa95'}
need,near=base.need,base.near
base.TARGETS.update(halfminute_multileg=Q(36),halfminute_capacity=Q(15,2),
                    halfminute_capacity_failure=None,halfminute_coincidence=Q(9),three_service_multivisit=Q(1423,19))
_original_branches=base.branches

def branches(cell):
    if cell['id']=='three_service_multivisit':
        c=cell['case']; need(c['max_vehicles']==1 and len(c['trips'])==3,'multivisit fixed single bus')
        need([t['id'] for t in c['trips']]==['A','B','C'] and [t['energy_kwh'] for t in c['trips']]==[8]*3,'multivisit service definition')
        need(set(m['id'] for m in c['movements'])=={'out_A','in_A','out_B','in_B','out_C','in_C','depot_AB','depot_BC'},'complete multivisit declared mode graph')
        # One bus and service A's only incoming out_A force the unique path
        # out_A -> depot_AB -> depot_BC -> in_C. Sum all selected energy/time.
        chosen=[m for m in c['movements'] if m['id'] in {'out_A','depot_AB','depot_BC','in_C'}]
        energy=sum(Q(t['energy_kwh']) for t in c['trips'])+sum(Q(l['energy_kwh']) for m in chosen for l in m['legs'])
        duration=sum(Q(l['arrive_min'])-Q(l['depart_min']) for m in chosen for l in m['legs'])
        need(energy==36 and duration==60 and all(p==1 for p in cell['prices']),'multivisit exact total energy/cost and flat prices')
        eta=Q(c['efficiency']); total=energy/eta
        # Feasible constructive allocation:10kWh in40..60,10 in120..140,
        # then total-20 in200..240. Reserve and capacity can be checked exactly.
        need(Q(1)<=Q(8)+10*eta<=20 and Q(1)<=Q(-4)+20*eta<=20,'multivisit charge SOC bounds')
        need(Q(-14)+20*eta>=Q(1) and 0<=total-20<=20,'multivisit final arrival and terminal capacity')
        ops=Q(c['vehicle_cost'])+Q(c['deadhead_cost_per_min'])*duration
        return [(ops,[Q(10),Q(0),Q(10),total-20],[Q(0)]*4,Q(0),Q(0))]
    if not cell['id'].startswith('halfminute_'):
        return _original_branches(cell)
    if cell['id']!='halfminute_coincidence':
        c=cell['case'];need(len(c['trips'])==1,'new single-service fixture')
        energy=Q(c['trips'][0]['energy_kwh'])+sum((Q(l['energy_kwh']) for m in c['movements'] for l in m['legs']),Q(0))
        total=energy/Q(c['efficiency'])
        returned=Q(next(m['legs'][-1]['arrive_min'] for m in c['movements'] if m['kind']=='pullin'))
        capacity=sum((Q(min(r['per_bus_kw'],r['grid_kw']))*max(Q(0),Q(r['end_min'])-max(returned,Q(c['terminal_open_min']),Q(r['start_min'])))/60
                      for r in c['resources'] if r['connectors']),Q(0))
        if total>capacity:return []
        duration=sum((Q(l['arrive_min'])-Q(l['depart_min']) for m in c['movements'] for l in m['legs']),Q(0))
        ops=Q(c['vehicle_cost'])+Q(c['deadhead_cost_per_min'])*duration
        need(len(c['market_edges_min'])==3 and returned>=Q(c['market_edges_min'][1]),'new fixed terminal allocation')
        return [(ops,[Q(0),total],[Q(0),Q(0)],Q(0),Q(0))]
    # The immutable fixture has one bus and only one service-covering path:
    # pullout A -> depot AB -> pullin B. A consumes 1, then the instantaneous
    # outbound depot leg consumes 1; zero-energy B finishes at 2. Full initial
    # SOC=capacity=1 forces exactly 1 kWh in [.5,1.5] and 1 in [2,2.5].
    c=cell['case']
    need(c['max_vehicles']==1 and c['battery_kwh']==c['efficiency']==1 and c['reserve_kwh']==0,
         'coincidence complete physical branch')
    need([t['energy_kwh'] for t in c['trips']]==[1,0] and len(c['movements'])==5,
         'coincidence declared service/path graph')
    return [(Q(7),[Q(0),Q(1),Q(0),Q(1)],[Q(0)]*4,Q(0),Q(0))]

base.branches=branches

def definition_checks(cells,repo):
    prior=repo/'result/native_halfminute/20260927-attempt1/frozen.json'
    old=json.loads(prior.read_bytes())['controls']
    need(list(cells.values())[:19]==old,'all nineteen timing control JSON objects unchanged')
    for cell in cells.values():
        c=cell['case'];times=list(c['market_edges_min'])+[c['terminal_open_min'],c['recharge_deadline_min']]
        times += [t[k] for t in c['trips'] for k in ('start_min','end_min')]
        times += [l[k] for m in c['movements'] for l in m['legs'] for k in ('depart_min','arrive_min')]
        need(all(type(x) in (int,float) and Q(x)>=0 and Q(x)<=2**20 and (2*Q(x)).denominator==1 for x in times),'exact halfminute input times')
    return {'old_control_JSON_unchanged':19,'new_three_service_case':True,
            'timing_reference_sha256':base.digest(prior.read_bytes())}


def value_record(entry):
    value=entry['value']; representation=entry['repr']
    if value is None:
        need(representation in ('inf','-inf','None','nan'),'unknown absent numeric representation')
        return None
    need(math.isfinite(value) and float(representation)==value,'raw numeric representation')
    return Q(value)


def intervals(case):
    windows={}
    for m in case['movements']:
        if m['kind']=='depot': windows[m['id']]=(m['legs'][m['depot_split']-1]['arrive_min'],m['legs'][m['depot_split']]['depart_min'])
        elif m['kind']=='pullin': windows[m['id']]=(max(m['legs'][-1]['arrive_min'],case['terminal_open_min']),case['recharge_deadline_min'])
    edges=set(case['market_edges_min'])|{case['terminal_open_min']}
    for r in case['resources']: edges|={r['start_min'],r['end_min']}
    for a,b in windows.values(): edges|={a,b}
    out=[]
    for a,b in zip(sorted(edges),sorted(edges)[1:]):
        resource=next(r for r in case['resources'] if r['start_min']<=a and b<=r['end_min'])
        period=next(k for k,(x,y) in enumerate(zip(case['market_edges_min'],case['market_edges_min'][1:])) if x<=a and b<=y)
        rate=min(resource['per_bus_kw'],resource['grid_kw']) if resource['connectors'] else 0.
        out.append({'start':a,'end':b,'hours':(b-a)/60,'period':period,'rate_kw':rate,'visits':[mid for mid,(x,y) in windows.items() if x<=a and b<=y]})
    return out


def raw_primal(cell,start,stats,snapshot):
    case=cell['case'];trips=case['trips'];modes=case['movements'];mp=snapshot['mapping'];records=snapshot['variables']
    need(snapshot['case_identity']==cell['case_identity'] and snapshot['extraction_policy']==POLICY,'raw snapshot identity/policy')
    need(snapshot['formulation']=='egg-native-pathflow-v1','compact raw formulation identity')
    need([r['index'] for r in records]==list(range(len(records))) and len(records)==stats['n_vars'],'complete raw indices')
    need(mp['trip_ids']==[t['id'] for t in trips] and mp['movement_ids']==[m['id'] for m in modes],'semantic IDs')
    grid=intervals(case);need(mp['intervals']==grid,'independent elementary intervals')
    vals={r['index']:value_record(r['solution']) for r in records};need(all(v is not None for v in vals.values()),'finite raw incumbent')
    N,M,T=len(trips),len(modes),len(case['market_edges_min'])-1
    for key,size in [('movement_selection',M),('soc_before',N),('soc_after',N),('market_load',T)]:need(len(mp[key])==size,'flat mapping shape '+key)
    allidx=sum((mp[k] for k in ['movement_selection','soc_before','soc_after','market_load','epigraph']),[])+[r['variable'] for r in mp['grid_energy']]
    need(len(allidx)==len(set(allidx))==len(records) and set(allidx)==set(vals),'complete unique flat variable mapping')
    violations=[];constraints=Counter()
    def le(a,b,tag):
        v=max(Q(0),a-b);violations.append(v);constraints[tag]+=1
        need(v<=TOL,'compact '+tag+' residual '+str(float(v)))
    def eq(a,b,tag):le(a,b,tag);le(b,a,tag)
    def declared(idx,kind,lo,hi=None):
        r=records[idx];need(r['type']==kind,'raw type')
        lower,upper=value_record(r['lower']),value_record(r['upper']);need(lower==Q(lo),'raw declared lower')
        if hi is not None:need(upper==Q(hi),'raw declared upper')
        if lower is not None:le(lower,vals[idx],'variable lower')
        if upper is not None:le(vals[idx],upper,'variable upper')
        if kind=='B':need(min(abs(vals[idx]),abs(vals[idx]-1))<=TOL,'binary integrality')
    B,r,eta=Q(case['battery_kwh']),Q(case['reserve_kwh']),Q(case['efficiency'])
    x=[vals[i] for i in mp['movement_selection']];sb=[vals[i] for i in mp['soc_before']];sa=[vals[i] for i in mp['soc_after']]
    for idx in mp['movement_selection']:declared(idx,'B',0,1)
    for idx in mp['soc_before']+mp['soc_after']:declared(idx,'C',r,B)
    raw={tuple(z['key']):vals[z['variable']] for z in mp['grid_energy']};indices={tuple(z['key']):z['variable'] for z in mp['grid_energy']}
    need(len(raw)==len(mp['grid_energy']),'unique compact energy keys')
    expected={(j,k) for k,g in enumerate(grid) for j,m in enumerate(modes) if m['id'] in g['visits'] and g['rate_kw']>0}
    need(set(raw)==expected,'complete flat eligible energy variables')
    for (j,k),e in raw.items():
        cap=Q(grid[k]['rate_kw']*grid[k]['hours']);declared(indices[j,k],'C',0,cap);le(e,cap*x[j],'owned energy activation')
    for k,g in enumerate(grid):le(sum(e for (j,kk),e in raw.items() if kk==k),Q(g['rate_kw']*g['hours']),'shared interval capacity')
    starts=sum(x[j] for j,m in enumerate(modes) if m['kind']=='pullout');ends=sum(x[j] for j,m in enumerate(modes) if m['kind']=='pullin')
    le(starts,Q(case['max_vehicles']),'fleet path cap');eq(starts,ends,'start end count')
    tid={t['id']:i for i,t in enumerate(trips)}
    for i,t in enumerate(trips):
        eq(sum(x[j] for j,m in enumerate(modes) if m['after']==t['id']),Q(1),'incoming flow')
        eq(sum(x[j] for j,m in enumerate(modes) if m['before']==t['id']),Q(1),'outgoing flow')
        eq(sa[i],sb[i]-Q(t['energy_kwh']),'service SOC')
    for j,m in enumerate(modes):
        e=Q(sum(l['energy_kwh'] for l in m['legs']));big=B+e;selected=x[j];charge=sum(z for (jj,k),z in raw.items() if jj==j)
        if m['kind']=='pullout':res=sb[tid[m['after']]]-(B-e)
        elif m['kind']=='direct':res=sb[tid[m['after']]]-sa[tid[m['before']]]+e
        elif m['kind']=='depot':
            incoming=Q(sum(l['energy_kwh'] for l in m['legs'][:m['depot_split']]));arr=sa[tid[m['before']]]-incoming
            le(r-big*(1-selected),arr,'depot arrival reserve');le(arr+eta*charge,B+big*(1-selected),'depot battery capacity')
            res=sb[tid[m['after']]]-sa[tid[m['before']]]+e-eta*charge
        else:
            arr=sa[tid[m['before']]]-e;le(r-big*(1-selected),arr,'terminal arrival reserve');res=arr+eta*charge-B
        le(res,big*(1-selected),'movement SOC upper');le(-res,big*(1-selected),'movement SOC lower')
    loads=[vals[i] for i in mp['market_load']]
    for t,idx in enumerate(mp['market_load']):
        declared(idx,'C',0);eq(loads[t],sum(z for (j,k),z in raw.items() if grid[k]['period']==t),'market energy sum')
    base_rows=2+3*N+len(raw)+len(grid)+2*M+sum(2 if m['kind']=='depot' else 1 if m['kind']=='pullin' else 0 for m in modes)+T
    need(stats['physical_constraints']==base_rows,'complete compact physical row count')
    need(stats['n_int']==M,'compact integer dimension')
    need(stats['n_vars']==M+2*N+len(raw)+T+len(mp['epigraph']),'compact variable dimension')
    ops=Q(case['vehicle_cost'])*starts+Q(case['deadhead_cost_per_min'])*sum(x[j]*sum(Q(l['arrive_min'])-Q(l['depart_min']) for l in m['legs']) for j,m in enumerate(modes))
    if cell['objective']=='pricing':
        need(not mp['epigraph'],'pricing has no epigraph');objective=ops+sum(Q(p)*L for p,L in zip(cell['prices'],loads));expected_rows=base_rows
    else:
        need(len(mp['epigraph'])==T,'planner epigraph shape');expected_rows=base_rows+sum(len(row) for row in start['tangents'])
        for t,idx in enumerate(mp['epigraph']):
            rr=records[idx];need(rr['type']=='C' and value_record(rr['lower'])<-Q(10)**100,'free-below epigraph')
            for slope,intercept in start['tangents'][t]:le(Q(slope)*loads[t]+Q(intercept),vals[idx],'saved tangent row')
        objective=ops+sum(vals[i] for i in mp['epigraph'])
    need(stats['n_constraints']==expected_rows,'complete native row count including objective')
    near(float(objective),stats['incumbent'],'raw compact objective',1e-6)
    # Independent path traversal from the flat selected graph, without author helpers.
    chosen=[m for j,m in enumerate(modes) if x[j]>Q(1,2)];owners={};paths=[];covered=[]
    for first in [m for m in chosen if m['kind']=='pullout']:
        vi=len(paths);m=first;seq=[];path=[]
        while True:
            need(m['id'] not in owners,'no repeated/merged selected mode');owners[m['id']]=vi;path.append(m['id'])
            if m['after'] is None:need(m['kind']=='pullin','path ends at terminal');break
            t=m['after'];need(t not in covered,'unique selected service ownership');covered.append(t);seq.append(t)
            nxt=[n for n in chosen if n['before']==t];need(len(nxt)==1,'unique successor');m=nxt[0]
        paths.append({'vehicle':vi,'trips':seq,'movements':path})
    need(set(owners)=={m['id'] for m in chosen} and sorted(covered)==sorted(tid),'complete selected path partition')
    need(0<len(paths)<=case['max_vehicles'],'derived used fleet cap')
    return {'variables':len(records),'raw_objective':objective,'max_constraint_residual':max(violations,default=Q(0)),
            'constraint_checks':dict(constraints),'raw_energy':raw,'x':x,'grid':grid,'native_load':loads,
            'owners':owners,'paths':paths}


def conversion(cell,raw,norm,decoded,obj,plan,start,stats):
    case=cell['case']; grid=raw['grid']; modes=case['movements']; raw_energy=raw['raw_energy']
    need(plan['vehicles']==raw['paths'],'flat selection to independent path ownership')
    need(plan['formulation']=='egg-native-pathflow-v1','plan formulation identity')
    need(norm['policy']==decoded['policy']==POLICY and norm['accepted'] is True,'normalization policy/acceptance')
    need(norm['budget_kwh']==decoded['budget_kwh']==1e-8,'fixed combined budget')
    negatives={key:e for key,e in raw_energy.items() if e<0}; total=-sum(negatives.values(),Q(0))
    need(Q(norm['negative_l1_exact'])==total and norm['negative_l1_kwh']==float(total),'negative exact L1 ledger')
    listed={tuple(x['key']):Q(x['before_kwh']) for x in norm['negative_to_zero']}
    need(listed==negatives and len(listed)==len(norm['negative_to_zero']) and all(x['after_kwh']==0 for x in norm['negative_to_zero']),'exact negative correction list')
    need(total<=TOL,'whole-incumbent negative budget')
    owners=raw['owners']
    normalized={key:max(Q(0),e) for key,e in raw_energy.items()}
    expected=[]; details=[]; session_excess=Q(0); interval_excess=Q(0)
    for k,g in enumerate(grid):
        rows=[]
        for (j,kk),e in normalized.items():
            if kk==k and e>0:
                need(modes[j]['id'] in owners and raw['x'][j]>Q(1,2),'every positive belongs to a selected used mode')
                rows.append((owners[modes[j]['id']],modes[j]['id'],e))
        if not rows: continue
        rows.sort(); E=sum(e for _,_,e in rows); capacity=Q(g['rate_kw'])*(g['end']-g['start'])/60
        excess=max(Q(0),E-capacity); interval_excess+=excess; prefix=Q(0); a=float(g['start'])
        for i,(v,mid,e) in enumerate(rows):
            prefix+=e; b=float(g['end']) if i==len(rows)-1 else float(Q(g['start'])+Q(g['end']-g['start'])*prefix/E)
            need(a<b<=g['end'],'positive representable contained session')
            cap=Q(g['rate_kw'])*(Q(b)-Q(a))/60; session_excess+=max(Q(0),e-cap)
            expected.append({'vehicle':v,'movement':mid,'connector':0,'start_min':a,'end_min':b,'grid_kwh':float(e)}); a=b
        details.append({'interval':k,'start_min':g['start'],'end_min':g['end'],'grid_kwh':float(E),'capacity_kwh':float(capacity),'capacity_excess_kwh':float(excess),'capacity_excess_exact':str(excess),'saturated_roundoff_adjustment':excess>0})
    need(decoded['endpoint_rule']=='exact-energy-proportional-full-interval' and decoded['charges']==expected==plan['charges'],'exact retained energies and emitted endpoints')
    need(decoded['intervals']==details,'interval correction ledger')
    for key,exact in [('capacity_excess',interval_excess),('materialized_session_excess',session_excess),('combined_roundoff',total+session_excess)]:
        need(Q(decoded[key+'_exact'])==exact and decoded[key+'_kwh']==float(exact),'exact '+key+' ledger')
    need(total+session_excess<=TOL and total+interval_excess<=TOL,'combined fleet correction budget')
    need(plan['roundoff']['negative_correction']=={k:v for k,v in norm.items() if k not in ('event','round')},'plan normalization ledger')
    need(plan['roundoff']['serial_decoding']=={k:v for k,v in decoded.items() if k not in ('event','round','charges')},'plan decoding ledger')
    old=[sum(e for (j,k),e in raw_energy.items() if grid[k]['period']==t) for t in range(len(plan['load']))]
    new=[sum(e for (j,k),e in normalized.items() if grid[k]['period']==t) for t in range(len(plan['load']))]
    for t,(a,b) in enumerate(zip(old,new)):
        near(plan['raw_charge_load'][t],float(a),'raw charge period sum',1e-12); near(plan['load'][t],float(b),'normalized period sum',1e-12)
        near(plan['roundoff']['load_delta_kwh'][t],plan['load'][t]-plan['raw_charge_load'][t],'load delta ledger',1e-15)
    if cell['objective']=='pricing':
        exact_delta=sum(Q(p)*(b-a) for p,a,b in zip(cell['prices'],old,new))
        near(obj['charge_correction_objective_delta'],float(exact_delta),'linear correction objective delta',1e-12)
        near(obj['linear_objective'],plan['ops_cost']+sum(p*x for p,x in zip(cell['prices'],plan['load'])),'objective event pricing')
    else:
        def envelope(load): return sum(max(Q(m)*x+Q(z) for m,z in row) for row,x in zip(start['tangents'],load))
        exact_delta=envelope(new)-envelope(old)
        true_delta=sum(Q(a)*(y-x)+Q(b)*(y*y-x*x)/2 for a,b,x,y in zip(cell['a'],cell['b'],old,new))
        near(obj['pwl_charge_correction_delta'],float(exact_delta),'PWL correction objective delta',1e-12)
        near(obj['true_charge_correction_delta'],float(true_delta),'true correction objective delta',1e-12)
        near(obj['pwl_objective'],plan['ops_cost']+float(envelope(new)),'objective event PWL')
        near(obj['true_cost'],plan['ops_cost']+base.cost(cell['a'],cell['b'],plan['load']),'objective event true cost')
    near(obj['native_incumbent'],stats['incumbent'],'objective event native incumbent')
    return {'negative_variables':len(negatives),'negative_l1':total,'interval_capacity_excess':interval_excess,
            'materialized_session_capacity_excess':session_excess,'combined_correction':total+session_excess,
            'charge_correction_objective_delta':exact_delta,'positive_sessions_retained':len(expected)}


def audit_cell(cell,blob):
    events=blob['events']; reduced=copy.deepcopy(blob); reduced['events']=[e for e in events if e['event'] in ('native_start','native_status','replayed_iteration')]
    record=base.audit_cell(cell,reduced)
    by_round={}
    for e in events: by_round.setdefault(e['round'],[]).append(e)
    extra=[]
    for r,es in by_round.items():
        types=[e['event'] for e in es]; need(types[:2]==['native_start','native_status'],'status ordering')
        start,stats=es[0],es[1]['stats']
        if stats['status']=='INFEASIBLE': need(len(es)==2,'infeasible trace'); continue
        expected=['native_start','native_status','native_incumbent','charge_normalization','serial_decoding','objective_reconstruction']
        if cell['objective']=='planner': expected+=['replayed_iteration']
        need(types==expected,'complete ordered native evidence stages')
        plan=es[-1]['plan'] if cell['objective']=='planner' else blob['result']['result']['plan']
        raw=raw_primal(cell,start,stats,es[2]); conversion_result=conversion(cell,raw,es[3],es[4],es[5],plan,start,stats)
        extra.append({'round':r,'raw_variables':raw['variables'],'raw_objective':raw['raw_objective'],
                      'max_raw_constraint_residual':raw['max_constraint_residual'],'constraint_checks':raw['constraint_checks'],**conversion_result})
    record['raw_incumbent_audit']=extra
    return record


def corruptions(cells,blobs):
    controls=[]
    def reject(label,name,change):
        cell=copy.deepcopy(cells[name]); blob=copy.deepcopy(blobs[name]); change(cell,blob)
        try: audit_cell(cell,blob)
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError) as exc: controls.append({'control':label,'rejected':True,'reason':str(exc)})
        else: raise AssertionError('corrupted timing copy accepted: '+label)
    event=lambda b,kind:next(e for e in b['events'] if e['event']==kind)
    def raw_change(blob,mapping,value):
        snap=event(blob,'native_incumbent'); idx=snap['mapping'][mapping][0]
        snap['variables'][idx]['solution']={'value':value,'repr':repr(value)}
    reject('raw SOC equality','cyclic_planner',lambda c,b:raw_change(b,'soc_after',3.0))
    reject('raw selected coverage','cyclic_planner',lambda c,b:raw_change(b,'movement_selection',.5))
    reject('missing raw snapshot','single_linear',lambda c,b:b['events'].pop(2))
    reject('raw variable representation','single_linear',lambda c,b:event(b,'native_incumbent')['variables'][0]['solution'].__setitem__('repr','0.0'))
    reject('raw semantic mapping duplication','single_linear',lambda c,b:event(b,'native_incumbent')['mapping']['market_load'].__setitem__(0,0))
    reject('compiled interval capacity','single_linear',lambda c,b:event(b,'native_incumbent')['mapping']['intervals'][-1].__setitem__('rate_kw',99))
    reject('negative correction exact total','cyclic_own_price',lambda c,b:event(b,'charge_normalization').__setitem__('negative_l1_exact','1'))
    reject('omitted corrected variable','cyclic_own_price',lambda c,b:event(b,'charge_normalization')['negative_to_zero'].append({'key':[0,0],'before_kwh':-1e-12,'after_kwh':0.0}))
    reject('materialized correction total','joint_planner',lambda c,b:event(b,'serial_decoding').__setitem__('materialized_session_excess_exact','1'))
    reject('endpoint spill','serial_connector',lambda c,b:event(b,'serial_decoding')['charges'][0].__setitem__('end_min',60.1))
    reject('positive energy deleted','serial_connector',lambda c,b:event(b,'serial_decoding')['charges'].pop())
    reject('objective correction accounting','cyclic_own_price',lambda c,b:event(b,'objective_reconstruction').__setitem__('charge_correction_objective_delta',1))
    reject('saved SOC','single_linear',lambda c,b:b['result']['result']['plan']['replay']['soc_trajectories'][0][-1].__setitem__('soc_kwh',19))
    reject('native lower bound','single_linear',lambda c,b:event(b,'native_status')['stats'].__setitem__('lower_bound',23))
    reject('certificate interval','single_linear',lambda c,b:b['result']['result'].__setitem__('upper',21))
    reject('tangent history','cyclic_planner',lambda c,b:event(b,'native_start')['tangents'][1][0].__setitem__(0,5))
    reject('half-minute endpoint crosses resource close','halfminute_capacity',lambda c,b:event(b,'serial_decoding')['charges'][0].__setitem__('end_min',1.0000001))
    reject('half-minute raw shared capacity','halfminute_capacity',lambda c,b:event(b,'native_incumbent')['mapping']['intervals'][-1].__setitem__('rate_kw',59))
    reject('instantaneous leg energy lost','halfminute_coincidence',lambda c,b:c['case']['movements'][-1]['legs'][-1].__setitem__('energy_kwh',0))
    reject('half-minute true lower bound changed','halfminute_capacity',lambda c,b:event(b,'native_status')['stats'].__setitem__('lower_bound',8))
    reject('infeasible half-minute control relabelled','halfminute_capacity_failure',lambda c,b:b['result']['result'].__setitem__('status','certified'))
    reject('scaled driving cost lost','halfminute_multileg',lambda c,b:c['case'].__setitem__('deadhead_cost_per_min',1))
    reject('compact multi-visit ownership changed','three_service_multivisit',lambda c,b:b['result']['result']['plan']['charges'][0].__setitem__('vehicle',1))
    reject('flat mode-interval key loses interval','three_service_multivisit',lambda c,b:event(b,'native_incumbent')['mapping']['grid_energy'][0].__setitem__('key',[0]))
    reject('compact physical row omitted','three_service_multivisit',lambda c,b:event(b,'native_status')['stats'].__setitem__('physical_constraints',1))
    return controls


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None));ap.add_argument('--out',type=Path);args=ap.parse_args()
    need(args.repository is not None,'supply frozen Git repository'); repo=args.repository.resolve()
    out=args.out or Path(tempfile.gettempdir())/('egg-native-pathflow-audit-'+uuid.uuid4().hex+'.json');resolved=out.resolve()
    need(repo!=resolved and repo not in resolved.parents and not any((p/'.git').exists() for p in (resolved,*resolved.parents)),'output outside repositories')
    need(not out.exists() and not out.is_symlink(),'exclusively new output')
    started=time.perf_counter();attempt=args.attempt;manifest=base.read(attempt/'MANIFEST.json')
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA and manifest['source_commit']==COMMIT,'original manifest/freeze identity')
    for p,item in manifest['files'].items():
        data=(attempt/p).read_bytes();need(base.digest(data)==item['sha256'] and len(data)==item['bytes'],'raw manifest '+p)
    actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()
            and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
    need(actual==set(manifest['files']),'complete original evidence manifest')
    frozen=base.read(attempt/'frozen.json');need(frozen['freeze_label']==COMMIT[:7] and frozen['protocol']=='native-pathflow-qualification-20260927-v1','half-minute freeze')
    for p,sha in frozen['source_hashes'].items():need(base.digest(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p]))==sha,'frozen source '+p)
    cells={c['id']:c for c in frozen['controls']};need(list(cells)==list(base.TARGETS),'prospective input grid')
    definitions=definition_checks(cells,repo)
    summary=base.read(attempt/'summary.json');need(summary['all_pass'] is True and summary['source_hashes_unchanged'] is True,'unchanged successful original attempt')
    blobs={}
    for receipt in summary['cells']:
        name=receipt['cell'];folder=attempt/name;inp=base.read(folder/'input.json');need({k:inp[k] for k in cells[name]}==cells[name],'frozen input equality')
        need(inp['source_hashes']==frozen['source_hashes'] and receipt==base.read(folder/'receipt.json'),'input/receipt provenance')
        blobs[name]={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()], 'receipt':receipt,'result':base.read(folder/'result.json')}
    need(list(blobs)==list(cells),'all 20 cells preserved')
    records=[audit_cell(c,blobs[n]) for n,c in cells.items()];controls=corruptions(cells,blobs)
    rounds=[r for c in records for r in c['raw_incumbent_audit']];witnesses=[w for c in records for w in c['physical_witnesses']]
    statuses=Counter(s['native_status'] for c in records for s in c['native_rounds']);widths=[c['certified_interval'][1]-c['certified_interval'][0] for c in records if c['certified_interval']]
    report={'audit_status':'PASS for all 20 frozen compact path-flow qualification fixtures and numerical witness policy',
      'frozen_commit':COMMIT,'original_manifest_sha256':MANIFEST_SHA,'definition_checks':definitions,
      'auditor_sha256':base.digest(Path(__file__).read_bytes()),'independent_core_sha256':base.digest((HERE/'independent_fixture_core.py').read_bytes()),
      'counts':{'raw_files':len(manifest['files']),'controls':len(records),'certified_controls':len(widths),'expected_infeasibilities':statuses['INFEASIBLE'],
        'native_calls':sum(statuses.values()),'independently_minimized_native_objectives':statuses['OPTIMAL'],'raw_incumbents':len(rounds),
        'raw_variable_values':sum(r['raw_variables'] for r in rounds),'physical_witness_instances':len(witnesses),
        'sessions':sum(w['sessions'] for w in witnesses),'SOC_events':sum(w['soc_events'] for w in witnesses),
        'corrected_negative_variables':sum(r['negative_variables'] for r in rounds),'nonzero_correction_incumbents':sum(r['combined_correction']>0 for r in rounds)},
      'native_status_counts':dict(statuses),'certified_width_min_max':[min(widths),max(widths)],
      'max_raw_constraint_residual':max(r['max_raw_constraint_residual'] for r in rounds),
      'total_negative_charge_correction':sum((r['negative_l1'] for r in rounds),Q(0)),
      'max_combined_correction':max(r['combined_correction'] for r in rounds),
      'max_interval_capacity_excess':max(r['interval_capacity_excess'] for r in rounds),
      'max_SOC_residual_kwh':max(w['worst_soc_residual_kwh'] for w in witnesses),'cells':records,'corruption_controls':controls,
      'scope':'No author imports or optimizer. Independently reconstructed compact flat variable mapping, every physical matrix row and selected path ownership; independent physical session/SOC replay; exact binary-rational normalization/endpoint/capacity ledgers and fixture-specific global objective/PWL minimization. Numerical feasibility, not exact repaired physical feasibility. Prior independently authored fixture/replay core is preserved verbatim; new compact matrix and three-service proof are separately reviewed.',
      'audit_wall_s':time.perf_counter()-started}
    with out.open('x') as f:json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    for p,item in manifest['files'].items():need(base.digest((attempt/p).read_bytes())==item['sha256'],'raw preservation '+p)
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'original manifest preservation')
    print(json.dumps({'status':report['audit_status'],'out':str(resolved),'counts':report['counts'],'widths':report['certified_width_min_max'],'max_raw_residual':float(report['max_raw_constraint_residual']),'max_combined_correction':float(report['max_combined_correction']),'corruptions_rejected':len(controls)},indent=2))

if __name__=='__main__':main()
