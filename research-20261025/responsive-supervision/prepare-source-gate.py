"""One timed manifest-authoring batch; data-only AST extraction, no project import."""
import time
START = time.monotonic()
import ast
import hashlib
import json
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'research-20261025/cf1-responsive-checks/attempt01-design'
DRIVER = ROOT/'research-20261025/run_responsive_source_checks.py'
NON_NATIVE_SAMPLE_POLICY = {'scope': 'source-tests-and-metadata-only',
    'process_sample_timeout_s': 1., 'completed_sample_gap_limit_s': 1.25,
    'poll_interval_s': .05, 'absolute_work_deadline_clipping': True,
    'numerical_monitor_changed': False}
BASE.mkdir(parents=True, exist_ok=False)


def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


budget = {'initial_charge_s': 2541.8243213823207,
    'absolute_package_end_s': 2571.8243213823207,
    'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
    'administration_allowance_s': 0., 'additional_hard_cap_s': 30.,
    'work_limit_s': 20., 'outer_limit_s': 22.5,
    'inclusive_check_planning_s': 25., 'analysis_finalization_reserve_s': 5.,
    'threads': 1, 'rss_limit_bytes': 5*1024**3,
    'automatic_retry': False, 'native_dispatch_allowed': False,
    'metadata_freeze_allowed': False, 'research_asset_access_allowed': False,
    'model_source_asset_access_allowed': False}
write_new(BASE/'prospective-budget.json', budget)
tree = ast.parse(DRIVER.read_text())
values = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('TESTS', 'QUALIFIED_TEST_DEPENDENCIES'):
                values[target.id] = ast.literal_eval(node.value)
inventory = next(node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == 'source_inventory')
relative = [node.value for node in ast.walk(inventory)
    if isinstance(node, ast.Constant) and isinstance(node.value, str)
    and node.value.startswith('research-')]
paths = [path for folder in ('src/experiments', 'src/egglab')
    for path in (ROOT/folder).rglob('*.py')]
paths += [ROOT/'src/tests'/name for name in
    values['TESTS']+values['QUALIFIED_TEST_DEPENDENCIES']]
paths += [ROOT/name for name in relative]
paths += [DRIVER, BASE/'prospective-budget.json',
    Path(__file__).resolve(), ROOT/'research-20261025/responsive-supervision/budget-adoption.json']
hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(set(paths))}
write_new(BASE/'command.json', {
    'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
    'command': [str(ROOT/'.venv-local/bin/python'), str(DRIVER)],
    'selected_tests': ['test_responsive_supervision_v6.py'],
    'automatic_retry': False, 'native_dispatch_allowed': False,
    'metadata_freeze_allowed': False, 'research_asset_access_allowed': False,
    'model_source_asset_access_allowed': False,
    'source_hashes': hashes})
usage = resource.getrusage(resource.RUSAGE_SELF)
elapsed = time.monotonic()-START
cpu = usage.ru_utime+usage.ru_stime
charge = max(elapsed, cpu)
write_new(BASE/'preparation.json', {'phase': 'metered_manifest_authoring',
    'non_native_sample_policy': NON_NATIVE_SAMPLE_POLICY,
    'command': [str(ROOT/'.venv-local/bin/python'), str(Path(__file__).resolve())],
    'elapsed_s': elapsed, 'self_cpu_s': cpu, 'charged_cpu_s': charge,
    'hard_cap_s': 1., 'passed': charge <= 1.,
    'project_imported': False, 'tests_run': False, 'native_dispatch': False,
    'source_paths': len(hashes)})
if charge > 1.:
    raise RuntimeError('Manifest preparation exceeded its prospective one-second provision')
print(json.dumps({'passed': True, 'source_paths': len(hashes), 'charge_s': charge}))
