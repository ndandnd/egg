"""Fake-only freeze supervision checks; no backend, process or fixture generation."""
import builtins
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess

import pytest


@pytest.fixture
def freeze(monkeypatch):
    original = builtins.__import__
    def guarded(name,*args,**kwargs):
        if name.split('.')[0] in {'mip','gurobipy'}:
            raise AssertionError('Native imports forbidden in freeze checks')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    monkeypatch.setattr(subprocess,'Popen',lambda *a,**kw:pytest.fail('Real process launch forbidden'))
    directory = Path(__file__).resolve().parents[2]/'research-20261023'
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location('recovery_freeze_v2_under_test',directory/'run_recovery_freeze_v2.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cleanup_permission_error_preserves_monitor_primary_and_owned_groups(freeze,monkeypatch):
    f = freeze
    calls = []
    def stop(proc,groups,deadline):
        calls.append((set(groups),deadline))
        raise PermissionError('actual cleanup denied')
    monkeypatch.setattr(f.reviewed.q,'stop_owned',stop)
    monkeypatch.setattr(f.reviewed.q,'group_probe',lambda pgid:{'pgid':pgid,'state':'unknown'})
    proc = SimpleNamespace(pid=37089,returncode=-9,poll=lambda:-9)
    primary = {'type':'TimeoutExpired','message':'primary process monitor timeout'}
    termination,failure,secondary = f.cleanup_owned(proc,{37089,37090},132.5,failure=primary)
    assert calls == [({37089,37090},132.5)]
    assert failure == primary
    assert termination['owned_pgids'] == [37089,37090]
    assert termination['surviving_pgids'] == [37089,37090]
    assert termination['reaped'] and termination['leader_returncode'] == -9
    assert termination['cleanup_deadline'] == 132.5
    assert any(row.get('error_type') == 'PermissionError' for row in secondary)
    assert not f.cleanup_confirmed(termination)


def test_unexpected_cleanup_helper_exception_retains_unknown_inventory(freeze,monkeypatch):
    monkeypatch.setattr(freeze.reviewed,'cleanup_receipt',
        lambda *a,**kw:(_ for _ in ()).throw(PermissionError('helper denied')))
    proc = SimpleNamespace(pid=37089,returncode=None)
    termination,failure,secondary = freeze.cleanup_owned(proc,{37090},132.5)
    assert termination['owned_pgids'] == termination['surviving_pgids'] == [37089,37090]
    assert termination['group_states'] == [{'pgid':37089,'state':'unknown'},{'pgid':37090,'state':'unknown'}]
    assert not termination['reaped'] and not termination['group_absent']
    assert failure['error_type'] == 'PermissionError' and secondary == []
    assert not freeze.cleanup_confirmed(termination)


@pytest.mark.parametrize('state,reaped,confirmed',[('unknown',True,False),('absent',False,False),('absent',True,True)])
def test_cleanup_requires_both_absence_and_reap(freeze,monkeypatch,state,reaped,confirmed):
    q = freeze.reviewed.q
    monkeypatch.setattr(q,'stop_owned',lambda proc,groups,deadline:{
        'owned_pgids':sorted(groups),'cleanup_errors':[],'probe_diagnostics':[]})
    monkeypatch.setattr(q,'group_probe',lambda pgid:{'pgid':pgid,'state':state})
    proc = SimpleNamespace(pid=37089,returncode=0 if reaped else None,poll=lambda:0 if reaped else None)
    termination,failure,secondary = freeze.cleanup_owned(proc,{37089},132.5)
    assert freeze.cleanup_confirmed(termination) is confirmed
    assert (failure is None) is confirmed
    assert termination['reaped'] is reaped
    assert termination['owned_pgids'] == [37089]


@pytest.mark.parametrize('ceiling,stop,carried,accepted',[
    (1800.,1620.,1000.,True),(1800.,1620.,1587.5,True),
    (1800.,1620.,1587.5001,False),(900.,720.,1000.,False)])
def test_inputs_use_checked_runner_budget_constants(freeze,tmp_path,monkeypatch,ceiling,stop,carried,accepted):
    f,q = freeze,freeze.reviewed.q
    monkeypatch.setattr(q,'CEILING',ceiling)
    monkeypatch.setattr(q,'DISPATCH_STOP',stop)
    monkeypatch.setattr(q,'SHUTDOWN_RESERVE',180.)
    monkeypatch.setattr(q,'checked_sources',lambda *a:None)
    monkeypatch.setattr(q,'accounting',lambda *a:{'charged_cpu_s':carried})
    monkeypatch.setattr(q,'reservation',lambda *a:None)
    checks = tmp_path/'checks'
    checks.mkdir()
    for name,value in (('result.json',{'cumulative_qualification_charge_s':0.}),('attempt.json',{'source_hashes':{}})):
        (checks/name).write_text(json.dumps(value))
    for name in ('stdout.log','stderr.log'):
        (checks/name).write_text('')
    account,registry,design,library,protocol = [tmp_path/name for name in
        ('accounting.json','registry.json','design.json','fake-library','protocol.md')]
    for path in (account,registry,design):
        path.write_text('{}')
    library.write_text('identity only')
    protocol.write_text('fake source protocol')
    lock = tmp_path/'lock.json'
    command = [f.sys.executable,'-m','experiments.recovery_qualification','freeze',
        '--lock',str(lock),'--checks',str(checks),'--accounting',str(account),
        '--reservations',str(registry),'--design',str(design),'--native-library',str(library),'--backend','GRB']
    command_json = tmp_path/'command.json'
    command_json.write_text(json.dumps(command))
    args = SimpleNamespace(checks=str(checks),accounting=str(account),command_json=str(command_json),
                           lock=str(lock),protocol=str(protocol))
    if accepted:
        actual,charge,sources = f.inputs(args)
        assert actual == command and charge == carried
        assert str(Path(f.reviewed.__file__).resolve()) in sources
    else:
        with pytest.raises(ValueError,match='Insufficient full freeze allocation'):
            f.inputs(args)


@pytest.mark.parametrize('cpu_failure',[False,True])
def test_supervise_retains_primary_and_cleanup_evidence_in_terminal_receipt(freeze,tmp_path,monkeypatch,cpu_failure):
    f,q = freeze,freeze.reviewed.q
    monkeypatch.setattr(f.time,'monotonic',lambda:100.)
    monkeypatch.setattr(f.time,'process_time',lambda:10.)
    monkeypatch.setattr(f.signal,'signal',lambda *a:0)
    usage_calls = []
    def usage(*args):
        usage_calls.append(args)
        if cpu_failure and len(usage_calls)>1:
            raise OSError('Final child CPU unavailable')
        return SimpleNamespace(ru_utime=0.,ru_stime=0.)
    monkeypatch.setattr(f.resource,'getrusage',usage)
    monkeypatch.setattr(f,'inputs',lambda args:(['fake freeze'],600.,{}))
    queries = []
    def snapshot(deadline):
        queries.append(deadline)
        if len(queries)>1:
            raise subprocess.TimeoutExpired(['ps','-axo'],.2)
        return {os.getpid():{'ppid':1,'pgid':os.getpgrp(),'rss':0,'cpu':0.}}
    monkeypatch.setattr(f.checked,'snapshot',snapshot)
    monkeypatch.setattr(f.prior,'memory_state',lambda end:{'free_percent':75.})
    proc = SimpleNamespace(pid=37089,returncode=None)
    def poll():
        if len(queries)>1:
            proc.returncode = 0
            return 0
        return None
    proc.poll = poll
    monkeypatch.setattr(f.subprocess,'Popen',lambda *a,**kw:proc)
    monkeypatch.setattr(q,'stop_owned',lambda *a,**kw:(_ for _ in ()).throw(PermissionError('cleanup denied')))
    monkeypatch.setattr(q,'group_probe',lambda pgid:{'pgid':pgid,'state':'unknown'})
    monkeypatch.setattr(q,'verify_lock',lambda *a:None)
    lock = tmp_path/'lock.json'
    lock.write_text(json.dumps({'carried_charge_s':600.}))
    folder = tmp_path/'attempt'
    args = SimpleNamespace(attempt_dir=str(folder),lock=str(lock),checks=str(tmp_path/'checks'))
    assert f.supervise(args) == 1
    receipt = json.loads((folder/'supervisor.json').read_text())
    assert receipt['failure']['type'] == 'TimeoutExpired'
    assert any(row.get('error_type') == 'PermissionError' for row in receipt['secondary_errors'])
    assert receipt['termination']['owned_pgids'] == [37089]
    assert receipt['termination']['group_states'] == [{'pgid':37089,'state':'unknown'}]
    assert receipt['termination']['reaped'] and receipt['termination']['cleanup_deadline'] == 132.5
    assert not receipt['passed'] and receipt['monitor_failure']['type'] == 'TimeoutExpired'
    assert receipt['accounting_observations_complete'] is (not cpu_failure)
    assert receipt['accounting_unresolved'] is cpu_failure
    assert receipt['charge_is_lower_bound'] is cpu_failure
    if cpu_failure:
        assert receipt['observed_children_cpu_s'] is None
        assert any(row.get('context') == 'child_cpu_audit' and row.get('error_type') == 'OSError'
                   for row in receipt['secondary_errors'])
    else:
        assert receipt['observed_children_cpu_s'] == 0.
    assert receipt['charged_cpu_s'] >= receipt['elapsed_allocation_s']
