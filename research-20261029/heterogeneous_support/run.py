"""Single serial owner; DRAFT until a separate exact LAUNCH.json is frozen."""
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
ASSIGNED = ('crossmatching-gap','crossmatching-boundary','crossmatching-large-fee',
            'zero-thresholds','positive-threshold-assignment-ties','three-per-batch-gap',
            'three-per-batch-boundary','flat-price-responses')


def main():
    started = time.monotonic()
    def expired(signum,frame):
        raise TimeoutError('Owner 87-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(87)
    resource.setrlimit(resource.RLIMIT_CPU,(5,50))
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    args = parser.parse_args()
    control = json.loads((HERE/'LAUNCH.json').read_text())
    if (control['status'] != 'FROZEN' or control['run_id'] != args.run_id
            or args.run_id != 'cycle01'
            or not re.fullmatch(r'[0-9a-f]{40}',control['source_revision'])):
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
    command = [sys.executable,'-I','-S','-B',str(HERE/'verify.py'),
               '--out',str(out),'--source-revision',control['source_revision']]
    env = dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    child,failure = None,None
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        anchor = time.monotonic()
        try:
            child = subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,
                                     stderr=stderr,start_new_session=True)
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
    result = None
    result_read_error = None
    try:
        if child is not None and child.returncode is not None and (out/'results.json').exists():
            result = json.loads((out/'results.json').read_text())
            if (not isinstance(result,dict) or result.get('status') not in ('PASS','FAIL')
                    or result.get('assigned') != 8 or not isinstance(result.get('rows'),list)
                    or any(not isinstance(r,dict) or not isinstance(r.get('spec'),dict)
                           or r.get('status') not in ('PASS','FAIL','UNATTEMPTED') for r in result['rows'])
                    or sorted(r['spec']['id'] for r in result['rows']) != sorted(ASSIGNED)):
                raise ValueError('Malformed or incomplete eight-case master ledger')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        result_read_error = type(exc).__name__+': '+str(exc)
        result = None
    ledger = ([dict(id=r['spec']['id'],status=r['status']) for r in result['rows']]
              if result is not None else [dict(id=name,status='UNKNOWN_UNREPORTED') for name in ASSIGNED])
    own,waited = resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    own_cpu,child_cpu = own.ru_utime+own.ru_stime,waited.ru_utime+waited.ru_stime
    elapsed = time.monotonic()-started
    rss = max(own.ru_maxrss,waited.ru_maxrss)*(1 if sys.platform == 'darwin' else 1024)
    receipt = dict(source_revision=control['source_revision'],run_id=args.run_id,
        command=command,child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,
        reaped=child is not None and child.returncode is not None,failure=failure,
        result_status=result['status'] if result else 'MISSING',
        assigned_cases=8,worker_packet_available=result is not None,
        assigned_state_ledger=ledger,result_read_error=result_read_error,
        reported_attempted=result.get('attempted') if result else None,
        reported_passed=result.get('passed') if result else None,
        missing_packet_semantics='Unknown progress, never infer unattempted after abrupt worker loss',
        self_cpu_s=own_cpu,waited_children_cpu_s=child_cpu,
        inclusive_cpu_observed_s=own_cpu+child_cpu,elapsed_s=time.monotonic()-started,
        peak_process_rss_bytes=rss,
        resource_pass=own_cpu+child_cpu < 60 and elapsed < 90 and rss <= 512*1024**2,
        no_doublecount='Worker and source Git subprocesses are inside the inclusive owner meter',
        scope='Prepublication receipt; full external POSIX meter is authoritative')
    with (out/'owner_receipt.json').open('x') as stream:
        json.dump(receipt,stream,indent=2)
        stream.write('\n')
    print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit'] == 0 and not failure
                 and receipt['resource_pass'] and receipt['result_status'] == 'PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
