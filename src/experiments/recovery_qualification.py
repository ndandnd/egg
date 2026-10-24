"""Single-worker recovery qualification: freeze, solver-free checks, run, analyze.

Importing this module never imports a numerical backend or creates a fixture.
Native dispatch requires a checked source lock and identity-only reservations.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import resource
import signal
import subprocess
import sys
import time

from experiments import codex_local_campaign as campaign

ROOT = Path(__file__).resolve().parents[2]
POLICY = 'recovery-phase1-runner-v1'
CARRIED_MINIMUM = 88.20958837542922
CEILING, DISPATCH_STOP, SHUTDOWN_RESERVE = 900., 720., 180.
OUTER_ALLOCATION, RSS_LIMIT = 32.5, 5*1024**3
MONITOR_INTERVAL_S = .05
SUPERVISOR_STOP_S = 31.
_monitor_child_cpu_s = 0.
THREAD_KEYS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
               'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS')
ARMS = ('static', 'recovery', 'cold', 'start_fault')
DESIGN = ({'base_id':50998, 'trips':40}, {'base_id':50999, 'trips':80})
sha = campaign.digest
stable = campaign.stable


def finite(value, minimum=0.):
    return (not isinstance(value, bool) and isinstance(value, (int,float))
            and math.isfinite(value) and value >= minimum)


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    """Reuse exclusive writes, adding directory durability for receipt entries."""
    path = Path(path)
    campaign.write_new(path, value)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def ledger_events(path):
    path = Path(path)
    values, previous = [], None
    if path.exists():
        for line in path.read_text().splitlines():
            value = json.loads(line)
            if value.get('index') != len(values) or value.get('previous') != previous:
                raise ValueError('Corrupt ledger sequence')
            claimed = value.pop('sha256', None)
            if claimed != stable(value):
                raise ValueError('Corrupt ledger hash')
            value['sha256'] = claimed
            values.append(value)
            previous = claimed
    return values


def append_ledger(path, event):
    values = ledger_events(path)
    value = {**event, 'index':len(values), 'previous':values[-1]['sha256'] if values else None}
    value['sha256'] = stable(value)
    campaign.append(path, value)


def task_matrix(cases):
    if sorted(case['trips'] for case in cases) != [40,80]:
        raise ValueError('Exactly the prespecified 40/80 pair is required')
    tasks = []
    for case in sorted(cases, key=lambda row:row['trips']):
        for arm in ARMS:
            value = {'base_id':case['base_id'], 'trips':case['trips'], 'arm':arm,
                     'seed':17, 'seconds':30., 'fault':'start_setter_exception' if arm == 'start_fault' else None}
            tasks.append({**value, 'id':stable(value)[:20]})
    return tasks


def environment():
    versions = {}
    for name in ('mip','gurobipy','numpy'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {'python':sys.version, 'executable':str(Path(sys.executable).resolve()),
            'system':platform.system(), 'machine':platform.machine(), 'versions':versions,
            'threads':{key:'1' for key in THREAD_KEYS}}


def checked_sources(directory):
    """Require an actual passing solver-free check bound to current runner/tests."""
    directory = Path(directory).resolve()
    result, attempt = read(directory/'result.json'), read(directory/'attempt.json')
    if result.get('passed') is not True or result.get('returncode') != 0 or result.get('failure'):
        raise ValueError('Runner checks have not passed')
    sources = attempt.get('source_hashes', {})
    required = ('src/experiments/recovery_qualification.py', 'src/tests/test_recovery_qualification.py',
                'src/egglab/recovery_coordinator.py')
    for relative in required:
        candidates = [value for key,value in sources.items()
                      if Path(key).resolve() == (ROOT/relative).resolve()
                      or key == relative]
        if candidates != [sha(ROOT/relative)]:
            raise ValueError('Passing check does not bind current source: '+relative)
    if result.get('source_changes'):
        raise ValueError('Sources changed during solver-free check')
    termination = result.get('termination',{})
    groups_gone = (termination.get('group_absent') is True or
                   bool(termination.get('owned_pgids')) and termination.get('surviving_pgids')==[])
    if (not groups_gone
            or result.get('stdout_sha256')!=sha(directory/'stdout.log')
            or result.get('stderr_sha256')!=sha(directory/'stderr.log')
            or not finite(result.get('cumulative_qualification_charge_s'),CARRIED_MINIMUM)):
        raise ValueError('Runner check output/ownership/accounting receipt is incomplete')
    return {str(directory/name):sha(directory/name) for name in ('attempt.json','result.json')}


def reservation(design, registry):
    """Identity metadata only; never inspect outcome or protected-case records."""
    if registry.get('scopes') != ['screen','training','study'] or not registry.get('attestation'):
        raise ValueError('Require complete identity-only exclusion registry and attestation')
    used = registry.get('used_base_ids')
    if not isinstance(used, list) or any(type(value) is not int for value in used):
        raise ValueError('Malformed excluded identity inventory')
    ids = [row['base_id'] for row in design]
    if (len(ids) != 2 or len(set(ids)) != 2 or any(type(i) is not int or not 50000 <= i < 51000 for i in ids)
            or set(ids) & set(used)):
        raise ValueError('Qualification bases are not fresh, independent reserved scale IDs')
    task_matrix(design)


def accounting(path):
    value = read(path)
    if not finite(value.get('charged_cpu_s'), CARRIED_MINIMUM):
        raise ValueError('Cumulative qualification accounting cannot restart below carried charge')
    evidence = value.get('evidence_hashes', {})
    required = ROOT/'research-20261023/RECOVERY_COORDINATOR_RESULTS.md'
    if evidence.get(str(required)) != sha(required):
        raise ValueError('Accounting must bind the coordinator cumulative-charge evidence')
    verify_hashes(evidence)
    return value


def verify_hashes(inventory):
    for path, expected in inventory.items():
        if sha(path) != expected:
            raise ValueError('Frozen file changed: '+str(path))


def freeze_accounting(lock, lockpath, receiptpath):
    """Native launch stays disabled until an external bounded freeze is receipted."""
    receipt = read(receiptpath)
    termination = receipt.get('termination',{})
    if (receipt.get('phase')!='recovery_fixture_freeze' or receipt.get('passed') is not True
            or receipt.get('failure') is not None or receipt.get('monitor_failure') is not None
            or receipt.get('source_changes')!=[] or receipt.get('lock_sha256')!=sha(lockpath)
            or not termination.get('owned_pgids') or termination.get('surviving_pgids')!=[]
            or not finite(receipt.get('charged_cpu_s')) or not finite(receipt.get('supervisor_cpu_s'))
            or not finite(receipt.get('elapsed_allocation_s')) or receipt['elapsed_allocation_s']>OUTER_ALLOCATION
            or not finite(receipt.get('sampled_peak_rss_bytes')) or receipt['sampled_peak_rss_bytes']>RSS_LIMIT
            or not finite(receipt.get('cumulative_qualification_charge_s'),
                          lock['carried_charge_s']+receipt.get('charged_cpu_s',0)+receipt.get('supervisor_cpu_s',0))):
        raise ValueError('Missing/invalid externally supervised freeze resource/accounting receipt')
    return {**lock,'freeze_charge_s':max(lock['freeze_charge_s'],
        receipt['cumulative_qualification_charge_s']-lock['carried_charge_s'])}


def freeze(args):
    """Only an explicitly invoked, externally budgeted freeze constructs fixtures."""
    before, cpu0 = time.monotonic(), time.process_time()
    checks = checked_sources(args.checks)
    prior = accounting(args.accounting)
    if prior['charged_cpu_s'] < read(Path(args.checks)/'result.json')['cumulative_qualification_charge_s']:
        raise ValueError('Carried accounting omits the passing runner check/admin charges')
    design = read(args.design) if args.design else list(DESIGN)
    registry = read(args.reservations)
    reservation(design, registry)
    if prior['charged_cpu_s']+OUTER_ALLOCATION+SHUTDOWN_RESERVE > CEILING:
        raise ValueError('No room for freeze allocation plus shutdown')
    library = Path(args.native_library).resolve()
    if not library.is_file():
        raise ValueError('An explicit native library must be hashed without loading it')
    from egglab import claude_scale_cases as generator
    from experiments.codex_offline_rank import heuristic
    folder = Path(args.lock).resolve().parent/'fixtures'
    folder.mkdir()  # A partial previous freeze cannot be silently reused.
    cases, assets = [], {}
    for item in design:
        case = generator.make_case(item['base_id'], item['trips'])
        market = generator.market(case, 'day')
        source = campaign.prune(case, heuristic(case), keep=.30, floor=3)
        path = folder/f"base{item['base_id']}-n{item['trips']}.json"
        payload = {'case':asdict(case), 'a':list(market.a), 'b':list(market.b)}
        write_new(path, payload)
        assets[str(path)] = sha(path)
        cases.append({**item, 'fixture':str(path), 'identity':case.identity(),
                      'movement_ids':[m.id for m in case.movements],
                      'restricted_identity':source.identity(),
                      'restricted_movement_ids':[m.id for m in source.movements],
                      'market_sha256':stable({'a':payload['a'],'b':payload['b']})})
    proof_paths = [Path(args.accounting).resolve(), Path(args.reservations).resolve()]
    if args.design:
        proof_paths.append(Path(args.design).resolve())
    lock = {'policy':POLICY, 'cases':cases, 'tasks':task_matrix(cases), 'sources':campaign.sources(),
            'assets':assets, 'models':{}, 'checks':checks,
            'evidence':{str(path):sha(path) for path in proof_paths},
            'prior_evidence':prior['evidence_hashes'], 'carried_charge_s':prior['charged_cpu_s'],
            'environment':environment(), 'backend':args.backend,
            'native_library':{'path':str(library),'sha256':sha(library)},
            'generator':'claude-scale-v1; TRAIN-derived parameter assignment; fresh identity-only bases',
            'ranking':'experiments.codex_offline_rank.heuristic', 'keep':.30, 'coverage_floor':3,
            'tariff':'day', 'split':{'prefix_integer_s':12.,'prefix_physical_s':15.,
                                    'full_integer_s':24.,'physical_s':27.,'deadline_s':30.,
                                    'completion_cumulative_s':3.,'finalization_s':3.},
            'freeze_charge_s':max(time.monotonic()-before,time.process_time()-cpu0)+1.,
            'freeze_accounting':'conservative elapsed/CPU maximum plus one-second materialization allowance'}
    write_new(args.lock, lock)
    return {'lock':str(Path(args.lock).resolve()),'sha256':sha(args.lock),'tasks':8,
            'carried_plus_freeze_s':lock['carried_charge_s']+lock['freeze_charge_s']}


def verify_lock(lock, *, worker=False):
    if lock.get('policy') != POLICY or lock.get('tasks') != task_matrix(lock['cases']):
        raise ValueError('Invalid phase-1 task lock')
    if not finite(lock.get('carried_charge_s'), CARRIED_MINIMUM) or not finite(lock.get('freeze_charge_s')):
        raise ValueError('Invalid carried qualification accounting')
    for key in ('sources','assets','checks','evidence','prior_evidence'):
        verify_hashes(lock[key])
    check_results = [Path(path).parent for path in lock['checks'] if Path(path).name=='result.json']
    if len(check_results)!=1 or checked_sources(check_results[0])!=lock['checks']:
        raise ValueError('Native lock lacks source-bound runner checks')
    if (lock.get('backend') not in ('CBC','GRB') or lock.get('models')!={}
            or lock.get('keep')!=.30 or lock.get('coverage_floor')!=3 or lock.get('tariff')!='day'
            or lock.get('ranking')!='experiments.codex_offline_rank.heuristic'
            or lock.get('split')!={'prefix_integer_s':12.,'prefix_physical_s':15.,'full_integer_s':24.,
                'physical_s':27.,'deadline_s':30.,'completion_cumulative_s':3.,'finalization_s':3.}):
        raise ValueError('Qualification policy differs from prospective protocol')
    verify_hashes({lock['native_library']['path']:lock['native_library']['sha256']})
    if environment() != lock['environment']:
        raise ValueError('Frozen interpreter/backend environment changed')
    if worker and any(os.environ.get(key) != '1' for key in THREAD_KEYS):
        raise ValueError('Worker numerical thread limits differ from lock')


def restore_case(payload):
    from egglab import native_recharge as nr
    data = deepcopy(payload)
    data['trips'] = tuple(nr.Trip(**value) for value in data['trips'])
    data['movements'] = tuple(nr.Movement(**{**value,'legs':tuple(nr.Leg(**leg) for leg in value['legs'])})
                              for value in data['movements'])
    data['resources'] = tuple(nr.Resource(**value) for value in data['resources'])
    data['market_edges_min'] = tuple(data['market_edges_min'])
    return nr.NativeCase(**data)


PATTERNS = ((rb'Loaded user MIP start with objective[^\r\n]*', 'accepted'),
            (rb'User MIP start produced solution[^\r\n]*', 'accepted'),
            (rb'MIPStart provided solution with cost[^\r\n]*', 'accepted'),
            (rb'mipstart values could not be used[^\r\n]*', 'rejected'),
            (rb'User MIP start did not produce a new incumbent[^\r\n]*', 'unknown'),
            (rb'MIPStart values read[^\r\n]*', 'unknown'))


def start_evidence(raw, submissions):
    matches = []
    for pattern,status in PATTERNS:
        for match in re.finditer(pattern, raw, re.IGNORECASE):
            matches.append({'offset_start':match.start(),'offset_end':match.end(),
                            'text':match.group().decode(errors='replace'),'status':status})
    matches.sort(key=lambda value:value['offset_start'])
    # Status is per actual submission, never inferred from setter success alone.
    classified = []
    for item in submissions:
        hits = [match for match in matches if item.get('log_start', math.inf) <= match['offset_start']
                and match['offset_end'] <= item.get('log_end', -math.inf)]
        statuses = {hit['status'] for hit in hits}
        status = 'accepted' if statuses == {'accepted'} else 'rejected' if statuses == {'rejected'} else 'unknown'
        classified.append({'inventory_sha256':item['inventory_sha256'], 'status':status,
                           'processed':bool(hits), 'evidence':hits})
    return {'submitted':len(submissions),'classified':classified,'unattributed_log_matches':[
        match for match in matches if not any(match in item['evidence'] for item in classified)]}


def native_append(folder, event):
    campaign.append(Path(folder)/'native.jsonl', event)


def capture_metadata(task, policy, case_identity, round_index):
    phase, _ = integer_gate_spec(task,policy,case_identity)
    if type(round_index) is not int or round_index < 0:
        raise ValueError('Invalid incumbent capture round')
    for key in ('lock_sha256','attempt_sha256'):
        if not isinstance(policy.get(key),str) or re.fullmatch('[0-9a-f]{64}',policy[key]) is None:
            raise ValueError('Missing incumbent capture '+key)
    return {'task_id':task['id'],'task_sha256':stable(task),'case_identity':case_identity,
            'phase':phase,'round':round_index,'anchor':policy['anchor'],
            'lock_sha256':policy['lock_sha256'],'attempt_sha256':policy['attempt_sha256']}


def verify_capture_reference(folder, task, policy, reference):
    """Check one immutable flat capture; no model/backend objects are involved."""
    metadata = capture_metadata(task,policy,reference['case_identity'],reference['round'])
    name = f"incumbent-{metadata['phase']}-round{metadata['round']}.json"
    if (reference.get('event') != 'native_incumbent_reference' or
            reference.get('schema') != 'recovery-native-incumbent-reference-v1' or
            any(reference.get(key) != value for key,value in metadata.items()) or
            reference.get('path') != name or type(reference.get('offset_bytes')) is not int or
            reference['offset_bytes'] != 0 or type(reference.get('length_bytes')) is not int or
            reference['length_bytes'] <= 0):
        raise ValueError('Incumbent capture reference identity/range mismatch')
    path = Path(folder)/name
    if path.is_symlink():
        raise ValueError('Incumbent capture must be an owned flat file')
    raw = path.read_bytes()
    if (len(raw) != reference['length_bytes'] or
            hashlib.sha256(raw).hexdigest() != reference.get('sha256')):
        raise ValueError('Incumbent capture bytes/hash mismatch')
    payload = json.loads(raw)
    if (payload.get('schema') != 'recovery-native-incumbent-capture-v1' or
            any(payload.get(key) != value for key,value in metadata.items()) or
            payload.get('capture',{}).get('event') != 'native_incumbent' or
            payload['capture'].get('case_identity') != metadata['case_identity'] or
            payload['capture'].get('round') != metadata['round']):
        raise ValueError('Incumbent capture envelope mismatch')
    return True


def persist_incumbent_capture(folder, task, policy, event):
    """Serialize the complete diagnostic once, durably, then forward only its reference."""
    from egglab.recovery_coordinator import _diagnostic
    if event.get('event') != 'native_incumbent':
        raise ValueError('Expected complete native incumbent capture')
    metadata = capture_metadata(task,policy,event['case_identity'],event['round'])
    name = f"incumbent-{metadata['phase']}-round{metadata['round']}.json"
    payload = {'schema':'recovery-native-incumbent-capture-v1',**metadata,'capture':_diagnostic(event)}
    raw = (json.dumps(payload,separators=(',',':'),allow_nan=False)+'\n').encode()
    path = Path(folder)/name
    with path.open('xb') as stream:
        if stream.write(raw) != len(raw):
            raise OSError('Incomplete incumbent capture write')
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent,os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    reference = {'event':'native_incumbent_reference','schema':'recovery-native-incumbent-reference-v1',
                 **metadata,'path':name,'offset_bytes':0,'length_bytes':len(raw),
                 'sha256':hashlib.sha256(raw).hexdigest()}
    verify_capture_reference(folder,task,policy,reference)
    return reference


def record_planner_event(folder, task, state, event, record=None):
    """Fail-closed planner sink, including callbacks whose exceptions the core catches."""
    from egglab.recovery_coordinator import _diagnostic
    try:
        if native_event_is_failure(task,state,event):
            state['engineering_events'].append(_diagnostic(event))
        forwarded = event
        if event.get('event') == 'native_incumbent':
            forwarded = persist_incumbent_capture(folder,task,state['capture_policy'],event)
            state.setdefault('capture_references',[]).append(deepcopy(forwarded))
        native_append(folder,{'source':'planner',**_diagnostic(forwarded)})
        if record:
            record(forwarded)
    except Exception as exc:
        state['sink_failure'] = repr(exc)
        raise


def audit_capture_references(folder, task, state, events):
    registered = state.get('capture_references',[])
    identities = {stable(reference) for reference in registered}
    for event in events:
        if event.get('event') == 'native_incumbent':
            raise ValueError('Unreferenced full incumbent reached materialization')
        if event.get('event') == 'native_incumbent_reference':
            # The frozen coordinator adds its prefix/full stage to callback rows.
            reference = {key:value for key,value in event.items() if key != 'stage'}
            if (('stage' in event and event['stage'] != event.get('phase')) or
                    stable(reference) not in identities):
                raise ValueError('Unregistered incumbent capture reference')
    for reference in registered:
        verify_capture_reference(folder,task,state['capture_policy'],reference)
    return len(registered)


def stage_timing(event, task, anchor, at, cutoff):
    if not finite(anchor) or not finite(at,anchor):
        raise ValueError('Invalid anchored admission timing')
    return {'event':event,'task_id':task['id'],'anchor':anchor,'at':at,
            'elapsed_s':at-anchor,'cutoff':cutoff}


def materialization_reference(folder, task, locksha, anchor, started, receipt, *, clock=time.monotonic):
    """Bind immutable completion after it exists; never rewrite result or completion."""
    marker = read(Path(folder)/'completion.json')
    if (marker['task'] != task or marker['lock_sha256'] != locksha or
            marker['parent_monotonic'] != anchor or
            marker['result_sha256'] != receipt['result_sha256'] or
            marker['finished_monotonic'] != receipt['finished_monotonic']):
        raise ValueError('Materialization completion identity mismatch')
    value = {'schema':'recovery-materialization-reference-v1','task_id':task['id'],
             'lock_sha256':locksha,'anchor':anchor,'started_monotonic':started,
             'started_elapsed_s':started-anchor,
             'completion_marker':{'path':'completion.json','sha256':sha(Path(folder)/'completion.json'),
                 'finished_monotonic':marker['finished_monotonic'],'elapsed_s':marker['elapsed_s'],
                 'censored':marker['censored']},
             'post_completion_monotonic':receipt['completion_monotonic'],
             'result_sha256':receipt['result_sha256']}
    write_new(Path(folder)/'materialization-reference.json',value)
    ended = clock()
    return {**receipt,'completion_monotonic':ended,'censored':receipt['censored'] or ended>anchor+30.}


class IntegerGateClosed(TimeoutError):
    """Guard-owned refusal issued before any underlying model build."""
    def __init__(self, token):
        self.token = token
        super().__init__('integer_gate_closed:'+token)


def integer_gate_spec(task, policy, case_identity):
    """Resolve only the frozen case/arm's original anchored integer cutoff."""
    if (not isinstance(policy,dict) or not isinstance(task.get('id'),str) or not task['id'] or
            policy.get('task_id') != task['id'] or
            policy.get('task_sha256') != stable(task) or
            not finite(policy.get('anchor'))):
        raise ValueError('Integer gate task/anchor mismatch')
    full, restricted = policy['full_identity'], policy['restricted_identity']
    if not all(isinstance(value,str) and value for value in (full,restricted,case_identity)):
        raise ValueError('Integer gate requires frozen case identities')
    arm = task['arm']
    if arm in ('recovery','start_fault') and case_identity == restricted and restricted != full:
        phase, seconds = 'prefix', 12.
    elif arm in ('recovery','start_fault') and case_identity == full:
        phase, seconds = 'full', 24.
    elif arm == 'static' and case_identity == restricted:
        phase, seconds = 'static', 24.
    elif arm == 'cold' and case_identity == full:
        phase, seconds = 'cold', 24.
    else:
        raise ValueError('Integer gate case/phase differs from immutable lock')
    return phase, policy['anchor']+seconds


def expected_integer_gate(task, state, event):
    """Consume one durable pre-build token; malformed/stale evidence fails closed."""
    pending = state.pop('integer_gate_pending', None)
    if not isinstance(pending, dict) or state.get('sink_failure'):
        return False
    try:
        evidence, policy = pending['evidence'], state['integer_gate_policy']
        if not isinstance(evidence,dict):
            return False
        token = evidence['token']
        phase, cutoff = integer_gate_spec(task, policy, evidence['case_identity'])
        observed, anchor = evidence['observed_monotonic'], evidence['anchor']
        matched = (pending.get('durable') is True and
                   isinstance(token,str) and re.fullmatch('[0-9a-f]{32}',token) is not None and
                   event.get('event') == 'native_search_failed' and
                   event.get('stage') == 'model_build' and
                   event.get('error_type') == IntegerGateClosed.__name__ and
                   event.get('error') == pending['error'] == str(IntegerGateClosed(token)) and
                   evidence.get('event') == 'integer_gate_closed' and
                   evidence.get('task_id') == task.get('id') == policy['task_id'] and
                   evidence.get('task_sha256') == stable(task) == policy['task_sha256'] and
                   evidence.get('phase') == phase and
                   evidence.get('guard_point') == 'before_model_build' and
                   evidence.get('native_dispatched') is False and
                   finite(anchor) and anchor == policy['anchor'] and
                   finite(evidence.get('integer_cutoff')) and evidence['integer_cutoff'] == cutoff and
                   finite(observed) and observed >= cutoff and
                   finite(evidence.get('elapsed_s')) and evidence['elapsed_s'] == observed-anchor)
    except (KeyError, TypeError, ValueError):
        return False
    if matched:
        state.setdefault('expected_budget_stops', []).append(deepcopy(evidence))
    return bool(matched)


def native_event_is_failure(task, state, event):
    expected_fault = (task['arm']=='start_fault' and state['fault_exercised']
                      and event.get('event')=='native_search_failed'
                      and event.get('stage')=='start_attach'
                      and 'prospectively injected' in event.get('error',''))
    expected_cutoff = (event.get('event')=='native_search_failed'
                       and expected_integer_gate(task,state,event))
    return ((event.get('event')=='native_search_failed' and not expected_fault and not expected_cutoff)
            or (event.get('event')=='candidate_rejected' and
                event.get('stage') not in ('raw_admission','completion_admission')))


def dispatch_allowed(parent_pid, folder, state):
    return (os.getppid()==parent_pid and not state['sink_failure']
            and not state['engineering_events'] and not (Path(folder)/'STOP').exists())


@contextmanager
def instrument_native(lock, task, folder, *, anchor=None):
    """Existing planner hooks only: seed, actual binary inventory and native log offsets."""
    from egglab import native_pathflow as pf
    original_build, original_attach, original_optimize = pf.build_feasible_model, pf._attach_pricing_start, pf._optimize_once
    state = {'submission':None,'submissions':[],'fault_exercised':False,'sink_failure':None,
             'engineering_events':[], 'expected_budget_stops':[]}
    if anchor is not None:
        frozen = next(row for row in lock['cases'] if row['base_id']==task['base_id'])
        state['integer_gate_policy'] = {'task_id':task['id'],'task_sha256':stable(task),
            'anchor':anchor,'full_identity':frozen['identity'],
            'restricted_identity':frozen['restricted_identity']}

    def emit(value):
        try:
            native_append(folder, value)
        except Exception as exc:
            state['sink_failure'] = repr(exc)
            raise

    def build(*args, **kwargs):
        if anchor is not None:
            case = args[0] if args else kwargs['case']
            identity = case.identity()
            phase, cutoff = integer_gate_spec(task,state['integer_gate_policy'],identity)
            observed = time.monotonic()
            if not finite(observed):
                raise ValueError('Nonfinite integer gate observation')
            if observed >= cutoff:
                exc = IntegerGateClosed(os.urandom(16).hex())
                evidence = {'event':'integer_gate_closed','token':exc.token,
                    'task_id':task['id'],'task_sha256':stable(task),'case_identity':identity,
                    'phase':phase,'anchor':anchor,'integer_cutoff':cutoff,
                    'observed_monotonic':observed,'elapsed_s':observed-anchor,
                    'guard_point':'before_model_build','native_dispatched':False}
                emit(evidence)
                state['integer_gate_pending'] = {'evidence':deepcopy(evidence),
                    'error':str(exc),'durable':True}
                raise exc
        built = original_build(*args, **kwargs)
        if anchor is not None and time.monotonic()>=cutoff:
            raise TimeoutError('Native model build exhausted integer allowance')
        runtime = built['backend_runtime']
        if (runtime.get('requested') != lock['backend'] or
                runtime.get('native_library_sha256') != lock['native_library']['sha256']):
            raise ValueError('Native backend/library differs from immutable lock')
        built['model'].seed, built['model'].threads, built['model'].verbose = 17, 1, 1
        emit({'event':'native_model','runtime':runtime,'seed':17,'threads':1})
        return built

    def attach(case, built, selected):
        if anchor is not None and time.monotonic()>=anchor+24.:
            raise TimeoutError('No start setter after full integer gate')
        if task['arm'] == 'start_fault':
            if not (Path(folder)/'fallback.json').is_file():
                raise ValueError('Fault injection attempted before durable fallback')
            state['fault_exercised'] = True
            emit({'event':'injected_start_setter_exception','after_durable_fallback':True})
            raise RuntimeError('prospectively injected binary start setter exception')
        bounds = [(var.idx,var.lb,var.ub) for var in built['model'].vars]
        constraints = len(built['model'].constrs)
        mapping = original_attach(case, built, selected)
        actual = built['model'].start
        inventory = [{'movement_id':mode.id,'variable_index':var.idx,'value':value}
                     for mode,var,(submitted,value) in zip(case.movements,built['x'],actual)
                     if submitted is var]
        if (len(actual) != len(case.movements) or len(inventory) != len(actual)
                or any(row['value'] not in (0,1) for row in inventory)
                or any(var.var_type != 'B' for var,_ in actual)
                or [row['value'] for row in inventory] != [int(mode.id in selected) for mode in case.movements]
                or bounds != [(var.idx,var.lb,var.ub) for var in built['model'].vars]
                or constraints != len(built['model'].constrs)):
            raise ValueError('Actual native binary start inventory differs from full movement mapping')
        item = {'event':'binary_start_inventory','inventory':inventory,
                'inventory_sha256':stable(inventory),'continuous_submitted':0,
                'continuous_unset':sum(var.var_type == 'C' for var in built['model'].vars),
                'bounds_constraints_unchanged':True,'mapping':mapping}
        state['submission'] = item
        emit(item)
        return mapping

    def offset():
        # Native CBC/Gurobi output uses C stdio; Python flush alone does not
        # establish useful byte spans. This is libc flushing, not a solver call.
        import ctypes
        sys.stdout.flush()
        sys.stderr.flush()
        flush = ctypes.CDLL(None).fflush
        flush.argtypes, flush.restype = [ctypes.c_void_p], ctypes.c_int
        if flush(None)!=0:
            raise OSError('Native log stdio flush failed')
        return os.fstat(1).st_size

    def optimize(built, budget, deadline):
        item = state['submission']
        fixed = bool(built['x']) and all(var.lb == var.ub for var in built['x'])
        start = offset()
        try:
            return original_optimize(built, budget, deadline)
        finally:
            end = offset()
            emit({'event':'native_log_span','log_start':start,'log_end':end,'fixed_topology':fixed,
                  'inventory_sha256':None if item is None else item['inventory_sha256']})
            if item is not None and not fixed:
                state['submissions'].append({**item,'log_start':start,'log_end':end})
            state['submission'] = None

    pf.build_feasible_model, pf._attach_pricing_start, pf._optimize_once = build, attach, optimize
    try:
        yield state
    finally:
        pf.build_feasible_model, pf._attach_pricing_start, pf._optimize_once = original_build, original_attach, original_optimize


def control(case, target, a, b, task, anchor, storage, budget, planner, allowed):
    """Standalone static/cold controls share the recovery final reserves and guards."""
    from egglab import recovery_coordinator as rc
    schedule = rc.Schedule(anchor, anchor+30.)
    events, failures, selected, lower, provenance = [], [], None, None, []
    allowance = rc.CompletionAllowance()
    native = None
    try:
        now = time.monotonic()
        if now < schedule.full_integer_end and allowed():
            inner = replace(budget, wall_seconds=schedule.planner_end-now,
                            phase_seconds=min(budget.phase_seconds,schedule.full_integer_end-now))
            with rc.native_limits(integer_end=schedule.full_integer_end, planner_end=schedule.planner_end,
                                  allowance=allowance, clock=time.monotonic, allowed=allowed, events=events):
                native = planner(target,a,b,inner,record=lambda row:events.append(row), completion=True,
                                 start_plan=None,start_case=None,deadline=schedule.planner_end)
            returned = time.monotonic()
            events.append(stage_timing('control_planner_return',task,anchor,returned,schedule.planner_end))
            if native.get('plan') is not None:
                entered = time.monotonic()
                if entered >= schedule.planner_end:
                    raise TimeoutError('Control planner returned after physical admission cutoff')
                events.append(stage_timing('control_lift_enter',task,anchor,entered,schedule.planner_end))
                try:
                    selected = rc.lift_plan(target,case,native['plan'],a=a,b=b)
                finally:
                    events.append(stage_timing('control_lift_exit',task,anchor,time.monotonic(),schedule.planner_end))
                if time.monotonic() > schedule.planner_end:
                    selected = None
                    raise TimeoutError('Control physical admission exceeded shared planner cutoff')
                storage.save_fallback(deepcopy(selected))
            if task['arm'] == 'cold':
                lower, provenance = rc._full_lower(native,case,a,b,time.monotonic,schedule.planner_end)
    except Exception as exc:
        failures.append({'stage':'control','error_type':type(exc).__name__,'error':str(exc)})
    status = 'feasible' if selected else 'no_plan'
    if lower is not None and selected is not None:
        if lower > selected['true_bill']+rc.pf.BOUND_GUARD:
            status, lower, provenance = 'bound_replay_contradiction', None, []
        else:
            status = 'certified' if selected['true_bill']-lower <= budget.epsilon else 'bounded'
    events.append(stage_timing('control_materialization_start',task,anchor,time.monotonic(),schedule.deadline))
    result = {'policy':POLICY,'status':status,'mode':'static_restricted' if task['arm']=='static' else 'cold_full',
              'fallback':selected,'selected':selected,'global_lower_bound':lower,'bound_provenance':provenance,
              'restricted_prefix_lower_diagnostic':rc._diagnostic(None if native is None else native.get('lower'))
                  if task['arm']=='static' else None,
              'completion_spent_s':allowance.spent,'events':rc._diagnostic(events),'failures':failures}
    return storage.materialize(result,schedule=schedule,clock=time.monotonic)


def worker(args):
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGINT})
    folder = Path(args.output).resolve()
    # The frozen campaign watchdog holds PGID identity and kills on supervisor death.
    subprocess.Popen([sys.executable,'-m','experiments.codex_local_campaign','watch-parent',
                      '--parent-pid',str(args.parent_pid),'--worker-pid',str(os.getpid()),
                      '--output',str(folder)], preexec_fn=lambda:signal.signal(signal.SIGTERM,signal.SIG_IGN))
    attempt, lock = read(folder/'attempt.json'), read(args.lock)
    task, anchor = attempt['task'], attempt['parent_monotonic']
    if attempt['lock_sha256'] != sha(args.lock) or task not in lock['tasks']:
        raise ValueError('Worker attempt/lock mismatch')
    from egglab import recovery_coordinator as rc
    state = None

    class Storage(rc.DirectoryStorage):
        def _write(self, name, value):
            if name == 'completion.json':
                value = {**value,'task':task,'lock_sha256':attempt['lock_sha256']}
            return super()._write(name,value)

        def materialize(self, result, *, schedule, clock):
            started = clock()
            result.setdefault('events',[]).append(stage_timing('materialization_start',task,anchor,started,schedule.deadline))
            if state is not None:
                try:
                    audit_capture_references(folder,task,state,result['events'])
                except Exception as exc:
                    state['sink_failure'] = repr(exc)
                    result.setdefault('failures',[]).append({'stage':'capture_reference',
                        'error_type':type(exc).__name__,'error':str(exc)})
            for event in result.get('events', []):
                native_append(folder, {'source':'coordinator',**event})
            selected = result.get('selected')
            if selected is not None:
                self._write('plan.json',selected['plan'])
                self._write('replay.json',selected['replay'])
            result.update(task=task,lock_sha256=attempt['lock_sha256'],cpu_s=time.process_time(),
                          native_state=deepcopy(state),case_identity=frozen['identity'])
            if state is not None and state['sink_failure']:
                result['failures'].append({'stage':'native_sink','error':state['sink_failure']})
            receipt = super().materialize(result,schedule=schedule,clock=clock)
            receipt = materialization_reference(folder,task,attempt['lock_sha256'],anchor,started,receipt,clock=clock)
            ack = {'task_id':task['id'],'lock_sha256':attempt['lock_sha256'],
                   'parent_monotonic':anchor,'completion_monotonic':receipt['completion_monotonic'],
                   'completion_sha256':sha(folder/'completion.json'),
                   'result_sha256':receipt['result_sha256']}
            payload = (json.dumps(ack,sort_keys=True,allow_nan=False)+'\n').encode()
            if len(payload)>4096 or os.write(args.ack_fd,payload)!=len(payload):
                raise OSError('Completion acknowledgment pipe failed')
            return receipt

    storage = Storage(folder)
    frozen = {'identity':None}
    try:
        verify_lock(lock,worker=True)
        frozen = next(row for row in lock['cases'] if row['base_id']==task['base_id'])
        payload = read(frozen['fixture'])
        case = restore_case(payload['case'])
        from experiments.codex_offline_rank import heuristic
        target = campaign.prune(case,heuristic(case),keep=.30,floor=3)
        if (case.identity()!=frozen['identity'] or [m.id for m in case.movements]!=frozen['movement_ids']
                or target.identity()!=frozen['restricted_identity']
                or [m.id for m in target.movements]!=frozen['restricted_movement_ids']
                or stable({'a':payload['a'],'b':payload['b']})!=frozen['market_sha256']):
            raise ValueError('Fixture, market or movement-order lock mismatch')
        budget = rc.pf.Budget(backend=lock['backend'],threads=1,phase_seconds=24.,wall_seconds=30.)
        with instrument_native(lock,task,folder,anchor=anchor) as state:
            state['capture_policy'] = {**state['integer_gate_policy'],
                'lock_sha256':attempt['lock_sha256'],'attempt_sha256':sha(folder/'attempt.json')}
            state['capture_references'] = []
            def allowed():
                return dispatch_allowed(args.parent_pid,folder,state)

            def planner(*a, record=None, **kw):
                def sink(event):
                    record_planner_event(folder,task,state,event,record)
                return rc.pf.solve_planner(*a, record=sink, **kw)

            if task['arm'] in ('recovery','start_fault'):
                rc.coordinate(target,case,payload['a'],payload['b'],parent_monotonic=anchor,
                              deadline=anchor+30.,storage=storage,budget=budget,planner=planner,allowed=allowed)
            else:
                control(case,target if task['arm']=='static' else case,payload['a'],payload['b'],
                        task,anchor,storage,budget,planner,allowed)
    except Exception as exc:
        if not (folder/'result.json').exists():
            storage.materialize({'policy':POLICY,'status':'worker_failure','selected':None,'fallback':None,
                                 'global_lower_bound':None,'bound_provenance':[], 'events':[],
                                 'failures':[{'stage':'worker','error_type':type(exc).__name__,'error':str(exc)}]},
                                schedule=rc.Schedule(anchor,anchor+30.),clock=time.monotonic)


def completion_endpoint(folder, task, locksha, anchor, *, acknowledgment):
    """Strict endpoint validation; failures may be terminal but never timely-valid."""
    try:
        folder = Path(folder)
        marker, result = read(folder/'completion.json'), read(folder/'result.json')
        end = marker['finished_monotonic']
        if (marker['task'] != task or marker['lock_sha256'] != locksha
                or marker['parent_monotonic'] != anchor or marker['deadline'] != anchor+30.
                or result['task'] != task or result['lock_sha256'] != locksha
                or not finite(end,anchor) or not finite(marker['elapsed_s'])
                or marker['elapsed_s'] != end-anchor or marker['result_sha256'] != sha(folder/'result.json')
                or type(marker['censored']) is not bool):
            raise ValueError('Completion identity/hash/schema mismatch')
        elapsed = end-anchor
        ack = acknowledgment
        if (not isinstance(ack,dict) or ack.get('task_id')!=task['id'] or ack.get('lock_sha256')!=locksha
                or ack.get('parent_monotonic')!=anchor or ack.get('result_sha256')!=marker['result_sha256']
                or ack.get('completion_sha256')!=sha(folder/'completion.json')
                or not finite(ack.get('completion_monotonic'),end)):
            raise ValueError('Missing/malformed post-fsync completion acknowledgment')
        censored = elapsed>30. or marker['censored'] or ack['completion_monotonic']>anchor+30.
        return {'endpoint_wall_s':elapsed,'endpoint_censored':censored,'completion_issue':None}
    except (OSError,ValueError,KeyError,TypeError):
        return {'endpoint_wall_s':None,'endpoint_censored':True,'completion_issue':'missing_or_malformed_completion'}


class MonitorError(RuntimeError):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__(json.dumps(diagnostic,sort_keys=True))


def monitor_diagnostic(exc, *, context=None, command=None, deadline=None, timeout=None):
    if isinstance(exc,MonitorError):
        return deepcopy(exc.diagnostic)
    return {'error_type':type(exc).__name__,'error':str(exc),'context':context,
            'command':getattr(exc,'cmd',command),'timeout_s':getattr(exc,'timeout',timeout),
            'sample_deadline':deadline}


def monitor_command(command, deadline, context):
    global _monitor_child_cpu_s
    remaining = deadline-time.monotonic()
    children0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        if remaining<=0:
            raise TimeoutError('Shared monitor sample deadline exhausted')
        result = subprocess.run(command,capture_output=True,text=True,check=True,timeout=remaining)
        if time.monotonic()>deadline:
            raise TimeoutError('Monitor command exceeded shared sample deadline')
        return result.stdout
    except Exception as exc:
        raise MonitorError(monitor_diagnostic(exc,context=context,command=command,
                           deadline=deadline,timeout=max(0.,remaining))) from exc
    finally:
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        _monitor_child_cpu_s += max(0.,children.ru_utime+children.ru_stime-
                                   children0.ru_utime-children0.ru_stime)


def snapshot(deadline=None):
    deadline = time.monotonic()+.24 if deadline is None else deadline
    raw = monitor_command(['ps','-axo','pid=,ppid=,pgid=,rss=,time='],deadline,'process_snapshot')
    table = {}
    for line in raw.splitlines():
        pid, parent, group, rss, cpu = line.split()
        table[int(pid)] = {'ppid':int(parent),'pgid':int(group),'rss':int(rss)*1024,'cpu':campaign.seconds(cpu)}
    if os.getpid() not in table:
        raise RuntimeError('Incomplete process monitor snapshot')
    return table


def memory_state(deadline=None):
    deadline = time.monotonic()+.24 if deadline is None else deadline
    if platform.system() == 'Darwin':
        raw = monitor_command(['/usr/bin/memory_pressure','-Q'],deadline,'memory_pressure')
        match = re.search(r'System-wide memory free percentage:\s*(\d+)%',raw)
        if not match:
            raise RuntimeError('Unparseable memory pressure monitor')
        return float(match.group(1))
    values = {key:int(value.split()[0]) for key,value in
              (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
    return 100.*values['MemAvailable']/values['MemTotal']


def monitor_sample(deadline, include_memory=True):
    table = snapshot(deadline)
    free = memory_state(deadline) if include_memory else None
    if time.monotonic()>deadline:
        raise MonitorError(monitor_diagnostic(TimeoutError('Complete monitor sample exceeded deadline'),
                           context='complete_sample',deadline=deadline))
    return table,free


def monitor_deadline(tick, last_completed=None, outer_deadline=math.inf):
    return min(tick+.24,outer_deadline,
               last_completed+.25 if last_completed is not None else math.inf)


def group_probe(pgid):
    try:
        os.killpg(pgid,0)
        return {'pgid':pgid,'state':'present'}
    except ProcessLookupError:
        return {'pgid':pgid,'state':'absent'}
    except PermissionError as exc:
        return {'pgid':pgid,'state':'unknown','error_type':type(exc).__name__,
                'errno':exc.errno,'error':str(exc)}


def group_absent(pgid):
    return group_probe(pgid)['state']=='absent'


def stop_owned(proc, groups=(), deadline=None):
    owned = set(groups)|{proc.pid}
    diagnostics,errors = [],[]
    deadline = time.monotonic()+1.5 if deadline is None else deadline
    if not finite(deadline,-math.inf):
        raise ValueError('Owned cleanup requires a finite absolute deadline')

    def send(signum, states=None):
        for pgid in sorted(owned):
            if states is not None and states[pgid]['state']=='absent':
                continue
            try:
                os.killpg(pgid,signum)
            except ProcessLookupError:
                pass
            except OSError as exc:
                diagnostics.append({'stage':'signal','pgid':pgid,'signal':int(signum),
                                    'error_type':type(exc).__name__,'error':str(exc)})

    def probe_until(end):
        while True:
            states = {pgid:group_probe(pgid) for pgid in sorted(owned)}
            diagnostics.extend(value for value in states.values() if value['state']=='unknown')
            if all(value['state']=='absent' for value in states.values()) or time.monotonic()>=end:
                return states
            time.sleep(min(.02,max(0.,end-time.monotonic())))

    send(signal.SIGTERM)
    states = probe_until(min(time.monotonic()+.5,deadline))
    send(signal.SIGKILL,states)
    try:
        proc.wait(timeout=max(0.,min(.5,deadline-time.monotonic())))
    except Exception as exc:
        errors.append({'stage':'reap','error_type':type(exc).__name__,'error':str(exc)})
    states = probe_until(min(time.monotonic()+.5,deadline))
    absent = all(value['state']=='absent' for value in states.values())
    if not absent:
        errors.append({'stage':'absence_confirmation','error':'Owned group absence unresolved',
                       'group_states':list(states.values())})
    return {'pgid':proc.pid,'owned_pgids':sorted(owned),'group_absent':absent,
            'returncode':proc.returncode,'probe_diagnostics':diagnostics,'cleanup_errors':errors,
            'group_states':list(states.values()),'cleanup_deadline':deadline}


def resource_step(item, table, free_percent, now):
    """Pure state update for deterministic monitor/pressure tests."""
    if not finite(free_percent) or free_percent>100:
        raise ValueError('Invalid resource monitor value')
    sample_gap = item.get('last_sample') is not None and now-item['last_sample']>.25
    item['last_sample'] = now
    descendants = {item['proc'].pid}
    while True:
        expanded = descendants | {pid for pid,row in table.items() if row['ppid'] in descendants}
        if expanded == descendants:
            break
        descendants = expanded
    # Keep every observed owned descendant even if its session leader later exits.
    item['owned_pids'].update(descendants)
    groups = {row['pgid'] for pid,row in table.items() if pid in item['owned_pids']}
    item['owned_pgids'].update(groups)
    if groups-{item['proc'].pid}:
        return 'unexpected_descendant_process_group'
    rows = [row for pid,row in table.items() if pid in item['owned_pids']]
    rss, cpu = sum(row['rss'] for row in rows), sum(row['cpu'] for row in rows)
    item['peak_rss'] = max(item['peak_rss'],rss)
    item['cpu'] = max(item['cpu'],cpu)
    item['pressure_since'] = (now if item['pressure_since'] is None else item['pressure_since']) if free_percent<10 else None
    if sample_gap:
        return 'monitor_sampling_gap'
    if rss>RSS_LIMIT:
        return 'worker_rss_limit'
    if item['pressure_since'] is not None and now-item['pressure_since']>=5.:
        return 'system_memory_pressure'
    return None


def resume_state(output, lock, locksha):
    output = Path(output)
    events = ledger_events(output/'ledger.jsonl')
    if (not events or events[0].get('event')!='carry_forward'
            or events[0].get('charged_cpu_s')!=lock['carried_charge_s']
            or events[0].get('freeze_charge_s')!=lock['freeze_charge_s']
            or sum(value['event']=='carry_forward' for value in events)!=1):
        raise ValueError('Missing/corrupt cumulative carry-forward ledger')
    if any(value.get('event') in ('terminal_audit_error','incomplete_terminal_audit') for value in events):
        raise ValueError('Terminal audit failure blocks resume/analyze pending audited reconciliation')
    completed, total = {}, lock['carried_charge_s']+lock['freeze_charge_s']
    finishes = {value['task_id']:value for value in events if value['event']=='finish'}
    expected = {task['id']:task for task in lock['tasks']}
    for folder in (path for path in output.iterdir() if path.is_dir()):
        if folder.name not in expected:
            raise ValueError('Unknown attempt directory blocks resume')
        attempt, receipt = read(folder/'attempt.json'), read(folder/'supervisor.json')
        task = expected[folder.name]
        if (attempt['task']!=task or attempt['lock_sha256']!=locksha or receipt['task']!=task
                or receipt['lock_sha256']!=locksha or receipt.get('terminal') is not True
                or receipt.get('parent_monotonic')!=attempt['parent_monotonic']
                or not finite(receipt.get('charged_cpu_s')) or receipt.get('group_absent') is not True
                or not isinstance(receipt.get('returncode'),int)
                or folder.name not in finishes or finishes[folder.name]['receipt_sha256']!=sha(folder/'supervisor.json')):
            raise ValueError('Incomplete/corrupt prior attempt blocks resume; audited reconciliation required')
        verify_hashes({str(folder/name):value for name,value in receipt['artifacts'].items()})
        total += receipt['charged_cpu_s']
        completed[folder.name] = receipt
    if set(finishes) != set(completed) or len(finishes)!=sum(value['event']=='finish' for value in events):
        raise ValueError('Ledger/receipt task inventory mismatch')
    for value in events:
        if value['event']=='supervisor_cpu':
            if not finite(value.get('charged_cpu_s')):
                raise ValueError('Invalid prior supervisor CPU charge')
            total += value['charged_cpu_s']
    launches = [value['task_id'] for value in events if value['event']=='launch']
    if len(launches)!=len(set(launches)) or set(launches)!=set(completed):
        raise ValueError('Launch/terminal inventory mismatch; never repeat incomplete work')
    return completed, total


def launch(args, task, output, locksha):
    ack_read = ack_write = stdout = stderr = None
    mask = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGINT})
    try:
        folder = Path(output)/task['id']
        folder.mkdir()
        stdout, stderr = (folder/'stdout.log').open('x'), (folder/'stderr.log').open('x')
        ack_read, ack_write = os.pipe()
        os.set_blocking(ack_read,False)
        os.set_blocking(ack_write,False)
        anchor = time.monotonic()
        write_new(folder/'attempt.json',{'policy':POLICY,'task':task,'lock_sha256':locksha,
                                        'parent_monotonic':anchor,'deadline':anchor+30.})
        append_ledger(Path(output)/'ledger.jsonl',{'event':'launch','task_id':task['id'],'parent_monotonic':anchor})
        command = [sys.executable,'-m','experiments.recovery_qualification','worker','--lock',
                   str(Path(args.lock).resolve()),'--output',str(folder.resolve()),'--parent-pid',str(os.getpid()),
                   '--ack-fd',str(ack_write)]
        try:
            proc = subprocess.Popen(command,env={**os.environ,**{key:'1' for key in THREAD_KEYS}},
                                    stdout=stdout,stderr=stderr,start_new_session=True,pass_fds=(ack_write,))
        except BaseException as exc:
            os.close(ack_read)
            receipt = {'policy':POLICY,'terminal':True,'task':task,'lock_sha256':locksha,
                       'parent_monotonic':anchor,'charged_cpu_s':max(0.,time.monotonic()-anchor),
                       'sampled_tree_cpu_s':0.,'peak_tree_rss_bytes':0.,'returncode':-1,
                       'failure':'launch_failed:'+type(exc).__name__,'group_absent':True,
                       'worker_failure':True,'endpoint_wall_s':None,'endpoint_censored':True,
                       'completion_issue':'missing_or_malformed_completion',
                       'artifacts':{path.name:sha(path) for path in folder.iterdir() if path.is_file()}}
            write_new(folder/'supervisor.json',receipt)
            append_ledger(Path(output)/'ledger.jsonl',{'event':'finish','task_id':task['id'],
                         'receipt_sha256':sha(folder/'supervisor.json'),'charged_cpu_s':receipt['charged_cpu_s']})
            raise
        finally:
            os.close(ack_write)
            stdout.close()
            stderr.close()
        item = {'proc':proc,'folder':folder,'task':task,'anchor':anchor,'cpu':0.,'peak_rss':0,
                'owned_pids':{proc.pid},'last_sample':None,'pressure_since':None,'completion_observed':None}
        item.update(ack_fd=ack_read,ack_bytes=b'',acknowledgment=None)
        item['owned_pgids'] = {proc.pid}
        args.active = item  # Publish ownership before signals are unblocked.
        return item
    finally:
        for stream in (stdout,stderr):
            if stream is not None:
                stream.close()
        for fd in (ack_read,ack_write):
            owned_read = (getattr(args,'active',None) or {}).get('ack_fd')
            if fd is not None and fd!=owned_read:
                try:
                    os.close(fd)
                except OSError:
                    pass
        signal.pthread_sigmask(signal.SIG_SETMASK,mask)


def receive_ack(item):
    """Bounded nonblocking read; exactly one atomic JSON acknowledgment is allowed."""
    try:
        chunk = os.read(item['ack_fd'],4097)
    except BlockingIOError:
        return
    item['ack_bytes'] += chunk
    if len(item['ack_bytes'])>4096:
        raise ValueError('Oversized completion acknowledgment')
    if b'\n' in item['ack_bytes']:
        if item['ack_bytes'].count(b'\n')!=1 or not item['ack_bytes'].endswith(b'\n'):
            raise ValueError('Multiple/malformed completion acknowledgments')
        item['acknowledgment'] = json.loads(item['ack_bytes'])


def preserve_stop(item, reason, diagnostic=None):
    if reason and not item.get('primary_reason'):
        item['primary_reason'] = reason
    if diagnostic is not None and not item.get('monitor_failure'):
        item['monitor_failure'] = deepcopy(diagnostic)


def write_once_equal(path, value):
    if Path(path).exists():
        if read(path)!=value:
            raise ValueError('Existing terminal artifact differs: '+str(path))
    else:
        write_new(path,value)


def finish(item, locksha, output, reason):
    """One owned-group cleanup, one acknowledgment close, resumable terminal audit."""
    proc, folder, task = item['proc'], item['folder'], item['task']
    secondary = item.setdefault('secondary_errors',[])
    if not item.get('primary_reason') and (folder/'STOP').exists():
        stop = read(folder/'STOP')
        preserve_stop(item,stop.get('reason'),stop.get('monitor_failure'))
    preserve_stop(item,reason)
    item.setdefault('cleanup_started',time.monotonic())
    try:
        path = folder/'supervisor.json'
        if path.exists():
            receipt = read(path)
            if (receipt.get('task')!=task or receipt.get('lock_sha256')!=locksha
                    or receipt.get('parent_monotonic')!=item['anchor']):
                raise ValueError('Existing terminal receipt identity mismatch')
            item['retired'] = receipt['group_absent']
        else:
            if 'termination' not in item:
                try:
                    item['termination'] = stop_owned(proc,item['owned_pgids'],item['anchor']+OUTER_ALLOCATION)
                except Exception as exc:
                    item['termination'] = {'owned_pgids':sorted(item['owned_pgids']),
                        'group_absent':False,'cleanup_errors':[{'stage':'cleanup',
                        'error_type':type(exc).__name__,'error':str(exc)}]}
                secondary.extend(deepcopy(item['termination'].get('cleanup_errors',[])))
            termination = item['termination']
            item['retired'] = termination['group_absent']
            if termination.get('cleanup_errors'):
                preserve_stop(item,'owned_cleanup_error')
            if not item.get('ack_closed'):
                try:
                    if item.get('ack_fd') is not None:
                        receive_ack(item)
                except (OSError,ValueError,TypeError) as exc:
                    secondary.append({'stage':'completion_ack','error_type':type(exc).__name__,'error':str(exc)})
                    preserve_stop(item,'completion_ack_failure:'+type(exc).__name__)
                finally:
                    fd = item.get('ack_fd')
                    item['ack_fd'],item['ack_closed'] = None,True
                    if fd is not None:
                        try:
                            os.close(fd)
                        except OSError as exc:
                            secondary.append({'stage':'ack_close','error_type':type(exc).__name__,'error':str(exc)})
            elapsed = time.monotonic()-item['anchor']
            try:
                result = read(folder/'result.json')
                if not isinstance(result,dict):
                    raise ValueError('Worker result must be a mapping')
            except (OSError,ValueError,TypeError):
                result = {}
                preserve_stop(item,'missing_or_malformed_worker_result')
            endpoint = completion_endpoint(folder,task,locksha,item['anchor'],
                                           acknowledgment=item.get('acknowledgment'))
            if not termination['group_absent']:
                preserve_stop(item,'owned_group_survived_cleanup')
            charge = max(elapsed,item['cpu'],result.get('cpu_s',0.) if finite(result.get('cpu_s')) else elapsed)
            submissions = (result.get('native_state') or {}).get('submissions',[])
            evidence = start_evidence((folder/'stdout.log').read_bytes(),submissions)
            write_once_equal(folder/'start-evidence.json',evidence)
            artifacts = {value.name:sha(value) for value in folder.iterdir()
                         if value.is_file() and value.name!='supervisor.json'}
            receipt = {'policy':POLICY,'terminal':True,'task':task,'lock_sha256':locksha,
                'parent_monotonic':item['anchor'],'charged_cpu_s':charge,'sampled_tree_cpu_s':item['cpu'],
                'peak_tree_rss_bytes':item['peak_rss'],'failure':item.get('primary_reason'),
                'monitor_failure':item.get('monitor_failure'),'secondary_errors':deepcopy(secondary),
                'returncode':proc.returncode,'group_absent':termination['group_absent'],
                'artifacts':artifacts,**endpoint,'owned_pgids':termination['owned_pgids'],
                'cleanup_probe_diagnostics':termination.get('probe_diagnostics',[]),
                'completion_acknowledgment':item.get('acknowledgment'),
                'cleanup_wall_s':time.monotonic()-item['cleanup_started'],'allocation_elapsed_s':elapsed,
                'worker_failure':bool(result.get('failures')) or result.get('status') in
                    ('worker_failure','storage_failed','model_replay_contradiction','bound_replay_contradiction')
                    or bool((result.get('native_state') or {}).get('engineering_events'))}
            write_once_equal(path,receipt)
        ledger = Path(output)/'ledger.jsonl'
        events = ledger_events(ledger)
        existing = [value for value in events if value['event']=='finish' and value['task_id']==task['id']]
        expected = {'event':'finish','task_id':task['id'],'receipt_sha256':sha(path),
                    'charged_cpu_s':receipt['charged_cpu_s']}
        if existing:
            if len(existing)!=1 or any(existing[0].get(key)!=value for key,value in expected.items()):
                raise ValueError('Existing terminal ledger record differs')
        else:
            append_ledger(ledger,expected)
        # Failures after a receipt was fsynced cannot rewrite that receipt. Bind
        # their retained diagnostics in the append-only audit instead.
        for index,error in enumerate(secondary[len(receipt.get('secondary_errors',[])):],
                                     start=len(receipt.get('secondary_errors',[]))):
            if not any(value.get('event')=='terminal_audit_error' and value.get('task_id')==task['id']
                       and value.get('error_index')==index for value in ledger_events(ledger)):
                append_ledger(ledger,{'event':'terminal_audit_error','task_id':task['id'],
                                     'error_index':index,'error':error,'receipt_sha256':sha(path)})
        item['terminalized'] = True
        return receipt
    except Exception as exc:
        secondary.append({'stage':'terminal_audit','error_type':type(exc).__name__,'error':str(exc)})
        raise


def run(args):
    global _monitor_child_cpu_s
    _monitor_child_cpu_s = 0.
    cpu0 = time.process_time()
    lock, locksha = read(args.lock), sha(args.lock)
    verify_lock(lock)
    budget_lock = freeze_accounting(lock,args.lock,args.freeze_receipt)
    output = Path(args.output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    owner = output/'.supervisor-owner'
    write_new(owner,{'pid':os.getpid(),'lock_sha256':locksha})
    old = {sig:signal.signal(sig,campaign.signal_stop) for sig in (signal.SIGTERM,signal.SIGINT)}
    args.active = None
    halt = None
    try:
        binding = {'policy':POLICY,'lock_sha256':locksha,'mock':False,
                   'freeze_receipt':str(Path(args.freeze_receipt).resolve()),
                   'freeze_receipt_sha256':sha(args.freeze_receipt)}
        if (output/'campaign.json').exists():
            if read(output/'campaign.json') != binding:
                raise ValueError('Output namespace/lock mismatch')
        else:
            write_new(output/'campaign.json',binding)
            append_ledger(output/'ledger.jsonl',{'event':'carry_forward','charged_cpu_s':lock['carried_charge_s'],
                                               'freeze_charge_s':budget_lock['freeze_charge_s']})
        completed, spent = resume_state(output,budget_lock,locksha)
        if any(row['failure'] or row['returncode'] or row['worker_failure'] or row['endpoint_censored']
               for row in completed.values()):
            halt = 'completed_failure_stops_dispatch'
        for task in lock['tasks']:
            if task['id'] in completed:
                continue
            if halt:
                break
            current = spent+time.process_time()-cpu0+_monitor_child_cpu_s
            if current+OUTER_ALLOCATION>DISPATCH_STOP or current+OUTER_ALLOCATION+SHUTDOWN_RESERVE>CEILING:
                halt = 'cumulative_dispatch_budget'
                break
            # Monitoring must be healthy before creating an attempt/owned worker.
            _,free = monitor_sample(time.monotonic()+.24)
            if not finite(free) or free>100:
                raise ValueError('Invalid predispatch memory monitor')
            if free<10:
                halt = 'low_memory_before_dispatch'
                break
            item = launch(args,task,output,locksha)
            reason, last_pressure, free = None, 0., 100.
            while item['proc'].poll() is None and reason is None:
                tick = time.monotonic()
                if tick>=item['anchor']+SUPERVISOR_STOP_S:
                    reason = 'outer_wall_deadline'
                    preserve_stop(item,reason)
                    write_once_equal(item['folder']/'STOP',{'reason':item['primary_reason'],
                                     'monitor_failure':item.get('monitor_failure')})
                    break
                sample_end = monitor_deadline(tick,item['last_sample'],item['anchor']+SUPERVISOR_STOP_S)
                try:
                    table,pressure = monitor_sample(sample_end,include_memory=tick-last_pressure>=1.)
                    receive_ack(item)
                    if pressure is not None:
                        free,last_pressure = pressure,tick
                    reason = resource_step(item,table,free,time.monotonic())
                    campaign.append(item['folder']/'resources.jsonl',{'monotonic':time.monotonic(),
                                    'rss_bytes':item['peak_rss'],'tree_cpu_s':item['cpu'],'free_percent':free,
                                    'sample_deadline':sample_end})
                    marker = item['folder']/'completion.json'
                    if marker.exists() and item['completion_observed'] is None:
                        item['completion_observed'] = time.monotonic()
                    if time.monotonic()-item['anchor']>=SUPERVISOR_STOP_S:
                        reason = reason or 'outer_wall_deadline'
                    if spent+item['cpu']+time.process_time()-cpu0+_monitor_child_cpu_s>=CEILING:
                        reason = 'cumulative_hard_cpu_limit'
                except Exception as exc:
                    diagnostic = monitor_diagnostic(exc,context='worker_sample',deadline=sample_end)
                    reason = 'monitor_failure:'+diagnostic['error_type']
                    preserve_stop(item,reason,diagnostic)
                if reason:
                    preserve_stop(item,reason)
                    write_once_equal(item['folder']/'STOP',{'reason':item['primary_reason'],
                                     'monitor_failure':item.get('monitor_failure')})
                    break
                time.sleep(max(0.,MONITOR_INTERVAL_S-(time.monotonic()-tick)))
            # A fast worker can finish between monitor ticks: use its actual file
            # mtime in this supervisor's monotonic observation interval only if
            # completion was observed while it was alive; otherwise conservative censor.
            if item['completion_observed'] is None and (item['folder']/'completion.json').exists():
                item['completion_observed'] = time.monotonic()
            receipt = finish(item,locksha,output,reason)
            if receipt['group_absent']:
                args.active = None
            spent += receipt['charged_cpu_s']
            if (receipt['failure'] or receipt['returncode'] or receipt['worker_failure']
                    or receipt['endpoint_censored']):
                halt = 'attempt_failure_stops_dispatch'
        return {'halted':halt,'planned':8,'attempted':len(list(output.glob('*/attempt.json')))}
    finally:
        # Mask cancellation while retiring every owned descendant and materializing
        # its terminal accounting; the owner file remains if that audit fails.
        for sig in old:
            signal.signal(sig,signal.SIG_IGN)
        success = False
        try:
            try:
                if args.active is not None:
                    exc = sys.exc_info()[1]
                    fallback = ('supervisor_interrupted' if isinstance(exc,(KeyboardInterrupt,campaign.SupervisorStop))
                                else 'terminal_audit_failure:'+type(exc).__name__ if exc is not None
                                else 'supervisor_shutdown')
                    receipt = finish(args.active,locksha,output,fallback)
                    if receipt['group_absent']:
                        args.active = None
            finally:
                if args.active is not None and not args.active.get('terminalized'):
                    active = args.active
                    append_ledger(output/'ledger.jsonl',{'event':'incomplete_terminal_audit',
                        'task_id':active['task']['id'],'primary_reason':active.get('primary_reason'),
                        'monitor_failure':active.get('monitor_failure'),
                        'secondary_errors':active.get('secondary_errors',[]),
                        'group_absent':active.get('retired',False),
                        'provisional_worker_charge_s':max(time.monotonic()-active['anchor'],active['cpu'])})
                supervisor_cpu = time.process_time()-cpu0
                append_ledger(output/'ledger.jsonl',{'event':'supervisor_cpu',
                    'process_cpu_s':supervisor_cpu,'monitor_child_cpu_s':_monitor_child_cpu_s,
                    'charged_cpu_s':supervisor_cpu+_monitor_child_cpu_s})
            success = args.active is None
        finally:
            if success:
                owner.unlink()
            for sig,handler in old.items():
                signal.signal(sig,handler)


def _analyze(args):
    before = time.process_time()
    lock, locksha, output = read(args.lock), sha(args.lock), Path(args.output).resolve()
    verify_lock(lock)
    binding = read(output/'campaign.json')
    if binding.get('lock_sha256')!=locksha or binding.get('freeze_receipt_sha256')!=sha(binding['freeze_receipt']):
        raise ValueError('Freeze/run output binding changed')
    budget_lock = freeze_accounting(lock,args.lock,binding['freeze_receipt'])
    completed, total = resume_state(output,budget_lock,locksha)
    rows, unresolved = [], []
    counts = {'submitted':0,'accepted':0,'rejected':0,'unknown':0,'native_processing':0,
              'fallback':0,'fault_exercised':0,'terminal':len(completed),'planned':8,
              'invalid_witnesses':0,'mapping_violations':0,'bound_scope_violations':0,'censored':0}
    for task in lock['tasks']:
        if task['id'] not in completed:
            unresolved.append('undispatched:'+task['id'])
            continue
        folder = output/task['id']
        receipt = completed[task['id']]
        result = read(folder/'result.json') if (folder/'result.json').exists() else {}
        evidence = (read(folder/'start-evidence.json') if (folder/'start-evidence.json').exists()
                    else {'submitted':0,'classified':[],'unattributed_log_matches':[]})
        counts['submitted'] += evidence['submitted']
        for item in evidence['classified']:
            counts[item['status']] += 1
            counts['native_processing'] += int(item['processed'])
        fallback, selected = result.get('fallback'),result.get('selected')
        state = result.get('native_state') or {}
        counts['fallback'] += int(fallback is not None)
        counts['fault_exercised'] += int(state.get('fault_exercised') is True and fallback is not None)
        issues = []
        if receipt['failure'] or receipt['returncode'] or receipt['worker_failure']:
            issues.append('engineering_failure')
        if receipt['endpoint_censored'] or receipt['completion_issue']:
            issues.append('censored_endpoint')
            counts['censored'] += 1
        if receipt['peak_tree_rss_bytes']>RSS_LIMIT:
            issues.append('rss_limit')
        if any(item['scope']!='full_unrestricted_mip' for item in result.get('bound_provenance',[])):
            issues.append('bound_scope')
            counts['bound_scope_violations'] += 1
        if task['arm']=='static' and result.get('global_lower_bound') is not None:
            issues.append('restricted_bound_promoted')
            counts['bound_scope_violations'] += 1
        frozen = next(value for value in lock['cases'] if value['base_id']==task['base_id'])
        payload = read(frozen['fixture'])
        case = restore_case(payload['case'])
        from egglab import recovery_coordinator as rc
        for kind,witness in (('fallback',fallback),('selected',selected)):
            if witness is None:
                continue
            try:
                checked = rc.lift_plan(case,case,witness['plan'],a=payload['a'],b=payload['b'])
                if (checked['true_bill_exact']!=witness['true_bill_exact']
                        or checked['true_bill']!=witness['true_bill']):
                    raise ValueError('Saved witness bill differs from independent exact replay')
            except Exception as exc:
                issues.append('invalid_'+kind+':'+type(exc).__name__)
                counts['invalid_witnesses'] += 1
        if selected is not None and result.get('global_lower_bound') is not None:
            bound = result['global_lower_bound']
            if not finite(bound,-math.inf) or bound>selected['true_bill']+rc.pf.BOUND_GUARD:
                issues.append('invalid_global_bound')
                counts['bound_scope_violations'] += 1
        for submission in state.get('submissions',[]):
            inventory = submission.get('inventory',[])
            if (stable(inventory)!=submission.get('inventory_sha256')
                    or [value.get('movement_id') for value in inventory]!=frozen['movement_ids']
                    or len({value.get('variable_index') for value in inventory})!=len(inventory)
                    or any(value.get('value') not in (0,1) for value in inventory)
                    or submission.get('continuous_submitted')!=0
                    or submission.get('bounds_constraints_unchanged') is not True):
                issues.append('native_start_mapping_violation')
                counts['mapping_violations'] += 1
        unresolved.extend(task['id']+':'+issue for issue in issues)
        rows.append({'task':task,'issues':issues,'endpoint_wall_s':receipt['endpoint_wall_s'],
                     'censored':receipt['endpoint_censored'],'charged_cpu_s':receipt['charged_cpu_s'],
                     'rss_bytes':receipt['peak_tree_rss_bytes'],
                     'prefix_bill_exact':None if fallback is None else fallback.get('provenance',{}).get(
                         'source_replay_bill_at_target_market_exact'),
                     'fallback_bill_exact':None if fallback is None else fallback['true_bill_exact'],
                     'final_bill_exact':None if selected is None else selected['true_bill_exact'],
                     'selected_witness_sha256':None if selected is None else stable(selected['plan']),
                     'bound_provenance':result.get('bound_provenance',[]),'native':evidence})
    normal_processed = any(row['task']['arm']=='recovery' and row['fallback_bill_exact'] is not None
                           and any(item['processed'] for item in row['native']['classified']) for row in rows)
    if not normal_processed:
        unresolved.append('normal_recovery_native_partial_start_processing_unobserved')
    if not counts['fault_exercised']:
        unresolved.append('durable_fallback_start_fault_path_unexercised')
    charge = time.process_time()-before
    if total+charge>CEILING:
        unresolved.append('cumulative_hard_ceiling_exceeded')
    report = {'policy':POLICY,'passed':not unresolved,'counts':counts,'rows':rows,
              'unresolved':unresolved,'cumulative_charged_cpu_s':total+charge,
              'hard_ceiling_s':CEILING,'dispatch_stop_s':DISPATCH_STOP,
              'check_evidence':lock['checks'],'claim':'engineering qualification only; no ranking inference'}
    write_new(args.report,report)
    return report


def analyze(args):
    cpu0 = time.process_time()
    output = Path(args.output).resolve()
    owner = output/'.supervisor-owner'
    write_new(owner,{'pid':os.getpid(),'phase':'analyze','lock_sha256':sha(args.lock)})
    success = False
    try:
        return _analyze(args)
    finally:
        try:
            append_ledger(output/'ledger.jsonl',{'event':'supervisor_cpu','phase':'analyze',
                                               'charged_cpu_s':time.process_time()-cpu0})
            success = True
        finally:
            if success:
                owner.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    p = commands.add_parser('freeze')
    for name in ('lock','checks','accounting','reservations','native-library'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--design')
    p.add_argument('--backend',choices=('CBC','GRB'),default='GRB')
    for name in ('run','worker','analyze'):
        p = commands.add_parser(name)
        p.add_argument('--lock',required=True)
        p.add_argument('--output',required=True)
        if name=='worker':
            p.add_argument('--parent-pid',type=int,required=True)
            p.add_argument('--ack-fd',type=int,required=True)
        if name=='run':
            p.add_argument('--freeze-receipt',required=True)
        if name=='analyze':
            p.add_argument('--report',required=True)
    commands.add_parser('self-test')
    args = parser.parse_args()
    if args.command=='self-test':
        # The caller owns this check's allocation/receipt; no unaccounted helper run.
        raise SystemExit(subprocess.call([sys.executable,'-m','pytest','-q',
                                          str(ROOT/'src/tests/test_recovery_qualification.py')]))
    try:
        result = globals()[args.command](args)
    finally:
        if args.command=='worker':
            os.close(args.ack_fd)
    if result is not None:
        print(json.dumps(result,allow_nan=False))


if __name__ == '__main__':
    main()
