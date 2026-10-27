"""One bounded metadata transfer binding; no project/backend imports or banks."""
import time
START=time.monotonic()
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading
ROOT=Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE=ROOT/'research-20261027/conventional_recovery_continuation'
OLD=ROOT/'research-20261027/conventional_recovery_pilot'
SOURCE='234668a879f31c3a49254adf6e313f8fbdfaa1a6'

def stop(signum,frame): raise TimeoutError('Binding resource stop')
def save(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
    c=json.loads((HERE/'BINDING_LAUNCH.json').read_text())
    if (c.get('mode')!='FROZEN' or c.get('review_disposition')!='PASS' or not c.get('command')
        or c.get('budgets')!={'cpu_s':5,'wall_s':10} or c.get('master_path')!=str(OLD/'attempt01/receipt.json')
        or Path.cwd()!=ROOT or Path(__file__).resolve()!=HERE/'bind_reuse.py'):
        raise SystemExit('DRAFT/PENDING denies metadata consumption')
    resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    for s in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGXCPU):signal.signal(s,stop)
    signal.setitimer(signal.ITIMER_REAL,max(.001,10-(time.monotonic()-START)))
    folder=HERE/'binding01';folder.mkdir(exist_ok=False)
    report=dict(receipt_complete=False,passed=False,failures=[],project_imports=False,raw_bank_reads=0,native_calls=0)
    save(folder/'receipt.json',dict(receipt_complete=False,passed=False))
    try:
        path=OLD/'attempt01/receipt.json';before=path.stat()
        if path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>8*1024**2:
            raise ValueError('Literal bounded compact prior master required')
        raw=path.read_bytes();after=path.stat()
        if len(raw)!=before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('Prior master changed')
        digest=hashlib.sha256(raw).hexdigest();master=json.loads(raw)
        if (master.get('receipt_complete') is not True or master.get('passed') is not False
            or master.get('accounting_complete') is not True or master.get('unresolved_cpu_reserve_s')!=0
            or master.get('source_revision')!=SOURCE or master.get('stop_signal') is not None):
            raise ValueError('Prior closed master/source differs')
        rows=[s[k] for s in master['sequences'] for k in ('F','N','D','UN','UD')]
        attempted=[r for r in rows if r.get('attempted')]
        if len(rows)!=40 or [r['task_id'] for r in attempted]!=[f'B62001-N12-{p}' for p in ('F','N','D','UN')] or any(not r.get('reaped') for r in attempted):
            raise ValueError('Original attempted/reaped denominator differs')
        contract=dict(master_path=str(path),expected_master_sha256=digest,source_revision=SOURCE,control_revision='c7c69a75',rows={})
        for phase in ('F','N','D'):
            row=next(r for r in attempted if r['phase']==phase);w=row['worker'];task=f'B62001-N12-{phase}'
            if (row['task_id']!=task or row.get('folder')!=str(OLD/'attempt01'/task)
                or row.get('returncode')!=0 or not row.get('administrative_packet_accepted')
                or not row.get('physical_endpoint_accepted') or not row.get('strict_delivery') or not row.get('bank_qualified')
                or row.get('source_revision')!=SOURCE or w.get('source_revision')!=SOURCE
                or any(row.get(k) or w.get(k) for k in ('fatal_contract','identity_failure','config_failure','resource_violation'))
                or w.get('receipt_complete') is not True or w.get('stop_signal') is not None):
                raise ValueError('Reusable producer not source-bound/qualified')
            dep=dict(folder=row['folder'],spec_sha256=row['spec_sha256'],receipt_sha256=row['worker_receipt_sha256'],selected_sha256=w['selected_sha256'],bank_sha256=w['bank_sha256'],strict_delivery=True,physical_valid=True,bank_qualified=True)
            if any(not isinstance(dep[k],str) or len(dep[k])!=64 or any(x not in '0123456789abcdef' for x in dep[k]) for k in ('spec_sha256','receipt_sha256','selected_sha256','bank_sha256')):
                raise ValueError('Invalid producer pin')
            contract['rows'][task]=dep
        failed=attempted[-1]
        if failed.get('returncode')!=2 or not failed.get('fatal_contract'):
            raise ValueError('Original failed UN state must remain recorded')
        report.update(passed=True,master_sha256=digest,consumed_bytes=len(raw),reused_task_ids=list(contract['rows']),prior_failed_task_id=failed['task_id'])
        save(HERE/'REUSE_BINDINGS.json',contract)
    except BaseException as exc:report['failures'].append(dict(type=type(exc).__name__,message=str(exc)))
    finally:
        u=resource.getrusage(resource.RUSAGE_SELF)
        report.update(receipt_complete=True,cpu_prepublication_s=u.ru_utime+u.ru_stime,elapsed_prepublication_s=time.monotonic()-START,peak_rss_bytes=u.ru_maxrss if sys.platform=='darwin' else u.ru_maxrss*1024,python_threads=threading.active_count(),children_cpu_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime)
        save(folder/'receipt.final.tmp',report);os.replace(folder/'receipt.final.tmp',folder/'receipt.json')
        print(json.dumps(report),flush=True);signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
