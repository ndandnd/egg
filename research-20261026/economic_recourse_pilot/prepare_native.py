"""One metered source/cohort-pin batch; no original data or project imports."""
import time
START = time.monotonic()
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
COMMAND = '/usr/bin/time -p -o research-20261026/economic_recourse_pilot/process-time.txt .venv-local/bin/python -B research-20261026/economic_recourse_pilot/run.py > research-20261026/economic_recourse_pilot/stdout.txt 2> research-20261026/economic_recourse_pilot/stderr.txt'
SOURCES = ('research-20261026/economic_recourse_pilot/run.py',
    'research-20261026/economic_recourse_pilot/worker.py',
    'research-20261026/economic_recourse_pilot/miqp_control.py',
    'research-20261025/warm_replication/qp_control.py',
    'research-20261025/topology_charging/worker.py', 'src/egglab/__init__.py',
    'src/egglab/native_recharge.py', 'src/egglab/native_hull.py',
    'src/egglab/native_pathflow.py', 'src/egglab/physical_learning_cases.py',
    'research-20261026/economic_recourse_pilot/PROTOCOL.md',
    'research-20261026/economic_recourse_pilot/OWNER_NOTE.md',
    'research-20261026/economic_recourse_design/STUDY_DESIGN.md')


def read(path):
    before = path.stat()
    if before.st_size > 8*1024**2:
        raise ValueError('Fixed preparation input exceeds provision')
    raw = path.read_bytes(); after = path.stat()
    if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ValueError('Preparation bytes changed during read')
    return raw


def save(path, value, exclusive=False):
    temp = path if exclusive else path.with_name(path.name+'.tmp')
    with temp.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    if not exclusive:
        os.replace(temp, path)


def main():
    if Path(__file__).resolve() != HERE/'prepare_native.py':
        raise SystemExit('Wrong native preparation namespace')
    folder = HERE/'native-preparation01'; folder.mkdir(exist_ok=False)
    target = folder/'receipt.json'
    save(target, dict(receipt_complete=False, preparation_complete=False), exclusive=True)
    out = dict(receipt_complete=False, preparation_complete=False, failures=[], input_sha256={},
        original_input_read=False, project_imports=False, native_calls=0,
        budgets=dict(total_cpu_s=5, total_wall_s=15, body_cpu_s=3, body_wall_s=10))
    stopped = None
    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        raise TimeoutError('Native preparation stop')
    def check():
        use = resource.getrusage(resource.RUSAGE_SELF)
        rss = use.ru_maxrss if sys.platform == 'darwin' else use.ru_maxrss*1024
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        if stopped or time.monotonic()-START >= 10 or use.ru_utime+use.ru_stime >= 3:
            raise TimeoutError('Native preparation body provision')
        if threading.active_count() != 1 or child.ru_utime+child.ru_stime or rss > 5*1024**3:
            raise ValueError('Unexpected native preparation resources')
    def consume(path):
        check(); raw = read(path)
        out['input_sha256'][str(path)] = hashlib.sha256(raw).hexdigest()
        return raw
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (3, 5))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 10-(time.monotonic()-START)))
        for path in (Path(__file__).resolve(), HERE/'NATIVE_PREPARATION_PROTOCOL.md',
                     HERE/'NATIVE_ADOPTION_DECISION.md', HERE/'NATIVE_INPUT_AUTHORITY.md'):
            consume(path)
        launch = json.loads(consume(HERE/'LAUNCH.json'))
        if (launch.get('mode') != 'NATIVE_PREPARATION_FROZEN' or launch.get('review_disposition') != 'PASS'
                or launch.get('command') != COMMAND or launch.get('source_sha256') is not None
                or launch.get('workdir') != str(ROOT)):
            raise ValueError('Native preparation control not admitted; no derived metadata read')
        selected = json.loads(consume(HERE/'selection01/receipt.json'))
        prior = json.loads(consume(HERE/'FINAL_SELECTION_RESOURCE_RECEIPT.json'))
        if (launch.get('cohort_admission', {}).get('expected_groups') != selected.get('groups')
                or selected.get('receipt_complete') is not True or selected.get('selection_passed') is not True
                or [(g['base_id'], g['services']) for g in selected['groups']]
                    != [(10007,20),(10013,20),(10017,28),(10021,28)]
                or prior.get('state') != 'CLOSED' or prior.get('package_retained_cpu_s') != .12
                or prior.get('package_elapsed_sum_s') != .13
                or launch.get('tracking_prefix', {}).get('current_retained_tracking_cpu_s') != 19811.58):
            raise ValueError('Prospective native authority/cohort/carry differs')
        pins = {}
        for name in SOURCES:
            path = ROOT/name; consume(path); pins[str(path)] = out['input_sha256'][str(path)]
        launch['source_sha256'] = pins
        launch['cohort_admission']['receipt_sha256'] = out['input_sha256'][str(HERE/'selection01/receipt.json')]
        launch['authority_document_sha256'] = out['input_sha256'][str(HERE/'NATIVE_INPUT_AUTHORITY.md')]
        launch.update(mode='SOURCE_PINNED', no_execution_authority=True)
        check(); save(HERE/'LAUNCH.json', launch)
        out.update(preparation_complete=True, source_sha256=pins,
            cohort_receipt_sha256=launch['cohort_admission']['receipt_sha256'],
            prior_metadata_charge_s=.12, prior_metadata_elapsed_s=.13,
            main_still_denied_until_external_acceptance=True)
    except BaseException as exc:
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        remaining = min(5., 15-(time.monotonic()-START))
        if remaining <= 0:
            raise TimeoutError('No native-preparation publication reserve')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        use = resource.getrusage(resource.RUSAGE_SELF)
        out.update(receipt_complete=True, stopped_signal=stopped,
            resources_prepublication=dict(user_s=use.ru_utime, system_s=use.ru_stime,
                elapsed_s=time.monotonic()-START, python_threads=threading.active_count(),
                observed_peak_rss_bytes=use.ru_maxrss if sys.platform == 'darwin' else use.ru_maxrss*1024),
            external_total_acceptance_pending=True)
        save(target, out)
        print(json.dumps(dict(preparation_complete=out['preparation_complete'], failures=out['failures'])))
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['preparation_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
