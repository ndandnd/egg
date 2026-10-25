"""Timed assembly of the unchanged inspected-case freeze; no project imports."""
import time
START = time.monotonic()
from pathlib import Path
import hashlib
import json
import resource

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research-20261024/cf1-entry-repaired-v5d'
RESUME = ROOT/'research-20261024/cf1-resumption'
CHECKS = ROOT/'research-20261024/cf1-entry-repaired-checks'
NON_NATIVE_SAMPLE_POLICY = {'scope': 'source-tests-and-metadata-only',
    'process_sample_timeout_s': 1., 'completed_sample_gap_limit_s': 1.25,
    'poll_interval_s': .05, 'absolute_work_deadline_clipping': True,
    'numerical_monitor_changed': False}
BASE.mkdir()


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((ROOT/'research-20261023/cf1-small-approved-v4/design.json').read_text())
task = {'arm': 'cf1', 'base_id': 50997, 'trips': 40, 'seed': 17,
    'seconds': 60., 'fault': None, 'protocol_revision': 5}
task['id'] = hashlib.sha256(json.dumps(task, sort_keys=True, default=str).encode()).hexdigest()[:20]
budget = {'initial_charged_cpu_s': 2426.723449631016,
    'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
    'additional_hard_cap_s': 275., 'absolute_package_ceiling_s': 2701.723449631016,
    'analysis_reserve_s': 30., 'next_worker_allocation_s': 62.5,
    'next_worker_supervision_reservation_s': 45., 'physical_and_ack_endpoint_s': 60.,
    'supervisor_stop_s': 61., 'outer_allocation_s': 62.5,
    'global_hard_ceiling_s': 3000., 'global_dispatch_stop_s': 2820.,
    'global_shutdown_reserve_s': 180., 'threads': 1, 'numerical_workers': 1,
    'rss_limit_bytes': 5*1024**3, 'automatic_retry': False,
    'check_planning_s': 20., 'freeze_planning_s': 25.,
    'metadata_work_s': 15., 'metadata_outer_s': 17.5, 'metadata_phase_s': 25.,
    'entry_precharge_planning_s': 7.5, 'independent_analysis_planning_s': 20.,
    'artifact_finalization_planning_s': 10.}
analysis = [str(ROOT/'.venv-local/bin/python'), '-m', 'experiments.cf1_entry_repaired',
    'analyze', '--lock', str(BASE/'lock.json'), '--output', str(BASE/'runs'),
    '--report', str(BASE/'report.json')]
write_new(BASE/'analysis-command.json', analysis)
write_new(BASE/'run-command-template.json', {
    'status': 'template_only_not_launch_command',
    'module': 'experiments.cf1_entry_repaired', 'command': 'run',
    'lock': str(BASE/'lock.json'), 'output': str(BASE/'runs'),
    'freeze_receipt': str(BASE/'freeze-attempt01/result.json'),
    'accounting': str(BASE/'freeze-accounting.json'),
    'independent_expected_roots_and_current_total_required_after_freeze': True,
    'external_owner_required': True, 'automatic_retry': False})
evidence_paths = [RESUME/'approval4.json', RESUME/'accepted-carry.json',
    RESUME/'failed-monitor-accounting.json', RESUME/'native-launcher-v5d.py',
    CHECKS/'attempt07-accounting.json',
    Path(__file__).resolve(), ROOT/'research-20261024/CF1_RESUMPTION_PROTOCOL.md',
    ROOT/'research-20261024/CF1_RESUMPTION_REVIEW.md',
    ROOT/'research-20261024/CF1_RESUMPTION_WRAPPERS.md',
    ROOT/'research-20261024/CF1_RESUMPTION2_PROTOCOL.md',
    ROOT/'research-20261024/CF1_RESUMPTION2_WRAPPERS.md',
    ROOT/'research-20261024/CF1_RESUMPTION3_PROTOCOL.md',
    ROOT/'research-20261024/CF1_RESUMPTION3_WRAPPERS.md',
    ROOT/'research-20261024/CF1_METADATA_MONITOR_DIRECTION.md',
    ROOT/'research-20261024/CF1_RESUMPTION4_WRAPPERS.md',
    RESUME/'finalize-source07.py', RESUME/'finalize-freeze-v5d.py',
    BASE/'analysis-command.json', BASE/'run-command-template.json']
design = {'policy': 'cf1-entry-repaired-v5', 'backend': 'GRB', 'tariff': 'day',
    'models': {}, 'case_specs': old['case_specs'], 'tasks': [task],
    'native_library': old['native_library'], 'package_budget': budget,
    'evidence': {str(path): sha(path) for path in evidence_paths},
    'scope': 'One inspected40 CF1 mechanism under approved resumption; no ML quality or comparative claim',
    'automatic_retry': False}
write_new(BASE/'design.json', design)
write_new(BASE/'freeze-command.json', [str(ROOT/'.venv-local/bin/python'), '-m',
    'experiments.cf1_entry_repaired', 'freeze', '--design', str(BASE/'design.json'),
    '--lock', str(BASE/'lock.json'), '--checks', str(CHECKS/'attempt07'),
    '--accounting', str(CHECKS/'attempt07-accounting.json')])
u = resource.getrusage(resource.RUSAGE_SELF)
elapsed, cpu = time.monotonic()-START, u.ru_utime+u.ru_stime
charge = max(elapsed, cpu)
write_new(RESUME/'freeze-preparation4.json', {'phase': 'metered_metadata_assembly',
    'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
    'command': [str(ROOT/'.venv-local/bin/python'), str(Path(__file__).resolve())],
    'elapsed_s': elapsed, 'self_cpu_s': cpu, 'charged_cpu_s': charge,
    'hard_cap_s': 1., 'passed': charge <= 1., 'project_imported': False,
    'fixture_payload_loaded': False, 'solver_called': False, 'native_dispatch': False})
if charge > 1.:
    raise RuntimeError('Metadata assembly exceeded its one-second provision')
print(json.dumps({'passed': True, 'task_id': task['id'], 'charge_s': charge}))
