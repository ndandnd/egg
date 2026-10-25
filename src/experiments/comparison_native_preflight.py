"""Candidate two-task 60s native preflight; explicit invocation only.

Reuse qualified supervision under serialized, fully restored bindings. Importing
this module generates no fixture and imports no numerical backend.
"""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import argparse
import os
import sys
import threading
import time

from experiments import recovery_qualification as q

POLICY = 'comparison-native-preflight-v1'
PACKAGE_START = 1296.29257734018
PACKAGE_LIMIT = 230.
PACKAGE_CAP = PACKAGE_START+PACKAGE_LIMIT
ENDPOINT_S, STOP_S, OUTER_S = 60., 61., 62.5
FREEZE_ELAPSED_LIMIT_S = 10.
ANALYSIS_FINAL_RESERVE_S, SUPERVISION_RESERVE_S = 5., 40.
WORKER_ARGV_PREFIX = ('-m','experiments.comparison_native_worker')
# Explicit adapter bindings; defaults retain the original engineering80 policy.
ENGINEERING_BASE_ID, ENGINEERING_TRIPS = 50999, 80
FIXTURE_POLICY = 'same previously frozen engineering50999/80; no generation'
_LOCK = threading.Lock()
_BASE_LAUNCH = q.launch


def task_matrix(cases):
    if (len(cases)!=1 or cases[0].get('base_id')!=ENGINEERING_BASE_ID
            or cases[0].get('trips')!=ENGINEERING_TRIPS):
        raise ValueError('Preflight requires its explicitly configured engineering case only')
    case = cases[0]
    tasks = []
    for arm in ('cf1','recovery'):
        task = {'arm':arm,'base_id':ENGINEERING_BASE_ID,'trips':ENGINEERING_TRIPS,'seed':17,'seconds':60.,
                'fault':None}
        task['id'] = q.stable(task)[:20]
        tasks.append(task)
    return tasks


def schedule_spec():
    from egglab.comparison_coordinator import Schedule60
    return Schedule60(0.,60.).as_dict()


def verify_artifacts(folder, inventory):
    folder = Path(folder).resolve()
    rebased = {}
    for name,digest in inventory.items():
        path = Path(name)
        path = path if path.is_absolute() else folder/path
        if path.is_symlink() or path.resolve().parent!=folder:
            raise ValueError('Artifact escapes flat receipt folder')
        rebased[str(path)] = digest
    q.verify_hashes(rebased)


def checked_sources(directory):
    directory = Path(directory).resolve()
    result,attempt = q.read(directory/'result.json'),q.read(directory/'attempt.json')
    termination = result.get('termination',{})
    if (result.get('passed') is not True or result.get('returncode')!=0
            or result.get('failure') is not None or result.get('source_changes')!=[]
            or termination.get('group_absent') is not True or termination.get('reaped') is not True
            or not termination.get('owned_pgids') or termination.get('surviving_pgids')!=[]
            or termination.get('cleanup_errors') or result.get('primary_failure')
            or result.get('secondary_errors')
            or result.get('accounting_observations_complete') is not True
            or result.get('accounting_unresolved') or result.get('charge_is_lower_bound')
            or not isinstance(result.get('artifact_hashes'),dict) or not result['artifact_hashes']
            or result.get('stdout_sha256')!=q.sha(directory/'stdout.log')
            or result.get('stderr_sha256')!=q.sha(directory/'stderr.log')
            or not q.finite(result.get('cumulative_qualification_charge_s'),PACKAGE_START)):
        raise ValueError('Incomplete source-bound adapter check receipt')
    verify_artifacts(directory,result['artifact_hashes'])
    sources = attempt.get('source_hashes',{})
    required = ('src/experiments/recovery_qualification.py',
                'src/experiments/comparison_native_preflight.py',
                'src/experiments/comparison_native_worker.py',
                'src/egglab/comparison_coordinator.py',
                'src/egglab/constructive_proposal.py',
                'src/tests/test_comparison_native_adapter.py')
    for name in required:
        matches = [value for key,value in sources.items() if Path(key).resolve()==(q.ROOT/name).resolve()]
        if matches != [q.sha(q.ROOT/name)]:
            raise ValueError('Passing check misses current dependency: '+name)
    q.verify_hashes(sources)
    return {str(directory/name):q.sha(directory/name) for name in ('attempt.json','result.json')}


def verify_lock(lock, *, worker=False):
    if lock.get('policy')!=POLICY or lock.get('tasks')!=task_matrix(lock['cases']):
        raise ValueError('Invalid comparison-native task lock')
    if (lock.get('schedule')!=schedule_spec() or lock.get('backend')!='GRB'
            or lock.get('models')!={} or lock.get('tariff')!='day'
            or lock.get('package_start_charge_s')!=PACKAGE_START
            or lock.get('package_limit_s')!=PACKAGE_LIMIT or lock.get('package_cap_s')!=PACKAGE_CAP
            or not q.finite(lock.get('carried_charge_s'),PACKAGE_START)
            or not q.finite(lock.get('freeze_charge_s'))
            or lock['carried_charge_s']+lock['freeze_charge_s']>PACKAGE_CAP):
        raise ValueError('Comparison native policy/accounting mismatch')
    for key in ('sources','assets','checks','evidence','prior_evidence'):
        if not isinstance(lock.get(key),dict) or not lock[key]:
            raise ValueError('Missing frozen '+key)
        q.verify_hashes(lock[key])
    if lock['sources']!=q.campaign.sources():
        raise ValueError('Frozen source closure is incomplete or changed')
    for case in lock['cases']:
        if (lock['assets'].get(case['fixture'])!=q.sha(case['fixture'])
                or not case.get('movement_ids') or not case.get('restricted_movement_ids')
                or not case.get('restricted_identity') or not case.get('market_sha256')
                or not case.get('selection_policy')):
            raise ValueError('Incomplete frozen engineering case metadata')
    checks = [Path(path).parent for path in lock['checks'] if Path(path).name=='result.json']
    if len(checks)!=1 or checked_sources(checks[0])!=lock['checks']:
        raise ValueError('Lock lacks passing adapter gate')
    q.verify_hashes({lock['native_library']['path']:lock['native_library']['sha256']})
    if lock.get('environment')!=q.environment():
        raise ValueError('Frozen environment changed')
    if worker and any(os.environ.get(key)!='1' for key in q.THREAD_KEYS):
        raise ValueError('Numerical thread limits differ from lock')


def freeze(args):
    """Metadata freeze only: reuse explicitly supplied engineering fixture assets."""
    started,cpu0 = time.monotonic(),time.process_time()
    design_path = getattr(args,'design',None) or getattr(args,'manifest',None)
    manifest,prior = q.read(design_path),q.accounting(args.accounting)
    checks = checked_sources(args.checks)
    check_charge = q.read(Path(args.checks)/'result.json')['cumulative_qualification_charge_s']
    if prior['charged_cpu_s']<check_charge or prior['charged_cpu_s']<PACKAGE_START:
        raise ValueError('Prior account omits adapter check charge')
    if prior['charged_cpu_s']+10.+ANALYSIS_FINAL_RESERVE_S>PACKAGE_CAP:
        raise ValueError('No package room for freeze and final analysis')
    if (manifest.get('policy')!=POLICY or manifest.get('backend')!='GRB'
            or manifest.get('tariff')!='day' or manifest.get('models')!={}):
        raise ValueError('Invalid prospective comparison design')
    budget_spec = manifest.get('package_budget',{})
    expected_budget = {'initial_charged_cpu_s':PACKAGE_START,'additional_hard_cap_s':PACKAGE_LIMIT,
        'absolute_package_ceiling_s':PACKAGE_CAP,'analysis_reserve_s':ANALYSIS_FINAL_RESERVE_S,
        'next_worker_allocation_s':OUTER_S,'next_worker_supervision_reservation_s':SUPERVISION_RESERVE_S,
        'physical_and_ack_endpoint_s':ENDPOINT_S,'supervisor_stop_s':STOP_S,'outer_allocation_s':OUTER_S,
        'global_hard_ceiling_s':q.CEILING,'global_dispatch_stop_s':q.DISPATCH_STOP,
        'global_shutdown_reserve_s':q.SHUTDOWN_RESERVE,'threads':1,'numerical_workers':1,
        'rss_limit_bytes':q.RSS_LIMIT,'automatic_retry':False}
    if any(budget_spec.get(key)!=value for key,value in expected_budget.items()):
        raise ValueError('Prospective package budget differs')
    if (len(manifest['case_specs'])!=1
            or manifest['case_specs'][0].get('base_id')!=ENGINEERING_BASE_ID
            or manifest['case_specs'][0].get('trips')!=ENGINEERING_TRIPS):
        raise ValueError('Wrong engineering case specification')
    from egglab import classical_controls as cc
    from egglab import native_recharge as nr
    from experiments.codex_offline_rank import heuristic
    cases,assets = [],{}
    for spec in manifest['case_specs']:
        payload = q.read(spec['fixture'])
        case = q.restore_case(payload['case'])
        nr._check_market(case,payload['a'],payload['b'])
        if len(case.trips)!=ENGINEERING_TRIPS:
            raise ValueError('Engineering fixture scale mismatch')
        market_sha = q.stable({'a':payload['a'],'b':payload['b']})
        if (case.identity()!=spec.get('full_identity',spec.get('identity'))
                or market_sha!=spec['market_sha256']):
            raise ValueError('Engineering fixture identity/market mismatch')
        source,selection = cc.restrict_case(case,heuristic(case))
        cases.append({'base_id':ENGINEERING_BASE_ID,'trips':ENGINEERING_TRIPS,'fixture':str(Path(spec['fixture']).resolve()),
            'identity':case.identity(),'movement_ids':[m.id for m in case.movements],
            'restricted_identity':source.identity(),'restricted_movement_ids':[m.id for m in source.movements],
            'market_sha256':market_sha,'selection_policy':selection['policy']})
        assets[cases[-1]['fixture']] = q.sha(spec['fixture'])
    if manifest.get('tasks')!=task_matrix(cases):
        raise ValueError('Prospective task order/identities differ')
    native = manifest['native_library']
    q.verify_hashes({native['path']:native['sha256']})
    evidence = {str(Path(path).resolve()):q.sha(path) for path in (design_path,args.accounting)}
    evidence.update(manifest.get('evidence',{}))
    q.verify_hashes(evidence)
    lock = {'policy':POLICY,'cases':cases,'tasks':task_matrix(cases),
        'sources':q.campaign.sources(),'assets':assets,'models':{},'checks':checks,
        'evidence':evidence,'prior_evidence':prior['evidence_hashes'],
        'environment':q.environment(),'backend':'GRB','native_library':native,
        'tariff':'day','schedule':schedule_spec(),'carried_charge_s':prior['charged_cpu_s'],
        'freeze_charge_s':0.,
        'package_start_charge_s':PACKAGE_START,'package_limit_s':PACKAGE_LIMIT,'package_cap_s':PACKAGE_CAP,
        'prior_accounting_sha256':q.sha(args.accounting),
        'package_budget':deepcopy(budget_spec),
        'fixture_policy':FIXTURE_POLICY,
        'freeze_accounting':'external supervised receipt required before native launch'}
    # Pure policy/source verification before exclusive durable lock creation.
    verify_lock(lock)
    q.write_new(args.lock,lock)
    return {'lock':str(Path(args.lock).resolve()),'sha256':q.sha(args.lock),'tasks':2,
            'external_freeze_receipt_required':True}


def freeze_accounting(lock, lockpath, receiptpath):
    receipt = q.read(receiptpath)
    termination = receipt.get('termination',{})
    charged,supervisor = receipt.get('charged_cpu_s'),receipt.get('supervisor_cpu_s')
    cumulative = receipt.get('cumulative_qualification_charge_s')
    if (receipt.get('policy')!=POLICY or receipt.get('phase')!='comparison_native_freeze'
            or receipt.get('passed') is not True or receipt.get('failure') is not None
            or receipt.get('monitor_failure') is not None or receipt.get('source_changes')!=[]
            or receipt.get('returncode')!=0 or receipt.get('secondary_errors')
            or receipt.get('primary_failure') is not None
            or receipt.get('accounting_observations_complete') is not True
            or receipt.get('accounting_unresolved') or receipt.get('charge_is_lower_bound')
            or not isinstance(receipt.get('artifact_hashes'),dict) or not receipt['artifact_hashes']
            or receipt.get('lock_sha256')!=q.sha(lockpath)
            or receipt.get('prior_accounting_sha256')!=lock['prior_accounting_sha256']
            or not isinstance(receipt.get('source_hashes'),dict)
            or receipt['source_hashes']!=lock['sources']
            or termination.get('group_absent') is not True or termination.get('reaped') is not True
            or not termination.get('owned_pgids') or termination.get('surviving_pgids')!=[]
            or termination.get('cleanup_errors') or termination.get('probe_diagnostics')
            or not q.finite(charged) or not q.finite(supervisor)
            or not q.finite(receipt.get('charged_allocation_s'))
            or charged!=receipt['charged_allocation_s']+supervisor
            or not q.finite(receipt.get('elapsed_allocation_s'))
            or receipt['elapsed_allocation_s']>FREEZE_ELAPSED_LIMIT_S
            or not q.finite(receipt.get('sampled_peak_rss_bytes')) or receipt['sampled_peak_rss_bytes']>q.RSS_LIMIT
            or not q.finite(cumulative,lock['carried_charge_s']+charged)
            or cumulative!=lock['carried_charge_s']+charged
            or cumulative+ANALYSIS_FINAL_RESERVE_S>PACKAGE_CAP):
        raise ValueError('Missing/incomplete external comparison freeze receipt')
    q.verify_hashes(receipt['source_hashes'])
    folder = Path(receiptpath).resolve().parent
    verify_artifacts(folder,receipt['artifact_hashes'])
    if (receipt.get('stdout_sha256')!=q.sha(folder/'stdout.log')
            or receipt.get('stderr_sha256')!=q.sha(folder/'stderr.log')):
        raise ValueError('Freeze output hashes changed')
    return {**lock,'freeze_charge_s':cumulative-lock['carried_charge_s']}


def completion_endpoint(folder, task, locksha, anchor, *, acknowledgment):
    try:
        folder = Path(folder)
        marker,result = q.read(folder/'completion.json'),q.read(folder/'result.json')
        outcome = q.read(folder/'worker-outcome.json')
        end = marker['finished_monotonic']
        if (marker['task']!=task or marker['lock_sha256']!=locksha
                or marker['parent_monotonic']!=anchor or marker['deadline']!=anchor+ENDPOINT_S
                or result['task']!=task or result['lock_sha256']!=locksha
                or not q.finite(end,anchor) or not q.finite(marker['elapsed_s'])
                or marker['elapsed_s']!=end-anchor or marker['result_sha256']!=q.sha(folder/'result.json')
                or type(marker['censored']) is not bool):
            raise ValueError('Completion identity/hash mismatch')
        ack = acknowledgment
        if (not isinstance(ack,dict) or ack.get('task_id')!=task['id'] or ack.get('lock_sha256')!=locksha
                or ack.get('parent_monotonic')!=anchor or ack.get('result_sha256')!=marker['result_sha256']
                or ack.get('completion_sha256')!=q.sha(folder/'completion.json')
                or not q.finite(ack.get('completion_monotonic'),end)
                or ack.get('worker_outcome_sha256')!=q.sha(folder/'worker-outcome.json')
                or outcome.get('task')!=task or outcome.get('lock_sha256')!=locksha
                or outcome.get('result_sha256')!=marker['result_sha256']
                or type(outcome.get('censored')) is not bool
                or not isinstance(outcome.get('status'),str) or not outcome['status']
                or result.get('status')=='clock_failed'
                or ack.get('worker_censored') is not outcome['censored']
                or ack.get('worker_status')!=outcome.get('status')
                or outcome.get('status') in ('clock_failed','worker_failure','storage_failed')):
            raise ValueError('Missing/malformed post-fsync acknowledgment')
        return {'endpoint_wall_s':end-anchor,'endpoint_censored':marker['censored'] or outcome['censored'] or end>anchor+ENDPOINT_S
                or ack['completion_monotonic']>anchor+ENDPOINT_S,'completion_issue':None}
    except (OSError,ValueError,KeyError,TypeError):
        return {'endpoint_wall_s':None,'endpoint_censored':True,'completion_issue':'missing_or_malformed_completion'}


def launch(args, task, output, locksha):
    """Reuse original ownership/FD/signal body; change only command and anchor marker."""
    original_write,original_popen = q.write_new,q.subprocess.Popen
    def write(path,value):
        if Path(path).name=='attempt.json':
            if value.get('deadline')!=value['parent_monotonic']+30.:
                raise ValueError('Unexpected legacy launch schema')
            value = {**value,'deadline':value['parent_monotonic']+ENDPOINT_S}
        return original_write(path,value)
    def popen(command,*args,**kwargs):
        if command[1:4]!=['-m','experiments.recovery_qualification','worker']:
            raise ValueError('Unexpected legacy worker command')
        command = [command[0],*WORKER_ARGV_PREFIX,*command[4:]]
        return original_popen(command,*args,**kwargs)
    q.write_new,q.subprocess.Popen = write,popen
    try:
        return _BASE_LAUNCH(args,task,output,locksha)
    finally:
        q.write_new,q.subprocess.Popen = original_write,original_popen


def package_charge(state, item=None, now=None):
    own = time.process_time()-state['cpu0']
    observations = [state['base_spent'],*state['finished'].values(),own,q._monitor_child_cpu_s]
    if not all(q.finite(value) for value in observations):
        raise ValueError('Incomplete package charge observations')
    total = state['base_spent']+sum(state['finished'].values())
    total += own+q._monitor_child_cpu_s
    if item is not None and item['task']['id'] not in state['finished']:
        elapsed = (time.monotonic() if now is None else now)-item['anchor']
        if not q.finite(elapsed) or not q.finite(item['cpu']):
            raise ValueError('Invalid active package charge')
        total += max(elapsed,item['cpu'])
    return total


@contextmanager
def bound60(state=None):
    """Serialized adapter; restore all changed constants/functions even on failure."""
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('Comparison supervision binding requires serialized use')
    replacements = {'POLICY':POLICY,'OUTER_ALLOCATION':OUTER_S,'SUPERVISOR_STOP_S':STOP_S,
        'launch':launch,'completion_endpoint':completion_endpoint,
        'verify_lock':verify_lock,'freeze_accounting':freeze_accounting,'_analyze':_analyze}
    names = set(replacements)|({'resume_state','finish','resource_step'} if state is not None else set())
    old = {name:getattr(q,name) for name in names}
    if state is not None:
        def resume(*args):
            completed,total = old['resume_state'](*args)
            state.update(base_spent=total,prior_ids=set(completed))
            return completed,total
        def finish(item,*args):
            receipt = old['finish'](item,*args)
            if item['task']['id'] not in state.get('prior_ids',set()):
                previous = state['finished'].setdefault(item['task']['id'],receipt['charged_cpu_s'])
                if previous!=receipt['charged_cpu_s']:
                    raise ValueError('Reentrant terminal charge changed')
            return receipt
        def step(item,table,free,now):
            reason = old['resource_step'](item,table,free,now)
            if package_charge(state,item,now)+2.5+ANALYSIS_FINAL_RESERVE_S>=PACKAGE_CAP:
                return reason or 'comparison_package_cleanup_reserve'
            return reason
        def gated_launch(*args):
            if package_charge(state)+OUTER_S+SUPERVISION_RESERVE_S+ANALYSIS_FINAL_RESERVE_S>PACKAGE_CAP:
                raise RuntimeError('Comparison package next-worker reserve exhausted')
            return launch(*args)
        replacements.update(resume_state=resume,finish=finish,resource_step=step,launch=gated_launch)
    try:
        for name,value in replacements.items():
            setattr(q,name,value)
        yield
    finally:
        for name,value in old.items():
            setattr(q,name,value)
        _LOCK.release()


def run(args):
    lock = q.read(args.lock)
    state = {'base_spent':lock['carried_charge_s']+lock['freeze_charge_s'],
             'finished':{},'prior_ids':set(),'cpu0':time.process_time()}
    with bound60(state):
        result = q.run(args)
    return {**result,'planned':len(lock['tasks']),'package_cap_s':PACKAGE_CAP}


def _analyze(args):
    cpu0 = time.process_time()
    lock,locksha,output = q.read(args.lock),q.sha(args.lock),Path(args.output).resolve()
    verify_lock(lock)
    binding = q.read(output/'campaign.json')
    if (binding.get('policy')!=POLICY or binding.get('lock_sha256')!=locksha
            or binding.get('freeze_receipt_sha256')!=q.sha(binding['freeze_receipt'])):
        raise ValueError('Freeze/run output binding changed')
    budget_lock = freeze_accounting(lock,args.lock,binding['freeze_receipt'])
    completed,total = q.resume_state(output,budget_lock,locksha)
    rows,issues = [],[]
    from egglab import recovery_coordinator as rc
    from experiments import comparison_native_worker as worker
    frozen = lock['cases'][0]
    payload = q.read(frozen['fixture'])
    case = q.restore_case(payload['case'])
    for task in lock['tasks']:
        if total+time.process_time()-cpu0>=PACKAGE_CAP:
            raise RuntimeError('Analysis exhausted aggregate package cap')
        if task['id'] not in completed:
            issues.append('undispatched:'+task['id']);continue
        folder,receipt = output/task['id'],completed[task['id']]
        result = q.read(folder/'result.json')
        state = result.get('native_state') or {}
        row_issues = [key for key in ('failure','monitor_failure','worker_failure','endpoint_censored','completion_issue')
                      if receipt.get(key)]
        endpoint = completion_endpoint(folder,task,locksha,receipt['parent_monotonic'],
                                       acknowledgment=receipt.get('completion_acknowledgment'))
        if endpoint['endpoint_censored'] or endpoint['completion_issue']:
            row_issues.append('independent_completion_endpoint')
        if receipt.get('returncode')!=0 or receipt.get('group_absent') is not True:
            row_issues.append('ownership_or_returncode')
        if not q.finite(receipt.get('peak_tree_rss_bytes')) or receipt['peak_tree_rss_bytes']>q.RSS_LIMIT:
            row_issues.append('rss_limit')
        if result.get('failures') or state.get('engineering_events') or state.get('sink_failure'):
            row_issues.append('worker_engineering_failure')
        evidence = q.start_evidence((folder/'stdout.log').read_bytes(),state.get('submissions',[]))
        if evidence!=q.read(folder/'start-evidence.json'):
            row_issues.append('native_evidence_mismatch')
        capture_checks = []
        try:
            worker.audit_captures(folder,state,result.get('events',[]),
                lock=lock,task=task,anchor=receipt['parent_monotonic'])
            capture_checks = [worker.verify_capture_reference(folder,lock,task,
                receipt['parent_monotonic'],ref) for ref in state.get('capture_references',[])]
        except Exception as exc:
            row_issues.append('invalid_capture_reference:'+type(exc).__name__)
        fallback,selected = result.get('fallback'),result.get('selected')
        for kind,witness in (('fallback',fallback),('selected',selected)):
            if witness is None:
                continue
            try:
                checked = rc.lift_plan(case,case,witness['plan'],a=payload['a'],b=payload['b'])
                if (checked['true_bill_exact']!=witness['true_bill_exact']
                        or checked['true_bill']!=witness['true_bill']):
                    raise ValueError('Saved bill differs from independent exact replay')
            except Exception as exc:
                row_issues.append('invalid_'+kind+':'+type(exc).__name__)
        if fallback is None or selected is None:
            row_issues.append('missing_physical_witness')
        artifact = result.get('fallback_artifact') or {}
        if (not (folder/'fallback.json').is_file()
                or artifact.get('sha256')!=q.sha(folder/'fallback.json')
                or Path(artifact.get('path','')).resolve()!=(folder/'fallback.json').resolve()):
            row_issues.append('missing_or_changed_durable_fallback')
        if ((result.get('global_lower_bound') is not None and not result.get('bound_provenance'))
                or any(value.get('scope')!='full_unrestricted_mip' for value in result.get('bound_provenance',[]))):
            row_issues.append('bound_scope')
        lower = result.get('global_lower_bound')
        if lower is not None and (selected is None or not q.finite(lower,-q.math.inf)
                                  or lower>selected['true_bill']+rc.pf.BOUND_GUARD):
            row_issues.append('invalid_global_bound')
        for submission in state.get('submissions',[]):
            inventory = submission.get('inventory',[])
            if (q.stable(inventory)!=submission.get('inventory_sha256')
                    or [value.get('movement_id') for value in inventory]!=frozen['movement_ids']
                    or len({value.get('variable_index') for value in inventory})!=len(inventory)
                    or any(type(value.get('value')) is not int or value['value'] not in (0,1) for value in inventory)
                    or submission.get('continuous_submitted')!=0
                    or submission.get('bounds_constraints_unchanged') is not True):
                row_issues.append('native_start_mapping_violation')
        processed = any(value.get('processed') is True for value in evidence.get('classified',[]))
        if not processed:
            row_issues.append('native_partial_start_processing_unobserved')
        if evidence.get('unattributed_log_matches'):
            row_issues.append('unattributed_start_log_evidence')
        if task['arm']=='cf1':
            fixed_captures = [capture for capture in capture_checks if capture['phase']=='cf1']
            if (not fixed_captures or any(capture['all_mapped_binary_fixed'] is not True
                    or capture['all_unmapped_continuous'] is not True for capture in fixed_captures)):
                row_issues.append('cf1_fixed_capture_unverified')
            provider = result.get('provider_audit') or {}
            charged = [entry.get('result',{}) for entry in provider.get('stages',[])
                       if entry.get('stage','').startswith('charging')]
            valid = [entry for entry in charged if entry.get('status')=='feasible']
            if result.get('provider_status')!='proposal' or not valid:
                row_issues.append('cf1_charging_path_unexercised')
            for entry in charged:
                inventory = entry.get('inventory') or {}
                if (inventory.get('case_identity')!=frozen['identity']
                        or inventory.get('movement_ids')!=frozen['movement_ids']
                        or inventory.get('all_unfixed_continuous') is not True
                        or inventory.get('physical_rows_preserved') is not True):
                    row_issues.append('cf1_fixed_inventory')
        rows.append({'task':task,'issues':row_issues,'endpoint_wall_s':endpoint['endpoint_wall_s'],
                     'censored':endpoint['endpoint_censored'],'native':evidence,
                     'fallback_bill_exact':None if fallback is None else fallback.get('true_bill_exact'),
                     'selected_bill_exact':None if selected is None else selected.get('true_bill_exact')})
        issues.extend(task['id']+':'+value for value in row_issues)
    if total+time.process_time()-cpu0>PACKAGE_CAP:
        issues.append('package_hard_cap')
    report = {'policy':POLICY,'passed':not issues and len(rows)==len(lock['tasks']),
        'planned':len(lock['tasks']),'terminal':len(rows),'rows':rows,'issues':issues,
        'cumulative_before_analysis_tail_s':total,'package_cap_s':PACKAGE_CAP,
        'scope':'two engineering80 preflight paths only; no comparative quality/optimality/generalization claim'}
    q.write_new(args.report,report)
    return report


def analyze(args):
    with bound60():
        return q.analyze(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    p = commands.add_parser('freeze')
    p.add_argument('--design','--manifest',dest='design',required=True)
    for name in ('lock','checks','accounting'):
        p.add_argument('--'+name,required=True)
    for name in ('run','analyze'):
        p = commands.add_parser(name)
        for option in ('lock','output'):
            p.add_argument('--'+option,required=True)
        p.add_argument('--freeze-receipt' if name=='run' else '--report',required=True)
    args = parser.parse_args()
    result = {'freeze':freeze,'run':run,'analyze':analyze}[args.command](args)
    print(q.json.dumps(result,indent=2))


if __name__=='__main__':
    main()
