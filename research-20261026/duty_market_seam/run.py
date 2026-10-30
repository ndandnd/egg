"""DRAFT one-base duty/economic seam: serial owner, no fixture before admission."""
import time
WALL0 = time.monotonic()
from fractions import Fraction as Q
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
ROOT = Path('/Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017')
HERE = ROOT/'research-20261026/duty_market_seam'
POLICY = 'literal-synthetic-duty-market-seam-owner-v1'
CONTEXT_IDS = ('b0_all', 'posted', 'system', 'strategic')
PHASES = ('target_qp', 'fixed_duty', 'full')
TOTAL_CPU, TOTAL_WALL, DISPATCH_CPU = 1500., 2400., 1320.
CHILD_PUBLICATION, PUBLICATION_STOP = False, None
THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
SOURCE_FILES = ('research-20261026/duty_market_seam/run.py',
    'research-20261026/duty_market_seam/adapter.py', 'research-20261026/duty_market_seam/worker.py',
    'research-20261025/warm_replication/qp_control.py',
    'research-20261026/economic_recourse_pilot/miqp_control.py',
    'src/egglab/__init__.py', 'src/egglab/native_recharge.py',
    'src/egglab/native_hull.py', 'src/egglab/native_pathflow.py')


class ContractError(ValueError):
    pass


def save_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False,
                  default=lambda v: str(v) if isinstance(v, Q) else v)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def publish(path, value):
    path = Path(path); temporary = path.with_name(path.name+'.final.tmp')
    save_new(temporary, value); os.replace(temporary, path)


def self_cpu():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime+usage.ru_stime


def children_cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime+usage.ru_stime


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == 'darwin' else value*1024)


def read_once(path, cap=8*1024**2):
    path = Path(path); before = path.stat()
    if before.st_size > cap:
        raise ContractError('Declared source/control/owned artifact exceeds cap')
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    after = path.stat()
    if (len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ContractError('Frozen consumed bytes changed during bounded read')
    return raw


def canonical_paths(plan):
    return sorted((tuple(v['trips']), tuple(v['movements'])) for v in plan['vehicles'])


def duty_signature(duties):
    return sorted(tuple(d) for d in duties)


def plan_duties(plan):
    return sorted(tuple(v['trips']) for v in plan['vehicles'])


def tasks():
    result = []
    for index, context_id in enumerate(CONTEXT_IDS):
        record = dict(context_id=context_id, dispatch_order=['target_qp']+
            (['fixed_duty', 'full'] if index % 2 == 0 else ['full', 'fixed_duty']))
        for phase_index, phase in enumerate(PHASES):
            ordinal = 3*index+phase_index+1
            record[phase] = dict(context_id=context_id, phase=phase, ordinal=ordinal,
                task_id=f'T{ordinal:02d}-{phase}', attempted=False)
        result.append(record)
    return result


def launch_gate():
    raw = read_once(HERE/'LAUNCH.json'); launch = json.loads(raw)
    revision = launch.get('source_revision')
    preparation = launch.get('preparation_accounting') or {}
    dependent_order = {context: (['fixed_duty', 'full'] if index % 2 == 0 else ['full', 'fixed_duty'])
        for index, context in enumerate(CONTEXT_IDS)}
    budgets = dict(total_cpu_s=1500, total_wall_s=2400, dispatch_cpu_s=1320, closure_cpu_s=180,
        preflight_cpu_s=60, finalization_cpu_s=60, finalization_wall_s=90,
        preparation_cpu_s=10, preparation_wall_s=30, worker_hard_cpu_s=90,
        native_cutoff_s=52, endpoint_s=60, cleanup_s=3)
    if (Path(__file__).resolve() != HERE/'run.py' or launch.get('mode') != 'FROZEN'
            or launch.get('review_disposition') != 'PASS' or launch.get('policy') != POLICY
            or launch.get('workdir') != str(ROOT) or launch.get('command') is None
            or launch.get('tracking_prefix') is None or launch.get('numerical_resource_prefix') is None
            or launch.get('source_sha256') is None
            or launch.get('budgets') != budgets or launch.get('context_ids') != list(CONTEXT_IDS)
            or launch.get('phases') != list(PHASES) or launch.get('fixture') != 'duty-market-seam-v1'
            or launch.get('dependent_dispatch_order') != dependent_order
            or launch.get('environment') != {k: '1' for k in THREAD_ENV}
            or launch.get('source_freeze_assumption') != 'parent-approved-frozen-commit'
            or launch.get('mixed_integer_parameters') is None
            or not isinstance(revision, str) or len(revision) != 40
            or any(c not in '0123456789abcdef' for c in revision)
            or preparation.get('external_accepted') is not True
            or type(preparation.get('charged_cpu_s')) not in (int, float)
            or type(preparation.get('elapsed_s')) not in (int, float)
            or not 0 <= preparation['charged_cpu_s'] <= 10
            or not 0 <= preparation['elapsed_s'] <= 30):
        raise SystemExit('DRAFT/PENDING: literal fixture construction and dispatch denied')
    return launch, raw


def preflight(launch, report, check):
    required = {str(ROOT/p) for p in SOURCE_FILES} | {str(HERE/'PROTOCOL.md'),
        str(HERE/'OWNER_NOTE.md'), str(HERE/'WORKER_NOTE.md'),
        str(HERE/'prepare.py'),
        str(ROOT/'research-20261026/evspdr_correspondence/STUDY_DECISION.md')}
    if set(launch['source_sha256']) != required:
        raise ContractError('Literal consumed source/protocol inventory differs')
    for path, expected in launch['source_sha256'].items():
        check(); raw = read_once(path); digest = hashlib.sha256(raw).hexdigest()
        report['input_sha256'][path] = digest
        if digest != expected:
            raise ContractError('Frozen consumed source/protocol bytes differ')
    sys.path.insert(0, str(ROOT/'src'))
    spec = importlib.util.spec_from_file_location('duty_market_owner_adapter', HERE/'adapter.py')
    if spec is None or spec.loader is None:
        raise ContractError('Explicit adapter path unavailable')
    adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    from egglab import native_recharge as nr
    if Path(nr.__file__).resolve() != ROOT/'src/egglab/native_recharge.py':
        raise ContractError('Paid native physical import path differs')
    check(); case, reference, duties = adapter.make_fixture(); check()
    nr.validate_case(case)
    replay = nr.replay_native(case, reference); check()
    if (case.name != 'duty-market-seam-v1' or case.max_vehicles != 2
            or len(case.trips) != 8 or len(reference['vehicles']) != 2
            or reference['case_identity'] != case.identity() or replay.get('replay_ok') is not True
            or plan_duties(reference) != duty_signature(duties)):
        raise ContractError('Literal synthetic reference/case/ordered duty admission differs')
    contexts = adapter.contexts()
    if (not isinstance(contexts, list) or [c['id'] for c in contexts] != list(CONTEXT_IDS)
            or len({c['id'] for c in contexts}) != 4):
        raise ContractError('Four fixed economic contexts/order differ')
    context_map = {c['id']: c for c in contexts}
    report.update(fixture=dict(name=case.name, case_identity=case.identity(), trip_count=8,
        fleet_N=2, reference_plan_sha256=nr.digest(reference), ordered_duties=duties,
        literal_source_only=True, no_original_data_or_old_plan_input=True), economic_contexts=contexts)
    for row in report['contexts']:
        context = context_map[row['context_id']]
        row.update(objective_identity=nr.digest(context), institution=context['institution'],
            unchanged_components=adapter.value(case, reference, replay, context))
    report['preflight_admitted'] = True; check()
    return adapter, nr, case, reference, duties, context_map


def launch_worker(task, input_plan, qualification, context, adapter, nr, case, reference, duties):
    global CHILD_PUBLICATION
    folder = HERE/'attempt01'/f"{task['ordinal']:03d}-{task['phase']}"; folder.mkdir(exist_ok=False)
    worker_spec = dict(task_id=task['task_id'], context_id=task['context_id'], phase=task['phase'],
        input_plan=input_plan, common_qualification=qualification)
    raw = (json.dumps(worker_spec, indent=2, allow_nan=False)+'\n').encode()
    with (folder/'spec.json').open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    spec_sha = hashlib.sha256(raw).hexdigest()
    save_new(folder/'receipt.json', dict(receipt_complete=False, method_endpoint_accepted=False))
    row = dict(task, attempted=False, reaped=False, parent_endpoint_accepted=False,
        common_qualified=False, strict_method_success=False, config_failure=False, fatal_contract=False,
        failures=[], folder=str(folder), spec_sha256=spec_sha)
    child = None; cleanup_end = None; packet = {}; endpoint = None
    before_children, before_self = children_cpu(), self_cpu(); anchor = time.monotonic()
    row['parent_anchor'] = anchor
    with (folder/'stdout.txt').open('x') as out, (folder/'stderr.txt').open('x') as err:
        try:
            if threading.active_count() != 1:
                raise ContractError('Parent must have one Python thread at spawn')
            CHILD_PUBLICATION = True
            try:
                child = subprocess.Popen([sys.executable, str(HERE/'worker.py'), '--worker', str(folder),
                    '--parent-anchor', repr(anchor), '--spec-sha256', spec_sha], cwd=ROOT,
                    env=dict(os.environ), stdout=out, stderr=err, start_new_session=True,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_CPU, (90, 90)))
                row.update(attempted=True, pid=child.pid)
            finally:
                CHILD_PUBLICATION = False
            if PUBLICATION_STOP is not None:
                raise TimeoutError('Stop deferred through owned PID publication')
            try:
                child.wait(timeout=max(.001, anchor+60-time.monotonic()))
            except subprocess.TimeoutExpired:
                row['timed_out'] = True; cleanup_end = time.monotonic()+3; child.terminate()
                try:
                    child.wait(timeout=min(1., max(.001, cleanup_end-time.monotonic())))
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
            row.update(returncode=child.returncode, reaped=True)
        except BaseException as exc:
            row['failures'].append(dict(type=type(exc).__name__, message=str(exc)))
            if child is None:
                row['config_failure'] = row['fatal_contract'] = True
            if child is not None and child.returncode is None:
                try:
                    cleanup_end = cleanup_end or time.monotonic()+3
                    child.kill(); child.wait(timeout=max(.001, cleanup_end-time.monotonic()))
                    row.update(returncode=child.returncode, reaped=True)
                except BaseException as secondary:
                    row['failures'].append(dict(stage='cleanup', type=type(secondary).__name__, message=str(secondary)))
    row['process_return_elapsed_s'] = time.monotonic()-anchor
    try:
        packet = json.loads(read_once(folder/'receipt.json'))
        if packet.get('receipt_complete') is True and any(packet.get(k) != task[k]
                for k in ('task_id', 'context_id', 'phase')):
            raise ContractError('Returned worker task/context/phase differs')
        prelim = bool(row['reaped'] and row.get('returncode') == 0 and not row.get('timed_out')
            and not row['failures'] and packet.get('receipt_complete') is True
            and packet.get('method_endpoint_accepted') is True and time.monotonic() < anchor+60
            and not any(packet.get(f) for f in ('config_failure', 'fatal_contract', 'resource_violation', 'identity_failure')))
        if prelim:
            artifact = read_once(folder/'best-plan.json'); plan = json.loads(artifact)
            replay = nr.replay_native(case, plan)
            if (plan['case_identity'] != case.identity() or len(plan['vehicles']) != 2
                    or replay.get('replay_ok') is not True
                    or task['phase'] == 'target_qp' and canonical_paths(plan) != canonical_paths(reference)
                    or task['phase'] == 'fixed_duty' and plan_duties(plan) != duty_signature(duties)):
                raise ContractError('Restored full-case physical/N/movement/duty admission differs')
            components = adapter.value(case, plan, replay, context)
            if Q(components['total_exact']) != Q(packet['retained_bill_exact']):
                raise ContractError('Parent full-case retained U exact objective value differs')
            endpoint = dict(plan=plan, plan_sha256=nr.digest(plan), components=components)
            row['owned_retained_artifact'] = dict(path=str(folder/'best-plan.json'),
                bytes_sha256=hashlib.sha256(artifact).hexdigest(), canonical_plan_sha256=endpoint['plan_sha256'],
                full_case_replay_valid=True, parent_values_retained_U=True, caller_replayed_hidden_C=False)
    except Exception as exc:
        row['config_failure'] = row['fatal_contract'] = True
        row['failures'].append(dict(stage='complete_parent_endpoint', type=type(exc).__name__, message=str(exc)))
    end = time.monotonic()
    row.update(worker=packet, complete_endpoint_read_monotonic=end, parent_elapsed_s=end-anchor,
        method_late=end > anchor+60, waited_child_cpu_s=children_cpu()-before_children,
        parent_cpu_s=self_cpu()-before_self, cpu_observation_complete=child is None or row['reaped'],
        unresolved_cpu_reserve_s=90. if child is not None and not row['reaped'] else 0.)
    for flag in ('config_failure', 'fatal_contract', 'resource_violation', 'identity_failure'):
        row[flag] = bool(row.get(flag) or packet.get(flag))
    accepted = bool(endpoint is not None and not row['method_late'] and not row['failures']
        and not row['config_failure'] and not row['fatal_contract'])
    row.update(parent_endpoint_accepted=accepted,
        common_qualified=bool(accepted and task['phase'] == 'target_qp' and packet.get('acquisition_qualified') is True),
        strict_method_success=bool(accepted and packet.get('strict_method_success') is True))
    if not accepted:
        endpoint = None
    save_new(folder/'external-receipt.json', row)
    return row, endpoint


def summary(report):
    increments = {key: [] for key in ('qp_to_fixed_duty', 'qp_to_full', 'fixed_duty_to_full')}
    for context in report['contexts']:
        common = context.get('common_components')
        fixed = context.get('fixed_duty_operational_components'); full = context.get('full_operational_components')
        contrasts = {}
        for key, left, right in (('qp_to_fixed_duty', common, fixed), ('qp_to_full', common, full),
                                  ('fixed_duty_to_full', fixed, full)):
            value = Q(left['total_exact'])-Q(right['total_exact']) if left is not None and right is not None else None
            contrasts[key] = value; increments[key].append(value)
        context['operational_increment_exact'] = contrasts
        for phase in ('fixed_duty', 'full'):
            packet = context[phase].get('worker', {})
            context[phase+'_qualification_discrepancies'] = packet.get('qualification_discrepancies')
            context[phase+'_same_movement_path_discrepancy'] = packet.get('same_movement_path_improvement_discrepancy')
    ledger = [c[p] for c in report['contexts'] for p in PHASES]
    return dict(planned_base_units=1, planned_contexts=4, planned_workers=12,
        recorded_contexts=len(report['contexts']), attempted=sum(r.get('attempted', False) for r in ledger),
        qualified_common=sum(c.get('common_qualified', False) for c in report['contexts']),
        strict_dependent_deliveries=sum(c[p].get('strict_method_success', False)
            for c in report['contexts'] for p in ('fixed_duty', 'full')),
        operational_dependent_endpoints=sum(c.get(p+'_operational_components') is not None
            for c in report['contexts'] for p in ('fixed_duty', 'full')),
        max_observed_worker_rss_bytes=max(((r.get('worker', {}).get('resources') or {}).get('peak_rss_bytes')
            for r in ledger if type((r.get('worker', {}).get('resources') or {}).get('peak_rss_bytes')) in (int, float)), default=None),
        defined_contrasts={k: sum(x is not None for x in v) for k, v in increments.items()},
        complete_four_context_report=len(report['contexts']) == 4
            and all(all(x is not None for x in values) for values in increments.values()),
        pooled_cross_institution_cost_or_gain_mean=None,
        b0_aliases='Posted/strategic/system are economic aliases atb0; onecontext/onesetofsolves',
        available_only_mean=None, scope='Operational delivered endpoint contrasts across4economic contexts ofONEliteralbase, not independentcases',
        promotion_rule=None, statistical_claim=False, certificate_claim=False)


def compact(report):
    rows = []
    for context in report['contexts']:
        costs = {}
        for label in ('unchanged', 'common', 'fixed_duty_operational', 'full_operational'):
            value = context.get(label+'_components')
            costs[label] = None if value is None else dict(total_exact=value['total_exact'],
                total_decimal=float(Q(value['total_exact'])), components=value)
        methods = {}
        for phase in PHASES:
            external = context[phase]; worker = external.get('worker', {}); stats = worker.get('stats') or {}
            methods[phase] = dict(attempted=external.get('attempted'),
                parent_endpoint_accepted=external.get('parent_endpoint_accepted'),
                common_qualified=external.get('common_qualified'), strict_method_success=external.get('strict_method_success'),
                unattempted_reason=external.get('unattempted_reason'), parent_elapsed_s=external.get('parent_elapsed_s'),
                native_calls=worker.get('native_calls'), native_call_attempts=worker.get('native_call_attempts'),
                native_status=stats.get('Status'), native_optimal=stats.get('native_optimal'), raw_MIPGap=stats.get('MIPGap'),
                C=worker.get('candidate_bill_exact'), B=worker.get('fallback_bill_exact'), U=worker.get('retained_bill_exact'),
                native_point=worker.get('native_point'), native_bound=worker.get('native_bound'), bound_scope=worker.get('bound_scope'),
                native_start=worker.get('native_start'), movement_path_changed=worker.get('movement_path_changed'),
                candidate_movement_path_changed=worker.get('candidate_movement_path_changed'),
                duty_assignment_changed=worker.get('duty_assignment_changed'), fixed_duties_preserved=worker.get('fixed_duties_preserved'),
                used_fallback=worker.get('used_fallback'),
                qualification_discrepancies=worker.get('qualification_discrepancies'),
                failures=external.get('failures'), helper_failures=worker.get('helper_failures'), worker_failures=worker.get('failures'))
        increments = context.get('operational_increment_exact', {})
        rows.append(dict(context_id=context['context_id'], institution=context.get('institution'),
            dispatch_order=context['dispatch_order'], pipeline_elapsed_s=context.get('pipeline_elapsed_s'),
            costs=costs, increment_exact=increments,
            increment_decimal={k: None if v is None else float(v) for k, v in increments.items()}, methods=methods))
    return dict(passed=report.get('passed'), summary=report.get('summary'), contexts=rows,
        resources=report.get('resources'), failures=report['failures'],
        scope='ONEliteralbase; no pooledmean acrossinstitutions; externalwrite/exittailacceptancepending')


def publish_markdown(path, readout):
    """Format existing in-memory scalars only; no additional analysis or reads."""
    def show(value):
        if value is None:
            return '—'
        return format(value, '.10g') if type(value) is float else str(value)

    lines = ['# Duty/market seam — compact operational readout', '',
        'One literal synthetic base, four economic contexts. Display decimals only; '
        'READOUT.json retains exact represented costs and components. '
        'No cross-institution pooled mean, physical-optimum or ML claim.', '',
        '| Context | Institution | Unchanged | QP U | Fixed duty | Full | QP−duty | QP−full | Duty−full |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in readout['contexts']:
        costs = [None if row['costs'][key] is None else row['costs'][key]['total_decimal']
            for key in ('unchanged', 'common', 'fixed_duty_operational', 'full_operational')]
        values = costs+[row['increment_decimal'].get(key)
            for key in ('qp_to_fixed_duty', 'qp_to_full', 'fixed_duty_to_full')]
        lines.append('| '+row['context_id']+' | '+str(row['institution'])+' | '+
            ' | '.join(show(v) for v in values)+' |')
    lines += ['', 'The b0 context has three equivalent economic aliases from one set of solves. '
        'QP qualification and strict MIQP delivery are different flags; native status is separate. '
        'Failure counts are retained records, not deduplicated incidents.', '',
        '| Context | Phase | Attempted | QP qualified | Strict MIQP | Native status | Duties changed | Used fallback | Failure records | Parent seconds |',
        '|---|---|---|---|---|---|---|---|---:|---:|']
    for row in readout['contexts']:
        for phase in PHASES:
            method = row['methods'][phase]
            failures = sum(len(method.get(key) or []) for key in ('failures', 'worker_failures', 'helper_failures'))
            values = [method['attempted'], method['common_qualified'] if phase == 'target_qp' else None,
                method['strict_method_success'] if phase != 'target_qp' else None,
                method['native_status'], method['duty_assignment_changed'], method['used_fallback'],
                failures, method['parent_elapsed_s']]
            lines.append('| '+row['context_id']+' | '+phase+' | '+' | '.join(show(v) for v in values)+' |')
    lines += ['', '## Closure and resource observations', '',
        'Administrative passed: '+show(readout['passed'])+'. External publication/exit-tail acceptance remains pending.', '',
        '```json', json.dumps(dict(summary=readout['summary'], resources=readout['resources'], failures=readout['failures']),
            indent=2, allow_nan=False, default=lambda value: str(value) if isinstance(value, Q) else value),
        '```', '', 'Self plus waited-child CPU is one cumulative owner observation; '
        'task deltas are not another charge. Source preparation is adopted once for package caps. '
        'These prepublication measurements are not final external acceptance or containment.', '']
    path = Path(path); temporary = path.with_name(path.name+'.final.tmp')
    with temporary.open('x') as stream:
        stream.write('\n'.join(lines)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def main():
    launch, raw_gate = launch_gate()  # Denies before fixture imports/construction.
    output = HERE/'attempt01'; output.mkdir(exist_ok=False)
    target = output/'receipt.json'; save_new(target, dict(receipt_complete=False, passed=False))
    # All twelve task states exist before any fixture code is loaded.
    report = dict(policy=POLICY, receipt_complete=False, passed=False, config_failure=False,
        contexts=tasks(), failures=[], input_sha256={str(HERE/'LAUNCH.json'): hashlib.sha256(raw_gate).hexdigest()},
        budgets=launch['budgets'], source_revision=launch['source_revision'],
        source_freeze_assumption=launch['source_freeze_assumption'], tracking_prefix=launch['tracking_prefix'],
        numerical_resource_prefix=launch['numerical_resource_prefix'],
        preparation_accounting=launch['preparation_accounting'], no_automatic_retry=True,
        no_external_data_input=True, no_ML_fit=True)
    stopped = None; unresolved = 0.; phase = 'preflight'; final_cpu0 = final_wall0 = None
    preparation = launch['preparation_accounting']

    def stop(signum, frame):
        global PUBLICATION_STOP
        nonlocal stopped
        stopped = stopped or signum
        if CHILD_PUBLICATION:
            PUBLICATION_STOP = PUBLICATION_STOP or signum; return
        raise TimeoutError('Latched owner stop '+str(signum))

    def check():
        if stopped is not None:
            raise TimeoutError('Owner stop remains latched')
        if (threading.active_count() != 1 or rss_bytes() > 5*1024**3
                or self_cpu()+children_cpu()+unresolved+preparation['charged_cpu_s'] > TOTAL_CPU
                or time.monotonic()-WALL0+preparation['elapsed_s'] > TOTAL_WALL):
            report['config_failure'] = True; raise ContractError('Owner thread/RSS/packageCPU/wall bound exceeded')
        if phase == 'preflight' and self_cpu()+preparation['charged_cpu_s'] > 60 or phase == 'finalization' and (
                self_cpu()-final_cpu0 > 60 or time.monotonic()-final_wall0 > 90):
            report['config_failure'] = True; raise ContractError('Preflight/finalization provision exceeded')

    def funded(count):
        return (self_cpu()+children_cpu()+unresolved+preparation['charged_cpu_s']+90*count <= DISPATCH_CPU
            and time.monotonic()-WALL0+preparation['elapsed_s']+63*count+90 <= TOTAL_WALL)

    try:
        for key in THREAD_ENV:
            os.environ[key] = '1'
        resource.setrlimit(resource.RLIMIT_CPU, (60, 1500))
        for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        signal.setitimer(signal.ITIMER_REAL, max(.001, TOTAL_WALL-preparation['elapsed_s']-30-(time.monotonic()-WALL0)))
        adapter, nr, case, reference, duties, contexts = preflight(launch, report, check)
        save_new(output/'preflight.json', {k: report[k] for k in ('input_sha256', 'fixture', 'economic_contexts', 'preflight_admitted')})
        phase = 'dispatch'; resource.setrlimit(resource.RLIMIT_CPU, (1500, 1500))
        for context in report['contexts']:
            check()
            if not funded(3):
                report['dispatch_stopped_reason'] = 'Insufficient270CPU plus closure/wall provision for completecontext'; break
            context['pipeline_anchor'] = time.monotonic(); common = None
            objective = contexts[context['context_id']]
            for index, task_phase in enumerate(context['dispatch_order']):
                task = context[task_phase]
                if task_phase != 'target_qp' and common is None:
                    task['unattempted_reason'] = 'Missing timely fresh-qualified target-QP common U'; continue
                if not funded(3-index):
                    report['dispatch_stopped_reason'] = 'Insufficient remainingcontext funding'; break
                row, endpoint = launch_worker(task, None if task_phase == 'target_qp' else common['plan'],
                    None if task_phase == 'target_qp' else context['common_qualification'],
                    objective, adapter, nr, case, reference, duties)
                context[task_phase] = row; unresolved += row['unresolved_cpu_reserve_s']
                if task_phase == 'target_qp' and row['common_qualified'] and endpoint is not None:
                    common = endpoint; context.update(common_qualified=True, common_components=common['components'])
                    context['common_qualification'] = dict(target_qp_qualified=True, task_id=row['task_id'],
                        context_id=context['context_id'], case_identity=case.identity(),
                        objective_identity=context['objective_identity'], input_plan_sha256=common['plan_sha256'],
                        retained_bill_exact=common['components']['total_exact'], parent_endpoint_accepted=True,
                        caller_replayed_hidden_C=False)
                    for dependent in ('fixed_duty', 'full'):
                        context[dependent+'_operational_components'] = common['components']
                        context[dependent+'_operational_source'] = 'qualified_common_fallback'
                if task_phase != 'target_qp' and endpoint is not None:
                    if Q(endpoint['components']['total_exact']) > Q(common['components']['total_exact']):
                        report['config_failure'] = True
                        raise ContractError('Dependent retained endpoint worsened protected common U')
                    context[task_phase+'_operational_components'] = endpoint['components']
                    context[task_phase+'_operational_source'] = 'parent_admitted_worker_U'
                if row['config_failure'] or row['fatal_contract'] or unresolved:
                    report['config_failure'] = True; report['dispatch_stopped_reason'] = 'Fatalcontract or unresolvedownedchild'; break
                check()
            context['pipeline_complete_monotonic'] = time.monotonic()
            context['pipeline_elapsed_s'] = context['pipeline_complete_monotonic']-context['pipeline_anchor']
            context['pipeline_scope'] = 'Three paid worker anchors plus all transitions/cleanup; not single60second pipeline'
            context['branch_scope'] = 'Each logical QP-to-MIQP branch hastwopaidanchors; commonQPexecuted/chargedONCE; laterbranchwaitvisibleincontextlatency'
            if report['config_failure'] or report.get('dispatch_stopped_reason'):
                break
    except BaseException as exc:
        report['config_failure'] = True
        report['failures'].append(dict(stage=phase, type=type(exc).__name__, message=str(exc)))
    finally:
        phase = 'finalization'; final_cpu0 = self_cpu(); final_wall0 = time.monotonic()
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(90., TOTAL_WALL-preparation['elapsed_s']-(final_wall0-WALL0))))
        try:
            for context in report['contexts']:
                if 'pipeline_anchor' in context and 'pipeline_complete_monotonic' not in context:
                    context['pipeline_complete_monotonic'] = time.monotonic()
                    context['pipeline_elapsed_s'] = context['pipeline_complete_monotonic']-context['pipeline_anchor']
                    context['pipeline_scope'] = 'Aborted paid context through failure/cleanup; no missing stage marked successful'
                for p in PHASES:
                    if not context[p].get('attempted'):
                        context[p].setdefault('unattempted_reason', report.get('dispatch_stopped_reason', 'Owner/prerequisitefailure'))
            report['summary'] = summary(report); check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='finalization', type=type(exc).__name__, message=str(exc)))
        ledger = [c[p] for c in report['contexts'] for p in PHASES]
        report.update(receipt_complete=True, ledger=ledger,
            ledger_complete=len(ledger) == 12 and len({r['task_id'] for r in ledger}) == 12,
            accounting_complete=unresolved == 0, unresolved_cpu_reserve_s=unresolved, stop_signal=stopped,
            resources=dict(self_cpu_s=self_cpu(), waited_children_cpu_s=children_cpu(),
                combined_cpu_s=self_cpu()+children_cpu(), preparation_charge_s=preparation['charged_cpu_s'],
                package_cpu_before_publication_s=self_cpu()+children_cpu()+preparation['charged_cpu_s'],
                package_elapsed_sum_before_publication_s=time.monotonic()-WALL0+preparation['elapsed_s'],
                observed_self_peak_rss_bytes=rss_bytes(), python_threads=threading.active_count(),
                prepublication_only=True, external_total_acceptance_pending=True),
            passed_scope='Administrative all12ledger/accounting closure, not completecomparisons/nativeoptimality')
        try:
            check()
        except BaseException as exc:
            report['config_failure'] = True
            report['failures'].append(dict(stage='final_resource_observation', type=type(exc).__name__, message=str(exc)))
        report['passed'] = bool(not report['config_failure'] and not report['failures']
            and report['ledger_complete'] and report['accounting_complete'] and stopped is None)
        report['compact_readout'] = compact(report)
        remaining = min(90-(time.monotonic()-final_wall0), TOTAL_WALL-preparation['elapsed_s']-(time.monotonic()-WALL0))
        if remaining <= 0:
            raise TimeoutError('No publication/totalwall remains; owned receipt stays incomplete')
        signal.setitimer(signal.ITIMER_REAL, remaining)
        publish(output/'READOUT.json', report['compact_readout'])
        publish_markdown(output/'READOUT.md', report['compact_readout'])
        check()
        publish(target, report)
        print(json.dumps(dict(passed=report['passed'], summary=report.get('summary'),
            resources=report['resources'], readout_json=str(output/'READOUT.json'),
            readout_markdown=str(output/'READOUT.md')), allow_nan=False,
            default=lambda value: str(value) if isinstance(value, Q) else value), flush=True)
        check()
        signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
