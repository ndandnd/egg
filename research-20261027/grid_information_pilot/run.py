"""Stdlib-only, single-child owner for the prospectively frozen information study."""
import time
START = time.monotonic()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PYTHON = ROOT/'.venv-local/bin/python'
OUTPUT = HERE/'attempt01'
SOURCE_RECEIPT = OUTPUT/'source_receipt.json'
WORKER_RECEIPT = OUTPUT/'worker_receipt.json'
BUDGETS = dict(total_cpu_s=5400,total_wall_s=7200,child_cpu_s=5340,child_wall_s=7000,
    closure_wall_s=200,cleanup_s=3,owner_cpu_reserve_s=60)
ENVIRONMENT = {name:'1' for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
    'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS')}
ENVIRONMENT['PYTHONHASHSEED'] = '17'
CHILD = None
SPAWNING = False
STOPPED = None


class ContractError(ValueError):
    pass


def cpu(who=resource.RUSAGE_SELF):
    usage = resource.getrusage(who)
    return usage.ru_utime+usage.ru_stime


def observed_cpu():
    # Waited child usage is cumulative; worker-reported CPU is never added.
    return cpu()+cpu(resource.RUSAGE_CHILDREN)


def rss():
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))


def full_hex(value):
    return isinstance(value,str) and len(value)==40 and all(c in '0123456789abcdef' for c in value)


def read_once(path,cap):
    path = Path(path)
    before = path.stat()
    if path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>cap:
        raise ContractError('Bounded canonical regular file required: '+str(path))
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    if (len(raw)!=before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)
            !=(after.st_ino,after.st_size,after.st_mtime_ns)):
        raise ContractError('Consumed file changed during its single read: '+str(path))
    return raw


def save(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path,value):
    temporary = path.with_name(path.name+'.final.tmp')
    save(temporary,value)
    os.replace(temporary,path)


def check():
    if STOPPED is not None:
        raise TimeoutError('Latched owner stop '+str(STOPPED))
    if observed_cpu()>=BUDGETS['total_cpu_s'] or time.monotonic()-START>=BUDGETS['total_wall_s']:
        raise TimeoutError('All-inclusive owner self plus waited-child CPU/wall exhausted')


def stop(signum,frame):
    global STOPPED
    STOPPED = STOPPED or signum
    # Finish exact PID registration before raising into owned-child cleanup.
    if not SPAWNING:
        raise TimeoutError('Owner signal '+str(signum))


def git_bytes(arguments,cap=4*1024**2):
    check()
    remaining = START+BUDGETS['total_wall_s']-time.monotonic()
    completed = subprocess.run(['git','-C',str(ROOT),*arguments],stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=max(.001,min(20.,remaining)),check=False)
    check()
    if completed.returncode!=0 or len(completed.stdout)>cap or len(completed.stderr)>65536:
        raise ContractError('Read-only git source inspection failed: '+' '.join(arguments))
    return completed.stdout


def source_paths(launch):
    files = launch.get('source_files')
    if not isinstance(files,list) or not files or len(files)>128 or len(set(files))!=len(files):
        raise ContractError('Frozen explicit bounded unique source_files list required')
    paths = []
    for item in files:
        if (not isinstance(item,str) or not item or item.startswith('/') or '\\' in item
                or any(part in ('','.','..') for part in item.split('/'))):
            raise ContractError('Source authority must be a literal ROOT-relative path without traversal')
        path = ROOT/item
        if path.resolve()!=path or not path.is_relative_to(ROOT):
            raise ContractError('Source authority escaped ROOT or used a symlink')
        paths.append(path)
    if not {HERE/'run.py',HERE/'worker.py',HERE/'physics.py'}<=set(paths):
        raise ContractError('Owner, worker and physics must all be listed source authority')
    return paths


def gate():
    launch = json.loads(read_once(HERE/'LAUNCH.json',128*1024))
    command = '/usr/bin/time -p .venv-local/bin/python -I -B research-20261027/grid_information_pilot/run.py'
    if (launch.get('mode')!='FROZEN' or launch.get('review_disposition')!='PASS'
            or launch.get('workdir')!=str(ROOT) or launch.get('command')!=command
            or not full_hex(launch.get('source_revision')) or launch.get('budgets')!=BUDGETS
            or not isinstance(launch.get('branch'),str) or not launch['branch']
            or Path.cwd().resolve()!=ROOT or Path(__file__).resolve()!=HERE/'run.py'):
        raise SystemExit('DRAFT/PENDING: source audit, generation, imports and dispatch denied')
    paths = source_paths(launch)
    branch = git_bytes(['symbolic-ref','--short','HEAD'],1024).decode().strip()
    if branch!=launch['branch']:
        raise SystemExit('Frozen branch differs; source audit and dispatch denied')
    revision = git_bytes(['rev-parse','--verify',launch['source_revision']+'^{commit}'],1024).decode().strip()
    if revision!=launch['source_revision']:
        raise SystemExit('Frozen full source commit unavailable')
    return launch,paths,branch


def audit_sources(launch,paths,branch,receipt):
    git_root = Path(git_bytes(['rev-parse','--show-toplevel'],8192).decode().strip()).resolve()
    if not ROOT.is_relative_to(git_root):
        raise ContractError('ROOT must lie inside its discovered Git source repository')
    total = 0
    receipt.update(source_revision=launch['source_revision'],branch=branch,git_root=str(git_root),
        source_sha256={},sources=[],python_executable=sys.executable,
        python_executable_resolved=str(Path(sys.executable).resolve()),python_version=sys.version,
        child_python=str(PYTHON),isolated_mode=bool(sys.flags.isolated),environment=ENVIRONMENT,
        receipt_complete=False,source_admitted=False)
    for path in paths:
        check(); raw = read_once(path,4*1024**2); total += len(raw)
        if total>32*1024**2:
            raise ContractError('Total explicit source inventory exceeds32MiB')
        relative = path.relative_to(git_root).as_posix()
        committed = git_bytes(['show',launch['source_revision']+':'+relative])
        if raw!=committed:
            raise ContractError('Current source buffer differs byte-for-byte from frozen commit: '+relative)
        digest = hashlib.sha256(raw).hexdigest()
        receipt['source_sha256'][str(path)] = digest
        receipt['sources'].append(dict(path=str(path),git_path=relative,bytes=len(raw),sha256=digest,
            committed_bytes_equal=True,current_buffer_hashed_once=True))
    check()
    receipt.update(receipt_complete=True,source_admitted=True,total_current_bytes=total,
        consumed_source_buffers_once=True,project_imports=False,fixture_generation=False)
    save(SOURCE_RECEIPT,receipt)


def terminate_owned(child,report):
    if child is None or child.returncode is not None:
        return
    report['owned_process_group_killed'] = True
    try:
        os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=BUDGETS['cleanup_s'])
        report['reaped'] = True
    except subprocess.TimeoutExpired:
        report['reaped'] = False
        report['unresolved_child'] = True


def main():
    global CHILD,SPAWNING
    if OUTPUT.exists():
        raise SystemExit('Fresh attempt01 required; no automatic retry or existing outcome input')
    for key,value in ENVIRONMENT.items():
        os.environ[key] = value
    resource.setrlimit(resource.RLIMIT_CPU,(60,BUDGETS['total_cpu_s']))
    for signum in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM,signal.SIGINT):
        signal.signal(signum,stop)
    signal.setitimer(signal.ITIMER_REAL,BUDGETS['total_wall_s'])
    launch,paths,branch = gate()
    OUTPUT.mkdir(exist_ok=False)
    target = OUTPUT/'owner_receipt.json'
    save(target,dict(receipt_complete=False,source_admitted=False,child_started=False))
    report = dict(receipt_complete=False,passed=False,failures=[],source_admitted=False,
        child_started=False,reaped=False,unresolved_child=False,budgets=BUDGETS,
        source_revision=launch['source_revision'],branch=branch,owned_pid=None,
        process_group_policy='Only this exact newly registered child PID/session is owned',
        worker_receipt=None,worker_receipt_read_complete=False)
    source_receipt = {}
    try:
        audit_sources(launch,paths,branch,source_receipt)
        report['source_admitted'] = True
        # Git source-inspection children are inside the sixty-second owner provision.
        owner_provision = BUDGETS['owner_cpu_reserve_s']-cpu(resource.RUSAGE_CHILDREN)
        owner_self_cap = int(owner_provision)
        if owner_self_cap<1 or cpu()>=owner_self_cap:
            raise TimeoutError('Source admission exhausted the owner CPU provision')
        resource.setrlimit(resource.RLIMIT_CPU,(owner_self_cap,BUDGETS['total_cpu_s']))
        check()
        anchor = time.monotonic()
        report.update(child_anchor=anchor,child_command=[str(PYTHON),'-I','-B',str(HERE/'worker.py'),
            '--anchor',repr(anchor),'--source-receipt',str(SOURCE_RECEIPT)])
        def child_limits():
            resource.setrlimit(resource.RLIMIT_CPU,(BUDGETS['child_cpu_s'],BUDGETS['child_cpu_s']))
        with (OUTPUT/'worker_stdout.txt').open('x') as stdout,(OUTPUT/'worker_stderr.txt').open('x') as stderr:
            SPAWNING = True
            try:
                CHILD = subprocess.Popen(report['child_command'],cwd=ROOT,env=dict(os.environ),
                    stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True,
                    preexec_fn=child_limits)
                report.update(child_started=True,owned_pid=CHILD.pid,process_start_recorded_monotonic=time.monotonic())
                save(OUTPUT/'process_start.json',dict(owned_pid=CHILD.pid,owned_process_group=CHILD.pid,
                    anchor=anchor,command=report['child_command'],workdir=str(ROOT),
                    environment=ENVIRONMENT,source_receipt=str(SOURCE_RECEIPT),
                    recorded_monotonic=report['process_start_recorded_monotonic']))
            finally:
                SPAWNING = False
            check()
            child_end = min(anchor+BUDGETS['child_wall_s'],START+BUDGETS['total_wall_s']-BUDGETS['closure_wall_s'])
            report['child_hard_wall_deadline'] = child_end
            while CHILD.poll() is None:
                check()
                remaining = child_end-time.monotonic()
                if remaining<=0:
                    report['hard_wall_exhausted'] = True
                    terminate_owned(CHILD,report)
                    break
                try:
                    CHILD.wait(timeout=min(1.,remaining))
                except subprocess.TimeoutExpired:
                    pass
            if CHILD.returncode is not None:
                report.update(reaped=True,exitcode=CHILD.returncode)
        check()
    except BaseException as exc:
        report['failures'].append(dict(stage='owner',type=type(exc).__name__,message=str(exc)))
    finally:
        terminate_owned(CHILD,report)
        if CHILD is not None and CHILD.returncode is not None:
            report.update(reaped=True,exitcode=CHILD.returncode)
        if CHILD is not None and report['reaped']:
            tick = time.monotonic()
            try:
                raw = read_once(WORKER_RECEIPT,8*1024**2)
                packet = json.loads(raw)
                if not isinstance(packet,dict):
                    raise ContractError('Compact worker receipt must be an object')
                report.update(worker_receipt=packet,worker_receipt_read_complete=True)
            except BaseException as exc:
                report['failures'].append(dict(stage='worker_receipt',type=type(exc).__name__,message=str(exc)))
            report['worker_receipt_read_elapsed_s'] = time.monotonic()-tick
        own,waited = cpu(),cpu(resource.RUSAGE_CHILDREN)
        elapsed = time.monotonic()-START
        report.update(receipt_complete=True,stop_signal=STOPPED,
            elapsed_s=elapsed,self_cpu_s=own,waited_children_cpu_s=waited,observed_total_cpu_s=own+waited,
            observed_owner_peak_rss_bytes=rss(),worker_usage_not_added_twice=True,
            worker_receipt_read_included_in_elapsed=True,external_process_meter_authoritative=True,
            source_receipt=str(SOURCE_RECEIPT) if report['source_admitted'] else None)
        report['passed'] = bool(report['source_admitted'] and report['child_started'] and report['reaped']
            and not report['unresolved_child'] and report.get('exitcode')==0 and not report['failures']
            and report['worker_receipt_read_complete'] and STOPPED is None
            and own+waited<BUDGETS['total_cpu_s'] and elapsed<BUDGETS['total_wall_s'])
        publish(target,report)
        print(json.dumps(dict(passed=report['passed'],exitcode=report.get('exitcode'),
            owner_receipt=str(target),self_cpu_s=own,waited_children_cpu_s=waited,elapsed_s=elapsed),allow_nan=False),flush=True)
        signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
