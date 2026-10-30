"""Small deterministic check-supervisor regressions; no child or native dispatch."""
import builtins
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import subprocess

import pytest


@pytest.fixture(params=['run_admission_capture_checks_v2.py','run_admission_capture_budget_check.py'],
                ids=['original_v2','approved_budget'])
def supervisor(monkeypatch,request):
    original=builtins.__import__
    def guarded(name,*args,**kwargs):
        if name.split('.')[0] in {'mip','gurobipy'}:
            raise AssertionError('Native backend forbidden in check-supervisor tests')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    directory=Path(__file__).resolve().parents[2]/'research-20261023'
    monkeypatch.syspath_prepend(str(directory))
    # Loading the module must not execute its check command or main routine.
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('Import dispatched a child'))
    spec=importlib.util.spec_from_file_location('check_supervision_'+Path(request.param).stem+'_under_test',
        directory/request.param)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Clock:
    def __init__(self,now=100.):
        self.now=now
    def __call__(self):
        return self.now
    def sleep(self,seconds):
        self.now += seconds


def test_sample_uses_shared_deadline_with_early_cadence(supervisor,tmp_path,monkeypatch):
    s=supervisor
    clock=Clock(100.05)
    monkeypatch.setattr(s.q.time,'monotonic',clock)
    calls=[]
    def monitor(deadline):
        calls.append(deadline)
        clock.now=100.10
        return ({123:{'ppid':1,'pgid':123,'rss':4096,'cpu':2.}},75.)
    monkeypatch.setattr(s.q,'monitor_sample',monitor)
    monkeypatch.setattr(s.ownership,'registered_groups',lambda *a:None)
    groups={123}
    result=s.sample_owned(SimpleNamespace(pid=123),groups,tmp_path/'registry',100.,100.01)
    assert calls==[pytest.approx(100.26)]
    assert calls[0]-100.05==pytest.approx(.21)
    assert result['completed_monotonic']-100.01<=.25
    assert result['rss_bytes']==4096 and result['cpu_s']==2. and result['free_percent']==75.
    assert result['owned_pgids']==[123]


def test_ps_timeout_is_fatal_and_retains_command_context(supervisor,tmp_path,monkeypatch):
    s=supervisor
    monkeypatch.setattr(s.q.time,'monotonic',lambda:100.)
    timeout=subprocess.TimeoutExpired(['ps','-axo'],.24)
    monkeypatch.setattr(s.q,'monitor_sample',lambda *a,**kw:(_ for _ in ()).throw(timeout))
    with pytest.raises(subprocess.TimeoutExpired):
        s.sample_owned(SimpleNamespace(pid=123),{123},tmp_path/'registry',100.,None)
    state={}
    s.retain_error(state,timeout,'owned_sample')
    assert state['primary_failure']['command']==['ps','-axo']
    assert state['primary_failure']['context']=='owned_sample'
    assert state['primary_failure']['error_type']=='TimeoutExpired'


def test_cleanup_exception_retains_ownership_reap_and_both_errors(supervisor,monkeypatch):
    s=supervisor
    monkeypatch.setattr(s.q.time,'monotonic',lambda:100.)
    monkeypatch.setattr(s.q,'stop_owned',lambda *a,**kw:(_ for _ in ()).throw(PermissionError('cleanup denied')))
    monkeypatch.setattr(s.q,'group_probe',lambda pgid:{'pgid':pgid,'state':'unknown','error_type':'PermissionError'})
    proc=SimpleNamespace(pid=123,returncode=-9,poll=lambda:-9)
    receipt=s.cleanup_receipt(proc,{123,456},100.5)
    assert set(receipt['owned_pgids'])=={123,456}
    assert set(receipt['surviving_pgids'])=={123,456}
    assert receipt['leader_returncode']==-9 and receipt['reaped']
    assert receipt['cleanup_errors'] and receipt['probe_diagnostics']
    state={}
    s.retain_error(state,subprocess.TimeoutExpired(['ps'],.24),'monitor')
    s.retain_error(state,PermissionError('cleanup denied'),'cleanup')
    assert state['primary_failure']['error_type']=='TimeoutExpired'
    assert state['secondary_errors'][0]['error_type']=='PermissionError'


def test_cleanup_unknown_never_counts_as_absent_and_respects_deadline(supervisor,monkeypatch):
    s=supervisor
    clock=Clock(132.4)
    monkeypatch.setattr(s.q.time,'monotonic',clock)
    monkeypatch.setattr(s.q.time,'sleep',clock.sleep)
    monkeypatch.setattr(s.q.os,'killpg',lambda *a:(_ for _ in ()).throw(PermissionError('unknown')))
    waits=[]
    def wait(timeout):
        waits.append(timeout)
        clock.now += timeout
        raise subprocess.TimeoutExpired(['fake-check'],timeout)
    proc=SimpleNamespace(pid=123,returncode=None,poll=lambda:None,wait=wait)
    receipt=s.cleanup_receipt(proc,{123},132.5)
    assert clock.now<=132.5
    assert receipt['surviving_pgids']==[123] and not receipt['group_absent']
    assert not receipt['reaped'] and receipt['cleanup_errors']
    monkeypatch.setattr(s.q.os,'killpg',lambda *a:(_ for _ in ()).throw(ProcessLookupError()))
    proc.returncode=-9
    proc.poll=lambda:-9
    proc.wait=lambda timeout:-9
    absent=s.cleanup_receipt(proc,{123},132.5)
    assert absent['group_absent'] and absent['surviving_pgids']==[] and absent['reaped']


def test_reaped_children_charge_already_includes_monitor_cpu(supervisor):
    charged=supervisor.accounting(elapsed=10.,sampled_cpu=15.,children_cpu=20.,
        supervisor_cpu=3.,monitor_cpu=2.)
    assert charged['charged_cpu_s']==23.
    assert charged['monitor_child_cpu_s']==2.


def test_output_audit_retains_primary_and_missing_hash_evidence(supervisor,tmp_path,monkeypatch):
    s=supervisor
    (tmp_path/'stdout.log').write_text('retained output')
    (tmp_path/'stderr.log').write_text('retained error')
    state={}
    s.retain_error(state,subprocess.TimeoutExpired(['ps'],.24),'monitor')
    primary=dict(state['primary_failure'])
    calls=[]
    def digest(path):
        calls.append(path.name)
        if path.name=='stdout.log':
            raise OSError('stdout hash unavailable')
        return 'e'*64
    monkeypatch.setattr(s.q,'sha',digest)
    audit=s.output_audit(tmp_path,state)
    assert state['primary_failure']==primary
    assert state['secondary_errors'][0]['error_type']=='OSError'
    assert state['secondary_errors'][0]['context']=='output_audit:stdout'
    assert audit['stdout_sha256'] is None and audit['stderr_sha256']=='e'*64
    assert audit['artifact_hashes']=={'stdout.log':None,'stderr.log':'e'*64}
    assert calls.count('stdout.log')==1 and calls.count('stderr.log')==1
