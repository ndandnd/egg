"""One frozen exact qualification; no native backend or historical inputs."""
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
SOURCES = ('reference.py','candidate.py','verify.py','run.py','cases.json','PROTOCOL.md')
IDS = ('crossmatching-gap','crossmatching-boundary','crossmatching-large-fee',
       'zero-thresholds','positive-threshold-assignment-ties','three-per-batch-gap',
       'three-per-batch-boundary','flat-price-responses')
LITERALS = (((5,15),(14,15),'7'),((5,15),(14,15),'81/10'),
            ((5,15),(14,15),'13'),((4,6),(7,9),'7'),
            ((18,16),(10,11),'7'),((3,11,17),(8,12,13),'5'),
            ((3,11,17),(8,12,13),'32/5'),((8,9,10),(10,11,12),'7'))


def encode(value):
    if isinstance(value,F):
        return str(value)
    raise TypeError(type(value).__name__)


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,default=encode)
        stream.write('\n')


def pairs(value):
    return tuple(sorted(tuple(p) for p in value))


def responses(value):
    return tuple(sorted((pairs(s['pairs']),tuple(s['early_interval']),s['total_energy'],
                         s['ops'],s['price_cost']) for s in value['response_sets']))


def optimum(value):
    return (value['early'],value['late'],value['ops'],value['value'],
            tuple(value['prices']),value['regret'],responses(value))


def section(constraints,E,n,enumerate_vertices):
    constraints = list(constraints)+[
        dict(row=(F(1),)*n,rhs=E),dict(row=(F(-1),)*n,rhs=-E)]
    return tuple(enumerate_vertices(n,constraints))


def box_constraints(lower,upper,n):
    assert len(lower) == len(upper) == n
    constraints = []
    for i,(lo,hi) in enumerate(zip(lower,upper)):
        assert lo <= hi, 'inverted allocation bound'
        unit = tuple(F(j == i) for j in range(n))
        constraints.extend([dict(row=unit,rhs=hi),dict(row=tuple(-x for x in unit),rhs=-lo)])
    return constraints


def compare(reference,candidate,n,enumerate_vertices):
    assert reference['D'] == candidate['D'], 'physical objective mismatch'
    assert reference['CH'] == candidate['CH'], 'hull objective mismatch'
    gap = reference['D']-reference['CH']
    assert gap == candidate['gap'] and gap >= 0, 'gap mismatch'
    assert (gap > 0) == candidate['positive_gap'], 'support criterion mismatch'
    hull = lambda v: sorted((h['early'],h['late'],h['ops'],h['value']) for h in v['hull_optima'])
    assert hull(reference) == hull(candidate), 'hull minimizer mismatch'
    raw = {pairs(a['pairs']):a for a in reference['assignments']}
    analytic = {pairs(a['pairs']):a for a in candidate['assignments']}
    assert len(raw) == reference['rawcount'] == len(analytic) == candidate['rawcount'], 'assignment count mismatch'
    assert set(raw) == set(analytic), 'complete crossmatching set mismatch'
    for key,a in raw.items():
        assert tuple(a['interval']) == tuple(analytic[key]['interval']) and a['ops'] == analytic[key]['ops'], 'assignment projection mismatch'
        constraints = box_constraints(analytic[key]['lower'],analytic[key]['upper'],n)
        assert tuple(a['vertices']) == tuple(enumerate_vertices(n,constraints)), 'complete assignment allocation polytope mismatch'
    thresholds = [min(a['interval'][0] for key,a in raw.items() if len(key) == m) for m in range(n+1)]
    assert thresholds == candidate['matching_thresholds'], 'matching DP threshold mismatch'
    r_opts = {pairs(o['pairs']):o for o in reference['physical_optima']}
    c_opts = {pairs(o['pairs']):o for o in candidate['physical_optima']}
    assert len(r_opts) == len(reference['physical_optima']) and len(c_opts) == len(candidate['physical_optima']), 'duplicate optimum assignment'
    assert set(r_opts) == set(c_opts), 'optimal assignment tie mismatch'
    for key,r in r_opts.items():
        c = c_opts[key]
        assert optimum(r) == optimum(c), 'optimal values/prices/regrets/response sets mismatch'
        assert r['regret'] >= gap, 'regret lower inequality'
        if gap == 0:
            assert r['regret'] == 0, 'quadratic optimum unsupported at zero gap'
        raw_set = r['allocation_set']
        assert tuple(raw_set['sum_equality'][0]) == (F(1),)*n and raw_set['sum_equality'][1] == r['early']
        box = c['allocation_set']
        assert box['sum'] == c['early'] and len(box['lower']) == len(box['upper']) == n
        constraints = box_constraints(box['lower'],box['upper'],n)
        reference_vertices = section(raw_set['inequalities'],r['early'],n,enumerate_vertices)
        candidate_vertices = section(constraints,c['early'],n,enumerate_vertices)
        assert reference_vertices and reference_vertices == candidate_vertices, 'continuous allocation polytope mismatch'


def rejected(name,action,controls):
    try:
        action()
    except (AssertionError,ValueError):
        controls.append(dict(id=name,rejected=True))
    else:
        controls.append(dict(id=name,rejected=False))


def arguments(spec):
    return dict(A=tuple(map(F,spec['A'])),B=tuple(map(F,spec['B'])),fee=F(spec['fee']))


def admit_cases(specs):
    assert len(specs) == 8 and tuple(s['id'] for s in specs) == IDS, 'case denominator/order changed'
    for spec,(A,B,fee) in zip(specs,LITERALS):
        assert arguments(spec) == dict(A=tuple(map(F,A)),B=tuple(map(F,B)),fee=F(fee)), 'literal case changed'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--source-revision',required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    specs = [dict(id=name) for name in IDS]
    rows,controls,failures = [],[],[]
    try:
        assert not sys.flags.optimize, 'assertions must remain enabled'
        cached,manifest = {},{}
        for name in SOURCES:
            data = (HERE/name).read_bytes()
            committed = subprocess.check_output(['git','--no-pager','-c','pack.threads=1',
                'show',args.source_revision+':'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT,timeout=.5)
            if committed != data:
                raise ValueError('Frozen source mismatch: '+name)
            cached[name] = data
            manifest[name] = dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        write(out/'source_manifest.json',dict(revision=args.source_revision,sources=manifest,
              python=sys.version,platform=platform.platform(),dependencies='stdlib only',threads=1))
        modules = {}
        for name in ('reference','candidate'):
            namespace = {'__name__':name,'__file__':str(HERE/(name+'.py'))}
            exec(compile(cached[name+'.py'],namespace['__file__'],'exec'),namespace)
            modules[name] = namespace
        reference,analytic = modules['reference']['evaluate'],modules['candidate']['evaluate']
        vertices = modules['reference']['_vertices']
        proposed = json.loads(cached['cases.json'])['cases']
        admit_cases(proposed)
        specs = proposed
        for spec in specs:
            row = dict(spec=spec,status='ATTEMPTED',baseline=None,candidate=None)
            rows.append(row)
            kwargs = arguments(spec)
            before = time.monotonic()
            row['baseline'] = reference(**kwargs)
            row['baseline_elapsed_s'] = time.monotonic()-before
            before = time.monotonic()
            row['candidate'] = analytic(**kwargs)
            row['candidate_elapsed_s'] = time.monotonic()-before
            try:
                compare(row['baseline'],row['candidate'],len(kwargs['A']),vertices)
                row['status'] = 'PASS'
            except AssertionError as exc:
                row.update(status='FAIL',reason=str(exc))
                failures.append(spec['id']+': '+str(exc))
        first = rows[0]
        base = first['baseline']
        assert (base['D'],base['CH'],base['D']-base['CH']) == (F(2681,20),F(434201,3240),F(121,3240))
        assert {o['regret'] for o in base['physical_optima']} == {F(11,10)}
        controls.append(dict(id='hand-derived-smoke',pass_check=True))
        changed = copy.deepcopy(first['candidate'])
        changed['D'] += 1
        rejected('corrupt-objective',lambda:compare(base,changed,2,vertices),controls)
        changed = copy.deepcopy(first['candidate'])
        changed['matching_thresholds'][-1] += 1
        rejected('corrupt-DP-threshold',lambda:compare(base,changed,2,vertices),controls)
        tied = rows[4]
        changed = copy.deepcopy(tied['candidate'])
        assert len(changed['physical_optima']) >= 2, 'predeclared assignment tie absent'
        changed['physical_optima'].pop()
        rejected('erase-assignment-tie',lambda:compare(tied['baseline'],changed,2,vertices),controls)
        flat = rows[7]
        changed = copy.deepcopy(flat['candidate'])
        altered = False
        for opt in changed['physical_optima']:
            for response in opt['response_sets']:
                lo,hi = response['early_interval']
                if lo < hi:
                    response['early_interval'] = (lo,lo)
                    altered = True
        assert altered, 'predeclared flat response absent'
        rejected('collapse-flat-response',lambda:compare(flat['baseline'],changed,3,vertices),controls)
        changed = copy.deepcopy(first['candidate'])
        box = changed['physical_optima'][0]['allocation_set']
        lower = list(box['lower'])
        lower[0] += 1
        box['lower'] = tuple(lower)
        rejected('corrupt-allocation-continuum',lambda:compare(base,changed,2,vertices),controls)
        replay = modules['reference']['replay']
        opt = base['physical_optima'][0]
        for kind in ('missing-terminal-charge','wrong-service','excessive-power'):
            witness = copy.deepcopy(opt['witness'])
            if kind == 'missing-terminal-charge':
                witness['charges'].pop()
            elif kind == 'wrong-service':
                item = list(witness['services'][0])
                item[0] = 99
                witness['services'][0] = tuple(item)
            else:
                item = list(witness['charges'][0])
                item[-1] += 1
                witness['charges'][0] = tuple(item)
            rejected(kind,lambda w=witness:replay((5,15),(14,15),opt['pairs'],opt['early'],w),controls)
        invalid = [dict(A=(0,),B=(15,),fee=7),dict(A=(20,),B=(20,),fee=7),
                   dict(A=(5,),B=(5,6),fee=7),dict(A=(5,),B=(5,),fee=0),
                   dict(A=(5,)*4,B=(5,)*4,fee=7)]
        for name,fn in (('reference',reference),('candidate',analytic)):
            for index,kwargs in enumerate(invalid):
                rejected(name+'-domain-'+str(index),lambda f=fn,k=kwargs:f(**k),controls)
        failures.extend(c['id'] for c in controls if c.get('rejected') is False)
    except BaseException as exc:
        reason = type(exc).__name__+': '+str(exc)
        failures.append(reason)
        for row in rows:
            if row['status'] == 'ATTEMPTED':
                row.update(status='FAIL',reason=reason)
    attempted = {row['spec']['id'] for row in rows}
    for spec in specs:
        if spec['id'] not in attempted:
            rows.append(dict(spec=spec,status='UNATTEMPTED',reason='earlier fatal failure'))
    report = dict(status='PASS' if len(rows) == 8 and not failures else 'FAIL',
        assigned=8,attempted=len(attempted),unattempted=8-len(attempted),
        passed=sum(r['status'] == 'PASS' for r in rows),failures=failures,controls=controls,rows=rows,
        scope='Eight fixed exact-model implementation cases; not population, novelty or ML evidence')
    write(out/'results.json',report)
    table = ['# Exact heterogeneous support comparison','','|Case|D|CH|Gap|Optimal assignments|Regrets|Status|',
             '|---|---:|---:|---:|---:|---|---|']
    for row in rows:
        baseline = row.get('baseline')
        values = [str(baseline['D']),str(baseline['CH']),str(baseline['D']-baseline['CH']),
                  str(len(baseline['physical_optima'])),str(sorted({str(o['regret']) for o in baseline['physical_optima']}))] if baseline else ['—']*5
        table.append('|'+ '|'.join([row['spec']['id']]+values+[row['status']])+'|')
    with (out/'TABLE.md').open('x') as stream:
        stream.write('\n'.join(table)+'\n')
    own,children = resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    self_cpu,child_cpu = own.ru_utime+own.ru_stime,children.ru_utime+children.ru_stime
    elapsed = time.monotonic()-started
    rss = own.ru_maxrss*(1 if sys.platform == 'darwin' else 1024)
    accepted = self_cpu+child_cpu < 45 and elapsed < 60 and rss <= 512*1024**2
    write(out/'worker_receipt.json',dict(status=report['status'],self_cpu_s=self_cpu,
        waited_children_cpu_s=child_cpu,inclusive_cpu_observed_s=self_cpu+child_cpu,
        elapsed_s=elapsed,peak_rss_bytes=rss,resource_pass=accepted,
        self_cpu_limit_s=40,inclusive_cpu_allowance_s=45,wall_allowance_s=60,
        note='Prepublication observation; external owner meter is authoritative'))
    return 0 if report['status'] == 'PASS' and accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
