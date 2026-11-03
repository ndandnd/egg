"""DRAFT paid reference invocation of EVSP-DR on new synthetic data only."""
import time
START = time.monotonic()
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading

POLICY = 'adjacent-synthetic-capacity-comparison-worker-v1'
THREAD_ENV = ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
    'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')


class ContractError(ValueError):
    pass


def local(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ContractError('Declared local source unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ContractError('Local source origin differs')
    return module


def write(path, value):
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', required=True, type=Path)
    parser.add_argument('--parent-anchor', required=True, type=float)
    parser.add_argument('--spec-sha256', required=True)
    args = parser.parse_args(argv)
    anchor, folder = args.parent_anchor, args.worker.resolve()
    if (not args.worker.is_absolute() or not math.isfinite(anchor) or anchor > time.monotonic()
            or len(args.spec_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.spec_sha256)):
        raise ValueError('Absolute folder, parent anchor and spec SHA256 required')
    end = anchor+240.
    root = Path(__file__).resolve().parents[2]
    report = dict(policy=POLICY, receipt_complete=False, method_endpoint_accepted=False,
        fixture_id='adjacent-six-trip-v1',source_revision=None,
        physical_valid=False, config_failure=False, fatal_contract=False,
        resource_violation=False, identity_failure=False, failures=[], oracle_run_calls=0,
        oracle_run_completed=False, native_optimize_calls=None, selected_summary=None,
        cg_certificate=None, full_model_certificate=False, native_seed=None,
        seed_policy='Unchanged sibling native default; no explicit seed parameter on run API',
        parent_anchor=anchor, endpoint_deadline=end)
    stopped, stage = None, 'launch_admission'

    def fatal(message, *, resource_failure=False, identity=False):
        report['config_failure'] = report['fatal_contract'] = True
        report['resource_violation'] |= resource_failure
        report['identity_failure'] |= identity
        raise ContractError(message)

    def stop(signum, frame):
        nonlocal stopped
        stopped = signum
        if signum == signal.SIGXCPU:
            report['config_failure'] = report['fatal_contract'] = report['resource_violation'] = True
        raise TimeoutError('Synthetic bridge signal '+str(signum))

    def check():
        if stopped is not None or time.monotonic() >= end:
            raise TimeoutError('Synthetic bridge parent-anchored240s boundary')
        use = resource.getrusage(resource.RUSAGE_SELF)
        rss = use.ru_maxrss if sys.platform == 'darwin' else use.ru_maxrss*1024
        if rss > 5*1024**3 or use.ru_utime+use.ru_stime >= 240:
            fatal('Observed worker CPU/RSS limit', resource_failure=True)
        if threading.active_count() != 1 or any(os.environ.get(k) != '1' for k in THREAD_ENV):
            fatal('Worker thread environment differs', resource_failure=True)
        try:
            os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        fatal('Unexpected worker child', resource_failure=True)

    try:
        for key in THREAD_ENV:
            os.environ[key] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (240,240))
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGXCPU):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001,end-time.monotonic()))
        check()
        launch = json.loads(Path(__file__).with_name('LAUNCH.json').read_text())
        report['source_revision'] = launch.get('source_revision')
        if launch.get('mode') != 'FROZEN' or launch.get('review_disposition') != 'PASS':
            fatal('DRAFT/PENDING cannot read spec/import oracle/generate fixture')
        stage = 'spec_admission'
        raw = (folder/'spec.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != args.spec_sha256:
            fatal('Spec SHA256 differs', identity=True)
        spec = json.loads(raw); del raw
        if (set(spec) != {'task_id','arm'} or spec['arm'] not in ('fixed_duty','full')
                or spec['task_id'] != ('T01-fixed_duty' if spec['arm'] == 'fixed_duty' else 'T02-full')):
            fatal('Literal task/arm identity differs', identity=True)
        report.update(task_id=spec['task_id'], arm=spec['arm'])
        stage = 'paid_sibling_bootstrap'
        boundary = local(root/'research-20261026/adjacent_oracle_boundary/boundary.py','adjacent_frozen_boundary')
        fixture = local(Path(__file__).with_name('fixture.py'),'adjacent_literal_fixture')
        sibling_src = boundary.REGISTERED/'src'
        if (launch.get('sibling_source_revision') != boundary.SOURCE_REVISION
                or launch.get('sibling_source_root') != str(boundary.REGISTERED)
                or launch.get('environment') != {key:'1' for key in THREAD_ENV}
                or launch.get('clean_argv') != ['--start-fee','0'] or launch.get('start_fee') != 0
                or not isinstance(launch.get('source_sha256'),dict)):
            fatal('Frozen sibling/bootstrap/source authority differs',identity=True)

        def loaded_sources():
            paths = set()
            for module in tuple(sys.modules.values()):
                filename = getattr(module,'__file__',None)
                if filename:
                    path = Path(filename).resolve()
                    if path.is_relative_to(sibling_src) and path.suffix == '.py':
                        if str(path) not in launch['source_sha256']:
                            fatal('Loaded sibling source is outside frozen source authority: '+str(path),identity=True)
                        for key,value in fixture.EXPECTED_COSTS.items():
                            if hasattr(module,key) and getattr(module,key) != value:
                                fatal('Loaded sibling captured cost constant differs: '+str(path)+':'+key)
                        paths.add(str(path))
            return sorted(paths)
        # No generic sibling name may be preloaded before the fee-setting runner.
        names = ('run_capacity_terminal_cg','run_terminal_energy_cg','config',
            'event_pricer_network','capacity_event_pricer','terminal_energy_pricer','expanded_path_realization')
        if any(name in sys.modules for name in names):
            fatal('Worker is not a fresh oracle import process', identity=True)
        sys.path.insert(0,str(sibling_src))
        original_argv = sys.argv
        try:
            sys.argv = [str(sibling_src/'run_capacity_terminal_cg.py'),'--start-fee','0']
            runner = importlib.import_module('run_capacity_terminal_cg')
        finally:
            sys.argv = original_argv
        for name in names:
            module = sys.modules.get(name)
            if module is None or Path(getattr(module,'__file__','')).resolve() != sibling_src/(name+'.py'):
                fatal('Registered sibling module origin differs: '+name, identity=True)
        for name in ('config','event_pricer_network','capacity_event_pricer','expanded_path_realization',
                     'fixed_duty_continuous_optimizer','fixed_duty_expanded_optimizer'):
            module = sys.modules[name]
            for key in ('BUS_COST_KX','CHARGE_START_COST'):
                if getattr(module,key) != fixture.EXPECTED_COSTS[key]:
                    fatal('Captured oracle cost constant differs: '+name+'.'+key)
            if hasattr(module,'charge_cost_premium') and module.charge_cost_premium != 1:
                fatal('Captured oracle price premium differs')
        report['loaded_sibling_python_paths_before_graph'] = loaded_sources()
        check()
        stage = 'literal_fixture_and_graph'
        pandas = sys.modules['pandas']
        problem, prices, plugs, duties, physics, descriptor = fixture.make_fixture(boundary,pandas)
        report.update(fixture_id=fixture.FIXTURE_ID, fixture=descriptor,
            sibling_source_revision=boundary.SOURCE_REVISION, sibling_root=str(boundary.REGISTERED))
        base = runner.CapacityTerminalNetwork
        network_type = boundary.make_fixed_duty_network_type(base,duties) if spec['arm'] == 'fixed_duty' else base
        graph_started = time.monotonic()
        net = boundary.construct(network_type,problem,prices,plugs=plugs,
            soc_step=physics['soc_step'],block_min=physics['block_min'],battery_kwh=physics['battery_kwh'],
            default_kw=physics['default_kw'],reserve_kwh=physics['reserve_kwh'],
            expected_costs=fixture.EXPECTED_COSTS,station_kw=physics['station_kw'])
        report['graph'] = dict(nodes=len(net.node_meta), alternatives=net.n_alternatives,
            constructor_wall_s=time.monotonic()-graph_started,
            soc_step=net.soc_step,event_block_min=net.block_min,power=net.power.record(),
            scope='Fresh referenced conservative event graph; no imported seeds/cache')
        check()
        stage = 'one_oracle_run'
        entered = time.monotonic()
        report['oracle_run_calls'] = 1
        summary = runner.run(net,folder/'oracle',target=80.,fleet_cap=2,cg_seconds=60.,mip_seconds=90.,
            batch_size=30,seeds=(),max_iters=100000,rc_eps=1e-6,viol_tol=1e-6,
            smoothing=0.,dive_seconds=0.,partial_pricing=None,directional=False,
            integer_pricing_seconds=0.,partition=True)
        report.update(oracle_run_completed=True,oracle_summary=summary,
            cg_certificate=summary.get('cg_pricing_certified'),oracle_elapsed_s=time.monotonic()-entered,
            native_optimize_calls_scope='Unknown: unchanged runner may perform multiple LP/MIP optimizes')
        report['loaded_sibling_python_paths_after_oracle'] = loaded_sources()
        check()
        selected_path = folder/'oracle/selected_routes.json'
        if not selected_path.is_file():
            report['failures'].append(dict(stage='selection',type='NoSelection',message='Unchanged runner returned no selected fleet; no retry'))
        else:
            stage = 'selected_physical_cost_capacity_validation'
            validation_started = time.monotonic()
            selected = json.loads(selected_path.read_bytes())
            if (len(selected) != 2 or Counter(t for record in selected for t in record['trips']) != Counter(problem.trips)
                    or spec['arm'] == 'fixed_duty' and sorted(tuple(r['trips']) for r in selected) != sorted(duties)):
                fatal('Selected fleet/partition/prescribed-duty contract differs',identity=True)
            realization = sys.modules['expanded_path_realization']
            validator = sys.modules['run_exact_pool_mip'].validate_injected_route
            capacity = sys.modules['capacity_event_pricer']
            grid_occ, continuous_occ = defaultdict(int),defaultdict(int)
            grid_loads = {s:[0.]*26 for s in boundary.BASES}
            continuous_loads = {s:[0.]*26 for s in boundary.BASES}
            grid_terminal = continuous_terminal = grid_cost = continuous_cost = 0.
            route_checks = []
            for record in selected:
                check()
                audited = runner.audit_energy(net,dict(record))
                realized,detail = realization.realize_expanded_path(problem,record,g_kwh=net.g,charge_kw=net.power,
                    reserve_kwh=net.reserve,soc_step=net.soc_step,block_min=net.block_min,time_model='event')
                if realized is None:
                    fatal('Selected route failed original realization: '+str(detail))
                reason = validator(problem,realized,net.g,net.power,net.reserve,boundary.HORIZON_MIN,arrival_grace_min=0.)
                if reason is not None:
                    fatal('Selected route failed original physical replay: '+str(reason))
                costs = realization.realized_costs(realized,detail['mapping'],station_prices=net.prices)
                if (not math.isclose(costs['recomputed_expanded_grid_cost'],record['cost'],rel_tol=1e-10,abs_tol=1e-6)
                        or not math.isclose(costs['continuous_realized_cost'],record['continuous_realized_cost'],rel_tol=1e-10,abs_tol=1e-6)):
                    fatal('Selected stored/recomputed grid or continuous cost differs')
                grid_cost += costs['recomputed_expanded_grid_cost']; continuous_cost += costs['continuous_realized_cost']
                grid_terminal += audited['terminal_energy_kwh']; continuous_terminal += audited['continuous_terminal_energy_kwh']
                for key,count in capacity.record_occupancy(record).items():
                    grid_occ[key] += count
                for block in costs['continuous_realized_charging_blocks']:
                    station = sys.modules['utils_v2'].base_station_name(block['station'])
                    hour = block['tariff_hour']
                    grid_loads[station][hour] += block['expanded_grid_kwh']
                    continuous_loads[station][hour] += block['realized_kwh']
                    if block['realized_kwh'] > 0:
                        first,last = capacity.occupied_range(block['start_min'],block['end_min'])
                        for minute in range(first,last+1):
                            continuous_occ[station,minute] += 1
                route_checks.append(dict(trips=record['trips'],physical_valid=True,
                    expanded_grid_terminal_kwh=audited['terminal_energy_kwh'],
                    continuous_terminal_kwh=audited['continuous_terminal_energy_kwh']))
            grid_over = {f'{s}:{m}':v for (s,m),v in grid_occ.items() if v > plugs[s]}
            continuous_over = {f'{s}:{m}':v for (s,m),v in continuous_occ.items() if v > plugs[s]}
            if grid_over or continuous_over or grid_terminal < 80.-1e-6 or continuous_terminal < 80.-1e-6:
                fatal('Selected shared occupancy/aggregate terminal-energy contract differs')
            report['selected_summary'] = dict(fleet=2,exact_service_once=True,
                prescribed_duties_preserved=sorted(tuple(r['trips']) for r in selected)==sorted(duties),
                route_checks=route_checks,grid_terminal_kwh=grid_terminal,continuous_terminal_kwh=continuous_terminal,
                expanded_grid_full_cost=grid_cost,continuous_full_cost=continuous_cost,
                expanded_grid_charging_cost=grid_cost-2*fixture.EXPECTED_COSTS['BUS_COST_KX'],
                continuous_charging_cost=continuous_cost-2*fixture.EXPECTED_COSTS['BUS_COST_KX'],
                expanded_grid_kwh=sum(sum(v) for v in grid_loads.values()),
                continuous_grid_kwh=sum(sum(v) for v in continuous_loads.values()),
                expanded_grid_hourly_station_kwh=grid_loads,continuous_hourly_station_kwh=continuous_loads,
                expanded_grid_shared_plug_violations=grid_over,continuous_shared_plug_violations=continuous_over,
                maximum_grid_plug_occupancy={s:max((v for (station,m),v in grid_occ.items() if station==s),default=0) for s in plugs},
                maximum_continuous_plug_occupancy={s:max((v for (station,m),v in continuous_occ.items() if station==s),default=0) for s in plugs},
                continuous_cost_pricing_certified=False,certificate_scope=summary.get('proof_scope'))
            write(folder/'selected-routes.json',selected)
            check()
            report['selected_validation_and_witness_publication_wall_s'] = time.monotonic()-validation_started
            report['physical_valid'] = True
    except Exception as exc:
        report['failures'].append(dict(stage=stage,type=type(exc).__name__,message=str(exc)))
        if isinstance(exc,ContractError) or not isinstance(exc,TimeoutError):
            report['config_failure'] = report['fatal_contract'] = True
    finally:
        usage,now = resource.getrusage(resource.RUSAGE_SELF),time.monotonic()
        report.update(receipt_complete=True,stop_signal=stopped,returned_monotonic=now,elapsed_s=now-anchor,
            method_endpoint_accepted=bool(report['physical_valid'] and not report['failures'] and not report['fatal_contract'] and stopped is None and now<end),
            resources=dict(user_s=usage.ru_utime,system_s=usage.ru_stime,cpu_s=usage.ru_utime+usage.ru_stime,
                peak_rss_bytes=usage.ru_maxrss if sys.platform=='darwin' else usage.ru_maxrss*1024,
                cpu_limit_s=240,wall_limit_s=240,rss_limit_bytes=5*1024**3,python_threads=threading.active_count()),
            interpretation='Posted-price synthetic by-reference composition; LP/event-grid, finite-pool MIP, realized fleet validity and continuous cost are distinct')
        write(folder/'receipt.json',report)
        signal.setitimer(signal.ITIMER_REAL,0)
    return 2 if report['fatal_contract'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
