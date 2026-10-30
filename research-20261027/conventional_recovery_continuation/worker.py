"""Prospective repaired continuation worker; main is the paid boundary.

Importing defines policy only. The original EGG helpers and native algorithms are
loaded by reference after frozen-control admission. No fixture is generated here.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HELPER = ROOT/'research-20261026/pricing_workload_pilot/worker.py'
REUSED_HERE = ROOT/'research-20261027/conventional_recovery_pilot'
REUSED_SOURCE_REVISION = '234668a879f31c3a49254adf6e313f8fbdfaa1a6'
REUSED_CONTROL_REVISION = 'c7c69a75'
REUSED_PHASES = ('F','N','D')
SEEDS = (62001, 62002, 62003, 62004)
SIZES = (12, 24)
ARMS = dict(F='fixed_duty', N='full', D='full_dive', UN='union_n', UD='union_d')
ENV = ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
       'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')
SPEC_KEYS = {'task_id','phase','base_seed','services','arm','quote','descriptor_sha256','dependencies'}
DEPENDENCY_KEYS = {'folder','spec_sha256','receipt_sha256','selected_sha256','bank_sha256',
                   'strict_delivery','physical_valid','bank_qualified'}
NATIVE_PARAMETERS = dict(oracle=dict(Threads=1,Method=1,MIPGap=0,Seed='unchanged_native_default',
    CG_nominal_s=50,MIP_nominal_s=dict(F=50,N=50,D=25),dive_nominal_s=dict(F=0,N=0,D=25),
    seeds=[],partition=True,batch_size=30,max_iters=100000,rc_eps=1e-6,viol_tol=1e-6,
    smoothing=0,dive_theta=.7,dive_mode='simple',partial_pricing=None,directional=False,
    integer_pricing_seconds=0),union=dict(Threads=1,Method=1,MIPGap=0,
    Seed='unchanged_native_default',nominal_s=100,optimize_calls=1),
    native_cutoff_s=150,parent_wall_s=180,hard_cpu_s=120,rss_bytes=5*1024**3)


class ContractError(ValueError):
    pass


class StageLimit(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def is_sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def task_id(seed,n,phase):
    return f'B{seed}-N{n}-{phase}'


def publish(path,value):
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)
    return sha(raw)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',required=True,type=Path)
    parser.add_argument('--parent-anchor',required=True,type=float)
    parser.add_argument('--spec-sha256',required=True)
    args=parser.parse_args(argv)
    folder=args.worker.resolve(); anchor=args.parent_anchor; cutoff=anchor+150.; end=anchor+180.
    report=dict(policy='conventional-recovery-v1',receipt_complete=False,strict_delivery=False,
        physical_valid=False,native_optimal=False,bank_qualified=False,method_endpoint_accepted=False,
        selected_sha256=None,bank_sha256=None,config_failure=False,fatal_contract=False,
        identity_failure=False,resource_violation=False,failures=[],input_sha256={},
        candidate_value=None,candidate_components=None,fallback_value=None,fallback_components=None,
        retained_value=None,retained_components=None,used_fallback=False,native_stages=[],timings={},
        native_optimize_calls=None,oracle_run_calls=0,parent_anchor=anchor,
        nominal_native_cutoff=cutoff,endpoint_deadline=end,native_seed=None,
        seed_policy='Unchanged native default; construction seed never seeds the solver',
        bank_raw_columns=None,bank_unique_physical_witnesses=None)
    helper=None; env=None; spec=None; retained=None; best=None; common=None
    stopped=None; native_region=False; native_deadline_hit=False; folder_bound=False; stage='gate'

    def fail(where,kind,message):
        report['failures'].append(dict(stage=where,type=kind,message=message))

    def stop(signum,frame):
        nonlocal stopped,native_deadline_hit
        if signum==signal.SIGALRM and native_region:
            native_deadline_hit=True
            raise TimeoutError('Native cutoff parent+150; signal interruption may be deferred')
        stopped=stopped or signum
        if signum==signal.SIGXCPU: report['resource_violation']=True
        raise TimeoutError('Worker stop '+str(signum))

    def check():
        use=resource.getrusage(resource.RUSAGE_SELF)
        if stopped is not None or time.monotonic()>=end: raise StageLimit('Inclusive180wall exhausted')
        peak=use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024
        if use.ru_utime+use.ru_stime>=120 or peak>5*1024**3:
            report['resource_violation']=True
            raise StageLimit('CPU120 or observed RSS5GiB exceeded')
        if threading.active_count()!=1 or any(os.environ.get(k)!='1' for k in ENV):
            raise ContractError('Thread environment differs')
        try: os.waitpid(-1,os.WNOHANG)
        except ChildProcessError: return
        raise ContractError('Unexpected child process')

    def read(path,label,expected=None,cap=512*1024**2):
        check(); before=path.stat()
        if label in report['input_sha256'] or path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>cap:
            raise ContractError('Bounded once-only regular input required: '+label)
        with path.open('rb') as stream: raw=stream.read(cap+1)
        after=path.stat()
        if (len(raw)!=before.st_size or len(raw)>cap or path.is_symlink() or path.resolve()!=path
                or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns)):
            raise ContractError('Input changed during read: '+label)
        got=sha(raw); report['input_sha256'][label]=got
        if expected is not None and got!=expected: raise ContractError('Input digest differs: '+label)
        check(); return raw

    def endpoint(entries,components):
        nonlocal retained,best
        if best is None or components['grid_cost']<best['grid_cost']:
            retained,best=entries,components

    def selected(raw,origin,fixed=False):
        records=json.loads(raw)
        if not isinstance(records,list): raise ContractError('Selection must be an explicit record list')
        entries=[helper.admit(record,origin,'selected-'+str(i),env,env['prices'],check)
                 for i,record in enumerate(records)]
        return entries,helper.fleet(entries,env,fixed=fixed)

    def bank(path,label,pin,origin,keep,*,own_completed_d=False):
        """Stream complete journal exactly once; invalid records are fatal, never dropped."""
        check(); before=path.stat()
        if label in report['input_sha256'] or path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>512*1024**2:
            raise StageLimit('Complete journal unavailable/oversized; no truncation')
        digest=hashlib.sha256(); entries=[]; witnesses=set(); total=count=0
        with path.open('rb') as stream:
            while True:
                line=stream.readline(16*1024**2+1)
                if not line: break
                check(); total+=len(line); digest.update(line); count+=1
                if len(line)>16*1024**2 or total>512*1024**2: raise StageLimit('Complete journal bound exceeded')
                record=json.loads(line)
                entry=helper.admit(record,origin,str(count),env,env['prices'],check)
                if origin=='F' and tuple(entry['projection']['trips']) not in env['duties']:
                    raise ContractError('F journal contains foreign ordered duty')
                witnesses.add(helper.witness_key(record))
                if keep: entries.append(entry)
        after=path.stat(); got=digest.hexdigest(); report['input_sha256'][label]=got
        if (total!=before.st_size or path.is_symlink() or path.resolve()!=path
                or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns)):
            raise ContractError('Complete journal changed during admission')
        if not own_completed_d and (not is_sha(pin) or got!=pin):
            raise ContractError('Complete producer journal digest differs')
        if own_completed_d and (origin!='D' or label!='own_bank' or path!=folder/'oracle/columns.jsonl'):
            raise ContractError('Final post-dive digest authority is restricted to this completed D producer')
        report.setdefault('banks',{})[origin]=dict(raw_columns=count,unique_physical_witnesses=len(witnesses),sha256=got)
        return entries,got

    def dependency(phase):
        dep=spec['dependencies'][phase]
        reused=spec['base_seed']==62001 and spec['services']==12 and phase in REUSED_PHASES
        dependency_id=task_id(spec['base_seed'],spec['services'],phase)
        expected=(REUSED_HERE if reused else HERE)/'attempt01'/dependency_id
        expected_revision=REUSED_SOURCE_REVISION if reused else report['source_revision']
        if reused and dep!=launch['reuse_contract']['rows'][dependency_id]:
            raise ContractError('Approved reused dependency differs from frozen metadata contract')
        if (not isinstance(dep,dict) or set(dep)!=DEPENDENCY_KEYS or dep['folder']!=str(expected)
                or any(not is_sha(dep[k]) for k in ('spec_sha256','receipt_sha256'))
                or any(dep[k] is not None and not is_sha(dep[k]) for k in ('selected_sha256','bank_sha256'))
                or any(type(dep[k]) is not bool for k in ('strict_delivery','physical_valid','bank_qualified'))):
            raise ContractError('Dependency exact path/fields/pins differ')
        oldspec=json.loads(read(expected/'spec.json',phase+'_spec',dep['spec_sha256'],8*1024**2))
        old=json.loads(read(expected/'receipt.json',phase+'_receipt',dep['receipt_sha256'],8*1024**2))
        if (set(oldspec)!=SPEC_KEYS or any(oldspec[k]!=spec[k] for k in ('base_seed','services','quote','descriptor_sha256'))
                or oldspec['phase']!=phase or oldspec['arm']!=ARMS[phase] or oldspec['task_id']!=expected.name
                or old.get('source_revision')!=expected_revision or old.get('receipt_complete') is not True
                or any(old.get(k)!=oldspec[k] for k in ('task_id','phase','base_seed','services','arm','quote','descriptor_sha256'))
                or any(old.get(k)!=dep[k] for k in ('selected_sha256','bank_sha256','strict_delivery','physical_valid','bank_qualified'))
                or any(old.get(k) for k in ('fatal_contract','config_failure','identity_failure','resource_violation'))
                or old.get('stop_signal') is not None or not isinstance(old.get('elapsed_s'),(int,float))
                or not 0<=old['elapsed_s']<180):
            raise ContractError('Dependency source/receipt/identity/timeliness differs')
        if dep['selected_sha256'] is not None and old.get('selected_path')!=str(expected/'best-records.json'):
            raise ContractError('Dependency selected path differs')
        if dep['bank_sha256'] is not None and old.get('bank_path')!=str(expected/'oracle/columns.jsonl'):
            raise ContractError('Dependency journal path differs')
        return expected,dep,old

    def native_enter():
        nonlocal native_region
        check()
        if time.monotonic()>=cutoff: raise StageLimit('No native time before parent+150')
        native_region=True; signal.setitimer(signal.ITIMER_REAL,max(.001,cutoff-time.monotonic()))

    def native_exit():
        nonlocal native_region
        native_region=False; signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic()))
        report['native_deadline_overrun_s']=max(0.,time.monotonic()-cutoff)
        if native_deadline_hit or report['native_deadline_overrun_s']:
            fail('native_deadline','NativeDeadlineOverrun','No strict delivery or qualified journal after native cutoff')

    try:
        if not args.worker.is_absolute() or not math.isfinite(anchor) or anchor>time.monotonic() or not is_sha(args.spec_sha256):
            raise ContractError('Invalid worker namespace/anchor/spec pin')
        for key in ENV: os.environ[key]='1'
        resource.setrlimit(resource.RLIMIT_CPU,(120,120))
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGXCPU): signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic()))
        launch=json.loads((HERE/'LAUNCH.json').read_text())
        if launch.get('mode')!='FROZEN' or launch.get('review_disposition')!='PASS':
            raise ContractError('DRAFT/PENDING denies input admission, fixture generation and native imports')
        reused_ids={task_id(62001,12,p) for p in REUSED_PHASES}
        allowed={HERE/'attempt01'/task_id(seed,n,p) for seed in SEEDS for n in SIZES for p in ARMS
                 if task_id(seed,n,p) not in reused_ids}
        if folder not in allowed: raise ContractError('Worker outside literal37 fresh namespaces; first producer triple is reuse-only')
        if launch.get('native_parameters')!=NATIVE_PARAMETERS or launch.get('environment')!={k:'1' for k in ENV}:
            raise ContractError('Native/environment frozen control differs')
        reuse_contract=launch.get('reuse_contract')
        if (not isinstance(reuse_contract,dict)
                or set(reuse_contract)!={'master_path','expected_master_sha256','source_revision','control_revision','rows'}
                or reuse_contract['master_path']!=str(REUSED_HERE/'attempt01/receipt.json')
                or not is_sha(reuse_contract['expected_master_sha256'])
                or reuse_contract['source_revision']!=REUSED_SOURCE_REVISION
                or reuse_contract['control_revision']!=REUSED_CONTROL_REVISION
                or not isinstance(reuse_contract['rows'],dict) or set(reuse_contract['rows'])!=reused_ids):
            raise ContractError('Exactly the approved three reused producer rows are required')
        for reused_id,dep in reuse_contract['rows'].items():
            if (not isinstance(dep,dict) or set(dep)!=DEPENDENCY_KEYS
                    or dep['folder']!=str(REUSED_HERE/'attempt01'/reused_id)
                    or any(not is_sha(dep[k]) for k in ('spec_sha256','receipt_sha256','selected_sha256','bank_sha256'))
                    or any(type(dep[k]) is not bool for k in ('strict_delivery','physical_valid','bank_qualified'))):
                raise ContractError('Reused producer exact literal path/metadata fields/pins differ')
        source=launch.get('source_sha256')
        if (not isinstance(source,dict) or any(not is_sha(v) for v in source.values())
                or any(str(p) not in source for p in (Path(__file__).resolve(),HERE/'fixture.py',HELPER))):
            raise ContractError('Parent-admitted frozen source inventory incomplete')
        report.update(source_revision=launch.get('source_revision'),source_binding='Parent frozen/admitted inventory; source immutability assumed during paid worker',
                      frozen_source_paths=sorted(source))
        spec=json.loads(read(folder/'spec.json','spec',args.spec_sha256,8*1024**2))
        if (set(spec)!=SPEC_KEYS or type(spec['base_seed']) is not int or spec['base_seed'] not in SEEDS
                or type(spec['services']) is not int or spec['services'] not in SIZES or spec['phase'] not in ARMS
                or spec['arm']!=ARMS[spec['phase']] or spec['quote']!='source_shape'
                or spec['task_id']!=task_id(spec['base_seed'],spec['services'],spec['phase'])
                or folder!=HERE/'attempt01'/spec['task_id'] or not is_sha(spec['descriptor_sha256'])
                or not isinstance(spec['dependencies'],dict)):
            raise ContractError('Assigned exact spec/cohort/namespace differs')
        phase=spec['phase']; deps=set(spec['dependencies'])
        permitted=({'F'} if phase in ('N','D') else {'F','N'} if phase=='UN' else {'F','D'} if phase=='UD' else set())
        if deps!=permitted and not (phase in ('N','D') and not deps):
            raise ContractError('Assigned dependency phases differ')
        folder_bound=True
        report.update({k:spec[k] for k in ('task_id','phase','base_seed','services','arm','quote','descriptor_sha256')})
        stage='bootstrap'; tick=time.monotonic()
        loader=importlib.util.spec_from_file_location('recovery_original_helpers',HELPER)
        helper=importlib.util.module_from_spec(loader); sys.modules[loader.name]=helper; loader.loader.exec_module(helper)
        if Path(helper.__file__).resolve()!=HELPER: raise ContractError('Helper origin differs')
        # Only the fixture lookup changes; helper ROOT and all algorithms stay original.
        helper.HERE=HERE
        env=helper.bootstrap(launch,spec,check)
        report['timings']['bootstrap_wall_s']=time.monotonic()-tick
        report['loaded_sibling_python_paths_before_graph']=env['loaded']()
        stage='dependency_admission'
        admitted={p:dependency(p) for p in spec['dependencies']}
        if 'F' in admitted:
            stage='common_F_admission'; path,dep,old=admitted['F']
            if not dep['physical_valid'] or not is_sha(dep['selected_sha256']) or old.get('method_endpoint_accepted') is not True:
                raise ContractError('F protection requires operational admitted endpoint')
            common,physical=selected(read(path/'best-records.json','F_selected',dep['selected_sha256']),'F',True)
            components=helper.value(common,env['prices'],env); endpoint(common,components)
            report.update(fallback_value=components['grid_cost'],fallback_components=components,common_physical=physical,used_fallback=True)
        if phase in ('F','N','D'):
            stage='graph'; tick=time.monotonic()
            kind=(env['boundary'].make_fixed_duty_network_type(env['runner'].CapacityTerminalNetwork,env['duties'])
                  if phase=='F' else env['runner'].CapacityTerminalNetwork)
            net=env['boundary'].construct(kind,env['problem'],env['prices'],plugs=env['plugs'],soc_step=10.,
                block_min=30,battery_kwh=80.,default_kw=60.,reserve_kwh=10.,
                expected_costs=env['fixture'].EXPECTED_COSTS,station_kw={'4808':120.})
            report['timings']['graph_wall_s']=time.monotonic()-tick
            check(); stage='oracle'; remaining=cutoff-time.monotonic(); scale=min(1.,remaining/100.)
            if scale<=0: raise StageLimit('No native recovery allowance')
            cg=50.*scale; dive=(25. if phase=='D' else 0.)*scale; mip=(25. if phase=='D' else 50.)*scale
            report.update(oracle_run_calls=1,oracle_allowances=dict(cg_seconds=cg,dive_seconds=dive,mip_seconds=mip,
                scale=scale,scope='Nominal100 seconds; internal CG closure LP may request300; signals may be deferred'))
            tick=time.monotonic(); summary=None; normal_return=False; native_enter()
            try:
                summary=env['runner'].run(net,folder/'oracle',target=160.,fleet_cap=4,cg_seconds=cg,mip_seconds=mip,
                    batch_size=30,seeds=(),max_iters=100000,rc_eps=1e-6,viol_tol=1e-6,smoothing=0.,
                    dive_seconds=dive,dive_theta=.7,dive_mode='simple',partial_pricing=None,directional=False,
                    integer_pricing_seconds=0.,partition=True)
                normal_return=True
            except TimeoutError as exc: fail(stage,type(exc).__name__,str(exc))
            finally:
                native_exit(); report['timings']['full_recovery_wall_s']=time.monotonic()-tick
            if summary is None and (folder/'oracle/summary.json').is_file():
                summary=json.loads(read(folder/'oracle/summary.json','oracle_partial_summary'))
            summary=summary or {}; report['oracle_summary']=summary
            report['timings'].update(pricing_event_wall_s=summary.get('pricing_seconds'),
                cg_wall_s=summary.get('cg_seconds'),lp_wall_s=summary.get('lp_seconds'),
                dive_wall_s=None,fleet_mip_wall_s=(summary.get('fleet_stage') or {}).get('seconds'),charging_mip_wall_s=None)
            report['telemetry_scope']='Source completed/partial summaries; absent dive and charging-MIP durations/call counts remain UNKNOWN'
            report['loaded_sibling_python_paths_after_oracle']=env['loaded'](); check()
            gp=sys.modules['gurobipy']; supported=(gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.SUBOPTIMAL,
                gp.GRB.INTERRUPTED,gp.GRB.ITERATION_LIMIT,gp.GRB.WORK_LIMIT)
            charging=summary.get('charging_stage') or {}
            report.update(candidate_native_status=charging.get('status'),candidate_native_bound=charging.get('bound'),
                native_optimal=charging.get('status')==gp.GRB.OPTIMAL,
                source_initial_columns_sha256=summary.get('columns_sha256'))
            report['native_stages']=[dict(stage=name,source_summary=summary.get(name))
                                     for name in ('fleet_stage','charging_stage','dive') if name in summary]
            # Qualification is independent of native selection. A missing endpoint cannot hide a valid journal.
            stage='whole_bank_admission'; tick=time.monotonic(); path=folder/'oracle/columns.jsonl'; pin=summary.get('columns_sha256')
            timely=not native_deadline_hit and not report.get('native_deadline_overrun_s')
            own_completed_d=phase=='D' and normal_return and isinstance(summary,dict) and bool(summary) and timely
            source_pinned=phase in ('F','N') and is_sha(pin)
            if path.is_file() and timely and (source_pinned or own_completed_d):
                _,digest=bank(path,'own_bank',pin,phase,False,own_completed_d=own_completed_d)
                report.update(bank_qualified=True,bank_path=str(path),bank_sha256=digest,
                    bank_source='wrapper_admitted_final_post_dive_journal' if own_completed_d else 'source_returned_columns_sha256',
                    bank_raw_columns=report['banks'][phase]['raw_columns'],bank_unique_physical_witnesses=report['banks'][phase]['unique_physical_witnesses'])
            else: fail(stage,'NoCompleteBank','No timely complete producer-pinned journal')
            report['timings']['bank_admission_wall_s']=time.monotonic()-tick
            path=folder/'oracle/selected_routes.json'; stage='candidate_physical'
            if path.is_file():
                candidate,physical=selected(read(path,'oracle_selected'),phase,phase=='F')
                components=helper.value(candidate,env['prices'],env)
                report.update(candidate_value=components['grid_cost'],candidate_components=components,candidate_physical=physical,
                    strict_delivery=bool(charging.get('status') in supported and not native_deadline_hit and not report.get('native_deadline_overrun_s')))
                endpoint(candidate,components)
            else: fail('selection','NoSelection','No supported native selected fleet; common fallback is operational only')
        else:
            stage='union_whole_banks'; tick=time.monotonic(); entries=[]
            for origin in ('F','N' if phase=='UN' else 'D'):
                path,dep,old=admitted[origin]
                if not dep['bank_qualified'] or not is_sha(dep['bank_sha256']):
                    raise ContractError('Union requires both complete independently qualified journals')
                admitted_entries,_=bank(path/'oracle/columns.jsonl',origin+'_bank',dep['bank_sha256'],origin,True)
                entries.extend(admitted_entries)  # No dropping or deduplication, including physical duplicates.
            report.update(bank_raw_columns=len(entries),
                bank_unique_physical_witnesses=len({helper.witness_key(e['record']) for e in entries}))
            report['timings']['bank_admission_wall_s']=time.monotonic()-tick
            marked=set()
            for chosen in common:
                matches=[i for i,e in enumerate(entries) if e['projection']['origin_id']=='F'
                         and canonical(e['record'])==canonical(chosen['record']) and i not in marked]
                if not matches: raise ContractError('Canonical common F record absent from consumed F journal')
                marked.add(matches[0])
            stage='union_native'; import gurobipy as gp; model=gp.Model('complete_union_grid_selection')
            event=dict(attempted=False,scope='Complete F+N or F+D finite journals only; grid objective')
            report['native_stages'].append(event); report['native_optimize_calls']=0
            report['timings']['pricing_event_wall_s']=0.
            try:
                model.Params.Threads=1; model.Params.Method=1; model.Params.MIPGap=0
                model.Params.LogFile=str(folder/'union.gurobi.log')
                if model.Params.Threads!=1 or model.Params.Method!=1 or model.Params.MIPGap!=0:
                    raise ContractError('Union native parameters differ')
                matrix=tuple(tuple(float(k%26==h) for k in range(156)) for h in range(26))
                adders=tuple(env['prices'][s][h] for s in env['boundary'].BASES for h in range(26))
                built=env['builder'].build(model,gp,[e['projection'] for e in entries],
                    market=SimpleNamespace(a=(0.,)*26,b=(0.,)*26,U=(0.,)*26),load_map=matrix,
                    station_adders=adders,trip_universe=env['problem'].trips,fleet_cap=4,plugs=env['plugs'],
                    grid_terminal_target=160.,realized_terminal_target=0.,mode='binary',institution='posted',
                    representation='grid',posted_prices=(0.,)*26)
                for i,var in enumerate(built['weights']): var.Start=int(i in marked)
                remaining=min(100.,cutoff-time.monotonic())
                if remaining<=0: raise StageLimit('No union native allowance')
                model.Params.TimeLimit=remaining; event['attempted']=True; report['native_optimize_calls']=1
                tick=time.monotonic(); native_enter()
                try: model.optimize()
                finally:
                    native_exit(); event.update(wall_s=time.monotonic()-tick,
                        statistics={k:helper.attribute(model,k) for k in ('Status','SolCount','ObjVal','ObjBound','MIPGap','Runtime','Work','NodeCount')},
                        parameters={k:getattr(model.Params,k) for k in ('Threads','Method','MIPGap','Seed','TimeLimit','FeasibilityTol','IntFeasTol','OptimalityTol')})
                    report['timings']['union_mip_wall_s']=time.monotonic()-tick
                check(); report.update(candidate_native_status=model.Status,candidate_native_bound=helper.attribute(model,'ObjBound'))
                supported=(gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.SUBOPTIMAL,gp.GRB.INTERRUPTED,gp.GRB.ITERATION_LIMIT,gp.GRB.WORK_LIMIT)
                if model.Status in supported and model.SolCount:
                    weights=[float(v.X) for v in built['weights']]; loads=[float(v.X) for v in built['period_loads']]
                    if (any(not math.isfinite(x) or abs(x-round(x))>model.Params.IntFeasTol for x in weights)
                            or any(not math.isfinite(x) for x in loads)):
                        raise ContractError('Union finite binary primal differs')
                    residual=helper.cache_residual(weights,loads,entries,env); event['max_recomputed_row_violation']=residual
                    candidate=[e for e,x in zip(entries,weights) if x>.5]
                    physical=helper.fleet(candidate,env,fixed=False); components=helper.value(candidate,env['prices'],env)
                    # Candidate entries are selected directly from these two consumed admitted journals.
                    if any(not any(canonical(e['record'])==canonical(pool['record']) for pool in entries) for e in candidate):
                        raise ContractError('Union selected record absent from consumed complete journals')
                    if residual>model.Params.FeasibilityTol or not math.isclose(components['grid_cost'],model.ObjVal,rel_tol=1e-10,abs_tol=1e-6):
                        raise ContractError('Union row residual or physical/native objective differs')
                    if model.Status==gp.GRB.OPTIMAL and components['grid_cost']>best['grid_cost']+1e-6:
                        raise ContractError('Optimal union worse than protected admitted common')
                    report.update(candidate_value=components['grid_cost'],candidate_components=components,candidate_physical=physical,
                        candidate_column_ids=[(e['projection']['origin_id'],e['projection']['record_id']) for e in candidate],
                        native_optimal=model.Status==gp.GRB.OPTIMAL,
                        strict_delivery=not native_deadline_hit and not report.get('native_deadline_overrun_s'))
                    endpoint(candidate,components)
                else: fail(stage,'NoIncumbent','One union call returned no supported finite incumbent')
            finally: model.dispose()
    except Exception as exc:
        fail(stage,type(exc).__name__,str(exc))
        physical_error=helper is not None and isinstance(exc,helper.PhysicalRejection)
        limited=isinstance(exc,(StageLimit,TimeoutError))
        if not physical_error and not limited: report['config_failure']=report['fatal_contract']=True
        if not limited and stage in ('gate','bootstrap','dependency_admission'):
            report['identity_failure']=True
    finally:
        if folder_bound and retained is not None and stopped is None and time.monotonic()<end:
            try:
                check(); physical=helper.fleet(retained,env,fixed=spec['phase']=='F')
                path=folder/'best-records.json'; digest=publish(path,[e['record'] for e in retained])
                report.update(physical_valid=True,selected_sha256=digest,selected_path=str(path),
                    retained_value=best['grid_cost'],retained_components=best,retained_physical=physical,
                    used_fallback=common is not None and retained is common)
                if spec['phase']=='F':
                    report.update(target_common_grid_electricity=best['grid_electricity'],
                                  target_common_value=best['grid_cost'],target_common_components=best)
            except Exception as exc:
                fail('retained_publication',type(exc).__name__,str(exc)); report['fatal_contract']=True
        use=resource.getrusage(resource.RUSAGE_SELF); now=time.monotonic()
        report.update(receipt_complete=True,stop_signal=stopped,native_deadline_hit=native_deadline_hit,
            returned_monotonic=now,elapsed_s=now-anchor,resources=dict(cpu_s=use.ru_utime+use.ru_stime,
                user_s=use.ru_utime,system_s=use.ru_stime,peak_rss_bytes=use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024,
                python_threads=threading.active_count(),hard_cpu_s=120,parent_wall_s=180,rss_limit_bytes=5*1024**3))
        if report['fatal_contract'] or report['resource_violation'] or stopped is not None or now>=end:
            report['strict_delivery']=report['bank_qualified']=False
        if native_deadline_hit or report.get('native_deadline_overrun_s'): report['bank_qualified']=False
        report['method_endpoint_accepted']=bool(report['physical_valid'] and not report['fatal_contract']
            and not report['resource_violation'] and stopped is None and now<end)
        report['native_certificate_scope']='Source expanded-grid LP if certified; finite journal MIP otherwise; no continuous/full-space certificate'
        if folder_bound: publish(folder/'receipt.json',report)
        signal.setitimer(signal.ITIMER_REAL,0)
    return 2 if report['fatal_contract'] else 0


if __name__=='__main__':
    raise SystemExit(main())
