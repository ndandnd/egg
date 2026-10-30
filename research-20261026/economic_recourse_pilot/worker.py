"""DRAFT target-QP acquisition or one protected-incumbent economic MIQP worker."""
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

POLICY = 'target-charged-common-incumbent-economic-recourse-worker-v1'
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
MAX_RSS = 5*1024**3


class ContractError(ValueError):
    pass


def library(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ContractError('Cannot load a declared source library')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ContractError('Imported library path differs')
    return module


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', required=True, type=Path)
    parser.add_argument('--parent-anchor', required=True, type=float)
    parser.add_argument('--spec-sha256', required=True)
    args = parser.parse_args(argv)
    anchor = args.parent_anchor
    if (not args.worker.is_absolute() or not math.isfinite(anchor) or anchor > time.monotonic()
            or len(args.spec_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.spec_sha256)):
        raise ValueError('Require absolute task folder, parent anchor and lowercase SHA256')
    folder, root = args.worker.resolve(), Path(__file__).resolve().parents[2]
    native_end, end = anchor+52., anchor+60.
    report = dict(policy=POLICY, receipt_complete=False, method_endpoint_accepted=False,
        acquisition_qualified=False, cell_qualified=False, strict_method_success=False,
        config_failure=False, fatal_contract=False, resource_violation=False, identity_failure=False,
        physical_witness_valid=False, failures=[], helper_failures=[], qualification_discrepancies=[],
        native_calls=None, native_call_attempts=None,
        qp_success=False, qp_candidate_admitted=False, miqp_success=False, miqp_candidate_admitted=False,
        candidate_bill_exact=None, fallback_bill_exact=None, retained_bill_exact=None,
        native_point=None, native_bound=None, native_lower_bound=None, native_start=None,
        parent_anchor=anchor, native_deadline=native_end, admission_deadline=end,
        candidate_path_verification='not_available', retained_route_changed_from_input=False,
        global_lower_bound=None, certificate_claim=False, optimization_bound_supported=False,
        ideal_route_ordering='UNRESOLVED')
    shared = None
    stage, phase, stopped = 'launch_admission', None, None
    best_plan = best_replay = best_bill = best_brief = None
    initial_bill = initial_electricity = None
    input_signature = None
    event_counts = Counter()
    published = False

    def fatal(message, *, identity=False, resource_failure=False):
        report['config_failure'] = report['fatal_contract'] = True
        report['identity_failure'] |= identity
        report['resource_violation'] |= resource_failure
        raise ContractError(message)

    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        if signum == signal.SIGXCPU:
            report['config_failure'] = report['fatal_contract'] = report['resource_violation'] = True
        raise TimeoutError('Economic worker stop signal '+str(signum))

    def check(deadline=end):
        if stopped is not None or time.monotonic() >= deadline:
            raise TimeoutError('Economic worker absolute clock/stop boundary')
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024
        if rss > MAX_RSS or usage.ru_utime+usage.ru_stime >= 90:
            fatal('Economic worker CPU/RSS resource ceiling', resource_failure=True)
        if threading.active_count() != 1 or any(os.environ.get(key) != '1' for key in THREAD_ENV):
            fatal('Economic worker thread contract changed', resource_failure=True)
        try:
            child, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            child = None
        if child is not None:
            fatal('Unexpected economic worker child process', resource_failure=True)

    def record(event):
        check()
        event_counts[str(event.get('event', 'unknown'))] += 1
        check()

    def brief(plan, replay):
        output = shared._brief(case, plan, replay, nh, market.a, market.b)
        modes = {m.id: m for m in case.movements}
        service = sum((Q(t.energy_kwh) for t in case.trips), Q(0))
        movement = sum((Q(leg.energy_kwh) for vehicle in plan['vehicles']
                        for mid in vehicle['movements'] for leg in modes[mid].legs), Q(0))
        ideal_grid = (service+movement)/Q(case.efficiency)
        output.update(period_loads=list(replay['load']), service_energy_exact=str(service),
            movement_energy_exact=str(movement), ideal_grid_demand_exact=str(ideal_grid),
            replay_grid_minus_ideal_exact=str(nh.rational(replay['grid_kwh'])-ideal_grid))
        return output

    try:
        for key in THREAD_ENV:
            os.environ[key] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
        for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGXCPU):
            signal.signal(sig, stop)
        check()
        signal.setitimer(signal.ITIMER_REAL, max(.001, end-time.monotonic()))
        launch = json.loads(Path(__file__).with_name('LAUNCH.json').read_text())
        if launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS':
            fatal('DRAFT/unreviewed economic launch cannot read a worker spec')
        miqp = library(Path(__file__).with_name('miqp_control.py'), 'economic_frozen_miqp_definitions')
        if launch.get('mixed_integer_parameters') != miqp.PARAMETERS:
            fatal('Frozen mixed-integer parameter commitment differs')
        shared = library(root/'research-20261025/topology_charging/worker.py', 'economic_shared_pure_helpers')
        stage = 'spec_admission'
        data = (folder/'spec.json').read_bytes()
        if hashlib.sha256(data).hexdigest() != args.spec_sha256:
            fatal('Worker spec digest differs', identity=True)
        spec = json.loads(data)
        del data
        required = {'root', 'task_id', 'context_id', 'phase', 'group', 'base_id', 'services', 'case',
            'expected_case_identity', 'fleet_N', 'target_source', 'expected_market_identity',
            'a', 'b', 'input_plan', 'input_plan_sha256', 'original_source0_plan_hash'}
        if not required <= set(spec) or set(spec)-required-{'common_incumbent_qualification'}:
            fatal('Economic spec field contract differs', identity=True)
        report.update({key: spec[key] for key in ('task_id', 'context_id', 'phase', 'group',
                       'base_id', 'services', 'target_source', 'fleet_N', 'original_source0_plan_hash')})
        phase = spec['phase']
        if (Path(spec['root']).resolve() != root or phase not in ('target_qp', 'route_miqp')
                or type(spec['base_id']) is not int or spec['base_id'] not in range(10000, 10128)
                or spec['group'] != f"physical_v2_s{spec['base_id']}"
                or type(spec['services']) is not int or spec['services'] not in (20, 28)
                or spec['target_source'] not in ('source0', 'source1')
                or type(spec['fleet_N']) is not int or spec['fleet_N'] <= 0):
            fatal('Economic task identity/profile/fleet/source differs', identity=True)
        stage = 'paid_project_imports'
        sys.path.insert(0, str(root/'src'))
        from egglab import native_recharge as nr, native_hull as nh, native_pathflow as pf
        from egglab import physical_learning_cases as physical
        for module, name in ((nr, 'native_recharge.py'), (nh, 'native_hull.py'),
                             (pf, 'native_pathflow.py'), (physical, 'physical_learning_cases.py')):
            if Path(module.__file__).resolve() != root/'src/egglab'/name:
                fatal('Project import path differs', identity=True)
        check()
        stage = 'input_physical_admission'
        case = shared._case(spec['case'], nr)
        if (case.identity() != spec['expected_case_identity'] or len(case.trips) != spec['services']
                or physical.assignment(spec['base_id'])['services'] != spec['services']
                or not 1 <= spec['fleet_N'] <= case.max_vehicles
                or any(r.grid_kw != 90 or r.per_bus_kw != 90 or r.connectors != 1 for r in case.resources)):
            fatal('Unchanged original physics/profile/exact-N differs', identity=True)
        market = physical.market(case, spec['target_source'])
        nh.validate_market(case, market)
        if (market.identity() != spec['expected_market_identity']
                or list(market.a) != spec['a'] or list(market.b) != spec['b']):
            fatal('Economic target market identity differs', identity=True)
        prior = spec['input_plan']
        digest = nr.digest(prior)
        if digest != spec['input_plan_sha256']:
            fatal('Input physical plan canonical digest differs', identity=True)
        replay = nr.replay_native(case, prior)
        if len(prior['vehicles']) != spec['fleet_N']:
            fatal('Input physical plan differs from exact N', identity=True)
        input_signature = shared._canonical(prior)
        ids = [mid for v in prior['vehicles'] for mid in v['movements']]
        recovered, _ = pf.recover_paths(case, ids)
        if shared._canonical({'vehicles': recovered}) != input_signature:
            fatal('Input topology is not uniquely recovered', identity=True)
        bill = nh.rational(replay['ops_cost'])+nh.supply(market, replay['load'])
        if phase == 'target_qp':
            if digest != spec['original_source0_plan_hash'] or spec.get('common_incumbent_qualification') is not None:
                fatal('Target acquisition must use the original source0 witness', identity=True)
        else:
            qualification = spec.get('common_incumbent_qualification')
            if not isinstance(qualification, dict) or qualification.get('target_qp_qualified') is not True:
                fatal('Routing prerequisite has no qualified target-QP incumbent', identity=True)
            expected = dict(case_identity=case.identity(), target_market_identity=market.identity(),
                target_source=spec['target_source'], fleet_N=spec['fleet_N'], retained_bill_exact=str(bill),
                input_plan_sha256=digest)
            if (not qualification.get('task_id') or any(qualification.get(k) != v for k, v in expected.items())):
                fatal('Common incumbent qualification join differs', identity=True)
            report['common_incumbent_qualification'] = qualification
        best_plan, best_replay, best_bill = prior, replay, bill
        best_brief = brief(prior, replay)
        initial_bill, initial_electricity = bill, Q(best_brief['electricity_exact'])
        report.update(case_identity=case.identity(), target_market_identity=market.identity(),
            input_plan_sha256=digest, fallback_bill_exact=str(bill), initial_bill_exact=str(bill),
            initial_electricity_exact=str(initial_electricity), fixed_path_recovery_verified=True)
        check()
        stage = 'durable_input_endpoint'
        shared._write(folder/'best-plan.json', best_plan)
        shared._write(folder/'brief-replay.json', best_brief)
        check()
        stage = 'helper_load'
        helper_path = (root/'research-20261025/warm_replication/qp_control.py' if phase == 'target_qp'
                       else Path(__file__).with_name('miqp_control.py'))
        helper = library(helper_path, 'economic_target_qp_source_bound_helper') if phase == 'target_qp' else miqp
        check(native_end)
        stage = 'one_native_'+phase
        if phase == 'target_qp':
            result = helper.solve(case, market.a, market.b, prior, 17, native_end, end, check, record)
            candidate_flag, success_flag = result['qp_candidate_admitted'], result['qp_success']
            report.update(qp_candidate_admitted=candidate_flag, qp_success=success_flag)
        else:
            result = helper.solve(case, market.a, market.b, prior, 17, native_end, end, check, record,
                                  fleet_N=spec['fleet_N'])
            candidate_flag, success_flag = result['miqp_candidate_admitted'], result['miqp_success']
            report.update(miqp_candidate_admitted=candidate_flag, miqp_success=success_flag,
                native_start=result['native_start'], candidate_route_changed_from_input=result['candidate_route_changed_from_prior'])
        report.update(native_calls=result['native_calls'], native_call_attempts=result['native_call_attempts'],
            helper_status=result['status'], helper_failures=result['failures'], stats=result['stats'],
            copy_contract=result['copy_contract'], selected_source=result['selected_source'], used_fallback=result['used_fallback'],
            candidate_bill_exact=result.get('candidate_bill_exact'), helper_true_bill_exact=result.get('true_bill_exact'),
            native_point=result['stats'].get('ObjVal'), native_bound=result['stats'].get('ObjBound'),
            native_lower_bound=result['stats'].get('native_lower_bound'), bound_scope=result['bound_scope'])
        if result['config_failure'] or result['fatal_contract']:
            report['config_failure'] = report['fatal_contract'] = True
        if result['native_calls'] == 0 and any(f.get('stage') in ('original_model', 'copy_contract', 'partial_start')
                and f.get('type') != 'TimeoutError' for f in result['failures']):
            report['config_failure'] = report['fatal_contract'] = True
        if result['policy'] != helper.POLICY or type(result['native_calls']) is not int or result['native_calls'] not in (0, 1):
            fatal('One-call helper result policy/count differs', identity=True)
        check()
        if report['fatal_contract']:
            raise ContractError('Native bootstrap/copy/start contract failed')
        stage = 'independent_retained_endpoint'
        retained = result['plan']
        retained_replay = nr.replay_native(case, retained)
        signature = shared._canonical(retained)
        if (retained.get('case_identity') != case.identity() or len(retained['vehicles']) != spec['fleet_N']
                or phase == 'target_qp' and signature != input_signature):
            fatal('Retained physical case/N/fixed-acquisition topology differs', identity=True)
        retained_bill = nh.rational(retained_replay['ops_cost'])+nh.supply(market, retained_replay['load'])
        if (retained_bill != Q(result['true_bill_exact']) or retained_bill > initial_bill
                or Q(result['fallback_bill_exact']) != initial_bill):
            fatal('Protected retained/fallback physical cost differs', identity=True)
        agreement = shared._agreement(result, nr.OBJECTIVE_TOL)
        report['numerical_agreement'] = agreement
        discrepancy = agreement.get('optimal_candidate_fallback_discrepancy', False)
        report['optimal_candidate_fallback_discrepancy'] = discrepancy
        if phase == 'target_qp':
            if result['selected_source'] == 'direct_qp' and not result['used_fallback']:
                if not candidate_flag or retained_bill != Q(result['candidate_bill_exact']):
                    fatal('Exposed acquisition candidate point differs', identity=True)
                report['candidate_path_verification'] = 'direct_candidate_comparison'
            elif candidate_flag and result['copy_contract'].get('passed') is True and not result['failures']:
                report['candidate_path_verification'] = 'source_guarded_unique_path_inference_not_caller_replay_of_C'
        else:
            report['candidate_path_verification'] = ('helper_full_graph_NR_replay_exact_N_guard; '
                'caller independently replays U, not any unreturned C')
            envelope = agreement.get('e_agree_exact')
            candidate = result.get('candidate_bill_exact')
            report['same_topology_improvement_discrepancy'] = bool(candidate_flag and envelope is not None
                and result['candidate_route_changed_from_prior'] is False and candidate is not None
                and initial_bill-Q(candidate) > Q(envelope))
            if report['same_topology_improvement_discrepancy']:
                report['qualification_discrepancies'].append('same_topology_improvement_beyond_source_agreement_screen')
        best_plan, best_replay, best_bill = retained, retained_replay, retained_bill
        best_brief = brief(retained, retained_replay)
        stats = result['stats']
        qualified = bool(success_flag and candidate_flag and result['copy_contract'].get('passed') is True
            and not result['failures'] and result['native_calls'] == result['native_call_attempts'] == 1
            and stats.get('threads') == 1 and stats.get('seed') == 17
            and agreement.get('source_guards_passed') is True and not discrepancy
            and not report['qualification_discrepancies'])
        if phase == 'target_qp':
            qualified = (qualified and stats.get('Status') == 2 and stats.get('native_optimal') is True
                and report['candidate_path_verification'] in (
                'direct_candidate_comparison', 'source_guarded_unique_path_inference_not_caller_replay_of_C')
            )
        report['cell_qualified'] = qualified
        report['acquisition_qualified'] = qualified if phase == 'target_qp' else False
        report['strict_method_success'] = qualified if phase == 'route_miqp' else False
        report['retained_route_changed_from_input'] = signature != input_signature
        check()
    except Exception as exc:
        report['failures'].append(dict(stage=stage, type=type(exc).__name__, message=str(exc)))
        report['acquisition_qualified'] = report['cell_qualified'] = report['strict_method_success'] = False
        if isinstance(exc, ContractError) or (not isinstance(exc, TimeoutError) and stage in (
                'launch_admission', 'spec_admission', 'paid_project_imports', 'input_physical_admission',
                'helper_load', 'independent_retained_endpoint')):
            report['config_failure'] = report['fatal_contract'] = True
    finally:
        if shared is not None and best_plan is not None and not report['fatal_contract']:
            try:
                check()
                shared._write(folder/'best-plan.json', best_plan)
                shared._write(folder/'brief-replay.json', best_brief)
                check()
                published = True
                gain = initial_bill-best_bill
                report.update(physical_witness_valid=True, retained_bill_exact=str(best_bill), true_bill_exact=str(best_bill),
                    selected_decomposition=best_brief, retained_increment_exact=str(gain),
                    increment_role='unchanged_to_charging' if phase == 'target_qp' else 'charged_common_to_routing',
                    increment_over_input_electricity_exact=str(gain/initial_electricity) if initial_electricity > 0 else None)
            except Exception as exc:
                report['failures'].append(dict(stage='durable_retained_output', type=type(exc).__name__, message=str(exc)))
                report['acquisition_qualified'] = report['cell_qualified'] = report['strict_method_success'] = False
        usage = resource.getrusage(resource.RUSAGE_SELF)
        now = time.monotonic()
        report.update(receipt_complete=True, stop_signal=stopped, event_counts=dict(event_counts),
            returned_monotonic=now, elapsed_s=now-anchor,
            method_endpoint_accepted=bool(published and stopped is None and now < end and not report['fatal_contract']),
            resources=dict(user_s=usage.ru_utime, system_s=usage.ru_stime, cpu_s=usage.ru_utime+usage.ru_stime,
                peak_rss_bytes=usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024,
                cpu_limit_s=90, rss_limit_bytes=MAX_RSS, python_threads=threading.active_count()))
        if not report['method_endpoint_accepted']:
            report['acquisition_qualified'] = report['cell_qualified'] = report['strict_method_success'] = False
        if shared is not None:
            shared._write(folder/'receipt.json', report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 2 if report['fatal_contract'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
