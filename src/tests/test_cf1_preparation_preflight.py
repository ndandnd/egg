"""Configuration-only fakes for the single-CF1 revision; no backend permitted."""
import builtins
from copy import deepcopy
import json

import pytest

_original_import=builtins.__import__
def _guard(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in configuration checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__=_guard
try:
    from experiments import cf1_preparation_preflight as revision
    from experiments import comparison_native_preflight as adapter
    from experiments import comparison_native_worker as worker
    from experiments import recovery_qualification as q
    from test_comparison_native_adapter import capture_case, capture_raw, capture_reference
finally:
    builtins.__import__=_original_import

START=1416.3727097992353
CAP=START+165.
POLICY='cf1-preparation-native-v2'


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guard)


def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True))


def snapshot():
    names=('POLICY','PACKAGE_START','PACKAGE_LIMIT','PACKAGE_CAP','ENDPOINT_S','STOP_S','OUTER_S',
           'ANALYSIS_FINAL_RESERVE_S','SUPERVISION_RESERVE_S','WORKER_ARGV_PREFIX','task_matrix','checked_sources','_LOCK')
    return ({name:getattr(adapter,name) for name in names},worker.POLICY,worker.task_matrix)


def test_single_new_revision_task_and_exact_budget_preserve_old_defaults():
    before=snapshot()
    old=adapter.task_matrix([{'base_id':50999,'trips':80}])
    with revision.revision2():
        tasks=adapter.task_matrix([{'base_id':50999,'trips':80}])
        assert tasks==worker.task_matrix() and len(tasks)==1
        expected={'arm':'cf1','base_id':50999,'trips':80,'seed':17,'seconds':60.,
                  'fault':None,'protocol_revision':2}
        assert tasks[0]=={**expected,'id':q.stable(expected)[:20]}
        assert tasks[0]['id'] not in {row['id'] for row in old}
        assert adapter.POLICY==worker.POLICY==POLICY
        assert (adapter.PACKAGE_START,adapter.PACKAGE_LIMIT,adapter.PACKAGE_CAP)==(START,165.,CAP)
        assert (adapter.ENDPOINT_S,adapter.STOP_S,adapter.OUTER_S)==(60.,61.,62.5)
        assert adapter.ANALYSIS_FINAL_RESERVE_S==30. and adapter.SUPERVISION_RESERVE_S==45.
        with pytest.raises(ValueError):adapter.task_matrix([{'base_id':50997,'trips':40}])
    assert snapshot()==before and len(adapter.task_matrix([{'base_id':50999,'trips':80}]))==2


@pytest.mark.parametrize('interrupt',[False,True])
def test_binding_restores_after_success_or_error_and_rejects_nesting(interrupt):
    before=snapshot();qnames=('POLICY','OUTER_ALLOCATION','SUPERVISOR_STOP_S','launch','verify_lock')
    qbefore={name:getattr(q,name) for name in qnames}
    try:
        with revision.revision2():
            with pytest.raises(RuntimeError):
                with revision.revision2():pytest.fail('Nested revision accepted')
            with adapter.bound60():
                assert q.POLICY==POLICY and q.OUTER_ALLOCATION==62.5 and q.SUPERVISOR_STOP_S==61.
                with pytest.raises(RuntimeError):
                    with adapter.bound60():pytest.fail('Nested native binding accepted')
            if interrupt:raise KeyboardInterrupt('fake interrupt')
    except KeyboardInterrupt:
        assert interrupt
    assert snapshot()==before
    assert all(getattr(q,name) is value for name,value in qbefore.items())
    with adapter.bound60():assert q.POLICY=='comparison-native-preflight-v1'


def test_launch_uses_new_worker_cli_and_restores_scoped_hooks_on_error(monkeypatch,tmp_path):
    commands=[];writes=[]
    def original_write(path,value):writes.append(deepcopy(value))
    def original_popen(command,*args,**kwargs):commands.append(command);raise OSError('fake Popen')
    monkeypatch.setattr(q,'write_new',original_write)
    monkeypatch.setattr(q.subprocess,'Popen',original_popen)
    def legacy(*args):
        q.write_new(tmp_path/'attempt.json',{'parent_monotonic':100.,'deadline':130.})
        q.subprocess.Popen(['python','-m','experiments.recovery_qualification','worker','--lock','locked'])
    monkeypatch.setattr(adapter,'_BASE_LAUNCH',legacy)
    with revision.revision2():
        with pytest.raises(OSError):adapter.launch(None,adapter.task_matrix()[0],tmp_path,'locksha')
        assert commands==[['python','-m','experiments.cf1_preparation_preflight','worker','--lock','locked']]
        assert writes==[{'parent_monotonic':100.,'deadline':160.}]
        assert q.write_new is original_write and q.subprocess.Popen is original_popen


@pytest.mark.parametrize('excess',[0.,.01])
def test_prelaunch_reserves_worker_supervision_and_combined_finalization(monkeypatch,excess):
    monkeypatch.setattr(adapter.time,'process_time',lambda:0.)
    monkeypatch.setattr(q,'_monitor_child_cpu_s',0.)
    called=[];monkeypatch.setattr(adapter,'launch',lambda *args:called.append(args))
    state={'base_spent':CAP-62.5-45.-30.+excess,'finished':{},'prior_ids':set(),'cpu0':0.}
    with revision.revision2():
        with adapter.bound60(state):
            if excess:
                with pytest.raises(RuntimeError):q.launch('fake')
            else:q.launch('fake')
    assert bool(called) is (excess==0.)


@pytest.mark.parametrize('at_boundary',[False,True])
def test_active_cap_preserves_cleanup_and_combined_reserve(monkeypatch,at_boundary):
    monkeypatch.setattr(adapter.time,'process_time',lambda:0.)
    monkeypatch.setattr(q,'_monitor_child_cpu_s',0.)
    monkeypatch.setattr(q,'resource_step',lambda *args:None)
    state={'base_spent':CAP-2.5-30.-(0. if at_boundary else .01),
           'finished':{},'prior_ids':set(),'cpu0':0.}
    item={'task':{'id':'active'},'anchor':100.,'cpu':0.}
    with revision.revision2():
        with adapter.bound60(state):reason=q.resource_step(item,{},100.,100.)
    assert reason==('comparison_package_cleanup_reserve' if at_boundary else None)


def freeze_files(tmp_path):
    source=tmp_path/'source.py';source.write_text('# fake checked source\n')
    lock={'sources':{str(source):q.sha(source)},'prior_accounting_sha256':'prior',
          'carried_charge_s':START,'freeze_charge_s':0.}
    lockpath=tmp_path/'lock.json';write(lockpath,lock)
    folder=tmp_path/'freeze';folder.mkdir()
    for name in ('stdout.log','stderr.log'):(folder/name).write_text('')
    write(folder/'attempt.json',{'lock':str(lockpath)})
    total=1.+.2
    value={'policy':POLICY,'phase':'comparison_native_freeze','passed':True,
        'failure':None,'primary_failure':None,'monitor_failure':None,'secondary_errors':[],
        'returncode':0,'source_changes':[],'source_hashes':lock['sources'],
        'accounting_observations_complete':True,'accounting_unresolved':False,'charge_is_lower_bound':False,
        'lock_sha256':q.sha(lockpath),'prior_accounting_sha256':'prior',
        'charged_allocation_s':1.,'supervisor_cpu_s':.2,'charged_cpu_s':total,
        'cumulative_qualification_charge_s':START+total,'elapsed_allocation_s':1.,
        'sampled_peak_rss_bytes':1024.,'termination':{'group_absent':True,'reaped':True,
            'owned_pgids':[123],'surviving_pgids':[],'cleanup_errors':[],'probe_diagnostics':[]},
        'artifact_hashes':{name:q.sha(folder/name) for name in ('attempt.json','stdout.log','stderr.log')},
        'stdout_sha256':q.sha(folder/'stdout.log'),'stderr_sha256':q.sha(folder/'stderr.log')}
    path=folder/'supervisor.json';write(path,value)
    return lock,lockpath,path,value


@pytest.mark.parametrize('damage',[None,'old_policy','wrong_phase','double_supervisor'])
def test_new_policy_keeps_freeze_phase_and_total_charge_convention(tmp_path,damage):
    lock,lockpath,path,value=freeze_files(tmp_path)
    if damage=='old_policy':value['policy']='comparison-native-preflight-v1'
    elif damage=='wrong_phase':value['phase']='native_worker'
    elif damage=='double_supervisor':value['cumulative_qualification_charge_s']+=.2
    write(path,value)
    with revision.revision2():
        if damage:
            with pytest.raises(ValueError):adapter.freeze_accounting(lock,lockpath,path)
        else:
            result=adapter.freeze_accounting(lock,lockpath,path)
            assert result['freeze_charge_s']==pytest.approx(1.2)
            assert result['carried_charge_s']==START


def test_capture_membership_optimization_preserves_valid_fixed_scope(tmp_path):
    case,source,lock,task=capture_case(tmp_path)
    ref=capture_reference(tmp_path,lock,task,case)
    proof=worker.verify_capture_reference(tmp_path,lock,task,100.,ref)
    assert proof['case_identity']==case.identity() and proof['phase']=='cf1'
    assert proof['all_mapped_binary_fixed'] and proof['all_unmapped_continuous']
    assert proof['sha256']==ref['sha256']


def test_capture_membership_still_rejects_hidden_discrete_and_duplicate_mapping(tmp_path):
    case,source,lock,task=capture_case(tmp_path)
    for sequence,damage in enumerate(('hidden_discrete','duplicate_mapping'),1):
        raw=capture_raw(case)
        if damage=='hidden_discrete':raw['variables'][-1]['type']='I'
        else:raw['mapping']['movement_selection'][-1]=raw['mapping']['movement_selection'][0]
        ref=capture_reference(tmp_path,lock,task,case,sequence=sequence,raw=raw)
        with pytest.raises(ValueError):worker.verify_capture_reference(tmp_path,lock,task,100.,ref)
