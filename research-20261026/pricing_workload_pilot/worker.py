"""One paid synthetic A0/F1 discovery or own-A0 finite-pool C1 stage."""
import time
START = time.monotonic()
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import threading
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENV = ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
       'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')
SPEC_KEYS = {'task_id','phase','base_seed','services','arm','quote','descriptor_sha256',
             'a0_folder','a0_receipt_sha256','a0_spec_sha256','a0_selected_sha256','a0_bank_sha256'}
NATIVE_PARAMETERS = dict(oracle=dict(Threads=1,Method=1,MIPGap=0,Seed='unchanged_native_default',
    CG_nominal_s=50,MIP_nominal_s=50,seeds=[],partition=True,batch_size=30,max_iters=100000,
    rc_eps=1e-6,viol_tol=1e-6,smoothing=0,dive_seconds=0,partial_pricing=None,
    directional=False,integer_pricing_seconds=0),cache=dict(Threads=1,Method=1,MIPGap=0,
    Seed='unchanged_native_default',nominal_s=100))


class ContractError(ValueError):
    pass


class StageLimit(RuntimeError):
    pass


class PhysicalRejection(ValueError):
    """A returned grid selection fails the additional physical endpoint screen."""


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def is_sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def local(path,name):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve()!=path.resolve():
        raise ContractError('Local source origin differs')
    return module


def publish(path,value):
    raw = (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)
    return sha(raw)


def attribute(model,name):
    try:
        value=model.getAttr(name)
        return value if type(value) in (int,float) and math.isfinite(value) else None
    except Exception:
        return None


def bootstrap(launch,spec,check):
    boundary = local(ROOT/'research-20261026/adjacent_oracle_boundary/boundary.py','workload_boundary')
    fixture = local(HERE/'fixture.py','workload_fixture')
    if (launch.get('sibling_source_root')!=str(boundary.REGISTERED)
            or launch.get('sibling_source_revision')!=boundary.SOURCE_REVISION):
        raise ContractError('Registered sibling authority differs')
    src=boundary.REGISTERED/'src'
    names=('run_capacity_terminal_cg','config','event_pricer_network','capacity_event_pricer',
           'terminal_energy_pricer','expanded_path_realization','run_terminal_energy_cg')
    if any(name in sys.modules for name in names):
        raise ContractError('Fresh sibling bootstrap required')
    sys.path.insert(0,str(src)); previous=sys.argv
    try:
        sys.argv=[str(src/'run_capacity_terminal_cg.py'),'--start-fee','0']
        runner=importlib.import_module('run_capacity_terminal_cg')
    finally:
        sys.argv=previous
    for name in names:
        if Path(sys.modules[name].__file__).resolve()!=src/(name+'.py'):
            raise ContractError('Sibling module origin differs: '+name)

    def loaded():
        result=[]
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).resolve()
                if path.is_relative_to(src) and path.suffix=='.py':
                    if str(path) not in launch['source_sha256']:
                        raise ContractError('Loaded sibling source outside frozen inventory')
                    for key,value in fixture.EXPECTED_COSTS.items():
                        if hasattr(module,key) and getattr(module,key)!=value:
                            raise ContractError('Captured cost constant differs')
                    result.append(str(path))
        return sorted(set(result))
    loaded(); check()
    descriptor=fixture.make_descriptor(spec['base_seed'],spec['services'],spec['quote'])
    if sha(canonical(descriptor).encode())!=spec['descriptor_sha256']:
        raise ContractError('Fresh descriptor differs from pre-outcome frozen descriptor')
    problem,prices,plugs,duties,physics,_=fixture.make_fixture(boundary,sys.modules['pandas'],descriptor)
    target=fixture.make_descriptor(spec['base_seed'],spec['services'],'source_shape')
    target_prices={s:{int(h):p for h,p in hours.items()} for s,hours in target['prices'].items()}
    flat=fixture.make_descriptor(spec['base_seed'],spec['services'],'flat')
    flat_prices={s:{int(h):p for h,p in hours.items()} for s,hours in flat['prices'].items()}
    power=sys.modules['station_power'].StationPower(physics['default_kw'],physics['station_kw'])
    net=SimpleNamespace(problem=problem,g=physics['battery_kwh'],reserve=physics['reserve_kwh'],
        soc_step=physics['soc_step'],block_min=physics['block_min'],power=power,charge_kw=physics['default_kw'])
    projector=local(ROOT/'research-20261026/adjacent_nonlinear_design/column_contract.py','workload_projector')
    builder=local(ROOT/'research-20261026/adjacent_nonlinear_design/bank_master.py','workload_bank_builder')
    aliases={s:s for s in boundary.BASES}; aliases.update(zip(boundary.STATIONS,boundary.BASES))
    return dict(boundary=boundary,fixture=fixture,runner=runner,descriptor=descriptor,problem=problem,
        prices=prices,target_prices=target_prices,flat_prices=flat_prices,plugs=plugs,duties=duties,
        physics=physics,net=net,projector=projector,builder=builder,aliases=aliases,loaded=loaded)


def admit(record,origin,index,env,source_prices,check):
    """Original physical/source-cost guards; target coefficients are recomputed."""
    check(); net=env['net']; realization=sys.modules['expanded_path_realization']
    audited=env['runner'].audit_energy(net,deepcopy(record))
    realized,detail=realization.realize_expanded_path(env['problem'],record,g_kwh=net.g,charge_kw=net.power,
        reserve_kwh=net.reserve,soc_step=net.soc_step,block_min=net.block_min,time_model='event')
    if realized is None:
        raise ContractError('Column realization failed: '+str(detail))
    reason=sys.modules['run_exact_pool_mip'].validate_injected_route(env['problem'],realized,net.g,
        net.power,net.reserve,1560.,arrival_grace_min=0.)
    if reason is not None:
        raise ContractError('Column physical validation failed: '+str(reason))
    source=realization.realized_costs(realized,detail['mapping'],station_prices=source_prices)
    if (not math.isclose(record['cost'],source['recomputed_expanded_grid_cost'],rel_tol=1e-10,abs_tol=1e-6)
            or not math.isclose(record['continuous_realized_cost'],source['continuous_realized_cost'],rel_tol=1e-10,abs_tol=1e-6)
            or not math.isclose(record['continuous_terminal_energy_kwh'],audited['continuous_terminal_energy_kwh'],rel_tol=1e-9,abs_tol=1e-6)):
        raise ContractError('Stored original-quote cost/terminal assertion differs')
    occupancy=sys.modules['capacity_event_pricer'].record_occupancy(record)
    if sorted(record['capacity_occupancy'])!=sorted([s,m,c] for (s,m),c in occupancy.items()):
        raise ContractError('Stored counted occupancy differs')
    target=realization.realized_costs(realized,detail['mapping'],station_prices=env['target_prices'])
    fresh=deepcopy(record)
    fresh.update(continuous_realized_charging_blocks=target['continuous_realized_charging_blocks'],
        terminal_energy_kwh=audited['terminal_energy_kwh'],
        continuous_terminal_energy_kwh=audited['continuous_terminal_energy_kwh'])
    p=env['projector'].project_column(fresh,origin_id=origin,record_id=str(index),
        trip_universe=env['problem'].trips,station_aliases=env['aliases'],station_order=env['boundary'].BASES,
        hour_order=tuple(range(26)),minute_horizon=1560,bus_cost=100000,session_fee=0,target='grid')
    # Every route covers at most one service in the compulsory overlap clique.
    if sum(t in (0,1,2,3) for t in p['trips'])>1:
        raise ContractError('Admitted route invalidates the common fleet lower bound')
    check()
    return dict(record=record,projection=p,blocks=target['continuous_realized_charging_blocks'],
        source_grid_cost=source['recomputed_expanded_grid_cost'],target_grid_cost=target['recomputed_expanded_grid_cost'])


def fleet(entries,env,*,fixed):
    if (len(entries)!=4 or Counter(t for e in entries for t in e['projection']['trips'])!=Counter(env['problem'].trips)
            or fixed and sorted(tuple(e['projection']['trips']) for e in entries)!=sorted(env['duties'])):
        raise ContractError('Fleet count/service partition/prescribed duties differ')
    grid=defaultdict(int); continuous=defaultdict(int)
    for entry in entries:
        for s,m,count in entry['projection']['occupancy']: grid[s,m]+=count
        for block in entry['blocks']:
            if block['realized_kwh']>0:
                lo,hi=sys.modules['capacity_event_pricer'].occupied_range(block['start_min'],block['end_min'])
                for minute in range(lo,hi+1): continuous[env['aliases'][block['station']],minute]+=1
    tg=sum(e['projection']['terminal_grid_kwh'] for e in entries)
    tc=sum(e['projection']['terminal_realized_kwh'] for e in entries)
    if any(c>env['plugs'][s] for (s,m),c in grid.items()) or any(c>env['plugs'][s] for (s,m),c in continuous.items()) or min(tg,tc)<160.-1e-6:
        raise PhysicalRejection('Selected fleet fails joint plugs/grid+realized terminal160 screen')
    return dict(fleet=4,exact_service_once=True,grid_terminal_kwh=tg,realized_terminal_kwh=tc,
        prescribed_duties_preserved=sorted(tuple(e['projection']['trips']) for e in entries)==sorted(env['duties']),
        shared_grid_plugs_valid=True,shared_realized_plugs_valid=True)


def value(entries,prices,env):
    result=dict(ops=100000.*len(entries))
    for representation in ('grid','realized'):
        load=[math.fsum(e['projection']['load_'+representation][k] for e in entries) for k in range(156)]
        electricity=math.fsum(prices[s][h]*load[26*i+h] for i,s in enumerate(env['boundary'].BASES) for h in range(26))
        result[representation+'_electricity']=electricity
        result[representation+'_cost']=result['ops']+electricity
        result[representation+'_kwh']=math.fsum(load)
        result[representation+'_station_hour_kwh']=load
        result[representation+'_terminal_kwh']=math.fsum(e['projection']['terminal_'+representation+'_kwh'] for e in entries)
    return result


def witness_key(record):
    return canonical(dict(trips=record['trips'],route_nodes=record.get('route_nodes',record.get('route')),
        charging_stops=record['charging_stops'],expanded_grid_charging_stops=record.get('expanded_grid_charging_stops')))


def cache_residual(weights,loads,entries,env):
    p=[e['projection'] for e in entries]
    residual=[max(0.,-w,w-1.) for w in weights]
    residual.extend(abs(sum(w for w,c in zip(weights,p) if t in c['trips'])-1.) for t in env['problem'].trips)
    residual.extend((max(0.,sum(weights)-4.),max(0.,160.-sum(w*c['terminal_grid_kwh'] for w,c in zip(weights,p)))))
    occupancy=defaultdict(float)
    for w,c in zip(weights,p):
        for s,m,count in c['occupancy']: occupancy[s,m]+=w*count
    residual.extend(max(0.,count-env['plugs'][s]) for (s,m),count in occupancy.items())
    mapped=[sum(w*sum(c['load_grid'][26*s+h] for s in range(6)) for w,c in zip(weights,p)) for h in range(26)]
    residual.extend(abs(a-b) for a,b in zip(loads,mapped))
    return max(residual,default=0.)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',required=True,type=Path); parser.add_argument('--parent-anchor',required=True,type=float)
    parser.add_argument('--spec-sha256',required=True); args=parser.parse_args(argv)
    folder=args.worker.resolve(); anchor=args.parent_anchor; end=anchor+180.; cutoff=anchor+150.
    report=dict(policy='pricing-workload-stage-v1',receipt_complete=False,method_endpoint_accepted=False,
        strict_delivery=False,physical_valid=False,native_optimal=False,bank_qualified=False,
        config_failure=False,fatal_contract=False,resource_violation=False,identity_failure=False,
        failures=[],input_sha256={},candidate_value=None,fallback_value=None,retained_value=None,
        used_fallback=False,target_common_value=None,target_common_grid_electricity=None,
        native_stages=[],timings={},native_optimize_calls=None,oracle_run_calls=0,
        native_seed=None,seed_policy='Unchanged native default; base_seed is construction only',
        parent_anchor=anchor,endpoint_deadline=end,nominal_native_cutoff=cutoff,
        bank_raw_columns=None,bank_unique_physical_witnesses=None)
    spec=None; env=None; best=None; retained=None; common=None; stopped=None; native_region=False
    native_deadline_hit=False; folder_bound=False; stage='gate'

    def stop(signum,frame):
        nonlocal stopped,native_deadline_hit
        if signum==signal.SIGALRM and native_region:
            native_deadline_hit=True
            raise TimeoutError('Nominal native region reached parent+150; interruption may be deferred')
        stopped=stopped or signum
        if signum==signal.SIGXCPU: report['resource_violation']=True
        raise TimeoutError('Stage stop '+str(signum))

    def check():
        use=resource.getrusage(resource.RUSAGE_SELF)
        if stopped is not None or time.monotonic()>=end: raise StageLimit('Inclusive stage180wall exhausted')
        if use.ru_utime+use.ru_stime>=120: raise StageLimit('Stage120CPU exhausted')
        peak=use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024
        if peak>5*1024**3: raise StageLimit('Observed stage RSS exceeds5GiB')
        if threading.active_count()!=1 or any(os.environ.get(k)!='1' for k in ENV):
            raise ContractError('Stage thread environment differs')
        try: os.waitpid(-1,os.WNOHANG)
        except ChildProcessError: return
        raise ContractError('Unexpected stage child')

    def read(path,label,expected=None,cap=512*1024**2):
        check(); before=path.stat()
        if label in report['input_sha256'] or path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>cap:
            raise ContractError('Exact bounded once-only regular input required: '+label)
        with path.open('rb') as stream: raw=stream.read(cap+1)
        after=path.stat()
        if (len(raw)!=before.st_size or len(raw)>cap or path.is_symlink() or path.resolve()!=path
                or not path.is_file() or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns)):
            raise ContractError('Input changed during read: '+label)
        digest=sha(raw); report['input_sha256'][label]=digest
        if expected is not None and digest!=expected: raise ContractError('Input digest differs: '+label)
        check(); return raw

    def records(path,label,expected,source_prices,keep):
        """One streamed byte hash/read; no column may be silently dropped."""
        check(); before=path.stat()
        if label in report['input_sha256'] or path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>512*1024**2:
            raise StageLimit('Complete bank unavailable/oversized; no truncation')
        digest=hashlib.sha256(); entries=[]; identities=set(); count=0; total=0
        with path.open('rb') as stream:
            while True:
                line=stream.readline(16*1024**2+1)
                if not line: break
                check(); total+=len(line); digest.update(line)
                if len(line)>16*1024**2 or total>512*1024**2: raise StageLimit('Complete bank line/file bound')
                count+=1; record=json.loads(line)
                entry=admit(record,spec['arm'],count,env,source_prices,check)
                if spec['arm']=='fixed_duty' and tuple(entry['projection']['trips']) not in env['duties']:
                    raise ContractError('Fixed-duty bank contains foreign duty')
                identities.add(witness_key(record))
                if keep: entries.append(entry)
        after=path.stat(); got=digest.hexdigest(); report['input_sha256'][label]=got
        if (total!=before.st_size or path.is_symlink() or path.resolve()!=path or not path.is_file()
                or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns)):
            raise ContractError('Complete bank changed during streamed admission')
        if not is_sha(expected) or got!=expected: raise ContractError('Complete journal producer pin differs')
        report.update(bank_raw_columns=count,bank_unique_physical_witnesses=len(identities))
        return entries,got

    def endpoint(entries,components):
        nonlocal retained,best
        if best is None or components['grid_cost']<best['grid_cost']:
            retained,best=entries,components

    def validate_selected(raw,source_prices):
        selected=json.loads(raw)
        entries=[admit(record,spec['arm'],'selected-'+str(i),env,source_prices,check) for i,record in enumerate(selected)]
        physical=fleet(entries,env,fixed=spec['arm']=='fixed_duty')
        return entries,physical

    try:
        if not args.worker.is_absolute() or not math.isfinite(anchor) or anchor>time.monotonic() or not is_sha(args.spec_sha256):
            raise ContractError('Invalid worker namespace/anchor/spec pin')
        for key in ENV: os.environ[key]='1'
        resource.setrlimit(resource.RLIMIT_CPU,(120,120))
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGXCPU): signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic()))
        launch=json.loads((HERE/'LAUNCH.json').read_text()); report['source_revision']=launch.get('source_revision')
        if launch.get('mode')!='FROZEN' or launch.get('review_disposition')!='PASS':
            raise ContractError('DRAFT/PENDING denies inputs, fixture generation and imports')
        allowed_folders={HERE/'attempt01'/f'B{seed}-N{n}-{arm}-{phase}'
            for seed in (61001,61002,61003,61004) for n in (12,24)
            for arm in ('fixed_duty','full') for phase in ('A0','F1','C1')}
        if folder not in allowed_folders:
            raise ContractError('Folder is outside the literal48 owned task namespaces; spec read denied')
        if launch.get('native_parameters')!=NATIVE_PARAMETERS or launch.get('environment')!={k:'1' for k in ENV}:
            raise ContractError('Native/environment frozen policy differs')
        spec=json.loads(read(folder/'spec.json','spec',args.spec_sha256,8*1024**2))
        if set(spec)!=SPEC_KEYS: raise ContractError('Stage spec fields differ')
        if (type(spec['base_seed']) is not int or spec['base_seed'] not in (61001,61002,61003,61004)
                or type(spec['services']) is not int or spec['services'] not in (12,24)
                or spec['phase'] not in ('A0','F1','C1') or spec['arm'] not in ('fixed_duty','full')
                or spec['quote']!=('flat' if spec['phase']=='A0' else 'source_shape')
                or spec['task_id']!=f'B{spec["base_seed"]}-N{spec["services"]}-{spec["arm"]}-{spec["phase"]}'
                or not is_sha(spec['descriptor_sha256']) or folder!=HERE/'attempt01'/spec['task_id']):
            raise ContractError('Assigned task/cohort/namespace differs')
        folder_bound=True
        report.update({k:spec[k] for k in ('task_id','phase','base_seed','services','arm','quote','descriptor_sha256')})
        a0keys=('a0_folder','a0_receipt_sha256','a0_spec_sha256','a0_selected_sha256','a0_bank_sha256')
        has_a0=spec['a0_folder'] is not None
        expected_a0=HERE/'attempt01'/f'B{spec["base_seed"]}-N{spec["services"]}-{spec["arm"]}-A0'
        if spec['phase']=='A0' and any(spec[k] is not None for k in a0keys): raise ContractError('A0 cannot inherit cache')
        if not has_a0 and any(spec[k] is not None for k in a0keys): raise ContractError('Partial A0 authority')
        if has_a0 and (spec['a0_folder']!=str(expected_a0) or any(not is_sha(spec[k]) for k in a0keys[1:4])
                or spec['a0_bank_sha256'] is not None and not is_sha(spec['a0_bank_sha256'])):
            raise ContractError('Own A0 paths/pins differ')
        if spec['phase']=='C1' and (not has_a0 or not is_sha(spec['a0_bank_sha256'])):
            raise ContractError('C1 requires independently qualified own bank/common endpoint')
        stage='bootstrap'; tick=time.monotonic(); env=bootstrap(launch,spec,check)
        report['timings']['bootstrap_wall_s']=time.monotonic()-tick
        report['loaded_sibling_python_paths_before_graph']=env['loaded']()
        if has_a0:
            stage='own_common_admission'
            oldspec=json.loads(read(expected_a0/'spec.json','a0_spec',spec['a0_spec_sha256'],8*1024**2))
            old=json.loads(read(expected_a0/'receipt.json','a0_receipt',spec['a0_receipt_sha256'],8*1024**2))
            flat_descriptor=env['fixture'].make_descriptor(spec['base_seed'],spec['services'],'flat')
            if (set(oldspec)!=SPEC_KEYS or any(oldspec[k]!=spec[k] for k in ('base_seed','services','arm'))
                    or oldspec['phase']!='A0' or oldspec['quote']!='flat' or oldspec['task_id']!=expected_a0.name
                    or oldspec['descriptor_sha256']!=sha(canonical(flat_descriptor).encode())
                    or old.get('source_revision')!=report['source_revision']
                    or any(old.get(k)!=oldspec[k] for k in ('task_id','phase','base_seed','services','arm','quote','descriptor_sha256'))
                    or old.get('receipt_complete') is not True or old.get('method_endpoint_accepted') is not True
                    or old.get('physical_valid') is not True or old.get('selected_sha256')!=spec['a0_selected_sha256']
                    or old.get('config_failure') or old.get('fatal_contract') or old.get('identity_failure')
                    or old.get('resource_violation') or old.get('stop_signal') is not None):
                raise ContractError('Own A0 source/spec/selected endpoint binding differs')
            raw=read(expected_a0/'best-records.json','a0_selected',spec['a0_selected_sha256'])
            common,physical=validate_selected(raw,env['flat_prices'])
            common_value=value(common,env['target_prices'],env); endpoint(common,common_value)
            report.update(fallback_value=common_value['grid_cost'],fallback_components=common_value,
                common_physical=physical,used_fallback=True)
        if spec['phase'] in ('A0','F1'):
            stage='graph'; tick=time.monotonic()
            kind=env['boundary'].make_fixed_duty_network_type(env['runner'].CapacityTerminalNetwork,env['duties']) if spec['arm']=='fixed_duty' else env['runner'].CapacityTerminalNetwork
            net=env['boundary'].construct(kind,env['problem'],env['prices'],plugs=env['plugs'],
                soc_step=10.,block_min=30,battery_kwh=80.,default_kw=60.,reserve_kwh=10.,
                expected_costs=env['fixture'].EXPECTED_COSTS,station_kw={'4808':120.})
            report['timings']['graph_wall_s']=time.monotonic()-tick
            check(); stage='oracle'; remaining=cutoff-time.monotonic()
            if remaining<=0: raise StageLimit('No nominal oracle allowance before native cutoff')
            cg=min(50.,remaining/2); mip=min(50.,remaining-cg)
            report.update(oracle_run_calls=1,oracle_allowances=dict(cg_seconds=cg,mip_seconds=mip,
                native_cutoff=cutoff,scope='Nominal runner durations; native signal may be deferred, parent180 authoritative'))
            tick=time.monotonic(); native_region=True
            signal.setitimer(signal.ITIMER_REAL,max(.001,cutoff-time.monotonic()))
            try:
                summary=env['runner'].run(net,folder/'oracle',target=160.,fleet_cap=4,cg_seconds=cg,mip_seconds=mip,
                    batch_size=30,seeds=(),max_iters=100000,rc_eps=1e-6,viol_tol=1e-6,smoothing=0.,
                    dive_seconds=0.,partial_pricing=None,directional=False,integer_pricing_seconds=0.,partition=True)
                report['oracle_summary']=summary
            except TimeoutError as exc:
                report['failures'].append(dict(stage='oracle',type=type(exc).__name__,message=str(exc)))
            finally:
                native_region=False; signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic()))
                report['timings']['oracle_wall_s']=time.monotonic()-tick
            report['native_deadline_overrun_s']=max(0.,time.monotonic()-cutoff)
            if native_deadline_hit or report['native_deadline_overrun_s']>0:
                report['failures'].append(dict(stage='oracle_deadline',type='NativeDeadlineOverrun',message='Nominal native cutoff exceeded; no strict delivery'))
            report['loaded_sibling_python_paths_after_oracle']=env['loaded'](); check()
            summary=report.get('oracle_summary') or {}
            report['timings']['pricing_event_wall_s']=summary.get('pricing_seconds')
            report['telemetry_scope']='Completed source summary only; incomplete histories/call counts UNKNOWN; no extra pricing'
            selected=folder/'oracle/selected_routes.json'
            if selected.is_file():
                stage='candidate_physical'; raw=read(selected,'oracle_selected')
                candidate,physical=validate_selected(raw,env['prices'])
                candidate_value=value(candidate,env['prices'],env)
                gp=sys.modules['gurobipy']
                supported=((summary.get('charging_stage') or {}).get('status') in
                    (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.SUBOPTIMAL,gp.GRB.INTERRUPTED,
                     gp.GRB.ITERATION_LIMIT,gp.GRB.WORK_LIMIT))
                report.update(candidate_value=candidate_value['grid_cost'],candidate_components=candidate_value,
                    candidate_physical=physical,native_optimal=(summary.get('charging_stage') or {}).get('status')==2,
                    native_status_supported=supported,
                    strict_delivery=bool(report.get('oracle_summary') and supported and not native_deadline_hit
                        and report['native_deadline_overrun_s']==0 and not report['failures']))
                endpoint(candidate,candidate_value)
                if spec['phase']=='A0':
                    target_value=value(candidate,env['target_prices'],env)
                    report.update(target_common_value=target_value['grid_cost'],target_common_components=target_value,
                        target_common_grid_electricity=target_value['grid_electricity'])
                report['physical_valid']=True
                report['selected_sha256']=publish(folder/'best-records.json',[e['record'] for e in retained])
                report['selected_path']=str(folder/'best-records.json')
                report.update(retained_value=best['grid_cost'],retained_components=best)
            else:
                report['failures'].append(dict(stage='selection',type='NoSelection',message='No new selected fleet; fallback-only is not strict delivery'))
            if report['physical_valid']:
                stage='whole_bank_admission'; tick=time.monotonic()
                path=folder/'oracle/columns.jsonl'; pin=summary.get('columns_sha256')
                if path.is_file() and is_sha(pin):
                    _,digest=records(path,'own_bank',pin,env['prices'],False)
                    report.update(bank_qualified=True,bank_path=str(path),bank_sha256=digest)
                else:
                    report['failures'].append(dict(stage=stage,type='NoCompleteBank',message='No complete pinned bank; retain selected fleet'))
                report['timings']['bank_admission_wall_s']=time.monotonic()-tick
        else:
            stage='complete_own_bank'; tick=time.monotonic()
            report['native_optimize_calls']=0
            report['timings']['pricing_event_wall_s']=0.
            if (old.get('bank_qualified') is not True or old.get('bank_sha256')!=spec['a0_bank_sha256']
                    or old.get('bank_path')!=str(expected_a0/'oracle/columns.jsonl')):
                raise ContractError('C1 own A0 complete-bank binding differs')
            entries,digest=records(expected_a0/'oracle/columns.jsonl','a0_bank',spec['a0_bank_sha256'],env['flat_prices'],True)
            report['timings']['bank_admission_wall_s']=time.monotonic()-tick
            check(); stage='cache_native'; import gurobipy as gp
            model=gp.Model('own_bank_grid_selection')
            event=dict(attempted=False,scope='Own-A0 retained finite pool only; grid objective')
            report['native_stages'].append(event)
            try:
                model.Params.Threads=1; model.Params.Method=1; model.Params.MIPGap=0
                model.Params.LogFile=str(folder/'cache.gurobi.log')
                if model.Params.Threads!=1 or model.Params.Method!=1 or model.Params.MIPGap!=0: raise ContractError('Cache native parameters differ')
                matrix=tuple(tuple(float(k%26==h) for k in range(156)) for h in range(26))
                adders=tuple(env['target_prices'][s][h] for s in env['boundary'].BASES for h in range(26))
                built=env['builder'].build(model,gp,[e['projection'] for e in entries],
                    market=SimpleNamespace(a=(0.,)*26,b=(0.,)*26,U=(0.,)*26),load_map=matrix,
                    station_adders=adders,trip_universe=env['problem'].trips,fleet_cap=4,plugs=env['plugs'],
                    grid_terminal_target=160.,realized_terminal_target=0.,mode='binary',institution='posted',
                    representation='grid',posted_prices=(0.,)*26,duties=env['duties'] if spec['arm']=='fixed_duty' else None)
                # Exact full-record matching of the admitted common selection, with no duplicate hint.
                marked=set()
                for chosen in common:
                    matches=[i for i,e in enumerate(entries) if canonical(e['record'])==canonical(chosen['record']) and i not in marked]
                    if not matches: raise ContractError('Common fleet absent from complete own bank')
                    marked.add(matches[0])
                for i,var in enumerate(built['weights']): var.Start=int(i in marked)
                remaining=min(100.,cutoff-time.monotonic())
                if remaining<=0: raise StageLimit('No cache native allowance before cutoff')
                model.Params.TimeLimit=remaining; event['attempted']=True; report['native_optimize_calls']=1
                tick=time.monotonic(); native_region=True
                signal.setitimer(signal.ITIMER_REAL,max(.001,cutoff-time.monotonic()))
                try: model.optimize()
                finally:
                    native_region=False; signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic()))
                    event.update(wall_s=time.monotonic()-tick,statistics={k:attribute(model,k) for k in
                        ('Status','SolCount','ObjVal','ObjBound','MIPGap','Runtime','Work','NodeCount')},
                        parameters={k:getattr(model.Params,k) for k in ('Threads','Method','MIPGap','Seed','TimeLimit','FeasibilityTol','IntFeasTol','OptimalityTol')})
                check(); report['native_deadline_overrun_s']=max(0.,time.monotonic()-cutoff)
                if native_deadline_hit or report['native_deadline_overrun_s']>0:
                    report['failures'].append(dict(stage='cache_deadline',type='NativeDeadlineOverrun',message='No strict delivery after native cutoff'))
                if model.Status in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.SUBOPTIMAL,gp.GRB.INTERRUPTED,gp.GRB.ITERATION_LIMIT,gp.GRB.WORK_LIMIT) and model.SolCount:
                    weights=[float(v.X) for v in built['weights']]
                    if any(not math.isfinite(x) or abs(x-round(x))>model.Params.IntFeasTol for x in weights): raise ContractError('Cache integrality/finite point differs')
                    loads=[float(v.X) for v in built['period_loads']]
                    if any(not math.isfinite(x) for x in loads): raise ContractError('Nonfinite cache market load')
                    event['max_recomputed_row_violation']=cache_residual(weights,loads,entries,env)
                    candidate=[e for e,x in zip(entries,weights) if x>.5]
                    physical=fleet(candidate,env,fixed=spec['arm']=='fixed_duty')
                    components=value(candidate,env['target_prices'],env)
                    report.update(candidate_value=components['grid_cost'],candidate_components=components,candidate_physical=physical,
                        candidate_column_ids=[e['projection']['record_id'] for e in candidate])
                    if not math.isclose(components['grid_cost'],model.ObjVal,rel_tol=1e-10,abs_tol=1e-6): raise ContractError('Cache physical/native grid objective differs')
                    if event['max_recomputed_row_violation']>model.Params.FeasibilityTol: raise ContractError('Cache coefficient-model row residual exceeds recorded default tolerance')
                    if model.Status==gp.GRB.OPTIMAL and components['grid_cost']>best['grid_cost'] and not math.isclose(components['grid_cost'],best['grid_cost'],rel_tol=1e-10,abs_tol=1e-6): raise ContractError('Optimal cache candidate worse than common incumbent')
                    report.update(native_optimal=model.Status==gp.GRB.OPTIMAL,
                        strict_delivery=not native_deadline_hit and report['native_deadline_overrun_s']==0)
                    endpoint(candidate,components)
                else: report['failures'].append(dict(stage=stage,type='NoIncumbent',message='Cache returned no supported finite incumbent'))
            finally:
                model.dispose()
    except Exception as exc:
        report['failures'].append(dict(stage=stage,type=type(exc).__name__,message=str(exc)))
        if isinstance(exc,ContractError) or not isinstance(exc,(StageLimit,TimeoutError,PhysicalRejection)):
            report['config_failure']=report['fatal_contract']=True
    finally:
        if folder_bound and best is not None and retained is not None and stopped is None and time.monotonic()<end:
            try:
                check(); physical=fleet(retained,env,fixed=spec['arm']=='fixed_duty')
                path=folder/'best-records.json'
                if not path.exists(): report['selected_sha256']=publish(path,[e['record'] for e in retained])
                report.update(physical_valid=True,retained_value=best['grid_cost'],retained_components=best,
                    retained_physical=physical,selected_path=str(path),used_fallback=common is not None and retained is common)
            except Exception as exc:
                report['failures'].append(dict(stage='retained_publication',type=type(exc).__name__,message=str(exc)))
                if isinstance(exc,ContractError): report['config_failure']=report['fatal_contract']=True
        use=resource.getrusage(resource.RUSAGE_SELF); now=time.monotonic()
        report.update(receipt_complete=True,stop_signal=stopped,native_deadline_hit=native_deadline_hit,
            returned_monotonic=now,elapsed_s=now-anchor,resources=dict(cpu_s=use.ru_utime+use.ru_stime,
                user_s=use.ru_utime,system_s=use.ru_stime,peak_rss_bytes=use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024,
                python_threads=threading.active_count(),hard_cpu_s=120,parent_wall_s=180))
        if report['fatal_contract'] or stopped is not None or now>=end:
            report['strict_delivery']=report['bank_qualified']=False
        report['method_endpoint_accepted']=bool(report['physical_valid'] and not report['fatal_contract'] and stopped is None and now<end)
        report['native_certificate_scope']='Source grid-LP if certified / source finite-pool MIP or C1 own finite pool; never continuous-cost/full-space certificate'
        if folder_bound: publish(folder/'receipt.json',report)
        signal.setitimer(signal.ITIMER_REAL,0)
    return 2 if report['fatal_contract'] else 0


if __name__=='__main__':
    raise SystemExit(main())
