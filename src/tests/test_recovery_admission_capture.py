"""Solver-free control admission and durable full-incumbent capture checks."""
import builtins
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

_original_import=builtins.__import__
def _guarded_import(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in admission/capture checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__=_guarded_import
try:
    from experiments import recovery_qualification as q
    from egglab import recovery_coordinator as rc
finally:
    builtins.__import__=_original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guarded_import)


class Storage:
    def __init__(self):
        self.fallbacks=[]
        self.result=None
    def save_fallback(self,witness):
        self.fallbacks.append(deepcopy(witness))
    def materialize(self,result,*,schedule,clock):
        self.result=deepcopy(result)
        return result


@pytest.mark.parametrize('arm',['static','cold'])
@pytest.mark.parametrize('returned',[127.,127.001])
def test_control_never_lifts_at_or_after_admission_cutoff(monkeypatch,arm,returned):
    clock=SimpleNamespace(now=100.)
    monkeypatch.setattr(q.time,'monotonic',lambda:clock.now)
    lifted=[]
    monkeypatch.setattr(rc,'lift_plan',lambda *a,**kw:lifted.append(True))
    monkeypatch.setattr(rc,'_full_lower',lambda *a,**kw:(None,[]))
    def planner(*a,**kw):
        clock.now=returned
        return {'plan':{'candidate':'late'}}
    storage=Storage()
    result=q.control('full','target',[1.],[0.],{'id':'task','arm':arm},100.,storage,
        rc.pf.Budget(),planner,lambda:True)
    assert lifted==[] and storage.fallbacks==[]
    assert result['selected'] is None and result['fallback'] is None
    assert result['failures']


@pytest.mark.parametrize('lift_end,admitted',[(126.999,True),(127.,True),(127.001,False)])
def test_control_precheck_and_postlift_cutoff(monkeypatch,lift_end,admitted):
    clock=SimpleNamespace(now=100.)
    monkeypatch.setattr(q.time,'monotonic',lambda:clock.now)
    lifted=[]
    witness={'plan':{'route':'saved'},'replay':{'valid':True},'true_bill':7.,'true_bill_exact':'7'}
    def planner(*a,**kw):
        clock.now=126.
        return {'plan':{'candidate':'before-cutoff'}}
    def lift(*a,**kw):
        lifted.append(clock.now)
        clock.now=lift_end
        return deepcopy(witness)
    monkeypatch.setattr(rc,'lift_plan',lift)
    storage=Storage()
    result=q.control('full','target',[1.],[0.],{'id':'task','arm':'static'},100.,storage,
        rc.pf.Budget(),planner,lambda:True)
    assert lifted==[126.]
    timing=[event for event in result['events'] if event.get('event') in {
        'control_planner_return','control_lift_enter','control_lift_exit','control_materialization_start'}]
    assert [event['event'] for event in timing]==[
        'control_planner_return','control_lift_enter','control_lift_exit','control_materialization_start']
    assert [event['at'] for event in timing]==[126.,126.,lift_end,lift_end]
    assert all(event['anchor']==100. and event['task_id']=='task'
               and event['elapsed_s']==event['at']-100. for event in timing)
    assert [event['cutoff'] for event in timing]==[127.,127.,127.,130.]
    assert bool(storage.fallbacks) is admitted
    assert (result['selected'] is not None) is admitted
    assert bool(result['failures']) is (not admitted)
    if admitted:
        assert result['selected']==witness and storage.fallbacks==[witness]
    else:
        assert result['fallback'] is None


@pytest.fixture
def capture():
    task={'id':'task','base_id':50997,'arm':'recovery'}
    policy={'task_id':'task','task_sha256':q.stable(task),'anchor':100.,
            'full_identity':'full-case','restricted_identity':'prefix-case',
            'lock_sha256':'a'*64,'attempt_sha256':'b'*64}
    event={'event':'native_incumbent','round':0,'case_identity':'full-case',
           'formulation':'fake-formulation','native_matrix':'fake-matrix',
           'extraction_policy':'fake-extraction','energy_balance':{'constraint_indices':[7]},
           'variables':[{'index':0,'name':'move','type':'B',
                         'lower':{'value':0.,'repr':'0.0'},
                         'upper':{'value':1.,'repr':'1.0'},
                         'solution':{'value':1.,'repr':'1.0'}}],
           'mapping':{'trip_ids':['trip'],'movement_ids':['move'],'intervals':[[0,60]],
                      'movement_selection':[0],'soc_before':[],'soc_after':[],
                      'grid_energy':[],'market_load':[],'epigraph':[]}}
    return task,policy,event


def test_full_capture_is_exact_durable_and_reference_resolves(tmp_path,capture):
    task,policy,event=capture
    reference=q.persist_incumbent_capture(tmp_path,task,policy,event)
    assert reference['event']=='native_incumbent_reference'
    assert reference['phase']=='full' and reference['round']==0
    assert reference['task_id']==task['id'] and reference['task_sha256']==q.stable(task)
    assert reference['case_identity']=='full-case' and reference['anchor']==100.
    assert reference['offset_bytes']==0
    path=tmp_path/reference['path']
    raw=path.read_bytes()
    assert reference['length_bytes']==len(raw)
    assert reference['sha256']==hashlib.sha256(raw).hexdigest()
    envelope=json.loads(raw)
    assert envelope['capture']==event
    assert q.verify_capture_reference(tmp_path,task,policy,reference) is True
    assert 'variables' not in reference and len(list(tmp_path.glob('incumbent-*.json')))==1


@pytest.mark.parametrize('damage',['truncate','tamper','task','case','phase','offset','hash','lock','attempt'])
def test_capture_reference_rejects_corruption_and_wrong_identity(tmp_path,capture,damage):
    task,policy,event=capture
    reference=q.persist_incumbent_capture(tmp_path,task,policy,event)
    path=tmp_path/reference['path']
    if damage=='truncate':
        path.write_bytes(path.read_bytes()[:-1])
    elif damage=='tamper':
        path.write_bytes(path.read_bytes().replace(b'fake-matrix',b'fake-MATRIX'))
    else:
        field={'task':'task_id','case':'case_identity','phase':'phase','offset':'offset_bytes',
               'hash':'sha256','lock':'lock_sha256','attempt':'attempt_sha256'}[damage]
        reference[field]=1 if damage=='offset' else 'wrong'
    with pytest.raises((ValueError,OSError)):
        q.verify_capture_reference(tmp_path,task,policy,reference)


def test_actual_planner_sink_forwards_compact_ref_and_preserves_capture_on_sink_failure(
        tmp_path,capture,monkeypatch):
    task,policy,event=capture
    state={'capture_policy':policy,'capture_references':[],
           'engineering_events':[],'sink_failure':None,'fault_exercised':False}
    accumulated=[]
    q.record_planner_event(tmp_path,task,state,event,record=accumulated.append)
    assert len(accumulated)==1
    reference=accumulated[0]
    assert reference['event']=='native_incumbent_reference'
    assert 'variables' not in reference
    assert q.verify_capture_reference(tmp_path,task,policy,reference) is True
    assert state['capture_references']==[reference]
    path=tmp_path/reference['path']
    old=path.read_bytes()
    def failed_sink(*args,**kwargs):
        raise OSError('append sink failed')
    monkeypatch.setattr(q,'native_append',failed_sink)
    with pytest.raises(OSError,match='append sink'):
        q.record_planner_event(tmp_path,task,state,{'event':'native_status','status':'fake'})
    assert state['sink_failure']
    assert path.read_bytes()==old
    assert q.verify_capture_reference(tmp_path,task,policy,reference) is True


def test_duplicate_capture_never_overwrites_original(tmp_path,capture):
    task,policy,event=capture
    reference=q.persist_incumbent_capture(tmp_path,task,policy,event)
    original=(tmp_path/reference['path']).read_bytes()
    with pytest.raises(FileExistsError):
        q.persist_incumbent_capture(tmp_path,task,policy,{**event,'variables':[]})
    assert (tmp_path/reference['path']).read_bytes()==original
    assert q.verify_capture_reference(tmp_path,task,policy,reference) is True


@pytest.mark.parametrize('corrupt',[False,True])
def test_worker_actual_sink_record_materialization_keeps_witness_and_compact_refs(
        tmp_path,capture,monkeypatch,corrupt):
    task,_,event=capture
    full=SimpleNamespace(identity=lambda:'full-case',movements=[],trips=[])
    restricted=SimpleNamespace(identity=lambda:'prefix-case',movements=[])
    fixture=tmp_path/'fixture.json'
    fixture.write_text(json.dumps({'case':{},'a':[1.],'b':[0.]}))
    lock={'tasks':[task],'backend':'FAKE','native_library':{'sha256':'c'*64},'cases':[{
        'base_id':50997,'identity':'full-case','restricted_identity':'prefix-case',
        'fixture':str(fixture),'movement_ids':[],'restricted_movement_ids':[],
        'market_sha256':q.stable({'a':[1.],'b':[0.]})}]}
    lockpath=tmp_path/'lock.json'
    lockpath.write_text(json.dumps(lock))
    folder=tmp_path/'attempt'
    folder.mkdir()
    (folder/'attempt.json').write_text(json.dumps({'task':task,'parent_monotonic':100.,
        'lock_sha256':q.sha(lockpath)}))
    monkeypatch.setattr(q.signal,'pthread_sigmask',lambda *a:None)
    monkeypatch.setattr(q.subprocess,'Popen',lambda *a,**kw:SimpleNamespace(pid=123))
    monkeypatch.setattr(q,'verify_lock',lambda *a,**kw:None)
    monkeypatch.setattr(q,'restore_case',lambda payload:full)
    monkeypatch.setattr(q.campaign,'prune',lambda *a,**kw:restricted)
    monkeypatch.setattr(q.time,'monotonic',lambda:105.)
    acknowledgments=[]
    original_write=q.os.write
    monkeypatch.setattr(q.os,'write',lambda fd,payload:(acknowledgments.append(payload) or len(payload))
                        if fd==987 else original_write(fd,payload))
    def planner(*a,record=None,**kw):
        record(deepcopy(event))
        return {'status':'fake-no-plan'}
    monkeypatch.setattr(rc.pf,'solve_planner',planner)
    witness={'plan':{'route':'prior'},'replay':{'valid':True},'true_bill':7.,'true_bill_exact':'7'}
    def coordinate(*a,storage,planner,**kw):
        events=[]
        planner(record=lambda row:events.append({'stage':'full',**row}))
        if corrupt:
            path=next(folder.glob('incumbent-*.json'))
            path.write_bytes(path.read_bytes()[:-1])
        return storage.materialize({'selected':deepcopy(witness),'fallback':deepcopy(witness),
            'events':events,'failures':[],'status':'feasible'},schedule=rc.Schedule(100.,130.),clock=q.time.monotonic)
    monkeypatch.setattr(rc,'coordinate',coordinate)
    q.worker(SimpleNamespace(output=str(folder),lock=str(lockpath),parent_pid=123,ack_fd=987))
    result=q.read(folder/'result.json')
    assert result['selected']==witness and result['fallback']==witness
    references=[e for e in result['events'] if e['event']=='native_incumbent_reference']
    assert len(references)==1 and 'variables' not in references[0]
    assert not any(e['event']=='native_incumbent' for e in result['events'])
    assert len(list(folder.glob('incumbent-*.json')))==1
    native_events=[json.loads(line) for line in (folder/'native.jsonl').read_text().splitlines()]
    assert not any(e['event']=='native_incumbent' for e in native_events)
    assert bool(result['failures']) is corrupt
    if corrupt:
        assert {f['stage'] for f in result['failures']}=={'capture_reference','native_sink'}
    else:
        assert q.verify_capture_reference(folder,task,result['native_state']['capture_policy'],references[0])
    ack=json.loads(acknowledgments[0])
    material=q.read(folder/'materialization-reference.json')
    assert material['completion_marker']['sha256']==q.sha(folder/'completion.json')
    assert material['result_sha256']==q.sha(folder/'result.json')
    assert ack['completion_monotonic']>=material['post_completion_monotonic']


def test_postcompletion_audit_fsync_time_censors_without_rewriting_completion(tmp_path,capture,monkeypatch):
    task,policy,_=capture
    marker={'task':task,'lock_sha256':policy['lock_sha256'],'parent_monotonic':100.,
            'result_sha256':'d'*64,'finished_monotonic':129.,'elapsed_s':29.,'censored':False}
    (tmp_path/'completion.json').write_text(json.dumps(marker))
    original=(tmp_path/'completion.json').read_bytes()
    receipt={'result_sha256':'d'*64,'finished_monotonic':129.,'completion_monotonic':129.1,'censored':False}
    result=q.materialization_reference(tmp_path,task,policy['lock_sha256'],100.,128.,receipt,clock=lambda:130.1)
    assert result['completion_monotonic']==130.1 and result['censored']
    assert (tmp_path/'completion.json').read_bytes()==original
    audit=q.read(tmp_path/'materialization-reference.json')
    assert audit['started_monotonic']==128. and audit['started_elapsed_s']==28.
    assert audit['post_completion_monotonic']==129.1


@pytest.mark.parametrize('damage',[None,'wrong_stage','canonical_tamper'])
def test_coordinator_stage_enrichment_keeps_reference_identity(tmp_path,capture,damage):
    task,policy,event=capture
    state={'capture_policy':policy,'capture_references':[],
           'engineering_events':[],'sink_failure':None,'fault_exercised':False}
    accumulated=[]
    q.record_planner_event(tmp_path,task,state,event,
                           record=lambda row:accumulated.append({'stage':'full',**row}))
    if damage=='wrong_stage':
        accumulated[0]['stage']='prefix'
    elif damage=='canonical_tamper':
        accumulated[0]['sha256']='0'*64
    if damage is None:
        assert q.audit_capture_references(tmp_path,task,state,accumulated)==1
    else:
        with pytest.raises(ValueError):
            q.audit_capture_references(tmp_path,task,state,accumulated)


def test_prefix_full_and_later_round_captures_have_distinct_immutable_files(tmp_path,capture):
    task,policy,event=capture
    originals=[{**deepcopy(event),'case_identity':'prefix-case','round':0},
               {**deepcopy(event),'case_identity':'full-case','round':0},
               {**deepcopy(event),'case_identity':'full-case','round':1}]
    references=[q.persist_incumbent_capture(tmp_path,task,policy,original)
                for original in originals]
    assert [reference['path'] for reference in references]==[
        'incumbent-prefix-round0.json','incumbent-full-round0.json','incumbent-full-round1.json']
    assert len({reference['path'] for reference in references})==3
    assert len(list(tmp_path.glob('incumbent-*.json')))==3
    for original,reference in zip(originals,references):
        assert q.verify_capture_reference(tmp_path,task,policy,reference) is True
        raw=(tmp_path/reference['path']).read_bytes()
        assert json.loads(raw)['capture']==original
        assert reference['sha256']==hashlib.sha256(raw).hexdigest()
        assert reference['length_bytes']==len(raw) and reference['offset_bytes']==0
