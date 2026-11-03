"""One source-bound fixed-route/target-tariff decision; never dispatch a retry."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading
import time

POLICY = 'topology-charging-stored-witness-one-QP-worker-v1'
MAX_RSS = 5 * 1024**3
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')


class ContractError(ValueError):
    pass


def _write(path, value):
    """One durable replacement; parent owns the original receipt placeholder."""
    temporary = path.with_name(path.name + '.worker-tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, allow_nan=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _canonical(plan):
    return tuple(sorted((tuple(v['trips']), tuple(v['movements']))
                        for v in plan['vehicles']))


def _case(raw, nr):
    fields = dict(raw)
    fields['trips'] = tuple(nr.Trip(**t) for t in raw['trips'])
    fields['movements'] = tuple(nr.Movement(**dict(
        m, legs=tuple(nr.Leg(**leg) for leg in m['legs']))) for m in raw['movements'])
    fields['resources'] = tuple(nr.Resource(**r) for r in raw['resources'])
    fields['market_edges_min'] = tuple(raw['market_edges_min'])
    return nr.NativeCase(**fields)


def _brief(case, plan, replay, nh, a, b):
    modes = {m.id: m for m in case.movements}
    minutes = sum((Q(leg.arrive_min)-Q(leg.depart_min)
                   for vehicle in plan['vehicles'] for mid in vehicle['movements']
                   for leg in modes[mid].legs), Q(0))
    vehicle_cost = nh.rational(case.vehicle_cost)*len(plan['vehicles'])
    deadhead_cost = nh.rational(case.deadhead_cost_per_min)*minutes
    linear = sum((nh.rational(aa)*nh.rational(load)
                  for aa, load in zip(a, replay['load'])), Q(0))
    quadratic = sum((nh.rational(bb)*nh.rational(load)**2/2
                     for bb, load in zip(b, replay['load'])), Q(0))
    ops = nh.rational(replay['ops_cost'])
    return dict(replay_ok=replay['replay_ok'], fleet_count=len(plan['vehicles']),
        vehicle_cost_exact=str(vehicle_cost), deadhead_minutes_exact=str(minutes),
        deadhead_cost_exact=str(deadhead_cost), ops_cost_exact=str(ops),
        ops_component_residual_exact=str(ops-vehicle_cost-deadhead_cost),
        linear_electricity_exact=str(linear), quadratic_electricity_exact=str(quadratic),
        electricity_exact=str(linear+quadratic), total_exact=str(ops+linear+quadratic),
        grid_kwh_exact=str(nh.rational(replay['grid_kwh'])),
        consumption_kwh_exact=str(nh.rational(replay['consumption_kwh'])),
        max_grid_kw=replay['max_grid_kw'], units='generator cost units; kWh; minutes')


def _agreement(result, objective_tol):
    """Point-agreement envelope only; supplies no optimization-gap bound."""
    stats = result['stats']
    candidate = result.get('candidate_bill_exact')
    if candidate is None:
        return dict(available=False, reason='No admitted fresh candidate')
    native = stats.get('ObjVal')
    if (type(native) not in (int, float) or not math.isfinite(native)
            or stats.get('raw_objective_exact') is None):
        return dict(available=False, reason='Missing finite native point/raw objective')
    raw = Q(stats['raw_objective_exact'])
    bill, fallback = Q(candidate), Q(result['fallback_bill_exact'])
    native_float, rounded_raw = float(native), float(raw)
    subtraction = rounded_raw-native_float
    if not all(math.isfinite(v) for v in (native_float, rounded_raw, subtraction)):
        return dict(available=False, reason='Nonfinite point-agreement conversion')
    epsilon = Q(objective_tol)
    raw_conversion = abs(raw-Q(rounded_raw))
    subtraction_rounding = abs(Q(subtraction)-(Q(rounded_raw)-Q(native_float)))
    envelope = 2*epsilon+raw_conversion+subtraction_rounding
    passed = abs(subtraction) <= objective_tol and abs(bill-raw) <= epsilon
    return dict(available=True, source_guards_passed=passed,
        objective_tol_binary_exact=str(epsilon), raw_conversion_exact=str(raw_conversion),
        subtraction_rounding_exact=str(subtraction_rounding), e_agree_exact=str(envelope),
        candidate_minus_raw_exact=str(bill-raw),
        candidate_minus_native_point_exact=str(bill-Q(native_float)),
        candidate_minus_fallback_exact=str(bill-fallback),
        optimal_candidate_fallback_discrepancy=(
            stats.get('native_optimal') is True and bill-fallback > envelope),
        interpretation='Source-point agreement only; optimization uncertainty unbounded here')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', required=True, type=Path)
    parser.add_argument('--parent-anchor', required=True, type=float)
    parser.add_argument('--spec-sha256', required=True)
    args = parser.parse_args(argv)
    anchor = args.parent_anchor
    folder = args.worker
    if (not folder.is_absolute() or not math.isfinite(anchor) or anchor > time.monotonic()
            or len(args.spec_sha256) != 64
            or any(c not in '0123456789abcdef' for c in args.spec_sha256)):
        raise ValueError('Require absolute task folder, finite anchor and lowercase SHA256')
    folder = folder.resolve()
    native_end, end = anchor+52., anchor+60.
    report = dict(policy=POLICY, receipt_complete=False, method_endpoint_accepted=False,
        cell_qualified=False, config_failure=False, fatal_contract=False,
        resource_violation=False, identity_failure=False, failures=[],
        parent_anchor=anchor, native_deadline=native_end, admission_deadline=end,
        native_calls=None, native_call_attempts=None, qp_success=False,
        qp_candidate_admitted=False, candidate_path_verification='not_available',
        route_identity_method='unavailable', fixed_path_recovery_verified=False,
        optimization_bound_supported=False, route_ordering='UNRESOLVED',
        global_lower_bound=None, certificate_claim=False)
    active = 'worker_setup'
    stopped = None
    best_plan = best_replay = best_bill = None
    best_brief = None
    fallback_signature = None
    numerical = None
    event_counts = Counter()
    publication_complete = False

    def fail_contract(message, *, identity=False, resource_failure=False):
        report['config_failure'] = report['fatal_contract'] = True
        report['identity_failure'] |= identity
        report['resource_violation'] |= resource_failure
        raise ContractError(message)

    def on_signal(signum, frame):
        nonlocal stopped
        stopped = signum
        if signum == signal.SIGXCPU:
            report['config_failure'] = report['fatal_contract'] = True
            report['resource_violation'] = True
        raise TimeoutError('Worker stop signal '+str(signum))

    def check(deadline=end):
        if stopped is not None:
            raise TimeoutError('Worker stop signal remains latched')
        if time.monotonic() >= deadline:
            raise TimeoutError('Inclusive worker deadline exhausted')
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024
        if rss > MAX_RSS or usage.ru_utime+usage.ru_stime >= 90.:
            fail_contract('Worker RSS/CPU resource limit exceeded', resource_failure=True)
        if threading.active_count() != 1 or any(os.environ.get(k) != '1' for k in THREAD_ENV):
            fail_contract('Worker thread contract changed', resource_failure=True)
        try:
            child, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            child = None
        if child is not None:
            fail_contract('Worker created an unexpected child process', resource_failure=True)

    def record(event):
        check()
        # Never copy extraction ledgers, sessions, native values or matrices.
        event_counts[str(event.get('event', 'unknown'))] += 1
        check()

    try:
        for key in THREAD_ENV:
            os.environ[key] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
        for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGXCPU):
            signal.signal(signum, on_signal)
        check()
        signal.setitimer(signal.ITIMER_REAL, max(0.001, end-time.monotonic()))
        active = 'spec_read_once'
        data = (folder/'spec.json').read_bytes()
        if hashlib.sha256(data).hexdigest() != args.spec_sha256:
            fail_contract('Worker spec digest differs', identity=True)
        spec = json.loads(data)
        del data
        required = {'root', 'task_id', 'group', 'base_id', 'services', 'route_source',
            'target_source', 'case', 'prior_plan', 'expected_case_identity',
            'expected_market_identity', 'a', 'b'}
        optional = {'baseline_F_exact', 'original_Ebar_exact'}
        if not required <= set(spec) or set(spec)-required-optional:
            fail_contract('Worker spec field contract differs', identity=True)
        report.update({key: spec[key] for key in ('task_id', 'group', 'base_id',
                      'services', 'route_source', 'target_source')})
        for key in optional & set(spec):
            if not isinstance(spec[key], str):
                fail_contract('Optional baseline metadata must be exact strings', identity=True)
            Q(spec[key])
            report[key] = spec[key]
        root = Path(spec['root']).resolve()
        if root != Path(__file__).resolve().parents[2]:
            fail_contract('Worker root differs from its source tree', identity=True)
        if (spec['route_source'] not in ('source0', 'source1')
                or spec['target_source'] not in ('source0', 'source1')
                or type(spec['base_id']) is not int or spec['base_id'] not in range(10000, 10128)
                or spec['group'] != f"physical_v2_s{spec['base_id']}"
                or type(spec['services']) is not int or spec['services'] not in (20, 28)):
            fail_contract('Worker case/source routing contract differs', identity=True)
        check()
        active = 'paid_project_imports'
        sys.path.insert(0, str(root/'src'))
        from egglab import native_recharge as nr, native_hull as nh, native_pathflow as pf
        from egglab import physical_learning_cases as physical
        for module, name in ((nr, 'native_recharge.py'), (nh, 'native_hull.py'),
                             (pf, 'native_pathflow.py'),
                             (physical, 'physical_learning_cases.py')):
            if Path(module.__file__).resolve() != root/'src'/'egglab'/name:
                fail_contract('Worker imported another project source', identity=True)
        check()
        active = 'stored_case_prior_replay'
        case = _case(spec['case'], nr)
        if (case.identity() != spec['expected_case_identity']
                or len(case.trips) != spec['services']
                or physical.assignment(spec['base_id'])['services'] != spec['services']):
            fail_contract('Stored case identity/service assignment differs', identity=True)
        market = physical.market(case, spec['target_source'])
        nh.validate_market(case, market)
        if (market.identity() != spec['expected_market_identity']
                or list(market.a) != spec['a'] or list(market.b) != spec['b']):
            fail_contract('Target market identity/coefficients differ', identity=True)
        report.update(case_identity=case.identity(), target_market_identity=market.identity(),
                      native_seed=17, expected_native_method=0)
        fallback = spec['prior_plan']
        best_replay = nr.replay_native(case, fallback)
        fallback_signature = _canonical(fallback)
        fixed_ids = [mid for vehicle in fallback['vehicles'] for mid in vehicle['movements']]
        recovered, _ = pf.recover_paths(case, fixed_ids)
        if _canonical({'vehicles': recovered}) != fallback_signature:
            fail_contract('Unique fixed-ID path recovery differs from the stored prior', identity=True)
        report['fixed_path_recovery_verified'] = True
        best_plan = fallback
        best_bill = nh.rational(best_replay['ops_cost'])+nh.supply(market, best_replay['load'])
        best_brief = _brief(case, best_plan, best_replay, nh, market.a, market.b)
        report.update(fallback_bill_exact=str(best_bill), fleet_count=len(fallback['vehicles']))
        if 'baseline_F_exact' in spec and Q(spec['baseline_F_exact']) != best_bill:
            fail_contract('Frozen baseline valuation differs from independent replay', identity=True)
        check()
        active = 'durable_prior'
        _write(folder/'best-plan.json', best_plan)
        _write(folder/'brief-replay.json', best_brief)
        check()

        active = 'helper_load'
        helper_path = root/'research-20261025'/'warm_replication'/'qp_control.py'
        module_spec = importlib.util.spec_from_file_location('topology_charging_frozen_qp', helper_path)
        if module_spec is None or module_spec.loader is None:
            fail_contract('Cannot load the frozen QP helper', identity=True)
        helper = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(helper)
        if Path(helper.__file__).resolve() != helper_path.resolve():
            fail_contract('QP helper path identity differs', identity=True)
        check(native_end)
        active = 'one_fixed_route_QP'
        result = helper.solve(case, market.a, market.b, fallback, 17,
                              native_end, end, check, record)
        if result['policy'] != helper.POLICY:
            fail_contract('QP helper result policy differs', identity=True)
        report.update(native_calls=result['native_calls'], native_call_attempts=result['native_call_attempts'],
            qp_success=result['qp_success'], qp_candidate_admitted=result['qp_candidate_admitted'],
            qp_status=result['status'], stats=result['stats'], copy_contract=result['copy_contract'],
            helper_failures=result['failures'], selected_source=result['selected_source'],
            used_fallback=result['used_fallback'], candidate_bill_exact=result.get('candidate_bill_exact'),
            helper_true_bill_exact=result.get('true_bill_exact'),
            native_point=result['stats'].get('ObjVal'), native_bound=result['stats'].get('ObjBound'),
            native_lower_bound=result['stats'].get('native_lower_bound'),
            native_bound_scope=result['stats'].get('lower_bound_scope'))
        # Latch fatal metadata before any post-call timeout check.
        if result['config_failure'] or result['fatal_contract']:
            report['config_failure'] = report['fatal_contract'] = True
        if result['native_calls'] == 0 and any(
                failure.get('stage') in ('original_model', 'copy_contract')
                and failure.get('type') != 'TimeoutError' for failure in result['failures']):
            report['bootstrap_or_model_qualification_failure'] = True
            report['config_failure'] = report['fatal_contract'] = True
        if result['native_calls'] not in (0, 1) or type(result['native_calls']) is not int:
            fail_contract('QP helper violated one-call dispatch contract')
        check()
        if report['fatal_contract']:
            raise ContractError('QP helper reported fatal copy/configuration failure')
        active = 'independent_retained_replay'
        plan = result['plan']
        if plan is None:
            raise ValueError('QP helper returned no retained physical plan')
        replay = nr.replay_native(case, plan)
        if (_canonical(plan) != fallback_signature or len(plan['vehicles']) != report['fleet_count']
                or plan.get('case_identity') != spec['expected_case_identity']):
            fail_contract('Retained physical plan changed canonical fixed paths/identity', identity=True)
        bill = nh.rational(replay['ops_cost'])+nh.supply(market, replay['load'])
        if bill != Q(result['true_bill_exact']) or bill > best_bill:
            fail_contract('Retained physical bill differs or fails fallback retention', identity=True)
        if Q(result['fallback_bill_exact']) != best_bill:
            fail_contract('Helper fallback valuation differs', identity=True)
        if result['selected_source'] == 'direct_qp' and not result['used_fallback']:
            if (not result['qp_candidate_admitted'] or result.get('candidate_bill_exact') is None
                    or bill != Q(result['candidate_bill_exact'])):
                fail_contract('Exposed candidate selection/cost fields disagree', identity=True)
            report['candidate_path_verification'] = 'independently_verified_exposed_candidate'
            report['route_identity_method'] = 'direct_candidate_canonical_comparison'
        elif result['qp_candidate_admitted']:
            inference_conditions = (result['selected_source'] == 'fallback' and result['used_fallback']
                and report['fixed_path_recovery_verified']
                and result['copy_contract'].get('passed') is True and not result['failures']
                and result['native_calls'] == result['native_call_attempts'] == 1)
            if inference_conditions:
                # Frozen helper's fresh-candidate admission proves same unique ID set,
                # fleet, case and physical replay. Unique recovery fixes its paths.
                # The independently replayed fallback is NOT presented as that candidate.
                report['candidate_path_verification'] = 'source_guarded_unique_recovery_verified'
                report['route_identity_method'] = 'source_guarded_unique_path_inference'
            else:
                report['candidate_path_verification'] = 'unknown_not_exposed_by_helper'
        numerical = _agreement(result, nr.OBJECTIVE_TOL)
        report['numerical_agreement'] = numerical
        discrepancy = numerical.get('optimal_candidate_fallback_discrepancy', False)
        report['optimal_candidate_fallback_discrepancy'] = discrepancy
        best_plan, best_replay, best_bill = plan, replay, bill
        best_brief = _brief(case, plan, replay, nh, market.a, market.b)
        stats = result['stats']
        report['cell_qualified'] = bool(result['qp_success'] and result['qp_candidate_admitted']
            and result['copy_contract'].get('passed') is True and not result['failures']
            and result['native_calls'] == result['native_call_attempts'] == 1
            and stats.get('Status') == 2 and stats.get('native_optimal') is True
            and stats.get('Method') == 0 and stats.get('threads') == 1 and stats.get('seed') == 17
            and numerical.get('source_guards_passed') is True and not discrepancy
            and report['route_identity_method'] in ('direct_candidate_canonical_comparison',
                                                    'source_guarded_unique_path_inference'))
        check()
    except Exception as exc:
        report['failures'].append(dict(stage=active, type=type(exc).__name__, message=str(exc)))
        report['cell_qualified'] = False
        if isinstance(exc, ContractError) or (not isinstance(exc, TimeoutError) and active in (
                'spec_read_once', 'paid_project_imports', 'stored_case_prior_replay',
                'helper_load', 'one_fixed_route_QP', 'independent_retained_replay')):
            report['config_failure'] = report['fatal_contract'] = True
    finally:
        report['stop_signal'] = stopped
        report['event_counts'] = dict(event_counts)
        if best_plan is not None and not report['fatal_contract']:
            try:
                active = 'durable_retained_physical_output'
                check()
                _write(folder/'best-plan.json', best_plan)
                _write(folder/'brief-replay.json', best_brief)
                check()
                publication_complete = True
                report.update(true_bill_exact=str(best_bill),
                    retained_bill_exact=str(best_bill), physical_witness_valid=True,
                    selected_decomposition=best_brief)
                if report.get('baseline_F_exact') is not None:
                    gain = Q(report['baseline_F_exact'])-best_bill
                    report['charging_gain_exact'] = str(gain)
                    denominator = report.get('original_Ebar_exact')
                    report['charging_gain_over_original_Ebar'] = (
                        str(gain/Q(denominator)) if denominator is not None and Q(denominator) > 0 else None)
            except Exception as exc:
                report['failures'].append(dict(stage=active, type=type(exc).__name__, message=str(exc)))
                report['cell_qualified'] = False
        now = time.monotonic()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['resources'] = dict(user_s=usage.ru_utime, system_s=usage.ru_stime,
            cpu_s=usage.ru_utime+usage.ru_stime,
            peak_rss_bytes=usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024,
            cpu_limit_s=90, rss_limit_bytes=MAX_RSS, python_threads=threading.active_count())
        report.update(returned_monotonic=now, elapsed_s=now-anchor,
            method_endpoint_accepted=bool(publication_complete and stopped is None
                and now < end and not report['fatal_contract']), receipt_complete=True)
        if not report['method_endpoint_accepted']:
            report['cell_qualified'] = False
        # Always preserve failure/spend, even when the scientific deadline is lost.
        signal.setitimer(signal.ITIMER_REAL, 0)
        _write(folder/'receipt.json', report)
        # Parent must observe process exit and complete receipt within its same end.
    return 2 if report['fatal_contract'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
