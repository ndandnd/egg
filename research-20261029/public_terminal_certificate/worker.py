"""One metered exact construction and independent replay, without a solver."""
import argparse
import copy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='research-20261029/public_terminal_certificate/'
VERIFY='research-20261029/public_support_resolution/independent_verify.py'
SOURCES=[REL+n for n in ('construct.py','worker.py','run.py','PROTOCOL.md')]+[VERIFY]
INPUT_ROOT='research-20261029/public_support_resolution/attempt01/'
INPUT_REV='253c1e29295e766b3889fc8f5c28d9808e00b3d6'

def write(path,value):
    def encode(item):
        if isinstance(item,Q): return str(item)
        raise TypeError(type(item).__name__)
    with path.open('x') as f:
        json.dump(value,f,indent=2,default=encode,allow_nan=False)
        f.write('\n')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True)
    p.add_argument('--source-revision',required=True)
    args=p.parse_args()
    out=Path(args.out)
    started=time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    failures,rows,manifest,cache=[],[],{},{}
    active=None
    try:
        for relative in SOURCES+[INPUT_ROOT+'case_descriptor.json',INPUT_ROOT+'MIQP.json']:
            raw=(ROOT/relative).read_bytes()
            rev=args.source_revision if relative in SOURCES else INPUT_REV
            committed=subprocess.check_output(['git','--no-pager','-c','pack.threads=1','show',rev+':'+relative],cwd=ROOT,timeout=10)
            if raw!=committed: raise ValueError('Frozen byte mismatch '+relative)
            cache[relative]=raw
            manifest[relative]=dict(revision=rev,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        write(out/'admission.json',manifest)
        modules=[]
        for relative in (REL+'construct.py',VERIFY):
            ns={'__name__':relative,'__file__':str(ROOT/relative)}
            exec(compile(cache[relative],ns['__file__'],'exec'),ns)
            modules.append(ns)
        construct,verify=modules[0]['construct'],modules[1]['verify']
        literal=dict(name='terminal-certificate-literal',depot='D',max_vehicles=1,battery_kwh=20,
            reserve_kwh=0,efficiency=1,terminal_open_min=0,recharge_deadline_min=120,vehicle_cost=7,
            deadhead_cost_per_min=0,graph_scope='declared-movement-modes-only',market_edges_min=[0,60,120],
            resources=[dict(start_min=0,end_min=120,per_bus_kw=20,grid_kw=20,connectors=1)],
            trips=[dict(id='s',start_min=30,end_min=60,start_place='D',end_place='D',energy_kwh=10)],
            movements=[dict(id='out',kind='pullout',before=None,after='s',depot_split=None,
                legs=[dict(origin='D',destination='D',depart_min=30,arrive_min=30,energy_kwh=0)]),
                dict(id='in',kind='pullin',before='s',after=None,depot_split=None,
                legs=[dict(origin='D',destination='D',depart_min=60,arrive_min=60,energy_kwh=0)])])
        active=dict(id='literal',status='ATTEMPTED');rows.append(active)
        controls=[]
        for delta in (-Q(1,1024),Q(1,1024)):
            raw=dict(selected_movement_ids=['out','in'],charge_by_interval=[dict(movement='in',interval=1,energy=Q(10)+delta)])
            new,change=construct(literal,raw)
            audit=verify(literal,new)
            if not audit['strict_pass'] or audit['total_grid_exact']!=10: raise ValueError('Literal construction not exact')
            controls.append(dict(delta=delta,changes=change,audit=audit))
        bad=copy.deepcopy(new);bad['charge_by_interval'][0]['energy']-=1
        if verify(literal,bad)['physical_strict_pass']: raise ValueError('Missing terminal energy was accepted')
        empty=copy.deepcopy(literal);empty['resources'][0]['grid_kw']=0
        try: construct(empty,dict(selected_movement_ids=['out','in'],charge_by_interval=[]))
        except ValueError: controls.append(dict(zero_power_deficit_rejected=True))
        else: raise ValueError('Impossible literal terminal deficit accepted')
        active.update(status='PASS',controls=controls);active=None
        active=dict(id='public',status='ATTEMPTED');rows.append(active)
        case=json.loads(cache[INPUT_ROOT+'case_descriptor.json'])
        original=json.loads(cache[INPUT_ROOT+'MIQP.json'])['result']['candidate']
        new,changes=construct(case,original)
        write(out/'new_candidate.json',new)
        write(out/'changes.json',changes)
        audit=verify(case,new)
        write(out/'independent_replay.json',audit)
        if not audit['strict_pass']: raise ValueError('New public candidate failed strict independent replay')
        service=sum((Q(t['energy_kwh']) for t in case['trips']),Q(0))
        if case['vehicle_cost']<0 or case['deadhead_cost_per_min']<0 or any(Q(l['energy_kwh'])<0 for m in case['movements'] for l in m['legs']):
            raise ValueError('Three-bus elementary bound prerequisites failed')
        lower3=3*Q(case['vehicle_cost'])+Q(float(.2))*service/Q(case['efficiency'])
        active.update(status='PASS',upper_exact=audit['objective_exact'],upper_display=float(audit['objective_exact']),
            fleet_count=len(audit['routes']),changed_cells=len(changes['changed_cells']),
            atleast_three_bus_lower_exact=lower3,atleast_three_bus_lower_display=float(lower3),
            three_plus_cannot_improve_upper=lower3>audit['objective_exact'],
            scope='Exact physical upper and elementary physical fleet-count exclusion; support unresolved')
        active=None
    except BaseException as exc:
        failures.append(type(exc).__name__+': '+str(exc))
        if active is not None: active.update(status='FAILED',failure=failures[-1])
    for name in ('literal','public'):
        if not any(r['id']==name for r in rows): rows.append(dict(id=name,status='UNATTEMPTED'))
    own,children=resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime
    rss=max(own.ru_maxrss,children.ru_maxrss)*(1 if sys.platform=='darwin' else 1024)
    report=dict(status='PASS' if not failures else 'FAILED',rows=rows,failures=failures,cpu_s=cpu,
        elapsed_s=time.monotonic()-started,peak_rss_bytes=rss,resource_pass=cpu<45 and time.monotonic()-started<60 and rss<=5*1024**3)
    write(out/'results.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
    return 0 if report['status']=='PASS' and report['resource_pass'] else 1

if __name__=='__main__': raise SystemExit(main())
