"""One owner for fixed certified-price LP/MIP responses; no retry."""
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
ASSIGNED=('Q0','PRICE_LP','PRICE_MIP')


def main():
    started=time.monotonic()
    def expired(signum,frame):raise TimeoutError('Owner897-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(897)
    resource.setrlimit(resource.RLIMIT_CPU,(30,600))
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or args.run_id!='attempt01' or control.get('run_id')!=args.run_id
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No exact frozen authority')
    if tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))!=(600,900,550,780):
        raise ValueError('Resource control mismatch')
    if tuple(control.get('assigned',()))!=ASSIGNED:raise ValueError('Assigned-state denominator mismatch')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True,timeout=2).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False)
    child,failure,result=None,None,None
    command=[sys.executable,'-I','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        anchor=time.monotonic()
        try:
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(780,897-(anchor-started)))
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:failure+='; UNRESOLVED_CHILD'
    try:
        if child is not None and child.returncode is not None and (out/'results.json').exists():
            result=json.loads((out/'results.json').read_text())
            if (tuple(result.get('assigned',()))!=ASSIGNED or tuple(r['id'] for r in result['rows'])!=ASSIGNED
                or result['status'] not in ('COMPLETED','FATAL')):raise ValueError('Incomplete outcome ledger')
            if (any(r.get('status') not in ('DELIVERED','LATE','FAILED','UNATTEMPTED') for r in result['rows'])
                or type(result.get('resource_pass')) is not bool
                or type(result.get('all_assigned_timely')) is not bool
                or result['all_assigned_timely'] != all(r['status']=='DELIVERED' for r in result['rows'])):
                raise ValueError('Malformed outcome status, resource flag or timely ledger')
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        failure=(failure or '')+'; result read: '+str(exc);result=None
    ledger=[dict(id=r['id'],status=r['status'],summary=r.get('summary')) for r in result['rows']] if result else [dict(id=n,status='UNKNOWN_UNREPORTED') for n in ASSIGNED]
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
    elapsed=time.monotonic()-started;rss=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=ledger,result_status=result['status'] if result else 'MISSING',
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu<600 and elapsed<900 and rss<=5*1024**3,
        scope='Administrative completion distinct from exact support/response delivery',
        accounting='Owner plus waited children; no duplicate child charge; full external meter authoritative')
    with (out/'owner_receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
        and result and result['resource_pass'] and result['all_assigned_timely'] and result['status']=='COMPLETED') else 1


if __name__=='__main__':raise SystemExit(main())
