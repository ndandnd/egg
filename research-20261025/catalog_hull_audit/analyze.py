"""One-start convexification of an admitted finite fixed-plan catalog only."""
import time

PROCESS_WALL0 = time.monotonic()
PROCESS_CPU0 = time.process_time()

import argparse
from collections import Counter, defaultdict
from fractions import Fraction as Q
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading


class BudgetExhausted(TimeoutError):
    pass


def stored_number(value):
    if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
        raise ValueError('Expected a finite nonnegative original JSON number')
    return Q.from_float(float(value))


def dot(left, right):
    return sum((x*y for x, y in zip(left, right)), Q(0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError('Exclusive output already exists: '+str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(passed=False, scientific_qualification=False,
        scope='convex relaxation of observed minimum-fleet development catalogs only',
        full_problem_bounds=False, full_price_certificate=False, equilibrium=False,
        model_calls=0, scheduling_solver_calls=0, replay_calls=0,
        native_owner_calls=0, raw_source_reads=0, sealed_source_reads=0,
        optimizer_calls=0, cells=[], banks=[], planned_cells=120)
    hashes, planned, done = {}, [], set()
    body_wall0 = body_cpu0 = None
    body_wall_end = body_cpu_end = None
    pools = None

    def expired(signum, frame):
        raise BudgetExhausted('Total-process CPU soft limit or wall alarm reached')

    def check():
        if threading.active_count() != 1:
            raise RuntimeError('More than one Python thread')
        wall, cpu = time.monotonic(), time.process_time()
        if cpu-PROCESS_CPU0 > 70 or wall-PROCESS_WALL0 > 100:
            raise BudgetExhausted('Total body/startup allowance exhausted; publication reserve5')
        if body_wall_end is not None and (wall > body_wall_end or cpu > body_cpu_end):
            raise BudgetExhausted('Body CPU60/wall90 allowance exhausted')

    def consume(path, *, parse=False):
        check()
        path = path.resolve()
        name = str(path.relative_to(root))
        if name in hashes:
            raise ValueError('Repeated consumed-file read/hash: '+name)
        with path.open('rb') as stream:
            raw = stream.read(64*1024*1024+1)
        if len(raw) > 64*1024*1024:
            raise ValueError('Consumed file exceeds64MiB')
        hashes[name] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw) if parse else None

    try:
        resource.setrlimit(resource.RLIMIT_CPU, (70, 75))
        signal.signal(signal.SIGXCPU, expired)
        signal.signal(signal.SIGALRM, expired)
        signal.signal(signal.SIGTERM, expired)
        signal.signal(signal.SIGINT, expired)
        signal.setitimer(signal.ITIMER_REAL, max(.001, 105-(time.monotonic()-PROCESS_WALL0)))
        for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS'):
            os.environ[variable] = '1'
        import numpy as np
        from scipy.optimize import minimize
        from threadpoolctl import threadpool_info, threadpool_limits
        pools = threadpool_limits(limits=1)
        pool_info = threadpool_info()
        if any(pool.get('num_threads') != 1 for pool in pool_info):
            raise RuntimeError('Native computation thread limit not one')
        report['native_thread_pools'] = [dict(internal_api=p.get('internal_api'),
            num_threads=p.get('num_threads'), version=p.get('version')) for p in pool_info]
        consume(Path(__file__))
        consume(Path(__file__).with_name('PROTOCOL.md'))
        source = consume(root/'research-20261025/price_signal_audit/results.json', parse=True)
        if (source.get('passed') is not True or source.get('admitted_endpoints') != 342
                or source.get('cases') != 20):
            raise ValueError('Upstream admitted development audit incomplete')
        report['inherited_price_audit_input_sha256'] = source.get('input_sha256', {})
        report['upstream_cpu_s'] = source.get('cpu_s')
        report['upstream_objective_comparisons'] = dict(
            location='price_signal_audit/results.json:objective_comparisons',
            original_curvature_only=True, newly_computed_here=False)
        tariffs = {name: tuple(Q(x) for x in source['tariffs'][name]) for name in ('day', 'late')}
        original_b = Q(source['curvature_b'])
        if (any(len(a) != 30 or any(x < 0 for x in a) for a in tariffs.values())
                or original_b <= 0):
            raise ValueError('Invalid upstream tariff or curvature')
        rows = source['admitted_rows']
        if len(rows) != 342:
            raise ValueError('Expected exactly342 admitted endpoint rows')
        by_case, seen = defaultdict(list), set()
        for row in rows:
            check()
            case, directory = row['case'], row['directory']
            parts = case.split(':')
            if (len(parts) != 3 or parts[0] != 'scale' or not 50000 <= int(parts[1]) <= 50999
                    or parts[2] not in ('40', '80') or len(directory) != 20
                    or any(x not in '0123456789abcdef' for x in directory)
                    or directory in seen or type(row['vehicles']) is not int or row['vehicles'] <= 0
                    or row['seed'] not in (17, 41, 73)
                    or row['arm'] not in ('v8', 'catboost_v5', 'nonlearned', 'random', 'full4', 'cold')):
                raise ValueError('Unexpected admitted row identity')
            seen.add(directory)
            loads = tuple(stored_number(x) for x in row['load'])
            ops = stored_number(row['ops_cost'])
            if len(loads) != 30 or ops != 100*row['vehicles']:
                raise ValueError('Unexpected load length or observed fleet-cost accounting')
            original_cost = ops+dot(tariffs['day'], loads)+original_b*dot(loads, loads)/2
            if original_cost != Q(row['bill_exact']):
                raise ValueError('Upstream admitted row original bill differs')
            by_case[case].append(dict(fleet=row['vehicles'], ops=ops, load=loads,
                alias=dict(directory=directory, arm=row['arm'], seed=row['seed'])))
        if (len(by_case) != 20
                or Counter(int(case.split(':')[2]) for case in by_case) != {40: 10, 80: 10}):
            raise ValueError('Expected original twenty timetable groups')
        report.update(admitted_endpoints=len(rows), cases=len(by_case))
        objectives = source.get('objective_comparisons', [])
        for case in by_case:
            for tariff in tariffs:
                for scope in ('minimum_observed_fleet', 'all_fleet'):
                    entries = [r for r in objectives if (r.get('case'), r.get('tariff'), r.get('scope'))
                        == (case, tariff, scope)]
                    if len(entries) != 1:
                        raise ValueError('Upstream original-curvature payment comparison missing/duplicate')
        body_wall0, body_cpu0 = time.monotonic(), time.process_time()
        if body_wall0-PROCESS_WALL0 > 10 or body_cpu0-PROCESS_CPU0 > 10:
            raise BudgetExhausted('Startup exceeds10s of combined15s startup/publication allowance')
        body_wall_end, body_cpu_end = body_wall0+90, body_cpu0+60
        report['original_curvature_b'] = original_b
        report['tariffs'] = tariffs
        for case in sorted(by_case):
            for tariff in tariffs:
                for multiplier in (0, 1, 5):
                    planned.append((case, tariff, multiplier))
        for case, available in sorted(by_case.items()):
            check()
            fleet = min(row['fleet'] for row in available)
            selected = [row for row in available if row['fleet'] == fleet]
            deduplicated = {}
            for row in selected:
                check()
                deduplicated.setdefault((row['ops'], row['load']), []).append(row['alias'])
            bank = [dict(ops=key[0], load=key[1], aliases=aliases)
                for key, aliases in deduplicated.items()]
            costs, loads = [r['ops'] for r in bank], [r['load'] for r in bank]
            costs_np = np.asarray([float(x) for x in costs], dtype=float)
            loads_np = np.asarray([[float(x) for x in load] for load in loads], dtype=float)
            check()
            differences = loads_np-loads_np[0]
            singular = np.linalg.svd(differences, compute_uv=False)
            check()
            energy = singular*singular
            if not np.all(np.isfinite(singular)) or not np.all(np.isfinite(energy)):
                raise ValueError('Nonfinite load-variation descriptor')
            total_energy = float(energy.sum())
            rank_tolerance = max(differences.shape)*np.finfo(float).eps*float(singular[0])
            if total_energy:
                shares = energy[energy > 0]/total_energy
                effective_rank = float(np.exp(-np.sum(shares*np.log(shares))))
                dimensions95 = int(np.searchsorted(np.cumsum(energy), .95*total_energy)+1)
            else:
                effective_rank, dimensions95 = 0.0, 0
            descriptor = dict(method='binary64 SVD of rows L_j-L_0; descriptor only',
                singular_values=singular.tolist(), numerical_rank=int(np.sum(singular > rank_tolerance)),
                numerical_rank_tolerance=rank_tolerance, squared_energy_dimensions95=dimensions95,
                squared_energy_entropy_effective_rank=effective_rank)
            report['banks'].append(dict(case=case, size=int(case.split(':')[2]),
                admitted_rows=len(available), minimum_observed_fleet=fleet,
                minimum_fleet_rows=len(selected), deduplicated_candidates=len(bank),
                candidates=[dict(index=j, **row) for j, row in enumerate(bank)],
                load_difference_descriptor=descriptor))
            for tariff, a in tariffs.items():
                for multiplier in (0, 1, 5):
                    key = (case, tariff, multiplier)
                    cell = dict(case=case, tariff=tariff, curvature_multiplier=multiplier,
                        curvature_b=multiplier*original_b, candidate_count=len(bank),
                        minimum_observed_fleet=fleet, passed=False,
                        numerical_catalog_qualification=False)
                    try:
                        check()
                        b = multiplier*original_b
                        pure = [c+dot(a, load)+b*dot(load, load)/2 for c, load in zip(costs, loads)]
                        best_pure = min(pure)
                        if b == 0:
                            weights = [Q(int(j == pure.index(best_pure))) for j in range(len(bank))]
                            optimizer = dict(method='exact linear minimum vertex', success=True,
                                calls=0, iterations=0)
                        else:
                            a_np, b_float = np.asarray([float(x) for x in a]), float(b)

                            def objective(x):
                                check()
                                z = x @ loads_np
                                return float(costs_np @ x+a_np @ z+.5*b_float*(z @ z))

                            def gradient(x):
                                check()
                                return costs_np+loads_np @ (a_np+b_float*(x @ loads_np))

                            def equality(x):
                                check()
                                return float(np.sum(x)-1)

                            def equality_gradient(x):
                                check()
                                return np.ones_like(x)

                            report['optimizer_calls'] += 1
                            cell['optimizer'] = dict(method='SLSQP', calls=1, success=False,
                                status=None, initial_point='uniform', maxiter=300, ftol=1e-12,
                                retries=0, returned=False)
                            result = minimize(objective, np.full(len(bank), 1.0/len(bank)),
                                method='SLSQP', jac=gradient, bounds=[(0., 1.)]*len(bank),
                                constraints=[dict(type='eq', fun=equality, jac=equality_gradient)],
                                callback=lambda x: check(), options=dict(maxiter=300, ftol=1e-12))
                            check()
                            raw = np.asarray(result.x, dtype=float)
                            optimizer = dict(method='SLSQP', calls=1, success=bool(result.success),
                                status=int(result.status), message=str(result.message),
                                iterations=int(result.nit), function_evaluations=int(result.nfev),
                                raw_weights=[float(x) if math.isfinite(float(x)) else repr(float(x))
                                    for x in raw.flat], initial_point='uniform', maxiter=300,
                                ftol=1e-12, retries=0, returned=True)
                            cell['optimizer'] = optimizer
                            if raw.shape != (len(bank),) or not np.all(np.isfinite(raw)):
                                raise ValueError('Optimizer returned nonfinite or wrong-length weights')
                            clipped = np.maximum(raw, 0.)
                            if not math.isfinite(float(clipped.sum())) or float(clipped.sum()) <= 0:
                                raise ValueError('No positive finite clipped weight mass')
                            normalized = clipped/clipped.sum()
                            rational = [Q.from_float(float(x)) for x in normalized]
                            mass = sum(rational)
                            weights = [x/mass for x in rational]
                            cell['weight_repair'] = dict(raw_min=float(raw.min()), raw_max=float(raw.max()),
                                clipped_negative_count=int(np.sum(raw < 0)),
                                exact_normalization_mass=mass)
                        if sum(weights) != 1 or any(x < 0 for x in weights):
                            raise ValueError('Rationalized mixture is not exactly feasible')
                        cbar = dot(weights, costs)
                        lbar = []
                        for period in range(30):
                            check()
                            lbar.append(sum((weight*load[period] for weight, load in zip(weights, loads)), Q(0)))
                        upper = cbar+dot(a, lbar)+b*dot(lbar, lbar)/2
                        price = [x+b*y for x, y in zip(a, lbar)]
                        affine = [c+dot(price, load) for c, load in zip(costs, loads)]
                        eta = min(affine)
                        lower = eta-sum(((p-x)**2 for p, x in zip(price, a)), Q(0))/(2*b) if b else eta
                        locs, distances = [], []
                        for value, linear, load in zip(pure, affine, loads):
                            check()
                            loc = linear-eta
                            distance = sum(((x-y)**2 for x, y in zip(load, lbar)), Q(0))
                            if loc < 0 or value-lower != loc+b*distance/2:
                                raise ValueError('Exact pure-minus-dual LOC/distance identity failed')
                            locs.append(loc)
                            distances.append(distance)
                        expected_pure = dot(weights, pure)
                        variance = dot(weights, distances)
                        if (expected_pure-upper != b*variance/2 or upper < lower
                                or best_pure < lower or best_pure <= 0):
                            raise ValueError('Exact Jensen or catalog bound identity failed')
                        if b == 0 and (upper != lower or lower != best_pure):
                            raise ValueError('Exact linear vertex optimum identity failed')
                        tolerance = Q(1, 1_000_000)*(1+abs(upper))
                        qualified = upper-lower <= tolerance
                        cell.update(passed=optimizer['success'] and qualified, optimizer=optimizer,
                            optimizer_failure=None if optimizer['success'] else
                                dict(status=optimizer.get('status'), message=optimizer.get('message')),
                            exact_mixture_feasible=True, exact_identity_checks_passed=True,
                            numerical_catalog_qualification=qualified,
                            qualification_failure=None if qualified else 'Exact catalog gap exceeds frozen tolerance',
                            qualification_tolerance=tolerance, catalog_upper=upper, catalog_lower=lower,
                            catalog_optimization_gap=upper-lower, best_pure=best_pure,
                            best_pure_indices=[j for j, value in enumerate(pure) if value == best_pure],
                            pure_minus_hull_gap_interval=[best_pure-upper, best_pure-lower],
                            relative_gap_interval=[(best_pure-upper)/best_pure, (best_pure-lower)/best_pure],
                            weights=weights, support_indices=[j for j, weight in enumerate(weights) if weight > 0],
                            mixture_ops=cbar, mixture_load=lbar, marginal_price=price, eta=eta,
                            catalog_loc=locs, squared_load_distance=distances,
                            weighted_pure_cost=expected_pure, weighted_squared_load_variance=variance,
                            exact_jensen_gap=expected_pure-upper)
                    except BudgetExhausted as exc:
                        cell['failure'] = dict(type=type(exc).__name__, message=str(exc))
                        raise
                    except Exception as exc:
                        cell['failure'] = dict(type=type(exc).__name__, message=str(exc))
                    finally:
                        report['cells'].append(cell)
                        done.add(key)
        check()
        if any(pool.get('num_threads') != 1 for pool in threadpool_info()):
            raise RuntimeError('Native computation thread count changed')
        report['passed'] = len(report['cells']) == 120 and all(c['passed'] for c in report['cells'])
    except BaseException as exc:
        report['failure'] = dict(type=type(exc).__name__, message=str(exc))
    finally:
        signal.signal(signal.SIGXCPU, signal.SIG_IGN)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        if children.ru_utime != 0 or children.ru_stime != 0 or threading.active_count() != 1:
            report['passed'] = False
            report['resource_failure'] = 'Unexpected waited child CPU or Python thread count'
        report.update(input_sha256=hashes, exact_number_encoding='rational strings; original binary64 inputs reconstructed exactly',
            completed_cells=len(report['cells']), qualified_cells=sum(c['numerical_catalog_qualification'] for c in report['cells']),
            analysis_completed=len(report['cells']) == 120 and all(c.get('exact_identity_checks_passed') for c in report['cells']),
            numerical_catalog_qualification=len(report['cells']) == 120 and all(c['numerical_catalog_qualification'] for c in report['cells']),
            failed_cells=sum(not c['passed'] for c in report['cells']),
            unprocessed_cell_count=120-len(report['cells']),
            unprocessed_cells=[dict(case=c, tariff=t, curvature_multiplier=b) for c, t, b in planned if (c, t, b) not in done],
            cpu_s=time.process_time()-PROCESS_CPU0, wall_s=time.monotonic()-PROCESS_WALL0,
            startup_cpu_s=None if body_cpu0 is None else body_cpu0-PROCESS_CPU0,
            startup_wall_s=None if body_wall0 is None else body_wall0-PROCESS_WALL0,
            body_cpu_s=None if body_cpu0 is None else time.process_time()-body_cpu0,
            body_wall_s=None if body_wall0 is None else time.monotonic()-body_wall0,
            rusage=dict(utime_s=usage.ru_utime, stime_s=usage.ru_stime,
                maxrss_platform_units=usage.ru_maxrss, platform=sys.platform,
                waited_child_utime_s=children.ru_utime, waited_child_stime_s=children.ru_stime),
            active_python_threads=threading.active_count(),
            timing_scope='through report preparation; parent meter charges encoding/write/exit',
            budget=dict(body_cpu_s=60, body_wall_s=90, total_cpu_hard_s=75,
                total_cpu_soft_s=70, total_wall_alarm_s=105, startup_limit_s=10,
                publication_reserve_s=5, combined_startup_final_allowance_s=15),
            caveats=['finite observed bank only; not full-problem upper/lower bounds',
                'fractional mixtures are catalog relaxations, not executable fractional fleets',
                'minimum observed fleet and pooled arm/seed plans are hindsight selection',
                'no equilibrium, full-price certificate, causality, ML generalization or new theorem',
                'load SVD describes this catalog only; curvature scaling changes no physical witness',
                'optimizer failures and unqualified cells are retained without retry'])
        payload = json.dumps(report, indent=2, default=lambda value: str(value) if isinstance(value, Q) else value,
            allow_nan=False)
        with output.open('x') as stream:
            stream.write(payload+'\n')
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(dict(passed=report['passed'], output=str(output), cells=report['completed_cells'],
        qualified_cells=report['qualified_cells'], cpu_s=report['cpu_s'])))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
