#!/usr/bin/env python3
"""Independent V2 raw-incumbent, correction, witness and analytical audit.

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
COMMIT='997575d049a66d952a0cb8d79f974f7ba5f4ccf0'
MANIFEST_SHA='d32b90ed66deea0418e56e5996219401eeea1d0d998ee2cab21e9bd239ac5a10'
POLICY='native-roundoff-qualification-v2'
TOL=Q(1e-8)
base.FAILURES={}
need,near=base.need,base.near


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
    case=cell['case']; trips=case['trips']; modes=case['movements']; mp=snapshot['mapping']; records=snapshot['variables']
    need(snapshot['case_identity']==cell['case_identity'] and snapshot['extraction_policy']==POLICY,'raw snapshot identity/policy')
    need([r['index'] for r in records]==list(range(len(records))) and len(records)==stats['n_vars'],'complete raw variable indices')
    need(mp['trip_ids']==[t['id'] for t in trips] and mp['movement_ids']==[m['id'] for m in modes],'semantic IDs')
    grid=intervals(case); need(mp['intervals']==grid,'independently compiled elementary intervals')
    vals={r['index']:value_record(r['solution']) for r in records}
    need(all(x is not None for x in vals.values()),'all incumbent values finite/present')
    violations=[]; constraints=Counter()
    def le(lhs,rhs,tag):
        v=max(Q(0),lhs-rhs); violations.append(v); constraints[tag]+=1
        need(v<=TOL,f'raw {tag} residual {float(v)} exceeds native tolerance')
    def eq(lhs,rhs,tag): le(lhs,rhs,tag); le(rhs,lhs,tag)
    def declared(idx,kind,lo,hi=None):
        record=records[idx]; need(record['type']==kind,'raw variable type')
        actual_lo=value_record(record['lower']); actual_hi=value_record(record['upper'])
        need(actual_lo==Q(lo),'raw declared lower bound')
        if hi is not None: need(actual_hi==Q(hi),'raw declared upper bound')
        if actual_lo is not None: le(actual_lo,vals[idx],'variable lower')
        if actual_hi is not None: le(vals[idx],actual_hi,'variable upper')
        if kind=='B': need(min(abs(vals[idx]),abs(vals[idx]-1))<=TOL,'binary integrality')
    V=case['max_vehicles']; N=len(trips); M=len(modes); B=Q(case['battery_kwh']); reserve=Q(case['reserve_kwh']); eta=Q(case['efficiency'])
    need(len(mp['used'])==V,'used vector shape')
    for key,width in [('assignment',N),('movement_selection',M),('soc_before',N),('soc_after',N)]:
        need(len(mp[key])==V and all(len(row)==width for row in mp[key]),'semantic matrix shape '+key)
    union=[]
    for key in ('used','market_load','epigraph'): union+=mp[key]
    for key in ('assignment','movement_selection','soc_before','soc_after'): union += [i for row in mp[key] for i in row]
    union += [r['variable'] for r in mp['grid_energy']]
    need(len(union)==len(set(union))==len(records) and set(union)==set(vals),'every raw variable mapped exactly once')
    used=[vals[i] for i in mp['used']]
    u=[[vals[i] for i in row] for row in mp['assignment']]
    x=[[vals[i] for i in row] for row in mp['movement_selection']]
    sb=[[vals[i] for i in row] for row in mp['soc_before']]; sa=[[vals[i] for i in row] for row in mp['soc_after']]
    for idx in mp['used']+[i for row in mp['assignment']+mp['movement_selection'] for i in row]: declared(idx,'B',0,1)
    for idx in [i for row in mp['soc_before']+mp['soc_after'] for i in row]: declared(idx,'C',0,B)
    raw={tuple(r['key']):vals[r['variable']] for r in mp['grid_energy']}; raw_indices={tuple(r['key']):r['variable'] for r in mp['grid_energy']}
    need(len(raw)==len(mp['grid_energy']),'unique energy keys')
    expected={(v,j,k) for v in range(V) for k,g in enumerate(grid) for j,m in enumerate(modes) if m['id'] in g['visits'] and g['rate_kw']>0}
    need(set(raw)==expected,'complete eligible native energy variables')
    for (v,j,k),energy in raw.items():
        cap=Q(grid[k]['rate_kw'])*Q(grid[k]['hours']); declared(raw_indices[(v,j,k)],'C',0,cap)
        le(energy,cap*x[v][j],'selected energy')
    for k,g in enumerate(grid):
        le(sum(e for (v,j,kk),e in raw.items() if kk==k),Q(g['rate_kw'])*Q(g['hours']),'shared interval capacity')
        for v in range(V): le(sum(x[v][j] for j,m in enumerate(modes) if m['id'] in g['visits']),used[v],'single active vehicle visit')
    tid={t['id']:i for i,t in enumerate(trips)}
    for i in range(N): eq(sum(u[v][i] for v in range(V)),Q(1),'service coverage')
    for v in range(V):
        eq(sum(x[v][j] for j,m in enumerate(modes) if m['kind']=='pullout'),used[v],'pullout count')
        eq(sum(x[v][j] for j,m in enumerate(modes) if m['kind']=='pullin'),used[v],'pullin count')
        if v+1<V: le(used[v+1],used[v],'used vehicle symmetry')
        for i,t in enumerate(trips):
            eq(sum(x[v][j] for j,m in enumerate(modes) if m['after']==t['id']),u[v][i],'incoming path flow')
            eq(sum(x[v][j] for j,m in enumerate(modes) if m['before']==t['id']),u[v][i],'outgoing path flow')
            for soc in (sb[v][i],sa[v][i]): le(soc,B*u[v][i],'owned SOC capacity'); le(reserve*u[v][i],soc,'owned SOC reserve')
            eq(sa[v][i],sb[v][i]-Q(t['energy_kwh'])*u[v][i],'service SOC equality')
        for j,m in enumerate(modes):
            e=sum(Q(l['energy_kwh']) for l in m['legs']); big=B+e; selected=x[v][j]
            charge=sum(energy for (vv,jj,k),energy in raw.items() if vv==v and jj==j)
            if m['kind']=='pullout': residual=sb[v][tid[m['after']]]-(B-e)
            elif m['kind']=='direct': residual=sb[v][tid[m['after']]]-sa[v][tid[m['before']]]+e
            elif m['kind']=='depot':
                inbound=sum(Q(l['energy_kwh']) for l in m['legs'][:m['depot_split']]); arrival=sa[v][tid[m['before']]]-inbound
                le(reserve-big*(1-selected),arrival,'depot arrival reserve'); le(arrival+eta*charge,B+big*(1-selected),'depot charge capacity')
                residual=sb[v][tid[m['after']]]-sa[v][tid[m['before']]]+e-eta*charge
            else:
                arrival=sa[v][tid[m['before']]]-e; le(reserve-big*(1-selected),arrival,'return reserve'); residual=arrival+eta*charge-B
            le(residual,big*(1-selected),'movement SOC upper'); le(-residual,big*(1-selected),'movement SOC lower')
    loads=[vals[i] for i in mp['market_load']]; need(len(loads)==len(case['market_edges_min'])-1,'market vector shape')
    for t,idx in enumerate(mp['market_load']):
        declared(idx,'C',0); eq(loads[t],sum(e for (v,j,k),e in raw.items() if grid[k]['period']==t),'grid energy aggregation')
    ops=Q(case['vehicle_cost'])*sum(used)+Q(case['deadhead_cost_per_min'])*sum(x[v][j]*sum(l['arrive_min']-l['depart_min'] for l in m['legs']) for v in range(V) for j,m in enumerate(modes))
    if cell['objective']=='pricing':
        need(not mp['epigraph'],'no pricing epigraph'); objective=ops+sum(Q(p)*L for p,L in zip(cell['prices'],loads))
    else:
        need(len(mp['epigraph'])==len(loads),'planner epigraph shape')
        for t,idx in enumerate(mp['epigraph']):
            r=records[idx]; need(r['type']=='C' and value_record(r['lower'])<-Q(10)**100,'free-below epigraph')
            for slope,intercept in start['tangents'][t]: le(Q(slope)*loads[t]+Q(intercept),vals[idx],'saved tangent epigraph')
        objective=ops+sum(vals[i] for i in mp['epigraph'])
    near(float(objective),stats['incumbent'],'raw native objective',1e-6)
    return {'variables':len(records),'raw_objective':objective,'max_constraint_residual':max(violations,default=Q(0)),
            'constraint_checks':dict(constraints),'raw_energy':raw,'used':used,'x':x,'grid':grid,'native_load':loads}


def conversion(cell,raw,norm,decoded,obj,plan,start,stats):
    case=cell['case']; grid=raw['grid']; modes=case['movements']; raw_energy=raw['raw_energy']
    need(norm['policy']==decoded['policy']==POLICY and norm['accepted'] is True,'normalization policy/acceptance')
    need(norm['budget_kwh']==decoded['budget_kwh']==1e-8,'fixed combined budget')
    negatives={key:e for key,e in raw_energy.items() if e<0}; total=-sum(negatives.values(),Q(0))
    need(Q(norm['negative_l1_exact'])==total and norm['negative_l1_kwh']==float(total),'negative exact L1 ledger')
    listed={tuple(x['key']):Q(x['before_kwh']) for x in norm['negative_to_zero']}
    need(listed==negatives and len(listed)==len(norm['negative_to_zero']) and all(x['after_kwh']==0 for x in norm['negative_to_zero']),'exact negative correction list')
    need(total<=TOL,'whole-incumbent negative budget')
    mapping={v:i for i,v in enumerate(v for v,u in enumerate(raw['used']) if u>Q(1,2))}
    normalized={key:max(Q(0),e) for key,e in raw_energy.items()}
    expected=[]; details=[]; session_excess=Q(0); interval_excess=Q(0)
    for k,g in enumerate(grid):
        rows=[]
        for (v,j,kk),e in normalized.items():
            if kk==k and e>0:
                need(v in mapping and raw['x'][v][j]>Q(1,2),'every positive belongs to a selected used mode')
                rows.append((mapping[v],modes[j]['id'],e))
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
    old=[sum(e for (v,j,k),e in raw_energy.items() if grid[k]['period']==t) for t in range(len(plan['load']))]
    new=[sum(e for (v,j,k),e in normalized.items() if grid[k]['period']==t) for t in range(len(plan['load']))]
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
        need(types==expected,'complete ordered V2 evidence stages')
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
        else: raise AssertionError('corrupted V2 copy accepted: '+label)
    event=lambda b,kind:next(e for e in b['events'] if e['event']==kind)
    def raw_change(blob,mapping,value):
        snap=event(blob,'native_incumbent'); idx=snap['mapping'][mapping][0][0]
        snap['variables'][idx]['solution']={'value':value,'repr':repr(value)}
    reject('raw SOC equality','cyclic_planner',lambda c,b:raw_change(b,'soc_after',3.0))
    reject('raw assignment coverage','cyclic_planner',lambda c,b:raw_change(b,'assignment',.5))
    reject('missing raw snapshot','single_linear',lambda c,b:b['events'].pop(2))
    reject('raw variable representation','single_linear',lambda c,b:event(b,'native_incumbent')['variables'][0]['solution'].__setitem__('repr','0.0'))
    reject('raw semantic mapping duplication','single_linear',lambda c,b:event(b,'native_incumbent')['mapping']['market_load'].__setitem__(0,0))
    reject('compiled interval capacity','single_linear',lambda c,b:event(b,'native_incumbent')['mapping']['intervals'][-1].__setitem__('rate_kw',99))
    reject('negative correction exact total','cyclic_own_price',lambda c,b:event(b,'charge_normalization').__setitem__('negative_l1_exact','0'))
    reject('omitted corrected variable','cyclic_own_price',lambda c,b:event(b,'charge_normalization')['negative_to_zero'].clear())
    reject('materialized correction total','joint_planner',lambda c,b:event(b,'serial_decoding').__setitem__('materialized_session_excess_exact','1'))
    reject('endpoint spill','serial_connector',lambda c,b:event(b,'serial_decoding')['charges'][0].__setitem__('end_min',60.1))
    reject('positive energy deleted','serial_connector',lambda c,b:event(b,'serial_decoding')['charges'].pop())
    reject('objective correction accounting','cyclic_own_price',lambda c,b:event(b,'objective_reconstruction').__setitem__('charge_correction_objective_delta',1))
    reject('saved SOC','single_linear',lambda c,b:b['result']['result']['plan']['replay']['soc_trajectories'][0][-1].__setitem__('soc_kwh',19))
    reject('native lower bound','single_linear',lambda c,b:event(b,'native_status')['stats'].__setitem__('lower_bound',23))
    reject('certificate interval','single_linear',lambda c,b:b['result']['result'].__setitem__('upper',21))
    reject('tangent history','cyclic_planner',lambda c,b:event(b,'native_start')['tangents'][1][0].__setitem__(0,5))
    return controls


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None));ap.add_argument('--out',type=Path);args=ap.parse_args()
    need(args.repository is not None,'supply frozen Git repository'); repo=args.repository.resolve()
    out=args.out or Path(tempfile.gettempdir())/('egg-native-attempt2-audit-'+uuid.uuid4().hex+'.json');resolved=out.resolve()
    need(repo!=resolved and repo not in resolved.parents and not any((p/'.git').exists() for p in (resolved,*resolved.parents)),'output outside repositories')
    need(not out.exists() and not out.is_symlink(),'exclusively new output')
    started=time.perf_counter();attempt=args.attempt;manifest=base.read(attempt/'MANIFEST.json')
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA and manifest['source_commit']==COMMIT,'original manifest/freeze identity')
    for p,item in manifest['files'].items():
        data=(attempt/p).read_bytes();need(base.digest(data)==item['sha256'] and len(data)==item['bytes'],'raw manifest '+p)
    actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()
            and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
    need(actual==set(manifest['files']),'complete original evidence manifest')
    frozen=base.read(attempt/'frozen.json');need(frozen['freeze_label']==COMMIT and frozen['protocol']=='native-recharge-qualification-20260927-v2','V2 freeze')
    for p,sha in frozen['source_hashes'].items():need(base.digest(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p]))==sha,'frozen source '+p)
    cells={c['id']:c for c in frozen['controls']};need(list(cells)==list(base.TARGETS),'prospective input grid')
    summary=base.read(attempt/'summary.json');need(summary['all_pass'] is True and summary['source_hashes_unchanged'] is True,'unchanged successful original attempt')
    blobs={}
    for receipt in summary['cells']:
        name=receipt['cell'];folder=attempt/name;inp=base.read(folder/'input.json');need({k:inp[k] for k in cells[name]}==cells[name],'frozen input equality')
        need(inp['source_hashes']==frozen['source_hashes'] and receipt==base.read(folder/'receipt.json'),'input/receipt provenance')
        blobs[name]={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()], 'receipt':receipt,'result':base.read(folder/'result.json')}
    need(list(blobs)==list(cells),'all 15 cells preserved')
    records=[audit_cell(c,blobs[n]) for n,c in cells.items()];controls=corruptions(cells,blobs)
    rounds=[r for c in records for r in c['raw_incumbent_audit']];witnesses=[w for c in records for w in c['physical_witnesses']]
    statuses=Counter(s['native_status'] for c in records for s in c['native_rounds']);widths=[c['certified_interval'][1]-c['certified_interval'][0] for c in records if c['certified_interval']]
    report={'audit_status':'PASS for frozen V2 fixtures and numerical witness policy; attempt1 remains separately FAILED',
      'frozen_commit':COMMIT,'original_manifest_sha256':MANIFEST_SHA,
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
      'scope':'No author imports or optimizer. Raw variable/mapping/primal checks, exact binary-rational normalization/endpoint/capacity ledgers, unchanged floating physical replay and exact fixture-specific global objective/PWL minimization. Numerical feasibility, not exact repaired physical feasibility.',
      'audit_wall_s':time.perf_counter()-started}
    with out.open('x') as f:json.dump(base.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    for p,item in manifest['files'].items():need(base.digest((attempt/p).read_bytes())==item['sha256'],'raw preservation '+p)
    need(base.digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'original manifest preservation')
    print(json.dumps({'status':report['audit_status'],'out':str(resolved),'counts':report['counts'],'widths':report['certified_width_min_max'],'max_raw_residual':float(report['max_raw_constraint_residual']),'max_combined_correction':float(report['max_combined_correction']),'corruptions_rejected':len(controls)},indent=2))

if __name__=='__main__':main()
