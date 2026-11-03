"""DRAFT resource-recourse child: fresh acquisition, fixed QP, or bounded routing→QP.

No solver is initialized on import. A source-bound FROZEN/PASS launch is required.
"""
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

POLICY = 'resource-recourse-current-physics-exact-N-worker-v1'
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')
MAX_RSS = 5*1024**3
GROUPS = {10001: 20, 10006: 20, 10009: 28, 10005: 28}


class ContractError(ValueError):
    pass


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ContractError('Cannot load a declared source library')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ContractError('Loaded library path differs')
    return module


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', required=True, type=Path)
    parser.add_argument('--parent-anchor', required=True, type=float)
    parser.add_argument('--spec-sha256', required=True)
    args = parser.parse_args(argv)
    anchor, folder = args.parent_anchor, args.worker
    if (not folder.is_absolute() or not math.isfinite(anchor) or anchor > time.monotonic()
            or len(args.spec_sha256) != 64
            or any(c not in '0123456789abcdef' for c in args.spec_sha256)):
        raise ValueError('Require absolute folder, valid parent anchor and lowercase digest')
    folder = folder.resolve()
    root = Path(__file__).resolve().parents[2]
    first_end, routing_end, native_end, end = anchor+17.5, anchor+35., anchor+52., anchor+60.
    report = dict(policy=POLICY, receipt_complete=False, method_endpoint_accepted=False,
        cell_qualified=False, full_method_success=False, physical_new_prior_valid=False,
        config_failure=False, fatal_contract=False, identity_failure=False, resource_violation=False,
        failures=[], helper_failures=[], parent_anchor=anchor, first_routing_native_deadline=first_end,
        routing_deadline=routing_end, native_deadline=native_end, admission_deadline=end,
        qp_success=False, qp_candidate_admitted=False, route_search_candidate_admitted=False,
        candidate_bill_exact=None, fallback_bill_exact=None, retained_bill_exact=None,
        native_point=None, native_bound=None, native_lower_bound=None,
        route_identity_method='unavailable', fixed_path_recovery_verified=False,
        global_lower_bound=None, certificate_claim=False, route_ordering='UNRESOLVED',
        optimization_bound_supported=False)
    ledger = dict(acquisition_linear=0, routing_MIP=0, QP=0)
    event_counts = Counter()
    stopped = None
    stage = 'launch_admission'
    shared = None
    best_plan = best_replay = best_bill = brief = market = case = None
    phase = None
    published = False

    def fatal(message, *, identity=False, resource_failure=False):
        report['config_failure'] = report['fatal_contract'] = True
        report['identity_failure'] |= identity
        report['resource_violation'] |= resource_failure
        raise ContractError(message)

    def on_signal(signum, frame):
        nonlocal stopped
        stopped = signum
        if signum == signal.SIGXCPU:
            report['config_failure'] = report['fatal_contract'] = report['resource_violation'] = True
        raise TimeoutError('Resource-recourse stop signal '+str(signum))

    def check():
        if stopped is not None or time.monotonic() >= end:
            raise TimeoutError('Inclusive resource-recourse worker stopped/late')
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024
        if rss > MAX_RSS or usage.ru_utime+usage.ru_stime >= 90.:
            fatal('Worker RSS/CPU ceiling exceeded', resource_failure=True)
        if threading.active_count() != 1 or any(os.environ.get(k) != '1' for k in THREAD_ENV):
            fatal('Worker thread contract changed', resource_failure=True)
        try:
            child, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            child = None
        if child is not None:
            fatal('Unexpected worker child process', resource_failure=True)

    def before(deadline):
        check()
        if time.monotonic() >= deadline:
            raise TimeoutError('Absolute resource-recourse stage cutoff exhausted')

    def record(event):
        check()
        event_counts[str(event.get('event', 'unknown'))] += 1
        check()

    def retain(plan, replay, *, enforce_reference=False):
        nonlocal best_plan, best_replay, best_bill, brief
        if (plan.get('case_identity') != case.identity() or len(plan['vehicles']) != spec['fleet_N']
                or enforce_reference and shared._canonical(plan) != reference_paths):
            fatal('Physical witness changed case/exact N/fixed reference paths', identity=True)
        if replay.get('replay_ok') is not True:
            fatal('Physical witness lacks independent replay', identity=True)
        bill = (nh.rational(replay['ops_cost'])+nh.supply(market, replay['load'])) if market else None
        if best_plan is None or bill is None or best_bill is None or bill < best_bill:
            best_plan, best_replay, best_bill = plan, replay, bill
            aa = market.a if market else (0.,)*len(replay['load'])
            bb = market.b if market else (0.,)*len(replay['load'])
            brief = shared._brief(case, plan, replay, nh, aa, bb)
            modes = {m.id: m for m in case.movements}
            service = sum((Q(t.energy_kwh) for t in case.trips), Q(0))
            movement = sum((Q(leg.energy_kwh) for vehicle in plan['vehicles']
                            for mid in vehicle['movements'] for leg in modes[mid].legs), Q(0))
            ideal_grid = (service+movement)/Q(case.efficiency)
            brief.update(period_loads=list(replay['load']), service_energy_exact=str(service),
                movement_energy_exact=str(movement), ideal_grid_demand_exact=str(ideal_grid),
                replay_grid_minus_ideal_exact=str(nh.rational(replay['grid_kwh'])-ideal_grid))
            brief['opportunity_diagnostics'] = classical.opportunity(case, plan, nh)

    try:
        for key in THREAD_ENV:
            os.environ[key] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
        for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGXCPU):
            signal.signal(signum, on_signal)
        check()
        signal.setitimer(signal.ITIMER_REAL, max(.001, end-time.monotonic()))
        launch = json.loads(Path(__file__).with_name('LAUNCH.json').read_text())
        if launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS':
            fatal('DRAFT/unreviewed resource-recourse launch cannot run')
        shared = _load_module(root/'research-20261025/topology_charging/worker.py',
                              'resource_recourse_frozen_pure_helpers')
        classical = _load_module(Path(__file__).with_name('classical.py'),
                                 'resource_recourse_classical')
        stage = 'spec_admission'
        data = (folder/'spec.json').read_bytes()
        if hashlib.sha256(data).hexdigest() != args.spec_sha256:
            fatal('Spec digest differs', identity=True)
        spec = json.loads(data)
        del data
        required = {'root', 'task_id', 'phase', 'group', 'base_id', 'services', 'grid_kw',
            'case', 'expected_case_identity', 'fleet_N', 'reference_selected_ids',
            'original_source0_plan_hash', 'acquisition_plan', 'target_source',
            'expected_market_identity', 'a', 'b'}
        optional = {'acquisition_plan_sha256', 'E_ref_exact', 'original_reference_bill_exact'}
        if not required <= set(spec) or set(spec)-required-optional:
            fatal('Spec field contract differs', identity=True)
        if Path(spec['root']).resolve() != root:
            fatal('Spec source root differs', identity=True)
        phase = spec['phase']
        report.update({key: spec[key] for key in ('task_id', 'phase', 'group', 'base_id',
                       'services', 'grid_kw', 'fleet_N', 'original_source0_plan_hash')})
        if (phase not in ('acquisition', 'fixed', 'adaptive')
                or type(spec['base_id']) is not int or GROUPS.get(spec['base_id']) != spec['services']
                or type(spec['services']) is not int
                or spec['group'] != f"physical_v2_s{spec['base_id']}"
                or type(spec['grid_kw']) not in (int, float) or spec['grid_kw'] not in (90, 45)
                or type(spec['fleet_N']) is not int or spec['fleet_N'] < 1):
            fatal('Spec outside fixed cohort/resource/phase/N', identity=True)
        for key in ('E_ref_exact', 'original_reference_bill_exact'):
            value = spec.get(key)
            if value is not None:
                if not isinstance(value, str):
                    fatal('Optional cost denominator/reference must be exact string', identity=True)
                Q(value)
            report[key] = value
        stage = 'paid_project_imports'
        sys.path.insert(0, str(root/'src'))
        from egglab import native_recharge as nr, native_hull as nh, native_pathflow as pf
        from egglab import physical_learning_cases as physical
        for module, name in ((nr, 'native_recharge.py'), (nh, 'native_hull.py'),
                             (pf, 'native_pathflow.py'), (physical, 'physical_learning_cases.py')):
            if Path(module.__file__).resolve() != root/'src/egglab'/name:
                fatal('Project import path differs', identity=True)
        check()
        stage = 'current_physics_admission'
        case = shared._case(spec['case'], nr)
        nr.validate_case(case)
        if (case.identity() != spec['expected_case_identity'] or len(case.trips) != spec['services']
                or spec['fleet_N'] > case.max_vehicles
                or any(r.grid_kw != spec['grid_kw'] or r.per_bus_kw != 90 or r.connectors != 1
                       for r in case.resources)):
            fatal('Current case/resource/exact-N identity differs', identity=True)
        reference_ids = spec['reference_selected_ids']
        reference_vehicles, _ = pf.recover_paths(case, reference_ids)
        reference_paths = shared._canonical({'vehicles': reference_vehicles})
        if len(reference_vehicles) != spec['fleet_N']:
            fatal('Reference source0 topology differs from frozen N', identity=True)
        report.update(case_identity=case.identity(), native_seed=17, expected_native_method=0,
            original_reference_role='Parent-only no-solve counterfactual, never worker fallback')
        if phase == 'acquisition':
            if (spec['acquisition_plan'] is not None or spec['target_source'] is not None
                    or any(spec[k] is not None for k in ('expected_market_identity', 'a', 'b'))):
                fatal('Acquisition must be one target-independent zero-price solve', identity=True)
        else:
            if spec['target_source'] not in ('source0', 'source1'):
                fatal('Unknown target source tariff', identity=True)
            market = physical.market(case, spec['target_source'])
            nh.validate_market(case, market)
            if (market.identity() != spec['expected_market_identity']
                    or list(market.a) != spec['a'] or list(market.b) != spec['b']):
                fatal('Target market identity differs', identity=True)
            report.update(target_source=spec['target_source'], target_market_identity=market.identity())
        check()

        if phase == 'acquisition':
            stage = 'one_fresh_reference_acquisition'
            acquired = classical.acquire(case, reference_ids, spec['fleet_N'],
                native_end=native_end, end=end, check=check, ledger=ledger, record=record)
            report.update(acquisition_packets=acquired['packets'], acquisition_failures=acquired['failures'])
            if acquired['fatal_contract']:
                fatal('Reference acquisition physical composition failed')
            check()
            if acquired['plan'] is not None:
                replay = nr.replay_native(case, acquired['plan'])
                retain(acquired['plan'], replay, enforce_reference=True)
                report['physical_new_prior_valid'] = True
                report['full_method_success'] = True
            else:
                report['missing_reason'] = 'Fresh current-physics reference acquisition unresolved; no fallback'
        else:
            stage = 'current_acquisition_join'
            prior = spec['acquisition_plan']
            if prior is not None:
                if (spec.get('acquisition_plan_sha256') is not None
                        and nr.digest(prior) != spec['acquisition_plan_sha256']):
                    fatal('Owned acquisition plan canonical digest differs', identity=True)
                replay = nr.replay_native(case, prior)
                retain(prior, replay, enforce_reference=True)
                report['common_prior_bill_exact'] = str(best_bill)
                report['current_acquisition_available'] = True
                shared._write(folder/'best-plan.json', best_plan)
                shared._write(folder/'brief-replay.json', brief)
            else:
                report.update(current_acquisition_available=False, common_prior_bill_exact=None)
            check()
            if phase == 'adaptive':
                stage = 'bounded_classical_routing'
                routed = classical.route(case, market.a, market.b, spec['fleet_N'], prior_plan=prior,
                    first_native_end=first_end, routing_end=routing_end, check=check, ledger=ledger, record=record)
                report.update(routing_packets=routed['packets'], routing_failures=routed['failures'],
                    route_search_candidate_admitted=routed['route_search_candidate_admitted'],
                    selected_route_source=routed['selected_route_source'],
                    routing_bound_scope=routed['bound_scope'])
                if routed['fatal_contract']:
                    fatal('Classical route composition failed')
                check()
                if routed['plan'] is not None:
                    replay = nr.replay_native(case, routed['plan'])
                    retain(routed['plan'], replay)
            if best_plan is None:
                report['missing_reason'] = ('Reference acquisition missing; fixed arm has no QP'
                    if phase == 'fixed' else 'Cold full-graph routing has no admitted witness; no QP')
            else:
                stage = 'QP_fallback_path_admission'
                qp_prior = best_plan
                qp_signature = shared._canonical(qp_prior)
                report['QP_fixed_route_changed_from_reference'] = qp_signature != reference_paths
                selected = [mid for v in qp_prior['vehicles'] for mid in v['movements']]
                recovered, _ = pf.recover_paths(case, selected)
                if shared._canonical({'vehicles': recovered}) != qp_signature:
                    fatal('Selected QP route fails unique canonical recovery', identity=True)
                report['fixed_path_recovery_verified'] = True
                helper = _load_module(root/'research-20261025/warm_replication/qp_control.py',
                                      'resource_recourse_frozen_qp')
                before(native_end)
                stage = 'one_current_route_QP'
                ledger['QP'] = None  # A raised helper cannot invent a zero dispatch count.
                result = helper.solve(case, market.a, market.b, qp_prior, 17,
                                      native_end, end, check, record)
                ledger['QP'] = result['native_calls']
                report.update(qp_status=result['status'], qp_success=result['qp_success'],
                    qp_candidate_admitted=result['qp_candidate_admitted'],
                    candidate_bill_exact=result.get('candidate_bill_exact'),
                    fallback_bill_exact=result.get('fallback_bill_exact'),
                    helper_true_bill_exact=result.get('true_bill_exact'), stats=result['stats'],
                    copy_contract=result['copy_contract'], helper_failures=result['failures'],
                    used_fallback=result['used_fallback'], qp_selected_source=result['selected_source'],
                    qp_native_calls=result['native_calls'], qp_native_call_attempts=result['native_call_attempts'],
                    native_point=result['stats'].get('ObjVal'), native_bound=result['stats'].get('ObjBound'),
                    native_lower_bound=result['stats'].get('native_lower_bound'))
                if result['config_failure'] or result['fatal_contract']:
                    report['config_failure'] = report['fatal_contract'] = True
                if result['policy'] != helper.POLICY or type(ledger['QP']) is not int or ledger['QP'] not in (0, 1):
                    fatal('QP result policy/call count differs', identity=True)
                check()
                if report['fatal_contract']:
                    raise ContractError('QP copy/configuration contract failed')
                stage = 'independent_QP_retained_replay'
                plan = result['plan']
                replay = nr.replay_native(case, plan)
                if shared._canonical(plan) != qp_signature:
                    fatal('QP changed selected fixed-route paths', identity=True)
                bill = nh.rational(replay['ops_cost'])+nh.supply(market, replay['load'])
                if (bill != Q(result['true_bill_exact']) or bill > best_bill
                        or Q(result['fallback_bill_exact']) != best_bill):
                    fatal('QP retained/fallback cost contract differs', identity=True)
                if result['selected_source'] == 'direct_qp' and not result['used_fallback']:
                    if result.get('candidate_bill_exact') is None or bill != Q(result['candidate_bill_exact']):
                        fatal('Exposed QP candidate cost differs', identity=True)
                    report['route_identity_method'] = 'direct_candidate_canonical_comparison'
                elif (result['qp_candidate_admitted'] and result['selected_source'] == 'fallback'
                        and result['used_fallback'] and not result['failures']
                        and result['copy_contract'].get('passed') is True
                        and result['native_calls'] == result['native_call_attempts'] == 1):
                    report['route_identity_method'] = 'source_guarded_unique_path_inference'
                agreement = shared._agreement(result, nr.OBJECTIVE_TOL)
                report['numerical_agreement'] = agreement
                discrepancy = agreement.get('optimal_candidate_fallback_discrepancy', False)
                report['optimal_candidate_fallback_discrepancy'] = discrepancy
                retain(plan, replay, enforce_reference=phase == 'fixed')
                stats = result['stats']
                report['cell_qualified'] = bool(result['qp_success'] and result['qp_candidate_admitted']
                    and result['copy_contract'].get('passed') is True and not result['failures']
                    and result['native_calls'] == result['native_call_attempts'] == 1
                    and stats.get('Status') == 2 and stats.get('native_optimal') is True
                    and stats.get('Method') == 0 and stats.get('seed') == 17 and stats.get('threads') == 1
                    and agreement.get('source_guards_passed') is True and not discrepancy
                    and report['route_identity_method'] in ('direct_candidate_canonical_comparison',
                                                          'source_guarded_unique_path_inference'))
                report['full_method_success'] = report['cell_qualified'] and (
                    phase == 'fixed' or report['route_search_candidate_admitted'])
                check()
    except Exception as exc:
        report['failures'].append(dict(stage=stage, type=type(exc).__name__, message=str(exc)))
        report['cell_qualified'] = report['full_method_success'] = False
        if isinstance(exc, ContractError) or (not isinstance(exc, TimeoutError) and stage in (
                'launch_admission', 'spec_admission', 'paid_project_imports', 'current_physics_admission',
                'current_acquisition_join', 'QP_fallback_path_admission', 'independent_QP_retained_replay')):
            report['config_failure'] = report['fatal_contract'] = True
    finally:
        if shared is not None and best_plan is not None and not report['fatal_contract']:
            try:
                check()
                shared._write(folder/'best-plan.json', best_plan)
                shared._write(folder/'brief-replay.json', brief)
                check()
                published = True
                report.update(physical_witness_valid=True, selected_decomposition=brief,
                    retained_route_changed_from_reference=shared._canonical(best_plan) != reference_paths,
                    retained_bill_exact=str(best_bill) if best_bill is not None else None,
                    true_bill_exact=str(best_bill) if best_bill is not None else None)
                denominator = report.get('E_ref_exact')
                report['retained_cost_over_E_ref'] = (str(best_bill/Q(denominator))
                    if best_bill is not None and denominator is not None and Q(denominator) > 0 else None)
            except Exception as exc:
                report['failures'].append(dict(stage='durable_physical_output', type=type(exc).__name__, message=str(exc)))
                report['cell_qualified'] = report['full_method_success'] = False
        report['stage_native_calls'] = dict(ledger)
        report['native_calls'] = sum(ledger.values()) if all(type(v) is int for v in ledger.values()) else None
        report['event_counts'] = dict(event_counts)
        report['stop_signal'] = stopped
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report['resources'] = dict(user_s=usage.ru_utime, system_s=usage.ru_stime,
            cpu_s=usage.ru_utime+usage.ru_stime,
            peak_rss_bytes=usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024,
            cpu_limit_s=90, rss_limit_bytes=MAX_RSS, python_threads=threading.active_count())
        now = time.monotonic()
        report.update(receipt_complete=True, returned_monotonic=now, elapsed_s=now-anchor,
            method_endpoint_accepted=bool(published and stopped is None and now < end
                                          and not report['fatal_contract']))
        if not report['method_endpoint_accepted']:
            report['cell_qualified'] = report['full_method_success'] = report['physical_new_prior_valid'] = False
        signal.setitimer(signal.ITIMER_REAL, 0)
        if shared is not None:
            shared._write(folder/'receipt.json', report)
        else:
            # Draft rejection/bootstrap failure preserves the parent's false placeholder.
            return 2
    return 2 if report['fatal_contract'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
