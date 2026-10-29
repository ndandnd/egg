"""One frozen fourteen-state shared-connector qualification; stdlib only."""
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCES=('reference.py','candidate.py','verify.py','run.py','cases.json','PROTOCOL.md')
IDS=('shared-gap','terminal-clipped-L','infeasible-pairing-count','infeasible-total-capacity',
     'zero-early-power','zero-terminal-power','zero-fee','three-per-batch-clipped-gap',
     'three-per-batch-clipped-boundary','three-per-batch-count-truncation','single-load','flat-response-ties',
     'collinear-physical-threshold','clipped-first-edge-lower-boundary')
LITERALS=(((5,15),(14,15),15,49,'7'),((5,15),(14,15),15,40,'7'),
          ((5,15),(14,15),8,49,'7'),((5,15),(14,15),8,40,'7'),
          ((5,15),(14,15),0,49,'7'),((5,15),(14,15),15,0,'7'),
          ((5,15),(14,15),15,49,'0'),((3,11,17),(8,12,13),10,59,'2'),
          ((3,11,17),(8,12,13),10,59,'12/5'),((3,11,17),(8,12,13),7,59,'2'),
          ((15,),(15,),10,20,'7'),((8,9,10),(10,11,12),20,60,'7'),
          ((15,15,15),(15,15,15),30,90,'20/3'),((3,11,17),(8,12,13),10,59,'6/5'))


def encode(v):
    if isinstance(v,F):return str(v)
    raise TypeError(type(v).__name__)


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,default=encode,allow_nan=False)
        stream.write('\n')


def kwargs(spec):
    return dict(A=tuple(map(F,spec['A'])),B=tuple(map(F,spec['B'])),
                **{k:F(spec[k]) for k in ('capacity','K','H','fee')})


def admit(specs):
    assert len(specs)==14 and tuple(s['id'] for s in specs)==IDS
    for s,(A,B,K,H,fee) in zip(specs,LITERALS):
        assert kwargs(s)==dict(A=tuple(map(F,A)),B=tuple(map(F,B)),capacity=F(20),K=F(K),H=F(H),fee=F(fee)), 'literal state changed'


def label(value):return tuple(sorted(tuple(p) for p in value))


def allocation_rows(value,n):
    if 'inequalities' in value:
        rows=list(value['inequalities'])
    else:
        assert len(value['lower'])==len(value['upper'])==n
        rows=[]
        for i,(lo,hi) in enumerate(zip(value['lower'],value['upper'])):
            assert lo<=hi
            unit=tuple(F(i==j) for j in range(n))
            rows += [dict(row=unit,rhs=hi),dict(row=tuple(-x for x in unit),rhs=-lo)]
    if 'sum_equality' in value:
        coefficients,E=value['sum_equality']
        assert tuple(coefficients)==(F(1),)*n
        lo=hi=E
    else:lo,hi=value['sum_interval']
    return rows+[dict(row=(F(1),)*n,rhs=hi),dict(row=(F(-1),)*n,rhs=-lo)]


def response_summary(opt):
    return tuple(sorted((label(r['pairs']),tuple(r['early_interval']),r['ops'],r['price_cost']) for r in opt['response_sets']))


def compare(raw,analytic,n,vertices):
    assert raw['status']==analytic['status'], 'feasibility classification mismatch'
    assert (raw['D'],raw['CH'],raw['gap'])==(analytic['D'],analytic['CH'],analytic['gap']), 'objective/gap mismatch'
    descriptor=raw['provenance']
    S=sum(descriptor['A'])+sum(descriptor['B'])
    expected_L=max(F(0),S-descriptor['H'])
    expected_U=min(sum(descriptor['A']),descriptor['K'])
    assert (analytic['L'],analytic['U'])==(expected_L,expected_U), 'resource clipping endpoints mismatch'
    reference={label(a['pairs']):a for a in raw['assignments']}
    candidate={label(a['pairs']):a for a in analytic['assignments']}
    assert len(reference)==raw['rawcount']==len(candidate)==analytic['rawcount'] and set(reference)==set(candidate), 'assignment labels/count mismatch'
    # Derive unclipped matching minima from raw SOC polytopes after removing
    # only the two identified aggregate charger rows. No threshold formula.
    minima={m:[] for m in range(n+1)}
    for key,r in reference.items():
        c=candidate[key]
        assert r['interval']==c['interval'] and r['ops']==c['ops'], 'physical interval/cardinality mismatch'
        assert tuple(r['vertices'])==tuple(vertices(n,allocation_rows(c,n))), 'full allocation polytope mismatch'
        unclipped=[row for row in r['constraints'] if row['description'] not in
                   ('one shared early connector energy','one shared terminal connector energy')]
        assert len(r['constraints'])-len(unclipped)==2
        points=vertices(n,unclipped)
        assert points
        minima[len(key)].append(min(map(sum,points)))
    thresholds=[min(minima[m]) for m in range(n+1)]
    assert thresholds==analytic['matching_thresholds'], 'sorted matching threshold mismatch'
    r_opts={label(o['pairs']):o for o in raw['physical_optima']}
    c_opts={label(o['pairs']):o for o in analytic['physical_optima']}
    assert len(r_opts)==len(raw['physical_optima']) and len(c_opts)==len(analytic['physical_optima'])
    assert set(r_opts)==set(c_opts), 'optimal assignment tie mismatch'
    hull=lambda result:sorted((h['early'],h['late'],h['ops'],h['value']) for h in result['hull_optima'])
    assert hull(raw)==hull(analytic), 'hull minimizer mismatch'
    if raw['status']=='INFEASIBLE':
        assert expected_L>expected_U and not analytic['positive_gap'] and not r_opts
        return
    assert analytic['mmax']==max(m for m,r in enumerate(thresholds) if r<=expected_U)
    assert analytic['m0']==max(m for m,r in enumerate(thresholds) if r<=expected_L)
    assert raw['gap']>=0 and (raw['gap']>0)==analytic['positive_gap'], 'strict support criterion mismatch'
    for key,r in r_opts.items():
        c=c_opts[key]
        for name in ('early','late','ops','value','regret'):
            assert r[name]==c[name], 'physical optimum value mismatch: '+name
        assert tuple(r['prices'])==tuple(c['prices']) and response_summary(r)==response_summary(c), 'price/response mismatch'
        assert r['regret']>=raw['gap'] and (raw['gap']!=0 or r['regret']==0)
        assert vertices(n,allocation_rows(r['allocation_set'],n))==vertices(n,allocation_rows(c['allocation_set'],n)), 'optimal allocation continuum mismatch'
        r_response={label(s['pairs']):s for s in r['response_sets']}
        c_response={label(s['pairs']):s for s in c['response_sets']}
        for response_key,s in r_response.items():
            assert vertices(n,allocation_rows(s['allocation_set'],n))==vertices(n,allocation_rows(c_response[response_key]['allocation_set'],n)), 'response allocation continuum mismatch'


def rejected(name,action,controls):
    try:action()
    except (ValueError,AssertionError):controls.append(dict(id=name,rejected=True))
    else:controls.append(dict(id=name,rejected=False))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    out=Path(args.out).resolve()
    started=time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    rows,controls,failures=[],[],[]
    specs=[dict(id=n) for n in IDS]
    try:
        assert not sys.flags.optimize
        cache,manifest={},{}
        for name in SOURCES:
            data=(HERE/name).read_bytes()
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',
                args.source_revision+':'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT,timeout=.5)
            if data!=committed:raise ValueError('Frozen byte mismatch: '+name)
            cache[name]=data
            manifest[name]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        write(out/'source_manifest.json',dict(revision=args.source_revision,sources=manifest,python=sys.version,platform=platform.platform()))
        modules={}
        for name in ('reference','candidate'):
            namespace={'__name__':name,'__file__':str(HERE/(name+'.py'))}
            exec(compile(cache[name+'.py'],namespace['__file__'],'exec'),namespace)
            modules[name]=namespace
        reference,analytic=modules['reference']['evaluate'],modules['candidate']['evaluate']
        vertices=modules['reference']['_vertices']
        proposed=json.loads(cache['cases.json'])['cases'];admit(proposed);specs=proposed
        for spec in specs:
            row=dict(spec=spec,status='ATTEMPTED',baseline=None,candidate=None);rows.append(row)
            inputs=kwargs(spec)
            before=time.monotonic();row['baseline']=reference(**inputs);row['baseline_elapsed_s']=time.monotonic()-before
            before=time.monotonic();row['candidate']=analytic(**inputs);row['candidate_elapsed_s']=time.monotonic()-before
            try:compare(row['baseline'],row['candidate'],len(inputs['A']),vertices);row['status']='PASS'
            except AssertionError as exc:row.update(status='FAIL',reason=str(exc));failures.append(spec['id']+': '+str(exc))
        first=rows[0]
        assert (first['baseline']['D'],first['baseline']['CH'],first['baseline']['gap'])==(F(2681,20),F(434201,3240),F(121,3240))
        controls.append(dict(id='analytical-shared-smoke',pass_check=True))
        def corruption(index,name,mutate):
            changed=copy.deepcopy(rows[index]['candidate']);mutate(changed)
            rejected(name,lambda:compare(rows[index]['baseline'],changed,len(kwargs(specs[index])['A']),vertices),controls)
        corruption(0,'corrupt-objective',lambda c:c.update(D=c['D']+1))
        corruption(0,'corrupt-sorted-threshold',lambda c:c['matching_thresholds'].__setitem__(-1,c['matching_thresholds'][-1]+1))
        def relabel(c):
            o=c['physical_optima'][0];o['pairs']=tuple((1-i,j) for i,j in o['pairs'])
        corruption(0,'reordered-service-label-association',relabel)
        wrong=analytic(A=(5,15),B=(14,15),capacity=20,K=15,H=49,fee=7)
        rejected('omitted-terminal-L',lambda:compare(rows[1]['baseline'],wrong,2,vertices),controls)
        def fake(c):
            next(a for a in c['assignments'] if len(a['pairs'])==2)['interval']=(c['U'],c['U'])
        corruption(2,'fake-clipped-infeasible-cardinality',fake)
        corruption(6,'fee-zero-positive-gap',lambda c:c.update(positive_gap=True))
        corruption(4,'zero-power-positive-interval',lambda c:c['assignments'][0].update(interval=(F(0),F(1))))
        corruption(3,'infeasible-as-feasible',lambda c:c.update(status='FEASIBLE'))
        def erase(c):
            assert len(c['physical_optima'])>1;c['physical_optima'].pop()
        corruption(6,'erase-zero-fee-assignment-tie',erase)
        def collapse(c):
            count=0
            for o in c['physical_optima']:
                for r in o['response_sets']:
                    lo,hi=r['early_interval']
                    if lo<hi:r['early_interval']=(lo,lo);count+=1
            assert count
        corruption(11,'collapse-flat-response',collapse)
        def change_allocation(c):
            box=c['physical_optima'][0]['allocation_set'];lo=list(box['lower']);lo[0]+=1;box['lower']=tuple(lo)
        corruption(0,'changed-optimal-allocation-continuum',change_allocation)
        replay=modules['reference']['replay'];opt=first['baseline']['physical_optima'][0]
        common=dict(A=(5,15),B=(14,15),capacity=20,pairs=opt['pairs'],E=opt['early'],witness=opt['witness'])
        rejected('early-shared-power-corruption',lambda:replay(K=14,H=49,**common),controls)
        rejected('terminal-shared-power-corruption',lambda:replay(K=15,H=48,**common),controls)
        witness=copy.deepcopy(opt['witness']);witness['charges'].pop()
        rejected('missing-terminal-charge',lambda:replay((5,15),(14,15),20,15,49,opt['pairs'],opt['early'],witness),controls)
        invalid=[dict(A=(5,),B=(5,),K=-1),dict(A=(5,),B=(5,),H=-1),dict(A=(5,),B=(5,),fee=-1),
                 dict(A=(21,),B=(5,)),dict(A=(5,)*4,B=(5,)*4)]
        for name,fn in (('reference',reference),('candidate',analytic)):
            for i,k in enumerate(invalid):rejected(name+'-domain-'+str(i),lambda f=fn,v=k:f(**v),controls)
        failures += [c['id'] for c in controls if c.get('rejected') is False]
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);failures.append(reason)
        for row in rows:
            if row['status']=='ATTEMPTED':row.update(status='FAIL',reason=reason)
    attempted={r['spec']['id'] for r in rows}
    for spec in specs:
        if spec['id'] not in attempted:rows.append(dict(spec=spec,status='UNATTEMPTED',reason='earlier fatal'))
    report=dict(status='PASS' if len(rows)==14 and not failures else 'FAIL',assigned=14,attempted=len(attempted),
        unattempted=14-len(attempted),passed=sum(r['status']=='PASS' for r in rows),failures=failures,controls=controls,rows=rows,
        scope='Exact fixed shared-connector implementation qualification, not empirical cohort evidence')
    write(out/'results.json',report)
    table=['# Exact fixed shared-connector comparison','','|Case|Feasibility|D|CH|Gap|Status|','|---|---|---:|---:|---:|---|']
    for row in rows:
        b=row.get('baseline');values=[b['status'],str(b['D']),str(b['CH']),str(b['gap'])] if b else ['—']*4
        table.append('|'+ '|'.join([row['spec']['id']]+values+[row['status']])+'|')
    with (out/'TABLE.md').open('x') as stream:stream.write('\n'.join(table)+'\n')
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
    elapsed=time.monotonic()-started;rss=own.ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    accepted=cpu<45 and elapsed<60 and rss<=512*1024**2
    write(out/'worker_receipt.json',dict(status=report['status'],inclusive_cpu_observed_s=cpu,elapsed_s=elapsed,
          peak_rss_bytes=rss,resource_pass=accepted,self_cpu_limit_s=40,inclusive_allowance_s=45,wall_allowance_s=60))
    return 0 if report['status']=='PASS' and accepted else 1


if __name__=='__main__':raise SystemExit(main())
