"""One frozen fixed-topology QP/recovery and conditional own-price diagnostic."""
import argparse
from dataclasses import asdict
from fractions import Fraction as Q
import gc
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_fixed_topology/'
MODEL='research-20261029/public_support_resolution/'
SOURCES=[REL+n for n in ('worker.py','run.py','PROTOCOL.md')]+[MODEL+n for n in
    ('exact_fixed_topology.py','energy_flow.py','exact_dual.py','independent_verify.py')]+[
    'src/egglab/__init__.py','src/egglab/native_recharge.py']
INPUTS=dict(case=('253c1e29295e766b3889fc8f5c28d9808e00b3d6',
    'research-20261029/public_support_resolution/attempt01/case_descriptor.json'),
    topology=('f8a043132863db5ce631d5691d35b5d788bdf256',
    'research-20261029/public_energy_flow/attempt01/MIQP.json.gz'))
ASSIGNED=('Q0','FIXED_QP_RECOVERY','OWN_PRICE_LP','OWN_PRICE_MIP')
RECOVERY_LIMITS=dict(dimension=250,operations=2000000,fraction_bits=16384,seconds=30)


def encode(value):
    if isinstance(value,Q): return str(value)
    raise TypeError(type(value).__name__)


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,default=encode,allow_nan=False)
        stream.write('\n')


def compressed(path,value):
    with gzip.open(path,'xt',encoding='utf-8',compresslevel=6) as stream:
        json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'))
        stream.write('\n')


def usage():
    own,child=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime,
                peak_rss_bytes=max(own.ru_maxrss,child.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))


def load_module(name,relative,cache,package=False):
    module=types.ModuleType(name)
    module.__file__=str(ROOT/relative)
    module.__package__=name if package else name.rpartition('.')[0]
    if package: module.__path__=[]
    sys.modules[name]=module
    exec(compile(cache[relative],module.__file__,'exec'),module.__dict__)
    return module


def case_from_dict(nr,data):
    values=dict(data)
    values['trips']=tuple(nr.Trip(**t) for t in data['trips'])
    values['movements']=tuple(nr.Movement(**dict(m,legs=tuple(nr.Leg(**l) for l in m['legs']))) for m in data['movements'])
    values['resources']=tuple(nr.Resource(**r) for r in data['resources'])
    values['market_edges_min']=tuple(data['market_edges_min'])
    return nr.NativeCase(**values)


def fixed_native(problem,seconds,event):
    """One cold charge-only continuous QP; no method or face retry."""
    started=time.monotonic()
    import gurobipy as gp
    model=gp.Model('one-fixed-topology-charge-qp')
    try:
        model.Params.OutputFlag=0
        model.Params.Threads=1
        model.Params.Method=0
        model.Params.FeasibilityTol=1e-8
        model.Params.OptimalityTol=1e-8
        variables=[model.addVar(lb=float(v['lower']),ub=float(v['upper']),name=v['name']) for v in problem['variables']]
        model.update()
        constraints=[]
        for row in problem['rows']:
            lhs=gp.LinExpr([float(c) for c in row['coefficients'].values()],
                          [variables[i] for i in row['coefficients']])
            if row['sense']=='=': c=model.addConstr(lhs==float(row['rhs']),name=row['name'])
            elif row['sense']=='<=': c=model.addConstr(lhs<=float(row['rhs']),name=row['name'])
            elif row['sense']=='>=': c=model.addConstr(lhs>=float(row['rhs']),name=row['name'])
            else: raise ValueError('Invalid fixed-QP row sense')
            constraints.append(c)
        loads=[gp.quicksum(variables[v['index']] for v in problem['variables'] if v['period']==t)
               for t in range(len(problem['a']))]
        model.setObjective(float(problem['ops'])+gp.quicksum(float(a)*load+float(b/2)*load*load
            for a,b,load in zip(problem['a'],problem['b'],loads)),gp.GRB.MINIMIZE)
        remaining=seconds-(time.monotonic()-started)
        if remaining<=0: raise RuntimeError('Fixed-QP model assembly exhausted complete native allowance')
        model.Params.TimeLimit=remaining
        event(dict(event='fixed_qp_begin',seconds=seconds,remaining_s=remaining,method=0,start='cold'))
        model.optimize()
        result=dict(raw_status=int(model.Status),solution_count=int(model.SolCount),method=0,
                    native_only=True,exact_certificate=False,start_policy='cold',proposal=None)
        if model.SolCount:
            result['raw_objective']=float(model.ObjVal)
            result['values']=[float(v.X) for v in variables]
            try:
                pi={row['name']:float(c.Pi) for row,c in zip(problem['rows'],constraints)}
                result['proposal']=dict(values=result['values'],dual_by_row=pi)
            except gp.GurobiError as exc:
                result['proposal_unavailable']=str(exc)
        result['inclusive_native_elapsed_s']=time.monotonic()-started
        return result
    finally:
        model.dispose()
        gc.collect()


def compact(packet):
    result={}
    native=packet.get('native',{})
    result.update(raw_status=native.get('raw_status'),solution_count=native.get('solution_count'),
                  raw_objective=native.get('raw_objective'),raw_bound=native.get('raw_bound'),
                  exact_global_optimum_claim=False)
    if 'recovery' in packet:
        r=packet['recovery']
        result['recovery']=dict(status=r['status'],stage=r.get('stage'),reason=r.get('reason'),
            objective_exact=r.get('objective_exact'),lower_exact=r.get('lower_exact'),
            exact_operations=r.get('exact_operations'),elapsed_s=r.get('elapsed_s'))
    if 'exact_certificate' in packet:
        r=packet['exact_certificate']
        result['exact_certificate']=dict(status=r['status'],lower_bound=r.get('lower_bound'),reason=r.get('reason'))
    if 'replay' in packet:
        r=packet['replay']
        result['replay']=dict(strict_pass=r['strict_pass'],physical_strict_pass=r['physical_strict_pass'],
            violations=len(r['violations']),classification=r['classification'])
    if 'known_exact_value' in packet: result['known_exact_value']=packet['known_exact_value']
    for key in ('exact_support_equality','certified_own_price_regret_upper'):
        if key in packet: result[key]=packet[key]
    if 'qualification_status' in packet:
        result['qualification_status']=packet['qualification_status']
        result['qualification_failure']=packet.get('qualification_failure')
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--source-revision',required=True)
    args=parser.parse_args()
    out=Path(args.out).resolve()
    started=time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(1100,1100))
    rows,failures,cache,manifest=[],[],{},{}
    active=None
    recovered=None
    def event(value):
        with (out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(worker_elapsed_s=time.monotonic()-started,**value),default=encode,allow_nan=False)+'\n')
    def stage(name,funding_seconds,action):
        nonlocal active
        u=usage()
        if u['cpu_s']+funding_seconds+120>=1100 or time.monotonic()-started+funding_seconds+180>=1600:
            raise RuntimeError('Insufficient complete stage funding and publication reserve')
        if u['peak_rss_bytes']>5*1024**3: raise RuntimeError('Observed RSS ceiling exceeded')
        active=dict(id=name,status='ATTEMPTED',complete_action_allowance_s=funding_seconds)
        rows.append(active)
        anchor=time.monotonic()
        event(dict(event='stage_begin',id=name))
        packet=action()
        compressed(out/(name+'.json.gz'),packet)
        elapsed=time.monotonic()-anchor
        active.update(status='DELIVERED' if elapsed<=funding_seconds+45 else 'LATE',
            packet=name+'.json.gz',summary=compact(packet),stage_elapsed_s=elapsed,
            stage_clock_scope='through complete gzip packet serialization',resources=usage())
        write(out/(name+'.status.json'),active)
        event(dict(event='stage_end',id=name,status=active['status'],elapsed_s=time.monotonic()-anchor))
        delivered=dict(active)
        active=None
        del packet
        gc.collect()
        return delivered
    try:
        launch_raw=(HERE/'LAUNCH.json').read_bytes()
        control=json.loads(launch_raw)
        if (control.get('status')!='FROZEN' or control.get('run_id')!='attempt01'
            or control.get('source_revision')!=args.source_revision): raise ValueError('No exact frozen launch authority')
        if tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))!=(1200,1800,1100,1600):
            raise ValueError('Resource control mismatch')
        manifest['LAUNCH.json']=dict(bytes=len(launch_raw),sha256=hashlib.sha256(launch_raw).hexdigest())
        for relative in SOURCES:
            raw=(ROOT/relative).read_bytes()
            frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',args.source_revision+':'+relative],cwd=ROOT,timeout=2)
            if raw!=frozen: raise ValueError('Frozen source mismatch: '+relative)
            cache[relative]=raw
            manifest[relative]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if importlib.metadata.version('gurobipy')!='12.0.1': raise ValueError('Unexpected backend version')
        specs=control.get('inputs',[])
        if len(specs)!=2 or {s.get('id') for s in specs}!=set(INPUTS): raise ValueError('Input identity mismatch')
        buffers={}
        for spec in specs:
            revision,path=INPUTS[spec['id']]
            if (spec.get('revision'),spec.get('path'))!=(revision,path): raise ValueError('Input revision/fixed-path mismatch')
            raw=(ROOT/path).read_bytes()
            frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=2)
            if raw!=frozen: raise ValueError('Pinned input mismatch: '+spec['id'])
            buffers[spec['id']]=raw
            manifest['input:'+spec['id']]=dict(spec,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        case_data=json.loads(buffers.pop('case'))
        original=json.loads(gzip.decompress(buffers.pop('topology')))
        if original.get('id')!='MIQP': raise ValueError('Wrong source topology packet')
        selected=list(original['native']['candidate']['selected_movement_ids'])
        del original
        gc.collect()
        write(out/'admission.json',dict(source_revision=args.source_revision,files=manifest,
            topology_use='selected movement IDs only; original charge values neither used nor replayed',
            gurobipy='12.0.1',python=sys.version))
        pkg=load_module('egglab','src/egglab/__init__.py',cache,True)
        nr=load_module('egglab.native_recharge','src/egglab/native_recharge.py',cache)
        pkg.native_recharge=nr
        helper=load_module('exact_fixed_topology',MODEL+'exact_fixed_topology.py',cache)
        exact=load_module('exact_dual',MODEL+'exact_dual.py',cache)
        verifier=load_module('independent_verify',MODEL+'independent_verify.py',cache)
        flow=load_module('energy_flow',MODEL+'energy_flow.py',cache)
        case=case_from_dict(nr,case_data)
        if case.identity()!='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7':
            raise ValueError('Original public case identity mismatch')
        def fixed_action(data,selection,seconds,literal=False):
            nonlocal recovered
            problem=helper.build_problem(data,selection,exact._reconstruct)
            native=fixed_native(problem,seconds,event)
            if native.get('proposal') is None:
                recovery=dict(status='RECOVERY_UNAVAILABLE',stage='NATIVE_PROPOSAL',reason='No continuous primal/dual proposal')
            else:
                recovery=helper.recover(problem,native['proposal'],verifier.verify,limits=RECOVERY_LIMITS)
            packet=dict(native=native,recovery=recovery,problem=problem)
            if literal:
                known=Q(7)+10*Q(float(.2))+25*Q(float(1/900))
                qualification_failure=None
                if native['raw_status']!=2 or recovery['status']!='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM':
                    qualification_failure='Literal native/recovery qualification failed'
                elif Q(recovery['objective_exact'])!=known or Q(recovery['lower_exact'])!=known:
                    qualification_failure='Literal exact fixed-topology optimum mismatch'
                packet.update(known_exact_value=known,qualification_status='FAIL' if qualification_failure else 'PASS',
                    qualification_failure=qualification_failure,
                    negative_controls='No invented proposal-corruption rejection; independent helper review required')
            elif recovery['status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM':
                recovered=recovery
            return packet
        literal=dict(name='fixed-topology-literal',depot='D',max_vehicles=1,battery_kwh=20,reserve_kwh=0,
            terminal_open_min=0,recharge_deadline_min=120,vehicle_cost=7,deadhead_cost_per_min=0,efficiency=1,
            graph_scope='declared-movement-modes-only',market_edges_min=[0,60,120],
            resources=[dict(start_min=0,end_min=120,per_bus_kw=20,grid_kw=20,connectors=1)],
            trips=[dict(id='T',start_min=0,end_min=30,start_place='D',end_place='D',energy_kwh=10)],
            movements=[dict(id='out',kind='pullout',before=None,after='T',depot_split=None,
                legs=[dict(origin='D',destination='D',depart_min=0,arrive_min=0,energy_kwh=0)]),
                dict(id='in',kind='pullin',before='T',after=None,depot_split=None,
                legs=[dict(origin='D',destination='D',depart_min=30,arrive_min=30,energy_kwh=0)])])
        q0=stage('Q0',50,lambda:fixed_action(literal,['out','in'],20,True))
        if q0['summary']['qualification_status']!='PASS':
            raise ValueError('Q0 qualification failed; complete native/recovery packet preserved')
        stage('FIXED_QP_RECOVERY',90,lambda:fixed_action(case_data,selected,60))
        if recovered is None:
            for name in ('OWN_PRICE_LP','OWN_PRICE_MIP'):
                rows.append(dict(id=name,status='UNATTEMPTED',reason='Exact fixed-topology recovery did not certify a new physical candidate'))
        else:
            prices=[Q(float(.2))+Q(float(1/900))*Q(x) for x in recovered['loads_exact']]
            if list(map(Q,recovered['own_prices']))!=prices: raise ValueError('Recovered gradient mismatch')
            candidate=recovered['candidate']
            private=Q(recovered['replay']['ops_exact'])+sum((p*Q(x) for p,x in zip(prices,recovered['loads_exact'])),Q(0))
            write(out/'new_fixed_price.json',dict(prices=prices,private_score=private,
                certified_physical_upper=recovered['objective_exact'],source='new exact fixed-topology recovery',
                unchanged_across_price_methods=True,global_optimum_claim=False))
            def own_price(continuous,seconds):
                built=flow.build(case,continuous=continuous)
                try:
                    native=flow.solve(built,method='linear',seconds=seconds,prices=prices,
                        startmovementids=None if continuous else candidate['selected_movement_ids'],record=event)
                finally:
                    built['model'].dispose()
                    built.clear()
                    gc.collect()
                if list(map(Q,native.get('prices',[])))!=prices: raise ValueError('Exported own-price vector mismatch')
                packet=dict(native=native)
                if continuous:
                    certificate=exact.verify_and_bound(case_data,native)
                    packet['exact_certificate']=certificate
                    if certificate['status']=='CERTIFIED_LOWER_BOUND':
                        lower=Q(certificate['lower_bound'])
                        if lower>private: raise ValueError('Global response lower exceeds certified physical response upper')
                        packet['exact_support_equality']=lower==private
                        packet['certified_own_price_regret_upper']=private-lower
                elif native.get('candidate') is not None:
                    packet['replay']=verifier.verify(case_data,native['candidate'])
                return packet
            stage('OWN_PRICE_LP',60,lambda:own_price(True,60))
            stage('OWN_PRICE_MIP',120,lambda:own_price(False,120))
    except BaseException as exc:
        text=type(exc).__name__+': '+str(exc)
        failures.append(text)
        if active is not None:
            active.update(status='FAILED',reason=text)
            try: write(out/(active['id']+'.status.json'),active)
            except OSError: pass
        event(dict(event='worker_failure',reason=text))
    present={row['id'] for row in rows}
    for name in ASSIGNED:
        if name not in present: rows.append(dict(id=name,status='UNATTEMPTED',reason='Prior fatal source/qualification/resource failure'))
    u=usage()
    elapsed=time.monotonic()-started
    resources=u['cpu_s']<1100 and elapsed<1600 and u['peak_rss_bytes']<=5*1024**3
    status='CLOSED' if not failures and resources and all(row['status'] in ('DELIVERED','UNATTEMPTED') for row in rows) else 'CLOSED_FAILED'
    report=dict(status=status,assigned=4,rows=rows,failures=failures,resource_pass=resources,
        resources=u,elapsed_s=elapsed,recovery_status='CERTIFIED' if recovered is not None else 'UNRESOLVED',
        no_automatic_retries=True,original_native_charging_not_reused=True,
        scope='Fixed-topology exact charging certificate and conditional full-graph own-price diagnostics; native OPTIMAL is not a global certificate')
    write(out/'results.json',report)
    write(out/'worker_receipt.json',dict(status=status,elapsed_s=time.monotonic()-started,**usage(),
        resource_pass=resources,threads=1,memory_limit_bytes=5*1024**3,
        self_cpu_limit_s=1100,worker_wall_allowance_s=1600))
    return 0 if status=='CLOSED' else 1


if __name__=='__main__':
    raise SystemExit(main())
