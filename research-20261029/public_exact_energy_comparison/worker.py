"""Distinct completion of comparison only; no physical/semantic/proof replay."""
import argparse
from fractions import Fraction as Q
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];REL='research-20261029/public_exact_energy_comparison/'
OLD='d27f9f13ff8e61721dda39ee680be612c01c8ecc';BASE='research-20261029/public_exact_energy_target/attempt01/'
PINNED_SOURCE='6665c2b9f045410b4bbf19060b6780b0779f5534'
PRICE='f5ec2aa5770188d173af7297620a5fcea99fef9a';WEIGHT_PATH='research-20261029/public_price_witness/attempt01/MIXTURE.json.gz'
WEIGHT_SHA='8b3b30effbeb2234f32f8ce4c927b979b571f112db6adbb4481c84dac935efe0'
ASSIGNED=('SOURCE','Q0','TRANSFER','COMPARISON')
RESOURCES=dict(package_cpu_s=120,package_wall_s=180,worker_cpu_s=100,worker_wall_s=150,worker_self_hard_cpu_s=100,closure_cpu_s=20,closure_wall_s=30,observed_rss_bytes=5*1024**3,native_calls=0)
STAGES=dict(SOURCE=(10,15),Q0=(10,15),TRANSFER=(30,45),COMPARISON=(30,45))
INPUTS={k:(OLD,BASE+name) for k,name in dict(results='results.json',owner='owner_receipt.json',worker='worker_receipt.json',left='INCUMBENT_ROUTES.json.gz',right='RESPONSE_ROUTES.json.gz').items()}
INPUTS['weights']=(PRICE,WEIGHT_PATH)
FILES=('worker.py','run.py','projector.py','independent.py','PROTOCOL.md','API_HANDOFF.md')

class ResourceStop(RuntimeError):pass
def need(ok,message):
    if not ok:raise ValueError(message)
def usage():
    a,b=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime,self_cpu_s=a.ru_utime+a.ru_stime,peak_rss_bytes=max(a.ru_maxrss,b.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def encode(v):
    if isinstance(v,Q):return str(v)
    raise TypeError(type(v).__name__)
def write(path,v):
    with path.open('x') as stream:json.dump(v,stream,default=encode,indent=2,allow_nan=False);stream.write('\n')
def unique(pairs):
    result={}
    for key,value in pairs:need(key not in result,'Duplicate key');result[key]=value
    return result
def nonfinite(value):raise ValueError('Nonfinite token')
def decode(raw):return json.loads(raw,parse_float=str,parse_constant=nonfinite,object_pairs_hook=unique)
def git(rev,path):
    raw=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',rev+':'+path],cwd=ROOT,timeout=5)
    need(len(raw)<=512*1024**2,'Consumed buffer cap');return raw
def module(name,raw):
    result=types.ModuleType(name);exec(compile(raw,name,'exec'),result.__dict__);return result

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(100,100))
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out);rows=[];failure=None;manifest={};cache={};left=right=weights=lower=report=None
    def expired(signum,frame):raise ResourceStop('Stage wall/selfCPU ceiling')
    signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGPROF,expired)
    def stage(name,action):
        cpu,wall=STAGES[name];before=usage();elapsed=time.monotonic()-started
        if before['cpu_s']+cpu+20>=100 or before['self_cpu_s']+cpu+20>=100 or elapsed+wall+30>=150 or before['peak_rss_bytes']>5*1024**3:raise ResourceStop('Full stage plus closure unfunded')
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic()
        signal.setitimer(signal.ITIMER_REAL,wall);signal.setitimer(signal.ITIMER_PROF,cpu)
        try:
            value=action();write(out/(name+'.json'),value);after=usage();duration=time.monotonic()-anchor
            if after['cpu_s']-before['cpu_s']>cpu or duration>wall or after['peak_rss_bytes']>5*1024**3:
                row.update(status='LATE',reason='Published but stage resource ceiling exceeded');raise ResourceStop(row['reason'])
            row.update(status='DELIVERED',cpu_s=after['cpu_s']-before['cpu_s'],elapsed_s=duration);return value
        except BaseException as exc:
            if row['status']=='ATTEMPTED':row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc))
            raise
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.setitimer(signal.ITIMER_PROF,0)
    try:
        need(sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize,'Isolated stdlib command')
        need(sys.implementation.name=='cpython' and sys.version_info[:3]==(3,12,2) and (sys.float_info.radix,sys.float_info.mant_dig,sys.float_info.max_exp,sys.float_info.rounds)==(2,53,1024,1),'Frozen runtime')
        raw_control=(HERE/'LAUNCH.json').read_bytes();control=decode(raw_control)
        need(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision and re.fullmatch('[0-9a-f]{40}',args.source_revision),'No frozen authority')
        need(control.get('run_id')=='attempt01' and out.resolve()==(HERE/'attempt01').resolve() and tuple(control.get('assigned',()))==ASSIGNED,'Namespace/denominator')
        need(control.get('resources')==RESOURCES and control.get('stages')=={k:list(v) for k,v in STAGES.items()} and control.get('inputs')=={k:list(v) for k,v in INPUTS.items()},'Fixed resources/pins')
        need(control.get('native_threads')==1 and all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')),'Thread contract')
        def admission():
            manifest['LAUNCH.json']=dict(bytes=len(raw_control),sha256=hashlib.sha256(raw_control).hexdigest(),binding='separate frozen control')
            for name in FILES:
                raw=git(args.source_revision,REL+name);need(raw==(HERE/name).read_bytes(),'Source differs '+name);cache[name]=raw
                manifest[name]=dict(revision=args.source_revision,path=REL+name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            return dict(status='SOURCE_ADMITTED',manifest=manifest,public_inputs_read=False,native_calls=0)
        stage('SOURCE',admission)
        projector=module('comparison_projector',cache['projector.py']);checker=module('comparison_independent',cache['independent.py']);cache.clear()
        def q0():
            a=projector.literal_qualification(checker);b=checker.literal_qualification();need(a['status']=='PASS' and b['status']=='PASS','Q0 failed')
            return dict(status='PASS',projector=a,independent=b,native_calls=0)
        stage('Q0',q0)
        closed=None
        def consume(key):
            rev,path=INPUTS[key];raw=git(rev,path)
            if key=='weights':
                prior=closed['manifest']['weights'];need(prior==dict(revision=PRICE,path=WEIGHT_PATH,bytes=1182,sha256=WEIGHT_SHA) and len(raw)==1182,'Closed fixed weight authority')
                manifest[key]=dict(revision=rev,path=path,bytes=len(raw),prior_sha256=WEIGHT_SHA,binding='Same Git object; prior digest adopted without rehash')
            else:manifest[key]=dict(revision=rev,path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if path.endswith('.gz'):
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:raw=stream.read(512*1024**2+1)
                need(len(raw)<=512*1024**2,'Decompressed buffer cap')
            return decode(raw)
        def transfer():
            nonlocal closed,left,right,weights,lower
            closed=consume('results');owner=consume('owner');worker=consume('worker')
            old=('SOURCE_ADMISSION','Q0','TARGET','LOWER','INCUMBENT_ROUTES','RESPONSE_ROUTES','COMPARISON')
            need(closed['status']=='FAILED' and closed['scientific_status']=='NOT_CERTIFIED' and closed['comparison'] is None and closed['failure']=='ValueError: String dictionary keys required','Exact historical failed completion')
            need(tuple(closed['assigned'])==old and tuple(r['id'] for r in closed['rows'])==old and all(r['status']=='DELIVERED' for r in closed['rows'][:6]) and closed['rows'][6]['status']=='FAILED','Fixed predecessor denominator')
            need(closed['resource_pass'] is True and closed['native_calls']==0 and owner['source_revision']==PINNED_SOURCE and owner['child_exit']==1 and owner['reaped'] is True and owner['failure'] is None and owner['resource_pass'] is True and owner['native_calls']==0,'Failed owner closure')
            need(tuple(owner['assigned'])==tuple(worker['assigned'])==old and owner['ledger']==closed['rows'] and worker['rows']==closed['rows'] and worker['status']=='FAILED' and worker['failure']==closed['failure'] and worker['resource_pass'] is True and worker['native_calls']==0,'Closed ledgers agree')
            need(closed['rows'][3]['summary']==closed['lower'] and closed['rows'][4]['summary']==closed['points']['INCUMBENT_ROUTES'] and closed['rows'][5]['summary']==closed['points']['RESPONSE_ROUTES'],'Closed scientific summaries agree')
            lower=dict(closed['lower']);need(lower['status']=='COMPLETE_TARGET_BOUND' and lower['target_identity']==projector.IDENTITY,'Delivered target lower')
            lower={k:lower[k] for k in ('status','target_identity','lower')};lower['lower']=projector.q(lower['lower'])
            packet=consume('left');left=projector.project(packet,closed['points']['INCUMBENT_ROUTES']);del packet
            packet=consume('right');right=projector.project(packet,closed['points']['RESPONSE_ROUTES']);del packet
            packet=consume('weights');weights={k:projector.q(packet['mixture'][k]) for k in ('lambda_left','lambda_right')};del packet
            weights.update(source_revision=PRICE,path=WEIGHT_PATH)
            return dict(status='TRANSFERRED_ADMITTED_SUMMARIES',prior_attempt_status='FAILED',prior_source=PINNED_SOURCE,lower=lower,left=left,right=right,weights=weights,manifest=manifest,
                physical_replays=0,semantic_reconstructions=0,tree_checks=0,face_attempts=0,native_calls=0)
        stage('TRANSFER',transfer)
        def compare():
            objects=dict(left=left,right=right,weights=weights,lower=lower);seals={k:checker.seal(v) for k,v in objects.items()}
            def admitted(label,obj):return label in objects and obj is objects[label] and checker.seal(obj)==seals[label]
            proposed=projector.direct(left,right,weights,lower['lower'])
            verified=checker.check(left,right,weights,lower,projector.IDENTITY,admit=admitted,seals=seals)
            need(verified.get('status') in ('POSITIVE_TARGET_GAP_CERTIFIED','TARGET_GAP_UNRESOLVED'),'Independent result missing')
            for key in ('status','lower','upper','gap','physical_upper','loads'):need(verified[key]==proposed[key],'Direct/variance comparison differs '+key)
            for direct_key,independent_key in (('physical_lower_floor_units','lower_floor_units'),('hull_upper_ceil_units','upper_ceil_units'),('gap_lower_floor_units','gap_floor_units'),('physical_upper_ceil_units','physical_upper_ceil_units')):
                need(proposed['outward'][direct_key]==verified[independent_key],'Independent outward arithmetic differs '+direct_key)
            return dict(proposed,independent=verified,physical_replays=0,tree_checks=0,face_attempts=0,native_calls=0,predecessor_remains_failed=True)
        report=stage('COMPARISON',compare)
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.setitimer(signal.ITIMER_PROF,0)
    for name in ASSIGNED[len(rows):]:rows.append(dict(id=name,status='UNATTEMPTED',reason=failure or 'Missing dependency'))
    observed=usage();elapsed=time.monotonic()-started;passed=observed['cpu_s']<100 and observed['self_cpu_s']<100 and elapsed<150 and observed['peak_rss_bytes']<=5*1024**3
    status='COMPLETED' if failure is None and passed and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    result=dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resources=observed,elapsed_s=elapsed,resource_pass=passed,
        scientific_status=report['status'] if status=='COMPLETED' else 'NOT_CERTIFIED',comparison=report,manifest=manifest,native_calls=0,
        physical_replays=0,tree_checks=0,face_attempts=0,predecessor_remains_failed=True)
    write(out/'results.json',result);write(out/'worker_receipt.json',dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resource_pass=passed,resources=usage(),elapsed_s=time.monotonic()-started,native_calls=0))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
