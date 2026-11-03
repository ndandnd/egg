"""One bounded stdlib owner for rational recovery; no native retry or fallback."""
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
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ASSIGNED=('Q0','PUBLIC_PRIMAL','PUBLIC_DUAL')


def main():
    started=time.monotonic()
    def expired(signum,frame):raise TimeoutError('Owner237-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(237)
    resource.setrlimit(resource.RLIMIT_CPU,(15,180))
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or control.get('run_id')!=args.run_id or args.run_id!='attempt01'
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No exact frozen authority')
    if tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))!=(180,240,150,180):
        raise ValueError('Resource control mismatch')
    if tuple(control.get('assigned',()))!=ASSIGNED:raise ValueError('Assigned-state denominator mismatch')
    if (control.get('literal_cases'),control.get('negative_controls'))!=(10,8):
        raise ValueError('Qualification denominator mismatch')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True,timeout=2).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False)
    child,failure,result=None,None,None
    command=[sys.executable,'-I','-S','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        anchor=time.monotonic()
        try:
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(180,237-(anchor-started)))
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL)
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:failure+='; UNRESOLVED_CHILD'
    try:
        if child is not None and child.returncode is not None and (out/'results.json').exists():
            result=json.loads((out/'results.json').read_text())
            if (tuple(result.get('assigned',()))!=ASSIGNED or tuple(r['id'] for r in result['rows'])!=ASSIGNED
                or result['status'] not in ('COMPLETED','FATAL')):raise ValueError('Incomplete or changed assigned ledger')
            if (any(r.get('status') not in ('DELIVERED','FAILED','UNATTEMPTED') for r in result['rows'])
                or type(result.get('resource_pass')) is not bool):
                raise ValueError('Malformed terminal outcome or resource flag')
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        failure=(failure or '')+'; result read: '+str(exc);result=None
    ledger=[dict(id=r['id'],status=r['status'],primal_status=r.get('primal_status'),dual_status=r.get('dual_status'))
            for r in result['rows']] if result else [dict(id=n,status='UNKNOWN_UNREPORTED') for n in ASSIGNED]
    own,child_usage=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+child_usage.ru_utime+child_usage.ru_stime
    elapsed=time.monotonic()-started;rss=max(own.ru_maxrss,child_usage.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=ledger,result_status=result['status'] if result else 'MISSING',
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu<180 and elapsed<240 and rss<=5*1024**3,
        scope='Exit0 denotes administrative completion, not primal/dual/global-support success',
        accounting='Owner plus waited children; worker/source children overlap; external POSIX meter authoritative')
    with (out/'owner_receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
                 and result and result['resource_pass'] and result['status']=='COMPLETED') else 1


if __name__=='__main__':raise SystemExit(main())
