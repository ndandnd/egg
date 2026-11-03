"""Prospective v6 single-thread owner; no import grants execution clearance."""
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

from experiments import cf1_entry_owner as legacy
from egglab.async_resource_probe import Probe

q = legacy.q
POLICY = 'cf1-responsive-supervision-v6'
ENTRY_S, STARTUP_OBSERVED_S = 65., 20.
SUFFIX_S, PERMIT_S, CONTROL_S = 2.5, .1, .25
RESOURCE_AGE_S, CAPACITY_MAX = 2.25, 12
CONTROLLER_CPU_S, OWNER_CPU_S = 31.5, 15.
PACKAGE_CAP, FINAL_S, SUPERVISION_S = 3026.723449631016, 45., 120.
HARD_CEILING, DISPATCH_STOP, SHUTDOWN_RESERVE = 3600., 3420., 180.
WORKER_PREFIX = ('-m', 'experiments.cf1_responsive_supervision', 'worker')
MAX_FRAME, MAX_BUFFER = 32768, 131072


@contextmanager
def legacy_bindings():
    """Reuse exact precharge/final-Popen validation without changing old policy."""
    if threading.active_count() != 1:
        raise RuntimeError('Responsive legacy bindings require one Python thread')
    changes = {'POLICY': POLICY, 'ENTRY_S': ENTRY_S, 'PACKAGE_CAP': PACKAGE_CAP,
        'HARD_CEILING': HARD_CEILING, 'DISPATCH_STOP': DISPATCH_STOP,
        'SHUTDOWN_RESERVE': SHUTDOWN_RESERVE, 'ANALYSIS_FINAL_S': FINAL_S,
        'WORKER_PREFIX': WORKER_PREFIX}
    old = {name: getattr(legacy, name) for name in changes}
    try:
        for name, value in changes.items():
            setattr(legacy, name, value)
        yield
    finally:
        for name, value in old.items():
            setattr(legacy, name, value)


class FrameChannel:
    """Bounded nonblocking frames. Privileged and telemetry sockets stay separate."""

    def __init__(self, channel, *, clock=time.monotonic):
        self.channel, self.clock = channel, clock
        self.incoming, self.outgoing = bytearray(), bytearray()
        self.eof = False
        channel.setblocking(False)

    def send(self, value):
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()+b'\n'
        if len(raw) > MAX_FRAME or len(self.outgoing)+len(raw) > MAX_BUFFER:
            raise ValueError('Responsive frame/output buffer exceeded')
        self.outgoing.extend(raw)

    def flush(self):
        if self.outgoing:
            try:
                count = self.channel.send(self.outgoing[:MAX_FRAME])
                if count <= 0:
                    raise EOFError('Responsive channel cannot write')
                del self.outgoing[:count]
            except BlockingIOError:
                pass

    def pump(self):
        self.flush()
        if not self.eof:
            for _ in range(2):
                try:
                    raw = self.channel.recv(MAX_FRAME)
                except BlockingIOError:
                    break
                if not raw:
                    self.eof = True
                    break
                self.incoming.extend(raw)
                if len(self.incoming) > MAX_BUFFER:
                    raise ValueError('Responsive input buffer exceeded')
        frames = []
        for _ in range(8):
            end = self.incoming.find(b'\n')
            if end < 0:
                if len(self.incoming) > MAX_FRAME:
                    raise ValueError('Oversized partial responsive frame')
                break
            if end+1 > MAX_FRAME:
                raise ValueError('Oversized responsive frame')
            raw = bytes(self.incoming[:end])
            del self.incoming[:end+1]
            value = json.loads(raw)
            if type(value) is not dict:
                raise ValueError('Responsive frame must be an object')
            frames.append(value)
        if self.eof and self.incoming and b'\n' not in self.incoming:
            raise EOFError('Truncated responsive frame')
        return frames


def uncertainty(capacity, resource_age, control_age=0., *, cleanup=False):
    if (type(capacity) is not int or not 0 < capacity <= CAPACITY_MAX
            or not q.finite(resource_age) or resource_age > RESOURCE_AGE_S
            or not q.finite(control_age)):
        raise ValueError('Unknown capacity or stale resource provenance')
    rate = capacity+3
    # ps TIME is rounded; retain a labelled conservative two-centisecond slot
    # allowance in addition to unobserved-time capacity tails.
    return rate*(max(resource_age, control_age)+CONTROL_S+.02+(1.5 if cleanup else 0.))


def funded(total, remaining_native, *, final=FINAL_S):
    if (not all(q.finite(value) for value in (total, remaining_native, final))
            or total+remaining_native+final > PACKAGE_CAP
            or total+remaining_native > DISPATCH_STOP
            or total+remaining_native+SHUTDOWN_RESERVE > HARD_CEILING):
        raise ValueError('Responsive conservative package/global funding exhausted')


def watchdog_binding(folder, worker_pid):
    """Validate the unchanged physical worker's one fixed same-PGID watchdog."""
    folder = Path(folder).resolve()
    path = folder/'owned-processes.json'
    if not path.exists():
        return None
    if path.is_symlink() or path.resolve().parent != folder:
        raise ValueError('Watchdog registration escaped its exact native task folder')
    with path.open('rb') as stream:
        raw = stream.read(4097)
    if len(raw) > 4096:
        raise ValueError('Oversized fixed watchdog registration')
    value = json.loads(raw)
    if (type(value) is not dict or set(value) != {'worker_pid', 'watchdog_pid',
            'owned_pgids', 'watchdog_contract'} or value['worker_pid'] != worker_pid
            or type(value['watchdog_pid']) is not int or value['watchdog_pid'] <= 0
            or value['watchdog_pid'] == worker_pid or value['owned_pgids'] != [worker_pid]
            or value['watchdog_contract'] != 'codex_local_campaign.watch_parent; inherited PGID'):
        raise ValueError('Physical watchdog PID/group/source contract differs')
    return value['watchdog_pid']


class EntryClient(legacy.EntryClient):
    """Retains legacy exact precharge and one-use final-Popen enforcement."""

    def __init__(self, channel, telemetry, **bindings):
        self.telemetry = FrameChannel(telemetry)
        self.latest_resource = None
        self.resource_sequence, self.sent_sequence = 0, 0
        self.last_service = self.last_status = None
        self.controller_gate_cpu = None
        self.terminal_phase = False
        self.created_pid = self.created_anchor = None
        self.publication_failure = None
        super().__init__(channel, **bindings)
        expected = {'responsive_protocol_revision': 6, 'capacity_upper_bound': CAPACITY_MAX,
            'resource_start_age_limit_s': RESOURCE_AGE_S, 'resource_pair_limit_s': 1.,
            'cpu_resolution_limit_s': .01, 'cpu_quantization_slot_guard_s': .02,
            'completed_resource_gap_s': 1.25, 'minimum_probe_start_interval_s': .25,
            'control_freshness_s': CONTROL_S, 'startup_observed_limit_s': STARTUP_OBSERVED_S,
            'controller_cpu_cap_s': CONTROLLER_CPU_S, 'owner_cpu_cap_s': OWNER_CPU_S,
            'supervision_reserve_s': SUPERVISION_S, 'analysis_final_reserve_s': FINAL_S,
            'package_cap_s': PACKAGE_CAP, 'hard_total_ceiling_s': HARD_CEILING,
            'dispatch_stop_s': DISPATCH_STOP, 'shutdown_reserve_s': SHUTDOWN_RESERVE,
            'physical_watchdog_contract': 'codex_local_campaign.watch_parent; inherited PGID',
            'telemetry_channel_separate': True}
        if any(self.root.get(name) != value for name, value in expected.items()):
            raise ValueError('Responsive policy missing from independent owner root')

    def _status(self):
        self.service(force=True)

    def service(self, *, force=False):
        self._identity(check_time=not self.used)
        now = time.monotonic()
        if not self.terminal_phase and self.last_service is not None and now-self.last_service > CONTROL_S:
            raise ValueError('Controller control service gap exceeds .25s')
        self.last_service = now
        if force or self.last_status is None or now-self.last_status >= .05:
            own = resource.getrusage(resource.RUSAGE_SELF)
            children = resource.getrusage(resource.RUSAGE_CHILDREN)
            self.sent_sequence += 1
            self.telemetry.send({**self._binding(), 'operation': 'runtime_status',
                'sequence': self.sent_sequence, 'controller_sample_monotonic': now,
                'controller_cpu_s': own.ru_utime+own.ru_stime,
                'controller_reaped_child_cpu_s': children.ru_utime+children.ru_stime,
                'active_control_claim': not self.terminal_phase})
            self.last_status = now
        for record in self.telemetry.pump():
            if (record.get('operation') != 'resource'
                    or any(record.get(key) != value for key, value in self._binding().items())
                    or record.get('sequence') != self.resource_sequence+1):
                raise ValueError('Unknown/reordered resource telemetry')
            sample = record['sample']
            start, end = sample['start_monotonic'], sample['completed_monotonic']
            if (sample.get('sequence') != record['sequence']
                    or sample.get('accounting_observations_complete') is not True
                    or not q.finite(sample.get('cpu_resolution_s'))
                    or not 0 < sample['cpu_resolution_s'] <= .01
                    or not q.finite(start, self.root['anchor']) or not q.finite(end, start)
                    or end-start > 1. or end > now or now-start > RESOURCE_AGE_S
                    or (self.latest_resource is not None
                        and (end <= self.latest_resource['completed_monotonic']
                            or end-self.latest_resource['completed_monotonic'] > 1.25
                            or start-self.latest_resource['start_monotonic'] < .25))):
                raise ValueError('Resource telemetry start/gap/duration differs')
            sample['table'] = {int(pid): row for pid, row in sample['table'].items()}
            self.latest_resource, self.resource_sequence = sample, record['sequence']
        if self.telemetry.eof:
            raise EOFError('Owning resource channel closed')
        if self.latest_resource is not None and now-self.latest_resource['start_monotonic'] > RESOURCE_AGE_S:
            raise ValueError('Cached resource record expired')
        return self.latest_resource

    def _permit(self, funding):
        # Wait for an independently completed sample BEFORE taking new rusage.
        # No request timestamp is carried across an expensive probe wait.
        while True:
            sample = self.service(force=True)
            if sample is not None:
                break
            if time.monotonic() >= self.root['anchor']+ENTRY_S:
                raise TimeoutError('No complete owned resource sample before entry end')
            select.select([self.telemetry.channel], [], [], .01)
        own = resource.getrusage(resource.RUSAGE_SELF)
        self.controller_gate_cpu = own.ru_utime+own.ru_stime
        permit = super()._permit(funding)
        self.current_permit_expiry = permit['expires_monotonic']
        return permit

    def _publish_worker(self, proc, anchor):
        if self.created_pid is not None or type(proc.pid) is not int or proc.pid <= 0:
            raise ValueError('Worker publication is exact and one-use')
        self.created_pid, self.created_anchor = proc.pid, anchor
        record = {**self._binding(), 'operation': 'worker_created', 'pid': proc.pid, 'anchor': anchor}
        q.write_new(self.root_path.parent/'worker-created.json', record)
        self.telemetry.send({**self._binding(), 'operation': 'worker_created',
            'pid': proc.pid, 'anchor': anchor})
        deadline = min(time.monotonic()+.1, anchor+62.5)
        while self.telemetry.outgoing:
            self.telemetry.flush()
            if time.monotonic() > deadline:
                raise TimeoutError('Actual worker PID publication deadline')
            select.select([], [self.telemetry.channel], [], .005)

    def launch_guard(self, args, task, output, locksha, *, delegate, funding_check):
        original, original_read = q.subprocess.Popen, q.read
        observed_attempt = {}
        attempt_path = (Path(output)/task['id']/'attempt.json').resolve()
        def read(path):
            value = original_read(path)
            if Path(path).resolve() == attempt_path:
                observed_attempt['anchor'] = value.get('parent_monotonic')
            return value
        def publish_after_popen(command, *positional, **kwargs):
            # Reuse the actual guard's preceding validated read; no new blocking
            # IO may be inserted between its final expiry check and real Popen.
            anchor = observed_attempt.get('anchor')
            if self.worker_creation and not q.finite(anchor):
                raise ValueError('Actual guarded native anchor was not observed')
            if self.worker_creation and time.monotonic() > self.current_permit_expiry:
                raise ValueError('Responsive permit expired at actual Popen boundary')
            proc = original(command, *positional, **kwargs)
            if not self.worker_creation:
                return proc
            try:
                # Still inside legacy q.launch's signal-masked Popen/PID boundary.
                # Publish before returning the actual Popen object to that caller.
                self._publish_worker(proc, anchor)
            except BaseException as exc:
                # Popen DID create a child. Return it through q.launch so its
                # original masked boundary publishes args.active; raising here
                # would make legacy launch write a false unspawned/absent receipt.
                self.publication_failure = {'type': type(exc).__name__, 'error': str(exc)}
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                except BaseException as cleanup_exc:
                    self.publication_failure['signal_error'] = {
                        'type': type(cleanup_exc).__name__, 'error': str(cleanup_exc)}
            return proc
        q.subprocess.Popen, q.read = publish_after_popen, read
        try:
            return super().launch_guard(args, task, output, locksha,
                delegate=delegate, funding_check=funding_check)
        finally:
            q.subprocess.Popen, q.read = original, original_read

    def worker_created(self, item):
        if (item['proc'].pid, item['anchor']) != (self.created_pid, self.created_anchor):
            raise ValueError('Returned launch item differs from already published worker')
        if self.publication_failure is not None:
            raise RuntimeError('Actual worker publication failed: '+str(self.publication_failure))
        self.service(force=True)

    def terminal(self, item, reason):
        self.service(force=True)
        self.terminal_phase = True
        self.telemetry.send({**self._binding(), 'operation': 'terminal_cleanup',
            'pid': item['proc'].pid, 'anchor': item['anchor'], 'reason': reason,
            'returncode': item['proc'].poll()})
        # Deliver phase transition before legacy bounded cleanup/file audit.
        deadline = time.monotonic()+.1
        while self.telemetry.outgoing:
            self.telemetry.flush()
            if time.monotonic() > deadline:
                raise TimeoutError('Terminal transition could not be delivered')
            select.select([], [self.telemetry.channel], [], .005)


class OwnerSupervisor(legacy.OwnerSupervisor):
    """Fixed-probe state machine and socket service on the owning Python thread."""

    def __init__(self, *, directory, roots, task, output, policy=POLICY):
        with legacy_bindings():
            super().__init__(directory=directory, roots=roots, task=task, output=output, policy=policy)

    def _binding6(self):
        return {'root_sha256': self.root_sha256, 'nonce': self.nonce,
            'controller_pid': self.proc.pid, 'policy': self.policy, 'task': self.task,
            'output': self.output, 'lock_sha256': self.roots['expected_lock_sha256']}

    def _identity6(self, value):
        if any(value.get(key) != expected for key, expected in self._binding6().items()):
            raise ValueError('Responsive control/telemetry identity differs')

    def _accept_status(self, value, proc):
        self._identity6(value)
        if value.get('sequence') != self.status_sequence+1:
            raise ValueError('Responsive status sequence differs')
        previous = self.latest_status or {name: 0. for name in (
            'controller_cpu_s', 'controller_reaped_child_cpu_s', 'controller_sample_monotonic')}
        for name in previous:
            if name.startswith('controller_') and name in value:
                if not q.finite(value[name], previous[name]):
                    raise ValueError('Incomplete/decreasing controller resource report')
        if not all(q.finite(value.get(name), previous.get(name, 0.)) for name in (
                'controller_cpu_s', 'controller_reaped_child_cpu_s', 'controller_sample_monotonic')):
            raise ValueError('Missing controller resource observations')
        if value['controller_sample_monotonic'] > time.monotonic():
            raise ValueError('Controller status comes from the future')
        self.latest_status = deepcopy(value)
        self.status_sequence += 1

    def _resource(self, sample, now):
        """Validate host-table ownership in bounded chunks between control turns."""
        if sample is not None:
            if self.pending_resource is not None:
                raise ValueError('Resource ownership validation queue exceeded one record')
            self.pending_resource = {'sample': sample, 'rows': iter(sample['table'].items()),
                                     'owned_table': {}, 'candidate': None, 'child_counts': {},
                                     'group_members': {}, 'child_members': {}}
        pending = self.pending_resource
        if pending is None:
            return
        sample = pending['sample']
        if now > sample['deadline']:
            raise TimeoutError('Owned resource validation exceeded pair deadline')
        included = {self.proc.pid, os.getpid(), *sample['registered_probe_pids']}
        if self.worker_pid is not None:
            included.add(self.worker_pid)
        done = False
        for _ in range(32):
            try:
                pid, row = next(pending['rows'])
            except StopIteration:
                done = True
                break
            pending['child_counts'][row['ppid']] = pending['child_counts'].get(row['ppid'], 0)+1
            children = pending['child_members'].setdefault(row['ppid'], [])
            if len(children) < 2:
                children.append(pid)
            members = pending['group_members'].setdefault(row['pgid'], [])
            if len(members) < 3:
                members.append(pid)
            if row['ppid'] == self.proc.pid:
                if not self.gate_issued or self.worker_pid is not None and pid != self.worker_pid:
                    raise ValueError('Unexpected controller child in complete resource table')
                if self.worker_pid is None:
                    if pending['candidate'] is not None and pending['candidate'] != pid:
                        raise ValueError('More than one worker appeared before registration')
                    pending['candidate'] = pid
                    included.add(pid)
                if row['pgid'] != pid:
                    raise ValueError('Native worker session differs from registered spawn policy')
            if (pid in included or pid == pending['candidate']
                    or self.worker_pid is not None and row['pgid'] == self.worker_pid):
                pending['owned_table'][pid] = row
        if not done:
            return
        native_pid = self.worker_pid if self.worker_pid is not None else pending['candidate']
        if native_pid is not None:
            watcher = watchdog_binding(Path(self.output)/self.task['id'], native_pid)
            extra = set(pending['group_members'].get(native_pid, []))-{native_pid}
            if watcher is None and (extra or pending['child_counts'].get(native_pid, 0)):
                return  # The worker's exclusive registration may follow its Popen by one turn.
            allowed = {native_pid} | (set() if watcher is None else {watcher})
            if (extra-allowed
                    or set(pending['child_members'].get(native_pid, []))-(set() if watcher is None else {watcher})
                    or pending['child_counts'].get(native_pid, 0) > (1 if watcher else 0)):
                raise ValueError('Unregistered numerical descendant/group member')
            if watcher is not None:
                if pending['child_counts'].get(watcher, 0):
                    raise ValueError('Fixed watchdog spawned an unregistered descendant')
                if self.watchdog_pid is not None and self.watchdog_pid != watcher:
                    raise ValueError('Physical watchdog identity changed')
                self.watchdog_pid = watcher
                row = sample['table'].get(watcher)
                if row is not None:
                    if row['pgid'] != native_pid or row['ppid'] not in (native_pid, 1):
                        raise ValueError('Physical watchdog ancestry/group differs')
                    pending['owned_table'][watcher] = row
        validated = time.monotonic()
        if validated > sample['deadline']:
            raise TimeoutError('Owned resource completion exceeded pair deadline')
        ready = {**sample, 'probe_completed_monotonic': sample['completed_monotonic'],
                 'completed_monotonic': validated, 'table': pending['owned_table']}
        self.pending_resource = None
        self._accept_resource(ready, validated)

    def _accept_resource(self, sample, now):
        if sample.get('accounting_observations_complete') is not True:
            raise ValueError('Incomplete probe accounting cannot qualify resource sample')
        if not q.finite(sample.get('cpu_resolution_s')) or not 0 < sample['cpu_resolution_s'] <= .01:
            raise ValueError('Unqualified process CPU precision')
        if self.latest_resource is None and sample['sequence'] != 1:
            raise ValueError('First probe resource sequence differs')
        if self.latest_resource is not None and sample['sequence'] != self.latest_resource['sequence']+1:
            raise ValueError('Probe resource sequence differs')
        if self.latest_resource is not None and sample['completed_monotonic']-self.latest_resource['completed_monotonic'] > 1.25:
            raise ValueError('Complete owned resource record gap exceeded1.25s')
        table = sample['table']
        if os.getpid() not in table:
            raise ValueError('Owner absent from aggregate resource observation')
        if self.proc.pid not in table:
            if self.proc.poll() is None:
                raise ValueError('Controller absent from complete process sample')
            return
        row = table[self.proc.pid]
        if row['ppid'] != os.getpid() or row['pgid'] != self.proc.pid:
            raise ValueError('Controller parent/session identity changed')
        descendants = {self.proc.pid}
        while True:
            expanded = descendants | {pid for pid, row in table.items() if row['ppid'] in descendants}
            if expanded == descendants:
                break
            descendants = expanded
        if not self.gate_issued and descendants != {self.proc.pid}:
            raise ValueError('Unexpected pre-native controller descendant')
        allowed = {self.proc.pid, self.worker_pid, self.watchdog_pid}
        if self.worker_pid is not None and descendants-allowed:
            raise ValueError('Unregistered native descendant')
        if self.worker_pid is None and len(descendants-{self.proc.pid}) > (1 if self.gate_issued else 0):
            raise ValueError('More than the one permitted worker appeared')
        group_members = {pid for pid, row in table.items() if self.worker_pid is not None and row['pgid'] == self.worker_pid}
        if group_members-{self.worker_pid, self.watchdog_pid}:
            raise ValueError('Unknown native group member')
        descendants.update(group_members)
        self.owned_pids.update(descendants)
        self.groups.update(table[pid]['pgid'] for pid in descendants)
        included = descendants | {os.getpid()} | set(sample['registered_probe_pids'])
        rows = [row for pid, row in table.items() if pid in included]
        rss = sum(row['rss'] for row in rows)
        if (rss > q.RSS_LIMIT or not q.finite(sample['free'])
                or not 10 <= sample['free'] <= 100):
            raise ValueError('Responsive aggregate RSS/memory observation unsafe')
        self.peak_cpu = max(self.peak_cpu, sum(table[pid]['cpu'] for pid in descendants))
        self.active_other_cpu = sum(table[pid]['cpu'] for pid in descendants if pid != self.proc.pid)
        self.peak_rss = max(self.peak_rss, rss)
        self.latest_resource = deepcopy(sample)
        sent = {**sample, 'table': {pid: row for pid, row in table.items() if pid in included}}
        self.resource_channel.send({**self._binding6(), 'operation': 'resource',
            'sequence': sample['sequence'], 'sample': sent})

    def _cost(self, now, *, cleanup=False):
        if self.latest_resource is None:
            raise ValueError('No complete resource observation')
        age = now-self.latest_resource['start_monotonic']
        status = self.latest_status or self.permit_status
        if status is None:
            raise ValueError('No controller CPU observation')
        status_age = now-status['controller_sample_monotonic']
        if not self.terminal_phase and status_age > CONTROL_S:
            raise ValueError('Missing/stale active controller status')
        own = time.process_time()-self.cpu0
        monitors = self.probe.helper_waited_cpu_s
        if not q.finite(own) or not q.finite(monitors) or own+monitors > OWNER_CPU_S:
            raise ValueError('Responsive owner CPU15 provision exhausted')
        reported = status['controller_cpu_s']+status['controller_reaped_child_cpu_s']
        body = max(now-self.anchor, self.peak_cpu, reported+self.active_other_cpu,
                   getattr(self, 'terminal_waited_cpu_s', 0.))+own+monitors
        tail = uncertainty(self.capacity, age, 0. if self.terminal_phase else status_age,
                           cleanup=cleanup)
        self.max_uncertainty = max(self.max_uncertainty, tail)
        return body, tail, own, monitors

    def _startup_guard(self, now):
        own, monitors = time.process_time()-self.cpu0, self.probe.helper_waited_cpu_s
        status = self.latest_status
        reported = 0. if status is None else status['controller_cpu_s']+status['controller_reaped_child_cpu_s']
        body = max(now-self.anchor, self.peak_cpu, reported+self.active_other_cpu)+own+monitors
        if (not all(q.finite(value) for value in (own, monitors, body))
                or own+monitors > OWNER_CPU_S or body > STARTUP_OBSERVED_S):
            raise ValueError('Responsive startup observed20/ownerCPU15 provision exhausted')
        if self.latest_resource is not None:
            age = now-self.latest_resource['start_monotonic']
            tail = uncertainty(self.capacity, age)
            self.max_uncertainty = max(self.max_uncertainty, tail)
            if body+tail+SUFFIX_S > ENTRY_S:
                raise ValueError('Responsive startup uncertainty exceeds entry65')
        funded(self.roots['expected_cumulative_charge_s']+ENTRY_S, 62.5,
               final=SUPERVISION_S+FINAL_S)
        return body

    def _gate(self, request, proc):
        self._identity6(request)
        if self.gate_issued or request.get('operation') != 'prelaunch' or request.get('entry_helpers') != []:
            raise ValueError('Only one fresh worker permit, without controller probe children')
        if self.latest_resource is None:
            raise ValueError('Permit requested without complete owned resource record')
        events = q.ledger_events(Path(self.output)/'ledger.jsonl')
        charges = [event for event in events if event.get('phase') == 'whole_entry_precharge']
        if (len(charges) != 1 or charges[0].get('sha256') != request.get('precharge_sha256')
                or charges[0].get('charged_cpu_s') != ENTRY_S
                or charges[0].get('event') != 'supervisor_cpu'
                or charges[0].get('nonrefundable') is not True
                or charges[0].get('owner_root_sha256') != self.root_sha256
                or any(charges[0].get(key) != value for key, value in self._binding6().items()
                       if key != 'root_sha256')
                or any(event.get('event') == 'launch' for event in events)):
            raise ValueError('Exactly one independently bound entry65 precharge required')
        now = time.monotonic()
        for name in ('controller_cpu_s', 'controller_reaped_child_cpu_s', 'controller_sample_monotonic'):
            if not q.finite(request.get(name)):
                raise ValueError('Missing fresh permit CPU observation')
        if not self.latest_resource['completed_monotonic'] <= request['controller_sample_monotonic'] <= now:
            raise ValueError('Permit sample timestamp differs')
        # Actual fresh request replaces status for this synchronous response only;
        # telemetry sequence remains independent and must remain monotone later.
        reported = request['controller_cpu_s']+request['controller_reaped_child_cpu_s']
        own = time.process_time()-self.cpu0
        monitors = self.probe.helper_waited_cpu_s
        body = max(now-self.anchor, self.peak_cpu, reported+self.active_other_cpu)+own+monitors
        age = now-self.latest_resource['start_monotonic']
        tail = uncertainty(self.capacity, age, now-request['controller_sample_monotonic'])
        bound = body+tail+SUFFIX_S
        if (body > STARTUP_OBSERVED_S or own+monitors > OWNER_CPU_S
                or bound > ENTRY_S or now+SUFFIX_S > self.anchor+ENTRY_S):
            raise ValueError('Responsive entry observed20/uncertainty/suffix exceeds entry65')
        funded(self.roots['expected_cumulative_charge_s']+ENTRY_S, 62.5,
               final=SUPERVISION_S+FINAL_S)
        expires = min(now+PERMIT_S, self.anchor+ENTRY_S,
            request['controller_sample_monotonic']+SUFFIX_S/(self.capacity+3))
        if expires <= now:
            raise ValueError('Fresh request expired before permit publication')
        permit = {**request, 'allowed': True, 'observations_complete': True,
            'unexpected_descendants': [], 'entry_bound_s': bound, 'suffix_s': SUFFIX_S,
            'issued_monotonic': now, 'expires_monotonic': expires,
            'sample_completed_monotonic': self.latest_resource['completed_monotonic'],
            'resource_start_monotonic': self.latest_resource['start_monotonic'],
            'owner_cpu_s': own, 'monitor_child_cpu_s': monitors,
            'observed_body_s': body, 'conservative_uncertainty_s': tail,
            'cpu_quantization_guard_s': (self.capacity+3)*.02,
            'capacity_cpu_count': self.capacity, 'capacity_rate': self.capacity+3}
        path = self.directory.parent/'entry-owner-gate.json'
        q.write_new(path, permit)
        self.gate_issued, self.gate_controller_cpu = True, request['controller_cpu_s']
        self.permit_issued = now
        self.permit_status = {name: request[name] for name in (
            'controller_cpu_s', 'controller_reaped_child_cpu_s', 'controller_sample_monotonic')}
        return {'allowed': True, 'permit': permit, 'evidence_path': str(path),
                'evidence_sha256': q.sha(path)}

    def _live_guard(self, now):
        body, tail, own, monitors = self._cost(now, cleanup=True)
        status = self.latest_status or self.permit_status
        cpu = status['controller_cpu_s']
        if self.terminal_phase and self.proc.pid in self.latest_resource['table']:
            cpu = max(cpu, self.latest_resource['table'][self.proc.pid]['cpu'])
        if cpu-self.gate_controller_cpu > CONTROLLER_CPU_S:
            raise ValueError('Responsive controller CPU31.5 provision exhausted')
        remaining = 62.5 if self.worker_anchor is None else max(0., self.worker_anchor+62.5-now)
        total = self.roots['expected_cumulative_charge_s']+ENTRY_S+body+tail
        funded(total, remaining)
        return {'charged_cpu_s': total, 'observed_body_s': body,
            'conservative_uncertainty_s': tail, 'remaining_native_s': remaining,
            'cpu_quantization_guard_s': (self.capacity+3)*.02,
            'owner_cpu_s': own, 'monitor_child_cpu_s': monitors,
            'resource_start_age_s': now-self.latest_resource['start_monotonic'],
            'control_status_age_s': now-status['controller_sample_monotonic'],
            'active_control_claim': not self.terminal_phase}

    def run(self, command):
        if (list(command[:4]) != [sys.executable, '-m', 'experiments.cf1_responsive_supervision', 'run']
                or any(str(item).startswith('--owner-') for item in command)
                or threading.active_count() != 1):
            raise ValueError('Require exact single-thread responsive controller command')
        self.capacity = os.cpu_count()
        if type(self.capacity) is not int or not 0 < self.capacity <= CAPACITY_MAX:
            raise ValueError('Actual capacity exceeds prospectively bound maximum12')
        expected_roots = {'lock_path', 'freeze_receipt_path', 'accounting_path',
            'expected_lock_sha256', 'expected_freeze_receipt_sha256',
            'expected_accounting_sha256', 'expected_cumulative_charge_s', 'expected_policy'}
        if set(self.roots) != expected_roots or self.roots['expected_policy'] != POLICY:
            raise ValueError('Require complete independent responsive preparation roots')
        funded(self.roots['expected_cumulative_charge_s']+ENTRY_S, 62.5,
               final=SUPERVISION_S+FINAL_S)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.anchor, self.cpu0 = time.monotonic(), time.process_time()
        child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.waited0 = child0.ru_utime+child0.ru_stime
        self.nonce = secrets.token_hex(32)
        self.groups, self.owned_pids = set(), set()
        self.gate_issued, self.terminal_phase = False, False
        self.latest_resource, self.latest_status, self.status_sequence = None, None, 0
        self.pending_resource = None
        self.permit_status = None
        self.worker_pid = self.worker_anchor = self.watchdog_pid = None
        self.max_uncertainty = 0.
        self.peak_cpu, self.active_other_cpu, self.peak_rss = 0., 0., 0
        root_path = self.directory.parent/'entry-owner.json'
        root = {'schema': 'cf1-entry-owner-v1', 'policy': self.policy,
            'anchor': self.anchor, 'owner_pid': os.getpid(), 'nonce': self.nonce,
            'controller_command': list(command), 'roots': self.roots, 'task': self.task,
            'output': self.output, 'entry_allocation_s': ENTRY_S, 'suffix_s': SUFFIX_S,
            'permit_lifetime_s': PERMIT_S, 'capacity_cpu_count': self.capacity,
            'capacity_upper_bound': CAPACITY_MAX, 'resource_start_age_limit_s': RESOURCE_AGE_S,
            'responsive_protocol_revision': 6, 'resource_pair_limit_s': 1.,
            'cpu_resolution_limit_s': .01, 'cpu_quantization_slot_guard_s': .02,
            'completed_resource_gap_s': 1.25, 'minimum_probe_start_interval_s': .25,
            'control_freshness_s': CONTROL_S, 'startup_observed_limit_s': STARTUP_OBSERVED_S,
            'controller_cpu_cap_s': CONTROLLER_CPU_S, 'owner_cpu_cap_s': OWNER_CPU_S,
            'supervision_reserve_s': SUPERVISION_S, 'analysis_final_reserve_s': FINAL_S,
            'package_cap_s': PACKAGE_CAP, 'hard_total_ceiling_s': HARD_CEILING,
            'dispatch_stop_s': DISPATCH_STOP, 'shutdown_reserve_s': SHUTDOWN_RESERVE,
            'physical_watchdog_contract': 'codex_local_campaign.watch_parent; inherited PGID',
            'telemetry_channel_separate': True}
        q.write_new(root_path, root)
        self.root_sha256 = q.sha(root_path)
        control, child = socket.socketpair()
        telemetry, child_telemetry = socket.socketpair()
        self.proc, failure, cleanup, probe_cleanup = None, None, None, None
        self.probe = Probe(q, root_pid=os.getpid(), capacity=self.capacity, clock=time.monotonic)
        secondary, stop_signals = [], []
        old = {sig: signal.signal(sig, lambda signum, frame: stop_signals.append(signum))
               for sig in (signal.SIGTERM, signal.SIGINT)}
        try:
            env = {**os.environ, **{key: '1' for key in q.THREAD_KEYS},
                   'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}
            with (self.directory/'stdout.log').open('x') as out, (self.directory/'stderr.log').open('x') as err:
                runtime = [*command, '--owner-fd', str(child.fileno()),
                    '--owner-telemetry-fd', str(child_telemetry.fileno()),
                    '--owner-root', str(root_path), '--owner-root-sha256', self.root_sha256,
                    '--owner-nonce', self.nonce]
                self.proc = subprocess.Popen(runtime, env=env, start_new_session=True,
                    pass_fds=(child.fileno(), child_telemetry.fileno()), stdout=out, stderr=err)
                self.groups.add(self.proc.pid)
                self.owned_pids.add(self.proc.pid)
                child.close(); child_telemetry.close()
                q.write_new(self.directory/'controller.json', {'root_sha256': self.root_sha256,
                    'nonce': self.nonce, 'controller_pid': self.proc.pid, 'owner_pid': os.getpid(),
                    'runtime_command': runtime})
                self.control, self.resource_channel = FrameChannel(control), FrameChannel(telemetry)
                self.control.send({'operation': 'ready', 'root_sha256': self.root_sha256,
                    'nonce': self.nonce, 'controller_pid': self.proc.pid})
                last_turn = time.monotonic()
                while self.proc.poll() is None:
                    now = time.monotonic()
                    if now-last_turn > CONTROL_S or stop_signals:
                        raise TimeoutError('Owner control service gap/stop signal')
                    last_turn = now
                    if not self.gate_issued and now >= self.anchor+ENTRY_S:
                        raise TimeoutError('Responsive whole-entry end')
                    for value in self.resource_channel.pump():
                        self._identity6(value)
                        operation = value.get('operation')
                        if operation == 'runtime_status':
                            self._accept_status(value, self.proc)
                        elif operation == 'worker_created':
                            if (not self.gate_issued or self.worker_pid is not None
                                    or type(value.get('pid')) is not int
                                    or value['pid'] <= 0 or value['pid'] in (self.proc.pid, os.getpid())
                                    or not q.finite(value.get('anchor'), self.permit_issued)
                                    or value['anchor'] > now):
                                raise ValueError('Unexpected responsive worker registration')
                            self.worker_pid, self.worker_anchor = value['pid'], value['anchor']
                            self.groups.add(self.worker_pid)
                            self.owned_pids.add(self.worker_pid)
                        elif operation == 'terminal_cleanup':
                            if (not self.gate_issued or self.worker_pid is None or self.terminal_phase
                                    or value.get('pid') != self.worker_pid
                                    or value.get('anchor') != self.worker_anchor):
                                raise ValueError('Unknown terminal accounting transition')
                            self.terminal_phase, self.terminal_started = True, now
                        else:
                            raise ValueError('Unexpected resource-channel operation')
                    for request in self.control.pump():
                        self.control.send(self._gate(request, self.proc))
                    # Socket/control service occurs before any bounded probe work.
                    self.control.flush(); self.resource_channel.flush()
                    end = (self.anchor+ENTRY_S if not self.gate_issued else
                           self.anchor+ENTRY_S+62.5+SUPERVISION_S+FINAL_S)
                    if self.terminal_phase:
                        end = min(end, self.terminal_started+FINAL_S)
                    if now >= end:
                        raise TimeoutError('Responsive owner outer accounting end')
                    if not self.probe.active and self.pending_resource is None:
                        previous = self.probe.latest
                        earliest = self.anchor if previous is None else max(
                            previous['start_monotonic']+.25, previous['completed_monotonic'])
                        if now >= earliest:
                            self.probe.start(now, end)
                    sample = self.probe.pump(time.monotonic())
                    self._resource(sample, time.monotonic())
                    if self.latest_resource is not None:
                        self.probe.validate_fresh(time.monotonic())
                    if self.gate_issued:
                        if self.worker_pid is None and time.monotonic()-self.permit_issued > CONTROL_S:
                            raise TimeoutError('Worker creation/registration exceeded control deadline')
                        self._live_guard(time.monotonic())
                    else:
                        self._startup_guard(time.monotonic())
                    if self.worker_anchor is not None:
                        if now >= self.worker_anchor+61. and q.group_probe(self.worker_pid)['state'] == 'present':
                            os.killpg(self.worker_pid, signal.SIGTERM)
                        if now >= self.worker_anchor+62.5 and q.group_probe(self.worker_pid)['state'] != 'absent':
                            raise TimeoutError('Native owned group not closed by62.5')
                    select.select([control, telemetry, *self.probe.filenos], [], [], .005)
                self.proc.wait(timeout=0)
                if self.proc.returncode != 0 or not self.gate_issued or not self.terminal_phase:
                    raise RuntimeError('Responsive controller failed/missing terminal phase')
                final_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                self.terminal_waited_cpu_s = final_usage.ru_utime+final_usage.ru_stime-self.waited0
                self._live_guard(time.monotonic())
        except BaseException as exc:
            failure = {'type': type(exc).__name__, 'error': str(exc)}
        finally:
            deadline = time.monotonic()+1.5
            published = self.directory.parent/'worker-created.json'
            if published.exists():
                try:
                    value = q.read(published)
                    self._identity6(value)
                    if (value.get('operation') != 'worker_created' or type(value.get('pid')) is not int
                            or value['pid'] <= 0 or value['pid'] in (self.proc.pid, os.getpid())
                            or not q.finite(value.get('anchor'), self.anchor)):
                        raise ValueError('Invalid durable worker publication during cleanup')
                    if (not self.gate_issued or self.worker_pid is not None
                            and (value['pid'], value['anchor']) != (self.worker_pid, self.worker_anchor)):
                        raise ValueError('Durable and live worker registrations differ')
                    self.worker_pid, self.worker_anchor = value['pid'], value['anchor']
                    self.groups.add(value['pid'])
                    self.owned_pids.add(value['pid'])
                except BaseException as exc:
                    secondary.append({'stage': 'worker_publication_recovery', 'type': type(exc).__name__, 'error': str(exc)})
            for pgid in self.groups:
                try:
                    os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                except BaseException as exc:
                    secondary.append({'stage': 'initial_cleanup_signal', 'type': type(exc).__name__, 'error': str(exc)})
            try:
                probe_cleanup = self.probe.close(deadline)
            except BaseException as exc:
                secondary.append({'stage': 'probe_cleanup_start', 'type': type(exc).__name__, 'error': str(exc)})
            if self.proc is not None:
                try:
                    native_end = deadline if self.worker_anchor is None else min(deadline, self.worker_anchor+62.5)
                    cleanup = q.stop_owned(self.proc, self.groups, deadline=native_end)
                except BaseException as exc:
                    secondary.append({'stage': 'controller_cleanup', 'type': type(exc).__name__, 'error': str(exc)})
            try:
                while not self.probe.closed and time.monotonic() < deadline:
                    self.probe.pump(time.monotonic())
                    select.select(list(self.probe.filenos), [], [], .005)
                probe_cleanup = self.probe.close(deadline)
            except BaseException as exc:
                secondary.append({'stage': 'probe_cleanup', 'type': type(exc).__name__, 'error': str(exc)})
            for channel in (control, telemetry, child, child_telemetry):
                channel.close()
            for sig, handler in old.items():
                signal.signal(sig, handler)
            waited = resource.getrusage(resource.RUSAGE_CHILDREN)
            elapsed = time.monotonic()-self.anchor
            owner_cpu = time.process_time()-self.cpu0
            observed = waited.ru_utime+waited.ru_stime-self.waited0
            complete = (failure is None and not secondary and cleanup is not None
                and all(q.finite(value) for value in (elapsed, owner_cpu, observed))
                and cleanup.get('group_absent') is True and not cleanup.get('cleanup_errors')
                and probe_cleanup is not None and probe_cleanup.get('accounting_observations_complete') is True
                and probe_cleanup.get('complete') is True
                and owner_cpu+self.probe.helper_waited_cpu_s <= OWNER_CPU_S)
            receipt = {'policy': POLICY, 'root_sha256': self.root_sha256,
                'failure': failure, 'secondary_errors': secondary, 'termination': cleanup,
                'probe_cleanup': probe_cleanup, 'controller_returncode': None if self.proc is None else self.proc.returncode,
                'entry_gate_issued': self.gate_issued, 'terminal_phase': self.terminal_phase,
                'worker_pid': self.worker_pid, 'worker_anchor': self.worker_anchor,
                'watchdog_pid': self.watchdog_pid,
                'terminal_transition_observed_monotonic': getattr(self, 'terminal_started', None),
                'whole_owner_elapsed_s': elapsed, 'owner_cpu_s': owner_cpu,
                'reaped_child_cpu_s': observed, 'probe_waited_cpu_s': self.probe.helper_waited_cpu_s,
                'sampled_peak_rss_bytes': self.peak_rss,
                'conservative_uncertainty_highwater_s': self.max_uncertainty,
                'charged_cpu_s': max(elapsed, self.peak_cpu, observed)+owner_cpu+self.max_uncertainty,
                'accounting_observations_complete': complete,
                'independent_analysis_required': True, 'scientific_qualification': False,
                'charge_is_lower_bound': not q.finite(observed), 'reconciliation_required': True,
                'coverage_assumption': 'trusted frozen code; registered fixed probes, worker and exact physical watchdog',
                'active_control_claim_ends_at_terminal_transition': True}
            q.write_new(self.directory/'owner-receipt.json', receipt)
        if not complete:
            raise RuntimeError('Responsive owner did not close complete observations: '+str(self.directory))
        return receipt
