"""One CF1-only metadata freeze; no solver/retry; reviewed supervision helpers unchanged."""
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from experiments import recovery_qualification as q
import run_recovery_runner_checks as ownership

ADMIN = 0.
PACKAGE_END, FINALIZATION_RESERVE = 1581.3727097992353, 30.
FREEZE_ROOT = ROOT/'research-20261023/cf1-preparation-native-v2'
CHECK_ROOT = ROOT/'research-20261023/cf1-preparation-native-checks'


def retain_error(state, exc, context):
    diagnostic = q.monitor_diagnostic(exc,context=context)
    if state.get('primary_failure') is None:
        state['primary_failure'] = diagnostic
    else:
        state.setdefault('secondary_errors',[]).append(diagnostic)
    return diagnostic


def sample_owned(proc, groups, registry, anchor, last_completed):
    tick = time.monotonic()
    deadline = q.monitor_deadline(tick,last_completed,anchor+7.5)
    ownership.registered_groups(registry,groups)
    table,free = q.monitor_sample(deadline)
    rows = ownership.owned_rows(proc.pid,groups,table)
    ownership.registered_groups(registry,groups)
    # Newly registered detached children must count even before ancestry is sampled.
    rows = [row for pid,row in table.items() if row['pgid'] in groups or row in rows]
    completed = time.monotonic()
    if completed>deadline or (last_completed is not None and completed-last_completed>.25):
        raise q.MonitorError(q.monitor_diagnostic(TimeoutError('Complete sample gap exceeded .25s'),
                             context='complete_sample',deadline=deadline))
    if not q.finite(free) or free>100:
        raise ValueError('Invalid check memory monitor')
    return {'completed_monotonic':completed,'sample_deadline':deadline,
            'rss_bytes':sum(row['rss'] for row in rows),'cpu_s':sum(row['cpu'] for row in rows),
            'free_percent':free,'owned_pgids':sorted(groups)}


def cleanup_receipt(proc, groups, deadline):
    """Keep owned identity and secondary evidence even if the shared helper raises."""
    known = set(groups)|{proc.pid}
    errors,diagnostics = [],[]
    result = {}
    try:
        result = q.stop_owned(proc,known,deadline=deadline)
        known.update(result.get('owned_pgids',[]))
        errors.extend(result.get('cleanup_errors',[]))
        diagnostics.extend(result.get('probe_diagnostics',[]))
    except BaseException as exc:
        errors.append(q.monitor_diagnostic(exc,context='owned_cleanup'))
    # A failed cleanup must not erase the known inventory or fabricate a reap.
    try:
        reaped = proc.poll() is not None
    except BaseException as exc:
        reaped = False
        errors.append(q.monitor_diagnostic(exc,context='leader_reap_state'))
    states = []
    for pgid in sorted(known):
        try:
            probe = q.group_probe(pgid)
        except BaseException as exc:
            probe = {'pgid':pgid,'state':'unknown',**q.monitor_diagnostic(exc,context='final_group_probe')}
        states.append(probe)
        if probe['state']=='unknown':
            diagnostics.append(probe)
    survivors = [row['pgid'] for row in states if row['state']!='absent']
    if survivors or not reaped:
        errors.append({'context':'terminal_ownership','error':'Owned absence/reap unconfirmed',
                       'surviving_pgids':survivors,'reaped':reaped})
    return {'owned_pgids':sorted(known),'leader_returncode':proc.returncode,'reaped':reaped,
            'group_absent':not survivors and reaped,'surviving_pgids':survivors,
            'group_states':states,'probe_diagnostics':diagnostics,'cleanup_errors':errors,
            'cleanup_deadline':deadline,'helper_result':result}


def accounting(elapsed, sampled_cpu, children_cpu, supervisor_cpu, monitor_cpu):
    if not all(q.finite(value) for value in (elapsed,sampled_cpu,children_cpu,supervisor_cpu,monitor_cpu)):
        raise ValueError('Invalid check accounting observation')
    allocation = max(elapsed,sampled_cpu,children_cpu)
    return {'elapsed_allocation_s':elapsed,'sampled_process_tree_cpu_s':sampled_cpu,
            'observed_children_cpu_s':children_cpu,'monitor_child_cpu_s':monitor_cpu,
            'charged_allocation_s':allocation,'supervisor_cpu_s':supervisor_cpu,
            'charged_cpu_s':allocation+supervisor_cpu}


def output_audit(folder, state):
    hashes = {}
    for name in ('stdout','stderr'):
        try:
            hashes[name+'_sha256'] = q.sha(Path(folder)/(name+'.log'))
        except BaseException as exc:
            hashes[name+'_sha256'] = None
            retain_error(state,exc,'output_audit:'+name)
    artifacts = {}
    try:
        for path in sorted(Path(folder).iterdir()):
            try:
                if not path.is_file() or path.name == 'result.json':
                    continue
                if path.name in ('stdout.log','stderr.log'):
                    artifacts[path.name] = hashes[path.stem+'_sha256']
                    continue
                artifacts[path.name] = q.sha(path)
            except BaseException as exc:
                artifacts[path.name] = None
                retain_error(state,exc,'artifact_audit:'+path.name)
    except BaseException as exc:
        retain_error(state,exc,'artifact_inventory')
    hashes['artifact_hashes'] = artifacts
    return hashes


def source_inventory():
    checked = q.read(CHECK_ROOT/'attempt01/attempt.json')
    inherited = checked['source_hashes']
    q.verify_hashes(inherited)
    files = [Path(__file__).resolve(),FREEZE_ROOT/'freeze-command.json',
             FREEZE_ROOT/'design.json',ROOT/'research-20261023/CF1_PREPARATION_NATIVE_PROTOCOL.md',
             ROOT/'research-20261023/CF1_PREPARATION_NATIVE_WRAPPERS.md',
             CHECK_ROOT/'accounting.json']
    files += [CHECK_ROOT/'attempt01'/name for name in ('attempt.json','result.json','stdout.log','stderr.log')]
    return {**inherited,**{str(path):q.sha(path) for path in files}}


def main():
    cpu0,wall0 = time.process_time(),time.monotonic()
    carried = None
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    q._monitor_child_cpu_s = 0.
    folder = FREEZE_ROOT/'freeze-attempt01'
    folder.mkdir(parents=True,exist_ok=False)
    command = q.read(FREEZE_ROOT/'freeze-command.json')
    if (not isinstance(command,list) or not all(isinstance(x,str) for x in command)
            or command[:4] != [sys.executable,'-m','experiments.cf1_preparation_preflight','freeze']):
        raise ValueError('Freeze requires explicit same-interpreter metadata-only command')
    registry = folder/'owned-test-groups.jsonl'
    state = {'primary_failure':None,'secondary_errors':[]}
    groups,sources,evidence = set(),{},{}
    proc,anchor = None,None
    peak = sampled_cpu = 0.
    termination = {'owned_pgids':[],'leader_returncode':None,'reaped':False,
                   'group_absent':False,'surviving_pgids':[],'cleanup_errors':[]}

    def interrupted(signum,frame):
        raise KeyboardInterrupt('Check supervisor signal '+str(signum))

    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig,interrupted)
    with (folder/'stdout.log').open('x') as out,(folder/'stderr.log').open('x') as err:
        try:
            prior = CHECK_ROOT/'accounting.json'
            account = q.read(prior)
            if (q.CEILING,q.DISPATCH_STOP,q.SHUTDOWN_RESERVE) != (1800.,1620.,180.):
                raise ValueError('Approved cumulative qualification policy differs')
            carried = account['charged_cpu_s']
            checked = q.read(CHECK_ROOT/'attempt01/result.json')
            if (checked.get('passed') is not True or checked.get('returncode') != 0
                    or not checked.get('accounting_observations_complete') or checked.get('source_changes')
                    or carried < checked['cumulative_qualification_charge_s']):
                raise ValueError('Freeze requires complete passing affected-adapter check accounting')
            q.verify_hashes(account['evidence_hashes'])
            evidence = {**account['evidence_hashes'],str(prior):q.sha(prior)}
            # Prior freeze/reconciliation artifacts are already bound by its immutable inventory.
            q.verify_hashes(evidence)
            if carried+ADMIN+10.>q.DISPATCH_STOP or carried+ADMIN+10.+q.SHUTDOWN_RESERVE>q.CEILING:
                raise ValueError('Insufficient remaining check allocation/reserve')
            sources = source_inventory()
            design = q.read(FREEZE_ROOT/'design.json')
            if (design['package_budget']['absolute_package_ceiling_s']!=PACKAGE_END
                    or carried+10.+FINALIZATION_RESERVE>PACKAGE_END):
                raise ValueError('Insufficient metadata-freeze package headroom')
            anchor = time.monotonic()
            q.write_new(folder/'attempt.json',{'attempt_id':'attempt01','revision':2,'command':command,
                'phase':'comparison_native_freeze','solver_free':True,
                'command_sha256':q.stable(command),
                'parent_monotonic':anchor,'source_hashes':sources,'prior_evidence_hashes':evidence,
                'carried_charge_s':carried+ADMIN,'prior_charge_s':carried,'administration_allowance_s':ADMIN,
                'administration_scope':'No new allowance; prior single shared 20 seconds already included',
                'hard_ceiling_s':q.CEILING,'dispatch_stop_s':q.DISPATCH_STOP,'shutdown_reserve_s':q.SHUTDOWN_RESERVE,
                'wall_limit_s':7.5,'outer_limit_s':10.,'rss_limit_bytes':q.RSS_LIMIT,'solver_free':True})
            table,free = q.monitor_sample(q.monitor_deadline(time.monotonic(),None,anchor+7.5))
            initial_completed = time.monotonic()
            if not q.finite(free) or free>100 or free<10:
                raise ValueError('Unsafe initial check memory monitor')
            env = {**os.environ,'PYTHONPATH':str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1',
                   'EGG_CHECK_PGID_REGISTRY':str(registry),**{key:'1' for key in q.THREAD_KEYS}}
            proc = subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err,start_new_session=True)
            groups.add(proc.pid)
            q.campaign.append(folder/'ownership.jsonl',{'event':'launch','owned_pgids':sorted(groups)})
            last_completed,pressure_since = initial_completed,None
            while proc.poll() is None:
                tick = time.monotonic()
                if tick>=anchor+7.5:
                    raise TimeoutError('Freeze work limit')
                sample = sample_owned(proc,groups,registry,anchor,last_completed)
                last_completed = sample['completed_monotonic']
                peak,sampled_cpu = max(peak,sample['rss_bytes']),max(sampled_cpu,sample['cpu_s'])
                q.campaign.append(folder/'resources.jsonl',sample)
                q.campaign.append(folder/'ownership.jsonl',{'event':'sample','owned_pgids':sorted(groups)})
                if sample['rss_bytes']>q.RSS_LIMIT:
                    raise RuntimeError('Check process-tree RSS limit')
                pressure_since = (last_completed if pressure_since is None else pressure_since) if sample['free_percent']<10 else None
                if pressure_since is not None and last_completed-pressure_since>=5.:
                    raise RuntimeError('Sustained check memory pressure')
                time.sleep(max(0.,q.MONITOR_INTERVAL_S-(time.monotonic()-tick)))
        except BaseException as exc:
            retain_error(state,exc,'check_supervision')
        finally:
            for sig in (signal.SIGTERM,signal.SIGINT):
                signal.signal(sig,signal.SIG_IGN)
            if proc is not None:
                try:
                    ownership.registered_groups(registry,groups)
                except BaseException as exc:
                    retain_error(state,exc,'final_group_registry')
                try:
                    q.campaign.append(folder/'ownership.jsonl',{'event':'before_cleanup','owned_pgids':sorted(groups),
                                      'leader_returncode':proc.returncode,'primary_failure':state['primary_failure']})
                except BaseException as exc:
                    retain_error(state,exc,'ownership_audit')
                termination = cleanup_receipt(proc,groups,anchor+10.)
                state['secondary_errors'].extend(termination['cleanup_errors'])
                if termination['cleanup_errors'] or not termination['group_absent']:
                    retain_error(state,RuntimeError('Owned cleanup incomplete or reported errors'),'cleanup_gate')
    if not (folder/'attempt.json').exists():
        q.write_new(folder/'attempt.json',{'attempt_id':'attempt01','revision':2,'command':command,
                'phase':'comparison_native_freeze','solver_free':True,
            'command_sha256':q.stable(command),
            'source_hashes':sources,'prior_evidence_hashes':evidence,'preflight_failure':state['primary_failure'],
            'carried_charge_s':None if carried is None else carried+ADMIN,
            'administration_allowance_s':ADMIN,'solver_free':True})
    changed = []
    for name,expected in sources.items():
        try:
            if q.sha(name) != expected:
                changed.append(name)
        except OSError:
            changed.append(name)
    output_hashes = output_audit(folder,state)
    try:
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        child_cpu = max(0.,children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime)
    except BaseException as exc:
        retain_error(state,exc,'child_cpu_audit')
        child_cpu = None  # Unknown is retained; later accounting needs reconciliation.
    elapsed = time.monotonic()-(wall0 if anchor is None else anchor)
    charges = accounting(elapsed,sampled_cpu,child_cpu or 0.,time.process_time()-cpu0,q._monitor_child_cpu_s)
    charges['observed_children_cpu_s'] = child_cpu
    charges['accounting_observations_complete'] = child_cpu is not None
    if elapsed>10.:
        retain_error(state,TimeoutError('Freeze outer allocation exceeded 10 seconds'),'outer_deadline')
    # An unreadable prior account is retained as unknown, never reset to zero.
    cumulative = None if carried is None else carried+ADMIN+charges['charged_cpu_s']
    lock,checked_sources = None,{}
    try:
        lock = q.read(FREEZE_ROOT/'lock.json')
        q.verify_hashes(lock['sources'])
        if lock['carried_charge_s'] != carried:
            raise ValueError('Frozen lock carry differs from authoritative prior account')
        checked_sources = q.read(CHECK_ROOT/'attempt01/attempt.json')['source_hashes']
        if any(checked_sources.get(path)!=value for path,value in lock['sources'].items()):
            raise ValueError('Frozen native sources differ from passing checked closure')
        q.verify_hashes(checked_sources)
    except BaseException as exc:
        retain_error(state,exc,'freeze_lock_audit')
    if proc is not None and proc.returncode != 0 and state['primary_failure'] is None:
        retain_error(state,RuntimeError('Metadata freeze exited with return code '+str(proc.returncode)),'pytest_exit')
    if cumulative is None or cumulative>q.CEILING or cumulative+FINALIZATION_RESERVE>PACKAGE_END:
        retain_error(state,RuntimeError('Qualification charge exceeded hard ceiling'),'accounting')
    passed = bool(proc is not None and proc.returncode==0 and termination['group_absent']
                  and not state['primary_failure'] and not state['secondary_errors'] and not changed)
    try:
        prior_accounting_sha = q.sha(CHECK_ROOT/'accounting.json')
    except BaseException as exc:
        prior_accounting_sha = None
        retain_error(state,exc,'prior_accounting_hash')
        passed = False
    result = {'attempt_id':'attempt01','revision':2,'returncode':None if proc is None else proc.returncode,
              'failure':state['primary_failure'],'secondary_errors':state['secondary_errors'],
              'termination':termination,'source_changes':changed,'passed':passed,
              'sampled_peak_rss_bytes':peak,**charges,**output_hashes,
              'cumulative_qualification_charge_s':cumulative,
              'administration_scope':'No new allowance; prior single shared 20 seconds already included',
              'hard_ceiling_s':q.CEILING,'dispatch_stop_s':q.DISPATCH_STOP,'shutdown_reserve_s':q.SHUTDOWN_RESERVE,
              'scope':'One source-bound metadata-only freeze; native launch is separate',
              'policy':'cf1-preparation-native-v2','phase':'comparison_native_freeze',
              'source_hashes':{} if lock is None else lock['sources'],
              'checked_source_hashes':checked_sources,
              'absolute_package_end_s':PACKAGE_END,'analysis_finalization_reserve_s':FINALIZATION_RESERVE,
              'freeze_input_hashes':sources,'prior_accounting_sha256':prior_accounting_sha,
              'prior_charged_cpu_s':carried,
              'lock_sha256':q.sha(FREEZE_ROOT/'lock.json') if (FREEZE_ROOT/'lock.json').is_file() else None}
    q.write_new(folder/'result.json',result)
    print(json.dumps(result,indent=2))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
