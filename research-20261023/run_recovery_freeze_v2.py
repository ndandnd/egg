"""One externally supervised fixture freeze; no native solve and no automatic retry.

Use the checked interpreter. --command-json contains an exact runner freeze argv.
Importing this wrapper creates no fixture and starts no process.
"""
import argparse
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

import run_recovery_runner_checks as checked
import run_admission_capture_budget_check as reviewed

prior = checked.prior
ROOT = checked.ROOT
MINIMUM = 128.4036048752605
THREADS = ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
           'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    prior.write(path,value)
    fd = os.open(path.parent,os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def finite(value, minimum=0.):
    return type(value) in (int,float) and math.isfinite(value) and value>=minimum


def hash_changes(inventory):
    changed = []
    for path, expected in inventory.items():
        try:
            valid = prior.digest(Path(path))==expected
        except OSError:
            valid = False
        if not valid:
            changed.append(path)
    return changed


def retain_failure(failure, secondary_errors, exc, context):
    state = {'primary_failure':failure,'secondary_errors':secondary_errors}
    reviewed.retain_error(state,exc,context)
    return state['primary_failure']


def cleanup_confirmed(termination):
    states = termination.get('group_states',[])
    return bool(termination.get('owned_pgids') and termination.get('group_absent') is True
                and termination.get('reaped') is True and not termination.get('surviving_pgids')
                and type(termination.get('leader_returncode')) is int
                and {row['pgid'] for row in states} == set(termination['owned_pgids'])
                and all(row['state']=='absent' for row in states)
                and not termination.get('cleanup_errors'))


def cleanup_owned(proc, groups, deadline, *, failure=None):
    """Use the reviewed bounded cleanup; unexpected helper failure retains unknowns."""
    known = set(groups)|{proc.pid}
    termination = {'owned_pgids':sorted(known),'surviving_pgids':sorted(known),
        'leader_returncode':proc.returncode,'reaped':proc.returncode is not None,
        'group_absent':False,'cleanup_deadline':deadline,
        'group_states':[{'pgid':pgid,'state':'unknown'} for pgid in sorted(known)],
        'probe_diagnostics':[],'cleanup_errors':[]}
    secondary_errors = []
    try:
        termination = reviewed.cleanup_receipt(proc,known,deadline)
    except BaseException as exc:
        diagnostic = reviewed.q.monitor_diagnostic(exc,context='freeze_cleanup_helper')
        termination['cleanup_errors'].append(diagnostic)
        termination['leader_returncode'] = proc.returncode
        termination['reaped'] = proc.returncode is not None
    errors = termination.get('cleanup_errors',[])
    for diagnostic in errors:
        if failure is None:
            failure = diagnostic
        else:
            secondary_errors.append(diagnostic)
    if not cleanup_confirmed(termination) and not errors:
        failure = retain_failure(failure,secondary_errors,
            RuntimeError('Owned freeze cleanup incomplete or reported errors'),'freeze_cleanup_gate')
    return termination,failure,secondary_errors


def inputs(args):
    """Validate only explicit source-lock inputs; no case generation or backend load."""
    from experiments import recovery_qualification as runner
    checks = Path(args.checks).resolve()
    runner.checked_sources(checks)
    accounting = runner.accounting(args.accounting)
    carried = accounting['charged_cpu_s']
    if not finite(carried, max(MINIMUM,read(checks/'result.json')['cumulative_qualification_charge_s'])):
        raise ValueError('Current cumulative spend/admin/check charges must be carried forward')
    if (carried+runner.OUTER_ALLOCATION>runner.DISPATCH_STOP or
            carried+runner.OUTER_ALLOCATION+runner.SHUTDOWN_RESERVE>runner.CEILING):
        raise ValueError('Insufficient full freeze allocation plus shutdown reserve')
    command = read(args.command_json)
    if (not isinstance(command,list) or any(not isinstance(item,str) for item in command)
            or command[:4] != [sys.executable,'-m','experiments.recovery_qualification','freeze']):
        raise ValueError('Only an explicit same-interpreter checked runner freeze command is allowed')
    parser = argparse.ArgumentParser(add_help=False,allow_abbrev=False)
    for name in ('lock','checks','accounting','reservations','native-library'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--backend',choices=('CBC','GRB'),required=True)
    parser.add_argument('--design')
    parsed = parser.parse_args(command[4:])
    for key in ('lock','checks','accounting','reservations','native_library','design'):
        value = getattr(parsed,key)
        if value is not None and not Path(value).is_absolute():
            raise ValueError('Freeze argv paths must be absolute: '+key)
    for key in ('lock','checks','accounting'):
        if Path(getattr(parsed,key)).resolve()!=Path(getattr(args,key)).resolve():
            raise ValueError('Command/input path mismatch: '+key)
    lockpath = Path(args.lock).resolve()
    if not lockpath.parent.is_dir() or lockpath.exists() or (lockpath.parent/'fixtures').exists():
        raise ValueError('Lock parent must exist with new lock and fixture destinations')
    registry = read(parsed.reservations)
    design = read(parsed.design) if parsed.design else list(runner.DESIGN)
    runner.reservation(design,registry)
    sources = {str(Path(path).resolve()):value for path,value in read(checks/'attempt.json')['source_hashes'].items()}
    if hash_changes(sources):
        raise ValueError('Passing checked source inventory changed')
    paths = [Path(__file__),Path(args.command_json),Path(args.accounting),Path(parsed.reservations),
             checks/'attempt.json',checks/'result.json',checks/'stdout.log',checks/'stderr.log',
             Path(parsed.native_library),Path(args.protocol),
             Path(__file__).with_name('RECOVERY_FIXTURE_FREEZE_PROTOCOL.md'),
             Path(reviewed.__file__),Path(checked.__file__),
             Path(__file__).with_name('run_recovery_freeze.py'),
             Path(__file__).with_name('RECOVERY_FREEZE_V2_IMPLEMENTATION.md')]
    if parsed.design:
        paths.append(Path(parsed.design))
    sources.update({str(path.resolve()):prior.digest(path.resolve()) for path in paths})
    return command,carried,sources


def guarded_worker(folder, parent_pid):
    """Keep the freeze worker owned if its actual supervisor dies mid-generation."""
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGINT})
    folder = Path(folder).resolve()
    subprocess.Popen([sys.executable,'-m','experiments.codex_local_campaign','watch-parent',
                      '--parent-pid',str(parent_pid),'--worker-pid',str(os.getpid()),
                      '--output',str(folder)],preexec_fn=lambda:signal.signal(signal.SIGTERM,signal.SIG_IGN))
    attempt = read(folder/'attempt.json')
    if os.getppid()!=parent_pid or hash_changes(attempt['source_hashes']):
        raise RuntimeError('Parent/source binding lost before freeze')
    result = subprocess.run(attempt['command'],cwd=ROOT,check=False)
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    write(folder/'worker.json',{'returncode':result.returncode,'finished_monotonic':time.monotonic(),
          'cpu_s':time.process_time()+usage.ru_utime+usage.ru_stime})
    return result.returncode


def supervise(args):
    cpu0 = time.process_time()
    children0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    folder = Path(args.attempt_dir).resolve()
    folder.mkdir(parents=True,exist_ok=False)  # Failed/incomplete attempts are never resumed.
    validation0 = time.monotonic()
    try:
        command,carried,sources = inputs(args)
    except BaseException as exc:
        carried,unresolved = MINIMUM,True
        try:
            value = read(args.accounting)['charged_cpu_s']
            if finite(value,MINIMUM):
                carried,unresolved = value,False
        except (OSError,ValueError,KeyError,TypeError):
            pass
        elapsed = time.monotonic()-validation0
        failure = {'type':type(exc).__name__,'message':str(exc)}
        write(folder/'attempt.json',{'phase':'recovery_fixture_freeze','validation_only':True,
              'command_json':str(Path(args.command_json).resolve()),'carried_charge_s':carried,
              'accounting_unresolved':unresolved,'automatic_retry':False})
        supervisor_cpu = time.process_time()-cpu0
        receipt = {'phase':'recovery_fixture_freeze','passed':False,'failure':failure,'secondary_errors':[],
                   'monitor_failure':None,'lock_sha256':None,'source_changes':[],
                   'elapsed_allocation_s':elapsed,'charged_cpu_s':elapsed,'supervisor_cpu_s':supervisor_cpu,
                   'cumulative_qualification_charge_s':carried+elapsed+supervisor_cpu,
                   'sampled_peak_rss_bytes':0,'termination':{'owned_pgids':[],'surviving_pgids':[],
                       'reaped':False,'group_absent':False},
                   'accounting_unresolved':unresolved,'scope':'rejected before worker launch; audited reconciliation required'}
        receipt['attempt_sha256'] = prior.digest(folder/'attempt.json')
        write(folder/'supervisor.json',receipt)
        print(json.dumps(receipt,sort_keys=True,indent=2))
        return 1
    anchor = time.monotonic()
    write(folder/'attempt.json',{'phase':'recovery_fixture_freeze','command':command,
          'parent_monotonic':anchor,'worker_deadline':anchor+30.,'outer_deadline':anchor+32.5,
          'source_hashes':sources,'carried_charge_s':carried,'lock':str(Path(args.lock).resolve()),
          'checks':str(Path(args.checks).resolve()),'rss_limit_bytes':5*1024**3,
          'threads':{key:'1' for key in THREADS},'automatic_retry':False})
    env = {**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
           **{key:'1' for key in THREADS}}
    proc = None
    groups = set()
    peak = sampled_cpu = last_pressure = 0.
    last_sample = pressure_since = None
    exit_observed = None
    failure = monitor_failure = None
    stage = 'preflight_monitor'
    termination = {'owned_pgids':[],'surviving_pgids':[],'reaped':False,'group_absent':False}
    secondary_errors = []
    previous = {}

    def interrupted(signum, frame):
        raise KeyboardInterrupt('Freeze supervisor signal '+str(signum))

    for sig in (signal.SIGTERM,signal.SIGINT):
        previous[sig] = signal.signal(sig,interrupted)
    try:
        with (folder/'stdout.log').open('x') as out,(folder/'stderr.log').open('x') as err:
            try:
                end = time.monotonic()+.24
                if os.getpid() not in checked.snapshot(end):
                    raise RuntimeError('incomplete_process_monitor')
                free = prior.memory_state(end)['free_percent']
                if not finite(free) or free>100:
                    raise RuntimeError('invalid_memory_monitor')
                stage = 'preflight_resource'
                if free<10:
                    raise RuntimeError('low_memory_before_dispatch')
                stage = 'worker_launch'
                proc = subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--guarded-worker',
                    str(folder),'--parent-pid',str(os.getpid())],cwd=ROOT,env=env,
                    stdout=out,stderr=err,start_new_session=True)
                groups.add(proc.pid)
                while proc.poll() is None:
                    now = time.monotonic()
                    if now>=anchor+30.:
                        raise TimeoutError('freeze_worker_deadline')
                    if last_sample is not None and now-last_sample>.25:
                        monitor_failure = {'type':'RuntimeError','message':'resource_monitor_sampling_gap'}
                        raise RuntimeError('resource_monitor_sampling_gap')
                    last_sample = now
                    sample_end = min(now+.20,anchor+30.)
                    try:
                        table = checked.snapshot(sample_end)
                        if os.getpid() not in table:
                            raise RuntimeError('incomplete_process_monitor')
                        rows = checked.owned_rows(proc.pid,groups,table)
                        rss,cpu = sum(row['rss'] for row in rows),sum(row['cpu'] for row in rows)
                        peak,sampled_cpu = max(peak,rss),max(sampled_cpu,cpu)
                        event = {'monotonic':now,'rss_bytes':rss,'cpu_s':cpu,'owned_pgids':sorted(groups)}
                        if now-last_pressure>=1.:
                            memory = prior.memory_state(sample_end)
                            if not finite(memory['free_percent']) or memory['free_percent']>100:
                                raise RuntimeError('invalid_memory_monitor')
                            event.update(memory)
                            last_pressure = now
                            pressure_since = (now if pressure_since is None else pressure_since) if memory['free_percent']<10 else None
                        prior.monitor.append(folder/'resources.jsonl',event)
                    except BaseException as exc:
                        monitor_failure = {'type':type(exc).__name__,'message':str(exc)}
                        raise
                    if rss>5*1024**3:
                        raise RuntimeError('freeze_process_tree_rss_limit')
                    if pressure_since is not None and now-pressure_since>=5.:
                        raise RuntimeError('sustained_memory_pressure')
                    time.sleep(max(0.,.20-(time.monotonic()-now)))
                exit_observed = time.monotonic()
            except BaseException as exc:
                failure = {'type':type(exc).__name__,'message':str(exc)}
                if stage=='preflight_monitor':
                    monitor_failure = failure
            finally:
                for sig in previous:
                    signal.signal(sig,signal.SIG_IGN)
                if proc is not None:
                    groups.add(proc.pid)
                    termination,failure,cleanup_errors = cleanup_owned(
                        proc,groups,anchor+32.5,failure=failure)
                    secondary_errors.extend(cleanup_errors)
    finally:
        for sig in previous:
            signal.signal(sig,signal.SIG_IGN)
    elapsed = time.monotonic()-anchor
    changes = hash_changes(sources)
    try:
        worker = read(folder/'worker.json') if (folder/'worker.json').exists() else {}
        if not isinstance(worker,dict):
            raise ValueError('Malformed freeze worker CPU receipt')
    except (OSError,ValueError,TypeError) as exc:
        worker = {}
        failure = retain_failure(failure,secondary_errors,exc,'worker_receipt')
    try:
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        child_cpu = children.ru_utime+children.ru_stime-children0.ru_utime-children0.ru_stime
    except BaseException as exc:
        child_cpu = None
        failure = retain_failure(failure,secondary_errors,exc,'child_cpu_audit')
    charged = max(elapsed,sampled_cpu,child_cpu if finite(child_cpu) else 0.,
                  worker.get('cpu_s',0.) if finite(worker.get('cpu_s')) else elapsed)
    locksha = None
    try:
        from experiments import recovery_qualification as runner
        lock = read(args.lock)
        runner.verify_lock(lock)
        if lock['carried_charge_s']!=carried:
            raise ValueError('Generated lock changed carried qualification charge')
        locksha = prior.digest(Path(args.lock))
    except BaseException as exc:
        failure = retain_failure(failure,secondary_errors,exc,'lock_validation')
    audit = {'primary_failure':failure,'secondary_errors':secondary_errors}
    output_hashes = reviewed.output_audit(folder,audit)
    failure = audit['primary_failure']
    try:
        attemptsha = prior.digest(folder/'attempt.json')
    except BaseException as exc:
        attemptsha = None
        failure = retain_failure(failure,secondary_errors,exc,'attempt_audit')
    elapsed = time.monotonic()-anchor
    charged = max(charged,elapsed)
    worker_timely = finite(worker.get('finished_monotonic'),anchor) and worker['finished_monotonic']<=anchor+30.
    passed = bool(proc is not None and proc.returncode==0 and worker.get('returncode')==0
                  and worker_timely and exit_observed is not None and exit_observed<=anchor+30.
                  and elapsed<=32.5 and failure is None and monitor_failure is None and not secondary_errors
                  and child_cpu is not None and not changes and cleanup_confirmed(termination))
    supervisor_cpu = time.process_time()-cpu0
    receipt = {'phase':'recovery_fixture_freeze','passed':passed,'failure':failure,
        'secondary_errors':secondary_errors,'monitor_failure':monitor_failure,'lock_sha256':locksha,'source_changes':changes,
        'parent_monotonic':anchor,'elapsed_allocation_s':elapsed,'charged_cpu_s':charged,
        'supervisor_cpu_s':supervisor_cpu,'cumulative_qualification_charge_s':carried+charged+supervisor_cpu,
        'sampled_peak_rss_bytes':peak,'sampled_process_tree_cpu_s':sampled_cpu,
        'observed_children_cpu_s':child_cpu,'accounting_observations_complete':child_cpu is not None,
        'accounting_unresolved':child_cpu is None,'charge_is_lower_bound':child_cpu is None,
        'termination':termination,'worker':worker,
        'worker_exit_observed_monotonic':exit_observed,
        'attempt_sha256':attemptsha,**output_hashes,
        'scope':'fixture/source freeze only; no native solve or qualification task dispatch'}
    write(folder/'supervisor.json',receipt)
    for sig,handler in previous.items():
        signal.signal(sig,handler)
    print(json.dumps(receipt,sort_keys=True,indent=2))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--guarded-worker')
    parser.add_argument('--parent-pid',type=int)
    for name in ('attempt-dir','command-json','lock','checks','accounting','protocol'):
        parser.add_argument('--'+name)
    args = parser.parse_args()
    if args.guarded_worker:
        if not args.parent_pid:
            parser.error('Guarded worker requires its actual supervisor PID')
        return guarded_worker(args.guarded_worker,args.parent_pid)
    if any(getattr(args,key) is None for key in ('attempt_dir','command_json','lock','checks','accounting','protocol')):
        parser.error('Supervisor requires explicit attempt/command/lock/check/accounting/protocol paths')
    return supervise(args)


if __name__=='__main__':
    raise SystemExit(main())
