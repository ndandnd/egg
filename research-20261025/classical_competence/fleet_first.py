"""One global fleet-count solve on each of two exposed development cases."""
import argparse
from fractions import Fraction as F
import hashlib
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
        'scope': 'exposed-case offline competence; no matched GNN or main60s qualification',
        'native_seed': None, 'seed_policy': 'backend default, unmodified; numeric default unknown',
        'scientific_qualification': False, 'repairs': 0, 'retries': 0, 'secondary_solves': 0}

    def check(deadline=None):
        if stopped is not None:
            raise TimeoutError('Retained package stop '+str(stopped))
        if time.process_time()-cpu0 >= 345 or time.monotonic()-anchor >= 285:
            raise TimeoutError('Package body345CPU/285wall exhausted; reserve15 for closure')
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
            if name == 'egglab' or name.startswith('egglab.'):
                filename = getattr(module, '__file__', None)
                if filename and filename.endswith('.py'):
                    path = Path(filename).resolve()
                    if not path.is_relative_to(root/'src/egglab'):
                        raise ValueError('Project module outside frozen worktree')
                    if path not in sources:
                        read(path, parse=False); sources.add(path)

    try:
        def stop(signum, frame):
            nonlocal stopped
            if stopped is None:
                stopped = signum
            raise TimeoutError('Offline fleet-first stop '+str(signum))
        resource.setrlimit(resource.RLIMIT_CPU, (360, 360))
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
            signal.signal(sig, stop)
        signal.alarm(300)
        read(Path(__file__), parse=False)
        read(Path(__file__).with_name('NEXT_BASELINE_PROTOCOL.md'), parse=False)
        read(Path(__file__).with_name('STATIC_DIAGNOSIS.md'), parse=False)
        lock = read(root/'research-20261017/local-assets-v3.json')
        summary = read(root/'research-20261017/screen-analysis-v3-final/summary.json')
        audit = read(root/'research-20261017/FINAL_REPLAY_VERIFICATION.json')
        if not summary.get('complete') or not audit.get('passed') or audit.get('mismatch_count') != 0:
            raise ValueError('Historical development context incomplete')
        selected = tuple(min(c['case_key'] for c in lock['manifest']['cohorts']['screen']
            if c['services'] == size) for size in (40, 80))
        if selected != CASES:
            raise ValueError('Prospectively selected exposed screen cases differ')
        context = {}
        for case_key in CASES:
            candidates = [c for c in summary['cells'] if c['task']['case_key'] == case_key
                and c['task']['seed'] == 17 and c['task']['arm'] == 'v8' and c['valid']]
            if len(candidates) != 1:
                raise ValueError('Unique historical graph context missing')
            cell = candidates[0]
            folder = root/'research-20261017/local-screen-v3'/cell['directory']
            old = read(folder/'result.json', audit['input_sha256'])
            sup = read(folder/'supervisor.json', audit['input_sha256'])
            if (old['task'] != cell['task'] or old.get('accepted_valid') is not True
                    or sup.get('endpoint_valid') is not True or sup.get('endpoint_censored') is not False):
                raise ValueError('Historical graph context admission differs')
            context[case_key] = {'vehicles': old['vehicles'], 'objective_exact': old['bill_exact'],
                'directory': cell['directory'], 'seed': 17, 'interpretation': 'unmatched reused-case context only'}
        sys.path.insert(0, str(root/'src'))
        from egglab import claude_cases, physical_learning_cases as bank
        from egglab import native_pathflow as pf, native_recharge as nr, native_hull as nh
        from egglab.constructive_charging import _row_signature
        import mip
        source_closure()
        optimizer, builder = pf._optimize_once, pf.build_feasible_model
        if optimizer is not nr._optimize_once:
            raise RuntimeError('Unexpected native hook; none is disabled or replaced')
        report.update(formulation=pf.FORMULATION, native_matrix=pf.NATIVE_MATRIX,
            extraction_policy=pf.EXTRACTION_POLICY, mip_version=getattr(mip, '__version__', None),
            old_greedy_context={'scale:50685:40': '15 independently replayed vehicles',
                'scale:50605:80': '29 constructed vehicles; no independently timely admitted endpoint'})
        for case_key in CASES:
            check()
            folder = output/case_key.replace(':', '-')
            folder.mkdir(exist_ok=False)
            target = folder/'receipt.json'
            case_anchor, case_cpu = time.monotonic(), time.process_time()
            preparation_end, native_end, case_end = case_anchor+30., case_anchor+90., case_anchor+120.
            save_new(target, {'complete': False, 'case': case_key})
            row = {'case': case_key, 'case_anchor': case_anchor, 'case_deadline': case_end,
                'complete': False, 'physical_witness_valid': False, 'status': 'unresolved',
                'stages': [], 'failures': [], 'native_seed': None,
                'seed_policy': report['seed_policy'], 'historical_graph_context': context[case_key]}
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
                check(preparation_end)
                built = timed('full_physical_model', lambda: pf.build_feasible_model(case, 'GRB'))
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
                check(native_end)
                if stats.get('threads') != 1:
                    raise RuntimeError('Native stage did not report one thread')
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
                            or abs(stats['incumbent']-vehicles) > nr.BOUND_GUARD):
                        raise ValueError('Physical witness/native fleet objective differs')
                    bill = F(replay['ops_cost'])+nh.supply(market, replay['load'])
                    timed('save_physical_witness', lambda: (save_new(folder/'plan.json', plan),
                        save_new(folder/'replay.json', replay)))
                    check(case_end)
                    old = F(context[case_key]['objective_exact'])
                    row.update(status='replayed_fleet_first_witness', physical_witness_valid=True,
                        vehicles=vehicles, integrated_cost_exact=str(bill), fleet_objective_tolerance=nr.BOUND_GUARD,
                        unmatched_relative_cost_context=str((old-bill)/old), witness_ready_monotonic=time.monotonic())
            except Exception as exc:
                row['status'] = 'failed_or_unresolved'
                row['failures'].append({'stage': stage, 'type': type(exc).__name__, 'message': str(exc)})
            finally:
                events.flush(); os.fsync(events.fileno()); events.close()
                row.update(complete=True, elapsed_before_receipt_s=time.monotonic()-case_anchor,
                    cpu_before_receipt_s=time.process_time()-case_cpu, observed_peak_rss_bytes=rss_bytes())
                publish(target, row)
            elapsed = time.monotonic()-case_anchor
            report['cases'].append({'case': case_key, 'status': row['status'],
                'receipt': str(target.relative_to(root)), 'elapsed_including_receipt_s': elapsed,
                'cpu_including_receipt_s': time.process_time()-case_cpu,
                'accepted_within_offline120': row['physical_witness_valid'] and elapsed <= 120.,
                'physical_witness_valid': row['physical_witness_valid'], 'vehicles': row.get('vehicles'),
                'integrated_cost_exact': row.get('integrated_cost_exact')})
            if pf._optimize_once is not optimizer or pf.build_feasible_model is not builder:
                raise RuntimeError('Unexpected native hook mutation stops this package')
            del built
            source_closure()
        check()
        report.update(complete=True, passed=True,
            feasible_cases=sum(c['accepted_within_offline120'] for c in report['cases']))
    except BaseException as exc:
        report.update(passed=False, failure={'type': type(exc).__name__, 'message': str(exc)})
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report.update(stop_signal=stopped, input_source_sha256=hashes, cpu_s=time.process_time()-cpu0,
            wall_s=time.monotonic()-anchor, observed_peak_rss_bytes=rss_bytes(),
            rusage={'utime_s': usage.ru_utime, 'stime_s': usage.ru_stime,
                'maxrss_platform_units': usage.ru_maxrss, 'platform': sys.platform},
            budget={'cpu_s': 360, 'wall_s': 300, 'case_s': 120, 'preparation_s': 30,
                'native_deadline_s': 90, 'native_cap_s': 60, 'capture_replay_final_s': 30},
            interpretation='Diagnostic completion is not feasibility of both cases, economic optimality or a paired performance result')
        publish(master, report)
        signal.alarm(0)
    print(json.dumps({'complete': report['complete'], 'passed': report['passed'],
        'feasible_cases': report.get('feasible_cases'), 'receipt': str(master)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
