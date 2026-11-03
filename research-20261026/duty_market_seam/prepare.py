"""One prospective, metered source-pin preparation; no fixtures/imports/native work.

Run only after focused source review. The candidate is not the active LAUNCH;
the parent must reconcile the external meter and explicitly adopt the candidate.
"""
import time
START = time.monotonic()
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RELATIVE = (
    'research-20261026/duty_market_seam/run.py',
    'research-20261026/duty_market_seam/adapter.py',
    'research-20261026/duty_market_seam/worker.py',
    'research-20261026/duty_market_seam/prepare.py',
    'research-20261025/warm_replication/qp_control.py',
    'research-20261026/economic_recourse_pilot/miqp_control.py',
    'src/egglab/__init__.py', 'src/egglab/native_recharge.py',
    'src/egglab/native_hull.py', 'src/egglab/native_pathflow.py',
    'research-20261026/duty_market_seam/PROTOCOL.md',
    'research-20261026/duty_market_seam/OWNER_NOTE.md',
    'research-20261026/duty_market_seam/WORKER_NOTE.md',
    'research-20261026/evspdr_correspondence/STUDY_DECISION.md',
)


def cpu():
    u = resource.getrusage(resource.RUSAGE_SELF)
    return u.ru_utime+u.ru_stime


def stop(signum, frame):
    raise TimeoutError('Source preparation hard resource boundary '+str(signum))


def check():
    if cpu() >= 8 or time.monotonic()-START >= 25:
        raise TimeoutError('Source preparation body8CPU/25wall exhausted; preserve failure')


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    signal.signal(signal.SIGALRM, stop)
    signal.signal(signal.SIGXCPU, stop)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 30-(time.monotonic()-START)))
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    if len(args.source_revision) != 40 or any(c not in '0123456789abcdef' for c in args.source_revision):
        raise ValueError('Full prospective source revision required')
    folder = HERE/'preparation01'
    folder.mkdir(exist_ok=False)
    report = dict(receipt_complete=False, preparation_complete=False, failures=[],
        source_revision=args.source_revision, source_hashes={}, phase_cpu_cap_s=10,
        phase_wall_cap_s=30, fixture_generation=False, project_imports=False,
        native_calls=0, original_data_read=False, external_meter_pending=True)
    passed = False
    try:
        check()
        launch = json.loads((HERE/'LAUNCH.json').read_text())
        if (launch.get('mode') != 'DRAFT' or launch.get('review_disposition') != 'PENDING'
                or launch.get('workdir') != str(ROOT)):
            raise ValueError('Require untouched DRAFT/PENDING launch rooted at repository')
        for relative in RELATIVE:
            check()
            path = ROOT/relative
            if path.is_symlink() or path.resolve() != path or not path.is_file():
                raise ValueError('Source path is not exact regular input '+relative)
            with path.open('rb') as stream:
                data = stream.read(2*1024**2+1)
            if len(data) > 2*1024**2:
                raise ValueError('Source exceeds prospective2MiB bound '+relative)
            report['source_hashes'][str(path)] = hashlib.sha256(data).hexdigest()
            del data
        check()
        candidate = dict(launch)
        candidate.update(mode='FROZEN', review_disposition='PASS',
            source_revision=args.source_revision,
            source_freeze_assumption='parent-approved-frozen-commit',
            source_sha256=report['source_hashes'])
        candidate['preparation_accounting'] = dict(external_accepted=False,
            charged_cpu_s=None, elapsed_s=None,
            purpose='Source binding preparation inside preflight60/total1500; external reconciliation pending')
        save(HERE/'LAUNCH_FROZEN_CANDIDATE.json', candidate)
        report['candidate_path'] = str(HERE/'LAUNCH_FROZEN_CANDIDATE.json')
        report['preparation_complete'] = passed = True
    except BaseException as exc:
        report['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report.update(receipt_complete=True, self_cpu_prepublication_s=cpu(),
            elapsed_prepublication_s=time.monotonic()-START,
            observed_self_peak_rss_bytes=usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024,
            own_children_cpu_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+
                resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,
            not_exact_session_cpu=True)
        save(folder/'receipt.json', report)
        print(json.dumps({k:report[k] for k in ('preparation_complete','failures','self_cpu_prepublication_s','elapsed_prepublication_s')}))
    return 0 if passed else 2


if __name__ == '__main__':
    sys.exit(main())
