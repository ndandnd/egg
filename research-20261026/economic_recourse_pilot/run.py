"""DRAFT: paid target-QP then dependent direct-MIQP economic-recourse owner."""
import time
WALL0 = time.monotonic()
from dataclasses import asdict
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/economic_recourse_pilot'
POLICY = 'paid-target-QP-common-incumbent-direct-MIQP-pilot-v1'
TARGETS = ('source0', 'source1')
EXCLUDED = (10001, 10002, 10018, 10006, 10009, 10010, 10015, 10005)
TOTAL_CPU, TOTAL_WALL, DISPATCH_CPU = 2400., 3600., 2040.
CHILD_PUBLICATION, PUBLICATION_STOP = False, None
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
# Final consumed sources and exact pins must be prospectively frozen by parent.
SOURCE_FILES = ('research-20261026/economic_recourse_pilot/run.py',
    'research-20261026/economic_recourse_pilot/worker.py',
    'research-20261026/economic_recourse_pilot/miqp_control.py',
    'research-20261025/warm_replication/qp_control.py',
    'research-20261025/topology_charging/worker.py', 'src/egglab/__init__.py',
    'src/egglab/native_recharge.py', 'src/egglab/native_hull.py',
    'src/egglab/native_pathflow.py', 'src/egglab/physical_learning_cases.py')


class ContractError(ValueError):
    pass


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
                  default=lambda v: str(v) if isinstance(v, Q) else v)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path); temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value); os.replace(temporary, path)


def self_cpu():
    use = resource.getrusage(resource.RUSAGE_SELF)
    return use.ru_utime+use.ru_stime


def child_cpu():
    use = resource.getrusage(resource.RUSAGE_CHILDREN)
    return use.ru_utime+use.ru_stime


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value*1024)


def read_bytes(path, cap=8*1024**2):
    path = Path(path); before = path.stat()
    if before.st_size > cap:
        raise ContractError('Source/metadata/artifact exceeds bounded byte cap')
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ContractError('Frozen bytes changed during one read')
    return raw


def bind(path, expected, report):
    path = Path(path)
    if str(path) in report['input_sha256']:
        raise ContractError('Duplicate consumed-byte admission')
    raw = read_bytes(path); digest = hashlib.sha256(raw).hexdigest()
    report['input_sha256'][str(path)] = digest
    if digest != expected:
        raise ContractError('Prospectively frozen source/input digest differs')
    return raw


def canonical(plan):
    return sorted((tuple(v['trips']), tuple(v['movements'])) for v in plan['vehicles'])


def stored_case(raw, nr):
    fields = dict(raw)
    fields['trips'] = tuple(nr.Trip(**v) for v in raw['trips'])
    fields['movements'] = tuple(nr.Movement(**dict(v,
        legs=tuple(nr.Leg(**leg) for leg in v['legs']))) for v in raw['movements'])
    fields['resources'] = tuple(nr.Resource(**v) for v in raw['resources'])
    fields['market_edges_min'] = tuple(raw['market_edges_min'])
    return nr.NativeCase(**fields)


def brief(case, plan, replay, market, nh):
    modes = {m.id: m for m in case.movements}
    minutes = sum((nh.rational(leg.arrive_min-leg.depart_min) for v in plan['vehicles']
        for mid in v['movements'] for leg in modes[mid].legs), Q(0))
    fleet = nh.rational(case.vehicle_cost)*len(plan['vehicles'])
    deadhead = nh.rational(case.deadhead_cost_per_min)*minutes
    linear = sum((nh.rational(a)*nh.rational(load) for a, load in zip(market.a, replay['load'])), Q(0))
    quadratic = sum((nh.rational(b)*nh.rational(load)**2/2 for b, load in zip(market.b, replay['load'])), Q(0))
    ops = nh.rational(replay['ops_cost'])
    service = sum((nh.rational(t.energy_kwh) for t in case.trips), Q(0))
    movement = sum((nh.rational(leg.energy_kwh) for v in plan['vehicles']
        for mid in v['movements'] for leg in modes[mid].legs), Q(0))
    return dict(replay_ok=True, fleet_count=len(plan['vehicles']), vehicle_cost_exact=str(fleet),
        deadhead_minutes_exact=str(minutes), deadhead_cost_exact=str(deadhead), ops_cost_exact=str(ops),
        ops_component_residual_exact=str(ops-fleet-deadhead), linear_electricity_exact=str(linear),
        quadratic_electricity_exact=str(quadratic), electricity_exact=str(linear+quadratic),
        total_exact=str(ops+nh.supply(market, replay['load'])),
        grid_kwh_exact=str(nh.rational(replay['grid_kwh'])), service_energy_exact=str(service),
        movement_energy_exact=str(movement), consumption_kwh_exact=str(nh.rational(replay['consumption_kwh'])),
        period_loads=list(replay['load']), max_grid_kw=replay['max_grid_kw'],
        units='generator cost units, kWh, movement-leg minutes; no causal component attribution')


def tasks(groups):
    contexts = []
    for group in groups:
        for target in TARGETS:
            number = len(contexts)+1
            common = dict(group=group['group'], base_id=group['base_id'], services=group['services'],
                context_id=f'C{number:02d}', target_source=target)
            contexts.append(dict(common, target_qp=dict(common, phase='target_qp', ordinal=2*number-1,
                task_id=f'T{2*number-1:02d}-target_qp', attempted=False),
                route_miqp=dict(common, phase='route_miqp', ordinal=2*number,
                task_id=f'T{2*number:02d}-route_miqp', attempted=False)))
    return contexts


def frozen_launch():
    raw = read_bytes(HERE/'LAUNCH.json'); launch = json.loads(raw)
    if (Path(__file__).resolve() != HERE/'run.py' or launch.get('mode') != 'FROZEN'
            or launch.get('review_disposition') != 'PASS' or launch.get('policy') != POLICY
            or launch.get('workdir') != str(ROOT) or launch.get('command') is None
            or launch.get('tracking_prefix') is None or launch.get('cohort_admission') is None
            or launch.get('data_authority') is None or launch.get('source_sha256') is None
            or launch.get('mixed_integer_parameters') is None or launch.get('environment') is None):
        raise SystemExit('DRAFT/PENDING: metadata, original rows and dispatch are not admitted')
    if launch.get('budgets') != dict(total_cpu_s=2400, total_wall_s=3600, dispatch_cpu_s=2040,
        closure_cpu_s=360, preflight_cpu_s=120, finalization_cpu_s=120, finalization_wall_s=180,
        worker_hard_cpu_s=90, native_cutoff_s=52, endpoint_s=60, cleanup_s=3):
        raise SystemExit('Frozen package budgets differ')
    cohort = launch['cohort_admission']
    if (not isinstance(cohort, dict) or set(cohort) != {'receipt_sha256', 'expected_groups', 'selection_accounting'}
            or not isinstance(cohort['selection_accounting'], dict)
            or cohort['selection_accounting'].get('external_accepted') is not True
            or not isinstance(cohort['selection_accounting'].get('charged_cpu_s'), (int, float))
            or not isinstance(cohort['selection_accounting'].get('elapsed_s'), (int, float))
            or not 0 <= cohort['selection_accounting']['charged_cpu_s'] <= 10
            or not 0 <= cohort['selection_accounting']['elapsed_s'] <= 30
            or launch['environment'] != {k: '1' for k in THREAD_ENV}):
        raise SystemExit('Frozen selection accounting/thread environment is incomplete')
    return launch, raw


def admit_cohort(launch, report, check):
    check(); admission = launch['cohort_admission']
    if set(admission) != {'receipt_sha256', 'expected_groups', 'selection_accounting'}:
        raise ContractError('Cohort receipt/identities/accounting must be frozen together')
    raw = bind(HERE/'selection01/receipt.json', admission['receipt_sha256'], report)
    selected = json.loads(raw)
    accounting = admission['selection_accounting']
    if (selected.get('policy') != 'first-two-per-declared-profile-exposed-FIT-cohort-v1'
            or selected.get('receipt_complete') is not True or selected.get('selection_passed') is not True
            or selected.get('admitted_FIT_identity_count') != 80
            or selected.get('excluded_prior_pilot_union') != list(EXCLUDED)
            or selected.get('groups') != admission['expected_groups']
            or selected.get('failures') or selected.get('stopped_signal') is not None
            or accounting.get('external_accepted') is not True
            or accounting.get('charged_cpu_s') is None or accounting.get('elapsed_s') is None):
        raise ContractError('Cohort selection or external resource adoption not admitted')
    groups = selected['groups']
    if (len(groups) != 4 or len({g['base_id'] for g in groups}) != 4
            or [g['services'] for g in groups] != [20, 20, 28, 28]
            or any(type(g['base_id']) is not int or g['base_id'] in EXCLUDED
                or not 10000 <= g['base_id'] < 10128 or g['group'] != f"physical_v2_s{g['base_id']}"
                for g in groups)):
        raise ContractError('Frozen cohort canonical identities/profile counts differ')
    charge, elapsed = float(accounting['charged_cpu_s']), float(accounting['elapsed_s'])
    if not 0 <= charge <= 10 or not 0 <= elapsed <= 30:
        raise ContractError('Selection charge outside its within-campaign provision')
    report.update(groups=groups, contexts=tasks(groups), cohort_admission=admission,
        selection_resources=accounting, selection_inherited_source_hashes=selected.get('input_sha256'),
        selection_charge_adopted_once=True)
    check()
    return groups


def preflight(launch, report, check):
    pins = launch['source_sha256']
    required = {str(ROOT/name) for name in SOURCE_FILES} | {str(HERE/'PROTOCOL.md'),
        str(HERE/'OWNER_NOTE.md'), str(ROOT/'research-20261026/economic_recourse_design/STUDY_DESIGN.md')}
    if required != set(pins):
        raise ContractError('Consumed owner/worker source closure not frozen')
    for path, pin in pins.items():
        check(); bind(Path(path), pin, report)
    groups = admit_cohort(launch, report, check)
    sys.path.insert(0, str(ROOT/'src'))
    import egglab
    from egglab import native_recharge as nr, native_hull as nh, native_pathflow as pf, physical_learning_cases as physical
    for module, name in ((egglab, '__init__.py'), (nr, 'native_recharge.py'), (nh, 'native_hull.py'),
                         (pf, 'native_pathflow.py'), (physical, 'physical_learning_cases.py')):
        if Path(module.__file__).resolve() != ROOT/'src'/'egglab'/name:
            raise ContractError('Paid pure import path differs')
    declared = {g['group']: g for g in groups}; cases = {}; plans = {}; seen = set()
    authority = launch['data_authority']
    if set(authority) != {'cases', 'source_inputs'}:
        raise ContractError('Only the two prospectively admitted TRAIN streams may be read')
    for label in ('cases', 'source_inputs'):
        descriptor = authority[label]
        if set(descriptor) != {'path', 'sha256', 'fields'} or not descriptor['fields']:
            raise ContractError('Explicit literal row-field authority is required')
        path = Path(descriptor['path']); before = path.stat()
        if str(path) in report['input_sha256'] or before.st_size > 512*1024**2:
            raise ContractError('Duplicate/oversized TRAIN stream')
        digest = hashlib.sha256(); size = count = discarded = 0
        with path.open('rb') as stream:
            while True:
                check(); raw = stream.readline(16*1024**2)
                if not raw:
                    break
                digest.update(raw); size += len(raw); count += 1
                if size > 512*1024**2 or len(raw) == 16*1024**2 and not raw.endswith(b'\n'):
                    raise ContractError('TRAIN byte/line cap exceeded')
                row = json.loads(raw)
                if not isinstance(row, dict) or not isinstance(row.get('base_group'), str):
                    raise ContractError('Top-level group routing key missing')
                group = row['base_group']
                if group not in declared or label == 'source_inputs' and row.get('source') != 'source0':
                    discarded += 1; row = None; continue
                key = (label, group)
                if key in seen:
                    raise ContractError('Duplicate selected case/source0 row')
                seen.add(key)
                if any(k not in row for k in descriptor['fields']):
                    raise ContractError('Selected row missing declared fields')
                row = {k: row[k] for k in descriptor['fields']}
                meta = declared[group]
                if row['base_id'] != meta['base_id'] or type(row['base_id']) is not int:
                    raise ContractError('Selected base join differs')
                if label == 'cases':
                    case = stored_case(row['case'], nr)
                    profile = physical.assignment(meta['base_id'])
                    if (row['split'] != 'train' or row['generator'] != physical.GENERATOR
                            or row['physical_profile'] != profile or len(case.trips) != meta['services']
                            or profile['services'] != meta['services'] or case.identity() != row['case_identity']
                            or len(case.resources) != 1 or case.resources[0] != nr.Resource(0, 1800, 90., 90., 1)
                            or tuple(case.market_edges_min) != tuple(range(0, 1801, 60))):
                        raise ContractError('Original case/profile/numeric identity differs')
                    nr.validate_case(case); cases[group] = case
                else:
                    case = cases[group]; plan = row['source_plan']; flat = [m for v in plan['vehicles'] for m in v['movements']]
                    if (row['case_identity'] != case.identity() or row['market_kind'] != 'source0'
                            or row['market_identity'] != physical.market(case, 'source0').identity()
                            or nr.digest(plan) != row['source_plan_hash'] or plan['case_identity'] != case.identity()
                            or not flat or len(flat) != len(set(flat))
                            or not set(flat) <= {m.id for m in case.movements}):
                        raise ContractError('Original source0 plan/market/membership identity differs')
                    plans[group] = plan
                row = None
        after = path.stat(); actual = digest.hexdigest(); report['input_sha256'][str(path)] = actual
        report['table_streams'][label] = dict(bytes=size, lines=count, routing_discarded=discarded,
            pin_matched=actual == descriptor['sha256'])
        if (actual != descriptor['sha256'] or size != before.st_size or
                (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ContractError('Whole-stream pin/stability differs; no physical admission')
    if set(cases) != set(declared) or set(plans) != set(declared):
        raise ContractError('Selected source0 admission missing; no replacement')
    originals = {}
    for group in declared:
        check(); case, plan = cases[group], plans[group]
        replay = nr.replay_native(case, plan); check()
        if replay.get('replay_ok') is not True:
            raise ContractError('Original source0 replay rejected')
        recovered, _ = pf.recover_paths(case, [m for v in plan['vehicles'] for m in v['movements']])
        if canonical(plan) != canonical({'vehicles': recovered}):
            raise ContractError('Original reference canonical paths differ')
        markets = {target: physical.market(case, target) for target in TARGETS}
        for market in markets.values():
            nh.validate_market(case, market)
        originals[group] = dict(case=case, plan=plan, plan_hash=nr.digest(plan), markets=markets,
            fleet_N=len(plan['vehicles']), components={t: brief(case, plan, replay, m, nh) for t, m in markets.items()})
    report['originals'] = [dict(group=g, base_id=declared[g]['base_id'], services=declared[g]['services'],
        case_identity=o['case'].identity(), original_source0_plan_hash=o['plan_hash'], fleet_N=o['fleet_N'],
        unchanged_target_components=o['components']) for g, o in originals.items()]
    for context in report['contexts']:
        original = originals[context['group']]
        context.update(unchanged_components=original['components'][context['target_source']],
            fleet_N=original['fleet_N'])
    report['preflight_admitted'] = True; check()
    return originals, nr, nh


def launch_worker(task, spec, original, nr, nh):
    global CHILD_PUBLICATION
    folder = HERE/'attempt01'/f"{task['ordinal']:03d}-{task['phase']}"; folder.mkdir(exist_ok=False)
    raw = (json.dumps(spec, indent=2, allow_nan=False)+'\n').encode()
    with (folder/'spec.json').open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    spec_sha = hashlib.sha256(raw).hexdigest()
    save_new(folder/'receipt.json', dict(receipt_complete=False, method_endpoint_accepted=False))
    row = dict(task, attempted=False, reaped=False, parent_endpoint_accepted=False,
        target_common_qualified=False, full_method_success=False, config_failure=False,
        fatal_contract=False, failures=[], folder=str(folder), spec_sha256=spec_sha)
    child = None; cleanup_end = None; endpoint = None; packet = {}
    cpu0, parent0 = child_cpu(), self_cpu(); anchor = time.monotonic(); row['parent_anchor'] = anchor
    with (folder/'stdout.txt').open('x') as out, (folder/'stderr.txt').open('x') as err:
        try:
            if threading.active_count() != 1:
                raise ContractError('Parent must have one Python thread')
            CHILD_PUBLICATION = True
            try:
                child = subprocess.Popen([sys.executable, str(HERE/'worker.py'), '--worker', str(folder),
                    '--parent-anchor', repr(anchor), '--spec-sha256', spec_sha], cwd=ROOT,
                    env=dict(os.environ), stdout=out, stderr=err, start_new_session=True,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (90, 90)))
                row.update(attempted=True, pid=child.pid)
            finally:
                CHILD_PUBLICATION = False
            if PUBLICATION_STOP is not None:
                raise TimeoutError('Stop deferred through owned child publication')
            try:
                child.wait(timeout=max(.001, anchor+60.-time.monotonic()))
            except subprocess.TimeoutExpired:
                row['timed_out'] = True; cleanup_end = time.monotonic()+3.; child.terminate()
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            row.update(returncode=child.returncode, reaped=True)
        except BaseException as exc:
            row['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
            if child is None:
                row['config_failure'] = row['fatal_contract'] = True
            if child is not None and child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3.
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    row.update(returncode=child.returncode, reaped=True)
                except BaseException as exc:
                    row['failures'].append(dict(stage='cleanup', type=type(exc).__name__, message=str(exc)))
    row['process_return_elapsed_s'] = time.monotonic()-anchor
    try:
        packet = json.loads(read_bytes(folder/'receipt.json'))
        keys = ('task_id', 'context_id', 'phase', 'group', 'base_id', 'services', 'target_source')
        if packet.get('receipt_complete') is True and any(packet.get(k) != task[k] for k in keys):
            raise ContractError('Worker task identity differs')
        preliminary = bool(row['reaped'] and row.get('returncode') == 0 and not row.get('timed_out')
            and packet.get('receipt_complete') is True and packet.get('method_endpoint_accepted') is True
            and not any(packet.get(k) for k in ('config_failure', 'fatal_contract', 'identity_failure', 'resource_violation'))
            and not row['failures'] and time.monotonic() < anchor+60.)
        if preliminary:
            artifact = read_bytes(folder/'best-plan.json'); plan = json.loads(artifact)
            replay = nr.replay_native(original['case'], plan)
            if (replay.get('replay_ok') is not True or plan['case_identity'] != original['case'].identity()
                    or len(plan['vehicles']) != original['fleet_N']
                    or task['phase'] == 'target_qp' and canonical(plan) != canonical(original['plan'])):
                raise ContractError('Returned retained U physical/case/fleet admission differs')
            components = brief(original['case'], plan, replay, original['markets'][task['target_source']], nh)
            if components['total_exact'] != packet.get('retained_bill_exact'):
                raise ContractError('Returned retained U exact value differs')
            plan_hash = nr.digest(plan)
            row['owned_retained_artifact'] = dict(path=str(folder/'best-plan.json'),
                bytes_sha256=hashlib.sha256(artifact).hexdigest(), canonical_plan_sha256=plan_hash,
                parent_replay_valid=True, parent_valued_retained_U=True, caller_replayed_fresh_C=False)
            endpoint = dict(plan=plan, plan_hash=plan_hash, components=components)
    except Exception as exc:
        row['config_failure'] = row['fatal_contract'] = True
        row['failures'].append(dict(stage='complete_endpoint_read', type=type(exc).__name__, message=str(exc)))
    end = time.monotonic()
    row.update(worker=packet, complete_endpoint_read_monotonic=end, parent_elapsed_s=end-anchor,
        method_late=end > anchor+60., waited_child_cpu_s=child_cpu()-cpu0,
        parent_cpu_s=self_cpu()-parent0, cpu_observation_complete=child is None or row['reaped'],
        unresolved_cpu_reserve_s=90. if child is not None and not row['reaped'] else 0.)
    for flag in ('config_failure', 'fatal_contract', 'resource_violation', 'identity_failure'):
        row[flag] = bool(row.get(flag) or packet.get(flag))
    accepted = bool(endpoint is not None and not row['method_late'] and not row['failures']
        and not row['config_failure'] and not row['fatal_contract'])
    row['parent_endpoint_accepted'] = accepted
    row['target_common_qualified'] = bool(accepted and task['phase'] == 'target_qp'
        and packet.get('acquisition_qualified') is True)
    row['full_method_success'] = bool(accepted and packet.get('strict_method_success') is True)
    if not accepted:
        endpoint = None
    save_new(folder/'external-receipt.json', row)
    return row, endpoint


def summarize(report):
    values = []; normalized = []; groups = []
    for context in report['contexts']:
        route_worker = context['route_miqp'].get('worker', {})
        context['same_topology_improvement_discrepancy'] = route_worker.get('same_topology_improvement_discrepancy')
        context['optimal_candidate_fallback_discrepancy'] = route_worker.get('optimal_candidate_fallback_discrepancy')
        context['qualification_discrepancies'] = route_worker.get('qualification_discrepancies')
        common = context.get('common_components'); operation = context.get('operational_components')
        defined = common is not None and operation is not None and context.get('common_incumbent_qualified') is True
        gain = Q(common['total_exact'])-Q(operation['total_exact']) if defined else None
        electricity = Q(common['electricity_exact']) if common is not None else None
        ratio = gain/electricity if gain is not None and electricity is not None and electricity > 0 else None
        unchanged = context.get('unchanged_components')
        context.update(economic_comparison_defined=defined, charging_to_routing_gain_exact=gain,
            charging_to_routing_over_target_common_electricity=ratio,
            unchanged_to_target_charging_gain_exact=Q(unchanged['total_exact'])-Q(common['total_exact'])
                if unchanged is not None and common is not None else None,
            target_common_electricity_denominator_exact=electricity,
            negative_retained_gain=bool(gain is not None and gain < 0))
        values.append(gain); normalized.append(ratio)
    for group in report.get('groups', []):
        rows = [r for r in report['contexts'] if r['group'] == group['group']]
        complete = len(rows) == 2 and all(r['economic_comparison_defined'] for r in rows)
        groups.append(dict(group=group['group'], planned_targets=2,
            defined_targets=sum(r['economic_comparison_defined'] for r in rows),
            complete_two_target_mean_gain_exact=sum((r['charging_to_routing_gain_exact'] for r in rows), Q(0))/2 if complete else None))
    return dict(planned_groups=4, planned_contexts=8, planned_workers=16,
        recorded_contexts=len(report['contexts']),
        qualified_common_contexts=sum(r.get('common_incumbent_qualified', False) for r in report['contexts']),
        defined_economic_contexts=sum(v is not None for v in values),
        attempted_workers=sum(r[p].get('attempted', False) for r in report['contexts'] for p in ('target_qp', 'route_miqp')),
        strict_route_method_successes=sum(r['route_miqp'].get('full_method_success', False) for r in report['contexts']),
        complete_eight_context_mean_gain_exact=sum(values, Q(0))/8 if len(values) == 8 and all(v is not None for v in values) else None,
        complete_eight_context_mean_normalized_gain=sum(normalized, Q(0))/8 if len(normalized) == 8 and all(v is not None for v in normalized) else None,
        complete_eight_context_mean_scope='OPERATIONAL delivered paid-pipeline increment; not intrinsic optimal route value or causal attribution',
        same_topology_improvement_discrepancy_contexts=sum(r.get('same_topology_improvement_discrepancy') is True for r in report['contexts']),
        optimal_candidate_fallback_discrepancy_contexts=sum(r.get('optimal_candidate_fallback_discrepancy') is True for r in report['contexts']),
        qualification_discrepancy_contexts=sum(r.get('same_topology_improvement_discrepancy') is True
            or r.get('optimal_candidate_fallback_discrepancy') is True or bool(r.get('qualification_discrepancies')) for r in report['contexts']),
        mean_contains_qualification_discrepancy=any(r.get('same_topology_improvement_discrepancy') is True
            or r.get('optimal_candidate_fallback_discrepancy') is True or bool(r.get('qualification_discrepancies')) for r in report['contexts']),
        group_summaries=groups, available_only_mean=None, statistical_claim=False,
        model_promotion_rule=None, ideal_route_ordering='UNRESOLVED')


def main():
    launch, gate_raw = frozen_launch()  # Before namespace, metadata, imports or data.
    output = HERE/'attempt01'; output.mkdir(exist_ok=False)
    target = output/'receipt.json'; save_new(target, dict(receipt_complete=False, passed=False))
    # Future frozen IDs preserve all planned contexts even if preflight fails.
    pending = launch['cohort_admission']['expected_groups']
    if not isinstance(pending, list) or len(pending) != 4:
        raise SystemExit('Frozen four-group identities are absent')
    report = dict(policy=POLICY, receipt_complete=False, passed=False, config_failure=False,
        failures=[], groups=pending, contexts=tasks(pending), input_sha256={str(HERE/'LAUNCH.json'): hashlib.sha256(gate_raw).hexdigest()},
        table_streams={}, accounting_complete=False, historical_tracking_prefix=launch['tracking_prefix'],
        historical_scope='Separate closed prefix, not charged again to this NEW package; old review CPU UNKNOWN',
        budgets=launch['budgets'], no_automatic_retry=True)
    stopped = None; unresolved = 0.; phase = 'preflight'; final_cpu0 = final_wall0 = None

    def stop(signum, frame):
        global PUBLICATION_STOP
        nonlocal stopped
        stopped = stopped or signum
        if CHILD_PUBLICATION:
            PUBLICATION_STOP = PUBLICATION_STOP or signum; return
        raise TimeoutError('Latched owner stop '+str(signum))

    def check():
        if stopped is not None:
            raise TimeoutError('Owner stop remains latched')
        selection = report.get('selection_resources', launch['cohort_admission']['selection_accounting'])
        prior_cpu, prior_elapsed = float(selection['charged_cpu_s']), float(selection['elapsed_s'])
        if (threading.active_count() != 1 or rss_bytes() > 5*1024**3
                or self_cpu()+child_cpu()+unresolved+prior_cpu > TOTAL_CPU
                or time.monotonic()-WALL0+prior_elapsed > TOTAL_WALL):
            report['config_failure'] = True; raise ContractError('Owner thread/RSS/CPU/wall bound exceeded')
        if phase == 'preflight' and self_cpu()+prior_cpu > 120. or phase == 'finalization' and (
                self_cpu()-final_cpu0 > 120. or time.monotonic()-final_wall0 > 180.):
            report['config_failure'] = True; raise ContractError('Preflight/finalization provision exceeded')

    def funded(workers=1):
        prior = report['selection_resources']
        return (self_cpu()+child_cpu()+unresolved+float(prior['charged_cpu_s'])+90.*workers <= DISPATCH_CPU
            and time.monotonic()-WALL0+float(prior['elapsed_s'])+63.*workers+180. <= TOTAL_WALL)

    try:
        for name in THREAD_ENV:
            os.environ[name] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (120, 2400))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        prior_elapsed = float(launch['cohort_admission']['selection_accounting']['elapsed_s'])
        signal.setitimer(signal.ITIMER_REAL, max(.001, TOTAL_WALL-prior_elapsed-60.-(time.monotonic()-WALL0)))
        originals, nr, nh = preflight(launch, report, check)
        save_new(output/'preflight.json', {k: report[k] for k in ('input_sha256', 'table_streams', 'groups', 'originals', 'preflight_admitted')})
        phase = 'dispatch'; resource.setrlimit(resource.RLIMIT_CPU, (2400, 2400))
        for context in report['contexts']:
            check(); original = originals[context['group']]; market = original['markets'][context['target_source']]
            context['unchanged_components'] = original['components'][context['target_source']]
            context['pipeline_anchor'] = time.monotonic()
            common = None
            for task_phase in ('target_qp', 'route_miqp'):
                task = context[task_phase]
                if task_phase == 'route_miqp' and common is None:
                    task['unattempted_reason'] = 'Missing timely fresh-qualified target-QP common incumbent'; continue
                if not funded(2 if task_phase == 'target_qp' else 1):
                    report['dispatch_stopped_reason'] = 'insufficient_remaining_funding'; break
                input_plan = original['plan'] if task_phase == 'target_qp' else common['plan']
                input_hash = original['plan_hash'] if task_phase == 'target_qp' else common['plan_hash']
                spec = dict(root=str(ROOT), **{k: task[k] for k in ('task_id', 'context_id', 'phase', 'group', 'base_id', 'services', 'target_source')},
                    case=asdict(original['case']), expected_case_identity=original['case'].identity(),
                    fleet_N=original['fleet_N'], expected_market_identity=market.identity(), a=list(market.a), b=list(market.b),
                    input_plan=input_plan, input_plan_sha256=input_hash, original_source0_plan_hash=original['plan_hash'],
                    common_incumbent_qualification=context.get('common_qualification'))
                row, endpoint = launch_worker(task, spec, original, nr, nh); context[task_phase] = row
                unresolved += row['unresolved_cpu_reserve_s']
                if task_phase == 'target_qp' and row['target_common_qualified'] and endpoint is not None:
                    common = endpoint; context['common_components'] = common['components']
                    context['common_incumbent_qualified'] = True
                    context['common_qualification'] = dict(task_id=row['task_id'], parent_endpoint_accepted=True,
                        target_qp_qualified=True, case_identity=original['case'].identity(),
                        target_market_identity=market.identity(), target_source=context['target_source'],
                        fleet_N=original['fleet_N'], retained_bill_exact=common['components']['total_exact'],
                        input_plan_sha256=common['plan_hash'],
                        helper_retained_used_fallback=row['worker'].get('used_fallback'), caller_replayed_fresh_C=False)
                    context['operational_components'] = common['components']; context['operational_source'] = 'qualified_target_common_incumbent'
                if task_phase == 'route_miqp' and endpoint is not None:
                    if Q(endpoint['components']['total_exact']) > Q(common['components']['total_exact']):
                        report['config_failure'] = True
                        raise ContractError('Route endpoint worsens protected common incumbent')
                    context['operational_components'] = endpoint['components']; context['operational_source'] = 'accepted_route_worker'
                if row['config_failure'] or row['fatal_contract'] or unresolved:
                    report['config_failure'] = True; report['dispatch_stopped_reason'] = 'fatal_contract_or_unresolved_child'; break
                check()
            context['pipeline_complete_monotonic'] = time.monotonic()
            context['pipeline_elapsed_s'] = context['pipeline_complete_monotonic']-context['pipeline_anchor']
            context['pipeline_scope'] = 'QP startup through transition, route endpoint and cleanup; two paid worker anchors, not a single60-second method'
            if report['config_failure'] or report.get('dispatch_stopped_reason'):
                break
    except BaseException as exc:
        report['config_failure'] = True
        report['failures'].append(dict(stage=phase, type=type(exc).__name__, message=str(exc)))
    finally:
        phase = 'finalization'; final_cpu0 = self_cpu(); final_wall0 = time.monotonic()
        prior = launch['cohort_admission']['selection_accounting']
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(180., TOTAL_WALL-float(prior['elapsed_s'])-(final_wall0-WALL0))))
        try:
            for context in report['contexts']:
                if 'pipeline_anchor' in context and 'pipeline_complete_monotonic' not in context:
                    context['pipeline_complete_monotonic'] = time.monotonic()
                    context['pipeline_elapsed_s'] = context['pipeline_complete_monotonic']-context['pipeline_anchor']
                    context['pipeline_scope'] = 'Aborted paid context through owner failure/cleanup; no missing stage declared successful'
                for p in ('target_qp', 'route_miqp'):
                    if not context[p].get('attempted'):
                        context[p].setdefault('unattempted_reason', report.get('dispatch_stopped_reason', 'owner_or_prerequisite_failure'))
            report['summary'] = summarize(report); check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='finalization', type=type(exc).__name__, message=str(exc)))
        ledger = [r[p] for r in report['contexts'] for p in ('target_qp', 'route_miqp')]
        report.update(receipt_complete=True, accounting_complete=unresolved == 0,
            ledger=ledger, unresolved_cpu_reserve_s=unresolved,
            ledger_complete=len(report['contexts']) == 8 and len(ledger) == 16 and len({r['task_id'] for r in ledger}) == 16,
            resources=dict(self_cpu_s=self_cpu(), waited_children_cpu_s=child_cpu(), combined_cpu_s=self_cpu()+child_cpu(),
                selection_charge_s=float(prior['charged_cpu_s']),
                package_cpu_before_publication_s=self_cpu()+child_cpu()+float(prior['charged_cpu_s']),
                package_elapsed_sum_before_publication_s=time.monotonic()-WALL0+float(prior['elapsed_s']),
                observed_self_peak_rss_bytes=rss_bytes(), prepublication_only=True, external_tail_acceptance_pending=True),
            elapsed_before_publication_s=time.monotonic()-WALL0, stop_signal=stopped,
            passed_scope='Administrative planned-ledger/accounting closure, not complete economic comparisons or method success')
        try:
            check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='final_resource_observation', type=type(exc).__name__, message=str(exc)))
        report['passed'] = bool(not report['config_failure'] and not report['failures'] and report['accounting_complete']
            and report['ledger_complete'] and stopped is None)
        remaining = min(180.-(time.monotonic()-final_wall0), TOTAL_WALL-float(prior['elapsed_s'])-(time.monotonic()-WALL0))
        if remaining <= 0:
            raise TimeoutError('No finalization/total wall remains for publication')
        signal.setitimer(signal.ITIMER_REAL, remaining); publish(target, report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
