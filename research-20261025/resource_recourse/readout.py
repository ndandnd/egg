"""One compact read of the closed resource-recourse owner; stdlib only."""
import time
START = time.monotonic()
from fractions import Fraction as Q
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal

HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
GROUPS = ((10001, 20, 'different_membership'), (10006, 20, 'same_membership'),
          (10009, 28, 'different_membership'), (10005, 28, 'same_membership'))
GRIDS, TARGETS = (90., 45.), ('source0', 'source1')
POLICY = 'resource-recourse-closed-owner-economic-readout-v1'


def display(value):
    if value is None:
        return None
    try:
        number = float(Q(value))
        return number if math.isfinite(number) else None
    except (OverflowError, ValueError, TypeError, ZeroDivisionError):
        return None


def displays(value):
    """Separate display projection; original exact strings stay in the full output."""
    if isinstance(value, dict):
        return {key: display(item) if key.endswith('_exact') and item is not None
                else displays(item) for key, item in value.items()}
    if isinstance(value, list):
        return [displays(item) for item in value]
    return value


def stage_packet(packet):
    result = {name: packet.get(name) for name in (
        'stage', 'index', 'entered_monotonic', 'returned_monotonic', 'native_deadline',
        'native_overrun_s', 'native_invocation_attempted', 'native_call_observed',
        'physical_candidate_admitted', 'physical_bill_exact', 'raw_tangent_envelope',
        'raw_tangent_native_slack', 'tangent_counts')}
    stats = packet.get('stats')
    result['stats'] = None if stats is None else {name: stats.get(name) for name in (
        'status', 'incumbent', 'lower_bound', 'wall_s', 'seconds_cap', 'threads', 'backend',
        'n_vars', 'n_int', 'n_constraints', 'physical_constraints')}
    return result


def compact(row):
    worker = row.get('worker') or {}
    stats = worker.get('stats') or {}
    result = {name: row.get(name) for name in (
        'task_id', 'ordinal', 'phase', 'group', 'base_id', 'services', 'grid_kw', 'target_source',
        'attempted', 'reaped', 'returncode', 'timed_out', 'method_late', 'parent_elapsed_s',
        'parent_endpoint_accepted', 'physical_new_prior_valid', 'cell_qualified', 'full_method_success',
        'config_failure', 'fatal_contract', 'resource_violation', 'identity_failure',
        'cpu_observation_complete', 'waited_child_cpu_s', 'parent_cpu_s', 'unresolved_cpu_reserve_s',
        'missing_reference', 'unattempted_reason', 'failures', 'operational_endpoint_available',
        'operational_bill_exact', 'operational_components', 'operational_source',
        'retained_route_changed_from_reference', 'new_prior_components')}
    result['worker'] = {name: worker.get(name) for name in (
        'receipt_complete', 'method_endpoint_accepted', 'physical_witness_valid',
        'physical_new_prior_valid', 'cell_qualified', 'full_method_success',
        'config_failure', 'fatal_contract', 'identity_failure', 'resource_violation',
        'stop_signal', 'missing_reason', 'failures', 'case_identity', 'target_market_identity',
        'native_calls', 'stage_native_calls', 'qp_native_calls', 'qp_native_call_attempts',
        'qp_status', 'qp_success', 'qp_candidate_admitted', 'route_search_candidate_admitted',
        'selected_route_source', 'qp_selected_source', 'used_fallback',
        'current_acquisition_available', 'common_prior_bill_exact',
        'candidate_bill_exact', 'fallback_bill_exact', 'retained_bill_exact', 'true_bill_exact',
        'helper_true_bill_exact', 'native_point', 'native_bound', 'native_lower_bound',
        'numerical_agreement', 'optimal_candidate_fallback_discrepancy',
        'route_identity_method', 'fixed_path_recovery_verified',
        'QP_fixed_route_changed_from_reference', 'retained_route_changed_from_reference',
        'copy_contract', 'helper_failures', 'acquisition_failures', 'routing_failures',
        'routing_bound_scope', 'selected_decomposition', 'E_ref_exact',
        'original_reference_bill_exact', 'retained_cost_over_E_ref', 'resources',
        'route_ordering', 'optimization_bound_supported', 'global_lower_bound', 'certificate_claim')}
    result['worker']['stats'] = {name: stats.get(name) for name in (
        'Status', 'SolCount', 'ObjVal', 'ObjBound', 'native_lower_bound', 'lower_bound_scope',
        'native_optimal', 'Method', 'seed', 'threads', 'FeasibilityTol', 'OptimalityTol', 'BarConvTol',
        'TimeLimit', 'Runtime', 'Work', 'IterCount', 'BarIterCount', 'MaxVio', 'ConstrVio',
        'BoundVio', 'DualVio', 'ComplVio', 'ConstrResidual', 'DualResidual',
        'raw_objective_exact', 'replay_objective_exact', 'native_to_physical_cost_delta',
        'raw_to_physical_cost_delta_exact', 'native_overrun_s', 'wall_s', 'cpu_s')}
    for name in ('acquisition_packets', 'routing_packets'):
        result['worker'][name] = [stage_packet(packet) for packet in worker.get(name, [])]
    result['points_display'] = dict(C=display(worker.get('candidate_bill_exact')),
        B=display(worker.get('fallback_bill_exact')), U=display(worker.get('retained_bill_exact')),
        N=worker.get('native_point'), operational=display(row.get('operational_bill_exact')),
        common_prior=display(worker.get('common_prior_bill_exact')))
    result['operational_components_display'] = displays(row.get('operational_components'))
    result['worker_selected_components_display'] = displays(worker.get('selected_decomposition'))
    return result


def opportunity_scalar(opportunity):
    if opportunity is None:
        return None
    fields = {name: opportunity.get(name) for name in (
        'available', 'unavailable_reasons', 'diagnostic_only', 'native_feasibility_certificate',
        'projected_load_set_equality_claim', 'price_optimality_claim',
        'total_ideal_grid_kwh_exact', 'common_terminal_start_min_exact',
        'all_return_by_terminal_open', 'all_no_midday_soc_sufficient',
        'common_terminal_capacity_grid_kwh_exact', 'source1_cheap_resource_capacity_grid_kwh_exact',
        'common_terminal_cheap_capacity_grid_kwh_exact', 'total_grid_le_common_terminal_capacity',
        'total_grid_le_common_terminal_cheap_capacity', 'E_le_cheapcap_conditional')}
    fields['vehicle_count'] = len(opportunity.get('per_vehicle', []))
    fields['selected_depot_visit_count'] = len(opportunity.get('selected_depot_windows', []))
    return displays(fields)


def main():
    if HERE != ROOT/'research-20261025/resource_recourse':
        raise ValueError('Wrong readout source namespace')
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    def stopped(*_):
        raise TimeoutError('Readout90s wall provision exhausted')
    signal.signal(signal.SIGALRM, stopped)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 90.-(time.monotonic()-START)))
    manifest_path = HERE/'READOUT_LAUNCH.json'
    manifest_bytes = manifest_path.read_bytes()
    launch = json.loads(manifest_bytes)
    if launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS':
        raise ValueError('DRAFT/unreviewed readout; no owner inputs admitted')
    expected_budget = dict(cpu_s=60, wall_s=90, inside_total_cpu_s=4500,
        inside_total_wall_s=7200, inside_closure_cpu_s=360, owner_finalization_reserved_cpu_s=120)
    if launch.get('budgets') != expected_budget:
        raise ValueError('Readout resource commitment differs')
    if launch.get('inputs') != ['attempt01/receipt.json', 'process-time.txt'] or launch.get('output') != 'READOUT.json':
        raise ValueError('Readout exact input/output scope differs')
    source_path = Path(__file__).resolve()
    pins = {str(source_path): hashlib.sha256(source_path.read_bytes()).hexdigest(),
            str(manifest_path): hashlib.sha256(manifest_bytes).hexdigest()}

    # Fund the complete new provision BEFORE parsing the closed owner receipt.
    meter_path = HERE/'process-time.txt'
    meter_bytes = meter_path.read_bytes()
    pins[str(meter_path)] = hashlib.sha256(meter_bytes).hexdigest()
    meter_text = meter_bytes.decode('utf-8')
    meter = {}
    for line in meter_text.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[0] not in ('real', 'user', 'sys') or fields[0] in meter:
            raise ValueError('Require one closed /usr/bin/time -p owner meter')
        meter[fields[0]] = Q(fields[1])
    if set(meter) != {'real', 'user', 'sys'} or any(value < 0 for value in meter.values()):
        raise ValueError('Owner external meter incomplete/nonpositive-domain')
    external_cpu = meter['user']+meter['sys']
    cpu_guard, wall_guard = Q('.02'), Q('.01')
    funded_cpu, funded_wall = external_cpu+cpu_guard, meter['real']+wall_guard
    if (funded_cpu+60 > 4500 or funded_wall+90 > 7200 or 120+60 > 360):
        raise ValueError('Readout provision does not fit existing total/closure')

    owner_path = HERE/'attempt01/receipt.json'
    raw = owner_path.read_bytes()
    pins[str(owner_path)] = hashlib.sha256(raw).hexdigest()
    owner = json.loads(raw)
    owner_bytes = len(raw)
    del raw
    if (owner.get('receipt_complete') is not True or owner.get('ledger_complete') is not True
            or owner.get('accounting_complete') is not True
            or owner.get('unresolved_cpu_reserve_s') != 0):
        raise ValueError('Require administratively closed ledger and complete owner accounting')
    # Method/acquisition success and owner.passed are NOT input eligibility tests.
    owner_combined = owner['resources']['combined_cpu_s']
    if type(owner_combined) not in (int, float) or not math.isfinite(owner_combined) or owner_combined < 0:
        raise ValueError('Owner combined CPU observation missing/nonfinite')
    funded_cpu = max(funded_cpu, Q(owner_combined))
    if funded_cpu+60 > 4500:
        raise ValueError('Owner CPU observation leaves insufficient total provision')
    original_map = {row['group']: row for row in owner.get('originals', [])}
    variants = owner.get('variants', [])
    if len(owner['acquisitions']) != 8 or len(owner['decisions']) != 32:
        raise ValueError('Require all planned acquisition/active ledger rows, including failures')
    acquisitions = [compact(row) for row in owner['acquisitions']]
    active = [compact(row) for row in owner['decisions']]
    acquisition_map = {(row['group'], row['grid_kw']): row for row in acquisitions}
    for row in active:
        components = row.get('operational_components') or {}
        opportunity = components.get('opportunity_diagnostics')
        source = 'operational_components' if opportunity is not None else None
        if opportunity is None and row.get('operational_source') == 'acquired_prior_fallback':
            prior = acquisition_map.get((row['group'], row['grid_kw']), {})
            if prior.get('physical_new_prior_valid'):
                opportunity = (prior.get('worker', {}).get('selected_decomposition') or {}).get('opportunity_diagnostics')
                source = 'accepted_acquisition_path_diagnostic' if opportunity is not None else None
        row.update(operational_opportunity_diagnostics=opportunity, operational_opportunity_source=source)

    # All economics below are formatting of the owner's ALREADY RECORDED summary.
    summary = owner['summary']
    blocks, interactions = [], []
    for group in summary['groups']:
        for level in group['levels']:
            methods = level['methods']
            bills = {phase: methods.get(phase, {}).get('operational_bill_exact') for phase in ('fixed', 'adaptive')}
            blocks.append(dict(group=group['group'], services=group['services'],
                stratum=group['declared_prior_stratum'], grid_kw=level['grid_kw'], target_source=level['target_source'],
                planned_methods=2, defined=level['defined'], E_ref_exact=group['E_ref_exact'],
                operational_bills_exact=bills, methods=methods,
                fixed_minus_adaptive_exact=level['adaptive_gain_fixed_minus_adaptive'],
                gain_over_fixed_E_ref_exact=level['adaptive_gain_over_fixed_E_ref'],
                display=dict(fixed=display(bills['fixed']), adaptive=display(bills['adaptive']),
                    fixed_minus_adaptive=display(level['adaptive_gain_fixed_minus_adaptive']),
                    gain_over_fixed_E_ref=display(level['adaptive_gain_over_fixed_E_ref']), E_ref=display(group['E_ref_exact']))))
        for interaction in group['interactions']:
            interactions.append(dict(group=group['group'], services=group['services'], **interaction,
                display=dict(gain45_minus_gain90=display(interaction['resource_interaction_gain45_minus_gain90']),
                             interaction_over_fixed_E_ref=display(interaction['interaction_over_fixed_E_ref']))))
    variant_map = {(row['group'], row['grid_kw']): row for row in variants}
    variant_rows = []
    for base, services, stratum in GROUPS:
        group = f'physical_v2_s{base}'
        for grid in GRIDS:
            variant = variant_map.get((group, grid), {})
            variant_rows.append(dict(group=group, services=services, grid_kw=grid, stratum=stratum,
                present=bool(variant), case_identity=variant.get('case_identity'),
                E_ref_exact=original_map.get(group, {}).get('E_ref_exact'),
                original_no_solve_reference=variant.get('original_reference'),
                opportunity_diagnostics=variant.get('opportunity_diagnostics')))
    counts = {name: summary.get(name) for name in (
        'planned_groups', 'planned_acquisitions', 'planned_active', 'attempted_acquisitions',
        'valid_new_priors', 'attempted_active', 'qualified_QP_cells', 'full_method_successes',
        'operational_active_defined', 'planned_interactions', 'defined_interactions')}
    counts.update(planned_blocks=16, defined_blocks=sum(row['defined'] for row in blocks),
                  planned_variants=8, variants_present=sum(row['present'] for row in variant_rows))
    output = dict(policy=POLICY, receipt_complete=True, source_manifest_sha256=pins,
        owner_receipt_path=str(owner_path), owner_receipt_bytes=owner_bytes,
        source_of_exact_cost_strings='Closed owner receipt; exact values retained below, floats are display only',
        owner_closure={name: owner.get(name) for name in ('passed', 'passed_scope', 'receipt_complete',
            'ledger_complete', 'accounting_complete', 'config_failure', 'failures', 'findings',
            'stop_signal', 'dispatch_stopped_reason', 'all40_assignments_attempted')},
        counts=counts, acquisitions=acquisitions, active=active, blocks=blocks, interactions=interactions,
        variants=variant_rows, originals=owner.get('originals', []),
        complete_eight_interaction_mean_exact=summary['complete_eight_interaction_mean'],
        available_only_mean=None, statistical_or_model_promotion_gate=False,
        ideal_route_ordering='UNRESOLVED', certificate_claim=False,
        interpretation='Operational feasible-cost contrasts including declared acquired-prior fallback; '
            'full-method/QP/search admission kept separate. Source-point agreement is not an optimum-gap bound.',
        resource_accounting=dict(external_owner_meter_path=str(meter_path),
            external_owner_real_s=str(meter['real']), external_owner_user_s=str(meter['user']),
            external_owner_system_s=str(meter['sys']), external_owner_displayed_cpu_s=str(external_cpu),
            external_cpu_rounding_guard_s=str(cpu_guard), external_wall_rounding_guard_s=str(wall_guard),
            guarded_closed_owner_cpu_s=str(funded_cpu), owner_resources=owner['resources'],
            readout_cpu_provision_s=60, readout_wall_provision_s=90,
            owner_finalization_closure_reservation_s=120, total_closure_s=360,
            reservation_is_not_an_extra_actual_charge=True, readout_external_meter_pending=True))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    output['resource_accounting'].update(readout_prepublication_user_s=usage.ru_utime,
        readout_prepublication_system_s=usage.ru_stime,
        readout_prepublication_elapsed_s=time.monotonic()-START)
    if usage.ru_utime+usage.ru_stime >= 60 or time.monotonic()-START >= 90:
        raise TimeoutError('No provision remains for readout publication')
    with (HERE/'READOUT.json').open('x') as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    brief_blocks = [dict(group=row['group'], services=row['services'], grid_kw=row['grid_kw'],
        target=row['target_source'], defined=row['defined'], **row['display'],
        method_success={name: values['full_method_success'] for name, values in row['methods'].items()},
        retained_route_changed={name: values['retained_route_changed_from_reference']
                                for name, values in row['methods'].items()},
        components={name: {key: display(value.get('operational_components', {}).get(key))
            if key.endswith('_exact') else value.get('operational_components', {}).get(key)
            for key in ('fleet_count', 'vehicle_cost_exact', 'deadhead_cost_exact',
                'linear_electricity_exact', 'quadratic_electricity_exact', 'grid_kwh_exact')}
            if value.get('operational_components') is not None else None
            for name, value in row['methods'].items()}) for row in blocks]
    brief_variants = [dict(group=row['group'], services=row['services'], grid_kw=row['grid_kw'],
        original_no_solve_valid=(row['original_no_solve_reference'] or {}).get('valid'),
        opportunity=opportunity_scalar(row['opportunity_diagnostics'])) for row in variant_rows]
    failures = [dict(task_id=row['task_id'], phase=row['phase'],
        parent_failures=row.get('failures'), worker_failures=row['worker'].get('failures'),
        acquisition_failures=row['worker'].get('acquisition_failures'),
        routing_failures=row['worker'].get('routing_failures'), helper_failures=row['worker'].get('helper_failures'),
        method_success=row.get('full_method_success'), physical_new_prior_valid=row.get('physical_new_prior_valid'),
        native_calls=row['worker'].get('stage_native_calls')) for row in acquisitions+active
        if row.get('failures') or row['worker'].get('failures') or row['worker'].get('acquisition_failures')
        or row['worker'].get('routing_failures') or row['worker'].get('helper_failures')
        or not row.get('full_method_success')]
    print(json.dumps(dict(owner_closure=output['owner_closure'], counts=counts,
        acquisitions=[dict(task_id=row['task_id'], accepted=row.get('physical_new_prior_valid'),
            native_status=[p['stats'].get('status') if p['stats'] else None for p in row['worker']['acquisition_packets']])
            for row in acquisitions], block_points=brief_blocks,
        interactions=[dict(group=row['group'], target=row['target_source'], defined=row['defined'], **row['display'])
            for row in interactions],
        complete_eight_interaction_mean_display=display(summary['complete_eight_interaction_mean']),
        failure_inventory=failures, variant_diagnostics=brief_variants),
                     indent=2, allow_nan=False))
    signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    main()
