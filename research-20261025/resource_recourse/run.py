"""DRAFT serial resource-recourse owner; a frozen PASS launch is mandatory."""
import time
WALL0 = time.monotonic()
from copy import deepcopy
from dataclasses import asdict, replace
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
HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
POLICY = 'one-grid-axis-fixed-fleet-conventional-recourse-v1'
GROUPS = ((10001, 20, 'different_membership'), (10006, 20, 'same_membership'),
          (10009, 28, 'different_membership'), (10005, 28, 'same_membership'))
GRIDS, SOURCES = (90., 45.), ('source0', 'source1')
TOTAL_CPU, TOTAL_WALL, DISPATCH_CPU = 4500., 7200., 4140.
CHILD_PUBLICATION, PUBLICATION_STOP = False, None
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
TABLES = {
    'cases': (Path('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl'),
              'faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6'),
    'sources': (Path('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl'),
                '7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5')}
SOURCE_FILES = ('research-20261025/resource_recourse/run.py',
    'research-20261025/resource_recourse/worker.py', 'research-20261025/resource_recourse/classical.py',
    'research-20261025/topology_charging/worker.py',
    'research-20261025/warm_replication/qp_control.py', 'src/egglab/__init__.py',
    'src/egglab/native_recharge.py', 'src/egglab/native_hull.py',
    'src/egglab/native_pathflow.py', 'src/egglab/physical_learning_cases.py')


class ContractError(ValueError):
    pass


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
                  default=lambda value: str(value) if isinstance(value, Q) else value)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path); temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value); os.replace(temporary, path)


def self_cpu():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime+usage.ru_stime


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime+usage.ru_stime


def rss_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == 'darwin' else raw*1024)


def resource_receipt():
    return dict(self_cpu_s=self_cpu(), waited_children_cpu_s=children_cpu(),
        combined_cpu_s=self_cpu()+children_cpu(), observed_self_peak_rss_bytes=rss_bytes(),
        scope='Before final publication; external owner meter includes waited children and write/exit tail')


def read_bytes(path, cap=8*1024**2):
    before = path.stat()
    if before.st_size > cap:
        raise ContractError('Owned metadata/artifact/source exceeds cap')
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ContractError('Frozen input changed during bounded read')
    return raw


def bind_file(path, report):
    if str(path) in report['input_sha256']:
        raise ContractError('Duplicate source/input admission')
    raw = read_bytes(path)
    report['input_sha256'][str(path)] = hashlib.sha256(raw).hexdigest()
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
    service_energy = sum((nh.rational(t.energy_kwh) for t in case.trips), Q(0))
    movement_energy = sum((nh.rational(leg.energy_kwh) for v in plan['vehicles']
        for mid in v['movements'] for leg in modes[mid].legs), Q(0))
    ideal_grid = (service_energy+movement_energy)/nh.rational(case.efficiency)
    return dict(replay_ok=True, fleet_count=len(plan['vehicles']), vehicle_cost_exact=str(fleet),
        deadhead_minutes_exact=str(minutes), deadhead_cost_exact=str(deadhead), ops_cost_exact=str(ops),
        ops_component_residual_exact=str(ops-fleet-deadhead), linear_electricity_exact=str(linear),
        quadratic_electricity_exact=str(quadratic), electricity_exact=str(linear+quadratic),
        total_exact=str(ops+nh.supply(market, replay['load'])),
        grid_kwh_exact=str(nh.rational(replay['grid_kwh'])),
        consumption_kwh_exact=str(nh.rational(replay['consumption_kwh'])),
        service_energy_exact=str(service_energy), movement_energy_exact=str(movement_energy),
        ideal_grid_demand_exact=str(ideal_grid), replay_grid_minus_ideal_exact=str(nh.rational(replay['grid_kwh'])-ideal_grid),
        max_grid_kw=replay['max_grid_kw'], period_loads=list(replay['load']),
        units='generator cost units; kWh; movement-leg minutes')


def tasks():
    acquisitions, decisions = [], []
    for group_index, (base, services, stratum) in enumerate(GROUPS):
        # Counterbalance resource order; retain one fixed ordinal assignment list.
        for grid in (GRIDS if group_index % 2 == 0 else GRIDS[::-1]):
            identity = dict(group=f'physical_v2_s{base}', base_id=base, services=services, grid_kw=grid)
            acquisitions.append(dict(identity, ordinal=len(acquisitions)+1,
                task_id=f'A{len(acquisitions)+1:03d}-g{base}-p{int(grid)}', phase='acquisition', target_source=None))
            for target in SOURCES:
                order = ('fixed', 'adaptive') if (len(decisions)//2) % 2 == 0 else ('adaptive', 'fixed')
                for arm in order:
                    decisions.append(dict(identity, ordinal=8+len(decisions)+1,
                        task_id=f'D{len(decisions)+1:03d}-g{base}-p{int(grid)}-t{target}-{arm}',
                        phase=arm, target_source=target))
    return acquisitions, decisions


def preflight(report, check):
    for path in (ROOT/'research-20261025/route_resource_mechanism/STUDY_DECISION.md', HERE/'PROTOCOL.md'):
        check(); bind_file(path, report)
    for name in SOURCE_FILES:
        check(); bind_file(ROOT/name, report)
    import importlib.util
    classical_spec = importlib.util.spec_from_file_location('resource_recourse_owner_classical', HERE/'classical.py')
    classical = importlib.util.module_from_spec(classical_spec)
    classical_spec.loader.exec_module(classical)
    sys.path.insert(0, str(ROOT/'src'))
    import egglab
    from egglab import native_recharge as nr, native_hull as nh, native_pathflow as pf, physical_learning_cases as physical
    for module, name in ((egglab, '__init__.py'), (nr, 'native_recharge.py'), (nh, 'native_hull.py'),
                         (pf, 'native_pathflow.py'), (physical, 'physical_learning_cases.py')):
        if Path(module.__file__).resolve() != ROOT/'src'/'egglab'/name:
            raise ContractError('Paid project import path differs')
    declared = {f'physical_v2_s{b}': (b, n, s) for b, n, s in GROUPS}
    cases, original_plans, originals = {}, {}, {}
    seen_cases, seen_sources = set(), set()

    def case_row(row, group):
        if group in seen_cases:
            raise ContractError('Duplicate selected case')
        seen_cases.add(group); base, services, _ = declared[group]
        profile = physical.assignment(base)
        case = stored_case(row['case'], nr)
        if (type(row['base_id']) is not int or row['base_id'] != base or row['split'] != 'train'
                or row['generator'] != physical.GENERATOR or row['physical_profile'] != profile
                or case.identity() != row['case_identity'] or len(case.trips) != services
                or profile['services'] != services or len(case.resources) != 1
                or case.resources[0] != nr.Resource(0, 1800, 90.0, 90.0, 1)
                or tuple(case.market_edges_min) != tuple(range(0, 1801, 60))):
            raise ContractError('Selected original case/profile/resource identity differs')
        nr.validate_case(case); cases[group] = case

    def source_row(row, group):
        if group in seen_sources:
            raise ContractError('Duplicate selected source0')
        seen_sources.add(group); case = cases[group]
        if (type(row['base_id']) is not int or row['base_id'] != declared[group][0]
                or row['case_identity'] != case.identity() or row['market_kind'] != 'source0'
                or row['market_identity'] != physical.market(case, 'source0').identity()):
            raise ContractError('Selected source0 joins/market identity differ')
        plan = row['source_plan']; flat = [mid for v in plan['vehicles'] for mid in v['movements']]
        if (nr.digest(plan) != row['source_plan_hash'] or plan['case_identity'] != case.identity()
                or not flat or any(not isinstance(mid, str) for mid in flat)
                or len(flat) != len(set(flat)) or row['selected_movements'] != sorted(flat)
                or not set(flat) <= {m.id for m in case.movements}):
            raise ContractError('Original source0 plan/membership identity differs')
        original_plans[group] = plan
        originals[group] = dict(original_source0_plan_hash=row['source_plan_hash'], reference_selected_ids=flat)

    for label, handler in (('cases', case_row), ('sources', source_row)):
        path, pin = TABLES[label]; before = path.stat()
        if before.st_size > 512*1024**2:
            raise ContractError('TRAIN table exceeds512MiB')
        digest = hashlib.sha256(); size = lines = discarded = 0
        with path.open('rb') as stream:
            while True:
                check(); raw = stream.readline(16*1024**2)
                if not raw:
                    break
                digest.update(raw); size += len(raw); lines += 1
                if size > 512*1024**2 or (len(raw) == 16*1024**2 and not raw.endswith(b'\n') and size < before.st_size):
                    raise ContractError('TRAIN byte/line cap exceeded')
                try:
                    row = json.loads(raw)
                    if not isinstance(row, dict) or not isinstance(row.get('base_group'), str):
                        raise ContractError('Missing top-level routing group')
                    group = row['base_group']
                    if group not in declared or label == 'sources' and row.get('source') != 'source0':
                        discarded += 1; row = None; continue
                    handler(row, group)
                except (ValueError, TypeError, KeyError, OverflowError) as exc:
                    report['findings'].append(dict(table=label, line=lines, type=type(exc).__name__, message=str(exc)))
                row = None
        actual = digest.hexdigest(); after = path.stat()
        report['input_sha256'][str(path)] = actual
        report['table_streams'][label] = dict(bytes=size, lines=lines, routing_discarded=discarded, pin_matched=actual == pin)
        if (actual != pin or size != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ContractError('Whole TRAIN table pin/stability differs')
    if report['findings'] or set(cases) != set(declared) or set(original_plans) != set(declared):
        raise ContractError('Four selected case/source0 records not admitted; no replacement')
    for group, case in cases.items():
        check(); plan = original_plans[group]; replay = nr.replay_native(case, plan); check()
        if replay.get('replay_ok') is not True:
            raise ContractError('Original source0 independent replay rejected')
        recovered, _ = pf.recover_paths(case, originals[group]['reference_selected_ids'])
        if canonical({'vehicles': recovered}) != canonical(plan):
            raise ContractError('Original reference does not equal unique recovered paths')
        original_markets = [physical.market(case, s) for s in SOURCES]
        for market in original_markets:
            nh.validate_market(case, market)
        electricity = [nh.supply(market, replay['load']) for market in original_markets]
        e_ref = sum(electricity, Q(0))/2
        originals[group].update(fleet_N=len(plan['vehicles']), E_ref_exact=str(e_ref) if e_ref > 0 else None,
            original_case_identity=case.identity(), original_source0_replay_valid=True)
    variants = {}
    for group, case in cases.items():
        for grid in GRIDS:
            check(); variant = replace(case, name=case.name+f'-resource-grid-{int(grid)}',
                resources=tuple(replace(r, grid_kw=grid) for r in case.resources))
            nr.validate_case(variant)
            markets = {s: physical.market(variant, s) for s in SOURCES}
            for market in markets.values():
                nh.validate_market(variant, market)
            reference = dict(valid=False, comparison_role='no-solve only; never a fallback', bills={}, components={})
            probe = deepcopy(original_plans[group]); probe['case_identity'] = variant.identity()
            try:
                replay = nr.replay_native(variant, probe)
                if replay.get('replay_ok') is not True:
                    raise ValueError('Counterfactual original witness not admitted')
                reference.update(valid=True, derived_plan_hash=nr.digest(probe))
                for source, market in markets.items():
                    reference['components'][source] = brief(variant, probe, replay, market, nh)
                    reference['bills'][source] = reference['components'][source]['total_exact']
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                reference.update(valid=False, bills={}, components={})
                reference['rejection'] = dict(type=type(exc).__name__, message=str(exc))
            check()
            variants[(group, grid)] = dict(case=variant, raw_case=asdict(variant), markets=markets,
                original=originals[group], reference=reference,
                opportunity_diagnostics=classical.opportunity(variant, original_plans[group], nh))
    report['originals'] = [dict(group=g,
        **{k: value for k, value in originals[g].items() if k != 'reference_selected_ids'},
        reference_movement_count=len(originals[g]['reference_selected_ids'])) for g in declared]
    report['variants'] = [dict(group=g, grid_kw=p, case_identity=v['case'].identity(),
        original_reference=v['reference'], opportunity_diagnostics=v['opportunity_diagnostics'])
        for (g, p), v in variants.items()]
    report['preflight_admitted'] = True; check()
    return variants, nr, nh, pf


def launch_worker(task, spec, variant, nr, nh, pf):
    global CHILD_PUBLICATION
    folder = HERE/'attempt01'/f"{task['ordinal']:03d}-{task['phase']}"
    folder.mkdir(exist_ok=False)
    raw = (json.dumps(spec, indent=2, allow_nan=False)+'\n').encode()
    with (folder/'spec.json').open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    spec_sha = hashlib.sha256(raw).hexdigest()
    save_new(folder/'receipt.json', dict(receipt_complete=False, method_endpoint_accepted=False))
    record = dict(task, attempted=False, reaped=False, parent_endpoint_accepted=False,
        cell_qualified=False, full_method_success=False, physical_new_prior_valid=False,
        config_failure=False, fatal_contract=False, failures=[], folder=str(folder), spec_sha256=spec_sha)
    child = None; cleanup_end = None; acquired = None
    before_child, before_self = children_cpu(), self_cpu(); anchor = time.monotonic()
    record['parent_anchor'] = anchor
    with (folder/'stdout.txt').open('x') as stdout, (folder/'stderr.txt').open('x') as stderr:
        try:
            if threading.active_count() != 1:
                raise ContractError('Parent must have one Python thread before fork')
            CHILD_PUBLICATION = True
            try:
                child = subprocess.Popen([sys.executable, str(HERE/'worker.py'), '--worker', str(folder),
                    '--parent-anchor', repr(anchor), '--spec-sha256', spec_sha], cwd=ROOT,
                    env=dict(os.environ), stdout=stdout, stderr=stderr, start_new_session=True,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (90, 90)))
                record.update(attempted=True, pid=child.pid)
            finally:
                CHILD_PUBLICATION = False
            if PUBLICATION_STOP is not None:
                raise TimeoutError('Stop deferred through owned child publication')
            try:
                child.wait(timeout=max(.001, anchor+60.-time.monotonic()))
            except subprocess.TimeoutExpired:
                record['timed_out'] = True; cleanup_end = time.monotonic()+3.; child.terminate()
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            record.update(returncode=child.returncode, reaped=True)
        except BaseException as exc:
            record['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
            if child is None:
                record['config_failure'] = record['fatal_contract'] = True
            if child is not None and child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3.
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    record.update(returncode=child.returncode, reaped=True)
                except BaseException as secondary:
                    record['failures'].append(dict(type=type(secondary).__name__, message=str(secondary)))
    record['process_return_elapsed_s'] = time.monotonic()-anchor
    try:
        packet = json.loads(read_bytes(folder/'receipt.json'))
        if any(packet.get(k) != task[k] for k in ('task_id', 'phase', 'group', 'base_id', 'services', 'grid_kw', 'target_source')):
            raise ContractError('Worker receipt task identity differs')
        if (task['phase'] == 'acquisition' and packet.get('physical_new_prior_valid') is True
                and packet.get('method_endpoint_accepted') is True and record['reaped']
                and record.get('returncode') == 0 and not record.get('timed_out')
                and time.monotonic() < anchor+60.):
            artifact = read_bytes(folder/'best-plan.json'); plan = json.loads(artifact)
            case = variant['case']; replay = nr.replay_native(case, plan)
            fixed, _ = pf.recover_paths(case, spec['reference_selected_ids'])
            if (replay.get('replay_ok') is not True or plan['case_identity'] != case.identity()
                    or len(plan['vehicles']) != spec['fleet_N'] or canonical(plan) != canonical({'vehicles': fixed})):
                raise ContractError('New acquisition artifact changed fixed paths/fleet/physics')
            plan_hash = nr.digest(plan)
            record['owned_prior_artifact'] = dict(path=str(folder/'best-plan.json'),
                bytes_sha256=hashlib.sha256(artifact).hexdigest(), canonical_plan_sha256=plan_hash,
                parent_replay_valid=True)
            acquired = dict(plan=plan, replay=replay, plan_hash=plan_hash,
                components={s: brief(case, plan, replay, m, nh) for s, m in variant['markets'].items()})
    except Exception as exc:
        packet = dict(receipt_complete=False)
        record['failures'].append(dict(stage='complete_endpoint_read', type=type(exc).__name__, message=str(exc)))
        record['config_failure'] = record['fatal_contract'] = True
    record.update(complete_endpoint_read_monotonic=time.monotonic(), worker=packet,
        waited_child_cpu_s=children_cpu()-before_child, parent_cpu_s=self_cpu()-before_self,
        cpu_observation_complete=child is None or record['reaped'],
        unresolved_cpu_reserve_s=90. if child is not None and not record['reaped'] else 0.)
    record['parent_elapsed_s'] = record['complete_endpoint_read_monotonic']-anchor
    record['method_late'] = record['parent_elapsed_s'] > 60.
    for flag in ('config_failure', 'fatal_contract', 'resource_violation', 'identity_failure'):
        record[flag] = bool(record.get(flag) or packet.get(flag))
    accepted = bool(record['reaped'] and record.get('returncode') == 0 and not record.get('timed_out')
        and not record['failures'] and not record['fatal_contract'] and not record['config_failure']
        and packet.get('receipt_complete') is True and packet.get('method_endpoint_accepted') is True
        and record['parent_elapsed_s'] <= 60.)
    record.update(parent_endpoint_accepted=accepted,
        physical_new_prior_valid=bool(accepted and acquired is not None),
        cell_qualified=bool(accepted and packet.get('cell_qualified') is True),
        full_method_success=bool(accepted and packet.get('full_method_success') is True))
    if not record['physical_new_prior_valid']:
        acquired = None
    save_new(folder/'external-receipt.json', record)
    return record, acquired


def operational(row, prior, target):
    packet = row.get('worker', {})
    if (row.get('parent_endpoint_accepted') and packet.get('physical_witness_valid') is True
            and packet.get('retained_bill_exact') is not None):
        row.update(operational_bill_exact=packet['retained_bill_exact'],
            operational_components=packet.get('selected_decomposition'), operational_source='accepted_worker',
            retained_route_changed_from_reference=packet.get('retained_route_changed_from_reference'))
    elif prior is not None:
        row.update(operational_bill_exact=prior['components'][target]['total_exact'],
            operational_components=prior['components'][target], operational_source='acquired_prior_fallback',
            retained_route_changed_from_reference=False)
    else:
        row.update(operational_bill_exact=None, operational_components=None, operational_source='missing_no_acquired_prior',
            retained_route_changed_from_reference=None)
    row['operational_endpoint_available'] = row['operational_bill_exact'] is not None


def readout(report):
    groups, interactions = [], []
    for base, services, stratum in GROUPS:
        group = f'physical_v2_s{base}'; levels = {}
        e_ref = next((r['E_ref_exact'] for r in report.get('originals', []) if r['group'] == group), None)
        for grid in GRIDS:
            for target in SOURCES:
                rows = {r['phase']: r for r in report['decisions'] if r['group'] == group
                    and r['grid_kw'] == grid and r['target_source'] == target}
                defined = len(rows) == 2 and all(r.get('operational_bill_exact') is not None for r in rows.values())
                gain = Q(rows['fixed']['operational_bill_exact'])-Q(rows['adaptive']['operational_bill_exact']) if defined else None
                levels[(grid, target)] = dict(grid_kw=grid, target_source=target, defined=defined,
                    adaptive_gain_fixed_minus_adaptive=gain,
                    adaptive_gain_over_fixed_E_ref=gain/Q(e_ref) if gain is not None and e_ref is not None and Q(e_ref) > 0 else None,
                    methods={p: {k: r.get(k) for k in ('attempted', 'parent_endpoint_accepted', 'cell_qualified',
                        'full_method_success', 'operational_source', 'operational_bill_exact', 'operational_components',
                        'retained_route_changed_from_reference')}
                        for p, r in rows.items()})
        paired = []
        for target in SOURCES:
            baseline, constrained = levels[(90., target)], levels[(45., target)]
            value = constrained['adaptive_gain_fixed_minus_adaptive']-baseline['adaptive_gain_fixed_minus_adaptive'] if baseline['defined'] and constrained['defined'] else None
            paired.append(dict(target_source=target, defined=value is not None,
                resource_interaction_gain45_minus_gain90=value,
                interaction_over_fixed_E_ref=value/Q(e_ref) if value is not None and e_ref is not None and Q(e_ref) > 0 else None))
            interactions.append(value)
        groups.append(dict(group=group, services=services, declared_prior_stratum=stratum, E_ref_exact=e_ref,
            levels=list(levels.values()), interactions=paired,
            complete_two_tariff_mean_interaction=sum((r['resource_interaction_gain45_minus_gain90'] for r in paired), Q(0))/2 if all(r['defined'] for r in paired) else None))
    return dict(groups=groups, planned_groups=4, planned_acquisitions=8, planned_active=32,
        attempted_acquisitions=sum(r.get('attempted', False) for r in report['acquisitions']),
        valid_new_priors=sum(r.get('physical_new_prior_valid', False) for r in report['acquisitions']),
        attempted_active=sum(r.get('attempted', False) for r in report['decisions']),
        qualified_QP_cells=sum(r.get('cell_qualified', False) for r in report['decisions']),
        full_method_successes=sum(r.get('full_method_success', False) for r in report['decisions']),
        operational_active_defined=sum(r.get('operational_endpoint_available', False) for r in report['decisions']),
        planned_interactions=8, defined_interactions=sum(v is not None for v in interactions),
        complete_eight_interaction_mean=sum(interactions, Q(0))/8 if all(v is not None for v in interactions) else None,
        available_only_mean=None, ideal_route_ordering='UNRESOLVED', statistical_or_model_promotion_gate=False)


def main():
    if HERE != ROOT/'research-20261025/resource_recourse':
        raise SystemExit('Wrong source namespace')
    # Metadata-only failclosed gate, BEFORE original inputs, imports or any job.
    gate_raw = read_bytes(HERE/'LAUNCH.json'); launch = json.loads(gate_raw)
    if (launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS'
            or Path(launch.get('workdir', '')) != ROOT):
        raise SystemExit('DRAFT: no frozen PASS launch; no original inputs or jobs admitted')
    acquisitions, decisions = tasks()
    if launch.get('acquisitions') != acquisitions or launch.get('decisions') != decisions:
        raise SystemExit('Frozen launch assignments differ; no data or jobs admitted')
    expected_budget = dict(total_cpu_s=4500, total_wall_s=7200, dispatch_cpu_s=4140,
        closure_cpu_s=360, preflight_cpu_s=120, finalization_cpu_s=120, finalization_wall_s=180,
        child_hard_cpu_s=90, parent_endpoint_s=60, native_s=52, routing_first_native_s=17.5,
        routing_second_native_s=35, cleanup_s=3, threads=1, observed_worker_rss_bytes=5*1024**3)
    if launch.get('budgets') != expected_budget:
        raise SystemExit('Frozen launch resources differ; no data or jobs admitted')
    output = HERE/'attempt01'; output.mkdir(exist_ok=False)
    target = output/'receipt.json'; save_new(target, dict(receipt_complete=False, passed=False))
    report = dict(policy=POLICY, receipt_complete=False, passed=False, config_failure=False,
        failures=[], findings=[], input_sha256={str(HERE/'LAUNCH.json'): hashlib.sha256(gate_raw).hexdigest()},
        table_streams={}, originals=[], variants=[], acquisitions=[dict(t, attempted=False) for t in acquisitions],
        decisions=[dict(t, attempted=False) for t in decisions], accounting_complete=False,
        budgets=dict(cpu_s=4500, wall_s=7200, dispatch_cpu_s=4140, closure_cpu_s=360,
            preflight_cpu_s=120, finalization_cpu_s=120, finalization_wall_s=180),
        historical_accounting='Separate closed prefix; no refund/reset or historical charge added to this NEW package')
    stopped = None; unresolved = 0.; phase = 'preflight'; final_cpu0 = final_wall0 = None
    variants = {}; acquired = {}

    def stop(signum, frame):
        global PUBLICATION_STOP
        nonlocal stopped
        stopped = stopped or signum
        if CHILD_PUBLICATION:
            PUBLICATION_STOP = PUBLICATION_STOP or signum
            return
        raise TimeoutError('Latched owner stop '+str(signum))

    def check():
        if stopped is not None:
            raise TimeoutError('Owner stop remains latched')
        if (threading.active_count() != 1 or rss_bytes() > 5*1024**3
                or self_cpu()+children_cpu()+unresolved > TOTAL_CPU or time.monotonic()-WALL0 > TOTAL_WALL):
            report['config_failure'] = True
            raise ContractError('Package thread/RSS/CPU/wall resource contract exceeded')
        if phase == 'preflight' and self_cpu() > 120. or phase == 'finalization' and (
                self_cpu()-final_cpu0 > 120. or time.monotonic()-final_wall0 > 180.):
            report['config_failure'] = True
            raise ContractError('Preflight/finalization provision exceeded')

    def funded():
        return self_cpu()+children_cpu()+unresolved+90. <= DISPATCH_CPU and time.monotonic()-WALL0+63.+180. <= TOTAL_WALL

    try:
        for name in THREAD_ENV:
            os.environ[name] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (120, 4500))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, TOTAL_WALL-60.-(time.monotonic()-WALL0)))
        variants, nr, nh, pf = preflight(report, check)
        save_new(output/'preflight.json', {k: report[k] for k in ('input_sha256', 'table_streams', 'originals', 'variants', 'preflight_admitted')})
        phase = 'dispatch'; resource.setrlimit(resource.RLIMIT_CPU, (4500, 4500))
        for rows in (report['acquisitions'], report['decisions']):
            for position, task in enumerate(list(rows)):
                check(); key = (task['group'], task['grid_kw']); variant = variants[key]
                prior = acquired.get(key)
                if task['phase'] == 'fixed' and prior is None:
                    rows[position] = dict(task, missing_reference=True, unattempted_reason='Fresh reference acquisition unavailable')
                    continue
                if not funded():
                    report['dispatch_stopped_reason'] = 'insufficient_remaining_funding'; break
                meta = variant['original']; market = variant['markets'].get(task['target_source'])
                spec = dict(root=str(ROOT), **{k: task[k] for k in ('task_id', 'phase', 'group', 'base_id', 'services', 'grid_kw', 'target_source')},
                    case=variant['raw_case'], expected_case_identity=variant['case'].identity(), fleet_N=meta['fleet_N'],
                    reference_selected_ids=meta['reference_selected_ids'], original_source0_plan_hash=meta['original_source0_plan_hash'],
                    acquisition_plan=prior['plan'] if prior is not None else None,
                    acquisition_plan_sha256=prior['plan_hash'] if prior is not None else None,
                    expected_market_identity=market.identity() if market is not None else None,
                    a=list(market.a) if market is not None else None, b=list(market.b) if market is not None else None,
                    E_ref_exact=meta['E_ref_exact'],
                    original_reference_bill_exact=variant['reference']['bills'].get(task['target_source']))
                record, new_prior = launch_worker(task, spec, variant, nr, nh, pf)
                rows[position] = record; unresolved += record['unresolved_cpu_reserve_s']
                if task['phase'] == 'acquisition' and new_prior is not None:
                    acquired[key] = new_prior
                    record['new_prior_components'] = new_prior['components']
                if record['config_failure'] or record['fatal_contract'] or unresolved:
                    report['config_failure'] = True; report['dispatch_stopped_reason'] = 'fatal_contract_or_unresolved_child'; break
                check()
            if report['config_failure'] or report.get('dispatch_stopped_reason'):
                break
    except BaseException as exc:
        report['config_failure'] = True
        report['failures'].append(dict(stage=phase, type=type(exc).__name__, message=str(exc)))
    finally:
        phase = 'finalization'; final_cpu0 = self_cpu(); final_wall0 = time.monotonic()
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(180., TOTAL_WALL-(final_wall0-WALL0))))
        try:
            for row in report['acquisitions']+report['decisions']:
                if not row.get('attempted'):
                    row.setdefault('unattempted_reason', report.get('dispatch_stopped_reason', 'owner_or_preflight_failure'))
            for row in report['decisions']:
                operational(row, acquired.get((row['group'], row['grid_kw'])), row['target_source'])
            report['summary'] = readout(report); check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='finalization', type=type(exc).__name__, message=str(exc)))
        report.update(ledger=report['acquisitions']+report['decisions'], receipt_complete=True,
            ledger_complete=len(report['acquisitions']) == 8 and len(report['decisions']) == 32,
            all40_assignments_attempted=all(r.get('attempted') for r in report['acquisitions']+report['decisions']),
            resources=resource_receipt(), unresolved_cpu_reserve_s=unresolved, accounting_complete=unresolved == 0,
            elapsed_before_publication_s=time.monotonic()-WALL0, stop_signal=stopped,
            passed_scope='Administrative ledger/accounting closure, not all priors/methods/QPs qualified',
            no_automatic_retry=True, no_model_promotion_gate=True)
        try:
            check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='final_resource_observation', type=type(exc).__name__, message=str(exc)))
        report['passed'] = bool(not report['config_failure'] and not report['failures']
            and report['accounting_complete'] and report['ledger_complete'] and stopped is None)
        remaining = min(180.-(time.monotonic()-final_wall0), TOTAL_WALL-(time.monotonic()-WALL0))
        if remaining <= 0:
            raise TimeoutError('No finalization/total wall remains for publication')
        signal.setitimer(signal.ITIMER_REAL, remaining); publish(target, report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
