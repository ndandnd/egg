"""One fresh source gate after the preserved metadata freeze failure."""
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'research-20261023'))
import run_comparison_binding_checks as reviewed

q, ownership = reviewed.q, reviewed.ownership
retain_error = reviewed.retain_error
CARRIED, ADMIN = 2443.974196631565, 0.
PACKAGE_END, FINALIZATION_RESERVE = 2463.974196631565, 5.
APPROVED_PACKAGE_START, CAMPAIGN_END = 2426.723449631016, 2651.723449631016
BASE = ROOT/'research-20261024/cf1-entry-repaired-checks'
DESIGN = BASE/'attempt05-design'
RESUMPTION = ROOT/'research-20261024/cf1-resumption'
TESTS = ('test_cf1_entry_repaired.py',)
POLICY = 'cf1-entry-repaired-v5'


QUALIFIED_TEST_DEPENDENCIES = (
    'test_constructive_controls.py', 'test_comparison_native_adapter.py',
    'test_cf1_preparation_preflight.py', 'test_cf1_small_mechanism_preflight.py',
    'test_cf1_small_mechanism_approved.py', 'test_launch_accounting.py',
    'test_launch_prefix_initializer.py', 'test_launch_entry_preparation.py')


def source_inventory():
    inherited = q.campaign.sources()  # Full current experiment/egglab source bytes only.
    paths = [ROOT/'src/tests'/name for name in TESTS+QUALIFIED_TEST_DEPENDENCIES]
    paths += [ROOT/relative for relative in (
        'research-20261023/run_comparison_binding_checks.py',
        'research-20261023/run_recovery_runner_checks.py',
        'research-20261023/run_coordinator_checks.py',
        'research-20261024/CF1_FRESH_MECHANISM_PROTOCOL.md',
        'research-20261024/CF1_FRESH_DECISION_REVIEW.md',
        'research-20261024/CF1_FRESH_IMPLEMENTATION_DESIGN.md',
        'research-20261024/CF1_FRESH_RECEIPT_NOTE.md',
        'research-20261024/CF1_V5_IMPLEMENTATION.md',
        'research-20261024/CF1_V5_OWNER_DESIGN.md',
        'research-20261024/CF1_V5_SOURCE_REVIEW.md',
        'research-20261024/CF1_V5_SOURCE_PROTOCOL.md',
        'research-20261024/CF1_V5_SOURCE_WRAPPER.md',
        'research-20261024/CF1_RESUMPTION_PROTOCOL.md',
        'research-20261024/CF1_RESUMPTION_BINDINGS.md',
        'research-20261024/CF1_RESUMPTION_REVIEW.md',
        'research-20261024/CF1_RESUMPTION_WRAPPERS.md',
        'research-20261024/run_cf1_resumption_freeze.py',
        'research-20261024/CF1_RESUMPTION2_PROTOCOL.md',
        'research-20261024/CF1_RESUMPTION2_WRAPPERS.md',
        'research-20261024/run_cf1_resumption2_freeze.py',
        'research-20261024/cf1-resumption/native-launcher-v5b.py',
        'research-20261024/cf1-resumption/freeze-preparation2.py',
        'research-20261024/cf1-entry-repaired-v5/freeze-attempt01/result.json',
        'research-20261024/cf1-entry-repaired-v5/freeze-whole-wrapper-output.json',
        'research-20261024/cf1-entry-repaired-v5/freeze-whole-wrapper-time.txt',
        'research-20261024/cf1-entry-repaired-checks/attempt04-accounting.json')]
    paths += [Path(__file__).resolve(), DESIGN/'prospective-budget.json', DESIGN/'command.json',
              RESUMPTION/'accepted-carry.json', RESUMPTION/'approval2.json',
              RESUMPTION/'failed-freeze-accounting.json', RESUMPTION/'manifest2-preparation.py']
    return {**inherited, **{str(path): q.sha(path) for path in sorted(set(paths))}}


def verify_approval():
    approval = q.read(RESUMPTION/'approval2.json')
    expected = {'policy': POLICY, 'hard_ceiling_s': 3000.,
        'dispatch_stop_s': 2820., 'shutdown_reserve_s': 180.,
        'package_start_s': APPROVED_PACKAGE_START, 'package_limit_s': 225.,
        'absolute_package_ceiling_s': CAMPAIGN_END,
        'absolute_package_end_s': CAMPAIGN_END,
        'analysis_finalization_reserve_s': 30., 'supervision_reserve_s': 45.,
        'source_phase_limit_s': 20., 'metadata_phase_s': 25.,
        'metadata_freeze_limit_s': 25.,
        'metadata_work_s': 15., 'metadata_outer_s': 17.5,
        'current_retained_carry_s': CARRIED, 'new_source_attempt': 'attempt05',
        'fresh_native_namespace': 'research-20261024/cf1-entry-repaired-v5b',
        'worker_allocation_s': 62.5, 'owner_precharge_s': 7.5,
        'tasks': 1, 'trips': 40, 'seed': 17, 'tariff': 'day',
        'fault': None, 'threads': 1, 'rss_limit_bytes': 5*1024**3,
        'automatic_retry': False, 'scope': 'same inspected50997/40 CF1seed17daynofault'}
    if (any(approval.get(key) != value or
            isinstance(approval.get(key), bool) != isinstance(value, bool)
            for key, value in expected.items())
            or not isinstance(approval.get('scope'), str) or not approval['scope'].strip()
            or not isinstance(approval.get('human_reply'), str) or not approval['human_reply'].strip()):
        raise ValueError('Explicit resumption approval/scope/human reply differs')


def preflight(command):
    verify_approval()
    prior = RESUMPTION/'failed-freeze-accounting.json'
    account = q.read(prior)
    if (account['charged_cpu_s'] != CARRIED or account['policy'] != POLICY
            or account['phase'] != 'failed_metadata_freeze_preservation'
            or account['accepted_conservative_guard'] is not True
            or account['prior_actual_cpu_s'] is not None
            or account['accounting_observations_complete'] is not True
            or account['historical_accounting_observations_complete'] is not False
            or account['freeze_passed'] is not False or account['source_gate_passed'] is not True
            or account['source_gate_attempt'] != 'attempt04'
            or account['native_dispatch'] is not False
            or account['owned_groups_absent_and_reaped'] is not True
            or (account['hard_ceiling_s'], account['dispatch_stop_s'],
                account['shutdown_reserve_s']) != (3000., 2820., 180.)):
        raise ValueError('Preserved failed-freeze carry differs or invents historical CPU completeness')
    prior_result = q.read(ROOT/'research-20261024/cf1-entry-repaired-v5/freeze-attempt01/result.json')
    if (prior_result['passed'] is not False or prior_result['revision'] != 5
            or prior_result['policy'] != POLICY or prior_result['attempt_id'] != 'attempt01'
            or prior_result['termination']['reaped'] is not True
            or prior_result['termination']['group_absent'] is not True
            or prior_result['termination']['surviving_pgids'] != []):
        raise ValueError('Prior metadata freeze failure/owned closure differs')
    source_account = q.read(BASE/'attempt04-accounting.json')
    if (source_account['policy'] != POLICY or source_account['check_passed'] is not True
            or source_account['charged_cpu_s'] != account['prior_charge_s']
            or source_account['accounting_observations_complete'] is not True
            or source_account['owned_groups_absent_and_reaped'] is not True
            or source_account['historical_accounting_observations_complete'] is not False
            or source_account['prior_actual_cpu_s'] is not None):
        raise ValueError('Prior passing source04 reconciliation differs from failed-freeze predecessor')
    evidence = {**source_account['evidence_hashes'], str(prior): q.sha(prior),
                **{str(Path(path)): q.sha(path) for path in account['evidence_paths'].values()}}
    q.verify_hashes(evidence)  # Bound historical bytes only; no research input parsing.
    expected = {'initial_charge_s': CARRIED, 'absolute_package_end_s': PACKAGE_END,
                'administration_allowance_s': ADMIN, 'additional_hard_cap_s': 20.,
                'work_limit_s': 10., 'outer_limit_s': 12.5,
                'inclusive_check_planning_s': 15., 'analysis_finalization_reserve_s': 5.,
                'threads': 1, 'rss_limit_bytes': 5*1024**3, 'automatic_retry': False,
                'native_dispatch_allowed': False, 'metadata_freeze_allowed': False,
                'research_asset_access_allowed': False}
    design = q.read(DESIGN/'prospective-budget.json')
    if any(isinstance(design[key], bool) != isinstance(value, bool)
           or design[key] != value for key, value in expected.items()):
        raise ValueError('Prospective affected-check package differs')
    if (CARRIED+15.+FINALIZATION_RESERVE > PACKAGE_END or PACKAGE_END > CAMPAIGN_END
            or PACKAGE_END > q.DISPATCH_STOP or PACKAGE_END+q.SHUTDOWN_RESERVE > q.CEILING):
        raise ValueError('Insufficient old/new dispatch headroom or shutdown reserve')
    sources = source_inventory()
    manifest = q.read(DESIGN/'command.json')
    if (manifest['command'] != command or manifest['selected_tests'] != list(TESTS)
            or manifest['automatic_retry'] is not False
            or any(manifest[key] is not False for key in
                   ('native_dispatch_allowed', 'metadata_freeze_allowed', 'research_asset_access_allowed'))):
        raise ValueError('Prospective command differs from this single pure gate')
    frozen = manifest['source_hashes']
    if any(frozen.get(path) != digest for path, digest in sources.items()
           if path != str(DESIGN/'command.json')):
        raise ValueError('Prospective command omits or changes an affected source')
    q.verify_hashes(frozen)
    return sources, evidence


def main():
    if len(sys.argv) != 1:
        raise ValueError('Only the prospectively recorded single gate command is allowed')
    cpu0, anchor = time.process_time(), time.monotonic()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    # Process-local approved policy; historical helper/source bytes remain unchanged.
    q.CEILING, q.DISPATCH_STOP, q.SHUTDOWN_RESERVE = 3000., 2820., 180.
    q._monitor_child_cpu_s = 0.
    folder = BASE/'attempt05'
    folder.mkdir(parents=True, exist_ok=False)  # No overwrite, resume, or automatic retry.
    command = [str(ROOT/'.venv-local/bin/python'), '-m', 'pytest', '-q',
               'src/tests/test_cf1_entry_repaired.py']
    wrapper_command = [str(ROOT/'.venv-local/bin/python'), str(Path(__file__).resolve())]
    registry = folder/'owned-test-groups.jsonl'
    state = {'primary_failure': None, 'secondary_errors': []}
    groups, sources, evidence = set(), {}, {}
    proc, peak, sampled_cpu = None, 0., 0.
    termination = {'owned_pgids': [], 'leader_returncode': None, 'reaped': False,
                   'group_absent': False, 'surviving_pgids': [], 'cleanup_errors': []}
    attempt = {'attempt_id': 'attempt05', 'revision': 5, 'command': command,
               'executed_tests': list(TESTS), 'hashed_qualified_test_dependencies': list(QUALIFIED_TEST_DEPENDENCIES),
               'command_sha256': q.stable(command), 'parent_monotonic': anchor,
               'carried_charge_s': CARRIED, 'prior_charge_s': CARRIED,
               'carry_is_accepted_conservative_guard': True, 'prior_actual_cpu_s': None,
               'historical_accounting_observations_complete': False,
               'administration_allowance_s': ADMIN, 'hard_ceiling_s': q.CEILING,
               'dispatch_stop_s': q.DISPATCH_STOP, 'shutdown_reserve_s': q.SHUTDOWN_RESERVE,
               'wall_limit_s': 10., 'outer_limit_s': 12.5, 'inclusive_planning_s': 15.,
               'absolute_package_end_s': PACKAGE_END,
               'analysis_finalization_reserve_s': FINALIZATION_RESERVE,
               'rss_limit_bytes': q.RSS_LIMIT, 'solver_free': True, 'policy': POLICY}

    def interrupted(signum, frame):
        raise KeyboardInterrupt('Check supervisor signal '+str(signum))

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, interrupted)
    with (folder/'stdout.log').open('x') as out, (folder/'stderr.log').open('x') as err:
        try:
            sources, evidence = preflight(wrapper_command)
            q.write_new(folder/'attempt.json', {**attempt, 'source_hashes': sources,
                                               'prior_evidence_hashes': evidence})
            table, free = q.monitor_sample(q.monitor_deadline(time.monotonic(), None, anchor+10.))
            last_completed, pressure_since = time.monotonic(), None
            if not q.finite(free) or free > 100 or free < 10:
                raise ValueError('Unsafe initial check memory monitor')
            env = {**os.environ, 'PYTHONPATH': str(ROOT/'src'), 'PYTHONDONTWRITEBYTECODE': '1',
                   'EGG_CHECK_PGID_REGISTRY': str(registry), **{key: '1' for key in q.THREAD_KEYS}}
            if time.monotonic() >= anchor+10.:
                raise TimeoutError('Check prelaunch wall limit')
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                    start_new_session=True)
            groups.add(proc.pid)
            q.campaign.append(folder/'ownership.jsonl', {'event': 'launch', 'owned_pgids': sorted(groups)})
            while proc.poll() is None:
                tick = time.monotonic()
                if tick >= anchor+10.:
                    raise TimeoutError('Check wall limit')
                sample = reviewed.sample_owned(proc, groups, registry, anchor, last_completed)
                last_completed = sample['completed_monotonic']
                peak, sampled_cpu = max(peak, sample['rss_bytes']), max(sampled_cpu, sample['cpu_s'])
                q.campaign.append(folder/'resources.jsonl', sample)
                q.campaign.append(folder/'ownership.jsonl', {'event': 'sample', 'owned_pgids': sorted(groups)})
                children = resource.getrusage(resource.RUSAGE_CHILDREN)
                reaped_cpu = max(0., children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime)
                active = max(last_completed-anchor, sampled_cpu+q._monitor_child_cpu_s, reaped_cpu)
                active += max(0., time.process_time()-cpu0)
                if CARRIED+active+2.5 >= min(CARRIED+15., PACKAGE_END-FINALIZATION_RESERVE):
                    raise TimeoutError('Fresh-CF1 check finalization reserve')
                if sample['rss_bytes'] > q.RSS_LIMIT:
                    raise RuntimeError('Check process-tree RSS limit')
                pressure_since = ((last_completed if pressure_since is None else pressure_since)
                                  if sample['free_percent'] < 10 else None)
                if pressure_since is not None and last_completed-pressure_since >= 5.:
                    raise RuntimeError('Sustained check memory pressure')
                time.sleep(max(0., q.MONITOR_INTERVAL_S-(time.monotonic()-tick)))
        except BaseException as exc:
            retain_error(state, exc, 'check_supervision')
        finally:
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, signal.SIG_IGN)
            if proc is not None:
                try:
                    ownership.registered_groups(registry, groups)
                except BaseException as exc:
                    retain_error(state, exc, 'final_group_registry')
                try:
                    q.campaign.append(folder/'ownership.jsonl', {'event': 'before_cleanup',
                        'owned_pgids': sorted(groups), 'leader_returncode': proc.returncode,
                        'primary_failure': state['primary_failure']})
                except BaseException as exc:
                    retain_error(state, exc, 'ownership_audit')
                termination = reviewed.cleanup_receipt(proc, groups, anchor+12.5)
                state['secondary_errors'].extend(termination['cleanup_errors'])
                if termination['cleanup_errors'] or not termination['group_absent']:
                    retain_error(state, RuntimeError('Owned cleanup incomplete or reported errors'), 'cleanup_gate')
    if not (folder/'attempt.json').exists():
        q.write_new(folder/'attempt.json', {**attempt, 'source_hashes': sources,
            'prior_evidence_hashes': evidence, 'preflight_failure': state['primary_failure']})
    changed = []
    for path, expected in {**evidence, **sources}.items():
        try:
            if q.sha(path) != expected:
                changed.append(path)
        except OSError:
            changed.append(path)
    output_hashes = reviewed.output_audit(folder, state)
    child_cpu = None
    try:
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        child_cpu = max(0., children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime)
    except BaseException as exc:
        retain_error(state, exc, 'child_cpu_audit')
    elapsed = time.monotonic()-anchor
    sampled_with_monitor = sampled_cpu+q._monitor_child_cpu_s
    charges = reviewed.accounting(elapsed, sampled_with_monitor, child_cpu or 0.,
                                 time.process_time()-cpu0, q._monitor_child_cpu_s)
    charges.update(sampled_process_tree_cpu_s=sampled_cpu, sampled_plus_monitor_cpu_s=sampled_with_monitor,
                   observed_children_cpu_s=child_cpu, accounting_observations_complete=child_cpu is not None)
    cumulative = CARRIED+ADMIN+charges['charged_cpu_s']
    if elapsed > 12.5 or cumulative > CARRIED+15. or cumulative+FINALIZATION_RESERVE > PACKAGE_END:
        retain_error(state, RuntimeError('Fresh-CF1 check outer/package cap exceeded'), 'package_accounting')
    if proc is not None and proc.returncode != 0:
        retain_error(state, RuntimeError('Pytest exited with return code '+str(proc.returncode)), 'pytest_exit')
    passed = bool(proc is not None and proc.returncode == 0 and termination['group_absent']
                  and not state['primary_failure'] and not state['secondary_errors'] and not changed)
    result = {**attempt, 'returncode': None if proc is None else proc.returncode,
              'failure': state['primary_failure'], 'secondary_errors': state['secondary_errors'],
              'termination': termination, 'source_changes': changed, 'passed': passed,
              'sampled_peak_rss_bytes': peak, **charges, **output_hashes,
              'cumulative_qualification_charge_s': cumulative,
              'administration_scope': 'No new administration allowance',
              'scope': 'Fake-execution source qualification only; no research input, real metadata freeze, numerical mechanism qualification or native clearance'}
    q.write_new(folder/'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
