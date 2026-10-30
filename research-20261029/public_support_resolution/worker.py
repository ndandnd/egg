"""One source-pinned public diagnostic; all publication is inside this worker."""
import argparse
import copy
from dataclasses import asdict
from fractions import Fraction
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_support_resolution/'
SOURCES=[REL+n for n in ('worker.py','run.py','native_probe.py','independent_verify.py','PROTOCOL.md')]+[
    'src/egglab/__init__.py','src/egglab/native_recharge.py','src/egglab/native_pathflow.py']
INPUTS={
 'data/public/sistig_26088190_v1/hildenbrand_native_cases.json':'af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6',
 'result/sistig_exact_witness/20260927-depot15-attempt1/depot15_exact_candidate.json':'fafb2e2721a283b0ef43b94357c497710ad113c79f85427a8aabc4211b8aa325'}
ASSIGNED=('Q0','OA','MIQP','ROOT_QP','PRICE_LP','PRICE_MIP')

def write(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False,default=lambda x:str(x) if isinstance(x,Fraction) else (_ for _ in ()).throw(TypeError(type(x).__name__)))
        f.write('\n')

def usage():
    a,b=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=a.ru_utime+a.ru_stime+b.ru_utime+b.ru_stime,
       peak_rss_bytes=max(a.ru_maxrss,b.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))

def load_module(name,relative,cache,package=False):
    m=types.ModuleType(name)
    m.__file__=str(ROOT/relative)
    if package: m.__path__=[]
    m.__package__=name if package else name.rpartition('.')[0]
    sys.modules[name]=m
    exec(compile(cache[relative],m.__file__,'exec'),m.__dict__)
    return m

def public_case(nr,v):
    return nr.NativeCase(name=v['case_name'],trips=tuple(nr.Trip(**t['native']) for t in v['trips']),
      movements=tuple(nr.Movement(id=m['id'],kind=m['kind'],before=m['before'],after=m['after'],
          legs=tuple(nr.Leg(**l) for l in m['legs']),depot_split=m['depot_split']) for m in v['movement_modes']),
      resources=(nr.Resource(**v['resource_policy']),),market_edges_min=tuple(v['market_edges_min']),
      depot=v['selected_depot_native_place'],max_vehicles=int(v['vehicle_cap']),
      battery_kwh=v['charging_model']['usable_battery_kwh'],reserve_kwh=v['charging_model']['reserve_kwh'],
      terminal_open_min=0,recharge_deadline_min=1800,vehicle_cost=v['cost_policy']['vehicle_cost'],
      deadhead_cost_per_min=v['cost_policy']['deadhead_cost_per_min'],efficiency=v['charging_model']['efficiency'],
      graph_scope='declared-movement-modes-only')

def dispose(built):
    built['model'].dispose()
    built['source']['model'].clear()
    built.clear()
    gc.collect()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    out=Path(args.out)
    started=time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(1700,1700))
    rows,failures,cache,manifest=[],[],{},{}
    active=None
    def event(e):
        with (out/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(worker_elapsed_s=time.monotonic()-started,**e),allow_nan=False)+'\n')
    def funding(seconds):
        u=usage()
        if u['cpu_s']+seconds+120>=1700 or time.monotonic()-started+seconds+180>=2200:
            raise RuntimeError('Insufficient full next-stage funding plus closure reserve')
        if u['peak_rss_bytes']>5*1024**3: raise RuntimeError('Observed RSS ceiling exceeded')
    def stage(name,seconds,action):
        nonlocal active
        funding(seconds)
        active=dict(id=name,status='ATTEMPTED')
        rows.append(active)
        anchor=time.monotonic()
        event(dict(event='stage_begin',id=name,seconds=seconds))
        result=action()
        elapsed=time.monotonic()-anchor
        active.update(status='DELIVERED' if elapsed<=seconds+30 else 'LATE',
          stage_elapsed_s=elapsed,stage_clock_scope='prepublication; complete duration in master results',
          native_allowance_s=seconds,result=result,resources=usage())
        write(out/(name+'.json'),active)
        elapsed=time.monotonic()-anchor
        active.update(stage_elapsed_s=elapsed,stage_clock_scope='through complete stage packet serialization',
                      status='DELIVERED' if elapsed<=seconds+30 else 'LATE')
        event(dict(event='stage_end',id=name,status=active['status'],elapsed_s=elapsed))
        active=None
        return result
    try:
        for relative in SOURCES:
            raw=(ROOT/relative).read_bytes()
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',
                args.source_revision+':'+relative],cwd=ROOT,timeout=2)
            if raw!=committed: raise ValueError('Frozen source mismatch: '+relative)
            cache[relative]=raw
            manifest[relative]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        packages={n:importlib.metadata.version(n) for n in ('mip','gurobipy')}
        if packages!={'mip':'1.17.6','gurobipy':'12.0.1'}: raise ValueError('Unexpected solver package version')
        buffers={}
        for relative,pin in INPUTS.items():
            raw=(ROOT/relative).read_bytes()
            digest=hashlib.sha256(raw).hexdigest()
            if digest!=pin: raise ValueError('Input byte-pin mismatch: '+relative)
            buffers[relative]=json.loads(raw)
            manifest[relative]=dict(bytes=len(raw),sha256=digest)
        write(out/'source_admission.json',dict(revision=args.source_revision,files=manifest,packages=packages,python=sys.version))
        pkg=load_module('egglab','src/egglab/__init__.py',cache,True)
        nr=load_module('egglab.native_recharge','src/egglab/native_recharge.py',cache)
        pkg.native_recharge=nr
        pf=load_module('egglab.native_pathflow','src/egglab/native_pathflow.py',cache)
        pkg.native_pathflow=pf
        probe=load_module('native_probe',REL+'native_probe.py',cache)
        verifier=load_module('independent_verify',REL+'independent_verify.py',cache)
        def qualification():
            q=nr.NativeCase(name='literal-forced-refill',trips=(nr.Trip('s',30,60,'D','D',10),),
                movements=(nr.Movement('out','pullout',None,'s',(nr.Leg('D','D',30,30,0),)),
                           nr.Movement('in','pullin','s',None,(nr.Leg('D','D',60,60,0),))),
                resources=(nr.Resource(0,120,10,10,1),),market_edges_min=(0,60,120),depot='D',
                max_vehicles=1,battery_kwh=20,reserve_kwh=0,terminal_open_min=0,
                recharge_deadline_min=120,vehicle_cost=7)
            checked=[]
            for method in ('oa','miqp','root','linear'):
                built=probe.build(q,continuous=method=='root')
                if method=='linear': r=probe.solve_pricing(built,[.2,.3],seconds=10,record=event)
                else: r=probe.solve(built,method='oa' if method=='oa' else 'miqp',seconds=10,record=event)
                c=r.get('best_candidate') if method=='oa' else r.get('candidate')
                if not c or r['raw_status']!=2: raise ValueError('Q0 native did not deliver OPTIMAL '+method)
                if max(abs(x-y) for x,y in zip(c['load'],[0,10]))>1e-6 or abs(c['ops']-7)>1e-6:
                    raise ValueError('Q0 forced solution mismatch '+method)
                expected=10 if method=='linear' else 7+.2*10+(1/900)*100/2
                actual=r.get('best_evaluated_upper') if method=='oa' else r['raw_objective']
                if actual is None or abs(actual-expected)>1e-6: raise ValueError('Q0 objective mismatch '+method)
                audit=verifier.verify(asdict(q),c)
                if not audit['physical_strict_pass']: raise ValueError('Q0 exact replay failed '+method)
                checked.append(dict(method=method,native=r,replay=audit))
                dispose(built)
            base=checked[1]['native']['candidate']
            negatives=[]
            for kind in ('missing-energy','extra-energy','missing-movement','duplicate-allocation'):
                bad=copy.deepcopy(base)
                if kind=='missing-energy': bad['charge_by_interval']=[]
                elif kind=='extra-energy': bad['charge_by_interval'][0]['energy']+=1
                elif kind=='missing-movement': bad['selected_movement_ids'].pop()
                else: bad['charge_by_interval'].append(copy.deepcopy(bad['charge_by_interval'][0]))
                a=verifier.verify(asdict(q),bad)
                if a['physical_strict_pass']: raise ValueError('Q0 corruption accepted '+kind)
                negatives.append(dict(kind=kind,rejected=True))
            return dict(status='PASS',checked=checked,negative_controls=negatives)
        stage('Q0',45,qualification)
        document=buffers[next(iter(INPUTS))]
        variants=[v for v in document['native_cases'] if v['selected_depot_id']==15]
        if len(variants)!=1: raise ValueError('Unique depot15 missing')
        case=public_case(nr,variants[0])
        if case.identity()!='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7':
            raise ValueError('Case identity mismatch')
        case_data=asdict(case)
        write(out/'case_descriptor.json',case_data)
        old=buffers[list(INPUTS)[1]]
        start={'selected_movement_ids':[mid for r in old['routes'] for mid in r['movements']]}
        write(out/'common_start.json',dict(start=start,source=list(INPUTS)[1],historically_admitted=True,new_replay=False))
        candidates=[]
        def physical(method):
            built=probe.build(case)
            r=probe.solve(built,method=method,seconds=300,record=event,start=start)
            c=r.get('best_candidate') if method=='oa' else r.get('candidate')
            if c:
                r['independent_replay']=verifier.verify(case_data,c)
                value=c['ops']+sum(.2*x+(1/900)*x*x/2 for x in c['load'])
                candidates.append(dict(method=method,candidate=c,evaluated_cost=value))
            dispose(built)
            return r
        stage('OA',300,lambda:physical('oa'))
        stage('MIQP',300,lambda:physical('miqp'))
        def root():
            built=probe.build(case,continuous=True)
            r=probe.solve(built,method='miqp',seconds=90,record=event)
            dispose(built)
            return r
        stage('ROOT_QP',90,root)
        if candidates:
            chosen=min(candidates,key=lambda c:c['evaluated_cost'])
            prices=[.2+(1/900)*x for x in chosen['candidate']['load']]
            write(out/'price_selection.json',dict(policy='lowest evaluated candidate cost; OA first on ties',
               chosen_method=chosen['method'],evaluated_cost=chosen['evaluated_cost'],prices=prices,
               physical_qualification='see independent replay; unqualified point is diagnostic only'))
            def price(continuous,seconds):
                built=probe.build(case,continuous=continuous)
                r=probe.solve_pricing(built,prices,seconds=seconds,record=event,
                    start=None if continuous else {'selected_movement_ids':chosen['candidate']['selected_movement_ids']})
                if not continuous and 'candidate' in r:
                    r['independent_replay']=verifier.verify(case_data,r['candidate'])
                dispose(built)
                return r
            stage('PRICE_LP',60,lambda:price(True,60))
            stage('PRICE_MIP',240,lambda:price(False,240))
    except BaseException as exc:
        failure=type(exc).__name__+': '+str(exc)
        failures.append(failure)
        if active is not None: active.update(status='FAILED',failure=failure,resources=usage())
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows): rows.append(dict(id=name,status='UNATTEMPTED',reason='prior fatal failure or missing price candidate'))
    u=usage()
    summary=[]
    for r in rows:
        s={k:v for k,v in r.items() if k!='result'}
        native=r.get('result',{})
        for k in ('raw_status','solution_count','raw_objective','raw_bound','best_evaluated_upper','best_native_lower','inclusive_elapsed_s'):
            if k in native: s[k]=native[k]
        if 'independent_replay' in native:
            s['physical_strict_pass']=native['independent_replay']['physical_strict_pass']
            s['violation_count']=len(native['independent_replay']['violations'])
        summary.append(s)
    report=dict(status='CLOSED' if not failures else 'CLOSED_FAILED',assigned=6,rows=summary,failures=failures,
        elapsed_s=time.monotonic()-started,resources=u,exact_public_support='UNRESOLVED; diagnostic only',
        resource_pass=u['cpu_s']<1740 and u['peak_rss_bytes']<=5*1024**3 and time.monotonic()-started<2200)
    write(out/'results.json',report)
    write(out/'worker_receipt.json',dict(**u,elapsed_s=time.monotonic()-started,source_revision=args.source_revision,
        accounting='self plus waited children, included in outer owner; prepublication snapshot'))
    print(json.dumps(report,allow_nan=False))
    return 0 if not failures and report['resource_pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
