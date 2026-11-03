"""One prospective exact qualification phase; nine fixed paid rows."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction as Q
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
import types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REL='research-20261029/full_lossy_polygon_qualification/'
IDS=('lossless-full','charge-loss-full','export-loss-full','both-loss-sparse',
     'terminal-boundary','zero-early-full','zero-terminal-empty','common-transition-full')
ASSIGNED=('Q0',)+IDS
FILES=('worker.py','run.py','reference.py','candidate.py','qualification.py','CASES.json','PROTOCOL.md')

class StageLimit(RuntimeError):pass
class FundingStop(RuntimeError):pass
def need(ok,message):
    if not ok:raise ValueError(message)
def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)
def write(path,value,packed=False):
    if packed:
        with path.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as z:
                with io.TextIOWrapper(z,encoding='utf-8') as stream:
                    json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'));stream.write('\n')
    else:
        with path.open('x') as stream:json.dump(value,stream,default=encode,indent=2,allow_nan=False);stream.write('\n')
def usage():
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(self_cpu_s=own.ru_utime+own.ru_stime,
        inclusive_cpu_s=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime,
        peak_rss_bytes=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def load(name,raw):
    m=types.ModuleType(name);exec(compile(raw,name,'exec'),m.__dict__);return m
def expired(signum,frame):raise StageLimit('Complete stage CPU/wall allowance exhausted')

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(270,270))
    signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGPROF,expired)
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out).resolve();rows=[];failures=[];cache={};manifest={};cases=None
    def funded(cpu,wall):
        u=usage()
        if not(u['self_cpu_s']+cpu+40<270 and u['inclusive_cpu_s']+cpu+40<275
               and time.monotonic()-started+wall+60<540):
            raise FundingStop('Full next-stage allowance plus protected final reserve unavailable')
        if u['peak_rss_bytes']>1024**3:
            raise FundingStop('Observed memory allowance exceeded before next stage; resource-fatal')
    def clocks(cpu,wall):
        signal.setitimer(signal.ITIMER_PROF,cpu);signal.setitimer(signal.ITIMER_REAL,wall)
    def stopclocks():
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    def stage(name,cpu,wall,action):
        funded(cpu,wall);row=dict(id=name,status='ATTEMPTED');rows.append(row)
        anchor=time.monotonic();before=usage();clocks(cpu,wall)
        try:
            value=action();write(out/(name+'.json.gz'),value,True)
            need(value.get('status') in ('PASS','MATCHED'),'Scientific stage did not pass; packet preserved')
            after=usage();elapsed=time.monotonic()-anchor
            if after['inclusive_cpu_s']-before['inclusive_cpu_s']>cpu or elapsed>wall:
                raise StageLimit('Complete stage exceeded its funded allowance')
            if after['peak_rss_bytes']>1024**3:raise FundingStop('Observed memory allowance exceeded')
            row.update(status='DELIVERED',elapsed_s=elapsed,resources=after,
                       summary=value.get('summary',dict(status=value.get('status'))))
        except BaseException as exc:
            row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc))
            if not (out/(name+'.json.gz')).exists():
                write(out/(name+'.json.gz'),dict(status='FAILED',reason=row['reason']),True)
            raise
        finally:
            row['pre_status_publication_elapsed_s']=time.monotonic()-anchor
            try:write(out/(name+'.status.json'),row)
            finally:stopclocks()
        return value
    try:
        funded(20,30);admission_start=started
        # process usage includes interpreter startup; preflight has no unpaid
        # import/read preparation before its inclusive20CPU allowance.
        clocks(max(0.001,20-usage()['inclusive_cpu_s']),max(0.001,30-(time.monotonic()-started)))
        try:
            need(not sys.flags.optimize,'Assertions required')
            control_raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(control_raw)
            need(control.get('status')=='FROZEN' and control.get('execution_authorized') is True and control.get('source_revision')==args.source_revision
                 and re.fullmatch('[0-9a-f]{40}',args.source_revision) is not None,'No frozen source authority')
            need(control.get('run_id')=='attempt01' and out==(HERE/'attempt01').resolve()
                 and tuple(control.get('assigned',()))==ASSIGNED,'Fixed namespace/denominator mismatch')
            need([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_self_cpu_s','worker_inclusive_cpu_s','worker_wall_s')]
                 ==[300,600,270,275,540],'Worker resource declaration mismatch')
            need(control.get('native_calls')==0 and control.get('observed_rss_bytes')==1024**3
                 and control.get('native_threads')==1
                 and control.get('stage_limits')==dict(preflight=[20,30],Q0=[20,30],case=[20,40],final_reserve=[40,60])
                 and control.get('hard_deadline_utc')=='2026-10-29T18:10:45Z'
                 and tuple(control.get('source_files',()))==FILES,'Limits/source closure mismatch')
            need(datetime.now(timezone.utc)<datetime(2026,10,29,18,10,45,tzinfo=timezone.utc),'Human deadline passed')
            manifest['LAUNCH.json']=dict(bytes=len(control_raw),sha256=hashlib.sha256(control_raw).hexdigest(),binding='separate frozen control')
            for name in FILES:
                raw=(HERE/name).read_bytes()
                frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',args.source_revision+':'+REL+name],cwd=ROOT,timeout=2)
                need(raw==frozen,'Frozen source/input differs: '+name)
                cache[name]=raw;manifest[name]=dict(revision=args.source_revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            cases=json.loads(cache['CASES.json']);need(tuple(c['id'] for c in cases)==IDS,'Fixed eight-case suite changed')
            reference=load('full_lossy_raw_reference',cache['reference.py']);candidate=load('full_lossy_formula',cache['candidate.py'])
            qualification=load('full_lossy_compare',cache['qualification.py'])
            write(out/'admission.json',dict(status='ADMITTED_SOURCE',files=manifest,case_ids=list(IDS),native_calls=0))
            need(usage()['inclusive_cpu_s']<=20
                 and time.monotonic()-admission_start<=30,'Admission exceeded complete allowance')
        finally:stopclocks()
        def q0():
            value=qualification.controls(reference,candidate)
            return value
        stage('Q0',20,30,q0)
        for spec in cases:
            try:
                def action(spec=spec):
                    physical=None;analytic=None;comparison=None
                    try:
                        physical=reference.enumerate_physical(spec);analytic=candidate.derive(spec)
                        comparison=qualification.compare(spec,reference,physical,analytic)
                    except (StageLimit,FundingStop,MemoryError,reference.ReferenceLimit):raise
                    except Exception as exc:
                        return dict(status='FAILED',case=spec,reference=physical,candidate=analytic,comparison=comparison,
                            reason=type(exc).__name__+': '+str(exc))
                    return dict(status='MATCHED' if comparison.get('status')=='PASS' else 'FAILED',case=spec,reference=physical,candidate=analytic,comparison=comparison,
                        summary=dict(status=comparison['status'],native_calls=0,
                            matching_count=comparison['matching_count'],cardinality_count=comparison['cardinality_count'],
                            strict_replayed_vertices=comparison['strict_replayed_vertices'],
                            cardinalities=comparison['cardinalities']))
                stage(spec['id'],20,40,action)
            except (FundingStop,StageLimit,MemoryError,reference.ReferenceLimit):raise
            except Exception as exc:
                failures.append(dict(id=spec['id'],reason=type(exc).__name__+': '+str(exc)))
                # A failed literal is retained; other prospectively assigned cases
                # receive one fresh stage if their full allowance remains funded.
    except BaseException as exc:failures.append(dict(id='package',reason=type(exc).__name__+': '+str(exc)))
    finally:stopclocks()
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='Earlier qualification/admission/funding failure'))
    clocks(40,60)
    u=usage();elapsed=time.monotonic()-started
    accepted=u['self_cpu_s']<270 and u['inclusive_cpu_s']<275 and elapsed<540 and u['peak_rss_bytes']<=1024**3
    status='COMPLETED' if accepted and not failures and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    report=dict(status=status,assigned=list(ASSIGNED),rows=rows,failures=failures,resource_pass=accepted,
        resources=u,elapsed_s=elapsed,native_calls=0,
        scientific_scope='Eight full-polygon implementation literals plus Q0; continuum theorem rests on proof')
    write(out/'results.json',report);write(out/'worker_receipt.json',dict(report,rows=None,resources=usage(),elapsed_s=time.monotonic()-started))
    stopclocks()
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
