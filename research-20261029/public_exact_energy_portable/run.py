"""One bounded local bundle owner; no publication or automatic retry."""
import argparse
from datetime import datetime, timezone
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
ASSIGNED=('PREFLIGHT','BUNDLE','ADAPTER_Q0','PORTABLE_CHECK')

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(50,600))
    def expired(signum,frame):raise TimeoutError('Owner897-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(897)
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or control.get('run_id')!='attempt01' or args.run_id!='attempt01'
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No frozen launch authority')
    if control.get('api_closure_status')!='REVIEWED' or not isinstance(control.get('input_pins'),dict) or not control.get('exact_command') or not isinstance(control.get('global_prefix'),dict):
        raise ValueError('API/input/command/prefix authority remains pending')
    if ([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s')]!=[600,900,550,780]
        or tuple(control.get('assigned',()))!=ASSIGNED or control.get('native_calls')!=0
        or control.get('observed_rss_bytes')!=5*1024**3
        or control.get('distribution_status')!='UNRESOLVED_LOCAL_REVIEW_ONLY'):
        raise ValueError('Resource/denominator/distribution declaration mismatch')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,timeout=2,text=True).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    deadline=datetime(2026,10,29,18,10,45,tzinfo=timezone.utc)
    if (deadline-datetime.now(timezone.utc)).total_seconds()<=900:
        raise ValueError('Full inclusive package cannot close before the human deadline')
    out=HERE/args.run_id;out.mkdir(exist_ok=False);child=None;failure=None;result=None
    command=[sys.executable,'-I','-S','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    environment=os.environ.copy()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):environment[key]='1'
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(780,897-(time.monotonic()-started)))
            if child.returncode!=0:
                # Best-effort cleanup of any unresolved exported CLI descendant
                # even when its direct worker has already exited.
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
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
            or any(r.get('status') not in ('DELIVERED','FAILED','LATE','UNATTEMPTED') for r in result['rows'])
            or (result['status']=='COMPLETED' and (not result['resource_pass'] or any(r['status']!='DELIVERED' for r in result['rows'])))):
            raise ValueError('Malformed terminal ledger/status/resource')
    except (OSError,KeyError,TypeError,ValueError,AttributeError) as exc:failure=(failure or '')+'; result read: '+str(exc);result=None
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime
    rss=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=result['rows'] if result else [dict(id=n,status='UNKNOWN_UNREPORTED') for n in ASSIGNED],
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu<600 and time.monotonic()-started<900 and rss<=5*1024**3,
        distribution_status='UNRESOLVED_LOCAL_REVIEW_ONLY',external_replication=False,native_calls=0,
        accounting='Owner plus waited children overlap worker; external meter includes startup/shutdown')
    with (out/'owner_receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
        and result and result['status']=='COMPLETED' and result['resource_pass']) else 1

if __name__=='__main__':raise SystemExit(main())
