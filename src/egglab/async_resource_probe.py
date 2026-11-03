"""Bounded resource probe pairs for the single-thread responsive supervisor.

This collector never waits for a process, a pipe, or a selector. Its caller must
service control/ACK/timers before each bounded ``pump`` and schedule ``start``
explicitly. It provides sampled observations, not continuous containment.
The selector belongs only to this collector; ``filenos`` may additionally be
watched by the caller's control selector. No legacy monitor globals are changed.
"""
import math
import os
import re
import selectors
import signal
import subprocess
import time


COMMANDS = (
    ('/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss=,time='),
    ('/usr/bin/memory_pressure', '-Q'),
)
MIN_START_INTERVAL_S = .25
MAX_PAIR_S = 1.
MAX_COMPLETED_GAP_S = 1.25
MAX_START_AGE_S = 2.25
READ_CHUNK_BYTES = 16384
MAX_READY_STREAMS = 4
MAX_PARSE_BYTES = 16384
MAX_PARSE_LINES = 256
MAX_LINE_BYTES = 4096
MAX_PS_BYTES = 1024*1024
MAX_MEMORY_BYTES = 65536
MAX_STDERR_BYTES = 16384
MAX_TABLE_ROWS = 16384
MAX_PAIRS = 1024
_FREE = re.compile(r'^\s*System-wide memory free percentage:\s*(\d{1,3})%\s*$')
_CPU = re.compile(r'^(?:\d+-)?\d+(?::\d+){0,2}(?:\.\d+)?$')


class ProbeError(RuntimeError):
    def __init__(self, message, *, context='resource_probe', **details):
        self.diagnostic = {'error_type': type(self).__name__, 'error': message,
                           'context': context, **details}
        super().__init__(message)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _waited_child(proc):
    """Reap this PID only; do not mislabel other children's CPU as probe CPU."""
    pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
    if not pid:
        return None, None
    code = os.waitstatus_to_exitcode(status)
    proc.returncode = code
    return code, usage.ru_utime+usage.ru_stime


def _group_state(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return 'absent'
    except PermissionError:
        return 'unknown'
    return 'present'


def _seconds(value):
    # Same day/hour/minute conversion as campaign.seconds, with bounded input
    # and explicit finite/nonnegative validation before a sample is accepted.
    if not _CPU.fullmatch(value):
        raise ValueError('Invalid process CPU time')
    fraction = value.rsplit(':', 1)[-1].partition('.')[2]
    if len(fraction) < 2:
        raise ValueError('Process CPU TIME requires at least two fractional decimal digits')
    days = 0
    if '-' in value:
        raw_days, value = value.split('-', 1)
        days = int(raw_days)
    parts = [float(part) for part in value.split(':')]
    result = days*86400+sum(part*60**index for index, part in enumerate(reversed(parts)))
    if not _finite(result) or result < 0:
        raise ValueError('Invalid process CPU observation')
    return result


class Probe:
    """One fixed concurrent ps/memory pair; all APIs are nonblocking.

    ``reap(proc)`` is injectable and returns ``(returncode, waited_cpu_s)`` or
    ``(None, None)`` while live. Real probe Popen objects must not be polled or
    reaped elsewhere. ``group_probe(pgid)`` returns absent/present/unknown.
    ``register`` receives a spawn metadata dict before its streams are accepted.
    Fake selectors implement register/unregister/select(0)/close; fake streams
    implement fileno/close, and ``read(fd, bound)`` may raise BlockingIOError.

    ``close(deadline)`` initiates cleanup and returns a current receipt. Continue
    pumping until ``closed``; a deadline expiry records incomplete cleanup and
    never invents a reap. An error initiates at most a 1.5s cleanup tail, clipped
    to phase end+1.5; the owner can shorten it with its actual outer deadline.
    """
    def __init__(self, q=None, *, root_pid, capacity, clock=time.monotonic,
                 popen=subprocess.Popen, selector=None, read=os.read,
                 set_blocking=os.set_blocking, killpg=os.killpg,
                 register=None, reap=None, group_probe=None):
        if type(root_pid) is not int or root_pid <= 0:
            raise ValueError('Require a positive independently owned root PID')
        if type(capacity) is not int or not 1 <= capacity <= 12:
            raise ValueError('Resource policy requires capacity at most twelve')
        self.q, self.root_pid, self.capacity = q, root_pid, capacity
        self.clock, self.popen, self.read = clock, popen, read
        self.set_blocking, self.killpg, self.register = set_blocking, killpg, register
        self.reap = _waited_child if reap is None else reap
        self.group_probe = _group_state if group_probe is None else group_probe
        self.selector = selectors.DefaultSelector() if selector is None else selector
        self._processes, self._streams = {}, {}
        self._retired = []
        self._unregistered_spawn = False
        self._pair = self._latest = None
        self._last_start = self._last_completed = self._last_observed = None
        self._sequence = 0
        self._closing = self._closed = False
        self._cleanup_deadline = self._kill_at = None
        self._helper_waited_cpu_s = 0.
        self._observations_complete = True
        self.primary_failure, self.cleanup_errors = None, []
        self._cleanup_error_keys = set()
        self._observe()

    def _observe(self, supplied=None):
        actual = self.clock()
        if (not _finite(actual) or actual < 0
                or self._last_observed is not None and actual < self._last_observed
                or supplied is not None and (not _finite(supplied) or supplied > actual)):
            raise ProbeError('Invalid or future probe clock observation', context='probe_clock')
        self._last_observed = actual
        return actual

    @property
    def active(self):
        return self._pair is not None and not self._closing

    @property
    def closed(self):
        return self._closed

    @property
    def filenos(self):
        return tuple(self._streams)

    @property
    def owned_pids(self):
        return set(self._processes)

    @property
    def owned_pgids(self):
        return {item['pgid'] for item in self._processes.values()}

    @property
    def live_pids(self):
        return {pid for pid, item in self._processes.items()
                if not item['reaped'] or item['group_state'] != 'absent'}

    @property
    def live_pgids(self):
        return {self._processes[pid]['pgid'] for pid in self.live_pids}

    @property
    def helper_waited_cpu_s(self):
        return self._helper_waited_cpu_s

    @property
    def accounting_observations_complete(self):
        return self._observations_complete

    @property
    def latest(self):
        # Copy the header only; the caller treats the bounded table as read-only.
        # Crucially, neither timestamp nor sequence changes on cache access.
        return None if self._latest is None else dict(self._latest)

    @property
    def next_start_monotonic(self):
        if self._last_start is None:
            return self._last_observed
        return max(self._last_start+MIN_START_INTERVAL_S,
                   self._last_completed if self._last_completed is not None else self._last_start)

    @property
    def next_deadline(self):
        if self._closed:
            return None
        if self._closing:
            return min(self._cleanup_deadline, self._kill_at)
        if self._pair is not None:
            end = self._pair['deadline']
            return end if self._last_completed is None else min(end, self._last_completed+MAX_COMPLETED_GAP_S)
        return self.next_start_monotonic

    def start(self, now, deadline):
        now = self._observe(now)
        if self._closing or self._closed or self.primary_failure is not None:
            raise ProbeError('Closed or failed probe cannot start another pair')
        if self._pair is not None:
            self._fail('A probe pair is already live', now, context='probe_start')
        if not _finite(deadline) or deadline <= now:
            self._fail('No remaining absolute probe work time', now, context='probe_start')
        if self._last_start is not None and now < self._last_start+MIN_START_INTERVAL_S:
            self._fail('Minimum probe-start interval violated', now, context='probe_cadence')
        if self._last_completed is not None and now > self._last_completed+.25:
            self._fail('Next probe did not start within .25s of completion', now, context='probe_cadence')
        if self._sequence >= MAX_PAIRS:
            self._fail('Bounded probe-pair inventory exhausted', now, context='probe_inventory')
        self._sequence += 1
        self._pair = {'sequence': self._sequence, 'start_monotonic': now,
            'deadline': min(now+MAX_PAIR_S, deadline), 'phase_deadline': deadline,
            'pids': [], 'table': {}, 'free': None, 'cpu_resolution_s': 0.}
        pending_proc = None
        try:
            for index, command in enumerate(COMMANDS):
                started = self._observe()
                if index == 0:
                    if self._last_completed is not None and started > self._last_completed+.25:
                        raise ProbeError('Next probe actual START missed service deadline')
                    # Stamp immediately before the first Popen, never on delivery
                    # or a cache read. This bounds both helper lifetimes from START.
                    self._last_start = self._pair['start_monotonic'] = started
                    self._pair['deadline'] = min(started+MAX_PAIR_S, deadline)
                if started > self._pair['deadline']:
                    raise ProbeError('Probe pair startup exceeded deadline')
                proc = self.popen(list(command), stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    start_new_session=True, close_fds=True, bufsize=0)
                pending_proc = proc
                if type(proc.pid) is not int or proc.pid <= 0:
                    raise ProbeError('Invalid probe PID')
                previous = self._processes.get(proc.pid)
                if previous is not None:
                    if not previous['reaped'] or previous['group_state'] != 'absent':
                        raise ProbeError('Probe PID aliases a live registered process')
                    self._retired.append(self._process_metadata(previous))
                item = {'proc': proc, 'pid': proc.pid, 'pgid': proc.pid,
                    'command': list(command), 'kind': 'ps' if index == 0 else 'memory',
                    'start_monotonic': started, 'exit_observed_monotonic': None,
                    'returncode': None, 'reaped': False, 'waited_cpu_s': None,
                    'group_state': 'present', 'stdout_eof': False, 'stderr_eof': False,
                    'stdout_pending': bytearray(), 'stdout_total': 0, 'stderr_total': 0,
                    'stderr': bytearray(), 'terminated': False, 'killed': False}
                # Registration precedes pipe acceptance, including partial startup.
                self._processes[proc.pid] = item
                self._pair['pids'].append(proc.pid)
                pending_proc = None
                if self.register is not None:
                    self.register({'sequence': self._sequence, **{key: item[key] for key in
                        ('pid', 'pgid', 'command', 'start_monotonic')}})
                for name in ('stdout', 'stderr'):
                    stream = getattr(proc, name)
                    fd = stream.fileno()
                    if type(fd) is not int or fd < 0 or fd in self._streams:
                        raise ProbeError('Invalid or aliased probe pipe')
                    self.set_blocking(fd, False)
                    self._streams[fd] = {'item': item, 'name': name, 'stream': stream}
                    self.selector.register(fd, selectors.EVENT_READ, fd)
                if self._observe() > self._pair['deadline']:
                    raise ProbeError('Probe pair startup exceeded deadline')
        except BaseException as exc:
            if pending_proc is not None:
                self._unregistered_spawn = True
                self._observations_complete = False
                for name in ('stdout', 'stderr'):
                    try:
                        stream = getattr(pending_proc, name, None)
                        if stream is not None:
                            stream.close()
                    except Exception as cleanup_exc:
                        self._cleanup_error('unregistered', 'partial_pipe_close', cleanup_exc)
            self._fail(str(exc), self._observe(), context='probe_spawn', cause=exc)

    def _drop_stream(self, fd):
        value = self._streams.pop(fd, None)
        if value is None:
            return
        try:
            self.selector.unregister(fd)
        except Exception as exc:
            self._cleanup_error(fd, 'selector_unregister', exc)
        try:
            value['stream'].close()
        except Exception as exc:
            self._cleanup_error(fd, 'pipe_close', exc)

    def _drain(self):
        # Dedicated selector only. Bound both event count and bytes per pump.
        events = self.selector.select(0)
        for key, mask in events[:MAX_READY_STREAMS]:
            fd = key.fd
            stream = self._streams.get(fd)
            if stream is None:
                continue
            try:
                raw = self.read(fd, READ_CHUNK_BYTES)
            except (BlockingIOError, InterruptedError):
                continue
            if type(raw) is not bytes:
                raise ProbeError('Probe pipe returned non-bytes')
            if len(raw) > READ_CHUNK_BYTES:
                raise ProbeError('Probe read exceeded requested byte bound')
            item, name = stream['item'], stream['name']
            if not raw:
                item[name+'_eof'] = True
                self._drop_stream(fd)
                continue
            item[name+'_total'] += len(raw)
            limit = (MAX_STDERR_BYTES if name == 'stderr' else
                     MAX_PS_BYTES if item['kind'] == 'ps' else MAX_MEMORY_BYTES)
            if item[name+'_total'] > limit:
                raise ProbeError('Probe output exceeded bound', context='probe_output',
                                 pid=item['pid'], stream=name, limit_bytes=limit)
            item['stderr' if name == 'stderr' else 'stdout_pending'].extend(raw)
            if self._observe() > self._pair['deadline']:
                raise ProbeError('Probe output drain exceeded pair deadline')

    def _parse(self):
        used = count = 0
        for pid in self._pair['pids']:
            item = self._processes[pid]
            pending = item['stdout_pending']
            while pending and count < MAX_PARSE_LINES and used < MAX_PARSE_BYTES:
                cut = pending.find(b'\n', 0, MAX_LINE_BYTES+1)
                if cut < 0:
                    if len(pending) > MAX_LINE_BYTES:
                        raise ProbeError('Probe output line exceeded bound')
                    if not item['stdout_eof']:
                        break
                    cut = len(pending)
                size = cut+(cut < len(pending))
                if size > MAX_PARSE_BYTES-used:
                    break
                line = bytes(pending[:cut]).decode('ascii', errors='strict')
                del pending[:size]
                used += size
                count += 1
                if not line.strip():
                    continue
                if item['kind'] == 'ps':
                    fields = line.split()
                    if len(fields) != 5:
                        raise ProbeError('Malformed process snapshot row')
                    if any(len(field) > 20 for field in fields[:4]):
                        raise ProbeError('Process numeric field exceeded bound')
                    proc_id, parent, group, rss = map(int, fields[:4])
                    cpu = _seconds(fields[4])
                    digits = len(fields[4].rsplit(':', 1)[-1].partition('.')[2])
                    # Raw column quantum plus a conservative upper envelope for
                    # positive day/hour/minute conversion rounding. A caller's
                    # 2*resolution tail covers their sum, never an assumed .01.
                    resolution = max(10.**-digits, 16*math.ulp(cpu))
                    if not _finite(resolution) or not 0 < resolution <= .01:
                        raise ProbeError('Process CPU TIME precision is coarser than .01s')
                    self._pair['cpu_resolution_s'] = max(self._pair['cpu_resolution_s'], resolution)
                    if min(proc_id, parent, group, rss) < 0 or proc_id in self._pair['table']:
                        raise ProbeError('Invalid or duplicate process snapshot identity')
                    self._pair['table'][proc_id] = {'ppid': parent, 'pgid': group,
                                                  'rss': rss*1024, 'cpu': cpu}
                    if len(self._pair['table']) > MAX_TABLE_ROWS:
                        raise ProbeError('Process snapshot row bound exceeded')
                else:
                    match = _FREE.fullmatch(line)
                    if match:
                        free = float(match.group(1))
                        if not 0 <= free <= 100 or self._pair['free'] is not None:
                            raise ProbeError('Invalid or duplicate memory observation')
                        self._pair['free'] = free
                if self._observe() > self._pair['deadline']:
                    raise ProbeError('Bounded parsing exceeded pair deadline')

    def _reap(self):
        for item in self._processes.values():
            if item['reaped']:
                continue
            try:
                code, cpu = self.reap(item['proc'])
            except Exception as exc:
                self._observations_complete = False
                if self._closing:
                    self._cleanup_error(item['pid'], 'probe_reap', exc)
                    continue
                raise ProbeError('Probe waited accounting unavailable', pid=item['pid']) from exc
            if code is None:
                continue
            item['returncode'], item['reaped'] = code, True
            item['exit_observed_monotonic'] = self._observe()
            if type(code) is not int or not _finite(cpu) or cpu < 0:
                self._observations_complete = False
                if self._closing:
                    self._cleanup_error(item['pid'], 'probe_waited_cpu', ValueError('Unknown waited CPU'))
                    continue
                raise ProbeError('Invalid waited probe accounting', pid=item['pid'])
            item['waited_cpu_s'] = cpu
            self._helper_waited_cpu_s += cpu
            if code != 0 and not self._closing:
                raise ProbeError('Resource helper exited unsuccessfully', pid=item['pid'], returncode=code)

    def pump(self, now):
        now = self._observe(now)
        if self._closed:
            return None
        if self._closing:
            self._cleanup_tick(now)
            return None
        if self._pair is None:
            if self._last_completed is not None and now > self._last_completed+.25:
                self._fail('Next probe start service deadline missed', now, context='probe_cadence')
            return None
        try:
            if now > self._pair['deadline']:
                raise ProbeError('Resource pair deadline exceeded', deadline=self._pair['deadline'])
            if self._last_completed is not None and now > self._last_completed+MAX_COMPLETED_GAP_S:
                raise ProbeError('Completed resource pair gap exceeded')
            self._reap()
            self._drain()
            self._parse()
            items = [self._processes[pid] for pid in self._pair['pids']]
            if len(items) != 2 or not all(item['reaped'] and item['stdout_eof'] and
                    item['stderr_eof'] and not item['stdout_pending'] for item in items):
                return None
            if self.root_pid not in self._pair['table'] or self._pair['free'] is None:
                raise ProbeError('Incomplete process/memory pair')
            if self.cleanup_errors:
                raise ProbeError('Resource probe pipe cleanup reported errors')
            for item in items:
                item['group_state'] = self.group_probe(item['pgid'])
                if item['group_state'] != 'absent':
                    raise ProbeError('Resource helper group absence unconfirmed', pid=item['pid'])
            completed = self._observe()
            if completed > self._pair['deadline']:
                raise ProbeError('Resource completion exceeded pair deadline')
            if self._last_completed is not None and completed > self._last_completed+MAX_COMPLETED_GAP_S:
                raise ProbeError('Completed resource pair gap exceeded')
            record = {key: self._pair[key] for key in ('sequence', 'start_monotonic',
                'deadline', 'table', 'free', 'cpu_resolution_s')}
            record.update(completed_monotonic=completed,
                probes=[self._process_metadata(item, self._pair['table']) for item in items],
                registered_probe_pids=list(self._pair['pids']),
                registered_probe_pgids=[item['pgid'] for item in items],
                helper_waited_cpu_s=self._helper_waited_cpu_s,
                accounting_observations_complete=self._observations_complete)
            self._last_completed, self._latest, self._pair = completed, record, None
            return dict(record)
        except BaseException as exc:
            self._fail(str(exc), self._observe(), context='probe_sample', cause=exc)

    def validate_fresh(self, now):
        now = self._observe(now)
        if self.primary_failure is not None or self._latest is None or self._closing:
            raise ProbeError('No complete usable resource record')
        if now-self._latest['start_monotonic'] > MAX_START_AGE_S:
            self._fail('Resource age from true earliest START exceeded', now, context='probe_start_age')
        if now-self._last_completed > MAX_COMPLETED_GAP_S:
            self._fail('Completed resource pair gap exceeded', now, context='probe_gap')
        return self.latest

    def _process_metadata(self, item, table=None):
        result = {key: item[key] for key in ('pid', 'pgid', 'command', 'start_monotonic',
            'exit_observed_monotonic', 'returncode', 'reaped', 'waited_cpu_s', 'group_state',
            'stdout_total', 'stderr_total')}
        result['sampled_rss_bytes'] = None if table is None or item['pid'] not in table else table[item['pid']]['rss']
        return result

    def _cleanup_error(self, identity, context, exc):
        key = (identity, context, type(exc).__name__, str(exc))
        if key not in self._cleanup_error_keys:
            self._cleanup_error_keys.add(key)
            self.cleanup_errors.append({'identity': identity, 'context': context,
                'error_type': type(exc).__name__, 'error': str(exc)})

    def _signal(self, item, sig):
        try:
            self.killpg(item['pgid'], sig)
        except ProcessLookupError:
            pass
        except Exception as exc:
            self._cleanup_error(item['pid'], 'probe_signal_'+str(sig), exc)

    def _begin_cleanup(self, now, deadline, *, failed=False):
        if self._closing:
            self._cleanup_deadline = min(self._cleanup_deadline, deadline)
            self._kill_at = min(self._kill_at, self._cleanup_deadline)
            return
        self._closing = True
        self._cleanup_deadline = deadline
        self._kill_at = now if failed else min(now+.1, deadline)
        for fd in tuple(self._streams):
            self._drop_stream(fd)
        for item in self._processes.values():
            # Registration or set_blocking may have failed before a stream was
            # entered in the selector. Close those partial-start pipes too.
            for name in ('stdout', 'stderr'):
                try:
                    stream = getattr(item['proc'], name, None)
                    if stream is not None:
                        stream.close()
                except Exception as exc:
                    self._cleanup_error(item['pid'], 'partial_pipe_close', exc)
            if not item['reaped'] or item['group_state'] != 'absent':
                self._signal(item, signal.SIGTERM)
                item['terminated'] = True

    def _cleanup_tick(self, now):
        for item in self._processes.values():
            if (not item['reaped'] or item['group_state'] != 'absent') and now >= self._kill_at and not item['killed']:
                self._signal(item, signal.SIGKILL)
                item['killed'] = True
        self._reap()
        for item in self._processes.values():
            if item['reaped'] and item['group_state'] == 'absent':
                continue  # An old, confirmed absent PGID must never be reacquired.
            try:
                item['group_state'] = self.group_probe(item['pgid'])
            except Exception as exc:
                item['group_state'] = 'unknown'
                self._cleanup_error(item['pid'], 'probe_group_state', exc)
        complete = not self._unregistered_spawn and all(
            item['reaped'] and item['group_state'] == 'absent' for item in self._processes.values())
        if complete or now >= self._cleanup_deadline:
            self._closed = True
            if not complete:
                self._observations_complete = False
                self._cleanup_error('probe_pair', 'cleanup_deadline', TimeoutError('Probe cleanup incomplete'))
            try:
                self.selector.close()
            except Exception as exc:
                self._cleanup_error('selector', 'selector_close', exc)

    def _fail(self, message, now, *, context='resource_probe', cause=None):
        error = cause if isinstance(cause, ProbeError) else ProbeError(message, context=context,
            cause_error_type=None if cause is None else type(cause).__name__)
        if self.primary_failure is None:
            self.primary_failure = dict(error.diagnostic)
        phase_end = self._pair['phase_deadline'] if self._pair is not None else now
        self._begin_cleanup(now, min(now+1.5, phase_end+1.5), failed=True)
        try:
            self._cleanup_tick(now)
        except BaseException as cleanup_exc:
            self._cleanup_error('probe_pair', 'failure_cleanup', cleanup_exc)
        raise error

    def close(self, deadline):
        now = self._observe()
        if not _finite(deadline):
            raise ValueError('Require an absolute bounded probe cleanup deadline')
        if not self._closed:
            self._begin_cleanup(now, deadline)
            self._cleanup_tick(now)
        return self.cleanup_receipt()

    def cleanup_receipt(self):
        complete = not self._unregistered_spawn and all(
            item['reaped'] and item['group_state'] == 'absent' for item in self._processes.values())
        return {'complete': self._closed and complete and not self.cleanup_errors, 'closed': self._closed,
            'owned_pids': sorted(self.owned_pids), 'owned_pgids': sorted(self.owned_pgids),
            'unreaped_pids': sorted(pid for pid, item in self._processes.items() if not item['reaped']),
            'helper_waited_cpu_s': self._helper_waited_cpu_s,
            'accounting_observations_complete': self._observations_complete,
            'primary_failure': self.primary_failure, 'cleanup_errors': list(self.cleanup_errors),
            'cleanup_deadline': self._cleanup_deadline,
            'unregistered_spawn': self._unregistered_spawn,
            'processes': self._retired+[self._process_metadata(item) for item in self._processes.values()]}
