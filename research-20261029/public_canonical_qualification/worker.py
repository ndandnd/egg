"""One source-bound canonical metadata/provenance gate; stdlib, no physical solve."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REL='research-20261029/public_canonical_qualification/'
OD_REL='research-20261029/public_movement_qualification/attempt01/'
OD_REV='6f87f052c1a6e30ffb89a984743514e0b2744aa1'
RICH_REV='2f386362aa241a8a4f197a88a50fa150b6d47d9c'
RICH_PATH='data/public/sistig_26088190_v1/hildenbrand_native_cases.json'
RICH_SHA='af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6'
DESC_REV='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
DESC_PATH='research-20261029/public_support_resolution/attempt01/case_descriptor.json'
ASSIGNED=('SOURCE_ADMISSION','Q0','PUBLIC_METADATA','CANONICAL','INDEPENDENT')
FILES=('worker.py','run.py','extractor.py','producer.py','checker.py','fixtures.py','PROTOCOL.md','FIELD_AUTHORITY.md')
LIMITS=dict(package_cpu_s=180,package_wall_s=240,worker_cpu_s=150,worker_wall_s=210,
    worker_self_hard_cpu_s=130,stage_gate_cpu_s=110,stage_gate_wall_s=180,observed_rss_bytes=1024**3,native_calls=0)
INPUTS=dict(rich=dict(revision=RICH_REV,path=RICH_PATH,bytes=8046032,prior_sha256=RICH_SHA),
    descriptor=dict(revision=DESC_REV,path=DESC_PATH),od=dict(revision=OD_REV,paths=[OD_REL+n for n in ('results.json','PUBLIC_OD.json','owner_receipt.json')]))

def need(ok,message):
    if not ok:raise ValueError(message)
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def usage():
    a,b=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime,
        peak_rss_bytes=max(a.ru_maxrss,b.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def unique(pairs):
    result={}
    for key,value in pairs:need(key not in result,'Duplicate JSON key');result[key]=value
    return result
def nonfinite(value):raise ValueError('Nonfinite JSON token')
def decode(raw):return json.loads(raw,parse_float=str,parse_int=int,parse_constant=nonfinite,object_pairs_hook=unique)
def module(name,raw):
    result=types.ModuleType(name);exec(compile(raw,name,'exec'),result.__dict__);return result
def git(revision,path):
    raw=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=5)
    need(len(raw)<=20*1024**2,'Input/source byte cap');return raw
def summary(value):
    return {k:v for k,v in value.items() if k not in ('checks','predicates','wait_classifications','direct_wait_classifications')}

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(130,130))
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out);rows=[];failure=None;cache={};manifest={};p=None;claim=None;audit=None
    def stage(name,action):
        observed=usage();need(observed['cpu_s']<110 and time.monotonic()-started<180 and observed['peak_rss_bytes']<=1024**3,'Resource/closure gate exhausted')
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic()
        try:
            value=action();write(out/(name+'.json'),value)
            row.update(status='DELIVERED',stage_elapsed_s=time.monotonic()-anchor);return value
        except BaseException as exc:row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc));raise
    try:
        need(sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize,'Required -I -S and no optimization')
        need(sys.implementation.name=='cpython' and sys.version_info[:3]==(3,12,2),'Frozen CPython 3.12.2 required')
        need((sys.float_info.radix,sys.float_info.mant_dig,sys.float_info.max_exp,sys.float_info.rounds)==(2,53,1024,1),'Frozen binary64 profile')
        raw_control=(HERE/'LAUNCH.json').read_bytes();control=decode(raw_control)
        need(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision and re.fullmatch('[0-9a-f]{40}',args.source_revision),'No frozen source authority')
        need(control.get('run_id')=='attempt01' and out.resolve()==(HERE/'attempt01').resolve() and tuple(control.get('assigned',()))==ASSIGNED,'Namespace/denominator')
        need(control.get('resources')==LIMITS and control.get('inputs')==INPUTS and control.get('native_threads')==1,'Control resource/input binding')
        need(control.get('runtime')==dict(implementation='cpython',version='3.12.2',radix=2,mant_dig=53,max_exp=1024,rounds=1),'Control runtime binding')
        need(all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')),'Thread environment')
        def admission():
            manifest['LAUNCH.json']=dict(bytes=len(raw_control),sha256=hashlib.sha256(raw_control).hexdigest(),binding='separate frozen control')
            for name in FILES:
                raw=(HERE/name).read_bytes();fixed=git(args.source_revision,REL+name);need(raw==fixed,'Changed source '+name)
                cache[name]=raw;manifest[name]=dict(revision=args.source_revision,path=REL+name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            return dict(status='SOURCE_ADMITTED',manifest=manifest,public_inputs_read=False,native_calls=0,
                runtime=dict(implementation='cpython',version='3.12.2',radix=2,mant_dig=53,max_exp=1024,rounds=1))
        stage('SOURCE_ADMISSION',admission)
        extractor=module('canonical_extractor',cache['extractor.py']);producer=module('canonical_producer',cache['producer.py'])
        checker=module('canonical_checker',cache['checker.py']);fixtures=module('canonical_fixtures',cache['fixtures.py']);cache.clear()
        def q0():
            value=fixtures.literal_qualification(extractor,producer,checker);need(value.get('status')=='PASS','Q0 failed');return value
        stage('Q0',q0)
        def public():
            nonlocal p
            # Prior closed evidence is admitted, never rerun. All reads follow fixed source paths.
            old={}
            for name in ('results.json','PUBLIC_OD.json','owner_receipt.json'):
                raw=git(OD_REV,OD_REL+name);old[name]=decode(raw)
                manifest['OD/'+name]=dict(revision=OD_REV,path=OD_REL+name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            result,packet,owner=(old[n] for n in ('results.json','PUBLIC_OD.json','owner_receipt.json'))
            names=('SOURCE_ADMISSION','Q0','PUBLIC_OD','INDEPENDENT')
            need(result.get('status')=='COMPLETED' and result.get('scientific_status')=='PASS' and result.get('resource_pass') is True,'Prior OD not closed PASS')
            need(tuple(result.get('assigned',()))==names and tuple(r['id'] for r in result['rows'])==names and all(r['status']=='DELIVERED' for r in result['rows']),'Prior complete denominator')
            need(owner.get('resource_pass') is True and owner.get('failure') is None and owner.get('child_exit')==0 and owner.get('reaped') is True,'Prior owner closure')
            need(tuple(owner.get('assigned',()))==names and owner.get('ledger')==result['rows'],'Prior owner ledger')
            need(owner.get('source_revision')=='4421b7f0b801e47be13aa1e12ca2dd3bc4f3e9b2','Prior source identity')
            need(result['independent'].get('status')=='PASS' and result['independent'].get('metric_status')=='PASS' and result['independent'].get('summary_matches') is True,'Prior independent agreement')
            need(result.get('claim')==packet.get('claim') and packet['claim'].get('status')=='PASS' and packet.get('native_calls')==0,'Prior packet identity')
            need(result.get('native_calls')==0 and owner.get('native_calls')==0,'Prior native-free scope')
            need(packet.get('input')==dict(revision=RICH_REV,path=RICH_PATH,bytes=8046032,sha256=RICH_SHA),'Same rich input authority')
            raw=git(RICH_REV,RICH_PATH);need(len(raw)==8046032,'Rich buffer size');rich=decode(raw)
            manifest['rich']=dict(INPUTS['rich'],binding='exact Git object; prior closed SHA adopted without rehash')
            del raw
            raw=git(DESC_REV,DESC_PATH);descriptor=decode(raw)
            manifest['descriptor']=dict(revision=DESC_REV,path=DESC_PATH,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());del raw
            transfer=dict(revision=OD_REV,source_bound_pass=True,same_rich_input=True,input_revision=RICH_REV,input_path=RICH_PATH)
            p=extractor.project(rich,descriptor,transfer);del rich,descriptor,old
            return dict(status='PROJECTED',expected_services=37,expected_case_identity=extractor.CASE_TOKEN,manifest=manifest,
                prior_OD_adopted=True,old_triangles_rerun=False,native_calls=0)
        stage('PUBLIC_METADATA',public)
        claim=stage('CANONICAL',lambda:producer.qualify(p))
        def independent():
            value=checker.independently_check(p,claim)
            need(claim.get('status') in ('PASS','FAIL') and value.get('summary_matches') is True and value.get('independent_status')==claim['status'] and value.get('status')==claim['status'],'Unknown/disagreement')
            return value
        audit=stage('INDEPENDENT',independent)
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    for name in ASSIGNED[len(rows):]:rows.append(dict(id=name,status='UNATTEMPTED',reason=failure or 'Missing dependency'))
    observed=usage();elapsed=time.monotonic()-started
    passed=observed['cpu_s']<150 and elapsed<210 and observed['peak_rss_bytes']<=1024**3
    status='COMPLETED' if failure is None and passed and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    result=dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resource_pass=passed,resources=observed,elapsed_s=elapsed,
        scientific_status=claim['status'] if status=='COMPLETED' else 'NOT_CERTIFIED',claim=summary(claim) if claim else None,independent=summary(audit) if audit else None,
        native_calls=0,broader_opportunity_extension='UNATTEMPTED',scope='Canonical coverage and stored binary provenance only; no path/wait energy dominance or public support scope extension.')
    write(out/'results.json',result)
    write(out/'worker_receipt.json',dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resource_pass=passed,resources=usage(),elapsed_s=time.monotonic()-started,native_calls=0))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
