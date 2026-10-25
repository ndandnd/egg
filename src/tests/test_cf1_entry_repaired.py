"""One affected v5 gate: inert source bindings and handwritten metadata only.

This file does not import numerical modules, inspect fixtures/environment, or
launch a process. Owner evidence is deliberately fake and establishes only
conditional source behavior, never runtime ownership/timing qualification.
"""

import ast
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def source(name, **bindings):
    """Compile reviewed source against inert injected project dependencies."""
    path = ROOT / 'src' / 'experiments' / (name + '.py')
    tree = ast.parse(path.read_text(), filename=str(path))
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom) and node.module and
        node.module.split('.')[0] in {'experiments', 'egglab'})]
    module = ModuleType('isolated_' + name)
    module.__dict__.update(bindings)
    exec(compile(tree, str(path), 'exec'), module.__dict__)
    return module


def selected_recovery_functions():
    """Use the actual ledger/read/resume consumer, without module imports."""
    path = ROOT / 'src/experiments/recovery_qualification.py'
    tree = ast.parse(path.read_text(), filename=str(path))
    names = {'finite', 'read', 'ledger_events', 'append_ledger', 'resume_state'}
    tree.body = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    def append(path, value):
        with Path(path).open('a') as stream:
            stream.write(json.dumps(value, sort_keys=True) + '\n')
    scope = {'Path': Path, 'json': json, 'math': math, 'stable': stable,
             'campaign': SimpleNamespace(append=append),
             'sha': lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest(),
             'verify_hashes': lambda inventory: None}
    exec(compile(tree, str(path), 'exec'), scope)
    return SimpleNamespace(**{name: scope[name] for name in names})


def wrapper_harness():
    store, writes, events = {}, [], []
    def read(path):
        return store[str(Path(path))]
    def write(path, value):
        key = str(Path(path))
        if key in store:
            raise FileExistsError(key)
        store[key] = value
        writes.append((key, value))
    q = SimpleNamespace(stable=stable, json=json, ROOT=ROOT, read=read,
        write_new=write, sha=lambda path: stable(store[str(Path(path))])
            if str(Path(path)) in store else 'source:' + str(Path(path).relative_to(ROOT)),
        finite=lambda value, minimum=0.: type(value) in (int, float)
            and math.isfinite(value) and value >= minimum,
        CEILING=1800., DISPATCH_STOP=1620., SHUTDOWN_RESERVE=180.,
        receive_ack=lambda item: None,
        campaign=SimpleNamespace(sources=lambda: {
            str(ROOT/'src/experiments/otherwise_unlisted.py'): 'complete-source-closure'}))
    adapter = SimpleNamespace(q=q, POLICY='original', PACKAGE_START=1.,
        PACKAGE_LIMIT=2., PACKAGE_CAP=3., ANALYSIS_FINAL_RESERVE_S=5.,
        SUPERVISION_RESERVE_S=40., FREEZE_ELAPSED_LIMIT_S=10., ENGINEERING_BASE_ID=50999,
        ENGINEERING_TRIPS=80, FIXTURE_POLICY='original',
        WORKER_ARGV_PREFIX=('original',), task_matrix=lambda cases: [],
        checked_sources=lambda directory: {'inherited': 'qualified-dependency'},
        _LOCK=threading.Lock())
    worker = SimpleNamespace(POLICY='original-worker', task_matrix=lambda: [])
    preparation = source('cf1_preparation_preflight', adapter=adapter, native_worker=worker)
    preflight = source('cf1_small_mechanism_preflight', preparation=preparation)
    approved = source('cf1_small_mechanism_approved', preflight=preflight)
    @contextmanager
    def bound60(state=None):
        if not adapter._LOCK.acquire(blocking=False):
            raise RuntimeError('Fake bound60 nested')
        events.append('bound-enter')
        try:
            yield
        finally:
            events.append('bound-exit')
            adapter._LOCK.release()
    adapter.bound60 = bound60
    def prepare(output, **roots):
        events.append('prepare')
        return {'resumed_total_s': roots['expected_cumulative_charge_s']}
    v5 = source('cf1_entry_repaired', approved=approved, prepare_new_output=prepare)
    return SimpleNamespace(v5=v5, approved=approved, preflight=preflight,
        adapter=adapter, worker=worker, q=q, store=store, writes=writes, events=events)


def owner_harness(directory):
    """Fake independently retained parent records; actual hash/ledger consumers."""
    real = selected_recovery_functions()
    q = SimpleNamespace(**vars(real), stable=stable,
        sha=lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        subprocess=SimpleNamespace(Popen=lambda *args, **kwargs: None),
        _monitor_child_cpu_s=0.)
    def write(path, value):
        with Path(path).open('x') as stream:
            json.dump(value, stream, sort_keys=True)
    q.write_new = write
    owner = source('cf1_entry_owner', q=q)
    now = SimpleNamespace(value=100.2)
    capacity = 8
    owner.time = SimpleNamespace(monotonic=lambda: now.value, process_time=lambda: .1)
    owner.os = SimpleNamespace(getpid=lambda: 211, getppid=lambda: 101,
        cpu_count=lambda: capacity)
    owner.threading = SimpleNamespace(get_ident=threading.get_ident, active_count=lambda: 1)
    owner.resource = SimpleNamespace(RUSAGE_CHILDREN=1, RUSAGE_SELF=0,
        getrusage=lambda who: SimpleNamespace(ru_utime=0., ru_stime=0.))
    directory = Path(directory)
    output = directory/'runs'
    output.mkdir()
    task = {'id': 'fresh-task', 'protocol_revision': 5}
    roots = {'expected_lock_sha256': 'a'*64, 'expected_cumulative_charge_s': 1540.,
             'lock_path': str(directory/'lock.json')}
    root_path = directory/'entry-owner.json'
    root = {'schema': 'cf1-entry-owner-v1', 'policy': owner.POLICY,
        'nonce': 'independent-nonce', 'owner_pid': 101, 'output': str(output.resolve()),
        'roots': roots, 'task': task, 'entry_allocation_s': owner.ENTRY_S,
        'suffix_s': owner.SUFFIX_S, 'permit_lifetime_s': owner.PERMIT_S,
        'capacity_cpu_count': capacity, 'anchor': 100.}
    write(root_path, root)
    root_sha = q.sha(root_path)
    (directory/'entry-owner-attempt01').mkdir()
    write(directory/'entry-owner-attempt01/controller.json', {'root_sha256': root_sha,
        'nonce': root['nonce'], 'controller_pid': 211, 'owner_pid': 101})
    channel = SimpleNamespace(sendall=lambda raw: None)
    original_receive = owner._receive
    owner._receive = lambda *args: {'operation': 'ready', 'root_sha256': root_sha,
        'nonce': root['nonce'], 'controller_pid': 211}
    client = owner.EntryClient(channel, root_path=root_path,
        expected_root_sha256=root_sha, nonce=root['nonce'], roots=roots,
        policy=owner.POLICY, task=task, output=output)
    owner._receive = original_receive
    budget = {'carried_charge_s': 1538., 'freeze_charge_s': 2., 'tasks': []}
    q.append_ledger(output/'ledger.jsonl', {'event': 'carry_forward',
        'charged_cpu_s': 1538., 'freeze_charge_s': 2.})
    return SimpleNamespace(owner=owner, q=q, now=now, client=client, task=task,
        roots=roots, root=root, root_path=root_path, output=output, budget=budget)


def precharge(h):
    return h.client.precharge(h.output, policy=h.owner.POLICY, task=h.task,
        lock_sha256='a'*64, postfreeze_total_s=1540., budget_lock=h.budget)


def wrapper_charge(h, output, lock_sha='a'*64):
    root = ROOT/h.v5.NAMESPACE/'entry-owner.json'
    digest = h.q.sha(root)
    return {'event': 'supervisor_cpu', 'phase': 'whole_entry_precharge',
        'charged_cpu_s': 7.5, 'nonrefundable': True, 'policy': h.v5.POLICY,
        'task': h.v5.task_matrix()[0], 'output': str(Path(output).resolve()),
        'lock_sha256': lock_sha, 'owner_root': str(root),
        'owner_root_sha256': digest, 'root_sha256': digest,
        'controller_pid': os.getpid(), 'nonce': 'fake-independent-owner'}


def funding_roots(h, total):
    base = ROOT/h.v5.NAMESPACE
    roots = {'expected_cumulative_charge_s': total}
    for key, name, digest_key in (
            ('lock_path', 'lock.json', 'expected_lock_sha256'),
            ('freeze_receipt_path', 'freeze-attempt01/result.json', 'expected_freeze_receipt_sha256'),
            ('accounting_path', 'freeze-accounting.json', 'expected_accounting_sha256')):
        roots[key] = base/name
        roots[digest_key] = h.q.sha(base/name)
    return roots


class OwnerTests(unittest.TestCase):
    def test_live_guard_refuses_stale_status_owner_reserve_and_package_exhaustion(self):
        for damage in ('none', 'stale', 'owner-reserve', 'package'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                h = owner_harness(temporary)
                supervisor = h.owner.OwnerSupervisor.__new__(h.owner.OwnerSupervisor)
                supervisor.latest_status = {'controller_cpu_s': .2,
                    'controller_reaped_child_cpu_s': .1,
                    'controller_sample_monotonic': 100.2}
                supervisor.cpu0, supervisor.monitor0, supervisor.anchor = 0., 0., 100.
                supervisor.peak_cpu, supervisor.active_other_cpu, supervisor.capacity = .4, .1, 8
                supervisor.roots = {**h.roots,
                    'expected_cumulative_charge_s': 2600. if damage == 'package' else 1540.}
                supervisor.output, supervisor.task = str(h.output), h.task
                if damage == 'owner-reserve':
                    h.owner.time.process_time = lambda: 15.01
                now = 100.5 if damage == 'stale' else 100.2
                if damage == 'none':
                    result = supervisor._live_guard(now)
                    self.assertEqual(result['remaining_native_s'], 62.5)
                    self.assertEqual(result['retained_final_s'], 31.5)
                    self.assertEqual(result['status_age_s'], 0.)
                    self.assertLess(result['charged_cpu_s']+62.5+31.5, h.owner.PACKAGE_CAP)
                else:
                    with self.assertRaises(ValueError):
                        supervisor._live_guard(now)

    def test_runtime_status_keeps_owner_binding_and_monotone_sequence(self):
        with tempfile.TemporaryDirectory() as temporary:
            h = owner_harness(temporary)
            supervisor = h.owner.OwnerSupervisor.__new__(h.owner.OwnerSupervisor)
            supervisor.root_sha256, supervisor.nonce = h.client.root_sha256, h.client.nonce
            supervisor.policy, supervisor.task, supervisor.roots = h.owner.POLICY, h.task, h.roots
            supervisor.output = str(h.output.resolve())
            supervisor.gate_issued, supervisor.status_sequence = True, 0
            supervisor.latest_status = {'controller_cpu_s': .1,
                'controller_reaped_child_cpu_s': 0., 'controller_sample_monotonic': 100.1}
            status = {**h.client._binding(), 'operation': 'runtime_status', 'sequence': 1,
                'controller_cpu_s': .2, 'controller_reaped_child_cpu_s': .1,
                'controller_sample_monotonic': 100.2}
            for key, changed in (('nonce', 'wrong-owner'), ('sequence', 2),
                                 ('controller_cpu_s', 0.)):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    supervisor._accept_status({**status, key: changed}, SimpleNamespace(pid=211))
            supervisor._accept_status(status, SimpleNamespace(pid=211))
            self.assertEqual(supervisor.latest_status, status)
            self.assertEqual(supervisor.status_sequence, 1)
            with self.assertRaises(ValueError):
                supervisor._accept_status(status, SimpleNamespace(pid=211))

    def test_owner_fake_process_anchor_argv_ready_and_cleanup_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            h = owner_harness(temporary)
            folder = Path(temporary)/'separate-owner'
            folder.mkdir()
            events = []
            class Channel:
                def fileno(self): return 9
                def sendall(self, raw): events.append(('send', json.loads(raw)))
                def close(self): pass
            h.owner.socket = SimpleNamespace(socketpair=lambda: (Channel(), Channel()))
            h.owner.os = SimpleNamespace(getpid=lambda: 101, cpu_count=lambda: 8, environ={})
            h.owner.signal = SimpleNamespace(SIG_BLOCK=0, SIG_SETMASK=1, SIGTERM=15,
                SIGINT=2, pthread_sigmask=lambda *args: set(), signal=lambda *args: None)
            h.owner.secrets = SimpleNamespace(token_hex=lambda size: 'fresh-owner-nonce')
            h.q.THREAD_KEYS = ('OMP_NUM_THREADS',)
            h.q.stop_owned = lambda *args, **kwargs: {'group_absent': True,
                'cleanup_errors': [], 'returncode': 0, 'owned_pgids': [211]}
            proc = SimpleNamespace(pid=211, returncode=0, poll=lambda: 0, wait=lambda **kwargs: 0)
            def popen(command, **kwargs):
                self.assertTrue((folder/'entry-owner.json').is_file())
                self.assertFalse((folder/'entry-owner-attempt01/controller.json').exists())
                events.append(('popen', command, kwargs))
                return proc
            h.owner.subprocess = SimpleNamespace(Popen=popen)
            supervisor = h.owner.OwnerSupervisor(directory=folder/'entry-owner-attempt01',
                roots=h.roots, task=h.task, output=h.output)
            command = [h.owner.sys.executable, '-m', 'experiments.cf1_entry_repaired', 'run']
            with self.assertRaisesRegex(RuntimeError, 'Owned entry failed'):
                supervisor.run(command)
            receipt = h.q.read(folder/'entry-owner-attempt01/owner-receipt.json')
            root = h.q.read(folder/'entry-owner.json')
            runtime = events[0][1]
            self.assertEqual(root['controller_command'], command)
            self.assertEqual(runtime[:4], command)
            self.assertEqual(runtime[-8:], ['--owner-fd', '9', '--owner-root',
                str((folder/'entry-owner.json').resolve()), '--owner-root-sha256',
                h.q.sha(folder/'entry-owner.json'), '--owner-nonce', 'fresh-owner-nonce'])
            self.assertTrue(events[0][2]['start_new_session'])
            self.assertEqual(events[0][2]['pass_fds'], (9,))
            self.assertEqual(events[1][1]['operation'], 'ready')
            self.assertEqual(h.q.read(folder/'entry-owner-attempt01/controller.json')['runtime_command'], runtime)
            self.assertFalse(receipt['accounting_observations_complete'])
            self.assertIn('without complete entry handoff', receipt['failure']['error'])
            self.assertTrue(receipt['reconciliation_required'])
            self.assertFalse(receipt['entry_gate_issued'])

    def test_parent_fake_observations_bound_entry_and_capacity_scaled_suffix(self):
        for damage in ('none', 'overcap', 'missing-observation'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                h = owner_harness(temporary)
                precharge(h)
                supervisor = h.owner.OwnerSupervisor.__new__(h.owner.OwnerSupervisor)
                supervisor.directory = Path(temporary)/'entry-owner-attempt01'
                supervisor.policy, supervisor.task = h.owner.POLICY, h.task
                supervisor.output, supervisor.roots = str(h.output.resolve()), h.roots
                supervisor.root_sha256, supervisor.nonce = h.client.root_sha256, h.client.nonce
                supervisor.gate_issued, supervisor.anchor = False, 100.
                supervisor.cpu0, supervisor.monitor0, supervisor.peak_cpu = 0., 0., .2
                supervisor.capacity, supervisor.monitor_registrations = 8, 0
                def sample(*args, **kwargs):
                    if damage == 'missing-observation':
                        raise ValueError('Missing owned sample')
                    return 100.2, []
                supervisor._sample = sample
                request = {**h.client._binding(), 'operation': 'prelaunch',
                    'precharge_sha256': h.client.precharge_sha256,
                    'funding_sha256': stable({'charged_cpu_s': 1547.5}),
                    'controller_reaped_child_cpu_s': 0.,
                    'controller_cpu_s': 8. if damage == 'overcap' else .2,
                    'controller_sample_monotonic': 100.2, 'entry_helpers': []}
                proc = SimpleNamespace(pid=211)
                if damage == 'none':
                    response = supervisor._gate(request, proc)
                    permit = response['permit']
                    self.assertTrue(permit['observations_complete'])
                    self.assertLessEqual(permit['entry_bound_s'], 7.5)
                    self.assertLessEqual((permit['expires_monotonic']-permit['issued_monotonic'])
                        *(supervisor.capacity+2), h.owner.SUFFIX_S+1.e-12)
                    self.assertEqual(h.q.read(response['evidence_path']), permit)
                    with self.assertRaises(ValueError):
                        supervisor._gate(request, proc)
                else:
                    with self.assertRaises(ValueError):
                        supervisor._gate(request, proc)
                    self.assertFalse(supervisor.gate_issued)

    def test_precharge_is_exact_nonrefundable_once_and_real_resume_consumes_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            h = owner_harness(temporary)
            precharge(h)
            completed, total = h.q.resume_state(h.output, h.budget, 'a'*64)
            self.assertEqual((completed, total), ({}, 1547.5))
            events = h.q.ledger_events(h.output/'ledger.jsonl')
            self.assertEqual(len(events), 2)
            event = events[-1]
            self.assertEqual(event['phase'], 'whole_entry_precharge')
            self.assertTrue(event['nonrefundable'])
            self.assertEqual(event['charged_cpu_s'], 7.5)
            self.assertEqual(event['owner_root_sha256'], h.q.sha(h.root_path))
            before = (h.output/'ledger.jsonl').read_bytes()
            with self.assertRaises(ValueError):
                precharge(h)
            self.assertEqual((h.output/'ledger.jsonl').read_bytes(), before)

    def test_identity_rejects_changed_root_late_entry_and_unowned_controller(self):
        for damage in ('root', 'late', 'unowned'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                h = owner_harness(temporary)
                if damage == 'root':
                    h.root_path.write_text(h.root_path.read_text()+' ')
                elif damage == 'late':
                    h.now.value = 108.
                else:
                    record = h.q.read(Path(temporary)/'entry-owner-attempt01/controller.json')
                    record['controller_pid'] = 212
                    (Path(temporary)/'entry-owner-attempt01/controller.json').write_text(json.dumps(record))
                with self.assertRaises(ValueError):
                    precharge(h)
                self.assertEqual(len(h.q.ledger_events(h.output/'ledger.jsonl')), 1)

    def test_socket_message_unit_and_missing_response(self):
        owner = source('cf1_entry_owner', q=SimpleNamespace())
        left, right = socket.socketpair()
        try:
            left.setblocking(False)
            right.setblocking(False)
            owner._send(left, {'operation': 'unit', 'id': 1})
            self.assertEqual(owner._receive(right, owner.time.monotonic()+.1),
                             {'operation': 'unit', 'id': 1})
            left.close()
            with self.assertRaises(EOFError):
                owner._receive(right, owner.time.monotonic()+.1)
        finally:
            left.close()
            right.close()

    def test_entry_scope_blocks_unregistered_spawn_and_restores_on_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            h = owner_harness(temporary)
            calls = []
            monitor = SimpleNamespace(pid=313, poll=lambda: 0, returncode=0,
                                      communicate=lambda *args, **kwargs: (b'', b''))
            h.q.subprocess.Popen = lambda *args, **kwargs: calls.append((args, kwargs)) or monitor
            original = h.q.subprocess.Popen
            h.client._request = lambda value: {'allowed': True}
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                with h.client.entry_scope():
                    with self.assertRaises(ValueError):
                        with h.client.entry_scope():
                            self.fail('Nested owner scope entered')
                    with self.assertRaises(ValueError):
                        h.q.subprocess.Popen(['unregistered', 'child'])
                    self.assertIs(h.q.subprocess.Popen(list(h.owner._MONITOR_COMMANDS[0])), monitor)
                    self.assertEqual(len(calls), 1)
                    h.client.used = True
                    h.now.value = 108.
                    h.client._request = lambda value: self.fail('Post-handoff monitor requested entry permit')
                    self.assertIs(h.q.subprocess.Popen(list(h.owner._MONITOR_COMMANDS[0])), monitor)
                    with self.assertRaises(ValueError):
                        h.q.subprocess.Popen(['unregistered', 'post-handoff-child'])
                    raise RuntimeError('injected')
            self.assertIs(h.q.subprocess.Popen, original)
            self.assertFalse(h.client.in_scope)
            self.assertFalse(h.owner._GUARD_LOCK.locked())

    def test_missing_incomplete_overcap_and_changed_binding_permits_reject(self):
        for damage in ('none', 'missing', 'incomplete', 'overcap', 'unowned', 'binding', 'late'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                h = owner_harness(temporary)
                precharge(h)
                funding = {'charged_cpu_s': 1547.5}
                request = {**h.client._binding(), 'operation': 'prelaunch',
                    'precharge_sha256': h.client.precharge_sha256,
                    'funding_sha256': stable(funding), 'controller_reaped_child_cpu_s': 0.,
                    'controller_cpu_s': 0., 'controller_sample_monotonic': 100.2,
                    'entry_helpers': []}
                permit = {**request, 'allowed': True, 'observations_complete': True,
                    'unexpected_descendants': [], 'entry_bound_s': 1.,
                    'suffix_s': h.owner.SUFFIX_S, 'issued_monotonic': 100.2,
                    'expires_monotonic': 100.25}
                if damage == 'incomplete': permit['observations_complete'] = False
                elif damage == 'overcap': permit['entry_bound_s'] = 7.6
                elif damage == 'unowned': permit['controller_pid'] = 212
                elif damage == 'binding': permit['lock_sha256'] = 'b'*64
                elif damage == 'late': permit['expires_monotonic'] = 108.
                gate = Path(temporary)/'entry-owner-gate.json'
                h.q.write_new(gate, permit)
                response = {'allowed': damage != 'missing', 'permit': permit,
                    'evidence_path': str(gate), 'evidence_sha256': h.q.sha(gate)}
                h.owner._receive = lambda *args: response
                if damage == 'none':
                    self.assertEqual(h.client._permit(funding), permit)
                else:
                    with self.assertRaises(ValueError):
                        h.client._permit(funding)
                self.assertFalse(h.client.used)

    def test_actual_popen_guard_one_use_exact_command_and_final_expiry(self):
        for damage in ('none', 'expired', 'command', 'binding', 'permit'):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temporary:
                h = owner_harness(temporary)
                precharge(h)
                calls, funding_calls = [], []
                h.q.subprocess.Popen = lambda *args, **kwargs: calls.append((args, kwargs)) or 'fake-process'
                original = h.q.subprocess.Popen
                permit = {'expires_monotonic': 100.25}
                gate = Path(temporary)/'entry-owner-gate.json'
                h.q.write_new(gate, permit)
                h.client.gate_sha256 = h.q.sha(gate)
                h.client._permit = lambda funding: permit
                args = SimpleNamespace(lock=h.roots['lock_path'], output=str(h.output))
                folder = h.output/h.task['id']
                folder.mkdir()
                h.q.write_new(folder/'attempt.json', {'task': h.task,
                    'lock_sha256': 'a'*64, 'parent_monotonic': 100.21})
                command = [h.owner.sys.executable, *h.owner.WORKER_PREFIX, '--lock',
                    str(Path(args.lock).resolve()), '--output', str(folder.resolve()),
                    '--parent-pid', '211', '--ack-fd', '9']
                def delegate(*ignored):
                    if damage == 'expired': h.now.value = 100.3
                    elif damage == 'command': command[2] = 'experiments.cf1_small_mechanism_approved'
                    elif damage == 'binding': h.client.roots['expected_lock_sha256'] = 'b'*64
                    elif damage == 'permit': gate.write_text('{"changed": true}')
                    return h.q.subprocess.Popen(command, start_new_session=True, pass_fds=(9,))
                def funding():
                    funding_calls.append(True)
                    return {'charged_cpu_s': 1547.5}
                with h.client.entry_scope():
                    if damage == 'none':
                        self.assertEqual(h.client.launch_guard(args, h.task, h.output, 'a'*64,
                            delegate=delegate, funding_check=funding), 'fake-process')
                        self.assertEqual(len(calls), 1)
                        self.assertEqual(len(funding_calls), 2)
                        with self.assertRaises(ValueError):
                            h.client.launch_guard(args, h.task, h.output, 'a'*64,
                                delegate=delegate, funding_check=funding)
                    else:
                        with self.assertRaises(ValueError):
                            h.client.launch_guard(args, h.task, h.output, 'a'*64,
                                delegate=delegate, funding_check=funding)
                        self.assertFalse(calls)
                self.assertIs(h.q.subprocess.Popen, original)


class WrapperTests(unittest.TestCase):
    def test_fresh_singleton_and_closed_entrypoints(self):
        h = wrapper_harness()
        task, = h.v5.task_matrix([{'base_id': 50997, 'trips': 40}])
        bare = {key: value for key, value in task.items() if key != 'id'}
        self.assertEqual(bare, {'arm': 'cf1', 'base_id': 50997, 'trips': 40,
            'seed': 17, 'seconds': 60., 'fault': None, 'protocol_revision': 5})
        self.assertEqual(task['id'], stable(bare)[:20])
        self.assertNotEqual(task['id'], h.approved.task_matrix()[0]['id'])
        self.assertFalse(h.preflight.NATIVE_DISPATCH_CLEARED)
        for cases in ([], [{'base_id': 50999, 'trips': 80}],
                      [{'base_id': 50997, 'trips': 40}] * 2):
            with self.assertRaises(ValueError):
                h.v5.task_matrix(cases)
        with self.assertRaises(RuntimeError):
            h.v5.run(None)
        for name in ('freeze', 'worker'):
            args = SimpleNamespace(lock=str(ROOT/'research-20261023/old-lock.json'),
                                   output=str(ROOT/'research-20261023/old-output'))
            with self.subTest(entry=name), self.assertRaises(ValueError):
                getattr(h.v5, name)(args)

    def test_scoped_configuration_restores_exact_bindings_on_failure(self):
        h = wrapper_harness()
        snapshots = [(module, vars(module).copy()) for module in
                     (h.approved, h.adapter, h.worker, h.q)]
        original_lock = h.approved._CONFIG_LOCK
        with self.assertRaisesRegex(ValueError, 'injected'):
            with h.v5.revision5():
                self.assertTrue(original_lock.locked())
                self.assertEqual(h.adapter.POLICY, h.v5.POLICY)
                self.assertEqual((h.adapter.PACKAGE_START, h.adapter.PACKAGE_LIMIT,
                                  h.adapter.PACKAGE_CAP),
                    (2426.723449631016, 275., 2701.723449631016))
                self.assertEqual(h.adapter.FREEZE_ELAPSED_LIMIT_S, 17.5)
                self.assertEqual((h.adapter.ANALYSIS_FINAL_RESERVE_S,
                    h.adapter.SUPERVISION_RESERVE_S), (30., 45.))
                self.assertEqual((h.q.CEILING, h.q.DISPATCH_STOP,
                                  h.q.SHUTDOWN_RESERVE), (3000., 2820., 180.))
                self.assertEqual(h.adapter.WORKER_ARGV_PREFIX,
                                 ('-m', 'experiments.cf1_entry_repaired', 'worker'))
                self.assertEqual(h.worker.task_matrix(), h.v5.task_matrix())
                self.assertEqual(h.approved.ACK_OBSERVATION,
                                 'controller-ack-observation-v5.json')
                with self.assertRaises(RuntimeError):
                    with h.v5.revision5():
                        self.fail('Nested prospective context entered')
                denied = []
                def cross_thread():
                    denied.append(h.approved._CONFIG_LOCK.acquire(blocking=False))
                thread = threading.Thread(target=cross_thread)
                thread.start()
                thread.join()
                self.assertEqual(denied, [False])
                raise ValueError('injected')
        for module, before in snapshots:
            self.assertEqual(vars(module), before)
        self.assertFalse(original_lock.locked())
        with h.v5.revision5():
            self.assertEqual(h.adapter.FREEZE_ELAPSED_LIMIT_S, 17.5)
        self.assertEqual(h.adapter.FREEZE_ELAPSED_LIMIT_S, 10.)

    def test_actual_freeze_consumer_obeys_only_its_installed_elapsed_limit(self):
        # Inert metadata validates the actual branch, not byte/OS qualification.
        q = SimpleNamespace(launch=lambda *args: None, RSS_LIMIT=5*1024**3,
            finite=lambda value, minimum=0.: type(value) in (int, float)
                and math.isfinite(value) and value >= minimum,
            sha=lambda path: 'digest', verify_hashes=lambda inventory: None)
        adapter = source('comparison_native_preflight', q=q)
        self.assertEqual(adapter.FREEZE_ELAPSED_LIMIT_S, 10.)
        lock = {'carried_charge_s': 1300., 'prior_accounting_sha256': 'prior',
                'sources': {'inert-source': 'digest'}}
        charged = 17.5+.2
        cumulative = lock['carried_charge_s']+charged
        receipt = {'policy': adapter.POLICY, 'phase': 'comparison_native_freeze',
            'passed': True, 'failure': None, 'monitor_failure': None, 'source_changes': [],
            'returncode': 0, 'secondary_errors': [], 'primary_failure': None,
            'accounting_observations_complete': True, 'accounting_unresolved': False,
            'charge_is_lower_bound': False, 'artifact_hashes': {'stdout.log': 'digest'},
            'lock_sha256': 'digest', 'prior_accounting_sha256': 'prior',
            'source_hashes': lock['sources'], 'termination': {'group_absent': True,
                'reaped': True, 'owned_pgids': [211], 'surviving_pgids': [],
                'cleanup_errors': [], 'probe_diagnostics': []},
            'charged_cpu_s': charged, 'supervisor_cpu_s': .2,
            'charged_allocation_s': 17.5, 'elapsed_allocation_s': 17.5,
            'sampled_peak_rss_bytes': 0, 'cumulative_qualification_charge_s': cumulative,
            'stdout_sha256': 'digest', 'stderr_sha256': 'digest'}
        q.read = lambda path: receipt
        args = (lock, '/inert-v5b-freeze/lock.json', '/inert-v5b-freeze/result.json')
        with self.assertRaises(ValueError):
            adapter.freeze_accounting(*args)
        adapter.FREEZE_ELAPSED_LIMIT_S = 17.5
        self.assertEqual(adapter.freeze_accounting(*args),
                         {**lock, 'freeze_charge_s': cumulative-lock['carried_charge_s']})
        receipt['elapsed_allocation_s'] = 17.500001
        with self.assertRaises(ValueError):
            adapter.freeze_accounting(*args)

    def test_original_lock_contention_and_partial_configuration_restore(self):
        h = wrapper_harness()
        before = vars(h.approved).copy()
        original = h.approved._CONFIG_LOCK
        original.acquire()
        try:
            with self.assertRaises(RuntimeError):
                with h.v5.revision5():
                    self.fail('Busy historical configuration entered')
            self.assertEqual(vars(h.approved), before)
        finally:
            original.release()
        h.adapter._LOCK.acquire()
        try:
            with self.assertRaises(RuntimeError):
                with h.v5.revision5():
                    self.fail('Busy supervision entered')
            self.assertEqual(vars(h.approved), before)
        finally:
            h.adapter._LOCK.release()

    def test_original_ack_observer_keeps_v5_identity_and_complete_read_rule(self):
        h = wrapper_harness()
        h.approved.time = SimpleNamespace(monotonic=lambda: 159.)
        task, = h.v5.task_matrix()
        folder = Path('/inert-v5')/task['id']
        h.store[str(folder/'attempt.json')] = {'policy': h.v5.POLICY,
            'task': task, 'lock_sha256': 'independent-lock',
            'parent_monotonic': 100., 'deadline': 160.}
        ack = {'task_id': task['id'], 'lock_sha256': 'independent-lock',
               'parent_monotonic': 100., 'completion_monotonic': 158.}
        raw = h.approved._ack_bytes(ack)
        item = {'folder': folder, 'task': task, 'anchor': 100.,
                'ack_bytes': b'', 'acknowledgment': None,
                'primary_reason': 'retained', 'secondary_errors': ['retained']}
        def receive(item):
            if not item['ack_bytes']:
                item['ack_bytes'] = raw[:4]
            elif item['acknowledgment'] is None:
                item.update(ack_bytes=raw, acknowledgment=ack)
        h.q.receive_ack = receive
        with h.v5.revision5():
            h.q.receive_ack(item)
            self.assertFalse(h.writes)
            h.q.receive_ack(item)
            h.q.receive_ack(item)
        self.assertEqual(len(h.writes), 1)
        path, observation = h.writes[0]
        self.assertEqual(Path(path).name, 'controller-ack-observation-v5.json')
        self.assertEqual(observation['policy'], h.v5.POLICY)
        self.assertEqual(observation['controller_observed_monotonic'], 159.)
        self.assertEqual(item['primary_reason'], 'retained')
        self.assertEqual(item['secondary_errors'], ['retained'])

    def test_transport_analysis_uses_original_v4_function_and_v5_inventory(self):
        h = wrapper_harness()
        base = ROOT/h.v5.NAMESPACE
        args = SimpleNamespace(lock=str(base/'lock.json'), report=str(base/'report.json'),
                               output=str(base/'runs'))
        task, = h.v5.task_matrix()
        h.store[args.lock] = {'tasks': [task]}
        original_analyze = h.approved.analyze
        original_transport = h.approved._transport_evidence
        def analyze(args):
            self.assertEqual((h.q.CEILING, h.q.DISPATCH_STOP,
                              h.q.SHUTDOWN_RESERVE), (3000., 2820., 180.))
            self.assertEqual(h.adapter.FREEZE_ELAPSED_LIMIT_S, 17.5)
            h.q.write_new(args.report, {'passed': True, 'issues': [],
                                      'rows': [{'task': task, 'issues': []}]})
        h.adapter.analyze = analyze
        writer = h.q.write_new
        report = h.v5.analyze(args)
        self.assertFalse(report['passed'])
        self.assertEqual(report['ack_transport'][0]['status'], 'timing_unestablished')
        self.assertIn(task['id'] + ':ack_transport_timing_unestablished', report['issues'])
        self.assertIs(h.approved.analyze, original_analyze)
        self.assertIs(h.approved._transport_evidence, original_transport)
        self.assertIs(h.q.write_new, writer)
        def failed_analyze(args):
            self.assertEqual((h.q.CEILING, h.q.DISPATCH_STOP,
                              h.q.SHUTDOWN_RESERVE), (3000., 2820., 180.))
            self.assertEqual(h.adapter.FREEZE_ELAPSED_LIMIT_S, 17.5)
            raise ValueError('analysis injected')
        h.adapter.analyze = failed_analyze
        with self.assertRaisesRegex(ValueError, 'analysis injected'):
            h.v5.analyze(args)
        self.assertIs(h.q.write_new, writer)
        self.assertEqual((h.q.CEILING, h.q.DISPATCH_STOP,
                          h.q.SHUTDOWN_RESERVE), (1800., 1620., 180.))
        self.assertEqual(h.adapter.FREEZE_ELAPSED_LIMIT_S, 10.)

    def test_source_gate_requires_new_execution_and_complete_current_closure(self):
        h = wrapper_harness()
        v5 = h.v5
        directory = ROOT/v5.CHECK_NAMESPACE
        dependencies = ('src/experiments/cf1_preparation_preflight.py',
            'src/tests/test_cf1_preparation_preflight.py',
            'src/experiments/cf1_small_mechanism_preflight.py',
            'src/tests/test_cf1_small_mechanism_preflight.py')
        hashes = {str(ROOT/name): h.q.sha(ROOT/name) for name in dependencies}
        hashes.update(h.q.campaign.sources())
        hashes.update({str(ROOT/'src/tests'/name): h.q.sha(ROOT/'src/tests'/name)
            for name in (*v5.QUALIFIED_TEST_DEPENDENCIES, 'test_cf1_entry_repaired.py')})
        command = v5.check_command()
        attempt = {'attempt_id': 'attempt07', 'revision': 5, 'policy': v5.POLICY,
            'command': command, 'command_sha256': stable(command),
            'executed_tests': ['test_cf1_entry_repaired.py'], 'source_hashes': hashes}
        result = {'attempt_id': 'attempt07', 'revision': 5, 'policy': v5.POLICY,
            'command': command, 'command_sha256': stable(command),
            'executed_tests': ['test_cf1_entry_repaired.py']}
        h.store[str(directory/'attempt.json')] = attempt
        h.store[str(directory/'result.json')] = result
        self.assertEqual(v5.checked_sources(directory), {'inherited': 'qualified-dependency'})
        for path in list(hashes):
            original = hashes.pop(path)
            with self.subTest(missing=path), self.assertRaises(ValueError):
                v5.checked_sources(directory)
            hashes[path] = original
        for record, key, value in (
                (attempt, 'attempt_id', 'attempt06'), (attempt, 'revision', 4),
                (attempt, 'policy', h.approved.POLICY),
                (attempt, 'command', command+['src/tests/test_constructive_controls.py']),
                (attempt, 'command_sha256', 'changed'),
                (attempt, 'executed_tests', ['test_cf1_small_mechanism_approved.py']),
                (result, 'attempt_id', 'attempt06'), (result, 'revision', 4),
                (result, 'policy', h.approved.POLICY)):
            original = record[key]
            record[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                v5.checked_sources(directory)
            record[key] = original
        for other in (ROOT/'research-20261023/cf1-small-approved-checks/attempt01',
                      directory.parent/'attempt01', directory.parent/'attempt03',
                      directory.parent/'attempt04', directory.parent/'attempt05',
                      directory.parent/'attempt06'):
            with self.assertRaises(ValueError):
                v5.checked_sources(other)

    def test_prepare_precharge_exit_then_run_and_guard_restore(self):
        h = wrapper_harness()
        base = ROOT/h.v5.NAMESPACE
        args = SimpleNamespace(lock=str(base/'lock.json'), output=str(base/'runs'),
                               freeze_receipt=str(base/'freeze-attempt01/result.json'))
        roots = {'lock_path': args.lock, 'freeze_receipt_path': args.freeze_receipt,
            'accounting_path': str(base/'freeze-accounting.json'),
            'expected_lock_sha256': 'a'*64, 'expected_freeze_receipt_sha256': 'b'*64,
            'expected_accounting_sha256': 'c'*64,
            'expected_cumulative_charge_s': 1540., 'expected_policy': h.v5.POLICY}
        h.store[args.lock] = {'carried_charge_s': 1538., 'freeze_charge_s': 2., 'tasks': []}
        h.adapter.freeze_accounting = lambda *args: h.store[str(base/'lock.json')]
        ledger = []
        h.q.ledger_events = lambda path: deepcopy(ledger)
        h.q.resume_state = lambda *args: ({}, 1547.5)
        original = lambda *args: h.events.append('fake-worker')
        h.adapter.launch = original
        class Owner:
            @contextmanager
            def entry_scope(self):
                yield self
            def precharge(self, output, **bindings):
                h.events.append('precharge')
                ledger.append(wrapper_charge(h, output))
                self.bindings = bindings
                self.output = output
            def launch_guard(self, *args, delegate, funding_check):
                h.events.append('guard')
                self.delegate = delegate
                return delegate(*args)
        owner = Owner()
        def run(args):
            self.assertEqual(h.events, ['bound-enter', 'prepare', 'precharge', 'bound-exit'])
            self.assertFalse(h.adapter._LOCK.locked())
            self.assertEqual(h.adapter.WORKER_ARGV_PREFIX, h.v5.WORKER_ARGV_PREFIX)
            h.events.append('run')
            h.adapter.launch(args, h.v5.task_matrix()[0], args.output, 'a'*64)
            return {'fake': True}
        h.adapter.run = run
        self.assertEqual(h.v5.run_prepared(args, roots=roots, owner_gate=owner), {'fake': True})
        self.assertEqual(h.events[-3:], ['run', 'guard', 'fake-worker'])
        self.assertIs(owner.delegate, original)
        self.assertEqual(owner.bindings['postfreeze_total_s'], 1540.)
        self.assertEqual(owner.bindings['policy'], h.v5.POLICY)
        self.assertIs(h.adapter.launch, original)
        h.events.clear()
        ledger.clear()
        def failed(output, **roots):
            h.events.append('partial-publication-retained')
            raise OSError('preparation injected')
        h.v5.prepare_new_output = failed
        with self.assertRaisesRegex(OSError, 'preparation injected'):
            h.v5.run_prepared(args, roots=roots, owner_gate=owner)
        self.assertEqual(h.events,
            ['bound-enter', 'partial-publication-retained', 'bound-exit'])
        self.assertIs(h.adapter.launch, original)
        h.v5.prepare_new_output = lambda *args, **kwargs: None
        h.adapter.run = lambda args: (_ for _ in ()).throw(ValueError('run injected'))
        with self.assertRaisesRegex(ValueError, 'run injected'):
            h.v5.run_prepared(args, roots=roots, owner_gate=owner)
        self.assertIs(h.adapter.launch, original)

    def test_exact_path_roots_reject_historical_and_substitute_metadata(self):
        h = wrapper_harness()
        base = ROOT/h.v5.NAMESPACE
        args = SimpleNamespace(lock=base/'lock.json', output=base/'runs',
                               freeze_receipt=base/'freeze-attempt01/result.json')
        roots = {'lock_path': args.lock, 'freeze_receipt_path': args.freeze_receipt,
            'accounting_path': base/'freeze-accounting.json',
            'expected_lock_sha256': 'a'*64, 'expected_freeze_receipt_sha256': 'b'*64,
            'expected_accounting_sha256': 'c'*64,
            'expected_cumulative_charge_s': 1540., 'expected_policy': h.v5.POLICY}
        self.assertEqual(h.v5._roots(args, roots)['lock_path'], args.lock.resolve())
        for key, replacement in (
                ('lock_path', ROOT/'research-20261023/cf1-small-approved-v4/lock.json'),
                ('lock_path', base/'alternate-lock.json'),
                ('freeze_receipt_path', base/'freeze-attempt02/result.json'),
                ('accounting_path', base/'self-described-accounting.json'),
                ('expected_policy', h.approved.POLICY)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                h.v5._roots(args, {**roots, key: replacement})
        for key in roots:
            bad = roots.copy()
            bad.pop(key)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                h.v5._roots(args, bad)
        with self.assertRaises(ValueError):
            h.v5._roots(SimpleNamespace(**{**vars(args), 'output': base/'runs2'}), roots)

    def test_live_funding_rechecks_real_ledger_and_exact_launch_intent(self):
        h = wrapper_harness()
        real = selected_recovery_functions()
        h.q.ledger_events, h.q.resume_state = real.ledger_events, real.resume_state
        h.q._monitor_child_cpu_s = 0.
        h.adapter.OUTER_S = 62.5
        h.q.CEILING, h.q.DISPATCH_STOP, h.q.SHUTDOWN_RESERVE = 3000., 2820., 180.
        h.v5.time = SimpleNamespace(process_time=lambda: 10.)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            ledger = output/'ledger.jsonl'
            real.append_ledger(ledger, {'event': 'carry_forward',
                'charged_cpu_s': 1538., 'freeze_charge_s': 2.})
            prefix = real.ledger_events(ledger)
            roots = funding_roots(h, 1540.)
            real.append_ledger(ledger, wrapper_charge(h, output, roots['expected_lock_sha256']))
            budget = {'carried_charge_s': 1538., 'freeze_charge_s': 2., 'tasks': []}
            h.v5._validate_precharge(output, prefix, budget, roots)
            state = {}
            task, = h.v5.task_matrix()
            evidence = h.v5._funding_check(output, budget, roots, task, 10., state)
            self.assertEqual(evidence['charged_cpu_s'], 1547.5)
            self.assertEqual(state['total'], real.resume_state(output, budget, roots['expected_lock_sha256'])[1])
            real.append_ledger(ledger, {'event': 'launch', 'task_id': task['id'],
                                        'parent_monotonic': 100.})
            self.assertEqual(h.v5._funding_check(output, budget, roots, task, 10., state), evidence)
            with self.assertRaises(ValueError):
                real.resume_state(output, budget, 'a'*64)
            real.append_ledger(ledger, {'event': 'supervisor_cpu', 'charged_cpu_s': 0.})
            with self.assertRaises(ValueError):
                h.v5._funding_check(output, budget, roots, task, 10., state)

    def test_duplicate_missing_precharge_and_unfunded_entry_stop(self):
        h = wrapper_harness()
        real = selected_recovery_functions()
        h.q.ledger_events, h.q.resume_state = real.ledger_events, real.resume_state
        h.q._monitor_child_cpu_s = 0.
        h.adapter.OUTER_S = 62.5
        h.q.CEILING, h.q.DISPATCH_STOP, h.q.SHUTDOWN_RESERVE = 3000., 2820., 180.
        h.v5.time = SimpleNamespace(process_time=lambda: 10.)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            ledger = output/'ledger.jsonl'
            real.append_ledger(ledger, {'event': 'carry_forward',
                'charged_cpu_s': 2580., 'freeze_charge_s': 2.})
            prefix = real.ledger_events(ledger)
            roots = funding_roots(h, 2582.)
            budget = {'carried_charge_s': 2580., 'freeze_charge_s': 2., 'tasks': []}
            with self.assertRaises(ValueError):
                h.v5._validate_precharge(output, prefix, budget, roots)
            real.append_ledger(ledger, wrapper_charge(h, output, roots['expected_lock_sha256']))
            h.v5._validate_precharge(output, prefix, budget, roots)
            with self.assertRaisesRegex(RuntimeError, 'reservation exhausted'):
                h.v5._funding_check(output, budget, roots, h.v5.task_matrix()[0], 10., {})
            real.append_ledger(ledger, {'event': 'supervisor_cpu', 'charged_cpu_s': 7.5})
            with self.assertRaises(ValueError):
                h.v5._validate_precharge(output, prefix, budget, roots)



