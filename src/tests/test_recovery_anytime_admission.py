"""Anytime admission targets and per-size gates, using symbolic records only."""
import builtins
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

_original_import=builtins.__import__
def _guarded_import(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in anytime admission checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__=_guarded_import
try:
    from experiments import recovery_qualification as q
    from egglab import recovery_coordinator as rc
    from test_recovery_admission_reserve import Clock,Storage,cases,witness
finally:
    builtins.__import__=_original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guarded_import)


def test_target_late_prefix_and_full_candidates_admit_within_hard_windows(monkeypatch):
    source,full=cases();clock=Clock();store=Storage();calls=[]
    def planner(case,a,b,budget,**kw):
        calls.append((case,budget,kw))
        clock.now=114. if case is source else 126.
        return {'plan':{'tag':'prefix' if case is source else 'full'}}
    def lift(source,full,plan,**kw):
        clock.now=114.5 if plan['tag']=='prefix' else 126.5
        return witness(plan['tag'],'7' if plan['tag']=='prefix' else '6')
    monkeypatch.setattr(rc,'lift_plan',lift)
    result=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
        storage=store,clock=clock,planner=planner)['result']
    assert len(calls)==2 and [c[2]['deadline'] for c in calls]==[113.,125.]
    assert result['fallback']==witness('prefix','7') and result['selected']==witness('full','6')
    assert store.saved==[witness('prefix','7')] and not result['failures']
    assert result['full_dispatched'] and not result['dispatch_stopped']
    returned=[e for e in result['events'] if e['event']=='planner_return']
    assert [e['target_overrun_s'] for e in returned]==[1.,1.]
    assert [e['admission_cutoff'] for e in returned]==[115.,127.]
    assert all(e['admission_open'] and e['admission_remaining_s']==1. for e in returned)


@pytest.mark.parametrize('arm',['static','cold'])
def test_target_late_no_plan_return_is_visible_without_failure(monkeypatch,arm):
    clock=Clock();store=Storage();bounds=[]
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(rc,'_full_lower',lambda *a,**kw:(bounds.append(clock.now) or (None,[])))
    def planner(*a,**kw):
        assert kw['deadline']==125.
        clock.now=126.
        return {'status':'NO_SOLUTION_FOUND'}
    q.control('full','target',[1.],[0.],{'id':'task','arm':arm},100.,store,
              rc.pf.Budget(),planner,lambda:True)
    assert not store.result['failures'] and store.result['selected'] is None
    assert bounds==([126.] if arm=='cold' else [])
    event=next(e for e in store.result['events'] if e['event']=='control_planner_return')
    assert event['target_overrun_s']==1. and event['admission_open']


@pytest.mark.parametrize('entered',[126.999,127.,127.001])
def test_initial_fallback_uses_hard_physical_cutoff_not_output_deadline(monkeypatch,entered):
    source,full=cases();clock=Clock(entered);store=Storage();lifts=[]
    def lift(*a,**kw):
        lifts.append(clock.now)
        return witness()
    monkeypatch.setattr(rc,'lift_plan',lift)
    result=rc.coordinate(source,full,[1.],[0.],parent_monotonic=100.,deadline=130.,
        storage=store,clock=clock,planner=lambda *a,**kw:pytest.fail('No search after22'),
        physical_fallback={'tag':'old'})['result']
    assert lifts==([entered] if entered<127. else [])
    assert (result['selected'] is not None) is (entered<127.)
    assert bool(result['failures']) is (entered>=127.)
    assert result['schedule']['deadline']==130. and result['schedule']['planner_end']==127.


def coverage_rows():
    return [{'task':{'trips':size,'arm':arm},'issues':[],'censored':False,
             'fallback_bill_exact':'7','fault_exercised':arm=='start_fault',
             'native':{'classified':[{'processed':True,'status':'unknown'}] if arm=='recovery' else []}}
            for size in (40,80) for arm in ('recovery','start_fault')]


@pytest.mark.parametrize('damage',[None,'missing80fault','issue','censored','no_fallback','unprocessed','fault_false'])
def test_size_coverage_requires_clean_paths_in_each_size(damage):
    rows=coverage_rows()
    index=2 if damage=='unprocessed' else 3
    if damage=='missing80fault':
        rows.pop(3)
    elif damage=='issue':
        rows[index]['issues']=['engineering_failure']
    elif damage=='censored':
        rows[index]['censored']=True
    elif damage=='no_fallback':
        rows[index]['fallback_bill_exact']=None
    elif damage=='unprocessed':
        rows[index]['native']['classified'][0]['processed']=False
    elif damage=='fault_false':
        rows[index]['fault_exercised']=False
    coverage=q.size_path_coverage(rows)
    assert all(coverage['40'].values())
    assert all(coverage['80'].values()) is (damage is None)
    if damage=='unprocessed':
        assert not coverage['80']['normal_recovery_processed']
    elif damage is not None:
        assert not coverage['80']['durable_fallback_start_fault_exercised']


@pytest.mark.parametrize('missing',[None,'fault80','normal80'])
def test_actual_analyzer_rejects_global_any_coverage_without_both_sizes(tmp_path,monkeypatch,missing):
    tasks=q.task_matrix([{'base_id':50997,'trips':40},{'base_id':50999,'trips':80}])
    payload=tmp_path/'symbolic.json'
    payload.write_text(json.dumps({'case':{},'a':[1.],'b':[0.]}))
    lock={'tasks':tasks,'cases':[{'base_id':base,'fixture':str(payload),'movement_ids':[]}
        for base in (50997,50999)],'checks':{},'carried_charge_s':1005.1053913375928,'freeze_charge_s':0.}
    lockpath=tmp_path/'lock.json';lockpath.write_text(json.dumps(lock))
    freeze=tmp_path/'freeze.json';freeze.write_text('{}')
    output=tmp_path/'runs';output.mkdir()
    (output/'campaign.json').write_text(json.dumps({'lock_sha256':q.sha(lockpath),
        'freeze_receipt':str(freeze),'freeze_receipt_sha256':q.sha(freeze)}))
    completed={}
    for task in tasks:
        folder=output/task['id'];folder.mkdir()
        fault=task['arm']=='start_fault' and not (missing=='fault80' and task['trips']==80)
        (folder/'result.json').write_text(json.dumps({'status':'feasible','fallback':witness(),
            'selected':witness(),'native_state':{'fault_exercised':fault},'bound_provenance':[]}))
        processed=task['arm']=='recovery' and not (missing=='normal80' and task['trips']==80)
        evidence={'submitted':int(processed),'classified':[{'status':'unknown','processed':True}]
                  if processed else [],'unattributed_log_matches':[]}
        (folder/'start-evidence.json').write_text(json.dumps(evidence))
        completed[task['id']]={'failure':None,'returncode':0,'worker_failure':False,
            'endpoint_censored':False,'completion_issue':None,'peak_tree_rss_bytes':0,
            'endpoint_wall_s':26.,'charged_cpu_s':27.}
    monkeypatch.setattr(q,'verify_lock',lambda *a,**kw:None)
    monkeypatch.setattr(q,'freeze_accounting',lambda lock,*a:lock)
    monkeypatch.setattr(q,'resume_state',lambda *a:(completed,1005.1053913375928))
    monkeypatch.setattr(q,'restore_case',lambda payload:SimpleNamespace())
    monkeypatch.setattr(rc,'lift_plan',lambda *a,**kw:witness())
    report=q._analyze(SimpleNamespace(lock=str(lockpath),output=str(output),report=str(tmp_path/'report.json')))
    assert report['passed'] is (missing is None)
    assert all(report['coverage_by_size']['40'].values())
    assert all(report['coverage_by_size']['80'].values()) is (missing is None)
    if missing=='fault80':
        assert 'durable_fallback_start_fault_path_unexercised:80' in report['unresolved']
    elif missing=='normal80':
        assert 'normal_recovery_native_partial_start_processing_unobserved:80' in report['unresolved']
