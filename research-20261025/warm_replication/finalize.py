"""Eight-group replication readout; no inference, optimization or replay."""
import time

WALL0, CPU0 = time.monotonic(), time.process_time()

from fractions import Fraction as Q
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys

BASE = Path(__file__).resolve().parent
GROUPS, SIZES, SEEDS = (50604, 50606, 50607, 50608, 50609, 50610, 50611, 50612), (40, 80), (17, 41, 73)
ARMS = ('GNN', 'CatBoost', 'CA1', 'CoverCA1', 'random', 'full', 'fixed_route_QP', 'GNN_day')
ADAPTATION_NEAR_ZERO_D = Q(1, 1_000_000)
PARTS = ('ops_exact', 'fleet_operating_exact', 'deadhead_exact', 'linear_electricity_exact',
         'quadratic_electricity_exact', 'electricity_exact', 'grid_kwh_exact', 'total_exact')


def check():
    if time.process_time()-CPU0 > 115 or time.monotonic()-WALL0 > 175:
        raise TimeoutError('Readout body allowance exhausted; retain5s publication reserve')


def median(values):
    values = sorted(values)
    n = len(values)
    return None if not n else values[n//2] if n % 2 else (values[n//2-1]+values[n//2])/2


def exact(value):
    if not isinstance(value, str):
        raise ValueError('Expected exact rational string, not a rounded numeric display')
    return Q(value)


def components(raw, total):
    values = {name: exact(raw[name]) for name in PARTS}
    if (any(value < 0 for value in values.values()) or values['total_exact'] != exact(total)
            or values['ops_exact'] != values['fleet_operating_exact']+values['deadhead_exact']
            or values['electricity_exact'] != values['linear_electricity_exact']+values['quadratic_electricity_exact']
            or values['total_exact'] != values['ops_exact']+values['electricity_exact']):
        raise ValueError('Compact exact cost decomposition differs')
    return values


def assignments():
    for g, base in enumerate(GROUPS):
        for s, size in enumerate(SIZES):
            for z, seed in enumerate(SEEDS):
                block = ((g*2+s)*3+z)
                shift = block % 8
                order = list(ARMS[shift:]+ARMS[:shift])
                if (block//8) % 2:
                    order.reverse()
                for position, arm in enumerate(order):
                    yield dict(group=base, case=f'scale:{base}:{size}', size=size,
                        seed=seed, arm=arm, block=block, position=position)


def conditioning_overlap(late, day):
    """Metadata-only set comparison, once per paired block; no raw scores."""
    pools = {'GNN': late.get('conditioning_pool'), 'GNN_day': day.get('conditioning_pool')}
    record = dict(defined=False, missing_reason=None)
    if any(not isinstance(p, dict) for p in pools.values()):
        return dict(record, missing_reason='One or both conditioning-pool records are missing')
    if any(p.get('status') != 'selected' for p in pools.values()):
        return dict(record, missing_reason='One or both conditioning pools were not selected',
            statuses={arm: p.get('status') for arm, p in pools.items()})
    if pools['GNN'].get('M') != pools['GNN_day'].get('M') or pools['GNN'].get('K') != pools['GNN_day'].get('K'):
        return dict(record, missing_reason='Conditioning pools do not share M/K')
    sets = {}
    for arm, pool in pools.items():
        ids = pool.get('selected_flexible_ids')
        if not isinstance(ids, list) or any(not isinstance(mid, str) for mid in ids):
            return dict(record, missing_reason=arm+' selected flexible IDs are unavailable')
        sets[arm] = set(ids)
        if len(sets[arm]) != len(ids) or len(ids) != pool['K']:
            return dict(record, missing_reason=arm+' selected flexible IDs are not a unique exact-K pool')
    a, b = sets['GNN'], sets['GNN_day']
    intersection, union = len(a & b), len(a | b)
    return dict(record, defined=True, M=pools['GNN']['M'], K=pools['GNN']['K'], identical=a == b,
        intersection_count=intersection, union_count=union, Jaccard=Q(intersection, union) if union else Q(1),
        empty_union_Jaccard_convention=1, differing_connection_count=len(a ^ b),
        exposure={arm: {key: pool.get(key) for key in ('protected_Bw_count', 'rank_fill_room', 'fill_count')}
            for arm, pool in pools.items()})


def archive_baseline_capture(record, archives, *, required):
    """Byte-only exception: one original stream into SHA256 and lossless gzip."""
    check()
    case, folder_name = record['case'], record.get('folder')
    entry = dict(case=case, source_exists=False, archive_complete=None, source_sha256=None)
    archives.append(entry)
    if not folder_name:
        if required:
            raise ValueError('Admitted acquisition missing its capture folder')
        return
    folder = Path(folder_name).resolve()
    if (folder.parent != (BASE/'attempt01').resolve() or not folder.name[:3].isdigit()
            or folder.name[3:] != '-acquisition-'+case.replace(':', '-')+'-CoverCA1'):
        raise ValueError('Capture folder is not the assigned acquisition folder')
    source = folder/'native-capture.json'
    archive = folder/'native-capture.json.gz'
    entry.update(source=str(source.relative_to(BASE)), archive=str(archive.relative_to(BASE)))
    if not source.exists():
        if required:
            raise FileNotFoundError('Admitted acquisition native capture missing: '+str(source))
        return
    entry.update(source_exists=True, archive_complete=False, hash_started=True)
    before, digest, size = source.stat(), hashlib.sha256(), 0
    try:
        with source.open('rb') as src, archive.open('xb') as dest:
            entry['source_opened'] = True
            with gzip.GzipFile(filename='', mode='wb', fileobj=dest, mtime=0, compresslevel=6) as packed:
                while True:
                    check()
                    chunk = src.read(1024*1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
                    packed.write(chunk)
            dest.flush()
            os.fsync(dest.fileno())
        after = source.stat()
        if ((before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_ino, after.st_size, after.st_mtime_ns) or size != before.st_size):
            raise ValueError('Original capture changed or stream byte count differs')
        entry.update(archive_complete=True, source_sha256=digest.hexdigest(), source_bytes=size,
            original_stat_bytes=before.st_size, source_byte_count_matches_stat=True,
            archive_bytes=archive.stat().st_size)
    except BaseException as exc:
        entry.update(failure=dict(type=type(exc).__name__, message=str(exc)),
            streamed_prefix_bytes=size, streamed_prefix_sha256=digest.hexdigest(),
            original_stat_bytes=before.st_size,
            partial_archive_bytes=archive.stat().st_size if archive.exists() else None)
        raise


def main():
    output = BASE/'summary.json'
    if output.exists():
        raise FileExistsError('Exclusive summary already exists')

    def expired(signum, frame):
        raise TimeoutError('Readout resource allowance reached')

    resource.setrlimit(resource.RLIMIT_CPU, (115, 120))
    signal.signal(signal.SIGXCPU, expired)
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, 175-(time.monotonic()-WALL0)))
    out = dict(finalization_complete=False, finalization_passed=False, scientific_qualification=False,
        scope='eight fixed new development groups; conditional fixed-fleet warm operational cost',
        learned_reporting_roles={'GNN': 'primary fixed family', 'CatBoost': 'secondary fixed family'},
        acquisitions=[], cells=[], pairwise_cells=[], pairwise_summaries=[],
        group_arm_summaries=[], learned_continuation={}, validation_errors=[], failures=[],
        baseline_capture_archives=[], planned_active_cells=384)
    out['cells'] = [{**row, 'recorded': False, 'attempted': False, 'method_endpoint_accepted': False,
        'method_success': False, 'config_failure': False, 'cost_defined': False,
        'operational_endpoint_available': False, 'late_or_timed_out': False,
        'finalizer_processed': False, 'cost_undefined_reason': 'Finalizer did not process this assigned cell'}
        for row in assignments()]
    master, priors, indexed = {}, {}, {}
    lookup = {(row['case'], row['seed'], row['arm']): row for row in out['cells']}
    invalid_admissions = []
    try:
        with (BASE/'attempt01/receipt.json').open('rb') as stream:
            raw = stream.read(64*1024*1024+1)
        if len(raw) > 64*1024*1024:
            raise ValueError('Compact campaign receipt exceeds64MiB')
        master = json.loads(raw)
        out.update(campaign_complete=master.get('complete'), campaign_passed=master.get('passed'),
            campaign_record_complete=master.get('campaign_record_complete'),
            campaign_failures=master.get('failures'), campaign_stop_signal=master.get('stop_signal'),
            campaign_resources=master.get('resources'), campaign_elapsed_s=master.get('elapsed_s'),
            campaign_unresolved_child_cpu_reserve_s=master.get('unresolved_child_cpu_reserve_s'),
            campaign_accounting_observations_complete=master.get('accounting_observations_complete'),
            campaign_preflight=master.get('preflight'), campaign_finalization=master.get('finalization'))
        acquisition_rows = master.get('acquisitions', [])
        expected_cases = {f'scale:{base}:{size}' for base in GROUPS for size in SIZES}
        if len(acquisition_rows) != 16 or {row.get('case') for row in acquisition_rows} != expected_cases:
            out['validation_errors'].append('Expected exactly sixteen assigned acquisition records')
        for case in sorted(expected_cases):
            check()
            records = [row for row in acquisition_rows if row.get('case') == case]
            record = records[0] if len(records) == 1 else {}
            worker = record.get('worker', {})
            admitted = record.get('method_endpoint_accepted') is True
            row = dict(case=case, recorded=len(records) == 1, attempted=record.get('attempted') is True,
                method_endpoint_accepted=admitted, method_success=worker.get('method_success'),
                folder=record.get('folder'), failures=record.get('failures'), worker_failures=worker.get('failures'),
                timed_out=record.get('timed_out'), parent_elapsed_s=record.get('parent_elapsed_s'),
                waited_child_cpu_s=record.get('waited_child_cpu_s'), parent_cpu_s=record.get('parent_cpu_s'),
                cpu_observation_complete=record.get('cpu_observation_complete'),
                unresolved_cpu_reserve_s=record.get('unresolved_cpu_reserve_s'),
                worker_resources=worker.get('resources'), valid_prior=False)
            out['acquisitions'].append(row)
            if len(records) != 1:
                out['validation_errors'].append('Missing/duplicate acquisition: '+case)
            if not admitted:
                continue
            try:
                if (record.get('attempted') is not True or worker.get('physical_witness_valid') is not True
                        or worker.get('admission_checks_passed') is not True
                        or type(worker.get('fleet_count')) is not int or worker['fleet_count'] <= 0):
                    raise ValueError('Admitted acquisition lacks physical/fleet checks')
                target = components(worker['target_decomposition'], worker['target_bill_exact'])
                day = components(worker['day_decomposition'], worker['day_bill_exact'])
                if day['fleet_operating_exact'] != target['fleet_operating_exact'] or day['deadhead_exact'] != target['deadhead_exact']:
                    raise ValueError('Repricing unchanged prior changed operating cost')
                prior = dict(case_identity=worker['case_identity'], fleet_count=worker['fleet_count'],
                    total=target['total_exact'], E0=target['electricity_exact'], target=target)
                priors[case] = prior
                row.update(valid_prior=True, fleet_count=worker['fleet_count'], day_decomposition=day,
                    target_decomposition=target, target_E0=prior['E0'], zero_E0=prior['E0'] == 0)
            except Exception as exc:
                row['validation_failure'] = dict(type=type(exc).__name__, message=str(exc))
                invalid_admissions.append(dict(kind='acquisition', case=case, reason=str(exc)))
        observed = master.get('decisions', [])
        for row in observed:
            check()
            key = (row.get('case'), row.get('seed'), row.get('arm'))
            if key in indexed:
                out['validation_errors'].append('Duplicate decision identity: '+repr(key))
            else:
                indexed[key] = row
        expected_keys = {(row['case'], row['seed'], row['arm']) for row in assignments()}
        if len(observed) != 384 or set(indexed) != expected_keys:
            out['validation_errors'].append('Campaign does not contain exactly384 frozen decision identities')
        references = master.get('reference_blocks', [])
        if len(references) != 48 or len({r.get('block') for r in references}) != 48:
            out['validation_errors'].append('Expected exactly48 unchanged reference blocks')
        for assignment in assignments():
            check()
            key = (assignment['case'], assignment['seed'], assignment['arm'])
            source = indexed.get(key, {})
            prior = priors.get(assignment['case'])
            execution = source.get('execution', {})
            worker = execution.get('worker', {})
            row = lookup[key]
            row.update({**assignment, 'recorded': key in indexed, 'attempted': source.get('attempted') is True,
                'method_endpoint_accepted': source.get('method_endpoint_accepted') is True,
                'method_success': source.get('method_success') is True,
                'config_failure': source.get('config_failure') is True,
                'operational_endpoint_available': source.get('operational_endpoint_available') is True,
                'operational_selected_source': source.get('operational_selected_source'),
                'missing_reason': source.get('missing_reason'),
                'not_dispatched_reason': source.get('not_dispatched_reason'),
                'contract_failure': source.get('contract_failure'),
                'late_or_timed_out': execution.get('timed_out') is True
                    or isinstance(execution.get('parent_elapsed_s'), (int, float)) and execution['parent_elapsed_s'] > 60,
                'parent_elapsed_s': execution.get('parent_elapsed_s'),
                'execution_returncode': execution.get('returncode'), 'execution_reaped': execution.get('reaped'),
                'execution_failures': execution.get('failures'), 'worker_failures': worker.get('failures'),
                'planner_status': worker.get('planner_status'), 'planner_failures': worker.get('planner_failures'),
                'qp_status': worker.get('qp_status'), 'qp_success': worker.get('qp_success'),
                'qp_candidate_admitted': worker.get('qp_candidate_admitted'),
                'qp_failures': worker.get('qp_failures'), 'qp_native_stats': worker.get('qp_native_stats'),
                'qp_copy_contract': worker.get('qp_copy_contract'),
                'qp_requested_native_seed': worker.get('qp_requested_native_seed'),
                'qp_actual_native_seed': worker.get('qp_actual_native_seed'),
                'qp_global_lower_bound': worker.get('qp_global_lower_bound'),
                'qp_certificate_claim': worker.get('qp_certificate_claim'),
                'native_calls': worker.get('native_calls'), 'native_call_attempts': worker.get('native_call_attempts'),
                'admission_checks_passed': worker.get('admission_checks_passed'),
                'admission_rejected': worker.get('admission_rejected'),
                'worker_used_fallback': worker.get('used_fallback'), 'worker_resources': worker.get('resources'),
                'rank_input_tariff': worker.get('rank_input_tariff'),
                'conditioning_pool': worker.get('conditioning_pool'),
                'selection_contract': worker.get('selection_contract'),
                'target_E0': None if prior is None else prior['E0'], 'cost_defined': False,
                'finalizer_processed': True, 'cost_undefined_reason': None})
            try:
                if source and any(source.get(field) != assignment[field] for field in ('block', 'position')):
                    raise ValueError('Frozen block/position differs')
                if row['method_success'] and not row['method_endpoint_accepted']:
                    raise ValueError('Method success asserted without endpoint admission')
                if row['method_endpoint_accepted'] and (worker.get('admission_checks_passed') is not True
                        or worker.get('physical_witness_valid') is not True
                        or worker.get('case_identity') != (prior or {}).get('case_identity')):
                    invalid_admissions.append(dict(kind='active', case=assignment['case'],
                        seed=assignment['seed'], arm=assignment['arm'], reason='Accepted endpoint lacks valid common physical checks'))
                    raise ValueError('Invalid admitted active endpoint')
                if not row['operational_endpoint_available']:
                    if prior is not None:
                        raise ValueError('Available common prior omitted from operational endpoint')
                    row['cost_undefined_reason'] = 'Predetermined acquisition unavailable; no free-zero endpoint'
                    continue
                if prior is None:
                    raise ValueError('Operational cost claimed without an admitted valid prior')
                parts = components(source['operational_decomposition'], source['operational_target_bill_exact'])
                if (source.get('fleet_count') != prior['fleet_count']
                        or parts['fleet_operating_exact'] != prior['target']['fleet_operating_exact']):
                    raise ValueError('Operational endpoint changes common fixed fleet')
                fallback = source.get('operational_selected_source') in ('preexisting_fallback', 'fallback')
                if not row['method_endpoint_accepted'] and (not fallback or parts != prior['target']):
                    raise ValueError('Failed/late/unattempted method does not retain exact operational fallback')
                if parts['total_exact'] > prior['total']:
                    raise ValueError('Operational retained plan worse than available common fallback')
                refs = [r for r in references if r.get('block') == assignment['block']]
                if len(refs) != 1 or (refs[0].get('case'), refs[0].get('seed'), refs[0].get('available')) != (
                        assignment['case'], assignment['seed'], True):
                    raise ValueError('Missing or inconsistent common unchanged reference')
                if (exact(refs[0]['target_bill_exact']) != prior['total']
                        or components(refs[0]['target_decomposition'], refs[0]['target_bill_exact']) != prior['target']):
                    raise ValueError('Common reference cost differs across seeds/arms')
                row.update(cost_defined=True, operational_decomposition=parts,
                    operational_cost=parts['total_exact'], unchanged_prior_cost=prior['total'],
                    delta_from_unchanged_prior=prior['total']-parts['total_exact'],
                    component_saving={name: prior['target'][name]-parts[name] for name in PARTS},
                    operational_uses_fallback=fallback,
                    E0_normalized_saving=(prior['total']-parts['total_exact'])/prior['E0'] if prior['E0'] > 0 else None,
                    normalization_undefined_reason=None if prior['E0'] > 0 else 'Common prior late electricity E0 is zero')
            except Exception as exc:
                row['validation_failure'] = dict(type=type(exc).__name__, message=str(exc))
                row['cost_undefined_reason'] = str(exc)
                out['validation_errors'].append(dict(case=assignment['case'], seed=assignment['seed'],
                    arm=assignment['arm'], reason=str(exc)))
                if row['method_endpoint_accepted'] and not any(r.get('kind') == 'active'
                        and (r.get('case'), r.get('seed'), r.get('arm')) == key for r in invalid_admissions):
                    invalid_admissions.append(dict(kind='active', case=assignment['case'],
                        seed=assignment['seed'], arm=assignment['arm'], reason=str(exc)))
        for group in GROUPS:
            for arm in ARMS:
                cells = [r for r in out['cells'] if r['group'] == group and r['arm'] == arm]
                available = [r for r in cells if r['cost_defined']]
                values = [r['E0_normalized_saving'] for r in available if r['E0_normalized_saving'] is not None]
                out['group_arm_summaries'].append(dict(group=group, arm=arm, planned=6,
                    recorded=sum(r['recorded'] for r in cells), attempted=sum(r['attempted'] for r in cells),
                    accepted=sum(r['method_endpoint_accepted'] for r in cells),
                    method_success=sum(r['method_success'] for r in cells), operational_cost_defined=len(available),
                    attempted_without_method_success=sum(r['attempted'] and not r['method_success'] for r in cells),
                    not_attempted=sum(not r['attempted'] for r in cells),
                    late_or_timed_out=sum(r['late_or_timed_out'] for r in cells),
                    config_failure=sum(r['config_failure'] for r in cells),
                    missing_prior=sum(r['case'] not in priors for r in cells),
                    fallback=sum(r.get('operational_uses_fallback', False) for r in available),
                    normalized_defined=len(values), median_normalized_saving=median(values) if len(values) == 6 else None,
                    available_only_median=median(values),
                    available_only_median_operational_cost=median([r['operational_cost'] for r in available])))
        for learned in ('GNN', 'CatBoost'):
            for control in (*ARMS, 'unchanged'):
                if control == learned:
                    continue
                paired, group_rows = [], []
                for group in GROUPS:
                    values = []
                    for size in SIZES:
                        for seed in SEEDS:
                            check()
                            case = f'scale:{group}:{size}'
                            left = lookup[(case, seed, learned)]
                            right = lookup.get((case, seed, control))
                            prior = priors.get(case)
                            d, reason, control_cost = None, None, None
                            if not left['cost_defined'] or prior is None:
                                reason = 'Learned operational endpoint or common prior missing/invalid'
                            elif prior['E0'] <= 0:
                                reason = 'Common prior late electricity E0 is zero'
                            elif control != 'unchanged' and not right['cost_defined']:
                                reason = 'Control operational endpoint missing/invalid'
                            else:
                                control_cost = prior['total'] if control == 'unchanged' else right['operational_cost']
                                d = (control_cost-left['operational_cost'])/prior['E0']
                                values.append(d)
                                paired.append(d)
                            out['pairwise_cells'].append(dict(group=group, case=case, size=size, seed=seed,
                                learned=learned, control=control, d=d, undefined_reason=reason,
                                learned_operational_cost=left.get('operational_cost'), control_operational_cost=control_cost,
                                common_prior_late_electricity_E0=None if prior is None else prior['E0']))
                    group_rows.append(dict(group=group, planned_pairs=6, defined_pairs=len(values),
                        median_d=median(values) if len(values) == 6 else None,
                        available_only_median_d=median(values)))
                out['pairwise_summaries'].append(dict(learned=learned, control=control, planned_pairs=48,
                    defined_pairs=len(paired), mean_d=sum(paired, Q(0))/48 if len(paired) == 48 else None,
                    available_only_mean_d=sum(paired, Q(0))/len(paired) if paired else None,
                    groups=group_rows, positive_complete_group_medians=sum(
                        r['median_d'] is not None and r['median_d'] > 0 for r in group_rows)))
        # Descriptive inference-conditioning contrast, never a promotion gate.
        adaptation_rows = [r for r in out['pairwise_cells']
            if (r['learned'], r['control']) == ('GNN', 'GNN_day')]
        adaptation_summary = next(r for r in out['pairwise_summaries']
            if (r['learned'], r['control']) == ('GNN', 'GNN_day'))

        def adaptation_counts(values):
            return dict(GNN_win=sum(value is not None and value > ADAPTATION_NEAR_ZERO_D for value in values),
                GNN_day_win=sum(value is not None and value < -ADAPTATION_NEAR_ZERO_D for value in values),
                nearzero=sum(value is not None and abs(value) <= ADAPTATION_NEAR_ZERO_D for value in values),
                undefined=sum(value is None for value in values))

        contrast_cells = []
        for pair in adaptation_rows:
            check()
            late = lookup[(pair['case'], pair['seed'], 'GNN')]
            day = lookup[(pair['case'], pair['seed'], 'GNN_day')]
            delta = day['operational_cost']-late['operational_cost'] if late['cost_defined'] and day['cost_defined'] else None
            contrast_cells.append({**pair, 'absolute_cost_difference_day_minus_late': delta,
                'GNN_method_success': late['method_success'], 'GNN_day_method_success': day['method_success'],
                'GNN_operational_fallback': late.get('operational_uses_fallback'),
                'GNN_day_operational_fallback': day.get('operational_uses_fallback'),
                'GNN_rank_input_tariff': late.get('rank_input_tariff'),
                'GNN_day_rank_input_tariff': day.get('rank_input_tariff'),
                'pool_overlap': conditioning_overlap(late, day)})
        absolute = [r['absolute_cost_difference_day_minus_late'] for r in contrast_cells
            if r['absolute_cost_difference_day_minus_late'] is not None]
        normalized = [r['d'] for r in contrast_cells if r['d'] is not None]
        contrast_groups = []
        for group_row in adaptation_summary['groups']:
            selected = [r for r in contrast_cells if r['group'] == group_row['group']]
            deltas = [r['absolute_cost_difference_day_minus_late'] for r in selected
                if r['absolute_cost_difference_day_minus_late'] is not None]
            contrast_groups.append({**group_row,
                'median_absolute_cost_difference': median(deltas) if len(deltas) == 6 else None,
                'available_only_median_absolute_cost_difference': median(deltas),
                'cell_win_loss_nearzero': adaptation_counts([r['d'] for r in selected])})
        out['GNN_day_contrast'] = dict(planned_pairs=48, defined_normalized_pairs=len(normalized),
            normalized_difference_definition='(GNN_day operational cost - GNN operational cost) / common prior late electricity E0',
            nearzero_abs_normalized_d_tolerance=ADAPTATION_NEAR_ZERO_D,
            mean_d=adaptation_summary['mean_d'], median_d=median(normalized) if len(normalized) == 48 else None,
            available_only_mean_d=adaptation_summary['available_only_mean_d'],
            available_only_median_d=median(normalized),
            mean_absolute_cost_difference=sum(absolute, Q(0))/48 if len(absolute) == 48 else None,
            median_absolute_cost_difference=median(absolute) if len(absolute) == 48 else None,
            cells=contrast_cells, groups=contrast_groups,
            cell_win_loss_nearzero=adaptation_counts([r['d'] for r in contrast_cells]),
            group_median_win_loss_nearzero=adaptation_counts([r['median_d'] for r in contrast_groups]),
            automatic_promotion_threshold=None, learned_information_causal_claim=False,
            interpretation='fixed-model inference-time ranking conditioning only; descriptive development evidence')
        defined_pools = [r['pool_overlap'] for r in contrast_cells if r['pool_overlap']['defined']]
        pool_exposure = {}
        for arm in ('GNN', 'GNN_day'):
            rooms = [p['exposure'][arm]['rank_fill_room'] for p in defined_pools
                if type(p['exposure'][arm]['rank_fill_room']) is int]
            pool_exposure[arm] = dict(planned=48, defined=len(rooms),
                zero_rank_fill_room=sum(room == 0 for room in rooms),
                mean_rank_fill_room=Q(sum(rooms), 48) if len(rooms) == 48 else None)
        out['GNN_day_contrast']['pool_overlap'] = dict(planned_pairs=48, defined_pairs=len(defined_pools),
            missing_pairs=48-len(defined_pools), identical_pairs=sum(p['identical'] for p in defined_pools),
            changed_pairs=sum(not p['identical'] for p in defined_pools),
            mean_Jaccard=sum((p['Jaccard'] for p in defined_pools), Q(0))/48 if len(defined_pools) == 48 else None,
            median_Jaccard=median([p['Jaccard'] for p in defined_pools]) if len(defined_pools) == 48 else None,
            mean_differing_connection_count=Q(sum(p['differing_connection_count'] for p in defined_pools), 48) if len(defined_pools) == 48 else None,
            exposure=pool_exposure,
            missing=[dict(case=r['case'], seed=r['seed'], reason=r['pool_overlap']['missing_reason'])
                for r in contrast_cells if not r['pool_overlap']['defined']],
            automatic_promotion_threshold=None, interpretation='pool exposure only; no available-only promotion or causal attribution')
        out['invalid_admissions'] = invalid_admissions
        # Canonical config_failure includes fatal resource/identity violations.
        # Inspect every record, including a fatal last task after all dispatches.
        fatal_rows = []
        for acquisition in acquisition_rows:
            for location, payload in (('acquisition', acquisition),
                    ('acquisition_worker', acquisition.get('worker', {}))):
                if payload.get('config_failure') or payload.get('contract_failure'):
                    fatal_rows.append(dict(location=location, case=acquisition.get('case'),
                        config_failure=payload.get('config_failure'), contract_failure=payload.get('contract_failure')))
        for decision in observed:
            execution = decision.get('execution', {})
            for location, payload in (('decision', decision), ('execution', execution),
                    ('worker', execution.get('worker', {}))):
                if payload.get('config_failure') or payload.get('contract_failure'):
                    fatal_rows.append(dict(location=location, case=decision.get('case'),
                        seed=decision.get('seed'), arm=decision.get('arm'),
                        config_failure=payload.get('config_failure'), contract_failure=payload.get('contract_failure')))
        qp_cells = [r for r in out['cells'] if r['arm'] == 'fixed_route_QP']
        qp_qualification = []
        for cell in qp_cells:
            checks = dict(recorded=cell['recorded'], attempted=cell['attempted'],
                parent_timely_endpoint=cell['method_endpoint_accepted'],
                new_physical_QP_candidate=cell.get('qp_candidate_admitted') is True,
                strict_QP_success=cell.get('qp_success') is True,
                native_numerical_OPTIMAL=(cell.get('qp_native_stats') or {}).get('native_optimal') is True)
            qp_qualification.append(dict(case=cell['case'], seed=cell['seed'], checks=checks,
                qualified=all(checks.values()), missing_or_failed_checks=[key for key, passed in checks.items() if not passed]))
        strong_QP_control_qualified = len(qp_qualification) == 48 and all(r['qualified'] for r in qp_qualification)
        out['strong_QP_control_qualification'] = dict(qualified=strong_QP_control_qualified,
            planned=48, assigned=len(qp_qualification), qualified_cells=sum(r['qualified'] for r in qp_qualification),
            cells=qp_qualification, operational_contrasts_retained_on_failure=True,
            interpretation='all48 require a new physical QP candidate plus native OPTIMAL and parent-timely admission; prior fallback alone cannot qualify')
        eligibility = dict(campaign_passed=master.get('passed') is True,
            campaign_complete=master.get('complete') is True,
            accounting_complete=master.get('accounting_observations_complete') is True,
            no_stop_signal=not master.get('stop_signal'),
            no_unresolved_cpu_reserve=master.get('unresolved_child_cpu_reserve_s') == 0,
            no_fatal_config_resource_identity_rows=not fatal_rows,
            all_sixteen_valid_priors=len(priors) == 16,
            all384_recorded_and_attempted=len(out['cells']) == 384
                and all(r['recorded'] and r['attempted'] for r in out['cells']),
            strong_QP_control_qualified=strong_QP_control_qualified,
            no_invalid_admissions=not invalid_admissions, compact_contracts_valid=not out['validation_errors'])
        out.update(continuation_eligibility_checks=eligibility, fatal_rows=fatal_rows)
        complete_inputs = all(eligibility.values())
        for learned in ('GNN', 'CatBoost'):
            checks = []
            for control in ('CoverCA1', 'fixed_route_QP'):
                summary = next(r for r in out['pairwise_summaries'] if (r['learned'], r['control']) == (learned, control))
                checks.append(dict(control=control, defined_pairs=summary['defined_pairs'],
                    positive_group_medians=summary['positive_complete_group_medians'], mean_d=summary['mean_d'],
                    criterion_passed=summary['defined_pairs'] == 48
                        and summary['positive_complete_group_medians'] >= 6
                        and summary['mean_d'] is not None and summary['mean_d'] > Q(1, 100)))
            family_continue = complete_inputs and all(r['criterion_passed'] for r in checks)
            out['learned_continuation'][learned] = dict(exploratory_continue=family_continue,
                status='inconclusive_unqualified_QP_control' if not strong_QP_control_qualified else
                    'inconclusive_incomplete_inputs' if not complete_inputs else 'continue' if family_continue else 'do_not_continue',
                strong_QP_control_qualified=strong_QP_control_qualified, complete_inputs=complete_inputs, comparisons=checks,
                interpretation='research-direction diagnostic only; no significance, superiority or model promotion')
        out['denominators'] = dict(planned_acquisitions=16, recorded_acquisitions=len(acquisition_rows),
            admitted_valid_priors=len(priors), planned_active_cells=384, recorded_active_rows=len(observed),
            attempted=sum(r['attempted'] for r in out['cells']),
            method_accepted=sum(r['method_endpoint_accepted'] for r in out['cells']),
            method_success=sum(r['method_success'] for r in out['cells']),
            attempted_without_method_success=sum(r['attempted'] and not r['method_success'] for r in out['cells']),
            not_attempted=sum(not r['attempted'] for r in out['cells']),
            operational_cost_defined=sum(r['cost_defined'] for r in out['cells']),
            missing_acquisition_cells=sum(r['case'] not in priors for r in out['cells']),
            late_or_timed_out=sum(r['late_or_timed_out'] for r in out['cells']),
            config_failure=sum(r['config_failure'] for r in out['cells']),
            operational_fallback=sum(r.get('operational_uses_fallback', False) for r in out['cells']),
            invalid_admissions=len(invalid_admissions))
        out['fixed_route_QP_diagnostics'] = dict(planned=48, assigned_rows=len(qp_cells),
            recorded=sum(r['recorded'] for r in qp_cells),
            attempted=sum(r['attempted'] for r in qp_cells),
            parent_endpoint_accepted=sum(r['method_endpoint_accepted'] for r in qp_cells),
            strict_method_success=sum(r['method_success'] for r in qp_cells),
            helper_physical_candidates=sum(r.get('qp_candidate_admitted') is True for r in qp_cells),
            parent_timely_candidates=sum(r['method_endpoint_accepted'] and r.get('qp_candidate_admitted') is True for r in qp_cells),
            helper_provisional_candidates=sum(r.get('qp_candidate_admitted') is True and r.get('qp_success') is False for r in qp_cells),
            raw_native_optimal=sum((r.get('qp_native_stats') or {}).get('native_optimal') is True for r in qp_cells),
            interpretation='numerical original-physics fixed-topology QP reports; no unrestricted or exact physical certificate')
        for acquisition in out['acquisitions']:
            archive_baseline_capture(acquisition, out['baseline_capture_archives'],
                required=acquisition['valid_prior'])
        out['finalization_complete'] = True
        out['finalization_passed'] = not out['validation_errors'] and not invalid_admissions
    except BaseException as exc:
        out['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 180-(time.monotonic()-WALL0)))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        external = BASE/'process-time.txt'
        external_time = None
        if external.exists():
            with external.open('r') as stream:
                external_time = stream.read(1024*1024+1)
            if len(external_time) > 1024*1024:
                external_time = None
                out['failures'].append(dict(type='OversizedExternalTime', message='External time text exceeds1MiB'))
        out.update(finalization_cpu_s=time.process_time()-CPU0, finalization_wall_s=time.monotonic()-WALL0,
            finalization_rusage=dict(utime_s=usage.ru_utime, stime_s=usage.ru_stime,
                maxrss_platform_units=usage.ru_maxrss, platform=sys.platform),
            measured_campaign_external_time=external_time,
            finalization_budget=dict(cpu_s=120, wall_s=180, body_cpu_s=115, body_wall_s=175,
                publication_reserve_s=5, reserved_inside_campaign_cpu_s=28800,
                campaign_total_wall_s=36000, campaign_closure_cpu_reserve_s=600, additional_budget=False),
            inherited_first_warm_prerun_measured_cpu_s=206.31,
            inherited_first_warm_prerun_measured_cpu_decimal='206.31',
            inherited_first_warm_prerun_measured_elapsed_sum_s=223.25,
            inherited_first_warm_prerun_measured_elapsed_decimal='223.25',
            prior_closed_cumulative_cpu_s=7064.41, prior_closed_cumulative_elapsed_sum_s=7239.65,
            prior_closed_QP_package_cpu_s=60.04, prior_closed_QP_package_elapsed_sum_s=62.39,
            historical_totals_charged_to_new_budget=False,
            cumulative_baseline_status='closed post-v3 plus preparatory metadata-query external-process sums from PREPARATORY_RESOURCE_RECEIPT.json; not whole-session exact CPU',
            legacy_conditional_guard_s=2546.091499549272, legacy_actual_review_cpu='UNKNOWN',
            legacy_reset=False, whole_session_exact_cpu_claim=False,
            exact_number_encoding='rational strings from compact receipts; no solver/score/replay recomputation',
            timing_scope='receipt/self measurements precede encoding/write/exit; parent external meter charges final tail',
            resource_scope='campaign launcher plus waited children already aggregated in campaign resources; do not double count child rows',
            source_reads=['attempt01/receipt.json', 'process-time.txt if present']
                +[entry['source'] for entry in out['baseline_capture_archives'] if entry.get('source_opened')],
            baseline_capture_archival_complete=out['finalization_complete'] and all(
                entry.get('archive_complete') is True for entry in out['baseline_capture_archives'] if entry['source_exists']),
            all_sixteen_baseline_captures_archived=sum(entry.get('archive_complete') is True
                for entry in out['baseline_capture_archives']) == 16,
            capture_archive_policy='acquired baseline bytes only; one SHA256+lossless gzip stream; originals retained/ignored; no reread audit',
            optimizer_calls=0, inference_calls=0, replay_calls=0,
            raw_capture_analysis_reads=0, active_raw_capture_reads=0,
            baseline_capture_stream_reads=sum(bool(entry.get('source_opened')) for entry in out['baseline_capture_archives']),
            asset_reads=0, hash_calls=sum(bool(entry.get('hash_started')) for entry in out['baseline_capture_archives']),
            caveats=['eight deterministic new development groups, not48 independent timetables or significance evidence',
                'operational fallback cost does not imply method success; missing priors have no free-zero cost',
                'admission validation here checks compact receipt contracts only; physical replay is not repeated',
                'GNN/CatBoost continuation decisions are separate and prospectively fixed; no winner selection',
                'GNN_day tests inference-time ranking conditioning; no learned-information causality or automatic promotion',
                'fixed_route_QP uses one Method0 call with actual block seed; fallback/provisional/optimal statuses stay separate',
                'fixed fleet within each variant; original resource power scales across sizes',
                'integrated system cost, not atomic payments, equilibrium or full-model certificate',
                'even positive continuation does not establish value of learned electricity information'])
        if out['failures']:
            out['finalization_passed'] = False
            for result in out['learned_continuation'].values():
                result['exploratory_continue'] = False
                result['status'] = 'inconclusive_finalization_failure'
                result['complete_inputs'] = False
        with output.open('x') as stream:
            json.dump(out, stream, indent=2, default=lambda value: str(value) if isinstance(value, Q) else value,
                allow_nan=False)
            stream.write('\n')
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(dict(finalization_complete=out['finalization_complete'],
        finalization_passed=out['finalization_passed'], denominators=out.get('denominators'),
        exploratory_continue={key: value['exploratory_continue'] for key, value in out['learned_continuation'].items()})))
    return 0 if out['finalization_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
