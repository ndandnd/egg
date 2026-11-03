"""One full-graph LP and MIP at a transferred exact physical plan's own prices."""
import argparse
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_certified_price/'
MODEL='research-20261029/public_support_resolution/'
FROZEN='3278d50f8323618bd36809b1bbb1a0da081e23ff'
CASE_REV='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
PACKET_REV='0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee'
AUTH_REV='3cbb8c9d965e9222ef8a98191bf775b4925382a1'
CASE_ID='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
PATHS=dict(case='research-20261029/public_support_resolution/attempt01/case_descriptor.json',
    primal='research-20261029/public_rational_recovery/attempt01/PUBLIC_PRIMAL.json.gz',
    dual='research-20261029/public_rational_recovery/attempt01/PUBLIC_DUAL.json.gz',
    authority='research-20261029/public_rational_recovery/TRANSFER_AUTHORITY.json')
INPUT_REVS=dict(case=CASE_REV,primal=PACKET_REV,dual=PACKET_REV,authority=AUTH_REV)
ASSIGNED=('Q0','PRICE_LP','PRICE_MIP')
NATIVE_SECONDS=dict(PRICE_LP=60,PRICE_MIP=180)
COMPLETE_SECONDS=dict(PRICE_LP=150,PRICE_MIP=270)


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


def require(condition,message):
    if not condition:raise ValueError(message)


def exact_number(value):
    require(not isinstance(value,bool),'Boolean coefficient');return Q(value)


def identity(loads,ops,a,b,objective,claimed_prices=None):
    loads=tuple(map(exact_number,loads));ops=exact_number(ops)
    require(loads and len(loads)==len(a)==len(b) and all(x>=0 for x in loads) and all(x>=0 for x in b),
            'Invalid price-transfer dimensions/sign')
    prices=tuple(at+bt*x for at,bt,x in zip(a,b,loads))
    if claimed_prices is not None:require(tuple(map(exact_number,claimed_prices))==prices,'Transferred gradient mismatch')
    cost=ops+sum((at*x+bt*x*x/2 for at,bt,x in zip(a,b,loads)),Q(0))
    require(cost==exact_number(objective),'Transferred physical cost mismatch')
    private=ops+sum((p*x for p,x in zip(prices,loads)),Q(0))
    conjugate=sum(((p-at)**2/(2*bt) if bt else Q(0) for p,at,bt in zip(prices,a,b)),Q(0))
    require(private-conjugate==cost,'Gradient/Fenchel identity failed')
    return dict(loads=loads,ops=ops,prices=prices,objective=cost,private_score=private,conjugate=conjugate)


def response_comparison(private,lower):
    private,lower=Q(private),Q(lower)
    if lower>private:return dict(status='CONTRADICTION',private_score=private,response_lower=lower,
        own_price_regret_upper=None,exact_support_equality=False,
        reason='Exact response lower exceeds certified physical bill')
    return dict(status='EXACT_SUPPORT_CERTIFIED' if lower==private else 'SUPPORT_UNRESOLVED',
                private_score=private,response_lower=lower,own_price_regret_upper=private-lower,
                exact_support_equality=lower==private)


def qualification():
    a,b=(Q(float(.2)),)*2,(Q(float(1/900)),)*2
    cost=Q(1)+2*a[0]+2*b[0]
    good=identity((0,2),1,a,b,cost)
    controls=[]
    def reject(name,action):
        try:action()
        except (ValueError,OverflowError):controls.append(dict(id=name,rejected=True))
        else:raise ValueError('Transfer negative control accepted: '+name)
    wrong=list(good['prices']);wrong[0]+=Q(1,1024)
    reject('changed-gradient',lambda:identity((0,2),1,a,b,cost,wrong))
    reject('changed-cost',lambda:identity((0,2),1,a,b,cost+1))
    reject('negative-load',lambda:identity((-1,2),1,a,b,cost))
    equal=response_comparison(good['private_score'],good['private_score'])
    loose=response_comparison(good['private_score'],good['private_score']-1)
    contradiction=response_comparison(good['private_score'],good['private_score']+1)
    require(equal['exact_support_equality'] and loose['own_price_regret_upper']==1
            and not loose['exact_support_equality'] and contradiction['status']=='CONTRADICTION',
            'Response certificate-identity qualification failed')
    return dict(status='PASS',literal=good,negative_controls=controls,
                comparisons=[equal,loose,contradiction],scope='New stdlib transfer/identity algebra only; no repeated native Q0')


def load_module(name,path,cache,package=False):
    module=types.ModuleType(name);module.__file__=str(ROOT/path)
    module.__package__=name if package else name.rpartition('.')[0]
    if package:module.__path__=[]
    sys.modules[name]=module
    exec(compile(cache[path],module.__file__,'exec'),module.__dict__)
    return module


def case_object(nr,data):
    values=dict(data)
    values['trips']=tuple(nr.Trip(**r) for r in data['trips'])
    values['movements']=tuple(nr.Movement(**dict(r,legs=tuple(nr.Leg(**v) for v in r['legs']))) for r in data['movements'])
    values['resources']=tuple(nr.Resource(**r) for r in data['resources'])
    values['market_edges_min']=tuple(data['market_edges_min'])
    return nr.NativeCase(**values)


def transfer(authority,primal_packet,dual_packet,n):
    expected=dict(status='QUALIFIED_TRANSFER',producer_source_revision='425bf35452eb3f5444f20058ad6fd6b540ffed88',
        producer_frozen_control_prefix='869cae89',producer_namespace='research-20261029/public_rational_recovery/attempt01',
        packet_artifact_revision=PACKET_REV,case_input_revision=CASE_REV,case_path=PATHS['case'],case_identity=CASE_ID,
        primal_packet_path=PATHS['primal'],dual_packet_path=PATHS['dual'],
        candidate_pointer='/recovery/candidate',replay_pointer='/recovery/replay',loads_pointer='/recovery/loads_exact',
        own_prices_pointer='/recovery/own_prices',dual_result_pointer='/result',dual_independent_check_pointer='/independent_check',
        candidate_fields=['selected_movement_ids','charge_by_interval'],required_primal_status='ADMITTED_PRIMAL',
        required_dual_status='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM',required_dual_check_status='VERIFIED_FIXED_TOPOLOGY_OPTIMUM',
        required_replay_flags=['strict_pass','physical_strict_pass','objective_is_certified_physical_upper'],
        physical_replays=1,producer_exit=0,qualification_literal_denominator=10,qualification_negative_control_denominator=8)
    require(all(authority.get(k)==v for k,v in expected.items()),'Qualified transfer metadata mismatch')
    for k in ('primal_admitted','fixed_topology_optimum_certified','worker_reaped','resource_pass'):
        require(authority.get(k) is True,'Unqualified transfer flag: '+k)
    primal=primal_packet['recovery'];dual=dual_packet['result'];check=dual_packet['independent_check']
    require(primal['status']=='ADMITTED_PRIMAL' and dual['status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM'
            and check['status']=='VERIFIED_FIXED_TOPOLOGY_OPTIMUM','Transferred acceptance statuses mismatch')
    require(primal_packet['physical_replays']==1 and all(primal['replay'].get(k) is True for k in expected['required_replay_flags']),
            'Transferred strict physical admission missing')
    require(set(primal['candidate'])==set(expected['candidate_fields']),'Transferred candidate field contract mismatch')
    objective=Q(authority['upper_exact'])
    require(all(Q(v)==objective for v in (authority['fixed_topology_lower_exact'],primal['objective_exact'],
        primal['replay']['objective_exact'],dual['objective_exact'],dual['lower_exact'],check['objective_exact'],check['lower_exact'])),
        'Transferred exact primal/dual costs disagree')
    a,b=(Q(float(.2)),)*n,(Q(float(1/900)),)*n
    require(tuple(map(Q,primal['loads_exact']))==tuple(map(Q,primal['replay']['loads_exact'])),'Transferred replay load mismatch')
    info=identity(primal['loads_exact'],primal['replay']['ops_exact'],a,b,objective,primal['own_prices'])
    info.update(selected_movement_ids=list(primal['candidate']['selected_movement_ids']),
        source='qualified source-bound exact primal/dual transfer; no repeated physical replay or dual solve',
        is_external_incumbent=True,is_new_response_delivery=False)
    return info


def usage():
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime,
                peak_rss_bytes=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out).resolve();started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(530,530))
    cache,manifest,rows,fatals={},{},[],[]
    transferred=None;lp_bound=None;regret_lower=Q(0);bound_contradiction=False
    packet=None;packet_published=False
    def event(value):
        with (out/'events.jsonl').open('a') as stream:stream.write(json.dumps(dict(elapsed_s=time.monotonic()-started,**value),default=encode,allow_nan=False)+'\n')
    try:
        require(not sys.flags.optimize,'Assertions must remain enabled')
        specs=[(REL+n,args.source_revision) for n in ('worker.py','run.py','PROTOCOL.md')]
        specs += [(MODEL+n,FROZEN) for n in ('energy_flow.py','exact_dual.py','independent_verify.py')]
        specs += [('src/egglab/__init__.py',FROZEN),('src/egglab/native_recharge.py',FROZEN)]
        specs += [(PATHS[name],INPUT_REVS[name]) for name in PATHS]
        for path,revision in specs:
            raw=(ROOT/path).read_bytes()
            expected=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=10)
            require(raw==expected,'Frozen source/input mismatch: '+path)
            cache[path]=raw;manifest[path]=dict(revision=revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        del expected
        write(out/'admission.json',dict(source_revision=args.source_revision,files=manifest,python=sys.version))
        active=dict(id='Q0',status='ATTEMPTED');rows.append(active)
        q0=qualification();write(out/'Q0.json',q0);active.update(status='DELIVERED',qualification_status='PASS')
        case_data=json.loads(cache[PATHS['case']])
        primal=json.loads(gzip.decompress(cache[PATHS['primal']]))
        dual=json.loads(gzip.decompress(cache[PATHS['dual']]))
        authority=json.loads(cache[PATHS['authority']])
        transferred=transfer(authority,primal,dual,len(case_data['market_edges_min'])-1)
        write(out/'transferred_incumbent.json',transferred)
        del primal,dual,authority;gc.collect()
        require(importlib.metadata.version('gurobipy')=='12.0.1','Unexpected native backend version')
        package=load_module('egglab','src/egglab/__init__.py',cache,True)
        nr=load_module('egglab.native_recharge','src/egglab/native_recharge.py',cache);package.native_recharge=nr
        flow=load_module('frozen_energy_flow',MODEL+'energy_flow.py',cache)
        exact=load_module('frozen_exact_dual',MODEL+'exact_dual.py',cache)
        verify=load_module('frozen_physical',MODEL+'independent_verify.py',cache)
        case=case_object(nr,case_data)
        for name,continuous in (('PRICE_LP',True),('PRICE_MIP',False)):
            observe=usage()
            require(observe['cpu_s']+NATIVE_SECONDS[name]+120<550
                and time.monotonic()-started+COMPLETE_SECONDS[name]+180<780,
                'Insufficient complete state allowance plus closure reserve')
            require(observe['peak_rss_bytes']<=5*1024**3,'Observed RSS exceeded')
            active=dict(id=name,status='ATTEMPTED',native_allowance_s=NATIVE_SECONDS[name]);rows.append(active)
            anchor=time.monotonic();built=None
            try:
                built=flow.build(case,continuous=continuous)
                native=flow.solve(built,method='linear',seconds=NATIVE_SECONDS[name],prices=transferred['prices'],
                    startmovementids=None if continuous else transferred['selected_movement_ids'],record=event)
            finally:
                if built is not None:built['model'].dispose()
                gc.collect()
            packet=dict(id=name,native=native,external_incumbent_substituted=False,fixed_price_reset=False)
            packet_published=False
            require(tuple(map(Q,native.get('prices',())))==transferred['prices'],'Native exported prices differ from fixed exact vector')
            summary=dict(optimize_called=native.get('optimize_called'),raw_status=native.get('raw_status'),
                solution_count=native.get('solution_count'),raw_objective=native.get('raw_objective'),
                raw_bound=native.get('raw_bound'),raw_gap=native.get('raw_gap'),native_start_acceptance=native.get('native_start_acceptance'))
            if continuous:
                certificate=exact.verify_and_bound(case_data,native);packet['exact_certificate']=certificate
                summary['exact_certificate_status']=certificate['status']
                if certificate['status']=='CERTIFIED_LOWER_BOUND':
                    require(certificate.get('V_lower') is not None and Q(certificate['V_lower'])==Q(certificate['lower_bound']),
                            'Exact checker did not return a linear response lower certificate')
                    lp_bound=Q(certificate['lower_bound']);comparison=response_comparison(transferred['private_score'],lp_bound)
                    packet['support_comparison']=comparison;summary.update(comparison)
                    bound_contradiction=comparison['status']=='CONTRADICTION'
                    require(comparison['status']!='CONTRADICTION','Exact LP lower exceeds transferred physical private score')
            elif native.get('candidate') is not None:
                audit=verify.verify(case_data,native['candidate']);packet['strict_screen']=audit
                summary['strict_pass']=audit.get('strict_pass');summary['physical_strict_pass']=audit.get('physical_strict_pass')
                if all(audit.get(k) is True for k in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')):
                    require(len(audit['loads_exact'])==len(transferred['prices']),'Strict response load dimension mismatch')
                    score=Q(audit['ops_exact'])+sum((p*Q(e) for p,e in zip(transferred['prices'],audit['loads_exact'])),Q(0))
                    regret_lower=max(Q(0),transferred['private_score']-score)
                    packet.update(admitted_response_private_score=score,own_price_regret_lower=regret_lower)
                    summary.update(admitted_response_private_score=score,own_price_regret_lower=regret_lower)
                    if lp_bound is not None:
                        bound_contradiction=score<lp_bound
                        require(not bound_contradiction,'Strict response below exact LP lower')
            write(out/(name+'.json.gz'),packet,True)
            packet_published=True
            elapsed=time.monotonic()-anchor
            active.update(status='DELIVERED' if elapsed<=COMPLETE_SECONDS[name] else 'LATE',
                summary=summary,stage_elapsed_s=elapsed,complete_allowance_s=COMPLETE_SECONDS[name],
                stage_clock_scope='build, solve, exact checking/screen and completed gzip output')
            write(out/(name+'.status.json'),active)
            del native;packet=None;gc.collect()
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);fatals.append(reason)
        for row in rows:
            if row['status']=='ATTEMPTED':row.update(status='FAILED',reason=reason)
        if packet is not None and not packet_published:
            try:write(out/(packet['id']+'.failed.json.gz'),dict(packet,fatal=reason),True)
            except BaseException as output_error:fatals.append('Failed packet publication: '+type(output_error).__name__+': '+str(output_error))
    for name in ASSIGNED:
        if not any(row['id']==name for row in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='earlier fatal'))
    observe=usage();elapsed=time.monotonic()-started
    accepted=observe['cpu_s']<550 and elapsed<780 and observe['peak_rss_bytes']<=5*1024**3
    result=dict(status='FATAL' if fatals else 'COMPLETED',assigned=list(ASSIGNED),rows=rows,fatals=fatals,
        all_assigned_timely=all(r['status']=='DELIVERED' for r in rows),
        resource_pass=accepted,elapsed_s=elapsed,**observe,own_price_regret_lower=regret_lower,
        own_price_regret_upper=None if lp_bound is None or transferred is None or bound_contradiction else transferred['private_score']-lp_bound,
        exact_bound_contradiction=bound_contradiction,
        scope='Exact support only if global response lower equals certified private score; native statuses remain diagnostics')
    write(out/'results.json',result);write(out/'worker_receipt.json',{k:v for k,v in result.items() if k!='rows'})
    return 0 if not fatals and accepted else 1


if __name__=='__main__':raise SystemExit(main())
