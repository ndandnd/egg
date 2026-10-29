"""Minimal serial bounded owner; consumes only this new experiment's sources."""
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    started = time.monotonic()
    # Reserve three seconds for owned cleanup. This covers work after Python
    # imports; the external meter also observes interpreter startup/shutdown.
    def expired(signum, frame):
        raise TimeoutError('Owner 27-second observation/cleanup boundary')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(27)
    resource.setrlimit(resource.RLIMIT_CPU,(2,20))
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    control = json.loads((HERE/'LAUNCH.json').read_text())
    if (control['status'] != 'FROZEN' or control['run_id'] != args.run_id or
            not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', args.run_id) or
            not re.fullmatch(r'[0-9a-f]{40}', control['source_revision'])):
        raise ValueError('No exact frozen launch authority')
    if (control['package_cpu_s'],control['package_wall_s'],control['worker_cpu_s'],
        control['worker_wall_s']) != (20,30,15,20):
        raise ValueError('Resource control mismatch')
    branch = subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,
                                     text=True,timeout=.5).strip()
    if branch != 'codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out = HERE/args.run_id
    out.mkdir(exist_ok=False)
    child = None
    failure = None
    command = [sys.executable,'-I','-S','-B',str(HERE/'verify.py'),'--out',str(out),
               '--source-revision',control['source_revision']]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    with (out/'stdout.txt').open('x') as stdout, (out/'stderr.txt').open('x') as stderr:
        anchor = time.monotonic()
        try:
            # The inherited hard ceiling permits the child's 10-second self
            # cap. Parent retains its own 2-second soft CPU ceiling.
            child = subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,
                                     start_new_session=True)
            child.wait(timeout=min(20,27-(anchor-started)))
        except BaseException as exc:
            failure = type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL)
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    failure += '; UNRESOLVED_CHILD'
    signal.alarm(0)
    own, waited = resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    total_cpu = own.ru_utime+own.ru_stime+waited.ru_utime+waited.ru_stime
    elapsed = time.monotonic()-started
    result = None
    if child is not None and child.returncode is not None and (out/'results.json').exists():
        result = json.loads((out/'results.json').read_text())
    receipt = dict(source_revision=control['source_revision'],run_id=args.run_id,
       command=command,child_pid=child.pid if child else None,
       child_exit=child.returncode if child else None,
       reaped=child is not None and child.returncode is not None,
       failure=failure,result_status=result['status'] if result else 'MISSING',
       elapsed_s=time.monotonic()-started,
       self_cpu_s=own.ru_utime+own.ru_stime,
       waited_children_cpu_s=waited.ru_utime+waited.ru_stime,
       inclusive_cpu_observed_s=total_cpu,
       resource_pass=total_cpu<20 and elapsed<30,
       no_doublecount='waited children and worker are inside owner meter',
       scope='prepublication receipt; full external meter is authoritative')
    with (out/'owner_receipt.json').open('x') as f:
        json.dump(receipt,f,indent=2)
        f.write('\n')
    print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure
                 and receipt['resource_pass'] and receipt['result_status']=='PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
