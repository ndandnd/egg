"""Once-only compact fixed-route QP readout; no project imports or numerical solve."""
import time

WALL0, CPU0 = time.monotonic(), time.process_time()

from collections import Counter
from decimal import Decimal
from fractions import Fraction as Q
import json
from pathlib import Path
import resource
import signal
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
CASES = tuple(f'scale:{base}:{size}' for base in range(50600, 50604) for size in (40, 80))
SEEDS = (17, 41, 73)
STATS = ('Status', 'SolCount', 'ObjVal', 'ObjBound', 'Runtime', 'Work', 'IterCount',
    'BarIterCount', 'MaxVio', 'ConstrVio', 'BoundVio', 'DualVio', 'ComplVio',
    'ConstrResidual', 'DualResidual', 'native_optimal', 'native_lower_bound',
    'lower_bound_scope', 'wall_s', 'cpu_s', 'native_overrun_s', 'solver', 'package_version',
    'native_version', 'threads', 'seed', 'FeasibilityTol', 'OptimalityTol', 'BarConvTol',
    'TimeLimit', 'raw_objective_exact', 'replay_objective_exact',
    'raw_to_physical_cost_delta_exact', 'native_to_physical_cost_delta')


def check():
    if time.process_time()-CPU0 >= 55 or time.monotonic()-WALL0 >= 85:
        raise TimeoutError('Analysis body provision exhausted')


def load(path, cap=64*1024*1024):
    check()
    with Path(path).open('rb') as stream:
        raw = stream.read(cap+1)
    if len(raw) > cap:
        raise ValueError('Compact input exceeds declared byte bound: '+str(path))
    return json.loads(raw)


def process_time(path):
    with Path(path).open() as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('External process-time file exceeds64KiB')
    values = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[0] not in ('real', 'user', 'sys') or parts[0] in values:
            raise ValueError('Unexpected external process-time format: '+str(path))
        value = Decimal(parts[1])
        if not value.is_finite() or value < 0:
            raise ValueError('Invalid external process-time value')
        values[parts[0]] = value
    if set(values) != {'real', 'user', 'sys'}:
        raise ValueError('Incomplete external process-time file')
    return dict(cpu_s=values['user']+values['sys'], elapsed_s=values['real'], **values)


def median(values):
    values = sorted(values)
    n = len(values)
    return None if not n else values[n//2] if n % 2 else (values[n//2-1]+values[n//2])/2


def describe(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    groups = []
    for group in range(50600, 50604):
        cells = [row[field] for row in rows if row['group'] == group and row[field] is not None]
        groups.append(dict(group=group, planned=6, defined=len(cells),
            median=median(cells) if len(cells) == 6 else None))
    return dict(planned=24, defined=len(values), missing=24-len(values),
        mean=sum(values, Q(0))/24 if len(values) == 24 else None,
        median=median(values) if len(values) == 24 else None,
        positive=sum(v > 0 for v in values), zero=sum(v == 0 for v in values),
        negative=sum(v < 0 for v in values), groups=groups,
        independent_base_units=4, repeated_sizes_and_seeds_not_independent=True)


def main():
    def expired(signum, frame):
        raise TimeoutError('Analysis resource provision exhausted')
    resource.setrlimit(resource.RLIMIT_CPU, (55, 60))
    signal.signal(signal.SIGXCPU, expired)
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 85-(time.monotonic()-WALL0)))
    out = dict(complete=False, analysis_passed=False, scientific_qualification=False,
        cells=[dict(case=case, processed=False) for case in CASES], comparisons=[],
        failures=[], validation_errors=[], provision=dict(cpu_s=60, wall_s=90, inside_shared_package=True))
    try:
        v1, v2 = process_time(BASE/'process-time.txt'), process_time(BASE/'process-time-v2.txt')
        out['external_process_measurements'] = dict(attempt01=v1, attempt02=v2,
            nonrefundable_attempt01_cpu_charge=Decimal('.72'), nonrefundable_attempt01_elapsed_charge=Decimal('.92'))
        if v1['cpu_s'] != Decimal('.72') or v1['elapsed_s'] != Decimal('.92'):
            raise ValueError('Actual v1 external meter differs from carried charge; preserve discrepancy')
        if v1['cpu_s']+v2['cpu_s']+60 > 1800 or v1['elapsed_s']+v2['elapsed_s']+90 > 2700:
            raise ValueError('Shared QP package cannot fund full analysis provision')
        master = load(BASE/'attempt02/receipt.json')
        warm = load(ROOT/'research-20261025/warm_replanning/summary.json')
        if warm.get('finalization_passed') is not True:
            raise ValueError('Original warm compact summary did not pass')
        priors = {r['case']: r for r in warm['acquisitions']}
        old = {(r['case'], r['seed'], r['arm']): r for r in warm['cells']
            if r['arm'] in ('GNN', 'fixed_route')}
        expected_old = {(case, seed, arm) for case in CASES for seed in SEEDS for arm in ('GNN', 'fixed_route')}
        if set(priors) != set(CASES) or set(old) != expected_old or len(old) != 48:
            raise ValueError('Original warm comparison denominator differs from eight cases/three seeds')
        records = master['cases']
        if len(records) != 8 or {r['case'] for r in records} != set(CASES):
            raise ValueError('QP master does not preserve exactly all eight assigned cases')
        indexed = {r['case']: r for r in records}
        out['campaign'] = {k: master.get(k) for k in ('complete', 'passed', 'stopped', 'failures',
            'resources', 'elapsed_s', 'attempted', 'admitted', 'qp_success', 'accounting_complete',
            'unresolved_cpu_reserve_s', 'charged_package_cpu_s', 'charged_package_elapsed_sum_s')}
        for ordinal, case in enumerate(CASES, 1):
            check()
            prior = priors[case]
            if prior.get('valid_prior') is not True:
                raise ValueError('Original common prior unavailable: '+case)
            prior_cost, e0 = Q(prior['target_decomposition']['total_exact']), Q(prior['target_E0'])
            if e0 <= 0:
                raise ValueError('Nonpositive E0 has no defined normalized comparison')
            record, helper = indexed[case], {}
            worker = record.get('worker', {})
            endpoint = record.get('method_endpoint_accepted') is True
            valid_endpoint = endpoint
            selected = Q(worker['objective_exact']) if endpoint else prior_cost
            row = dict(case=case, group=int(case.split(':')[1]), size=int(case.split(':')[2]), processed=True,
                attempted=record.get('attempted') is True, endpoint_accepted=endpoint,
                method_success=worker.get('method_success') is True, qp_success=worker.get('qp_success') is True,
                physical_witness_valid=worker.get('physical_witness_valid') is True,
                config_failure=record.get('config_failure'), identity_failure=record.get('identity_failure'),
                resource_violation=record.get('resource_violation'), native_calls=worker.get('native_calls'),
                native_call_attempts=worker.get('native_call_attempts'), parent_elapsed_s=record.get('parent_elapsed_s'),
                timed_out=record.get('timed_out'), reaped=record.get('reaped'), returncode=record.get('returncode'),
                not_dispatched_reason=record.get('not_dispatched_reason'),
                execution_failures=record.get('failures', []), worker_failures=worker.get('failures', []),
                helper_failures=worker.get('helper_failures', []), worker_resources=worker.get('resources'),
                prior_cost_exact=prior_cost, E0_exact=e0, operational_selected_cost_exact=selected,
                operational_source=worker.get('selected_source') if endpoint else 'preexisting_prior',
                worker_selected_cost_exact=worker.get('objective_exact'),
                prior_grid_kwh_exact=Q(prior['target_decomposition']['grid_kwh_exact']),
                selected_saving_from_prior_over_E0=(prior_cost-selected)/e0)
            out['cells'][ordinal-1] = row
            if endpoint and (worker.get('physical_witness_valid') is not True or selected > prior_cost
                    or worker.get('case_identity') != old[(case, 17, 'GNN')]['selection_contract']['case_identity']):
                out['validation_errors'].append(dict(case=case, error='Invalid admitted QP operational endpoint'))
                valid_endpoint = False
                selected = prior_cost
                row.update(operational_selected_cost_exact=selected, operational_source='preexisting_prior',
                    selected_saving_from_prior_over_E0=Q(0))
            folder = BASE/'attempt02'/('%03d-qp-%s' % (ordinal, case.replace(':', '-')))
            folder_valid = not record.get('folder') or Path(record['folder']).resolve() == folder
            if not folder_valid:
                out['validation_errors'].append(dict(case=case, error='QP case folder differs from frozen assignment'))
            packet = folder/'qp-result.json'
            if folder_valid and packet.exists():
                try:
                    helper = load(packet, 4*1024*1024)
                except (ValueError, OSError) as exc:
                    out['validation_errors'].append(dict(case=case, artifact='qp-result.json', error=str(exc)))
            copy = helper.get('copy_contract', worker.get('copy_contract', {}))
            row.update(helper_packet_present=bool(helper), helper_status=helper.get('status'),
                helper_qp_success=helper.get('qp_success'), helper_candidate_admitted=helper.get('qp_candidate_admitted'),
                helper_selected_cost_exact=helper.get('true_bill_exact'),
                helper_packet_failures=helper.get('failures', []), fatal_contract=helper.get('fatal_contract'),
                copy_contract=copy, native_stats={k: helper.get('stats', {}).get(k) for k in STATS},
                infinity_examples=copy.get('infinite_bound_examples', [])[:5],
                operational_admission_valid=valid_endpoint)
            candidate = None
            try:
                if (helper.get('qp_candidate_admitted') is True
                        and helper.get('candidate_bill_exact') is not None):
                    candidate = Q(helper['candidate_bill_exact'])
            except (ValueError, TypeError, ZeroDivisionError) as exc:
                out['validation_errors'].append(dict(case=case, field='candidate_bill_exact', error=str(exc)))
            row.update(candidate_cost_exact=candidate,
                reported_candidate_bill_exact_telemetry=helper.get('candidate_bill_exact'),
                candidate_physical_helper_admitted=helper.get('qp_candidate_admitted') is True,
                candidate_timely_operational_eligible=valid_endpoint and helper.get('qp_candidate_admitted') is True,
                candidate_saving_from_prior_over_E0=None if candidate is None else (prior_cost-candidate)/e0,
                replay_objective_consistency_delta_exact=helper.get('stats', {}).get('raw_to_physical_cost_delta_exact'))
            retained_prior = row['operational_source'] in ('preexisting_prior', 'retained_prior')
            energy = row['prior_grid_kwh_exact'] if retained_prior else None
            row['selected_replay_summary_read'] = False
            replay_path = folder/'selected-replay.json'
            if valid_endpoint and not retained_prior and folder_valid and replay_path.exists():
                try:
                    compact_replay = load(replay_path, 4*1024*1024)
                    energy = sum((Q(x) for x in compact_replay['load']), Q(0))
                    row['selected_replay_summary_read'] = True
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    row['energy_missing_reason'] = str(exc)
            row.update(operational_selected_grid_kwh_exact=energy,
                selected_energy_change_from_prior_kwh_exact=None if energy is None else energy-row['prior_grid_kwh_exact'])
            if energy is None:
                row.setdefault('energy_missing_reason', 'Selected compact replay load unavailable; no broader artifact reads')
            for seed in SEEDS:
                capped, gnn = old[(case, seed, 'fixed_route')], old[(case, seed, 'GNN')]
                if not capped['cost_defined'] or not gnn['cost_defined']:
                    raise ValueError('Original fixed denominator contains undefined operational cost')
                c, g = Q(capped['operational_cost']), Q(gnn['operational_cost'])
                out['comparisons'].append(dict(case=case, group=row['group'], size=row['size'], seed=seed,
                    capped_fixed_route_cost_exact=c, GNN_cost_exact=g,
                    GNN_grid_kwh_exact=gnn['operational_decomposition'].get('grid_kwh_exact'),
                    prior_grid_kwh_exact=row['prior_grid_kwh_exact'], selected_QP_grid_kwh_exact=energy,
                    old_GNN_advantage_over_capped_over_E0=(c-g)/e0,
                    selected_QP_gain_over_capped_over_E0=(c-selected)/e0,
                    GNN_advantage_over_selected_QP_over_E0=(selected-g)/e0,
                    candidate_QP_gain_over_capped_over_E0=None if candidate is None else (c-candidate)/e0,
                    GNN_advantage_over_candidate_QP_over_E0=None if candidate is None else (candidate-g)/e0))
        fields = ('old_GNN_advantage_over_capped_over_E0', 'selected_QP_gain_over_capped_over_E0',
            'GNN_advantage_over_selected_QP_over_E0', 'candidate_QP_gain_over_capped_over_E0',
            'GNN_advantage_over_candidate_QP_over_E0')
        out['comparison_summaries'] = {field: describe(out['comparisons'], field) for field in fields}
        out['denominators'] = dict(assigned=8, processed=sum(r['processed'] for r in out['cells']),
            attempted=sum(r.get('attempted', False) for r in out['cells']),
            endpoint_accepted=sum(r.get('endpoint_accepted', False) for r in out['cells']),
            qp_success=sum(r.get('endpoint_accepted') and r.get('qp_success') for r in out['cells']),
            copy_contract_passed=sum(r.get('copy_contract', {}).get('passed') is True for r in out['cells']),
            reported_native_optimal=sum(r.get('native_stats', {}).get('native_optimal') is True for r in out['cells']),
            physical_QP_candidate_admitted=sum(r.get('candidate_physical_helper_admitted', False) for r in out['cells']),
            parent_timely_QP_candidate_eligible=sum(r.get('candidate_timely_operational_eligible', False) for r in out['cells']),
            operational_physical_witness=sum(r.get('operational_admission_valid', False) for r in out['cells']),
            known_native_calls=sum(r.get('native_calls') for r in out['cells'] if type(r.get('native_calls')) is int),
            unknown_native_call_counts=sum(r.get('native_calls') is None for r in out['cells']),
            provisional_physical_candidate=sum(r.get('candidate_physical_helper_admitted')
                and r.get('helper_qp_success') is False for r in out['cells']),
            provisional_parent_timely_candidate=sum(r.get('candidate_timely_operational_eligible')
                and r.get('helper_qp_success') is False for r in out['cells']),
            native_status_counts=dict(Counter(str(r.get('native_stats', {}).get('Status')) for r in out['cells'])),
            repeated_old_seed_comparisons=len(out['comparisons']), independent_base_units=4)
        out.update(complete=True, analysis_passed=not out['validation_errors'])
    except BaseException as exc:
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 90-(time.monotonic()-WALL0)))
        cpu, wall = Decimal(str(time.process_time())), Decimal(str(time.monotonic()-WALL0))
        out.update(analysis_cpu_s_before_publication=cpu, analysis_wall_s_before_publication=wall,
            analysis_peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            analysis_platform=sys.platform,
            raw_captures_read=0, plan_reads=0, replay_calls=0, solver_calls=0, inference_calls=0, hash_calls=0,
            selected_replay_summary_reads=sum(r.get('selected_replay_summary_read', False) for r in out['cells']),
            caveats=['Same four exposed base groups; sizes nested and resources scaled; no new generalization evidence',
                'QP seed17 witness reused against three old solver seeds; these are repeated comparisons',
                'Numerical status and raw dual bounds are conditional reports, not full-problem certificates',
                'Candidate-only costs may be provisional or late; operational comparisons use parent-admitted selection or prior',
                'Energy differences flag demand change; they do not causally identify charging timing',
                'Different backend/procedure: no speedup claim; all prior failed work remains charged'])
        meters = out.get('external_process_measurements')
        if meters:
            one, two = meters['attempt01'], meters['attempt02']
            out['resource_reconciliation'] = dict(closed_before_v2_cpu_s=Decimal('7005.07'),
                closed_before_v2_elapsed_sum_s=Decimal('7178.14'),
                corrected_cumulative_cpu_before_analysis_s=Decimal('7005.07')+two['cpu_s'],
                corrected_cumulative_elapsed_before_analysis_s=Decimal('7178.14')+two['elapsed_s'],
                corrected_cumulative_cpu_through_analysis_prepublication_s=Decimal('7005.07')+two['cpu_s']+cpu,
                corrected_cumulative_elapsed_through_analysis_prepublication_s=Decimal('7178.14')+two['elapsed_s']+wall,
                shared_QP_package_cpu_prepublication_s=one['cpu_s']+two['cpu_s']+cpu,
                shared_QP_package_elapsed_sum_prepublication_s=one['elapsed_s']+two['elapsed_s']+wall,
                historical_guard_s=Decimal('2546.091499549272'), historical_actual_review_cpu='UNKNOWN',
                whole_session_exact_cpu_claim=False,
                self_wall_scope='from first script timestamp; Python startup and publication/exit need external meter',
                external_analysis_meter_needed_for_complete_process_cost=True,
                post_exit_cpu_formula='7005.07 + attempt02 external user+sys + analysis external user+sys',
                post_exit_elapsed_sum_formula='7178.14 + attempt02 external real + analysis external real')
        with (BASE/'analysis.json').open('x') as stream:
            json.dump(out, stream, indent=2, allow_nan=False,
                default=lambda value: str(value) if isinstance(value, (Q, Decimal)) else value)
            stream.write('\n')
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if out['analysis_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
