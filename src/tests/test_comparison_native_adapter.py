"""Affected 60s adapter paths with synthetic files and fake native calls only."""
import builtins
from copy import deepcopy
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

_original_import=builtins.__import__
def _guard(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in adapter unit checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__=_guard
try:
    from experiments import comparison_native_preflight as adapter
    from experiments import comparison_native_worker as worker
    from experiments import recovery_qualification as q
    from egglab import recovery_coordinator as rc
    from test_constructive_controls import chain_case,Clock
finally:
    builtins.__import__=_original_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins,'__import__',_guard)


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True))


def task(arm='cf1'):
    return next(value for value in adapter.task_matrix([{'base_id':50999,'trips':80}]) if value['arm']==arm)


def test_closed_two_task_scope_and_worker_task_identity():
    tasks=adapter.task_matrix([{'base_id':50999,'trips':80}])
    assert [value['arm'] for value in tasks]==['cf1','recovery']
    assert tasks==worker.task_matrix()
    assert all(value['seconds']==60. and value['seed']==17 and value['fault'] is None for value in tasks)
    with pytest.raises(ValueError):adapter.task_matrix([{'base_id':50997,'trips':40}])
    with pytest.raises(ValueError):adapter.task_matrix([{'base_id':50999,'trips':80}]*2)


def test_binding_restores_all_affected_functions_on_interrupt_and_rejects_nested_use():
    names=('POLICY','OUTER_ALLOCATION','SUPERVISOR_STOP_S','launch','completion_endpoint',
           'verify_lock','freeze_accounting','_analyze','resume_state','finish','resource_step')
    original={name:getattr(q,name) for name in names}
    unchanged={name:getattr(q,name) for name in ('run','monitor_sample','stop_owned','group_probe','receive_ack')}
    state={'base_spent':1300.,'finished':{},'cpu0':0.,'prior_ids':set()}
    with pytest.raises(KeyboardInterrupt):
        with adapter.bound60(state):
            assert q.POLICY==adapter.POLICY and q.OUTER_ALLOCATION==62.5 and q.SUPERVISOR_STOP_S==61.
            assert q.completion_endpoint is adapter.completion_endpoint
            assert all(getattr(q,name) is value for name,value in unchanged.items())
            with pytest.raises(RuntimeError):
                with adapter.bound60():pytest.fail('Nested context acquired')
            raise KeyboardInterrupt()
    assert all(getattr(q,name) is value for name,value in original.items())
    with adapter.bound60():assert q.OUTER_ALLOCATION==62.5


def test_launch_transforms_only_deadline_and_worker_argv_and_restores_on_failure(monkeypatch,tmp_path):
    writes=[];commands=[]
    def original_write(path,value):writes.append(deepcopy(value))
    def original_popen(command,*args,**kwargs):commands.append(command);raise OSError('fake launch failure')
    monkeypatch.setattr(q,'write_new',original_write)
    monkeypatch.setattr(q.subprocess,'Popen',original_popen)
    def legacy(*args):
        q.write_new(tmp_path/'attempt.json',{'parent_monotonic':100.,'deadline':130.})
        return q.subprocess.Popen(['python','-m','experiments.recovery_qualification','worker','--lock','lock'])
    monkeypatch.setattr(adapter,'_BASE_LAUNCH',legacy)
    with pytest.raises(OSError):adapter.launch(None,task(),tmp_path,'lock')
    assert writes[0]['deadline']==160.
    assert commands==[['python','-m','experiments.comparison_native_worker','--lock','lock']]
    assert q.write_new is original_write and q.subprocess.Popen is original_popen


def test_package_accounting_counts_active_or_finished_worker_and_monitor_once(monkeypatch):
    monkeypatch.setattr(adapter.time,'process_time',lambda:7.)
    monkeypatch.setattr(q,'_monitor_child_cpu_s',3.)
    state={'base_spent':1300.,'finished':{'one':10.},'cpu0':5.,'prior_ids':set()}
    item={'task':{'id':'two'},'anchor':100.,'cpu':6.}
    assert adapter.package_charge(state,item,104.)==1321.
    item['task']['id']='one'
    assert adapter.package_charge(state,item,104.)==1315.


def test_finish_wrapper_deduplicates_charge_and_preserves_resume_account(monkeypatch):
    monkeypatch.setattr(q,'resume_state',lambda *args:({'prior':{}},1300.))
    monkeypatch.setattr(q,'finish',lambda *args:{'charged_cpu_s':8.,'group_absent':False})
    state={'base_spent':0.,'finished':{},'cpu0':0.,'prior_ids':set()}
    with adapter.bound60(state):
        q.resume_state(None,None,None)
        item={'task':{'id':'new'}}
        assert q.finish(item,None,None,None)['group_absent'] is False
        q.finish(item,None,None,None)
    assert state['base_spent']==1300. and state['finished']=={'new':8.}


@pytest.mark.parametrize('extra',[0.,.01])
def test_next_worker_requires_allocation_supervision_and_analysis_reserve(monkeypatch,extra):
    monkeypatch.setattr(adapter.time,'process_time',lambda:0.)
    monkeypatch.setattr(q,'_monitor_child_cpu_s',0.)
    calls=[]
    monkeypatch.setattr(adapter,'launch',lambda *args:calls.append(True))
    state={'base_spent':adapter.PACKAGE_CAP-62.5-40.-5.+extra,'finished':{},'cpu0':0.,'prior_ids':set()}
    with adapter.bound60(state):
        if extra:
            with pytest.raises(RuntimeError):q.launch(None,None,None,None)
        else:q.launch(None,None,None,None)
    assert calls==([] if extra else [True])


def test_active_package_cap_reserves_cleanup_and_preserves_primary_resource_reason(monkeypatch):
    monkeypatch.setattr(adapter.time,'process_time',lambda:0.)
    monkeypatch.setattr(q,'_monitor_child_cpu_s',0.)
    monkeypatch.setattr(q,'resource_step',lambda *args:'worker_rss_limit')
    state={'base_spent':adapter.PACKAGE_CAP-8.,'finished':{},'cpu0':0.,'prior_ids':set()}
    item={'task':{'id':'new'},'anchor':100.,'cpu':1.}
    with adapter.bound60(state):assert q.resource_step(item,{},100.,101.)=='worker_rss_limit'
    monkeypatch.setattr(q,'resource_step',lambda *args:None)
    with adapter.bound60(state):assert q.resource_step(item,{},100.,101.)=='comparison_package_cleanup_reserve'


def completion_files(tmp_path,*,deadline=160.,ack_time=159.9,status='feasible'):
    value=task();locksha='locked-source';anchor=100.
    write(tmp_path/'result.json',{'task':value,'lock_sha256':locksha})
    resultsha=q.sha(tmp_path/'result.json')
    write(tmp_path/'completion.json',{'task':value,'lock_sha256':locksha,'parent_monotonic':anchor,
        'deadline':deadline,'finished_monotonic':159.8,'elapsed_s':159.8-anchor,
        'result_sha256':resultsha,'censored':False})
    write(tmp_path/'worker-outcome.json',{'task':value,'lock_sha256':locksha,
        'result_sha256':resultsha,'status':status,'censored':False})
    ack={'task_id':value['id'],'lock_sha256':locksha,'parent_monotonic':anchor,
        'result_sha256':resultsha,'completion_sha256':q.sha(tmp_path/'completion.json'),
        'completion_monotonic':ack_time,'worker_outcome_sha256':q.sha(tmp_path/'worker-outcome.json'),
        'worker_status':status,'worker_censored':False}
    return value,locksha,anchor,ack


@pytest.mark.parametrize('at',[160.,math.nextafter(160.,math.inf)])
def test_sixty_second_ack_endpoint_is_independent_of_process_exit_grace(tmp_path,at):
    value,locksha,anchor,ack=completion_files(tmp_path,ack_time=at)
    result=adapter.completion_endpoint(tmp_path,value,locksha,anchor,acknowledgment=ack)
    assert result['completion_issue'] is None
    assert result['endpoint_censored'] is (at>160.)


@pytest.mark.parametrize('damage',['old30','wrong_task','late_outcome_hash','clock_failed','missing_ack'])
def test_completion_and_final_worker_outcome_are_both_bound_before_timeliness(tmp_path,damage):
    value,locksha,anchor,ack=completion_files(tmp_path,deadline=130. if damage=='old30' else 160.,
        status='clock_failed' if damage=='clock_failed' else 'feasible')
    if damage=='wrong_task':ack['task_id']='other'
    elif damage=='late_outcome_hash':write(tmp_path/'worker-outcome.json',{'changed':True})
    elif damage=='missing_ack':ack=None
    result=adapter.completion_endpoint(tmp_path,value,locksha,anchor,acknowledgment=ack)
    assert result['endpoint_censored'] and result['completion_issue']


def test_incomplete_terminal_ledger_cannot_be_resumed_as_a_new_attempt(tmp_path):
    lock={'carried_charge_s':1300.,'freeze_charge_s':1.,'tasks':[task()]}
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'carry_forward','charged_cpu_s':1300.,'freeze_charge_s':1.})
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'incomplete_terminal_audit','task_id':task()['id']})
    with adapter.bound60():
        with pytest.raises(ValueError,match='Terminal audit failure'):q.resume_state(tmp_path,lock,'sha')


def test_unknown_owned_group_is_not_absence_even_after_leader_reap(monkeypatch):
    clock=Clock(161.);signals=[]
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(q.time,'sleep',lambda duration:setattr(clock,'now',clock.now+duration))
    monkeypatch.setattr(q.os,'killpg',lambda pgid,signum:signals.append((pgid,signum)))
    monkeypatch.setattr(q,'group_probe',lambda pgid:{'pgid':pgid,'state':'unknown','error_type':'PermissionError'})
    proc=SimpleNamespace(pid=777,returncode=None)
    def wait(*,timeout):clock.now+=timeout;proc.returncode=0
    proc.wait=wait
    with adapter.bound60():receipt=q.stop_owned(proc,{777},100.+q.OUTER_ALLOCATION)
    assert proc.returncode==0 and not receipt['group_absent']
    assert receipt['cleanup_deadline']==162.5 and clock.now<=162.5
    assert receipt['probe_diagnostics'] and receipt['cleanup_errors'] and signals


def freeze_receipt_files(tmp_path):
    source=tmp_path/'source.py';source.write_text('# synthetic source identity\n')
    lock={'sources':{str(source):q.sha(source)},'prior_accounting_sha256':'prior-account',
          'carried_charge_s':1300.,'freeze_charge_s':0.}
    lockpath=tmp_path/'lock.json';write(lockpath,lock)
    folder=tmp_path/'external-freeze';folder.mkdir()
    (folder/'stdout.log').write_text('');(folder/'stderr.log').write_text('')
    write(folder/'attempt.json',{'lock':str(lockpath)})
    receipt={'policy':adapter.POLICY,'phase':'comparison_native_freeze','passed':True,
        'failure':None,'primary_failure':None,'monitor_failure':None,'secondary_errors':[],
        'returncode':0,'source_changes':[],'source_hashes':lock['sources'],
        'accounting_observations_complete':True,'accounting_unresolved':False,'charge_is_lower_bound':False,
        'lock_sha256':q.sha(lockpath),'prior_accounting_sha256':lock['prior_accounting_sha256'],
        'charged_allocation_s':1.,'supervisor_cpu_s':.2,'charged_cpu_s':1.+.2,
        'cumulative_qualification_charge_s':1300.+1.+.2,'elapsed_allocation_s':1.,
        'sampled_peak_rss_bytes':1024.,'termination':{'group_absent':True,'reaped':True,
            'owned_pgids':[123],'surviving_pgids':[],'cleanup_errors':[],'probe_diagnostics':[]},
        'artifact_hashes':{name:q.sha(folder/name) for name in ('attempt.json','stdout.log','stderr.log')},
        'stdout_sha256':q.sha(folder/'stdout.log'),'stderr_sha256':q.sha(folder/'stderr.log')}
    path=folder/'supervisor.json';write(path,receipt)
    return lock,lockpath,path,receipt


def test_freeze_receipt_total_already_includes_supervisor_and_relative_artifacts(tmp_path):
    lock,lockpath,path,receipt=freeze_receipt_files(tmp_path)
    admitted=adapter.freeze_accounting(lock,lockpath,path)
    assert admitted['freeze_charge_s']==pytest.approx(1.2)
    assert admitted['carried_charge_s']==1300.


@pytest.mark.parametrize('damage',['secondary','unknown_cpu','unresolved','lower_bound','worker_exit',
                                  'unreaped','unknown_group','lock','prior','double_supervisor','artifact'])
def test_contradictory_or_incomplete_freeze_receipt_blocks_launch(tmp_path,damage):
    lock,lockpath,path,value=freeze_receipt_files(tmp_path)
    if damage=='secondary':value['secondary_errors']=[{'error':'audit failed'}]
    elif damage=='unknown_cpu':value['accounting_observations_complete']=False
    elif damage=='unresolved':value['accounting_unresolved']=True
    elif damage=='lower_bound':value['charge_is_lower_bound']=True
    elif damage=='worker_exit':value['returncode']=1
    elif damage=='unreaped':value['termination']['reaped']=False
    elif damage=='unknown_group':value['termination']['group_absent']=False
    elif damage=='lock':value['lock_sha256']='other'
    elif damage=='prior':value['prior_accounting_sha256']='other'
    elif damage=='double_supervisor':value['cumulative_qualification_charge_s']+=.2
    elif damage=='artifact':(path.parent/'stdout.log').write_text('changed after freeze')
    write(path,value)
    with pytest.raises(ValueError):adapter.freeze_accounting(lock,lockpath,path)


def checked_files(tmp_path,monkeypatch):
    root=tmp_path/'source-root';root.mkdir()
    monkeypatch.setattr(q,'ROOT',root)
    names=('src/experiments/recovery_qualification.py','src/experiments/comparison_native_preflight.py',
        'src/experiments/comparison_native_worker.py','src/egglab/comparison_coordinator.py',
        'src/egglab/constructive_proposal.py','src/tests/test_comparison_native_adapter.py')
    sources={}
    for name in names:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# synthetic checked identity\n')
        sources[str(path)]=q.sha(path)
    folder=tmp_path/'check';folder.mkdir()
    write(folder/'attempt.json',{'source_hashes':sources})
    (folder/'stdout.log').write_text('affected tests passed');(folder/'stderr.log').write_text('')
    value={'passed':True,'returncode':0,'failure':None,'primary_failure':None,
        'source_changes':[],'secondary_errors':[],'accounting_observations_complete':True,
        'accounting_unresolved':False,'charge_is_lower_bound':False,
        'cumulative_qualification_charge_s':adapter.PACKAGE_START+1.,
        'termination':{'group_absent':True,'reaped':True,'owned_pgids':[123],
                       'surviving_pgids':[],'cleanup_errors':[]},
        'stdout_sha256':q.sha(folder/'stdout.log'),'stderr_sha256':q.sha(folder/'stderr.log'),
        'artifact_hashes':{name:q.sha(folder/name) for name in ('attempt.json','stdout.log','stderr.log')}}
    write(folder/'result.json',value)
    return folder,sources,value


def test_source_check_closure_and_relative_artifacts_are_verified(tmp_path,monkeypatch):
    folder,sources,value=checked_files(tmp_path,monkeypatch)
    evidence=adapter.checked_sources(folder)
    assert set(Path(path).name for path in evidence)=={'attempt.json','result.json'}
    first=Path(next(iter(sources)));first.write_text('modified source')
    with pytest.raises(ValueError):adapter.checked_sources(folder)


def test_relative_artifacts_cannot_escape_receipt_folder(tmp_path):
    folder=tmp_path/'receipt';folder.mkdir();outside=tmp_path/'outside.log';outside.write_text('synthetic')
    with pytest.raises(ValueError):adapter.verify_artifacts(folder,{'../outside.log':q.sha(outside)})


@pytest.mark.parametrize('damage',['old_policy','old_schedule','library','fixture'])
def test_native_lock_rejects_old_thirty_second_policy_or_stale_assets(tmp_path,monkeypatch,damage):
    folder,sources,value=checked_files(tmp_path,monkeypatch)
    fixture=tmp_path/'synthetic-fixture.json';fixture.write_text('identity-only synthetic asset')
    library=tmp_path/'library-id';library.write_text('hash only; never loaded')
    proof=tmp_path/'proof';proof.write_text('immutable proof')
    cases=[{'base_id':50999,'trips':80,'fixture':str(fixture),'movement_ids':['a'],
        'restricted_movement_ids':['a'],'restricted_identity':'restricted','market_sha256':'market',
        'selection_policy':'common-priceblind-top3-exact30-v1'}]
    monkeypatch.setattr(q,'environment',lambda:{'synthetic':True})
    monkeypatch.setattr(q.campaign,'sources',lambda:sources)
    lock={'policy':adapter.POLICY,'cases':cases,'tasks':adapter.task_matrix(cases),'schedule':adapter.schedule_spec(),
        'backend':'GRB','models':{},'tariff':'day','package_start_charge_s':adapter.PACKAGE_START,
        'package_limit_s':adapter.PACKAGE_LIMIT,'package_cap_s':adapter.PACKAGE_CAP,
        'carried_charge_s':1300.,'freeze_charge_s':0.,'sources':sources,
        'assets':{str(fixture):q.sha(fixture)},'checks':adapter.checked_sources(folder),
        'evidence':{str(proof):q.sha(proof)},'prior_evidence':{str(proof):q.sha(proof)},
        'environment':{'synthetic':True},'native_library':{'path':str(library),'sha256':q.sha(library)},
        'package_budget':{'check_s':40.,'freeze_s':10.,'worker_s':125.,'monitor_s':50.,'analysis_s':5.}}
    adapter.verify_lock(lock)
    if damage=='old_policy':lock['policy']='recovery-phase1-runner-v1'
    elif damage=='old_schedule':lock['schedule']['deadline']=30.
    elif damage=='library':library.write_text('changed')
    elif damage=='fixture':fixture.write_text('changed')
    with pytest.raises(ValueError):adapter.verify_lock(lock)


def capture_case(tmp_path,arm='cf1'):
    full=chain_case(2);source=replace_case_without_link(full)
    value=task(arm)
    native=tmp_path/'library-id';native.write_text('hash only')
    lock={'tasks':worker.task_matrix(),'cases':[{'base_id':50999,'trips':80,
        'identity':full.identity(),'restricted_identity':source.identity(),
        'movement_ids':[m.id for m in full.movements],
        'restricted_movement_ids':[m.id for m in source.movements]}],
        'native_library':{'path':str(native),'sha256':q.sha(native)}}
    q.write_new(tmp_path/'lock.json',lock)
    q.write_new(tmp_path/'attempt.json',{'task':value,'lock_sha256':q.sha(tmp_path/'lock.json'),
                                      'parent_monotonic':100.,'deadline':160.})
    (tmp_path/'stdout.log').write_text('')
    return full,source,lock,value


def replace_case_without_link(full):
    from dataclasses import replace
    return replace(full,movements=full.movements[:-1])


def capture_raw(case,*,fixed=True):
    variables=[{'index':i,'name':'x'+str(i),'type':'B','lower':{'value':1. if fixed else 0.},
                'upper':{'value':1.},'primal':{'value':1.}} for i in range(len(case.movements))]
    variables.append({'index':len(variables),'name':'continuous','type':'C',
                      'lower':{'value':0.},'upper':{'value':100.},'primal':{'value':0.}})
    return {'case_identity':case.identity(),'formulation':worker.pf.FORMULATION,
            'native_matrix':worker.pf.NATIVE_MATRIX,'variables':variables,
            'mapping':{'movement_ids':[m.id for m in case.movements],
                       'movement_selection':list(range(len(case.movements)))}}


def capture_reference(folder,lock,value,case,*,phase='cf1',sequence=1,raw=None,identity_task=None):
    identity_task=value if identity_task is None else identity_task
    metadata={'task_id':identity_task['id'],'task_sha256':q.stable(identity_task),
        'lock_sha256':q.sha(folder/'lock.json'),'attempt_sha256':q.sha(folder/'attempt.json'),
        'anchor':100.,'phase':phase,'case_identity':case.identity(),'sequence':sequence,'round':0,
        'capture_started_monotonic':101.}
    ref=worker.persist_capture(folder,metadata,capture_raw(case) if raw is None else raw)
    return {**ref,'capture_finished_monotonic':101.1}


def test_capture_sequence_preserves_complete_payloads_across_repair_round_zero(tmp_path):
    full,source,lock,value=capture_case(tmp_path)
    raw=capture_raw(full);raw['additional_diagnostic']={'all_values':[1.,2.,3.]}
    first=capture_reference(tmp_path,lock,value,full,raw=raw)
    second=capture_reference(tmp_path,lock,value,full,phase='full',sequence=2)
    assert first['path']!=second['path'] and first['round']==second['round']==0
    assert q.read(tmp_path/first['path'])['capture']==raw
    assert worker.verify_capture_reference(tmp_path,lock,value,100.,first)['all_mapped_binary_fixed']
    count=worker.audit_captures(tmp_path,{'capture_references':[first,second]},
        [{**first,'stage':'cf1'}],lock=lock,task=value,anchor=100.)
    assert count==2  # A late persisted capture remains audited even if it was never forwarded.


@pytest.mark.parametrize('damage',['bytes','foreign_task','offset','path','wrong_stage','hidden_integer','unfixed_cf1'])
def test_capture_reference_integrity_context_and_fixed_scope_fail_closed(tmp_path,damage):
    full,source,lock,value=capture_case(tmp_path)
    raw=capture_raw(full,fixed=damage!='unfixed_cf1')
    if damage=='hidden_integer':raw['variables'][-1]['type']='I'
    ref=capture_reference(tmp_path,lock,value,full,raw=raw,
                          identity_task=task('recovery') if damage=='foreign_task' else None)
    if damage=='bytes':(tmp_path/ref['path']).write_text('modified')
    elif damage=='offset':ref['offset_bytes']=1
    elif damage=='path':ref['path']='../other.json'
    if damage=='wrong_stage':
        with pytest.raises(ValueError):worker.audit_captures(tmp_path,{'capture_references':[ref]},
            [{**ref,'stage':'full'}],lock=lock,task=value,anchor=100.)
    else:
        with pytest.raises(ValueError):worker.verify_capture_reference(tmp_path,lock,value,100.,ref)


def test_raw_capture_or_duplicate_registration_cannot_pass_final_audit(tmp_path):
    full,source,lock,value=capture_case(tmp_path)
    ref=capture_reference(tmp_path,lock,value,full)
    with pytest.raises(ValueError):worker.audit_captures(tmp_path,{'capture_references':[ref,ref]},[],lock=lock,task=value,anchor=100.)
    with pytest.raises(ValueError):worker.audit_captures(tmp_path,{'capture_references':[ref]},
        [{'event':'native_incumbent','variables':[]}],lock=lock,task=value,anchor=100.)


class FakeVar:
    def __init__(self,index,kind='C',lower=0.,upper=100.):
        self.idx,self.var_type,self.lb,self.ub=index,kind,lower,upper


@pytest.fixture
def instrument(tmp_path,monkeypatch):
    full,source,lock,value=capture_case(tmp_path,'recovery')
    clock=Clock(101.);builds=[];calls=[]
    runtime={'requested':'GRB','model_solver_name':'GRB','solver_module':'mip.gurobi',
        'solver_class':'SolverGurobi','native_library_path':lock['native_library']['path'],
        'native_library_sha256':lock['native_library']['sha256']}
    def build(case,*args,**kwargs):
        x=[FakeVar(i,'B',0.,1.) for i in range(len(case.movements))]
        continuous=FakeVar(len(x))
        row=SimpleNamespace(idx=0,name='physical',expr=SimpleNamespace(sense='=',const=0.,expr={continuous:1.}))
        built={'x':x,'model':SimpleNamespace(vars=x+[continuous],constrs=[row],start=None),
               'backend_runtime':deepcopy(runtime),'physical_identity':case.identity(),
               'compiled':{'identity':case.identity()}}
        builds.append(built);return built
    def optimize(*args):calls.append(True);return {'status':'FEASIBLE','incumbent':1.,'lower_bound':0.}
    def capture(case,built):
        raw=capture_raw(case,fixed=False)
        for row,var in zip(raw['variables'],built['model'].vars):
            row['lower']['value'],row['upper']['value']=var.lb,var.ub
        return raw
    monkeypatch.setattr(worker.pf,'build_feasible_model',build)
    monkeypatch.setattr(worker.pf,'_optimize_once',optimize)
    monkeypatch.setattr(worker.pf,'capture_incumbent',capture)
    monkeypatch.setattr(worker,'_offset',lambda:0)
    return SimpleNamespace(full=full,source=source,lock=lock,task=value,folder=tmp_path,
                           clock=clock,builds=builds,calls=calls,runtime=runtime)


@pytest.mark.parametrize('damage',[None,'row','bounds','continuous_hint'])
def test_actual_binary_hint_mapping_and_physical_rows_survive_setter(instrument,monkeypatch,damage):
    h=instrument;attach0=worker.pf._attach_pricing_start
    def attach(case,built,selected):
        mapping=attach0(case,built,selected)
        if damage=='row':built['model'].constrs[0].expr.const=1.
        elif damage=='bounds':built['x'][0].ub=0.
        elif damage=='continuous_hint':built['model'].start.append((built['model'].vars[-1],0.))
        return mapping
    monkeypatch.setattr(worker.pf,'_attach_pricing_start',attach)
    original=(worker.pf.build_feasible_model,worker.pf._attach_pricing_start,
              worker.pf._optimize_once,worker.pf.capture_incumbent)
    (h.folder/'fallback.json').write_text('durable witness marker')
    with worker.instrument_native60(h.lock,h.task,h.folder,anchor=100.,full_case=h.full,
            source_case=h.source,clock=h.clock) as state:
        with worker.native_phase(state,'full',144.):
            built=worker.pf.build_feasible_model(h.full,'GRB')
            if damage:
                with pytest.raises(ValueError):worker.pf._attach_pricing_start(h.full,built,{'outA','AB','inB'})
            else:
                worker.pf._attach_pricing_start(h.full,built,{'outA','AB','inB'})
                assert state['submission']['continuous_submitted']==0
                assert state['submission']['physical_rows_unchanged']
                assert len(built['model'].start)==len(h.full.movements)
                assert not state['submissions']  # Setter alone is not native processing.
    assert (worker.pf.build_feasible_model,worker.pf._attach_pricing_start,
            worker.pf._optimize_once,worker.pf.capture_incumbent)==original


def test_native_library_mismatch_rejected_before_optimizer(instrument):
    h=instrument;h.runtime['native_library_sha256']='wrong-library'
    with worker.instrument_native60(h.lock,h.task,h.folder,anchor=100.,full_case=h.full,
            source_case=h.source,clock=h.clock):
        with pytest.raises(ValueError):worker.pf.build_feasible_model(h.source,'GRB')
    assert not h.calls


@pytest.mark.parametrize('damage',[None,'cutoff','upper','observed','lock','case','task_sha'])
def test_sixty_second_prebuild_guard_requires_exact_scoped_single_use_evidence(instrument,damage):
    h=instrument;h.clock.now=120.
    with worker.instrument_native60(h.lock,h.task,h.folder,anchor=100.,full_case=h.full,
            source_case=h.source,clock=h.clock) as state:
        with pytest.raises(worker.IntegerGateClosed60) as error:worker.pf.build_feasible_model(h.source,'GRB')
        evidence=state['pending_gate']['evidence']
        if damage=='cutoff':evidence['integer_cutoff']=124.
        elif damage=='upper':evidence['integer_upper_cutoff']=120.
        elif damage=='observed':evidence['observed_monotonic']=float('nan')
        elif damage=='lock':evidence['lock_sha256']='other'
        elif damage=='case':evidence['case_identity']=h.full.identity()
        elif damage=='task_sha':evidence['task_sha256']='other'
        event={'event':'native_search_failed','stage':'model_build','round':0,
               'error_type':worker.IntegerGateClosed60.__name__,'error':str(error.value)}
        worker.record_event(h.folder,state,event)
        assert bool(state['expected_budget_stops']) is (damage is None)
        assert bool(state['engineering_events']) is (damage is not None)
        if damage is None:
            worker.record_event(h.folder,state,event)
            assert state['engineering_events']  # A consumed token cannot excuse another failure.
    assert not h.builds and not h.calls


def test_failed_native_sink_closes_further_build_dispatch(instrument,monkeypatch):
    h=instrument
    def fail(*args):raise OSError('synthetic evidence sink failure')
    monkeypatch.setattr(q,'native_append',fail)
    with worker.instrument_native60(h.lock,h.task,h.folder,anchor=100.,full_case=h.full,
            source_case=h.source,clock=h.clock) as state:
        with pytest.raises(OSError):worker.pf.build_feasible_model(h.source,'GRB')
        assert state['sink_failure']
        with pytest.raises(ValueError):worker.pf.build_feasible_model(h.source,'GRB')
    assert len(h.builds)==1 and not h.calls


@pytest.mark.parametrize('persist_ok',[True,False])
def test_real_planner_capture_hook_persists_before_candidate_or_fails_closed(instrument,monkeypatch,persist_ok):
    h=instrument;candidate=[]
    monkeypatch.setattr(worker.time,'monotonic',h.clock)
    monkeypatch.setattr(worker.pf,'attach_objective',lambda *args:None)
    def admit(case,*args,**kwargs):
        refs=state['capture_references']
        assert refs and (h.folder/refs[0]['path']).is_file()
        worker.verify_capture_reference(h.folder,h.lock,h.task,100.,refs[0])
        candidate.append(True)
        raise ValueError('Stop after proving capture precedes candidate processing')
    monkeypatch.setattr(worker.pf,'_candidate',admit)
    if not persist_ok:
        def fail(*args):raise OSError('capture fsync failed')
        monkeypatch.setattr(worker,'persist_capture',fail)
    with worker.instrument_native60(h.lock,h.task,h.folder,anchor=100.,full_case=h.full,
            source_case=h.source,clock=h.clock) as state:
        worker.pf.solve_planner(h.source,[1.],[0.],worker.pf.Budget(backend='GRB',max_rounds=1),
            deadline=126.,record=lambda event:worker.record_event(h.folder,state,event))
        assert bool(candidate) is persist_ok
        assert bool(state['capture_references']) is persist_ok
        assert bool(state['sink_failure']) is (not persist_ok)


def test_worker_storage_requires_observed_start_and_ack_follows_terminal_fsync(tmp_path,monkeypatch):
    full,source,lock,value=capture_case(tmp_path,'recovery');clock=Clock(159.);acks=[]
    state={'capture_references':[],'submissions':[],'engineering_events':[],
           'sink_failure':None,'cf1_fixed_inventories':0}
    storage=worker.WorkerStorage(tmp_path,task=value,lock=lock,anchor=100.,state=state,ack_fd=999,clock=clock)
    monkeypatch.setattr(worker,'_offset',lambda:0)
    witness={'plan':{'symbolic':'not a physical-performance claim'},'replay':{'replay_ok':True},
             'true_bill':10.,'true_bill_exact':'10'}
    result={'status':'feasible','fallback':witness,'selected':witness,'global_lower_bound':None,
        'bound_provenance':[],'start_proposal':{'proposed':True},'failures':[],
        'events':[{'event':'durable_fallback_admitted','stage':'prefix_lift'}]}
    original_write=storage._write
    def delayed_write(name,value):
        artifact=original_write(name,value)
        if name=='worker-outcome.json':clock.now+=2.
        return artifact
    monkeypatch.setattr(storage,'_write',delayed_write)
    receipt=storage.materialize(result,schedule=worker.pipeline.Schedule60(100.,160.),clock=clock)
    assert not state['path_qualification']['passed'] and not state['path_qualification']['native_processing_observed']
    assert any(row.get('stage')=='preflight_path' for row in result['failures'])
    def acknowledge(fd,raw):acks.append(raw);return len(raw)
    monkeypatch.setattr(worker.os,'write',acknowledge)
    assert not acks
    ack=storage.finalize({'result':result,'completion':receipt,'censored':False})
    assert ack['worker_outcome_sha256']==q.sha(tmp_path/'worker-outcome.json')
    assert ack['completion_monotonic']==161. and len(acks)==1
    validated=adapter.completion_endpoint(tmp_path,value,storage.locksha,100.,acknowledgment=ack)
    assert validated['endpoint_censored'] and validated['completion_issue'] is None
    with pytest.raises(ValueError):storage.finalize({'result':result})
    assert len(acks)==1


def test_worker_clock_failure_is_sticky_after_raw_clock_recovers():
    raw=Clock(101.);clock=worker.WorkerClock(100.,raw=raw)
    assert clock()==101.
    raw.now=float('nan')
    with pytest.raises(ValueError):clock()
    raw.now=102.
    with pytest.raises(ValueError):clock()
