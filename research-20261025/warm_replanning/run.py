"""One prospective warm-replanning campaign; fresh, paid worker per decision.

Static preparation only until the parent freezes protocol/source/command.
No attempt resume, retry, secondary cohort or unmetered verification path.
"""
import time

PROCESS_WALL0 = time.monotonic()

import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
for _name in THREAD_ENV:
    os.environ[_name] = '1'

POLICY = 'warm-day-to-late-fixed-fleet-fresh-worker-v1'
ARMS = ('GNN', 'CatBoost', 'CA1', 'CoverCA1', 'random', 'full', 'fixed_route')
GROUPS = (50600, 50601, 50602, 50603)
SEEDS = (17, 41, 73)
TOTAL_CPU, TOTAL_WALL, DISPATCH_CPU = 14400., 18000., 13800.
FINAL_CPU, FINAL_WALL = 120., 180.
SOURCE_FILES = (
    'research-20261025/warm_replanning/run.py',
    'research-20261025/warm_replanning/scoring.py',
    'research-20261025/warm_replanning/planner.py',
    'research-20261025/warm_replanning/finalize.py',
    'research-20261025/matching_pool/pool.py',
    'src/egglab/__init__.py', 'src/egglab/claude_cases.py',
    'src/egglab/claude_scale_cases.py', 'src/egglab/physical_learning_cases.py',
    'src/egglab/native_recharge.py', 'src/egglab/native_pathflow.py',
    'src/egglab/native_hull.py', 'src/egglab/native_pathflow_hull.py',
    'src/egglab/classical_controls.py', 'src/egglab/learned_proposals.py',
    'src/egglab/physical_route_graph_v6.py', 'src/egglab/physical_route_model_v2.py',
    'src/egglab/physical_route_model_v3.py', 'src/egglab/physical_route_model_families_v5.py',
    'src/experiments/codex_local_campaign.py', 'src/experiments/codex_train_classical.py',
    'src/experiments/codex_offline_rank.py', 'src/experiments/computational_benchmark.py',
    'src/experiments/pool_physical_route_training.py',
    'src/experiments/pool_physical_route_training_v3.py',
    'src/experiments/native_recharge_qualification.py',
    'src/experiments/native_pathflow_qualification.py',
    'src/experiments/native_halfminute_qualification.py',
    'src/experiments/sistig_native_case.py',
)
INPUT_FILES = (
    'research-20261025/warm_replanning/GROUP_MANIFEST.json',
    'research-20261025/warm_replanning/PROTOCOL.md',
    'research-20261017/local-assets-v3.json',
    'research-20261025/warm_replanning/RESOURCE_DECISION.md',
    'research-20261025/warm_replanning/LAUNCH.json',
)


class ConfigurationFailure(ValueError):
    pass


class IdentityFailure(ConfigurationFailure):
    pass


class ResourceViolation(RuntimeError):
    pass


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
                  default=lambda x: str(x) if isinstance(x, Fraction) else x)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value)
    os.replace(temporary, path)  # Only our exclusive incomplete placeholder.


def load(path):
    with Path(path).open() as stream:
        return json.load(stream)


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
    own, child = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(self_cpu_s=own.ru_utime+own.ru_stime,
        waited_children_cpu_s=child.ru_utime+child.ru_stime,
        combined_cpu_s=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime,
        observed_self_peak_rss_bytes=rss_bytes(), raw_self_maxrss=own.ru_maxrss,
        platform=sys.platform, timing_scope='through receipt preparation; external meter includes write and exit')


def decompose(case, replay, market, fleet_count):
    loads = tuple(Fraction(x) for x in replay['load'])
    if len(loads) != len(market.a) or any(x < 0 for x in loads):
        raise ValueError('Invalid independently replayed period energy')
    vehicle = Fraction(case.vehicle_cost)*fleet_count
    ops = Fraction(replay['ops_cost'])
    deadhead = ops-vehicle
    if deadhead < 0:
        raise ValueError('Operating cost smaller than declared fleet cost')
    linear = sum((Fraction(a)*x for a, x in zip(market.a, loads)), Fraction(0))
    quadratic = sum((Fraction(b)*x*x/2 for b, x in zip(market.b, loads)), Fraction(0))
    return dict(ops_exact=str(ops), fleet_operating_exact=str(vehicle), deadhead_exact=str(deadhead),
        linear_electricity_exact=str(linear),
        quadratic_electricity_exact=str(quadratic), electricity_exact=str(linear+quadratic),
        grid_kwh_exact=str(sum(loads)), total_exact=str(ops+linear+quadratic))


def model_mask(case, built, retained, check):
    ids = [m.id for m in case.movements]
    if (built['physical_identity'] != case.identity() or built['compiled']['identity'] != case.identity()
            or len(built['x']) != len(ids) or not retained <= set(ids)):
        raise IdentityFailure('Full physical model/movement identity differs')
    original_rows = built['constraint_count_before_objective']
    if built['model'].num_rows != original_rows:
        raise ConfigurationFailure('Unexpected physical model rows')
    for movement, var in zip(case.movements, built['x']):
        check()
        if str(var.var_type) != 'B' or var.lb != 0 or var.ub != 1:
            raise ConfigurationFailure('Original movement variable differs from free binary')
        if movement.id not in retained:
            var.ub = 0
        if var.lb != 0 or var.ub != int(movement.id in retained):
            raise ConfigurationFailure('Retained/free excluded/zero contract failed')
    return dict(physical_rows=original_rows, columns=built['model'].num_cols,
        case_identity=case.identity(), original_movements=len(ids),
        retained_movements=len(retained), physical_rows_unchanged=True,
        modification='excluded movement upper bounds only; no binary fixed1')


def imported_source_inventory(root, preflight):
    seen = set()
    for module_name, module in tuple(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if filename and filename.endswith('.py'):
            path = Path(filename).resolve()
            if (module_name == 'egglab' or module_name.startswith('egglab.')
                    or module_name == 'experiments' or module_name.startswith('experiments.')):
                if not path.is_relative_to(root/'src'):
                    raise IdentityFailure('Imported project module outside frozen worktree: '+module_name)
            if path.is_relative_to(root/'src'):
                name = str(path.relative_to(root))
                if name not in preflight['input_sha256']:
                    raise IdentityFailure('Unbound imported project dependency: '+name)
                seen.add(name)
    return sorted(seen)


def worker(args):
    """Exactly one acquired prior or active method; never spawn another process."""
    folder = args.worker.resolve()
    spec = load(folder/'spec.json')
    root, anchor = Path(spec['root']), args.parent_anchor
    acquisition = spec['kind'] == 'acquisition'
    end, native_end = anchor+(120. if acquisition else 60.), anchor+(90. if acquisition else 52.)
    resource.setrlimit(resource.RLIMIT_CPU, (150 if acquisition else 90,)*2)
    target = folder/'receipt.json'
    report = dict(complete=False, method_endpoint_accepted=False, physical_witness_valid=False,
        policy=POLICY, kind=spec['kind'], case=spec['case_key'], arm=spec['arm'],
        seed=spec['seed'], parent_anchor=anchor, admission_deadline=end,
        native_deadline=native_end, failures=[], stages=[], native_calls=0,
        method_attempted=True, method_success=False, config_failure=False,
        admission_checks_passed=False, admission_rejected=False, native_search_completed=False,
        resource_violation=False, identity_failure=False, fatal_violation=False)
    stopped, best_plan, best_replay, best_bill = None, None, None, None
    active_stage = 'startup'
    initial_children_cpu = children_cpu()

    def stop(signum, frame):
        nonlocal stopped
        stopped = stopped or signum
        raise TimeoutError('Worker stop '+str(signum))

    def check(deadline=end):
        if rss_bytes() > 5*1024**3 or threading.active_count() != 1:
            report.update(config_failure=True, resource_violation=True, fatal_violation=True)
            raise ResourceViolation('Worker observed RSS5GiB/Python thread limit failed')
        if children_cpu() != initial_children_cpu:
            report.update(config_failure=True, resource_violation=True, fatal_violation=True)
            raise ResourceViolation('Worker unexpectedly waited for a child process')
        if stopped is not None or time.monotonic() >= deadline:
            raise TimeoutError('Worker fixed deadline/stop reached')

    def stage(name, operation):
        nonlocal active_stage
        active_stage = name
        at, cpu = time.monotonic(), self_cpu()
        try:
            check()
            return operation()
        finally:
            report['stages'].append(dict(stage=name, wall_s=time.monotonic()-at,
                cpu_s=self_cpu()-cpu, observed_peak_rss_bytes=rss_bytes()))

    events = None
    try:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, end-time.monotonic()))
        events = (folder/'events.jsonl').open('x')
        def record(event):
            check()
            events.write(json.dumps(event, allow_nan=False)+'\n'); events.flush()
            check()
        preflight = load(spec['preflight'])
        allowed_cases = {f'scale:{base}:{size}' for base in GROUPS for size in (40, 80)}
        if (spec['case_key'] not in allowed_cases or spec['kind'] not in ('acquisition', 'replanning')
                or spec['seed'] not in SEEDS or spec['arm'] not in ARMS
                or acquisition and (spec['arm'] != 'CoverCA1' or spec['seed'] != 17)):
            raise ConfigurationFailure('Worker specification outside frozen cohort/arm/seed design')
        sys.path.insert(0, str(root/'src'))
        sys.path.insert(0, str(Path(__file__).parent))
        import scoring
        if Path(scoring.__file__).resolve() != Path(__file__).with_name('scoring.py').resolve():
            raise IdentityFailure('Worker imported a different scoring module')
        from egglab import claude_cases, physical_learning_cases as bank
        from egglab import native_recharge as nr, native_pathflow as pf, native_hull as nh
        optimizer, builder = pf._optimize_once, pf.build_feasible_model
        if optimizer is not nr._optimize_once:
            raise ConfigurationFailure('Unexpected native hook')
        case = stage('case_construction', lambda: claude_cases.make(spec['case_key']))
        day, late = bank.market(case, 'day'), bank.market(case, 'late')
        report.update(case_identity=case.identity(), day_market_identity=day.identity(),
            late_market_identity=late.identity(), physical_change_between_tariffs=False,
            input_source_sha256=preflight['input_sha256'],
            group_id='claude-scale-v1:'+spec['case_key'].split(':')[1],
            base_id=int(spec['case_key'].split(':')[1]), services=int(spec['case_key'].split(':')[2]))
        asset_lock = preflight['asset_lock']
        if acquisition:
            preparation_end = anchor+30.
            contract = dict(case_identity=case.identity(), trips=[asdict(t) for t in case.trips],
                movements={m.id: asdict(m) for m in case.movements},
                resources=[asdict(r) for r in case.resources], max_vehicles=case.max_vehicles)
            stage('save_case_contract', lambda: save_new(folder/'case-contract.json', contract))
            selected = stage('paid_CoverCA1_day_selection', lambda: scoring.select(case, day.a, day.b,
                'CoverCA1', root=root, asset_lock=asset_lock, case_key=spec['case_key'],
                random_seed=17, verified_asset_sha256=preflight['verified_asset_sha256'],
                common_prior_ids=[], check=lambda: check(preparation_end)))
            stage('save_selection', lambda: save_new(folder/'selection.json', selected))
            if not selected['native_dispatch_permitted']:
                report['config_failure'] = True
                raise ValueError('Preserved CoverCA1 acquisition design failure')
            check(preparation_end)
            built = stage('full_physical_model', lambda: pf.build_feasible_model(case, 'GRB'))
            built['model'].seed = 17
            if built['model'].seed != 17:
                raise ConfigurationFailure('Acquisition native seed readback failed')
            report['matrix'] = stage('pool_bounds', lambda: model_mask(case, built,
                set(selected['retained_movement_ids']), lambda: check(preparation_end)))
            import mip
            built['model'].objective = mip.xsum(v for m, v in zip(case.movements, built['x'])
                if m.kind == 'pullout')
            check(preparation_end)
            remaining = native_end-time.monotonic()
            budget = nr.Budget(backend='GRB', threads=1, phase_seconds=min(60., remaining),
                wall_seconds=end-time.monotonic(), max_rounds=1)
            report['native_calls'] = 1
            stats = stage('one_fleet_native_call', lambda: pf._optimize_once(built, budget, native_end))
            report['native'] = stats
            report['bound_scope'] = 'pool-restricted acquisition fleet count only'
            check(native_end)
            if built['model'].seed != 17:
                raise ConfigurationFailure('Acquisition native seed changed')
            if stats.get('threads') != 1:
                report.update(config_failure=True, resource_violation=True, fatal_violation=True)
                raise ResourceViolation('Acquisition native thread status differs')
            if (stats.get('status') not in ('OPTIMAL', 'FEASIBLE')
                    or not nr._finite(stats.get('incumbent'))):
                raise ValueError('No admissible acquisition incumbent/seed/thread status')
            report['native_search_completed'] = True
            # One acquisition capture only; active rounds do not duplicate raw captures.
            stage('one_native_capture', lambda: save_new(folder/'native-capture.json',
                pf.capture_incumbent(case, built)))
            plan = stage('unchanged_extraction', lambda: pf._extract(case, built, record=record, round_index=0))
            replay = stage('independent_full_case_replay', lambda: nr.replay_native(case, plan))
            vehicles = len(plan['vehicles'])
            actual_ids = {mid for v in plan['vehicles'] for mid in v['movements']}
            selected_starts = sum(m.kind == 'pullout' and v.x is not None and float(v.x) > .5
                for m, v in zip(case.movements, built['x']))
            if (replay.get('replay_ok') is not True or vehicles != selected_starts
                    or abs(stats['incumbent']-vehicles) > nr.BOUND_GUARD
                    or not actual_ids <= set(selected['retained_movement_ids'])):
                raise ValueError('Acquisition replay/topology/fleet objective mismatch')
            best_plan, best_replay = plan, replay
            best_bill = Fraction(replay['ops_cost'])+nh.supply(day, replay['load'])
            report.update(fleet_count=vehicles, day_bill_exact=str(best_bill),
                target_bill_exact=str(Fraction(replay['ops_cost'])+nh.supply(late, replay['load'])),
                day_decomposition=decompose(case, replay, day, vehicles),
                target_decomposition=decompose(case, replay, late, vehicles), selected_source='acquired_day_prior',
                scientific_context=dict(day_a=list(day.a), day_b=list(day.b),
                    target_a=list(late.a), target_b=list(late.b), replay_load=list(replay['load']),
                    market_edges_min=list(case.market_edges_min),
                    battery_kwh=case.battery_kwh, reserve_kwh=case.reserve_kwh,
                    efficiency=case.efficiency, resources=[asdict(r) for r in case.resources],
                    resource_scaling='one connector;180kW at40 trips,270kW at80 trips',
                    units=dict(cost='generator cost units', load='period grid energy, kWh',
                        linear_coefficient='generator cost units/kWh',
                        curvature_coefficient='generator cost units/kWh^2')))
        else:
            prior = load(spec['prior_receipt'])
            if (prior.get('method_endpoint_accepted') is not True
                    or prior['case_identity'] != case.identity()):
                report['config_failure'] = True
                raise IdentityFailure('Prior acquisition not timely/valid for exact physical case')
            fallback = load(Path(spec['prior_receipt']).parent/'best-plan.json')
            initial_replay = stage('paid_initial_fallback_replay', lambda: nr.replay_native(case, fallback))
            initial_bill = Fraction(initial_replay['ops_cost'])+nh.supply(late, initial_replay['load'])
            if (initial_replay.get('replay_ok') is not True or str(initial_bill) != prior['target_bill_exact']
                    or len(fallback['vehicles']) != prior['fleet_count']):
                raise IdentityFailure('Shared fallback replay/target bill/fleet mismatch')
            best_plan, best_replay, best_bill = fallback, initial_replay, initial_bill
            report.update(fleet_count=prior['fleet_count'], fallback_bill_exact=str(initial_bill),
                selected_source='retained_fallback', fallback_initially_valid=True)
            # A scorer failure does not erase the already available operational fallback.
            stage('save_initial_fallback', lambda: (
                save_new(folder/'best-plan.json', best_plan), save_new(folder/'best-replay.json', best_replay)))
            selected = stage('paid_fresh_scoring_and_selection', lambda: scoring.select(case, late.a, late.b,
                'full' if spec['arm'] == 'fixed_route' else spec['arm'], root=root,
                asset_lock=asset_lock, case_key=spec['case_key'], random_seed=spec['seed'],
                verified_asset_sha256=preflight['verified_asset_sha256'],
                common_prior_ids=[mid for vehicle in fallback['vehicles'] for mid in vehicle['movements']],
                check=check))
            stage('save_selection', lambda: save_new(folder/'selection.json', selected))
            report['selection_contract'] = {k: selected[k] for k in
                ('M', 'K', 'base_backbone_ids', 'backbone_ids', 'boundary_ids', 'case_identity')}
            report['selection_contract']['common_prior_ids'] = sorted(
                mid for vehicle in fallback['vehicles'] for mid in vehicle['movements'])
            report['selection_status'] = selected['status']
            if not selected['native_dispatch_permitted']:
                report['config_failure'] = True
                raise ValueError('Preserved selection design failure; no native dispatch')
            import planner
            if Path(planner.__file__).resolve() != Path(__file__).with_name('planner.py').resolve():
                raise IdentityFailure('Worker imported a different planning module')
            check(native_end)
            remaining = native_end-time.monotonic()
            budget = nr.Budget(backend='GRB', threads=1, phase_seconds=remaining/4.,
                wall_seconds=remaining, max_rounds=4, epsilon=1e-4)
            result = stage('fixed_fleet_economic_replanning', lambda: planner.replan(case, late.a, late.b,
                fallback_plan=fallback, retained_ids=selected['retained_movement_ids'],
                seed=spec['seed'], fleet_count=prior['fleet_count'], native_deadline=native_end,
                admission_deadline=end, budget=budget, use_native_start=True,
                fixed_route=spec['arm'] == 'fixed_route', completion=True, record=record))
            compact = {k: v for k, v in result.items() if k not in ('plan', 'replay')}
            stage('save_planner_telemetry', lambda: save_new(folder/'planner-result.json', compact))
            plan, replay = result['plan'], result['replay']
            bill = Fraction(replay['ops_cost'])+nh.supply(late, replay['load'])
            if (replay.get('replay_ok') is not True or len(plan['vehicles']) != prior['fleet_count']
                    or bill != Fraction(result['true_bill_exact']) or bill > initial_bill):
                raise ConfigurationFailure('Replanner returned invalid fleet/cost/nonretained fallback')
            check()
            if not result['used_fallback']:
                ids = {mid for vehicle in plan['vehicles'] for mid in vehicle['movements']}
                if not ids <= set(selected['retained_movement_ids']):
                    raise ConfigurationFailure('Native improvement outside allowed pool')
            best_plan, best_replay, best_bill = plan, replay, bill
            report.update(selected_source=result['selected_source'], used_fallback=result['used_fallback'],
                planner_status=result['status'], planner_failures=result['failures'],
                native_calls=result['native_calls_dispatched'],
                native_call_attempts=result['native_call_attempts'], bound_scope=result['bound_scope'],
                native_search_completed=bool(result['rounds'])
                    and any('admission' in row for row in result['rounds'])
                    and not any('failure' in row or row.get('search_status') == 'no_admissible_native_incumbent'
                        for row in result['rounds']))
            # The initial files remain immutable; the admitted choice is separate.
            stage('save_admitted_choice', lambda: (
                save_new(folder/'admitted-plan.json', best_plan), save_new(folder/'admitted-replay.json', best_replay)))
        if acquisition:
            stage('save_acquired_witness', lambda: (
                save_new(folder/'best-plan.json', best_plan), save_new(folder/'best-replay.json', best_replay)))
        if pf._optimize_once is not optimizer or pf.build_feasible_model is not builder:
            raise ConfigurationFailure('Unexpected persistent native hook mutation')
        report['imported_project_sources'] = stage('imported_source_binding',
            lambda: imported_source_inventory(root, preflight))
        report.update(physical_witness_valid=True, objective_exact=str(best_bill),
            objective_decomposition=decompose(case, best_replay, day if acquisition else late,
                report['fleet_count']), admission_checks_passed=True,
            witness_durable_monotonic=time.monotonic())
        check()
    except BaseException as exc:
        report['failures'].append(dict(stage=active_stage, type=type(exc).__name__, message=str(exc)))
        if (isinstance(exc, (ConfigurationFailure, ResourceViolation, MemoryError, ImportError, KeyError, TypeError))
                or not isinstance(exc, TimeoutError) and active_stage in
                ('case_construction', 'full_physical_model', 'pool_bounds',
                 'paid_fresh_scoring_and_selection', 'paid_CoverCA1_day_selection', 'imported_source_binding')):
            report['config_failure'] = True
        if isinstance(exc, IdentityFailure):
            report['identity_failure'] = True
        if isinstance(exc, (ResourceViolation, MemoryError)):
            report['resource_violation'] = True
        report['fatal_violation'] = report['config_failure']
        report['admission_rejected'] = best_plan is not None and not report['admission_checks_passed']
    finally:
        if events is not None:
            events.flush(); os.fsync(events.fileno()); events.close()
        report.update(complete=True, stop_signal=stopped, resources=resource_receipt(),
            elapsed_before_receipt_s=time.monotonic()-anchor,
            child_processes_permitted=False)
        report['method_endpoint_accepted'] = bool(report['physical_witness_valid'] and not report['failures']
            and time.monotonic() < end)
        report['method_success'] = bool(report['method_endpoint_accepted']
            and report['native_search_completed'] and not report.get('planner_failures'))
        publish(target, report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['method_endpoint_accepted'] else 1


def preflight(root, output):
    """One hash batch. Model loads repeat inside workers; their hashes never do."""
    paths = tuple(SOURCE_FILES)+tuple(INPUT_FILES)
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate preflight source/input')
    digests, documents = {}, {}
    for name in paths:
        path = (root/name).resolve()
        raw = path.read_bytes()
        digests[name] = hashlib.sha256(raw).hexdigest()
        if name in INPUT_FILES and name.endswith('.json'):
            documents[name] = json.loads(raw)
    manifest = documents[INPUT_FILES[0]]
    if (tuple(manifest['sampling']['selected_base_ids']) != GROUPS
            or tuple(manifest['active_arms_canonical']) != ARMS
            or tuple(manifest['native_solver_seeds_order']) != SEEDS
            or manifest['active_decisions'] != 168):
        raise ValueError('Frozen cohort/arm/seed manifest differs')
    if ({key for group in manifest['groups'] for key in group['case_keys']}
            != {f'scale:{base}:{size}' for base in GROUPS for size in (40, 80)}):
        raise ValueError('Frozen exact case-key list differs')
    sys.path.insert(0, str(Path(__file__).parent))
    import scoring  # stdlib-only module; no model/numerical imports or calls here.
    if Path(scoring.__file__).resolve() != Path(__file__).with_name('scoring.py').resolve():
        raise ValueError('Preflight imported a different scoring module')
    lock = documents[INPUT_FILES[2]]
    expected = scoring.expected_assets(lock, root)
    verified = {}
    for name, required in expected.items():
        if name in verified:
            raise ValueError('Duplicate selected asset')
        with Path(name).open('rb') as stream:
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024*1024), b''):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != required:
            raise ValueError('Pinned selected asset differs: '+name)
        verified[name] = actual
    result = dict(policy=POLICY, input_sha256=digests, verified_asset_sha256=verified,
        asset_lock=lock, group_manifest=manifest,
        source_freeze_assumption='Parent freezes these bytes throughout campaign; workers do not rehash',
        exactly_one_source_input_asset_hash_batch=True,
        inherited_backend_fingerprinting='Unchanged native build API hashes its backend library per model; paid inside worker clocks')
    save_new(output/'preflight.json', result)
    return result


def launch_worker(root, output, spec, index):
    """One owned direct child, bounded communicate/TERM/KILL; no retry."""
    name = '%03d-%s-%s-%s' % (index, spec['kind'], spec['case_key'].replace(':', '-'), spec['arm'])
    folder = output/name
    folder.mkdir(exist_ok=False)
    spec = dict(spec, root=str(root), preflight=str(output/'preflight.json'))
    save_new(folder/'spec.json', spec)
    save_new(folder/'receipt.json', dict(complete=False, method_endpoint_accepted=False,
        failure='Worker has not durably completed'))
    before_child, before_self = children_cpu(), self_cpu()
    anchor = time.monotonic()  # Includes Python startup/imports/scorer/model load.
    allowance = 120. if spec['kind'] == 'acquisition' else 60.
    record = dict(folder=str(folder), parent_anchor=anchor, admission_deadline=anchor+allowance,
        pid=None, returncode=None, timed_out=False, reaped=False, failures=[], attempted=False,
        config_failure=False, resource_violation=False, identity_failure=False, fatal_violation=False,
        child_cpu_hard_s=150. if spec['kind'] == 'acquisition' else 90.)
    child = None
    cleanup_end = None
    with (folder/'stdout.log').open('x') as stdout, (folder/'stderr.log').open('x') as stderr:
        try:
            if threading.active_count() != 1:
                record.update(config_failure=True, resource_violation=True, fatal_violation=True)
                raise ResourceViolation('Launcher must have one Python thread before child creation')
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(folder),
                '--parent-anchor', repr(anchor)], cwd=root, env=dict(os.environ),
                stdout=stdout, stderr=stderr, start_new_session=True,
                preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU,
                    (int(record['child_cpu_hard_s']),)*2))
            record['pid'] = child.pid
            record['attempted'] = True
            try:
                child.wait(timeout=max(.001, anchor+allowance-time.monotonic()))
            except subprocess.TimeoutExpired:
                record['timed_out'] = True
                cleanup_end = time.monotonic()+3.
                child.terminate()  # Direct, still-unreaped Popen child only.
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            record.update(returncode=child.returncode, reaped=True)
        except BaseException as exc:
            record['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
            if child is None and not isinstance(exc, TimeoutError):
                record.update(config_failure=True, fatal_violation=True)
                if isinstance(exc, (ResourceViolation, MemoryError)):
                    record['resource_violation'] = True
            if child is not None and child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3.
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    record.update(returncode=child.returncode, reaped=True)
                except BaseException as secondary:
                    record['failures'].append(dict(type=type(secondary).__name__, message=str(secondary)))
    record.update(parent_elapsed_s=time.monotonic()-anchor,
        waited_child_cpu_s=children_cpu()-before_child, parent_cpu_s=self_cpu()-before_self,
        cpu_observation_complete=child is None or record['reaped'],
        unresolved_cpu_reserve_s=record['child_cpu_hard_s'] if child is not None and not record['reaped'] else 0.)
    try:
        result = load(folder/'receipt.json')
    except Exception as exc:
        result = dict(complete=False, method_endpoint_accepted=False,
            failure=dict(type=type(exc).__name__, message=str(exc)))
    record['process_return_elapsed_s'] = record['parent_elapsed_s']
    record['complete_receipt_read_monotonic'] = time.monotonic()
    record['parent_elapsed_s'] = record['complete_receipt_read_monotonic']-anchor
    record['parent_cpu_s'] = self_cpu()-before_self
    record['method_late'] = record['parent_elapsed_s'] > allowance
    record['accounting_scope'] = 'through process return and complete receipt read; external-record publication also charged to campaign'
    record['worker'] = result
    for flag in ('config_failure', 'resource_violation', 'identity_failure', 'fatal_violation'):
        record[flag] = record[flag] or result.get(flag, False)
    record['method_endpoint_accepted'] = bool(record['reaped'] and record['returncode'] == 0
        and not record['timed_out'] and not record['failures'] and result.get('complete') is True
        and not record['config_failure']
        and result.get('method_endpoint_accepted') is True
        and record['parent_elapsed_s'] <= allowance)
    save_new(folder/'external-receipt.json', record)
    return record


def nested_contract_check(output, acquisitions):
    checks = []
    for base in GROUPS:
        records = [acquisitions[f'scale:{base}:{size}'] for size in (40, 80)]
        paths = [Path(r['folder'])/'case-contract.json' for r in records if r.get('folder')]
        if len(paths) != 2 or not all(path.exists() for path in paths):
            checks.append(dict(base_id=base, observed=False, passed=None,
                reason='Acquisition did not produce both case contracts; no replacement'))
            continue
        small, large = (load(path) for path in paths)
        passed = (small['trips'] == large['trips'][:40]
            and all(large['movements'].get(mid) == movement for mid, movement in small['movements'].items())
            and small['resources'][0]['grid_kw'] == 180 and large['resources'][0]['grid_kw'] == 270)
        checks.append(dict(base_id=base, observed=True, passed=passed,
            scope='nested trip/induced movement records, existing size-scaled resources'))
        if not passed:
            raise IdentityFailure('Generated nested timetable/resource contract differs for base '+str(base))
    save_new(output/'cohort-checks.json', checks)
    return checks


def assigned_cells():
    """All168 metadata assignments, independent of acquisition/worker outcomes."""
    for group_index, base in enumerate(GROUPS):
        for size_index, size in enumerate((40, 80)):
            for seed_index, seed in enumerate(SEEDS):
                b = ((group_index*2+size_index)*3+seed_index)
                shift = b % 7
                order = list(ARMS[shift:]+ARMS[:shift])
                if (b//7) % 2:
                    order.reverse()
                for position, arm in enumerate(order):
                    yield dict(block=b, position=position, case=f'scale:{base}:{size}', seed=seed, arm=arm,
                        group_id=f'claude-scale-v1:{base}', base_id=base, services=size)


def campaign(args):
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    receipt = output/'receipt.json'
    save_new(receipt, dict(complete=False, passed=False, failure='No final campaign receipt'))
    stopped = None
    report = dict(policy=POLICY, complete=False, passed=False, acquisitions=[], decisions=[],
        reference_blocks=[], assigned_active_decisions=168, group_count=4,
        scientific_qualification=False, failures=[], config_failure=False,
        resource_violation=False, identity_failure=False, fatal_violation=False, budgets=dict(cpu_s=TOTAL_CPU,
            wall_s=TOTAL_WALL, dispatch_cpu_s=DISPATCH_CPU, closure_cpu_reserve_s=600,
            finalization_cpu_s=FINAL_CPU, finalization_wall_s=FINAL_WALL))
    def stop(signum, frame):
        nonlocal stopped
        stopped = stopped or signum
        raise TimeoutError('Campaign stop '+str(signum))
    unresolved_cpu = 0.
    def funded(hard_cpu, wall):
        return (stopped is None and self_cpu()+children_cpu()+unresolved_cpu+hard_cpu <= DISPATCH_CPU
            and time.monotonic()-PROCESS_WALL0+wall+3.+FINAL_WALL <= TOTAL_WALL)
    acquisitions, common, launch_index = {}, {}, 0
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (int(TOTAL_CPU),)*2)
        for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, TOTAL_WALL-(time.monotonic()-PROCESS_WALL0)))
        at, cpu = time.monotonic(), self_cpu()
        binding = preflight(root, output)
        report['preflight'] = dict(path='preflight.json', wall_s=time.monotonic()-at, cpu_s=self_cpu()-cpu,
            input_sha256=binding['input_sha256'], verified_asset_sha256=binding['verified_asset_sha256'])
        for base in GROUPS:
            for size in (40, 80):
                key = f'scale:{base}:{size}'
                spec = dict(kind='acquisition', case_key=key, arm='CoverCA1', seed=17)
                if not funded(150., 120.):
                    stopped = stopped or 'Dispatch funding exhausted'
                    record = dict(case=key, method_endpoint_accepted=False, folder='',
                        attempted=False,
                        not_dispatched_reason='CPU/wall dispatch funding or retained stop')
                else:
                    launch_index += 1
                    record = launch_worker(root, output, spec, launch_index)
                    record['case'] = key
                    if record['config_failure']:
                        stopped = stopped or 'Acquisition fatal configuration/resource/identity violation'
                        report['config_failure'] = report['fatal_violation'] = True
                        report['resource_violation'] |= record['resource_violation']
                        report['identity_failure'] |= record['identity_failure']
                    unresolved_cpu += record['unresolved_cpu_reserve_s']
                    if record['pid'] is not None and not record['reaped']:
                        stopped = stopped or 'unreaped_owned_worker'
                acquisitions[key] = record
                report['acquisitions'].append(record)
        # Validate source-derived nesting once at actual generation, not repeatedly per arm.
        report['cohort_checks'] = nested_contract_check(output, acquisitions)
        for group_index, base in enumerate(GROUPS):
            for size_index, size in enumerate((40, 80)):
                key = f'scale:{base}:{size}'
                acquisition = acquisitions[key]
                prior_ok = acquisition.get('method_endpoint_accepted') is True
                prior = acquisition.get('worker', {})
                for seed_index, seed in enumerate(SEEDS):
                    b = ((group_index*2+size_index)*3+seed_index)
                    shift = b % 7
                    order = list(ARMS[shift:]+ARMS[:shift])
                    if (b//7) % 2:
                        order.reverse()
                    report['reference_blocks'].append(dict(block=b, case=key, seed=seed,
                        arm='unchanged', available=prior_ok,
                        target_bill_exact=prior.get('target_bill_exact') if prior_ok else None,
                        fleet_count=prior.get('fleet_count') if prior_ok else None,
                        target_decomposition=prior.get('target_decomposition') if prior_ok else None,
                        active_solve=False, acquisition_cost_reported_separately=True))
                    for position, arm in enumerate(order):
                        row = dict(block=b, position=position, case=key, seed=seed, arm=arm,
                            attempted=False, method_endpoint_accepted=False, method_success=False,
                            config_failure=False, method_late=False, native_search_completed=False,
                            resource_violation=False, identity_failure=False, fatal_violation=False,
                            operational_endpoint_available=prior_ok)
                        if not prior_ok:
                            row.update(missing_reason='Predetermined prior acquisition failed; no replacement',
                                operational_target_bill_exact=None)
                        else:
                            # This physically valid plan is already available before the clock;
                            # worker failures/late returns never erase this ITT reference.
                            row.update(operational_target_bill_exact=prior['target_bill_exact'],
                                operational_decomposition=prior['target_decomposition'],
                                operational_selected_source='preexisting_fallback', fleet_count=prior['fleet_count'])
                            if not funded(90., 60.):
                                stopped = stopped or 'Dispatch funding exhausted'
                                row['not_dispatched_reason'] = 'CPU/wall dispatch funding or retained stop'
                            else:
                                launch_index += 1
                                result = launch_worker(root, output, dict(kind='replanning', case_key=key,
                                    arm=arm, seed=seed, prior_receipt=str(Path(acquisition['folder'])/'receipt.json')),
                                    launch_index)
                                row['execution'] = result
                                row['attempted'] = result['attempted']
                                row['method_late'] = result['method_late']
                                unresolved_cpu += result['unresolved_cpu_reserve_s']
                                valid = result['method_endpoint_accepted']
                                child_receipt = result['worker']
                                for flag in ('config_failure', 'resource_violation', 'identity_failure', 'fatal_violation'):
                                    row[flag] = result[flag]
                                if row['config_failure']:
                                    valid = False
                                    stopped = stopped or 'Active worker fatal configuration/resource/identity violation'
                                    report['config_failure'] = report['fatal_violation'] = True
                                    report['resource_violation'] |= row['resource_violation']
                                    report['identity_failure'] |= row['identity_failure']
                                row['native_search_completed'] = child_receipt.get('native_search_completed', False)
                                contract = child_receipt.get('selection_contract')
                                if contract is not None and arm not in ('full', 'fixed_route'):
                                    if key in common and common[key] != contract:
                                        valid = False
                                        stopped = stopped or 'Common B/K/boundary mismatch'
                                        row['contract_failure'] = str(stopped)
                                        row['config_failure'] = True
                                        row['fatal_violation'] = True
                                        report['config_failure'] = report['fatal_violation'] = True
                                    common[key] = contract
                                if result['pid'] is not None and not result['reaped']:
                                    stopped = stopped or 'unreaped_owned_worker'
                                row['method_endpoint_accepted'] = valid
                                row['method_success'] = valid and child_receipt.get('method_success') is True
                                if valid:
                                    row.update(operational_target_bill_exact=child_receipt['objective_exact'],
                                        operational_decomposition=child_receipt['objective_decomposition'],
                                        operational_selected_source=child_receipt['selected_source'])
                        report['decisions'].append(row)
                        with (output/'decision-ledger.jsonl').open('a') as stream:
                            stream.write(json.dumps(row, allow_nan=False)+'\n'); stream.flush(); os.fsync(stream.fileno())
        report['complete'] = len(report['decisions']) == 168
        report['passed'] = report['complete'] and stopped is None
    except BaseException as exc:
        report['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
        if isinstance(exc, (ValueError, KeyError, TypeError, ImportError, ResourceViolation, MemoryError)):
            report['config_failure'] = report['fatal_violation'] = True
            stopped = stopped or 'Campaign fatal configuration/resource/identity violation'
        if isinstance(exc, IdentityFailure):
            report['identity_failure'] = True
        if isinstance(exc, (ResourceViolation, MemoryError)):
            report['resource_violation'] = True
    finally:
        # No numerical work here. This bounded compact finalization is inside4CPUh.
        final_at, final_cpu = time.monotonic(), self_cpu()
        # Preserve every assignment even if preflight, I/O, a stop or ownership
        # failure interrupted the normal loops. Existing fallback is an ITT
        # endpoint; undispatched methods are never silently completed.
        for base in GROUPS:
            for size in (40, 80):
                key = f'scale:{base}:{size}'
                if key not in acquisitions:
                    missing = dict(case=key, attempted=False, method_endpoint_accepted=False,
                        folder='', not_dispatched_reason='Campaign stopped before assigned acquisition')
                    acquisitions[key] = missing
                    report['acquisitions'].append(missing)
        observed = {(r['case'], r['seed'], r['arm']): r for r in report['decisions']}
        finalized, references = [], {}
        for assignment in assigned_cells():
            key = (assignment['case'], assignment['seed'], assignment['arm'])
            prior_record = acquisitions[assignment['case']]
            available = prior_record.get('method_endpoint_accepted') is True
            prior = prior_record.get('worker', {})
            if key in observed:
                row = observed[key]
            else:
                row = dict(assignment, attempted=False, method_endpoint_accepted=False,
                    method_success=False, config_failure=False, method_late=False,
                    resource_violation=False, identity_failure=False, fatal_violation=False,
                    native_search_completed=False, operational_endpoint_available=available,
                    not_dispatched_reason='Campaign stopped before assigned decision',
                    operational_target_bill_exact=prior.get('target_bill_exact') if available else None)
                if available:
                    row.update(operational_decomposition=prior['target_decomposition'],
                        operational_selected_source='preexisting_fallback', fleet_count=prior['fleet_count'])
                else:
                    row['missing_reason'] = 'Predetermined prior unavailable; no replacement'
            row.update(group_id=assignment['group_id'], base_id=assignment['base_id'],
                services=assignment['services'])
            finalized.append(row)
            references.setdefault(assignment['block'], dict(block=assignment['block'],
                case=assignment['case'], seed=assignment['seed'], arm='unchanged', available=available,
                target_bill_exact=prior.get('target_bill_exact') if available else None,
                target_decomposition=prior.get('target_decomposition') if available else None,
                fleet_count=prior.get('fleet_count') if available else None,
                active_solve=False, acquisition_cost_reported_separately=True))
        report['decision_ledger_rows_before_finalization'] = len(observed)
        report['decisions'], report['reference_blocks'] = finalized, list(references.values())
        report.update(stop_signal=stopped, resources=resource_receipt(), elapsed_s=time.monotonic()-PROCESS_WALL0,
            campaign_record_complete=len(finalized) == 168,
            attempted_decisions=sum(r['attempted'] for r in finalized),
            unresolved_child_cpu_reserve_s=unresolved_cpu,
            accounting_observations_complete=unresolved_cpu == 0,
            method_accepted=sum(r['method_endpoint_accepted'] for r in report['decisions']),
            operational_available=sum(r['operational_endpoint_available'] for r in report['decisions']),
            missing_prior=sum(not r['operational_endpoint_available'] for r in report['decisions']),
            no_automatic_retry=True, source_freeze_required=True,
            source_freeze_assumption='Parent keeps once-bound source/asset bytes unchanged; no repeated hash audit',
            interpretation='four development groups; fixed-fleet warm replanning; operational fallback is not method success')
        if report['resources']['combined_cpu_s'] > TOTAL_CPU:
            report['passed'] = False
            report['config_failure'] = report['resource_violation'] = report['fatal_violation'] = True
            report['failures'].append(dict(type='BudgetExhausted', message='Combined self+waited child CPU exceeds total'))
        if unresolved_cpu or self_cpu()-final_cpu > FINAL_CPU or time.monotonic()-final_at > FINAL_WALL:
            report['passed'] = False
            report['config_failure'] = report['resource_violation'] = report['fatal_violation'] = True
            report['failures'].append(dict(type='IncompleteAccountingOrFinalization',
                message='Unreaped child CPU or bounded finalization allowance failed'))
        report['finalization'] = dict(cpu_s_before_publication=self_cpu()-final_cpu,
            wall_s_before_publication=time.monotonic()-final_at,
            cpu_provision_s=FINAL_CPU, wall_provision_s=FINAL_WALL,
            scope='compact receipt only; no native rerun, raw capture reread or hash audit')
        publish(receipt, report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--parent-anchor', type=float)
    args = parser.parse_args()
    if args.worker is not None:
        if args.parent_anchor is None or not math.isfinite(args.parent_anchor):
            raise ValueError('Worker requires parent-owned finite monotonic anchor')
        return worker(args)
    if args.output is None:
        raise ValueError('Campaign requires a fresh exclusive output directory')
    return campaign(args)


if __name__ == '__main__':
    raise SystemExit(main())
