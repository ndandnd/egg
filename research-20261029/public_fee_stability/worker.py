"""One prospective stdlib-only fee interval phase; no scientific reruns."""
import argparse
import copy
from fractions import Fraction as Q
import gzip
import hashlib
import json
from pathlib import Path
import resource
import re
import subprocess
import sys
import time
import types

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REL='research-20261029/public_fee_stability/'
TREE='ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9'
PRICE='f5ec2aa5770188d173af7297620a5fcea99fef9a'
AUTH='c5f056b90ca895786c44f96903cdaafff97fce52'
ASSIGNED=('ADMISSION','Q0','PUBLIC_INTERVAL')
INPUTS={}
for prefix,revision,namespace in [('tree',TREE,'public_support_tree'),('price',PRICE,'public_price_witness')]:
    for label,filename in [('results','results.json'),('owner','owner_receipt.json'),('worker','worker_receipt.json')]:
        INPUTS[prefix+'_'+label]=(revision,'research-20261029/'+namespace+'/attempt01/'+filename)
INPUTS.update(authority=(AUTH,'research-20261029/public_price_witness/TRANSFER_AUTHORITY.json'),
    mixture=(PRICE,'research-20261029/public_price_witness/attempt01/MIXTURE.json.gz'),
    incumbent=(PRICE,'research-20261029/public_price_witness/attempt01/transferred_incumbent.json'),
    response=(PRICE,'research-20261029/public_price_witness/attempt01/new_physical_response.json'),
    audit=(TREE,'research-20261029/public_support_tree/attempt01/INDEPENDENT_TREE_CHECK.json.gz'))

def need(ok,message):
    if not ok:raise ValueError(message)
def encode(value):
    if isinstance(value,Q):return str(value)
    raise TypeError(type(value).__name__)
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,default=encode,indent=2,allow_nan=False);stream.write('\n')
def usage():
    own,child=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(cpu_s=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime,
        peak_rss_bytes=max(own.ru_maxrss,child.ru_maxrss)*(1 if sys.platform=='darwin' else 1024))
def module(name,raw):
    value=types.ModuleType(name);exec(compile(raw,name,'exec'),value.__dict__);return value

def qualification(checker,producer,admitted):
    arithmetic=checker.literal_qualification();need(arithmetic['status']=='PASS','Arithmetic qualification')
    # Fixed metadata-only anchor: U310,L2=311,L3=313,N0=2,N1=3,w1/2.
    literal=copy.deepcopy(admitted)
    literal.update(f0=100,L2=Q(311),U=Q(310),tau0=0,
        mixture=dict(w=Q(1,2),N0=2,N1=3,ops0=200,ops1=300,mixed_ops=250),
        floor=dict(kind='three_plus',L3=Q(313)))
    literal['authority'].update(original_fee=100,tree_L2=Q(311),tree_target_U=Q(310),mixture_U=Q(310),L3=Q(313))
    proposed=producer.propose(literal);result=checker.check(literal,proposed)
    need(result['tau_interval']==dict(empty=False,lower=Q(-6),lower_closed=False,upper=Q(2),upper_closed=False),
         'Literal interval anchor')
    controls=[]
    mutations=[('changed_fee',lambda f:f.__setitem__('f0',101)),
        ('changed_upper',lambda f:f.__setitem__('U',9)),
        ('changed_case',lambda f:f['authority'].__setitem__('tree_case_token','wrong')),
        ('noninteger_count',lambda f:f['mixture'].__setitem__('N0',Q(5,2))),
        ('changed_weight',lambda f:f['mixture'].__setitem__('w',Q(1,3))),
        ('changed_ops',lambda f:f['mixture'].__setitem__('ops1',301)),
        ('wrong_floor',lambda f:f['authority'].__setitem__('three_plus_algebraic_floor',False)),
        ('changed_floor',lambda f:f['floor'].__setitem__('L3',14)),
        ('open_tree',lambda f:f['authority'].__setitem__('tree_complete',False)),
        ('unadmitted_component',lambda f:f['authority'].__setitem__('components_admitted',False))]
    for name,mutate in mutations:
        changed=copy.deepcopy(literal);mutate(changed)
        try:checker.check(changed)
        except (ValueError,KeyError,TypeError):controls.append(dict(id=name,rejected=True))
        else:raise ValueError('Corruption accepted: '+name)
    wrong=dict(proposed,lower_closed=True)
    try:checker.check(literal,wrong)
    except ValueError:controls.append(dict(id='closed_strict_endpoint',rejected=True))
    else:raise ValueError('Closed strict endpoint accepted')
    return dict(status='PASS',arithmetic=arithmetic,anchor=result,negative_controls=controls,native_calls=0)

def main():
    started=time.monotonic();resource.setrlimit(resource.RLIMIT_CPU,(85,85))
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--source-revision',required=True);args=parser.parse_args()
    out=Path(args.out);rows=[];failure=None;cache={};manifest={};answer=None
    def stage(name,action):
        need(usage()['cpu_s']<70 and time.monotonic()-started<120,'Insufficient complete-stage closure allowance')
        row=dict(id=name,status='ATTEMPTED');rows.append(row);anchor=time.monotonic()
        try:
            value=action();write(out/(name+'.json'),value)
            row.update(status='DELIVERED',complete_elapsed_s=time.monotonic()-anchor)
            write(out/(name+'.status.json'),row);return value
        except BaseException as exc:row.update(status='FAILED',reason=type(exc).__name__+': '+str(exc));raise
    try:
        need(not sys.flags.optimize,'Assertions required')
        control_raw=(HERE/'LAUNCH.json').read_bytes();control=json.loads(control_raw)
        need(control.get('status')=='FROZEN' and control.get('source_revision')==args.source_revision
             and re.fullmatch('[0-9a-f]{40}',args.source_revision) is not None,'No frozen worker source authority')
        need(control.get('run_id')=='attempt01' and out.resolve()==(HERE/'attempt01').resolve()
             and tuple(control.get('assigned',()))==ASSIGNED,'Worker run/denominator mismatch')
        need([control.get(k) for k in ('package_cpu_s','package_wall_s','worker_cpu_s','worker_wall_s')]
             ==[120,180,90,150] and control.get('native_calls')==0
             and control.get('observed_rss_bytes')==512*1024**2,'Worker resource declaration mismatch')
        need(control.get('tree_artifact_revision')==TREE and control.get('mixture_artifact_revision')==PRICE
             and control.get('mixture_authority_revision')==AUTH
             and control.get('inputs')=={k:dict(revision=r,path=p) for k,(r,p) in INPUTS.items()},
             'Worker frozen input declarations mismatch')
        def admission():
            manifest['LAUNCH.json']=dict(path=REL+'LAUNCH.json',bytes=len(control_raw),
                sha256=hashlib.sha256(control_raw).hexdigest(),binding='separate frozen control; semantic gates checked before admission')
            specs={k:(args.source_revision,REL+k) for k in ('worker.py','producer.py','checker.py','run.py','PROTOCOL.md')}
            specs.update(INPUTS)
            for key,(revision,path) in specs.items():
                raw=(ROOT/path).read_bytes()
                fixed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',revision+':'+path],cwd=ROOT,timeout=2)
                need(raw==fixed,'Pinned buffer mismatch: '+path)
                cache[key]=raw;manifest[key]=dict(revision=revision,path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            data={key:json.loads(gzip.decompress(cache[key]) if INPUTS[key][1].endswith('.gz') else cache[key]) for key in INPUTS}
            p=module('fee_producer',cache['producer.py']);fields=p.project(data)
            # No loads, routes, physical candidate or proof vectors survive this projection.
            del data
            return dict(status='ADMITTED_METADATA',fields=fields,files=manifest,native_calls=0)
        admitted=stage('ADMISSION',admission)
        producer=module('fee_producer',cache['producer.py']);checker=module('fee_checker',cache['checker.py'])
        fields=admitted['fields'];cache.clear()
        stage('Q0',lambda:qualification(checker,producer,fields))
        def public():
            proposal=producer.propose(fields);result=checker.check(fields,proposal)
            need(checker.contains(result['tau_interval'],Q(0)),'Nominal absent')
            return dict(result=result,fields=fields,proposal=proposal,native_calls=0,
                no_physical_replay=True,no_mixture_reoptimization=True,no_tree_audit=True)
        answer=stage('PUBLIC_INTERVAL',public)
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    for name in ASSIGNED[len(rows):]:rows.append(dict(id=name,status='UNATTEMPTED',reason=failure or 'Missing dependency'))
    observed=usage();elapsed=time.monotonic()-started
    passed=observed['cpu_s']<90 and elapsed<150 and observed['peak_rss_bytes']<=512*1024**2
    status='COMPLETED' if not failure and passed and all(r['status']=='DELIVERED' for r in rows) else 'FAILED'
    report=dict(status=status,assigned=list(ASSIGNED),rows=rows,failure=failure,resource_pass=passed,
        resources=observed,elapsed_s=elapsed,scientific_status=answer['result']['status'] if status=='COMPLETED' else 'NOT_CERTIFIED',
        native_calls=0,summary=answer['result'] if status=='COMPLETED' else None)
    write(out/'results.json',report);write(out/'worker_receipt.json',dict(report,resources=usage(),elapsed_s=time.monotonic()-started))
    return 0 if status=='COMPLETED' else 1

if __name__=='__main__':raise SystemExit(main())
