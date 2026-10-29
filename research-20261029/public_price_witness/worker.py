"""New fixed-route LP proposal, rational physical admission and hull mixture.

Full-route discovery and old candidate replay are excluded. Original quadratic
primal recovery and fixed-price dual certification deliberately use different
objective descriptors, with the same original feasible charging system.
"""
import argparse
import copy
from fractions import Fraction as Q
import gc
import gzip
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REL='research-20261029/public_price_witness/';MODEL='research-20261029/public_support_resolution/'
AFFINE_REV='3278d50f8323618bd36809b1bbb1a0da081e23ff'
RECOVERY_REV='425bf35452eb3f5444f20058ad6fd6b540ffed88'
TRANSFER_SOURCE='0c562e338ea23e1c5de3215c968afeec6ba2e3bf'
PRICE_WORKER='research-20261029/public_certified_price/worker.py'
PATHS=dict(case='research-20261029/public_support_resolution/attempt01/case_descriptor.json',
    routes='research-20261029/public_certified_price/attempt01/PRICE_MIP.json.gz',
    primal='research-20261029/public_rational_recovery/attempt01/PUBLIC_PRIMAL.json.gz',
    dual='research-20261029/public_rational_recovery/attempt01/PUBLIC_DUAL.json.gz',
    authority='research-20261029/public_rational_recovery/TRANSFER_AUTHORITY.json')
REVISIONS=dict(case='253c1e29295e766b3889fc8f5c28d9808e00b3d6',routes='fef98584fe130da0c5647426a7ce599846340fd9',
    primal='0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee',dual='0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee',
    authority='3cbb8c9d965e9222ef8a98191bf775b4925382a1')
ASSIGNED=('Q0','FIXED_PRICE_LP','EXACT_PRIMAL','FIXED_PRICE_DUAL','MIXTURE')
PRIMAL_LIMITS=dict(dimension=250,operations=2000000,fraction_bits=16384,seconds=30)
DUAL_LIMITS=dict(rows=250,columns=1000,pivots=2000,operations=5000000,fraction_bits=16384,seconds=60)
STAGE_CAPS=dict(Q0=30,FIXED_PRICE_LP=105,EXACT_PRIMAL=60,FIXED_PRICE_DUAL=90,MIXTURE=30)
NEXT_CPU_ALLOWANCES=dict(Q0=30,FIXED_PRICE_LP=75,EXACT_PRIMAL=60,FIXED_PRICE_DUAL=90,MIXTURE=30)


def require(ok,message):
    if not ok:raise ValueError(message)


def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)


def write(path,value,packed=False):
    if packed:
        with path.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as compressed:
                with io.TextIOWrapper(compressed,encoding='utf-8') as stream:
                    json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'));stream.write('\n')
    else:
        with path.open('x') as stream:json.dump(value,stream,indent=2,default=encode,allow_nan=False);stream.write('\n')


def load(name,path,cache):
    module=types.ModuleType(name);module.__file__=str(ROOT/path)
    exec(compile(cache[path],module.__file__,'exec'),module.__dict__);return module


def cost(loads,ops,a,b):return Q(ops)+sum((Q(at)*Q(e)+Q(bt)*Q(e)**2/2 for at,bt,e in zip(a,b,loads)),Q(0))


def mixture(left,right,a,b):
    require(len(left['loads'])==len(right['loads'])==len(a)==len(b) and all(v>=0 for v in b),'Invalid convex mixture dimensions')
    require(cost(left['loads'],left['ops'],a,b)==left['objective'] and cost(right['loads'],right['ops'],a,b)==right['objective'],
            'Mixture endpoint objective mismatch')
    delta=[y-x for x,y in zip(left['loads'],right['loads'])]
    linear=right['ops']-left['ops']+sum(((at+bt*x)*d for at,bt,x,d in zip(a,b,left['loads'],delta)),Q(0))
    quadratic=sum((bt*d*d/2 for bt,d in zip(b,delta)),Q(0))
    w=min(Q(1),max(Q(0),-linear/(2*quadratic))) if quadratic else Q(int(linear<0))
    mean=[(1-w)*x+w*y for x,y in zip(left['loads'],right['loads'])]
    ops=(1-w)*left['ops']+w*right['ops']
    return dict(lambda_right=w,lambda_left=1-w,loads=mean,ops=ops,
        objective=left['objective']+linear*w+quadratic*w*w,
        weight_minimizers=(Q(0),Q(1)) if linear==quadratic==0 else (w,w))


def check_mixture(left,right,a,b,answer):
    require(len(left['loads'])==len(right['loads'])==len(a)==len(b) and all(v>=0 for v in b),'Mixture audit dimensions/curvature')
    w=Q(answer['lambda_right']);require(0<=w<=1 and Q(answer['lambda_left'])==1-w,'Invalid mixture weights')
    mean=tuple((1-w)*Q(x)+w*Q(y) for x,y in zip(left['loads'],right['loads']))
    ops=(1-w)*Q(left['ops'])+w*Q(right['ops'])
    value=cost(mean,ops,a,b)
    require(tuple(map(Q,answer['loads']))==mean and Q(answer['ops'])==ops and Q(answer['objective'])==value,'Mixture direct evaluation mismatch')
    derivative=Q(right['ops'])-Q(left['ops'])+sum(((Q(at)+Q(bt)*e)*(Q(y)-Q(x))
        for at,bt,e,x,y in zip(a,b,mean,left['loads'],right['loads'])),Q(0))
    require((w==0 and derivative>=0) or (w==1 and derivative<=0) or (0<w<1 and derivative==0),'Mixture KKT failed')
    curvature=sum((Q(bt)*(Q(y)-Q(x))**2 for bt,x,y in zip(b,left['loads'],right['loads'])),Q(0))
    expected=(Q(0),Q(1)) if curvature==0 and derivative==0 else (w,w)
    require(tuple(map(Q,answer['weight_minimizers']))==expected,'Mixture tie-set mismatch')
    return dict(status='PASS',objective_exact=value,derivative=derivative,curvature=curvature)


def qualification(helper,affine,semantic,verifier):
    rows=[]
    # New abstract mixture branch checks, not prior witness/qualification replay.
    specs=(('interior',(4,0),(0,4),3,3,Q(1,2)),('left',(0,),(1,),0,1,Q(0)),
           ('right',(0,),(1,),2,0,Q(1)),('flat',(1,),(1,),0,0,Q(0)),
           ('zero-curvature-improvement',(1,),(1,),1,0,Q(1)))
    for name,e0,e1,c0,c1,w in specs:
        a=[Q(0)]*len(e0);b=[Q(1)]*len(e0)
        left=dict(loads=tuple(map(Q,e0)),ops=Q(c0),objective=cost(e0,c0,a,b))
        right=dict(loads=tuple(map(Q,e1)),ops=Q(c1),objective=cost(e1,c1,a,b))
        answer=mixture(left,right,a,b);audit=check_mixture(left,right,a,b,answer)
        require(answer['lambda_right']==w,'Mixture branch anchor failed')
        rows.append(dict(id=name,status='PASS',result=answer,audit=audit))
        if name=='interior':interior=(left,right,a,b,answer)
    wrong=copy.deepcopy(answer);wrong['objective']+=1
    try:check_mixture(left,right,a,b,wrong)
    except ValueError:negative=dict(changed_objective_rejected=True)
    else:raise ValueError('Altered mixture objective accepted')
    il,ir,ia,ib,iv=interior
    wrong_weight=copy.deepcopy(iv)
    wrong_weight.update(lambda_right=Q(1,4),lambda_left=Q(3,4),loads=[Q(3),Q(1)],ops=Q(3),
                        objective=Q(8),weight_minimizers=(Q(1,4),Q(1,4)))
    try:check_mixture(il,ir,ia,ib,wrong_weight)
    except ValueError:negative['changed_weight_KKT_rejected']=True
    else:raise ValueError('Wrong stationary mixture weight accepted')
    case=dict(name='new-price-face-four-energy',depot='D',max_vehicles=1,battery_kwh=20,reserve_kwh=0,efficiency=1,
        terminal_open_min=0,recharge_deadline_min=120,vehicle_cost=3,deadhead_cost_per_min=0,graph_scope='declared-movement-modes-only',
        market_edges_min=[0,60,120],resources=[dict(start_min=0,end_min=120,per_bus_kw=20,grid_kw=20,connectors=1)],
        trips=[dict(id='T',start_min=0,end_min=30,start_place='D',end_place='D',energy_kwh=4)],
        movements=[dict(id='out',kind='pullout',before=None,after='T',depot_split=None,
            legs=[dict(origin='D',destination='D',depart_min=0,arrive_min=0,energy_kwh=0)]),
            dict(id='in',kind='pullin',before='T',after=None,depot_split=None,
            legs=[dict(origin='D',destination='D',depart_min=30,arrive_min=30,energy_kwh=0)])])
    problem=affine.build_problem(case,['out','in'],semantic._reconstruct)
    require(len(problem['variables'])==2,'New price-face literal variable contract changed')
    p=[problem['a'][0]+4*problem['b'][0],problem['a'][1]]
    calls=[0]
    def screen(c,x):calls[0]+=1;require(calls[0]==1,'Duplicate literal physical screen');return verifier(c,x)
    primal=helper.recover_primal(problem,dict(values=[0,4]),affine,screen,PRIMAL_LIMITS)
    require(primal['status']=='ADMITTED_PRIMAL' and calls[0]==1,'Original-quadratic face admission failed')
    price_problem=dict(problem,a=p,b=[Q(0)]*2)
    dual=helper.certify_dual(price_problem,primal['values'],DUAL_LIMITS)
    score=Q(primal['replay']['ops_exact'])+sum((price*Q(e) for price,e in zip(p,primal['loads_exact'])),Q(0))
    require(dual['status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM' and dual['lower_exact']==score
            and score!=primal['objective_exact'],'Linear/quadratic objective-interface qualification failed')
    audit=helper.check_certificate(price_problem,primal['values'],dual)
    require(audit['status']=='VERIFIED_FIXED_TOPOLOGY_OPTIMUM','Literal fixed-price certificate rejected')
    wrong_objective=copy.deepcopy(dual);wrong_objective['objective_exact']=primal['objective_exact']
    require(helper.check_certificate(price_problem,primal['values'],wrong_objective)['status']=='REJECTED',
            'Quadratic physical cost incorrectly accepted as fixed-price objective')
    negative['quadratic_as_linear_objective_rejected']=True
    return dict(status='PASS',mixture_branches=rows,negative_control=negative,
                physical_primal=primal,fixed_price_dual=dual,fixed_price_check=audit,physical_screens=calls[0],
                scope='New stdlib interface/mixture checks; no native Q0 or old public replay')


def native_lp(problem,prices,seconds):
    started=time.monotonic()
    import gurobipy as gp
    model=gp.Model('new-fixed-route-price-lp')
    try:
        model.Params.OutputFlag=0;model.Params.Threads=1;model.Params.Method=0
        model.Params.FeasibilityTol=1e-8;model.Params.OptimalityTol=1e-8
        variables=[model.addVar(lb=float(v['lower']),ub=float(v['upper']),name=v['name']) for v in problem['variables']]
        model.update()
        for row in problem['rows']:
            expr=gp.LinExpr([float(c) for c in row['coefficients'].values()],[variables[i] for i in row['coefficients']])
            if row['sense']=='=':model.addConstr(expr==float(row['rhs']),name=row['name'])
            elif row['sense']=='<=':model.addConstr(expr<=float(row['rhs']),name=row['name'])
            elif row['sense']=='>=':model.addConstr(expr>=float(row['rhs']),name=row['name'])
            else:raise ValueError('Unknown exact row sense')
        model.setObjective(float(problem['ops'])+gp.quicksum(float(prices[v['period']])*variables[v['index']] for v in problem['variables']),gp.GRB.MINIMIZE)
        remaining=seconds-(time.monotonic()-started)
        answer=dict(optimize_called=remaining>0,raw_status=None,solution_count=0,proposal=None,native_only=True,exact_certificate=False)
        if remaining>0:
            model.Params.TimeLimit=remaining;model.optimize()
            answer.update(raw_status=int(model.Status),solution_count=int(model.SolCount))
            if model.SolCount:answer.update(raw_objective=float(model.ObjVal),proposal=dict(values=[float(v.X) for v in variables]))
        answer['complete_native_elapsed_s']=time.monotonic()-started
        return answer
    finally:model.dispose();gc.collect()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out).resolve();started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(240,240))
    rows,fatals,cache,manifest=[],[],{},{}
    incumbent=None;primal=None;response=None;mix=None
    def stage(name,action):
        own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
        spent=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
        require(spent+NEXT_CPU_ALLOWANCES[name]+20<260 and
                time.monotonic()-started+STAGE_CAPS[name]+30<360,
                'Insufficient complete next-stage funding with closure reserve: '+name)
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic()
        try:packet=action()
        except BaseException as exc:row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc));raise
        write(out/(name+'.json.gz'),packet,True)
        summary=dict(packet.get('summary',{}))
        if 'recovery' in packet:
            r=packet['recovery'];summary.update(primal_status=r['status'],stage=r.get('stage'),reason=r.get('reason'),objective_exact=r.get('objective_exact'))
        if 'native' in packet:
            n=packet['native'];summary.update(optimize_called=n['optimize_called'],raw_status=n['raw_status'],solution_count=n['solution_count'])
        if name=='Q0':summary['qualification_status']=packet['status']
        row.update(status='DELIVERED' if time.monotonic()-anchor<=STAGE_CAPS[name] else 'LATE',
                   stage_elapsed_s=time.monotonic()-anchor,summary=summary)
        write(out/(name+'.status.json'),row)
        if row['status']=='LATE':raise TimeoutError('Complete stage exceeded frozen allowance: '+name)
        return packet
    try:
        require(not sys.flags.optimize,'Assertions must be enabled')
        specs=[(REL+n,args.source_revision) for n in ('worker.py','run.py','PROTOCOL.md')]
        specs += [(MODEL+n,AFFINE_REV) for n in ('exact_fixed_topology.py','exact_dual.py','independent_verify.py')]
        specs += [('research-20261029/public_rational_recovery/recovery.py',RECOVERY_REV),(PRICE_WORKER,TRANSFER_SOURCE)]
        specs += [(PATHS[name],REVISIONS[name]) for name in PATHS]
        for path,revision in specs:
            raw=(ROOT/path).read_bytes();frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=10)
            require(raw==frozen,'Frozen byte mismatch: '+path);cache[path]=raw
            manifest[path]=dict(revision=revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        del frozen
        write(out/'admission.json',dict(source_revision=args.source_revision,files=manifest,python=sys.version))
        affine=load('frozen_affine',MODEL+'exact_fixed_topology.py',cache)
        semantic=load('frozen_semantic',MODEL+'exact_dual.py',cache)
        verifier=load('frozen_physical',MODEL+'independent_verify.py',cache)
        helper=load('qualified_recovery','research-20261029/public_rational_recovery/recovery.py',cache)
        transfer_api=load('qualified_transfer',PRICE_WORKER,cache)
        stage('Q0',lambda:qualification(helper,affine,semantic,verifier.verify))
        case=json.loads(cache[PATHS['case']])
        oldprimal=json.loads(gzip.decompress(cache[PATHS['primal']]))
        olddual=json.loads(gzip.decompress(cache[PATHS['dual']]))
        authority=json.loads(cache[PATHS['authority']])
        incumbent=transfer_api.transfer(authority,oldprimal,olddual,len(case['market_edges_min'])-1)
        write(out/'transferred_incumbent.json',incumbent)
        del oldprimal,olddual,authority;gc.collect()
        packet=json.loads(gzip.decompress(cache[PATHS['routes']]))
        require(packet.get('id')=='PRICE_MIP' and packet['native']['continuous'] is False,'Wrong saved response state')
        selected=list(packet['native']['candidate']['selected_movement_ids'])
        write(out/'route_provenance.json',dict(revision=REVISIONS['routes'],path=PATHS['routes'],
            native_status=packet['native'].get('raw_status'),strict_pass=packet.get('strict_screen',{}).get('strict_pass'),
            classification=packet.get('strict_screen',{}).get('classification'),
            use='selected movement IDs only; old charges/ledger never used or replayed',selected_movement_ids=selected))
        del packet;gc.collect()
        require(importlib.metadata.version('gurobipy')=='12.0.1','Unexpected backend version')
        def lp_action():
            value=affine.build_problem(case,selected,semantic._reconstruct)
            require(len(value['a'])==len(incumbent['prices']),'Fixed-price dimension mismatch')
            return dict(problem=value,native=native_lp(value,incumbent['prices'],60),
                        summary=dict(scope='one cold price-only charging LP on selected fixed routes'))
        native=stage('FIXED_PRICE_LP',lp_action)
        problem=native['problem']
        if native['native']['proposal'] is None:
            for name in ASSIGNED[2:]:rows.append(dict(id=name,status='UNATTEMPTED',reason='No new fixed-LP value proposal'))
        else:
            calls=[0]
            def screen(c,x):calls[0]+=1;require(calls[0]==1,'Duplicate public physical screen');return verifier.verify(c,x)
            primal=stage('EXACT_PRIMAL',lambda:dict(recovery=helper.recover_primal(problem,native['native']['proposal'],affine,screen,PRIMAL_LIMITS)))['recovery']
            if primal['status']!='ADMITTED_PRIMAL':
                require(primal['status']=='PRIMAL_UNRESOLVED','Unknown primal status')
                rows += [dict(id=name,status='UNATTEMPTED',reason='New rational physical primal not admitted') for name in ASSIGNED[3:]]
            else:
                require(calls[0]==1 and all(primal['replay'].get(k) is True for k in
                    ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')),'Missing unique strict new physical screen')
                physical_loads=tuple(map(Q,primal['replay']['loads_exact']))
                require(physical_loads==tuple(map(Q,primal['loads_exact'])) and len(physical_loads)==len(incumbent['prices']),
                        'New physical replay/charge-model load mapping mismatch')
                response=dict(loads=physical_loads,ops=Q(primal['replay']['ops_exact']),objective=Q(primal['replay']['objective_exact']))
                require(response['objective']==Q(primal['objective_exact']),'New physical objective mismatch')
                score=response['ops']+sum((p*e for p,e in zip(incumbent['prices'],response['loads'])),Q(0))
                response.update(private_score=score,own_price_regret_lower=max(Q(0),incumbent['private_score']-score),
                    cheaper_at_fixed_price=score<incumbent['private_score'])
                write(out/'new_physical_response.json',response)
                price_problem=dict(problem,a=list(incumbent['prices']),b=[Q(0)]*len(problem['a']))
                def dual_action():
                    value=helper.certify_dual(price_problem,primal['values'],DUAL_LIMITS)
                    if value['status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM':
                        audit=helper.check_certificate(price_problem,primal['values'],value)
                        require(audit['status']=='VERIFIED_FIXED_TOPOLOGY_OPTIMUM' and audit['objective_exact']==score,'Fixed-price dual objective mismatch')
                    elif value['status']=='DUAL_INFEASIBLE_FOR_THIS_PRIMAL':
                        audit=helper.verify_phase_one(value['normal_cone_equations'],value['normal_cone_variables'],value['phase_one'])
                        require(audit['status']=='VERIFIED_INFEASIBLE','Invalid normal-cone Farkas proof')
                    elif value['status']=='DUAL_UNRESOLVED':audit=dict(status='UNAVAILABLE')
                    else:raise ValueError('Unknown dual status')
                    return dict(result=value,independent_check=audit,
                        objective_semantics='fixed-price linear bill plus operating cost; not original quadratic physical cost',
                        summary=dict(dual_status=value['status'],physical_response_remains_admitted=True))
                stage('FIXED_PRICE_DUAL',dual_action)
                def mix_action():
                    value=mixture(incumbent,response,problem['a'],problem['b'])
                    audit=check_mixture(incumbent,response,problem['a'],problem['b'],value)
                    return dict(mixture=value,independent_check=audit,hull_upper_exact=value['objective'],
                        summary=dict(hull_upper_exact=value['objective'],own_price_regret_lower=response['own_price_regret_lower'],
                            cheaper_at_fixed_price=response['cheaper_at_fixed_price'],
                            improves_transferred_physical_objective=value['objective']<incumbent['objective'],
                            comparator_exact=incumbent['objective'],global_gap_sign_claim=False))
                mix=stage('MIXTURE',mix_action)
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);fatals.append(reason)
        for row in rows:
            if row['status']=='ATTEMPTED':row.update(status='FAILED',reason=reason)
    for name in ASSIGNED:
        if not any(row['id']==name for row in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='earlier fatal'))
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime;elapsed=time.monotonic()-started
    rss=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    accepted=cpu<260 and elapsed<360 and rss<=5*1024**3
    report=dict(status='FATAL' if fatals else 'COMPLETED',assigned=list(ASSIGNED),rows=rows,fatals=fatals,
        resource_pass=accepted,cpu_s=cpu,elapsed_s=elapsed,peak_rss_bytes=rss,
        new_physical_response_admitted=response is not None,cheaper_at_fixed_price=response.get('cheaper_at_fixed_price',False) if response else False,
        own_price_regret_lower=response.get('own_price_regret_lower') if response else None,
        hull_upper_exact=mix.get('hull_upper_exact') if mix else None,
        scope='New fixed-route construction; no global response optimum, physical planner optimum or support-gap sign claim')
    write(out/'results.json',report);write(out/'worker_receipt.json',{k:v for k,v in report.items() if k!='rows'})
    return 0 if not fatals and accepted and not any(r['status']=='LATE' for r in rows) else 1


if __name__=='__main__':raise SystemExit(main())
