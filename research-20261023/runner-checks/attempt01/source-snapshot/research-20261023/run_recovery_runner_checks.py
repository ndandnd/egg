"""One prospective solver-free runner check, with retained descendant ownership."""
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

import run_coordinator_checks as prior

ROOT = prior.ROOT
BASE = ROOT / 'research-20261023/runner-checks'
ADMINISTRATION = 30.0


def snapshot(end):
    table = {}
    for line in prior.observed(['ps', '-axo', 'pid=,ppid=,pgid=,rss=,time='], end).splitlines():
        row = line.split()
        if len(row) == 5:
            table[int(row[0])] = {'ppid': int(row[1]), 'pgid': int(row[2]),
                                 'rss': int(row[3]) * 1024,
                                 'cpu': prior.monitor.seconds(row[4])}
    return table


def owned_rows(pid, groups, table):
    ids = {pid} | {p for p, r in table.items() if r['pgid'] in groups}
    while True:
        expanded = ids | {p for p, r in table.items() if r['ppid'] in ids}
        if expanded == ids:
            break
        ids = expanded
    # A detached test group is ours only after its descendant relationship was observed.
    groups.update(table[p]['pgid'] for p in ids if p in table
                  and table[p]['pgid'] != os.getpgrp())
    return [table[p] for p in ids if p in table]


def group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def registered_groups(path, groups):
    # Source-hashed ownership tests explicitly register groups they create before
    # exercising parent death. This closes a polling race for short-lived parents.
    if not path.exists():
        return
    raw = path.read_text()
    for line in raw.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        pgid = item['pgid']
        if type(pgid) is not int or pgid <= 1 or pgid == os.getpgrp():
            raise RuntimeError('Invalid owned test group registration')
        groups.add(pgid)


def cleanup(proc, groups):
    # Nested ownership tests may deliberately create separate sessions. Preserve their
    # observed PGIDs even if the pytest leader exits before the outer cleanup begins.
    for pgid in groups:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    end = time.monotonic() + .5
    while time.monotonic() < end and any(group_exists(g) for g in groups):
        time.sleep(.02)
    for pgid in groups:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    proc.wait(timeout=1)
    end = time.monotonic() + .5
    while time.monotonic() < end and any(group_exists(g) for g in groups):
        time.sleep(.02)
    return {'owned_pgids': sorted(groups), 'leader_returncode': proc.returncode,
            'surviving_pgids': sorted(g for g in groups if group_exists(g))}


def main():
    cpu0 = time.process_time()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    evidence = ROOT / 'research-20261023/coordinator-checks/accounting.json'
    accounting = json.loads(evidence.read_text())
    carried = accounting['cumulative_qualification_charge_s'] + ADMINISTRATION
    if accounting['cumulative_qualification_charge_s'] != 88.20958837542922:
        raise RuntimeError('Prospective prior accounting changed; reconcile before dispatch')
    if carried + 32.5 >= 720:
        raise RuntimeError('Insufficient remaining shared qualification budget')
    folder = BASE / 'attempt01'
    folder.mkdir(parents=True, exist_ok=False)  # Never resume, overwrite or retry this check.
    sources = prior.monitor.sources()
    for relative in ('src/tests/test_recovery_qualification.py',
                     'research-20261023/run_recovery_runner_checks.py',
                     'research-20261023/run_coordinator_checks.py',
                     'research-20261023/RECOVERY_RUNNER_CHECK_PROTOCOL.md',
                     'research-20261023/RECOVERY_QUALIFICATION_PROTOCOL.md'):
        sources[str(ROOT / relative)] = prior.digest(ROOT / relative)
    prior_files = [evidence, ROOT / 'research-20261023/native-primitive-lock-v1.json',
                   ROOT / 'research-20261023/native-primitive-v1/ledger.jsonl',
                   *sorted((ROOT / 'research-20261023/native-primitive-v1').glob('*/supervisor.json')),
                   *sorted((ROOT / 'research-20261023/coordinator-checks').glob('attempt*/attempt.json')),
                   *sorted((ROOT / 'research-20261023/coordinator-checks').glob('attempt*/result.json'))]
    command = [str(ROOT / '.venv-local/bin/python'), '-m', 'pytest', '-q',
               'src/tests/test_recovery_qualification.py']
    anchor = time.monotonic()
    prior.write(folder / 'attempt.json', {'attempt_id': 'attempt01', 'command': command,
        'parent_monotonic': anchor, 'source_hashes': sources,
        'prior_evidence_hashes': {str(p.relative_to(ROOT)): prior.digest(p) for p in prior_files},
        'carried_charge_s': carried, 'administration_allowance_s': ADMINISTRATION,
        'wall_limit_s': 30, 'rss_limit_bytes': 5 * 1024**3, 'solver_free': True})
    registry = folder / 'owned-test-groups.jsonl'
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src'), 'PYTHONDONTWRITEBYTECODE': '1',
           'EGG_CHECK_PGID_REGISTRY': str(registry),
           **{name: '1' for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')}}
    groups = set()
    proc = None
    peak = sampled_cpu = last_pressure = 0
    pressure_since = None
    failure = None
    termination = {'owned_pgids': [], 'surviving_pgids': []}

    def interrupted(signum, frame):
        raise KeyboardInterrupt('Check supervisor signal ' + str(signum))

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupted)
    with (folder / 'stdout.log').open('x') as out, (folder / 'stderr.log').open('x') as err:
        try:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                    start_new_session=True)
            groups.add(proc.pid)
            while proc.poll() is None:
                now = time.monotonic()
                sample_end = min(now + .24, anchor + 30)
                registered_groups(registry, groups)
                rows = owned_rows(proc.pid, groups, snapshot(sample_end))
                rss, cpu = sum(r['rss'] for r in rows), sum(r['cpu'] for r in rows)
                peak, sampled_cpu = max(peak, rss), max(sampled_cpu, cpu)
                event = {'monotonic': now, 'rss_bytes': rss, 'cpu_s': cpu,
                         'owned_pgids': sorted(groups)}
                if now - last_pressure >= 1:
                    state = prior.memory_state(sample_end)
                    event.update(state)
                    last_pressure = now
                    pressure_since = (pressure_since or now) if state['free_percent'] < 10 else None
                prior.monitor.append(folder / 'resources.jsonl', event)
                if rss > 5 * 1024**3:
                    raise RuntimeError('process_tree_rss_limit')
                if pressure_since is not None and now - pressure_since >= 5:
                    raise RuntimeError('sustained_memory_pressure')
                if now - anchor > 30:
                    raise TimeoutError('check_wall_limit')
                time.sleep(max(0., .25 - (time.monotonic() - now)))
        except BaseException as exc:
            failure = {'type': type(exc).__name__, 'message': str(exc)}
        finally:
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, signal.SIG_IGN)
            if proc is not None:
                try:
                    registered_groups(registry, groups)
                except BaseException as exc:
                    failure = {'type': type(exc).__name__, 'message': str(exc)}
                try:
                    termination = cleanup(proc, groups)
                    if termination['surviving_pgids']:
                        raise RuntimeError('owned_process_group_still_present')
                except BaseException as exc:
                    failure = {'type': type(exc).__name__, 'message': str(exc)}
    elapsed = time.monotonic() - anchor
    changed = []
    for name, expected in sources.items():
        try:
            unchanged = prior.digest(Path(name)) == expected
        except OSError:
            unchanged = False
        if not unchanged:
            changed.append(name)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = children.ru_utime + children.ru_stime - child0.ru_utime - child0.ru_stime
    charged = max(elapsed, sampled_cpu, child_cpu)
    supervisor_cpu = time.process_time() - cpu0
    result = {'attempt_id': 'attempt01', 'returncode': None if proc is None else proc.returncode,
        'failure': failure, 'source_changes': changed,
        'passed': bool(proc is not None and proc.returncode == 0 and failure is None and not changed),
        'elapsed_allocation_s': elapsed, 'sampled_process_tree_cpu_s': sampled_cpu,
        'observed_children_cpu_s': child_cpu, 'termination': termination,
        'sampled_peak_rss_bytes': peak, 'charged_allocation_s': charged,
        'supervisor_cpu_s': supervisor_cpu, 'cumulative_qualification_charge_s': carried + charged + supervisor_cpu,
        'stdout_sha256': prior.digest(folder / 'stdout.log'),
        'stderr_sha256': prior.digest(folder / 'stderr.log'),
        'scope': 'solver-free operational runner checks; native matrix not frozen or dispatched'}
    prior.write(folder / 'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
