"""Bounded solver-free check receipts; deliberately not a native campaign runner."""
import hashlib
import json
import os
from pathlib import Path
import resource
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from experiments import codex_local_campaign as monitor


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def observed(command, sample_end):
    remaining = sample_end-time.monotonic()
    if remaining <= 0:
        raise TimeoutError('resource_monitor_sample_deadline')
    return subprocess.check_output(command, text=True, timeout=remaining)


def process_table(sample_end):
    table = {}
    for line in observed(['ps','-axo','pid=,ppid=,rss=,time='], sample_end).splitlines():
        row = line.split()
        if len(row) == 4:
            table[int(row[0])] = {'ppid':int(row[1]), 'rss':int(row[2])*1024,
                                 'cpu':monitor.seconds(row[3])}
    return table


def memory_state(sample_end):
    pressure = observed(['/usr/bin/memory_pressure','-Q'], sample_end)
    match = re.search(r'System-wide memory free percentage:\s*(\d+)%', pressure)
    if not match:
        raise RuntimeError('Cannot parse memory pressure monitor')
    return {'free_percent':int(match.group(1))}


def main():
    attempt_id = sys.argv[1]
    if attempt_id not in ('attempt01', 'attempt02'):
        raise ValueError('Only the two prospectively recorded check IDs are permitted')
    base = ROOT / 'research-20261023/coordinator-checks'
    folder = base / attempt_id
    # Existing attempts, including incomplete ones, are never overwritten/retried.
    folder.mkdir(parents=True, exist_ok=False)
    cpu0 = time.process_time()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    prior = 66.880135
    allowance = 20.0
    source_files = [Path(__file__).resolve(),
        ROOT/'src/egglab/recovery_coordinator.py',
        ROOT/'src/tests/test_recovery_coordinator.py',
        ROOT/'src/egglab/native_pathflow.py', ROOT/'src/egglab/recovery_lift.py',
        ROOT/'src/experiments/codex_local_campaign.py',
        ROOT/'research-20261023/RECOVERY_QUALIFICATION_PROTOCOL.md',
        ROOT/'research-20261023/RECOVERY_COORDINATOR_CHECK_PROTOCOL.md']
    prior_files = [ROOT/'research-20261023/native-primitive-lock-v1.json',
        ROOT/'research-20261023/native-primitive-v1/ledger.jsonl',
        *sorted((ROOT/'research-20261023/native-primitive-v1').glob('*/supervisor.json'))]
    previous = []
    for other in sorted(base.iterdir()):
        if not other.is_dir() or other == folder:
            continue
        receipt = other/'result.json'
        if not receipt.exists():
            raise RuntimeError('Unreceipted prior check requires reconciliation: '+str(other))
        item = json.loads(receipt.read_text())
        previous.append({'path':str(receipt.relative_to(ROOT)), 'sha256':digest(receipt),
                         'charge_s':item['charged_allocation_s']+item['supervisor_cpu_s']})
    carried = prior + allowance + sum(row['charge_s'] for row in previous)
    if carried + 32.5 >= 720:
        raise RuntimeError('Insufficient qualification dispatch allowance')
    command = [str(ROOT/'.venv-local/bin/python'), '-m', 'pytest', '-q',
               'src/tests/test_recovery_coordinator.py']
    hashes = {str(p.relative_to(ROOT)):digest(p) for p in source_files}
    anchor = time.monotonic()
    write(folder/'attempt.json', {'attempt_id':attempt_id, 'command':command,
        'parent_monotonic':anchor, 'source_hashes':hashes,
        'prior_evidence_hashes':{str(p.relative_to(ROOT)):digest(p) for p in prior_files},
        'previous_checks':previous, 'phase0_charge_s':prior,
        'administrative_allowance_s':allowance, 'carried_charge_s':carried,
        'wall_limit_s':30, 'rss_limit_bytes':5*1024**3, 'solver_free':True})
    env = {**os.environ, 'PYTHONPATH':str(ROOT/'src'), 'PYTHONDONTWRITEBYTECODE':'1',
           **{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
                             'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')}}
    proc = None
    peak = sampled_cpu = 0
    pressure_since = None
    last_pressure = 0
    failure = None
    termination = {'started':False}
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Check supervisor signal '+str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupted)
    with (folder/'stdout.log').open('x') as out, (folder/'stderr.log').open('x') as err:
        try:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                    start_new_session=True)
            while proc.poll() is None:
                now = time.monotonic()
                sample_end = min(now+.24, anchor+30.)
                rss, cpu = monitor.tree_stats(proc.pid, process_table(sample_end))
                peak, sampled_cpu = max(peak, rss), max(sampled_cpu, cpu)
                event = {'monotonic':now, 'pid':proc.pid, 'rss_bytes':rss, 'cpu_s':cpu}
                if now-last_pressure >= 1:
                    state = memory_state(sample_end)
                    event.update(state)
                    last_pressure = now
                    pressure_since = (pressure_since or now) if state['free_percent'] < 10 else None
                monitor.append(folder/'resources.jsonl', event)
                if rss > 5*1024**3:
                    raise RuntimeError('process_tree_rss_limit')
                if pressure_since is not None and now-pressure_since >= 5:
                    raise RuntimeError('sustained_memory_pressure')
                if now-anchor > 30:
                    raise TimeoutError('check_wall_limit')
                # Target a 0.25s sampling period including monitor work.
                time.sleep(max(0., .25-(time.monotonic()-now)))
        except BaseException as exc:
            failure = {'type':type(exc).__name__, 'message':str(exc)}
        finally:
            if proc is not None:
                monitor.stop(proc)
                try:
                    os.killpg(proc.pid, 0)
                    group_gone = False
                except ProcessLookupError:
                    group_gone = True
                termination = {'started':True, 'owned_pgid':proc.pid,
                               'leader_returncode':proc.returncode, 'group_absent':group_gone}
                if not group_gone:
                    failure = {'type':'RuntimeError', 'message':'owned_process_group_still_present'}
    elapsed = time.monotonic()-anchor
    changed = [name for name,value in hashes.items() if digest(ROOT/name) != value]
    supervisor_cpu = time.process_time()-cpu0
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime
    charged = max(elapsed, sampled_cpu, child_cpu)
    result = {'attempt_id':attempt_id, 'returncode':None if proc is None else proc.returncode,
        'failure':failure, 'source_changes':changed,
        'passed':bool(proc is not None and proc.returncode == 0 and failure is None and not changed),
        'elapsed_allocation_s':elapsed, 'sampled_process_tree_cpu_s':sampled_cpu,
        'observed_children_cpu_s':child_cpu, 'termination':termination,
        'sampled_peak_rss_bytes':peak, 'charged_allocation_s':charged,
        'supervisor_cpu_s':supervisor_cpu, 'cumulative_qualification_charge_s':carried+charged+supervisor_cpu,
        'stdout_sha256':digest(folder/'stdout.log'), 'stderr_sha256':digest(folder/'stderr.log'),
        'scope':'solver-free coordinator checks; no native qualification or performance claim'}
    write(folder/'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
