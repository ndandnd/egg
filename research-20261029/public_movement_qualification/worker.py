"""Single source-bound public OD gate; no routes, witnesses or solver imports."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REL='research-20261029/public_movement_qualification/'
INPUT_REV='2f386362aa241a8a4f197a88a50fa150b6d47d9c'
INPUT_PATH='data/public/sistig_26088190_v1/hildenbrand_native_cases.json'
INPUT_SHA='af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6'
ASSIGNED=('SOURCE_ADMISSION','Q0','PUBLIC_OD','INDEPENDENT')
FILES=('worker.py','run.py','producer.py','independent.py','extractor.py','PROTOCOL.md','FIELD_AUTHORITY.md')
MAX_BYTES=20*1024**2

def need(ok,message):
    if not ok:raise ValueError(message)
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def usage():
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime,
                peak_rss_bytes=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def module(name,raw):
    result=types.ModuleType(name);exec(compile(raw,name,'exec'),result.__dict__);return result
def unique_object(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'Duplicate JSON object key');result[key]=value
    return result
def nonfinite(value):raise ValueError('Nonfinite JSON token: '+value)

def literal_document():
    # Two locations, exact30-second travel lattice, both matrices metric.
    return dict(source_field_semantics={
        'deadhead_trip_matrix.distances':'m; directional matrix values retained exactly',
        'deadhead_trip_matrix.times':'s; directional matrix values retained exactly'},
        source_data=dict(deadhead_stop_order_source=[15,17],stops=[dict(id=15,b_depot=True),dict(id=17,b_depot=False)],
            deadhead_arcs_directed_row_major=[dict(origin_stop_id=a,destination_stop_id=b,
                distance_m_source=0 if a==b else '1000.25',time_sec_source=0 if a==b else 30)
                for a in (15,17) for b in (15,17)]),
        native_cases='FORBIDDEN_LITERAL_SENTINEL_NOT_ACCESSED')

def qualification(extractor,producer,checker):
    doc=literal_document();full=extractor.project_od(doc)
    p={key:full[key] for key in ('locations','arcs','distance_unit','time_unit')};p['source_bytes']=1024
    claim=producer.qualify_od(p);verified=checker.independently_check(p,claim)
    need(claim['status']=='PASS' and verified['status']=='PASS','Literal metric anchor')
    controls=[]
    for label,change in [
        ('duplicate_arc',lambda d:d['source_data']['deadhead_arcs_directed_row_major'].__setitem__(1,copy.deepcopy(d['source_data']['deadhead_arcs_directed_row_major'][0]))),
        ('missing_arc',lambda d:d['source_data']['deadhead_arcs_directed_row_major'].pop()),
        ('float_quantity',lambda d:d['source_data']['deadhead_arcs_directed_row_major'][1].__setitem__('distance_m_source',1.0)),
        ('boolean_quantity',lambda d:d['source_data']['deadhead_arcs_directed_row_major'][1].__setitem__('time_sec_source',True)),
        ('changed_units',lambda d:d['source_field_semantics'].__setitem__('deadhead_trip_matrix.times','minutes'))]:
        changed=copy.deepcopy(doc);change(changed)
        try:extractor.project_od(changed)
        except (ValueError,KeyError,TypeError):controls.append(dict(id=label,rejected=True))
        else:raise ValueError('Extractor accepted: '+label)
    # Producer and checker supply fixed source-only arithmetic controls.
    a=producer.literal_qualification();b=checker.literal_qualification()
    need(a['status']=='PASS' and b['status']=='PASS','Independent literal controls')
    return dict(status='PASS',extractor_anchor=verified,extractor_controls=controls,
        producer_literals=a,independent_literals=b,native_calls=0)

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(620,620))
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out);rows=[];failure=None;manifest={};cache={};projected=None;claim=None;verified=None
    def stage(name,action):
        need(usage()['cpu_s']<600 and time.monotonic()-started<780,'Closure reserve exhausted')
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic()
        try:
            value=action();write(out/(name+'.json'),value)
            row.update(status='DELIVERED',stage_elapsed_s=time.monotonic()-anchor)
            write(out/(name+'.status.json'),row);return value
        except BaseException as exc:
            row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc));raise
    try:
        need(not sys.flags.optimize and sys.flags.isolated and sys.flags.no_site,'Isolated nonoptimized stdlib command required')
        raw_control=(HERE/'LAUNCH.json').read_bytes();control=json.loads(raw_control)
        need(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision
             and re.fullmatch('[0-9a-f]{40}',args.source_revision),'Frozen source required')
        need(control.get('run_id')=='attempt01' and out.resolve()==(HERE/'attempt01').resolve()
             and tuple(control.get('assigned',()))==ASSIGNED,'Exact namespace/denominator')
        need([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s')]==[720,900,660,840]
             and control.get('observed_rss_bytes')==5*1024**3 and control.get('native_calls')==0,'Resource declaration')
        need(control.get('input')==dict(revision=INPUT_REV,path=INPUT_PATH,sha256=INPUT_SHA,bytes=8046032),'Exact public source identity')
        def admission():
            manifest['LAUNCH.json']=dict(bytes=len(raw_control),sha256=hashlib.sha256(raw_control).hexdigest(),binding='separate frozen control')
            for name in FILES:
                raw=(HERE/name).read_bytes()
                fixed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',args.source_revision+':'+REL+name],cwd=ROOT,timeout=5)
                need(raw==fixed,'Source mismatch: '+name);cache[name]=raw
                manifest[name]=dict(revision=args.source_revision,path=REL+name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            return dict(status='SOURCE_ADMITTED',files=manifest,public_data_consumed=False,native_calls=0)
        stage('SOURCE_ADMISSION',admission)
        extractor=module('od_extractor',cache['extractor.py']);producer=module('od_producer',cache['producer.py']);checker=module('od_independent',cache['independent.py']);cache.clear()
        stage('Q0',lambda:qualification(extractor,producer,checker))
        def public():
            nonlocal projected,claim
            # Consume the committed public buffer once; never follow paths inside it.
            raw=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',INPUT_REV+':'+INPUT_PATH],cwd=ROOT,timeout=10)
            need(len(raw)==8046032 and len(raw)<=MAX_BYTES,'Public byte bound/identity')
            digest=hashlib.sha256(raw).hexdigest();need(digest==INPUT_SHA,'Public input hash mismatch')
            document=json.loads(raw,parse_float=str,parse_int=int,parse_constant=nonfinite,object_pairs_hook=unique_object)
            full=extractor.project_od(document)
            projected={key:full[key] for key in ('locations','arcs','distance_unit','time_unit')};projected['source_bytes']=len(raw)
            del document,raw
            claim=producer.qualify_od(projected)
            metadata={key:value for key,value in full.items() if key not in ('locations','arcs')}
            return dict(input=dict(revision=INPUT_REV,path=INPUT_PATH,bytes=8046032,sha256=digest),
                metadata=metadata,claim=claim,public_variants_accessed=False,native_calls=0)
        stage('PUBLIC_OD',public)
        verified=stage('INDEPENDENT',lambda:checker.independently_check(projected,claim))
        need(verified.get('summary_matches') is True and verified.get('metric_status')==claim['status']
             and claim['status'] in ('PASS','FAIL'),'Independent complete-matrix agreement failed')
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    for name in ASSIGNED[len(rows):]:rows.append(dict(id=name,status='UNATTEMPTED',reason=failure or 'Missing dependency'))
    observed=usage();elapsed=time.monotonic()-started
    passed=observed['cpu_s']<660 and elapsed<840 and observed['peak_rss_bytes']<=5*1024**3
    status='COMPLETED' if not failure and passed and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    result=dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resources=observed,elapsed_s=elapsed,resource_pass=passed,
        scientific_status=claim['status'] if status=='COMPLETED' else 'NOT_CERTIFIED',claim=claim,independent=verified,
        native_calls=0,mode_coverage_status='UNATTEMPTED',energy_dominance_status='UNATTEMPTED',charging_access_status='UNATTEMPTED',
        scope='Only exact public OD metric gate. No extension of current support certificate, new route solve, physical replay, or joint path realizability claim.')
    write(out/'results.json',result);write(out/'worker_receipt.json',dict(result,resources=usage(),elapsed_s=time.monotonic()-started))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
