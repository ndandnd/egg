"""One source-bound 32-cell stored-topology charging study; no retries."""
import time
WALL0 = time.monotonic()
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
POLICY = 'stored-topology-two-market-one-QP-per-cell-v1'
SOURCES = ('source0', 'source1')
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
TABLES = {
    'cases': ('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/cases.jsonl',
              'faf0428f79744a9e26fa04e80baec4734443e3cfe538e404d74f41f626a294d6'),
    'sources': ('/Users/nadan/Documents/ChatGPT/egg/claude-local/20260930-route-pool128-v3/source_inputs.jsonl',
                '7c5fab4c648b27fda5e9ecc55cd418f0a066c8e46196bc31d5f9405e5a6409d5')}
SOURCE_FILES = (
    'research-20261025/topology_charging/run.py',
    'research-20261025/topology_charging/worker.py',
    'research-20261025/warm_replication/qp_control.py',
    'src/egglab/__init__.py', 'src/egglab/native_recharge.py',
    'src/egglab/native_hull.py', 'src/egglab/native_pathflow.py',
    'src/egglab/physical_learning_cases.py')
INPUT_FILES = ('COHORT.json', 'PREPARATION_ACCOUNTING.json', 'PROTOCOL.md', 'LAUNCH.json')
TOTAL_CPU, TOTAL_WALL, DISPATCH_CPU = 3600., 7200., 3240.


class ContractError(ValueError):
    pass


# Local stdlib harness helpers copied from warm_replication/run.py. No import of
# that campaign, global rebinding, timing hooks or optimizer wrappers is used.
def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
                  default=lambda x: str(x) if isinstance(x, Q) else x)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value)
    os.replace(temporary, path)  # Only our exclusive incomplete placeholder.


def load(path):
    with Path(path).open() as stream:
        return json.load(stream)


def self_cpu():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime+usage.ru_stime


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime+usage.ru_stime


def rss_bytes():
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(raw if sys.platform == 'darwin' else raw*1024)


def resource_receipt():
    own, child = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(self_cpu_s=own.ru_utime+own.ru_stime,
        waited_children_cpu_s=child.ru_utime+child.ru_stime,
        combined_cpu_s=own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime,
        observed_self_peak_rss_bytes=rss_bytes(), raw_self_maxrss=own.ru_maxrss,
        platform=sys.platform, timing_scope='through receipt preparation; external meter includes write and exit')


def canonical(plan):
    return sorted((tuple(v['trips']), tuple(v['movements'])) for v in plan['vehicles'])


def stored_case(raw, nr):
    fields = dict(raw)
    fields['trips'] = tuple(nr.Trip(**v) for v in raw['trips'])
    fields['movements'] = tuple(nr.Movement(**dict(v,
        legs=tuple(nr.Leg(**leg) for leg in v['legs']))) for v in raw['movements'])
    fields['resources'] = tuple(nr.Resource(**v) for v in raw['resources'])
    fields['market_edges_min'] = tuple(raw['market_edges_min'])
    return nr.NativeCase(**fields)


def read_identity(path, report):
    path = Path(path)
    if str(path) in report['input_sha256']:
        raise ContractError('Duplicate input hash path')
    before = path.stat()
    if before.st_size > 8*1024**2:
        raise ContractError('Metadata/source exceeds8MiB')
    with path.open('rb') as stream:
        raw = stream.read(8*1024**2+1)
    after = path.stat()
    if (len(raw) != before.st_size or
            (before.st_ino, before.st_size, before.st_mtime_ns) !=
            (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ContractError('Frozen metadata/source changed during read')
    report['input_sha256'][str(path)] = hashlib.sha256(raw).hexdigest()
    return raw


def validate_cohort(cohort):
    old_source = str(ROOT/'research-20261025/catalog_coherence/attempt01/receipt.json')
    old_inputs = {str(HERE/name) for name in ('select_cohort.py',
        'COHORT_SELECTION_PROTOCOL.md', 'COHORT_SELECTION_LAUNCH.json')} | {old_source}
    pins = cohort['input_sha256']
    if (cohort.get('cohort_complete') is not True
            or cohort.get('selection_cost_fields_consulted') is not False
            or cohort.get('baseline_copy_after_ID_selection') is not True
            or cohort.get('numerical_QP_outcomes_observed') is not False
            or cohort.get('intended_FIT_groups') != 80 or cohort.get('original_complete_pairs') != 79
            or set(pins) != old_inputs or pins.get(old_source) != cohort['source_receipt_sha256']
            or any(not isinstance(v, str) or len(v) != 64
                or any(c not in '0123456789abcdef' for c in v) for v in pins.values())):
        raise ContractError('Closed cohort metadata/lineage backreference differs')
    groups, tasks = cohort['groups'], cohort['tasks']
    if len(groups) != 8 or len(tasks) != 32:
        raise ContractError('Require frozen8groups/32tasks')
    if len({g['group'] for g in groups}) != 8 or len({g['base_id'] for g in groups}) != 8:
        raise ContractError('Duplicate cohort group/base')
    ordered = sorted(groups, key=lambda g: (g['services'],
        g['membership_stratum'] == 'same_membership', g['base_id']))
    if groups != ordered:
        raise ContractError('Frozen group ordering differs')
    by_group = {g['group']: g for g in groups}
    for size in (20, 28):
        part = [g for g in groups if g['services'] == size]
        if (sum(g['membership_stratum'] == 'different_membership' for g in part) != 3
                or sum(g['membership_stratum'] == 'same_membership' for g in part) != 1):
            raise ContractError('Require3changed/1same per service count')
    seen = set()
    for gi, group in enumerate(groups):
        if (type(group['base_id']) is not int or group['base_id'] not in range(10000, 10128)
                or group['group'] != f"physical_v2_s{group['base_id']}"):
            raise ContractError('Canonical cohort group/base differs')
        for source in SOURCES:
            for target in SOURCES:
                if not isinstance(group['baseline'][source][target], str):
                    raise ContractError('Baseline F must be exact rational strings')
                Q(group['baseline'][source][target])
        if not isinstance(group['Ebar'], str):
            raise ContractError('Ebar must be exact rational string')
        Q(group['Ebar'])
        order = [(r, t) for r in SOURCES for t in SOURCES]
        shift = gi % 4
        order = order[shift:]+order[:shift]
        if (gi//4) % 2:
            order.reverse()
        for offset, pair in enumerate(order):
            task = tasks[gi*4+offset]
            token = json.dumps(task['task_id'], sort_keys=True, allow_nan=False)
            if token in seen or isinstance(task['task_id'], (list, dict)):
                raise ContractError('Task IDs must be unique opaque scalars')
            seen.add(token)
            if (task['index'] != gi*4+offset+1 or type(task['index']) is not int
                    or any(task[k] != group[k] for k in ('group', 'base_id', 'services'))
                    or (task['route_source'], task['target_source']) != pair):
                raise ContractError('Frozen task identity/order differs')
    return by_group


def preflight(report, check):
    cohort = json.loads(read_identity(HERE/'COHORT.json', report))
    # Preserve assignments even if a later source, identity or funding check fails.
    report['cells'] = [dict(task, attempted=False, parent_endpoint_accepted=False,
        cell_qualified=False, unattempted_reason='preflight_not_admitted') for task in cohort['tasks']]
    groups = validate_cohort(cohort)
    documents = {}
    for name in INPUT_FILES[1:]:
        check()
        raw = read_identity(HERE/name, report)
        if name.endswith('.json'):
            documents[name] = json.loads(raw)
    prep = documents['PREPARATION_ACCOUNTING.json']
    if (prep.get('receipt_complete') is not True or prep.get('stageA_complete') is not True
            or prep.get('exit_code') != 0 or prep.get('output') != 'COHORT.json'
            or prep.get('selected_cpu_s') != 30 or prep.get('selected_wall_s') != 60):
        raise ContractError('Cohort selection accounting incomplete or failed')
    charge, elapsed = prep['retained_charge_cpu_s'], prep['elapsed_s']
    if (type(charge) not in (int, float) or type(elapsed) not in (int, float)
            or not 0 <= charge <= 30 or not 0 <= elapsed <= 60
            or not 0 <= prep['displayed_cpu_s'] <= charge):
        raise ContractError('Cohort selection charge invalid')
    report['preparation_accounting'] = prep
    report['preparation_charge_cpu_s'], report['preparation_elapsed_s'] = charge, elapsed
    for name in SOURCE_FILES:
        check(); read_identity(ROOT/name, report)
    sys.path.insert(0, str(ROOT/'src'))
    import egglab
    from egglab import native_recharge as nr, native_hull as nh, physical_learning_cases as physical
    for module, name in ((egglab, '__init__.py'), (nr, 'native_recharge.py'),
                          (nh, 'native_hull.py'), (physical, 'physical_learning_cases.py')):
        if Path(module.__file__).resolve() != ROOT/'src'/'egglab'/name:
            raise ContractError('Paid pure import source differs')
    cases, raw_cases, markets, plans, values = {}, {}, {}, {}, {}
    case_seen, source_seen = set(), set()
    report['selected_groups'] = [dict(g, canonical_paths_equal=None,
        membership_verified=False) for g in cohort['groups']]

    def process_case(row, group):
        if group in case_seen:
            cases.pop(group, None); raise ContractError('Duplicate selected case')
        case_seen.add(group)
        meta = groups[group]
        if (type(row['base_id']) is not int or row['base_id'] != meta['base_id']
                or row['split'] != 'train'
                or row['generator'] != 'physical-fleet-learning-v2-full-factorial'
                or row['physical_profile']['base_id'] != meta['base_id']
                or row['physical_profile']['split'] != 'train'):
            raise ContractError('Stored selected TRAIN/profile join differs')
        case = stored_case(row['case'], nr)
        profile = physical.assignment(meta['base_id'])
        if (case.identity() != row['case_identity'] or len(case.trips) != meta['services']
                or row['physical_profile'] != profile
                or profile['services'] != meta['services']
                or row['physical_profile']['services'] != meta['services']
                or case.battery_kwh != profile['profile']['upper_kwh']
                or case.reserve_kwh != profile['profile']['reserve_kwh']
                or case.efficiency != profile['efficiency']
                or case.terminal_open_min != profile['terminal_open_min']
                or case.recharge_deadline_min != profile['deadline_min']
                or len(case.resources) != 1 or case.resources[0] != nr.Resource(0, 1800, 90.0, 90.0, 1)
                or tuple(case.market_edges_min) != tuple(range(0, 1801, 60))):
            raise ContractError('Stored case identity/service/profile/grid differs')
        ids = [m.id for m in case.movements]
        if not ids or len(ids) != len(set(ids)) or any(not isinstance(mid, str) for mid in ids):
            raise ContractError('Movement universe empty/duplicate/invalid')
        cases[group], raw_cases[group] = case, row['case']
        markets[group] = {s: physical.market(case, s) for s in SOURCES}
        for market in markets[group].values():
            nh.validate_market(case, market)

    def process_source(row, group):
        source = row['source']; key = (group, source)
        if key in source_seen:
            plans.pop(key, None); raise ContractError('Duplicate selected source')
        source_seen.add(key)
        if source not in SOURCES or group not in cases:
            raise ContractError('Selected source has no admitted common case/source kind')
        case, market = cases[group], markets[group][source]
        if (type(row['base_id']) is not int or row['base_id'] != groups[group]['base_id']
                or row['case_identity'] != case.identity() or row['market_kind'] != source
                or row['market_identity'] != market.identity()):
            raise ContractError('Source case/market join or identity differs')
        plan = row['source_plan']
        if nr.digest(plan) != row['source_plan_hash'] or plan['case_identity'] != case.identity():
            raise ContractError('Whole original source-plan identity differs')
        flat = [mid for v in plan['vehicles'] for mid in v['movements']]
        selected = row['selected_movements']
        if (not flat or not isinstance(selected, list) or any(not isinstance(mid, str) for mid in flat+selected)
                or len(flat) != len(set(flat)) or len(selected) != len(set(selected))
                or selected != sorted(flat) or not set(selected) <= {m.id for m in case.movements}):
            raise ContractError('Source selected membership duplicate/outside/disagrees')
        check(); replay = nr.replay_native(case, plan); check()
        if replay.get('replay_ok') is not True:
            raise ContractError('Original stored source replay rejected')
        vals = {s: nh.rational(replay['ops_cost'])+nh.supply(m, replay['load'])
                for s, m in markets[group].items()}
        elec = {s: nh.supply(m, replay['load']) for s, m in markets[group].items()}
        plans[key], values[key] = plan, dict(F=vals, electricity=elec)

    for label, handler in (('cases', process_case), ('sources', process_source)):
        name, pin = TABLES[label]; path = Path(name); before = path.stat()
        if before.st_size > 512*1024**2:
            raise ContractError('TRAIN table exceeds512MiB')
        digest = hashlib.sha256(); size = lines = discarded = 0
        with path.open('rb') as stream:
            while True:
                check(); raw = stream.readline(16*1024**2)
                if not raw:
                    break
                digest.update(raw); size += len(raw); lines += 1
                if size > 512*1024**2 or (len(raw) == 16*1024**2 and not raw.endswith(b'\n') and size < before.st_size):
                    raise ContractError('TRAIN file/line cap exceeded')
                try:
                    row = json.loads(raw)
                    if not isinstance(row, dict) or not isinstance(row.get('base_group'), str):
                        raise ContractError('Missing top-level routing group')
                    group = row['base_group']
                    if group not in groups:
                        discarded += 1; row = None; continue
                    handler(row, group)
                except (ValueError, TypeError, KeyError, OverflowError) as exc:
                    report['findings'].append(dict(table=label, line=lines,
                        type=type(exc).__name__, message=str(exc)))
                row = None
        actual = digest.hexdigest(); report['input_sha256'][name] = actual
        after = path.stat()
        report['table_streams'][label] = dict(bytes=size, lines=lines,
            nonselected_routing_discarded=discarded, pin_matched=actual == pin)
        if (actual != pin or size != before.st_size or
                (before.st_ino, before.st_size, before.st_mtime_ns) !=
                (after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ContractError('Whole TRAIN table pin/stability differs')
    for item in report['selected_groups']:
        group = item['group']; keys = [(group, s) for s in SOURCES]
        if group not in cases or any(key not in plans for key in keys):
            raise ContractError('Missing/invalid selected case/source; no replacement')
        same_ids = {m for v in plans[keys[0]]['vehicles'] for m in v['movements']} == {
                    m for v in plans[keys[1]]['vehicles'] for m in v['movements']}
        equal_paths = canonical(plans[keys[0]]) == canonical(plans[keys[1]])
        item.update(canonical_paths_equal=equal_paths, membership_verified=True)
        if same_ids != (item['membership_stratum'] == 'same_membership') or same_ids and not equal_paths:
            raise ContractError('Frozen membership/control canonical identity differs')
        for source in SOURCES:
            for target in SOURCES:
                if values[(group, source)]['F'][target] != Q(item['baseline'][source][target]):
                    raise ContractError('Frozen catalog F differs from original replay')
        ebar = sum((values[(group, s)]['electricity'][t] for s in SOURCES for t in SOURCES), Q(0))/4
        if ebar != Q(item['Ebar']):
            raise ContractError('Frozen original Ebar differs from original replay')
    if report['findings']:
        raise ContractError('TRAIN stream contains malformed/duplicate/invalid findings')
    check()
    return cohort, groups, cases, raw_cases, markets, plans


def launch_worker(output, task, spec):
    folder = output/f"{task['index']:03d}-cell"
    folder.mkdir(exist_ok=False)
    raw = (json.dumps(spec, indent=2, allow_nan=False)+'\n').encode()
    with (folder/'spec.json').open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    spec_sha = hashlib.sha256(raw).hexdigest()
    save_new(folder/'receipt.json', dict(receipt_complete=False, method_endpoint_accepted=False,
        cell_qualified=False, config_failure=False, fatal_contract=False))
    record = dict(task, folder=str(folder), attempted=False, reaped=False,
        returncode=None, timed_out=False, failures=[], config_failure=False,
        fatal_contract=False, parent_endpoint_accepted=False, cell_qualified=False,
        spec_sha256=spec_sha, child_cpu_hard_s=90.)
    child = None; cleanup_end = None
    before_child, before_self = children_cpu(), self_cpu()
    anchor = time.monotonic(); record['parent_anchor'] = anchor
    with (folder/'stdout.txt').open('x') as stdout, (folder/'stderr.txt').open('x') as stderr:
        try:
            if threading.active_count() != 1:
                raise ContractError('Parent must have one Python thread before fork')
            child = subprocess.Popen([sys.executable, str(HERE/'worker.py'), '--worker', str(folder),
                '--parent-anchor', repr(anchor), '--spec-sha256', spec_sha], cwd=ROOT,
                env=dict(os.environ), stdout=stdout, stderr=stderr, start_new_session=True,
                preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (90, 90)))
            record.update(attempted=True, pid=child.pid)
            try:
                child.wait(timeout=max(.001, anchor+60.-time.monotonic()))
            except subprocess.TimeoutExpired:
                record['timed_out'] = True; cleanup_end = time.monotonic()+3.
                child.terminate()
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            record.update(returncode=child.returncode, reaped=True)
        except BaseException as exc:
            record['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
            if child is None:
                record.update(config_failure=True, fatal_contract=True)
            if child is not None and child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3.
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    record.update(returncode=child.returncode, reaped=True)
                except BaseException as secondary:
                    record['failures'].append(dict(type=type(secondary).__name__, message=str(secondary)))
    record.update(process_return_elapsed_s=time.monotonic()-anchor,
        waited_child_cpu_s=children_cpu()-before_child, parent_cpu_s=self_cpu()-before_self,
        cpu_observation_complete=child is None or record['reaped'],
        unresolved_cpu_reserve_s=90. if child is not None and not record['reaped'] else 0.)
    try:
        path = folder/'receipt.json'
        if path.stat().st_size > 8*1024**2:
            raise ContractError('Worker compact receipt exceeds8MiB')
        packet = load(path)
        if any(packet.get(key) != task[key] for key in ('task_id', 'group', 'base_id', 'services', 'route_source', 'target_source')):
            raise ContractError('Worker receipt task identity differs')
    except Exception as exc:
        packet = dict(receipt_complete=False)
        record['failures'].append(dict(stage='complete_receipt_read', type=type(exc).__name__, message=str(exc)))
        if isinstance(exc, ContractError):
            record.update(config_failure=True, fatal_contract=True)
    record['complete_receipt_read_monotonic'] = time.monotonic()
    record['parent_elapsed_s'] = record['complete_receipt_read_monotonic']-anchor
    record['method_late'] = record['parent_elapsed_s'] > 60.
    record['worker'] = packet
    for flag in ('config_failure', 'fatal_contract', 'identity_failure', 'resource_violation'):
        record[flag] = bool(record.get(flag) or packet.get(flag))
    record['parent_endpoint_accepted'] = bool(record['reaped'] and record['returncode'] == 0
        and not record['timed_out'] and not record['failures'] and not record['fatal_contract']
        and not record['config_failure'] and packet.get('receipt_complete') is True
        and packet.get('method_endpoint_accepted') is True and record['parent_elapsed_s'] <= 60.)
    record['cell_qualified'] = bool(record['parent_endpoint_accepted'] and packet.get('cell_qualified') is True)
    save_new(folder/'external-receipt.json', record)
    return record


def readout(report):
    rows = report['cells']; groups = []
    for meta in report.get('selected_groups', []):
        cells = [r for r in rows if r.get('group') == meta['group']]
        contrasts = {}
        for target in SOURCES:
            pair = {r['route_source']: r for r in cells if r['target_source'] == target}
            costs, retained = {}, {}
            for source, row in pair.items():
                packet = row.get('worker', {})
                costs[source] = (Q(packet['candidate_bill_exact']) if row.get('cell_qualified')
                    and packet.get('qp_candidate_admitted') is True and packet.get('candidate_bill_exact') is not None else None)
                retained[source] = (Q(packet['true_bill_exact']) if row.get('parent_endpoint_accepted')
                    and packet.get('true_bill_exact') is not None else None)
            defined = len(costs) == 2 and all(v is not None for v in costs.values())
            retained_defined = len(retained) == 2 and all(v is not None for v in retained.values())
            original = Q(meta['baseline']['source1'][target])-Q(meta['baseline']['source0'][target])
            point = costs['source1']-costs['source0'] if defined else None
            contrasts[target] = dict(original_catalog_difference_route1_minus_route0=original,
                qualified_point_difference_route1_minus_route0=point,
                point_difference_change_from_original=point-original if defined else None,
                timely_retained_difference_route1_minus_route0=(
                    retained['source1']-retained['source0'] if retained_defined else None),
                timely_retained_comparison_defined=retained_defined,
                defined=defined, mathematical_route_ordering='UNRESOLVED',
                optimization_gap_bound_available=False)
        groups.append(dict(group=meta['group'], base_id=meta['base_id'], services=meta['services'],
            membership_stratum=meta['membership_stratum'], canonical_paths_equal=meta['canonical_paths_equal'],
            cells_planned=4, qualified_cells=sum(r.get('cell_qualified', False) for r in cells),
            target_point_comparisons=contrasts))
    return dict(groups=groups, groups_planned=8, cells_planned=32,
        changed_groups_planned=6, same_controls_planned=2,
        attempted=sum(r.get('attempted', False) for r in rows),
        parent_endpoints_accepted=sum(r.get('parent_endpoint_accepted', False) for r in rows),
        qualified_QP_cells=sum(r.get('cell_qualified', False) for r in rows),
        unattempted=sum(not r.get('attempted', False) for r in rows),
        interpretation='Exact feasible point comparisons only; no optimization-gap or route-order certificate')


def main():
    output = HERE/'attempt01'
    output.mkdir(exist_ok=False)
    target = output/'receipt.json'
    save_new(target, dict(receipt_complete=False, passed=False))
    report = dict(policy=POLICY, receipt_complete=False, passed=False,
        cells=[dict(index=i, attempted=False, parent_endpoint_accepted=False, cell_qualified=False,
            unattempted_reason='COHORT_not_read_or_admitted') for i in range(1, 33)], selected_groups=[],
        failures=[], findings=[], input_sha256={}, table_streams={}, config_failure=False,
        resource_violation=False, accounting_complete=False, preparation_charge_cpu_s=None,
        preparation_elapsed_s=None, scientific_certificate_claim=False,
        budgets=dict(total_cpu_s=3600, total_wall_s=7200, dispatch_cpu_s=3240,
            closure_reserve_cpu_s=360, preflight_cpu_s=120, finalization_cpu_s=120))
    stopped = None; unresolved = 0.; phase = 'preflight'; final_cpu0 = final_wall0 = None

    def stop(signum, frame):
        nonlocal stopped
        stopped = stopped or signum
        raise TimeoutError('Latched parent stop signal '+str(signum))

    def check():
        carry = report['preparation_charge_cpu_s']
        carry = carry if carry is not None else 30.  # Failclosed until actual StageA receipt is read.
        elapsed = report['preparation_elapsed_s']
        elapsed = elapsed if elapsed is not None else 60.
        if stopped is not None:
            raise TimeoutError('Parent stop signal remains latched')
        if (threading.active_count() != 1 or rss_bytes() > 5*1024**3
                or carry+self_cpu()+children_cpu()+unresolved > TOTAL_CPU
                or elapsed+time.monotonic()-WALL0 > TOTAL_WALL):
            report['config_failure'] = report['resource_violation'] = True
            raise ContractError('Package thread/RSS/CPU/wall contract exceeded')
        if phase == 'preflight' and carry+self_cpu() > 120.:
            report['resource_violation'] = report['config_failure'] = True
            raise ContractError('Paid preflight CPU120 exhausted')
        if phase == 'finalization' and self_cpu()-final_cpu0 > 120.:
            report['resource_violation'] = report['config_failure'] = True
            raise ContractError('Finalization CPU120 exhausted')
        if phase == 'finalization' and time.monotonic()-final_wall0 > 180.:
            report['resource_violation'] = report['config_failure'] = True
            raise ContractError('Finalization wall180 exhausted')

    try:
        if HERE != ROOT/'research-20261025'/'topology_charging':
            raise ContractError('Source namespace differs')
        for name in THREAD_ENV:
            os.environ[name] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (120, 3600))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, TOTAL_WALL-60.-(time.monotonic()-WALL0)))
        cohort, groups, cases, raw_cases, markets, plans = preflight(report, check)
        check(); report['preflight_admitted'] = True
        save_new(output/'preflight.json', {k: report[k] for k in ('input_sha256', 'table_streams',
            'selected_groups', 'preparation_accounting', 'findings', 'preflight_admitted')})
        phase = 'dispatch'
        # CPU usage remains cumulative; child hard limits are independent90s.
        resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))
        for position, task in enumerate(cohort['tasks']):
            check()
            if (report['preparation_charge_cpu_s']+self_cpu()+children_cpu()+unresolved+90. > DISPATCH_CPU
                    or report['preparation_elapsed_s']+time.monotonic()-WALL0+63.+180. > TOTAL_WALL):
                report['dispatch_stopped_reason'] = 'insufficient_remaining_funding'; break
            group, route, target_source = task['group'], task['route_source'], task['target_source']
            meta, case, market = groups[group], cases[group], markets[group][target_source]
            spec = dict(root=str(ROOT), **{k: task[k] for k in ('task_id', 'group', 'base_id',
                'services', 'route_source', 'target_source')}, case=raw_cases[group],
                prior_plan=plans[(group, route)], expected_case_identity=case.identity(),
                expected_market_identity=market.identity(), a=list(market.a), b=list(market.b),
                baseline_F_exact=meta['baseline'][route][target_source], original_Ebar_exact=meta['Ebar'])
            record = launch_worker(output, task, spec)
            report['cells'][position] = record
            unresolved += record['unresolved_cpu_reserve_s']
            if record['config_failure'] or record['fatal_contract'] or unresolved:
                report['config_failure'] = True
                report['dispatch_stopped_reason'] = 'fatal_contract_or_unresolved_child'; break
            check()
    except BaseException as exc:
        report['failures'].append(dict(stage=phase, type=type(exc).__name__, message=str(exc)))
        report['config_failure'] = True
    finally:
        phase = 'finalization'; final_cpu0 = self_cpu(); final_wall0 = time.monotonic()
        # Keep an absolute total-wall/publication tail even after the earlier
        # dispatch alarm fired; never clear its latched stop/failure state.
        remaining_wall = TOTAL_WALL-(report['preparation_elapsed_s'] or 60.)-(final_wall0-WALL0)
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(180., remaining_wall)))
        try:
            check()
            for row in report['cells']:
                if not row.get('attempted'):
                    row['unattempted_reason'] = report.get('dispatch_stopped_reason', 'preflight_or_parent_failure')
                meta = next((g for g in report['selected_groups'] if g['group'] == row.get('group')), None)
                if meta is not None:
                    row['known_original_fallback_bill_exact'] = meta['baseline'][row['route_source']][row['target_source']]
            report['summary'] = readout(report)
            check()
        except BaseException as exc:
            report['failures'].append(dict(stage='finalization', type=type(exc).__name__, message=str(exc)))
            report['config_failure'] = True
        report.update(stop_signal=stopped, resources=resource_receipt(), unresolved_cpu_reserve_s=unresolved,
            process_elapsed_s=time.monotonic()-WALL0, receipt_complete=True,
            accounting_complete=unresolved == 0 and report['preparation_charge_cpu_s'] is not None,
            historical_global_accounting='Separate closed prefix; not charged again to this3600CPU package')
        carry = report['preparation_charge_cpu_s']; elapsed = report['preparation_elapsed_s']
        report['package_cpu_s_through_preparation'] = None if carry is None else carry+self_cpu()+children_cpu()+unresolved
        report['package_elapsed_sum_s_through_preparation'] = None if elapsed is None else elapsed+time.monotonic()-WALL0
        report['passed'] = bool(not report['config_failure'] and not report['failures']
            and report['accounting_complete'] and len(report['cells']) == 32
            and all(r.get('parent_endpoint_accepted') for r in report['cells']))
        publication_now = time.monotonic()
        publication_remaining = min(180.-(publication_now-final_wall0),
            TOTAL_WALL-(elapsed if elapsed is not None else 60.)-(publication_now-WALL0))
        if publication_remaining <= 0:
            raise TimeoutError('No finalization/total wall allowance remains for publication')
        # The signal is one-shot; a caught alarm must not leave publication unbounded.
        signal.setitimer(signal.ITIMER_REAL, publication_remaining)
        publish(target, report)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
