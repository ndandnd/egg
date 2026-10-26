"""DRAFT metadata-only cohort selection; no project imports or row admission."""
import time
WALL0 = time.monotonic()
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import threading

sys.dont_write_bytecode = True
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/economic_recourse_pilot'
INPUT = ROOT/'research-20261025/fit_target_support/attempt01/receipt.json'
POLICY = 'first-two-per-declared-profile-exposed-FIT-cohort-v1'
EXCLUDED = (10001, 10002, 10018, 10006, 10009, 10010, 10015, 10005)
BUDGETS = dict(total_cpu_s=10, total_wall_s=30, body_cpu_s=5, body_wall_s=20,
               publication_cpu_s=5, publication_wall_s=10)


def read_once(path, cap):
    before = path.stat()
    if before.st_size > cap:
        raise ValueError('Frozen metadata/source byte cap exceeded')
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ValueError('Frozen bytes changed during one bounded read')
    return raw


def save_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def cpu():
    use = resource.getrusage(resource.RUSAGE_SELF)
    return use.ru_utime+use.ru_stime


def main():
    launch_raw = read_once(HERE/'SELECTION_LAUNCH.json', 1024**2)
    launch = json.loads(launch_raw)
    version = launch.get('input_version')
    revision = version.get('git_revision') if isinstance(version, dict) else None
    version_valid = bool(isinstance(version, dict) and set(version) == {
        'repository_root', 'repository_path', 'git_revision', 'freeze_assumption'}
        and version['repository_root'] == str(ROOT)
        and version['repository_path'] == 'research-20261025/fit_target_support/attempt01/receipt.json'
        and version['freeze_assumption'] == 'tracked-receipt-unchanged-from-named-revision'
        and isinstance(revision, str) and len(revision) == 40
        and all(c in '0123456789abcdefABCDEF' for c in revision))
    if (Path(__file__).resolve() != HERE/'select_cohort.py' or launch.get('mode') != 'FROZEN'
            or launch.get('review_disposition') != 'PASS' or launch.get('policy') != POLICY
            or launch.get('workdir') != str(ROOT) or launch.get('input') != str(INPUT)
            or launch.get('budgets') != BUDGETS or launch.get('command') is None
            or launch.get('tracking_prefix') is None or not isinstance(launch.get('source_sha256'), dict)
            or not version_valid):
        raise SystemExit('DRAFT/PENDING: cohort metadata input is not admitted')
    attempt = HERE/'selection01'; attempt.mkdir(exist_ok=False)
    target = attempt/'receipt.json'; save_new(target, dict(receipt_complete=False, selection_passed=False))
    out = dict(policy=POLICY, receipt_complete=False, selection_passed=False, failures=[], groups=[],
        input_sha256={str(HERE/'SELECTION_LAUNCH.json'): hashlib.sha256(launch_raw).hexdigest()},
        budgets=BUDGETS, tracking_prefix=launch['tracking_prefix'], input_version=version,
        inside_campaign_preflight_120_and_total_2400=True, no_original_row_or_plan_access=True,
        statistical_scope='Four exposed FIT development groups, not unseen confirmation',
        no_group_replacement=True, no_native_or_child_process=True)
    stopped = None; body = True

    def stop(signum, frame):
        nonlocal stopped
        stopped = stopped or signum
        raise TimeoutError('Latched metadata selection stop '+str(signum))

    def check():
        own = resource.getrusage(resource.RUSAGE_SELF)
        rss = own.ru_maxrss if sys.platform == 'darwin' else own.ru_maxrss*1024
        if stopped is not None or cpu() > (5 if body else 10) or time.monotonic()-WALL0 > (20 if body else 30):
            raise TimeoutError('Selection body/total provision exhausted')
        if threading.active_count() != 1 or rss > 5*1024**3:
            raise ValueError('Selection thread/observed RSS bound exceeded')
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        if children.ru_utime+children.ru_stime != 0:
            raise ValueError('Unexpected selection child CPU')

    try:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 10))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 20-(time.monotonic()-WALL0)))
        required = {str(HERE/'select_cohort.py'), str(HERE/'SELECTION_PROTOCOL.md')}
        if set(launch['source_sha256']) != required:
            raise ValueError('Selection literal source/protocol set differs')
        for path, pin in launch['source_sha256'].items():
            check(); raw = read_once(Path(path), 1024**2); digest = hashlib.sha256(raw).hexdigest()
            out['input_sha256'][path] = digest
            if digest != pin:
                raise ValueError('Selection source/protocol pin differs')
        check(); raw = read_once(INPUT, 32*1024**2)
        digest = hashlib.sha256(raw).hexdigest(); out['input_sha256'][str(INPUT)] = digest
        if launch.get('input_sha256') is not None and digest != launch['input_sha256']:
            raise ValueError('Selected metadata input pin differs')
        # Full JSON decode is transient; no other values are semantically read.
        parsed = json.loads(raw); raw = None
        projection = {k: parsed.get(k) for k in ('receipt_complete', 'checks_passed', 'support_report_complete')}
        records = parsed.get('groups')
        if not isinstance(records, list):
            raise ValueError('FIT identity list missing')
        identities = [dict(group=r.get('group'), base_id=r.get('base_id')) for r in records]
        parsed = records = None
        if any(v is not True for v in projection.values()) or len(identities) != 80:
            raise ValueError('Closed FIT metadata flags/count differ')
        seen = set()
        for item in identities:
            check(); base = item['base_id']
            if (type(base) is not int or not 10000 <= base < 10128
                    or item['group'] != f'physical_v2_s{base}' or base in seen):
                raise ValueError('FIT identities are not80 unique canonical declared TRAIN IDs')
            seen.add(base)
        ranked = {20: [], 28: []}
        for base in sorted(seen):
            if base in EXCLUDED:
                continue
            j = (7*(base-10000)) % 54
            services = 20 if (j//3) % 2 == 0 else 28
            ranked[services].append(base)
        if any(len(ranked[n]) < 2 for n in (20, 28)):
            raise ValueError('Insufficient metadata cohort; no replacement rule change')
        selected = [dict(group=f'physical_v2_s{base}', base_id=base, services=n,
            profile_source='source-derived declared assignment service projection; stored case must later match')
            for n in (20, 28) for base in ranked[n][:2]]
        out.update(groups=selected, admitted_FIT_identity_count=80, metadata_flags=projection,
            excluded_prior_pilot_union=list(EXCLUDED), eligible_counts={str(n): len(ranked[n]) for n in (20, 28)},
            selection_rule='First2 ascending numeric canonical FIT base IDs per declared20/28 profile after uniform full8pilot exclusion',
            profile_formula='j=(7*(base_id-10000))%54;20 if(j//3)%2==0 else28',
            selection_passed=True)
        check()
    except BaseException as exc:
        out['selection_passed'] = False
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        body = False; resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        out.update(receipt_complete=True, stopped_signal=stopped,
            resources_prepublication=dict(cpu_s=cpu(), elapsed_s=time.monotonic()-WALL0,
                observed_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    if sys.platform == 'darwin' else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),
            external_total_acceptance_pending=True)
        try:
            check()
        except BaseException as exc:
            out['selection_passed'] = False
            out['failures'].append(dict(stage='final_resource_observation', type=type(exc).__name__, message=str(exc)))
        remaining = min(10., 30-(time.monotonic()-WALL0))
        if remaining <= 0:
            raise TimeoutError('No metadata publication reserve remains')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        temporary = target.with_name('receipt.final.tmp'); save_new(temporary, out); temporary.replace(target)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['selection_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
