"""Fixed witnessed-plan catalog repricing. Stdlib only; never optimization."""
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
import time

EPS = Q(1, 1_000_000)
ARMS = {'v8': 60, 'catboost_v5': 60, 'nonlearned': 60, 'random': 59, 'full4': 44, 'cold': 59}


def finite(x):
    if type(x) not in (int, float) or not math.isfinite(x) or x < 0:
        raise ValueError('Nonfinite, negative or nonnumeric stored scalar')
    return Q.from_float(float(x))


def median(values):
    values = sorted(values)
    n = len(values)
    return None if not n else (values[n//2] if n % 2 else (values[n//2-1]+values[n//2])/2)


def signs(values):
    counts = Counter('positive' if x > 0 else 'negative' if x < 0 else 'zero' for x in values)
    return {name: counts[name] for name in ('positive', 'negative', 'zero')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError('Exclusive output already exists: '+str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    wall0, cpu0 = time.monotonic(), time.process_time()
    with output.open('x') as stream:
        json.dump({'passed': False, 'incomplete': True, 'pid': os.getpid(),
            'failure': {'type': 'IncompleteAnalysis', 'message': 'No complete final result published'}}, stream)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    hashes, report = {}, {'passed': False, 'scientific_qualification': False,
        'scope': 'posthoc fixed replay-valid development catalog; no adaptive charging, optimization or causality',
        'optimizer_calls': 0, 'model_calls': 0, 'training_calls': 0, 'threads': 1}

    def check():
        if time.process_time()-cpu0 > 115 or time.monotonic()-wall0 > 175:
            raise TimeoutError('Analysis body CPU115/wall175 exhausted; retain5s publication reserve')

    def read(path, expected=None, *, parse=True):
        check()
        path = path.resolve()
        name = str(path.relative_to(root))
        if name in hashes:
            raise ValueError('Repeated input read/hash: '+name)
        with path.open('rb') as stream:
            raw = stream.read(64*1024*1024+1)
        if len(raw) > 64*1024*1024:
            raise ValueError('Bounded JSON/source input exceeds64MiB: '+name)
        digest = hashlib.sha256(raw).hexdigest()
        hashes[name] = digest
        if expected is not None and expected.get(name) != digest:
            raise ValueError('Historical replay-audit input digest differs: '+name)
        return json.loads(raw) if parse else None

    try:
        def expired(signum, frame):
            raise TimeoutError('Analysis wall180 alarm expired')
        resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
        signal.signal(signal.SIGALRM, expired)
        signal.alarm(180)
        if threading.active_count() != 1:
            raise RuntimeError('Analysis requires one Python thread')
        read(Path(__file__), parse=False)
        read(Path(__file__).with_name('PROTOCOL.md'), parse=False)
        audit = read(root/'research-20261017/FINAL_REPLAY_VERIFICATION.json')
        summary = read(root/'research-20261017/screen-analysis-v3-final/summary.json')
        if (audit.get('passed') is not True or audit.get('mismatch_count') != 0
                or audit.get('supervisor_valid_endpoints') != 342
                or summary.get('complete') is not True or summary.get('planned') != 360
                or summary.get('stage') != 'screen' or summary.get('development_only') is not True):
            raise ValueError('Incomplete or mismatched authoritative completed-development evidence')
        admitted = {(r['case_key'], r['solver_seed'], r['arm']): r for r in audit['records']}
        a = tuple(finite(.10 if 10 <= t < 14 else .30) for t in range(30))
        mean, b = sum(a)/30, finite(1/900)
        tariffs = {'day': a, 'flat': (mean,)*30,
            'late': tuple(finite(.10 if 22 <= t < 26 else .30) for t in range(30)),
            **{'shift'+('%+d' % k): tuple(a[(t-k) % 30] for t in range(30)) for k in (6, -6)}}
        if any(sum(prices)/30 != mean for prices in tariffs.values()) or len(set(tariffs.values())) != 5:
            raise ValueError('Mean-preserving tariff identity failed')
        rows, seen, scheduled = [], set(), Counter()
        for cell in summary['cells']:
            task, directory = cell['task'], cell['directory']
            key = (task['case_key'], task['seed'], task['arm'])
            if key in seen or len(directory) != 20 or any(c not in '0123456789abcdef' for c in directory):
                raise ValueError('Duplicate task or noncanonical task folder')
            seen.add(key); scheduled[task['arm']] += 1
            parts = task['case_key'].split(':')
            if (len(parts) != 3 or parts[0] != 'scale' or not 50000 <= int(parts[1]) <= 50999
                    or parts[2] not in ('40', '80') or task['seed'] not in (17, 41, 73)):
                raise ValueError('Non-inspected synthetic-development task')
            if not cell['valid']:
                continue
            record = admitted[key]
            if not all(record.get(k) is True for k in ('supervisor_valid', 'replay_pass', 'exact_bill_match')) or record.get('issues'):
                raise ValueError('Endpoint missing independent historical admission')
            folder = root/'research-20261017/local-screen-v3'/directory
            result = read(folder/'result.json', audit['input_sha256'])
            replay = read(folder/'replay.json', audit['input_sha256'])
            sup = read(folder/'supervisor.json', audit['input_sha256'])
            if (result['task'] != task or result.get('accepted_valid') is not True
                    or replay.get('replay_ok') is not True or sup.get('endpoint_valid') is not True
                    or sup.get('endpoint_censored') is not False or sup.get('failure')
                    or sup.get('returncode') != 0 or sup.get('missing_worker_receipt')):
                raise ValueError('Stored admission flags disagree')
            loads = tuple(finite(x) for x in replay['load'])
            ops, vehicles = finite(replay['ops_cost']), result['vehicles']
            if (len(loads) != 30 or type(vehicles) is not int or vehicles <= 0
                    or ops != 100*vehicles or abs(float(sum(loads))-float(finite(replay['grid_kwh']))) > 1e-6):
                raise ValueError('Period-energy/fleet accounting differs')
            row = dict(case=key[0], seed=key[1], arm=key[2], directory=directory,
                size=int(parts[2]), fleet=vehicles, load=loads, ops=ops,
                original_load=replay['load'], original_ops=replay['ops_cost'])
            row['parts'] = {name: (ops, mean*sum(loads), sum((p-mean)*x for p, x in zip(prices, loads)),
                b*sum(x*x for x in loads)/2) for name, prices in tariffs.items()}
            row['cost'] = {name: sum(value) for name, value in row['parts'].items()}
            if row['cost']['day'] != Q(result['bill_exact']):
                raise ValueError('Independent exact original-day bill mismatch')
            rows.append(row)
        if (len(seen) != 360 or any(scheduled[arm] != 60 for arm in ARMS)
                or dict(Counter(r['arm'] for r in rows)) != ARMS):
            raise ValueError('Completed cohort/valid denominators differ')
        by_case = defaultdict(list)
        for row in rows:
            by_case[row['case']].append(row)
        if len(by_case) != 20 or Counter(r[0]['size'] for r in by_case.values()) != {40: 10, 80: 10}:
            raise ValueError('Timetable grouping differs')
        tie = lambda r: (r['arm'], r['seed'], r['directory'])
        catalogs, objectives = [], []
        for case, available in sorted(by_case.items()):
            check()
            nmin = min(r['fleet'] for r in available)
            for scope, bank in (('minimum_observed_fleet', [r for r in available if r['fleet'] == nmin]), ('all_fleet', available)):
                original = min(bank, key=lambda r: (r['cost']['day'], tie(r)))
                bounds = [(r['cost']['day']-original['cost']['day'])/sum(abs(x-y) for x, y in zip(r['load'], original['load']))
                    for r in bank if r['load'] != original['load']] if scope == 'minimum_observed_fleet' else []
                radius = min(bounds) if bounds else None
                for tariff in tariffs:
                    best = min(bank, key=lambda r: (r['cost'][tariff], tie(r)))
                    regret = original['cost'][tariff]-best['cost'][tariff]
                    delta = tuple(x-y for x, y in zip(original['parts'][tariff], best['parts'][tariff]))
                    if regret < 0 or sum(delta) != regret:
                        raise ValueError('Catalog regret/additive identity failed')
                    catalogs.append(dict(case=case, size=available[0]['size'], scope=scope, tariff=tariff,
                        candidate_count=len(bank), distinct_loads=len({r['load'] for r in bank}),
                        minimum_observed_fleet=nmin, day_winner=original['directory'], target_winner=best['directory'],
                        changed_over_1e_6=regret > EPS, regret=regret,
                        relative_regret=regret/original['cost'][tariff],
                        component_delta=delta, catalog_price_stability_radius=radius,
                        radius_scope='minimum observed fleet catalog only; null on all-fleet sensitivity'))
                for tariff in ('day', 'late'):
                    welfare = min(bank, key=lambda r: (r['cost'][tariff], tie(r)))
                    payment = lambda r: r['cost'][tariff] + r['parts'][tariff][3]
                    pay_best = min(bank, key=lambda r: (payment(r), tie(r)))
                    welfare_loss = pay_best['cost'][tariff]-welfare['cost'][tariff]
                    payment_gain = payment(welfare)-payment(pay_best)
                    components = tuple(x-y for x, y in zip(pay_best['parts'][tariff], welfare['parts'][tariff]))
                    if welfare_loss < 0 or payment_gain < 0 or sum(components) != welfare_loss:
                        raise ValueError('Catalog welfare/payment comparison identity failed')
                    objectives.append(dict(case=case, size=available[0]['size'], scope=scope, tariff=tariff,
                        planner_winner=welfare['directory'], payment_winner=pay_best['directory'],
                        identity_changed=welfare['directory'] != pay_best['directory'],
                        welfare_loss_over_1e_6=welfare_loss > EPS, planner_minimum=welfare['cost'][tariff],
                        payment_choice_welfare_cost=pay_best['cost'][tariff], welfare_loss=welfare_loss,
                        planner_choice_payment=payment(welfare), payment_minimum=payment(pay_best),
                        payment_gain=payment_gain, welfare_component_delta=components))
        pairs, eligibility, grouping = [], Counter(), defaultdict(list)
        lookup = {(r['case'], r['seed'], r['arm']): r for r in rows}
        for case in sorted(by_case):
            for seed in (17, 41, 73):
                for control in ('nonlearned', 'catboost_v5'):
                    graph, other = lookup.get((case, seed, 'v8')), lookup.get((case, seed, control))
                    status = 'missing_valid_endpoint' if graph is None or other is None else 'unequal_fleet' if graph['fleet'] != other['fleet'] else 'equal_fleet'
                    eligibility[(control, status)] += 1
                    if status != 'equal_fleet':
                        continue
                    for tariff in tariffs:
                        delta = tuple(x-y for x, y in zip(other['parts'][tariff], graph['parts'][tariff]))
                        gain = other['cost'][tariff]-graph['cost'][tariff]
                        if sum(delta) != gain or delta[0] != 0:
                            raise ValueError('Equal-fleet paired additive identity failed')
                        pairs.append(dict(case=case, size=graph['size'], seed=seed, control=control,
                            tariff=tariff, bill_gain=gain, relative_gain=gain/other['cost'][tariff], component_delta=delta))
                        grouping[(case, graph['size'], control, tariff)].append(gain/other['cost'][tariff])
        groups = [dict(case=k[0], size=k[1], control=k[2], tariff=k[3], pairs=len(v), median_relative_gain=median(v)) for k, v in sorted(grouping.items())]
        aggregates = []
        for size in (40, 80):
            for control in ('nonlearned', 'catboost_v5'):
                for tariff in tariffs:
                    selected = [g for g in groups if (g['size'], g['control'], g['tariff']) == (size, control, tariff)]
                    values = [g['median_relative_gain'] for g in selected]
                    exact = [p['bill_gain'] for p in pairs if (p['size'], p['control'], p['tariff']) == (size, control, tariff)]
                    aggregates.append(dict(size=size, control=control, tariff=tariff, groups=len(values),
                        paired_cells=len(exact), median_group_relative_gain=median(values),
                        exact_pair_sign_counts=signs(exact), exact_group_sign_counts=signs(values)))
        report.update(passed=True, admitted_endpoints=len(rows), cases=len(by_case),
            tariffs=tariffs, curvature_b=b, original_tariff='day',
            component_order=['fleet_ops', 'mean_price_energy', 'linear_timing', 'curvature'],
            catalog_results=catalogs, objective_comparisons=objectives,
            admitted_rows=[dict(case=r['case'], seed=r['seed'], arm=r['arm'], directory=r['directory'],
                vehicles=r['fleet'], ops_cost=r['original_ops'], load=r['original_load'], bill_exact=r['cost']['day']) for r in rows],
            exact_number_encoding='rational strings reconstructing stored finite binary64 numbers',
            admitted_row_load_encoding='original stored JSON numeric values; use Fraction.from_float for exact reconstruction',
            pair_eligibility=[dict(control=k[0], status=k[1], count=v) for k, v in sorted(eligibility.items())],
            paired_cells=pairs, group_medians=groups, aggregates=aggregates)
        check()
    except BaseException as exc:
        report.update(passed=False, failure={'type': type(exc).__name__, 'message': str(exc)})
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        report.update(input_sha256=hashes, cpu_s=time.process_time()-cpu0,
            incomplete=False, pid=os.getpid(),
            wall_s=time.monotonic()-wall0, rusage={'utime_s': usage.ru_utime, 'stime_s': usage.ru_stime,
                'maxrss_platform_units': usage.ru_maxrss, 'platform': sys.platform},
            active_python_threads=threading.active_count(),
            timing_scope='through report preparation; parent meter includes encoding, write and exit',
            budget={'cpu_s': 120, 'wall_s': 180, 'body_cpu_s': 115, 'body_wall_s': 175,
                'publication_reserve_s': 5, 'check': 'cooperative body plus RLIMIT_CPU120/SIGALRM180; no children'},
            caveats=['observed finite catalog only; no global optimum or full stability certificate',
                'fixed stored routes and charging; tariff-only changes preserve historical physical witnesses',
                'pooled seed plans are hindsight options, not independent timetables or a deployed selector',
                'minimum observed fleet selection may leave one candidate and hide missing tariff options',
                'planner-vs-payment comparison assumes exogenous marginal supply curve and no equilibrium',
                'no new-data generalization, learned tariff attribution or strategic-cost claim'])
        temporary = output.with_name(output.name+'.final.tmp')
        with temporary.open('x') as stream:
            json.dump(report, stream, indent=2, default=lambda x: str(x) if isinstance(x, Q) else x, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, output)  # Replace only this process's exclusively created incomplete result.
        signal.alarm(0)
    print(json.dumps({'passed': report['passed'], 'output': str(output), 'cpu_s': report['cpu_s']}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
