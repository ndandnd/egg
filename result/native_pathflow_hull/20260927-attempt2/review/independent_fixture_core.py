#!/usr/bin/env python3
"""Independent first native-recharge audit. Standard library; no author imports/solver.

Exact binary-rational scalar/PWL minimization is specific to the frozen fixtures.
Physical witnesses retain their stored floating values and declared tolerances.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
COMMIT = 'd37878392f0848d34f28921c97b6e8d8e6533a77'
MANIFEST_SHA = '9e8f76cbfabf7d7387792f9305123aaaf9cb7da4e0e47108279b001f47bb71db'
ET, TT, OT, GUARD = 1e-6, 1e-7, 1e-6, 1e-6
FAILURES = {'cyclic_own_price': 'Negative/nonfinite extracted native charge',
            'preserved_reserve_planner': 'Simultaneous charging exceeds connector/vehicle count',
            'serial_connector': 'Simultaneous charging exceeds connector/vehicle count'}
TARGETS = {'single_linear': F(22), 'efficiency_linear': F(433,19), 'cyclic_flat': F(37),
 'cyclic_own_price': F(134), 'cyclic_hull_price': F(307,2), 'cyclic_planner': F(97),
 'preserved_reserve_planner': F(97), 'joint_flat': F(733,19), 'joint_planner': F(38527,361),
 'fixed_reserve_planner': F(99), 'fixed_reserve_one_bus': None, 'terminal_capacity_failure': None,
 'partial_overlap_failure': None, 'serial_connector': F(24), 'directed_multileg': F(36)}


def need(ok, message):
    if not ok: raise AssertionError(message)


def near(a, b, message, tol=ET):
    need(math.isfinite(float(a)) and math.isfinite(float(b)) and abs(a-b) <= tol,
         f'{message}: {a!r} versus {b!r}')


def digest(data): return hashlib.sha256(data).hexdigest()
def q(x): return F(x)
def read(path): return json.loads(path.read_bytes())
def overlap(a,b,c,d): return max(0., min(b,d)-max(a,c))
def cost(a,b,loads): return sum(x*y+z*y*y/2 for x,z,y in zip(a,b,loads))
def pack(v):
    if isinstance(v,F): return {'exact_binary_rational':str(v),'value':float(v)}
    if isinstance(v,dict): return {k:pack(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [pack(x) for x in v]
    return v


def branches(cell):
    """Complete physical projections of THESE independently derived fixtures.

    Return (intrinsic cost, load-vector intercept, load-vector slope, xmin,xmax).
    Frozen manifest and case identity restrict use to these declared fixtures.
    """
    c=cell['case']; trips=c['trips']; eta=q(c['efficiency']); periods=len(c['market_edges_min'])-1
    if len(trips)==2 and [t['start_min'] for t in trips]==[0,120]:
        need([t['energy_kwh'] for t in trips]==[15,15], 'cyclic service energies')
        total=F(30)/eta; limit=q(c['resources'][1]['grid_kw'])
        hi=min(limit,F(15)/eta); late=q(c['resources'][3]['grid_kw'])
        intercept=[F(0),F(0),F(0),total]; slope=[F(0),F(1),F(0),F(-1)]
        out=[]
        for fleet in range(1,min(2,c['max_vehicles'])+1):
            lo=max(F(0),total-late)
            if fleet==1: lo=max(lo,(F(30)+q(c['reserve_kwh'])-q(c['battery_kwh']))/eta)
            if lo<=hi: out.append((q(c['vehicle_cost'])*fleet,intercept,slope,lo,hi))
        return out
    if len(trips)==2:
        need([t['start_min'] for t in trips]==[0,0] and [t['end_min'] for t in trips]==[30,30], 'simultaneous fixture timing')
        need([t['energy_kwh'] for t in trips]==[5,5] and c['resources'][0]['grid_kw']==10, 'simultaneous fixture physics')
        if c['recharge_deadline_min']==60: return []  # Only 5 kWh available, 10 necessary.
        need(c['recharge_deadline_min']==90 and eta==1, 'serial fixture horizon')
        return [(F(14),[F(5),F(5)],[F(0),F(0)],F(0),F(0))]
    need(len(trips)==1,'single-service fixture')
    energy=q(trips[0]['energy_kwh'])+sum(q(l['energy_kwh']) for m in c['movements'] for l in m['legs'])
    total=energy/eta
    return_at=next(m['legs'][-1]['arrive_min'] for m in c['movements'] if m['kind']=='pullin')
    capacity=sum(q(min(r['per_bus_kw'],r['grid_kw']))*max(0,r['end_min']-max(return_at,c['terminal_open_min'],r['start_min']))/60 for r in c['resources'] if r['connectors'])
    if total>capacity: return []
    intrinsic=q(c['vehicle_cost'])+q(c['deadhead_cost_per_min'])*sum(l['arrive_min']-l['depart_min'] for m in c['movements'] for l in m['legs'])
    need(periods==2 and return_at>=c['market_edges_min'][1], 'single-service market allocation')
    return [(intrinsic,[F(0),total],[F(0),F(0)],F(0),F(0))]


def scalar_min(cell, tangents=None):
    candidates=[]
    for ops,base,slope,lo,hi in branches(cell):
        xs={lo,hi}
        if cell['objective']=='pricing':
            def value(x): return ops+sum(q(p)*(aa+bb*x) for p,aa,bb in zip(cell['prices'],base,slope))
        elif tangents is None:
            a,b=list(map(q,cell['a'])),list(map(q,cell['b']))
            linear=sum(aa*ss+bb*xx*ss for aa,bb,xx,ss in zip(a,b,base,slope))
            quadratic=sum(bb*ss*ss/2 for bb,ss in zip(b,slope))
            if quadratic and lo<=-linear/(2*quadratic)<=hi: xs.add(-linear/(2*quadratic))
            def value(x): return ops+sum(aa*(xx+ss*x)+bb*(xx+ss*x)**2/2 for aa,bb,xx,ss in zip(a,b,base,slope))
        else:
            lines=[[(q(m)*ss,q(m)*xx+q(z)) for m,z in rows] for rows,xx,ss in zip(tangents,base,slope)]
            for rows in lines:
                for i,(m,z) in enumerate(rows):
                    for mm,zz in rows[i+1:]:
                        if m!=mm and lo<=(zz-z)/(m-mm)<=hi: xs.add((zz-z)/(m-mm))
            def value(x): return ops+sum(max(m*x+z for m,z in rows) for rows in lines)
        candidates += [(value(x),ops,x) for x in xs]
    return min(candidates) if candidates else None


def physical(cell, plan):
    c=cell['case']; modes={m['id']:m for m in c['movements']}; trips={t['id']:t for t in c['trips']}
    need(plan['case_identity']==cell['case_identity'] and plan['schema']=='egg-native-recharge-v1','plan identity')
    vs=plan['vehicles']; need(0<len(vs)<=c['max_vehicles'],'fleet cardinality')
    need(all(type(v['vehicle']) is int for v in vs) and [v['vehicle'] for v in vs]==list(range(len(vs))),'vehicle identifiers')
    owned={}; events={}; busy={}; covered=[]; ops=c['vehicle_cost']*len(vs); consumed=0.; count_soc=0
    for v in vs:
        vi=v['vehicle']; seq=v['trips']; ids=v['movements']
        need(seq and len(ids)==len(seq)+1,'nonempty complete path')
        expected=[(None,seq[0])]+list(zip(seq,seq[1:]))+[(seq[-1],None)]
        events[vi]=[]; busy[vi]=[]
        for j,(mid,pair) in enumerate(zip(ids,expected)):
            m=modes[mid]; need((m['before'],m['after'])==pair,'movement ownership')
            need(m['kind'] in (('pullout',) if j==0 else ('pullin',) if j==len(ids)-1 else ('direct','depot')),'movement kind')
            owned[(vi,mid)]=m
            for leg in m['legs']:
                events[vi].append((leg['arrive_min'],-leg['energy_kwh'],'movement'))
                busy[vi].append((leg['depart_min'],leg['arrive_min']))
                consumed+=leg['energy_kwh']; ops+=c['deadhead_cost_per_min']*(leg['arrive_min']-leg['depart_min'])
        for tid in seq:
            t=trips[tid]; events[vi].append((t['end_min'],-t['energy_kwh'],'service'))
            consumed+=t['energy_kwh']; busy[vi].append((t['start_min'],t['end_min']))
        covered+=seq
    need(sorted(covered)==sorted(trips),'exact mandatory coverage')
    loads=[0.]*(len(c['market_edges_min'])-1); sessions=plan['charges']; peak=0.
    for s in sessions:
        vi,mid=s['vehicle'],s['movement']; need((vi,mid) in owned,'charge owner')
        m=owned[(vi,mid)]; a,b,e=s['start_min'],s['end_min'],s['grid_kwh']
        need(type(s['connector']) is int and s['connector']==0,'connector identity')
        need(all(math.isfinite(z) for z in (a,b,e)) and 0<=a<b and e>0,'positive finite session')
        if m['kind']=='depot': lo,hi=m['legs'][m['depot_split']-1]['arrive_min'],m['legs'][m['depot_split']]['depart_min']
        else:
            need(m['kind']=='pullin','eligible charging mode')
            lo,hi=max(m['legs'][-1]['arrive_min'],c['terminal_open_min']),c['recharge_deadline_min']
        need(a>=lo-TT and b<=hi+TT,'native charge window')
        need(all(overlap(a,b,x,y)<=TT for x,y in busy[vi]),'charging during service/travel')
        for k,(x,y) in enumerate(zip(c['market_edges_min'],c['market_edges_min'][1:])):
            loads[k]+=e*overlap(a,b,x,y)/(b-a)
        events[vi].append((b,c['efficiency']*e,'charge'))
    # Pairwise session disjointness is independent of the author's active-set sweep.
    for i,s in enumerate(sessions):
        for t in sessions[i+1:]:
            need(overlap(s['start_min'],s['end_min'],t['start_min'],t['end_min'])==0,'strict single connector disjointness')
        duration=s['end_min']-s['start_min']; covered_time=0.
        for r in c['resources']:
            dt=overlap(s['start_min'],s['end_min'],r['start_min'],r['end_min'])
            if dt:
                need(r['connectors']==1,'charge on closed connector')
                used=s['grid_kwh']*dt/duration
                need(used<=min(r['per_bus_kw'],r['grid_kw'])*dt/60+ET,'instantaneous resource energy')
                covered_time+=dt
        near(covered_time,duration,'resource horizon coverage',TT)
        peak=max(peak,s['grid_kwh']*60/duration)
    traces=[]; worst_soc=0.
    for vi in range(len(vs)):
        soc=float(c['battery_kwh']); trace=[{'time_min':0.,'soc_kwh':soc,'kind':'initial'}]
        for at,delta,kind in sorted(events[vi],key=lambda x:(x[0],x[2]!='charge')):
            soc+=delta; worst_soc=max(worst_soc,c['reserve_kwh']-soc,soc-c['battery_kwh'])
            need(c['reserve_kwh']-ET<=soc<=c['battery_kwh']+ET,'SOC reserve/capacity')
            trace.append({'time_min':float(at),'soc_kwh':soc,'kind':kind}); count_soc+=1
        near(soc,c['battery_kwh'],'full replenishment')
        traces.append(trace)
    for saved,actual in zip(plan['load'],loads): near(saved,actual,'period grid load')
    need(len(plan['load'])==len(loads),'load length')
    need(len(plan['raw_solver_load'])==len(loads),'native load length')
    for saved,actual in zip(plan['raw_solver_load'],loads): near(saved,actual,'native load versus physical')
    near(plan['ops_cost'],ops,'intrinsic cost'); near(c['efficiency']*sum(loads),consumed,'fleet grid/battery conservation')
    saved=plan['replay']; need(saved['replay_ok'] is True,'saved replay verdict')
    for key,val in [('ops_cost',ops),('grid_kwh',sum(loads)),('consumption_kwh',consumed),('max_grid_kw',peak)]: near(saved[key],val,'saved '+key)
    need(len(saved['load'])==len(loads),'saved replay load length')
    for x,y in zip(saved['load'],loads): near(x,y,'saved replay load')
    need(len(saved['soc_trajectories'])==len(traces),'saved SOC vehicle count')
    for a,b in zip(saved['soc_trajectories'],traces):
        need(len(a)==len(b),'saved SOC event count')
        for x,y in zip(a,b):
            need(x['kind']==y['kind'],'saved SOC event kind'); near(x['time_min'],y['time_min'],'saved SOC time',TT); near(x['soc_kwh'],y['soc_kwh'],'saved SOC value')
    return {'load':loads,'ops':ops,'sessions':len(sessions),'soc_events':count_soc,'worst_soc_residual_kwh':max(0.,worst_soc),'peak_kw':peak}


def saved_bounds(cell, stats, plan, tangents=None):
    p=physical(cell,plan)
    if tangents is None:
        val=p['ops']+sum(x*y for x,y in zip(cell['prices'],p['load'])); env=val
        near(stats['incumbent'],val,'pricing incumbent objective',OT)
    else:
        val=p['ops']+cost(cell['a'],cell['b'],p['load'])
        env=p['ops']+sum(max(m*x+z for m,z in rows) for x,rows in zip(p['load'],tangents))
        need(stats['incumbent']>=env-OT,'epigraph incumbent below envelope')
    need(stats['lower_bound']<=env+GUARD and env<=val+GUARD,'native bound/envelope/true order')
    return p,val,env


def audit_cell(cell, blob):
    c=cell['case']; identity=digest(json.dumps({'schema':'egg-native-recharge-v1','case':c},sort_keys=True,allow_nan=False).encode())
    need(identity==cell['case_identity'],'input identity digest')
    model_min=scalar_min(cell); target=TARGETS[cell['id']]
    need((model_min is None)==(target is None),'analytical feasibility target')
    if target is not None: near(float(model_min[0]),float(target),'independent analytical target',1e-10)
    events=blob['events']; starts={}; statuses={}; replayed={}; oracle=[]; witnesses=[]
    for e in events:
        r=e['round']
        if e['event']=='native_start':
            need(r==len(starts) and r not in starts,'sequential native starts'); starts[r]=e
        elif e['event']=='native_status':
            need(r in starts and r not in statuses,'one returned status per start'); stats=e['stats']; statuses[r]=stats
            need(stats['backend']=='CBC' and stats['threads']==1 and stats['seconds_cap']<=10,'native budget/backend receipt')
            rt=stats['backend_runtime']; need(rt['requested']=='CBC' and rt['model_solver_name']=='CBC' and rt['solver_module']=='mip.cbc','actual backend identity')
            need(stats['wall_s']>=0 and stats['n_vars']>0 and stats['n_constraints']>=stats['physical_constraints'],'native receipt dimensions/time')
            tangent=starts[r].get('tangents')
            reference=scalar_min(cell,tangent)
            if reference is None:
                need(stats['status']=='INFEASIBLE' and stats['incumbent'] is None,'independently infeasible status')
            else:
                need(stats['status']=='OPTIMAL','first-run raw status preserved')
                near(stats['incumbent'],float(reference[0]),'independent global native objective',OT)
                near(stats['lower_bound'],float(reference[0]),'independent global native lower bound',OT)
            oracle.append({'round':r,'native_status':stats['status'],'reference':None if reference is None else reference[0], 'native_incumbent':stats['incumbent'],'native_lower_bound':stats['lower_bound'],'physical_witness_saved':False})
        elif e['event']=='replayed_iteration':
            need(r in statuses and r not in replayed,'replay after unique status')
            need(e['stats']==statuses[r] and e['tangents']==starts[r]['tangents'],'immutable round snapshot')
            p,val,env=saved_bounds(cell,statuses[r],e['plan'],e['tangents'])
            near(e['lower'],statuses[r]['lower_bound']-GUARD,'round widened lower')
            near(e['upper'],val+GUARD,'round widened true upper')
            near(e['replayed_tangent_objective'],env,'saved PWL envelope')
            near(e['native_epigraph_slack'],statuses[r]['incumbent']-env,'saved epigraph slack')
            replayed[r]=e; witnesses.append(p); oracle[r]['physical_witness_saved']=True
        else: raise AssertionError('unknown event')
    need(len(starts)==len(statuses),'all native starts returned')
    if cell['objective']=='planner':
        expected=[[[float(a),0.]] for a in cell['a']]
        for r in range(len(starts)):
            need(starts[r]['tangents']==expected,'exact saved tangent evolution')
            if r in replayed:
                loads=replayed[r]['plan']['load']
                for t,x in enumerate(loads): expected[t].append([float(cell['a'][t]+cell['b'][t]*x),float(-.5*cell['b'][t]*x*x)])
    receipt=blob['receipt']; need(receipt['native_calls_started']==len(starts) and receipt['native_calls_returned']==len(statuses),'call counts')
    near(receipt['native_wall_s'],sum(s['wall_s'] for s in statuses.values()),'native elapsed accounting',1e-9)
    need(receipt['native_accounting_complete'] and not receipt['hard_timeout'] and not receipt['evidence_issues'],'complete first-run accounting')
    result=blob.get('result')
    if cell['id'] in FAILURES:
        need(result is None and not receipt['pass'] and receipt['returncode']==2 and receipt['status']=='exception','failure preserved')
        need(blob['exception']['message']==FAILURES[cell['id']],'raw failure reason')
    else:
        need(result is not None and receipt['pass'] and receipt['returncode']==0,'successful receipt')
        need(result['assessment']['pass'] is True and result['cell']==cell['id'],'result ownership/assessment')
        result=result['result']; need(result['case_identity']==cell['case_identity'],'result physical identity')
        if target is None: need(result['status']=='infeasible','infeasible result')
        else:
            need(result['status']=='certified','certified status')
            if cell['objective']=='pricing':
                need(result['stats']==statuses[0],'pricing saved stats'); p,val,env=saved_bounds(cell,statuses[0],result['plan']); witnesses.append(p); oracle[0]['physical_witness_saved']=True
                lower=statuses[0]['lower_bound']-GUARD; upper=val+GUARD
            else:
                need(len(result['rounds'])==len(replayed),'all planner rounds archived')
                for r,saved in enumerate(result['rounds']):
                    need(saved=={k:v for k,v in replayed[r].items() if k not in ('event','round')},'event/result round equality')
                lower=max(e['lower'] for e in replayed.values()); upper=min(e['upper'] for e in replayed.values())
                need(any(result['plan']==e['plan'] and e['upper']==upper for e in replayed.values()),'best witness selection')
            near(result['lower'],lower,'final lower'); near(result['upper'],upper,'final upper'); near(result['gap'],upper-lower,'final width')
            need(0<=result['gap']<=1e-4 and q(result['lower'])<=model_min[0]<=q(result['upper']),'exact fixture optimum enclosed')
    return {'cell':cell['id'],'original_pass':receipt['pass'],'status':receipt['status'],
            'independent_true_optimum':None if model_min is None else model_min[0],
            'native_rounds':oracle,'physical_witnesses':witnesses,
            'certified_interval':None if not result or target is None else [result['lower'],result['upper']],
            'failure':FAILURES.get(cell['id'])}


def corruptions(cells,blobs):
    checks=[]
    def reject(label,name,change):
        cell=copy.deepcopy(cells[name]); blob=copy.deepcopy(blobs[name]); change(cell,blob)
        try: audit_cell(cell,blob)
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError) as exc: checks.append({'control':label,'rejected':True,'reason':str(exc)})
        else: raise AssertionError('Corrupt copy accepted: '+label)
    reject('physical energy','single_linear',lambda c,b:b['result']['result']['plan']['charges'][0].__setitem__('grid_kwh',16))
    reject('single-connector overlap','cyclic_flat',lambda c,b:b['result']['result']['plan']['charges'].append(copy.deepcopy(b['result']['result']['plan']['charges'][0])))
    reject('saved SOC','single_linear',lambda c,b:b['result']['result']['plan']['replay']['soc_trajectories'][0][-1].__setitem__('soc_kwh',19))
    reject('saved load','single_linear',lambda c,b:b['result']['result']['plan']['load'].__setitem__(1,14))
    reject('intrinsic cost','single_linear',lambda c,b:b['result']['result']['plan'].__setitem__('ops_cost',8))
    reject('native bound','single_linear',lambda c,b:b['events'][1]['stats'].__setitem__('lower_bound',23))
    reject('final interval','single_linear',lambda c,b:b['result']['result'].__setitem__('upper',21))
    reject('native status','single_linear',lambda c,b:b['events'][1]['stats'].__setitem__('status','FEASIBLE'))
    reject('tangent history','cyclic_planner',lambda c,b:b['events'][0]['tangents'][1][0].__setitem__(0,5))
    reject('case identity','single_linear',lambda c,b:c['case'].__setitem__('efficiency',.9))
    reject('failure relabeled success','cyclic_own_price',lambda c,b:b['receipt'].__setitem__('pass',True))
    reject('missing returned call','single_linear',lambda c,b:b['events'].pop(1))
    return checks


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--attempt',type=Path,default=HERE.parent)
    ap.add_argument('--repository',type=Path,default=next((p for p in HERE.parents if (p/'.git').exists()),None))
    ap.add_argument('--out',type=Path); args=ap.parse_args()
    need(args.repository is not None,'supply repository containing frozen Git commit')
    output=args.out or Path(tempfile.gettempdir())/('egg-native-attempt1-audit-'+uuid.uuid4().hex+'.json')
    resolved=output.resolve(); repo=args.repository.resolve()
    need(repo!=resolved and repo not in resolved.parents and not any((p/'.git').exists() for p in (resolved,*resolved.parents)),'output must be outside repositories')
    need(not output.exists() and not output.is_symlink(),'output must be exclusively new')
    start=time.perf_counter(); attempt=args.attempt; manifest_bytes=(attempt/'MANIFEST.json').read_bytes()
    need(digest(manifest_bytes)==MANIFEST_SHA,'original manifest identity'); manifest=json.loads(manifest_bytes)
    need(manifest['source_commit']==COMMIT,'original frozen commit')
    for path,entry in manifest['files'].items():
        data=(attempt/path).read_bytes(); need(digest(data)==entry['sha256'] and len(data)==entry['bytes'],'raw manifest '+path)
    actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file() and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
    need(actual==set(manifest['files']),'complete original evidence manifest')
    frozen=read(attempt/'frozen.json'); need(frozen['freeze_label']==COMMIT,'frozen label')
    for p,sha in frozen['source_hashes'].items():
        need(digest(subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+p]))==sha,'frozen source '+p)
    cells={c['id']:c for c in frozen['controls']}; need(list(cells)==list(TARGETS),'prospective grid/order')
    blobs={}; summary=read(attempt/'summary.json')
    for row in summary['cells']:
        name=row['cell']; folder=attempt/name; cell=cells[name]; inp=read(folder/'input.json')
        need({k:inp[k] for k in cell}==cell,'input/frozen equality'); need(inp['source_hashes']==frozen['source_hashes'],'input source hashes')
        blob={'events':[json.loads(x) for x in (folder/'events.jsonl').read_bytes().splitlines()], 'receipt':read(folder/'receipt.json')}
        need(row==blob['receipt'],'summary/receipt equality')
        for tag in ('result','exception'):
            if (folder/(tag+'.json')).exists(): blob[tag]=read(folder/(tag+'.json'))
        blobs[name]=blob
    need(list(blobs)==list(cells) and summary['all_pass'] is False and summary['source_hashes_unchanged'] is True,'campaign completeness/failure/source status')
    records=[audit_cell(c,blobs[n]) for n,c in cells.items()]
    checks=corruptions(cells,blobs)
    native=Counter(r['native_status'] for row in records for r in row['native_rounds']); witnesses=[w for row in records for w in row['physical_witnesses']]
    widths=[r['certified_interval'][1]-r['certified_interval'][0] for r in records if r['certified_interval']]
    report={'audit_status':'PASS: archived evidence consistent; original qualification FAILED',
      'frozen_commit':COMMIT,'original_manifest_sha256':MANIFEST_SHA,'auditor_sha256':digest(Path(__file__).read_bytes()),
      'raw_files_verified':len(manifest['files']),'cells':records,'native_status_counts':dict(native),
      'counts':{'cells':len(records),'original_passes':sum(r['original_pass'] for r in records),'original_failures':len(FAILURES),
        'certified_targets':len(widths),'analytical_infeasibilities':sum(v is None for v in TARGETS.values()),
        'native_calls':sum(native.values()),'independently_minimized_finite_native_objectives':native['OPTIMAL'],
        'saved_physical_witness_instances':len(witnesses),'sessions':sum(w['sessions'] for w in witnesses),'soc_events':sum(w['soc_events'] for w in witnesses)},
      'certified_width_min_max':[min(widths),max(widths)],'max_saved_SOC_residual_kwh':max(w['worst_soc_residual_kwh'] for w in witnesses),
      'corruption_controls':checks,'scope':'No author imports or optimizer; exact binary-rational analytical/PWL fixture minimization and tolerance-based raw floating session replay. No rationalization of physical witnesses; three failed extractions remain failed and lack full raw incumbent evidence.',
      'audit_wall_s':time.perf_counter()-start}
    with output.open('x') as f: json.dump(pack(report),f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')
    for path,entry in manifest['files'].items(): need(digest((attempt/path).read_bytes())==entry['sha256'],'raw unchanged after audit')
    need(digest((attempt/'MANIFEST.json').read_bytes())==MANIFEST_SHA,'original manifest unchanged')
    print(json.dumps({'audit_status':report['audit_status'],'out':str(resolved),'counts':report['counts'],'native_status_counts':dict(native),'widths':report['certified_width_min_max'],'corruptions_rejected':len(checks)},indent=2))

if __name__=='__main__': main()
