"""DRAFT transferred-bank/context worker; frozen original admission is preserved."""
import time
START = time.monotonic()
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import resource
import signal
import sys
import threading

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRODUCER = ROOT/'research-20261026/adjacent_bridge_qualification'
PRIOR = ROOT/'research-20261026/adjacent_nonlinear_pilot/attempt01/000-admission'
PRIOR_REVISION = '8ba29b54a338cb8b48176f8b85772ea73d018564'
PRIOR_SOURCE = '077b3bc4ff8f9c7e766df4c9a2e893ba8bc5f0ff'
PRIOR_PIN = '999310ae2e4f55c221bc5e26194c65ea170e09daa58d52d67658d6f4caef9e14'
ORIGINAL_POLICY = 'retained-synthetic-realized-bank-nonlinear-worker-v1'
POLICY = 'retained-synthetic-realized-bank-nonlinear-reuse-worker-v1'
MARKET_POLICY = 'hourly_portfolio_surcharge_a_U_zero_station_quotes_as_adders_v1'
ECONOMIC_POLICY = dict(policy='source-station-adders-portfolio-b1-over900-v1',hours=list(range(26)),
    market_a=0,market_U=0,station_adders='original_fixture_station_quotes',load_map='sum_all_six_stations_same_hour',
    posted_prices=0,posted_b=0,nonlinear_b_numerator=1,nonlinear_b_denominator=900,b_conversion='1.0/900.0',
    bus_cost=100000,session_fee=0,fleet_cap=2,grid_terminal_target=80,realized_terminal_target=80,representation='realized')
ENV = ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
       'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')
PARAMETERS = dict(relaxation=dict(Threads=1,Method=0,Seed=17,NonConvex=0),
    binary=dict(Threads=1,Method=1,NodeMethod=1,Seed=17,NonConvex=0,MIPGap=0.,MIPGapAbs=0.))
CONTEXTS = (('fixed_duty','posted'),('full','posted'),('fixed_duty','system'),
            ('full','system'),('fixed_duty','strategic'),('full','strategic'))
PATHS = dict(prior_external=PRIOR/'external-receipt.json',prior_bank=PRIOR/'prepared-bank.json')
PRIOR_EXTERNAL_FIELDS = ['task_id','phase','arm','institution','source_revision','reaped','returncode',
    'timed_out','method_late','parent_elapsed_s','failures','config_failure','fatal_contract',
    'resource_violation','identity_failure','cpu_observation_complete','unresolved_cpu_reserve_s',
    'administrative_packet_accepted','admission_qualified','worker.receipt_complete','worker.task_id',
    'worker.phase','worker.arm','worker.institution','worker.source_revision','worker.admission_qualified',
    'worker.prepared_bank_path','worker.prepared_bank_sha256','worker.retained_columns','worker.failures',
    'worker.config_failure','worker.fatal_contract','worker.resource_violation','worker.identity_failure',
    'worker.stop_signal','worker.resources.cpu_s','worker.resources.peak_rss_bytes','worker.resources.python_threads']
RECORD_FIELDS = ['trips','route_nodes','route','charging_stops.stations','charging_stops.cst',
    'charging_stops.cet','charging_stops.kwh','expanded_grid_charging_stops.stations',
    'expanded_grid_charging_stops.cst','expanded_grid_charging_stops.cet','expanded_grid_charging_stops.kwh',
    'cost','continuous_realized_cost','terminal_energy_kwh','continuous_terminal_energy_kwh',
    'capacity_occupancy[][0]','capacity_occupancy[][1]','capacity_occupancy[][2]',
    'continuous_realized_charging_blocks[].stop_index','continuous_realized_charging_blocks[].block_index',
    'continuous_realized_charging_blocks[].station','continuous_realized_charging_blocks[].start_min',
    'continuous_realized_charging_blocks[].end_min','continuous_realized_charging_blocks[].tariff_hour',
    'continuous_realized_charging_blocks[].tariff_key','continuous_realized_charging_blocks[].price_per_kwh',
    'continuous_realized_charging_blocks[].expanded_grid_kwh','continuous_realized_charging_blocks[].realized_kwh']
PROJECTION_FIELDS = ['origin_id','record_id','trips','station_order','hour_order','minute_horizon','vector_order',
    'load_grid','load_realized','terminal_grid_kwh','terminal_realized_kwh','occupancy','fleet_units','ops',
    'session_fee','charge_stop_count','target','target_load','target_terminal_kwh','caller_physical_admission_required',
    'physical_validation_performed','shared_fleet_validation_performed','pricing_certificate_claim','scope']
FIXTURE_FIELDS = ['fixture_id','trips','duties','start_min','end_min','trip_energy','horizon_min','depot',
    'active_stations','prices','plugs','physics','expected_costs','fleet_lower_bound_witness','frame_schema','unused_stations']
PRIOR_BANK_FIELDS = ['policy','admission_qualified','fallback_ids','physical_admission','entries (count)']+[
    'fixture.'+key for key in FIXTURE_FIELDS]+['producer_bindings.'+origin+'.'+key
    for origin in ('fixed_duty','full') for key in ('publication_revision','execution_source_revision')]+[
    'input_sha256.'+key for key in ('spec','external_fixed','external_full','columns_fixed','columns_full','fixed_selected')]+[
    'entries[].projection.'+key for key in PROJECTION_FIELDS]+[
    'entries[].record.'+key for key in RECORD_FIELDS]


class ContractError(ValueError):
    pass


class QualificationDiscrepancy(ContractError):
    """A source/native point inconsistency that stops onward dispatch."""


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def local(path,name):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ContractError('Local import path differs')
    return module


def write(path,value):
    data = (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)
    return data


def copy_buffer(path,data):
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)


def environment(launch,check):
    """Paid fresh imports and literal fixture, no network/oracle construction."""
    boundary = local(ROOT/'research-20261026/adjacent_oracle_boundary/boundary.py','nonlinear_boundary')
    fixture = local(PRODUCER/'fixture.py','nonlinear_literal_fixture')
    src = boundary.REGISTERED/'src'
    names = ('run_capacity_terminal_cg','config','event_pricer_network','capacity_event_pricer',
             'terminal_energy_pricer','expanded_path_realization','run_terminal_energy_cg')
    if any(name in sys.modules for name in names):
        raise ContractError('Fresh sibling bootstrap required')
    if (launch.get('sibling_source_root') != str(boundary.REGISTERED)
            or launch.get('sibling_source_revision') != boundary.SOURCE_REVISION):
        raise ContractError('Registered sibling authority differs')
    sys.path.insert(0,str(src)); previous = sys.argv
    try:
        sys.argv = [str(src/'run_capacity_terminal_cg.py'),'--start-fee','0']
        runner = importlib.import_module('run_capacity_terminal_cg')
    finally:
        sys.argv = previous
    for name in names:
        if Path(sys.modules[name].__file__).resolve() != src/(name+'.py'):
            raise ContractError('Sibling module origin differs: '+name)
    for module in tuple(sys.modules.values()):
        filename = getattr(module,'__file__',None)
        if filename and Path(filename).resolve().is_relative_to(src) and Path(filename).suffix == '.py':
            if str(Path(filename).resolve()) not in launch['source_sha256']:
                raise ContractError('Loaded sibling module not in frozen source authority')
            for key,value in fixture.EXPECTED_COSTS.items():
                if hasattr(module,key) and getattr(module,key) != value:
                    raise ContractError('Captured cost constants differ')
    check()
    problem,prices,plugs,duties,physics,descriptor = fixture.make_fixture(boundary,sys.modules['pandas'])
    power = sys.modules['station_power'].StationPower(physics['default_kw'],physics['station_kw'])
    net = SimpleNamespace(problem=problem,g=physics['battery_kwh'],reserve=physics['reserve_kwh'],
        soc_step=physics['soc_step'],block_min=physics['block_min'],power=power,charge_kw=physics['default_kw'])
    projector = local(ROOT/'research-20261026/adjacent_nonlinear_design/column_contract.py','nonlinear_projection')
    builder = local(ROOT/'research-20261026/adjacent_nonlinear_design/bank_master.py','nonlinear_bank_builder')
    market = local(ROOT/'src/egglab/market.py','nonlinear_affine_market')
    descriptor_wire = local(ROOT/'research-20261026/descriptor_wire_repair/descriptor.py','nonlinear_descriptor_wire')
    aliases = {base:base for base in boundary.BASES}
    aliases.update(dict(zip(boundary.STATIONS,('2190L','4808','PARX','3127L','7880C','JON_A'))))
    return dict(boundary=boundary,fixture=fixture,runner=runner,problem=problem,prices=prices,plugs=plugs,
        duties=duties,physics=physics,descriptor=descriptor,net=net,projector=projector,builder=builder,
        market=market,aliases=aliases,descriptor_wire=descriptor_wire)


def admit_column(record,origin,identity,env,check):
    check(); net = env['net']; problem = env['problem']
    audited = env['runner'].audit_energy(net,deepcopy(record))
    realization = sys.modules['expanded_path_realization']
    realized,detail = realization.realize_expanded_path(problem,record,g_kwh=net.g,charge_kw=net.power,
        reserve_kwh=net.reserve,soc_step=net.soc_step,block_min=net.block_min,time_model='event')
    if realized is None:
        raise ContractError('Retained column original realization failed: '+str(detail))
    reason = sys.modules['run_exact_pool_mip'].validate_injected_route(problem,realized,net.g,net.power,
        net.reserve,env['boundary'].HORIZON_MIN,arrival_grace_min=0.)
    if reason is not None:
        raise ContractError('Retained column original physical replay failed: '+str(reason))
    costs = realization.realized_costs(realized,detail['mapping'],station_prices=env['prices'])
    if (not math.isclose(record['cost'],costs['recomputed_expanded_grid_cost'],rel_tol=1e-10,abs_tol=1e-6)
            or not math.isclose(record['continuous_realized_cost'],costs['continuous_realized_cost'],rel_tol=1e-10,abs_tol=1e-6)
            or not math.isclose(record['continuous_terminal_energy_kwh'],audited['continuous_terminal_energy_kwh'],rel_tol=1e-9,abs_tol=1e-6)):
        raise ContractError('Retained cost/terminal assertions differ')
    occupancy = sys.modules['capacity_event_pricer'].record_occupancy(record)
    if sorted(record['capacity_occupancy']) != sorted([s,m,n] for (s,m),n in occupancy.items()):
        raise ContractError('Retained counted occupancy differs from original source helper')
    projection = env['projector'].project_column(record,origin_id=origin,record_id=identity,
        trip_universe=problem.trips,station_aliases=env['aliases'],station_order=env['boundary'].BASES,
        hour_order=tuple(range(26)),minute_horizon=1560,bus_cost=100000,session_fee=0,target='realized')
    fresh = deepcopy(record)
    fresh['continuous_realized_charging_blocks'] = costs['continuous_realized_charging_blocks']
    fresh['terminal_energy_kwh'] = audited['terminal_energy_kwh']
    fresh['continuous_terminal_energy_kwh'] = audited['continuous_terminal_energy_kwh']
    actual = env['projector'].project_column(fresh,origin_id=origin,record_id=identity,
        trip_universe=problem.trips,station_aliases=env['aliases'],station_order=env['boundary'].BASES,
        hour_order=tuple(range(26)),minute_horizon=1560,bus_cost=100000,session_fee=0,target='realized')
    if any(abs(x-y)>1e-6 for key in ('load_grid','load_realized') for x,y in zip(projection[key],actual[key])):
        raise ContractError('Projected grid/realized witness loads differ after original replay')
    check()
    return actual, costs['continuous_realized_charging_blocks']


def fleet(entries,env,check,*,fixed=False):
    if (len(entries)!=2 or Counter(t for e in entries for t in e['projection']['trips']) != Counter(env['problem'].trips)
            or fixed and sorted(tuple(e['projection']['trips']) for e in entries)!=sorted(env['duties'])):
        raise ContractError('Selected fleet does not satisfy count/partition/ordered duties')
    occupancy = defaultdict(int); real_occ = defaultdict(int)
    for entry in entries:
        p,replayed_blocks = admit_column(entry['record'],entry['projection']['origin_id'],entry['projection']['record_id'],env,check)
        if canonical(p)!=canonical(entry['projection']):
            raise ContractError('Prepared projection changed on selected physical admission')
        for s,m,n in p['occupancy']:
            occupancy[s,m] += n
        for block in replayed_blocks:
            if block['realized_kwh']>0:
                first,last = sys.modules['capacity_event_pricer'].occupied_range(block['start_min'],block['end_min'])
                s = env['aliases'][block['station']]
                for minute in range(first,last+1): real_occ[s,minute] += 1
    if (any(n>env['plugs'][s] for (s,m),n in occupancy.items())
            or any(n>env['plugs'][s] for (s,m),n in real_occ.items())
            or sum(e['projection']['terminal_grid_kwh'] for e in entries)<80.-1e-6
            or sum(e['projection']['terminal_realized_kwh'] for e in entries)<80.-1e-6):
        raise ContractError('Selected joint plugs/grid/realized terminal targets fail')
    return dict(fleet=2,exact_coverage=True,fixed_duties_preserved=sorted(tuple(e['projection']['trips']) for e in entries)==sorted(env['duties']),
        grid_terminal_kwh=sum(e['projection']['terminal_grid_kwh'] for e in entries),
        realized_terminal_kwh=sum(e['projection']['terminal_realized_kwh'] for e in entries),joint_plugs_valid=True)


def economic(entries,institution,env,representation='realized',weights=None):
    projected = [e['projection'] for e in entries]
    weights = [Q(1)]*len(projected) if weights is None else [Q(float(w)) for w in weights]
    energies = [sum((w*Q(float(p['load_'+representation][k])) for w,p in zip(weights,projected)),Q(0)) for k in range(156)]
    sigma = tuple(env['prices'][s][h] for s in env['boundary'].BASES for h in range(26))
    ops = sum((w*Q(float(p['ops'])) for w,p in zip(weights,projected)),Q(0))
    adders = sum((Q(float(s))*e for s,e in zip(sigma,energies)),Q(0))
    load = [sum((energies[26*i+h] for i in range(6)),Q(0)) for h in range(26)]
    curvature = Q(0) if institution=='posted' else Q(float(1/900))
    quadratic = sum((curvature*x*x/(2 if institution=='system' else 1) for x in load),Q(0))
    value = ops+adders+quadratic
    return dict(value=float(value),value_exact=str(value),ops_exact=str(ops),station_adders_exact=str(adders),
        quadratic_exact=str(quadratic),market_load_kwh=[float(x) for x in load],
        station_hour_kwh=[float(x) for x in energies],grid_kwh=float(sum(energies,Q(0))),representation=representation,
        interpretation='Exact arithmetic on represented column/curvature coefficients, not exact physical optimum')


def attr(model,name):
    try:
        value = model.getAttr(name)
        return value if type(value) in (int,float) and math.isfinite(value) else None
    except Exception:
        return None


def row_violation(weights,load_values,entries,env):
    p=[e['projection'] for e in entries]
    residual=[max(0.,-w,w-1.) for w in weights]
    residual += [abs(sum(w for w,c in zip(weights,p) if t in c['trips'])-1.) for t in env['problem'].trips]
    residual += [max(0.,sum(weights)-2.)]
    for key in ('terminal_grid_kwh','terminal_realized_kwh'):
        residual.append(max(0.,80.-sum(w*c[key] for w,c in zip(weights,p))))
    occupancy=defaultdict(float)
    for w,c in zip(weights,p):
        for s,m,n in c['occupancy']: occupancy[s,m] += w*n
    residual += [max(0.,n-env['plugs'][s]) for (s,m),n in occupancy.items()]
    mapped=[sum(w*sum(c['load_realized'][26*s+h] for s in range(6)) for w,c in zip(weights,p)) for h in range(26)]
    residual += [abs(x-y) for x,y in zip(load_values,mapped)]
    return max(residual,default=0.)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',required=True,type=Path); parser.add_argument('--parent-anchor',required=True,type=float)
    parser.add_argument('--spec-sha256',required=True); args=parser.parse_args(argv)
    folder,anchor=args.worker.resolve(),args.parent_anchor
    if not args.worker.is_absolute() or not math.isfinite(anchor) or anchor>time.monotonic(): raise ValueError('Invalid anchor/folder')
    report=dict(policy=POLICY,receipt_complete=False,admission_qualified=False,transfer_qualified=False,method_endpoint_accepted=False,
        physical_valid=False,context_qualified=False,relaxation_qualified=False,binary_model_optimal=False,native_delivery_valid=False,
        config_failure=False,fatal_contract=False,resource_violation=False,identity_failure=False,failures=[],
        candidate_value=None,retained_value=None,fallback_value=None,native_stages=[],input_sha256={},market_policy=MARKET_POLICY)
    stopped=None; phase='unknown'; cpu_limit=60.; end=anchor+90.; stage='launch_admission'; best=None; retained=None; env=None; folder_bound=False

    def stop(signum,frame):
        nonlocal stopped
        stopped=signum
        if signum==signal.SIGXCPU: report['resource_violation']=report['config_failure']=report['fatal_contract']=True
        raise TimeoutError('Nonlinear worker signal '+str(signum))

    def check():
        use=resource.getrusage(resource.RUSAGE_SELF)
        if stopped is not None or time.monotonic()>=end: raise TimeoutError('Parent-anchored worker deadline/stop')
        if (use.ru_utime+use.ru_stime>=cpu_limit or (use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024)>5*1024**3
                or threading.active_count()!=1 or any(os.environ.get(k)!='1' for k in ENV)):
            report['resource_violation']=True; raise ContractError('Worker CPU/RSS/thread contract')
        try: os.waitpid(-1,os.WNOHANG)
        except ChildProcessError: return
        raise ContractError('Unexpected worker child')

    def read(path,label,expected=None):
        check()
        cap=512*1024**2; path=Path(path); before=path.stat()
        if (label in report['input_sha256'] or path.is_symlink() or path.resolve()!=path
                or not path.is_file() or before.st_size>cap):
            raise ContractError('Exact regular bounded input path required: '+str(path))
        with path.open('rb') as stream: raw=stream.read(cap+1)
        after=path.stat()
        if (len(raw)>cap or len(raw)!=before.st_size or path.is_symlink() or path.resolve()!=path
                or not path.is_file() or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns)):
            raise ContractError('Input changed during bounded read: '+str(path))
        digest=hashlib.sha256(raw).hexdigest(); report['input_sha256'][label]=digest
        if expected is not None and digest!=expected: raise ContractError('Input SHA256 differs: '+label)
        check(); return raw

    try:
        for key in ENV: os.environ[key]='1'
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT,signal.SIGXCPU): signal.signal(sig,stop)
        launch=json.loads((HERE/'LAUNCH.json').read_text()); report['source_revision']=launch.get('source_revision')
        if launch.get('mode')!='FROZEN' or launch.get('review_disposition')!='PASS': raise ContractError('DRAFT/PENDING refuses input/import')
        if (launch.get('native_parameters')!=PARAMETERS or launch.get('environment')!={k:'1' for k in ENV}
                or launch.get('economic_policy')!=ECONOMIC_POLICY): raise ContractError('Frozen native/environment/economic policy differs')
        stage='spec_admission'; raw=read(folder/'spec.json','spec',args.spec_sha256); spec=json.loads(raw); del raw
        if set(spec)!={'task_id','phase','arm','institution','prepared_bank_sha256'}: raise ContractError('Spec keys differ')
        phase=spec['phase']; report.update({k:spec[k] for k in ('task_id','phase','arm','institution')})
        if phase=='admission':
            if spec!={'task_id':'A00','phase':'admission','arm':None,'institution':None,'prepared_bank_sha256':None}: raise ContractError('Admission identity differs')
            cpu_limit,end=45.,anchor+120.
        elif phase=='context':
            if (spec['arm'],spec['institution']) not in CONTEXTS or spec['task_id']!=f'T{CONTEXTS.index((spec["arm"],spec["institution"]))+1:02d}-{spec["arm"]}-{spec["institution"]}': raise ContractError('Context identity differs')
            if not isinstance(spec['prepared_bank_sha256'],str) or len(spec['prepared_bank_sha256'])!=64 or any(c not in '0123456789abcdef' for c in spec['prepared_bank_sha256']): raise ContractError('New owned prepared-bank pin is mandatory')
        else: raise ContractError('Unknown phase')
        expected_folder=HERE/'attempt01'/('000-admission' if phase=='admission' else spec['task_id'])
        if folder!=expected_folder: raise ContractError('Worker folder differs from the exact owned task namespace')
        folder_bound=True
        resource.setrlimit(resource.RLIMIT_CPU,(int(cpu_limit),int(cpu_limit)))
        signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic())); check()
        stage='paid_import_and_literal_physics'; env=environment(launch,check)
        if phase=='admission':
            stage='completed_admission_transfer'; authority=launch['data_authority']
            if set(authority)!=set(PATHS): raise ContractError('Only the completed prior admission and pinned bank may be transferred')
            for label,path in PATHS.items():
                descriptor=authority[label]
                version=(dict(git_revision=PRIOR_REVISION,assumption='parent-approved-immutable-producer')
                    if label=='prior_external' else dict(producer_receipt_git_revision=PRIOR_REVISION,
                        assumption='closed-local-untracked-output-unchanged',scope='producer receipt Git provenance only; raw artifact untracked'))
                if (descriptor.get('path')!=str(path) or descriptor.get('version')!=version
                        or descriptor.get('allowed_fields')!=(PRIOR_EXTERNAL_FIELDS if label=='prior_external' else PRIOR_BANK_FIELDS)):
                    raise ContractError('Literal prior admission transfer authority differs')
            if authority['prior_bank'].get('sha256')!=PRIOR_PIN: raise ContractError('Exact completed-bank pin required')
            row=json.loads(read(PATHS['prior_external'],'prior_external',authority['prior_external'].get('sha256')))
            packet=row['worker']; resource_fields=packet['resources']
            identity=dict(task_id='A00',phase='admission',arm=None,institution=None,source_revision=PRIOR_SOURCE)
            if (any(row.get(k)!=v or packet.get(k)!=v for k,v in identity.items())
                    or row['reaped'] is not True or row['returncode']!=0 or row.get('timed_out') is True
                    or row['method_late'] is not False or not 0<=row['parent_elapsed_s']<=120
                    or row['administrative_packet_accepted'] is not True or row['admission_qualified'] is not True
                    or row['cpu_observation_complete'] is not True or row['unresolved_cpu_reserve_s']!=0
                    or row['failures'] or packet['receipt_complete'] is not True or packet['admission_qualified'] is not True
                    or packet['prepared_bank_path']!=str(PATHS['prior_bank']) or packet['prepared_bank_sha256']!=PRIOR_PIN
                    or packet['retained_columns']!=360 or packet['failures'] or packet['stop_signal'] is not None
                    or any(row.get(k) or packet.get(k) for k in ('config_failure','fatal_contract','resource_violation','identity_failure'))
                    or not 0<=resource_fields['cpu_s']<=45 or not 0<=resource_fields['peak_rss_bytes']<=5*1024**3
                    or resource_fields['python_threads']!=1):
                raise ContractError('Completed A00 source/closure/resource/bank binding rejected')
            raw=read(PATHS['prior_bank'],'prior_bank',PRIOR_PIN); bank=json.loads(raw)
            if (bank.get('policy')!=ORIGINAL_POLICY or bank.get('admission_qualified') is not True or len(bank['entries'])!=360
                    or not env['descriptor_wire'].descriptor_equal(bank['fixture'],env['descriptor'])):
                raise ContractError('Completed bank policy/count/fixture descriptor rejected')
            lookup={(e['projection']['origin_id'],e['projection']['record_id']):e for e in bank['entries']}
            if len(lookup)!=360: raise ContractError('Transferred origin/record IDs are duplicated')
            fallback=[lookup[tuple(identity)] for identity in bank['fallback_ids']]
            common_physical=fleet(fallback,env,check,fixed=True)
            values={name:economic(fallback,name,env) for name in ('posted','system','strategic')}
            check(); copy_buffer(folder/'prepared-bank.json',raw)
            report.update(admission_qualified=True,transfer_qualified=True,prepared_bank_path=str(folder/'prepared-bank.json'),
                prepared_bank_sha256=report['input_sha256']['prior_bank'],retained_columns=360,
                transfer_binding=dict(prior_external_revision=PRIOR_REVISION,prior_source_revision=PRIOR_SOURCE,
                    prior_task='A00',prior_bank_path=str(PATHS['prior_bank']),prior_bank_sha256=PRIOR_PIN,
                    copied_unchanged_bytes=True,replayed_all_columns=False,original_policy=bank['policy'],
                    original_input_sha256=bank['input_sha256'],original_producer_bindings=bank['producer_bindings']),
                common_physical=common_physical,common_values={k:v['value'] for k,v in values.items()},common_decompositions=values)
        else:
            stage='prepared_bank_admission'; bank=json.loads(read(HERE/'attempt01/000-admission/prepared-bank.json','prepared_bank',spec['prepared_bank_sha256']))
            if bank.get('policy')!=ORIGINAL_POLICY or bank.get('admission_qualified') is not True or not env['descriptor_wire'].descriptor_equal(bank['fixture'],env['descriptor']): raise ContractError('Owned prepared-bank physical/source contract differs')
            lookup={(e['projection']['origin_id'],e['projection']['record_id']):e for e in bank['entries']}
            if len(lookup)!=len(bank['entries']): raise ContractError('Prepared origin/record IDs duplicated')
            fallback=[lookup[tuple(identity)] for identity in bank['fallback_ids']]
            fleet(fallback,env,check,fixed=True); best=economic(fallback,spec['institution'],env)
            report.update(fallback_value=best['value'],fallback_value_exact=best['value_exact'],used_fallback=True)
            retained=fallback
            entries=[e for e in bank['entries'] if spec['arm']=='full' or tuple(e['projection']['trips']) in env['duties']]
            if any(tuple(e['projection']['trips']) not in env['duties'] for e in fallback): raise ContractError('Common fallback outside fixed-duty control')
            import gurobipy as gp
            market=env['market'].AffineMarket([0.]*26,[0. if spec['institution']=='posted' else 1/900]*26,[0.]*26)
            matrix=tuple(tuple(float(k%26==hour) for k in range(156)) for hour in range(26))
            adders=tuple(env['prices'][s][h] for s in env['boundary'].BASES for h in range(26))
            for mode,seconds in (('relaxation',10.),('binary',30.)):
                check(); stage='native_'+mode; model=None
                event=dict(mode=mode,attempted=False,parameters=PARAMETERS[mode],status=None,scope='Finite retained bank only')
                report['native_stages'].append(event)
                try:
                    model=gp.Model('retained_'+mode)
                    model.Params.OutputFlag=0
                    for key,value in PARAMETERS[mode].items(): setattr(model.Params,key,value)
                    if any(getattr(model.Params,key)!=value for key,value in PARAMETERS[mode].items()): raise ContractError('Native parameter readback differs')
                    built=env['builder'].build(model,gp,[e['projection'] for e in entries],market=market,load_map=matrix,
                        station_adders=adders,trip_universe=env['problem'].trips,fleet_cap=2,plugs=env['plugs'],
                        grid_terminal_target=80.,realized_terminal_target=80.,mode=mode,institution=spec['institution'],
                        representation='realized',posted_prices=[0.]*26 if spec['institution']=='posted' else None,
                        duties=env['duties'] if spec['arm']=='fixed_duty' else None)
                    if mode=='binary':
                        ids=set(tuple(x) for x in bank['fallback_ids'])
                        for weight,entry in zip(built['weights'],entries): weight.Start=int((entry['projection']['origin_id'],entry['projection']['record_id']) in ids)
                        event['start']=dict(submitted=True,processing='UNKNOWN',scope='Partial route-binary hint; load values undefined')
                    remaining=min(seconds,anchor+80.-time.monotonic())
                    if remaining<=0: raise TimeoutError('No native time before reserved publication margin')
                    model.Params.TimeLimit=remaining; event['attempted']=True; tick=time.monotonic()
                    try: model.optimize()
                    except Exception as exc:
                        if not isinstance(exc,TimeoutError): report['config_failure']=report['fatal_contract']=True
                        raise
                    finally:
                        event.update(wall_s=time.monotonic()-tick,statistics={k:attr(model,k) for k in ('Status','SolCount','ObjVal','ObjBound','MIPGap','Runtime','Work','IterCount','BarIterCount','NodeCount','MaxVio','ConstrVio','BoundVio','IntVio')},
                            default_tolerances={k:getattr(model.Params,k) for k in ('FeasibilityTol','OptimalityTol','IntFeasTol','BarConvTol')},
                            solver_version=list(gp.gurobi.version()),package_version=getattr(gp,'__version__',None))
                    check(); status=model.Status; event['status']=status
                    if status not in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT,gp.GRB.SUBOPTIMAL,gp.GRB.INTERRUPTED,gp.GRB.ITERATION_LIMIT,gp.GRB.WORK_LIMIT) or model.SolCount<1:
                        event['no_incumbent']=True; continue
                    weights=[float(v.X) for v in built['weights']]
                    if any(not math.isfinite(v) for v in weights): raise ContractError('Nonfinite retained-column native weights')
                    point=economic(entries,spec['institution'],env,weights=weights)
                    native_loads=[float(v.X) for v in built['period_loads']]
                    if any(not math.isfinite(v) for v in native_loads): raise ContractError('Nonfinite native market loads')
                    event.update(coefficient_point_value=point['value'],coefficient_point_value_exact=point['value_exact'],
                        coefficient_point_agreement=math.isclose(point['value'],model.ObjVal,rel_tol=1e-10,abs_tol=1e-6),
                        max_recomputed_row_violation=row_violation(weights,native_loads,entries,env))
                    if mode=='relaxation':
                        if not event['coefficient_point_agreement'] or event['max_recomputed_row_violation']>model.Params.FeasibilityTol:
                            raise QualificationDiscrepancy('Relaxation native/coefficient objective agreement or model rows fail recorded source/default screen')
                        report['relaxation_qualified']=bool(status==gp.GRB.OPTIMAL and event['coefficient_point_agreement']
                            and event['max_recomputed_row_violation']<=model.Params.FeasibilityTol)
                        event['fractional_weights']=weights; event['not_a_schedule']=True
                    else:
                        if any(abs(x-round(x))>model.Params.IntFeasTol for x in weights): raise QualificationDiscrepancy('Native binary weight exceeds default integrality tolerance')
                        candidate=[e for e,x in zip(entries,weights) if x>.5]
                        physical=fleet(candidate,env,check,fixed=spec['arm']=='fixed_duty')
                        candidate_value=economic(candidate,spec['institution'],env)
                        agreement=math.isclose(candidate_value['value'],model.ObjVal,rel_tol=1e-10,abs_tol=1e-6)
                        report.update(candidate_value=candidate_value['value'],candidate_value_exact=candidate_value['value_exact'],
                            native_delivery_valid=True,binary_model_optimal=status==gp.GRB.OPTIMAL,
                            candidate_objective_agreement=agreement,candidate_physical=physical,
                            candidate_column_ids=[[e['projection']['origin_id'],e['projection']['record_id']] for e in candidate])
                        reasons=[]
                        if not agreement or not event['coefficient_point_agreement']: reasons.append('Physical/native coefficient objective agreement fails existing cost screen')
                        if event['max_recomputed_row_violation']>model.Params.FeasibilityTol: reasons.append('Native coefficient-model row residual exceeds recorded default feasibility tolerance')
                        if status==gp.GRB.OPTIMAL and candidate_value['value']>report['fallback_value'] and not math.isclose(candidate_value['value'],report['fallback_value'],rel_tol=1e-10,abs_tol=1e-6):
                            reasons.append('OPTIMAL candidate worse than admitted common fixed-bank incumbent beyond existing cost screen')
                        if Q(candidate_value['value_exact'])<Q(best['value_exact']): best,retained=candidate_value,candidate; report['used_fallback']=False
                        if reasons:
                            event['qualification_discrepancies']=reasons
                            raise QualificationDiscrepancy('; '.join(reasons))
                except Exception as exc:
                    if not isinstance(exc,TimeoutError) and not event['attempted']:
                        report['config_failure']=report['fatal_contract']=True
                    raise
                finally:
                    if model is not None:
                        try: model.dispose()
                        except Exception as exc: report['failures'].append(dict(stage='dispose_'+mode,type=type(exc).__name__,message=str(exc)))
            stage='durable_retained_endpoint'; check(); fleet(retained,env,check,fixed=spec['arm']=='fixed_duty')
            write(folder/'best-records.json',[e['record'] for e in retained])
            report.update(physical_valid=True,retained_value=best['value'],retained_value_exact=best['value_exact'],
                selected_decomposition=best,grid_diagnostic=economic(retained,spec['institution'],env,'grid'),
                context_qualified=bool(report['relaxation_qualified'] and report['binary_model_optimal'] and report['native_delivery_valid'] and not report['failures']))
            check()
    except Exception as exc:
        report['failures'].append(dict(stage=stage,type=type(exc).__name__,message=str(exc)))
        if isinstance(exc,ContractError) or (not isinstance(exc,TimeoutError) and stage not in ('native_relaxation','native_binary','durable_retained_endpoint')):
            report['config_failure']=report['fatal_contract']=True
    finally:
        if phase=='context' and best is not None and retained is not None and not report['fatal_contract'] and stopped is None and time.monotonic()<end and not report['physical_valid']:
            try:
                check(); fleet(retained,env,check,fixed=spec['arm']=='fixed_duty')
                write(folder/'best-records.json',[e['record'] for e in retained])
                report.update(physical_valid=True,retained_value=best['value'],retained_value_exact=best['value_exact'],
                    selected_decomposition=best,grid_diagnostic=economic(retained,spec['institution'],env,'grid'))
            except Exception as exc:
                report['failures'].append(dict(stage='retained_fallback_publication',type=type(exc).__name__,message=str(exc)))
                if isinstance(exc,ContractError): report['config_failure']=report['fatal_contract']=True
        use=resource.getrusage(resource.RUSAGE_SELF); now=time.monotonic()
        report.update(receipt_complete=True,stop_signal=stopped,returned_monotonic=now,elapsed_s=now-anchor,
            method_endpoint_accepted=bool(report['physical_valid'] and not report['fatal_contract'] and stopped is None and now<end),
            resources=dict(cpu_s=use.ru_utime+use.ru_stime,user_s=use.ru_utime,system_s=use.ru_stime,
                peak_rss_bytes=use.ru_maxrss if sys.platform=='darwin' else use.ru_maxrss*1024,python_threads=threading.active_count(),cpu_limit_s=cpu_limit))
        if report['fatal_contract'] or stopped is not None or now>=end or report['failures']: report['admission_qualified']=report['transfer_qualified']=report['context_qualified']=False
        if folder_bound: write(folder/'receipt.json',report)
        signal.setitimer(signal.ITIMER_REAL,0)
    return 2 if report['fatal_contract'] else 0


if __name__=='__main__': raise SystemExit(main())
