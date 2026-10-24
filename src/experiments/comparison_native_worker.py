"""Two-task real60s engineering preflight worker; never dispatch on import.

Separate from qualified30s instrumentation. Parent owns freeze, supervision,
resource accounting and permission to execute; this module creates no cases.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from experiments import recovery_qualification as q
from egglab import classical_controls as cc
from egglab import comparison_coordinator as pipeline
from egglab import constructive_charging as charging
from egglab import constructive_proposal as proposal
from egglab import native_pathflow as pf
from egglab import recovery_coordinator as rc

POLICY = 'comparison-native-preflight-v1'
CAPTURE_SCHEMA = 'comparison60-capture-reference-v1'


def task_matrix():
    tasks = []
    for arm in ('cf1','recovery'):
        value = {'base_id':50999,'trips':80,'arm':arm,'seed':17,'seconds':60.,'fault':None}
        tasks.append({**value,'id':q.stable(value)[:20]})
    return tasks


def _bytes(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def _write_bytes(path, raw):
    path = Path(path)
    with path.open('xb') as stream:
        if stream.write(raw)!=len(raw):
            raise OSError('Incomplete capture write')
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent,os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def persist_capture(folder, metadata, raw_capture):
    """Serialize complete diagnostics once; hash exactly the bytes durably saved."""
    if (metadata.get('phase') not in ('cf1','prefix','full')
            or type(metadata.get('sequence')) is not int or metadata['sequence']<1):
        raise ValueError('Invalid flat capture identity')
    name = f"capture-{metadata['phase']}-{metadata['sequence']:06d}.json"
    payload = {'schema':'comparison60-native-capture-v1',**metadata,
               'capture':rc._diagnostic(raw_capture)}
    raw = _bytes(payload)
    _write_bytes(Path(folder)/name,raw)
    return {'event':'native_incumbent_reference','schema':CAPTURE_SCHEMA,**metadata,
            'path':name,'offset_bytes':0,'length_bytes':len(raw),
            'sha256':hashlib.sha256(raw).hexdigest()}


def verify_capture_reference(folder, lock, task, anchor, reference):
    """Independent immutable reference verification; return scalar scope proof."""
    attempt = q.read(Path(folder)/'attempt.json')
    phase,sequence = reference.get('phase'),reference.get('sequence')
    if phase not in ('cf1','prefix','full') or type(sequence) is not int or sequence<1:
        raise ValueError('Invalid capture phase/sequence')
    frozen = lock['cases'][0]
    expected = {'task_id':task['id'],'task_sha256':q.stable(task),
        'lock_sha256':attempt['lock_sha256'],'attempt_sha256':q.sha(Path(folder)/'attempt.json'),
        'anchor':anchor,'case_identity':frozen['restricted_identity'] if phase=='prefix' else frozen['identity']}
    if (attempt['task']!=task or attempt['parent_monotonic']!=anchor
            or task not in lock['tasks'] or attempt['lock_sha256']!=hashlib.sha256(
                (json.dumps(lock,indent=2,default=str,allow_nan=False)+'\n').encode()).hexdigest()
            or any(reference.get(key)!=value for key,value in expected.items())
            or phase=='cf1' and task['arm']!='cf1'
            or phase=='prefix' and task['arm']!='recovery'):
        raise ValueError('Foreign capture task/lock/phase/case binding')
    name = f'capture-{phase}-{sequence:06d}.json'
    if (reference.get('event')!='native_incumbent_reference' or reference.get('schema')!=CAPTURE_SCHEMA
            or reference.get('path')!=name or reference.get('offset_bytes')!=0
            or type(reference.get('length_bytes')) is not int or reference['length_bytes']<=0
            or type(reference.get('round')) is not int or reference['round']<0):
        raise ValueError('Malformed capture reference')
    for key in ('capture_started_monotonic','capture_finished_monotonic'):
        if not q.finite(reference.get(key),anchor):
            raise ValueError('Nonfinite capture timestamp')
    if reference['capture_finished_monotonic']<reference['capture_started_monotonic']:
        raise ValueError('Capture clock reversed')
    path = Path(folder)/name
    if path.is_symlink():
        raise ValueError('Capture cannot be a symlink')
    raw = path.read_bytes()
    if len(raw)!=reference['length_bytes'] or hashlib.sha256(raw).hexdigest()!=reference.get('sha256'):
        raise ValueError('Capture bytes/hash changed')
    payload = json.loads(raw)
    for key in (*expected,'phase','sequence','round','capture_started_monotonic'):
        if payload.get(key)!=reference[key]:
            raise ValueError('Capture payload binding changed')
    capture = payload.get('capture',{})
    if (payload.get('schema')!='comparison60-native-capture-v1'
            or capture.get('case_identity')!=expected['case_identity']
            or capture.get('formulation')!=pf.FORMULATION or capture.get('native_matrix')!=pf.NATIVE_MATRIX):
        raise ValueError('Capture physical formulation changed')
    variables = capture['variables']
    lookup = {v['index']:v for v in variables}
    mapped = capture['mapping']['movement_selection']
    mapped_set = set(mapped)
    movements = frozen['restricted_movement_ids'] if phase=='prefix' else frozen['movement_ids']
    if (len(lookup)!=len(variables) or len(mapped)!=len(movements) or len(mapped_set)!=len(mapped)
            or capture['mapping']['movement_ids']!=movements
            or any(index not in lookup or lookup[index]['type']!='B' for index in mapped)
            or any(v['type']!='C' for index,v in lookup.items() if index not in mapped_set)):
        raise ValueError('Capture variable mapping changed')
    fixed = all(lookup[index]['lower']['value']==lookup[index]['upper']['value']
                and lookup[index]['lower']['value'] in (0.,1.) for index in mapped)
    if phase=='cf1' and not fixed:
        raise ValueError('CF1 capture is not fixed binary charging')
    return {'phase':phase,'sequence':sequence,'case_identity':expected['case_identity'],
            'all_mapped_binary_fixed':fixed,'all_unmapped_continuous':True,
            'sha256':reference['sha256']}


def audit_captures(folder, state, events, *, lock, task, anchor):
    registered = state['capture_references']
    expected = {reference['sequence']:reference for reference in registered}
    if len(expected)!=len(registered):
        raise ValueError('Duplicate capture sequence')
    canonical = set(registered[0]) if registered else set()
    for event in events:
        if event.get('event')=='native_incumbent':
            raise ValueError('Unpersisted full capture reached finalization')
        if event.get('event')=='native_incumbent_reference':
            reference = expected.get(event.get('sequence'))
            if (reference is None or any(event.get(key)!=reference[key] for key in canonical)
                    or event.get('stage',reference['phase'])!=reference['phase']):
                raise ValueError('Unknown/mismatched forwarded capture reference')
    for reference in registered:
        verify_capture_reference(folder,lock,task,anchor,reference)
    return len(registered)


class IntegerGateClosed60(TimeoutError):
    def __init__(self, token):
        super().__init__('comparison60_integer_gate_closed:'+token)
        self.token = token


@contextmanager
def native_phase(state, phase, deadline):
    previous = state['phase'],state['phase_deadline'],state.get('capture_round',0)
    state['phase'],state['phase_deadline'] = phase,deadline
    state['capture_round'] = 0
    try:
        yield
    finally:
        state['phase'],state['phase_deadline'],state['capture_round'] = previous


def _offset():
    import ctypes
    sys.stdout.flush()
    sys.stderr.flush()
    flush = ctypes.CDLL(None).fflush
    flush.argtypes,flush.restype = [ctypes.c_void_p],ctypes.c_int
    if flush(None)!=0:
        raise OSError('Native C stdio flush failed')
    return os.fstat(1).st_size


def _gate(state):
    return (not state['sink_failure'] and not state['engineering_events']
            and state.get('allowed',lambda:True)() is True)


@contextmanager
def instrument_native60(lock, task, folder, *, anchor, full_case, source_case, clock):
    """Own60s gates, capture-before-extraction and actual binary-only hint evidence."""
    originals = pf.build_feasible_model,pf._attach_pricing_start,pf._optimize_once,pf.capture_incumbent
    build0,attach0,optimize0,capture0 = originals
    schedule = pipeline.Schedule60(anchor,anchor+60.)
    phase = 'cf1' if task['arm']=='cf1' else 'prefix'
    state = {'phase':phase,'phase_deadline':schedule.charging_stage_end if phase=='cf1' else schedule.prefix_search_end,
             'sink_failure':None,'engineering_events':[],'expected_budget_stops':[],
             'submissions':[],'submission':None,'capture_references':[],
             'cf1_fixed_inventories':0,'fault_exercised':False,
             'task':deepcopy(task),'anchor':anchor,
             'case_identities':{'prefix':source_case.identity(),'full':full_case.identity(),'cf1':full_case.identity()}}
    attempt = q.read(Path(folder)/'attempt.json')
    state['lock_sha256'] = attempt['lock_sha256']
    attemptsha = q.sha(Path(folder)/'attempt.json')
    state['attempt_sha256'] = attemptsha

    def emit(event):
        try:
            q.native_append(folder,rc._diagnostic(event))
        except Exception as exc:
            state['sink_failure'] = repr(exc)
            raise

    def build(case,*args,**kwargs):
        phase = state['phase']
        identity = case.identity()
        wanted = source_case.identity() if phase=='prefix' else full_case.identity()
        if identity!=wanted or phase not in ('cf1','prefix','full') or not _gate(state):
            raise ValueError('Native build phase/case/gate mismatch')
        cutoff = state['phase_deadline']
        observed = clock()
        def guard(observed):
            if observed>=cutoff:
                if phase=='cf1':
                    raise TimeoutError('CF1 build after fixed charging window')
                exc = IntegerGateClosed60(os.urandom(16).hex())
                evidence = {'event':'integer_gate_closed60','token':exc.token,'task_id':task['id'],
                    'task_sha256':q.stable(task),'lock_sha256':attempt['lock_sha256'],
                    'attempt_sha256':attemptsha,
                    'case_identity':identity,'phase':phase,'anchor':anchor,'integer_cutoff':cutoff,
                    'integer_upper_cutoff':schedule.prefix_integer_end if phase=='prefix' else schedule.full_integer_end,
                    'observed_monotonic':observed,'guard_point':'before_model_build','native_dispatched':False}
                emit(evidence)
                state['pending_gate'] = {'evidence':evidence,'error':str(exc)}
                raise exc
        guard(observed)
        emit({'event':'native_model60_build','stage':'enter','phase':phase,
              'case_identity':identity,'at':observed,'deadline':cutoff})
        observed = clock()
        guard(observed)
        built = build0(case,*args,**kwargs)
        build_finished = clock()
        if not q.finite(build_finished,observed):
            raise ValueError('Invalid native model build clock')
        emit({'event':'native_model60_build','stage':'return','phase':phase,
              'case_identity':identity,'at':build_finished,'started_monotonic':observed,
              'elapsed_s':build_finished-observed,'deadline':cutoff})
        if clock()>=cutoff:
            raise TimeoutError('Native model build exhausted planned60s stage search')
        runtime = built['backend_runtime']
        if (runtime.get('requested')!='GRB' or runtime.get('model_solver_name') not in ('GRB','GUROBI')
                or runtime.get('solver_module')!='mip.gurobi' or runtime.get('solver_class')!='SolverGurobi'
                or runtime.get('native_library_sha256')!=lock['native_library']['sha256']
                or Path(runtime.get('native_library_path','')).resolve()!=Path(lock['native_library']['path']).resolve()
                or built['physical_identity']!=identity or built['compiled']['identity']!=identity):
            raise ValueError('Native model/backend/library differs from locked identity')
        built['model'].seed,built['model'].threads,built['model'].verbose = 17,1,1
        emit({'event':'native_model60','phase':phase,'case_identity':identity,'runtime':runtime,'seed':17,'threads':1,
              'at':build_finished,'build_started_monotonic':observed,'build_finished_monotonic':build_finished,
              'build_elapsed_s':build_finished-observed,'deadline':cutoff})
        return built

    def attach(case,built,selected):
        if (state['phase']!='full' or case.identity()!=full_case.identity()
                or clock()>=schedule.full_search_end or not _gate(state)
                or not (Path(folder)/'fallback.json').is_file()):
            raise ValueError('Full binary start requires timely durable fallback and full phase')
        variables = list(built['model'].vars)
        indices = [v.idx for v in variables]
        mapped = [v.idx for v in built['x']]
        if (len(indices)!=len(set(indices)) or len(mapped)!=len(case.movements)
                or len(mapped)!=len(set(mapped)) or any(index not in indices for index in mapped)
                or any(str(v.var_type)!='C' for v in variables if v.idx not in set(mapped))):
            raise ValueError('Start model has invalid binary/continuous inventory')
        before = [(v.idx,v.lb,v.ub,str(v.var_type)) for v in variables]
        rows = tuple(charging._row_signature(row) for row in built['model'].constrs)
        mapping = attach0(case,built,selected)
        actual = list(built['model'].start)
        inventory = [{'movement_id':m.id,'variable_index':v.idx,'value':value}
                     for m,v,(submitted,value) in zip(case.movements,built['x'],actual) if submitted is v]
        if (len(actual)!=len(case.movements) or len(inventory)!=len(actual)
                or any(str(v.var_type)!='B' or value not in (0,1) for v,value in actual)
                or [row['value'] for row in inventory]!=[int(m.id in selected) for m in case.movements]
                or before!=[(v.idx,v.lb,v.ub,str(v.var_type)) for v in built['model'].vars]
                or rows!=tuple(charging._row_signature(row) for row in built['model'].constrs)):
            raise ValueError('Actual hint changed mapping, variable bounds/types or physical rows')
        item = {'event':'binary_start_inventory','inventory':inventory,'inventory_sha256':q.stable(inventory),
                'continuous_submitted':0,'continuous_unset':sum(str(v.var_type)=='C' for v in variables),
                'bounds_constraints_unchanged':True,'physical_rows_unchanged':True,'mapping':mapping}
        state['submission'] = item
        emit(item)
        if clock()>=schedule.full_search_end:
            raise TimeoutError('Binary start setup exhausted planned full search')
        return mapping

    def optimize(built,budget,deadline):
        fixed = bool(built['x']) and all(v.lb==v.ub for v in built['x'])
        target = state['phase_deadline'] if state['phase']=='cf1' else (
            schedule.prefix_handoff_end if state['phase']=='prefix' else schedule.full_handoff_end)
        if (not _gate(state) or clock()>=min(deadline,target)
                or state['phase']=='cf1' and not fixed):
            raise TimeoutError('Native60 dispatch gate closed')
        item = state['submission']
        start = _offset()
        try:
            return optimize0(built,budget,deadline)
        finally:
            end = _offset()
            emit({'event':'native_log_span','log_start':start,'log_end':end,'fixed_topology':fixed,
                  'phase':state['phase'],'inventory_sha256':None if item is None else item['inventory_sha256']})
            if item is not None and not fixed:
                state['submissions'].append({**item,'log_start':start,'log_end':end})
            state['submission'] = None

    def capture(case,built):
        # Preserve even late/unadmitted diagnostic captures. No time gate before
        # persistence: caller admission checks still decide physical eligibility.
        try:
            started = clock()
            raw = capture0(case,built)
            metadata = {'task_id':task['id'],'task_sha256':q.stable(task),
                'lock_sha256':attempt['lock_sha256'],'attempt_sha256':attemptsha,
                'anchor':anchor,'phase':state['phase'],'case_identity':case.identity(),
                'sequence':len(state['capture_references'])+1,'round':state.get('capture_round',0),
                'capture_started_monotonic':started}
            reference = persist_capture(folder,metadata,raw)
            reference['capture_finished_monotonic'] = clock()
            state['capture_references'].append(deepcopy(reference))
            emit({'event':'capture_persisted',**reference})
            return reference
        except Exception as exc:
            state['sink_failure'] = repr(exc)
            raise

    state['emit'] = emit
    pf.build_feasible_model,pf._attach_pricing_start,pf._optimize_once,pf.capture_incumbent = build,attach,optimize,capture
    try:
        yield state
    finally:
        pf.build_feasible_model,pf._attach_pricing_start,pf._optimize_once,pf.capture_incumbent = originals
        state.pop('emit',None)
        state.pop('allowed',None)


def record_event(folder,state,event,record=None):
    try:
        if event.get('event') in ('native_status','fixed_topology_solve'):
            index = event.get('round')
            if type(index) is not int or index<0:
                raise ValueError('Invalid native capture round')
            state['capture_round'] = index
        expected = False
        if event.get('event')=='native_search_failed':
            pending = state.pop('pending_gate',None)
            if pending:
                evidence = pending['evidence']
                phase = state['phase']
                anchor = state['anchor']
                cutoff = anchor+(20. if phase=='prefix' else 44.)
                expected = (event.get('stage')=='model_build' and
                    event.get('error_type')==IntegerGateClosed60.__name__ and
                    event.get('error')==pending['error'] and evidence['phase']==state['phase'] and
                    not state['sink_failure'] and phase in ('prefix','full') and
                    evidence.get('task_id')==state['task']['id'] and
                    evidence.get('task_sha256')==q.stable(state['task']) and
                    evidence.get('lock_sha256')==state['lock_sha256'] and
                    evidence.get('attempt_sha256')==state['attempt_sha256'] and
                    evidence.get('case_identity')==state['case_identities'][phase] and
                    evidence.get('anchor')==anchor and evidence.get('integer_cutoff')==cutoff and
                    evidence.get('integer_upper_cutoff')==anchor+(24. if phase=='prefix' else 48.) and
                    q.finite(evidence.get('observed_monotonic'),cutoff) and
                    evidence.get('guard_point')=='before_model_build' and
                    isinstance(evidence.get('token'),str) and len(evidence['token'])==32 and
                    pending['error']=='comparison60_integer_gate_closed:'+evidence['token'] and
                    evidence['native_dispatched'] is False)
                if expected:
                    state['expected_budget_stops'].append(deepcopy(evidence))
        failure = (event.get('event')=='native_search_failed' and not expected or
            event.get('event')=='candidate_rejected' and
            event.get('stage') not in ('raw_admission','completion_admission'))
        if failure:
            state['engineering_events'].append(rc._diagnostic(event))
        if event.get('event')=='native_incumbent':
            raise ValueError('Raw capture bypassed durable capture hook')
        if (event.get('event')=='fixed_topology_inventory' and state['phase']=='cf1'
                and event.get('all_unfixed_continuous') is True):
            state['cf1_fixed_inventories'] += 1
        q.native_append(folder,{'source':'planner',**rc._diagnostic(event)})
        if record:
            record(event)
    except Exception as exc:
        state['sink_failure'] = repr(exc)
        raise


class WorkerClock:
    """Sticky checked supervisor clock; recovering a bad raw clock cannot reopen work."""
    def __init__(self, anchor, raw=time.monotonic):
        self.anchor,self.raw,self.last,self.failure = anchor,raw,None,None

    def __call__(self):
        if self.failure is not None:
            raise ValueError('Worker clock previously failed: '+self.failure)
        try:
            at = self.raw()
            if (not q.finite(at,self.anchor) or self.last is not None and at<self.last):
                raise ValueError('Invalid/nonmonotonic worker clock')
        except Exception as exc:
            self.failure = repr(exc)
            raise ValueError(self.failure) from exc
        self.last = at
        return at


class WorkerStorage(rc.DirectoryStorage):
    """Persist complete60s evidence; ACK only after coordinator terminal checks."""
    def __init__(self, folder, *, task, lock, anchor, state, ack_fd, clock):
        super().__init__(folder)
        self.task,self.lock,self.anchor,self.state = task,lock,anchor,state
        self.ack_fd,self.clock = ack_fd,clock
        self.attempt = q.read(self.directory/'attempt.json')
        self.locksha = self.attempt['lock_sha256']
        self.selection_ledger = None
        self.acked = False

    def _write(self,name,value):
        if name=='completion.json':
            value = {**value,'task':self.task,'lock_sha256':self.locksha,
                     'worker_policy':POLICY}
        return super()._write(name,value)

    def materialize(self,result,*,schedule,clock):
        entered = clock()
        result.setdefault('events',[]).append({'event':'materialization_start60',
            'at':entered,'anchor':self.anchor,'elapsed_s':entered-self.anchor})
        state = self.state
        try:
            count = audit_captures(self.directory,state,result['events'],lock=self.lock,
                                  task=self.task,anchor=self.anchor)
            state['capture_audit'] = {'verified':count,'at':clock()}
        except Exception as exc:
            state['sink_failure'] = repr(exc)
            result.setdefault('failures',[]).append(rc._failure('capture_reference',exc))
        for event in result['events']:
            try:
                q.native_append(self.directory,{'source':'coordinator',**event})
            except Exception as exc:
                state['sink_failure'] = repr(exc)
                result.setdefault('failures',[]).append(rc._failure('native_sink',exc))
                break
        # Only actual attributable native-log matches establish processing.
        try:
            _offset()
            evidence = q.start_evidence((self.directory/'stdout.log').read_bytes(),state['submissions'])
        except Exception as exc:
            evidence = {'submitted':len(state.get('submissions',[])),'classified':[],
                        'unattributed_log_matches':[],'error':repr(exc)}
            state['sink_failure'] = repr(exc)
        state['start_evidence'] = evidence
        acquisition = 'cf1_lift' if self.task['arm']=='cf1' else 'prefix_lift'
        admitted = any(row.get('event')=='durable_fallback_admitted' and row.get('stage')==acquisition
                       for row in result['events'])
        processed = any(row.get('processed') is True for row in evidence['classified'])
        path = {'acquisition':acquisition,'durable_fallback':admitted,
                'replay_valid_fallback':result.get('fallback') is not None,
                'full_start_proposed':(result.get('start_proposal') or {}).get('proposed') is True,
                'binary_submitted':bool(state.get('submissions')),'native_processing_observed':processed,
                'cf1_fixed_inventory':state.get('cf1_fixed_inventories',0)>0}
        path['passed'] = all(path[key] for key in ('durable_fallback','replay_valid_fallback',
            'full_start_proposed','binary_submitted','native_processing_observed')) and (
            self.task['arm']!='cf1' or path['cf1_fixed_inventory'])
        state['path_qualification'] = path
        if not path['passed']:
            failure = {'stage':'preflight_path','error_type':'UnexercisedNativePath',
                       'error':'Required charged/prefix durable fallback and attributable warm full start not exercised'}
            state['engineering_events'].append(failure)
        if state.get('sink_failure'):
            result.setdefault('failures',[]).append({'stage':'native_sink','error':state['sink_failure']})
        for failure in state.get('engineering_events',[]):
            if failure not in result.setdefault('failures',[]):
                result['failures'].append(deepcopy(failure))
        selected = result.get('selected')
        if selected is not None:
            self._write('plan.json',selected['plan'])
            self._write('replay.json',selected['replay'])
        native_state = {key:deepcopy(value) for key,value in state.items() if not callable(value)}
        result.update(task=self.task,lock_sha256=self.locksha,cpu_s=time.process_time(),
            case_identity=self.lock['cases'][0]['identity'],native_state=native_state,
            selection_ledger=self.selection_ledger,worker_policy=POLICY)
        return super().materialize(result,schedule=schedule,clock=clock)

    def finalize(self,outcome):
        if self.acked:
            raise ValueError('Duplicate worker completion ACK')
        result = outcome['result']
        resultsha = q.sha(self.directory/'result.json')
        flat = {'policy':POLICY,'task':self.task,'lock_sha256':self.locksha,
                'result_sha256':resultsha,'status':result['status'],
                'censored':bool(outcome.get('censored',True)),
                'materialization_failure':outcome.get('materialization_failure'),
                'clock_failure':result.get('clock_failure'),
                'failures':result.get('failures',[])}
        self._write('worker-outcome.json',rc._diagnostic(flat))
        # Timestamp after both immutable completion and terminal outcome fsyncs.
        endpoint = self.clock()
        marker = q.read(self.directory/'completion.json')
        if marker['result_sha256']!=resultsha:
            raise ValueError('Completion/result changed before ACK')
        ack = {'task_id':self.task['id'],'lock_sha256':self.locksha,
               'parent_monotonic':self.anchor,'completion_monotonic':endpoint,
               'completion_sha256':q.sha(self.directory/'completion.json'),'result_sha256':resultsha,
               'worker_outcome_sha256':q.sha(self.directory/'worker-outcome.json'),
               'worker_status':flat['status'],'worker_censored':flat['censored']}
        raw = _bytes(ack)
        if len(raw)>=4096 or os.write(self.ack_fd,raw)!=len(raw):
            raise OSError('Atomic completion acknowledgment failed')
        self.acked = True
        return ack


def launch_watchdog(folder,parent_pid):
    watcher = subprocess.Popen([sys.executable,'-m','experiments.codex_local_campaign','watch-parent',
        '--parent-pid',str(parent_pid),'--worker-pid',str(os.getpid()),'--output',str(folder)],
        preexec_fn=lambda:signal.signal(signal.SIGTERM,signal.SIG_IGN))
    # No new session: watcher and worker stay in the supervisor-owned PGID.
    q.write_new(Path(folder)/'owned-processes.json',{'worker_pid':os.getpid(),
        'watchdog_pid':watcher.pid,'owned_pgids':[os.getpgrp()],
        'watchdog_contract':'codex_local_campaign.watch_parent; inherited PGID'})
    return watcher


def worker(args):
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGINT})
    folder = Path(args.output).resolve()
    attempt,lock = q.read(folder/'attempt.json'),q.read(args.lock)
    task,anchor = attempt['task'],attempt['parent_monotonic']
    if (not q.finite(anchor) or attempt['lock_sha256']!=q.sha(args.lock)
            or task not in task_matrix() or task not in lock['tasks']
            or attempt.get('deadline')!=anchor+60.):
        raise ValueError('Worker60 attempt/task/deadline/lock mismatch')
    clock = WorkerClock(anchor)
    clock()
    launch_watchdog(folder,args.parent_pid)
    state = {'capture_references':[],'submissions':[],'engineering_events':[],
             'sink_failure':None,'cf1_fixed_inventories':0}
    storage = WorkerStorage(folder,task=task,lock=lock,anchor=anchor,state=state,
                            ack_fd=args.ack_fd,clock=clock)
    try:
        from experiments.comparison_native_preflight import verify_lock
        verify_lock(lock,worker=True)
        clock()
        frozen = lock['cases'][0]
        payload = q.read(frozen['fixture'])
        case = q.restore_case(payload['case'])
        from experiments.codex_offline_rank import heuristic
        source,selection = cc.restrict_case(case,heuristic(case))
        clock()
        if (case.identity()!=frozen['identity'] or [m.id for m in case.movements]!=frozen['movement_ids']
                or source.identity()!=frozen['restricted_identity']
                or [m.id for m in source.movements]!=frozen['restricted_movement_ids']
                or q.stable({'a':payload['a'],'b':payload['b']})!=frozen['market_sha256']
                or selection['policy']!=frozen['selection_policy']):
            raise ValueError('Frozen fixture/market/selector identity or movement order changed')
        storage.selection_ledger = selection
        budget = pf.Budget(backend='GRB',threads=1,phase_seconds=44.,wall_seconds=60.,max_rounds=8)
        schedule = pipeline.Schedule60(anchor,anchor+60.)
        with instrument_native60(lock,task,folder,anchor=anchor,full_case=case,source_case=source,clock=clock) as native:
            storage.state = state = native

            def allowed():
                return (clock.failure is None and os.getppid()==args.parent_pid
                        and not (folder.parent/'STOP').exists() and not state['sink_failure']
                        and not state['engineering_events'])

            state['allowed'] = allowed

            def planner(current,*a,record=None,**kw):
                identity = current.identity()
                phase = 'prefix' if identity==source.identity() else 'full' if identity==case.identity() else None
                if phase is None:
                    raise ValueError('Unknown60 planner physical case')
                end = schedule.prefix_search_end if phase=='prefix' else schedule.full_search_end
                with native_phase(state,phase,end):
                    return pf.solve_planner(current,*a,record=lambda event:record_event(folder,state,event,record),**kw)

            def completer(*a,deadline,record=None,**kw):
                with native_phase(state,'cf1',deadline):
                    return charging.complete_topology(*a,deadline=deadline,
                        record=lambda event:record_event(folder,state,event,record),**kw)

            def provider(*a,**kw):
                return proposal.propose(*a,completer=completer,**kw)

            outcome = pipeline.coordinate60(source,case,payload['a'],payload['b'],arm=task['arm'],
                parent_monotonic=anchor,deadline=anchor+60.,storage=storage,budget=budget,
                planner=planner,proposal_provider=provider,clock=clock,allowed=allowed)
            storage.finalize(outcome)
            return outcome
    except Exception as exc:
        failure = rc._failure('worker',exc)
        if not (folder/'result.json').exists() and clock.failure is None:
            result = {'policy':pipeline.POLICY,'status':'worker_failure','selected':None,'fallback':None,
                      'global_lower_bound':None,'bound_provenance':[],'events':[],'failures':[failure]}
            try:
                receipt = storage.materialize(result,schedule=pipeline.Schedule60(anchor,anchor+60.),clock=clock)
                storage.finalize({'result':result,'completion':receipt,'censored':True})
            except Exception as terminal:
                q.write_new(folder/'worker-failure.json',{'primary':failure,'terminal':rc._failure('terminal',terminal)})
        else:
            # Existing immutable result/completion remain untouched; missing ACK
            # or outcome makes the supervisor fail closed rather than certify.
            q.write_new(folder/'worker-failure.json',{'primary':failure,'clock_failure':clock.failure})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--parent-pid',type=int,required=True)
    parser.add_argument('--ack-fd',type=int,required=True)
    worker(parser.parse_args())


if __name__=='__main__':
    main()
