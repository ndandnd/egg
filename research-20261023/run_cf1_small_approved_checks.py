"""One approved CF1 engineering40 source gate; no native execution or data access."""
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

CARRIED, ADMIN = 1509.9511370494984, 0.
PACKAGE_END, FINALIZATION_RESERVE = 1674.9511370494984, 30.
PARENT_CLOSURE_RESERVE = 5.
TESTS = ('test_cf1_small_mechanism_approved.py',)
# Historical qualified tests are hashed dependencies, not executed by this unit gate.
QUALIFIED_TEST_DEPENDENCIES = ('test_constructive_controls.py','test_comparison_native_adapter.py',
                              'test_cf1_preparation_preflight.py','test_cf1_small_mechanism_preflight.py')


def retain_error(state, exc, context):
    diagnostic = q.monitor_diagnostic(exc,context=context)
    if state.get('primary_failure') is None:
        state['primary_failure'] = diagnostic
    else:
        state.setdefault('secondary_errors',[]).append(diagnostic)
    return diagnostic


def sample_owned(proc, groups, registry, anchor, last_completed):
    tick = time.monotonic()
    deadline = q.monitor_deadline(tick,last_completed,anchor+10.)
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
    files = [path for name in ('egglab','experiments') for path in (ROOT/'src'/name).rglob('*.py')]
    files += [ROOT/'src/tests'/name for name in TESTS+QUALIFIED_TEST_DEPENDENCIES]
    files += [Path(__file__).resolve(),ROOT/'research-20261023/run_recovery_runner_checks.py',
              ROOT/'research-20261023/run_coordinator_checks.py']
    files += [ROOT/'research-20261023'/name for name in (
        'CF1_SMALL_APPROVED_PROTOCOL.md','CF1_SMALL_APPROVED_REVIEW.md','CF1_SMALL_APPROVED_WRAPPERS.md',
        'run_cf1_small_approved_freeze.py','cf1-small-approved-v4/approval.json',
        'cf1-small-approved-checks/prospective-budget.json',
        'cf1-small-approved-checks/command.json')]
    return {str(path):q.sha(path) for path in sorted(set(files))}


def verify_approval():
    approval = q.read(ROOT/'research-20261023/cf1-small-approved-v4/approval.json')
    expected = {'policy':'cf1-small-approved-v4','hard_ceiling_s':1920.,
        'dispatch_stop_s':1740.,'shutdown_reserve_s':180.,
        'package_start_s':1509.9511370494984,'package_limit_s':165.,
        'absolute_package_end_s':1674.9511370494984,
        'analysis_finalization_reserve_s':30.,'supervision_reserve_s':45.,
        'tasks':1,'trips':40}
    if any(approval.get(key)!=value for key,value in expected.items()):
        raise ValueError('Explicit approved CF1 package policy differs')


def main():
    # This explicit approval changes policy only in this launcher process.
    q.CEILING,q.DISPATCH_STOP,q.SHUTDOWN_RESERVE = 1920.,1740.,180.
    cpu0,wall0 = time.process_time(),time.monotonic()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    q._monitor_child_cpu_s = 0.
    folder = ROOT/'research-20261023/cf1-small-approved-checks/attempt01'
    folder.mkdir(parents=True,exist_ok=False)
    command = [str(ROOT/'.venv-local/bin/python'),'-m','pytest','-q',
               *['src/tests/'+name for name in TESTS]]
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
            verify_approval()
            prior = ROOT/'research-20261023/comparison-binding-checks/accounting.json'
            account = q.read(prior)
            if (q.CEILING,q.DISPATCH_STOP,q.SHUTDOWN_RESERVE) != (1920.,1740.,180.):
                raise ValueError('Approved cumulative qualification policy differs')
            if account['charged_cpu_s'] != CARRIED:
                raise ValueError('Reconcile authoritative prior check accounting')
            q.verify_hashes(account['evidence_hashes'])
            evidence = {**account['evidence_hashes'],str(prior):q.sha(prior)}
            # Prior freeze/reconciliation artifacts are already bound by its immutable inventory.
            q.verify_hashes(evidence)
            if CARRIED+ADMIN+15.>q.DISPATCH_STOP or CARRIED+ADMIN+15.+q.SHUTDOWN_RESERVE>q.CEILING:
                raise ValueError('Insufficient remaining check allocation/reserve')
            design = q.read(ROOT/'research-20261023/cf1-small-approved-checks/prospective-budget.json')
            if (design['initial_charge_s']!=CARRIED or design['absolute_package_end_s']!=PACKAGE_END
                    or CARRIED+15.+FINALIZATION_RESERVE>PACKAGE_END):
                raise ValueError('Insufficient affected-check package headroom')
            if q.read(ROOT/'research-20261023/cf1-small-approved-checks/command.json') != command:
                raise ValueError('Source-check command differs from prospective command')
            sources = source_inventory()
            anchor = time.monotonic()
            q.write_new(folder/'attempt.json',{'attempt_id':'attempt01','revision':4,'command':command,
                'executed_tests':list(TESTS),'hashed_qualified_test_dependencies':list(QUALIFIED_TEST_DEPENDENCIES),
                'command_sha256':q.stable(command),
                'parent_monotonic':anchor,'source_hashes':sources,'prior_evidence_hashes':evidence,
                'carried_charge_s':CARRIED+ADMIN,'prior_charge_s':CARRIED,'administration_allowance_s':ADMIN,
                'administration_scope':'No new allowance; prior single shared 20 seconds already included',
                'hard_ceiling_s':q.CEILING,'dispatch_stop_s':q.DISPATCH_STOP,'shutdown_reserve_s':q.SHUTDOWN_RESERVE,
                'wall_limit_s':10.,'outer_limit_s':12.5,'inclusive_planning_s':15.,
                'absolute_package_end_s':PACKAGE_END,'analysis_finalization_reserve_s':FINALIZATION_RESERVE,
                'parent_closure_reserve_s':PARENT_CLOSURE_RESERVE,
                'rss_limit_bytes':q.RSS_LIMIT,'solver_free':True})
            table,free = q.monitor_sample(q.monitor_deadline(time.monotonic(),None,anchor+10.))
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
                if tick>=anchor+10.:
                    raise TimeoutError('Check wall limit')
                sample = sample_owned(proc,groups,registry,anchor,last_completed)
                last_completed = sample['completed_monotonic']
                peak,sampled_cpu = max(peak,sample['rss_bytes']),max(sampled_cpu,sample['cpu_s'])
                q.campaign.append(folder/'resources.jsonl',sample)
                q.campaign.append(folder/'ownership.jsonl',{'event':'sample','owned_pgids':sorted(groups)})
                observed_children = resource.getrusage(resource.RUSAGE_CHILDREN)
                reaped_cpu = max(0.,observed_children.ru_utime+observed_children.ru_stime
                                 -child0.ru_utime-child0.ru_stime)
                active_charge = max(last_completed-anchor,
                                    sampled_cpu+q._monitor_child_cpu_s,reaped_cpu)
                active_charge += max(0.,time.process_time()-cpu0)
                if CARRIED+active_charge+2.5>=min(CARRIED+15.,PACKAGE_END-FINALIZATION_RESERVE):
                    raise TimeoutError('Approved-small-CF1-check package finalization reserve')
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
                termination = cleanup_receipt(proc,groups,anchor+12.5)
                state['secondary_errors'].extend(termination['cleanup_errors'])
                if termination['cleanup_errors'] or not termination['group_absent']:
                    retain_error(state,RuntimeError('Owned cleanup incomplete or reported errors'),'cleanup_gate')
    if not (folder/'attempt.json').exists():
        q.write_new(folder/'attempt.json',{'attempt_id':'attempt01','revision':4,'command':command,
                'executed_tests':list(TESTS),'hashed_qualified_test_dependencies':list(QUALIFIED_TEST_DEPENDENCIES),
            'command_sha256':q.stable(command),
            'source_hashes':sources,'prior_evidence_hashes':evidence,'preflight_failure':state['primary_failure'],
            'carried_charge_s':CARRIED+ADMIN,'administration_allowance_s':ADMIN,'solver_free':True})
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
    if elapsed>12.5:
        retain_error(state,TimeoutError('Check outer allocation exceeded 12.5 seconds'),'outer_deadline')
    cumulative = CARRIED+ADMIN+charges['charged_cpu_s']
    if cumulative>CARRIED+15. or cumulative+FINALIZATION_RESERVE>PACKAGE_END:
        retain_error(state,RuntimeError('Approved-small-CF1-check package hard cap exceeded'),'package_accounting')
    if proc is not None and proc.returncode != 0 and state['primary_failure'] is None:
        retain_error(state,RuntimeError('Pytest exited with return code '+str(proc.returncode)),'pytest_exit')
    if cumulative>q.CEILING:
        retain_error(state,RuntimeError('Qualification charge exceeded hard ceiling'),'accounting')
    passed = bool(proc is not None and proc.returncode==0 and termination['group_absent']
                  and not state['primary_failure'] and not state['secondary_errors'] and not changed)
    result = {'attempt_id':'attempt01','revision':4,'returncode':None if proc is None else proc.returncode,
              'failure':state['primary_failure'],'secondary_errors':state['secondary_errors'],
              'termination':termination,'source_changes':changed,'passed':passed,
              'sampled_peak_rss_bytes':peak,**charges,**output_hashes,
              'cumulative_qualification_charge_s':cumulative,
              'administration_scope':'No new allowance; prior single shared 20 seconds already included',
              'hard_ceiling_s':q.CEILING,'dispatch_stop_s':q.DISPATCH_STOP,'shutdown_reserve_s':q.SHUTDOWN_RESERVE,
              'policy':'cf1-small-approved-v4','inclusive_planning_s':15.,
              'absolute_package_end_s':PACKAGE_END,'analysis_finalization_reserve_s':FINALIZATION_RESERVE,
              'parent_closure_reserve_s':PARENT_CLOSURE_RESERVE,
              'scope':'One affected approved CF1 engineering40 configuration fake gate; metadata freeze/native execution are separate'}
    q.write_new(folder/'result.json',result)
    print(json.dumps(result,indent=2))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
