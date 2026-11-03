"""One bounded stdlib owner; ordinary construction failure is a retained result."""
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
NEW_IDS = ('MIQP_new','PRICE_MIP_new')
PAIR_IDS = ('protected__MIQP_new','protected__PRICE_MIP_new','MIQP_new__PRICE_MIP_new')


def main():
    started = time.monotonic()
    def expired(signum,frame):
        raise TimeoutError('Owner177-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(177)
    resource.setrlimit(resource.RLIMIT_CPU,(10,120))
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    args = parser.parse_args()
    control = json.loads((HERE/'LAUNCH.json').read_text())
    if (control['status'] != 'FROZEN' or args.run_id != 'cycle01'
            or control['run_id'] != args.run_id
            or not re.fullmatch('[0-9a-f]{40}',control['source_revision'])):
        raise ValueError('No exact frozen launch authority')
    if (control['package_cpu_s'],control['package_wall_s'],control['worker_cpu_s'],
            control['worker_wall_s']) != (120,180,100,150):
        raise ValueError('Resource control mismatch')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True,timeout=2).strip() != 'codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out = HERE/args.run_id
    out.mkdir(exist_ok=False)
    child,failure,result = None,None,None
    command = [sys.executable,'-I','-S','-B',str(HERE/'worker.py'),
               '--out',str(out),'--source-revision',control['source_revision']]
    env = dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
               VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        anchor = time.monotonic()
        try:
            child = subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,
                                     start_new_session=True)
            child.wait(timeout=min(150,177-(anchor-started)))
        except BaseException as exc:
            failure = type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL)
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    failure += '; UNRESOLVED_CHILD'
    try:
        if (out/'results.json').exists():
            result = json.loads((out/'results.json').read_text())
            if (result.get('status') not in ('PASS','COMPLETED_WITH_FAILURES','FATAL')
                    or result.get('assigned_constructions') != 2 or result.get('assigned_pairs') != 3
                    or tuple(row['id'] for row in result['candidate_rows']) != NEW_IDS
                    or tuple(row['id'] for row in result['pair_rows']) != PAIR_IDS):
                raise ValueError('Incomplete or changed outcome denominator')
            candidate_statuses = {'ADMITTED','MISSING_RAW_CANDIDATE','CONSTRUCTION_FAILED',
                                  'STRICT_REPLAY_FAILED','FATAL','UNATTEMPTED'}
            pair_statuses = {'ADMITTED_HULL_UPPER','MISSING_COMPONENT','FATAL','UNATTEMPTED'}
            if (any(row.get('status') not in candidate_statuses for row in result['candidate_rows'])
                    or any(row.get('status') not in pair_statuses for row in result['pair_rows'])
                    or any(type(result.get(key)) is not bool for key in
                           ('resource_pass','administrative_complete','scientific_all_delivered'))):
                raise ValueError('Malformed outcome status or closure flags')
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        failure = (failure or '')+'; result read: '+str(exc)
        result = None
    ledger = ([dict(id=r['id'],status=r['status']) for r in result['candidate_rows']+result['pair_rows']]
              if result else [dict(id=name,status='UNKNOWN_UNREPORTED') for name in NEW_IDS+PAIR_IDS])
    own,children = resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
    elapsed = time.monotonic()-started
    rss = max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform == 'darwin' else 1024)
    receipt = dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,ledger=ledger,result_status=result['status'] if result else 'MISSING',
        scientific_all_delivered=result.get('scientific_all_delivered',False) if result else False,
        administrative_complete=result.get('administrative_complete',False) if result else False,
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu < 120 and elapsed < 180 and rss <= 5*1024**3,
        accounting='Owner plus waited children; worker/source checks overlap; external meter authoritative',
        interpretation='Exit0 denotes administrative closure, not success of every construction')
    with (out/'owner_receipt.json').open('x') as stream:
        json.dump(receipt,stream,indent=2)
        stream.write('\n')
    signal.alarm(0)
    print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit'] == 0 and not failure
                 and receipt['resource_pass'] and receipt['administrative_complete']
                 and result and result['resource_pass']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
