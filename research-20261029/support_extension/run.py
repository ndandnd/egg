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
        raise TimeoutError('Owner 87-second observation/cleanup boundary')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(87)
    resource.setrlimit(resource.RLIMIT_CPU,(5,50))
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    control = json.loads((HERE/'LAUNCH.json').read_text())
    if (control['status'] != 'FROZEN' or control['run_id'] != args.run_id or
            args.run_id != 'cycle01' or
            not re.fullmatch(r'[0-9a-f]{40}', control['source_revision'])):
        raise ValueError('No exact frozen launch authority')
    if (control['package_cpu_s'],control['package_wall_s'],control['worker_cpu_s'],
        control['worker_wall_s']) != (60,90,45,60):
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
            # The inherited hard ceiling permits the worker's 40-second self
            # cap. Parent retains its own 5-second soft CPU ceiling.
            child = subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,
                                     start_new_session=True)
            child.wait(timeout=min(60,87-(anchor-started)))
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
    observed_rss = max(own.ru_maxrss, waited.ru_maxrss)*(1 if sys.platform == 'darwin' else 1024)
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
       peak_process_rss_bytes=observed_rss,
       memory_observation_pass=observed_rss <= 512*1024**2,
       resource_pass=total_cpu<60 and elapsed<90 and observed_rss <= 512*1024**2,
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
