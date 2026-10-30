"""Four exact-density conventional decisions; original physics and native seed17."""
import argparse
from fractions import Fraction as F
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
import time

CASES = ('scale:50685:40', 'scale:50605:80')
DECISIONS = ((CASES[0], 'CA1'), (CASES[0], 'CoverCA1'),
             (CASES[1], 'CoverCA1'), (CASES[1], 'CA1'))
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
sys.dont_write_bytecode = True


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value)
    os.replace(temporary, path)  # Only this process's own exclusive placeholder.


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value*1024)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    master = output/'receipt.json'
    save_new(master, {'complete': False, 'passed': False, 'failure': 'No final report published'})
    anchor, cpu0, stopped = time.monotonic(), time.process_time(), None
    hashes, sources = {}, set()
    report = {'complete': False, 'passed': False, 'cases': [], 'pid': os.getpid(),
        'objective': 'minimize vehicle count only; economic cost evaluated after replay',
        'scope': 'single-seed exact-density exposed-case control; no matched GNN or main60s qualification',
        'native_seed': 17, 'seed_policy': 'native model.seed=17 with explicit readback',
        'frozen_decisions': [{'ordinal': i, 'case': c, 'arm': a} for i, (c, a) in enumerate(DECISIONS, 1)],
        'scientific_qualification': False, 'repairs': 0, 'retries': 0, 'secondary_solves': 0}

    def check(deadline=None):
        if stopped is not None:
            raise TimeoutError('Retained package stop '+str(stopped))
        if time.process_time()-cpu0 >= 705 or time.monotonic()-anchor >= 585:
            raise TimeoutError('Package body705CPU/585wall exhausted; reserve15 for closure')
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('Prospective case stage deadline exhausted')
        if rss_bytes() > 5*1024**3 or threading.active_count() != 1:
            raise RuntimeError('Observed peakRSS5GiB or one-Python-thread condition failed')

    def read(path, expected=None, parse=True):
        check()
        path = path.resolve()
        name = str(path.relative_to(root))
        if name in hashes:
            raise ValueError('Repeated source/input read and hash: '+name)
        with path.open('rb') as stream:
            raw = stream.read(64*1024*1024+1)
        if len(raw) > 64*1024*1024:
            raise ValueError('Input/source exceeds64MiB')
        hashes[name] = hashlib.sha256(raw).hexdigest()
        if expected is not None and expected.get(name) != hashes[name]:
            raise ValueError('Historical context digest differs: '+name)
        return json.loads(raw) if parse else None

    def source_closure():
        for name, module in sorted(tuple(sys.modules.items())):
            if name == 'egglab' or name.startswith('egglab.') or name in ('experiments', 'experiments.codex_offline_rank'):
                filename = getattr(module, '__file__', None)
                if filename and filename.endswith('.py'):
                    path = Path(filename).resolve()
                    if not path.is_relative_to(root/'src'):
                        raise ValueError('Project module outside frozen worktree')
                    if path not in sources:
                        read(path, parse=False); sources.add(path)

    try:
        def stop(signum, frame):
            nonlocal stopped
            if stopped is None:
                stopped = signum
            raise TimeoutError('Offline density-control stop '+str(signum))
        resource.setrlimit(resource.RLIMIT_CPU, (720, 720))
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
            signal.signal(sig, stop)
        signal.alarm(600)
        read(Path(__file__), parse=False)
        read(Path(__file__).with_name('PROTOCOL.md'), parse=False)
        read(Path(__file__).with_name('RESOURCE_DECISION.md'), parse=False)
        read(Path(__file__).with_name('selector.py'), parse=False)
        old_pool_path = root/'research-20261025/matching_pool/pool.py'
        read(old_pool_path, parse=False)
        read(root/'research-20261025/matching_pool/NEXT_CONTROL_DECISION.md', parse=False)
        lock = read(root/'research-20261017/local-assets-v3.json')
        selected = tuple(min(c['case_key'] for c in lock['manifest']['cohorts']['screen']
            if c['services'] == size) for size in (40, 80))
        if selected != CASES:
            raise ValueError('Prospectively selected exposed screen cases differ')
        sys.path.insert(0, str(root/'src'))
        import selector
        import numpy
        import scipy
        if Path(selector.__file__).resolve() != Path(__file__).with_name('selector.py').resolve():
            raise RuntimeError('Selector module differs from consumed source')
        spec = importlib.util.spec_from_file_location('density_frozen_cover', old_pool_path)
        cover_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cover_module)
        from egglab import claude_cases, physical_learning_cases as bank
        from egglab import native_pathflow as pf, native_recharge as nr, native_hull as nh
        from egglab.constructive_charging import _row_signature
        import mip
        source_closure()
        optimizer, builder = pf._optimize_once, pf.build_feasible_model
        if optimizer is not nr._optimize_once:
            raise RuntimeError('Unexpected native hook; none is disabled or replaced')
        report.update(formulation=pf.FORMULATION, native_matrix=pf.NATIVE_MATRIX,
            selector_policy=selector.POLICY, frozen_cover_policy=cover_module.POLICY,
            extraction_policy=pf.EXTRACTION_POLICY, mip_version=getattr(mip, '__version__', None),
            numpy_version=numpy.__version__, scipy_version=scipy.__version__,
            native_bound_scope='candidate-pool-restricted fleet count, never unrestricted full-model bound')
        common = {}
        for ordinal, (case_key, arm) in enumerate(DECISIONS, 1):
            check()
            folder = output/('%02d-' % ordinal+case_key.replace(':', '-')+'-'+arm)
            folder.mkdir(exist_ok=False)
            target = folder/'receipt.json'
            case_anchor, case_cpu = time.monotonic(), time.process_time()
            preparation_end, native_end, case_end = case_anchor+30., case_anchor+90., case_anchor+120.
            save_new(target, {'complete': False, 'case': case_key, 'arm': arm, 'ordinal': ordinal})
            row = {'case': case_key, 'arm': arm, 'ordinal': ordinal,
                'case_anchor': case_anchor, 'case_deadline': case_end,
                'complete': False, 'physical_witness_valid': False, 'status': 'unresolved',
                'stages': [], 'failures': [], 'native_seed_requested': 17, 'native_seed_readback': None,
                'seed_policy': report['seed_policy']}
            events = (folder/'events.jsonl').open('x')
            stage, built = 'preparation', None
            def timed(label, operation):
                nonlocal stage
                stage = label
                at, cpu = time.monotonic(), time.process_time()
                try:
                    return operation()
                finally:
                    row['stages'].append({'stage': label, 'wall_s': time.monotonic()-at,
                        'cpu_s': time.process_time()-cpu, 'observed_peak_rss_bytes': rss_bytes()})
            def record(event):
                check(case_end)
                events.write(json.dumps(event, allow_nan=False)+'\n'); events.flush()
                check(case_end)
            try:
                case = timed('case_construction', lambda: claude_cases.make(case_key))
                mapping = lock['cases'][case_key]
                if case.identity() != mapping['identity'] or [m.id for m in case.movements] != mapping['movement_ids']:
                    raise ValueError('Original full case/movement mapping differs')
                market = bank.market(case, 'day')
                row.update(case_identity=case.identity(), market_identity=market.identity(), trips=len(case.trips))
                candidate = timed('fresh_CA1_and_selection', lambda: selector.select(case,
                    market.a, market.b, arm, cover_function=cover_module.candidate_pool,
                    check=lambda: check(preparation_end)))
                def save_selection():
                    save_new(folder/'selection.json', {key: value for key, value in candidate.items()
                        if key not in ('cover_ledger', 'mode_ledger')})
                    if candidate['cover_ledger'] is not None:
                        save_new(folder/'cover-ledger.json', candidate['cover_ledger'])
                    with (folder/'mode-ledger.jsonl').open('x') as stream:
                        for mode in candidate['mode_ledger']:
                            check(preparation_end)
                            stream.write(json.dumps(mode, allow_nan=False)+'\n')
                        stream.flush(); os.fsync(stream.fileno())
                timed('save_selection_ledgers', save_selection)
                retained = set(candidate['retained_movement_ids'])
                row['pool'] = {key: candidate[key] for key in ('policy', 'status', 'M', 'K',
                    'declared_movements', 'retained_movements', 'backbone_count', 'cover_flexible_count',
                    'protected_count', 'fill_count', 'ordinary_CA1_overlap', 'backbone_cover_overlap', 'mode_counts')}
                contract = (candidate['M'], candidate['K'], tuple(candidate['backbone_ids']), tuple(candidate['boundary_ids']))
                if case_key in common and common[case_key] != contract:
                    raise ValueError('Matched arms differ in common B/K/boundaries')
                common[case_key] = contract
                if candidate['status'] != 'selected':
                    raise ValueError('Design failure: B union cover exceeds unchanged K; no native dispatch')
                check(preparation_end)
                built = timed('full_physical_model', lambda: pf.build_feasible_model(case, 'GRB'))
                built['model'].seed = 17
                row['native_seed_readback'] = built['model'].seed
                if row['native_seed_readback'] != 17:
                    raise RuntimeError('Native seed17 assignment/readback failed')
                check(preparation_end)
                def inventory():
                    model = built['model']
                    count = built['constraint_count_before_objective']
                    if (built['physical_identity'] != case.identity() or built['compiled']['identity'] != case.identity()
                            or len(built['x']) != len(case.movements) or model.num_rows != count):
                        raise ValueError('Original physical matrix identity/count differs')
                    mapped = {v.idx for v in built['x']}
                    if len(mapped) != len(built['x']):
                        raise ValueError('Aliased movement variables')
                    variables = set()
                    with (folder/'physical-inventory.jsonl').open('x') as stream:
                        def emit(value):
                            check(preparation_end)
                            stream.write(json.dumps(value, allow_nan=False)+'\n')
                        emit({'kind': 'header', 'physical_rows': count, 'columns': model.num_cols,
                            'case_identity': case.identity(), 'backend_runtime': built['backend_runtime'],
                            'movement_ids': [m.id for m in case.movements], 'mapped_x': [v.idx for v in built['x']]})
                        def bound(value):
                            return {'value': float(value) if value is not None and math.isfinite(float(value)) else None,
                                'repr': repr(value)}
                        for var in model.vars:
                            if var.idx in variables or (var.idx not in mapped and str(var.var_type) != 'C'):
                                raise ValueError('Unexpected variable identity/type')
                            variables.add(var.idx)
                            if var.idx in mapped and (str(var.var_type) != 'B' or var.lb != 0 or var.ub != 1):
                                raise ValueError('Full routing binary was fixed or altered')
                            emit({'kind': 'variable', 'index': var.idx, 'name': var.name,
                                'type': str(var.var_type), 'lower': bound(var.lb), 'upper': bound(var.ub)})
                        if len(variables) != model.num_cols or not mapped <= variables:
                            raise ValueError('Incomplete variable inventory')
                        for physical in model.constrs:
                            emit({'kind': 'physical_row', 'signature': _row_signature(physical,
                                check=lambda: check(preparation_end))})
                        stream.flush(); os.fsync(stream.fileno())
                    return {'physical_rows': count, 'columns': model.num_cols, 'single_inventory': True}
                row['inventory'] = timed('one_physical_inventory', inventory)
                def restrict_bounds():
                    with (folder/'movement-bounds.jsonl').open('x') as stream:
                        for movement, var in zip(case.movements, built['x']):
                            check(preparation_end)
                            before = (var.lb, var.ub)
                            if before != (0, 1):
                                raise ValueError('Original routing bounds differ before pool restriction')
                            if movement.id not in retained:
                                var.ub = 0
                            expected_upper = 1 if movement.id in retained else 0
                            if str(var.var_type) != 'B' or var.lb != 0 or var.ub != expected_upper:
                                raise ValueError('Retained-free/excluded-zero routing invariant failed')
                            stream.write(json.dumps({'movement': movement.id, 'variable': var.idx,
                                'retained': movement.id in retained, 'before_lower': before[0],
                                'before_upper': before[1], 'after_lower': var.lb, 'after_upper': var.ub})+'\n')
                        stream.flush(); os.fsync(stream.fileno())
                timed('pool_upper_bound_restriction', restrict_bounds)
                fleet = mip.xsum(var for movement, var in zip(case.movements, built['x']) if movement.kind == 'pullout')
                built['model'].objective = fleet
                if (built['model'].num_rows != row['inventory']['physical_rows']
                        or built['model'].num_cols != row['inventory']['columns']):
                    raise ValueError('Fleet objective unexpectedly changed matrix dimensions')
                check(preparation_end)
                remaining = native_end-time.monotonic()
                budget = nr.Budget(backend='GRB', threads=1, phase_seconds=min(60., remaining),
                    wall_seconds=case_end-time.monotonic(), max_rounds=1)
                stats = timed('one_fleet_native_solve', lambda: pf._optimize_once(built, budget, native_end))
                row['native'] = stats
                row['native_bound_scope'] = report['native_bound_scope']
                check(native_end)
                if stats.get('threads') != 1:
                    raise RuntimeError('Native stage did not report one thread')
                if built['model'].seed != 17:
                    raise RuntimeError('Native seed17 changed during solve')
                if stats['status'] not in ('OPTIMAL', 'FEASIBLE') or not nr._finite(stats.get('incumbent')):
                    row['status'] = 'unresolved_native_no_admissible_incumbent'
                else:
                    timed('one_capture', lambda: save_new(folder/'native-capture.json', pf.capture_incumbent(case, built)))
                    check(case_end)
                    plan = timed('unchanged_extraction', lambda: pf._extract(case, built, record=record, round_index=0))
                    replay = timed('independent_replay', lambda: nr.replay_native(case, plan))
                    check(case_end)
                    selected = sum(1 for movement, var in zip(case.movements, built['x'])
                        if movement.kind == 'pullout' and var.x is not None and float(var.x) > .5)
                    vehicles = len(plan['vehicles'])
                    if (replay.get('replay_ok') is not True or selected != vehicles
                            or abs(stats['incumbent']-vehicles) > nr.BOUND_GUARD
                            or not {mid for vehicle in plan['vehicles'] for mid in vehicle['movements']} <= retained):
                        raise ValueError('Physical witness/native fleet objective differs')
                    bill = F(replay['ops_cost'])+nh.supply(market, replay['load'])
                    timed('save_physical_witness', lambda: (save_new(folder/'plan.json', plan),
                        save_new(folder/'replay.json', replay)))
                    check(case_end)
                    row.update(status='replayed_density_control_witness', physical_witness_valid=True,
                        vehicles=vehicles, integrated_cost_exact=str(bill), fleet_objective_tolerance=nr.BOUND_GUARD,
                        witness_ready_monotonic=time.monotonic())
            except Exception as exc:
                row['status'] = 'failed_or_unresolved'
                row['failures'].append({'stage': stage, 'type': type(exc).__name__, 'message': str(exc)})
            finally:
                events.flush(); os.fsync(events.fileno()); events.close()
                row.update(complete=True, elapsed_before_receipt_s=time.monotonic()-case_anchor,
                    cpu_before_receipt_s=time.process_time()-case_cpu, observed_peak_rss_bytes=rss_bytes())
                publish(target, row)
            elapsed = time.monotonic()-case_anchor
            report['cases'].append({'case': case_key, 'arm': arm, 'ordinal': ordinal, 'status': row['status'],
                'receipt': str(target.relative_to(root)), 'elapsed_including_receipt_s': elapsed,
                'cpu_including_receipt_s': time.process_time()-case_cpu,
                'accepted_within_offline120': row['physical_witness_valid'] and elapsed <= 120.,
                'physical_witness_valid': row['physical_witness_valid'], 'vehicles': row.get('vehicles'),
                'integrated_cost_exact': row.get('integrated_cost_exact'), 'pool': row.get('pool'),
                'declared_matrix': row.get('inventory'), 'native_bound_scope': row.get('native_bound_scope'),
                'native_seed_readback': row['native_seed_readback']})
            if pf._optimize_once is not optimizer or pf.build_feasible_model is not builder:
                raise RuntimeError('Unexpected native hook mutation stops this package')
            del built
            source_closure()
        check()
        report.update(complete=True, passed=True,
            feasible_decisions=sum(c['accepted_within_offline120'] for c in report['cases']))
    except BaseException as exc:
        report.update(passed=False, failure={'type': type(exc).__name__, 'message': str(exc)})
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report.update(stop_signal=stopped, input_source_sha256=hashes, cpu_s=time.process_time()-cpu0,
            wall_s=time.monotonic()-anchor, observed_peak_rss_bytes=rss_bytes(),
            rusage={'utime_s': usage.ru_utime, 'stime_s': usage.ru_stime,
                'maxrss_platform_units': usage.ru_maxrss, 'platform': sys.platform},
            budget={'cpu_s': 720, 'wall_s': 600, 'case_s': 120, 'preparation_s': 30,
                'native_deadline_s': 90, 'native_cap_s': 60, 'capture_replay_final_s': 30},
            interpretation='Diagnostic completion is not feasibility of both cases, unrestricted optimality or a paired performance result')
        publish(master, report)
        signal.alarm(0)
    print(json.dumps({'complete': report['complete'], 'passed': report['passed'],
        'feasible_decisions': report.get('feasible_decisions'), 'receipt': str(master)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
