"""One prospective exact qualification phase; eleven fixed paid states."""
import argparse
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
REL='research-20261029/lossy_projection_qualification/'
IDS=('lossless-one','charge-loss-one','discharge-loss-one','both-losses-complete',
     'negative-early-no-edges','terminal-clip','zero-early-count-clip','zero-terminal-infeasible',
     'collinear-thresholds','forbidden-crossing')
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
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(1650,1650))
    signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGPROF,expired)
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out).resolve();rows=[];failures=[];cache={};manifest={};cases=None
    def funded(cpu,wall):
        u=usage()
        if not(u['self_cpu_s']+cpu+150<1650 and u['inclusive_cpu_s']+cpu+150<1700
               and time.monotonic()-started+wall+180<2200):
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
            after=usage();elapsed=time.monotonic()-anchor
            need(after['inclusive_cpu_s']-before['inclusive_cpu_s']<=cpu and elapsed<=wall,
                 'Complete stage exceeded its funded allowance')
            need(after['peak_rss_bytes']<=1024**3,'Observed memory allowance exceeded')
            row.update(status='DELIVERED',elapsed_s=elapsed,resources=after,
                       summary=value.get('summary',dict(status=value.get('status'))))
        except BaseException as exc:
            row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc));raise
        finally:
            stopclocks();row['complete_elapsed_s']=time.monotonic()-anchor
            write(out/(name+'.status.json'),row)
        return value
    try:
        funded(50,60);admission_start=started
        # process usage includes interpreter startup; preflight has no unpaid
        # import/read preparation before its inclusive50CPU allowance.
        clocks(max(0.001,50-usage()['inclusive_cpu_s']),max(0.001,60-(time.monotonic()-started)))
        try:
            need(not sys.flags.optimize,'Assertions required')
            control_raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(control_raw)
            need(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision
                 and re.fullmatch('[0-9a-f]{40}',args.source_revision) is not None,'No frozen source authority')
            need(control.get('run_id')=='attempt01' and out==(HERE/'attempt01').resolve()
                 and tuple(control.get('assigned',()))==ASSIGNED,'Fixed namespace/denominator mismatch')
            need([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_self_cpu_s','worker_inclusive_cpu_s','worker_wall_s')]
                 ==[1800,2400,1650,1700,2200],'Worker resource declaration mismatch')
            need(control.get('native_calls')==0 and control.get('observed_rss_bytes')==1024**3
                 and control.get('stage_limits')==dict(admission=[50,60],Q0=[40,60],case=[140,180],final_reserve=[150,180])
                 and control.get('active_systems_per_enumeration')==2000000
                 and tuple(control.get('source_files',()))==FILES,'Limits/source closure mismatch')
            manifest['LAUNCH.json']=dict(bytes=len(control_raw),sha256=hashlib.sha256(control_raw).hexdigest(),binding='separate frozen control')
            for name in FILES:
                raw=(HERE/name).read_bytes()
                frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',args.source_revision+':'+REL+name],cwd=ROOT,timeout=2)
                need(raw==frozen,'Frozen source/input differs: '+name)
                cache[name]=raw;manifest[name]=dict(revision=args.source_revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            cases=json.loads(cache['CASES.json']);need(tuple(c['id'] for c in cases)==IDS,'Fixed ten-case suite changed')
            reference=load('lossy_raw_reference',cache['reference.py']);candidate=load('lossy_formula',cache['candidate.py'])
            qualification=load('lossy_compare',cache['qualification.py'])
            write(out/'admission.json',dict(status='ADMITTED_SOURCE',files=manifest,case_ids=list(IDS),native_calls=0))
            need(usage()['inclusive_cpu_s']<=50
                 and time.monotonic()-admission_start<=60,'Admission exceeded complete allowance')
        finally:stopclocks()
        stage('Q0',40,60,lambda:qualification.controls(reference,candidate))
        for spec in cases:
            try:
                def action(spec=spec):
                    physical=reference.enumerate_physical(spec);analytic=candidate.derive(spec)
                    comparison=qualification.compare(reference,physical,analytic)
                    return dict(status='MATCHED',case=spec,reference=physical,candidate=analytic,comparison=comparison,
                        summary=dict(status=comparison['status'],assignments=comparison['assignment_count'],
                                     cardinalities=comparison['cardinality_count'],
                                     active_systems=physical['active_systems_considered'],native_calls=0))
                stage(spec['id'],140,180,action)
            except FundingStop:raise
            except Exception as exc:
                failures.append(dict(id=spec['id'],reason=type(exc).__name__+': '+str(exc)))
                # A failed literal is retained; other prospectively assigned cases
                # receive one fresh stage if their full allowance remains funded.
    except BaseException as exc:failures.append(dict(id='package',reason=type(exc).__name__+': '+str(exc)))
    finally:stopclocks()
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='Earlier qualification/admission/funding failure'))
    u=usage();elapsed=time.monotonic()-started
    accepted=u['self_cpu_s']<1650 and u['inclusive_cpu_s']<1700 and elapsed<2200 and u['peak_rss_bytes']<=1024**3
    status='COMPLETED' if accepted and not failures and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    report=dict(status=status,assigned=list(ASSIGNED),rows=rows,failures=failures,resource_pass=accepted,
        resources=u,elapsed_s=elapsed,native_calls=0,
        scientific_scope='Ten exact implementation literals; continuum theorem rests on proof, not these cases')
    write(out/'results.json',report);write(out/'worker_receipt.json',dict(report,rows=None,resources=usage(),elapsed_s=time.monotonic()-started))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
