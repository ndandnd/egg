"""One fixed-mixture-gradient all-fleet linear certificate; no price retry."""
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
REL='research-20261029/public_hull_lower/'
MODEL='research-20261029/public_support_resolution/'
SEMANTIC_REV='3278d50f8323618bd36809b1bbb1a0da081e23ff'
CHECKER_REV='6a171357b65254b52cade63ed95dcce798485f36'
CHECKER_PATH='research-20261029/public_support_tree/checker.py'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
PINS=dict(case=('253c1e29295e766b3889fc8f5c28d9808e00b3d6','research-20261029/public_support_resolution/attempt01/case_descriptor.json'),
    authority=('c5f056b90ca895786c44f96903cdaafff97fce52','research-20261029/public_price_witness/TRANSFER_AUTHORITY.json'),
    packet=('f5ec2aa5770188d173af7297620a5fcea99fef9a','research-20261029/public_price_witness/attempt01/MIXTURE.json.gz'))
ASSIGNED=('Q0','METADATA','PUBLIC_TREE','INDEPENDENT_TREE_CHECK')
SEARCH=dict(nodes=255,native_calls=300,seconds=720,cpu_seconds=600,lp_seconds=10,
            checker_seconds=10,closure_seconds=10,closure_cpu_seconds=5)


def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)


def write(path,value,packed=False):
    if packed:
        with path.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as zipped:
                with io.TextIOWrapper(zipped,encoding='utf-8') as stream:
                    json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'));stream.write('\n')
    else:
        with path.open('x') as stream:json.dump(value,stream,indent=2,default=encode,allow_nan=False);stream.write('\n')


def usage():
    own,child=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime,
                peak_rss_bytes=max(own.ru_maxrss,child.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))


def load(name,path,cache,package=False):
    module=types.ModuleType(name);module.__file__=str(ROOT/path)
    module.__package__=name if package else name.rpartition('.')[0]
    if package:module.__path__=[]
    sys.modules[name]=module
    exec(compile(cache[path],module.__file__,'exec'),module.__dict__)
    return module


def require(condition,message):
    if not condition:raise ValueError(message)


def outward(value,up=False):
    value=Q(value)*1000000
    integer=(-((-value.numerator)//value.denominator) if up
             else value.numerator//value.denominator)
    return ('-' if integer<0 else '')+str(abs(integer)//1000000)+'.'+str(abs(integer)%1000000).zfill(6)


def case_object(nr,data):
    values=dict(data)
    values['trips']=tuple(nr.Trip(**t) for t in data['trips'])
    values['movements']=tuple(nr.Movement(**dict(m,legs=tuple(nr.Leg(**l) for l in m['legs']))) for m in data['movements'])
    values['resources']=tuple(nr.Resource(**r) for r in data['resources'])
    values['market_edges_min']=tuple(data['market_edges_min'])
    return nr.NativeCase(**values)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True)
    args=parser.parse_args();out=Path(args.out).resolve();started=time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(840,840))
    rows,failures,cache,manifest=[],[],{},{}
    active=None;tree_packet=None;scientific=None
    def event(value):
        with (out/'events.jsonl').open('a') as stream:stream.write(json.dumps(dict(elapsed_s=time.monotonic()-started,**value),default=encode,allow_nan=False)+'\n')
    def stage(name,action,summarize):
        nonlocal active
        require(usage()['peak_rss_bytes']<=5*1024**3,'Observed memory ceiling exceeded')
        active=dict(id=name,status='ATTEMPTED');rows.append(active);anchor=time.monotonic()
        event(dict(event='stage_begin',id=name))
        value=action();write(out/(name+'.json.gz'),value,True)
        active.update(status='DELIVERED',summary=summarize(value),stage_elapsed_s=time.monotonic()-anchor,
                      clock_scope='through complete compressed publication')
        write(out/(name+'.status.json'),active);event(dict(event='stage_end',id=name))
        active=None
        return value
    try:
        require(not sys.flags.optimize,'Assertions must remain enabled')
        control_raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(control_raw)
        require(control.get('status')=='FROZEN' and control.get('run_id')=='attempt01'
                and control.get('source_revision')==args.source_revision,'No frozen authority')
        require(tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))==(900,1200,840,1000),
                'Resource declaration mismatch')
        require(tuple(control.get('assigned',()))==ASSIGNED and control.get('epsilon')=='1/10000','Fixed objective/denominator mismatch')
        require(control.get('search_limits')==SEARCH and control.get('audit_reserve_cpu_s')==180
                and control.get('audit_reserve_wall_s')==240,'Search/audit funding changed')
        require(control.get('inputs')=={name:dict(revision=rev,path=path) for name,(rev,path) in PINS.items()},'Input pins changed')
        manifest['LAUNCH.json']=dict(bytes=len(control_raw),sha256=hashlib.sha256(control_raw).hexdigest())
        specs=[(REL+n,args.source_revision) for n in ('producer.py','worker.py','run.py','admission.py','qualification.py','PROTOCOL.md')]
        specs += [(CHECKER_PATH,CHECKER_REV)]
        specs += [(MODEL+n,SEMANTIC_REV) for n in ('energy_flow.py','exact_dual.py')]
        specs += [('src/egglab/'+n,SEMANTIC_REV) for n in ('__init__.py','native_recharge.py')]
        specs += [(path,rev) for rev,path in PINS.values()]
        for path,revision in specs:
            raw=(ROOT/path).read_bytes()
            frozen=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=2)
            require(raw==frozen,'Pinned source/input differs: '+path)
            cache[path]=raw;manifest[path]=dict(revision=revision,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        del frozen
        write(out/'admission.json',dict(files=manifest,source_revision=args.source_revision,no_old_root=True,no_physical_replay=True))
        checker=load('hull_tree_checker',CHECKER_PATH,cache)
        admission=load('hull_admission',REL+'admission.py',cache)
        qualification=load('hull_qualification',REL+'qualification.py',cache)
        q0=stage('Q0',lambda:qualification.run(admission,checker),
                 lambda r:dict(status=r['status'],backend_calls=r.get('backend_calls'),checks=len(r.get('checks',[]))))
        require(q0['status']=='PASS' and q0.get('backend_calls')==0,'New qualification failed')
        data=json.loads(cache[PINS['case'][1]])
        periods=len(data['market_edges_min'])-1
        def metadata():
            authority=json.loads(cache[PINS['authority'][1]])
            packet=json.loads(gzip.decompress(cache[PINS['packet'][1]]))
            coefficients=dict(a=[Q(float(.2))]*periods,b=[Q(float(1/900))]*periods)
            return admission.admit(authority,packet,coefficients,PINS)
        transformed=stage('METADATA',metadata,lambda r:{k:r.get(k) for k in ('status','H','k','epsilon','target','fleet_count','all_bus_counts_retained')})
        require(Q(transformed['epsilon'])==Q(1,10000) and transformed['fleet_count'] is None
                and transformed['all_bus_counts_retained'] is True,'Transformed domain mismatch')
        require(importlib.metadata.version('gurobipy')=='12.0.1','Unexpected backend version')
        pkg=load('egglab','src/egglab/__init__.py',cache,True)
        nr=load('egglab.native_recharge','src/egglab/native_recharge.py',cache);pkg.native_recharge=nr
        flow=load('hull_energy_flow',MODEL+'energy_flow.py',cache)
        exact=load('hull_exact_dual',MODEL+'exact_dual.py',cache)
        producer=load('hull_linear_producer',REL+'producer.py',cache)
        case=case_object(nr,data);require(case.identity()==CASE_TOKEN,'Descriptor/native identity mismatch')
        context=checker.prepare(data,exact._reconstruct,mode='linear',prices=transformed['p'],fleet_count=None,case_token=CASE_TOKEN)
        require(context['minimum_fleet_proof']['minimum_fleet']>=2,'Original minimum fleet cut not admitted')
        del context
        before=usage();elapsed=time.monotonic()-started
        funded=dict(SEARCH)
        funded['cpu_seconds']=min(SEARCH['cpu_seconds'],840-before['cpu_s']-180)
        funded['seconds']=min(SEARCH['seconds'],1000-elapsed-240)
        require(funded['cpu_seconds']>0 and funded['seconds']>0,'No full search and audit funding')
        write(out/'funding.json',dict(funded=funded,pre_search=before,audit_cpu_reserve=180,audit_wall_reserve=240))
        def search():
            nonlocal tree_packet
            tree_packet=producer.produce(case,data,flow=flow,checker=checker,semantic_reconstruct=exact._reconstruct,
                case_token=CASE_TOKEN,prices=transformed['p'],target=transformed['target'],limits=funded,record=event)
            return tree_packet
        stage('PUBLIC_TREE',search,lambda r:dict(status=r['status'],nodes=len(r['tree']['nodes']),native_calls=r['native_calls'],
            open_fringe=r.get('open_fringe'),stop_reason=r.get('stop_reason'),cpu_s=r['cpu_s'],elapsed_s=r['elapsed_s']))
        def audit():
            nonlocal scientific
            anchor=time.monotonic();u=usage()
            require(u['cpu_s']+180<840 and time.monotonic()-started+240<1000,'Complete final reserve unavailable')
            ctx=checker.prepare(data,exact._reconstruct,mode='linear',prices=transformed['p'],fleet_count=None,case_token=CASE_TOKEN)
            expanded=producer.materialize_tree(tree_packet)
            allowance=150-(time.monotonic()-anchor)
            require(allowance>0,'Final context/materialization exhausted checking window')
            checked=checker.verify_tree(ctx,expanded,target=transformed['target'],
                limits=dict(nodes=255,depth=255,operations=100000000,fraction_bits=32768,seconds=allowance))
            complete=checked.get('status')=='COMPLETE' and checked.get('complete') is True and isinstance(checked.get('global_lower_bound'),Q)
            require(not (checked.get('status')=='COMPLETE' and checked.get('all_leaves_infeasible')),
                    'All-fleet infeasibility contradicts admitted mixture components')
            result=dict(checked)
            result['leaves']=[dict(id=l['id'],status=l['certificate']['status'],lower_bound=l['certificate']['lower_bound'],
                contradiction=l['certificate']['contradiction']) for l in checked.get('leaves',[])]
            if complete:
                closure=admission.close_bound(transformed,checked['global_lower_bound'])
                closure.update(hull_lower_outward_6dp=outward(closure['hull_lower']),
                               hull_upper_outward_6dp=outward(closure['hull_upper'],True),
                               width_upper_outward_6dp=outward(closure['width'],True))
                result['closure']=closure
                scientific='EPSILON_MET' if closure['epsilon_met'] else 'VALID_LOWER_ACCURACY_UNRESOLVED'
            else:scientific='NO_COMPLETE_LINEAR_LOWER'
            result.update(scientific_outcome=scientific,prices_unchanged=True,physical_gap_sign_certificate_unchanged=True,
                no_exact_optimum_claim=True,scope='All-fleet V(p) lower plus frozen tangent k gives CH lower')
            return result
        stage('INDEPENDENT_TREE_CHECK',audit,lambda r:dict(status=r['status'],complete=r.get('complete'),
              global_linear_lower=r.get('global_lower_bound'),closure=r.get('closure'),scientific_outcome=r['scientific_outcome']))
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);failures.append(reason)
        if active is not None:
            active.update(status='FAILED',reason=reason)
            try:write(out/(active['id']+'.status.json'),active)
            except OSError:pass
        event(dict(event='worker_failure',reason=reason))
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='earlier fatal'))
    u=usage();elapsed=time.monotonic()-started
    accepted=u['cpu_s']<840 and elapsed<1000 and u['peak_rss_bytes']<=5*1024**3
    result=dict(status='COMPLETED' if not failures and accepted else 'FATAL',assigned=list(ASSIGNED),rows=rows,failures=failures,
                resource_pass=accepted,scientific_outcome=scientific,elapsed_s=elapsed,**u)
    write(out/'results.json',result);write(out/'worker_receipt.json',{k:v for k,v in result.items() if k!='rows'})
    return 0 if not failures and accepted else 1


if __name__=='__main__':raise SystemExit(main())
