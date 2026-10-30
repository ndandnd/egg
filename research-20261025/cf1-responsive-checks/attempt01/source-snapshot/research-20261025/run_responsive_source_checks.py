"""One prospective v6 fake-execution source gate; no primitive/native dispatch."""
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
CARRIED, ADMIN = 2541.8243213823207, 0.
PACKAGE_END, FINALIZATION_RESERVE = 2571.8243213823207, 5.
CAMPAIGN_END = 3026.723449631016
BASE = ROOT/'research-20261025/cf1-responsive-checks'
DESIGN = BASE/'attempt01-design'
HERE = ROOT/'research-20261025/responsive-supervision'
TESTS = ('test_responsive_supervision_v6.py',)
QUALIFIED_TEST_DEPENDENCIES = (
    'test_constructive_controls.py', 'test_comparison_native_adapter.py',
    'test_cf1_preparation_preflight.py', 'test_cf1_small_mechanism_preflight.py',
    'test_cf1_small_mechanism_approved.py', 'test_launch_accounting.py',
    'test_launch_prefix_initializer.py', 'test_launch_entry_preparation.py',
    'test_cf1_entry_repaired.py')
POLICY = 'cf1-responsive-supervision-v6'
NON_NATIVE_SAMPLE_POLICY = {'scope': 'source-tests-and-metadata-only',
    'process_sample_timeout_s': 1., 'completed_sample_gap_limit_s': 1.25,
    'poll_interval_s': .05, 'absolute_work_deadline_clipping': True,
    'numerical_monitor_changed': False}


def non_native_deadline(tick, last_completed, work_end):
    gap_end = work_end if last_completed is None else last_completed+1.25
    return min(tick+1., gap_end, work_end)


def sample_owned(proc, groups, registry, anchor, last_completed):
    tick = time.monotonic()
    deadline = non_native_deadline(tick, last_completed, anchor+20.)
    ownership.registered_groups(registry, groups)
    table, free = q.monitor_sample(deadline)
    rows = ownership.owned_rows(proc.pid, groups, table)
    ownership.registered_groups(registry, groups)
    rows = [row for pid, row in table.items() if row['pgid'] in groups or row in rows]
    completed = time.monotonic()
    if completed>deadline or (last_completed is not None and completed-last_completed>1.25):
        raise q.MonitorError(q.monitor_diagnostic(TimeoutError('Complete sample gap exceeded 1.25s'),
                             context='complete_sample', deadline=deadline))
    if not q.finite(free) or free>100:
        raise ValueError('Invalid check memory monitor')
    return {'completed_monotonic': completed, 'sample_deadline': deadline,
            'rss_bytes': sum(row['rss'] for row in rows), 'cpu_s': sum(row['cpu'] for row in rows),
            'free_percent': free, 'owned_pgids': sorted(groups)}


def source_inventory():
    inherited = q.campaign.sources()
    paths = [ROOT/'src/tests'/name for name in TESTS+QUALIFIED_TEST_DEPENDENCIES]
    paths += [ROOT/relative for relative in (
        'research-20261023/run_comparison_binding_checks.py',
        'research-20261023/run_recovery_runner_checks.py',
        'research-20261023/run_coordinator_checks.py',
        'research-20261025/NATIVE_MONITOR_FAILURE.md',
        'research-20261025/NATIVE_MONITOR_DESIGN.md',
        'research-20261025/NATIVE_MONITOR_IMPLEMENTATION_PROTOCOL.md',
        'research-20261025/RESPONSIVE_CORE_INTEGRATION.md',
        'research-20261025/RESPONSIVE_SOURCE_GATE_PROTOCOL.md',
        'research-20261025/responsive-supervision/budget-adoption.json',
        'research-20261025/responsive-supervision/prepare-source-gate.py',
        'research-20261025/responsive-supervision/finalize-source-account.py')]
    paths += [Path(__file__).resolve(), DESIGN/'prospective-budget.json', DESIGN/'command.json']
    return {**inherited, **{str(path): q.sha(path) for path in sorted(set(paths))}}


def preflight(command):
    adoption_path = HERE/'budget-adoption.json'
    adoption = q.read(adoption_path)
    expected_adoption = {'policy': POLICY, 'phase': 'prospective_resource_policy_adoption',
        'charged_cpu_s': CARRIED, 'prior_charge_s': CARRIED, 'current_charge_s': 0.,
        'adoption_is_administrative_not_new_cpu_measurement': True,
        'historical_actual_cpu_s': None, 'historical_accounting_observations_complete': False,
        'accepted_conservative_guard': True, 'legacy_owner_observations_complete': False,
        'hard_total_ceiling_s': 3600., 'dispatch_stop_s': 3420., 'shutdown_reserve_s': 180.,
        'package_start_s': 2426.723449631016, 'package_limit_s': 600.,
        'package_hard_end_s': CAMPAIGN_END, 'actual_recorded_host_capacity': 12,
        'capacity_upper_bound': 12, 'capacity_uncertainty_rate_upper_bound': 15,
        'controller_supervision_cpu_cap_s': 31.5, 'owner_cpu_cap_s': 15.,
        'native_workers': 1, 'native_threads': 1, 'aggregate_sampled_rss_limit_bytes': 5*1024**3,
        'case_scope': 'same inspected synthetic50997/40 CF1seed17/day/no-fault',
        'source_gate_passed': False, 'primitive_passed': False, 'metadata_freeze_passed': False,
        'native_dispatch_allowed': False, 'automatic_retry': False}
    expected_adoption['protocol'] = str(ROOT/'research-20261025/NATIVE_MONITOR_IMPLEMENTATION_PROTOCOL.md')
    if (any(adoption.get(key)!=value or isinstance(adoption.get(key), bool)!=isinstance(value, bool)
            for key, value in expected_adoption.items())
            or not isinstance(adoption.get('human_authority'), str) or not adoption['human_authority'].strip()
            or adoption.get('prospective_components_s') != {'source': 30., 'no_native_primitive': 20.,
                'metadata_freeze': 25., 'whole_entry_precharge': 65., 'native_outer': 62.5,
                'supervision': 120., 'analysis_finalization': 45.}):
        raise ValueError('Prospective v6 adoption or retained uncertainty differs')
    prior = ROOT/'research-20261024/cf1-resumption/failed-native-monitor-accounting.json'
    if adoption.get('previous_accounting') != str(prior):
        raise ValueError('V6 adoption does not name the preserved failed v5e account')
    account = q.read(prior)
    if (account['policy']!='cf1-entry-repaired-v5'
            or account['phase']!='failed_native_owner_monitor_preservation'
            or account['charged_cpu_s']!=CARRIED or account['source_gate_attempt']!='attempt08'
            or account['source_gate_passed'] is not True or account['freeze_passed'] is not True
            or account['controller_entry_passed'] is not False or account['entry_gate_issued'] is not False
            or account['entry_precharge_recorded'] is not False or account['native_dispatch'] is not False
            or account['owned_groups_absent_and_reaped'] is not True
            or account['accounting_observations_complete'] is not True
            or account['actual_owner_receipt_observations_complete'] is not False
            or account['historical_accounting_observations_complete'] is not False
            or account['prior_actual_cpu_s'] is not None or account['accepted_conservative_guard'] is not True
            or (account['hard_total_ceiling_s'], account['dispatch_stop_s'], account['shutdown_reserve_s'])
                !=(3000.,2820.,180.)):
        raise ValueError('Preserved failed v5e account differs; no legacy observations upgraded')
    source_account = q.read(ROOT/'research-20261024/cf1-entry-repaired-checks/attempt08-accounting.json')
    freeze_account = q.read(ROOT/'research-20261024/cf1-entry-repaired-v5e/freeze-accounting.json')
    if (source_account['check_passed'] is not True
            or source_account['charged_cpu_s']!=freeze_account['prior_charge_s']
            or freeze_account['charged_cpu_s']!=account['prior_charge_s']
            or freeze_account['freeze_passed'] is not True or freeze_account['metadata_freeze'] is not True
            or freeze_account['native_dispatch'] is not False):
        raise ValueError('Preserved source08/freeze/failed-owner predecessor charge chain differs')
    evidence = {**source_account['evidence_hashes'], **freeze_account['evidence_hashes'],
        str(prior): q.sha(prior), str(adoption_path): q.sha(adoption_path),
        **{str(Path(path)): q.sha(path) for path in account['evidence_paths'].values()}}
    q.verify_hashes(evidence)
    expected = {'initial_charge_s': CARRIED, 'absolute_package_end_s': PACKAGE_END,
        'administration_allowance_s': ADMIN, 'additional_hard_cap_s': 30.,
        'work_limit_s': 20., 'outer_limit_s': 22.5, 'inclusive_check_planning_s': 25.,
        'analysis_finalization_reserve_s': 5., 'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
        'threads': 1, 'rss_limit_bytes': 5*1024**3, 'automatic_retry': False,
        'native_dispatch_allowed': False, 'metadata_freeze_allowed': False,
        'research_asset_access_allowed': False, 'model_source_asset_access_allowed': False}
    design = q.read(DESIGN/'prospective-budget.json')
    if any(design.get(key)!=value or isinstance(design.get(key), bool)!=isinstance(value, bool)
           for key, value in expected.items()):
        raise ValueError('Prospective v6 source phase differs')
    if (CARRIED+25.+FINALIZATION_RESERVE>PACKAGE_END or PACKAGE_END>CAMPAIGN_END
            or PACKAGE_END>q.DISPATCH_STOP or PACKAGE_END+q.SHUTDOWN_RESERVE>q.CEILING):
        raise ValueError('Insufficient source/package/global shutdown headroom')
    sources = source_inventory()
    manifest = q.read(DESIGN/'command.json')
    if (manifest['command']!=command or manifest['selected_tests']!=list(TESTS)
            or manifest.get('non_native_sample_policy')!=NON_NATIVE_SAMPLE_POLICY
            or manifest['automatic_retry'] is not False
            or any(manifest[key] is not False for key in ('native_dispatch_allowed',
                'metadata_freeze_allowed', 'research_asset_access_allowed', 'model_source_asset_access_allowed'))):
        raise ValueError('Prospective single v6 fake-execution command differs')
    frozen = manifest['source_hashes']
    if any(frozen.get(path)!=digest for path, digest in sources.items()
           if path!=str(DESIGN/'command.json')):
        raise ValueError('Prospective manifest omits or changes an affected source')
    q.verify_hashes(frozen)
    return sources, evidence


def main():
    if len(sys.argv) != 1:
        raise ValueError('Only the prospectively recorded single gate command is allowed')
    cpu0, anchor = time.process_time(), time.monotonic()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    # Process-local approved policy; historical helper/source bytes remain unchanged.
    q.CEILING, q.DISPATCH_STOP, q.SHUTDOWN_RESERVE = 3600., 3420., 180.
    q._monitor_child_cpu_s = 0.
    folder = BASE/'attempt01'
    folder.mkdir(parents=True, exist_ok=False)  # No overwrite, resume, or automatic retry.
    command = [str(ROOT/'.venv-local/bin/python'), '-m', 'pytest', '-q',
               'src/tests/test_responsive_supervision_v6.py']
    wrapper_command = [str(ROOT/'.venv-local/bin/python'), str(Path(__file__).resolve())]
    registry = folder/'owned-test-groups.jsonl'
    state = {'primary_failure': None, 'secondary_errors': []}
    groups, sources, evidence = set(), {}, {}
    proc, peak, sampled_cpu = None, 0., 0.
    termination = {'owned_pgids': [], 'leader_returncode': None, 'reaped': False,
                   'group_absent': False, 'surviving_pgids': [], 'cleanup_errors': []}
    attempt = {'attempt_id': 'attempt01', 'revision': 6, 'command': command,
               'source_gate_only': True, 'native_dispatch': False, 'metadata_freeze': False,
               'model_source_asset_access': False, 'research_data_loaded_for_analysis': False,
               'no_native_primitive_performed': False,
               'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
               'executed_tests': list(TESTS), 'hashed_qualified_test_dependencies': list(QUALIFIED_TEST_DEPENDENCIES),
               'command_sha256': q.stable(command), 'parent_monotonic': anchor,
               'carried_charge_s': CARRIED, 'prior_charge_s': CARRIED,
               'carry_is_accepted_conservative_guard': True, 'prior_actual_cpu_s': None,
               'historical_accounting_observations_complete': False,
               'legacy_owner_observations_complete': False,
               'administration_allowance_s': ADMIN, 'hard_ceiling_s': q.CEILING,
               'dispatch_stop_s': q.DISPATCH_STOP, 'shutdown_reserve_s': q.SHUTDOWN_RESERVE,
               'wall_limit_s': 20., 'outer_limit_s': 22.5, 'inclusive_planning_s': 25.,
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
            table, free = q.monitor_sample(non_native_deadline(time.monotonic(), None, anchor+20.))
            last_completed, pressure_since = time.monotonic(), None
            if not q.finite(free) or free > 100 or free < 10:
                raise ValueError('Unsafe initial check memory monitor')
            env = {**os.environ, 'PYTHONPATH': str(ROOT/'src'), 'PYTHONDONTWRITEBYTECODE': '1',
                   'EGG_CHECK_PGID_REGISTRY': str(registry), **{key: '1' for key in q.THREAD_KEYS}}
            if time.monotonic() >= anchor+20.:
                raise TimeoutError('Check prelaunch wall limit')
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err,
                                    start_new_session=True)
            groups.add(proc.pid)
            q.campaign.append(folder/'ownership.jsonl', {'event': 'launch', 'owned_pgids': sorted(groups)})
            while proc.poll() is None:
                tick = time.monotonic()
                if tick >= anchor+20.:
                    raise TimeoutError('Check wall limit')
                sample = sample_owned(proc, groups, registry, anchor, last_completed)
                last_completed = sample['completed_monotonic']
                peak, sampled_cpu = max(peak, sample['rss_bytes']), max(sampled_cpu, sample['cpu_s'])
                q.campaign.append(folder/'resources.jsonl', sample)
                q.campaign.append(folder/'ownership.jsonl', {'event': 'sample', 'owned_pgids': sorted(groups)})
                children = resource.getrusage(resource.RUSAGE_CHILDREN)
                reaped_cpu = max(0., children.ru_utime+children.ru_stime-child0.ru_utime-child0.ru_stime)
                active = max(last_completed-anchor, sampled_cpu+q._monitor_child_cpu_s, reaped_cpu)
                active += max(0., time.process_time()-cpu0)
                if CARRIED+active+2.5 >= min(CARRIED+25., PACKAGE_END-FINALIZATION_RESERVE):
                    raise TimeoutError('Fresh-CF1 check finalization reserve')
                if sample['rss_bytes'] > q.RSS_LIMIT:
                    raise RuntimeError('Check process-tree RSS limit')
                pressure_since = ((last_completed if pressure_since is None else pressure_since)
                                  if sample['free_percent'] < 10 else None)
                if pressure_since is not None and last_completed-pressure_since >= 5.:
                    raise RuntimeError('Sustained check memory pressure')
                time.sleep(max(0., .05-(time.monotonic()-tick)))
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
                termination = reviewed.cleanup_receipt(proc, groups, anchor+22.5)
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
    if elapsed > 22.5 or cumulative > CARRIED+25. or cumulative+FINALIZATION_RESERVE > PACKAGE_END:
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
              'scope': 'V6 fake-execution source qualification only; no real resource primitive, model/source asset, metadata freeze, native worker or mechanism clearance'}
    q.write_new(folder/'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
