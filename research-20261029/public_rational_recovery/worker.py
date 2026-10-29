"""One exact primal admission and distinct signed phase-I dual certificate.

No native solve, price query, old-candidate replay, alternate face or retry.
"""
import argparse
import copy
from fractions import Fraction as Q
import gc
import gzip
import hashlib
import io
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_rational_recovery/'
MODEL='research-20261029/public_support_resolution/'
OLD_SOURCE='3278d50f8323618bd36809b1bbb1a0da081e23ff'
CASE_REV='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
PROPOSAL_REV='2c62f1eaecf94f34071820a7ee30b096e440b251'
INPUTS=dict(case=(CASE_REV,'research-20261029/public_support_resolution/attempt01/case_descriptor.json'),
    proposal=(PROPOSAL_REV,'research-20261029/public_fixed_topology/attempt01/FIXED_QP_RECOVERY.json.gz'))
ASSIGNED=('Q0','PUBLIC_PRIMAL','PUBLIC_DUAL')
PRIMAL_LIMITS=dict(dimension=250,operations=2000000,fraction_bits=16384,seconds=30)
DUAL_LIMITS=dict(rows=250,columns=1000,pivots=2000,operations=5000000,fraction_bits=16384,seconds=60)
LITERAL_IDS=('phase-degenerate','phase-negative-rhs','phase-negative-coefficient','phase-zero-row',
             'dual-degenerate','dual-positive-sign','dual-negative-sign','dual-zero-coordinate',
             'dual-infeasible-cone','new-physical-primal')
NEGATIVE_IDS=('altered-phase-solution','zeroed-farkas','changed-lower','changed-objective',
              'wrong-positive-row-sign','wrong-negative-row-sign','forged-zero-cone-certificate','changed-residual')


def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)


def write(path,value,packed=False):
    if packed:
        with path.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as compressed:
                with io.TextIOWrapper(compressed,encoding='utf-8') as stream:
                    json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'))
                    stream.write('\n')
    else:
        with path.open('x') as stream:
            json.dump(value,stream,indent=2,default=encode,allow_nan=False);stream.write('\n')


def load(name,path,cache):
    module=types.ModuleType(name);module.__file__=str(ROOT/path)
    exec(compile(cache[path],module.__file__,'exec'),module.__dict__)
    return module


def require(condition,message):
    if not condition:raise ValueError(message)


def toy(a,b,values,rows):
    return dict(variables=[dict(index=i,period=0,lower=Q(0),upper=Q(2)) for i in range(len(values))],
                rows=rows,ops=Q(0),a=[Q(a)],b=[Q(b)])


def row(name,terms,sense,rhs):return dict(name=name,coefficients=terms,sense=sense,rhs=Q(rhs))


def qualification(helper,affine,semantic,verify,packet):
    """Fixed new certificate-algebra cases, not old native QP qualification."""
    literals,controls=packet['literals'],packet['negative_controls']
    phase_specs=(('phase-degenerate',[({0:1,1:1},1),({0:2,1:2},2),({},0)],2,'FEASIBLE'),
                 ('phase-negative-rhs',[({0:1},-1)],1,'INFEASIBLE'),
                 ('phase-negative-coefficient',[({0:-1},1)],1,'INFEASIBLE'),
                 ('phase-zero-row',[({},1)],0,'INFEASIBLE'))
    phase_results={}
    for name,equations,n,expected in phase_specs:
        item=dict(id=name,status='ATTEMPTED');literals.append(item)
        answer=helper.phase_one(equations,n,DUAL_LIMITS)
        audit=helper.verify_phase_one(equations,n,answer)
        item.update(result=answer,independent_check=audit)
        require(answer['status']==expected and audit['status']=='VERIFIED_'+expected,'Literal phase-I mismatch: '+name)
        item['status']='PASS';phase_results[name]=(equations,n,answer)
    specs=(('dual-degenerate',toy(0,1,(1,0),[
        row('sum',{0:1,1:1},'=',1),row('twice',{0:2,1:2},'=',2),
        row('ge',{0:1,1:1},'>=',1),row('le',{0:-1,1:-1},'<=',-1)]),(Q(1),Q(0)),'CERTIFIED_FIXED_TOPOLOGY_OPTIMUM'),
        ('dual-positive-sign',toy(1,0,(1,),[row('ge',{0:1},'>=',1)]),(Q(1),),'CERTIFIED_FIXED_TOPOLOGY_OPTIMUM'),
        ('dual-negative-sign',toy(-1,0,(1,),[row('le',{0:1},'<=',1)]),(Q(1),),'CERTIFIED_FIXED_TOPOLOGY_OPTIMUM'),
        ('dual-zero-coordinate',toy(1,0,(0,),[]),(Q(0),),'CERTIFIED_FIXED_TOPOLOGY_OPTIMUM'),
        ('dual-infeasible-cone',toy(-1,0,(0,),[]),(Q(0),),'DUAL_INFEASIBLE_FOR_THIS_PRIMAL'))
    certificates={}
    for name,problem,values,expected in specs:
        item=dict(id=name,status='ATTEMPTED');literals.append(item)
        result=helper.certify_dual(problem,values,DUAL_LIMITS);item['result']=result
        require(result['status']==expected,'Literal dual-cone mismatch: '+name)
        if expected=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM':
            audit=helper.check_certificate(problem,values,result);item['independent_check']=audit
            require(audit['status']=='VERIFIED_FIXED_TOPOLOGY_OPTIMUM','Literal complete certificate rejected')
            certificates[name]=(problem,values,result)
        else:
            audit=helper.verify_phase_one(result['normal_cone_equations'],result['normal_cone_variables'],result['phase_one'])
            item['independent_check']=audit
            require(audit['status']=='VERIFIED_INFEASIBLE','Literal normal-cone Farkas proof rejected')
        item['status']='PASS'
    def reject(name,action):
        result=action();controls.append(dict(id=name,result=result,status='PASS' if result['status']=='REJECTED' else 'FAIL'))
        require(result['status']=='REJECTED','Negative certificate control accepted: '+name)
    eq,n,solved=phase_results['phase-degenerate'];bad=copy.deepcopy(solved);bad['solution']=[Q(0)]*n
    reject('altered-phase-solution',lambda:helper.verify_phase_one(eq,n,bad))
    eq2,n2,solved2=phase_results['phase-negative-rhs'];bad2=copy.deepcopy(solved2);bad2['farkas']=[Q(0)]*len(eq2)
    reject('zeroed-farkas',lambda:helper.verify_phase_one(eq2,n2,bad2))
    p,x,c=certificates['dual-positive-sign']
    bad3=copy.deepcopy(c);bad3['lower_exact']+=1
    reject('changed-lower',lambda:helper.check_certificate(p,x,bad3))
    bad4=copy.deepcopy(c);bad4['objective_exact']+=1
    reject('changed-objective',lambda:helper.check_certificate(p,x,bad4))
    bad5=copy.deepcopy(c);require(bad5['multipliers']['ge']>0,'Positive-sign anchor missing');bad5['multipliers']['ge']*=-1
    reject('wrong-positive-row-sign',lambda:helper.check_certificate(p,x,bad5))
    pn,xn,cn=certificates['dual-negative-sign'];bad6=copy.deepcopy(cn)
    require(bad6['multipliers']['le']<0,'Negative-sign anchor missing');bad6['multipliers']['le']*=-1
    reject('wrong-negative-row-sign',lambda:helper.check_certificate(pn,xn,bad6))
    reject('forged-zero-cone-certificate',lambda:helper.check_certificate(toy(-1,0,(0,),[]),(Q(0),),dict(multipliers={})))
    pz,xz,cz=certificates['dual-zero-coordinate'];bad8=copy.deepcopy(cz);bad8['residuals']=[Q(-1)]
    reject('changed-residual',lambda:helper.check_certificate(pz,xz,bad8))
    item=dict(id='new-physical-primal',status='ATTEMPTED');literals.append(item)
    case=dict(name='new-rational-six-energy-literal',depot='D',max_vehicles=1,battery_kwh=20,reserve_kwh=0,
        terminal_open_min=0,recharge_deadline_min=120,vehicle_cost=4,deadhead_cost_per_min=0,efficiency=1,
        graph_scope='declared-movement-modes-only',market_edges_min=[0,60,120],
        resources=[dict(start_min=0,end_min=120,per_bus_kw=20,grid_kw=20,connectors=1)],
        trips=[dict(id='T',start_min=0,end_min=20,start_place='D',end_place='D',energy_kwh=6)],
        movements=[dict(id='out',kind='pullout',before=None,after='T',depot_split=None,
            legs=[dict(origin='D',destination='D',depart_min=0,arrive_min=0,energy_kwh=0)]),
            dict(id='in',kind='pullin',before='T',after=None,depot_split=None,
            legs=[dict(origin='D',destination='D',depart_min=20,arrive_min=20,energy_kwh=0)])])
    problem=affine.build_problem(case,['out','in'],semantic._reconstruct)
    require(len(problem['variables'])==2 and [v['period'] for v in problem['variables']]==[0,1],'Physical literal variable contract changed')
    calls=[0]
    def admission(c,value):
        calls[0]+=1;require(calls[0]==1,'Duplicate literal replay');return verify(c,value)
    recovered=helper.recover_primal(problem,dict(values=[3,3]),affine,admission,PRIMAL_LIMITS)
    item['primal']=recovered
    known=Q(4)+6*Q(float(.2))+9*Q(float(1/900))
    require(recovered['status']=='ADMITTED_PRIMAL' and recovered['objective_exact']==known and calls[0]==1,'Physical primal qualification failed')
    dual=helper.certify_dual(problem,recovered['values'],DUAL_LIMITS);item['dual']=dual
    require(dual['status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM' and dual['lower_exact']==known,'Physical literal dual qualification failed')
    item.update(status='PASS',known_exact_value=known,physical_replays=calls[0])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out).resolve();started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(140,140))
    cache,manifest,rows,fatals={},{},[],[]
    q0=dict(literals=[],negative_controls=[],status='ATTEMPTED')
    try:
        require(not sys.flags.optimize,'Assertions must be enabled')
        specs=[(REL+n,args.source_revision) for n in ('worker.py','run.py','PROTOCOL.md','recovery.py')]
        specs += [(MODEL+n,OLD_SOURCE) for n in ('exact_fixed_topology.py','exact_dual.py','independent_verify.py')]
        specs += [(path,rev) for rev,path in INPUTS.values()]
        for path,revision in specs:
            raw=(ROOT/path).read_bytes()
            fixed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=10)
            require(raw==fixed,'Stale source/input bytes: '+path)
            cache[path]=raw;manifest[path]=dict(revision=revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        del fixed
        write(out/'admission.json',dict(source_revision=args.source_revision,files=manifest,python=sys.version))
        affine=load('frozen_affine',MODEL+'exact_fixed_topology.py',cache)
        semantic=load('frozen_semantic',MODEL+'exact_dual.py',cache)
        verifier=load('frozen_physical',MODEL+'independent_verify.py',cache)
        helper=load('new_recovery',REL+'recovery.py',cache)
        active=dict(id='Q0',status='ATTEMPTED');rows.append(active)
        try:
            qualification(helper,affine,semantic,verifier.verify,q0)
            require(tuple(r['id'] for r in q0['literals'])==LITERAL_IDS and all(r['status']=='PASS' for r in q0['literals']),
                    'Literal qualification denominator/order mismatch')
            require(tuple(r['id'] for r in q0['negative_controls'])==NEGATIVE_IDS and all(r['status']=='PASS' for r in q0['negative_controls']),
                    'Negative-control denominator/order mismatch')
            q0['status']='PASS'
        except BaseException as exc:
            q0.update(status='FAIL',reason=type(exc).__name__+': '+str(exc))
            for item in q0['literals']+q0['negative_controls']:
                if item['status']=='ATTEMPTED':item.update(status='FAIL',reason=q0['reason'])
            raise
        finally:
            for name in LITERAL_IDS:
                if not any(r['id']==name for r in q0['literals']):q0['literals'].append(dict(id=name,status='UNATTEMPTED'))
            for name in NEGATIVE_IDS:
                if not any(r['id']==name for r in q0['negative_controls']):q0['negative_controls'].append(dict(id=name,status='UNATTEMPTED'))
            if q0['status']!='PASS':q0['status']='FAIL'
            write(out/'Q0.json.gz',q0,True)
        active.update(status='DELIVERED',qualification_status='PASS',literal_denominator=10,negative_control_denominator=8)
        case=json.loads(cache[INPUTS['case'][1]])
        saved=json.loads(gzip.decompress(cache[INPUTS['proposal'][1]]))
        require(saved['native']['raw_status']==2 and saved['recovery']['status']=='RECOVERY_FAILED'
            and saved['recovery']['stage']=='ALL_COORDINATE_BOX_CERTIFICATE'
            and saved['recovery']['reason']=='Recovered multiplier has wrong sign','Unexpected saved failure class')
        selected=list(saved['problem']['selected_movement_ids'])
        proposal=dict(values=list(saved['native']['proposal']['values']))
        old_mapping=[(v['index'],v['movement'],v['interval'],v['period'],Q(v['lower']),Q(v['upper'])) for v in saved['problem']['variables']]
        del saved;gc.collect()
        problem=affine.build_problem(case,selected,semantic._reconstruct)
        mapping=[(v['index'],v['movement'],v['interval'],v['period'],Q(v['lower']),Q(v['upper'])) for v in problem['variables']]
        require(mapping==old_mapping and len(proposal['values'])==len(mapping),'Saved proposal coordinate mapping mismatch')
        active=dict(id='PUBLIC_PRIMAL',status='ATTEMPTED');rows.append(active)
        calls=[0]
        def admission(c,candidate):
            calls[0]+=1;require(calls[0]==1,'Duplicate public physical replay');return verifier.verify(c,candidate)
        primal=helper.recover_primal(problem,proposal,affine,admission,PRIMAL_LIMITS)
        write(out/'PUBLIC_PRIMAL.json.gz',dict(recovery=primal,problem=problem,physical_replays=calls[0]),True)
        active.update(status='DELIVERED',primal_status=primal['status'],physical_replays=calls[0],
            physical_upper=primal.get('objective_exact') if primal['status']=='ADMITTED_PRIMAL' else None)
        if primal['status']=='ADMITTED_PRIMAL':
            require(calls[0]==1 and primal.get('physical_upper_certified') is True
                and all(primal['replay'].get(k) is True for k in
                        ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')),
                'Admitted primal lacks unique strict physical replay')
            active=dict(id='PUBLIC_DUAL',status='ATTEMPTED');rows.append(active)
            dual=helper.certify_dual(problem,primal['values'],DUAL_LIMITS)
            if dual['status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM':
                check=helper.check_certificate(problem,primal['values'],dual)
                require(check['status']=='VERIFIED_FIXED_TOPOLOGY_OPTIMUM'
                        and check['objective_exact']==primal['objective_exact'],'Public certificate does not match admitted primal')
            elif dual['status']=='DUAL_INFEASIBLE_FOR_THIS_PRIMAL':
                check=helper.verify_phase_one(dual['normal_cone_equations'],dual['normal_cone_variables'],dual['phase_one'])
                require(check['status']=='VERIFIED_INFEASIBLE','Unverified public normal-cone infeasibility')
            elif dual['status']=='DUAL_UNRESOLVED':check=dict(status='UNAVAILABLE')
            else:raise ValueError('Unknown dual result status')
            write(out/'PUBLIC_DUAL.json.gz',dict(result=dual,independent_check=check),True)
            active.update(status='DELIVERED',dual_status=dual['status'],lower_exact=dual.get('lower_exact'),
                          physical_upper_remains_admitted=True,global_optimality_or_support_claim=False)
        else:
            require(primal['status']=='PRIMAL_UNRESOLVED','Unknown primal result status')
            rows.append(dict(id='PUBLIC_DUAL',status='UNATTEMPTED',reason='New physical primal not admitted'))
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);fatals.append(reason)
        for row in rows:
            if row['status']=='ATTEMPTED':row.update(status='FAILED',reason=reason)
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='earlier fatal'))
    own,child=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime;elapsed=time.monotonic()-started
    rss=max(own.ru_maxrss,child.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    accepted=cpu<150 and elapsed<180 and rss<=5*1024**3
    result=dict(status='FATAL' if fatals else 'COMPLETED',assigned=list(ASSIGNED),rows=rows,fatals=fatals,
        resource_pass=accepted,cpu_s=cpu,elapsed_s=elapsed,peak_rss_bytes=rss,
        scope='New rational primal admission plus signed dual phase I; no native solve or global support claim')
    write(out/'results.json',result);write(out/'worker_receipt.json',{k:v for k,v in result.items() if k!='rows'})
    return 0 if not fatals and accepted else 1


if __name__=='__main__':raise SystemExit(main())
