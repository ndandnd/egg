"""Bounded single owner; prospective controls do not authorize execution."""
import argparse
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
IDS=('lossless-one','charge-loss-one','discharge-loss-one','both-losses-complete',
     'negative-early-no-edges','terminal-clip','zero-early-count-clip','zero-terminal-infeasible',
     'collinear-thresholds','forbidden-crossing')
ASSIGNED=('Q0',)+IDS

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(100,1800))
    def expired(signum,frame):raise TimeoutError('Owner2397-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(2397)
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or control.get('run_id')!='attempt01' or args.run_id!='attempt01'
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No frozen launch authority')
    if ([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_self_cpu_s','worker_inclusive_cpu_s','worker_wall_s')]
        !=[1800,2400,1650,1700,2200] or tuple(control.get('assigned',()))!=ASSIGNED
        or control.get('native_calls')!=0 or control.get('observed_rss_bytes')!=1024**3):
        raise ValueError('Resource/denominator declaration mismatch')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,timeout=2,text=True).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False);child=None;failure=None;result=None
    command=[sys.executable,'-I','-S','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(2200,2397-(time.monotonic()-started)))
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
    except (OSError,KeyError,TypeError,ValueError,AttributeError) as exc:failure=(failure or '')+'; result read: '+str(exc);result=None
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime
    rss=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=result['rows'] if result else [dict(id=n,status='UNKNOWN_UNREPORTED') for n in ASSIGNED],
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu<1800 and time.monotonic()-started<2400 and rss<=1024**3,
        native_calls=0,accounting='Owner plus waited children overlap worker; full external meter authoritative')
    with (out/'owner_receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
        and result and result['status']=='COMPLETED' and result['resource_pass']) else 1

if __name__=='__main__':raise SystemExit(main())
