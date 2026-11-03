"""One paid admitted-partition refinement; no historical numerical audit."""
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
import re
import resource
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_physical_refinement/'
MODEL='research-20261029/public_support_resolution/'
SEMANTIC_REV='3278d50f8323618bd36809b1bbb1a0da081e23ff'
EXACT_REV='6a171357b65254b52cade63ed95dcce798485f36'
EXACT_PATH='research-20261029/public_support_tree/checker.py'
CASE_REV='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
CASE_PATH='research-20261029/public_support_resolution/attempt01/case_descriptor.json'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
MODEL_REVIEW_PATH='paper/focused-theory-20261029/MODEL_TO_CERTIFICATE_REVIEW.md'
ASSIGNED=('PREFLIGHT','Q0','PUBLIC_REFINEMENT','INDEPENDENT_REFINEMENT_CHECK')
SEARCH=dict(new_nodes=255,native_calls=300,seconds=1100,cpu_seconds=800,
    qp_seconds=10,feasibility_seconds=10,checker_seconds=10,closure_seconds=10,closure_cpu_seconds=5)


def require(condition,message):
    if not condition:raise ValueError(message)


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
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime,
        peak_rss_bytes=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))


def load(name,path,cache,package=False):
    module=types.ModuleType(name);module.__file__=str(ROOT/path)
    module.__package__=name if package else name.rpartition('.')[0]
    if package:module.__path__=[]
    sys.modules[name]=module
    exec(compile(cache[path],module.__file__,'exec'),module.__dict__)
    return module


def native_case(nr,data):
    values=dict(data)
    values['trips']=tuple(nr.Trip(**t) for t in data['trips'])
    values['movements']=tuple(nr.Movement(**dict(m,legs=tuple(nr.Leg(**l) for l in m['legs']))) for m in data['movements'])
    values['resources']=tuple(nr.Resource(**r) for r in data['resources'])
    values['market_edges_min']=tuple(data['market_edges_min'])
    return nr.NativeCase(**values)


def outward(value,up=False):
    scaled=Q(value)*1000000
    number=-((-scaled.numerator)//scaled.denominator) if up else scaled.numerator//scaled.denominator
    return ('-' if number<0 else '')+str(abs(number)//1000000)+'.'+str(abs(number)%1000000).zfill(6)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True)
    args=parser.parse_args();started=time.monotonic();out=Path(args.out).resolve()
    require(re.fullmatch('[0-9a-f]{40}',args.source_revision) is not None and out==(HERE/'attempt01').resolve(),
        'Exact source and new attempt01 namespace required')
    resource.setrlimit(resource.RLIMIT_CPU,(1100,1100))
    cache,manifest,modules,rows,failures={}, {}, {}, [], []
    active=None;base=None;base_seal=None;manifest_seal=None;data=None;case=None;packet=None;outcome=None
    def event(value):
        require('worker_elapsed_s' not in value,'Reserved worker clock collision')
        record=dict(value);record['worker_elapsed_s']=time.monotonic()-started
        with (out/'events.jsonl').open('a') as stream:stream.write(json.dumps(record,default=encode,allow_nan=False)+'\n')
    def stage(name,action,summarize,cpu_cap=None,wall_cap=None):
        nonlocal active
        require(usage()['peak_rss_bytes']<=5*1024**3,'Observed RSS exceeded')
        active=dict(id=name,status='ATTEMPTED');rows.append(active);anchor=time.monotonic();before=usage()['cpu_s']
        event(dict(event='stage_begin',id=name))
        value=action();write(out/(name+'.json.gz'),value,True)
        elapsed=time.monotonic()-anchor;cpu=usage()['cpu_s']-before
        timely=(cpu_cap is None or cpu<cpu_cap) and (wall_cap is None or elapsed<wall_cap)
        active.update(status='DELIVERED' if timely else 'LATE',summary=summarize(value),stage_cpu_s=cpu,
            stage_elapsed_s=elapsed,clock_scope='through complete compressed publication')
        write(out/(name+'.status.json'),active);event(dict(event='stage_end',id=name))
        active=None
        require(timely,'Complete frozen stage allowance exceeded: '+name)
        return value
    def preflight():
        nonlocal base,base_seal,manifest_seal,data,case
        require(not sys.flags.optimize,'Assertions must remain enabled')
        raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(raw)
        require(control.get('status')=='FROZEN' and control.get('run_id')=='attempt01'
            and control.get('source_revision')==args.source_revision,'No frozen authority')
        require(tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))==(1200,1800,1100,1500),
            'Funding mismatch')
        require(tuple(control.get('assigned',()))==ASSIGNED and control.get('epsilon')=='1/10000'
            and control.get('search_limits')==SEARCH,'Objective/domain/count changed')
        require(control.get('native_threads')==1 and type(control.get('native_threads')) is int
            and control.get('backend_version')=='12.0.1' and control.get('observed_rss_bytes')==5*1024**3,
            'Backend/thread/RSS mismatch')
        require(control.get('model_to_certificate_review')=='PASS'
            and control.get('model_review_pin')==dict(path=MODEL_REVIEW_PATH,revision=args.source_revision),
            'Independent model-to-certificate review authority differs')
        require(control.get('preflight_cpu_s')==50 and control.get('preflight_wall_s')==60
            and control.get('qualification_cpu_s')==40 and control.get('qualification_wall_s')==60
            and control.get('audit_reserve_cpu_s')==180 and control.get('audit_reserve_wall_s')==240,'Stage reserves changed')
        manifest['LAUNCH.json']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        specs=[(REL+n,args.source_revision) for n in ('worker.py','run.py','producer.py','extractor.py','checker.py','qualification.py','PROTOCOL.md')]
        specs += [(MODEL_REVIEW_PATH,args.source_revision)]
        specs += [(EXACT_PATH,EXACT_REV)]
        specs += [(MODEL+n,SEMANTIC_REV) for n in ('energy_flow.py','exact_dual.py')]
        specs += [('src/egglab/'+n,SEMANTIC_REV) for n in ('__init__.py','native_recharge.py')]
        def consume(path,revision):
            require(path not in cache,'Duplicate consumed buffer')
            value=(ROOT/path).read_bytes()
            pinned=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=2)
            require(value==pinned,'Pinned buffer differs: '+path)
            cache[path]=value;manifest[path]=dict(revision=revision,bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
        for path,revision in specs:consume(path,revision)
        modules['extractor']=load('refinement_extractor',REL+'extractor.py',cache)
        extractor=modules['extractor']
        require(control.get('input_pins')=={n:dict(revision=r,path=p) for n,(r,p) in extractor.PINS.items()},'Base input pins changed')
        require(control.get('case_pin')==dict(revision=CASE_REV,path=CASE_PATH)
            and control.get('immutable_checker_revision')==EXACT_REV and control.get('semantic_revision')==SEMANTIC_REV,
            'Original case/checker/semantic pin changed')
        for revision,path in extractor.PINS.values():consume(path,revision)
        consume(CASE_PATH,CASE_REV)
        decoded={}
        for name,(revision,path) in extractor.PINS.items():
            value=cache[path]
            decoded[name]=json.loads(gzip.decompress(value) if path.endswith('.gz') else value)
        base=extractor.adopt(decoded['tree'],decoded['audit'],decoded['results'],decoded['owner'],decoded['upper_authority'],extractor.PINS)
        require(Q(control['physical_upper'])==base['physical_upper'] and control.get('target_rule')=='physical_upper-epsilon',
            'Fixed incumbent/target declaration differs')
        del decoded;gc.collect()
        modules['wrapper']=load('refinement_wrapper',REL+'checker.py',cache)
        wrapper=modules['wrapper']
        # Seal ONCE immediately after authenticated extraction; never reseal edits.
        base_seal=wrapper.seal_base(base);manifest_seal=wrapper.seal_base(manifest)
        modules['exact_checker']=load('immutable_node_checker',EXACT_PATH,cache)
        modules['qualification']=load('refinement_qualification',REL+'qualification.py',cache)
        modules['producer']=load('refinement_producer',REL+'producer.py',cache)
        pkg=load('egglab','src/egglab/__init__.py',cache,True)
        nr=load('egglab.native_recharge','src/egglab/native_recharge.py',cache);pkg.native_recharge=nr
        modules['flow']=load('refinement_energy_flow',MODEL+'energy_flow.py',cache)
        modules['semantic']=load('refinement_semantic',MODEL+'exact_dual.py',cache)
        data=json.loads(cache[CASE_PATH]);case=native_case(nr,data)
        require(case.identity()==CASE_TOKEN==base['case_token'],'Descriptor/base/native case mismatch')
        require(control.get('opportunity_scope')==data['graph_scope']=='declared-movement-modes-only',
            'Declared movement-mode opportunity scope differs')
        require(importlib.metadata.version('gurobipy')=='12.0.1','Backend version differs')
        return dict(base=base,admitted_manifest=manifest,old_numeric_audit_repeated=False,old_search_repeated=False)
    try:
        stage('PREFLIGHT',preflight,lambda r:dict(status=r['base']['status'],base_nodes=r['base']['base_nodes'],
            frontier_count=len(r['base']['frontier']),physical_upper=r['base']['physical_upper'],target=r['base']['target']),50,60)
        wrapper=modules['wrapper']
        def original_admitted(record):
            return (record is base and wrapper.seal_base(record)==base_seal
                and wrapper.seal_base(manifest)==manifest_seal)
        require(original_admitted(base),'Base/manifest mutated after extraction')
        q0=stage('Q0',lambda:modules['qualification'].run(wrapper,modules['extractor']),
            lambda r:dict(status=r['status'],checks=len(r.get('checks',[])),native_calls=r.get('native_calls')),40,60)
        require(q0['status']=='PASS' and q0.get('native_calls')==0,'New interface qualification failed')
        require(original_admitted(base),'Qualification changed base or manifest')
        u=usage();elapsed=time.monotonic()-started
        require(u['cpu_s']+800+180+20<1100 and elapsed+1100+240+30<1500,
            'Full fixed search, final audit and publication funding unavailable')
        funded=dict(SEARCH)
        write(out/'funding.json',dict(funded=funded,pre_search=u,audit_reserve_cpu_s=180,audit_reserve_wall_s=240))
        producer_base=copy.deepcopy(base)
        def producer_admitted(record):
            return record is producer_base and wrapper.seal_base(record)==base_seal and original_admitted(base)
        require(producer_admitted(producer_base),'Separate producer copy differs from authority seal')
        def search():
            nonlocal packet
            require(producer_admitted(producer_base),'Base copy changed before search')
            packet=modules['producer'].produce(case,data,producer_base,flow=modules['flow'],checker=modules['exact_checker'],
                semantic_reconstruct=modules['semantic']._reconstruct,admit_base=producer_admitted,limits=funded,record=event)
            require(producer_admitted(producer_base) and original_admitted(base),'Base/manifest mutated during search')
            return packet
        stage('PUBLIC_REFINEMENT',search,lambda r:dict(status=r['status'],new_nodes=r['new_nodes'],native_calls=r['native_calls'],
            open_nodes=r.get('open_nodes'),stop_reason=r.get('stop_reason'),producer_failure=r.get('producer_failure')))
        def audit():
            nonlocal outcome
            anchor=time.monotonic();u=usage()
            require(u['cpu_s']+180<1100 and time.monotonic()-started+240<1500,'Complete final reserve unavailable')
            require(original_admitted(base) and producer_admitted(producer_base),'Base mutation before final audit')
            context=modules['exact_checker'].prepare(data,modules['semantic']._reconstruct,mode='quadratic',fleet_count=2,case_token=CASE_TOKEN)
            allowance=150-(time.monotonic()-anchor);require(allowance>0,'Context exhausted final checking window')
            result=wrapper.verify_refinements(context,base,packet,modules['exact_checker'],original_admitted,
                limits=dict(nodes=255,depth=255,seconds=allowance,node_seconds=10),base_seal=base_seal)
            require(original_admitted(base) and producer_admitted(producer_base),'Base/manifest changed during final check')
            valid=result.get('complete_base_coverage') is True and result.get('status') in ('VALID_REFINEMENT','VALID_BASE_WITH_REJECTED_REFINEMENTS')
            outcome='EPSILON_MET' if valid and result.get('epsilon_met') is True else 'VALID_LOWER_TARGET_UNRESOLVED' if valid else 'NO_NEW_REFINEMENT_CERTIFICATE'
            result.update(scientific_outcome=outcome,physical_only_not_CH=True,old_numeric_audit_repeated=False)
            if valid:
                result['physical_lower_outward_6dp']=outward(result['global_lower_bound'])
                result['physical_upper_outward_6dp']=outward(base['physical_upper'],True)
                result['width_upper_outward_6dp']=outward(base['physical_upper']-result['global_lower_bound'],True)
            return result
        stage('INDEPENDENT_REFINEMENT_CHECK',audit,lambda r:{k:r.get(k) for k in
            ('status','complete_base_coverage','global_lower_bound','epsilon_met','scientific_outcome',
             'new_nodes_checked','physical_lower_outward_6dp','physical_upper_outward_6dp','width_upper_outward_6dp','reason')})
    except BaseException as exc:
        reason=type(exc).__name__+': '+str(exc);failures.append(reason)
        if packet is not None and not (out/'PUBLIC_REFINEMENT.json.gz').exists():
            try:write(out/'PUBLIC_REFINEMENT.failed.json.gz',dict(packet,fatal=reason),True)
            except BaseException as output_error:
                failures.append('Failed packet preservation: '+type(output_error).__name__+': '+str(output_error))
        if active is not None:
            active.update(status='FAILED',reason=reason)
            try:write(out/(active['id']+'.status.json'),active)
            except OSError:pass
        event(dict(event='worker_failure',reason=reason))
    for name in ASSIGNED:
        if not any(r['id']==name for r in rows):rows.append(dict(id=name,status='UNATTEMPTED',reason='earlier fatal'))
    u=usage();elapsed=time.monotonic()-started
    accepted=u['cpu_s']<1100 and elapsed<1500 and u['peak_rss_bytes']<=5*1024**3
    report=dict(status='COMPLETED' if not failures and accepted else 'FATAL',assigned=list(ASSIGNED),rows=rows,failures=failures,
        resource_pass=accepted,scientific_outcome=outcome,elapsed_s=elapsed,
        opportunity_scope='declared-movement-modes-only; fixed leg times and selected depot-gap modes',
        unrestricted_retiming_or_extra_visit_claim=False,**u)
    write(out/'results.json',report);write(out/'worker_receipt.json',{k:v for k,v in report.items() if k!='rows'})
    return 0 if not failures and accepted else 1


if __name__=='__main__':raise SystemExit(main())
