"""Bounded single owner; prospective controls do not authorize execution."""
import argparse
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
IDS=('lossless-full','charge-loss-full','export-loss-full','both-loss-sparse',
     'terminal-boundary','zero-early-full','zero-terminal-empty','common-transition-full')
ASSIGNED=('Q0',)+IDS
DEADLINE=datetime(2026,10,29,18,10,45,tzinfo=timezone.utc)

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(25,300))
    def expired(signum,frame):raise TimeoutError('Owner597-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.signal(signal.SIGXCPU,expired);signal.alarm(597)
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or control.get('run_id')!='attempt01' or args.run_id!='attempt01'
        or control.get('execution_authorized') is not True
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No frozen launch authority')
    if ([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_self_cpu_s','worker_inclusive_cpu_s','worker_wall_s')]
        !=[300,600,270,275,540] or tuple(control.get('assigned',()))!=ASSIGNED
        or control.get('native_calls')!=0 or control.get('native_threads')!=1
        or control.get('observed_rss_bytes')!=1024**3
        or control.get('hard_deadline_utc')!='2026-10-29T18:10:45Z'):
        raise ValueError('Resource/denominator declaration mismatch')
    expected=[sys.executable,'-I','-S','-B',str(HERE/'run.py'),'--run-id','attempt01']
    if control.get('command')!=expected or HERE.name!='full_lossy_polygon_qualification':raise ValueError('Wrong command/namespace')
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize):raise ValueError('Wrong interpreter flags')
    if any(os.environ.get(k)!='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')):
        raise ValueError('Thread environment must be fixed to one')
    if (DEADLINE-datetime.now(timezone.utc)).total_seconds()<600:raise ValueError('Full package plus cleanup unavailable before human deadline')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,timeout=2,text=True).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False);child=None;failure=None;result=None
    command=[sys.executable,'-I','-S','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(540,597-(time.monotonic()-started),(DEADLINE-datetime.now(timezone.utc)).total_seconds()-3))
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:failure+='; UNRESOLVED_CHILD'
    try:
        result=json.loads((out/'results.json').read_text())
        if (not isinstance(result,dict) or tuple(result.get('assigned',()))!=ASSIGNED
            or tuple(r['id'] for r in result['rows'])!=ASSIGNED or result.get('status') not in ('COMPLETED','FAILED')
            or type(result.get('resource_pass')) is not bool
            or any(r.get('status') not in ('DELIVERED','FAILED','UNATTEMPTED') for r in result['rows'])
            or (result['status']=='COMPLETED' and (not result['resource_pass'] or any(r['status']!='DELIVERED' for r in result['rows'])))):
            raise ValueError('Malformed fixed ledger/status/resource closure')
        # Complete administrative read of all published stage packets is paid
        # inside the owner's still-active wall/CPU clock; no scientific replay.
        for row in result['rows']:
            if row['status']=='UNATTEMPTED':continue
            saved=json.loads((out/(row['id']+'.status.json')).read_text())
            if saved.get('id')!=row['id'] or saved.get('status')!=row['status']:
                raise ValueError('Status packet disagrees with master')
            packet=out/(row['id']+'.json.gz')
            if packet.exists():
                with gzip.open(packet,'rb') as stream:raw=stream.read(128*1024**2+1)
                if len(raw)>128*1024**2:raise ValueError('Packet decode bound exceeded')
                value=json.loads(raw)
                if not isinstance(value,dict):raise ValueError('Malformed stage packet')
            elif row['status']=='DELIVERED':raise ValueError('Delivered packet missing')
        if (out/'admission.json').exists():json.loads((out/'admission.json').read_text())
        worker=json.loads((out/'worker_receipt.json').read_text())
        if worker.get('status')!=result['status'] or worker.get('assigned')!=list(ASSIGNED):
            raise ValueError('Worker closure disagrees with master')
    except BaseException as exc:failure=(failure or '')+'; result read: '+str(exc);result=None
    fallback=[]
    if result is None:
        for name in ASSIGNED:
            try:
                row=json.loads((out/(name+'.status.json')).read_text())
                if row.get('id')!=name or row.get('status') not in ('DELIVERED','FAILED'):raise ValueError('Invalid durable status')
                fallback.append(row)
            except (OSError,ValueError,TypeError,AttributeError):
                fallback.append(dict(id=name,status='UNKNOWN_UNREPORTED',reason='No valid durable stage status; no success inferred'))
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime
    rss=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=result['rows'] if result else fallback,
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu<300 and time.monotonic()-started<600 and rss<=1024**3 and datetime.now(timezone.utc)<DEADLINE,
        native_calls=0,accounting='Owner plus waited children overlap worker; full external meter authoritative')
    with (out/'owner_receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
        and result and result['status']=='COMPLETED' and result['resource_pass']) else 1

if __name__=='__main__':raise SystemExit(main())
