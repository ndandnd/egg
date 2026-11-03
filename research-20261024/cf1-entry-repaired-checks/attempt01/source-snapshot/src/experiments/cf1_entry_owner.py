"""Owning parent and one-use pre-native handoff for the prospective CF1 v5.

Source only until separately reviewed. The ps monitor has the same trusted,
frozen-source/registered-spawn assumption as q: it is not an OS containment
boundary and cannot certify hostile fork-and-escape code. No import starts work.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import resource
import secrets
import select
import signal
import socket
import subprocess
import sys
import threading
import time

from experiments import recovery_qualification as q

ENTRY_S = 7.5
SUFFIX_S = 2.5
PERMIT_S = .1
MAX_MESSAGE = 32768
POLICY = 'cf1-entry-repaired-v5'
WORKER_PREFIX = ('-m', 'experiments.cf1_entry_repaired', 'worker')
PACKAGE_CAP = 1527.8351450899538+175.
HARD_CEILING, DISPATCH_STOP, SHUTDOWN_RESERVE = 1920., 1740., 180.
ANALYSIS_FINAL_S, CLEANUP_S, OWNER_CPU_MAX_S = 30., 1.5, 15.
_GUARD_LOCK = threading.Lock()
_MONITOR_COMMANDS = (('ps', '-axo', 'pid=,ppid=,pgid=,rss=,time='),
                     ('/usr/bin/memory_pressure', '-Q'))


def _canonical(path):
    return str(Path(path).resolve())


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _send(channel, value):
    raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()+b'\n'
    _require(len(raw) <= MAX_MESSAGE, 'Entry control message too large')
    channel.sendall(raw)


def _receive(channel, deadline):
    # All handshakes are strictly request/response; no pipelining is accepted.
    raw = b''
    while not raw.endswith(b'\n'):
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Entry owner handshake expired')
        channel.settimeout(remaining)
        part = channel.recv(MAX_MESSAGE-len(raw)+1)
        if not part:
            raise EOFError('Entry owner channel closed')
        raw += part
        _require(len(raw) <= MAX_MESSAGE, 'Oversized entry owner response')
        _require(b'\n' not in raw[:-1], 'Pipelined/trailing entry owner message')
    value = json.loads(raw)
    _require(type(value) is dict, 'Entry owner response must be an object')
    return value


class EntryClient:
    """Child side. Roots must be retained independently by the owning parent."""

    def __init__(self, channel, *, root_path, expected_root_sha256, nonce,
                 roots, policy, task, output):
        self.channel = channel
        self.root_path = Path(root_path).resolve(strict=True)
        self.root_sha256 = expected_root_sha256
        self.nonce = nonce
        self.roots = deepcopy(roots)
        self.policy, self.task, self.output = policy, deepcopy(task), _canonical(output)
        self.charged = False
        self.used = False
        self.owner_thread = threading.get_ident()
        self.in_scope = False
        self.worker_creation = False
        self.entry_helpers = []
        self.status_sequence = 0
        self.root = q.read(self.root_path)
        ready = _receive(self.channel, min(time.monotonic()+.3,
                                          self.root['anchor']+ENTRY_S))
        _require(ready == {'operation': 'ready', 'root_sha256': self.root_sha256,
                           'nonce': self.nonce, 'controller_pid': os.getpid()},
                 'Missing initial owning parent handoff')
        self._identity()

    def _identity(self, *, check_time=True):
        root = self.root
        _require(threading.get_ident() == self.owner_thread
                 and threading.active_count() == 1, 'Entry gate crossed threads')
        _require(q.sha(self.root_path) == self.root_sha256
                 and q.read(self.root_path) == root, 'Entry owner root changed')
        _require(root.get('schema') == 'cf1-entry-owner-v1'
                 and root.get('policy') == self.policy == POLICY
                 and root.get('nonce') == self.nonce
                 and root.get('owner_pid') == os.getppid()
                 and root.get('output') == self.output
                 and root.get('roots') == self.roots
                 and root.get('task') == self.task
                 and root.get('entry_allocation_s') == ENTRY_S
                 and root.get('suffix_s') == SUFFIX_S
                 and root.get('permit_lifetime_s') == PERMIT_S
                 and root.get('capacity_cpu_count') == os.cpu_count()
                 and q.finite(root.get('anchor')),
                 'Entry owner/root/nonce/task/path binding differs')
        spawned = q.read(self.root_path.parent/'entry-owner-attempt01'/'controller.json')
        _require(spawned.get('root_sha256') == self.root_sha256
                 and spawned.get('nonce') == self.nonce
                 and spawned.get('controller_pid') == os.getpid()
                 and spawned.get('owner_pid') == os.getppid(),
                 'Controller is not the independently owned child')
        _require(not check_time or time.monotonic() <= root['anchor']+ENTRY_S,
                 'Whole-entry provision expired')

    def _binding(self):
        return {'root_sha256': self.root_sha256, 'nonce': self.nonce,
                'controller_pid': os.getpid(), 'policy': self.policy,
                'task': self.task, 'output': self.output,
                'lock_sha256': self.roots['expected_lock_sha256']}

    def _request(self, value, timeout=.3):
        _send(self.channel, {**self._binding(), **value})
        return _receive(self.channel, min(time.monotonic()+timeout,
                                         self.root['anchor']+ENTRY_S))

    @contextmanager
    def entry_scope(self):
        """Register the only pre-native child channels, restoring Popen on exit."""
        self._identity()
        _require(not self.in_scope and _GUARD_LOCK.acquire(blocking=False),
                 'Entry spawn scope nested or concurrently owned')
        original = q.subprocess.Popen
        self.in_scope = True
        try:
            def registered(command, *positional, **kwargs):
                if self.worker_creation:
                    return original(command, *positional, **kwargs)
                self._identity(check_time=not self.used)
                _require(type(command) in (list, tuple)
                         and tuple(command) in _MONITOR_COMMANDS
                         and not positional and not kwargs.get('shell', False)
                         and not kwargs.get('start_new_session', False)
                         and kwargs.get('preexec_fn') is None,
                         'Unregistered pre-native subprocess is forbidden')
                if self.used:
                    # Native supervision owns these fixed monitor commands;
                    # consumed entry permits cannot create another worker.
                    proc = original(command, *positional, **kwargs)
                    communicate = proc.communicate
                    reported = False
                    def completed(*args, **kw):
                        nonlocal reported
                        result = communicate(*args, **kw)
                        if not reported:
                            _require(proc.poll() is not None, 'Runtime monitor not reaped')
                            self._status()
                            reported = True
                        return result
                    proc.communicate = completed
                    return proc
                reply = self._request({'operation': 'monitor', 'command': list(command)})
                _require(reply.get('allowed') is True, 'Owner denied monitor subprocess')
                # q.monitor_command waits/reaps synchronously; report cumulative
                # waited child CPU at the final handoff, independently sampled by owner.
                helper = original(command, *positional, **kwargs)
                self.entry_helpers.append(helper)
                return helper
            q.subprocess.Popen = registered
            yield self
        finally:
            q.subprocess.Popen = original
            self.in_scope = False
            _GUARD_LOCK.release()

    def _status(self):
        self._identity(check_time=False)
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.status_sequence += 1
        self.channel.settimeout(.1)
        _send(self.channel, {**self._binding(), 'operation': 'runtime_status',
                            'sequence': self.status_sequence,
                            'controller_cpu_s': own.ru_utime+own.ru_stime,
                            'controller_reaped_child_cpu_s': children.ru_utime+children.ru_stime,
                            'controller_sample_monotonic': time.monotonic()})

    def precharge(self, output, *, policy, task, lock_sha256,
                  postfreeze_total_s, budget_lock):
        self._identity()
        _require(not self.charged and not self.used, 'Entry precharge is one-use')
        _require(_canonical(output) == self.output and policy == self.policy
                 and task == self.task
                 and lock_sha256 == self.roots['expected_lock_sha256']
                 and postfreeze_total_s == self.roots['expected_cumulative_charge_s'],
                 'Entry precharge changed independently retained roots')
        events = q.ledger_events(Path(output)/'ledger.jsonl')
        _require(not any(event.get('phase') == 'whole_entry_precharge'
                         or event.get('owner_root_sha256') == self.root_sha256
                         or event.get('event') == 'launch' for event in events),
                 'Existing precharge/launch blocks entry reuse')
        completed, total = q.resume_state(output, budget_lock, lock_sha256)
        _require(not completed and total == postfreeze_total_s,
                 'Prepared real resume differs from postfreeze total')
        event = {'event': 'supervisor_cpu', 'phase': 'whole_entry_precharge',
                 'charged_cpu_s': ENTRY_S, 'nonrefundable': True,
                 'owner_root': str(self.root_path),
                 'owner_root_sha256': self.root_sha256, **self._binding()}
        q.append_ledger(Path(output)/'ledger.jsonl', event)
        after = q.ledger_events(Path(output)/'ledger.jsonl')
        _require(len(after) == len(events)+1
                 and all(after[-1].get(key) == value for key, value in event.items()),
                 'Entry charge durable readback differs')
        completed, total = q.resume_state(output, budget_lock, lock_sha256)
        _require(not completed and total == postfreeze_total_s+ENTRY_S,
                 'Real resume did not consume exactly one full entry precharge')
        self.precharge_sha256 = after[-1]['sha256']
        self.charged = True

    def _permit(self, funding):
        self._identity()
        _require(self.charged and not self.used, 'Missing or consumed entry precharge')
        waited = resource.getrusage(resource.RUSAGE_CHILDREN)
        own = resource.getrusage(resource.RUSAGE_SELF)
        _require(all(proc.poll() is not None and proc.returncode is not None
                     for proc in self.entry_helpers), 'Entry helper remains live/unreaped')
        request = {**self._binding(), 'operation': 'prelaunch',
                   'precharge_sha256': self.precharge_sha256,
                   'funding_sha256': q.stable(funding),
                   'controller_reaped_child_cpu_s': waited.ru_utime+waited.ru_stime,
                   'controller_cpu_s': own.ru_utime+own.ru_stime,
                   'controller_sample_monotonic': time.monotonic(),
                   'entry_helpers': [{'pid': proc.pid, 'returncode': proc.returncode,
                                      'reaped': True} for proc in self.entry_helpers]}
        _send(self.channel, request)
        response = _receive(self.channel, min(time.monotonic()+.3,
                                             self.root['anchor']+ENTRY_S))
        _require(response.get('allowed') is True, 'Owning parent denied entry: '+str(response))
        evidence_path = Path(response['evidence_path']).resolve(strict=True)
        _require(evidence_path == self.root_path.parent/'entry-owner-gate.json'
                 and q.sha(evidence_path) == response.get('evidence_sha256'),
                 'Entry permit evidence escaped or changed')
        permit = q.read(evidence_path)
        self.gate_sha256 = response['evidence_sha256']
        _require(permit == response.get('permit'), 'Entry permit readback differs')
        _require(all(permit.get(key) == value for key, value in request.items())
                 and permit.get('allowed') is True
                 and permit.get('observations_complete') is True
                 and permit.get('unexpected_descendants') == []
                 and q.finite(permit.get('entry_bound_s'))
                 and permit['entry_bound_s'] <= ENTRY_S
                 and permit.get('suffix_s') == SUFFIX_S
                 and q.finite(permit.get('issued_monotonic'), self.root['anchor'])
                 and q.finite(permit.get('expires_monotonic'), permit['issued_monotonic'])
                 and permit['expires_monotonic'] <= min(
                     permit['issued_monotonic']+PERMIT_S, self.root['anchor']+ENTRY_S),
                 'Missing/incomplete/over-cap owning parent evidence')
        return permit

    def launch_guard(self, args, task, output, locksha, *, delegate, funding_check):
        self._identity()
        _require(self.in_scope and self.charged and not self.used
                 and task == self.task and _canonical(output) == self.output
                 and locksha == self.roots['expected_lock_sha256']
                 and _canonical(args.lock) == _canonical(self.roots['lock_path'])
                 and _canonical(args.output) == self.output,
                 'Entry launch identity differs')
        original = q.subprocess.Popen
        called = False
        try:
            funding = funding_check()
            _require(type(funding) is dict and funding, 'Missing prelaunch funding readback')
            permit = self._permit(funding)

            def popen(command, *positional, **kwargs):
                nonlocal called
                self._identity()
                _require(not called and not self.used, 'Entry worker creation is one-use')
                expected = [sys.executable, *WORKER_PREFIX, '--lock',
                            _canonical(args.lock), '--output',
                            _canonical(Path(output)/task['id']), '--parent-pid',
                            str(os.getpid()), '--ack-fd']
                _require(type(command) in (tuple, list)
                         and not positional and not kwargs.get('shell', False)
                         and kwargs.get('preexec_fn') is None
                         and list(command[:-1]) == expected
                         and str(command[-1]).isdigit()
                         and kwargs.get('start_new_session') is True
                         and kwargs.get('pass_fds') == (int(command[-1]),),
                         'Only the exact v5 worker command is allowed')
                attempt = q.read(Path(output)/task['id']/'attempt.json')
                _require(attempt.get('task') == task
                         and attempt.get('lock_sha256') == locksha
                         and q.finite(attempt.get('parent_monotonic')),
                         'Original native clock anchor missing before final Popen')
                final_funding = funding_check()
                _require(type(final_funding) is dict and final_funding,
                         'Final funding readback missing')
                gate_path = self.root_path.parent/'entry-owner-gate.json'
                _require(q.sha(gate_path) == self.gate_sha256
                         and q.read(gate_path) == permit, 'Final entry permit changed')
                _require(time.monotonic() <= permit['expires_monotonic'],
                         'Entry permit expired before actual worker Popen')
                # The native q anchor is already running; suffix overlap earns no credit.
                called = self.used = True
                self.worker_creation = True
                try:
                    return original(command, *positional, **kwargs)
                finally:
                    self.worker_creation = False

            q.subprocess.Popen = popen
            return delegate(args, task, output, locksha)
        finally:
            q.subprocess.Popen = original


class OwnerSupervisor:
    """Real external owner. Construct from independent freeze/launch bindings.

    run() retains cleanup and accounting even when the child never handshakes.
    The caller must separately authorize a frozen command before invoking run.
    """

    def __init__(self, *, directory, roots, task, output, policy=POLICY):
        self.directory = Path(directory).resolve()
        self.roots, self.task = deepcopy(roots), deepcopy(task)
        self.output, self.policy = _canonical(output), policy
        _require(policy == POLICY, 'Unexpected entry policy')

    def _sample(self, proc, deadline, *, allow_worker=False):
        table, free = q.monitor_sample(deadline)
        now = time.monotonic()
        if proc.pid not in table and allow_worker and proc.poll() is not None:
            # A normal exit can race the complete OS sample. It proves no live
            # sample; the caller moves immediately to waited terminal accounting.
            return now, []
        _require(proc.pid in table, 'Owned controller missing from complete live sample')
        row = table[proc.pid]
        _require(row['ppid'] == os.getpid() and row['pgid'] == proc.pid,
                 'Controller parent/session identity changed')
        descendants = {proc.pid}
        while True:
            expanded = descendants | {pid for pid, row in table.items()
                                      if row['ppid'] in descendants}
            if expanded == descendants:
                break
            descendants = expanded
        # Keep every observed group, including a worker that changes session.
        self.owned_pids.update(descendants)
        self.groups.update(table[pid]['pgid'] for pid in self.owned_pids if pid in table)
        _require(now-(self.anchor if self.last_sample is None else self.last_sample) <= .25,
                 'Entry owning monitor sampling gap')
        self.last_sample = now
        _require(q.finite(free) and 10 <= free <= 100, 'Entry memory pressure/unknown')
        rows = [table[pid] for pid in self.owned_pids if pid in table]
        _require(sum(row['rss'] for row in rows) <= q.RSS_LIMIT, 'Entry RSS limit')
        self.peak_cpu = max(self.peak_cpu, sum(row['cpu'] for row in rows))
        self.active_other_cpu = sum(row['cpu'] for pid, row in table.items()
                                    if pid in self.owned_pids and pid != proc.pid)
        unexpected = sorted(descendants-{proc.pid})
        if not allow_worker and self.monitor_until >= now:
            # One synchronous registered monitor can transiently coexist with the
            # controller. It must stay in the controller's existing process group.
            monitor = [pid for pid in unexpected if table[pid]['ppid'] == proc.pid
                       and table[pid]['pgid'] == proc.pid]
            _require(len(monitor) <= 1 and len(unexpected) == len(monitor),
                     'Unowned descendant in registered monitor slot')
            unexpected = []
        _require(allow_worker or not unexpected, 'Unexpected entry descendant processes')
        return now, unexpected

    def _gate(self, request, proc):
        expected = {'root_sha256': self.root_sha256, 'nonce': self.nonce,
                    'controller_pid': proc.pid, 'policy': self.policy, 'task': self.task,
                    'output': self.output,
                    'lock_sha256': self.roots['expected_lock_sha256']}
        _require(not self.gate_issued
                 and all(request.get(key) == value for key, value in expected.items())
                 and request.get('operation') in ('monitor', 'prelaunch'),
                 'Unexpected/repeated entry handshake')
        if request['operation'] == 'monitor':
            _require(tuple(request.get('command', ())) in _MONITOR_COMMANDS,
                     'Unregistered controller monitor command')
            self.monitor_until = min(time.monotonic()+.25, self.anchor+ENTRY_S)
            self.monitor_registrations += 1
            return {'allowed': True}
        self.monitor_until = 0.
        helpers = request.get('entry_helpers')
        _require(type(helpers) is list and len(helpers) == self.monitor_registrations
                 and all(type(item) is dict and type(item.get('pid')) is int
                         and item['pid'] > 0 and item.get('reaped') is True
                         and type(item.get('returncode')) is int for item in helpers)
                 and len({item['pid'] for item in helpers}) == len(helpers),
                 'Missing/unknown/unreaped entry helper registry')
        events = q.ledger_events(Path(self.output)/'ledger.jsonl')
        charges = [event for event in events if event.get('phase') == 'whole_entry_precharge']
        _require(len(charges) == 1 and charges[0].get('sha256') == request.get('precharge_sha256')
                 and charges[0].get('event') == 'supervisor_cpu'
                 and charges[0].get('charged_cpu_s') == ENTRY_S
                 and charges[0].get('nonrefundable') is True
                 and charges[0].get('owner_root_sha256') == self.root_sha256
                 and all(charges[0].get(key) == value for key, value in expected.items())
                 and not any(event.get('event') == 'launch' for event in events),
                 'Owning parent cannot validate exactly one unspent entry precharge')
        now, unexpected = self._sample(proc, min(time.monotonic()+.24, self.anchor+ENTRY_S))
        own = time.process_time()-self.cpu0
        monitors = q._monitor_child_cpu_s-self.monitor0
        _require(q.finite(own) and q.finite(monitors)
                 and q.finite(request.get('controller_reaped_child_cpu_s'))
                 and q.finite(request.get('controller_cpu_s'))
                 and q.finite(request.get('controller_sample_monotonic'), self.anchor)
                 and request['controller_sample_monotonic'] <= now,
                 'Incomplete parent/controller child CPU accounting')
        reported = request['controller_cpu_s']+request['controller_reaped_child_cpu_s']
        # Waited-child rusage retains short-lived registered monitor CPU. The OS
        # tree samples and complete parent elapsed interval provide independent
        # crosschecks. No timestamp supplied by the child establishes the anchor.
        bound = max(self.peak_cpu, reported, now-self.anchor)+own+monitors+SUFFIX_S
        _require(bound <= ENTRY_S and now+SUFFIX_S <= self.anchor+ENTRY_S,
                 'Whole-entry cost plus conservative suffix exceeds 7.5 seconds')
        expires = min(now+PERMIT_S, self.anchor+ENTRY_S,
                      request['controller_sample_monotonic']+SUFFIX_S/(self.capacity+2))
        _require(expires > now, 'Controller CPU report too old for conservative suffix')
        permit = {**request, 'allowed': True, 'observations_complete': True,
                  'unexpected_descendants': unexpected,
                  'entry_bound_s': bound, 'suffix_s': SUFFIX_S,
                  'sample_completed_monotonic': now,
                  'owner_cpu_s': own, 'monitor_child_cpu_s': monitors,
                  'sampled_tree_cpu_s': self.peak_cpu,
                  'capacity_cpu_count': self.capacity,
                  'coverage_assumption': 'trusted frozen imports and registered spawn channels',
                  'issued_monotonic': now,
                  'expires_monotonic': expires}
        gate_path = self.directory.parent/'entry-owner-gate.json'
        q.write_new(gate_path, permit)
        self.gate_issued = True
        self.latest_status = deepcopy(request)
        self.status_sequence = 0
        return {'allowed': True, 'permit': permit,
                'evidence_path': str(gate_path),
                'evidence_sha256': q.sha(gate_path)}

    def _accept_status(self, value, proc):
        expected = {'root_sha256': self.root_sha256, 'nonce': self.nonce,
                    'controller_pid': proc.pid, 'policy': self.policy, 'task': self.task,
                    'output': self.output, 'lock_sha256': self.roots['expected_lock_sha256']}
        _require(self.gate_issued and value.get('operation') == 'runtime_status'
                 and all(value.get(key) == item for key, item in expected.items())
                 and value.get('sequence') == self.status_sequence+1,
                 'Unknown/out-of-order runtime owner status')
        for field in ('controller_cpu_s', 'controller_reaped_child_cpu_s',
                      'controller_sample_monotonic'):
            _require(q.finite(value.get(field), self.latest_status[field]),
                     'Incomplete/decreasing runtime owner status')
        _require(value['controller_sample_monotonic'] <= time.monotonic(),
                 'Runtime owner status is from the future')
        self.latest_status = deepcopy(value)
        self.status_sequence += 1

    def _live_guard(self, now):
        """Conservative whole-package funding while the owned controller is live."""
        status = self.latest_status
        age = now-status['controller_sample_monotonic']
        _require(q.finite(age) and age <= .25, 'Missing/stale runtime owner CPU status')
        own = time.process_time()-self.cpu0
        monitors = q._monitor_child_cpu_s-self.monitor0
        _require(q.finite(own) and q.finite(monitors)
                 and own+monitors <= OWNER_CPU_MAX_S,
                 'External owner exceeded its 15 seconds inside supervision45')
        reported = status['controller_cpu_s']+status['controller_reaped_child_cpu_s']
        observed = max(now-self.anchor, self.peak_cpu, reported+self.active_other_cpu,
                       getattr(self, 'terminal_waited_cpu_s', 0.))
        charged = (self.roots['expected_cumulative_charge_s']+ENTRY_S+observed
                   +own+monitors+(self.capacity+2)*age)
        attempt_path = Path(self.output)/self.task['id']/'attempt.json'
        remaining_native = 62.5
        if attempt_path.exists():
            attempt = q.read(attempt_path)
            _require(attempt.get('task') == self.task
                     and attempt.get('lock_sha256') == self.roots['expected_lock_sha256']
                     and q.finite(attempt.get('parent_monotonic'), self.anchor)
                     and attempt['parent_monotonic'] <= now, 'Native live anchor changed')
            remaining_native = max(0., 62.5-(now-attempt['parent_monotonic']))
        projected = charged+remaining_native
        _require(projected+ANALYSIS_FINAL_S+CLEANUP_S <= PACKAGE_CAP
                 and projected <= DISPATCH_STOP
                 and projected+SHUTDOWN_RESERVE <= HARD_CEILING,
                 'Owning live whole-package funding exhausted')
        return {'charged_cpu_s': charged, 'remaining_native_s': remaining_native,
                'owner_cpu_s': own, 'owner_monitor_cpu_s': monitors,
                'status_age_s': age, 'retained_final_s': ANALYSIS_FINAL_S+CLEANUP_S}

    def run(self, command):
        """Own one controller; never retries or launches a native worker itself.

        The CLI requires the independently frozen command, complete retained
        roots and live owner gates; this helper itself supplies no phase clearance.
        """
        _require(type(command) in (list, tuple) and len(command) >= 4
                 and command[0] == sys.executable
                 and list(command[1:3]) == ['-m', 'experiments.cf1_entry_repaired']
                 and command[3] == 'run'
                 and not any(str(item).startswith('--owner-') for item in command),
                 'Owner requires the frozen v5 controller command')
        capacity = os.cpu_count()
        _require(type(capacity) is int and capacity > 0, 'Unknown CPU capacity')
        _require(threading.active_count() == 1, 'Owning supervisor must be single threaded')
        self.capacity = capacity
        self.directory.mkdir(parents=True, exist_ok=False)
        self.anchor, self.cpu0 = time.monotonic(), time.process_time()
        self.monitor0 = q._monitor_child_cpu_s
        child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.waited0 = child0.ru_utime+child0.ru_stime
        self.nonce = secrets.token_hex(32)
        self.groups, self.owned_pids = set(), set()
        self.last_sample, self.peak_cpu, self.gate_issued = None, 0., False
        self.monitor_until = 0.
        self.monitor_registrations = 0
        self.latest_status = None
        self.active_other_cpu = 0.
        root = {'schema': 'cf1-entry-owner-v1', 'policy': self.policy,
                'anchor': self.anchor, 'owner_pid': os.getpid(), 'nonce': self.nonce,
                'controller_command': list(command), 'roots': self.roots,
                'task': self.task, 'output': self.output,
                'entry_allocation_s': ENTRY_S, 'suffix_s': SUFFIX_S,
                'permit_lifetime_s': PERMIT_S, 'capacity_cpu_count': capacity}
        root_path = self.directory.parent/'entry-owner.json'
        q.write_new(root_path, root)
        self.root_sha256 = q.sha(root_path)
        parent, child = socket.socketpair()
        proc, failure, cleanup = None, None, None
        secondary = []
        old_signals, pending_signals = {}, []
        try:
            def stop_requested(signum, frame):
                # Record without raising during Popen: publication of the returned
                # child PID/ownership must finish before cleanup can interrupt it.
                pending_signals.append(signum)
            for sig in (signal.SIGTERM, signal.SIGINT):
                old_signals[sig] = signal.signal(sig, stop_requested)
            env = {**os.environ, **{key: '1' for key in q.THREAD_KEYS},
                   'PATH': '/usr/bin:/bin',
                   'CF1_ENTRY_OWNER_FD': str(child.fileno()),
                   'CF1_ENTRY_OWNER_ROOT': str(root_path),
                   'CF1_ENTRY_OWNER_SHA256': self.root_sha256,
                   'CF1_ENTRY_OWNER_NONCE': self.nonce}
            with (self.directory/'stdout.log').open('x') as out, (self.directory/'stderr.log').open('x') as err:
                runtime_command = [*command, '--owner-fd', str(child.fileno()),
                                   '--owner-root', str(root_path),
                                   '--owner-root-sha256', self.root_sha256,
                                   '--owner-nonce', self.nonce]
                proc = subprocess.Popen(runtime_command, env=env, start_new_session=True,
                                        pass_fds=(child.fileno(),), stdout=out, stderr=err)
                self.groups.add(proc.pid)
                self.owned_pids.add(proc.pid)
                child.close()
                q.write_new(self.directory/'controller.json',
                            {'root_sha256': self.root_sha256, 'nonce': self.nonce,
                             'controller_pid': proc.pid, 'owner_pid': os.getpid(),
                             'runtime_command': runtime_command})
                _send(parent, {'operation': 'ready', 'root_sha256': self.root_sha256,
                               'nonce': self.nonce, 'controller_pid': proc.pid})
                incoming = b''
                while proc.poll() is None:
                    _require(not pending_signals, 'Owning supervisor received stop signal')
                    now = time.monotonic()
                    # After handoff the original 62.5 native clock remains separately owned.
                    end = self.anchor+(ENTRY_S+62.5+45. if self.gate_issued else ENTRY_S)
                    _require(now < end, 'Owning controller outer deadline exhausted')
                    self._sample(proc, min(now+.24, end), allow_worker=self.gate_issued)
                    if proc.poll() is not None:
                        break
                    ready, _, _ = select.select([parent], [], [], .02)
                    if ready:
                        parent.settimeout(.1)
                        part = parent.recv(MAX_MESSAGE+1)
                        if not part:
                            _require(self.gate_issued, 'Owned controller channel closed before handoff')
                            # run() closes its channel before the CLI's final JSON
                            # print/exit. Retain ownership through that bounded tail.
                            proc.wait(timeout=.1)
                            break
                        incoming += part
                        while b'\n' in incoming:
                            raw, incoming = incoming.split(b'\n', 1)
                            _require(len(raw) <= MAX_MESSAGE, 'Oversized controller message')
                            request = json.loads(raw)
                            _require(type(request) is dict, 'Malformed controller message')
                            if request.get('operation') == 'runtime_status':
                                self._accept_status(request, proc)
                            else:
                                _send(parent, self._gate(request, proc))
                        _require(len(incoming) <= MAX_MESSAGE, 'Oversized partial controller message')
                    if self.gate_issued:
                        self._live_guard(time.monotonic())
                proc.wait(timeout=.1)
                _require(proc.returncode == 0, 'Owned controller returned a failure')
                _require(self.gate_issued, 'Controller exited without complete entry handoff')
                final_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                self.terminal_waited_cpu_s = final_usage.ru_utime+final_usage.ru_stime-self.waited0
                _require(q.finite(self.terminal_waited_cpu_s), 'Final waited ownership CPU missing')
                self._live_guard(time.monotonic())
        except BaseException as exc:
            failure = {'type': type(exc).__name__, 'error': str(exc)}
        finally:
            for channel in (parent, child):
                try:
                    channel.close()
                except BaseException as exc:
                    secondary.append({'stage': 'channel_close', 'type': type(exc).__name__, 'error': str(exc)})
            if proc is not None:
                try:
                    cleanup = q.stop_owned(proc, self.groups, deadline=time.monotonic()+1.5)
                except BaseException as exc:
                    cleanup = {'group_absent': False, 'owned_pgids': sorted(self.groups),
                               'cleanup_errors': [{'type': type(exc).__name__, 'error': str(exc)}]}
                    secondary.append({'stage': 'owned_cleanup', 'type': type(exc).__name__, 'error': str(exc)})
            waited = charge = own = monitor = elapsed = None
            try:
                child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                waited = child_usage.ru_utime+child_usage.ru_stime-self.waited0
                elapsed = time.monotonic()-self.anchor
                own = time.process_time()-self.cpu0
                monitor = q._monitor_child_cpu_s-self.monitor0
                _require(all(q.finite(value) for value in (waited, elapsed, own, monitor)),
                         'Invalid final owner accounting observation')
                charge = max(elapsed, self.peak_cpu, waited)
            except BaseException as exc:
                secondary.append({'stage': 'terminal_accounting', 'type': type(exc).__name__, 'error': str(exc)})
            receipt = {'policy': self.policy, 'root_sha256': self.root_sha256,
                       'failure': failure, 'termination': cleanup,
                       'secondary_errors': secondary,
                       'controller_returncode': None if proc is None else proc.returncode,
                       'entry_gate_issued': self.gate_issued,
                       'whole_owner_elapsed_s': elapsed,
                       'conservative_tree_charge_s': charge,
                       'reaped_child_cpu_s': waited,
                       'owner_cpu_s': own, 'monitor_child_cpu_s': monitor,
                       'charged_cpu_s': None if charge is None else charge+own+monitor,
                       'charge_is_lower_bound': charge is None,
                       'accounting_observations_complete': failure is None and cleanup is not None
                           and not secondary and cleanup['group_absent'] and not cleanup['cleanup_errors'],
                       'reconciliation_required': True,
                       'coverage_assumption': 'trusted frozen imports and registered spawn channels'}
            try:
                q.write_new(self.directory/'owner-receipt.json', receipt)
            except BaseException as exc:
                raise RuntimeError('Owner receipt publication failed; primary='+str(failure)
                                   +'; secondary='+str(secondary)) from exc
            finally:
                for sig, handler in old_signals.items():
                    signal.signal(sig, handler)
        if failure is not None:
            raise RuntimeError('Owned entry failed; retained receipt: '+str(self.directory))
        _require(cleanup is not None and cleanup['group_absent']
                 and not cleanup['cleanup_errors'] and not secondary,
                 'Owned controller cleanup/accounting unresolved')
        return receipt
