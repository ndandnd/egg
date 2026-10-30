#!/usr/bin/env python3
"""Independent public pilot audit. Standard library and independent replay only.

Never imports the author adapter/model or an optimizer; never reads log contents
into its public report. Native global lower bounds remain conditional evidence.
"""
import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

import independent_physical_core as physical
import independent_compact_core as compact

need,near=physical.need,physical.near
COMMIT='282e00b80b6fd9457006429b089269b2a9e2be92'
PROTOCOL='sistig-pricing-pilot-20260927-v1'
PAYLOAD='data/public/sistig_26088190_v1/hildenbrand_native_cases.json'
PAYLOAD_SHA='af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6'
IDENTITIES={15:'1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7',16:'216693551f2e58ec8aab3cba68352656ec99bab8db13c671edd028542acfeb3d'}
BUDGET={'backend':'GRB','threads':1,'phase_seconds':180,'wall_seconds':240,'max_rounds':1,'epsilon':1e-4}
EVENTS=['native_start','native_status','native_incumbent','charge_normalization','serial_decoding','objective_reconstruction']
GUARD=1e-6
HERE=Path(__file__).resolve().parent


def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_bytes())
def finite(value):return type(value) in (int,float) and math.isfinite(value)
def case_identity(case):return sha(json.dumps({'schema':'egg-native-recharge-v1','case':case},sort_keys=True,allow_nan=False).encode())


def reconstruct_case(variant):
    """Independent field projection of already independently source-audited JSON."""
    charging,cost=variant['charging_model'],variant['cost_policy']
    return {'name':variant['case_name'],'trips':[t['native'] for t in variant['trips']],
        'movements':[{k:m[k] for k in ('id','kind','before','after','legs','depot_split')} for m in variant['movement_modes']],
        'resources':[variant['resource_policy']],'market_edges_min':variant['market_edges_min'],
        'depot':variant['selected_depot_native_place'],'max_vehicles':int(variant['vehicle_cap']),
        'battery_kwh':charging['usable_battery_kwh'],'reserve_kwh':charging['reserve_kwh'],
        'terminal_open_min':0,'recharge_deadline_min':1800,'vehicle_cost':cost['vehicle_cost'],
        'deadhead_cost_per_min':cost['deadhead_cost_per_min'],'efficiency':charging['efficiency'],
        'graph_scope':'declared-movement-modes-only'}


def reference_witness(cell):
    """Construct/replay dedicated buses exactly from binary-stored energy inputs."""
    c=cell['case']; trips=c['trips']; modes=c['movements']; resources=c['resources']
    need(len(resources)==1 and resources[0]['start_min']==0 and resources[0]['end_min']==1800,'reference resource horizon')
    r=resources[0];need(r['connectors']==1 and r['per_bus_kw']==r['grid_kw']==360,'reference finite connector')
    need(c['battery_kwh']==400 and c['reserve_kwh']==0 and c['efficiency']==1,'reference unchanged battery physics')
    need(c['vehicle_cost']==100 and c['deadhead_cost_per_min']==0 and len(trips)==c['max_vehicles']==37,'reference full fleet/cost')
    outs={m['after']:m for m in modes if m['kind']=='pullout'};ins={m['before']:m for m in modes if m['kind']=='pullin'}
    need(len(outs)==len(ins)==37 and set(outs)==set(ins)=={t['id'] for t in trips},'reference complete directed pullout/pullin')
    jobs=[];service=sum((Q(t['energy_kwh']) for t in trips),Q(0));movement=Q(0)
    for t in trips:
        a,b=outs[t['id']],ins[t['id']]
        need(a['legs'][-1]['destination']==t['start_place'] and b['legs'][0]['origin']==t['end_place'],'reference directed service endpoints')
        legs=a['legs']+b['legs'];energy=Q(t['energy_kwh'])+sum((Q(l['energy_kwh']) for l in legs),Q(0))
        need(all(Q(l['energy_kwh'])>=0 for l in legs) and 0<=energy<=400,'reference monotone reserve before terminal')
        need(a['legs'][-1]['arrive_min']<=t['start_min'] and b['legs'][0]['depart_min']>=t['end_min'],'reference movement/service ordering')
        movement+=sum((Q(l['energy_kwh']) for l in legs),Q(0))
        jobs.append((Q(b['legs'][-1]['arrive_min']),t['id'],energy,a['id'],b['id']))
    jobs.sort();cursor=Q(c['terminal_open_min']);total=Q(0);sessions=[]
    for i,(release,tid,energy,first,last) in enumerate(jobs):
        start=max(release,cursor);end=start+energy/6
        need(start>=release and end<=1800 and start>=cursor,'reference serial release/deadline')
        need(Q(400)-energy>=0 and Q(400)-energy+energy==400,'reference full terminal SOC')
        sessions.append({'vehicle':i,'trip':tid,'movements':[first,last],'start_exact':str(start),'end_exact':str(end),'grid_energy_exact':str(energy)})
        total+=energy;cursor=end
    need(total==service+movement,'reference battery/grid conservation')
    objective=Q(3700)+Q(.2)*total
    saved=cell['reference_witness']
    need(saved['used_vehicle_count']==37 and saved['replay_ok'] is True and saved['solver_invoked'] is False,'saved reference classification')
    for key,value in [('service_energy_total_kwh',service),('one_trip_per_bus_pullout_pullin_energy_total_kwh',movement),('one_trip_per_bus_total_battery_energy_kwh',total),('total_terminal_charge_kwh',total),('last_terminal_charge_end_min',cursor),('maximum_one_trip_bus_energy_kwh',max(j[2] for j in jobs)),('latest_pullin_arrival_min',max(j[0] for j in jobs))]:
        near(saved[key],float(value),'saved independent reference '+key,1e-8)
    near(cell['reference_upper'],float(objective),'reference flat objective',1e-8)
    return {'buses':37,'grid_energy':total,'objective':objective,'last_end_min':cursor,
            'maximum_individual_energy':max(j[2] for j in jobs),'sessions':sessions,
            'scope':'Explicit feasible upper reference, not an optimum or solver start'}


def input_checks(frozen,payload):
    need(frozen['protocol']==PROTOCOL and frozen['freeze_label']==COMMIT,'exact public pilot source/protocol freeze')
    need(frozen['budget']==BUDGET,'all native and routine budgets unchanged')
    need(frozen['dataset']['doi']=='10.6084/m9.figshare.26088190.v1','versioned public DOI')
    need('creativecommons.org/licenses/by/4.0' in frozen['dataset']['license'],'CC BY4 attribution')
    cells=frozen['controls'];variants=payload['native_cases']
    need([c['id'] for c in cells]==['depot_15_flat','depot_16_flat'],'exact two independent cells')
    need([v['selected_depot_id'] for v in variants]==[15,16],'public variants')
    reports={}
    for cell,v in zip(cells,variants):
        c=reconstruct_case(v);depot=v['selected_depot_id']
        need(c==cell['case'],'full pinned case equality, no graph/service reduction')
        need(case_identity(c)==v['case_identity']==cell['case_identity']==IDENTITIES[depot],'case digest')
        need(cell['objective']=='pricing' and cell['prices']==[.2]*30,'single synthetic flat objective')
        need(cell['source_payload_sha256']==PAYLOAD_SHA,'cell public payload anchor')
        counts=Counter(m['kind'] for m in c['movements'])
        need(counts=={'pullout':37,'pullin':37,'direct':666,'depot':630 if depot==15 else 595},'complete declared movement graph')
        reports[cell['id']]={'trips':len(c['trips']),'movements':dict(counts),'identity':cell['case_identity'],'reference':reference_witness(cell)}
    return reports


def native_identity(stats):
    need(stats['backend']=='GRB' and stats['threads']==1,'requested backend/threads')
    need(0<stats['seconds_cap']<=180 and finite(stats['wall_s']) and stats['wall_s']>=0,'native cap/time')
    rt=stats['backend_runtime']
    need(rt['requested']==rt['model_solver_name']=='GRB' and rt['solver_module']=='mip.gurobi','actual backend no fallback')
    need(re.fullmatch('[0-9a-f]{64}',rt['native_library_sha256']) is not None and bool(rt['native_library_path']),'recorded native library identity')
    need(stats['n_vars']>0 and stats['n_constraints']>=stats['physical_constraints']>0,'native dimensions')
    for field in ('incumbent','lower_bound'):
        if stats[field] is not None:need(finite(stats[field]) and float(stats['raw_'+field+'_repr'])==stats[field],'native numeric representation '+field)


def audit_cell(cell,blob,reference):
    es=blob['events'];receipt=blob['receipt'];package=blob['result'];launch=blob['launch']
    names=[e['event'] for e in es]
    need(names==EVENTS[:len(names)] and len(es)<=6 and all(e['round']==0 for e in es),'one unique ordered round-zero phase')
    starts=names.count('native_start');returns=names.count('native_status')
    need(starts<=1 and returns<=1,'at most one cold native call')
    need(receipt['cell']==cell['id'] and receipt['native_calls_started']==starts and receipt['native_calls_returned']==returns,'exact phase accounting')
    need(launch['hard_timeout_s']==255,'hard child cap')
    command=launch['command'];need(command[command.index('-m')+1]=='experiments.sistig_pricing_pilot' and command[command.index('--worker')+1]==cell['id'],'owned worker dispatch')
    stats=es[1]['stats'] if returns else None
    if stats:native_identity(stats)
    near(receipt['native_wall_s'],stats['wall_s'] if stats else 0,'native time accounting',1e-9)
    record={'cell':cell['id'],'original_status':receipt['status'],'original_pass':receipt['pass'],
            'native_status':None if stats is None else stats['status'],'native_calls':starts,
            'native_wall_s':receipt['native_wall_s'],'conditional_bound':None,'raw_incumbent':None,
            'reference_objective':reference['objective'],'independent_global_optimum':None}
    if len(es)>=3:
        raw=compact.raw_primal(cell,es[0],stats,es[2])
        record['raw_incumbent']={k:raw[k] for k in ('variables','raw_objective','max_constraint_residual','constraint_checks')}
    if not package or package['result'].get('status') not in ('certified','bounded'):
        need(receipt['pass'] is False,'failed/incomplete cell not admitted')
        record['evidence_verdict']='NO ADMITTED INTERVAL; failure preserved'
        record['exception_type']=blob.get('exception',{}).get('type')
        record['exception_message']=blob.get('exception',{}).get('message')
        return record
    need(names==EVENTS and starts==returns==1,'complete finite interval trace')
    result=package['result'];assessment=package['assessment'];plan=result['plan']
    need(receipt['returncode']==0 and not receipt['hard_timeout'] and receipt['native_accounting_complete'] is True and not receipt['evidence_issues'],'passing worker receipt')
    need(package['cell']==cell['id'] and assessment['pass'] is True and receipt['pass'] is True and not assessment['issues'],'result/assessment ownership')
    need(result['stats']==stats and result['case_identity']==cell['case_identity'] and result['prices']==cell['prices'],'result native stats/input equality')
    need(finite(package['elapsed_s']) and 0<=package['elapsed_s']<=240,'scientific wall deadline')
    need(assessment['routine_cap_s']==240 and assessment['routine_within_budget'] is True and assessment['routine_elapsed_s']==package['elapsed_s'],'scientific deadline receipt')
    need(stats['status'] in ('OPTIMAL','FEASIBLE'),'admitted native status')
    ledger=compact.conversion(cell,raw,es[3],es[4],es[5],plan,es[0],stats)
    witness=physical.physical(cell,plan)
    objective=witness['ops']+sum(p*e for p,e in zip(cell['prices'],witness['load']))
    need(finite(stats['incumbent']) and finite(stats['lower_bound']),'finite native endpoints')
    near(stats['incumbent'],objective,'native incumbent versus independent physical objective',1e-6)
    need(stats['lower_bound']<=stats['incumbent']+GUARD and stats['lower_bound']<=objective+GUARD,'native lower consistency')
    lo=stats['lower_bound']-GUARD;hi=objective+GUARD
    near(result['lower'],lo,'outward lower guard',1e-8);near(result['upper'],hi,'outward upper guard',1e-8)
    near(result['gap'],hi-lo,'reported interval width',1e-8)
    need(result['gap']>=0 and result['status']==('certified' if result['gap']<=1e-4 else 'bounded'),'width classification')
    need(assessment['optimality_certified']==(result['status']=='certified'),'bounded not relabelled optimal')
    near(assessment['reference_upper'],cell['reference_upper'],'reference assessment consistency',1e-8)
    need(lo<=float(reference['objective'])+GUARD,'native lower versus independent known feasible reference')
    need(result['objective']=='complete-fleet-linear','explicit linear objective identity')
    near(result['charge_correction_objective_delta'],es[5]['charge_correction_objective_delta'],'saved correction delta',1e-12)
    record.update(evidence_verdict='PASS conditional numerical interval and independent physical replay',
        conditional_bound=[lo,hi],width=hi-lo,used_buses=len(plan['vehicles']),physical_witness=witness,
        correction_ledger=ledger,auxiliary_upper=min(hi,float(reference['objective'])+GUARD),
        backend_library_sha256=stats['backend_runtime']['native_library_sha256'])
    return record


def verify_manifest(attempt,manifest_sha):
    path=attempt/'MANIFEST.json';need(sha(path.read_bytes())==manifest_sha,'independently supplied manifest anchor')
    manifest=read(path);need(manifest['source_commit']==COMMIT,'manifest source commit')
    for name,entry in manifest['files'].items():
        p=Path(name);need(not p.is_absolute() and '..' not in p.parts,'safe manifest relative path')
        data=(attempt/p).read_bytes();need(sha(data)==entry['sha256'] and len(data)==entry['bytes'],'manifest bytes '+name)
    actual={str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file() and 'review' not in p.relative_to(attempt).parts and p.name!='MANIFEST.json'}
    need(actual==set(manifest['files']),'complete evidence manifest')
    return manifest


def read_blob(folder):
    events=[];issues=[]
    if (folder/'events.jsonl').exists():
        for i,line in enumerate((folder/'events.jsonl').read_bytes().splitlines()):
            try:events.append(json.loads(line))
            except (ValueError,UnicodeError):issues.append({'line':i+1,'error':'truncated/malformed JSON'});break
    def optional(name):return read(folder/name) if (folder/name).exists() else None
    result=optional('result.json')
    return {'events':events,'parse_issues':issues,'result':result,'receipt':read(folder/'receipt.json'),
            'launch':read(folder/'launch.json'),'exception':optional('exception.json')}


def corruptions(cells,blobs,references):
    """Copy-only evidence controls; no solve or alteration of saved artifacts."""
    out=[]
    candidates=[c for c in cells if blobs[c['id']]['result'] and blobs[c['id']]['result']['result'].get('status') in ('bounded','certified')]
    if not candidates:return out
    original=candidates[0]
    def event(b,name):return next(e for e in b['events'] if e['event']==name)
    def reject(label,change):
        cell=copy.deepcopy(original);blob=copy.deepcopy(blobs[cell['id']]);change(cell,blob)
        try:audit_cell(cell,blob,references[cell['id']]['reference'])
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError) as exc:out.append({'control':label,'rejected':True,'reason':str(exc)})
        else:raise AssertionError('Corrupted evidence accepted: '+label)
    def setraw(b,key,value):
        s=event(b,'native_incumbent');idx=s['mapping'][key][0];s['variables'][idx]['solution']={'value':value,'repr':repr(value)}
    reject('foreign round',lambda c,b:b['events'][0].__setitem__('round',1))
    reject('missing raw snapshot',lambda c,b:b['events'].pop(2))
    reject('duplicate phase',lambda c,b:b['events'].insert(1,copy.deepcopy(b['events'][0])))
    reject('raw coverage nonintegral',lambda c,b:setraw(b,'movement_selection',.5))
    reject('raw SOC changed',lambda c,b:setraw(b,'soc_before',-2.0))
    reject('omitted raw variable',lambda c,b:event(b,'native_incumbent')['variables'].pop())
    reject('wrong compact row count',lambda c,b:event(b,'native_status')['stats'].__setitem__('physical_constraints',1))
    reject('negative correction ledger changed',lambda c,b:event(b,'charge_normalization').__setitem__('negative_l1_exact','1'))
    reject('serial positive session omitted',lambda c,b:event(b,'serial_decoding')['charges'].pop())
    reject('physical terminal replenishment changed',lambda c,b:b['result']['result']['plan']['replay']['soc_trajectories'][0][-1].__setitem__('soc_kwh',399))
    reject('native result stats mismatch',lambda c,b:b['result']['result']['stats'].__setitem__('incumbent',1e9))
    reject('lower endpoint invented',lambda c,b:b['result']['result'].__setitem__('lower',1e9))
    reject('wrong price',lambda c,b:b['result']['result']['prices'].__setitem__(0,.3))
    reject('missing phase accounting',lambda c,b:b['receipt'].__setitem__('native_calls_started',0))
    reject('late scientific result',lambda c,b:b['result'].__setitem__('elapsed_s',241))
    reject('worker timeout after result',lambda c,b:b['receipt'].__setitem__('hard_timeout',True))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--attempt',type=Path,required=True)
    p.add_argument('--repository',type=Path,required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--out',type=Path);args=p.parse_args();repo=args.repository.resolve();attempt=args.attempt.resolve()
    out=args.out or Path(tempfile.gettempdir())/('sistig-pricing-audit-'+uuid.uuid4().hex+'.json')
    need(not out.exists() and not out.is_symlink() and repo not in out.resolve().parents,'exclusive report outside repository')
    start=time.perf_counter();manifest=verify_manifest(attempt,args.manifest_sha256);frozen=read(attempt/'frozen.json')
    for name,digest in frozen['source_hashes'].items():
        data=subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+name]);need(sha(data)==digest,'published frozen dependency '+name)
    data=subprocess.check_output(['git','-C',str(repo),'show',COMMIT+':'+PAYLOAD]);need(sha(data)==PAYLOAD_SHA,'independent public data anchor')
    refs=input_checks(frozen,json.loads(data));cells=frozen['controls'];summary=read(attempt/'summary.json')
    need(summary['protocol']==PROTOCOL and summary['source_hashes_unchanged'] is True,'unchanged source at completion')
    need([r['cell'] for r in summary['cells']]==[c['id'] for c in cells],'both sequential independent cells accounted')
    gate=frozen['compact_gate'];need(gate['attempt']=='result/native_pathflow/20260927-attempt1' and gate['freeze_label']=='ebb146e' and gate['independent_audit_status'].startswith('PASS for all 20'),'qualified compact gate identity')
    blobs={};records=[]
    for c,row in zip(cells,summary['cells']):
        folder=attempt/c['id'];inp=read(folder/'input.json')
        need({k:inp[k] for k in c}==c and inp['source_hashes']==frozen['source_hashes'] and inp['budget']==BUDGET,'complete per-cell input and dependency equality')
        blob=read_blob(folder);need(blob['receipt']==row,'saved summary/receipt equality');blobs[c['id']]=blob
        try:
            need(not blob['parse_issues'] or not row['pass'],'truncated evidence never admitted')
            records.append(audit_cell(c,blob,refs[c['id']]['reference']))
        except (AssertionError,ValueError,TypeError,KeyError,ZeroDivisionError) as exc:
            records.append({'cell':c['id'],'evidence_verdict':'FAIL independent audit','error':str(exc),'original_status':row['status']})
    supervisor=read(attempt/'supervisor_receipt.json')
    need(supervisor['outer_cap_s']==560 and supervisor['kill_grace_s']==10,'hard outer policy receipt')
    need(supervisor['timeout_exit']==(supervisor['returncode'] in (124,137)),'outer timeout/exit consistency')
    need(summary['all_pass']==all(r['pass'] for r in summary['cells']),'full original aggregate pass')
    if summary['all_pass']:need(supervisor['returncode']==0 and not supervisor['timeout_exit'],'successful attempt outer receipt')
    controls=corruptions(cells,blobs,refs) if all(not r['evidence_verdict'].startswith('FAIL') for r in records) else []
    report={'audit_status':'PASS numerical evidence' if all(r['evidence_verdict'].startswith('PASS') for r in records) else 'FAIL or unresolved numerical evidence',
        'scope':'Conditional native global lower bounds; independent complete raw-constraint and physical-witness/objective checks. No independently proved global optimum.',
        'source_commit':COMMIT,'manifest_sha256':args.manifest_sha256,'raw_files':len(manifest['files']),
        'input_checks':refs,'cells':records,'corruptions':controls,'supervisor_receipt':supervisor,
        'scheduler_audit':'PENDING separate immutable Slurm receipt review; no complete operational verdict yet',
        'auditor_sources':{p.name:sha(p.read_bytes()) for p in (HERE/'audit_sistig_pricing.py',HERE/'independent_physical_core.py',HERE/'independent_compact_core.py')},
        'wall_s':time.perf_counter()-start}
    with out.open('x') as f:json.dump(physical.pack(report),f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    verify_manifest(attempt,args.manifest_sha256)
    print(json.dumps({'status':report['audit_status'],'out':str(out.resolve()),'cells':[{'cell':r['cell'],'verdict':r['evidence_verdict']} for r in records],'corruptions_rejected':len(controls),'wall_s':report['wall_s']},indent=2))

if __name__=='__main__':main()
