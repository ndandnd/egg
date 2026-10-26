"""DRAFT one-call synthetic duty/economic seam worker; no data-bank inputs."""
import time
START = time.monotonic()
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

POLICY = 'synthetic-duty-market-seam-worker-v1'
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
    'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')


class ContractError(ValueError):
    pass


def library(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ContractError('Declared source library missing')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ContractError('Source library path differs')
    return module


def write(path, value):
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def agreement(result, tolerance):
    stats, candidate = result['stats'], result.get('candidate_bill_exact')
    native = stats.get('ObjVal')
    if (candidate is None or type(native) not in (int, float) or not math.isfinite(native)
            or stats.get('raw_objective_exact') is None):
        return dict(available=False, source_guards_passed=False)
    raw, C, B = Q(stats['raw_objective_exact']), Q(candidate), Q(result['fallback_bill_exact'])
    rounded, native = float(raw), float(native)
    subtraction = rounded-native
    epsilon = Q(tolerance)
    residual = abs(raw-Q(rounded))+abs(Q(subtraction)-(Q(rounded)-Q(native)))
    envelope = 2*epsilon+residual
    return dict(available=True, source_guards_passed=abs(subtraction) <= tolerance and abs(C-raw) <= epsilon,
        e_agree_exact=str(envelope), objective_tol_binary_exact=str(epsilon),
        candidate_minus_raw_exact=str(C-raw), candidate_minus_native_point_exact=str(C-Q(native)),
        optimal_candidate_fallback_discrepancy=bool(stats.get('native_optimal') is True and C-B > envelope),
        interpretation='Unchanged source point agreement; no optimization-gap/equivalence guarantee')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', required=True, type=Path)
    parser.add_argument('--parent-anchor', required=True, type=float)
    parser.add_argument('--spec-sha256', required=True)
    args = parser.parse_args(argv)
    anchor = args.parent_anchor
    if (not args.worker.is_absolute() or not math.isfinite(anchor) or anchor > time.monotonic()
            or len(args.spec_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.spec_sha256)):
        raise ValueError('Require absolute folder, parent clock anchor and lowercase spec SHA256')
    folder, root = args.worker.resolve(), Path(__file__).resolve().parents[2]
    native_end, end = anchor+52., anchor+60.
    report = dict(policy=POLICY, receipt_complete=False, method_endpoint_accepted=False,
        acquisition_qualified=False, cell_qualified=False, strict_method_success=False,
        config_failure=False, fatal_contract=False, resource_violation=False, identity_failure=False,
        physical_witness_valid=False, failures=[], helper_failures=[], qualification_discrepancies=[],
        native_calls=None, native_call_attempts=None, candidate_bill_exact=None, fallback_bill_exact=None,
        retained_bill_exact=None, native_point=None, native_bound=None, native_start=None,
        qp_success=False, qp_candidate_admitted=False, miqp_success=False, miqp_candidate_admitted=False,
        fixed_duties_preserved=None, movement_path_changed=None, duty_assignment_changed=None,
        candidate_path_verification='unavailable', global_lower_bound=None, certificate_claim=False,
        parent_anchor=anchor, native_deadline=native_end, admission_deadline=end)
    stage, phase, stopped = 'launch_admission', None, None
    best_plan = best_replay = best_value = None
    adapter = None
    counts = Counter()
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
        raise TimeoutError('Seam worker signal '+str(signum))

    def check(deadline=end):
        if stopped is not None or time.monotonic() >= deadline:
            raise TimeoutError('Seam worker parent-anchored deadline/stop')
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024
        if rss > 5*1024**3 or usage.ru_utime+usage.ru_stime >= 90:
            fatal('Worker observed CPU/RSS ceiling', resource_failure=True)
        if threading.active_count() != 1 or any(os.environ.get(k) != '1' for k in THREAD_ENV):
            fatal('Worker thread contract differs', resource_failure=True)
        try:
            os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        fatal('Unexpected worker child process', resource_failure=True)

    def record(event):
        check()
        counts[str(event.get('event', 'unknown'))] += 1
        check()

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
            fatal('DRAFT/PENDING cannot import fixture or read worker spec')
        stage = 'spec_admission'
        raw = (folder/'spec.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != args.spec_sha256:
            fatal('Spec digest differs', identity=True)
        spec = json.loads(raw); del raw
        required = {'task_id', 'context_id', 'phase', 'input_plan'}
        if not required <= set(spec) or set(spec)-required-{'common_qualification'}:
            fatal('Spec field contract differs', identity=True)
        phase = spec['phase']
        report.update(task_id=spec['task_id'], context_id=spec['context_id'], phase=phase)
        adapter = library(Path(__file__).with_name('adapter.py'), 'duty_seam_source_bound_adapter')
        if (spec['context_id'] not in adapter.CONTEXT_IDS or phase not in adapter.PHASES
                or spec['task_id'] != adapter.task_id(spec['context_id'], phase)
                or (phase == 'target_qp') != (spec['input_plan'] is None)):
            fatal('Canonical task/context/phase/input differs', identity=True)
        stage = 'paid_imports_and_fixture'
        sys.path.insert(0, str(root/'src'))
        from egglab import native_recharge as nr, native_hull as nh, native_pathflow as pf
        for module, name in ((nr, 'native_recharge.py'), (nh, 'native_hull.py'), (pf, 'native_pathflow.py')):
            if Path(module.__file__).resolve() != root/'src/egglab'/name:
                fatal('Pure project import path differs', identity=True)
        case, reference, duties = adapter.make_fixture()
        context = next(c for c in adapter.contexts() if c['id'] == spec['context_id'])
        objective_id = adapter.objective_identity(context)
        replay_reference = nr.replay_native(case, reference)
        if len(reference['vehicles']) != 2 or adapter.duty_signature(reference) != tuple(sorted(duties)):
            fatal('Constructive reference exact-N/duties differ', identity=True)
        report.update(case_identity=case.identity(), objective_identity=objective_id, institution=context['institution'],
            fleet_N=2, unchanged_components=adapter.value(case, reference, replay_reference, context))
        prior = reference if phase == 'target_qp' else spec['input_plan']
        stage = 'input_physical_admission'
        prior_replay = replay_reference if phase == 'target_qp' else nr.replay_native(case, prior)
        prior_value = adapter.value(case, prior, prior_replay, context)
        if len(prior['vehicles']) != 2 or adapter.duty_signature(prior) != tuple(sorted(duties)):
            fatal('Common target input does not preserve exact-N/committed duties', identity=True)
        prior_hash = nr.digest(prior)
        if phase == 'target_qp':
            if spec.get('common_qualification') is not None:
                fatal('Target acquisition cannot claim predecessor qualification', identity=True)
        else:
            qualification = spec.get('common_qualification')
            expected = dict(target_qp_qualified=True, task_id=adapter.task_id(context['id'], 'target_qp'),
                context_id=context['id'], case_identity=case.identity(), objective_identity=objective_id,
                input_plan_sha256=prior_hash, retained_bill_exact=prior_value['total_exact'])
            if not isinstance(qualification, dict) or any(qualification.get(k) != v for k,v in expected.items()):
                fatal('Qualified common incumbent provenance differs', identity=True)
            report['common_qualification'] = qualification
        input_signature = adapter.canonical(prior)
        recovered, _ = pf.recover_paths(case, [mid for v in prior['vehicles'] for mid in v['movements']])
        if adapter.canonical({'vehicles': recovered}) != input_signature:
            fatal('Common path recovery differs', identity=True)
        best_plan, best_replay, best_value = prior, prior_replay, prior_value
        report.update(input_plan_sha256=prior_hash, fallback_bill_exact=prior_value['total_exact'],
            initial_components=prior_value)
        write(folder/'best-plan.json', best_plan)
        write(folder/'brief-replay.json', best_value)
        check()
        stage = 'helper_load'
        if phase == 'target_qp':
            helper = library(root/'research-20261025/warm_replication/qp_control.py', 'seam_frozen_qp')
            search_case, search_prior = case, prior
        else:
            helper = library(root/'research-20261026/economic_recourse_pilot/miqp_control.py', 'seam_frozen_miqp')
            if launch.get('mixed_integer_parameters') != helper.PARAMETERS:
                fatal('Frozen MIQP parameter commitment differs')
            search_case, search_prior = adapter.restrict_duties(case, prior, duties) if phase == 'fixed_duty' else (case, prior)
        report.update(search_case_identity=search_case.identity(), view_source_case_identity=case.identity(),
            search_scope='fixed-duty movement-subset view' if phase == 'fixed_duty' else 'original full declared graph')
        check(native_end)
        stage = 'one_native_'+phase
        arguments = (search_case, context['alpha'], context['beta'], search_prior, 17, native_end, end, check, record)
        result = helper.solve(*arguments) if phase == 'target_qp' else helper.solve(*arguments, fleet_N=2)
        candidate_flag = result['qp_candidate_admitted'] if phase == 'target_qp' else result['miqp_candidate_admitted']
        success_flag = result['qp_success'] if phase == 'target_qp' else result['miqp_success']
        report.update(native_calls=result['native_calls'], native_call_attempts=result['native_call_attempts'],
            candidate_bill_exact=result.get('candidate_bill_exact'), helper_retained_bill_exact=result.get('true_bill_exact'),
            helper_status=result['status'], helper_failures=result['failures'], stats=result['stats'],
            copy_contract=result['copy_contract'], selected_source=result['selected_source'], used_fallback=result['used_fallback'],
            native_point=result['stats'].get('ObjVal'), native_bound=result['stats'].get('ObjBound'),
            native_lower_bound=result['stats'].get('native_lower_bound'), helper_bound_scope=result['bound_scope'],
            bound_scope=result['bound_scope'],
            native_start=result.get('native_start'), candidate_movement_path_changed=result.get('candidate_route_changed_from_prior'))
        if phase == 'fixed_duty':
            report['bound_scope'] = 'Numerical fixed-duty movement-subset view with exact N only; not original full fixture graph'
            report['stats'] = dict(result['stats'])
            report['stats']['helper_lower_bound_scope'] = result['stats'].get('lower_bound_scope')
            report['stats']['lower_bound_scope'] = 'Raw numerical attribute for fixed-duty movement-subset exact-N view only; no original full-graph or physical certificate'
        if phase == 'target_qp':
            report.update(qp_success=success_flag, qp_candidate_admitted=candidate_flag)
        else:
            report.update(miqp_success=success_flag, miqp_candidate_admitted=candidate_flag)
        if result['config_failure'] or result['fatal_contract']:
            report['config_failure'] = report['fatal_contract'] = True
        if result['native_calls'] == 0 and any(f.get('stage') in ('original_model','copy_contract','partial_start')
                and f.get('type') != 'TimeoutError' for f in result['failures']):
            report['config_failure'] = report['fatal_contract'] = True
        if result['policy'] != helper.POLICY or type(result['native_calls']) is not int or result['native_calls'] not in (0,1):
            fatal('Frozen helper policy/one-call count differs', identity=True)
        check()
        if report['fatal_contract']:
            raise ContractError('Native bootstrap/copy/API contract failed')
        stage = 'independent_full_case_retained_replay'
        if result['plan'].get('case_identity') != search_case.identity():
            fatal('Helper retained identity differs before explicit restoration', identity=True)
        retained = adapter.restore_plan(result['plan'], case) if phase == 'fixed_duty' else result['plan']
        retained_replay = nr.replay_native(case, retained)
        retained_value = adapter.value(case, retained, retained_replay, context)
        signature = adapter.canonical(retained)
        if (retained.get('case_identity') != case.identity() or len(retained['vehicles']) != 2
                or phase in ('target_qp','fixed_duty') and adapter.duty_signature(retained) != tuple(sorted(duties))
                or phase == 'target_qp' and signature != input_signature):
            fatal('Retained case/exact-N/commitment differs', identity=True)
        U, B = Q(retained_value['total_exact']), Q(prior_value['total_exact'])
        if U != Q(result['true_bill_exact']) or Q(result['fallback_bill_exact']) != B or U > B:
            fatal('Original-lens protected retained cost differs', identity=True)
        screen = agreement(result, nr.OBJECTIVE_TOL)
        report['numerical_agreement'] = screen
        report['optimal_candidate_fallback_discrepancy'] = screen.get('optimal_candidate_fallback_discrepancy', False)
        envelope = screen.get('e_agree_exact')
        report['same_movement_path_improvement_discrepancy'] = bool(phase != 'target_qp' and candidate_flag
            and result.get('candidate_route_changed_from_prior') is False and envelope is not None
            and result.get('candidate_bill_exact') is not None and B-Q(result['candidate_bill_exact']) > Q(envelope))
        if report['same_movement_path_improvement_discrepancy']:
            report['qualification_discrepancies'].append('same_movement_path_improvement_beyond_source_agreement')
        if phase == 'target_qp' and candidate_flag and result['copy_contract'].get('passed') and not result['failures']:
            report['candidate_path_verification'] = ('direct_selected_candidate_comparison' if result['selected_source'] == 'direct_qp'
                and not result['used_fallback'] else 'source_guarded_unique_path_inference_not_caller_replay_of_C')
        elif candidate_flag:
            report['candidate_path_verification'] = 'frozen_helper_NR_replay_exact_N_view_ID_guard; caller_full_case_replays_U'
        best_plan, best_replay, best_value = retained, retained_replay, retained_value
        stats = result['stats']
        qualified = bool(success_flag and candidate_flag and result['copy_contract'].get('passed') is True
            and not result['failures'] and result['native_calls'] == result['native_call_attempts'] == 1
            and stats.get('threads') == 1 and stats.get('seed') == 17
            and screen.get('source_guards_passed') is True
            and not report['optimal_candidate_fallback_discrepancy'] and not report['qualification_discrepancies'])
        if phase == 'target_qp':
            qualified = qualified and stats.get('Status') == 2 and stats.get('native_optimal') is True
        report.update(cell_qualified=qualified, acquisition_qualified=qualified if phase == 'target_qp' else False,
            strict_method_success=qualified if phase != 'target_qp' else False,
            fixed_duties_preserved=adapter.duty_signature(retained) == tuple(sorted(duties)),
            movement_path_changed=signature != input_signature,
            duty_assignment_changed=adapter.duty_signature(retained) != adapter.duty_signature(prior))
        check()
    except Exception as exc:
        report['failures'].append(dict(stage=stage, type=type(exc).__name__, message=str(exc)))
        report['acquisition_qualified'] = report['cell_qualified'] = report['strict_method_success'] = False
        if isinstance(exc, ContractError) or (not isinstance(exc, TimeoutError) and stage in (
                'launch_admission','spec_admission','paid_imports_and_fixture','input_physical_admission',
                'helper_load','independent_full_case_retained_replay')):
            report['config_failure'] = report['fatal_contract'] = True
    finally:
        if best_plan is not None and not report['fatal_contract']:
            try:
                check()
                write(folder/'best-plan.json', best_plan)
                write(folder/'brief-replay.json', best_value)
                check()
                published = True
                report.update(physical_witness_valid=True, retained_bill_exact=best_value['total_exact'],
                    true_bill_exact=best_value['total_exact'], selected_decomposition=best_value,
                    retained_plan_sha256=nr.digest(best_plan))
                if report['movement_path_changed'] is None:
                    report.update(movement_path_changed=adapter.canonical(best_plan) != input_signature,
                        duty_assignment_changed=adapter.duty_signature(best_plan) != adapter.duty_signature(prior),
                        fixed_duties_preserved=adapter.duty_signature(best_plan) == tuple(sorted(duties)))
            except Exception as exc:
                report['failures'].append(dict(stage='durable_retained_output', type=type(exc).__name__, message=str(exc)))
                report['acquisition_qualified'] = report['cell_qualified'] = report['strict_method_success'] = False
        usage, now = resource.getrusage(resource.RUSAGE_SELF), time.monotonic()
        report.update(receipt_complete=True, stop_signal=stopped, returned_monotonic=now, elapsed_s=now-anchor,
            method_endpoint_accepted=bool(published and stopped is None and now < end and not report['fatal_contract']),
            event_counts=dict(counts), resources=dict(user_s=usage.ru_utime, system_s=usage.ru_stime,
                cpu_s=usage.ru_utime+usage.ru_stime,
                peak_rss_bytes=usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss*1024,
                cpu_limit_s=90, rss_limit_bytes=5*1024**3, python_threads=threading.active_count()))
        if not report['method_endpoint_accepted']:
            report['acquisition_qualified'] = report['cell_qualified'] = report['strict_method_success'] = False
        write(folder/'receipt.json', report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 2 if report['fatal_contract'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
