"""Typed integer guard tests with fake builders/clocks and durable temp events."""
import builtins
from contextlib import contextmanager
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

_original_import=builtins.__import__
def _guarded_import(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in integer cutoff checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__=_guarded_import
try:
    from experiments import recovery_qualification as q
    from egglab import native_pathflow as pf
finally:
    builtins.__import__=_original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guarded_import)


@pytest.fixture
def harness(tmp_path,monkeypatch):
    @contextmanager
    def enter(phase='prefix',now=None,builder_error=None,build_end=None):
        task={'id':'task','base_id':50997,'arm':{
            'prefix':'recovery','full':'recovery','static':'static','cold':'cold'}[phase]}
        lock={'backend':'FAKE','native_library':{'sha256':'library'},'cases':[{
            'base_id':50997,'identity':'full-case','restricted_identity':'prefix-case'}]}
        identity='prefix-case' if phase in ('prefix','static') else 'full-case'
        clock=SimpleNamespace(now=(112. if phase=='prefix' else 124.) if now is None else now)
        monkeypatch.setattr(q.time,'monotonic',lambda:clock.now)
        calls=[]
        built={'model':SimpleNamespace(),'backend_runtime':{
            'requested':'FAKE','native_library_sha256':'library'}}
        def build(*args,**kwargs):
            calls.append(args)
            if build_end is not None:
                clock.now=build_end
            if builder_error is not None:
                raise builder_error
            return built
        monkeypatch.setattr(pf,'build_feasible_model',build)
        case=SimpleNamespace(identity=lambda:identity)
        with q.instrument_native(lock,task,tmp_path,anchor=100.) as state:
            yield SimpleNamespace(task=task,lock=lock,case=case,state=state,
                                  calls=calls,built=built,clock=clock,folder=tmp_path)
    return enter


def planner_failure(h):
    """The native planner's actual caught-exception failure event schema."""
    try:
        pf.build_feasible_model(h.case,'FAKE')
    except Exception as exc:
        return {'event':'native_search_failed','stage':'model_build',
                'error_type':type(exc).__name__,'error':str(exc)}
    raise AssertionError('Expected fake planner to observe a refused build')


@pytest.mark.parametrize('phase',['prefix','full','static','cold'])
def test_exact_integer_boundary_is_durable_single_use_expected_stop(harness,phase):
    with harness(phase) as h:
        event=planner_failure(h)
        assert issubclass(q.IntegerGateClosed,TimeoutError)
        assert event['error_type']=='IntegerGateClosed'
        assert h.calls==[]
        pending=deepcopy(h.state['integer_gate_pending'])
        evidence=pending['evidence']
        assert pending['durable'] is True
        assert evidence['phase']==phase
        assert evidence['integer_cutoff']==(112. if phase=='prefix' else 124.)
        assert evidence['observed_monotonic']==evidence['integer_cutoff']
        assert evidence['guard_point']=='before_model_build'
        assert evidence['native_dispatched'] is False
        durable=[json.loads(line) for line in (h.folder/'native.jsonl').read_text().splitlines()]
        assert evidence in durable
        assert not q.native_event_is_failure(h.task,h.state,event)
        assert h.state['expected_budget_stops']==[evidence]
        assert q.native_event_is_failure(h.task,h.state,event)


def test_before_cutoff_builds_without_expected_stop(harness):
    with harness(now=111.999) as h:
        assert pf.build_feasible_model(h.case,'FAKE') is h.built
        assert len(h.calls)==1
        assert not h.state.get('integer_gate_pending')
        assert not h.state.get('expected_budget_stops')


@pytest.mark.parametrize('field,value',[
    ('phase','full'),('case_identity','other-case'),('task_id','other-task'),
    ('task_sha256','other-hash'),('anchor',99.),('integer_cutoff',113.),
    ('observed_monotonic',111.999),('guard_point','after_model_build'),
    ('native_dispatched',True),('elapsed_s',13.),
    ('observed_monotonic',float('nan')),('observed_monotonic',float('inf')),
    ('anchor',float('-inf')),('integer_cutoff',float('nan'))])
def test_malformed_or_wrong_guard_evidence_is_fatal(harness,field,value):
    with harness() as h:
        event=planner_failure(h)
        h.state['integer_gate_pending']['evidence'][field]=value
        if field=='observed_monotonic' and value==111.999:
            h.state['integer_gate_pending']['evidence']['elapsed_s']=value-100.
        assert q.native_event_is_failure(h.task,h.state,event)
        assert not h.state.get('expected_budget_stops')


@pytest.mark.parametrize('damage',['missing','not_durable','wrong_token','wrong_type','wrong_stage','wrong_task'])
def test_unmatched_guard_tokens_fail_closed(harness,damage):
    with harness() as h:
        event=planner_failure(h)
        task=h.task
        if damage=='missing':
            h.state.pop('integer_gate_pending')
        elif damage=='not_durable':
            h.state['integer_gate_pending']['durable']=False
        elif damage=='wrong_token':
            event['error']='integer_gate_closed:'+'0'*32
        elif damage=='wrong_type':
            event['error_type']='TimeoutError'
        elif damage=='wrong_stage':
            event['stage']='optimization'
        else:
            task={**task,'id':'different'}
        assert q.native_event_is_failure(task,h.state,event)
        assert not h.state.get('expected_budget_stops')


def test_generic_builder_timeout_remains_fatal(harness):
    with harness(now=111.,builder_error=TimeoutError('No native model build after integer gate')) as h:
        event=planner_failure(h)
        assert len(h.calls)==1 and event['error_type']=='TimeoutError'
        assert not h.state.get('integer_gate_pending')
        assert q.native_event_is_failure(h.task,h.state,event)


def test_actual_postbuild_overrun_is_fatal(harness):
    with harness(now=111.,build_end=112.) as h:
        event=planner_failure(h)
        assert len(h.calls)==1 and event['error_type']=='TimeoutError'
        assert not h.state.get('integer_gate_pending')
        assert q.native_event_is_failure(h.task,h.state,event)


def test_sink_failure_cannot_mint_expected_cutoff_token(harness,monkeypatch):
    with harness() as h:
        def failed_sink(*args,**kwargs):
            raise OSError('durable cutoff sink failed')
        monkeypatch.setattr(q,'native_append',failed_sink)
        event=planner_failure(h)
        assert h.calls==[] and event['error_type']=='OSError'
        assert h.state['sink_failure']
        assert not h.state.get('integer_gate_pending')
        assert q.native_event_is_failure(h.task,h.state,event)
        monkeypatch.setattr(q.os,'getppid',lambda:123)
        assert not q.dispatch_allowed(123,h.folder,h.state)


@pytest.mark.parametrize('expected',['typed_cutoff','generic_timeout','postbuild_overrun','sink_failure'])
def test_actual_planner_catch_routes_guard_event_to_classifier(harness,monkeypatch,expected):
    monkeypatch.setattr(pf,'_check_market',lambda *args:None)
    monkeypatch.setattr(pf,'_check_budget',lambda *args:None)
    options={
        'typed_cutoff':{},
        'generic_timeout':{'now':111.,'builder_error':TimeoutError('ordinary native build timeout')},
        'postbuild_overrun':{'now':111.,'build_end':112.},
        'sink_failure':{}}[expected]
    with harness(**options) as h:
        if expected=='sink_failure':
            monkeypatch.setattr(q,'native_append',lambda *args:(_ for _ in ()).throw(OSError('sink failed')))
        events=[]
        def sink(event):
            events.append(deepcopy(event))
            if q.native_event_is_failure(h.task,h.state,event):
                h.state['engineering_events'].append(deepcopy(event))
        budget=SimpleNamespace(wall_seconds=30.,max_rounds=1,backend='FAKE')
        result=pf.solve_planner(h.case,[1.],[0.],budget,record=sink,deadline=130.)
        failure=[event for event in events if event['event']=='native_search_failed']
        assert len(failure)==1 and failure[0]['stage']=='model_build'
        assert result['status']=='search_failed'
        assert bool(h.state['engineering_events']) is (expected!='typed_cutoff')
        assert len(h.state['expected_budget_stops'])==int(expected=='typed_cutoff')
        monkeypatch.setattr(q.os,'getppid',lambda:123)
        assert q.dispatch_allowed(123,h.folder,h.state) is (expected=='typed_cutoff')
