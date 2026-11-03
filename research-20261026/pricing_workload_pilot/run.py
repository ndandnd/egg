"""Gated serial A0/F1/C1 pricing workload; no generation before admission."""
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
from statistics import median
import subprocess
import sys
import threading

ROOT=Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE=ROOT/'research-20261026/pricing_workload_pilot'
SIBLING=Path('/Users/nadan/Documents/projects/demandresponse/.codex-work/capacity-packed-20261001')
POLICY='independent-pricing-workload-owner-v1'
SEEDS=(61001,61002,61003,61004)
SIZES=(12,24)
ENV=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
    'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','SLURM_CPUS_PER_TASK')
BUDGETS=dict(total_cpu_s=7200,total_wall_s=10800,dispatch_cpu_s=6600,closure_cpu_s=600,
    preflight_cpu_s=120,preflight_wall_s=180,worker_cpu_s=120,worker_wall_s=180,
    native_cutoff_s=150,cleanup_s=3,unresolved_child_cpu_s=120,finalization_cpu_s=120,finalization_wall_s=180)
NATIVE=dict(oracle=dict(Threads=1,Method=1,MIPGap=0,Seed='unchanged_native_default',
    CG_nominal_s=50,MIP_nominal_s=50,seeds=[],partition=True,batch_size=30,max_iters=100000,
    rc_eps=1e-6,viol_tol=1e-6,smoothing=0,dive_seconds=0,partial_pricing=None,directional=False,
    integer_pricing_seconds=0),cache=dict(Threads=1,Method=1,MIPGap=0,
    Seed='unchanged_native_default',nominal_s=100))
LOCAL=(
    'research-20261026/pricing_workload_pilot/run.py','research-20261026/pricing_workload_pilot/prepare.py',
    'research-20261026/pricing_workload_pilot/worker.py','research-20261026/pricing_workload_pilot/fixture.py',
    'research-20261026/pricing_workload_pilot/PROTOCOL.md','research-20261026/pricing_workload_pilot/OWNER_NOTE.md',
    'research-20261026/pricing_workload_pilot/WORKER_NOTE.md','research-20261026/pricing_workload_pilot/FIXTURE_NOTE.md',
    'research-20261026/pricing_workload_pilot/PREPARATION_LAUNCH.json',
    'research-20261026/pricing_workload_pilot/FIELD_AUTHORITY.md',
    'research-20261026/adjacent_nonlinear_design/column_contract.py',
    'research-20261026/adjacent_nonlinear_design/bank_master.py',
    'research-20261026/adjacent_oracle_boundary/boundary.py',
    'research-20261026/pricing_workload_design/STUDY_DESIGN.md',
    'research-20261026/pricing_workload_design/SYNTHETIC_SPEC.md')
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
            for a,arm in enumerate(('fixed_duty','full') if b%2 else ('full','fixed_duty'),1):
                order=['A0']+(['F1','C1'] if (b+s+a)%2==0 else ['C1','F1'])
                sequence=dict(base_seed=seed,services=n,arm=arm,base_ordinal=b,
                    size_ordinal=s,restriction_ordinal=a,dispatch_order=order)
                for phase in ('A0','F1','C1'):
                    sequence[phase]=dict(task_id=f'B{seed}-N{n}-{arm}-{phase}',phase=phase,
                        base_seed=seed,services=n,arm=arm,quote='flat' if phase=='A0' else 'source_shape',attempted=False)
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
            or not finite(p.get('elapsed_s')) or not 0<=p['charged_cpu_s']<=limits.get('cpu_s',-1)<=120
            or not 0<=p['elapsed_s']<=limits.get('wall_s',-1)<=180):
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
    descriptors={}; hashes={}; aliases={}; parent={seed:seed for seed in SEEDS}
    def find(seed):
        while parent[seed]!=seed: seed=parent[seed]
        return seed
    for seed in SEEDS:
        for n in SIZES:
            for quote in ('flat','source_shape'):
                check(); descriptor=fixture.make_descriptor(seed,n,quote); key=f'{seed}:{n}:{quote}'
                descriptors[key]=descriptor; hashes[key]=hashlib.sha256(canonical(descriptor)).hexdigest()
                alias=fixture.physical_alias(descriptor)
                if not isinstance(alias,str): raise ContractError('Canonical physical alias must be a string')
                if (seed,n) in aliases and aliases[seed,n]!=alias:
                    raise ContractError('Quotes changed a physical descriptor')
                aliases[seed,n]=alias
            for earlier in SEEDS:
                if earlier<seed and aliases.get((earlier,n))==aliases[seed,n]: parent[find(seed)]=find(earlier)
        for quote in ('flat','source_shape'):
            if fixture.assert_nested(descriptors[f'{seed}:12:{quote}'],descriptors[f'{seed}:24:{quote}']) is not True:
                raise ContractError('Declared 12/24 prefix contract failed')
    clusters={}
    for seed in SEEDS: clusters.setdefault(str(find(seed)),[]).append(seed)
    report.update(descriptors=descriptors,descriptor_sha256=hashes,alias_groups=list(clusters.values()),
        distinct_group_clusters=len(clusters),preflight_admitted=True)
    save(HERE/'attempt01/preflight.json',dict(descriptors=descriptors,descriptor_sha256=hashes,
        physical_aliases={f'{s}:{n}':v for (s,n),v in aliases.items()},alias_groups=report['alias_groups'],
        sequences=report['sequences'],source_sha256=report['source_sha256']))
    check()


def run_worker(row,a0):
    global PUBLISHING_CHILD
    started=time.monotonic(); old_self=cpu(); old_child=cpu(resource.RUSAGE_CHILDREN)
    folder=HERE/'attempt01'/row['task_id']; folder.mkdir(exist_ok=False)
    spec={k:row[k] for k in ('task_id','phase','base_seed','services','arm','quote','descriptor_sha256')}
    common=bool(a0 and a0.get('physical_endpoint_accepted'))
    spec.update(a0_folder=a0['folder'] if common else None,
        a0_receipt_sha256=a0['worker_receipt_sha256'] if common else None,
        a0_spec_sha256=a0['spec_sha256'] if common else None,
        a0_selected_sha256=a0['worker']['selected_sha256'] if common else None,
        a0_bank_sha256=a0['worker'].get('bank_sha256') if common and a0.get('bank_qualified') else None)
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
        bank_qualified=bool(physical and row['phase']=='A0' and packet.get('bank_qualified') is True
            and hex_string(packet.get('bank_sha256'),64)),
        native_optimal=bool(physical and packet.get('native_optimal') is True))
    save(folder/'external-receipt.json',row)


def ratio(cost_control,cost_method,denominator):
    if not all(finite(x) for x in (cost_control,cost_method)) or not finite(denominator,True): return None
    return (Q(cost_control)-Q(cost_method))/Q(denominator)


def compact_and_screens(report):
    cells=[]; lookup={}; methods_ready=True; unknown=[]
    for seq in report['sequences']:
        a0=seq['A0']; acquisition=bool(a0.get('physical_endpoint_accepted'))
        prior=a0.get('worker') or {}; common=prior.get('target_common_value') if acquisition else None
        E=prior.get('target_common_grid_electricity') if acquisition else None
        for phase in ('A0','F1','C1'):
            row=seq[phase]; packet=row.get('worker') or {}
            if phase=='A0': operational=packet.get('retained_value') if acquisition else None
            else: operational=packet.get('retained_value') if row.get('physical_endpoint_accepted') else common
            qualified=bool(row.get('physical_endpoint_accepted') and (phase=='A0' and row.get('strict_delivery') or
                phase=='F1' and row.get('strict_delivery') or phase=='C1' and row.get('strict_delivery') and row.get('native_optimal')))
            cell=dict(task_id=row['task_id'],base_seed=seq['base_seed'],services=seq['services'],arm=seq['arm'],phase=phase,
                attempted=row.get('attempted',False),parent_elapsed_s=row.get('parent_elapsed_s'),
                stage_elapsed_s=row.get('stage_elapsed_s'),administrative_packet_accepted=row.get('administrative_packet_accepted',False),
                physical_endpoint_accepted=row.get('physical_endpoint_accepted',False),method_qualified=qualified,
                strict_delivery=row.get('strict_delivery',False),native_optimal=row.get('native_optimal',False),
                bank_qualified=row.get('bank_qualified',False),operational_value=operational,
                operational_source='worker_retained' if row.get('physical_endpoint_accepted') else
                    'admitted_A0_target_fallback' if phase!='A0' and common is not None else 'missing',
                method_value=packet.get('retained_value') if qualified else None,
                target_common_grid_electricity=E,worker=packet,failures=row.get('failures',[]),
                unattempted_reason=row.get('unattempted_reason'),method_late=row.get('method_late'))
            cells.append(cell); lookup[seq['base_seed'],seq['services'],seq['arm'],phase]=cell
            methods_ready=methods_ready and qualified
        f1,c1=seq['F1'],seq['C1']
        seq['pipeline_costs']={phase:dict(cpu_s=None if not all(key in row for row in (a0,seq[phase])
                for key in ('parent_cpu_s','waited_child_cpu_s')) else
                a0['parent_cpu_s']+a0['waited_child_cpu_s']+seq[phase]['parent_cpu_s']+seq[phase]['waited_child_cpu_s'],
            elapsed_stage_sum_s=None if 'stage_elapsed_s' not in a0 or 'stage_elapsed_s' not in seq[phase] else
                a0['stage_elapsed_s']+seq[phase]['stage_elapsed_s'],
            uninterrupted_elapsed_s=None if 'parent_anchor' not in a0 or 'parent_elapsed_s' not in seq[phase] else
                seq[phase]['parent_anchor']+seq[phase]['parent_elapsed_s']-a0['parent_anchor'],
            scope='Observed stage-sum telemetry; A0 once per counterfactual branch. Common preflight overhead separate; uninterrupted second branch includes intervening work') for phase in ('F1','C1')}

    def value_screen(arm,control_arm,control_phase):
        values=[]; groups={}; pairs=[]
        for seed in SEEDS:
            group=[]
            for n in SIZES:
                method=lookup[seed,n,arm,'F1']; control=lookup[seed,n,control_arm,control_phase]
                d=ratio(control['method_value'],method['method_value'],method['target_common_grid_electricity'])
                op=ratio(control['operational_value'],method['operational_value'],method['target_common_grid_electricity'])
                values.append(d); group.append(d); pairs.append(dict(base_seed=seed,services=n,
                    method=arm+'_F1',control=control_arm+'_'+control_phase,ratio=d,operational_fallback_ratio=op))
            groups[str(seed)]=None if any(v is None for v in group) else median(group)
        complete=all(v is not None for v in values); mean=sum(values,Q(0))/8 if complete else None
        positives=sum(v is not None and v>0 for v in groups.values())
        return dict(planned_pairs=8,defined_pairs=sum(v is not None for v in values),pairs=pairs,
            group_medians=groups,positive_groups=positives,mean_of_eight_ratios=mean,
            passed=bool(complete and positives>=3 and mean>Q(1,100)),available_only_mean=None)

    def effort(arm):
        groups={}; passed=0; complete=True
        for seed in SEEDS:
            walls=[]; shares=[]
            for n in SIZES:
                c=lookup[seed,n,arm,'F1']; w=(c['worker'].get('timings') or {}).get('pricing_event_wall_s'); elapsed=c['stage_elapsed_s']
                valid=finite(w) and finite(elapsed,True) and 0<=w<=elapsed
                walls.append(w if valid else None); shares.append(w/elapsed if valid else None)
            known=all(w is not None for w in walls); complete=complete and known
            mw=median(walls) if known else None; ms=median(shares) if known else None
            hit=bool(known and mw>=5 and ms>=.25); passed+=hit
            groups[str(seed)]=dict(pricing_event_wall_median_s=mw,share_of_paid_F1_median=ms,passed=hit)
        if not complete: unknown.append(arm+': missing/inconsistent completed-event timing')
        return dict(groups=groups,passing_groups=passed,complete=complete,passed=bool(complete and passed>=3),
            share_denominator='stage_elapsed_s, including folder/spec setup; parent_elapsed_s is admission cutoff only')

    primary_cache=value_screen('full','full','C1'); primary_fixed=value_screen('full','fixed_duty','F1')
    secondary=value_screen('fixed_duty','fixed_duty','C1'); full_effort=effort('full'); fixed_effort=effort('fixed_duty')
    eligible=bool(report.get('passed') and report.get('preflight_admitted') and report.get('distinct_group_clusters')==4
        and methods_ready and all(finite(c['target_common_grid_electricity'],True) for c in cells))
    def decision(e,values):
        ready=eligible and e['complete'] and all(v['defined_pairs']==8 for v in values)
        return dict(eligible=ready,status='inconclusive' if not ready else
            'continue_to_separate_target_audit' if e['passed'] and all(v['passed'] for v in values) else 'scoped_stop',
            passed=bool(ready and e['passed'] and all(v['passed'] for v in values)),automatic_job_authorized=False)
    pipeline_totals={}
    for phase in ('F1','C1'):
        costs=[s['pipeline_costs'][phase] for s in report['sequences']]
        complete=all(c['cpu_s'] is not None and c['elapsed_stage_sum_s'] is not None for c in costs)
        prefix=report.get('common_preflight') or {}
        pipeline_totals[phase]=dict(planned_sequences=16,complete_stage_costs=complete,
            cpu_s=None if not complete else sum(c['cpu_s'] for c in costs)+prefix.get('cpu_s',0),
            elapsed_stage_sum_s=None if not complete else sum(c['elapsed_stage_sum_s'] for c in costs)+prefix.get('elapsed_s',0),
            scope='Counterfactual workload stage sums plus common preflight once; no available-only pipeline total. Physical campaign charges A0 once.')
    requirements=dict(strict_A0=sum(c['method_qualified'] for c in cells if c['phase']=='A0'),
        operational_A0=sum(c['physical_endpoint_accepted'] for c in cells if c['phase']=='A0'),
        strict_F1=sum(c['method_qualified'] for c in cells if c['phase']=='F1'),
        strict_native_optimal_C1=sum(c['method_qualified'] for c in cells if c['phase']=='C1'),
        planned_per_phase=16,accounting_complete=report.get('accounting_complete'),
        source_preflight_admitted=report.get('preflight_admitted',False),
        four_distinct_alias_clusters=report.get('distinct_group_clusters')==4,
        positive_A0_target_E_sequences=sum(finite((s['A0'].get('worker') or {}).get('target_common_grid_electricity'),True)
            and s['A0'].get('physical_endpoint_accepted',False) for s in report['sequences']))
    return dict(policy=POLICY,passed=report['passed'],planned_states=48,recorded_states=len(cells),cells=cells,
        sequences=report['sequences'],alias_groups=report.get('alias_groups'),distinct_group_clusters=report.get('distinct_group_clusters'),
        investment_readiness_eligible=eligible,readiness_requirements=requirements,
        primary=dict(effort=full_effort,vs_own_cache=primary_cache,vs_fixed_F1=primary_fixed,
            decision=decision(full_effort,[primary_cache,primary_fixed])),
        secondary=dict(effort=fixed_effort,vs_own_cache=secondary,decision=decision(fixed_effort,[secondary])),
        operational_fallback_results_do_not_satisfy_method_readiness=True,source_conditional_unknowns=unknown,
        common_preflight=report.get('common_preflight'),counterfactual_pipeline_totals=pipeline_totals,
        per_column_reduced_cost_labels='UNKNOWN',exact_physical_pricing_call_count='UNKNOWN',
        pooled_scope_mean=None,independent_groups_claim=False,resources=report['resources'],failures=report['failures'])


def main():
    launch,raw=gate(); output=HERE/'attempt01'; output.mkdir(exist_ok=False)
    target=output/'receipt.json'; save(target,dict(receipt_complete=False,passed=False))
    report=dict(policy=POLICY,passed=False,receipt_complete=False,config_failure=False,failures=[],
        source_revision=launch['source_revision'],launch_sha256=hashlib.sha256(raw).hexdigest(),source_sha256={},
        budgets=BUDGETS,tracking_prefix=launch['tracking_prefix'],numerical_resource_prefix=launch['numerical_resource_prefix'],
        preparation_accounting=launch['preparation_accounting'],sequences=assigned_sequences())
    for seq in report['sequences']:
        for phase in ('A0','F1','C1'): seq[phase]['source_revision']=launch['source_revision']
    p=launch['preparation_accounting']; stopped=None; unresolved=0.; phase='preflight'; final_cpu=final_wall=None

    def stop(signum,frame):
        global DEFERRED_STOP
        nonlocal stopped
        stopped=stopped or signum
        if PUBLISHING_CHILD: DEFERRED_STOP=DEFERRED_STOP or signum; return
        raise TimeoutError('Latched owner stop '+str(signum))

    def check():
        if stopped is not None: raise TimeoutError('Owner stop remains latched')
        spent=cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s']+unresolved
        if threading.active_count()!=1 or rss()>5*1024**3 or spent>7200 or time.monotonic()-START+p['elapsed_s']>10800:
            report['config_failure']=True; raise ContractError('Total resource/thread/RSS bound')
        if (phase=='preflight' and (spent>120 or time.monotonic()-START+p['elapsed_s']>180)
                or phase=='finalization' and (cpu()-final_cpu>120 or time.monotonic()-final_wall>180)):
            report['config_failure']=True; raise ContractError('Preflight/final provision exceeded')

    try:
        for key in ENV: os.environ[key]='1'
        resource.setrlimit(resource.RLIMIT_CPU,(120,7200))
        for sig in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM,signal.SIGINT): signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,180-p['elapsed_s']-(time.monotonic()-START)))
        preflight(launch,report,check)
        report['common_preflight']=dict(cpu_s=cpu()+p['charged_cpu_s'],elapsed_s=time.monotonic()-START+p['elapsed_s'])
        phase='dispatch'; resource.setrlimit(resource.RLIMIT_CPU,(7200,7200))
        signal.setitimer(signal.ITIMER_REAL,max(.001,10800-p['elapsed_s']-(time.monotonic()-START)))
        for seq in report['sequences']:
            for name in seq['dispatch_order']:
                row=seq[name]; check()
                row['descriptor_sha256']=report['descriptor_sha256'][f"{row['base_seed']}:{row['services']}:{row['quote']}"]
                if name=='C1' and not seq['A0'].get('bank_qualified'):
                    row['unattempted_reason']='No timely admitted own A0 complete bank/common fleet'; continue
                if (cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s']+unresolved+120>6600
                        or time.monotonic()-START+p['elapsed_s']+183+180>10800):
                    report['dispatch_stopped_reason']='Whole next stage/closure not funded'; break
                run_worker(row,None if name=='A0' else seq['A0']); unresolved+=row['unresolved_cpu_reserve_s']
                if unresolved or any(row.get(f) for f in ('config_failure','fatal_contract','resource_violation','identity_failure')):
                    report['config_failure']=True; report['dispatch_stopped_reason']='Fatal stage or unresolved owned child'; break
                check()
            if report.get('dispatch_stopped_reason'): break
    except BaseException as exc:
        report['config_failure']=True; report['failures'].append(dict(stage=phase,type=type(exc).__name__,message=str(exc)))
    finally:
        phase='finalization'; final_cpu=cpu(); final_wall=time.monotonic()
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(180.,10800-p['elapsed_s']-(final_wall-START))))
        for seq in report['sequences']:
            for name in ('A0','F1','C1'):
                if not seq[name].get('attempted'): seq[name].setdefault('unattempted_reason',report.get('dispatch_stopped_reason','Owner/preflight failure'))
        report.update(receipt_complete=True,accounting_complete=unresolved==0,unresolved_cpu_reserve_s=unresolved,stop_signal=stopped,
            resources=dict(self_cpu_s=cpu(),waited_children_cpu_s=cpu(resource.RUSAGE_CHILDREN),preparation_charge_s=p['charged_cpu_s'],
                package_cpu_prepublication_s=cpu()+cpu(resource.RUSAGE_CHILDREN)+p['charged_cpu_s'],
                package_elapsed_sum_prepublication_s=time.monotonic()-START+p['elapsed_s'],observed_self_peak_rss_bytes=rss(),
                python_threads=threading.active_count(),task_deltas_not_added_twice=True,external_total_acceptance_pending=True))
        try: check()
        except BaseException as exc:
            report['config_failure']=True; report['failures'].append(dict(stage='final_resource',type=type(exc).__name__,message=str(exc)))
        report['passed']=bool(not report['config_failure'] and not report['failures'] and report['accounting_complete'] and stopped is None)
        readout=compact_and_screens(report)
        remaining=min(180-(time.monotonic()-final_wall),10800-p['elapsed_s']-(time.monotonic()-START))
        if remaining<=0: raise TimeoutError('Publication provision exhausted; master remains incomplete')
        signal.setitimer(signal.ITIMER_REAL,remaining)
        publish(output/'READOUT.json',readout)
        with (output/'READOUT.md').open('x') as stream:
            stream.write('# Independent pricing workload\n\nFour development groups; all48 planned stages retained.\n\n')
            stream.write('```json\n'+json.dumps(readout,indent=2,allow_nan=False,default=lambda v:str(v) if isinstance(v,Q) else v)+'\n```\n')
            stream.flush(); os.fsync(stream.fileno())
        check(); publish(target,report)
        print(json.dumps(dict(passed=report['passed'],primary=readout['primary']['decision'],secondary=readout['secondary']['decision'],
            readout=str(output/'READOUT.md'),resources=report['resources']),allow_nan=False),flush=True)
        check(); signal.setitimer(signal.ITIMER_REAL,0)
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
