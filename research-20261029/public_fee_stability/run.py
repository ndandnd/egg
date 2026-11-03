"""Bounded owner; DRAFT control denies execution until parent freeze."""
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
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ASSIGNED=('ADMISSION','Q0','PUBLIC_INTERVAL')

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(20,120))
    def expired(signum,frame):raise TimeoutError('Owner177-second cleanup boundary')
    signal.signal(signal.SIGALRM,expired);signal.alarm(177)
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    control=json.loads((HERE/'LAUNCH.json').read_text())
    if (control.get('status')!='FROZEN' or args.run_id!='attempt01' or control.get('run_id')!='attempt01'
        or not re.fullmatch('[0-9a-f]{40}',control.get('source_revision',''))):raise ValueError('No frozen launch authority')
    if [control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s')]!=[120,180,90,150]:
        raise ValueError('Changed resource declaration')
    if tuple(control.get('assigned',()))!=ASSIGNED:raise ValueError('Changed assigned denominator')
    if (control.get('native_calls')!=0 or control.get('observed_rss_bytes')!=512*1024**2
        or control.get('tree_artifact_revision')!='ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9'
        or control.get('mixture_artifact_revision')!='f5ec2aa5770188d173af7297620a5fcea99fef9a'
        or control.get('mixture_authority_revision')!='c5f056b90ca895786c44f96903cdaafff97fce52'):
        raise ValueError('Changed input/native/memory declaration')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,timeout=1,text=True).strip()!='codex/ml-prediction-20261017':
        raise ValueError('Wrong branch')
    out=HERE/args.run_id;out.mkdir(exist_ok=False)
    child=None;failure=None;result=None
    command=[sys.executable,'-I','-S','-B',str(HERE/'worker.py'),'--out',str(out),'--source-revision',control['source_revision']]
    with (out/'stdout.txt').open('x') as stdout,(out/'stderr.txt').open('x') as stderr:
        try:
            child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            child.wait(timeout=min(150,177-(time.monotonic()-started)))
        except BaseException as exc:
            failure=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:failure+='; UNRESOLVED_CHILD'
    try:
        result=json.loads((out/'results.json').read_text())
        if (tuple(result['assigned'])!=ASSIGNED or tuple(r['id'] for r in result['rows'])!=ASSIGNED
            or any(r['status'] not in ('DELIVERED','FAILED','UNATTEMPTED') for r in result['rows'])):
            raise ValueError('Malformed fixed ledger')
        if (result.get('status') not in ('COMPLETED','FAILED') or type(result.get('resource_pass')) is not bool
            or (result['status']=='COMPLETED' and (result['resource_pass'] is not True
                or any(r['status']!='DELIVERED' for r in result['rows'])))):
            raise ValueError('Inconsistent terminal status/resource/delivery')
    except (OSError,ValueError,KeyError,TypeError) as exc:failure=(failure or '')+'; result read: '+str(exc);result=None
    own,kids=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+kids.ru_utime+kids.ru_stime
    rss=max(own.ru_maxrss,kids.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    receipt=dict(source_revision=control['source_revision'],child_pid=child.pid if child else None,
        child_exit=child.returncode if child else None,reaped=child is not None and child.returncode is not None,
        failure=failure,assigned=list(ASSIGNED),ledger=result['rows'] if result else [dict(id=n,status='UNKNOWN_UNREPORTED') for n in ASSIGNED],
        cpu_s=cpu,elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,
        resource_pass=cpu<120 and time.monotonic()-started<180 and rss<=512*1024**2,
        accounting='Owner plus waited children overlap worker observations; external meter authoritative',native_calls=0)
    with (out/'owner_receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    signal.alarm(0);print(json.dumps(receipt))
    return 0 if (receipt['reaped'] and receipt['child_exit']==0 and not failure and receipt['resource_pass']
        and result and result['status']=='COMPLETED' and result['resource_pass']) else 1

if __name__=='__main__':raise SystemExit(main())
