"""Prospective v6 CF1 bindings/controller; source alone clears no execution."""
from contextlib import contextmanager
from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import select
import signal
import socket
import threading
import time

from experiments import cf1_entry_repaired as legacy
from experiments import cf1_responsive_owner as entry_owner
from experiments.launch_entry_preparation import prepare_new_output

adapter, native_worker, approved = legacy.adapter, legacy.native_worker, legacy.approved
POLICY = 'cf1-responsive-supervision-v6'
PACKAGE_START, PACKAGE_LIMIT, PACKAGE_CAP = 2426.723449631016, 600., 3026.723449631016
SUPERVISION_RESERVE_S, ANALYSIS_FINAL_RESERVE_S, ENTRY_PRECHARGE_S = 120., 45., 65.
NAMESPACE = 'research-20261025/cf1-responsive-v6'
CHECK_NAMESPACE = 'research-20261025/cf1-responsive-checks/attempt01'
ACK_OBSERVATION = 'controller-ack-observation-v6.json'
WORKER_ARGV_PREFIX = ('-m', 'experiments.cf1_responsive_supervision', 'worker')
_CONFIG_LOCK = threading.Lock()
_ACTIVE_CLIENT = None


def task_matrix(cases=None):
    if cases is not None and (len(cases) != 1
            or cases[0].get('base_id') != 50997 or cases[0].get('trips') != 40):
        raise ValueError('Responsive v6 requires inspected50997/40 only')
    task = {'arm': 'cf1', 'base_id': 50997, 'trips': 40, 'seed': 17,
            'seconds': 60., 'fault': None, 'protocol_revision': 6}
    return [{**task, 'id': adapter.q.stable(task)[:20]}]


def check_command():
    return [str(adapter.q.ROOT/'.venv-local/bin/python'), '-m', 'pytest', '-q',
            'src/tests/test_responsive_supervision_v6.py']


def checked_sources(directory):
    q = adapter.q
    directory = Path(directory).resolve()
    if directory != (q.ROOT/CHECK_NAMESPACE).resolve():
        raise ValueError('Require exact new responsive source attempt01')
    checks = legacy._BASE_CHECKED(directory)
    attempt, result = q.read(directory/'attempt.json'), q.read(directory/'result.json')
    command = check_command()
    for record in (attempt, result):
        if (record.get('attempt_id') != 'attempt01' or record.get('revision') != 6
                or record.get('policy') != POLICY or record.get('command') != command
                or record.get('command_sha256') != q.stable(command)
                or record.get('executed_tests') != ['test_responsive_supervision_v6.py']):
            raise ValueError('Responsive source execution identity differs')
    required = dict(q.campaign.sources())
    for name in (*legacy.QUALIFIED_TEST_DEPENDENCIES, 'test_cf1_entry_repaired.py',
                 'test_responsive_supervision_v6.py'):
        path = q.ROOT/'src/tests'/name
        required[str(path)] = q.sha(path)
    for path, digest in required.items():
        matches = [value for name, value in attempt['source_hashes'].items()
                   if Path(name).resolve() == Path(path).resolve()]
        if matches != [digest]:
            raise ValueError('Responsive source check misses current dependency: '+path)
    return checks


@contextmanager
def configuration6():
    """Hold original locks and restore every legacy/global binding on all exits."""
    if threading.active_count() != 1 or not _CONFIG_LOCK.acquire(blocking=False):
        raise RuntimeError('Responsive v6 requires serialized single-thread use')
    original_lock, held, saved = legacy._CONFIG_LOCK, False, {}
    try:
        if not original_lock.acquire(blocking=False):
            raise RuntimeError('Legacy entry configuration already owned')
        held = True
        changes = {'POLICY': POLICY, 'PACKAGE_START': PACKAGE_START,
            'PACKAGE_LIMIT': PACKAGE_LIMIT, 'PACKAGE_CAP': PACKAGE_CAP,
            'ANALYSIS_FINAL_RESERVE_S': ANALYSIS_FINAL_RESERVE_S,
            'SUPERVISION_RESERVE_S': SUPERVISION_RESERVE_S,
            'ENTRY_PRECHARGE_S': ENTRY_PRECHARGE_S, 'NAMESPACE': NAMESPACE,
            'CHECK_NAMESPACE': CHECK_NAMESPACE, 'ACK_OBSERVATION': ACK_OBSERVATION,
            'WORKER_ARGV_PREFIX': WORKER_ARGV_PREFIX, 'task_matrix': task_matrix,
            'checked_sources': checked_sources, 'entry_owner': entry_owner,
            '_CONFIG_LOCK': legacy._DelegateLock()}
        for name, value in changes.items():
            saved[name] = getattr(legacy, name)
            setattr(legacy, name, value)
        with legacy.configuration5(), entry_owner.legacy_bindings():
            original_revision4 = approved.revision4
            @contextmanager
            def responsive_revision4():
                with original_revision4():
                    q = adapter.q
                    replacements = {'CEILING': 3600., 'DISPATCH_STOP': 3420.,
                        'SHUTDOWN_RESERVE': 180., 'run': responsive_run,
                        'receive_ack': receive_ack}
                    old = {name: getattr(q, name) for name in replacements}
                    try:
                        for name, value in replacements.items():
                            setattr(q, name, value)
                        yield
                    finally:
                        for name, value in old.items():
                            setattr(q, name, value)
            approved.revision4 = responsive_revision4
            try:
                yield
            finally:
                approved.revision4 = original_revision4
    finally:
        for name, value in reversed(tuple(saved.items())):
            setattr(legacy, name, value)
        if held:
            original_lock.release()
        _CONFIG_LOCK.release()


@contextmanager
def revision6():
    with configuration6(), approved.revision4():
        adapter.WORKER_ARGV_PREFIX = WORKER_ARGV_PREFIX
        yield


class ControlClock:
    """Actual controller service/ACK timer independent of resource sample arrival."""

    def __init__(self, anchor, *, clock=time.monotonic):
        self.anchor, self.clock, self.last_control = anchor, clock, anchor
        self.outer_deadline = anchor+62.5

    def tick(self, now=None):
        now = self.clock() if now is None else now
        if now < self.last_control or now-self.last_control > .25:
            raise TimeoutError('Native control service gap exceeds .25s')
        self.last_control = now
        return 'supervisor_stop' if now >= self.anchor+61. else None

    def observe_ack(self, item, receive):
        receive(item)
        return item.get('complete_ack_read_monotonic')


def receive_ack(item):
    """Timestamp the complete real read before JSON parsing or filesystem audit."""
    try:
        chunk = os.read(item['ack_fd'], 4097)
    except BlockingIOError:
        return
    if not chunk:
        return
    if item.get('acknowledgment') is not None:
        raise ValueError('Repeated acknowledgment payload')
    item['ack_bytes'] += chunk
    raw = item['ack_bytes']
    if len(raw) > 4096:
        raise ValueError('Oversized completion acknowledgment')
    if b'\n' not in raw:
        return
    observed = time.monotonic()
    item['complete_ack_read_monotonic'] = observed
    if raw.count(b'\n') != 1 or not raw.endswith(b'\n'):
        raise ValueError('Multiple/malformed completion acknowledgments')
    ack = json.loads(raw)
    q, task, anchor = adapter.q, item['task'], item['anchor']
    attempt = q.read(Path(item['folder'])/'attempt.json')
    if (not isinstance(ack, dict) or task != task_matrix()[0]
            or attempt.get('policy') != POLICY or attempt.get('task') != task
            or attempt.get('parent_monotonic') != anchor or attempt.get('deadline') != anchor+60.
            or ack.get('task_id') != task['id']
            or ack.get('lock_sha256') != attempt.get('lock_sha256')
            or not isinstance(ack.get('lock_sha256'), str) or not ack['lock_sha256']
            or ack.get('parent_monotonic') != anchor
            or not q.finite(ack.get('completion_monotonic'), anchor)
            or not q.finite(observed, ack['completion_monotonic'])
            or raw != approved._ack_bytes(ack)):
        raise ValueError('Responsive ACK observation identity/payload differs')
    item['acknowledgment'] = ack
    q.write_new(Path(item['folder'])/ACK_OBSERVATION, {'policy': POLICY,
        'task_id': task['id'], 'lock_sha256': attempt['lock_sha256'],
        'parent_monotonic': anchor, 'raw_payload_sha256': hashlib.sha256(raw).hexdigest(),
        'controller_observed_monotonic': observed})


def resource_record(item, sample, now):
    """Consume each true-start resource record once; never refresh a cache read."""
    if not sample or sample['sequence'] <= item.get('resource_sequence', 0):
        return
    if sample['start_monotonic'] < item['worker_registered_monotonic']:
        return
    if (now-sample['start_monotonic'] > 2.25 or sample['completed_monotonic'] > now
            or not adapter.q.finite(sample.get('cpu_resolution_s'))
            or not 0 < sample['cpu_resolution_s'] <= .01
            or sample['completed_monotonic']-sample['start_monotonic'] > 1.
            or (item.get('last_sample') is not None
                and sample['completed_monotonic']-item['last_sample'] > 1.25)):
        raise ValueError('Native resource start-age/duration/completed-gap differs')
    q, table, pid = adapter.q, sample['table'], item['proc'].pid
    if pid not in table:
        if item['proc'].poll() is None:
            raise ValueError('Live native worker missing from complete resource table')
        return
    descendants = {pid}
    while True:
        expanded = descendants | {child for child, row in table.items() if row['ppid'] in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    item['owned_pids'].update(descendants)
    watcher = entry_owner.watchdog_binding(item['folder'], pid)
    if watcher is not None and watcher in table:
        row = table[watcher]
        if row['pgid'] != pid or row['ppid'] not in (pid, 1):
            raise ValueError('Physical watchdog ancestry/group differs')
    expected = {pid} | (set() if watcher is None else {watcher})
    group_members = {child for child, row in table.items() if row['pgid'] == pid}
    if descendants-expected or group_members-expected:
        raise ValueError('Unregistered numerical descendant/group')
    item['owned_pids'].update(group_members)
    groups = {table[child]['pgid'] for child in descendants | group_members}
    item['owned_pgids'].update(groups)
    if groups != {pid}:
        raise ValueError('Unregistered numerical descendant/group')
    rows = [table[child] for child in item['owned_pids'] if child in table]
    item['cpu'] = max(item['cpu'], sum(row['cpu'] for row in rows))
    item['peak_rss'] = max(item['peak_rss'], sum(row['rss'] for row in rows))
    if item['peak_rss'] > q.RSS_LIMIT or not q.finite(sample['free']) or not 10 <= sample['free'] <= 100:
        raise ValueError('Unsafe native sampled RSS/memory pressure')
    item['last_sample'] = sample['completed_monotonic']
    item['resource_sequence'] = sample['sequence']
    item['resource_start'] = sample['start_monotonic']


def responsive_run(args):
    """One owned case; legacy physical launch/finish/ledger consumers are reused."""
    client, q = _ACTIVE_CLIENT, adapter.q
    if client is None or threading.active_count() != 1:
        raise RuntimeError('Responsive controller requires its live single-thread owner client')
    cpu0 = time.process_time()
    q._monitor_child_cpu_s = 0.
    lock, locksha = q.read(args.lock), q.sha(args.lock)
    q.verify_lock(lock)
    budget = q.freeze_accounting(lock, args.lock, args.freeze_receipt)
    output = Path(args.output).resolve()
    marker = output/'.supervisor-owner'
    q.write_new(marker, {'pid': os.getpid(), 'lock_sha256': locksha})
    old = {sig: signal.signal(sig, q.campaign.signal_stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    args.active, receipt, reason = None, None, None
    try:
        completed, total = q.resume_state(output, budget, locksha)
        if completed or lock['tasks'] != task_matrix():
            raise ValueError('Responsive native dispatch requires its unused exact singleton')
        entry_owner.funded(total+time.process_time()-cpu0, 62.5, final=120.+45.)
        item = args.active = q.launch(args, task_matrix()[0], output, locksha)
        item['worker_registered_monotonic'] = time.monotonic()
        client.worker_created(item)
        clock = ControlClock(item['anchor'], clock=time.monotonic)
        while item['proc'].poll() is None:
            # Actual complete-read timestamp precedes optional telemetry parsing.
            observed = clock.observe_ack(item, q.receive_ack)
            reason = clock.tick()
            if observed is not None and observed > item['anchor']+60.:
                reason = 'late_complete_ack'
            sample = client.service()
            if time.process_time()-client.controller_gate_cpu > entry_owner.CONTROLLER_CPU_S:
                raise RuntimeError('Controller supervision CPU31.5 provision exhausted')
            if reason:
                break
            resource_record(item, sample, time.monotonic())
            start = item.get('resource_start')
            if time.monotonic()-(item['worker_registered_monotonic'] if start is None else start) > 2.25:
                raise TimeoutError('Native resource provenance expired')
            if sample is not None:
                projected = (total+max(time.monotonic()-item['anchor'], item['cpu'])
                    +time.process_time()-cpu0+entry_owner.uncertainty(
                        os.cpu_count(), time.monotonic()-sample['start_monotonic'], cleanup=True))
                entry_owner.funded(projected, max(0., clock.outer_deadline-time.monotonic()))
            if (Path(item['folder'])/'completion.json').exists() and item['completion_observed'] is None:
                item['completion_observed'] = time.monotonic()
            select.select([item['ack_fd'], client.telemetry.channel], [], [], .005)
        observed = clock.observe_ack(item, q.receive_ack)
        if observed is not None and observed > item['anchor']+60.:
            reason = reason or 'late_complete_ack'
        if reason:
            q.preserve_stop(item, reason)
            q.write_once_equal(Path(item['folder'])/'STOP', {'reason': reason, 'monitor_failure': None})
        if item['completion_observed'] is None and (Path(item['folder'])/'completion.json').exists():
            item['completion_observed'] = time.monotonic()
        # Explicit phase boundary: owner continues resource/cleanup accounting,
        # but neither process claims .25s controller service inside legacy finish.
        client.terminal(item, reason)
        receipt = q.finish(item, locksha, output, reason)
        if receipt['group_absent']:
            args.active = None
        if time.process_time()-client.controller_gate_cpu > entry_owner.CONTROLLER_CPU_S:
            raise RuntimeError('Controller terminal CPU31.5 provision exhausted')
        return {'halted': ('attempt_failure_stops_dispatch' if receipt['failure']
            or receipt['returncode'] or receipt['worker_failure'] or receipt['endpoint_censored'] else None),
            'planned': 1, 'attempted': 1}
    except BaseException as exc:
        if args.active is not None:
            q.preserve_stop(args.active, 'responsive_controller_failure:'+type(exc).__name__)
            if not getattr(client, 'terminal_phase', False):
                client.terminal(args.active, str(exc))
            if not args.active.get('terminalized'):
                receipt = q.finish(args.active, locksha, output, args.active['primary_reason'])
                if receipt['group_absent']:
                    args.active = None
        raise
    finally:
        for sig in old:
            signal.signal(sig, signal.SIG_IGN)
        try:
            if args.active is not None and not args.active.get('terminalized'):
                q.append_ledger(output/'ledger.jsonl', {'event': 'incomplete_terminal_audit',
                    'task_id': args.active['task']['id'], 'primary_reason': args.active.get('primary_reason'),
                    'monitor_failure': args.active.get('monitor_failure'),
                    'secondary_errors': args.active.get('secondary_errors', []),
                    'group_absent': args.active.get('retired', False),
                    'provisional_worker_charge_s': max(time.monotonic()-args.active['anchor'], args.active['cpu'])})
            own = time.process_time()-cpu0
            q.append_ledger(output/'ledger.jsonl', {'event': 'supervisor_cpu',
                'process_cpu_s': own, 'monitor_child_cpu_s': 0., 'charged_cpu_s': own})
            if args.active is None:
                marker.unlink()
        finally:
            for sig, handler in old.items():
                signal.signal(sig, handler)


def freeze(args):
    with revision6():
        legacy._exact_path(args.lock, NAMESPACE+'/lock.json')
        legacy._exact_path(args.design, NAMESPACE+'/design.json')
        legacy._exact_path(args.checks, CHECK_NAMESPACE)
        legacy._exact_path(args.accounting, str(Path(CHECK_NAMESPACE).parent/'attempt01-accounting.json'))
        return {**adapter.freeze(args), 'tasks': 1}


def run_prepared(args, *, roots, owner_gate):
    global _ACTIVE_CLIENT
    with revision6(), owner_gate.entry_scope():
        roots = legacy._roots(args, roots)
        with adapter.bound60():
            prepare_new_output(args.output, **roots)
            budget = adapter.freeze_accounting(adapter.q.read(roots['lock_path']),
                roots['lock_path'], roots['freeze_receipt_path'])
            prefix = deepcopy(adapter.q.ledger_events(Path(args.output)/'ledger.jsonl'))
            owner_gate.precharge(args.output, policy=POLICY, task=task_matrix()[0],
                lock_sha256=roots['expected_lock_sha256'],
                postfreeze_total_s=roots['expected_cumulative_charge_s'], budget_lock=budget)
            legacy._validate_precharge(args.output, prefix, budget, roots)
        original, previous_client = adapter.launch, _ACTIVE_CLIENT
        state, launched = {}, False
        cpu0 = time.process_time()
        try:
            _ACTIVE_CLIENT = owner_gate
            def launch(args, task, output, locksha):
                nonlocal launched
                if launched or task != task_matrix()[0] or locksha != roots['expected_lock_sha256']:
                    raise ValueError('Only the exact fresh responsive worker may launch')
                legacy._exact_path(output, NAMESPACE+'/runs')
                launched = True
                return owner_gate.launch_guard(args, task, output, locksha, delegate=original,
                    funding_check=lambda: legacy._funding_check(output, budget, roots, task, cpu0, state))
            adapter.launch = launch
            return adapter.run(args)
        finally:
            adapter.launch, _ACTIVE_CLIENT = original, previous_client


def run(args):
    required = ('lock', 'output', 'freeze_receipt', 'accounting', 'expected_lock_sha256',
        'expected_freeze_receipt_sha256', 'expected_accounting_sha256',
        'expected_cumulative_charge_s', 'owner_fd', 'owner_telemetry_fd',
        'owner_root', 'owner_root_sha256', 'owner_nonce')
    if any(getattr(args, name, None) is None for name in required):
        raise RuntimeError('Require complete independent v6 roots and both inherited channels')
    if Path(args.owner_root).resolve() != (adapter.q.ROOT/NAMESPACE/'entry-owner.json').resolve():
        raise ValueError('Require exact fresh responsive owner root')
    roots = {'lock_path': str(Path(args.lock).resolve()),
        'freeze_receipt_path': str(Path(args.freeze_receipt).resolve()),
        'accounting_path': str(Path(args.accounting).resolve()), 'expected_policy': POLICY,
        **{name: getattr(args, name) for name in required if name.startswith('expected_')}}
    # Construct under temporary identity bindings; run_prepared owns the full
    # serialized policy context. Import/constructor alone never starts a worker.
    with (entry_owner.legacy_bindings(), socket.socket(fileno=args.owner_fd) as control,
            socket.socket(fileno=args.owner_telemetry_fd) as telemetry):
        owner = entry_owner.EntryClient(control, telemetry,
            root_path=args.owner_root, expected_root_sha256=args.owner_root_sha256,
            nonce=args.owner_nonce, roots=roots, policy=POLICY, task=task_matrix()[0], output=args.output)
        return run_prepared(args, roots=roots, owner_gate=owner)


def analyze(args):
    with configuration6():
        legacy._exact_path(args.lock, NAMESPACE+'/lock.json')
        legacy._exact_path(args.output, NAMESPACE+'/runs')
        legacy._exact_path(args.report, NAMESPACE+'/report.json')
        return approved.analyze(args)


def worker(args):
    with revision6():
        legacy._exact_path(args.lock, NAMESPACE+'/lock.json')
        legacy._exact_path(args.output, NAMESPACE+'/runs/'+task_matrix()[0]['id'])
        return native_worker.worker(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('freeze')
    for name in ('design', 'lock', 'checks', 'accounting'):
        p.add_argument('--'+name, required=True)
    for name in ('run', 'analyze', 'worker'):
        p = commands.add_parser(name)
        for field in ('lock', 'output'):
            p.add_argument('--'+field, required=True)
        if name == 'run':
            for field in ('freeze_receipt', 'accounting', 'expected_lock_sha256',
                    'expected_freeze_receipt_sha256', 'expected_accounting_sha256',
                    'owner_root', 'owner_root_sha256', 'owner_nonce'):
                p.add_argument('--'+field.replace('_', '-'), required=True)
            p.add_argument('--expected-cumulative-charge-s', type=float, required=True)
            p.add_argument('--owner-fd', type=int, required=True)
            p.add_argument('--owner-telemetry-fd', type=int, required=True)
        elif name == 'analyze':
            p.add_argument('--report', required=True)
        else:
            p.add_argument('--parent-pid', type=int, required=True)
            p.add_argument('--ack-fd', type=int, required=True)
    args = parser.parse_args()
    result = {'freeze': freeze, 'run': run, 'analyze': analyze, 'worker': worker}[args.command](args)
    if args.command != 'worker':
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
