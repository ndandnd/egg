"""Gated serial owner: transfer a completed bank admission, then six contexts."""
import time
START = time.monotonic()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/adjacent_nonlinear_reuse'
SIBLING = Path('/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001')
SIBLING_REV = '3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c'
PRODUCER_REV = '8ba29b54a338cb8b48176f8b85772ea73d018564'
PRIOR_ADMISSION_SOURCE = '077b3bc4ff8f9c7e766df4c9a2e893ba8bc5f0ff'
PRIOR_BANK_SHA = '999310ae2e4f55c221bc5e26194c65ea170e09daa58d52d67658d6f4caef9e14'
POLICY = 'adjacent-retained-bank-admission-reuse-v1'
THREAD_ENV = ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
    'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')
CONTEXTS = (('T01-fixed_duty-posted','fixed_duty','posted'), ('T02-full-posted','full','posted'),
    ('T04-full-system','full','system'), ('T03-fixed_duty-system','fixed_duty','system'),
    ('T05-fixed_duty-strategic','fixed_duty','strategic'), ('T06-full-strategic','full','strategic'))
BUDGETS = dict(total_cpu_s=480,total_wall_s=900,dispatch_cpu_s=420,closure_cpu_s=60,
    combined_preflight_cpu_s=60,preparation_cpu_s=10,preparation_wall_s=20,
    admission_cpu_s=45,admission_wall_s=120,worker_cpu_s=60,worker_wall_s=90,
    native_cutoff_s=80,relaxation_native_s=10,binary_native_s=30,
    cleanup_s=3,finalization_cpu_s=60,finalization_wall_s=120)
LOCAL = ('research-20261026/adjacent_nonlinear_reuse/run.py',
    'research-20261026/adjacent_nonlinear_reuse/prepare.py',
    'research-20261026/adjacent_nonlinear_reuse/worker.py',
    'research-20261026/adjacent_nonlinear_reuse/PROTOCOL.md',
    'research-20261026/adjacent_nonlinear_reuse/OWNER_NOTE.md',
    'research-20261026/adjacent_nonlinear_reuse/WORKER_NOTE.md',
    'research-20261026/adjacent_nonlinear_design/column_contract.py',
    'research-20261026/adjacent_nonlinear_design/bank_master.py',
    'research-20261026/adjacent_nonlinear_design/ORACLE_AND_TARGET_CONTRACT.md',
    'research-20261026/adjacent_nonlinear_design/ECONOMIC_COMPOSITION.md',
    'research-20261026/descriptor_wire_repair/descriptor.py',
    'research-20261026/adjacent_bridge_qualification/fixture.py',
    'research-20261026/adjacent_oracle_boundary/boundary.py',
    'src/egglab/__init__.py','src/egglab/market.py')
PARAMETERS = dict(relaxation=dict(Threads=1,Method=0,Seed=17,NonConvex=0),
    binary=dict(Threads=1,Method=1,NodeMethod=1,Seed=17,NonConvex=0,MIPGap=0.,MIPGapAbs=0.))
ECONOMICS = dict(policy='source-station-adders-portfolio-b1-over900-v1',hours=list(range(26)),
    market_a=0,market_U=0,station_adders='original_fixture_station_quotes',
    load_map='sum_all_six_stations_same_hour',posted_prices=0,posted_b=0,
    nonlinear_b_numerator=1,nonlinear_b_denominator=900,b_conversion='1.0/900.0',
    bus_cost=100000,session_fee=0,fleet_cap=2,grid_terminal_target=80,
    realized_terminal_target=80,representation='realized')
PUBLISHING_CHILD = False
DEFERRED_STOP = None
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


def cpu(who=resource.RUSAGE_SELF):
    u=resource.getrusage(who)
    return u.ru_utime+u.ru_stime


def rss():
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))


def number(x):
    return type(x) in (int,float) and math.isfinite(x) and x>=0


def revision(x):
    return isinstance(x,str) and len(x)==40 and all(c in '0123456789abcdef' for c in x)


def read_once(path, cap=8*1024**2):
    path=Path(path); before=path.stat()
    if path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>cap:
        raise ContractError('Exact bounded regular path required: '+str(path))
    with path.open('rb') as stream:
        raw=stream.read(cap+1)
    after=path.stat()
    if len(raw)!=before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
        raise ContractError('Consumed bytes changed during read')
    return raw


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path,value):
    path=Path(path); temp=path.with_name(path.name+'.final.tmp')
    save(temp,value); os.replace(temp,path)


def authority_paths():
    base=ROOT/'research-20261026/adjacent_nonlinear_pilot/attempt01/000-admission'
    return dict(prior_external=str(base/'external-receipt.json'),prior_bank=str(base/'prepared-bank.json'))


def gate():
    raw=read_once(HERE/'LAUNCH.json'); launch=json.loads(raw)
    p=launch.get('preparation_accounting') or {}; authority=launch.get('data_authority') or {}
    if (Path(__file__).resolve()!=HERE/'run.py' or Path.cwd().resolve()!=ROOT
            or launch.get('mode')!='FROZEN' or launch.get('review_disposition')!='PASS'
            or launch.get('policy')!=POLICY or launch.get('workdir')!=str(ROOT)
            or not revision(launch.get('source_revision')) or not launch.get('command')
            or launch.get('source_freeze_assumption')!='parent-approved-frozen-commit'
            or launch.get('sibling_source_root')!=str(SIBLING) or launch.get('sibling_source_revision')!=SIBLING_REV
            or launch.get('budgets')!=BUDGETS or launch.get('native_parameters')!=PARAMETERS
            or launch.get('economic_policy')!=ECONOMICS
            or launch.get('environment')!={k:'1' for k in THREAD_ENV}
            or launch.get('clean_argv')!=['--start-fee','0'] or launch.get('start_fee')!=0
            or launch.get('context_order')!=[t[0] for t in CONTEXTS]
            or launch.get('tracking_prefix') is None or launch.get('numerical_resource_prefix') is None
            or not isinstance(launch.get('source_sha256'),dict) or set(authority)!=set(authority_paths())
            or p.get('external_accepted') is not True or not number(p.get('charged_cpu_s'))
            or p['charged_cpu_s']>10 or not number(p.get('elapsed_s')) or p['elapsed_s']>20):
        raise SystemExit('DRAFT/PENDING: sources, producer inputs, admission and dispatch denied')
    for key,path in authority_paths().items():
        d=authority[key]
        external=key=='prior_external'
        version=({'git_revision':PRODUCER_REV,'assumption':'parent-approved-immutable-producer'} if external else
            {'producer_receipt_git_revision':PRODUCER_REV,'assumption':'closed-local-untracked-output-unchanged',
             'scope':'producer receipt Git provenance only; raw artifact untracked'})
        if (d.get('path')!=path or d.get('version')!=version
                or d.get('allowed_fields')!=(PRIOR_EXTERNAL_FIELDS if external else PRIOR_BANK_FIELDS)):
            raise SystemExit('Frozen literal producer input/field authority differs')
    if (authority['prior_bank'].get('sha256')!=PRIOR_BANK_SHA
            or authority['prior_bank'].get('producer_pin')!='prior_external.worker.prepared_bank_sha256'
            or launch.get('prior_admission_source_revision')!=PRIOR_ADMISSION_SOURCE
            or launch.get('prior_retained_columns')!=360):
        raise SystemExit('Completed admission source / mandatory bank pin differs')
    return launch,raw


def preflight(launch,report,check):
    closure=launch.get('source_closure') or {}; sibling=closure.get('sibling_python_paths')
    if closure.get('roots')!=['run_capacity_terminal_cg'] or not isinstance(sibling,list) or not sibling:
        raise ContractError('Frozen registered sibling source closure required')
    if len(sibling)>192 or len(set(sibling))!=len(sibling) or any(
            not Path(p).is_relative_to(SIBLING/'src') or Path(p).suffix!='.py' for p in sibling):
        raise ContractError('Invalid source closure')
    names={str(ROOT/p) for p in LOCAL}|set(sibling)
    if set(launch['source_sha256'])!=names:
        raise ContractError('Frozen consumed-source inventory differs')
    for path in sorted(names):
        check(); digest=hashlib.sha256(read_once(path,2*1024**2)).hexdigest()
        report['source_sha256'][path]=digest
        if digest!=launch['source_sha256'][path]:
            raise ContractError('Execution-integrity source bytes differ: '+path)


def worker(row,bank_sha):
    global PUBLISHING_CHILD
    admission=row['phase']=='admission'; cap=45 if admission else 60; wall=120 if admission else 90
    folder=HERE/'attempt01'/('000-admission' if admission else row['task_id'])
    folder.mkdir(exist_ok=False)
    raw=(json.dumps({k:row[k] for k in ('task_id','phase','arm','institution')}|
        dict(prepared_bank_sha256=bank_sha),indent=2)+'\n').encode()
    with (folder/'spec.json').open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    sha=hashlib.sha256(raw).hexdigest()
    save(folder/'receipt.json',dict(receipt_complete=False))
    row.update(folder=str(folder),attempted=False,reaped=False,failures=[],config_failure=False)
    child=None; packet={}; cleanup_end=None
    old_child,old_self=cpu(resource.RUSAGE_CHILDREN),cpu(); anchor=time.monotonic()
    row['parent_anchor']=anchor
    with (folder/'stdout.txt').open('x') as out,(folder/'stderr.txt').open('x') as err:
        try:
            PUBLISHING_CHILD=True
            try:
                child=subprocess.Popen([str(ROOT/'.venv-local/bin/python'),'-B',str(HERE/'worker.py'),
                    '--worker',str(folder),'--parent-anchor',repr(anchor),'--spec-sha256',sha],
                    cwd=ROOT,env=dict(os.environ),stdout=out,stderr=err,start_new_session=True,
                    preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CPU,(cap,cap)))
                row.update(attempted=True,pid=child.pid)
            finally:
                PUBLISHING_CHILD=False
            if DEFERRED_STOP is not None:
                raise TimeoutError('Stop deferred through owned child PID publication')
            try:
                child.wait(timeout=max(.001,anchor+wall-time.monotonic()))
            except subprocess.TimeoutExpired:
                row['timed_out']=True; cleanup_end=time.monotonic()+3; child.terminate()
                try:
                    child.wait(timeout=min(1.,max(.001,cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001,cleanup_end-time.monotonic()))
            row.update(reaped=True,returncode=child.returncode)
        except BaseException as exc:
            row['failures'].append(dict(stage='process',type=type(exc).__name__,message=str(exc)))
            if child is None:
                row['config_failure']=True
            elif child.returncode is None:
                try:
                    cleanup_end=cleanup_end or time.monotonic()+3
                    child.kill(); child.wait(timeout=max(.001,cleanup_end-time.monotonic()))
                    row.update(reaped=True,returncode=child.returncode)
                except BaseException as secondary:
                    row['failures'].append(dict(stage='cleanup',type=type(secondary).__name__,message=str(secondary)))
    row['process_return_elapsed_s']=time.monotonic()-anchor
    try:
        packet=json.loads(read_once(folder/'receipt.json'))
        if packet.get('receipt_complete') is True and any(packet.get(k)!=row[k]
                for k in ('task_id','phase','arm','institution')):
            raise ContractError('Complete worker packet identity differs')
        if packet.get('receipt_complete') is True and packet.get('source_revision')!=row['source_revision']:
            raise ContractError('Complete worker packet source revision differs from frozen launch')
    except BaseException as exc:
        row['config_failure']=True
        row['failures'].append(dict(stage='compact_packet',type=type(exc).__name__,message=str(exc)))
    now=time.monotonic(); usage=packet.get('resources') or {}
    row.update(worker=packet,parent_elapsed_s=now-anchor,method_late=now>anchor+wall,
        waited_child_cpu_s=cpu(resource.RUSAGE_CHILDREN)-old_child,parent_cpu_s=cpu()-old_self,
        cpu_observation_complete=child is None or row['reaped'],
        unresolved_cpu_reserve_s=60. if child is not None and not row['reaped'] else 0.)
    for flag in ('config_failure','fatal_contract','resource_violation','identity_failure'):
        row[flag]=bool(row.get(flag) or packet.get(flag))
    if packet.get('receipt_complete') is True and (not number(usage.get('peak_rss_bytes'))
            or usage['peak_rss_bytes']>5*1024**3 or usage.get('python_threads')!=1):
        row['config_failure']=row['resource_violation']=True
    if (not admission and packet.get('method_endpoint_accepted') is True
            and not number(packet.get('retained_value'))):
        row['config_failure']=True
    accepted=bool(row['reaped'] and row.get('returncode')==0 and not row.get('timed_out')
        and not row['method_late'] and not row['failures'] and packet.get('receipt_complete') is True
        and not any(row.get(f) for f in ('config_failure','fatal_contract','resource_violation','identity_failure')))
    row.update(administrative_packet_accepted=accepted,
        admission_qualified=bool(admission and accepted and packet.get('admission_qualified') is True),
        physical_endpoint_accepted=bool(not admission and accepted and packet.get('method_endpoint_accepted') is True
            and packet.get('physical_valid') is True))
    save(folder/'external-receipt.json',row)
    return row


def readout(report):
    rows=[]; by_key={}
    for row in report['contexts']:
        p=row.get('worker') or {}
        fallback=(report.get('common_values') or {}).get(row['institution'])
        fresh=p.get('retained_value') if row.get('physical_endpoint_accepted') else None
        value=fresh if fresh is not None else fallback
        r=dict(task_id=row['task_id'],arm=row['arm'],institution=row['institution'],attempted=row.get('attempted',False),
            administrative_packet_accepted=row.get('administrative_packet_accepted',False),
            physical_endpoint_accepted=row.get('physical_endpoint_accepted',False),
            context_qualified=bool(row.get('physical_endpoint_accepted') and p.get('context_qualified') is True),
            retained_value=value,operational_endpoint_available=value is not None,
            operational_source='parent_accepted_worker' if fresh is not None else
                'admitted_common_fallback' if fallback is not None else 'missing_admission',
            operational_decomposition=p.get('selected_decomposition') if fresh is not None else
                (report.get('common_decompositions') or {}).get(row['institution']),
            worker=p,failures=row.get('failures',[]),
            unattempted_reason=row.get('unattempted_reason'),parent_elapsed_s=row.get('parent_elapsed_s'))
        rows.append(r); by_key[row['arm'],row['institution']]=r
    operational_contrasts={}; method_contrasts={}
    for institution in ('posted','system','strategic'):
        left=by_key['fixed_duty',institution]['retained_value']; right=by_key['full',institution]['retained_value']
        operational_contrasts[institution]=dict(fixed_minus_full=None if left is None or right is None else left-right,
            both_operational=left is not None and right is not None,
            scope='Operational delivered endpoints, including admitted common fallback; not evidence both methods succeeded')
        l=by_key['fixed_duty',institution]; r=by_key['full',institution]
        qualified=l['context_qualified'] and r['context_qualified']
        method_contrasts[institution]=dict(fixed_minus_full=left-right if qualified else None,
            both_method_qualified=qualified,planned_methods=2,
            scope='Undefined unless both planned methods are timely physically admitted and context-qualified; finite bank only')
    return dict(passed=report['passed'],scope=report['passed_scope'],planned_contexts=6,
        admission=report['admission'],contexts=rows,paired_method_qualified_contrasts=method_contrasts,
        paired_operational_fallback_contrasts=operational_contrasts,
        complete_all_six=len(rows)==6 and all(r['attempted'] and r['administrative_packet_accepted']
            and r['physical_endpoint_accepted'] for r in rows),
        complete_all_six_scope='Six attempted timely physical packets; native/context qualification separately retained',
        complete_operational_six=len(rows)==6 and all(r['operational_endpoint_available'] for r in rows),
        all_six_context_qualified=len(rows)==6 and all(r['context_qualified'] for r in rows),
        pooled_cross_institution_mean=None,available_only_mean=None,resources=report['resources'],
        failures=report['failures'],external_tail_acceptance_pending=True)


def main():
    launch,raw=gate(); output=HERE/'attempt01'; output.mkdir(exist_ok=False)
    target=output/'receipt.json'; save(target,dict(receipt_complete=False,passed=False))
    report=dict(policy=POLICY,passed=False,receipt_complete=False,failures=[],config_failure=False,
        source_revision=launch['source_revision'],launch_sha256=hashlib.sha256(raw).hexdigest(),source_sha256={},
        budgets=BUDGETS,tracking_prefix=launch['tracking_prefix'],numerical_resource_prefix=launch['numerical_resource_prefix'],
        preparation_accounting=launch['preparation_accounting'],
        admission=dict(task_id='A00',phase='admission',arm=None,institution=None,attempted=False,
            source_revision=launch['source_revision']),
        contexts=[dict(task_id=t,phase='context',arm=a,institution=i,attempted=False,
            source_revision=launch['source_revision']) for t,a,i in CONTEXTS])
    p=launch['preparation_accounting']; stopped=None; unresolved=0.; phase='preflight'; final_cpu=final_wall=None

    def stop(signum,frame):
        global DEFERRED_STOP
        nonlocal stopped
        stopped=stopped or signum
        if PUBLISHING_CHILD:
            DEFERRED_STOP=DEFERRED_STOP or signum; return
        raise TimeoutError('Latched owner stop '+str(signum))

    def check():
        if stopped is not None:
            raise TimeoutError('Owner stop remains latched')
        spend=cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s']+unresolved
        if threading.active_count()!=1 or rss()>5*1024**3 or spend>480 or time.monotonic()-START+p['elapsed_s']>900:
            report['config_failure']=True; raise ContractError('Owner thread/RSS/total resource bound')
        if (phase=='preflight' and spend>60 or phase=='finalization'
                and (cpu()-final_cpu>60 or time.monotonic()-final_wall>120)):
            report['config_failure']=True; raise ContractError('Combined preflight/finalization provision exceeded')

    def funded(cap,wall):
        return (cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s']+unresolved+cap<=420
            and time.monotonic()-START+p['elapsed_s']+wall+3+120<=900)

    try:
        for key in THREAD_ENV:
            os.environ[key]='1'
        resource.setrlimit(resource.RLIMIT_CPU,(60,480))
        for sig in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM,signal.SIGINT):
            signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,900-p['elapsed_s']-(time.monotonic()-START)))
        preflight(launch,report,check)
        if cpu()+p['charged_cpu_s']+45>60 or not funded(45,120):
            raise ContractError('Admission45CPU not funded inside unchanged combined preflight60')
        worker(report['admission'],None); unresolved+=report['admission']['unresolved_cpu_reserve_s']; check()
        if unresolved or any(report['admission'].get(f) for f in
                ('config_failure','fatal_contract','resource_violation','identity_failure')):
            raise ContractError('Fatal bank admission or unresolved owned admission child')
        packet=report['admission'].get('worker') or {}
        if (not report['admission'].get('admission_qualified') or packet.get('transfer_qualified') is not True):
            report['dispatch_stopped_reason']='Completed-admission transfer missing/late/failed; no owned bank authority'
        else:
            bank_sha=packet.get('prepared_bank_sha256'); bank_path=packet.get('prepared_bank_path')
            if (bank_sha!=PRIOR_BANK_SHA
                    or bank_path!=str(output/'000-admission/prepared-bank.json')):
                raise ContractError('Prepared-bank path/digest authority differs')
            common=packet.get('common_values')
            if (not isinstance(common,dict) or set(common)!={'posted','system','strategic'}
                    or any(not number(v) for v in common.values())):
                raise ContractError('Admitted common values absent/nonfinite; no operational fallback invented')
            report['common_values']=common; report['common_decompositions']=packet.get('common_decompositions')
            phase='dispatch'; resource.setrlimit(resource.RLIMIT_CPU,(480,480))
            for row in report['contexts']:
                check()
                if not funded(60,90):
                    report['dispatch_stopped_reason']='Next paid context not funded with closure'; break
                worker(row,bank_sha); unresolved+=row['unresolved_cpu_reserve_s']
                if unresolved or any(row.get(f) for f in ('config_failure','fatal_contract','resource_violation','identity_failure')):
                    report['config_failure']=True; report['dispatch_stopped_reason']='Fatal context/owned-child closure'; break
                check()
    except BaseException as exc:
        report['config_failure']=True
        report['failures'].append(dict(stage=phase,type=type(exc).__name__,message=str(exc)))
    finally:
        phase='finalization'; final_cpu=cpu(); final_wall=time.monotonic()
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(120.,900-p['elapsed_s']-(final_wall-START))))
        for row in [report['admission']]+report['contexts']:
            if not row.get('attempted'):
                row.setdefault('unattempted_reason',report.get('dispatch_stopped_reason','Owner/preflight failure'))
        report.update(receipt_complete=True,accounting_complete=unresolved==0,unresolved_cpu_reserve_s=unresolved,
            stop_signal=stopped,resources=dict(self_cpu_s=cpu(),waited_children_cpu_s=cpu(resource.RUSAGE_CHILDREN),
                preparation_charge_s=p['charged_cpu_s'],package_cpu_prepublication_s=cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s'],
                package_elapsed_sum_prepublication_s=time.monotonic()-START+p['elapsed_s'],observed_self_peak_rss_bytes=rss(),
                python_threads=threading.active_count(),task_deltas_not_added_twice=True,external_total_acceptance_pending=True),
            passed_scope='Administrative seven-state closure, not six successful deliveries or a pricing certificate')
        try:
            check()
        except BaseException as exc:
            report['config_failure']=True; report['failures'].append(dict(stage='final_resource_observation',type=type(exc).__name__,message=str(exc)))
        report['passed']=bool(not report['config_failure'] and not report['failures'] and report['accounting_complete'] and stopped is None)
        compact=readout(report)
        remaining=min(120-(time.monotonic()-final_wall),900-p['elapsed_s']-(time.monotonic()-START))
        if remaining<=0:
            raise TimeoutError('No final publication provision; master remains incomplete')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        publish(output/'READOUT.json',compact)
        with (output/'READOUT.md').open('x') as stream:
            stream.write('# Finite retained-bank admission reuse\n\nSix planned contexts; method-qualified and operational fallback contrasts remain separate.\n\n')
            stream.write('| Task | Attempted | Physical endpoint | Method-qualified | Operational retained value |\n|---|---:|---:|---:|---:|\n')
            for row in compact['contexts']:
                stream.write('| '+ ' | '.join(str(row[k]) for k in ('task_id','attempted','physical_endpoint_accepted','context_qualified','retained_value'))+' |\n')
            stream.write('\n```json\n'+json.dumps(compact,indent=2,allow_nan=False)+'\n```\n')
            stream.flush(); os.fsync(stream.fileno())
        check(); publish(target,report)
        print(json.dumps(dict(passed=report['passed'],paired_method_qualified_contrasts=compact['paired_method_qualified_contrasts'],
            paired_operational_fallback_contrasts=compact['paired_operational_fallback_contrasts'],resources=report['resources'],
            readout=str(output/'READOUT.md')),allow_nan=False),flush=True)
        check(); signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
