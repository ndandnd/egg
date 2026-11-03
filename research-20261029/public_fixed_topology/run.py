"""Existing-pattern serial bounded owner, one fresh worker and no retries."""
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
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(1797)
    resource.setrlimit(resource.RLIMIT_CPU,(30,1200))
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control['status']!='FROZEN' or args.run_id!='attempt01' or control['run_id']!=args.run_id
        or not re.fullmatch('[0-9a-f]{40}',control['source_revision'])): raise ValueError('No frozen launch authority')
    if (control['package_cpu_s'],control['package_wall_s'],control['worker_cpu_s'],control['worker_wall_s'])!=(1200,1800,1100,1600):
        raise ValueError('Funding mismatch')
    inputs=control.get('inputs',[])
    if (len(inputs)!=2 or {item.get('id') for item in inputs}!={'case','topology'}
        or any(not re.fullmatch('[0-9a-f]{40}',item.get('revision',''))
               or ('sha256' in item and not re.fullmatch('[0-9a-f]{64}',item['sha256']))
               or not isinstance(item.get('path'),str) or not item['path']
               or Path(item['path']).is_absolute() or '..' in Path(item['path']).parts for item in inputs)):
        raise ValueError('All input revisions and byte pins must be frozen; DRAFT/PENDING cannot dispatch')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True,timeout=2).strip()
    if branch!='codex/ml-prediction-20261017': raise ValueError('Wrong branch')
    out=HERE/args.run_id
    out.mkdir(exist_ok=False)
    child=None
    failure=None
    command=[sys.executable,'-I','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        anchor=time.monotonic()
        try:
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(1600,1797-(anchor-started)))
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                os.killpg(child.pid,signal.SIGKILL)
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired: failure+='; UNRESOLVED_CHILD'
    signal.alarm(0)
    result=None
    assigned=('Q0','FIXED_QP_RECOVERY','OWN_PRICE_LP','OWN_PRICE_MIP')
    result_read_error=None
    try:
        if child is not None and child.returncode is not None and (out/'results.json').exists():
            result=json.loads((out/'results.json').read_text())
            if (not isinstance(result,dict) or result.get('status') not in ('CLOSED','CLOSED_FAILED')
                or not isinstance(result.get('rows'),list)
                or any(not isinstance(r,dict) or not isinstance(r.get('status'),str) for r in result['rows'])):
                raise ValueError('Malformed master status or assignment records')
            if sorted(r['id'] for r in result['rows'])!=sorted(assigned):
                raise ValueError('Incomplete or duplicate assigned-state ledger')
            if (any(r['status'] not in ('DELIVERED','LATE','FAILED','UNATTEMPTED') for r in result['rows'])
                or type(result.get('resource_pass')) is not bool
                or result.get('assigned')!=4
                or (result['status']=='CLOSED' and
                    (not result['resource_pass'] or any(r['status'] not in ('DELIVERED','UNATTEMPTED') for r in result['rows'])))):
                raise ValueError('Malformed terminal status or resource closure')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        result_read_error=type(exc).__name__+': '+str(exc)
        result=None
    if result is None:
        # Administrative preservation only: no numerical export or recompute.
        begins=set()
        event_read_errors=[]
        if (out/'events.jsonl').exists():
            try:
                for line_number,line in enumerate((out/'events.jsonl').read_text().splitlines(),1):
                    try:
                        row=json.loads(line)
                        if not isinstance(row,dict): raise ValueError('Non-object event')
                        if row.get('event')=='stage_begin': begins.add(row['id'])
                    except (ValueError,KeyError,TypeError): event_read_errors.append(line_number)
            except OSError as exc: event_read_errors.append(str(exc))
        ledger=[]
        for name in assigned:
            state={'id':name,'status':'ATTEMPTED_UNREPORTED' if name in begins else 'UNATTEMPTED',
                   'reason':'worker did not publish a complete readable master report'}
            path=out/(name+'.status.json')
            if path.exists():
                try:
                    packet=json.loads(path.read_text())
                    if packet['id']!=name: raise ValueError('Stage packet identity mismatch')
                    state={'id':name,'status':packet['status'],'evidence':'compact durable stage receipt',
                           'timing_scope':packet.get('stage_clock_scope','UNKNOWN'),
                           'exact_support_claim':False}
                except (OSError,ValueError,KeyError,TypeError) as exc:
                    state.update(status='UNKNOWN_UNREADABLE_PACKET',packet_error=str(exc))
            elif event_read_errors:
                state.update(status='UNKNOWN_EVENT_LEDGER_INCOMPLETE')
            ledger.append(state)
        with (out/'administrative_fallback.json').open('x') as f:
            json.dump(dict(assigned=4,rows=ledger,event_read_errors=event_read_errors,
                           result_read_error=result_read_error,not_a_numerical_readout=True),f,indent=2)
    else:
        ledger=[{'id':r['id'],'status':r['status']} for r in result['rows']]
    own,waited=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+waited.ru_utime+waited.ru_stime
    elapsed=time.monotonic()-started
    rss=max(own.ru_maxrss,waited.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],run_id=args.run_id,command=command,
        child_pid=child.pid if child else None,child_exit=child.returncode if child else None,
        reaped=child is not None and child.returncode is not None,failure=failure,
        result_status=result['status'] if result else 'MISSING',elapsed_s=elapsed,
        assigned_state_ledger=ledger,result_read_error=result_read_error,
        self_cpu_s=own.ru_utime+own.ru_stime,waited_children_cpu_s=waited.ru_utime+waited.ru_stime,
        inclusive_cpu_observed_s=cpu,peak_process_rss_bytes=rss,
        resource_pass=cpu<1200 and elapsed<1800 and rss<=5*1024**3,
        no_doublecount='worker and waited children overlap owner meter',scope='prepublication; final external meter authoritative')
    with (out/'owner_receipt.json').open('x') as f: json.dump(receipt,f,indent=2)
    print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
                 and result is not None and result_read_error is None and result['status']=='CLOSED') else 1

if __name__=='__main__':
    raise SystemExit(main())
