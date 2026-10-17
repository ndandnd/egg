"""Bounded local campaign. freeze constructs cases only; run executes locked tasks.

Run from src with PYTHONPATH=. python -m experiments.codex_local_campaign --help.
Heavy numerical imports occur only inside freeze/worker, never supervisor/self-test.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import tempfile
import time
import traceback

class SupervisorStop(RuntimeError):
    pass

def signal_stop(signum, frame):
    raise SupervisorStop(f'supervisor_signal_{signum}')

SALT = 'egg-ranking-local-20261017-v1'
ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def clean(value):
    if isinstance(value,float) and not math.isfinite(value):return str(value)
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    return value

def write_new(path, value):
    path = Path(path)
    with path.open('x') as f:
        json.dump(clean(value), f, indent=2, default=str, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())

def append(path, value):
    with Path(path).open('a') as f:
        f.write(json.dumps(clean(value), default=str, allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())

def stable(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()

def sources():
    # Freeze all experiment and egglab Python source to catch transitive helper edits.
    return {str(p):digest(p) for folder in ('src/experiments','src/egglab')
            for p in sorted((ROOT/folder).rglob('*.py'))}

def verify(lock):
    for path, sha in {**lock['sources'], **lock['assets']}.items():
        if digest(path) != sha: raise ValueError(f'Frozen file changed: {path}')

def freeze(args):
    cpu0=time.process_time()
    from egglab import claude_cases
    manifest=json.loads(Path(args.manifest).read_text())
    modelroot=Path(args.v8_root).resolve()
    folder=modelroot/'task00'/'inner_progress'
    files=[folder/'graph_attention_selected.npz',folder/'fit_only_preprocessing_and_groups.json']
    assets={str(p):digest(p) for p in files}
    arms=[a['id'] for a in manifest['arms'] if a['id']!='catboost_v5']
    classical=None
    if args.classical_root:
        classical=str(Path(args.classical_root).resolve())
        candidates=sorted((Path(classical)/'catboost').rglob('*'))
        files=[p for p in candidates if p.is_file()]
        if not files: raise ValueError('CatBoost directory has no frozen artifacts')
        assets.update({str(p):digest(p) for p in files})
        arms.insert(1,'catboost_v5')
    cases={}
    for cell in sum(manifest['cohorts'].values(),[]):
        case=claude_cases.make(cell['case_key'])
        cases[cell['case_key']]={'identity':case.identity(),'movement_ids':[m.id for m in case.movements]}
    lock={'version':2,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
          'manifest':manifest,'manifest_sha256':digest(args.manifest),'sources':sources(),
          'assets':assets,'cases':cases,'arms':arms,'v8_root':str(modelroot),
          'classical_root':classical,'heuristic':'experiments.codex_offline_rank.heuristic',
          'catboost_definition':'newly trained classical comparator; fixed before campaign outcomes',
          'completion':True,'timing':'cold start, imports through final receipt preparation',
          'host':platform.uname()._asdict(),'freeze_cpu_s':time.process_time()-cpu0,
          'python_executable':sys.executable,'python_version':sys.version}
    write_new(args.lock,lock)
    print(json.dumps({'lock':args.lock,'arms':arms,'cases':len(cases)}))

def prune(case,scores,keep=.30,floor=3):
    if len(scores)!=len(case.movements) or not all(math.isfinite(float(x)) for x in scores):
        raise ValueError('Invalid score vector')
    order=sorted((i for i,m in enumerate(case.movements) if m.kind in ('direct','depot')),
                 key=lambda i:(-float(scores[i]),case.movements[i].id))
    selected=set(order[:math.ceil(keep*len(order))])
    for field in ('before','after'):
        counts={}
        for i in order:
            trip=getattr(case.movements[i],field)
            if counts.get(trip,0)<floor: selected.add(i)
            counts[trip]=counts.get(trip,0)+1
    selected.update(i for i,m in enumerate(case.movements) if m.kind in ('pullout','pullin'))
    target=replace(case,name=case.name+'-campaign',movements=tuple(m for i,m in enumerate(case.movements) if i in selected))
    return target

def v8_scores(case,prices,root):
    import numpy as np
    import torch
    from egglab import learned_proposals as edge
    from egglab import physical_route_graph_v6 as graph
    graph.configure_cpu()
    folder=Path(root)/'task00'/'inner_progress'
    pre=json.loads((folder/'fit_only_preprocessing_and_groups.json').read_text())
    model=graph.restore_model(folder/'graph_attention_selected.npz')
    sample={'x':edge.edge_features(case,prices),'graph':graph.topology(case),
            'group':case.name,'source':'scoring','trip_count':len(case.trips)}
    with torch.no_grad():
        return model(graph.batches([sample],np.asarray(pre['mean_fit_only']),
                       np.asarray(pre['scale_fit_only']),labelled=False)[0]).numpy().tolist()

def worker(args):
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGINT})
    started=time.monotonic(); usage0=resource.getrusage(resource.RUSAGE_SELF)
    folder=Path(args.output)
    if args.parent_pid:
        subprocess.Popen([sys.executable,'-m','experiments.codex_local_campaign','watch-parent',
                          '--parent-pid',str(args.parent_pid),'--worker-pid',str(os.getpid()),
                          '--output',str(folder.resolve())],preexec_fn=lambda:signal.signal(signal.SIGTERM,signal.SIG_IGN))
    lock=json.loads(Path(args.lock).read_text())
    task=json.loads((folder/'attempt.json').read_text())['task']
    row={'task':task,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         'lock_sha256':digest(args.lock),'events_file':'native.jsonl','host':platform.uname()._asdict()}
    try:
        verify(lock)
        if args.mock:
            append(folder/'native.jsonl',{'event':'mock_attempt','worker_pid':os.getpid()})
            if args.mock_delay:time.sleep(args.mock_delay)
            if task['arm']=='random': raise RuntimeError('intentional mock failure')
            row.update(status='mock_success',accepted_valid=False)
        else:
            from egglab import claude_cases, native_recharge as nr, native_pathflow as pf, native_hull as nh
            from egglab import physical_learning_cases as bank
            case=claude_cases.make(task['case_key']); frozen=lock['cases'][task['case_key']]
            if case.identity()!=frozen['identity'] or [m.id for m in case.movements]!=frozen['movement_ids']:
                raise ValueError('Case identity/movement-order mismatch')
            row['case_identity']=case.identity(); row['movement_ids_sha256']=stable(frozen['movement_ids'])
            market=bank.market(case,lock['manifest']['tariff']); arm=task['arm']; target=case
            prep=time.monotonic(); scores=None
            if arm=='v8': scores=v8_scores(case,market.a,lock['v8_root'])
            elif arm=='nonlearned':
                from experiments.codex_offline_rank import heuristic
                scores=heuristic(case)
            elif arm=='random':
                order=sorted(range(len(case.movements)),key=lambda i:hashlib.sha256(
                    f"{SALT}|{task['case_key']}|{task['seed']}|{case.movements[i].id}".encode()).hexdigest())
                scores=[0.]*len(order)
                for rank,i in enumerate(order): scores[i]=-rank
            elif arm=='catboost_v5':
                from experiments.codex_train_classical import score_case
                result=score_case(case,market.a,lock['classical_root'],'catboost')
                if result.get('case_identity')!=case.identity() or result['movement_ids']!=frozen['movement_ids']: raise ValueError('Classical movement mismatch')
                scores=result['logits']; row['model_metadata']=result.get('model_metadata'); row['classical_timings']={k:result.get(k) for k in ('score_seconds','cold_load_seconds','inference_seconds')}
            if scores is not None:
                row['score_sha256']=stable(scores)
                target=prune(case,scores,**{'keep':lock['manifest']['keep_rule']['global_fraction'],
                                          'floor':lock['manifest']['keep_rule']['min_incoming_outgoing']})
            nr.validate_case(target)
            row.update(preparation_total_s=time.monotonic()-started,score_prune_s=time.monotonic()-prep,movements_full=len(case.movements),
                       movements_kept=len(target.movements),retained_ids_sha256=stable([m.id for m in target.movements]))
            original=pf.build_feasible_model
            def seeded(*a,**kw):
                built=original(*a,**kw); built['model'].seed=task['seed']; built['model'].threads=1
                return built
            pf.build_feasible_model=seeded
            # Reserve 2s for independent full-case replay/materialization, inside outer cap.
            remaining=task['seconds']-(time.monotonic()-started)-1.0
            reserve=max(2.0,task['seconds']*.10)
            search=max(0.,remaining-reserve)
            if search<=0: raise TimeoutError('Preparation consumed decision budget')
            rounds=8 if arm=='cold' else 4
            budget=nr.Budget(backend='GRB',threads=1,phase_seconds=search if arm=='cold' else search/4,
                             wall_seconds=remaining,max_rounds=rounds,epsilon=1e-4)
            row.update(search_phase_cap_s=search if arm=='cold' else search/4,completion_reserve_s=reserve)
            native_optimize=pf._optimize_once
            search_spent=0.0
            def capped_optimize(built,inner_budget,deadline):
                nonlocal search_spent
                # Completion fixes every routing x; its LP calls use reserved time,
                # not the cumulative integer-search allowance.
                if built['x'] and all(v.lb==v.ub for v in built['x']):
                    return native_optimize(built,inner_budget,deadline)
                left=search-search_spent
                if left<=0:
                    return {'status':'CAMPAIGN_SEARCH_CAP','incumbent':None,'lower_bound':None,'wall_s':0.,'seconds_cap':0.}
                before=time.monotonic()
                try:
                    return native_optimize(built,replace(inner_budget,phase_seconds=min(inner_budget.phase_seconds,left)),
                                           min(deadline,time.monotonic()+left))
                finally:search_spent+=time.monotonic()-before
            pf._optimize_once=capped_optimize
            result=pf.solve_planner(target,market.a,market.b,budget,
                  record=lambda event:append(folder/'native.jsonl',event),completion=True)
            write_new(folder/'planner.json',result)
            row.update(status=result.get('status'),source_bound=result.get('lower'),
                       source_bound_scope='restricted_model_only' if scores is not None else 'full_model',
                       global_certificate_claim=False,accepted_valid=False)
            plan=result.get('plan')
            if plan:
                plan={**plan,'case_identity':case.identity()}
                replay=nr.replay_native(case,plan)
                bill=Fraction(replay['ops_cost'])+nh.supply(market,replay['load'])
                write_new(folder/'plan.json',plan); write_new(folder/'replay.json',replay)
                row.update(bill_exact=str(bill),bill=float(bill),accepted_valid=True,vehicles=len(plan['vehicles']))
            if time.monotonic()-started>task['seconds']:
                row['accepted_valid']=False
                raise TimeoutError('Finalization exceeded end-to-end deadline')
    except BaseException as exc:
        row.update(status='failure',accepted_valid=False,
                   failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()})
    usage=resource.getrusage(resource.RUSAGE_SELF)
    row.update(wall_s=time.monotonic()-started,cpu_s=(usage.ru_utime+usage.ru_stime)-(usage0.ru_utime+usage0.ru_stime),
               peak_rss_bytes=usage.ru_maxrss if sys.platform=='darwin' else usage.ru_maxrss*1024,
               versions={name:version(name) for name in ('mip','gurobipy','torch','numpy','catboost')})
    write_new(folder/'result.json',row)

def version(name):
    try:return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:return None

def seconds(value):
    days=0
    if '-' in value: d,value=value.split('-'); days=int(d)
    parts=[float(x) for x in value.split(':')]
    return days*86400+sum(v*60**i for i,v in enumerate(reversed(parts)))

def memory_state():
    pressure=subprocess.check_output(['/usr/bin/memory_pressure','-Q'],text=True)
    swap=subprocess.check_output(['/usr/sbin/sysctl','-n','vm.swapusage'],text=True).strip()
    import re
    match=re.search(r'System-wide memory free percentage:\s*(\d+)%',pressure)
    if not match:raise RuntimeError('Cannot parse memory pressure monitor')
    return {'free_percent':int(match.group(1)),'swap':swap}

def snapshot():
    result={}
    text=subprocess.check_output(['ps','-axo','pid=,ppid=,rss=,time='],text=True)
    for line in text.splitlines():
        fields=line.split()
        if len(fields)==4: result[int(fields[0])]={'ppid':int(fields[1]),'rss':int(fields[2])*1024,'cpu':seconds(fields[3])}
    return result

def tree_stats(pid,table):
    ids={pid}
    while True:
        expanded=ids|{i for i,r in table.items() if r['ppid'] in ids}
        if expanded==ids:break
        ids=expanded
    rows=[table[i] for i in ids if i in table]
    return sum(r['rss'] for r in rows),sum(r['cpu'] for r in rows)

def tasks(lock,stage):
    seeds=[17] if stage=='qualification' else lock['manifest']['solver_seeds']
    blocks=[(cell['case_key'],seed) for cell in lock['manifest']['cohorts'][stage] for seed in seeds]
    blocks.sort(key=lambda b:stable([SALT,*b,'block']))
    for n,(case,seed) in enumerate(blocks):
        arms=lock['arms']; rotated=arms[n%len(arms):]+arms[:n%len(arms)]
        if n%2:rotated=list(reversed(rotated))
        for arm in rotated:
            yield {'case_key':case,'seed':seed,'arm':arm,'block':n,
                   'seconds':30 if stage=='qualification' else 60}

def stop(proc):
    # The owned watchdog ignores TERM, keeping this PGID alive until final KILL.
    # Never infer descendant death from the session leader's return code.
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:
        proc.wait();return
    deadline=time.monotonic()+.5
    while time.monotonic()<deadline:time.sleep(max(0.,min(.02,deadline-time.monotonic())))
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proc.wait()

def qualification_gate(lock,path):
    path=Path(path); expected=list(tasks(lock,'qualification')); issues=[]
    for task in expected:
        folder=path/stable(task)[:20]
        receipt=folder/'supervisor.json'; result=folder/'result.json'
        if not receipt.exists() or not result.exists():issues.append(f'incomplete:{folder.name}');continue
        sup=json.loads(receipt.read_text());row=json.loads(result.read_text())
        if sup.get('failure') or sup.get('returncode') or sup.get('missing_worker_receipt'):issues.append(f'infrastructure:{folder.name}')
        if row.get('failure'):issues.append(f'worker_failure:{folder.name}')
        if sup['peak_tree_rss_bytes']>5*1024**3 or sup['wall_s']>task['seconds']+2:issues.append(f'resource:{folder.name}')
    return issues

def run(args):
    lock=json.loads(Path(args.lock).read_text()); verify(lock)
    if args.stage=='screen' and not args.mock:
        if not args.qualification_output:raise ValueError('Screen requires --qualification-output')
        binding=Path(args.qualification_output)/'campaign.json'
        if not binding.exists() or json.loads(binding.read_text())!={'stage':'qualification','lock_sha256':digest(args.lock),'mock':False}:
            raise ValueError('Qualification output must match this lock and real execution mode')
        issues=qualification_gate(lock,args.qualification_output)
        if issues:raise ValueError(f'Qualification gate failed: {issues}')
    output=Path(args.output); output.mkdir(parents=True,exist_ok=True)
    # Atomic owner prevents simultaneous supervisors, retained on abnormal supervisor exit.
    guard=output/'.supervisor-owner'
    with guard.open('x') as f:f.write(str(os.getpid()))
    args.active_processes=[]
    previous={sig:signal.signal(sig,signal_stop) for sig in (signal.SIGTERM,signal.SIGINT)}
    shutdown_reason='supervisor_shutdown'
    try:return supervise(args,lock,output)
    except BaseException as exc:
        shutdown_reason=str(exc)
        append(output/'ledger.jsonl',{'event':'supervisor_failure','traceback':traceback.format_exc(),'utc':time.time()})
        raise
    finally:
        for sig in previous:signal.signal(sig,signal.SIG_IGN)
        for item in list(args.active_processes):
            proc=item['proc'];stop(proc)
            args.active_processes.remove(item)
            receipt=item['folder']/'supervisor.json'
            if not receipt.exists():
                elapsed=time.monotonic()-item['start']
                value={'failure':shutdown_reason,'returncode':proc.returncode,'endpoint_valid':False,
                       'missing_worker_receipt':not (item['folder']/'result.json').exists(),
                       'charged_cpu_s':max(elapsed,item['cpu']),'wall_s':elapsed,
                       'peak_tree_rss_bytes':item['peak_rss']}
                write_new(receipt,value)
                append(output/'ledger.jsonl',{'event':'shutdown_receipt','task':item['task'],'receipt':value})
        guard.unlink()
        for sig,handler in previous.items():signal.signal(sig,handler)

def launch_owned(args,task,folder,locksha,ledger):
    previous_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGINT})
    try:
        folder.mkdir()
        write_new(folder/'attempt.json',{'task':task,'lock_sha256':locksha,'attempt_utc':time.time()})
        append(ledger,{'event':'launch','task':task,'directory':str(folder),'utc':time.time()})
        env={**os.environ,**{key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')}}
        stdout=(folder/'stdout.log').open('x');stderr=(folder/'stderr.log').open('x')
        command=[sys.executable,'-m','experiments.codex_local_campaign','worker','--lock',str(Path(args.lock).resolve()),'--output',str(folder.resolve()),'--parent-pid',str(os.getpid())]
        if args.mock:command+=['--mock','--mock-delay',str(getattr(args,'mock_delay',0))]
        try:proc=subprocess.Popen(command,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        except BaseException:
            stdout.close();stderr.close();write_new(folder/'supervisor.json',{'failure':'launch_failed','charged_cpu_s':0,'traceback':traceback.format_exc()});raise
        stdout.close();stderr.close()
        item={'proc':proc,'folder':folder,'task':task,'start':time.monotonic(),'cpu':0.,'peak_rss':0,'reason':None}
        args.active_processes.append(item)
        append(ledger,{'event':'owned_worker','pid':proc.pid,'pgid':proc.pid,'task':task})
        return item
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)

def supervise(args,lock,output):
    ledger=output/'ledger.jsonl'
    binding=output/'campaign.json'
    expected={'stage':args.stage,'lock_sha256':digest(args.lock),'mock':args.mock}
    if binding.exists():
        if json.loads(binding.read_text())!=expected:raise ValueError('Output stage/lock/mock mismatch')
    else:write_new(binding,expected)
    planned=list(tasks(lock,args.stage)); locksha=digest(args.lock)
    expected_tasks={stable(task)[:20]:task for task in planned}
    for folder in (p for p in output.iterdir() if p.is_dir()):
        if folder.name not in expected_tasks:
            raise RuntimeError(f'Receipt issue: unknown task directory {folder}; never retry automatically')
        try:
            attempt=json.loads((folder/'attempt.json').read_text())
            receipt=json.loads((folder/'supervisor.json').read_text())
            if attempt['lock_sha256']!=locksha or attempt['task']!=expected_tasks[folder.name]:
                raise ValueError('task/lock mismatch')
            if not isinstance(receipt,dict) or 'charged_cpu_s' not in receipt:
                raise ValueError('invalid supervisor receipt')
        except (OSError,ValueError,KeyError,TypeError) as exc:
            raise RuntimeError(f'Receipt issue: incomplete/corrupt prior attempt {folder}: {exc}; never retry automatically') from exc
    spent=sum(json.loads(p.read_text()).get('charged_cpu_s',0) for p in output.glob('*/supervisor.json'))
    if args.stage=='qualification':spent+=lock.get('freeze_cpu_s',0)
    if ledger.exists():
        try:spent+=sum(json.loads(line).get('supervisor_cpu_s',0) for line in ledger.read_text().splitlines() if json.loads(line).get('event')=='summary')
        except (ValueError,TypeError) as exc:raise RuntimeError(f'Receipt issue: corrupt launch ledger {ledger}') from exc
    ceiling=(.5 if args.stage=='qualification' else 8)*3600
    reserve=60 if args.stage=='qualification' else 1800
    pending=[]
    for task in planned:
        ident=stable(task)[:20]; folder=output/ident
        if folder.exists():continue # all attempted cells skipped, successful or failed
        pending.append((task,folder))
    running=[]; halted=False; last_memory=0.; pressure_since=None; supervisor_cpu0=time.process_time()
    while pending or running:
        while pending and len(running)<2 and not halted:
            if running and pending[0][0]['block']!=running[0]['task']['block']:break
            if spent+sum(x['cpu'] for x in running)+(time.process_time()-supervisor_cpu0)>=ceiling-reserve:
                halted=True;break
            task,folder=pending.pop(0)
            running.append(launch_owned(args,task,folder,locksha,ledger))
        if not running:
            if halted:break
            continue
        table={} if args.mock else snapshot(); rss_total=0
        if not args.mock and time.monotonic()-last_memory>=1.:
            memory=memory_state();last_memory=time.monotonic()
            append(ledger,{'event':'system_memory','utc':time.time(),**memory})
            if memory['free_percent']<10:
                pressure_since=pressure_since or time.monotonic()
                if time.monotonic()-pressure_since>=5.:
                    halted=True
                    for x in running:x['reason']='system_memory_pressure'
            else:pressure_since=None
        for x in running:
            rss,cpu=tree_stats(x['proc'].pid,table);x['cpu']=max(cpu,x['cpu']);x['peak_rss']=max(rss,x['peak_rss']);rss_total+=rss
            append(x['folder']/'resources.jsonl',{'wall_s':time.monotonic()-x['start'],'rss_bytes':rss,'cpu_s':cpu})
            if rss>5*1024**3:x['reason']='worker_memory_limit';halted=True
            if time.monotonic()-x['start']>x['task']['seconds']+2:x['reason']='outer_wall_deadline'
        if rss_total>10*1024**3:
            halted=True
            for x in running:x['reason']='aggregate_memory_limit'
        if spent+sum(x['cpu'] for x in running)+(time.process_time()-supervisor_cpu0)>=ceiling:
            halted=True
            for x in running:x['reason']='campaign_cpu_limit'
        for x in list(running):
            proc=x['proc']
            if halted and x['reason'] is None:x['reason']='campaign_safety_stop'
            if proc.poll() is None and not x['reason']:continue
            completion_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGINT})
            try:
                stop(proc) # remove any remaining owned watchdog/descendants
                args.active_processes.remove(x) # retire PGID before any fallible file work
                result_path=x['folder']/'result.json'
                result=json.loads(result_path.read_text()) if result_path.exists() else {}
                charged=max(x['cpu'],result.get('cpu_s',0))
                # Missing final CPU receipt conservatively charges complete elapsed allocation.
                if not result:charged=max(charged,time.monotonic()-x['start'])
                parent_wall=time.monotonic()-x['start']
                receipt={'endpoint_valid':bool(result.get('accepted_valid')) and not x['reason'] and parent_wall<=x['task']['seconds'],
                         'endpoint_censored':parent_wall>x['task']['seconds'],
                         'returncode':proc.returncode,'failure':x['reason'], 'missing_worker_receipt':not bool(result),
                         'charged_cpu_s':charged,'peak_tree_rss_bytes':x['peak_rss'],'wall_s':time.monotonic()-x['start']}
                write_new(x['folder']/'supervisor.json',receipt);spent+=charged;running.remove(x)
                append(ledger,{'event':'finish','task':x['task'],'receipt':receipt,'utc':time.time()})
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,completion_mask)
        time.sleep(.25)
    summary={'stage':args.stage,'planned':len(planned),'attempted':len(list(output.glob('*/attempt.json'))),
             'undispatched':len(pending),'halted':halted,'charged_worker_cpu_s':spent,
             'supervisor_cpu_s':time.process_time()-supervisor_cpu0,'mock':args.mock}
    append(ledger,{'event':'summary',**summary});print(json.dumps(summary));return summary

def watch_parent(args):
    # Keep group identity alive through TERM so either owner can safely escalate.
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    worker_gone_since=None
    while True:
        try:os.kill(args.parent_pid,0)
        except ProcessLookupError:
            path=Path(args.output)/'parent-death.json'
            if not path.exists():write_new(path,{'failure':'supervisor_parent_died','utc':time.time(),
                                                'worker_pgid':args.worker_pid})
            try:os.killpg(args.worker_pid,signal.SIGTERM)
            except ProcessLookupError:return
            time.sleep(.5)
            try:os.killpg(args.worker_pid,signal.SIGKILL)
            except ProcessLookupError:pass
            return
        try:os.kill(args.worker_pid,0)
        except ProcessLookupError:
            worker_gone_since=worker_gone_since or time.monotonic()
            # Give the living supervisor ample time to perform its .5s cleanup.
            if time.monotonic()-worker_gone_since>=2.:
                try:os.killpg(args.worker_pid,signal.SIGKILL)
                except ProcessLookupError:pass
                return
        time.sleep(.1)

def mock_group_tests(root):
    # Heartbeat proves a TERM-resistant descendant stopped without relying on ps.
    child_code="import signal,time,pathlib,sys;signal.signal(signal.SIGTERM,signal.SIG_IGN);p=pathlib.Path(sys.argv[1]);\nwhile True:p.write_text(str(time.monotonic()));time.sleep(.03)"
    def wait_file(path):
        deadline=time.monotonic()+5
        while not path.exists() and time.monotonic()<deadline:time.sleep(.02)
        assert path.exists(),f'mock heartbeat missing: {path}'
    def stopped(path):
        time.sleep(.1);value=path.read_text();time.sleep(.2)
        assert path.read_text()==value,'TERM-resistant descendant still executing'
    # Session leader exits before cleanup; stop must still KILL remaining group.
    beat=root/'descendant-heartbeat'
    code="import subprocess,sys;subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]])"
    leader=subprocess.Popen([sys.executable,'-c',code,child_code,str(beat)],start_new_session=True)
    wait_file(beat);leader.wait(timeout=5);stop(leader);stopped(beat)
    # Watchdog watches the *actual supervisor*, survives own TERM, then KILLs all.
    parent=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    beat2=root/'parent-death-heartbeat';watchout=root/'watch';watchout.mkdir()
    worker_code="import subprocess,sys,time,signal;signal.signal(signal.SIGTERM,signal.SIG_IGN);subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]]);subprocess.Popen([sys.executable,'-m','experiments.codex_local_campaign','watch-parent','--parent-pid',sys.argv[3],'--worker-pid',str(__import__('os').getpid()),'--output',sys.argv[4]]);time.sleep(30)"
    worker_proc=subprocess.Popen([sys.executable,'-c',worker_code,child_code,str(beat2),str(parent.pid),str(watchout)],start_new_session=True)
    try:
        wait_file(beat2);parent.kill();parent.wait(timeout=5)
        worker_proc.wait(timeout=5)
        assert worker_proc.returncode==-signal.SIGKILL
        assert json.loads((watchout/'parent-death.json').read_text())['failure']=='supervisor_parent_died'
        stopped(beat2)
    finally:
        if parent.poll() is None:parent.kill();parent.wait()
        if worker_proc.poll() is None:stop(worker_proc)

def self_test():
    with tempfile.TemporaryDirectory(prefix='egg-campaign-mock-') as tmp:
        root=Path(tmp); lock=root/'lock.json'; out=root/'runs'
        m={'cohorts':{'qualification':[{'case_key':'mock:1'}]},'solver_seeds':[17,41,73]}
        write_new(lock,{'sources':{},'assets':{},'arms':['full4','random'],'manifest':m})
        args=argparse.Namespace(lock=str(lock),output=str(out),stage='qualification',mock=True)
        first=run(args);second=run(args)
        assert first['attempted']==second['attempted']==2
        receipts=[json.loads(p.read_text()) for p in out.glob('*/result.json')]
        assert {r['status'] for r in receipts}=={'mock_success','failure'}
        assert sum('intentional mock failure' in json.dumps(r) for r in receipts)==1
        assert len(list(out.glob('*/native.jsonl')))==2
        incomplete=out/'incomplete-test';incomplete.mkdir()
        write_new(incomplete/'attempt.json',{'lock_sha256':digest(lock),'task':{'mock':'interrupted'}})
        try:run(args)
        except RuntimeError as exc:assert 'Receipt issue' in str(exc)
        else:raise AssertionError('Incomplete receipt must block resume')
        assert len(list(out.glob('*/attempt.json')))==3
        # Expected-but-empty directory models crash between mkdir and attempt write.
        emptyout=root/'empty';emptyout.mkdir()
        expected=next(tasks(json.loads(lock.read_text()),'qualification'))
        empty=emptyout/stable(expected)[:20];empty.mkdir()
        args.output=str(emptyout)
        try:run(args)
        except RuntimeError as exc:assert 'Receipt issue' in str(exc)
        else:raise AssertionError('Empty orphan task directory must block resume')
        assert not (empty/'attempt.json').exists()
        # Corrupt JSON must be diagnosed, never skipped as an attempted task.
        (empty/'attempt.json').write_text('{broken')
        try:run(args)
        except RuntimeError as exc:assert 'Receipt issue' in str(exc)
        else:raise AssertionError('Corrupt attempt must block resume')
        signalout=root/'signal';signalout.mkdir()
        command=[sys.executable,'-m','experiments.codex_local_campaign','run','--lock',str(lock),
                 '--stage','qualification','--output',str(signalout),'--mock','--mock-delay','30']
        with (root/'signal-stdout.log').open('w') as stdout,(root/'signal-stderr.log').open('w') as stderr:
            parent=subprocess.Popen(command,stdout=stdout,stderr=stderr)
            try:
                deadline=time.monotonic()+10
                while not list(signalout.glob('*/native.jsonl')) and time.monotonic()<deadline:
                    if parent.poll() is not None:raise AssertionError('Mock supervisor exited before signal test')
                    time.sleep(.02)
                events=list(signalout.glob('*/native.jsonl'))
                assert events,'Signal test worker failed to start'
                pid=json.loads(events[0].read_text().splitlines()[0])['worker_pid']
                parent.send_signal(signal.SIGTERM);parent.wait(timeout=5)
                assert parent.returncode!=0
                for attempt in signalout.glob('*/attempt.json'):
                    if not (attempt.parent/'supervisor.json').exists():
                        print((root/'signal-stderr.log').read_text())
                    receipt=json.loads((attempt.parent/'supervisor.json').read_text())
                    assert receipt['failure']=='supervisor_signal_15'
                    assert receipt['charged_cpu_s']>0 and not receipt['endpoint_valid']
                try:os.kill(pid,0)
                except ProcessLookupError:pass
                else:raise AssertionError('Owned worker survived supervisor SIGTERM')
            finally:
                if parent.poll() is None:parent.kill();parent.wait()
        mock_group_tests(root)
        assert args.active_processes==[] # completed ownership must be retired
        print('PASS: parent-death and TERM-resistant descendant escalation; no duplicate attempts; preserved failures; incomplete/empty/corrupt directories block resume; supervisor SIGTERM kills and receipts owned workers; no numerical imports.')

def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('freeze');p.add_argument('--manifest',required=True);p.add_argument('--lock',required=True)
    p.add_argument('--v8-root',required=True);p.add_argument('--classical-root')
    for name in ('run','worker'):
        p=sub.add_parser(name);p.add_argument('--lock',required=True);p.add_argument('--output',required=True)
        p.add_argument('--mock',action='store_true');p.add_argument('--mock-delay',type=float,default=0)
        if name=='worker':p.add_argument('--parent-pid',type=int,default=0)
        if name=='run':
            p.add_argument('--stage',choices=('qualification','screen'),required=True)
            p.add_argument('--qualification-output')
    p=sub.add_parser('watch-parent');p.add_argument('--parent-pid',type=int,required=True);p.add_argument('--worker-pid',type=int,required=True);p.add_argument('--output',required=True)
    sub.add_parser('self-test')
    args=parser.parse_args()
    if args.command=='freeze':freeze(args)
    elif args.command=='run':run(args)
    elif args.command=='worker':worker(args)
    elif args.command=='watch-parent':watch_parent(args)
    else:self_test()
if __name__=='__main__':main()
