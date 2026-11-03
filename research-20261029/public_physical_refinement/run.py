"""One bounded physical-refinement owner with complete paid closure and no retry."""
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
ASSIGNED=('PREFLIGHT','Q0','PUBLIC_REFINEMENT','INDEPENDENT_REFINEMENT_CHECK')


def main():
    started=time.monotonic()
    def expired(signum,frame):raise TimeoutError('Owner1797-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(1797)
    resource.setrlimit(resource.RLIMIT_CPU,(100,1200))
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or control.get('run_id')!=args.run_id or args.run_id!='attempt01'
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No frozen launch authority')
    if tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))!=(1200,1800,1100,1500):
        raise ValueError('Funding mismatch')
    if tuple(control.get('assigned',()))!=ASSIGNED or control.get('epsilon')!='1/10000':raise ValueError('Objective/denominator changed')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True,timeout=2).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False)
    child,failure,result=None,None,None
    command=[sys.executable,'-I','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(1500,1797-(time.monotonic()-started)))
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
            if (not isinstance(result,dict) or tuple(result.get('assigned',()))!=ASSIGNED
                or tuple(r['id'] for r in result['rows'])!=ASSIGNED or result.get('status') not in ('COMPLETED','FATAL')
                or type(result.get('resource_pass')) is not bool
                or any(r.get('status') not in ('DELIVERED','LATE','FAILED','UNATTEMPTED') for r in result['rows'])
                or (result['status']=='COMPLETED' and (not result['resource_pass'] or any(r['status']!='DELIVERED' for r in result['rows'])))):
                raise ValueError('Malformed/incomplete four-state closure')
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        failure=(failure or '')+'; result read: '+str(exc);result=None
    ledger=([dict(id=r['id'],status=r['status'],summary=r.get('summary')) for r in result['rows']] if result else
            [dict(id=n,status='UNKNOWN_UNREPORTED',reason='No complete readable master; no progress inferred') for n in ASSIGNED])
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
    elapsed=time.monotonic()-started;rss=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=ledger,result_status=result['status'] if result else 'MISSING',
        cpu_s=cpu,elapsed_s=elapsed,peak_rss_bytes=rss,resource_pass=cpu<1200 and elapsed<1800 and rss<=5*1024**3,
        scope='Administrative closure is separate from epsilon success or exact optimum',
        accounting='Owner plus waited children overlap worker; external meter includes complete publication/shutdown')
    write_path=out/'owner_receipt.json'
    with write_path.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
                 and result and result['status']=='COMPLETED' and result['resource_pass']) else 1


if __name__=='__main__':raise SystemExit(main())
