"""Prospective v2 correction; fresh attempt02, inherited frozen input bindings."""
import time

WALL0 = time.monotonic()

import argparse
from fractions import Fraction
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
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[name] = '1'

POLICY = 'original-warm-eight-priors-direct-fixed-route-qp-v2'
CASES = tuple(f'scale:{base}:{size}' for base in range(50600, 50604) for size in (40, 80))
TOTAL_CPU, TOTAL_WALL, DISPATCH_CPU = 1800., 2700., 1620.
PRIOR_CPU, PRIOR_WALL = .72, .92  # Nonrefundable closed attempt01 external charge.
FLAGS = ('config_failure', 'resource_violation', 'identity_failure')
PREDECESSOR = 'research-20261025/fixed_route_qp/attempt01/preflight.json'
FRESH_INPUTS = (
    'research-20261025/fixed_route_qp/run_v2.py',
    'research-20261025/fixed_route_qp/qp_control_v2.py',
    'research-20261025/fixed_route_qp/PROTOCOL_V2.md',
    'research-20261025/fixed_route_qp/RESOURCE_DECISION_V2.md',
    'research-20261025/fixed_route_qp/LAUNCH_V2.json',
)


class ConfigurationFailure(ValueError):
    pass


class ResourceViolation(RuntimeError):
    pass


# Minimal publication/resource helpers copied from warm_replanning/run.py.
# They operate on explicit paths; no imported __file__ rebinding or old launcher.
def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
                  default=lambda x: str(x) if isinstance(x, Fraction) else x)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value)
    os.replace(temporary, path)  # Replace only this attempt's exclusive placeholder.


def load(path):
    with Path(path).open() as stream:
        return json.load(stream)


def self_cpu():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime+usage.ru_stime


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime+usage.ru_stime


def rss_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == 'darwin' else raw*1024)


def resources():
    return dict(self_cpu_s=self_cpu(), waited_children_cpu_s=children_cpu(),
        combined_cpu_s=self_cpu()+children_cpu(), observed_peak_rss_bytes=rss_bytes(),
        scope='through receipt preparation; external meter includes publication/exit')


def preflight(root, output):
    """Bind predecessor once and only fresh v2 bytes; do not rehash old inputs."""
    digests, predecessor = {}, None
    for name in (PREDECESSOR,)+FRESH_INPUTS:
        raw = (root/name).read_bytes()
        digests[name] = hashlib.sha256(raw).hexdigest()
        if name == PREDECESSOR:
            predecessor = json.loads(raw)
    if (predecessor.get('policy') != 'original-warm-eight-priors-direct-fixed-route-qp-v1'
            or set(predecessor.get('priors', {})) != set(CASES)):
        raise ConfigurationFailure('Predecessor binding is not the exact original eight-prior cohort')
    inherited = predecessor['input_sha256']
    priors = predecessor['priors']
    original = root/'research-20261025/warm_replanning/attempt01'
    for index, case in enumerate(CASES, 1):
        expected = original/('%03d-acquisition-%s-CoverCA1' % (index, case.replace(':', '-')))
        expected_paths = {key: str((expected/file).relative_to(root)) for key, file in
            (('plan', 'best-plan.json'), ('replay', 'best-replay.json'), ('receipt', 'receipt.json'))}
        if (priors[case]['paths'] != expected_paths
                or any(name not in inherited for name in expected_paths.values())):
            raise ConfigurationFailure('Inherited prior path/binding differs: '+case)
    result = dict(policy=POLICY, fresh_input_sha256=digests,
        predecessor_preflight=PREDECESSOR, inherited_input_sha256=inherited, priors=priors,
        model_assets_read=False, hashes_repeated_by_workers=False,
        unchanged_prior_or_project_inputs_rehashed=False,
        source_freeze_assumption='Unchanged project/prior bytes retain frozen attempt01 bindings; parent freezes them and all new v2 bytes throughout attempt02',
        inherited_backend_fingerprinting='Original builder fingerprints its backend per build; paid in worker')
    save_new(output/'preflight.json', result)
    return result


def worker(args):
    folder, anchor = args.worker.resolve(), args.parent_anchor
    spec = load(folder/'spec.json')
    root = Path(spec['root'])
    end, native_end = anchor+60., anchor+52.
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    report = dict(policy=POLICY, case=spec['case'], seed=17, complete=False,
        method_endpoint_accepted=False, qp_success=False, physical_witness_valid=False,
        config_failure=False, resource_violation=False, identity_failure=False,
        parent_anchor=anchor, native_deadline=native_end, admission_deadline=end,
        failures=[], stages=[], native_calls=0)
    stopped, events, active = None, None, 'startup'
    best_plan = best_replay = best_bill = None
    child_cpu0 = children_cpu()
    def stop(signum, frame):
        nonlocal stopped
        stopped = stopped or signum
        raise TimeoutError('Worker stop '+str(signum))
    def check():
        if rss_bytes() > 5*1024**3 or threading.active_count() != 1 or children_cpu() != child_cpu0:
            report.update(config_failure=True, resource_violation=True)
            raise ResourceViolation('Worker RSS/thread/no-child limit failed')
        if stopped is not None or time.monotonic() >= end:
            raise TimeoutError('Worker final deadline/stop reached')
    def stage(name, operation, *, postcheck=True):
        nonlocal active
        active = name
        at, cpu = time.monotonic(), self_cpu()
        try:
            check()
            result = operation()
            if postcheck:
                check()
            return result
        finally:
            report['stages'].append(dict(stage=name, wall_s=time.monotonic()-at,
                cpu_s=self_cpu()-cpu, observed_peak_rss_bytes=rss_bytes()))
    try:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, end-time.monotonic()))
        events = (folder/'events.jsonl').open('x')
        def record(event):
            check()
            events.write(json.dumps(event, allow_nan=False)+'\n'); events.flush()
            check()
        if spec['case'] not in CASES or spec['seed'] != 17:
            raise ConfigurationFailure('Worker specification outside exact cohort')
        expected_name = '%03d-qp-%s' % (CASES.index(spec['case'])+1, spec['case'].replace(':', '-'))
        if (folder.parent != root/'research-20261025/fixed_route_qp/attempt02'
                or folder.name != expected_name):
            raise ConfigurationFailure('V2 worker namespace must be fresh canonical attempt02')
        binding = load(spec['preflight'])
        prior = binding['priors'][spec['case']]
        sys.path.insert(0, str(root/'src'))
        sys.path.insert(0, str(Path(__file__).parent))
        from egglab import claude_cases, physical_learning_cases as bank
        from egglab import native_recharge as nr, native_hull as nh
        case = stage('case_construction', lambda: claude_cases.make(spec['case']))
        market = stage('target_market', lambda: bank.market(case, 'late'))
        plan = stage('load_prior_plan', lambda: load(root/prior['paths']['plan']))
        saved_replay = stage('load_prior_replay', lambda: load(root/prior['paths']['replay']))
        if case.identity() != prior['case_identity'] or plan.get('case_identity') != case.identity():
            report['identity_failure'] = True
            raise ConfigurationFailure('Fresh case/saved prior physical identity mismatch')
        replay = stage('independent_prior_replay', lambda: nr.replay_native(case, plan))
        bill = Fraction(replay['ops_cost'])+nh.supply(market, replay['load'])
        if (replay.get('replay_ok') is not True or saved_replay.get('replay_ok') is not True
                or tuple(map(Fraction, replay['load'])) != tuple(map(Fraction, saved_replay['load']))
                or Fraction(replay['ops_cost']) != Fraction(saved_replay['ops_cost'])
                or bill != Fraction(prior['target_bill_exact']) or len(plan['vehicles']) != prior['fleet_count']):
            report['identity_failure'] = True
            raise ConfigurationFailure('Replayed prior/target bill/fleet differs from original witness')
        best_plan, best_replay, best_bill = plan, replay, bill
        report.update(case_identity=case.identity(), target_market_identity=market.identity(),
            fleet_count=len(plan['vehicles']), fallback_bill_exact=str(bill),
            selected_source='retained_prior', used_fallback=True)
        stage('save_replayed_fallback', lambda: (
            save_new(folder/'initial-fallback-plan.json', plan),
            save_new(folder/'initial-fallback-replay.json', replay)))
        import qp_control_v2 as qp_control
        if Path(qp_control.__file__).resolve() != Path(__file__).with_name('qp_control_v2.py').resolve():
            raise ConfigurationFailure('Imported a different QP helper')
        report['native_calls'] = None  # A raised helper call must not fabricate zero dispatch.
        result = stage('one_direct_fixed_topology_qp', lambda: qp_control.solve(case, market.a, market.b,
            plan, 17, native_end, end, check, record), postcheck=False)
        report.update(native_calls=result['native_calls'], native_call_attempts=result['native_call_attempts'],
            qp_success=result['qp_success'], qp_candidate_admitted=result['qp_candidate_admitted'],
            helper_failures=result['failures'], copy_contract=result['copy_contract'])
        if type(result['native_calls']) is not int or result['native_calls'] not in (0, 1):
            raise ConfigurationFailure('Helper violated single native-call contract')
        if result['config_failure'] or result['fatal_contract']:
            report['config_failure'] = True  # Preserve fatal contract even if the next clock check fails.
        compact = {k: v for k, v in result.items() if k not in ('plan', 'replay')}
        stage('save_qp_stats', lambda: save_new(folder/'qp-result.json', compact))
        if result['config_failure'] or result['fatal_contract']:
            raise ConfigurationFailure('QP helper full-model copy/configuration contract failed')
        candidate = result['plan']
        if candidate is not None:
            checked = stage('independent_qp_candidate_replay', lambda: nr.replay_native(case, candidate))
            candidate_bill = Fraction(checked['ops_cost'])+nh.supply(market, checked['load'])
            if candidate_bill != Fraction(result['true_bill_exact']):
                raise ConfigurationFailure('Helper bill differs from independent exact target recomputation')
            prior_routes = sorted(tuple(v['movements']) for v in plan['vehicles'])
            candidate_routes = sorted(tuple(v['movements']) for v in candidate['vehicles'])
            if (checked.get('replay_ok') is not True or candidate_routes != prior_routes
                    or len(candidate['vehicles']) != prior['fleet_count']):
                report['identity_failure'] = True
                raise ConfigurationFailure('QP candidate independently fails fixed-route physical replay')
            if candidate_bill < best_bill:
                best_plan, best_replay, best_bill = candidate, checked, candidate_bill
                report.update(selected_source='direct_qp', used_fallback=False)
    except BaseException as exc:
        report['failures'].append(dict(stage=active, type=type(exc).__name__, message=str(exc)))
        report['qp_success'] = False
        if (isinstance(exc, (ConfigurationFailure, ResourceViolation, MemoryError, ImportError, KeyError, TypeError))
                or getattr(exc, 'fatal_contract', False)
                or not isinstance(exc, TimeoutError) and active in
                ('case_construction', 'target_market', 'load_prior_plan', 'load_prior_replay',
                 'independent_prior_replay')):
            report['config_failure'] = True
        if isinstance(exc, (ResourceViolation, MemoryError)):
            report['resource_violation'] = True
    finally:
        try:
            if best_plan is not None and not report['config_failure']:
                check()
                save_new(folder/'selected-plan.json', best_plan)
                save_new(folder/'selected-replay.json', best_replay)
                report.update(physical_witness_valid=True, objective_exact=str(best_bill), objective=float(best_bill))
                check()
        except BaseException as exc:
            report['failures'].append(dict(stage='durable_selected_witness', type=type(exc).__name__, message=str(exc)))
            report['qp_success'] = False
        if events is not None:
            try:
                events.flush(); os.fsync(events.fileno()); events.close()
            except BaseException as exc:
                report['failures'].append(dict(stage='events_finalization', type=type(exc).__name__, message=str(exc)))
                report['config_failure'] = True
        report.update(complete=True, stop_signal=stopped, resources=resources(),
            elapsed_before_receipt_s=time.monotonic()-anchor)
        report['method_endpoint_accepted'] = bool(report['physical_witness_valid']
            and not report['config_failure'] and stopped is None and time.monotonic() < end)
        report['method_success'] = bool(report['method_endpoint_accepted'] and report['qp_success']
            and not report['failures'])
        publish(folder/'receipt.json', report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['method_endpoint_accepted'] else 1


def launch_worker(root, output, spec, index):
    """Minimal warm launcher copy: explicit current file, one direct child, no retry."""
    folder = output/('%03d-qp-%s' % (index, spec['case'].replace(':', '-')))
    folder.mkdir(exist_ok=False)
    save_new(folder/'spec.json', dict(spec, root=str(root), preflight=str(output/'preflight.json')))
    save_new(folder/'receipt.json', dict(complete=False, method_endpoint_accepted=False))
    before_child, before_self = children_cpu(), self_cpu()
    anchor = time.monotonic()
    record = dict(case=spec['case'], folder=str(folder), parent_anchor=anchor,
        attempted=False, pid=None, reaped=False, returncode=None, timed_out=False,
        config_failure=False, resource_violation=False, identity_failure=False, failures=[])
    child, cleanup_end = None, None
    with (folder/'stdout.log').open('x') as stdout, (folder/'stderr.log').open('x') as stderr:
        try:
            if threading.active_count() != 1 or rss_bytes() > 5*1024**3:
                record.update(config_failure=True, resource_violation=True)
                raise ResourceViolation('Parent thread/RSS limit failed')
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(folder),
                '--parent-anchor', repr(anchor)], cwd=root, env=dict(os.environ), stdout=stdout, stderr=stderr,
                start_new_session=True, preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (90, 90)))
            record.update(attempted=True, pid=child.pid)
            try:
                child.wait(timeout=max(.001, anchor+60.-time.monotonic()))
            except subprocess.TimeoutExpired:
                record['timed_out'] = True
                cleanup_end = time.monotonic()+3.
                child.terminate()
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            record.update(reaped=True, returncode=child.returncode)
        except BaseException as exc:
            record['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
            if child is None and not isinstance(exc, TimeoutError):
                record['config_failure'] = True
            if child is not None and child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3.
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    record.update(reaped=True, returncode=child.returncode)
                except BaseException as secondary:
                    record['failures'].append(dict(type=type(secondary).__name__, message=str(secondary)))
    try:
        result = load(folder/'receipt.json')
    except Exception as exc:
        result = dict(complete=False, method_endpoint_accepted=False,
            failure=dict(type=type(exc).__name__, message=str(exc)))
    record.update(worker=result, complete_receipt_read_monotonic=time.monotonic(),
        waited_child_cpu_s=children_cpu()-before_child, parent_cpu_s=self_cpu()-before_self,
        unresolved_cpu_reserve_s=90. if child is not None and not record['reaped'] else 0.)
    record['parent_elapsed_s'] = record['complete_receipt_read_monotonic']-anchor
    for flag in FLAGS:
        record[flag] |= result.get(flag, False)
    if result.get('complete') is not True and not record['timed_out']:
        record['config_failure'] = True
        record['failures'].append(dict(type='IncompleteWorkerPacket',
            message='Worker failed without a durable failure classification'))
    record['method_endpoint_accepted'] = bool(record['reaped'] and record['returncode'] == 0
        and not record['timed_out'] and not record['failures'] and not record['config_failure']
        and result.get('complete') is True and result.get('method_endpoint_accepted') is True
        and record['parent_elapsed_s'] <= 60.)
    save_new(folder/'external-receipt.json', record)
    return record


def campaign(args):
    root, output = args.root.resolve(), args.output.resolve()
    if output != root/'research-20261025/fixed_route_qp/attempt02':
        raise ConfigurationFailure('V2 driver permits only fresh canonical attempt02')
    output.mkdir(parents=True, exist_ok=False)
    save_new(output/'receipt.json', dict(complete=False, passed=False))
    report = dict(policy=POLICY, complete=False, passed=False, cases=[], failures=[],
        budgets=dict(cpu_s=TOTAL_CPU, wall_s=TOTAL_WALL, dispatch_cpu_s=DISPATCH_CPU, closure_cpu_s=180),
        scientific_qualification=False, no_automatic_retry=True,
        nonrefundable_attempt01_cpu_s=PRIOR_CPU, nonrefundable_attempt01_elapsed_s=PRIOR_WALL,
        previous_closed_cumulative_cpu_s=7005.07, previous_closed_cumulative_elapsed_sum_s=7178.14,
        legacy_conditional_guard_s=2546.091499549272, legacy_actual_review_cpu='UNKNOWN',
        whole_session_exact_cpu_claim=False)
    stopped, unresolved, binding = None, 0., None
    def stop(signum, frame):
        nonlocal stopped
        stopped = stopped or signum
        raise TimeoutError('Package stop '+str(signum))
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (1800, 1800))
        for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, TOTAL_WALL-PRIOR_WALL-(time.monotonic()-WALL0)))
        binding = preflight(root, output)
        report['fresh_input_sha256'] = binding['fresh_input_sha256']
        report['inherited_input_sha256'] = binding['inherited_input_sha256']
        report['predecessor_preflight'] = binding['predecessor_preflight']
        for index, case in enumerate(CASES, 1):
            if (stopped is not None or PRIOR_CPU+self_cpu()+children_cpu()+unresolved+90. > DISPATCH_CPU
                    or PRIOR_WALL+time.monotonic()-WALL0+63.+180. > TOTAL_WALL):
                stopped = stopped or 'CPU/wall dispatch funding exhausted'
                report['cases'].append(dict(case=case, attempted=False, method_endpoint_accepted=False,
                    operational_prior_available=True,
                    prior_target_bill_exact=binding['priors'][case]['target_bill_exact'],
                    not_dispatched_reason=str(stopped)))
                continue
            row = launch_worker(root, output, dict(case=case, seed=17), index)
            row['operational_prior_available'] = True
            row['prior_target_bill_exact'] = binding['priors'][case]['target_bill_exact']
            row['operational_target_bill_exact'] = (row['worker']['objective_exact']
                if row['method_endpoint_accepted'] else row['prior_target_bill_exact'])
            row['operational_selected_source'] = (row['worker']['selected_source']
                if row['method_endpoint_accepted'] else 'retained_prior')
            report['cases'].append(row)
            unresolved += row['unresolved_cpu_reserve_s']
            if row['config_failure'] or unresolved:
                stopped = stopped or 'Fatal configuration/resource/identity or unreaped worker'
    except BaseException as exc:
        report['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
        stopped = stopped or 'Package failed'
    finally:
        recorded = {row['case'] for row in report['cases']}
        for case in CASES:
            if case not in recorded:
                report['cases'].append(dict(case=case, attempted=False, method_endpoint_accepted=False,
                    operational_prior_available=binding is not None,
                    prior_target_bill_exact=None if binding is None else binding['priors'][case]['target_bill_exact'],
                    not_dispatched_reason=str(stopped)))
        report['cases'].sort(key=lambda row: CASES.index(row['case']))
        report.update(complete=len(report['cases']) == 8, stopped=stopped, resources=resources(),
            elapsed_s=time.monotonic()-WALL0, unresolved_cpu_reserve_s=unresolved,
            accounting_complete=unresolved == 0,
            attempted=sum(row.get('attempted') is True for row in report['cases']),
            admitted=sum(row.get('method_endpoint_accepted') is True for row in report['cases']),
            qp_success=sum(row.get('method_endpoint_accepted') is True
                and row.get('worker', {}).get('qp_success') is True for row in report['cases']))
        report['charged_package_cpu_s'] = PRIOR_CPU+report['resources']['combined_cpu_s']
        report['charged_package_elapsed_sum_s'] = PRIOR_WALL+report['elapsed_s']
        report['passed'] = (report['complete'] and stopped is None and unresolved == 0
            and report['charged_package_cpu_s'] <= TOTAL_CPU
            and report['charged_package_elapsed_sum_s'] <= TOTAL_WALL)
        publish(output/'receipt.json', report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--parent-anchor', type=float)
    args = parser.parse_args()
    if args.worker is not None:
        if args.parent_anchor is None or not math.isfinite(args.parent_anchor):
            raise ValueError('Worker needs parent-owned finite anchor')
        return worker(args)
    if args.output is None:
        raise ValueError('Package requires fresh output directory')
    return campaign(args)


if __name__ == '__main__':
    raise SystemExit(main())
