"""Single prospective solver-free supervision regression; no native dispatch."""
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

import run_recovery_runner_checks as checked

prior = checked.prior
ROOT = checked.ROOT
CARRIED = 169.35673816793766
ADMIN = 20.0
PRIOR_MONITOR_RECONCILIATION = 20.0


def cleanup_owned(proc, groups):
    original = checked.group_exists
    diagnostics = []

    def probe(pgid):
        try:
            return original(pgid)
        except PermissionError as exc:
            diagnostics.append({'pgid':pgid,'state':'unknown_permission',
                                'errno':exc.errno,'message':str(exc)})
            return True  # Unknown cannot satisfy confirmed absence.

    checked.group_exists = probe
    try:
        result = checked.cleanup(proc,groups)
        result['probe_diagnostics'] = diagnostics
        return result
    finally:
        checked.group_exists = original


def main():
    cpu0 = time.process_time()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    evidence = ROOT/'research-20261023/recovery-phase1-v1/accounting.json'
    account = json.loads(evidence.read_text())
    if account['charged_cpu_s'] != CARRIED:
        raise RuntimeError('Reconcile current native-v1 accounting before check')
    carried = CARRIED+PRIOR_MONITOR_RECONCILIATION+ADMIN
    if carried+32.5>720.:
        raise RuntimeError('Insufficient remaining dispatch allowance')
    folder = ROOT/'research-20261023/supervision-repair-checks/attempt01'
    folder.mkdir(parents=True,exist_ok=False)
    files = [Path(__file__),ROOT/'research-20261023/run_recovery_runner_checks.py',
             ROOT/'research-20261023/run_coordinator_checks.py',
             ROOT/'research-20261023/RECOVERY_SUPERVISION_REPAIR_PROTOCOL.md',
             ROOT/'src/tests/test_recovery_qualification.py',
             ROOT/'src/tests/test_recovery_supervision_repair.py']
    sources = prior.monitor.sources()
    sources.update({str(p):prior.digest(p) for p in files})
    prior_files = [evidence,ROOT/'research-20261023/recovery-phase1-v1/lock.json',
                   ROOT/'research-20261023/recovery-phase1-v1/runs/ledger.jsonl',
                   ROOT/'research-20261023/recovery-phase1-v1/gates.json',
                   ROOT/'research-20261023/recovery-phase1-v1/freeze-attempt01/supervisor.json',
                   *sorted((ROOT/'research-20261023/recovery-phase1-v1/runs').glob('*/supervisor.json')),
                   ROOT/'research-20261023/runner-checks/attempt02/attempt.json',
                   ROOT/'research-20261023/runner-checks/attempt02/result.json']
    command = [str(ROOT/'.venv-local/bin/python'),'-m','pytest','-q',
               'src/tests/test_recovery_qualification.py','src/tests/test_recovery_supervision_repair.py']
    anchor = time.monotonic()
    prior.write(folder/'attempt.json',{'attempt_id':'attempt01','command':command,
        'parent_monotonic':anchor,'source_hashes':sources,
        'prior_evidence_hashes':{str(p.relative_to(ROOT)):prior.digest(p) for p in prior_files},
        'carried_charge_s':carried,'administration_allowance_s':ADMIN,
        'prior_monitor_cpu_reconciliation_s':PRIOR_MONITOR_RECONCILIATION,
        'wall_limit_s':30,'rss_limit_bytes':5*1024**3,'solver_free':True})
    registry = folder/'owned-test-groups.jsonl'
    env = {**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
           'EGG_CHECK_PGID_REGISTRY':str(registry),
           **{name:'1' for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS')}}
    proc = None
    groups = set()
    peak = sampled_cpu = last_pressure = 0.
    last_sample = None
    pressure_since = None
    failure = None
    termination = {'owned_pgids':[],'surviving_pgids':[]}

    def interrupted(signum,frame):
        raise KeyboardInterrupt('Check supervisor signal '+str(signum))

    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,interrupted)
    with (folder/'stdout.log').open('x') as out,(folder/'stderr.log').open('x') as err:
        try:
            proc = subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err,
                                    start_new_session=True)
            groups.add(proc.pid)
            while proc.poll() is None:
                now = time.monotonic()
                if last_sample is not None and now-last_sample>.25:
                    raise RuntimeError('resource_monitor_sampling_gap')
                last_sample = now
                end = min(now+.24,anchor+30.)
                checked.registered_groups(registry,groups)
                table = checked.snapshot(end)
                if os.getpid() not in table:
                    raise RuntimeError('incomplete_process_monitor')
                rows = checked.owned_rows(proc.pid,groups,table)
                rss,cpu = sum(r['rss'] for r in rows),sum(r['cpu'] for r in rows)
                peak,sampled_cpu = max(peak,rss),max(sampled_cpu,cpu)
                event = {'monotonic':now,'rss_bytes':rss,'cpu_s':cpu,'owned_pgids':sorted(groups)}
                if now-last_pressure>=1.:
                    state = prior.memory_state(end)
                    free = state['free_percent']
                    if not isinstance(free,(int,float)) or not math.isfinite(free) or not 0<=free<=100:
                        raise RuntimeError('invalid_memory_monitor')
                    event.update(state)
                    last_pressure = now
                    pressure_since = (pressure_since or now) if state['free_percent']<10 else None
                prior.monitor.append(folder/'resources.jsonl',event)
                if rss>5*1024**3:
                    raise RuntimeError('process_tree_rss_limit')
                if pressure_since is not None and now-pressure_since>=5.:
                    raise RuntimeError('sustained_memory_pressure')
                if now-anchor>=30.:
                    raise TimeoutError('check_wall_limit')
                time.sleep(max(0.,.20-(time.monotonic()-now)))
        except BaseException as exc:
            failure = {'type':type(exc).__name__,'message':str(exc)}
        finally:
            for sig in (signal.SIGTERM,signal.SIGINT):
                signal.signal(sig,signal.SIG_IGN)
            if proc is not None:
                try:
                    checked.registered_groups(registry,groups)
                except BaseException as exc:
                    failure = failure or {'type':type(exc).__name__,'message':str(exc)}
                try:
                    termination = cleanup_owned(proc,groups)
                    if termination['surviving_pgids']:
                        raise RuntimeError('owned_process_group_still_present')
                except BaseException as exc:
                    failure = failure or {'type':type(exc).__name__,'message':str(exc)}
    elapsed = time.monotonic()-anchor
    changed = []
    for name,expected in sources.items():
        try:
            unchanged = prior.digest(Path(name))==expected
        except OSError:
            unchanged = False
        if not unchanged:
            changed.append(name)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime
    charged = max(elapsed,sampled_cpu,child_cpu)
    supervisor_cpu = time.process_time()-cpu0
    result = {'attempt_id':'attempt01','returncode':None if proc is None else proc.returncode,
        'failure':failure,'source_changes':changed,
        'passed':bool(proc is not None and proc.returncode==0 and failure is None and not changed),
        'elapsed_allocation_s':elapsed,'sampled_process_tree_cpu_s':sampled_cpu,
        'observed_children_cpu_s':child_cpu,'termination':termination,
        'sampled_peak_rss_bytes':peak,'charged_allocation_s':charged,'supervisor_cpu_s':supervisor_cpu,
        'cumulative_qualification_charge_s':carried+charged+supervisor_cpu,
        'stdout_sha256':prior.digest(folder/'stdout.log'),'stderr_sha256':prior.digest(folder/'stderr.log'),
        'scope':'solver-free supervision repair; no native rerun authorized or executed'}
    prior.write(folder/'result.json',result)
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
