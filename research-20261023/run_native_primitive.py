#!/usr/bin/env python3
"""Prospective local native recovery qualification. No solve on import or freeze."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from experiments import codex_local_campaign as util
TASKS = ['source_normal', 'full_normal', 'changed_tariff', 'start_setup_failure',
         'expired_search_deadline', 'invalid_fallback']


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, default=str, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(value, sort_keys=True, default=str, allow_nan=False)+'\n')
        stream.flush()
        os.fsync(stream.fileno())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sanitize(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k:sanitize(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [sanitize(v) for v in value]
    return value


def sources():
    return sorted(set([Path(__file__).resolve()] + list((ROOT/'src/egglab').glob('*.py')) +
                      list((ROOT/'src/experiments').glob('*.py')) +
                      [ROOT/'research-20261017/recovery-prototype/test_recovery_lift.py',
                       ROOT/'research-20261023/RECOVERY_NATIVE_PRIMITIVE_PROTOCOL.md']))


def verify(lock):
    for path, digest in {**lock['sources'],**lock.get('prior_evidence',{})}.items():
        if sha(path) != digest:
            raise ValueError('Frozen source changed: '+path)


def fixture():
    from dataclasses import replace
    from egglab import native_recharge as nr
    trip=nr.Trip('A',0,60,'D','D',15.)
    out=nr.Movement('out','pullout',None,'A',(nr.Leg('D','D',0,0,0.),))
    home=nr.Movement('home','pullin','A',None,(nr.Leg('D','D',60,60,0.),))
    source=nr.NativeCase('source',(trip,),(out,home),
        (nr.Resource(0,60,0.,0.,0),nr.Resource(60,120,30.,30.)),
        (0,60,120),'D',1,20.,1.,0,120,7.)
    extra=nr.Movement('extra','pullin','A',None,(nr.Leg('D','D',60,75,0.),))
    full=replace(source,name='full',movements=(extra,home,out))
    plan={'schema':nr.SCHEMA,'case_identity':source.identity(),
          'vehicles':[{'vehicle':0,'trips':['A'],'movements':['out','home']}],
          'charges':[{'vehicle':0,'movement':'home','connector':0,
                      'start_min':60.,'end_min':90.,'grid_kwh':15.}],
          'load':[0.,15.],'ops_cost':7.}
    return source,full,plan


def worker(args):
    folder=Path(args.output)
    attempt=json.loads((folder/'attempt.json').read_text())
    anchor=attempt['parent_monotonic']; deadline=anchor+30
    subprocess.Popen([sys.executable,str(ROOT/'src/experiments/codex_local_campaign.py'),
        'watch-parent','--parent-pid',str(os.getppid()),'--worker-pid',str(os.getpid()),
        '--output',str(folder)], preexec_fn=lambda:signal.signal(signal.SIGTERM,signal.SIG_IGN))
    cpu0=time.process_time()
    row={'task':args.worker,'handcrafted_fallback':True,'accepted_valid':False}
    try:
        lock=json.loads(Path(args.lock).read_text()); verify(lock)
        from fractions import Fraction
        from egglab import native_recharge as nr, native_pathflow as pf, native_hull as nh
        from egglab.recovery_lift import lift_plan
        source,full,plan=fixture()
        target=source if args.worker=='source_normal' else full
        a,b=([0.,4.],[0.,0.]) if args.worker=='changed_tariff' else ([1.,2.],[0.,.2])
        if args.worker=='invalid_fallback':
            plan['charges'][0]['grid_kwh']=10.
        expected=67. if args.worker=='changed_tariff' else 59.5
        record=lambda event:append(folder/'native.jsonl',sanitize(event))
        row.update(source_identity=source.identity(),full_identity=full.identity(),
                   source_intervals=len(nr.compile_case(source)['intervals']),
                   full_intervals=len(nr.compile_case(full)['intervals']))
        assert row['full_intervals']>row['source_intervals']
        if args.worker!='invalid_fallback':
            lifted=lift_plan(source,target,plan,a=a,b=b)
            write(folder/'fallback.json',sanitize(lifted))
            assert lifted['true_bill']==expected
            assert lifted['binary_start_spec']==[
                {'movement_id':m.id,'value':int(m.id in ('out','home'))} for m in target.movements]
        build=pf.build_feasible_model
        def instrumented_build(*pos,**kw):
            built=build(*pos,**kw)
            built['model'].threads=1; built['model'].seed=17; built['model'].verbose=1
            record({'event':'primitive_model_built'})
            return built
        pf.build_feasible_model=instrumented_build
        attach=pf._attach_pricing_start
        def instrumented_attach(case,built,selected):
            before=[(v.idx,v.lb,v.ub) for v in built['model'].vars]
            constraint_count=built['model'].num_rows
            if args.worker=='start_setup_failure':
                raise RuntimeError('prospective injected start setup failure')
            result=attach(case,built,selected)
            assignments=list(built['model'].start)
            assert len(assignments)==len(case.movements)
            assert all(v.var_type=='B' for v,value in assignments)
            assert {v.idx:value for v,value in assignments}=={
                v.idx:int(m.id in selected) for v,m in zip(built['x'],case.movements)}
            assert before==[(v.idx,v.lb,v.ub) for v in built['model'].vars]
            assert built['model'].num_rows==constraint_count
            record({'event':'primitive_binary_inventory_verified','mapping':[
                {'movement_id':m.id,'value':int(m.id in selected)} for m in case.movements],
                'continuous_start_count':0,'bounds_unchanged':True})
            return result
        pf._attach_pricing_start=instrumented_attach
        expired=args.worker in ('expired_search_deadline','invalid_fallback')
        search_deadline=min(deadline-3,time.monotonic()-1 if expired else deadline-6)
        budget=nr.Budget(backend='GRB',threads=1,phase_seconds=3.,wall_seconds=30.,max_rounds=2,epsilon=1e-4)
        result=pf.solve_planner(target,a,b,budget,record=record,completion=True,
                               start_plan=plan,start_case=source,deadline=search_deadline)
        write(folder/'planner.json',sanitize(result))
        events=[json.loads(x) for x in (folder/'native.jsonl').read_text().splitlines()]
        recovery=result.get('recovery',{})
        if expired:
            assert not any(e['event'] in ('primitive_model_built','native_start') for e in events)
            assert result.get('lower',-math.inf)==-math.inf
        if args.worker=='invalid_fallback':
            assert recovery['status']=='rejected' and not result.get('plan')
            row['expected_rejection']=True
        else:
            replay=nr.replay_native(target,result['plan'])
            bill=Fraction(replay['ops_cost'])+nh.supply(nh.Market('primitive',tuple(a),tuple(b)),replay['load'])
            assert replay['replay_ok'] and float(bill)<=expected+1e-7
            if args.worker=='start_setup_failure':
                assert recovery['start_status']=='rejected'
                assert float(bill)==expected and result.get('lower',-math.inf)==-math.inf
            if args.worker=='expired_search_deadline': assert float(bill)==expected
            write(folder/'plan.json',result['plan']); write(folder/'replay.json',sanitize(replay))
            row.update(accepted_valid=True,bill_exact=str(bill),bill=float(bill))
        row.update(test_pass=True,recovery=sanitize(recovery),lower=sanitize(result.get('lower')),
                   lower_scope='full_unrestricted' if target is full else 'source_restricted_only')
    except BaseException:
        row.update(test_pass=False,error=traceback.format_exc())
    row.update(cpu_s=time.process_time()-cpu0,wall_s=time.monotonic()-anchor,
               peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(folder/'result.json',sanitize(row))
    finished=time.monotonic()
    write(folder/'completion.json',{'task':args.worker,'lock_sha256':sha(args.lock),
        'parent_monotonic':anchor,'finished_monotonic':finished,'result_sha256':sha(folder/'result.json')})


def run(args):
    output=Path(args.output); output.mkdir(parents=True,exist_ok=True)
    lock=json.loads(Path(args.lock).read_text()); verify(lock)
    binding={'lock_sha256':sha(args.lock),'tasks':TASKS}
    if (output/'campaign.json').exists():
        assert json.loads((output/'campaign.json').read_text())==binding
    else: write(output/'campaign.json',binding)
    for folder in (p for p in output.iterdir() if p.is_dir()):
        if folder.name not in TASKS:
            raise ValueError('Unknown attempt directory: '+str(folder))
    spent=lock['freeze_cpu_s']+lock.get('prior_qualification_cpu_s',0)
    for event in (output/'ledger.jsonl').read_text().splitlines() if (output/'ledger.jsonl').exists() else []:
        spent+=json.loads(event).get('overhead_cpu_s',0)
    for task in TASKS:
        folder=output/task
        if folder.exists():
            receipt=json.loads((folder/'supervisor.json').read_text())
            assert receipt['lock_sha256']==binding['lock_sha256']
            spent+=receipt['charged_cpu_s']
    supervisor0=time.process_time(); child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        for task in TASKS:
            folder=output/task
            if folder.exists(): continue
            if spent+time.process_time()-supervisor0+32.5>720: break
            folder.mkdir(); anchor=time.monotonic()
            write(folder/'attempt.json',{'task':task,**binding,'parent_monotonic':anchor})
            env={**os.environ,**{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')}}
            failure=None; peak=0; sampled_cpu=0; pressure_since=None; last_memory=0
            with (folder/'stdout.log').open('xb') as stdout,(folder/'stderr.log').open('xb') as stderr:
                proc=subprocess.Popen([sys.executable,__file__,'--worker',task,'--lock',args.lock,
                    '--output',str(folder)],stdout=stdout,stderr=stderr,env=env,start_new_session=True)
                def interrupted(signum,frame): raise KeyboardInterrupt('supervisor signal '+str(signum))
                old={sig:signal.signal(sig,interrupted) for sig in (signal.SIGINT,signal.SIGTERM)}
                try:
                    while proc.poll() is None:
                        rss,cpu=util.tree_stats(proc.pid,util.snapshot()); peak=max(peak,rss);sampled_cpu=max(sampled_cpu,cpu)
                        append(folder/'resources.jsonl',{'monotonic':time.monotonic(),'rss':rss,'cpu_s':cpu})
                        if rss>5*1024**3: failure='rss_limit'
                        now=time.monotonic()
                        if now-last_memory>=1:
                            memory=util.memory_state(); last_memory=now
                            append(folder/'resources.jsonl',{'monotonic':now,**memory})
                            pressure_since=(pressure_since or now) if memory['free_percent']<10 else None
                            if pressure_since is not None and now-pressure_since>=5:failure='memory_pressure'
                        if now-anchor>32:failure='wall_deadline'
                        if failure:break
                        time.sleep(.25)
                except BaseException:
                    failure=traceback.format_exc()
                finally:
                    util.stop(proc)
                    for sig,handler in old.items():signal.signal(sig,handler)
            elapsed=time.monotonic()-anchor
            valid=False
            try:
                marker=json.loads((folder/'completion.json').read_text())
                assert marker['task']==task and marker['lock_sha256']==binding['lock_sha256']
                assert marker['parent_monotonic']==anchor and marker['result_sha256']==sha(folder/'result.json')
                endpoint=marker['finished_monotonic']-anchor
                valid=0<=endpoint<=30
            except (OSError,ValueError,KeyError,AssertionError):endpoint=None
            # Elapsed allocation conservatively covers children/watchdog and missed samples.
            charged=max(elapsed,sampled_cpu)
            receipt={'task':task,'lock_sha256':binding['lock_sha256'],'charged_cpu_s':charged,
                     'endpoint_valid':valid,'endpoint_wall_s':endpoint,'supervisor_elapsed_s':elapsed,
                     'peak_rss_bytes':peak,'failure':failure,'returncode':proc.returncode}
            write(folder/'supervisor.json',receipt);spent+=charged
            append(output/'ledger.jsonl',{'event':'attempt_finished',**receipt})
            if failure or not valid:break
            result=json.loads((folder/'result.json').read_text())
            if not result.get('test_pass'):break
    finally:
        children=resource.getrusage(resource.RUSAGE_CHILDREN)
        # Worker wall allocations already charged; add only supervisor CPU here.
        append(output/'ledger.jsonl',{'event':'supervisor_closeout',
            'overhead_cpu_s':time.process_time()-supervisor0,
            'observed_child_cpu_s':children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime})


def analyze(args):
    cpu0=time.process_time(); output=Path(args.output)
    lock=json.loads(Path(args.lock).read_text()); verify(lock)
    rows=[];spent=lock['freeze_cpu_s']+lock.get('prior_qualification_cpu_s',0)
    for task in TASKS:
        folder=output/task
        if not folder.exists():rows.append({'task':task,'missing':True});continue
        sup=json.loads((folder/'supervisor.json').read_text());spent+=sup['charged_cpu_s']
        result=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {}
        log=(folder/'stdout.log').read_text(errors='replace')
        accepted=any(s in log for s in ('Loaded user MIP start','User MIP start produced solution'))
        rejected='User MIP start did not produce a new incumbent solution' in log
        native='accepted' if accepted else ('rejected_or_nonimproving' if rejected else 'unknown')
        rows.append({'task':task,'test_pass':result.get('test_pass',False),
            'endpoint_valid':sup['endpoint_valid'],'failure':sup['failure'],'returncode':sup['returncode'],
            'native_start_status':native,'native_log_sha256':sha(folder/'stdout.log')})
    for line in (output/'ledger.jsonl').read_text().splitlines():spent+=json.loads(line).get('overhead_cpu_s',0)
    passed=all(r.get('test_pass') and r.get('endpoint_valid') and not r.get('failure') and r.get('returncode')==0 for r in rows)
    processed=any(r.get('native_start_status') in ('accepted','rejected_or_nonimproving') for r in rows if r['task'] in TASKS[:3])
    result={'engineering_pass':passed and processed and spent<=900,'tasks':rows,
            'native_start_processing_observed':processed,'charged_cpu_s_before_analysis':spent,
            'scope':'handcrafted primitive only; no route prediction efficacy; phase1 not qualified'}
    analysis_cpu=max(1.,time.process_time()-cpu0)
    result['charged_cpu_s_including_analysis']=spent+analysis_cpu
    result['engineering_pass']=result['engineering_pass'] and spent+analysis_cpu<=900
    write(output/('analysis-'+str(time.time_ns())+'.json'),result)
    append(output/'ledger.jsonl',{'event':'analysis','overhead_cpu_s':analysis_cpu})
    print(json.dumps(result,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--freeze',action='store_true');action.add_argument('--run',action='store_true')
    action.add_argument('--analyze',action='store_true');action.add_argument('--worker',choices=TASKS)
    parser.add_argument('--lock',required=True);parser.add_argument('--output')
    parser.add_argument('--prior-output');parser.add_argument('--prior-lock')
    args=parser.parse_args()
    if args.freeze:
        cpu0=time.process_time()
        value={'version':1,'tasks':TASKS,'seconds':30,'cpu_ceiling_s':900,'worker_count':1,
               'threads':1,'rss_bytes':5*1024**3,'sources':{str(p):sha(p) for p in sources()},
               'prior_qualification_cpu_s':60.,'preflight_allowance_cpu_s':60.,'freeze_cpu_s':0}
        if bool(args.prior_output)!=bool(args.prior_lock):
            raise ValueError('Prior output and prior lock must be supplied together')
        if args.prior_output:
            prior=Path(args.prior_output); old=json.loads(Path(args.prior_lock).read_text())
            evidence=[Path(args.prior_lock),prior/'campaign.json',prior/'ledger.jsonl']
            binding=json.loads((prior/'campaign.json').read_text())
            assert binding['lock_sha256']==sha(args.prior_lock)
            charge=old['freeze_cpu_s']+old.get('prior_qualification_cpu_s',0)
            for folder in (p for p in prior.iterdir() if p.is_dir()):
                attempt=folder/'attempt.json'; receipt=folder/'supervisor.json'
                row=json.loads(receipt.read_text())
                assert row['lock_sha256']==sha(args.prior_lock)
                charge+=row['charged_cpu_s'];evidence.extend([attempt,receipt])
            for line in (prior/'ledger.jsonl').read_text().splitlines():
                charge+=json.loads(line).get('overhead_cpu_s',0)
            value['prior_qualification_cpu_s']=charge
            value['preflight_allowance_cpu_s']=old.get('preflight_allowance_cpu_s',60.)
            value['prior_evidence']={str(p.resolve()):sha(p) for p in evidence}
        value['freeze_cpu_s']=max(1.,time.process_time()-cpu0)  # conservative startup/write allowance
        write(args.lock,value)
    elif args.worker:worker(args)
    elif args.run:run(args)
    else:analyze(args)


if __name__=='__main__': main()
