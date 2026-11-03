"""Small metered stdlib source-pin/final batch; never opens the FIT input."""
import time
WALL0 = time.monotonic()
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading

ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/economic_recourse_pilot'
VERSION = '21bd18e8fdedfbb4895c8e21008df1fd68ad50ec'
SELECT_COMMAND = '/usr/bin/time -p -o research-20261026/economic_recourse_pilot/selection-time.txt .venv-local/bin/python -I -S -B research-20261026/economic_recourse_pilot/select_cohort.py > research-20261026/economic_recourse_pilot/selection-stdout.txt 2> research-20261026/economic_recourse_pilot/selection-stderr.txt'


def read(path, cap=8*1024**2):
    before = path.stat()
    if before.st_size > cap:
        raise ValueError('Fixed administrative input exceeds byte provision')
    raw = path.read_bytes()
    after = path.stat()
    if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ValueError('Fixed administrative bytes changed during read')
    return raw


def write(path, value, exclusive=False):
    temporary = path if exclusive else path.with_name(path.name+'.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    if not exclusive:
        os.replace(temporary, path)


def meter(path):
    rows = dict(line.split() for line in read(path, 1024).decode().splitlines())
    if set(rows) != {'real', 'user', 'sys'}:
        raise ValueError('Incomplete external meter')
    values = {key: Decimal(value) for key, value in rows.items()}
    if any(not value.is_finite() or value < 0 for value in values.values()):
        raise ValueError('Invalid external meter scalar')
    return dict(real_s=float(values['real']), user_s=float(values['user']), system_s=float(values['sys']),
        displayed_cpu_s=float(values['user']+values['sys']),
        retained_cpu_s=float(values['user']+values['sys']+Decimal('.02')),
        conservative_wall_s=float(values['real']+Decimal('.01')))


def main():
    if (len(sys.argv) != 2 or sys.argv[1] not in ('prepare', 'finalize')
            or Path(__file__).resolve() != HERE/'selection_admin.py'):
        raise SystemExit('Require one fixed prepare/finalize phase')
    phase = sys.argv[1]
    folder = HERE/('selection-preparation01' if phase == 'prepare' else 'selection-finalization01')
    folder.mkdir(exist_ok=False)
    target = folder/'receipt.json'
    write(target, dict(receipt_complete=False, phase=phase, phase_complete=False), exclusive=True)
    out = dict(phase=phase, receipt_complete=False, phase_complete=False, failures=[],
        source_sha256={}, metadata_input_read=False, project_imports=False, native_calls=0,
        budgets=dict(total_cpu_s=5, total_wall_s=15, body_cpu_s=3, body_wall_s=10),
        inside_metadata20_and_pilot_preflight120_total2400=True)
    stopped = None

    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        raise TimeoutError('Administrative batch stop')

    def check():
        use = resource.getrusage(resource.RUSAGE_SELF)
        rss = use.ru_maxrss if sys.platform == 'darwin' else use.ru_maxrss*1024
        if (stopped is not None or use.ru_utime+use.ru_stime >= 3 or time.monotonic()-WALL0 >= 10):
            raise TimeoutError('Administrative body provision exhausted')
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        if threading.active_count() != 1 or child.ru_utime+child.ru_stime or rss > 5*1024**3:
            raise ValueError('Unexpected administrative process/thread/RSS')

    try:
        resource.setrlimit(resource.RLIMIT_CPU, (3, 5))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 10-(time.monotonic()-WALL0)))
        for path in (Path(__file__).resolve(), HERE/'PREPARATION_PROTOCOL.md'):
            check(); raw = read(path)
            out['source_sha256'][str(path)] = hashlib.sha256(raw).hexdigest()
        if phase == 'prepare':
            raw = read(HERE/'SELECTION_LAUNCH.json')
            out['manifest_before_sha256'] = hashlib.sha256(raw).hexdigest()
            launch = json.loads(raw)
            expected_version = dict(repository_root=str(ROOT),
                repository_path='research-20261025/fit_target_support/attempt01/receipt.json',
                git_revision=VERSION, freeze_assumption='tracked-receipt-unchanged-from-named-revision')
            if (launch.get('mode') != 'PREPARATION_FROZEN' or launch.get('review_disposition') != 'PASS'
                    or launch.get('input_version') != expected_version
                    or launch.get('command') != SELECT_COMMAND or launch.get('source_sha256') is not None
                    or launch.get('tracking_prefix', {}).get('base_retained_tracking_cpu_s') != 19811.46):
                raise ValueError('Prospective preparation manifest differs')
            pins = {}
            for path in (HERE/'select_cohort.py', HERE/'SELECTION_PROTOCOL.md'):
                check(); pins[str(path)] = hashlib.sha256(read(path)).hexdigest()
            launch.update(source_sha256=pins, mode='SOURCE_PINNED', no_execution_authority=True)
            check(); write(HERE/'SELECTION_LAUNCH.json', launch)
            out.update(preparation_complete=True, selection_source_sha256=pins,
                input_version=expected_version, selector_still_denied_until_parent_external_acceptance=True)
        else:
            prepared = json.loads(read(HERE/'selection-preparation01/receipt.json'))
            selected = json.loads(read(HERE/'selection01/receipt.json'))
            prep_meter = meter(HERE/'selection-prepare-time.txt')
            selection_meter = meter(HERE/'selection-time.txt')
            if (prepared.get('receipt_complete') is not True or selected.get('receipt_complete') is not True
                    or prepared.get('preparation_complete') is not True):
                raise ValueError('An administrative input is incomplete')
            within = (prep_meter['retained_cpu_s'] <= 5 and prep_meter['conservative_wall_s'] <= 15
                and selection_meter['retained_cpu_s'] <= 10 and selection_meter['conservative_wall_s'] <= 30)
            out.update(prior_components=dict(source_preparation=prep_meter, selector=selection_meter),
                prior_displayed_cpu_s=float(Decimal(str(prep_meter['displayed_cpu_s']))+Decimal(str(selection_meter['displayed_cpu_s']))),
                prior_retained_cpu_s=float(Decimal(str(prep_meter['retained_cpu_s']))+Decimal(str(selection_meter['retained_cpu_s']))),
                prior_elapsed_sum_s=float(Decimal(str(prep_meter['real_s']))+Decimal(str(selection_meter['real_s']))),
                earlier_components_within_selected_envelopes=within,
                selection_passed=selected.get('selection_passed') is True,
                finalized_prior_component_accounting=True,
                finalizer_external_meter_still_pending=True,
                global_prefix_before_metadata_retained_cpu_s=19811.46,
                global_rule='Add preparation, selector and finalizer retained charges once; no child overlap or native work')
            if not within:
                raise ValueError('Earlier metadata component exceeds selected envelope')
        check(); out['phase_complete'] = True
    except BaseException as exc:
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        remaining = min(5., 15.-(time.monotonic()-WALL0))
        if remaining <= 0:
            raise TimeoutError('No administrative publication reserve remains')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        use = resource.getrusage(resource.RUSAGE_SELF)
        out.update(receipt_complete=True, stopped_signal=stopped,
            resources_prepublication=dict(user_s=use.ru_utime, system_s=use.ru_stime,
                elapsed_s=time.monotonic()-WALL0, python_threads=threading.active_count(),
                observed_peak_rss_bytes=use.ru_maxrss if sys.platform == 'darwin' else use.ru_maxrss*1024),
            external_total_acceptance_pending=True)
        write(target, out)
        print(json.dumps(dict(phase=phase, phase_complete=out['phase_complete'], failures=out['failures'])))
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['phase_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
