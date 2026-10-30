"""Serial, gated owner for one literal six-trip adjacent-oracle comparison."""
import time
WALL0 = time.monotonic()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/adjacent_bridge_qualification'
SIBLING = Path('/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001')
SIBLING_REVISION = '3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c'
POLICY = 'adjacent-synthetic-capacity-bridge-v1'
ARMS = ('fixed_duty', 'full')
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS', 'SLURM_CPUS_PER_TASK')
BUDGETS = dict(total_cpu_s=900, total_wall_s=1800, dispatch_cpu_s=690, closure_cpu_s=210,
    preflight_cpu_s=60, preparation_cpu_s=30, preparation_wall_s=60,
    finalization_cpu_s=60, finalization_wall_s=90, worker_hard_cpu_s=240,
    worker_endpoint_s=240, cleanup_s=3, cg_seconds=60, mip_seconds=90)
LOCAL_SOURCES = (
    'research-20261026/adjacent_bridge_qualification/run.py',
    'research-20261026/adjacent_bridge_qualification/prepare.py',
    'research-20261026/adjacent_bridge_qualification/fixture.py',
    'research-20261026/adjacent_bridge_qualification/worker.py',
    'research-20261026/adjacent_bridge_qualification/PROTOCOL.md',
    'research-20261026/adjacent_bridge_qualification/OWNER_NOTE.md',
    'research-20261026/adjacent_bridge_qualification/WORKER_NOTE.md',
    'research-20261026/adjacent_oracle_boundary/boundary.py',
)
CHILD_PUBLICATION = False
PUBLICATION_STOP = None


class ContractError(ValueError):
    pass


def cpu(who=resource.RUSAGE_SELF):
    u = resource.getrusage(who)
    return u.ru_utime+u.ru_stime


def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(r if sys.platform == 'darwin' else r*1024)


def full_revision(value):
    return isinstance(value, str) and len(value) == 40 and all(c in '0123456789abcdef' for c in value)


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def read_once(path, cap=8*1024**2):
    path = Path(path)
    before = path.stat()
    if path.is_symlink() or path.resolve() != path or not path.is_file() or before.st_size > cap:
        raise ContractError('Exact regular bounded path required: '+str(path))
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    if len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino, after.st_size, after.st_mtime_ns):
        raise ContractError('Consumed bytes changed during read: '+str(path))
    return raw


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value)
    os.replace(temporary, path)


def gate():
    raw = read_once(HERE/'LAUNCH.json')
    launch = json.loads(raw)
    p = launch.get('preparation_accounting') or {}
    if (Path(__file__).resolve() != HERE/'run.py' or Path.cwd().resolve() != ROOT
            or launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS'
            or launch.get('policy') != POLICY or launch.get('workdir') != str(ROOT)
            or not full_revision(launch.get('source_revision'))
            or launch.get('source_freeze_assumption') != 'parent-approved-frozen-commit'
            or launch.get('sibling_source_revision') != SIBLING_REVISION
            or launch.get('sibling_source_root') != str(SIBLING)
            or launch.get('sibling_freeze_assumption') != 'registered-worktree-unchanged-from-named-revision'
            or launch.get('budgets') != BUDGETS or launch.get('arms') != list(ARMS)
            or launch.get('fixture') != 'adjacent-six-trip-v1'
            or launch.get('environment') != {k: '1' for k in THREAD_ENV}
            or launch.get('start_fee') != 0 or launch.get('clean_argv') != ['--start-fee', '0']
            or not isinstance(launch.get('command'), str) or not launch['command']
            or not isinstance(launch.get('source_sha256'), dict)
            or not isinstance(launch.get('tracking_prefix'), dict)
            or not isinstance(launch.get('numerical_resource_prefix'), dict)
            or p.get('external_accepted') is not True
            or not finite_nonnegative(p.get('charged_cpu_s')) or p['charged_cpu_s'] > 30
            or not finite_nonnegative(p.get('elapsed_s')) or p['elapsed_s'] > 60):
        raise SystemExit('DRAFT/PENDING: sibling imports, literal fixture and dispatch denied')
    return launch, raw


def preflight(launch, report, check):
    closure = launch.get('source_closure') or {}
    paths = closure.get('sibling_python_paths')
    if (closure.get('roots') != ['run_capacity_terminal_cg'] or not isinstance(paths, list)
            or not paths or len(paths) != len(set(paths)) or len(paths) > 192):
        raise ContractError('Frozen finite sibling AST source closure required')
    for value in paths:
        path = Path(value)
        if not path.is_relative_to(SIBLING/'src') or path.suffix != '.py':
            raise ContractError('Closure escapes registered sibling source')
    required = {str(ROOT/p) for p in LOCAL_SOURCES} | set(paths)
    if set(launch['source_sha256']) != required:
        raise ContractError('Frozen source inventory differs from declared local + sibling closure')
    for name in sorted(required):
        check(); raw = read_once(name, 2*1024**2)
        digest = hashlib.sha256(raw).hexdigest()
        report['source_sha256'][name] = digest
        if digest != launch['source_sha256'][name]:
            raise ContractError('Frozen execution source bytes differ: '+name)
    report['source_closure'] = closure
    report['preflight_admitted'] = True
    check()


def launch_worker(task):
    global CHILD_PUBLICATION
    folder = HERE/'attempt01'/f"{task['ordinal']:03d}-{task['arm']}"
    folder.mkdir(exist_ok=False)
    raw = (json.dumps(dict(task_id=task['task_id'], arm=task['arm']), indent=2)+'\n').encode()
    with (folder/'spec.json').open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    digest = hashlib.sha256(raw).hexdigest()
    save_new(folder/'receipt.json', dict(receipt_complete=False, method_endpoint_accepted=False))
    row = task
    row.update(attempted=False, reaped=False, parent_endpoint_accepted=False,
        administrative_packet_accepted=False, physical_endpoint_accepted=False,
        failures=[], folder=str(folder), spec_sha256=digest, config_failure=False)
    child = None; packet = {}; cleanup_end = None
    prior_child, prior_self = cpu(resource.RUSAGE_CHILDREN), cpu()
    anchor = time.monotonic(); row['parent_anchor'] = anchor
    with (folder/'stdout.txt').open('x') as out, (folder/'stderr.txt').open('x') as err:
        try:
            if threading.active_count() != 1:
                raise ContractError('Owner has multiple Python threads')
            CHILD_PUBLICATION = True
            try:
                child = subprocess.Popen([str(ROOT/'.venv-local/bin/python'), '-B', str(HERE/'worker.py'),
                    '--worker', str(folder), '--parent-anchor', repr(anchor), '--spec-sha256', digest],
                    cwd=ROOT, env=dict(os.environ), stdout=out, stderr=err, start_new_session=True,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (240, 240)))
                row.update(attempted=True, pid=child.pid)
            finally:
                CHILD_PUBLICATION = False
            if PUBLICATION_STOP is not None:
                raise TimeoutError('Stop deferred through direct owned PID registration')
            try:
                child.wait(timeout=max(.001, anchor+240-time.monotonic()))
            except subprocess.TimeoutExpired:
                row['timed_out'] = True; cleanup_end = time.monotonic()+3
                child.terminate()
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            row.update(reaped=True, returncode=child.returncode)
        except BaseException as exc:
            row['failures'].append(dict(stage='process', type=type(exc).__name__, message=str(exc)))
            if child is None:
                row['config_failure'] = True
            elif child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    row.update(reaped=True, returncode=child.returncode)
                except BaseException as secondary:
                    row['failures'].append(dict(stage='cleanup', type=type(secondary).__name__, message=str(secondary)))
    row['process_return_elapsed_s'] = time.monotonic()-anchor
    try:
        packet = json.loads(read_once(folder/'receipt.json'))
        if packet.get('receipt_complete') is True and (packet.get('task_id') != task['task_id']
                or packet.get('arm') != task['arm']):
            raise ContractError('Worker task/arm identity mismatch')
        if packet.get('receipt_complete') is True and packet.get('source_revision') != row['source_revision']:
            raise ContractError('Worker source revision differs')
        if packet.get('receipt_complete') is True and packet.get('fixture_id') != 'adjacent-six-trip-v1':
            raise ContractError('Worker literal fixture identity differs')
    except BaseException as exc:
        row['config_failure'] = True
        row['failures'].append(dict(stage='complete_packet_read', type=type(exc).__name__, message=str(exc)))
    endpoint = time.monotonic()
    row.update(worker=packet, complete_packet_read_monotonic=endpoint, parent_elapsed_s=endpoint-anchor,
        method_late=endpoint > anchor+240, waited_child_cpu_s=cpu(resource.RUSAGE_CHILDREN)-prior_child,
        parent_cpu_s=cpu()-prior_self, cpu_observation_complete=child is None or row['reaped'],
        unresolved_cpu_reserve_s=240. if child is not None and not row['reaped'] else 0.)
    fatal = ('config_failure', 'fatal_contract', 'resource_violation', 'identity_failure')
    for flag in fatal:
        row[flag] = bool(row.get(flag) or packet.get(flag))
    usage = packet.get('resources') or {}
    peak = usage.get('peak_rss_bytes')
    if packet.get('receipt_complete') is True and (not finite_nonnegative(peak)
            or peak > 5*1024**3 or usage.get('python_threads') != 1):
        row['resource_violation'] = row['config_failure'] = True
    if packet.get('receipt_complete') is True and packet.get('oracle_run_calls') not in (0, 1):
        row['config_failure'] = True
    admin = bool(row['reaped'] and row.get('returncode') == 0 and not row.get('timed_out')
        and not row['method_late'] and not row['failures'] and packet.get('receipt_complete') is True
        and not any(row.get(k) for k in fatal))
    physical = bool(admin and packet.get('method_endpoint_accepted') is True
        and packet.get('physical_valid') is True)
    row.update(administrative_packet_accepted=admin, parent_endpoint_accepted=physical,
        physical_endpoint_accepted=physical)
    save_new(folder/'external-receipt.json', row)
    return row


def compact(report):
    rows = []
    for row in report['ledger']:
        packet = row.get('worker') or {}
        rows.append(dict(task_id=row['task_id'], arm=row['arm'], attempted=row.get('attempted', False),
            administrative_packet_accepted=row.get('administrative_packet_accepted', False),
            physical_endpoint_accepted=row.get('physical_endpoint_accepted', False),
            method_late=row.get('method_late'), returncode=row.get('returncode'),
            parent_elapsed_s=row.get('parent_elapsed_s'), unattempted_reason=row.get('unattempted_reason'),
            oracle_run_calls=packet.get('oracle_run_calls'), native_optimize_calls=packet.get('native_optimize_calls'),
            oracle_summary=packet.get('oracle_summary'), selected_summary=packet.get('selected_summary'),
            worker_resources=packet.get('resources'), failures=row.get('failures', []),
            worker_failures=packet.get('failures', []), config_failure=row.get('config_failure', False)))
    return dict(policy=POLICY, passed=report['passed'], scope=report['passed_scope'],
        planned_bases=1, planned_quotes=1, planned_arms=2, rows=rows, resources=report['resources'],
        both_physical_endpoints=sum(r['physical_endpoint_accepted'] for r in rows) == 2,
        certificate_status='See each oracle_summary: grid LP/finite-pool native/continuous physical scopes remain distinct',
        independent_case_count=1, ML_claim=False, automatic_retry=False, failures=report['failures'])


def markdown(path, readout):
    lines = ['# Adjacent capacity-oracle synthetic qualification', '',
        'One literal six-trip base, one posted quote, two sequential arms. Administrative closure, '
        'selected physical witnesses and numerical/grid certificates have separate flags.', '',
        '| Arm | Attempted | Compact packet timely | Physical endpoint | Parent seconds |',
        '|---|---:|---:|---:|---:|']
    for row in readout['rows']:
        lines.append('| '+ ' | '.join(str(row[k]) for k in ('arm', 'attempted',
            'administrative_packet_accepted', 'physical_endpoint_accepted', 'parent_elapsed_s'))+' |')
    lines.extend(['', 'Full compact source-returned grid/continuous costs, energy, occupancy, '
        'fleet, LP/pricing status, finite-pool integer status and failure details:', '', '```json',
        json.dumps(readout, indent=2, allow_nan=False), '```', '',
        'Resources are prepublication observations. The external process meter includes publication/exit tails. '
        'This synthetic qualification establishes no private-data equivalence, nonlinear optimum or ML value.', ''])
    with Path(path).open('x') as stream:
        stream.write('\n'.join(lines)); stream.flush(); os.fsync(stream.fileno())


def main():
    launch, raw_launch = gate()
    output = HERE/'attempt01'; output.mkdir(exist_ok=False)
    target = output/'receipt.json'; save_new(target, dict(receipt_complete=False, passed=False))
    report = dict(policy=POLICY, passed=False, receipt_complete=False, failures=[], config_failure=False,
        source_revision=launch['source_revision'], sibling_source_revision=SIBLING_REVISION,
        launch_sha256=hashlib.sha256(raw_launch).hexdigest(), source_sha256={},
        budgets=BUDGETS, preparation_accounting=launch['preparation_accounting'],
        tracking_prefix=launch['tracking_prefix'], numerical_resource_prefix=launch['numerical_resource_prefix'],
        legacy_review_guard_s=2546.091499549272, legacy_actual_cpu_s=None,
        ledger=[dict(task_id=f'T{i+1:02d}-{arm}', ordinal=i+1, arm=arm,
            source_revision=launch['source_revision'], attempted=False) for i, arm in enumerate(ARMS)])
    p = launch['preparation_accounting']; stopped = None; unresolved = 0.
    phase = 'preflight'; final_cpu = final_wall = None

    def stop(signum, frame):
        global PUBLICATION_STOP
        nonlocal stopped
        stopped = stopped or signum
        if CHILD_PUBLICATION:
            PUBLICATION_STOP = PUBLICATION_STOP or signum
            return
        raise TimeoutError('Latched owner stop '+str(signum))

    def check():
        if stopped is not None:
            raise TimeoutError('Owner stop remains latched')
        if (threading.active_count() != 1 or rss() > 5*1024**3
                or cpu()+cpu(resource.RUSAGE_CHILDREN)+unresolved+p['charged_cpu_s'] > 900
                or time.monotonic()-WALL0+p['elapsed_s'] > 1800):
            report['config_failure'] = True
            raise ContractError('Owner thread/RSS/total CPU/wall provision exceeded')
        if (phase == 'preflight' and cpu()+p['charged_cpu_s'] > 60 or phase == 'finalization'
                and (cpu()-final_cpu > 60 or time.monotonic()-final_wall > 90)):
            report['config_failure'] = True
            raise ContractError('Preflight/finalization provision exceeded')

    try:
        for name in THREAD_ENV:
            os.environ[name] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (60, 900))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 1800-p['elapsed_s']-(time.monotonic()-WALL0)))
        preflight(launch, report, check)
        save_new(output/'preflight.json', dict(source_sha256=report['source_sha256'],
            source_closure=report['source_closure'], preflight_admitted=True))
        phase = 'dispatch'; resource.setrlimit(resource.RLIMIT_CPU, (900, 900))
        for index, task in enumerate(report['ledger']):
            check()
            remaining = 2-index
            if (cpu()+cpu(resource.RUSAGE_CHILDREN)+unresolved+p['charged_cpu_s']+240*remaining > 690
                    or time.monotonic()-WALL0+p['elapsed_s']+243*remaining+90 > 1800):
                report['dispatch_stopped_reason'] = 'Remaining planned workers not fully funded within dispatch/closure'
                break
            row = launch_worker(task); report['ledger'][index] = row
            unresolved += row['unresolved_cpu_reserve_s']
            if unresolved or any(row.get(k) for k in ('config_failure', 'fatal_contract', 'resource_violation', 'identity_failure')):
                report['config_failure'] = True
                report['dispatch_stopped_reason'] = 'Fatal interface/resource/identity failure or unresolved owned child'
                break
            check()
    except BaseException as exc:
        report['config_failure'] = True
        report['failures'].append(dict(stage=phase, type=type(exc).__name__, message=str(exc)))
    finally:
        phase = 'finalization'; final_cpu = cpu(); final_wall = time.monotonic()
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(90., 1800-p['elapsed_s']-(final_wall-WALL0))))
        for row in report['ledger']:
            if not row.get('attempted'):
                row.setdefault('unattempted_reason', report.get('dispatch_stopped_reason', 'Preflight/owner failure'))
        report.update(receipt_complete=True, ledger_complete=len(report['ledger']) == 2,
            accounting_complete=unresolved == 0, unresolved_cpu_reserve_s=unresolved, stop_signal=stopped,
            resources=dict(self_cpu_s=cpu(), waited_children_cpu_s=cpu(resource.RUSAGE_CHILDREN),
                combined_cpu_s=cpu()+cpu(resource.RUSAGE_CHILDREN), preparation_charge_s=p['charged_cpu_s'],
                package_cpu_prepublication_s=cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s'],
                package_elapsed_sum_prepublication_s=time.monotonic()-WALL0+p['elapsed_s'],
                observed_self_peak_rss_bytes=rss(), python_threads=threading.active_count(),
                external_total_acceptance_pending=True, task_deltas_not_added_again=True),
            passed_scope='Administrative complete two-arm ledger/accounting; not all physical results or global optimality')
        try:
            check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='final_resource_observation', type=type(exc).__name__, message=str(exc)))
        report['passed'] = bool(not report['config_failure'] and not report['failures']
            and report['ledger_complete'] and report['accounting_complete'] and stopped is None)
        readout = compact(report)
        remaining = min(90-(time.monotonic()-final_wall), 1800-p['elapsed_s']-(time.monotonic()-WALL0))
        if remaining <= 0:
            raise TimeoutError('No final publication provision; master remains incomplete')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        publish(output/'READOUT.json', readout); markdown(output/'READOUT.md', readout)
        check(); publish(target, report)
        print(json.dumps(dict(passed=report['passed'], attempted=sum(r.get('attempted', False) for r in report['ledger']),
            physical_endpoints=sum(r.get('physical_endpoint_accepted', False) for r in report['ledger']),
            readout=str(output/'READOUT.md'), resources=report['resources']), allow_nan=False), flush=True)
        check(); signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
