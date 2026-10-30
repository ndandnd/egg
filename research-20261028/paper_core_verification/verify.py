"""One paid exact comparison; only new source/configuration inputs are consumed."""
import argparse
import copy
from fractions import Fraction as F
import hashlib
import json
import os
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


def encode(value):
    if isinstance(value, F):
        return str(value)
    raise TypeError(type(value).__name__)


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, default=encode)
        f.write('\n')


def canonical_optima(value):
    return sorted((o['partition'], o['early'], o['late'], o['ops'],
                   o['objective'], o['prices'], o['own_price_regret'],
                   tuple(sorted((s['partition'], s['early_interval'])
                                for s in o['response_minimizer_sets'])))
                  for o in value['physical_optima'])


def compare(baseline, candidate):
    assert baseline['D'] == candidate['D'], 'physical objective mismatch'
    assert baseline['CH'] == candidate['CH'], 'hull objective mismatch'
    assert canonical_optima(baseline) == canonical_optima(candidate), 'optimum/deviation set mismatch'
    if baseline['D'] is None:
        assert not candidate['positive_gap'] and candidate['hull_early'] is None
    else:
        assert baseline['D'] >= baseline['CH']
        assert (baseline['D'] > baseline['CH']) == candidate['positive_gap']
        assert {o['early'] for o in baseline['hull_min_points']} == {candidate['hull_early']}
        assert all(o['own_price_regret'] >= baseline['D']-baseline['CH']
                   for o in baseline['physical_optima'])


def rejected(name, action, rows):
    try:
        action()
    except (AssertionError, ValueError):
        rows.append(dict(id=name, rejected=True))
    else:
        rows.append(dict(id=name, rejected=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    started, cpu = time.monotonic(), time.process_time()
    # A small fixed CPU cap is independent of any native solver return.
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    rows, controls, failures = [], [], []
    specs = []
    try:
        assert not sys.flags.optimize, 'assertions must be enabled'
        cached, manifest = {}, {}
        for name in SOURCES:
            path = HERE/name
            data = path.read_bytes()
            rel = path.relative_to(ROOT).as_posix()
            committed = subprocess.check_output(
                ['git', '--no-pager', '-c', 'pack.threads=1', 'show', args.source_revision+':'+rel],
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
        assert len(specs) == 20 and len({s['id'] for s in specs}) == 20
        by_id = {}
        for spec in specs:
            K, fee = F(spec['K']), F(spec['fee'])
            row = dict(spec=spec, status='ATTEMPTED', baseline=None, candidate=None)
            rows.append(row)
            before = time.monotonic()
            row['baseline'] = baseline(K, fee)
            row['baseline_elapsed_s'] = time.monotonic()-before
            before = time.monotonic()
            row['candidate'] = change(K, fee)
            row['candidate_elapsed_s'] = time.monotonic()-before
            try:
                compare(row['baseline'], row['candidate'])
                row['status'] = 'PASS'
            except AssertionError as exc:
                row.update(status='FAIL', failure=str(exc))
                failures.append(spec['id']+': '+str(exc))
            by_id[spec['id']] = row
        nominal = by_id['nominal-smoke']
        b = nominal['baseline']
        assert (b['D'], b['CH'], b['D']-b['CH']) == (F(97), F(7591,80), F(169,80))
        assert [o['own_price_regret'] for o in b['physical_optima']] == [F(13)]
        controls.append(dict(id='nominal-independent-arithmetic-smoke', pass_check=True))
        altered = copy.deepcopy(nominal['candidate'])
        altered['D'] += 1
        rejected('changed-objective', lambda: compare(b, altered), controls)
        tie = by_id['planner-tie-large-capacity']
        altered_tie = copy.deepcopy(tie['candidate'])
        assert len(altered_tie['physical_optima']) == 2
        altered_tie['physical_optima'].pop()
        rejected('erased-planner-tie', lambda: compare(tie['baseline'], altered_tie), controls)
        flat = by_id['vertex-zero-fee-flat-response']
        altered_flat = copy.deepcopy(flat['candidate'])
        interval = next(s for s in altered_flat['physical_optima'][0]['response_minimizer_sets']
                        if s['partition'] == 'A|B')
        assert interval['early_interval'][0] < interval['early_interval'][1]
        interval['early_interval'] = (interval['early_interval'][0],)*2
        rejected('omitted-flat-response-interval', lambda: compare(flat['baseline'], altered_flat), controls)
        opt = b['physical_optima'][0]
        validator = modules['reference']['_validate_witness']
        for kind in ('missing-terminal-charge', 'wrong-service-bus', 'excessive-power'):
            witness = copy.deepcopy(opt['witness'])
            if kind == 'missing-terminal-charge':
                witness['charges'].pop()
            elif kind == 'wrong-service-bus':
                _, start, end = witness['services'][0]
                witness['services'][0] = ('UNKNOWN', start, end)
            else:
                bus, start, end, power = witness['charges'][0]
                witness['charges'][0] = (bus, start, end, power+1)
            rejected(kind, lambda w=witness: validator('AB', F(10), F(30), w), controls)
        for name, func in [('baseline', baseline), ('candidate', change)]:
            for K, fee in [(F(-1), F(7)), (F(31), F(7)), (F(30), F(-1))]:
                rejected(name+'-domain-'+str((K,fee)), lambda fn=func,k=K,f=fee: fn(k,f), controls)
        failures.extend(c['id'] for c in controls if c.get('rejected') is False)
    except BaseException as exc:
        failures.append(type(exc).__name__+': '+str(exc))
    attempted = {r['spec']['id'] for r in rows}
    for spec in specs:
        if spec['id'] not in attempted:
            rows.append(dict(spec=spec,status='UNATTEMPTED',reason='earlier fatal failure'))
    report = dict(status='PASS' if len(rows)==20 and not failures else 'FAIL',
                  assigned=20, attempted=sum(r['status']!='UNATTEMPTED' for r in rows),
                  unattempted=20-sum(r['status']!='UNATTEMPTED' for r in rows),
                  passed=sum(r['status']=='PASS' for r in rows),
                  failures=failures, rows=rows, controls=controls,
                  scope='Exact deterministic synthetic implementation qualification, not population evidence')
    write(out/'results.json', report)
    table = ['# Exact comparison — generated inline from results.json rows', '',
             '|Case|K|Fee|D|CH|Gap|Planner optima|Own-price regrets|Status|',
             '|---|---:|---:|---:|---:|---:|---|---|---|']
    for r in rows:
        spec, base = r['spec'], r.get('baseline')
        if base and base['D'] is not None:
            vals = [str(base['D']),str(base['CH']),str(base['D']-base['CH']),
                    ', '.join(o['partition'] for o in base['physical_optima']),
                    ', '.join(str(o['own_price_regret']) for o in base['physical_optima'])]
        else:
            vals = ['—']*5
        table.append('|'+ '|'.join([spec['id'],spec['K'],spec['fee']]+vals+[r['status']])+'|')
    with (out/'TABLE.md').open('x') as f:
        f.write('\n'.join(table)+'\n')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux reports KiB.
    if sys.platform != 'darwin':
        rss *= 1024
    observed_self_cpu = time.process_time()
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    observed_child_cpu = child_usage.ru_utime+child_usage.ru_stime
    inclusive_cpu = observed_self_cpu+observed_child_cpu
    resource_pass = inclusive_cpu < 15 and rss <= 512*1024**2
    write(out/'worker_receipt.json', dict(status=report['status'], elapsed_s=time.monotonic()-started,
          self_cpu_s=observed_self_cpu, waited_children_cpu_s=observed_child_cpu,
          inclusive_cpu_observed_s=inclusive_cpu, resource_pass=resource_pass,
          peak_rss_bytes=rss, memory_observation_pass=rss <= 512*1024**2,
          exclusions=[], self_cpu_limit_s=10, inclusive_worker_allowance_s=15, owner_wall_limit_s=20,
          note='prepublication observations; external POSIX meter covers full owner'))
    return 0 if report['status']=='PASS' and resource_pass else 1


if __name__ == '__main__':
    raise SystemExit(main())
