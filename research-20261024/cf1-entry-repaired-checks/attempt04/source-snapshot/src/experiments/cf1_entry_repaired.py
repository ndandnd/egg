"""Fresh singleton CF1 entry policy; immutable roots and external owner required.

All numerical work remains in the reviewed adapter/worker. Import establishes
neither a launch context nor an output prefix, source receipt, or phase permit.
"""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import argparse
import os
import threading
import time

from experiments import cf1_small_mechanism_approved as approved
from experiments import cf1_entry_owner as entry_owner
from experiments.launch_entry_preparation import prepare_new_output

adapter, native_worker = approved.adapter, approved.native_worker
POLICY = 'cf1-entry-repaired-v5'
PACKAGE_START, PACKAGE_LIMIT, PACKAGE_CAP = 2426.723449631016, 175., 2601.723449631016
ANALYSIS_FINAL_RESERVE_S, SUPERVISION_RESERVE_S = 30., 45.
ENGINEERING_BASE_ID, ENGINEERING_TRIPS = 50997, 40
FIXTURE_POLICY, SCOPE = approved.FIXTURE_POLICY, approved.SCOPE
ACK_OBSERVATION = 'controller-ack-observation-v5.json'
WORKER_ARGV_PREFIX = ('-m', 'experiments.cf1_entry_repaired', 'worker')
NAMESPACE = 'research-20261024/cf1-entry-repaired-v5'
CHECK_NAMESPACE = 'research-20261024/cf1-entry-repaired-checks/attempt04'
ENTRY_PRECHARGE_S = 7.5
_CONFIG_LOCK = threading.Lock()
_BASE_CHECKED = approved.preflight.checked_sources
_DelegateLock = approved.preflight.preparation._DelegateLock
QUALIFIED_TEST_DEPENDENCIES = (
    'test_constructive_controls.py', 'test_comparison_native_adapter.py',
    'test_cf1_preparation_preflight.py', 'test_cf1_small_mechanism_preflight.py',
    'test_cf1_small_mechanism_approved.py', 'test_launch_accounting.py',
    'test_launch_prefix_initializer.py', 'test_launch_entry_preparation.py')


def task_matrix(cases=None):
    if cases is not None and (len(cases) != 1
            or cases[0].get('base_id') != ENGINEERING_BASE_ID
            or cases[0].get('trips') != ENGINEERING_TRIPS):
        raise ValueError('Revision5 requires inspected engineering50997/40 only')
    task = {'arm': 'cf1', 'base_id': ENGINEERING_BASE_ID,
            'trips': ENGINEERING_TRIPS, 'seed': 17, 'seconds': 60.,
            'fault': None, 'protocol_revision': 5}
    return [{**task, 'id': adapter.q.stable(task)[:20]}]


def check_command():
    return [str(adapter.q.ROOT/'.venv-local/bin/python'), '-m', 'pytest', '-q',
            'src/tests/test_cf1_entry_repaired.py']


def checked_sources(directory):
    q = adapter.q
    directory = Path(directory).resolve()
    if directory != (q.ROOT/CHECK_NAMESPACE).resolve():
        raise ValueError('Revision5 requires its exact fresh source-check attempt')
    # The inherited v3 chain retains the complete qualified receipt checks,
    # without invoking the historical exact-v4-attempt restriction.
    checks = _BASE_CHECKED(directory)
    attempt, result = q.read(directory/'attempt.json'), q.read(directory/'result.json')
    command = check_command()
    if (attempt.get('attempt_id') != 'attempt04' or attempt.get('revision') != 5
            or attempt.get('policy') != POLICY or attempt.get('command') != command
            or attempt.get('command_sha256') != q.stable(command)
            or attempt.get('executed_tests') != ['test_cf1_entry_repaired.py']
            or result.get('attempt_id') != 'attempt04' or result.get('revision') != 5
            or result.get('policy') != POLICY or result.get('command') != command
            or result.get('command_sha256') != q.stable(command)
            or result.get('executed_tests') != ['test_cf1_entry_repaired.py']):
        raise ValueError('Revision5 source-check execution identity differs')
    sources = attempt['source_hashes']
    required = dict(q.campaign.sources())
    required.update({str(q.ROOT/'src/tests'/name): q.sha(q.ROOT/'src/tests'/name)
                     for name in (*QUALIFIED_TEST_DEPENDENCIES, 'test_cf1_entry_repaired.py')})
    for path, digest in required.items():
        values = [value for name, value in sources.items()
                  if Path(name).resolve() == Path(path).resolve()]
        if values != [digest]:
            raise ValueError('Passing check misses current revision5 dependency: '+str(path))
    return checks


@contextmanager
def configuration5():
    """Own v4's original lock while its unchanged context uses a delegate."""
    if not _CONFIG_LOCK.acquire(blocking=False):
        raise RuntimeError('Revision5 requires serialized nonnested use')
    original_lock, held, saved = approved._CONFIG_LOCK, False, {}
    try:
        if not original_lock.acquire(blocking=False):
            raise RuntimeError('Revision4 configuration is already active')
        held = True
        original_revision4 = approved.revision4
        @contextmanager
        def budgeted_revision4():
            with original_revision4():
                adapter.q.CEILING, adapter.q.DISPATCH_STOP, adapter.q.SHUTDOWN_RESERVE = 3000., 2820., 180.
                yield
        changes = {'POLICY': POLICY, 'PACKAGE_START': PACKAGE_START,
            'PACKAGE_LIMIT': PACKAGE_LIMIT, 'PACKAGE_CAP': PACKAGE_CAP,
            'ANALYSIS_FINAL_RESERVE_S': ANALYSIS_FINAL_RESERVE_S,
            'SUPERVISION_RESERVE_S': SUPERVISION_RESERVE_S,
            'task_matrix': task_matrix, 'checked_sources': checked_sources,
            'ACK_OBSERVATION': ACK_OBSERVATION, '_CONFIG_LOCK': _DelegateLock(),
            'revision4': budgeted_revision4}
        for name, value in changes.items():
            saved[name] = getattr(approved, name)
            setattr(approved, name, value)
        yield
    finally:
        for name, value in reversed(tuple(saved.items())):
            setattr(approved, name, value)
        if held:
            original_lock.release()
        _CONFIG_LOCK.release()


@contextmanager
def revision5():
    with configuration5():
        with approved.revision4():
            # revision4 saves/restores this field, but hardcodes a v4 child.
            # Its original restore therefore also restores this inner override.
            adapter.WORKER_ARGV_PREFIX = WORKER_ARGV_PREFIX
            yield


def _exact_path(path, relative):
    expected = (adapter.q.ROOT/relative).resolve()
    if Path(path).resolve() != expected:
        raise ValueError('Revision5 requires exact fresh path: '+relative)
    return expected


def _roots(args, roots):
    expected = {'lock_path', 'freeze_receipt_path', 'accounting_path',
        'expected_lock_sha256', 'expected_freeze_receipt_sha256',
        'expected_accounting_sha256', 'expected_cumulative_charge_s', 'expected_policy'}
    if type(roots) is not dict or set(roots) != expected or roots['expected_policy'] != POLICY:
        raise ValueError('Require independent complete revision5 preparation roots')
    rooted = dict(roots)
    for key, suffix in (('lock_path', '/lock.json'),
            ('freeze_receipt_path', '/freeze-attempt01/result.json'),
            ('accounting_path', '/freeze-accounting.json')):
        rooted[key] = _exact_path(rooted[key], NAMESPACE+suffix)
    _exact_path(args.output, NAMESPACE+'/runs')
    if (rooted['lock_path'] != _exact_path(args.lock, NAMESPACE+'/lock.json')
            or rooted['freeze_receipt_path'] != _exact_path(
                args.freeze_receipt, NAMESPACE+'/freeze-attempt01/result.json')):
        raise ValueError('Entry arguments differ from independent fresh roots')
    return rooted


def freeze(args):
    _exact_path(args.lock, NAMESPACE+'/lock.json')
    _exact_path(getattr(args, 'design', None) or args.manifest, NAMESPACE+'/design.json')
    _exact_path(args.checks, CHECK_NAMESPACE)
    _exact_path(args.accounting, str(Path(CHECK_NAMESPACE).parent/'attempt04-accounting.json'))
    with revision5():
        return {**adapter.freeze(args), 'tasks': 1}


def run(args):
    """Explicit controller command; every independent root and owner FD is mandatory."""
    fields = ('lock', 'output', 'freeze_receipt', 'accounting',
        'expected_lock_sha256', 'expected_freeze_receipt_sha256',
        'expected_accounting_sha256', 'expected_cumulative_charge_s',
        'owner_fd', 'owner_root', 'owner_root_sha256', 'owner_nonce')
    if args is None or any(getattr(args, name, None) is None for name in fields):
        raise RuntimeError('Revision5 requires independent roots and a live owner gate')
    roots = {'lock_path': str(Path(args.lock).resolve()),
        'freeze_receipt_path': str(Path(args.freeze_receipt).resolve()),
        'accounting_path': str(Path(args.accounting).resolve()),
        **{name: getattr(args, name) for name in fields if name.startswith('expected_')},
        'expected_policy': POLICY}
    _roots(args, roots)
    root = _exact_path(args.owner_root, NAMESPACE+'/entry-owner.json')
    if type(args.owner_fd) is not int or args.owner_fd < 0:
        raise ValueError('Require an explicitly inherited owning-supervisor channel')
    import socket
    with socket.socket(fileno=args.owner_fd) as channel:
        owner = entry_owner.EntryClient(channel, root_path=root,
            expected_root_sha256=args.owner_root_sha256, nonce=args.owner_nonce,
            roots=roots, policy=POLICY, task=task_matrix()[0], output=args.output)
        return run_prepared(args, roots=roots, owner_gate=owner)


def run_prepared(args, *, roots, owner_gate):
    """Prepare once, durably precharge entry, then run under external dispatch control."""
    cpu0 = time.process_time()
    roots = _roots(args, roots)
    if (not callable(getattr(owner_gate, 'precharge', None))
            or not callable(getattr(owner_gate, 'launch_guard', None))
            or not callable(getattr(owner_gate, 'entry_scope', None))):
        raise ValueError('Require the live external whole-entry owner gate')
    with owner_gate.entry_scope(), revision5():
        q = adapter.q
        with adapter.bound60():
            prepare_new_output(args.output, **roots)
            lock = q.read(roots['lock_path'])
            budget_lock = adapter.freeze_accounting(
                lock, roots['lock_path'], roots['freeze_receipt_path'])
            prefix = deepcopy(q.ledger_events(Path(args.output)/'ledger.jsonl'))
            owner_gate.precharge(args.output, policy=POLICY, task=task_matrix()[0],
                lock_sha256=roots['expected_lock_sha256'],
                postfreeze_total_s=roots['expected_cumulative_charge_s'],
                budget_lock=budget_lock)
            _validate_precharge(args.output, prefix, budget_lock, roots)
        original_launch = adapter.launch
        funding_state, launched = {}, False
        try:
            def launch(args, task, output, locksha):
                nonlocal launched
                if (launched or task != task_matrix()[0]
                        or locksha != roots['expected_lock_sha256']
                        or Path(output).resolve() != Path(args.output).resolve()):
                    raise ValueError('Revision5 requires exactly its one fresh worker')
                _exact_path(output, NAMESPACE+'/runs')
                launched = True
                return owner_gate.launch_guard(args, task, output, locksha,
                    delegate=original_launch,
                    funding_check=lambda: _funding_check(
                        output, budget_lock, roots, task, cpu0, funding_state))
            adapter.launch = launch
            return adapter.run(args)
        finally:
            adapter.launch = original_launch


def _validate_precharge(output, prefix, budget_lock, roots):
    q = adapter.q
    events = q.ledger_events(Path(output)/'ledger.jsonl')
    if len(events) != len(prefix)+1 or events[:-1] != prefix:
        raise ValueError('Entry owner must append exactly one conservative precharge')
    event = events[-1]
    root = _exact_path(event.get('owner_root'), NAMESPACE+'/entry-owner.json')
    if (event.get('event') != 'supervisor_cpu'
            or event.get('phase') != 'whole_entry_precharge'
            or event.get('charged_cpu_s') != ENTRY_PRECHARGE_S
            or event.get('nonrefundable') is not True
            or event.get('policy') != POLICY or event.get('task') != task_matrix()[0]
            or event.get('output') != str(Path(output).resolve())
            or event.get('lock_sha256') != roots['expected_lock_sha256']
            or event.get('owner_root_sha256') != q.sha(root)
            or event.get('root_sha256') != event.get('owner_root_sha256')
            or event.get('controller_pid') != os.getpid()
            or type(event.get('nonce')) is not str or not event['nonce']
            or sum(value.get('phase') == 'whole_entry_precharge' for value in events) != 1):
        raise ValueError('Missing exact whole-entry precharge')
    completed, total = q.resume_state(output, budget_lock, roots['expected_lock_sha256'])
    if completed or total != roots['expected_cumulative_charge_s']+ENTRY_PRECHARGE_S:
        raise ValueError('Real resume does not consume exactly one entry precharge')


def _funding_check(output, budget_lock, roots, task, cpu0, state):
    """Recheck all live reservations without crediting the conservative overlap."""
    q = adapter.q
    for key, digest in (('lock_path', 'expected_lock_sha256'),
            ('freeze_receipt_path', 'expected_freeze_receipt_sha256'),
            ('accounting_path', 'expected_accounting_sha256')):
        if q.sha(roots[key]) != roots[digest]:
            raise ValueError('Independent entry root changed before worker creation')
    events = q.ledger_events(Path(output)/'ledger.jsonl')
    launches = [event for event in events if event.get('event') == 'launch']
    if launches:
        # The original launch records intent before its final Popen. Its live
        # intent is deliberately unresumable until a terminal receipt exists.
        # Validate the complete hash chain and the sole new intent against the
        # prefix already accepted by the real resume consumer at permit time.
        event = events[-1]
        intent = {key: value for key, value in event.items()
                  if key not in ('index', 'previous', 'sha256')}
        if (not state or len(launches) != 1 or events[:-1] != state['events']
                or set(intent) != {'event', 'task_id', 'parent_monotonic'}
                or intent['event'] != 'launch' or intent['task_id'] != task['id']
                or not q.finite(intent['parent_monotonic'])):
            raise ValueError('Worker launch changed the validated entry ledger')
        total = state['total']
    else:
        completed, total = q.resume_state(output, budget_lock, roots['expected_lock_sha256'])
        if completed or total != roots['expected_cumulative_charge_s']+ENTRY_PRECHARGE_S:
            raise ValueError('Entry precharge absent, duplicate, or changed')
        if state and (state['events'] != events or state['total'] != total):
            raise ValueError('Entry funding snapshot changed')
        state.update(events=deepcopy(events), total=total)
    own = time.process_time()-cpu0
    monitor = q._monitor_child_cpu_s
    if not all(q.finite(value) for value in (total, own, monitor)):
        raise ValueError('Incomplete current entry funding observations')
    charged = total+own+monitor
    if (charged+adapter.OUTER_S+SUPERVISION_RESERVE_S+ANALYSIS_FINAL_RESERVE_S > PACKAGE_CAP
            or charged+adapter.OUTER_S > q.DISPATCH_STOP
            or charged+adapter.OUTER_S+q.SHUTDOWN_RESERVE > q.CEILING):
        raise RuntimeError('Revision5 next-worker reservation exhausted')
    return {'charged_cpu_s': charged, 'package_cap_s': PACKAGE_CAP,
        'outer_allocation_s': adapter.OUTER_S, 'supervision_reserve_s': SUPERVISION_RESERVE_S,
        'analysis_final_reserve_s': ANALYSIS_FINAL_RESERVE_S,
        'global_hard_ceiling_s': q.CEILING, 'global_dispatch_stop_s': q.DISPATCH_STOP,
        'global_shutdown_reserve_s': q.SHUTDOWN_RESERVE}


def analyze(args):
    _exact_path(args.lock, NAMESPACE+'/lock.json')
    _exact_path(args.output, NAMESPACE+'/runs')
    _exact_path(args.report, NAMESPACE+'/report.json')
    # The unchanged analyzer enters the scoped, budgeted revision4 context.
    with configuration5():
        return approved.analyze(args)


def worker(args):
    _exact_path(args.lock, NAMESPACE+'/lock.json')
    _exact_path(args.output, NAMESPACE+'/runs/'+task_matrix()[0]['id'])
    with revision5():
        return native_worker.worker(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('freeze')
    p.add_argument('--design', '--manifest', dest='design', required=True)
    for name in ('lock', 'checks', 'accounting'):
        p.add_argument('--'+name, required=True)
    for name in ('run', 'analyze', 'worker'):
        p = commands.add_parser(name)
        for option in ('lock', 'output'):
            p.add_argument('--'+option, required=True)
        if name == 'run':
            p.add_argument('--freeze-receipt', required=True)
            p.add_argument('--accounting', required=True)
            for option in ('expected-lock-sha256', 'expected-freeze-receipt-sha256',
                    'expected-accounting-sha256', 'owner-root', 'owner-root-sha256', 'owner-nonce'):
                p.add_argument('--'+option, required=True)
            p.add_argument('--expected-cumulative-charge-s', type=float, required=True)
            p.add_argument('--owner-fd', type=int, required=True)
        elif name == 'analyze':
            p.add_argument('--report', required=True)
        else:
            p.add_argument('--parent-pid', type=int, required=True)
            p.add_argument('--ack-fd', type=int, required=True)
    args = parser.parse_args()
    result = {'freeze': freeze, 'run': run, 'analyze': analyze, 'worker': worker}[args.command](args)
    if args.command != 'worker':
        print(adapter.q.json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
