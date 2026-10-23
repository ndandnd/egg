"""Bounded operational tests: temporary receipts, fake clocks/models, no solver."""
import builtins
from copy import deepcopy
import json
import os
from types import SimpleNamespace
import sys

import pytest

# Install before importing the runner, so collection is solver-free too.
_real_import = builtins.__import__
def _guarded_import(name, *args, **kwargs):
    if name.split('.')[0] in {'mip', 'gurobipy'}:
        raise AssertionError('Native backend forbidden in runner checks')
    return _real_import(name, *args, **kwargs)

builtins.__import__ = _guarded_import
try:
    from experiments import recovery_qualification as q
finally:
    builtins.__import__ = _real_import


@pytest.fixture(autouse=True)
def no_native(monkeypatch):
    monkeypatch.setattr(builtins, '__import__', _guarded_import)


def dump(path, value):
    path.write_text(json.dumps(value))


def completion(folder, end=112., ack_end=112.1):
    task = {'id':'task', 'arm':'recovery'}
    dump(folder/'result.json', {'task':task, 'lock_sha256':'lock'})
    marker = {'task':task, 'lock_sha256':'lock', 'parent_monotonic':100.,
              'deadline':130., 'finished_monotonic':end, 'elapsed_s':end-100.,
              'result_sha256':q.sha(folder/'result.json'), 'censored':False}
    dump(folder/'completion.json', marker)
    ack = {'task_id':'task', 'lock_sha256':'lock', 'parent_monotonic':100.,
           'completion_monotonic':ack_end, 'result_sha256':marker['result_sha256'],
           'completion_sha256':q.sha(folder/'completion.json')}
    return task, ack


def test_backend_import_guard():
    with pytest.raises(AssertionError, match='Native backend'):
        __import__('mip')
    with pytest.raises(AssertionError, match='Native backend'):
        __import__('gurobipy')


def test_exclusive_attempt_write(tmp_path):
    path = tmp_path/'attempt.json'
    q.write_new(path, {'anchor':1})
    with pytest.raises(FileExistsError):
        q.write_new(path, {'anchor':2})
    assert q.read(path) == {'anchor':1}


def test_ledger_sequence_and_hash_tampering(tmp_path):
    path = tmp_path/'ledger.jsonl'
    q.append_ledger(path, {'event':'carry_forward','charged_cpu_s':123.})
    q.append_ledger(path, {'event':'supervisor_cpu','charged_cpu_s':2.})
    events = q.ledger_events(path)
    assert events[1]['previous'] == events[0]['sha256']
    path.write_text(path.read_text().replace('123.0', '124.0'))
    with pytest.raises(ValueError, match='hash'):
        q.ledger_events(path)


def test_task_identity_is_order_independent_and_complete():
    a = q.task_matrix(list(q.DESIGN))
    assert a == q.task_matrix(list(reversed(q.DESIGN)))
    assert len({t['id'] for t in a}) == 8
    assert all(t['seconds']==30. and t['seed']==17 for t in a)
    assert [t['fault'] for t in a if t['arm']=='start_fault'] == ['start_setter_exception']*2


def test_changed_source_hash_rejected(tmp_path):
    path = tmp_path/'source.py'
    path.write_text('first')
    inventory = {str(path):q.sha(path)}
    path.write_text('changed')
    with pytest.raises(ValueError, match='Frozen file changed'):
        q.verify_hashes(inventory)


def test_valid_completion_uses_parent_anchor_not_cleanup(tmp_path):
    task, ack = completion(tmp_path)
    assert q.completion_endpoint(tmp_path,task,'lock',100.,acknowledgment=ack) == {
        'endpoint_wall_s':12., 'endpoint_censored':False, 'completion_issue':None}


@pytest.mark.parametrize('field,value', [('task_id','other'),('parent_monotonic',99.),
    ('completion_monotonic',111.),('completion_sha256','bad'),('result_sha256','bad')])
def test_malformed_ack_censors(tmp_path, field, value):
    task, ack = completion(tmp_path)
    ack[field] = value
    outcome = q.completion_endpoint(tmp_path,task,'lock',100.,acknowledgment=ack)
    assert outcome['endpoint_censored'] and outcome['completion_issue']


def test_late_post_fsync_ack_censors_timely_result(tmp_path):
    task, ack = completion(tmp_path,ack_end=130.001)
    outcome = q.completion_endpoint(tmp_path,task,'lock',100.,acknowledgment=ack)
    assert outcome['endpoint_wall_s']==12. and outcome['endpoint_censored']


def test_missing_completion_and_mutated_result_censor(tmp_path):
    task, ack = completion(tmp_path)
    dump(tmp_path/'result.json', {'task':task,'lock_sha256':'lock','changed':True})
    assert q.completion_endpoint(tmp_path,task,'lock',100.,acknowledgment=ack)['completion_issue']
    (tmp_path/'completion.json').unlink()
    assert q.completion_endpoint(tmp_path,task,'lock',100.,acknowledgment=None)['endpoint_censored']


def test_ack_pipe_partial_and_multiple_records():
    r, w = os.pipe()
    os.set_blocking(r,False)
    item = {'ack_fd':r,'ack_bytes':b'','acknowledgment':None}
    try:
        q.receive_ack(item)
        os.write(w,b'{"ok":')
        q.receive_ack(item)
        assert item['acknowledgment'] is None
        os.write(w,b'true}\n')
        q.receive_ack(item)
        assert item['acknowledgment']=={'ok':True}
        os.write(w,b'{}\n')
        with pytest.raises(ValueError,match='Multiple/malformed'):
            q.receive_ack(item)
    finally:
        os.close(r)
        os.close(w)


def test_oversized_ack_rejected():
    r,w = os.pipe()
    try:
        os.write(w,b'x'*4097)
        with pytest.raises(ValueError,match='Oversized'):
            q.receive_ack({'ack_fd':r,'ack_bytes':b'','acknowledgment':None})
    finally:
        os.close(r)
        os.close(w)


def monitor_item():
    return {'proc':SimpleNamespace(pid=10),'owned_pids':{10},'owned_pgids':{10},
            'last_sample':None,'pressure_since':None,'peak_rss':0,'cpu':0.}


def table(rss=100, cpu=1., group=10):
    return {10:{'ppid':1,'pgid':10,'rss':rss,'cpu':cpu},
            11:{'ppid':10,'pgid':group,'rss':100,'cpu':2.}}


def test_monitor_aggregates_descendants_and_retains_cpu_peak():
    item = monitor_item()
    assert q.resource_step(item,table(),90.,1.) is None
    assert item['cpu']==3. and item['peak_rss']==200 and item['owned_pids']=={10,11}
    q.resource_step(item,table(cpu=0),90.,1.2)
    assert item['cpu']==3.


@pytest.mark.parametrize('free', [float('nan'),-1.,101.,True])
def test_monitor_invalid_pressure_fails_closed(free):
    with pytest.raises(ValueError):
        q.resource_step(monitor_item(),table(),free,1.)


def test_monitor_gap_rss_and_escaped_group_stop():
    item = monitor_item()
    q.resource_step(item,table(),90.,1.)
    assert q.resource_step(item,table(),90.,1.251)=='monitor_sampling_gap'
    assert q.resource_step(monitor_item(),table(rss=q.RSS_LIMIT),90.,1.)=='worker_rss_limit'
    item = monitor_item()
    assert q.resource_step(item,table(group=11),90.,1.)=='unexpected_descendant_process_group'
    assert 11 in item['owned_pgids']


def test_sustained_pressure_and_recovery():
    item = monitor_item()
    for i in range(21):
        reason = q.resource_step(item,table(),9.,i*.25)
    assert reason=='system_memory_pressure'
    assert q.resource_step(item,table(),10.,5.25) is None
    assert item['pressure_since'] is None


def resumed(tmp_path):
    task = {'id':'task','arm':'recovery'}
    lock = {'tasks':[task],'carried_charge_s':118.2,'freeze_charge_s':2.}
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'carry_forward','charged_cpu_s':118.2,'freeze_charge_s':2.})
    folder = tmp_path/'task'
    folder.mkdir()
    q.write_new(folder/'attempt.json',{'task':task,'lock_sha256':'lock','parent_monotonic':100.})
    receipt = {'task':task,'lock_sha256':'lock','parent_monotonic':100.,'terminal':True,
               'charged_cpu_s':7.,'group_absent':True,'returncode':1,'failure':'test failure',
               'artifacts':{'attempt.json':q.sha(folder/'attempt.json')}}
    q.write_new(folder/'supervisor.json',receipt)
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'launch','task_id':'task'})
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'finish','task_id':'task','receipt_sha256':q.sha(folder/'supervisor.json')})
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'supervisor_cpu','charged_cpu_s':.5})
    return lock, folder


def test_resume_terminal_failure_is_completed_and_charge_carries(tmp_path):
    lock, folder = resumed(tmp_path)
    completed, charge = q.resume_state(tmp_path,lock,'lock')
    assert completed['task']['failure']=='test failure'
    assert charge==pytest.approx(127.7)


@pytest.mark.parametrize('damage', ['missing_receipt','artifact','lock','unknown_attempt'])
def test_resume_corruption_blocks_retry(tmp_path,damage):
    lock,folder = resumed(tmp_path)
    if damage=='missing_receipt':
        (folder/'supervisor.json').unlink()
    elif damage=='artifact':
        (folder/'attempt.json').write_text('{}')
    elif damage=='lock':
        lock['tasks'][0]['arm']='cold'
    else:
        (tmp_path/'unknown').mkdir()
    with pytest.raises((ValueError,KeyError,OSError)):
        q.resume_state(tmp_path,lock,'lock')


def test_native_log_classification_requires_processing_and_span():
    raw = b'noise\nLoaded user MIP start with objective 7\n'
    sub = {'inventory_sha256':'inventory','log_start':0,'log_end':len(raw)}
    evidence = q.start_evidence(raw,[sub])
    assert evidence['classified'][0]['status']=='accepted'
    assert evidence['classified'][0]['processed']
    outside = q.start_evidence(raw,[{**sub,'log_end':3}])
    assert outside['classified'][0]['status']=='unknown'
    assert not outside['classified'][0]['processed']
    assert outside['unattributed_log_matches']


@pytest.mark.parametrize('raw,status', [(b'mipstart values could not be used','rejected'),
    (b'User MIP start did not produce a new incumbent','unknown'),
    (b'Loaded user MIP start with objective 1\nmipstart values could not be used','unknown')])
def test_native_log_ambiguous_and_rejected(raw,status):
    result = q.start_evidence(raw,[{'inventory_sha256':'x','log_start':0,'log_end':len(raw)}])
    assert result['classified'][0]['status']==status
    assert result['classified'][0]['processed']


def test_analyze_serializes_owner_and_accounts_failure(tmp_path,monkeypatch):
    lock = tmp_path/'lock.json'
    dump(lock,{})
    args = SimpleNamespace(lock=str(lock),output=str(tmp_path),report=str(tmp_path/'report.json'))
    owner = tmp_path/'.supervisor-owner'
    q.write_new(owner, {'pid':123})
    with pytest.raises(FileExistsError):
        q.analyze(args)
    assert q.read(owner)=={'pid':123}
    owner.unlink()
    def fail(args):
        assert owner.exists()
        raise ValueError('report failure')
    monkeypatch.setattr(q,'_analyze',fail)
    with pytest.raises(ValueError,match='report failure'):
        q.analyze(args)
    assert not owner.exists()
    assert q.ledger_events(tmp_path/'ledger.jsonl')[-1]['phase']=='analyze'


def test_run_budget_gate_creates_no_attempt(tmp_path,monkeypatch):
    lockpath = tmp_path/'lock.json'
    lock = {'tasks':[{'id':'never'}],'carried_charge_s':700.,'freeze_charge_s':0.}
    dump(lockpath,lock)
    output = tmp_path/'output'
    monkeypatch.setattr(q,'verify_lock',lambda *a,**k:None)
    monkeypatch.setattr(q,'freeze_accounting',lambda lock,*a:lock)
    monkeypatch.setattr(q,'launch',lambda *a:pytest.fail('budget gate dispatched worker'))
    outcome = q.run(SimpleNamespace(lock=str(lockpath),output=str(output),freeze_receipt=str(lockpath)))
    assert outcome['halted']=='cumulative_dispatch_budget' and outcome['attempted']==0
    assert not (output/'.supervisor-owner').exists()


def test_run_monitor_exception_prevents_dispatch(tmp_path,monkeypatch):
    lockpath = tmp_path/'lock.json'
    dump(lockpath,{'tasks':[{'id':'never'}],'carried_charge_s':120.,'freeze_charge_s':0.})
    monkeypatch.setattr(q,'verify_lock',lambda *a,**k:None)
    monkeypatch.setattr(q,'freeze_accounting',lambda lock,*a:lock)
    monkeypatch.setattr(q,'snapshot',lambda:(_ for _ in ()).throw(RuntimeError('monitor unavailable')))
    monkeypatch.setattr(q,'launch',lambda *a:pytest.fail('unhealthy monitor dispatched worker'))
    with pytest.raises(RuntimeError,match='monitor unavailable'):
        q.run(SimpleNamespace(lock=str(lockpath),output=str(tmp_path/'output'),freeze_receipt=str(lockpath)))


def test_native_inventory_reads_actual_model_and_restores_hooks(tmp_path,monkeypatch):
    # Importing planner definitions is permitted; constructing native models is not.
    from egglab import native_pathflow as pf
    x = [SimpleNamespace(idx=i,lb=0.,ub=1.,var_type='B') for i in range(2)]
    continuous = SimpleNamespace(idx=2,lb=0.,ub=10.,var_type='C')
    model = SimpleNamespace(vars=x+[continuous],constrs=[object()],start=[])
    built = {'model':model,'x':x,'backend_runtime':{
        'requested':'FAKE','native_library_sha256':'library'}}
    case = SimpleNamespace(movements=[SimpleNamespace(id='b'),SimpleNamespace(id='a')])
    def attach(case,built,selected):
        built['model'].start=[(var,int(mode.id in selected)) for mode,var in zip(case.movements,built['x'])]
        return {'selected':list(selected)}
    monkeypatch.setattr(pf,'build_feasible_model',lambda *a,**k:built)
    monkeypatch.setattr(pf,'_attach_pricing_start',attach)
    original = pf._attach_pricing_start
    with q.instrument_native({'backend':'FAKE','native_library':{'sha256':'library'}},
                             {'arm':'recovery'},tmp_path) as state:
        assert pf.build_feasible_model() is built
        pf._attach_pricing_start(case,built,{'a'})
        inventory = state['submission']
        assert [row['movement_id'] for row in inventory['inventory']]==['b','a']
        assert [row['value'] for row in inventory['inventory']]==[0,1]
        assert inventory['continuous_unset']==1 and inventory['continuous_submitted']==0
        assert inventory['bounds_constraints_unchanged']
    assert pf._attach_pricing_start is original


def test_start_fault_requires_durable_fallback(tmp_path):
    from egglab import native_pathflow as pf
    with q.instrument_native({}, {'arm':'start_fault'},tmp_path) as state:
        with pytest.raises(ValueError,match='durable fallback'):
            pf._attach_pricing_start(None,None,set())
        dump(tmp_path/'fallback.json',{'witness':'saved'})
        with pytest.raises(RuntimeError,match='prospectively injected'):
            pf._attach_pricing_start(None,None,set())
        assert state['fault_exercised']


def test_finish_propagates_worker_failure_and_charges_missing_cpu(tmp_path,monkeypatch):
    task,ack = completion(tmp_path)
    result = q.read(tmp_path/'result.json')
    result.update(status='worker_failure',failures=[{'error':'injected'}])
    dump(tmp_path/'result.json',result)
    (tmp_path/'stdout.log').write_text('')
    r,w = os.pipe()
    os.close(w)
    proc = SimpleNamespace(pid=10,returncode=1)
    item = {'proc':proc,'folder':tmp_path,'task':task,'anchor':100.,'cpu':2.,
            'peak_rss':20,'owned_pgids':{10},'ack_fd':r,'ack_bytes':b'',
            'acknowledgment':ack}
    monkeypatch.setattr(q,'stop_owned',lambda *a:{'group_absent':True,'owned_pgids':[10]})
    monkeypatch.setattr(q.time,'monotonic',lambda:135.)
    receipt = q.finish(item,'lock',tmp_path,None)
    assert receipt['charged_cpu_s']==35.
    assert receipt['worker_failure'] and receipt['endpoint_censored']
    assert receipt['terminal'] and q.read(tmp_path/'supervisor.json')==receipt


def test_run_terminal_failure_skips_without_retry(tmp_path,monkeypatch):
    lockpath = tmp_path/'lock.json'
    dump(lockpath,{'tasks':[{'id':'failed'},{'id':'next'}],
                   'carried_charge_s':120.,'freeze_charge_s':0.})
    monkeypatch.setattr(q,'verify_lock',lambda *a,**k:None)
    monkeypatch.setattr(q,'freeze_accounting',lambda lock,*a:lock)
    monkeypatch.setattr(q,'resume_state',lambda *a:({'failed':{
        'failure':'prior failure','returncode':1,'worker_failure':True,'endpoint_censored':True}},125.))
    monkeypatch.setattr(q,'launch',lambda *a:pytest.fail('terminal failure retried or dispatch continued'))
    result = q.run(SimpleNamespace(lock=str(lockpath),output=str(tmp_path/'output'),freeze_receipt=str(lockpath)))
    assert result['halted']=='completed_failure_stops_dispatch'
    assert result['attempted']==0


def test_real_owned_group_cleanup_and_parent_watchdog(tmp_path,monkeypatch):
    """Only real process test; existing bounded helper imports no native backend."""
    import signal
    from pathlib import Path
    campaign = q.campaign
    original_popen = campaign.subprocess.Popen
    captured = []
    # The outer check supervisor owns this durable registry for emergency cleanup.
    registry = Path(os.environ['EGG_CHECK_PGID_REGISTRY'])

    def registered_popen(*args, **kwargs):
        proc = original_popen(*args, **kwargs)
        is_group = kwargs.get('start_new_session') is True
        captured.append((proc,is_group))
        if is_group:
            # Complete before returning the process to the helper, which may then
            # inject actual parent death. No intervening wait or handshake.
            with registry.open('a') as stream:
                stream.write(json.dumps({'pgid':proc.pid})+'\n')
                stream.flush()
                os.fsync(stream.fileno())
        return proc

    monkeypatch.setattr(campaign.subprocess,'Popen',registered_popen)
    try:
        campaign.mock_group_tests(tmp_path)
        assert len([proc for proc,is_group in captured if is_group])==2
        records = [json.loads(line) for line in registry.read_text().splitlines()]
        assert all({'pgid':proc.pid} in records for proc,is_group in captured if is_group)
    finally:
        # Kill groups even when their leader exited before a helper assertion.
        for proc,is_group in reversed(captured):
            if is_group:
                try:
                    os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif proc.poll() is None:
                proc.kill()
        # Signal every owned process before any bounded reap can fail.
        errors = []
        for proc,_ in reversed(captured):
            try:
                proc.wait(timeout=1.)
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise AssertionError('Owned process cleanup failed') from errors[0]
