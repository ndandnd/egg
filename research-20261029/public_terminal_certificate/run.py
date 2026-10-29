"""One bounded stdlib worker; no retry or numerical finalizer."""
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

def main():
    started=time.monotonic()
    def expired(signum,frame): raise TimeoutError('Owner cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(87)
    resource.setrlimit(resource.RLIMIT_CPU,(5,50))
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);args=p.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if control['status']!='FROZEN' or args.run_id!='cycle01' or control['run_id']!=args.run_id or not re.fullmatch('[0-9a-f]{40}',control['source_revision']):
        raise ValueError('No frozen launch authority')
    if (control['package_cpu_s'],control['package_wall_s'])!=(50,90): raise ValueError('Funding mismatch')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True,timeout=2).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False)
    child=None;failure=None;result=None
    command=[sys.executable,'-I','-S','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=60)
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL)
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired: failure+='; UNRESOLVED_CHILD'
    try:
        if (out/'results.json').exists():
            result=json.loads((out/'results.json').read_text())
            if (not isinstance(result,dict) or result.get('status') not in ('PASS','FAILED')
                or not isinstance(result.get('rows'),list)
                or any(not isinstance(r,dict) or not isinstance(r.get('status'),str) for r in result['rows'])
                or sorted(r['id'] for r in result['rows'])!=['literal','public']):
                raise ValueError('Incomplete result ledger')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        failure=(failure or '')+'; result read: '+str(exc);result=None
    ledger=[dict(id=r['id'],status=r['status']) for r in result['rows']] if result else [dict(id=n,status='UNKNOWN_UNREPORTED') for n in ('literal','public')]
    own,waited=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+waited.ru_utime+waited.ru_stime
    elapsed=time.monotonic()-started
    rss=max(own.ru_maxrss,waited.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(child_pid=child.pid if child else None,child_exit=child.returncode if child else None,
        reaped=child is not None and child.returncode is not None,failure=failure,ledger=ledger,
        result_status=result['status'] if result else 'MISSING',cpu_s=cpu,elapsed_s=elapsed,peak_rss_bytes=rss,
        resource_pass=cpu<50 and elapsed<90 and rss<=5*1024**3,
        accounting='self plus waited children; worker overlaps; prepublication snapshot')
    with (out/'owner_receipt.json').open('x') as f: json.dump(receipt,f,indent=2)
    signal.alarm(0)
    print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass'] and result and result['status']=='PASS') else 1

if __name__=='__main__': raise SystemExit(main())
