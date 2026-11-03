"""One prospective checker qualification, physical tree search and final audit.

No physical replay, old-root packet, or native public backend probe is included.
All dispatch/input/funding fields must be frozen by the parent before execution.
"""
import argparse
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
REL='research-20261029/public_support_tree/'
MODEL='research-20261029/public_support_resolution/'
SEMANTIC_REVISION='3278d50f8323618bd36809b1bbb1a0da081e23ff'
CASE_REVISION='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
CASE_PATH='research-20261029/public_support_resolution/attempt01/case_descriptor.json'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
TARGET_SOURCE='cddd5072be949c36a8f674dd12298503a73407a7'
TARGET_CONTROL='61b14412'
TARGET_NAMESPACE='research-20261029/public_price_witness/attempt01'
INPUTS=dict(case=(CASE_REVISION,CASE_PATH),
    target=('c5f056b90ca895786c44f96903cdaafff97fce52','research-20261029/public_price_witness/TRANSFER_AUTHORITY.json'),
    target_results=('f5ec2aa5770188d173af7297620a5fcea99fef9a',TARGET_NAMESPACE+'/results.json'))
LOCAL=[REL+n for n in ('worker.py','run.py','checker.py','producer.py','qualification.py','PROTOCOL.md','QUALIFICATION_REVIEW.md')]
SEMANTIC=[MODEL+'energy_flow.py',MODEL+'exact_dual.py','src/egglab/__init__.py','src/egglab/native_recharge.py']
ASSIGNED=('Q0','PUBLIC_TREE','INDEPENDENT_TREE_CHECK')


def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)


def display_bound(value,up=False):
    """Outward six-decimal display only; all scientific comparisons stay exact."""
    scaled=Q(value)*1000000
    integer=-((-scaled).numerator//scaled.denominator) if up else scaled.numerator//scaled.denominator
    sign='-' if integer<0 else ''
    magnitude=abs(integer)
    return sign+str(magnitude//1000000)+'.'+str(magnitude%1000000).zfill(6)


def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,default=encode,allow_nan=False);stream.write('\n')


def compressed(path,value):
    with gzip.open(path,'xt',encoding='utf-8',compresslevel=6) as stream:
        json.dump(value,stream,default=encode,allow_nan=False,separators=(',',':'));stream.write('\n')


def usage():
    own,child=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime,
        peak_rss_bytes=max(own.ru_maxrss,child.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))


def load_module(name,path,cache,package=False):
    module=types.ModuleType(name);module.__file__=str(ROOT/path)
    module.__package__=name if package else name.rpartition('.')[0]
    if package:module.__path__=[]
    sys.modules[name]=module
    exec(compile(cache[path],module.__file__,'exec'),module.__dict__)
    return module


def case_from_dict(nr,data):
    values=dict(data)
    values['trips']=tuple(nr.Trip(**t) for t in data['trips'])
    values['movements']=tuple(nr.Movement(**dict(m,legs=tuple(nr.Leg(**l) for l in m['legs']))) for m in data['movements'])
    values['resources']=tuple(nr.Resource(**r) for r in data['resources'])
    values['market_edges_min']=tuple(data['market_edges_min'])
    return nr.NativeCase(**values)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True)
    args=parser.parse_args();out=Path(args.out).resolve()
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(3540,3540))
    rows,failures,cache,manifest=[],[],{},{}
    active=None;public_packet=None;audit_summary=None
    def event(value):
        with (out/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(worker_elapsed_s=time.monotonic()-started,**value),default=encode,allow_nan=False)+'\n')
    def stage(name,action,summarize):
        nonlocal active
        if usage()['peak_rss_bytes']>5*1024**3:raise RuntimeError('Observed memory ceiling exceeded')
        active=dict(id=name,status='ATTEMPTED');rows.append(active)
        anchor=time.monotonic();event(dict(event='stage_begin',id=name))
        value=action();compressed(out/(name+'.json.gz'),value)
        active.update(status='DELIVERED',packet=name+'.json.gz',summary=summarize(value),
            stage_elapsed_s=time.monotonic()-anchor,stage_clock_scope='through complete compressed packet publication',resources=usage())
        write(out/(name+'.status.json'),active);event(dict(event='stage_end',id=name))
        answer=dict(active);active=None;return answer
    try:
        if sys.flags.optimize:raise ValueError('Assertions/qualification guards must remain enabled')
        raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(raw)
        if (control.get('status')!='FROZEN' or control.get('source_revision')!=args.source_revision
            or control.get('run_id')!='attempt01'):raise ValueError('No frozen dispatch authority')
        if tuple(control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s'))!=(3600,5400,3540,5200):
            raise ValueError('Funding mismatch')
        planned=control['search_limits']
        if (set(planned)!={'nodes','native_calls','seconds','cpu_seconds','qp_seconds','infeasibility_lp_seconds',
                          'checker_seconds','closure_seconds','closure_cpu_seconds'}
            or type(planned['nodes']) is not int or not 1<=planned['nodes']<=500
            or type(planned['native_calls']) is not int or not 1<=planned['native_calls']<=1000
            or not 0<planned['seconds']<=4200 or not 0<planned['cpu_seconds']<=3000
            or not 0<planned['qp_seconds']<=30 or not 0<planned['infeasibility_lp_seconds']<=15
            or not 0<planned['checker_seconds']<=60
            or planned['closure_seconds']<10 or planned['closure_cpu_seconds']<5):
            raise ValueError('Unfrozen/out-of-scope search limits')
        if control.get('audit_reserve_cpu_s')!=600 or control.get('audit_reserve_wall_s')!=900:
            raise ValueError('Final audit reserves must be funded prospectively')
        manifest['LAUNCH.json']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        for path in LOCAL+SEMANTIC:
            data=(ROOT/path).read_bytes();revision=args.source_revision if path in LOCAL else SEMANTIC_REVISION
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=2)
            if data!=committed:raise ValueError('Pinned source mismatch: '+path)
            cache[path]=data;manifest[path]=dict(revision=revision,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if importlib.metadata.version('gurobipy')!='12.0.1':raise ValueError('Unexpected backend version')
        specs=control.get('inputs',[])
        if len(specs)!=3 or {s.get('id') for s in specs}!=set(INPUTS):raise ValueError('Wrong input set')
        admitted={}
        for spec in specs:
            if (not re.fullmatch('[0-9a-f]{40}',spec.get('revision','')) or not isinstance(spec.get('path'),str)
                or Path(spec['path']).is_absolute() or '..' in Path(spec['path']).parts):raise ValueError('PENDING input cannot be read')
            if (spec['revision'],spec['path'])!=INPUTS[spec['id']]:raise ValueError('Input differs from fixed source-bound target/case')
            data=(ROOT/spec['path']).read_bytes()
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',spec['revision']+':'+spec['path']],cwd=ROOT,timeout=2)
            if data!=committed:raise ValueError('Input differs from frozen revision')
            admitted[spec['id']]=json.loads(data);manifest['input:'+spec['id']]=dict(spec,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        write(out/'admission.json',dict(source_revision=args.source_revision,semantic_revision=SEMANTIC_REVISION,files=manifest,
            backend='gurobipy12.0.1',no_old_root_input=True,no_fresh_physical_replay=True))
        pkg=load_module('egglab','src/egglab/__init__.py',cache,True)
        nr=load_module('egglab.native_recharge','src/egglab/native_recharge.py',cache);pkg.native_recharge=nr
        exact=load_module('exact_dual',MODEL+'exact_dual.py',cache)
        flow=load_module('energy_flow',MODEL+'energy_flow.py',cache)
        checker=load_module('tree_checker',REL+'checker.py',cache)
        producer=load_module('tree_producer',REL+'producer.py',cache)
        qualification=load_module('tree_qualification',REL+'qualification.py',cache)
        q0=stage('Q0',lambda:qualification.run(checker,exact),lambda r:dict(status=r['status'],controls=len(r['checks']),backend_calls=r['backend_calls']))
        if q0['summary']['status']!='PASS':raise ValueError('Exact literal qualification failed; packet preserved')
        data=admitted['case'];case=case_from_dict(nr,data)
        if case.identity()!=CASE_TOKEN:raise ValueError('Public case identity mismatch')
        authority=admitted['target'];binding=control['target_binding']
        expected=dict(status='ADMITTED_HULL_UPPER',case_token=CASE_TOKEN,
            producer_source_revision=TARGET_SOURCE,producer_control_commit_prefix=TARGET_CONTROL,
            producer_namespace=TARGET_NAMESPACE,packet_artifact_revision=INPUTS['target_results'][0],
            case_input_revision=CASE_REVISION,case_path=CASE_PATH,
            mixture_path=TARGET_NAMESPACE+'/MIXTURE.json.gz',results_path=INPUTS['target_results'][1],
            owner_receipt_path=TARGET_NAMESPACE+'/owner_receipt.json',required_mixture_check_status='PASS',
            new_component_physical_status='ADMITTED_PRIMAL',new_component_strict_physical_replays=1)
        if any(authority.get(k)!=v for k,v in expected.items()):raise ValueError('Target source-bound metadata mismatch')
        if binding!=dict(producer_source_revision=TARGET_SOURCE,producer_control_commit_prefix=TARGET_CONTROL,
                         producer_namespace=TARGET_NAMESPACE):raise ValueError('Wrong frozen producer binding')
        for name in ('all_five_states_delivered_timely','worker_reaped','resource_pass'):
            if authority.get(name) is not True:raise ValueError('Unqualified mixture target: '+name)
        for name in ('owner_exit','worker_exit'):
            if type(authority.get(name)) is not int or authority[name]!=0:raise ValueError('Mixture producer did not close successfully')
        target=Q(authority['upper_bound'])
        if Q(control['target_upper_bound'])!=target:raise ValueError('Exact target differs from frozen control')
        previous=admitted['target_results']
        producer_rows={r['id']:r for r in previous.get('rows',[])}
        expected_ids={'Q0','FIXED_PRICE_LP','EXACT_PRIMAL','FIXED_PRICE_DUAL','MIXTURE'}
        if (previous.get('status')!='COMPLETED' or previous.get('resource_pass') is not True
            or len(previous.get('rows',[]))!=5 or set(producer_rows)!=expected_ids
            or any(r.get('status')!='DELIVERED' for r in producer_rows.values())
            or producer_rows['Q0']['summary'].get('qualification_status')!='PASS'
            or producer_rows['EXACT_PRIMAL']['summary'].get('primal_status')!='ADMITTED_PRIMAL'
            or producer_rows['FIXED_PRICE_DUAL']['summary'].get('dual_status')!='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM'
            or Q(producer_rows['MIXTURE']['summary']['hull_upper_exact'])!=target):
            raise ValueError('Completed producer PASS/identity/upper transfer mismatch')
        def admit_target(record):
            if record is not authority:raise ValueError('Unknown target object')
            return dict(status='ADMITTED_HULL_UPPER',case_token=CASE_TOKEN,upper_bound=target,
                        binding='cached source-bound passed mixture authority; no component replay')
        service=sum((Q(t['energy_kwh']) for t in data['trips']),Q(0))
        floor=dict(case_token=CASE_TOKEN,minimum_fleet=3,proof_kind='quadratic_affine_service_floor',scope='physical_ge_3',
            lower_bound=3*Q(data['vehicle_cost'])+Q(float(.2))*service/Q(data['efficiency']),
            construction='Literal affine service floor from byte-admitted original case, independently checked by tree checker',
            source_revision=CASE_REVISION,source_path=CASE_PATH)
        def admit_floor(record):return record is floor
        write(out/'scoped_inputs.json',dict(target=admit_target(authority),higher_fleet_floor=floor,
            preserved_old_certificates=True,no_old_root_or_physical_replay=True))
        u=usage();elapsed=time.monotonic()-started
        funded=dict(planned)
        funded['cpu_seconds']=min(planned['cpu_seconds']-u['cpu_s'],3540-u['cpu_s']-600)
        funded['seconds']=min(planned['seconds'],5200-elapsed-900)
        if funded['cpu_seconds']<=0 or funded['seconds']<=0:raise RuntimeError('No full search funding plus audit reserve remains')
        write(out/'funding.json',dict(planned=planned,funded=funded,pre_search=u,pre_search_wall_s=elapsed,
            reserved_audit_cpu_s=600,reserved_audit_wall_s=900,package_owner_headroom_cpu_s=60))
        def search():
            nonlocal public_packet
            public_packet=producer.produce(case,data,flow=flow,checker=checker,semantic_reconstruct=exact._reconstruct,
                case_token=CASE_TOKEN,target_authority=authority,admit_target=admit_target,
                exclusion=floor,admit_exclusion=admit_floor,limits=funded,record=event)
            return public_packet
        stage('PUBLIC_TREE',search,lambda r:dict(status=r['status'],search_complete=r.get('search_complete',False),
            nodes=len(r['tree']['nodes']),proofs=len(r['proofs']),native_calls=r['native_calls'],
            open_fringe=r.get('open_fringe'),stop_reason=r.get('stop_reason'),cpu_s=r['cpu_s'],elapsed_s=r['elapsed_s']))
        def audit():
            nonlocal audit_summary
            audit_started=time.monotonic()
            u=usage();remaining_wall=5200-(time.monotonic()-started)
            if u['cpu_s']+600>=3540 or remaining_wall<900:
                raise RuntimeError('Full independent audit reserve was consumed; no reduced-cap closure retry')
            context=checker.prepare(data,exact._reconstruct,mode='quadratic',fleet_count=2,case_token=CASE_TOKEN)
            expanded=producer.materialize_tree(public_packet)
            checker_allowance=550-(time.monotonic()-audit_started)
            if checker_allowance<=0:raise RuntimeError('Audit construction consumed complete checking allowance')
            result=checker.verify_tree(context,expanded,exclusion=floor,admit_transfer=admit_floor,target=target,
                limits=dict(nodes=500,depth=500,operations=100000000,fraction_bits=32768,seconds=checker_allowance))
            # The proof vectors already exist once in PUBLIC_TREE's proof store.
            # Keep only outcome/algebra summaries in this independent audit packet.
            compact=dict(result)
            compact['leaves']=[dict(id=l['id'],status=l['certificate']['status'],
                lower_bound=l['certificate']['lower_bound'],contradiction=l['certificate']['contradiction']) for l in result.get('leaves',[])]
            complete=result.get('status')=='COMPLETE' and result.get('complete') is True and result.get('global_lower_bound') is not None
            positive=complete and result.get('global_lower_exceeds_target') is True
            compact.update(positive_gap_certified=positive,scientific_outcome='POSITIVE_GAP_CERTIFIED' if positive else 'SUPPORT_SIGN_UNRESOLVED',
                target_admission=admit_target(authority),no_fresh_physical_replay=True,
                tree_bound_scope='physical D only; target is separately admitted complete-plan hull upper')
            compact['target_upper_outward_6dp']=display_bound(target,up=True)
            if complete and isinstance(result['global_lower_bound'],Q):
                compact['physical_lower_outward_6dp']=display_bound(result['global_lower_bound'])
                compact['gap_lower_outward_6dp']=display_bound(result['global_lower_bound']-target)
            audit_summary=compact
            del expanded;gc.collect()
            return compact
        stage('INDEPENDENT_TREE_CHECK',audit,lambda r:{k:r.get(k) for k in
            ('status','complete','global_lower_bound','supplied_target','strict_excess','positive_gap_certified','scientific_outcome','checked_nodes','reason',
             'target_upper_outward_6dp','physical_lower_outward_6dp','gap_lower_outward_6dp')})
    except BaseException as exc:
        text=type(exc).__name__+': '+str(exc);failures.append(text)
        if active is not None:
            active.update(status='FAILED',reason=text)
            try:write(out/(active['id']+'.status.json'),active)
            except OSError:pass
        event(dict(event='worker_failure',reason=text))
    present={r['id'] for r in rows}
    for name in ASSIGNED:
        if name not in present:rows.append(dict(id=name,status='UNATTEMPTED',reason='Earlier qualification/input/resource failure'))
    u=usage();elapsed=time.monotonic()-started
    resources=u['cpu_s']<3540 and elapsed<5200 and u['peak_rss_bytes']<=5*1024**3
    status='CLOSED' if not failures and resources and all(r['status']=='DELIVERED' for r in rows) else 'CLOSED_FAILED'
    report=dict(status=status,assigned=3,rows=rows,failures=failures,resource_pass=resources,resources=u,elapsed_s=elapsed,
        scientific_outcome=audit_summary.get('scientific_outcome') if audit_summary else 'NO_COMPLETE_AUDIT',
        administrative_close_is_not_optimality=True,no_fresh_physical_replay=True,no_old_root_input=True)
    write(out/'results.json',report)
    write(out/'worker_receipt.json',dict(status=status,**usage(),elapsed_s=time.monotonic()-started,
        resource_pass=resources,self_cpu_limit_s=3540,wall_allowance_s=5200,memory_allowance_bytes=5*1024**3,native_threads=1))
    return 0 if status=='CLOSED' else 1


if __name__=='__main__':raise SystemExit(main())
