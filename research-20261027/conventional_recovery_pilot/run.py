"""Gated conventional recovery; adapted pricing_workload_pilot serial owner."""
import time
START = time.monotonic()
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

ROOT=Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE=ROOT/'research-20261027/conventional_recovery_pilot'
SIBLING=Path('/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001')
POLICY='conventional-recovery-owner-v1'
SEEDS=(62001,62002,62003,62004)
SIZES=(12,24)
PHASES=('F','N','D','UN','UD')
ARMS=dict(F='fixed_duty',N='full',D='full_dive',UN='union_n',UD='union_d')
ENV=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
    'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')
BUDGETS=dict(total_cpu_s=5100,total_wall_s=7800,dispatch_cpu_s=4800,dispatch_wall_s=7200,
    closure_cpu_s=300,closure_wall_s=600,
    preflight_cpu_s=120,preflight_wall_s=180,worker_cpu_s=120,worker_wall_s=180,
    native_cutoff_s=150,cleanup_s=3,unresolved_child_cpu_s=120,finalization_cpu_s=120,finalization_wall_s=180)
NATIVE=dict(oracle=dict(Threads=1,Method=1,MIPGap=0,Seed='unchanged_native_default',
    CG_nominal_s=50,MIP_nominal_s=dict(F=50,N=50,D=25),dive_nominal_s=dict(F=0,N=0,D=25),
    seeds=[],partition=True,batch_size=30,max_iters=100000,rc_eps=1e-6,viol_tol=1e-6,
    smoothing=0,dive_theta=.7,dive_mode='simple',partial_pricing=None,directional=False,
    integer_pricing_seconds=0),union=dict(Threads=1,Method=1,MIPGap=0,
    Seed='unchanged_native_default',nominal_s=100,optimize_calls=1),native_cutoff_s=150,
    parent_wall_s=180,hard_cpu_s=120,rss_bytes=5*1024**3)
LOCAL=(
    'research-20261027/conventional_recovery_pilot/run.py','research-20261027/conventional_recovery_pilot/prepare.py',
    'research-20261027/conventional_recovery_pilot/worker.py','research-20261027/conventional_recovery_pilot/fixture.py',
    'research-20261027/conventional_recovery_pilot/PROTOCOL.md','research-20261027/conventional_recovery_pilot/OWNER_NOTE.md',
    'research-20261027/conventional_recovery_pilot/WORKER_NOTE.md','research-20261027/conventional_recovery_pilot/FIXTURE_NOTE.md',
    'research-20261027/conventional_recovery_pilot/PREPARATION_LAUNCH.json',
    'research-20261027/conventional_recovery_pilot/FIELD_AUTHORITY.md',
    'research-20261026/pricing_workload_pilot/worker.py',
    'research-20261026/adjacent_nonlinear_design/column_contract.py',
    'research-20261026/adjacent_nonlinear_design/bank_master.py',
    'research-20261026/adjacent_oracle_boundary/boundary.py')
PUBLISHING_CHILD=False
DEFERRED_STOP=None


class ContractError(ValueError):
    pass


def cpu(who=resource.RUSAGE_SELF):
    u=resource.getrusage(who)
    return u.ru_utime+u.ru_stime


def rss():
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))


def finite(x,positive=False):
    return type(x) in (int,float) and math.isfinite(x) and x>(0 if positive else -math.inf)


def hex_string(x,length):
    return isinstance(x,str) and len(x)==length and all(c in '0123456789abcdef' for c in x)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def read_once(path,cap=8*1024**2):
    path=Path(path); before=path.stat()
    if path.is_symlink() or path.resolve()!=path or not path.is_file() or before.st_size>cap:
        raise ContractError('Exact bounded owned/control/source path required')
    with path.open('rb') as stream: raw=stream.read(cap+1)
    after=path.stat()
    if len(raw)!=before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
        raise ContractError('Consumed bytes changed during read')
    return raw


def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False,default=lambda v:str(v) if isinstance(v,Q) else v)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path,value):
    path=Path(path); temp=path.with_name(path.name+'.final.tmp')
    save(temp,value); os.replace(temp,path)


def assigned_sequences():
    result=[]
    for b,seed in enumerate(SEEDS,1):
        for s,n in enumerate(SIZES if b%2 else SIZES[::-1],1):
            order=['F']+(['N','D'] if (b+s)%2==0 else ['D','N'])+(['UN','UD'] if (b+s)%2==0 else ['UD','UN'])
            sequence=dict(base_seed=seed,services=n,base_ordinal=b,size_ordinal=s,dispatch_order=order)
            for phase in PHASES:
                sequence[phase]=dict(task_id=f'B{seed}-N{n}-{phase}',phase=phase,
                    base_seed=seed,services=n,arm=ARMS[phase],quote='source_shape',attempted=False)
            result.append(sequence)
    return result


def gate():
    raw=read_once(HERE/'LAUNCH.json'); launch=json.loads(raw)
    p=launch.get('preparation_accounting') or {}; limits=launch.get('preparation_limits') or {}
    if (Path(__file__).resolve()!=HERE/'run.py' or Path.cwd().resolve()!=ROOT
            or launch.get('mode')!='FROZEN' or launch.get('review_disposition')!='PASS'
            or launch.get('policy')!=POLICY or not hex_string(launch.get('source_revision'),40)
            or launch.get('workdir')!=str(ROOT) or not launch.get('command')
            or launch.get('source_freeze_assumption')!='parent-approved-frozen-commit'
            or not isinstance(launch.get('source_sha256'),dict) or launch.get('budgets')!=BUDGETS
            or launch.get('native_parameters')!=NATIVE or launch.get('environment')!={k:'1' for k in ENV}
            or launch.get('tracking_prefix') is None or launch.get('numerical_resource_prefix') is None
            or launch.get('data_authority')!={'external_inputs':[],'own_campaign_artifacts_only':True}
            or launch.get('base_seeds')!=list(SEEDS) or launch.get('sizes')!=list(SIZES)
            or launch.get('start_fee')!=0 or launch.get('clean_argv')!=['--start-fee','0']
            or launch.get('sibling_source_root')!=str(SIBLING)
            or launch.get('sibling_source_revision')!='3a0ab6a8ab50e4af7d5a7be7688d5ffa1fbbf78c'
            or p.get('external_accepted') is not True or not finite(p.get('charged_cpu_s'))
            or not finite(p.get('elapsed_s')) or limits!={'cpu_s':10,'wall_s':20,'body_cpu_s':6,'body_wall_s':15}
            or not 0<=p['charged_cpu_s']<=10 or not 0<=p['elapsed_s']<=20):
        raise SystemExit('DRAFT/PENDING: generation, artifact input and dispatch denied')
    return launch,raw


def preflight(launch,report,check):
    closure=launch.get('source_closure') or {}; paths=closure.get('sibling_python_paths')
    if (closure.get('roots')!=['run_capacity_terminal_cg'] or not isinstance(paths,list) or not paths
            or len(paths)>192 or len(set(paths))!=len(paths) or any(
                not Path(p).is_relative_to(SIBLING/'src') or Path(p).suffix!='.py' for p in paths)):
        raise ContractError('Frozen registered import closure required')
    names={str(ROOT/p) for p in LOCAL}|set(paths)
    if set(launch['source_sha256'])!=names: raise ContractError('Source inventory differs')
    for path in sorted(names):
        check(); sha=hashlib.sha256(read_once(path,2*1024**2)).hexdigest()
        report['source_sha256'][path]=sha
        if sha!=launch['source_sha256'][path]: raise ContractError('Source integrity mismatch: '+path)
    spec=importlib.util.spec_from_file_location('pricing_workload_literal_fixture',HERE/'fixture.py')
    fixture=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    descriptors={}; hashes={}; aliases={}; nested_pairs=[]; parent={seed:seed for seed in SEEDS}
    def find(seed):
        while parent[seed]!=seed: seed=parent[seed]
        return seed
    for seed in SEEDS:
        for n in SIZES:
            for quote in ('source_shape',):
                check(); descriptor=fixture.make_descriptor(seed,n,quote); key=f'{seed}:{n}:{quote}'
                descriptors[key]=descriptor; hashes[key]=hashlib.sha256(canonical(descriptor)).hexdigest()
                alias=fixture.physical_alias(descriptor)
                if not isinstance(alias,str): raise ContractError('Canonical physical alias must be a string')
                if (seed,n) in aliases and aliases[seed,n]!=alias:
                    raise ContractError('Quotes changed a physical descriptor')
                aliases[seed,n]=alias
            for earlier in SEEDS:
                if earlier<seed and aliases.get((earlier,n))==aliases[seed,n]: parent[find(seed)]=find(earlier)
        for quote in ('source_shape',):
            if fixture.assert_nested(descriptors[f'{seed}:12:{quote}'],descriptors[f'{seed}:24:{quote}']) is not True:
                raise ContractError('Declared 12/24 prefix contract failed')
            nested_pairs.append(dict(base_seed=seed,quote=quote,small_services=12,large_services=24,validated=True))
    clusters={}
    for seed in SEEDS: clusters.setdefault(str(find(seed)),[]).append(seed)
    report.update(descriptors=descriptors,descriptor_sha256=hashes,nested_pairs=nested_pairs,alias_groups=list(clusters.values()),
        distinct_group_clusters=len(clusters),preflight_admitted=True)
    save(HERE/'attempt01/preflight.json',dict(descriptors=descriptors,descriptor_sha256=hashes,
        physical_aliases={f'{s}:{n}':v for (s,n),v in aliases.items()},alias_groups=report['alias_groups'],
        nested_pairs=nested_pairs,sequences=report['sequences'],source_sha256=report['source_sha256']))
    check()


def dependency(row):
    packet=row.get('worker') or {}
    return dict(folder=row['folder'],spec_sha256=row['spec_sha256'],
        receipt_sha256=row['worker_receipt_sha256'],selected_sha256=packet.get('selected_sha256'),
        bank_sha256=packet.get('bank_sha256'),strict_delivery=row.get('strict_delivery',False),
        physical_valid=row.get('physical_endpoint_accepted',False),bank_qualified=row.get('bank_qualified',False))


def run_worker(row,dependencies):
    global PUBLISHING_CHILD
    started=time.monotonic(); old_self=cpu(); old_child=cpu(resource.RUSAGE_CHILDREN)
    folder=HERE/'attempt01'/row['task_id']; folder.mkdir(exist_ok=False)
    spec={k:row[k] for k in ('task_id','phase','base_seed','services','arm','quote','descriptor_sha256')}
    spec['dependencies']={name:dependency(prior) for name,prior in dependencies.items()}
    raw=(json.dumps(spec,indent=2,allow_nan=False)+'\n').encode(); sha=hashlib.sha256(raw).hexdigest()
    with (folder/'spec.json').open('xb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    save(folder/'receipt.json',dict(receipt_complete=False))
    row.update(attempted=False,reaped=False,folder=str(folder),spec_sha256=sha,failures=[],config_failure=False)
    child=None; packet={}; cleanup_end=None; anchor=time.monotonic(); row['parent_anchor']=anchor
    with (folder/'stdout.txt').open('x') as out,(folder/'stderr.txt').open('x') as err:
        try:
            PUBLISHING_CHILD=True
            try:
                child=subprocess.Popen([str(ROOT/'.venv-local/bin/python'),'-B',str(HERE/'worker.py'),
                    '--worker',str(folder),'--parent-anchor',repr(anchor),'--spec-sha256',sha],cwd=ROOT,
                    env=dict(os.environ),stdout=out,stderr=err,start_new_session=True,
                    preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CPU,(120,120)))
                row.update(attempted=True,pid=child.pid)
            finally: PUBLISHING_CHILD=False
            if DEFERRED_STOP is not None: raise TimeoutError('Deferred stop after owned PID registration')
            try: child.wait(timeout=max(.001,anchor+180-time.monotonic()))
            except subprocess.TimeoutExpired:
                row['timed_out']=True; cleanup_end=time.monotonic()+3; child.terminate()
                try: child.wait(timeout=min(1.,max(.001,cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001,cleanup_end-time.monotonic()))
            row.update(reaped=True,returncode=child.returncode)
        except BaseException as exc:
            row['failures'].append(dict(stage='process',type=type(exc).__name__,message=str(exc)))
            if child is None: row['config_failure']=True
            elif child.returncode is None:
                try:
                    cleanup_end=cleanup_end or time.monotonic()+3
                    child.kill(); child.wait(timeout=max(.001,cleanup_end-time.monotonic()))
                    row.update(reaped=True,returncode=child.returncode)
                except BaseException as secondary:
                    row['failures'].append(dict(stage='cleanup',type=type(secondary).__name__,message=str(secondary)))
    row['process_return_elapsed_s']=time.monotonic()-anchor
    try:
        raw_packet=read_once(folder/'receipt.json'); row['worker_receipt_sha256']=hashlib.sha256(raw_packet).hexdigest()
        packet=json.loads(raw_packet)
        if packet.get('receipt_complete') is True and any(packet.get(k)!=row[k] for k in
                ('task_id','phase','base_seed','services','arm','quote','source_revision','descriptor_sha256')):
            raise ContractError('Complete packet task/source/descriptor binding differs')
    except BaseException as exc:
        row['config_failure']=True; row['failures'].append(dict(stage='complete_packet',type=type(exc).__name__,message=str(exc)))
    # Admission includes the complete packet read; telemetry publication is owner overhead.
    now=time.monotonic(); usage=packet.get('resources') or {}
    row.update(worker=packet,parent_elapsed_s=now-anchor,method_late=now>anchor+180,
        stage_elapsed_s=now-started,parent_cpu_s=cpu()-old_self,waited_child_cpu_s=cpu(resource.RUSAGE_CHILDREN)-old_child,
        cpu_observation_complete=child is None or row['reaped'],unresolved_cpu_reserve_s=120. if child and not row['reaped'] else 0.)
    flags=('config_failure','fatal_contract','resource_violation','identity_failure')
    for flag in flags: row[flag]=bool(row.get(flag) or packet.get(flag))
    if packet.get('receipt_complete') is True and (not finite(usage.get('peak_rss_bytes'))
            or not 0<=usage['peak_rss_bytes']<=5*1024**3 or usage.get('python_threads')!=1):
        row['resource_violation']=row['config_failure']=True
    row['worker_cpu_observed_s']=usage.get('cpu_s')
    row['waited_cpu_at_or_above_cap']=row['waited_child_cpu_s']>=120
    row['worker_cpu_at_or_above_cap']=bool(finite(usage.get('cpu_s')) and usage['cpu_s']>=120)
    if ((packet.get('receipt_complete') is True and (not finite(usage.get('cpu_s')) or usage['cpu_s']<0))
            or row['waited_cpu_at_or_above_cap'] or row['worker_cpu_at_or_above_cap']):
        row['resource_violation']=row['config_failure']=True
    admin=bool(row['reaped'] and row.get('returncode')==0 and not row.get('timed_out') and not row['method_late']
        and not row['failures'] and packet.get('receipt_complete') is True and not any(row.get(f) for f in flags))
    physical=bool(admin and packet.get('physical_valid') is True and packet.get('method_endpoint_accepted') is True)
    if physical and (not finite(packet.get('retained_value')) or not hex_string(packet.get('selected_sha256'),64)):
        row['config_failure']=True; physical=False; admin=False
    row.update(administrative_packet_accepted=admin,physical_endpoint_accepted=physical,
        strict_delivery=bool(physical and packet.get('strict_delivery') is True),
        bank_qualified=bool(admin and row['phase'] in ('F','N','D') and packet.get('bank_qualified') is True
            and hex_string(packet.get('bank_sha256'),64)),
        native_optimal=bool(physical and packet.get('native_optimal') is True))
    row.update(prepublication_snapshot=True,stage_telemetry_scope='Before external-receipt publication')
    save(folder/'external-receipt.json',row)
    # One external save only. Master/readout pipeline costs include that paid publication.
    row.update(parent_cpu_s=cpu()-old_self,waited_child_cpu_s=cpu(resource.RUSAGE_CHILDREN)-old_child,
        stage_elapsed_s=time.monotonic()-started,prepublication_snapshot=False,
        stage_telemetry_scope='After external-receipt publication; authoritative stage costs')


def ratio(cost_control,cost_method,denominator):
    if not all(finite(x) for x in (cost_control,cost_method)) or not finite(denominator,True): return None
    return (Q(cost_control)-Q(cost_method))/Q(denominator)


def compact_and_screens(report):
    cells=[]; lookup={}; pipelines={}
    for seq in report['sequences']:
        common=seq['F']; common_packet=common.get('worker') or {}
        fallback=common_packet.get('retained_value') if common.get('physical_endpoint_accepted') else None
        E=common_packet.get('target_common_grid_electricity') if common.get('physical_endpoint_accepted') else None
        for phase in PHASES:
            row=seq[phase]; packet=row.get('worker') or {}
            accepted=bool(row.get('physical_endpoint_accepted'))
            strict=bool(accepted and row.get('strict_delivery'))
            qualified=bool(strict and (phase not in ('UN','UD') or row.get('native_optimal')))
            operational=packet.get('retained_value') if accepted else fallback
            cell=dict(task_id=row['task_id'],base_seed=seq['base_seed'],services=seq['services'],phase=phase,
                attempted=row.get('attempted',False),strict_delivery=strict,method_qualified=qualified,
                physical_endpoint_accepted=accepted,bank_qualified=row.get('bank_qualified',False),
                native_optimal=row.get('native_optimal',False),method_value=packet.get('retained_value') if qualified else None,
                operational_value=operational,operational_source='worker_retained' if accepted else
                    'own_F_fallback' if fallback is not None else 'missing',target_common_grid_electricity=E,
                bank_raw_columns=packet.get('bank_raw_columns'),bank_unique_physical_witnesses=packet.get('bank_unique_physical_witnesses'),
                status=packet.get('status'),failures=row.get('failures',[])+packet.get('failures',[]),
                method_late=row.get('method_late'),unattempted_reason=row.get('unattempted_reason'),
                cheap_joint_completion_reaches_finite_bank_optimum=bool(qualified) if phase in ('UN','UD') else None)
            cells.append(cell); lookup[seq['base_seed'],seq['services'],phase]=cell
        seq['pipeline_costs']={}
        for label,names in (('F+N+UN',('F','N','UN')),('F+D+UD',('F','D','UD'))):
            rows=[seq[name] for name in names]
            complete=all(r.get('attempted') and r.get('cpu_observation_complete') and
                all(k in r for k in ('parent_cpu_s','waited_child_cpu_s','stage_elapsed_s')) for r in rows)
            seq['pipeline_costs'][label]=dict(complete=complete,
                cpu_s=sum(r['parent_cpu_s']+r['waited_child_cpu_s'] for r in rows) if complete else None,
                elapsed_stage_sum_s=sum(r['stage_elapsed_s'] for r in rows) if complete else None,
                scope='F and each acquisition paid exactly once in this counterfactual pipeline; common preparation/preflight separate')
    comparisons={}
    for method,control in (('UN','F'),('UD','F'),('UD','UN')):
        pairs=[]; groups={}
        for seed in SEEDS:
            group=[]; opgroup=[]
            for n in SIZES:
                m=lookup[seed,n,method]; c=lookup[seed,n,control]; E=lookup[seed,n,'F']['target_common_grid_electricity']
                strict=ratio(c['method_value'],m['method_value'],E)
                operational=ratio(c['operational_value'],m['operational_value'],E)
                pairs.append(dict(base_seed=seed,services=n,strict_ratio=strict,operational_ratio=operational))
                group.append(strict); opgroup.append(operational)
            groups[str(seed)]=dict(mean_12_24=None if any(x is None for x in group) else sum(group,Q(0))/2,
                operational_mean_12_24=None if any(x is None for x in opgroup) else sum(opgroup,Q(0))/2)
        stricts=[p['strict_ratio'] for p in pairs]; ops=[p['operational_ratio'] for p in pairs]
        comparisons[method+'_vs_'+control]=dict(planned_pairs=8,defined_strict_pairs=sum(x is not None for x in stricts),
            defined_operational_pairs=sum(x is not None for x in ops),pairs=pairs,group_means=groups,
            full_eight_mean=None if any(x is None for x in stricts) else sum(stricts,Q(0))/8,
            operational_full_eight_mean=None if any(x is None for x in ops) else sum(ops,Q(0))/8,
            available_only_mean=None,denominator='Own F source_shape grid electricity, finite and positive')
    coverage={}
    for seed in SEEDS:
        coverage[str(seed)]={phase:dict(planned=2,
            strict=sum(lookup[seed,n,phase]['strict_delivery'] for n in SIZES),
            operational=sum(lookup[seed,n,phase]['operational_value'] is not None for n in SIZES),
            native_optimal=sum(lookup[seed,n,phase]['native_optimal'] for n in SIZES),
            qualified_bank=sum(lookup[seed,n,phase]['bank_qualified'] for n in SIZES)) for phase in PHASES}
    for label in ('F+N+UN','F+D+UD'):
        rows=[seq['pipeline_costs'][label] for seq in report['sequences']]
        complete=all(r['complete'] for r in rows); prefix=report.get('common_preflight') or {}
        pipelines[label]=dict(complete=complete,planned_sequences=8,
            cpu_s=sum(r['cpu_s'] for r in rows)+prefix.get('cpu_s',0) if complete else None,
            elapsed_stage_sum_s=sum(r['elapsed_stage_sum_s'] for r in rows)+prefix.get('elapsed_s',0) if complete else None,
            scope='Counterfactual stage sums plus shared preparation/preflight once; distinct from physical campaign total')
    return dict(policy=POLICY,passed=report['passed'],planned_states=40,recorded_states=len(cells),cells=cells,
        group_coverage=coverage,comparisons=comparisons,sequences=report['sequences'],
        alias_groups=report.get('alias_groups'),distinct_group_clusters=report.get('distinct_group_clusters'),
        counterfactual_pipeline_totals=pipelines,common_preflight=report.get('common_preflight'),
        physical_campaign_resources=report['resources'],failures=report['failures'],
        ML_promotion_authorized=False,automatic_job_authorized=False,
        interpretation='Minimal conventional recovery study; broader candidate-rich, stabilized and random controls absent. Not the full NEXT_EXPERIMENT gate, a novelty claim, V2G result or nonlinear result.')


def markdown(readout):
    lines=['# Conventional recovery pilot','',readout['interpretation'],'',
        'All 40 planned states are retained, including unattempted and missing outcomes. Strict methods and operational fallback coverage remain separate.','',
        '| Group | Phase | Strict / 2 | Operational / 2 | Native optimal / 2 | Qualified banks / 2 |',
        '|---|---|---:|---:|---:|---:|']
    for seed,phases in readout['group_coverage'].items():
        for phase,c in phases.items():
            lines.append(f"| {seed} | {phase} | {c['strict']} | {c['operational']} | {c['native_optimal']} | {c['qualified_bank']} |")
    lines += ['', '| Comparison | Strict pairs / 8 | Full eight mean | Operational full eight mean |', '|---|---:|---:|---:|']
    for name,c in readout['comparisons'].items():
        lines.append(f"| {name} | {c['defined_strict_pairs']} | {c['full_eight_mean']} | {c['operational_full_eight_mean']} |")
        for seed,g in c['group_means'].items():
            lines.append(f"| {name}, group {seed} 12/24 mean | — | {g['mean_12_24']} | {g['operational_mean_12_24']} |")
    lines += ['', 'Ratios use each cell’s own positive finite F grid electricity. A full-eight mean is null if any planned pair is missing.','',
        '| Task | Attempted | Strict | Operational source | Finite-bank optimum reached | Status / failures / missing reason |',
        '|---|---|---|---|---|---|']
    for c in readout['cells']:
        reason=json.dumps(dict(status=c['status'],failures=c['failures'],unattempted_reason=c['unattempted_reason']),allow_nan=False).replace('|','/')
        lines.append(f"| {c['task_id']} | {c['attempted']} | {c['strict_delivery']} | {c['operational_source']} | {c['cheap_joint_completion_reaches_finite_bank_optimum']} | {reason} |")
    lines += ['', '| Pipeline | Complete | CPU seconds | Elapsed stage sum seconds |', '|---|---|---:|---:|']
    for name,p in readout['counterfactual_pipeline_totals'].items():
        lines.append(f"| {name} | {p['complete']} | {p['cpu_s']} | {p['elapsed_stage_sum_s']} |")
    lines += ['', 'Each pipeline pays F and its acquisition once; common preparation/preflight is added once. Physical campaign totals charge all executed work once.',
        '', 'Physical campaign resources: '+json.dumps(readout['physical_campaign_resources'],allow_nan=False),
        '', 'Owner failures: '+json.dumps(readout['failures'],allow_nan=False),'']
    return '\n'.join(lines)


def main():
    launch,raw=gate(); output=HERE/'attempt01'; output.mkdir(exist_ok=False)
    target=output/'receipt.json'; save(target,dict(receipt_complete=False,passed=False))
    report=dict(policy=POLICY,passed=False,receipt_complete=False,config_failure=False,failures=[],
        source_revision=launch['source_revision'],launch_sha256=hashlib.sha256(raw).hexdigest(),source_sha256={},
        budgets=BUDGETS,tracking_prefix=launch['tracking_prefix'],numerical_resource_prefix=launch['numerical_resource_prefix'],
        preparation_accounting=launch['preparation_accounting'],sequences=assigned_sequences())
    for seq in report['sequences']:
        for phase in PHASES: seq[phase]['source_revision']=launch['source_revision']
    p=launch['preparation_accounting']; stopped=None; unresolved=0.; phase='preflight'
    final_cpu=final_wall=dispatch_cpu=dispatch_wall=None

    def stop(signum,frame):
        global DEFERRED_STOP
        nonlocal stopped
        stopped=stopped or signum
        if PUBLISHING_CHILD: DEFERRED_STOP=DEFERRED_STOP or signum; return
        raise TimeoutError('Latched owner stop '+str(signum))

    def spent(): return cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s']+unresolved
    def elapsed(): return time.monotonic()-START+p['elapsed_s']
    def check():
        if stopped is not None: raise TimeoutError('Owner stop remains latched')
        if threading.active_count()!=1 or rss()>5*1024**3 or spent()>5100 or elapsed()>7800:
            report['config_failure']=True; raise ContractError('Total resource/thread/RSS bound')
        if (phase=='preflight' and (spent()>120 or elapsed()>180)
                or phase=='dispatch' and (spent()-dispatch_cpu>4800 or time.monotonic()-dispatch_wall>7200)
                or phase=='finalization' and (cpu()-final_cpu>120 or time.monotonic()-final_wall>180
                    or report.get('common_preflight',{}).get('cpu_s',0)+cpu()-final_cpu>300
                    or report.get('common_preflight',{}).get('elapsed_s',0)+time.monotonic()-final_wall>600)):
            report['config_failure']=True; raise ContractError('Frozen phase provision exceeded')

    try:
        for key in ENV: os.environ[key]='1'
        resource.setrlimit(resource.RLIMIT_CPU,(120,5100))
        for sig in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM,signal.SIGINT): signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,180-elapsed()))
        preflight(launch,report,check)
        report['common_preflight']=dict(cpu_s=spent(),elapsed_s=elapsed())
        phase='dispatch'; dispatch_cpu=spent(); dispatch_wall=time.monotonic()
        resource.setrlimit(resource.RLIMIT_CPU,(5100,5100))
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(7200,7800-elapsed()-180)))
        for seq in report['sequences']:
            for name in seq['dispatch_order']:
                row=seq[name]; check(); dependencies={}
                row['descriptor_sha256']=report['descriptor_sha256'][f"{row['base_seed']}:{row['services']}:source_shape"]
                if name in ('N','D') and seq['F'].get('physical_endpoint_accepted'): dependencies={'F':seq['F']}
                if name in ('UN','UD'):
                    acquisition='N' if name=='UN' else 'D'
                    if not seq['F'].get('physical_endpoint_accepted') or not all(seq[k].get('bank_qualified') for k in ('F',acquisition)):
                        row['unattempted_reason']='Requires own timely admitted F common fleet and qualified complete F/'+acquisition+' banks'; continue
                    dependencies={'F':seq['F'],acquisition:seq[acquisition]}
                if (spent()-dispatch_cpu+120>4800 or time.monotonic()-dispatch_wall+183>7200
                        or spent()+120+120>5100 or elapsed()+183+180>7800):
                    report['dispatch_stopped_reason']='Whole next stage, cleanup and finalization not funded'; break
                run_worker(row,dependencies); unresolved+=row['unresolved_cpu_reserve_s']
                if unresolved or any(row.get(f) for f in ('config_failure','fatal_contract','resource_violation','identity_failure')):
                    report['config_failure']=True; report['dispatch_stopped_reason']='Fatal stage or unresolved owned child'; break
                check()
            if report.get('dispatch_stopped_reason'): break
    except BaseException as exc:
        report['config_failure']=True; report['failures'].append(dict(stage=phase,type=type(exc).__name__,message=str(exc)))
    finally:
        phase='finalization'; final_cpu=cpu(); final_wall=time.monotonic()
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(180.,7800-elapsed())))
        for seq in report['sequences']:
            for name in PHASES:
                if not seq[name].get('attempted'): seq[name].setdefault('unattempted_reason',report.get('dispatch_stopped_reason','Owner/preflight failure'))
        report.update(receipt_complete=True,accounting_complete=unresolved==0,unresolved_cpu_reserve_s=unresolved,stop_signal=stopped,
            resources=dict(self_cpu_s=cpu(),waited_children_cpu_s=cpu(resource.RUSAGE_CHILDREN),preparation_charge_s=p['charged_cpu_s'],
                package_cpu_prepublication_s=cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s'],
                conservative_cpu_with_unresolved_reserve_s=spent(),package_elapsed_sum_prepublication_s=elapsed(),
                cumulative_retained_research_cpu_prepublication_s=20268.40+cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s'],
                cumulative_research_wall_elapsed_sum_prepublication_s=20889.24+elapsed(),
                legacy_excluded_cpu_s=2546.091499549272,source_review_cpu_s='UNKNOWN',
                observed_self_peak_rss_bytes=rss(),python_threads=threading.active_count(),
                task_deltas_not_added_twice=True,external_total_acceptance_pending=True))
        try: check()
        except BaseException as exc:
            report['config_failure']=True; report['failures'].append(dict(stage='final_resource',type=type(exc).__name__,message=str(exc)))
        report['passed']=bool(not report['config_failure'] and not report['failures'] and report['accounting_complete'] and stopped is None)
        readout=compact_and_screens(report)
        remaining=min(180-(time.monotonic()-final_wall),7800-elapsed())
        if remaining<=0: raise TimeoutError('Publication provision exhausted; master remains incomplete')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        publish(output/'READOUT.json',readout)
        with (output/'READOUT.md').open('x') as stream:
            stream.write(markdown(readout)); stream.flush(); os.fsync(stream.fileno())
        check(); publish(target,report)
        print(json.dumps(dict(passed=report['passed'],readout=str(output/'READOUT.md'),resources=report['resources']),allow_nan=False),flush=True)
        check(); signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
