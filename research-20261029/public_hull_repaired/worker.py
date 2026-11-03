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
import re
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_hull_repaired/'
OLD_SOURCE='199519ed9741ecc36ef88860479344a2ea9b70f7'
OLD_REL='research-20261029/public_hull_lower/'
ARTIFACT_REV='8353f03456c10c33bd2e1f0f79b3744f1ca2eac2'
MODEL='research-20261029/public_support_resolution/'
SEMANTIC_REV='3278d50f8323618bd36809b1bbb1a0da081e23ff'
CHECKER_REV='6a171357b65254b52cade63ed95dcce798485f36'
CHECKER_PATH='research-20261029/public_support_tree/checker.py'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
PINS=dict(case=('253c1e29295e766b3889fc8f5c28d9808e00b3d6','research-20261029/public_support_resolution/attempt01/case_descriptor.json'),
    metadata=(ARTIFACT_REV,OLD_REL+'attempt01/METADATA.json.gz'),
    results=(ARTIFACT_REV,OLD_REL+'attempt01/results.json'),
    owner=(ARTIFACT_REV,OLD_REL+'attempt01/owner_receipt.json'))
ASSIGNED=('LOGGING_Q0','METADATA_TRANSFER','PUBLIC_TREE','INDEPENDENT_TREE_CHECK')
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


def serialize_event(value,worker_elapsed_s):
    """Actual callback adapter: preserve native/producer clocks, add our own."""
    require(isinstance(value,dict) and 'worker_elapsed_s' not in value,'Reserved worker clock collision')
    record=dict(value)
    record['worker_elapsed_s']=worker_elapsed_s
    return json.dumps(record,default=encode,allow_nan=False)


def logging_qualification(record_event):
    examples=[dict(event='stage_begin',id='literal-phase'),
        dict(event='native_call_begin',call=1,node='literal-node',phase='literal',producer_elapsed_s=Q(1,2)),
        dict(event='native_call',call=1,node='literal-node',phase='literal',elapsed_s=0.25,producer_elapsed_s=0.75),
        dict(event='native_call_failure',call=2,node='literal-node',phase='literal',elapsed_s=0.125,producer_elapsed_s=0.875,reason='literal')]
    checks=[]
    for value in examples:
        original=dict(value)
        encoded=serialize_event(value,Q(5,4));decoded=json.loads(encoded)
        require(value==original and decoded['worker_elapsed_s']=='5/4','Event mutation/worker clock failure')
        for key,item in original.items():
            require(decoded[key]==(str(item) if isinstance(item,Q) else item),'Lost event identifier or clock')
        record_event(dict(value,qualification=True))
        checks.append(dict(id=value['event'],status='PASS'))
    for name,value in (('reserved-clock',dict(worker_elapsed_s=1)),('nonfinite-native-clock',dict(elapsed_s=float('nan')))):
        try:serialize_event(value,1)
        except ValueError:checks.append(dict(id=name,status='PASS'))
        else:raise ValueError('Invalid logging input accepted: '+name)
    return dict(status='PASS',checks=checks,backend_calls=0,old_mathematical_qualification_repeated=False)


def transfer_metadata(metadata,previous,owner,periods):
    expected=('Q0','METADATA','PUBLIC_TREE','INDEPENDENT_TREE_CHECK')
    require(previous.get('status')=='COMPLETED' and previous.get('resource_pass') is True
            and tuple(previous.get('assigned',()))==expected and tuple(r['id'] for r in previous['rows'])==expected
            and all(r['status']=='DELIVERED' for r in previous['rows']),'Previous administrative closure mismatch')
    require(owner.get('source_revision')==OLD_SOURCE and owner.get('result_status')=='COMPLETED'
            and owner.get('child_exit')==0 and owner.get('reaped') is True and owner.get('resource_pass') is True
            and owner.get('failure') is None,'Previous worker closure missing')
    require(previous['rows'][0]['summary']==dict(status='PASS',backend_calls=0,checks=19),'Previous Q0 gate mismatch')
    require(previous['rows'][2]['summary']['status']=='PRODUCER_UNRESOLVED'
            and previous['rows'][2]['summary']['native_calls']==1
            and previous['rows'][2]['summary']['stop_reason']=="TypeError: dict() got multiple values for keyword argument 'elapsed_s'",
            'Different cause than the explicitly selected repair')
    require(metadata.get('status')=='ADMITTED_FIXED_PRICE_TRANSFORM' and metadata.get('objective_mode')=='linear'
            and metadata.get('fleet_count') is None and metadata.get('all_bus_counts_retained') is True
            and metadata.get('minimum_fleet')==2,'Transferred objective/domain status mismatch')
    require(metadata['source_identity']['case_token']==CASE_TOKEN
            and metadata['source_identity']['case_input_revision']==PINS['case'][0]
            and metadata['source_identity']['case_path']==PINS['case'][1],'Transferred case identity mismatch')
    result=dict(metadata)
    for key in ('p','mean_loads','a','b'):result[key]=list(map(Q,metadata[key]))
    for key in ('H','k','epsilon','target','cbar'):result[key]=Q(metadata[key])
    require(all(len(result[k])==periods for k in ('p','mean_loads','a','b'))
            and all(p>=0 for p in result['p']) and all(e>=0 for e in result['mean_loads']), 'Transferred dimensions/sign mismatch')
    require(result['a']==[Q(float(.2))]*periods and result['b']==[Q(float(1/900))]*periods
            and result['epsilon']==Q(1,10000),'Transferred original market/epsilon mismatch')
    summary=previous['rows'][1]['summary']
    require(summary.get('status')=='ADMITTED_FIXED_PRICE_TRANSFORM'
            and all(Q(summary[k])==result[k] for k in ('H','k','epsilon','target')),'Transferred compact exact fields mismatch')
    # Adopt already admitted p/k/target as source-bound exact data; do not
    # rerun old derive/validate_derived, mixture optimization or physical replay.
    result.update(status='SOURCE_BOUND_TRANSFORM_TRANSFERRED',transfer_artifact_revision=ARTIFACT_REV,
                  old_metadata_derivation_repeated=False,old_physical_replay_repeated=False)
    return result


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
    require(re.fullmatch('[0-9a-f]{40}',args.source_revision) is not None,'Exact source revision required')
    require(out==(HERE/'attempt01').resolve(),'Only the new attempt01 output namespace is admitted')
    resource.setrlimit(resource.RLIMIT_CPU,(840,840))
    rows,failures,cache,manifest=[],[],{},{}
    active=None;tree_packet=None;scientific=None
    def event(value):
        with (out/'events.jsonl').open('a') as stream:stream.write(serialize_event(value,time.monotonic()-started)+'\n')
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
        require(control.get('native_threads')==1 and type(control.get('native_threads')) is int
                and control.get('backend_version')=='12.0.1'
                and control.get('observed_rss_bytes')==5*1024**3,'Backend/thread/memory declaration mismatch')
        require(control.get('producer_revision')==OLD_SOURCE and control.get('checker_revision')==CHECKER_REV
                and control.get('semantic_revision')==SEMANTIC_REV,'Frozen helper revision declaration mismatch')
        manifest['LAUNCH.json']=dict(bytes=len(control_raw),sha256=hashlib.sha256(control_raw).hexdigest())
        specs=[(REL+n,args.source_revision) for n in ('worker.py','run.py','PROTOCOL.md','TRANSFER_AUTHORITY.json')]
        specs += [(OLD_REL+'producer.py',OLD_SOURCE)]
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
        q0=stage('LOGGING_Q0',lambda:logging_qualification(event),
                 lambda r:dict(status=r['status'],backend_calls=r.get('backend_calls'),checks=len(r.get('checks',[]))))
        require(q0['status']=='PASS' and q0.get('backend_calls')==0,'New qualification failed')
        data=json.loads(cache[PINS['case'][1]])
        periods=len(data['market_edges_min'])-1
        def metadata():
            return transfer_metadata(json.loads(gzip.decompress(cache[PINS['metadata'][1]])),
                json.loads(cache[PINS['results'][1]]),json.loads(cache[PINS['owner'][1]]),periods)
        transformed=stage('METADATA_TRANSFER',metadata,lambda r:{k:r.get(k) for k in ('status','H','k','epsilon','target','fleet_count','all_bus_counts_retained')})
        require(Q(transformed['epsilon'])==Q(1,10000) and transformed['fleet_count'] is None
                and transformed['all_bus_counts_retained'] is True,'Transformed domain mismatch')
        require(importlib.metadata.version('gurobipy')=='12.0.1','Unexpected backend version')
        pkg=load('egglab','src/egglab/__init__.py',cache,True)
        nr=load('egglab.native_recharge','src/egglab/native_recharge.py',cache);pkg.native_recharge=nr
        flow=load('hull_energy_flow',MODEL+'energy_flow.py',cache)
        exact=load('hull_exact_dual',MODEL+'exact_dual.py',cache)
        producer=load('hull_linear_producer',OLD_REL+'producer.py',cache)
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
                lower=transformed['k']+checked['global_lower_bound']
                require(lower<=transformed['H'],'Global lower contradicts admitted hull upper')
                width=transformed['H']-lower
                closure=dict(linear_lower=checked['global_lower_bound'],hull_lower=lower,hull_upper=transformed['H'],
                             width=width,epsilon_met=width<=transformed['epsilon'])
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
