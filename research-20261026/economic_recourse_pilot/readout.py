"""One closed-owner field projection; no project/solver imports or new study gate."""
import time
START = time.monotonic()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import threading
from fractions import Fraction as Q

HERE = Path(__file__).resolve().parent
POLICY = 'economic-recourse-closed-owner-compact-readout-v1'
BUDGETS = dict(total_cpu_s=30, total_wall_s=45, body_cpu_s=20, body_wall_s=30,
               publication_cpu_s=10, publication_wall_s=15)
EXPECTED = {10007: 20, 10013: 20, 10017: 28, 10021: 28}
COMPONENTS = ('replay_ok', 'fleet_count', 'vehicle_cost_exact', 'deadhead_minutes_exact',
    'deadhead_cost_exact', 'ops_cost_exact', 'ops_component_residual_exact',
    'linear_electricity_exact', 'quadratic_electricity_exact', 'electricity_exact',
    'total_exact', 'grid_kwh_exact', 'service_energy_exact', 'movement_energy_exact',
    'consumption_kwh_exact', 'ideal_grid_demand_exact', 'replay_grid_minus_ideal_exact',
    'max_grid_kw', 'units')
WORKER = ('receipt_complete', 'method_endpoint_accepted', 'acquisition_qualified',
    'cell_qualified', 'strict_method_success', 'config_failure', 'fatal_contract',
    'resource_violation', 'identity_failure', 'physical_witness_valid', 'failures',
    'helper_failures', 'qualification_discrepancies', 'native_calls', 'native_call_attempts',
    'qp_success', 'qp_candidate_admitted', 'miqp_success', 'miqp_candidate_admitted',
    'candidate_bill_exact', 'fallback_bill_exact', 'retained_bill_exact', 'helper_true_bill_exact',
    'native_point', 'native_bound', 'native_lower_bound', 'bound_scope', 'native_start',
    'candidate_path_verification', 'candidate_route_changed_from_input',
    'retained_route_changed_from_input', 'same_topology_improvement_discrepancy',
    'optimal_candidate_fallback_discrepancy', 'numerical_agreement', 'copy_contract',
    'helper_status', 'selected_source', 'used_fallback', 'stats', 'resources',
    'parent_anchor', 'native_deadline', 'admission_deadline', 'returned_monotonic',
    'elapsed_s', 'stop_signal')
EXTERNAL = ('task_id', 'attempted', 'unattempted_reason', 'parent_endpoint_accepted',
    'target_common_qualified', 'full_method_success', 'config_failure', 'fatal_contract',
    'resource_violation', 'identity_failure', 'failures', 'timed_out', 'reaped',
    'returncode', 'method_late', 'parent_elapsed_s', 'process_return_elapsed_s',
    'waited_child_cpu_s', 'parent_cpu_s', 'cpu_observation_complete',
    'unresolved_cpu_reserve_s')


def pick(obj, keys):
    return {key: obj.get(key) for key in keys}


def number(value):
    if value is None:
        return None
    result = float(Q(value))
    if not math.isfinite(result):
        raise ValueError('Nonfinite exact-value display')
    return result


def exact(value):
    return None if value is None else str(Q(value))


def component(obj):
    if obj is None:
        return None
    result = pick(obj, COMPONENTS)
    result['decimal'] = {key: number(value) for key, value in result.items() if key.endswith('_exact')}
    return result


def component_deltas(common, operation):
    result = {}
    for key in ('grid_kwh_exact', 'linear_electricity_exact', 'quadratic_electricity_exact', 'ops_cost_exact'):
        value = (None if common is None or operation is None or common.get(key) is None
            or operation.get(key) is None else Q(common[key])-Q(operation[key]))
        result[key] = exact(value)
        result[key+'_decimal'] = number(value)
    return result


def main():
    stopped, publication = None, False
    publication_start = publication_cpu = None
    report = dict(policy=POLICY, passed=False, validation_failures=[], contexts=[],
        input_sha256=None, source_sha256={}, statistical_claim=False,
        available_only_mean=None, promotion_rule=None)

    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        raise TimeoutError('Readout stop signal '+str(signum))

    def check():
        use = resource.getrusage(resource.RUSAGE_SELF)
        cpu = use.ru_utime+use.ru_stime
        rss = use.ru_maxrss if os.uname().sysname == 'Darwin' else use.ru_maxrss*1024
        if (stopped is not None or cpu >= (30 if publication else 20)
                or time.monotonic()-START >= (45 if publication else 30)
                or publication and (cpu-publication_cpu >= 10 or time.monotonic()-publication_start >= 15)
                or rss > 5*1024**3 or threading.active_count() != 1):
            raise RuntimeError('Readout CPU/wall/RSS/thread boundary')
        try:
            os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        raise RuntimeError('Unexpected readout child')

    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGXCPU):
        signal.signal(sig, stop)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 45-(time.monotonic()-START)))
    check()
    gate_raw = (HERE/'READOUT_LAUNCH.json').read_bytes()
    gate = json.loads(gate_raw)
    expected_input = dict(path=str(HERE/'attempt01/receipt.json'), owner_source_commit='b44d08eb',
                          managed_session=72484, state='CLOSED', exit_code=0)
    source_version = gate.get('source_version') or {}
    revision = source_version.get('git_revision')
    if (gate.get('mode') != 'FROZEN' or gate.get('review_disposition') != 'PASS'
            or gate.get('policy') != POLICY or gate.get('budgets') != BUDGETS
            or gate.get('input_version') != expected_input
            or set(source_version) != {'git_revision', 'assumption'}
            or source_version.get('assumption') != 'parent-approved-frozen-commit'
            or not isinstance(revision, str) or len(revision) != 40
            or any(c not in '0123456789abcdef' for c in revision)):
        raise SystemExit('DRAFT/PENDING readout cannot open owner input')
    report.update(input_version=expected_input, source_version=source_version)
    report['launch_sha256'] = hashlib.sha256(gate_raw).hexdigest()
    for name in ('readout.py', 'READOUT_NOTE.md'):
        check()
        actual = hashlib.sha256((HERE/name).read_bytes()).hexdigest()
        report['source_sha256'][name] = actual
        expected = (gate.get('source_sha256') or {}).get(name)
        if expected is not None and actual != expected:
            raise SystemExit('Readout source pin differs before input')
    output = HERE/'readout01'
    output.mkdir(exist_ok=False)
    try:
        path = HERE/'attempt01/receipt.json'
        if path.stat().st_size > 64*1024**2:
            raise ValueError('Owner receipt exceeds compact-input cap')
        raw = path.read_bytes(); check()
        report['input_sha256'] = hashlib.sha256(raw).hexdigest()
        if gate.get('input_sha256') is not None and report['input_sha256'] != gate['input_sha256']:
            raise ValueError('Closed owner receipt pin differs')
        owner = json.loads(raw); del raw
        report['owner_flags'] = pick(owner, ('policy', 'receipt_complete', 'passed', 'passed_scope',
            'accounting_complete', 'ledger_complete', 'config_failure', 'failures', 'stop_signal',
            'unresolved_cpu_reserve_s', 'historical_scope', 'elapsed_before_publication_s'))
        report['owner_resources'] = owner.get('resources')
        report['owner_input_pins'] = owner.get('input_sha256')
        report['groups'] = owner.get('groups')
        report['stored_summary'] = owner.get('summary')
        if not (owner.get('receipt_complete') is True and owner.get('accounting_complete') is True
                and owner.get('ledger_complete') is True and owner.get('unresolved_cpu_reserve_s') == 0):
            report['validation_failures'].append('Owner accounting/planned-ledger closure incomplete')
        rows = owner['contexts']
        if len(rows) != 8 or len({r['context_id'] for r in rows}) != 8:
            raise ValueError('Expected all eight distinct planned context rows')
        expected_groups = {(f'physical_v2_s{base}', base, services) for base, services in EXPECTED.items()}
        if (len(owner.get('groups') or []) != 4 or
                {(g['group'], g['base_id'], g['services']) for g in owner['groups']} != expected_groups):
            report['validation_failures'].append('Fixed four base/service profiles differ')
        for group, base, services in expected_groups:
            members = [r for r in rows if r.get('group') == group]
            if (len(members) != 2 or {r.get('target_source') for r in members} != {'source0', 'source1'}
                    or any(r.get('base_id') != base or r.get('services') != services for r in members)):
                report['validation_failures'].append('Fixed group lacks both distinct matching targets: '+group)
        workers = []
        for source in rows:
            check()
            row = pick(source, ('context_id', 'group', 'base_id', 'services', 'target_source',
                'common_incumbent_qualified', 'economic_comparison_defined', 'operational_source',
                'negative_retained_gain', 'pipeline_elapsed_s', 'pipeline_scope',
                'same_topology_improvement_discrepancy', 'optimal_candidate_fallback_discrepancy',
                'qualification_discrepancies'))
            for label in ('unchanged', 'common', 'operational'):
                row[label+'_components'] = component(source.get(label+'_components'))
            for key in ('charging_to_routing_gain_exact', 'unchanged_to_target_charging_gain_exact',
                        'charging_to_routing_over_target_common_electricity',
                        'target_common_electricity_denominator_exact'):
                row[key] = exact(source.get(key)); row[key+'_decimal'] = number(source.get(key))
            ratio = source.get('charging_to_routing_over_target_common_electricity')
            row['routing_gain_percent_of_target_common_electricity'] = None if ratio is None else 100*number(ratio)
            for phase in ('target_qp', 'route_miqp'):
                external = source[phase]; worker = external.get('worker') or {}
                row[phase] = pick(external, EXTERNAL)
                row[phase]['worker'] = pick(worker, WORKER)
                workers.append((phase, external, worker))
            envelope = (row['route_miqp']['worker'].get('numerical_agreement') or {}).get('e_agree_exact')
            gain = row['charging_to_routing_gain_exact']
            row['routing_gain_within_source_point_screen'] = (None if gain is None or envelope is None
                else abs(Q(gain)) <= Q(envelope))
            row['routing_component_deltas_common_minus_operational'] = component_deltas(
                row['common_components'], row['operational_components'])
            native = row['route_miqp']['worker']
            native_stats = native.get('stats') or {}
            row['scalar_display'] = dict(native_status=native_stats.get('Status'),
                native_optimal=native_stats.get('native_optimal'), raw_MIPGap=native_stats.get('MIPGap'),
                retained_route_changed=native.get('retained_route_changed_from_input'),
                candidate_route_changed=native.get('candidate_route_changed_from_input'),
                start_processing=(native.get('native_start') or {}).get('processing'),
                qp_parent_elapsed_s=row['target_qp'].get('parent_elapsed_s'),
                miqp_parent_elapsed_s=row['route_miqp'].get('parent_elapsed_s'),
                full_pipeline_elapsed_s=row.get('pipeline_elapsed_s'),
                common_grid_kwh=number((row['common_components'] or {}).get('grid_kwh_exact')),
                operational_grid_kwh=number((row['operational_components'] or {}).get('grid_kwh_exact')),
                component_delta_decimals={key: value for key, value in
                    row['routing_component_deltas_common_minus_operational'].items() if key.endswith('_decimal')})
            report['contexts'].append(row)
        summary = owner['summary']
        for field, source_field in (
                ('complete_eight_context_mean_gain_exact', 'charging_to_routing_gain_exact'),
                ('complete_eight_context_mean_normalized_gain', 'charging_to_routing_over_target_common_electricity')):
            values = [r[source_field] for r in report['contexts']]
            derived = sum((Q(v) for v in values), Q(0))/8 if all(v is not None for v in values) else None
            report[field] = exact(derived); report[field+'_decimal'] = number(derived)
            if exact(derived) != exact(summary.get(field)):
                report['validation_failures'].append('Derived eight-context mean differs: '+field)
        normalized_mean = report['complete_eight_context_mean_normalized_gain']
        report['complete_eight_context_mean_percent_of_target_common_electricity'] = (
            None if normalized_mean is None else 100*number(normalized_mean))
        charging = [r['unchanged_to_target_charging_gain_exact'] for r in report['contexts']]
        charging_mean = sum((Q(v) for v in charging), Q(0))/8 if all(v is not None for v in charging) else None
        report['complete_eight_context_mean_unchanged_to_target_QP_gain_exact'] = exact(charging_mean)
        report['complete_eight_context_mean_unchanged_to_target_QP_gain_decimal'] = number(charging_mean)
        report['group_means'] = []
        for group in owner['groups']:
            members = [r for r in report['contexts'] if r['group'] == group['group']]
            values = [r['charging_to_routing_gain_exact'] for r in members]
            mean = sum((Q(v) for v in values), Q(0))/2 if len(values) == 2 and all(v is not None for v in values) else None
            stored = next((r for r in summary['group_summaries'] if r['group'] == group['group']), None)
            report['group_means'].append(dict(group=group['group'], planned_targets=2,
                defined_targets=sum(v is not None for v in values), mean_exact=exact(mean), mean_decimal=number(mean)))
            if stored is None or exact(mean) != exact(stored.get('complete_two_target_mean_gain_exact')):
                report['validation_failures'].append('Derived two-target mean differs: '+group['group'])
        report['counts'] = dict(planned_groups=4, planned_contexts=8, planned_workers=16,
            recorded_contexts=len(rows), recorded_workers=len(workers),
            qualified_target_priors=sum(e.get('target_common_qualified') is True for p,e,w in workers if p == 'target_qp'),
            strict_miqp_deliveries=sum(e.get('full_method_success') is True for p,e,w in workers if p == 'route_miqp'),
            attempted=sum(e.get('attempted') is True for p,e,w in workers),
            missing=sum(e.get('attempted') is not True for p,e,w in workers),
            failed_delivery=sum(e.get('attempted') is True and e.get('parent_endpoint_accepted') is not True for p,e,w in workers),
            timely_operational_endpoints=sum(e.get('parent_endpoint_accepted') is True and e.get('method_late') is False for p,e,w in workers),
            native_calls=sum(w['native_calls'] for p,e,w in workers if type(w.get('native_calls')) is int),
            native_count_unknown=sum(type(w.get('native_calls')) is not int for p,e,w in workers),
            native_optimal_miqp=sum((w.get('stats') or {}).get('native_optimal') is True for p,e,w in workers if p == 'route_miqp'),
            max_worker_peak_rss_bytes=max(((w.get('resources') or {}).get('peak_rss_bytes')
                for p,e,w in workers if type((w.get('resources') or {}).get('peak_rss_bytes')) in (int, float)), default=None),
            failure_records=sum(len(e.get('failures') or [])+len(w.get('failures') or [])+len(w.get('helper_failures') or []) for p,e,w in workers),
            qualification_discrepancies=summary.get('qualification_discrepancy_contexts'))
    except Exception as exc:
        report['validation_failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    try:
        check()
    except Exception as exc:
        report['validation_failures'].append(dict(stage='body_boundary', type=type(exc).__name__, message=str(exc)))
    publication_start = time.monotonic()
    use = resource.getrusage(resource.RUSAGE_SELF)
    publication_cpu = use.ru_utime+use.ru_stime
    publication = True
    try:
        check()
    except Exception as exc:
        report['validation_failures'].append(dict(stage='publication_boundary', type=type(exc).__name__, message=str(exc)))
    use = resource.getrusage(resource.RUSAGE_SELF)
    report.update(passed=not report['validation_failures'], resources=dict(cpu_s=use.ru_utime+use.ru_stime,
        elapsed_s=time.monotonic()-START, peak_rss_bytes=use.ru_maxrss if os.uname().sysname == 'Darwin' else use.ru_maxrss*1024,
        rss_convention='macOS ru_maxrss bytes; elsewhere KiB converted to bytes', prepublication_only=True),
        interpretation='Operational paid-pipeline increments; point-agreement screens are not optimization gaps, zeroing or equivalence')
    with (output/'READOUT.json').open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps(dict(passed=report['passed'], counts=report.get('counts'),
        rows=[dict(pick(r, ('context_id', 'group', 'target_source', 'charging_to_routing_gain_exact',
            'charging_to_routing_gain_exact_decimal', 'routing_gain_percent_of_target_common_electricity',
            'routing_gain_within_source_point_screen', 'scalar_display')),
            absolute_costs={name: number((r.get(name+'_components') or {}).get('total_exact'))
                for name in ('unchanged', 'common', 'operational')}) for r in report['contexts']],
        full_eight_mean=report.get('complete_eight_context_mean_gain_exact_decimal'),
        full_eight_normalized_mean_percent=report.get('complete_eight_context_mean_percent_of_target_common_electricity'),
        full_eight_unchanged_to_QP_mean=report.get('complete_eight_context_mean_unchanged_to_target_QP_gain_decimal')), allow_nan=False), flush=True)
    check()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
