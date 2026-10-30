"""Deterministic v6 source checks; this module never starts OS helpers.

These checks exercise transport and supervision mechanisms, not numerical
qualification or a hard real-time scheduling guarantee.
"""

import collections
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest import mock

from egglab.async_resource_probe import Probe, ProbeError
from experiments import cf1_responsive_owner as owner
from experiments import cf1_responsive_supervision as supervision


class FakeClock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds
        return self.value


class FakeSocket:
    """A partial, nonblocking socket; reading does not advance the clock."""

    def __init__(self):
        self.incoming = collections.deque()
        self.sent = bytearray()
        self.blocking = None
        self.closed = False

    def setblocking(self, blocking):
        self.blocking = blocking

    def recv(self, limit):
        if not self.incoming:
            raise BlockingIOError()
        data = self.incoming.popleft()
        if len(data) > limit:
            self.incoming.appendleft(data[limit:])
            data = data[:limit]
        return data

    def send(self, data):
        self.sent.extend(data)
        return len(data)

    def close(self):
        self.closed = True

    def fileno(self):
        return 20


class FakePipe:
    def __init__(self, fd, available, chunks):
        self.fd = fd
        self.available = available
        self.chunks = collections.deque(chunks)
        self.closed = False

    def fileno(self):
        return self.fd

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self, pid, clock, finished, stdout, stderr):
        self.pid = pid
        self.clock = clock
        self.finished = finished
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = None

    def poll(self):
        if self.returncode is None and self.clock() >= self.finished:
            self.returncode = 0
        return self.returncode


class FakeSelector:
    def __init__(self, clock):
        self.clock = clock
        self.registered = {}
        self.closed = False

    def register(self, fileobj, events, data=None):
        fd = fileobj if isinstance(fileobj, int) else fileobj.fileno()
        self.registered[fd] = types.SimpleNamespace(
            fd=fd, fileobj=fileobj, events=events, data=data
        )

    def unregister(self, fileobj):
        fd = fileobj if isinstance(fileobj, int) else fileobj.fileno()
        return self.registered.pop(fd)

    def select(self, timeout=0):
        if timeout != 0:
            raise AssertionError("probe must never block in select")
        return [(key, key.events) for key in list(self.registered.values())]

    def close(self):
        self.closed = True


class ProbeRig:
    """Injects all process/pipe operations; real Popen/read/wait are forbidden."""

    def __init__(self, clock, ps_delay=0.0, memory_delay=0.0):
        self.clock = clock
        self.delays = [ps_delay, memory_delay]
        self.processes = []
        self.pipes = {}
        self.kills = []
        self.registrations = []
        self.selector = FakeSelector(clock)

    def popen(self, command, **kwargs):
        index = len(self.processes)
        pid = 101 + index
        finished = self.clock() + self.delays[index % 2]
        if index % 2 == 0:
            payload = b"1 0 1 20 00:00.01\n101 1 101 4 00:00.00\n102 1 102 4 00:00.00\n"
        else:
            payload = b"System-wide memory free percentage: 24%\n"
        stdout = FakePipe(10 + 2 * index, finished, [payload, b""])
        stderr = FakePipe(11 + 2 * index, finished, [b""])
        self.pipes[stdout.fd] = stdout
        self.pipes[stderr.fd] = stderr
        process = FakeProcess(pid, self.clock, finished, stdout, stderr)
        self.processes.append(process)
        return process

    def read(self, fd, size):
        pipe = self.pipes[fd]
        if self.clock() < pipe.available:
            raise BlockingIOError()
        if not pipe.chunks:
            return b""
        chunk = pipe.chunks.popleft()
        if len(chunk) > size:
            pipe.chunks.appendleft(chunk[size:])
            chunk = chunk[:size]
        return chunk

    def reap(self, process):
        code = process.poll()
        return code, None if code is None else 0.01

    def killpg(self, pgid, sig):
        self.kills.append((pgid, sig))
        for process in self.processes:
            if process.pid == pgid:
                process.finished = self.clock()
                process.returncode = -sig
                process.stdout.available = self.clock()
                process.stderr.available = self.clock()

    def register(self, *args, **kwargs):
        self.registrations.append((args, kwargs))

    def probe(self, **overrides):
        arguments = dict(root_pid=1, capacity=12, clock=self.clock,
            popen=self.popen, selector=self.selector, read=self.read,
            set_blocking=lambda fd, blocking: None, killpg=self.killpg,
            register=self.register, reap=self.reap,
            group_probe=lambda pgid: 'absent')
        arguments.update(overrides)
        return Probe(**arguments)


def complete_pair(probe, clock, when):
    """One payload read and one EOF read, without waiting or advancing time."""
    clock.value = when
    first = probe.pump(clock())
    if first is not None:
        return first
    return probe.pump(clock())


class ProbeMechanismTests(unittest.TestCase):
    def test_slow_each_command_does_not_wait_and_returns_only_complete_pair(self):
        for delays in ((.31, .99), (.99, .31), (.99, .99)):
            with self.subTest(delays=delays):
                clock = FakeClock()
                rig = ProbeRig(clock, *delays)
                probe = rig.probe()
                probe.start(clock(), 10.)
                self.assertEqual(len(rig.registrations), 2)
                self.assertEqual(probe.owned_pids, {101, 102})
                for when in (.24, .30, .50):
                    clock.value = when
                    self.assertIsNone(probe.pump(when))
                    self.assertEqual(clock(), when)
                    self.assertIsNone(probe.latest)
                record = complete_pair(probe, clock, .99)
                self.assertIsNotNone(record)
                self.assertEqual(record['start_monotonic'], 0.)
                self.assertEqual(record['completed_monotonic'], .99)
                self.assertEqual(record['free'], 24.)
                self.assertEqual(record['table'][1]['rss'], 20 * 1024)
                self.assertAlmostEqual(record['helper_waited_cpu_s'], .02)
                self.assertGreater(record['cpu_resolution_s'], 0.)
                self.assertLessEqual(record['cpu_resolution_s'], .01)
                self.assertTrue(all(p['reaped'] and p['group_state'] == 'absent'
                                    for p in record['probes']))
                self.assertIsNone(probe.pump(clock()))
                clock.advance(.01)
                self.assertEqual(probe.latest['sequence'], record['sequence'])
                self.assertEqual(probe.latest['start_monotonic'], 0.)
                self.assertEqual(probe.latest['completed_monotonic'], .99)

    def test_pair_duration_boundary_rejects_late_even_if_helpers_exited(self):
        for when, accepted in ((1., True), (1.000001, False)):
            with self.subTest(when=when):
                clock = FakeClock()
                rig = ProbeRig(clock, 1., 1.)
                probe = rig.probe()
                probe.start(0., 10.)
                if accepted:
                    self.assertIsNotNone(complete_pair(probe, clock, when))
                else:
                    clock.value = when
                    with self.assertRaisesRegex(ProbeError, 'deadline'):
                        probe.pump(clock())
                    self.assertIsNone(probe.latest)
                    self.assertEqual(probe.primary_failure['context'], 'resource_probe')

    def test_phase_deadline_clips_pair_and_never_accepts_partial_result(self):
        clock = FakeClock()
        rig = ProbeRig(clock, .1, .7)
        probe = rig.probe()
        probe.start(0., .6)
        clock.value = .2
        self.assertIsNone(probe.pump(clock()))
        self.assertIsNone(probe.pump(clock()))
        self.assertIsNone(probe.latest)
        clock.value = .600001
        with self.assertRaisesRegex(ProbeError, 'deadline'):
            probe.pump(clock())
        self.assertIsNone(probe.latest)

    def test_cached_record_age_uses_start_and_completed_gap_independently(self):
        clock = FakeClock()
        probe = ProbeRig(clock, 1., 1.).probe()
        probe.start(0., 10.)
        record = complete_pair(probe, clock, 1.)
        clock.value = 2.25
        self.assertEqual(probe.validate_fresh(clock())['sequence'], record['sequence'])
        self.assertEqual(probe.latest['start_monotonic'], 0.)
        clock.advance(.000001)
        with self.assertRaisesRegex(ProbeError, 'earliest START'):
            probe.validate_fresh(clock())

        clock = FakeClock()
        probe = ProbeRig(clock, .1, .1).probe()
        probe.start(0., 10.)
        complete_pair(probe, clock, .1)
        clock.value = 1.350001
        with self.assertRaisesRegex(ProbeError, 'gap'):
            probe.validate_fresh(clock())

    def test_probe_start_cadence_enforces_both_bounds(self):
        for next_start, allowed in ((.249999, False), (.25, True), (.250001, False)):
            with self.subTest(next_start=next_start):
                clock = FakeClock()
                probe = ProbeRig(clock).probe()
                probe.start(0., 10.)
                self.assertIsNotNone(complete_pair(probe, clock, 0.))
                clock.value = next_start
                if allowed:
                    probe.start(clock(), 10.)
                    self.assertTrue(probe.active)
                else:
                    with self.assertRaisesRegex(ProbeError, 'interval|within'):
                        probe.start(clock(), 10.)

    def test_missing_memory_or_unclosed_group_cannot_publish(self):
        for missing_memory in (True, False):
            with self.subTest(missing_memory=missing_memory):
                clock = FakeClock()
                rig = ProbeRig(clock)
                probe = rig.probe(group_probe=lambda pgid: 'absent' if missing_memory else 'present')
                probe.start(0., 10.)
                if missing_memory:
                    rig.processes[1].stdout.chunks = collections.deque([b'no memory observation\n', b''])
                self.assertIsNone(probe.pump(0.))
                with self.assertRaisesRegex(ProbeError, 'Incomplete|absence'):
                    probe.pump(0.)
                self.assertIsNone(probe.latest)

    def test_primary_timeout_survives_signal_reap_and_cleanup_failures(self):
        clock = FakeClock()
        rig = ProbeRig(clock, 5., 5.)
        def failed_signal(pgid, sig):
            raise PermissionError('injected signal denial')
        def failed_reap(process):
            raise OSError('injected waited observation loss')
        probe = rig.probe(killpg=failed_signal, reap=failed_reap,
                          group_probe=lambda pgid: 'unknown')
        probe.start(0., 10.)
        clock.value = 1.01
        with self.assertRaisesRegex(ProbeError, 'deadline'):
            probe.pump(clock())
        primary = dict(probe.primary_failure)
        clock.value = 2.52
        probe.pump(clock())
        receipt = probe.cleanup_receipt()
        self.assertEqual(receipt['primary_failure'], primary)
        self.assertTrue(receipt['closed'])
        self.assertFalse(receipt['complete'])
        self.assertFalse(receipt['accounting_observations_complete'])
        self.assertEqual(receipt['unreaped_pids'], [101, 102])
        contexts = {error['context'] for error in receipt['cleanup_errors']}
        self.assertIn('probe_reap', contexts)
        self.assertIn('cleanup_deadline', contexts)
        self.assertTrue(any(context.startswith('probe_signal_') for context in contexts))

    def test_waited_cpu_missing_prevents_success_even_with_exited_helpers(self):
        clock = FakeClock()
        rig = ProbeRig(clock)
        probe = rig.probe(reap=lambda process: (0, None))
        probe.start(0., 10.)
        with self.assertRaisesRegex(ProbeError, 'waited probe accounting'):
            probe.pump(0.)
        self.assertIsNone(probe.latest)
        self.assertFalse(probe.cleanup_receipt()['accounting_observations_complete'])

    def test_capacity_above_bound_rejected_before_any_spawn(self):
        clock = FakeClock()
        rig = ProbeRig(clock)
        with self.assertRaises(ValueError):
            rig.probe(capacity=13)
        self.assertEqual(rig.processes, [])

    def test_partial_registration_failure_closes_both_spawned_processes(self):
        clock = FakeClock()
        rig = ProbeRig(clock, 5., 5.)
        def registration(metadata):
            rig.registrations.append(metadata)
            if len(rig.registrations) == 2:
                raise RuntimeError('injected registration rejection')
        probe = rig.probe(register=registration)
        with self.assertRaisesRegex(ProbeError, 'registration rejection'):
            probe.start(0., 10.)
        receipt = probe.cleanup_receipt()
        self.assertEqual(receipt['owned_pids'], [101, 102])
        self.assertTrue(receipt['closed'])
        self.assertTrue(receipt['complete'])
        self.assertTrue(receipt['accounting_observations_complete'])
        self.assertIsNone(probe.latest)
        self.assertTrue(all(process.stdout.closed and process.stderr.closed
                            for process in rig.processes))
        self.assertIn('registration rejection', receipt['primary_failure']['error'])

    def test_pipe_close_failure_cannot_be_published_as_a_successful_sample(self):
        clock = FakeClock()
        rig = ProbeRig(clock)
        probe = rig.probe()
        probe.start(0., 10.)
        def failed_close():
            raise OSError('injected pipe close failure')
        rig.processes[0].stdout.close = failed_close
        self.assertIsNone(probe.pump(0.))
        with self.assertRaisesRegex(ProbeError, 'pipe cleanup'):
            probe.pump(0.)
        receipt = probe.cleanup_receipt()
        self.assertIsNone(probe.latest)
        self.assertFalse(receipt['complete'])
        self.assertTrue(any(error['context'] == 'pipe_close'
                            for error in receipt['cleanup_errors']))

    def test_oversized_read_and_line_fail_before_sample_publication(self):
        for failure in ('read', 'line'):
            with self.subTest(failure=failure):
                clock = FakeClock()
                rig = ProbeRig(clock)
                overrides = {'read': lambda fd, count: b'x' * (count+1)} if failure == 'read' else {}
                probe = rig.probe(**overrides)
                probe.start(0., 10.)
                if failure == 'line':
                    rig.processes[0].stdout.chunks = collections.deque([b'x' * 4097 + b'\n', b''])
                with self.assertRaisesRegex(ProbeError, 'bound'):
                    probe.pump(0.)
                self.assertIsNone(probe.latest)
                self.assertIsNotNone(probe.cleanup_receipt()['primary_failure'])

    def test_bounded_parsing_yields_before_large_snapshot_is_complete(self):
        clock = FakeClock()
        rig = ProbeRig(clock)
        probe = rig.probe()
        probe.start(0., 10.)
        rows = [b'1 0 1 20 00:00.01\n']
        rows.extend(('%d 0 %d 1 00:00.00\n' % (pid, pid)).encode()
                    for pid in range(1000, 1300))
        rig.processes[0].stdout.chunks = collections.deque([b''.join(rows), b''])
        self.assertIsNone(probe.pump(0.))
        self.assertIsNone(probe.latest)
        # The first pump consumed a bounded prefix, leaving the owning control
        # loop an opportunity to service its next frame before more parsing.
        socket = FakeSocket()
        socket.incoming.append(b'{"operation":"runtime_status"}\n')
        self.assertEqual(owner.FrameChannel(socket, clock=clock).pump(),
                         [{'operation': 'runtime_status'}])
        record = probe.pump(0.)
        self.assertEqual(len(record['table']), 301)

    def test_pipe_setup_failure_closes_unregistered_streams_and_reaps(self):
        clock = FakeClock()
        rig = ProbeRig(clock, 5., 5.)
        calls = []
        def set_blocking(fd, blocking):
            calls.append(fd)
            if len(calls) == 3:
                raise OSError('injected pipe setup failure')
        probe = rig.probe(set_blocking=set_blocking)
        with self.assertRaisesRegex(ProbeError, 'pipe setup failure'):
            probe.start(0., 10.)
        receipt = probe.cleanup_receipt()
        self.assertTrue(receipt['complete'])
        self.assertTrue(receipt['accounting_observations_complete'])
        self.assertEqual(receipt['unreaped_pids'], [])
        self.assertTrue(all(process.stdout.closed and process.stderr.closed
                            for process in rig.processes))

    def test_coarse_process_cpu_time_cannot_qualify_a_pair(self):
        for raw_time in (b'00:00', b'00:00.1'):
            with self.subTest(raw_time=raw_time):
                clock = FakeClock()
                rig = ProbeRig(clock)
                probe = rig.probe()
                probe.start(0., 10.)
                rig.processes[0].stdout.chunks = collections.deque([
                    b'1 0 1 20 ' + raw_time + b'\n', b''])
                with self.assertRaisesRegex(ProbeError, 'two fractional decimal digits'):
                    probe.pump(0.)
                self.assertIsNone(probe.latest)
                self.assertIn('fractional decimal digits', probe.primary_failure['error'])


def finite(value, lower=0.):
    import math
    return type(value) in (int, float) and math.isfinite(value) and value >= lower


def client_fixture(clock):
    client = owner.EntryClient.__new__(owner.EntryClient)
    client.telemetry = owner.FrameChannel(FakeSocket(), clock=clock)
    client.latest_resource = None
    client.resource_sequence = client.sent_sequence = 0
    client.last_service = client.last_status = None
    client.root = {'anchor': 0.}
    client.used = False
    client.terminal_phase = False
    client._identity = lambda **kwargs: None
    binding = {'root_sha256': 'root', 'nonce': 'nonce', 'task': {'id': 'task'},
               'controller_pid': 7, 'output': '/unused', 'policy': owner.POLICY,
               'lock_sha256': 'lock'}
    client._binding = lambda: dict(binding)
    return client


def sample_record(sequence=1, start=0., end=.5):
    return {'sequence': sequence, 'start_monotonic': start,
            'completed_monotonic': end, 'table': {}, 'free': 24.,
            'cpu_resolution_s': .01,
            'accounting_observations_complete': True}


class ControlAndTelemetryTests(unittest.TestCase):
    def test_partial_frames_allow_control_progress_while_pair_remains_pending(self):
        clock = FakeClock()
        rig = ProbeRig(clock, .99, .99)
        probe = rig.probe()
        socket = FakeSocket()
        channel = owner.FrameChannel(socket, clock=clock)
        control = supervision.ControlClock(0., clock=clock)
        probe.start(0., 10.)
        socket.incoming.append(b'{"operation": "runtime_')
        self.assertEqual(channel.pump(), [])
        self.assertIsNone(probe.pump(0.))
        for when in (.2, .4, .6, .8):
            clock.value = when
            self.assertIsNone(control.tick())
            socket.incoming.append(b'status"}\n' if when == .2 else b'{}\n')
            self.assertEqual(len(channel.pump()), 1)
            self.assertIsNone(probe.pump(when))
        record = complete_pair(probe, clock, .99)
        self.assertIsNotNone(record)
        self.assertEqual(control.last_control, .8)
        self.assertFalse(socket.blocking)

    def test_control_stop_progresses_without_any_resource_completion(self):
        clock = FakeClock()
        control = supervision.ControlClock(0., clock=clock)
        for index in range(1, 244):
            clock.value = index * .25
            self.assertIsNone(control.tick())
        clock.value = 61.
        self.assertEqual(control.tick(), 'supervisor_stop')
        clock.value = 61.250001
        with self.assertRaisesRegex(TimeoutError, 'control service gap'):
            control.tick()

    def test_ack_read_timestamp_precedes_parsing_and_never_backdates_late_read(self):
        for completed_read in (59.999, 60.001):
            with self.subTest(completed_read=completed_read):
                clock = FakeClock(59.8)
                task = {'id': 'task', 'seconds': 60.}
                ack = {'task_id': 'task', 'lock_sha256': 'lock',
                       'parent_monotonic': 0., 'completion_monotonic': 59.7}
                raw = json.dumps(ack, sort_keys=True).encode() + b'\n'
                attempt = {'policy': supervision.POLICY, 'task': task,
                           'parent_monotonic': 0., 'deadline': 60., 'lock_sha256': 'lock'}
                item = {'ack_fd': 999, 'ack_bytes': b'', 'acknowledgment': None,
                        'task': task, 'anchor': 0., 'folder': '/unused'}
                chunks = collections.deque([raw[:-1], raw[-1:]])
                witnesses = []
                q = types.SimpleNamespace(finite=finite, read=lambda path: attempt,
                    write_new=lambda path, value: witnesses.append(value))
                original_loads = json.loads
                def delayed_parse(payload):
                    clock.advance(.4)
                    return original_loads(payload)
                with mock.patch.object(supervision.os, 'read', side_effect=lambda fd, size: chunks.popleft()), \
                        mock.patch.object(supervision.time, 'monotonic', clock), \
                        mock.patch.object(supervision.adapter, 'q', q), \
                        mock.patch.object(supervision, 'task_matrix', return_value=[task]), \
                        mock.patch.object(supervision.approved, '_ack_bytes', return_value=raw), \
                        mock.patch.object(supervision.json, 'loads', side_effect=delayed_parse):
                    control = supervision.ControlClock(0., clock=clock)
                    self.assertIsNone(control.observe_ack(item, supervision.receive_ack))
                    self.assertNotIn('complete_ack_read_monotonic', item)
                    clock.value = completed_read
                    observed = control.observe_ack(item, supervision.receive_ack)
                self.assertEqual(observed, completed_read)
                self.assertEqual(item['complete_ack_read_monotonic'], completed_read)
                self.assertGreater(clock(), 60.)
                self.assertEqual(observed <= 60., completed_read < 60.)
                self.assertEqual(witnesses[0]['controller_observed_monotonic'], completed_read)

    def test_client_rejects_missing_reordered_and_wrong_binding_telemetry(self):
        for mutation in ('missing', 'reordered', 'nonce', 'task', 'root_sha256'):
            with self.subTest(mutation=mutation):
                clock = FakeClock(.5)
                client = client_fixture(clock)
                record = {**client._binding(), 'operation': 'resource',
                          'sequence': 1, 'sample': sample_record()}
                if mutation == 'missing':
                    del record['sequence']
                elif mutation == 'reordered':
                    record['sequence'] = 2
                else:
                    record[mutation] = 'changed'
                client.telemetry.channel.incoming.append(json.dumps(record).encode()+b'\n')
                usage = types.SimpleNamespace(ru_utime=.01, ru_stime=0.)
                with mock.patch.object(owner.time, 'monotonic', clock), \
                        mock.patch.object(owner.resource, 'getrusage', return_value=usage):
                    with self.assertRaisesRegex(ValueError, 'reordered resource telemetry'):
                        client.service()
                self.assertEqual(client.resource_sequence, 0)
                self.assertIsNone(client.latest_resource)

    def test_client_cached_record_keeps_true_start_and_expires(self):
        clock = FakeClock(.5)
        client = client_fixture(clock)
        record = {**client._binding(), 'operation': 'resource',
                  'sequence': 1, 'sample': sample_record()}
        client.telemetry.channel.incoming.append(json.dumps(record).encode()+b'\n')
        usage = types.SimpleNamespace(ru_utime=.01, ru_stime=0.)
        with mock.patch.object(owner.time, 'monotonic', clock), \
                mock.patch.object(owner.resource, 'getrusage', return_value=usage):
            sample = client.service()
            for index in range(1, 8):
                clock.value = .5 + index * .25
                self.assertIs(client.service(), sample)
            self.assertEqual(sample['start_monotonic'], 0.)
            self.assertEqual(client.resource_sequence, 1)
            clock.value = 2.250001
            with self.assertRaisesRegex(ValueError, 'Cached resource record expired'):
                client.service()

    def test_terminal_status_ends_active_freshness_claim(self):
        clock = FakeClock(1.)
        client = client_fixture(clock)
        client.last_service = 0.
        usage = types.SimpleNamespace(ru_utime=.01, ru_stime=0.)
        with mock.patch.object(owner.time, 'monotonic', clock), \
                mock.patch.object(owner.resource, 'getrusage', return_value=usage):
            with self.assertRaisesRegex(ValueError, 'control service gap'):
                client.service()
            client.terminal_phase = True
            self.assertIsNone(client.service())
        status = json.loads(bytes(client.telemetry.channel.sent))
        self.assertIs(status['active_control_claim'], False)

    def test_new_sequence_cannot_relabel_old_or_incomplete_resource_pair(self):
        for invalid in ('start', 'completion', 'accounting'):
            with self.subTest(invalid=invalid):
                clock = FakeClock(1.)
                client = client_fixture(clock)
                client.latest_resource = sample_record(start=.5, end=1.)
                client.resource_sequence = 1
                next_sample = sample_record(2, start=.75, end=1.1)
                if invalid == 'start':
                    next_sample['start_monotonic'] = .749999
                elif invalid == 'completion':
                    next_sample['completed_monotonic'] = 1.
                else:
                    next_sample['accounting_observations_complete'] = False
                clock.value = 1.1
                record = {**client._binding(), 'operation': 'resource',
                          'sequence': 2, 'sample': next_sample}
                client.telemetry.channel.incoming.append(json.dumps(record).encode()+b'\n')
                usage = types.SimpleNamespace(ru_utime=.01, ru_stime=0.)
                with mock.patch.object(owner.time, 'monotonic', clock), \
                        mock.patch.object(owner.resource, 'getrusage', return_value=usage):
                    with self.assertRaisesRegex(ValueError, 'start/gap/duration'):
                        client.service()
                self.assertEqual(client.resource_sequence, 1)
                self.assertEqual(client.latest_resource['start_monotonic'], .5)

    def test_scoped_resource_consumer_does_not_refresh_repeated_sequence(self):
        item = {'worker_registered_monotonic': 0.,
                'folder': '/unused/task',
                'proc': types.SimpleNamespace(pid=7, poll=lambda: None),
                'owned_pids': {7}, 'owned_pgids': {7}, 'cpu': 0.,
                'peak_rss': 0, 'last_sample': None}
        sample = sample_record(start=.5, end=1.)
        sample['table'] = {7: {'ppid': 1, 'pgid': 7, 'cpu': 2., 'rss': 1024}}
        supervision.resource_record(item, sample, 1.)
        changed_cache = {**sample, 'table': {7: {'ppid': 1, 'pgid': 7, 'cpu': 100., 'rss': 2048}}}
        supervision.resource_record(item, changed_cache, 1.2)
        self.assertEqual(item['last_sample'], 1.)
        self.assertEqual(item['resource_start'], .5)
        self.assertEqual(item['resource_sequence'], 1)
        self.assertEqual(item['cpu'], 2.)

    def test_client_takes_new_rusage_after_asynchronous_probe_wait(self):
        clock = FakeClock()
        client = client_fixture(clock)
        calls = []
        def service(*, force):
            calls.append(('service', round(clock(), 6)))
            return sample_record(start=0., end=.99) if clock() >= .99 else None
        def select_ready(*args):
            clock.value = min(.99, clock()+.2)
            return [], [], []
        def usage(which):
            calls.append(('rusage', clock()))
            return types.SimpleNamespace(ru_utime=clock(), ru_stime=0.)
        def inherited_permit(instance, funding):
            calls.append(('permit', clock()))
            self.assertIs(instance, client)
            self.assertIs(funding, funding_marker)
            return {'allowed': True, 'expires_monotonic': 1.09}
        client.service = service
        funding_marker = object()
        with mock.patch.object(owner.time, 'monotonic', clock), \
                mock.patch.object(owner.resource, 'getrusage', side_effect=usage), \
                mock.patch.object(owner.select, 'select', side_effect=select_ready) as selected, \
                mock.patch.object(owner.legacy.EntryClient, '_permit', inherited_permit):
            result = client._permit(funding_marker)
        self.assertTrue(result['allowed'])
        self.assertEqual(calls, [('service', 0.), ('service', .2), ('service', .4),
                                 ('service', .6), ('service', .8), ('service', .99),
                                 ('rusage', .99), ('permit', .99)])
        self.assertEqual(client.controller_gate_cpu, .99)
        self.assertEqual(selected.call_count, 5)

    def test_actual_worker_publication_binds_pid_and_is_one_use(self):
        clock = FakeClock(100.21)
        client = client_fixture(clock)
        client.root_path = Path('/unused/entry-owner.json')
        client.created_pid = client.created_anchor = None
        writes = []
        q = types.SimpleNamespace(write_new=lambda path, value: writes.append(value))
        process = types.SimpleNamespace(pid=701)
        with mock.patch.object(owner, 'q', q), \
                mock.patch.object(owner.time, 'monotonic', clock), \
                mock.patch.object(owner.select, 'select', return_value=([], [], [])):
            client._publish_worker(process, 100.21)
            with self.assertRaisesRegex(ValueError, 'one-use'):
                client._publish_worker(process, 100.21)
        self.assertEqual((client.created_pid, client.created_anchor), (701, 100.21))
        frame = json.loads(bytes(client.telemetry.channel.sent))
        self.assertEqual(frame, writes[0])
        self.assertEqual(frame['pid'], 701)
        self.assertEqual(frame['anchor'], 100.21)
        for name, expected in client._binding().items():
            self.assertEqual(frame[name], expected)
        self.assertEqual(len(writes), 1)

    def test_missing_or_coarse_declared_cpu_resolution_fails_consumers(self):
        for resolution in (None, .1):
            with self.subTest(resolution=resolution):
                sample = sample_record()
                if resolution is None:
                    del sample['cpu_resolution_s']
                else:
                    sample['cpu_resolution_s'] = resolution
                clock = FakeClock(.5)
                client = client_fixture(clock)
                frame = {**client._binding(), 'operation': 'resource',
                         'sequence': 1, 'sample': sample}
                client.telemetry.channel.incoming.append(json.dumps(frame).encode()+b'\n')
                usage = types.SimpleNamespace(ru_utime=.01, ru_stime=0.)
                with mock.patch.object(owner.time, 'monotonic', clock), \
                        mock.patch.object(owner.resource, 'getrusage', return_value=usage):
                    with self.assertRaisesRegex(ValueError, 'start/gap/duration'):
                        client.service()
                self.assertIsNone(client.latest_resource)
                supervisor = owner_fixture()
                with self.assertRaisesRegex(ValueError, 'CPU precision'):
                    supervisor._accept_resource(sample, .5)


def owner_fixture():
    supervisor = owner.OwnerSupervisor.__new__(owner.OwnerSupervisor)
    supervisor.proc = types.SimpleNamespace(pid=7)
    supervisor.directory = Path('/unused/owner-attempt01')
    supervisor.output = '/unused/runs'
    supervisor.policy, supervisor.task = owner.POLICY, {'id': 'task'}
    supervisor.root_sha256, supervisor.nonce = 'root', 'nonce'
    supervisor.roots = {'lock_path': '/unused/lock.json',
        'freeze_receipt_path': '/unused/freeze.json', 'accounting_path': '/unused/accounting.json',
        'expected_lock_sha256': 'lock', 'expected_freeze_receipt_sha256': 'freeze',
        'expected_accounting_sha256': 'accounting', 'expected_policy': owner.POLICY,
        'expected_cumulative_charge_s': 2541.8243213823207}
    supervisor.gate_issued = False
    supervisor.latest_resource = sample_record(start=108., end=109.)
    supervisor.anchor, supervisor.cpu0 = 100., 0.
    supervisor.capacity = 12
    supervisor.probe = types.SimpleNamespace(helper_waited_cpu_s=.2)
    supervisor.peak_cpu, supervisor.active_other_cpu = 10., 0.
    supervisor.max_uncertainty = 0.
    supervisor.status_sequence, supervisor.latest_status = 0, None
    return supervisor


def gate_fixture(supervisor):
    request = {**supervisor._binding6(), 'operation': 'prelaunch', 'entry_helpers': [],
        'precharge_sha256': 'precharge', 'controller_cpu_s': 1.,
        'controller_reaped_child_cpu_s': 0., 'controller_sample_monotonic': 110.}
    charge = {**supervisor._binding6(), 'owner_root_sha256': supervisor.root_sha256,
        'phase': 'whole_entry_precharge', 'sha256': 'precharge',
        'charged_cpu_s': 65., 'event': 'supervisor_cpu', 'nonrefundable': True}
    charge.pop('root_sha256')
    writes = []
    q = types.SimpleNamespace(finite=finite, ledger_events=lambda path: [charge],
        write_new=lambda path, value: writes.append((path, value)), sha=lambda path: 'permit')
    return request, q, writes


class OwnershipAndFundingTests(unittest.TestCase):
    def test_owner_identity_rejects_root_nonce_task_and_controller_mutations(self):
        supervisor = owner_fixture()
        for key in ('root_sha256', 'nonce', 'task', 'controller_pid', 'lock_sha256'):
            with self.subTest(key=key):
                request = supervisor._binding6()
                request[key] = 'changed'
                with self.assertRaisesRegex(ValueError, 'identity differs'):
                    supervisor._identity6(request)

    def test_owner_status_rejects_missing_reordered_stale_and_decreasing_cpu(self):
        supervisor = owner_fixture()
        clock = FakeClock(110.)
        first = {**supervisor._binding6(), 'sequence': 1,
                 'controller_cpu_s': 1., 'controller_reaped_child_cpu_s': .1,
                 'controller_sample_monotonic': 110.}
        with mock.patch.object(owner.time, 'monotonic', clock):
            supervisor._accept_status(first, supervisor.proc)
            for changed in ({'sequence': 1}, {'sequence': 3},
                            {'controller_cpu_s': .9}, {'controller_sample_monotonic': 109.9},
                            {'controller_sample_monotonic': 110.1},
                            {'controller_reaped_child_cpu_s': None}):
                with self.subTest(changed=changed):
                    value = {**first, 'sequence': 2, **changed}
                    with self.assertRaises(ValueError):
                        supervisor._accept_status(value, supervisor.proc)
                    self.assertEqual(supervisor.status_sequence, 1)

    def test_capacity_scaled_tails_exhaust_funding_before_permit_is_written(self):
        for capacity in (1, 4, 12):
            with self.subTest(capacity=capacity):
                tail = owner.uncertainty(capacity, 2.25, .1, cleanup=True)
                self.assertGreaterEqual(tail, (capacity+3) * 4.)
                # Without the uncertainty tail this exact allocation fits.
                base = owner.PACKAGE_CAP - 62.5 - 45.
                owner.funded(base, 62.5)
                with self.assertRaisesRegex(ValueError, 'funding exhausted'):
                    owner.funded(base + tail, 62.5)
        supervisor = owner_fixture()
        supervisor.roots['expected_cumulative_charge_s'] = 2800.
        request, q, writes = gate_fixture(supervisor)
        with mock.patch.object(owner, 'q', q), \
                mock.patch.object(owner.time, 'monotonic', return_value=110.), \
                mock.patch.object(owner.time, 'process_time', return_value=.1):
            with self.assertRaisesRegex(ValueError, 'funding exhausted'):
                supervisor._gate(request, supervisor.proc)
        self.assertFalse(supervisor.gate_issued)
        self.assertEqual(writes, [])

    def test_gate_requires_new_status_after_probe_wait_and_issues_once(self):
        supervisor = owner_fixture()
        request, q, writes = gate_fixture(supervisor)
        # A request timestamp carried across the resource wait consumes more
        # than the entire .25s control service allowance and cannot get a permit.
        request['controller_sample_monotonic'] = 109.7
        with mock.patch.object(owner, 'q', q), \
                mock.patch.object(owner.time, 'monotonic', return_value=110.), \
                mock.patch.object(owner.time, 'process_time', return_value=.1):
            with self.assertRaises(ValueError):
                supervisor._gate(request, supervisor.proc)
            self.assertFalse(supervisor.gate_issued)
            self.assertEqual(writes, [])
            request['controller_sample_monotonic'] = 110.
            response = supervisor._gate(request, supervisor.proc)
            permit = response['permit']
            self.assertTrue(permit['allowed'])
            self.assertEqual(permit['resource_start_monotonic'], 108.)
            self.assertLessEqual(permit['expires_monotonic'] - permit['issued_monotonic'], .100001)
            self.assertEqual(len(writes), 1)
            with self.assertRaisesRegex(ValueError, 'Only one fresh worker permit'):
                supervisor._gate(request, supervisor.proc)
        self.assertEqual(len(writes), 1)

    def test_gate_rejects_unaffordable_start_age_and_capacity_without_write(self):
        for change in ('age', 'capacity', 'observed'):
            with self.subTest(change=change):
                supervisor = owner_fixture()
                request, q, writes = gate_fixture(supervisor)
                if change == 'age':
                    supervisor.latest_resource['start_monotonic'] = 107.749999
                elif change == 'capacity':
                    supervisor.capacity = 13
                else:
                    supervisor.peak_cpu = 20.000001
                with mock.patch.object(owner, 'q', q), \
                        mock.patch.object(owner.time, 'monotonic', return_value=110.), \
                        mock.patch.object(owner.time, 'process_time', return_value=.1):
                    with self.assertRaises(ValueError):
                        supervisor._gate(request, supervisor.proc)
                self.assertFalse(supervisor.gate_issued)
                self.assertEqual(writes, [])

    def test_live_cost_requires_active_status_and_funds_owner_helpers_together(self):
        supervisor = owner_fixture()
        supervisor.terminal_phase = False
        supervisor.latest_status = {'controller_cpu_s': 1.,
            'controller_reaped_child_cpu_s': 0., 'controller_sample_monotonic': 110.}
        with mock.patch.object(owner.time, 'process_time', return_value=14.8):
            body, tail, own, monitors = supervisor._cost(110., cleanup=True)
        self.assertAlmostEqual(own + monitors, 15.)
        self.assertGreaterEqual(body, own + monitors)
        self.assertGreater(tail, 0.)
        with mock.patch.object(owner.time, 'process_time', return_value=14.800001):
            with self.assertRaisesRegex(ValueError, 'owner CPU15'):
                supervisor._cost(110., cleanup=True)
        supervisor.latest_status['controller_sample_monotonic'] = 109.749999
        with mock.patch.object(owner.time, 'process_time', return_value=.1):
            with self.assertRaisesRegex(ValueError, 'stale active controller status'):
                supervisor._cost(110., cleanup=True)

    def test_live_guard_controller_cpu_cap_includes_boundary(self):
        supervisor = owner_fixture()
        supervisor.terminal_phase = False
        supervisor.gate_controller_cpu = .5
        supervisor.worker_anchor = 110.
        supervisor.latest_status = {'controller_cpu_s': 32.,
            'controller_sample_monotonic': 110.}
        supervisor._cost = lambda now, cleanup: (10., 15., .1, .2)
        observation = supervisor._live_guard(110.)
        self.assertIs(observation['active_control_claim'], True)
        supervisor.latest_status['controller_cpu_s'] += .000001
        with self.assertRaisesRegex(ValueError, 'controller CPU31.5'):
            supervisor._live_guard(110.)

    def test_startup_guard_enforces_cost_before_any_complete_probe_or_permit(self):
        for failure in ('body', 'owner_cpu', 'funding'):
            with self.subTest(failure=failure):
                supervisor = owner_fixture()
                supervisor.latest_resource = None
                if failure == 'body':
                    supervisor.peak_cpu = 20.000001
                if failure == 'funding':
                    supervisor.roots['expected_cumulative_charge_s'] = 2800.
                own = 14.800001 if failure == 'owner_cpu' else .1
                with mock.patch.object(owner.time, 'process_time', return_value=own):
                    with self.assertRaisesRegex(ValueError, 'provision exhausted|funding exhausted'):
                        supervisor._startup_guard(110.)
                self.assertFalse(supervisor.gate_issued)

    def test_terminal_cost_retains_larger_live_uncertainty_highwater(self):
        supervisor = owner_fixture()
        supervisor.terminal_phase = False
        supervisor.latest_status = {'controller_cpu_s': 1.,
            'controller_reaped_child_cpu_s': 0., 'controller_sample_monotonic': 110.}
        supervisor.latest_resource['start_monotonic'] = 107.75
        with mock.patch.object(owner.time, 'process_time', return_value=.1):
            _, live_tail, _, _ = supervisor._cost(110., cleanup=True)
            supervisor.terminal_phase = True
            supervisor.latest_resource = sample_record(2, start=110., end=110.25)
            body, terminal_tail, own, helpers = supervisor._cost(110.25, cleanup=True)
        self.assertLess(terminal_tail, live_tail)
        self.assertEqual(supervisor.max_uncertainty, live_tail)
        self.assertAlmostEqual(body, 10.25 + own + helpers)
        self.assertEqual(helpers, .2)


class WatchdogResourceTests(unittest.TestCase):
    def metadata(self, folder, *, contract='codex_local_campaign.watch_parent; inherited PGID'):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        value = {'worker_pid': 5, 'watchdog_pid': 6, 'owned_pgids': [5],
                 'watchdog_contract': contract}
        (folder/'owned-processes.json').write_text(json.dumps(value))

    def worker_item(self, folder):
        return {'folder': str(folder), 'worker_registered_monotonic': 0.,
                'proc': types.SimpleNamespace(pid=5, poll=lambda: None),
                'owned_pids': {5}, 'owned_pgids': {5}, 'cpu': 0.,
                'peak_rss': 0, 'last_sample': None}

    def worker_sample(self, *, reparented=False):
        sample = sample_record()
        sample['table'] = {5: {'ppid': 7, 'pgid': 5, 'cpu': 2., 'rss': 30},
            6: {'ppid': 1 if reparented else 5, 'pgid': 5, 'cpu': .25, 'rss': 40}}
        return sample

    def owner_sample(self, supervisor, folder, *, reparented=False, worker_present=True):
        supervisor.output, supervisor.task = str(folder.parent), {'id': folder.name}
        supervisor.proc = types.SimpleNamespace(pid=7, poll=lambda: None)
        supervisor.anchor = 0.
        supervisor.latest_resource = supervisor.pending_resource = None
        supervisor.worker_pid, supervisor.worker_anchor, supervisor.watchdog_pid = 5, 0., None
        supervisor.gate_issued, supervisor.terminal_phase = True, False
        supervisor.owned_pids, supervisor.groups = {7, 5}, {7, 5}
        supervisor.peak_cpu = supervisor.active_other_cpu = 0.
        supervisor.peak_rss = 0
        supervisor.resource_channel = owner.FrameChannel(FakeSocket())
        supervisor.latest_status = {'controller_cpu_s': 1.,
            'controller_reaped_child_cpu_s': 0., 'controller_sample_monotonic': .5}
        sample = self.worker_sample(reparented=reparented)
        sample.update(deadline=1., registered_probe_pids=[101, 102])
        sample['table'].update({1: {'ppid': 0, 'pgid': 1, 'cpu': .1, 'rss': 10},
            7: {'ppid': 1, 'pgid': 7, 'cpu': 1., 'rss': 20},
            101: {'ppid': 1, 'pgid': 101, 'cpu': .01, 'rss': 5},
            102: {'ppid': 1, 'pgid': 102, 'cpu': .01, 'rss': 5}})
        if not worker_present:
            del sample['table'][5]
        return sample

    def test_scoped_consumer_accepts_only_registered_same_group_watchdog(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'task'
            self.metadata(folder)
            for reparented in (False, True):
                with self.subTest(reparented=reparented):
                    item = self.worker_item(folder)
                    supervision.resource_record(item, self.worker_sample(reparented=reparented), .5)
                    self.assertEqual(item['owned_pids'], {5, 6})
                    self.assertEqual(item['owned_pgids'], {5})
                    self.assertEqual(item['cpu'], 2.25)
                    self.assertEqual(item['peak_rss'], 70)

    def test_scoped_consumer_rejects_unknown_pid_group_and_bad_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'task'
            for failure in ('unknown_pid', 'wrong_group', 'contract', 'arbitrary_parent'):
                with self.subTest(failure=failure):
                    self.metadata(folder, contract='changed' if failure == 'contract'
                                  else 'codex_local_campaign.watch_parent; inherited PGID')
                    item, sample = self.worker_item(folder), self.worker_sample()
                    if failure == 'unknown_pid':
                        sample['table'][8] = {'ppid': 5, 'pgid': 5, 'cpu': .01, 'rss': 1}
                    elif failure == 'wrong_group':
                        sample['table'][6]['pgid'] = 6
                    elif failure == 'arbitrary_parent':
                        sample['table'][6]['ppid'] = 99
                    with self.assertRaisesRegex(ValueError, 'Unregistered|contract differs|ancestry/group'):
                        supervision.resource_record(item, sample, .5)
                    self.assertIsNone(item['last_sample'])
                    self.assertNotIn('resource_sequence', item)

    def test_owner_includes_exact_watchdog_and_probe_rss_with_waited_helper_cpu(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'task'
            self.metadata(folder)
            for reparented, worker_present in ((False, True), (True, True), (True, False)):
                with self.subTest(reparented=reparented, worker_present=worker_present):
                    supervisor = owner_fixture()
                    sample = self.owner_sample(supervisor, folder, reparented=reparented,
                                               worker_present=worker_present)
                    with mock.patch.object(owner.os, 'getpid', return_value=1), \
                            mock.patch.object(owner.time, 'monotonic', return_value=.5), \
                            mock.patch.object(owner.time, 'process_time', return_value=.1):
                        supervisor._resource(sample, .5)
                        body, tail, own, helpers = supervisor._cost(.5, cleanup=True)
                    expected_cpu, expected_rss = (3.25, 110) if worker_present else (1.25, 80)
                    self.assertEqual(supervisor.watchdog_pid, 6)
                    self.assertIn(6, supervisor.owned_pids)
                    self.assertEqual(supervisor.peak_cpu, expected_cpu)
                    self.assertEqual(supervisor.peak_rss, expected_rss)
                    self.assertAlmostEqual(body, expected_cpu + own + helpers)
                    self.assertEqual(helpers, .2)
                    self.assertGreaterEqual(supervisor.max_uncertainty, tail)
                    frame = json.loads(bytes(supervisor.resource_channel.outgoing))
                    self.assertTrue({101, 102, 6}.issubset({int(pid) for pid in frame['sample']['table']}))

    def test_owner_rejects_escaped_child_and_arbitrary_watchdog_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)/'task'
            self.metadata(folder)
            for failure in ('escaped_child', 'arbitrary_parent'):
                with self.subTest(failure=failure):
                    supervisor = owner_fixture()
                    sample = self.owner_sample(supervisor, folder)
                    if failure == 'escaped_child':
                        del sample['table'][6]
                        sample['table'][8] = {'ppid': 5, 'pgid': 8, 'cpu': .01, 'rss': 1}
                    else:
                        sample['table'][6]['ppid'] = 99
                    with mock.patch.object(owner.os, 'getpid', return_value=1), \
                            mock.patch.object(owner.time, 'monotonic', return_value=.5):
                        with self.assertRaisesRegex(ValueError, 'Unregistered numerical descendant|ancestry/group'):
                            supervisor._resource(sample, .5)
                    self.assertIsNone(supervisor.latest_resource)
                    self.assertEqual(supervisor.resource_channel.outgoing, b'')


class FinalPopenGuardTests(unittest.TestCase):
    """Exercise the inherited physical guard through its v6 EntryClient API."""

    def fixture(self, *, popen_error=None):
        clock = FakeClock(100.21)
        client = owner.EntryClient.__new__(owner.EntryClient)
        client.owner_thread = threading.get_ident()
        client.in_scope = client.charged = True
        client.used = client.worker_creation = False
        client.current_permit_expiry = 100.25
        client.created_pid = client.created_anchor = client.publication_failure = None
        client.task = {'id': 'task', 'protocol_revision': 6}
        client.output = '/unused/responsive-v6/runs'
        client.roots = {'expected_lock_sha256': 'lock', 'lock_path': '/unused/lock.json'}
        client.root = {'anchor': 100.}
        client.root_path = Path('/unused/entry-owner.json')
        client.gate_sha256 = 'gate'
        client._identity = mock.Mock()
        client._publish_worker = mock.Mock()
        client._binding = lambda: {'root_sha256': 'root', 'nonce': 'nonce',
            'controller_pid': 7, 'policy': owner.POLICY, 'task': client.task,
            'output': client.output, 'lock_sha256': 'lock'}
        client.telemetry = owner.FrameChannel(FakeSocket(), clock=clock)
        permit = {'expires_monotonic': 100.25}
        client._permit = lambda funding: permit
        folder = Path(client.output)/client.task['id']
        attempt = {'task': client.task, 'lock_sha256': 'lock', 'parent_monotonic': 100.21}
        readback = {'permit': permit}
        def read(path):
            return readback['permit'] if Path(path).name == 'entry-owner-gate.json' else attempt
        process = types.SimpleNamespace(pid=701)
        popen = mock.Mock(return_value=process, side_effect=popen_error)
        q = types.SimpleNamespace(subprocess=types.SimpleNamespace(Popen=popen),
            finite=finite, read=read, sha=lambda path: 'gate')
        arguments = types.SimpleNamespace(lock='/unused/lock.json', output=client.output)
        funding = mock.Mock(return_value={'charged_cpu_s': 2600.})
        def delegate(args, task, output, locksha):
            proc = q.subprocess.Popen([sys.executable, *owner.WORKER_PREFIX,
                '--lock', str(Path(args.lock).resolve()), '--output', str(folder.resolve()),
                '--parent-pid', str(os.getpid()), '--ack-fd', '9'],
                start_new_session=True, pass_fds=(9,))
            return {'proc': proc, 'task': task, 'anchor': 100.21, 'folder': str(folder)}
        return clock, client, q, arguments, funding, delegate, popen, readback

    def test_final_popen_consumes_permit_once_and_restores_constructor(self):
        clock, client, q, args, funding, delegate, popen, readback = self.fixture()
        with owner.legacy_bindings(), mock.patch.object(owner.legacy, 'q', q), \
                mock.patch.object(owner, 'q', q), \
                mock.patch.object(owner.time, 'monotonic', clock):
            result = client.launch_guard(args, client.task, client.output, 'lock',
                delegate=delegate, funding_check=funding)
            self.assertEqual(result['proc'].pid, 701)
            self.assertTrue(client.used)
            self.assertFalse(client.worker_creation)
            self.assertIs(q.subprocess.Popen, popen)
            with self.assertRaises((RuntimeError, ValueError)):
                client.launch_guard(args, client.task, client.output, 'lock',
                    delegate=delegate, funding_check=funding)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(funding.call_count, 2)

    def test_expired_or_changed_final_readback_prevents_physical_popen(self):
        for failure in ('expired', 'readback'):
            with self.subTest(failure=failure):
                clock, client, q, args, funding, delegate, popen, readback = self.fixture()
                def delayed_delegate(*arguments):
                    if failure == 'expired':
                        clock.value = 100.250001
                    else:
                        readback['permit'] = {'expires_monotonic': 100.26}
                    return delegate(*arguments)
                with owner.legacy_bindings(), mock.patch.object(owner.legacy, 'q', q), \
                        mock.patch.object(owner, 'q', q), \
                        mock.patch.object(owner.time, 'monotonic', clock):
                    with self.assertRaises((RuntimeError, ValueError)):
                        client.launch_guard(args, client.task, client.output, 'lock',
                            delegate=delayed_delegate, funding_check=funding)
                    self.assertIs(q.subprocess.Popen, popen)
                self.assertEqual(popen.call_count, 0)

    def test_failed_physical_popen_still_consumes_permit_and_cannot_retry(self):
        clock, client, q, args, funding, delegate, popen, readback = self.fixture(
            popen_error=OSError('injected physical Popen failure'))
        with owner.legacy_bindings(), mock.patch.object(owner.legacy, 'q', q), \
                mock.patch.object(owner, 'q', q), \
                mock.patch.object(owner.time, 'monotonic', clock):
            with self.assertRaisesRegex(OSError, 'physical Popen failure'):
                client.launch_guard(args, client.task, client.output, 'lock',
                    delegate=delegate, funding_check=funding)
            self.assertTrue(client.used)
            self.assertFalse(client.worker_creation)
            self.assertIs(q.subprocess.Popen, popen)
            with self.assertRaises((RuntimeError, ValueError)):
                client.launch_guard(args, client.task, client.output, 'lock',
                    delegate=delegate, funding_check=funding)
        self.assertEqual(popen.call_count, 1)

    def test_publication_failure_keeps_created_process_visible_for_cleanup(self):
        clock, client, q, args, funding, delegate, popen, readback = self.fixture()
        client._publish_worker = types.MethodType(owner.EntryClient._publish_worker, client)
        q.write_new = mock.Mock(side_effect=OSError('injected durable publication failure'))
        with owner.legacy_bindings(), mock.patch.object(owner.legacy, 'q', q), \
                mock.patch.object(owner, 'q', q), \
                mock.patch.object(owner.time, 'monotonic', clock), \
                mock.patch.object(owner.os, 'killpg') as signalled:
            item = client.launch_guard(args, client.task, client.output, 'lock',
                delegate=delegate, funding_check=funding)
            self.assertEqual(item['proc'].pid, 701)
            self.assertEqual((client.created_pid, client.created_anchor), (701, 100.21))
            self.assertTrue(client.used)
            self.assertIn('durable publication failure', client.publication_failure['error'])
            with self.assertRaisesRegex(RuntimeError, 'publication failed'):
                client.worker_created(item)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(signalled.call_args.args[0], 701)


class OwnerTimerIntegrationTests(unittest.TestCase):
    def test_pending_probe_cannot_delay_stop_or_extend_native_cleanup_deadline(self):
        # Admission/cost guards have independent tests above. Here they are
        # replaced to isolate the actual owner's timer and final cleanup paths.
        # The deliberately never-completing probe is a scheduling fault fixture,
        # not a sample that could pass the real Probe's one-second deadline.
        for cleanup_fails in (False, True):
            with self.subTest(cleanup_fails=cleanup_fails), tempfile.TemporaryDirectory() as temporary:
                clock = FakeClock()
                supervisor = owner_fixture()
                supervisor.directory = Path(temporary)/'owner'
                controller = types.SimpleNamespace(pid=7, returncode=None, poll=lambda: None)
                control, child, telemetry, child_telemetry = [FakeSocket() for _ in range(4)]
                control.incoming.append(b'{}\n')
                writes, signals, cleanup_deadlines, pumps = {}, [], [], []
                class PendingProbe:
                    def __init__(self, *args, **kwargs):
                        self.active = self.closed = False
                        self.latest = None
                        self.filenos = ()
                        self.helper_waited_cpu_s = .4
                    def start(self, now, deadline):
                        self.active = True
                    def pump(self, now):
                        pumps.append(now)
                        return None
                    def close(self, deadline):
                        self.closed = True
                        return {'complete': True, 'accounting_observations_complete': True}
                def gate(request, proc):
                    supervisor.gate_issued = True
                    supervisor.worker_pid, supervisor.worker_anchor = 9, 0.
                    supervisor.groups.add(9)
                    supervisor.owned_pids.add(9)
                    return {'allowed': True}
                supervisor._gate = gate
                def live_guard(now):
                    supervisor.max_uncertainty = max(supervisor.max_uncertainty, 37.5)
                    return {}
                supervisor._live_guard = live_guard
                def select_ready(*args):
                    clock.advance(.125)
                    return [], [], []
                def stop_owned(proc, groups, *, deadline):
                    cleanup_deadlines.append(deadline)
                    if cleanup_fails:
                        raise OSError('injected controller cleanup failure')
                    return {'group_absent': False, 'cleanup_errors': []}
                def write(path, value):
                    writes[Path(path).name] = value
                q = types.SimpleNamespace(THREAD_KEYS=(), finite=finite,
                    write_new=write, sha=lambda path: 'root',
                    group_probe=lambda pid: {'state': 'present'}, stop_owned=stop_owned)
                usage = types.SimpleNamespace(ru_utime=0., ru_stime=0.)
                with mock.patch.object(owner, 'q', q), \
                        mock.patch.object(owner, 'Probe', PendingProbe), \
                        mock.patch.object(owner.os, 'cpu_count', return_value=12), \
                        mock.patch.object(owner.os, 'killpg', side_effect=lambda pid, sig: signals.append((clock(), pid, sig))), \
                        mock.patch.object(owner.time, 'monotonic', clock), \
                        mock.patch.object(owner.time, 'process_time', return_value=0.), \
                        mock.patch.object(owner.select, 'select', side_effect=select_ready), \
                        mock.patch.object(owner.socket, 'socketpair', side_effect=[(control, child), (telemetry, child_telemetry)]), \
                        mock.patch.object(owner.subprocess, 'Popen', return_value=controller), \
                        mock.patch.object(owner.resource, 'getrusage', return_value=usage), \
                        mock.patch.object(owner.signal, 'signal', return_value=None), \
                        mock.patch.object(owner.secrets, 'token_hex', return_value='nonce'):
                    with self.assertRaisesRegex(RuntimeError, 'did not close complete observations'):
                        supervisor.run([sys.executable, '-m', 'experiments.cf1_responsive_supervision', 'run'])
                native_signals = [when for when, pid, sig in signals if pid == 9]
                self.assertEqual(native_signals[0], 61.)
                self.assertEqual(cleanup_deadlines, [62.5])
                self.assertGreater(len(pumps), 400)
                receipt = writes['owner-receipt.json']
                self.assertEqual(receipt['failure']['type'], 'TimeoutError')
                self.assertIn('62.5', receipt['failure']['error'])
                self.assertFalse(receipt['accounting_observations_complete'])
                self.assertEqual(receipt['probe_waited_cpu_s'], .4)
                self.assertEqual(receipt['conservative_uncertainty_highwater_s'], 37.5)
                self.assertEqual(receipt['charged_cpu_s'], receipt['whole_owner_elapsed_s'] + 37.5)
                if cleanup_fails:
                    self.assertTrue(any(error['stage'] == 'controller_cleanup'
                        and 'injected controller cleanup failure' in error['error']
                        for error in receipt['secondary_errors']))


class ScopedBindingTests(unittest.TestCase):
    def test_revision6_restores_real_hooks_and_policy_after_exception(self):
        q = supervision.adapter.q
        targets = [(supervision.legacy, name) for name in (
            'POLICY', 'ENTRY_PRECHARGE_S', 'SUPERVISION_RESERVE_S', 'entry_owner', '_CONFIG_LOCK')]
        targets += [(q, name) for name in ('CEILING', 'DISPATCH_STOP', 'SHUTDOWN_RESERVE', 'run', 'receive_ack')]
        targets += [(supervision.approved, 'revision4'),
                    (supervision.adapter, 'WORKER_ARGV_PREFIX'),
                    (supervision.adapter, 'FREEZE_ELAPSED_LIMIT_S'), (owner.legacy, 'POLICY')]
        saved = [(target, name, getattr(target, name)) for target, name in targets]
        with mock.patch.object(owner.subprocess, 'Popen', side_effect=AssertionError('scope must not spawn')), \
                mock.patch.object(owner.subprocess, 'run', side_effect=AssertionError('scope must not run commands')):
            with self.assertRaisesRegex(RuntimeError, 'injected scoped exit'):
                with supervision.revision6():
                    self.assertIs(q.run, supervision.responsive_run)
                    self.assertIs(q.receive_ack, supervision.receive_ack)
                    self.assertEqual(supervision.legacy.POLICY, supervision.POLICY)
                    self.assertEqual(owner.legacy.POLICY, owner.POLICY)
                    self.assertEqual(supervision.adapter.FREEZE_ELAPSED_LIMIT_S, 17.5)
                    raise RuntimeError('injected scoped exit')
        for target, name, value in saved:
            with self.subTest(module=target.__name__, attribute=name):
                self.assertIs(getattr(target, name), value)
