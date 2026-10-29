"""One frozen exact comparison, with hash-on-consumption source capture."""
import argparse
import copy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = ('reference.py', 'candidate.py', 'verify.py', 'run.py', 'cases.json',
           'PROTOCOL.md', 'PROOF.md')
DECLARED_IDS = ('baseline', 'movement', 'B22', 'B22.6', 'B22.7', 'B23',
                'B25', 'B30', 'B25-fee8', 'B25-fee9', 'B25-fee10.5',
                'B25-fee11', 'B25-fee12-tie', 'B25-fee13')


def encode(value):
    if isinstance(value, F):
        return str(value)
    raise TypeError(type(value).__name__)


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, default=encode)
        stream.write('\n')


def normalized_sets(sets):
    groups = {}
    for s in sets:
        groups.setdefault((s['total_energy'], s['ops']), []).append(tuple(s['early_interval']))
    answer = []
    for (energy, ops), intervals in groups.items():
        merged = []
        for lo, hi in sorted(set(intervals)):
            assert lo <= hi
            if merged and lo <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
            else:
                merged.append((lo, hi))
        answer.extend((interval, energy, ops) for interval in merged)
    return tuple(sorted(answer))


def canonical_optima(result):
    return tuple(sorted({(o['early'], o['late'], o['ops'], tuple(o['prices']),
                          o['regret'], normalized_sets(o['response_sets']))
                         for o in result['physical_optima']}))


def compare(reference, candidate):
    assert reference['D'] == candidate['D'], 'physical objective mismatch'
    assert reference['CH'] == candidate['CH'], 'hull objective mismatch'
    assert sorted(set(map(tuple, reference['hull_points']))) == sorted(set(map(tuple, candidate['hull_points']))), 'hull minimizer mismatch'
    assert canonical_optima(reference) == canonical_optima(candidate), 'physical optimum or continuous response mismatch'
    assert reference['old_plan_regret'] == candidate['old_plan_regret'], 'old plan regret mismatch'
    assert reference['D'] >= reference['CH']
    assert all(o['regret'] >= reference['D']-reference['CH'] for o in reference['physical_optima'])


def rejected(name, action, controls):
    try:
        action()
    except (AssertionError, ValueError):
        controls.append(dict(id=name, rejected=True))
    else:
        controls.append(dict(id=name, rejected=False))


def _kwargs(spec):
    return dict(B=None if spec.get('B') is None else F(spec['B']),
                fee=None if spec.get('fee') is None else F(spec['fee']),
                detour=spec.get('detour', False))


def _fixed_cases(specs):
    expected = {(None, None, False), (None, None, True)}
    expected.update((F(b), F(7), False) for b in ('22', '22.6', '22.7', '23', '25', '30'))
    expected.update((F(25), F(h), False) for h in ('8', '9', '10.5', '11', '12', '13'))
    actual = {tuple(_kwargs(s)[k] for k in ('B', 'fee', 'detour')) for s in specs}
    assert len(specs) == 14 and len({s['id'] for s in specs}) == 14 and actual == expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    rows, controls, failures = [], [], []
    specs = [dict(id=name) for name in DECLARED_IDS]
    try:
        assert not sys.flags.optimize, 'assertions must be enabled'
        cached, manifest = {}, {}
        for name in SOURCES:
            path = HERE/name
            data = path.read_bytes()
            committed = subprocess.check_output(
                ['git', '--no-pager', '-c', 'pack.threads=1', 'show',
                 args.source_revision+':'+path.relative_to(ROOT).as_posix()],
                cwd=ROOT, timeout=.5)
            if committed != data:
                raise ValueError('Frozen source mismatch: '+name)
            cached[name] = data
            manifest[name] = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        write(out/'source_manifest.json', dict(revision=args.source_revision,
              sources=manifest, python=sys.version, platform=platform.platform(),
              dependencies='stdlib only; no solver', thread_configuration=1))
        modules = {}
        for name in ('reference', 'candidate'):
            namespace = {'__name__':name, '__file__':str(HERE/(name+'.py'))}
            exec(compile(cached[name+'.py'], namespace['__file__'], 'exec'), namespace)
            modules[name] = namespace
        baseline, change = modules['reference']['evaluate'], modules['candidate']['evaluate']
        specs = json.loads(cached['cases.json'])['cases']
        _fixed_cases(specs)
        assert tuple(s['id'] for s in specs) == DECLARED_IDS
        for spec in specs:
            row = dict(spec=spec, status='ATTEMPTED', baseline=None, candidate=None)
            rows.append(row)
            before = time.monotonic()
            row['baseline'] = baseline(**_kwargs(spec))
            row['baseline_elapsed_s'] = time.monotonic()-before
            before = time.monotonic()
            row['candidate'] = change(**_kwargs(spec))
            row['candidate_elapsed_s'] = time.monotonic()-before
            try:
                compare(row['baseline'], row['candidate'])
                row['status'] = 'PASS'
            except AssertionError as exc:
                row.update(status='FAIL', failure=str(exc))
                failures.append(spec['id']+': '+str(exc))
        def select(B, fee, detour=False):
            return next(r for r in rows if _kwargs(r['spec']) == dict(B=B, fee=fee, detour=detour))
        nominal = select(None, None)
        b = nominal['baseline']
        assert (b['D'], b['CH'], b['old_plan_regret']) == (F(97), F(7591,80), F(13))
        controls.append(dict(id='nominal-arithmetic-smoke', pass_check=True))
        altered = copy.deepcopy(nominal['candidate'])
        altered['D'] += 1
        rejected('corrupt-objective', lambda: compare(b, altered), controls)
        tie = select(F(25), F(12))
        altered = copy.deepcopy(tie['candidate'])
        assert len(canonical_optima(altered)) == 2
        point = altered['physical_optima'][0]
        altered['physical_optima'] = [o for o in altered['physical_optima']
                                    if (o['early'],o['late'],o['ops']) != (point['early'],point['late'],point['ops'])]
        rejected('erase-tie', lambda: compare(tie['baseline'], altered), controls)
        flat = select(F(25), F(7))
        altered = copy.deepcopy(flat['candidate'])
        changed = False
        for opt in altered['physical_optima']:
            for response in opt['response_sets']:
                lo, hi = response['early_interval']
                if lo < hi:
                    response['early_interval'] = (lo, lo)
                    changed = True
        assert changed
        rejected('collapse-flat-response', lambda: compare(flat['baseline'], altered), controls)
        validator = modules['reference']['replay']
        branch = next(br for br in b['branches'] if br['label'] == b['physical_optima'][0]['label'])
        opt = b['physical_optima'][0]
        for kind in ('remove-terminal-charge', 'wrong-service', 'excess-power'):
            witness = copy.deepcopy(opt['witness'])
            if kind == 'remove-terminal-charge':
                witness['charges'].pop()
            elif kind == 'wrong-service':
                bus, start, end, power = witness['services'][0]
                witness['services'][0] = (99, start, end, power)
            else:
                bus, start, end, power = witness['charges'][0]
                witness['charges'][0] = (bus, start, end, power+1)
            rejected(kind, lambda w=witness: validator(branch, opt['early'], w), controls)
        movement = select(None, None, True)['baseline']
        moving_branch = next(br for br in movement['branches'] if br['w'] == 2 and br['raw'])
        witness = copy.deepcopy(moving_branch['endpoints'][0]['witness'])
        bus, start, end, power = witness['movements'][0]
        witness['movements'][0] = (bus, start+F(1,100), end+F(1,100), power)
        rejected('wrong-movement-timing', lambda: validator(moving_branch, moving_branch['raw'][0][0], witness), controls)
        for name, fn in [('reference', baseline), ('candidate', change)]:
            for i, kwargs in enumerate([dict(B=19,fee=7), dict(B=31,fee=7),
                                       dict(B=25,fee=6), dict(B=25), dict(fee=7)]):
                rejected(name+'-domain-'+str(i), lambda f=fn,k=kwargs: f(**k), controls)
        failures.extend(c['id'] for c in controls if c.get('rejected') is False)
    except BaseException as exc:
        failures.append(type(exc).__name__+': '+str(exc))
        if rows and rows[-1]['status'] == 'ATTEMPTED':
            rows[-1].update(status='FAIL',failure=type(exc).__name__+': '+str(exc))
    attempted = {r['spec']['id'] for r in rows}
    for spec in specs:
        if spec['id'] not in attempted:
            rows.append(dict(spec=spec, status='UNATTEMPTED', reason='earlier fatal failure'))
    report = dict(status='PASS' if len(rows)==14 and not failures else 'FAIL',
                  assigned=14, attempted=sum(r['status']!='UNATTEMPTED' for r in rows),
                  unattempted=14-sum(r['status']!='UNATTEMPTED' for r in rows),
                  passed=sum(r['status']=='PASS' for r in rows), failures=failures,
                  rows=rows, controls=controls,
                  scope='Exact synthetic theorem-consequence and implementation qualification; no empirical cohort or speedup claim')
    write(out/'results.json', report)
    table = ['# Exact support extension comparison', '',
             '|Case|D|CH|Gap|Physical optimum points|Regrets|Status|',
             '|---|---:|---:|---:|---|---|---|']
    for row in rows:
        base = row.get('baseline')
        vals = [str(base['D']),str(base['CH']),str(base['D']-base['CH']),
                str(sorted({(o['early'],o['late'],o['ops']) for o in base['physical_optima']})),
                str(sorted({o['regret'] for o in base['physical_optima']}))] if base else ['—']*5
        table.append('|'+ '|'.join([row['spec']['id']]+vals+[row['status']])+'|')
    with (out/'TABLE.md').open('x') as stream:
        stream.write('\n'.join(table)+'\n')
    usage, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    rss = usage.ru_maxrss*(1 if sys.platform == 'darwin' else 1024)
    own_cpu, child_cpu = usage.ru_utime+usage.ru_stime, children.ru_utime+children.ru_stime
    elapsed = time.monotonic()-started
    resource_pass = own_cpu+child_cpu < 45 and elapsed < 60 and rss <= 512*1024**2
    write(out/'worker_receipt.json', dict(status=report['status'], elapsed_s=elapsed,
          self_cpu_s=own_cpu, waited_children_cpu_s=child_cpu,
          inclusive_cpu_observed_s=own_cpu+child_cpu, resource_pass=resource_pass,
          peak_rss_bytes=rss, memory_observation_pass=rss <= 512*1024**2,
          exclusions=[], self_cpu_limit_s=40, inclusive_worker_allowance_s=45,
          owner_worker_wall_limit_s=60, note='prepublication; external meter covers full owner'))
    return 0 if report['status']=='PASS' and resource_pass else 1


if __name__ == '__main__':
    raise SystemExit(main())
