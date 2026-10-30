"""One exact compact view of the frozen finalizer; no new scientific metrics."""
import time
WALL0 = time.monotonic()
from decimal import Decimal
from fractions import Fraction
import json
import os
from pathlib import Path
import resource
import signal

BASE = Path(__file__).resolve().parent
TOP = ('finalization_complete', 'finalization_passed', 'scientific_qualification', 'scope',
    'learned_reporting_roles', 'failures', 'validation_errors', 'denominators', 'learned_continuation',
    'continuation_eligibility_checks', 'fatal_rows', 'invalid_admissions', 'campaign_complete',
    'campaign_passed', 'campaign_record_complete', 'campaign_failures', 'campaign_stop_signal',
    'campaign_unresolved_child_cpu_reserve_s', 'campaign_accounting_observations_complete',
    'pairwise_summaries', 'group_arm_summaries', 'fixed_route_QP_diagnostics',
    'baseline_capture_archival_complete', 'all_sixteen_baseline_captures_archived', 'caveats')
RESOURCES = ('campaign_resources', 'campaign_elapsed_s', 'finalization_cpu_s', 'finalization_wall_s',
    'finalization_rusage', 'finalization_budget', 'campaign_finalization', 'prior_closed_cumulative_cpu_s',
    'prior_closed_cumulative_elapsed_sum_s', 'prior_closed_QP_package_cpu_s',
    'prior_closed_QP_package_elapsed_sum_s', 'historical_totals_charged_to_new_budget',
    'cumulative_baseline_status', 'legacy_conditional_guard_s', 'legacy_actual_review_cpu',
    'legacy_reset', 'whole_session_exact_cpu_claim', 'timing_scope', 'resource_scope')
CELL = ('group', 'case', 'size', 'seed', 'arm', 'block', 'position', 'recorded', 'attempted',
    'method_endpoint_accepted', 'method_success', 'config_failure', 'cost_defined',
    'operational_endpoint_available', 'operational_selected_source', 'operational_uses_fallback',
    'late_or_timed_out', 'parent_elapsed_s', 'missing_reason', 'not_dispatched_reason', 'contract_failure',
    'execution_returncode', 'execution_reaped', 'execution_failures', 'worker_failures',
    'planner_status', 'planner_failures', 'qp_status', 'qp_success', 'qp_candidate_admitted', 'qp_failures',
    'admission_checks_passed', 'admission_rejected', 'worker_used_fallback', 'validation_failure',
    'cost_undefined_reason', 'finalizer_processed')


def pick(value, keys):
    return {key: value.get(key) for key in keys}


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
            default=lambda v: str(v) if isinstance(v, Decimal) else v)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def meter(path):
    with path.open() as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('External meter exceeds64KiB')
    fields = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[0] not in ('real', 'user', 'sys') or parts[0] in fields:
            raise ValueError('Incomplete or unexpected closed external meter: '+str(path))
        value = Decimal(parts[1])
        if not value.is_finite() or value < 0:
            raise ValueError('Invalid external meter value')
        fields[parts[0]] = value
    if set(fields) != {'real', 'user', 'sys'}:
        raise ValueError('External meter must be complete before outcomes are read')
    return dict(cpu_s=fields['user']+fields['sys'], elapsed_s=fields['real'], **fields)


def rounded(value):
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rounded(item) for item in value]
    if isinstance(value, str):
        try:
            return round(float(Fraction(value)), 9)
        except (ValueError, ZeroDivisionError, OverflowError):
            return value
    return round(value, 9) if isinstance(value, float) else value


def main():
    def expired(signum, frame):
        raise TimeoutError('View export body provision exhausted')
    resource.setrlimit(resource.RLIMIT_CPU, (8, 10))
    signal.signal(signal.SIGXCPU, expired); signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 18-(time.monotonic()-WALL0)))
    target = BASE/'RESULTS_VIEW.json'
    write_new(target, dict(export_complete=False, export_passed=False, failure='No completed export'))
    out, display = dict(export_complete=False, export_passed=False, export_failures=[]), {}
    try:
        main_time, final_time = meter(BASE/'process-time.txt'), meter(BASE/'finalize-time.txt')
        out['external_process_measurements'] = dict(campaign=main_time, finalizer=final_time)
        cpu, wall = main_time['cpu_s']+final_time['cpu_s'], main_time['elapsed_s']+final_time['elapsed_s']
        if cpu+10 > 28800 or wall+20 > 36000 or final_time['cpu_s']+10 > 600:
            raise ValueError('Existing campaign/closure budget cannot fund full10CPU/20wall export')
        with (BASE/'summary.json').open('rb') as stream:
            raw = stream.read(64*1024*1024+1)
        if len(raw) > 64*1024*1024:
            raise ValueError('Frozen compact summary exceeds64MiB')
        saved = json.loads(raw)
        out.update(pick(saved, TOP))
        out['resources'] = pick(saved, RESOURCES)
        out['strong_QP_control_qualification'] = pick(saved.get('strong_QP_control_qualification', {}),
            ('qualified', 'planned', 'assigned', 'qualified_cells', 'operational_contrasts_retained_on_failure', 'interpretation'))
        out['GNN_day_contrast'] = {key: value for key, value in saved.get('GNN_day_contrast', {}).items() if key != 'cells'}
        out['non_success_cells'] = [pick(row, CELL) for row in saved.get('cells', []) if row.get('method_success') is not True]
        pair_display = []
        for row in saved.get('pairwise_summaries', []):
            item = pick(row, ('learned', 'control', 'planned_pairs', 'defined_pairs', 'mean_d', 'positive_complete_group_medians'))
            item['groups'] = [pick(group, ('group', 'planned_pairs', 'defined_pairs', 'median_d')) for group in row.get('groups', [])]
            pair_display.append(item)
        display = rounded(dict(finalization=pick(saved, ('finalization_complete', 'finalization_passed', 'failures')),
            denominators=out['denominators'], learned_continuation=out['learned_continuation'],
            strong_QP_control_qualification=out['strong_QP_control_qualification'],
            pairwise_summaries=pair_display, GNN_day_contrast=out['GNN_day_contrast']))
        out.update(export_complete=True, export_passed=True)
    except BaseException as exc:
        out['export_failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN); signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 20-(time.monotonic()-WALL0)))
        cpu, wall = Decimal(str(time.process_time())), Decimal(str(time.monotonic()-WALL0))
        out['export_resource'] = dict(provision_cpu_s=10, provision_wall_s=20, body_cpu_s=8, body_wall_s=18,
            cpu_before_publication_s=cpu, elapsed_before_publication_s=wall,
            prior_closed_cumulative_cpu_s=Decimal('7064.41'), prior_closed_cumulative_elapsed_sum_s=Decimal('7239.65'),
            legacy_conditional_guard_s=Decimal('2546.091499549272'), legacy_actual_review_cpu='UNKNOWN',
            whole_session_exact_cpu_claim=False, external_export_meter_required_for_complete_cost=True,
            solver_calls=0, replay_calls=0, inference_calls=0, hash_calls=0, archive_calls=0)
        meters = out.get('external_process_measurements')
        if meters:
            m, f = meters['campaign'], meters['finalizer']
            out['export_resource'].update(campaign_package_cpu_before_publication_s=m['cpu_s']+f['cpu_s']+cpu,
                campaign_package_elapsed_sum_before_publication_s=m['elapsed_s']+f['elapsed_s']+wall,
                cumulative_cpu_before_export_s=Decimal('7064.41')+m['cpu_s']+f['cpu_s'],
                cumulative_elapsed_sum_before_export_s=Decimal('7239.65')+m['elapsed_s']+f['elapsed_s'],
                post_exit_reconciliation='Add external export user+sys/real once to the closed totals; do not add campaign_resources again')
        temporary = target.with_name(target.name+'.final.tmp')
        write_new(temporary, out); os.replace(temporary, target)
        print(json.dumps(display if out['export_passed'] else pick(out, ('export_complete', 'export_passed', 'export_failures')),
            allow_nan=False, separators=(',', ':')))
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['export_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
