"""Deterministic supervision repair checks; no native backend or real subprocess."""
import builtins
import json
import subprocess
from types import SimpleNamespace

import pytest

_original_import = builtins.__import__
def _guarded_import(name,*args,**kwargs):
    if name.split('.')[0] in {'mip','gurobipy'}:
        raise AssertionError('Native backend forbidden in supervision repair checks')
    return _original_import(name,*args,**kwargs)

builtins.__import__ = _guarded_import
try:
    from experiments import recovery_qualification as q
finally:
    builtins.__import__ = _original_import


@pytest.fixture(autouse=True)
def forbid_native(monkeypatch):
    original = builtins.__import__
    def guarded(name,*args,**kwargs):
        if name.split('.')[0] in {'mip','gurobipy'}:
            raise AssertionError('Native backend forbidden in supervision repair checks')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)


class Clock:
    def __init__(self,now=100.):
        self.now=now
    def __call__(self):
        return self.now
    def sleep(self,seconds):
        self.now += seconds


def test_monitor_sample_shares_one_absolute_deadline(monkeypatch):
    monkeypatch.setattr(q.time,'monotonic',lambda:100.)
    calls=[]
    monkeypatch.setattr(q,'snapshot',lambda deadline=None:(calls.append(('ps',deadline)) or {'tree':'sample'}))
    monkeypatch.setattr(q,'memory_state',lambda deadline=None:(calls.append(('pressure',deadline)) or 75.))
    table,free=q.monitor_sample(100.2)
    assert table=={'tree':'sample'} and free==75.
    assert calls==[('ps',100.2),('pressure',100.2)]


def test_monitor_timeout_retains_command_deadline_and_context(monkeypatch):
    clock=Clock()
    monkeypatch.setattr(q.time,'monotonic',clock)
    def timed_out(command,**kwargs):
        raise subprocess.TimeoutExpired(command,kwargs['timeout'])
    monkeypatch.setattr(q.subprocess,'run',timed_out)
    with pytest.raises(q.MonitorError) as caught:
        q.snapshot(deadline=100.1)
    diagnostic=caught.value.diagnostic
    assert diagnostic['command'][0]=='ps'
    assert diagnostic['sample_deadline']==100.1
    assert diagnostic['error_type']=='TimeoutExpired'
    assert diagnostic['context']
    assert 0.<diagnostic['timeout_s']<=.1


def test_monitor_second_command_cannot_acquire_fresh_budget(monkeypatch):
    clock=Clock()
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(q.platform,'system',lambda:'Darwin')
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs['timeout']))
        if command[0]=='ps':
            clock.now += .09
            return SimpleNamespace(stdout=f'{q.os.getpid()} 1 {q.os.getpid()} 1 0:00.01\n')
        return SimpleNamespace(stdout='System-wide memory free percentage: 75%')
    monkeypatch.setattr(q.subprocess,'run',run)
    q.monitor_sample(100.1)
    assert len(calls)==2
    assert calls[1][1] <= .011


def test_permission_denied_group_probe_stays_unknown(monkeypatch):
    def denied(*args):
        raise PermissionError('ownership unavailable')
    monkeypatch.setattr(q.os,'killpg',denied)
    assert q.group_probe(123)['state']=='unknown'
    assert not q.group_absent(123)
    monkeypatch.setattr(q.os,'killpg',lambda *args:(_ for _ in ()).throw(ProcessLookupError()))
    assert q.group_probe(123)['state']=='absent'
    assert q.group_absent(123)


def test_unresolved_cleanup_is_bounded_and_never_reports_absent(monkeypatch):
    clock=Clock()
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(q.time,'sleep',clock.sleep)
    monkeypatch.setattr(q.os,'killpg',lambda *args:(_ for _ in ()).throw(PermissionError('denied')))
    proc=SimpleNamespace(pid=123,returncode=None,poll=lambda:None)
    proc.wait=lambda timeout=None:(_ for _ in ()).throw(subprocess.TimeoutExpired(['fake-worker'],timeout))
    receipt=q.stop_owned(proc,{123})
    assert not receipt['group_absent']
    assert receipt['owned_pgids']==[123]
    assert receipt['probe_diagnostics'] and receipt['cleanup_errors']
    assert clock.now-100. <= 3.


def fake_item(tmp_path):
    (tmp_path/'stdout.log').write_text('')
    (tmp_path/'result.json').write_text(json.dumps({'status':'worker_failure','failures':[{'stage':'fake'}]}))
    return {'proc':SimpleNamespace(pid=123,returncode=-9),'folder':tmp_path,
            'task':{'id':'task'},'anchor':100.,'cpu':1.,'peak_rss':20,
            'owned_pgids':{123},'last_sample':None,'ack_fd':987,'ack_bytes':b'','acknowledgment':None}


def test_finish_is_idempotent_for_ack_receipt_and_ledger(tmp_path,monkeypatch):
    item=fake_item(tmp_path)
    stopped=[];closed=[]
    monkeypatch.setattr(q.time,'monotonic',lambda:105.)
    monkeypatch.setattr(q,'stop_owned',lambda *args:(stopped.append(True) or {
        'group_absent':True,'owned_pgids':[123],'probe_diagnostics':[],'cleanup_errors':[]}))
    monkeypatch.setattr(q,'receive_ack',lambda item:None)
    original_close=q.os.close
    monkeypatch.setattr(q.os,'close',lambda fd:closed.append(fd) if fd==987 else original_close(fd))
    first=q.finish(item,'lock',tmp_path,'monitor_failure:TimeoutExpired')
    second=q.finish(item,'lock',tmp_path,'supervisor_interrupted')
    assert first==second
    assert stopped==[True] and closed==[987]
    assert item['ack_fd'] is None
    assert len([v for v in q.ledger_events(tmp_path/'ledger.jsonl') if v['event']=='finish'])==1
    assert second['failure']=='monitor_failure:TimeoutExpired'


def test_finish_retry_preserves_primary_monitor_failure(tmp_path,monkeypatch):
    item=fake_item(tmp_path)
    item['monitor_failure']={'command':['ps'],'context':'resource_sample','error_type':'TimeoutExpired'}
    stopped=[];closed=[]
    monkeypatch.setattr(q.time,'monotonic',lambda:105.)
    monkeypatch.setattr(q,'stop_owned',lambda *args:(stopped.append(True) or {
        'group_absent':False,'owned_pgids':[123],'probe_diagnostics':[{'state':'unknown'}],
        'cleanup_errors':['permission denied']}))
    monkeypatch.setattr(q,'receive_ack',lambda item:None)
    original_close=q.os.close
    monkeypatch.setattr(q.os,'close',lambda fd:closed.append(fd) if fd==987 else original_close(fd))
    original=q.write_new
    failed=[]
    def one_failure(path,value):
        if path.name=='start-evidence.json' and not failed:
            failed.append(True)
            raise OSError('secondary materialization failure')
        return original(path,value)
    monkeypatch.setattr(q,'write_new',one_failure)
    with pytest.raises(OSError,match='secondary'):
        q.finish(item,'lock',tmp_path,'monitor_failure:TimeoutExpired')
    receipt=q.finish(item,'lock',tmp_path,'supervisor_interrupted')
    assert receipt['failure']=='monitor_failure:TimeoutExpired'
    assert receipt['monitor_failure']['command'][0]=='ps'
    assert receipt['secondary_errors']
    assert not receipt['group_absent']
    assert stopped==[True] and closed==[987]


def test_run_finally_retries_audit_without_replacing_monitor_reason(tmp_path,monkeypatch):
    lockpath=tmp_path/'lock.json'
    task={'id':'fake'}
    lockpath.write_text(json.dumps({'tasks':[task],'carried_charge_s':150.,'freeze_charge_s':0.}))
    output=tmp_path/'output'
    args=SimpleNamespace(lock=str(lockpath),freeze_receipt=str(lockpath),output=str(output))
    monkeypatch.setattr(q,'verify_lock',lambda *a,**kw:None)
    monkeypatch.setattr(q,'freeze_accounting',lambda lock,*a:lock)
    monkeypatch.setattr(q.time,'monotonic',lambda:105.)
    samples=[]
    def sample(*a,**kw):
        samples.append(True)
        if len(samples)>1:
            raise subprocess.TimeoutExpired(['ps','-axo'],.1)
        return ({},100.)
    monkeypatch.setattr(q,'monitor_sample',sample)
    items=[]
    def launch(args,task,output,locksha):
        folder=output/task['id']
        folder.mkdir()
        item=fake_item(folder)
        item['task']=task
        item['proc'].poll=lambda:None
        item['completion_observed']=None
        item['folder'].joinpath('attempt.json').write_text('{}')
        args.active=item
        items.append(item)
        return item
    monkeypatch.setattr(q,'launch',launch)
    stopped=[];closed=[]
    monkeypatch.setattr(q,'stop_owned',lambda *a:(stopped.append(True) or {
        'group_absent':False,'owned_pgids':[123],'probe_diagnostics':[{'state':'unknown'}],
        'cleanup_errors':['permission denied']}))
    monkeypatch.setattr(q,'receive_ack',lambda item:None)
    original_close=q.os.close
    monkeypatch.setattr(q.os,'close',lambda fd:closed.append(fd) if fd==987 else original_close(fd))
    original_write=q.write_new
    failed=[]
    def write(path,value):
        if path.name=='start-evidence.json' and not failed:
            failed.append(True)
            raise OSError('secondary audit write failure')
        return original_write(path,value)
    monkeypatch.setattr(q,'write_new',write)
    with pytest.raises(OSError,match='secondary audit'):
        q.run(args)
    receipt=q.read(output/'fake'/'supervisor.json')
    assert receipt['failure']=='monitor_failure:TimeoutExpired'
    assert receipt['monitor_failure']['command'][0]=='ps'
    assert receipt['secondary_errors']
    assert not receipt['group_absent']
    assert stopped==[True] and closed==[987]
    assert items[0]['ack_fd'] is None
    assert (output/'.supervisor-owner').exists()
    assert q.ledger_events(output/'ledger.jsonl')[-1]['event']=='supervisor_cpu'


def test_scheduler_preserves_monitor_slack_and_outer_deadline():
    tick=100.+q.MONITOR_INTERVAL_S
    deadline=q.monitor_deadline(tick,last_completed=100.01)
    assert q.MONITOR_INTERVAL_S==.05
    assert deadline-tick==pytest.approx(.21)
    assert deadline-tick>.08
    assert q.monitor_deadline(tick,100.01,100.12)==100.12


def test_monitor_child_cpu_query_deltas_reset_and_charge_once(tmp_path,monkeypatch):
    monkeypatch.setattr(q,'_monitor_child_cpu_s',0.)
    monkeypatch.setattr(q.time,'monotonic',lambda:100.)
    readings=iter([10.,10.4,50.,50.2])
    def usage(kind):
        assert kind==q.resource.RUSAGE_CHILDREN
        return SimpleNamespace(ru_utime=next(readings),ru_stime=0.)
    monkeypatch.setattr(q.resource,'getrusage',usage)
    commands=[]
    def command(cmd,**kwargs):
        commands.append(cmd)
        if len(commands)==2:
            raise subprocess.TimeoutExpired(cmd,kwargs['timeout'])
        return SimpleNamespace(stdout='ok')
    monkeypatch.setattr(q.subprocess,'run',command)
    assert q.monitor_command(['fake-ps'],100.2,'first')=='ok'
    with pytest.raises(q.MonitorError):
        q.monitor_command(['fake-pressure'],100.2,'second')
    # The between-query cumulative jump represents other reaped work, excluded
    # from monitor CPU; both successful and failed queries charge their own delta.
    assert q._monitor_child_cpu_s==pytest.approx(.6)
    lockpath=tmp_path/'lock.json'
    lockpath.write_text(json.dumps({'tasks':[{'id':'never'}],
        'carried_charge_s':q.DISPATCH_STOP-20.,'freeze_charge_s':0.}))
    monkeypatch.setattr(q,'verify_lock',lambda *a,**kw:None)
    monkeypatch.setattr(q,'freeze_accounting',lambda lock,*a:lock)
    monkeypatch.setattr(q,'launch',lambda *a:pytest.fail('budget gate dispatched'))
    output=tmp_path/'output'
    q.run(SimpleNamespace(lock=str(lockpath),freeze_receipt=str(lockpath),output=str(output)))
    assert q._monitor_child_cpu_s==0.
    charges=[r for r in q.ledger_events(output/'ledger.jsonl') if r['event']=='supervisor_cpu']
    assert len(charges)==1
    assert charges[0]['monitor_child_cpu_s']==0.
    assert charges[0]['charged_cpu_s']==charges[0]['process_cpu_s']+charges[0]['monitor_child_cpu_s']


def test_cleanup_transient_permission_error_can_confirm_absence(monkeypatch):
    clock=Clock()
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(q.time,'sleep',clock.sleep)
    probes=[]
    def killpg(pgid,signum):
        if signum==0:
            probes.append(pgid)
            if len(probes)==1:
                raise PermissionError('transient ownership visibility')
            raise ProcessLookupError()
    monkeypatch.setattr(q.os,'killpg',killpg)
    proc=SimpleNamespace(pid=123,returncode=-9,wait=lambda timeout:None)
    receipt=q.stop_owned(proc,{123})
    assert receipt['group_absent']
    assert any(d.get('state')=='unknown' for d in receipt['probe_diagnostics'])
    assert receipt['group_states']==[{'pgid':123,'state':'absent'}]
    assert clock.now-100.<1.5


def test_postreceipt_ledger_failure_is_audited_and_blocks_resume(tmp_path,monkeypatch):
    item=fake_item(tmp_path)
    monkeypatch.setattr(q.time,'monotonic',lambda:105.)
    stopped=[];closed=[]
    monkeypatch.setattr(q,'stop_owned',lambda *a:(stopped.append(True) or {
        'group_absent':True,'owned_pgids':[123],'probe_diagnostics':[],'cleanup_errors':[]}))
    monkeypatch.setattr(q,'receive_ack',lambda item:None)
    original_close=q.os.close
    monkeypatch.setattr(q.os,'close',lambda fd:closed.append(fd) if fd==987 else original_close(fd))
    lock={'tasks':[item['task']],'carried_charge_s':150.,'freeze_charge_s':0.}
    q.append_ledger(tmp_path/'ledger.jsonl',{'event':'carry_forward','charged_cpu_s':150.,'freeze_charge_s':0.})
    append=q.append_ledger
    failed=[]
    def once(path,event):
        if event['event']=='finish' and not failed:
            failed.append(True)
            raise OSError('postreceipt ledger failure')
        return append(path,event)
    monkeypatch.setattr(q,'append_ledger',once)
    with pytest.raises(OSError,match='postreceipt'):
        q.finish(item,'lock',tmp_path,'monitor_failure:TimeoutExpired')
    receipt_hash=q.sha(tmp_path/'supervisor.json')
    q.finish(item,'lock',tmp_path,'supervisor_interrupted')
    assert q.sha(tmp_path/'supervisor.json')==receipt_hash
    assert stopped==[True] and closed==[987]
    events=q.ledger_events(tmp_path/'ledger.jsonl')
    assert sum(e['event']=='finish' for e in events)==1
    assert sum(e['event']=='terminal_audit_error' for e in events)==1
    with pytest.raises(ValueError,match='audit|reconcil'):
        q.resume_state(tmp_path,lock,'lock')


def test_cleanup_obeys_absolute_outer_allocation_cap(monkeypatch):
    clock=Clock(132.4)
    monkeypatch.setattr(q.time,'monotonic',clock)
    monkeypatch.setattr(q.time,'sleep',clock.sleep)
    monkeypatch.setattr(q.os,'killpg',lambda *a:(_ for _ in ()).throw(PermissionError('still unknown')))
    waits=[]
    def wait(timeout):
        waits.append(timeout)
        clock.now += timeout
        raise subprocess.TimeoutExpired(['fake-worker'],timeout)
    proc=SimpleNamespace(pid=123,returncode=None,wait=wait)
    receipt=q.stop_owned(proc,{123},deadline=100.+q.OUTER_ALLOCATION)
    assert clock.now<=132.5
    assert waits and all(0.<=timeout<=.1 for timeout in waits)
    assert not receipt['group_absent'] and receipt['cleanup_errors']
    assert receipt['cleanup_deadline']==132.5
