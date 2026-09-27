"""Pure explicit-oracle integration tests; no native optimization."""
import copy
from dataclasses import asdict
import importlib.abc
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from egglab import native_hull as nh, native_pathflow_hull as compact
from experiments import native_hull_qualification as indexed
from experiments import native_pathflow_hull_qualification as cq
import test_native_hull as helper


@pytest.fixture(autouse=True)
def forbid_native_imports():
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname.split('.')[0] in ('mip','gurobipy'):
                raise AssertionError('Native import forbidden during pure integration test')
    guard=Guard();sys.meta_path.insert(0,guard)
    yield
    sys.meta_path.remove(guard)


def fakes(monkeypatch):
    helper.install_fakes(monkeypatch)
    price=nh.nr.solve_pricing
    calls=[]
    def compact_price(case,prices,budget,record=None):
        calls.append((case.identity(),list(prices)))
        r=price(case,prices,budget,record)
        # Synthetic V3 result/plan carry the compact extraction policy.
        r['plan']['formulation']=compact.ORACLE_ID
        r['plan']['extraction_policy']=compact.EXTRACTION_POLICY
        r['extraction_policy']=compact.EXTRACTION_POLICY
        return r
    monkeypatch.setattr(compact.pathflow,'solve_pricing',compact_price)
    monkeypatch.setattr(nh.nr,'solve_pricing',lambda *a,**k:pytest.fail('indexed oracle was invoked'))
    return calls


def test_eight_definitions_and_original_budgets_are_preserved():
    assert cq.controls()==indexed.controls()
    cell=cq.controls()[0];budget=nh.Budget()
    a,b=indexed.manifest(cell,budget),cq.manifest(cell,budget)
    assert {k:v for k,v in a.items() if k!='state_identity'}=={k:v for k,v in b.items() if k not in ('state_identity','pricing_oracle','extraction_policy')}
    assert a['state_identity']!=b['state_identity']
    assert b['pricing_oracle']==compact.ORACLE_ID
    assert b['extraction_policy']==compact.EXTRACTION_POLICY
    assert 'src/egglab/native_pathflow.py' in cq.SOURCES
    assert set(indexed.SOURCES).issubset(cq.SOURCES)
    assert cq.WORKER_SECONDS==75 and cq.OUTER_SECONDS==650


def test_energy_band_v2_to_projection_v3_oracle_identity_changes():
    c=indexed.controls()[0];budget=nh.Budget()
    v2=nh.state_identity(c['case'],c['market'],c['arm'],c['state_index'],budget,
        oracle_id=compact.pathflow.NATIVE_MATRIX)
    v3=compact.state_identity(c['case'],c['market'],c['arm'],c['state_index'],budget)
    assert compact.ORACLE_ID==compact.pathflow.FORMULATION
    assert compact.pathflow.NATIVE_MATRIX!='' and v2!=v3


def test_indexed_default_state_digest_is_exactly_unchanged():
    c=indexed.controls()[0];b=nh.Budget()
    old_payload={'schema':nh.SCHEMA,'case':c['case'].identity(),'market':c['market'].identity(),
        'arm':c['arm'],'state_index':c['state_index'],'budget':asdict(b),'extraction_policy':nh.nr.EXTRACTION_POLICY}
    assert nh.state_identity(c['case'],c['market'],c['arm'],c['state_index'],b)==nh.nr.digest(old_payload)


def test_default_dispatch_preserves_indexed_result_shape(monkeypatch):
    helper.install_fakes(monkeypatch)
    monkeypatch.setattr(compact.pathflow,'solve_pricing',lambda *a,**k:pytest.fail('compact default invoked'))
    c=indexed.controls()[0];events=[]
    result=nh.certify(c['case'],c['market'],record=events.append)
    assert result['status']=='certified' and 'pricing_oracle' not in result
    assert all('pricing_oracle' not in e for e in events if e['event'] in ('state_start','pricing_request'))
    assert all('pricing_oracle' not in col['source'] for col in result['columns'])


def test_all_eight_compact_fake_controls_use_explicit_dispatch(monkeypatch):
    calls=fakes(monkeypatch);previous={}
    for cell in cq.controls():
        prev=previous.get(cell['predecessor']);events=[]
        result=compact.certify(cell['case'],cell['market'],arm=cell['arm'],state_index=cell['state_index'],
            previous=prev,expected_previous=prev['state_identity'] if prev else None,record=events.append)
        assert cq.assess(cell,result)['pass']
        assert result['pricing_oracle']==compact.ORACLE_ID
        assert result['state_identity']==cq.manifest(cell,nh.Budget())['state_identity']
        assert all(e['pricing_oracle']==compact.ORACLE_ID for e in events if e['event'] in ('state_start','pricing_request'))
        assert all(col['source']['pricing_oracle']==compact.ORACLE_ID for col in result['columns'])
        assert all(col['plan']['formulation']==compact.ORACLE_ID for col in result['columns'])
        previous[cell['id']]=result
    assert calls


@pytest.mark.parametrize('oracle,identity',[(None,'compact'),(lambda *a:None,None),(3,'compact'),(lambda *a:None,''),(lambda *a:None,4)])
def test_incomplete_or_invalid_explicit_dependency_fails_before_call(oracle,identity):
    c=cq.controls()[0]
    with pytest.raises(ValueError,match='oracle'):
        nh.certify(c['case'],c['market'],pricing_oracle=oracle,oracle_id=identity)


@pytest.mark.parametrize('changed',['result','plan'])
def test_every_compact_pricing_admission_checks_formulation(monkeypatch,changed):
    fakes(monkeypatch);original=compact.pathflow.solve_pricing;calls=[]
    def wrong(*args,**kwargs):
        result=original(*args,**kwargs);calls.append(1)
        # Corrupt only a later price, proving this is not merely a seed check.
        if len(calls)==2:
            if changed=='result':result['formulation']='other-formulation'
            else:result['plan']['formulation']='other-formulation'
        return result
    monkeypatch.setattr(compact.pathflow,'solve_pricing',wrong)
    c=cq.controls()[0]
    with pytest.raises(ValueError,match='formulation'):compact.certify(c['case'],c['market'])
    assert len(calls)==2


def test_direct_explicit_hook_rejects_forged_plan_formulation(monkeypatch):
    helper.install_fakes(monkeypatch);original=nh.nr.solve_pricing
    def wrong(*args,**kwargs):
        result=original(*args,**kwargs);result['formulation']='declared'
        return result
    c=cq.controls()[0]
    with pytest.raises(ValueError,match='formulation mismatch'):
        nh.certify(c['case'],c['market'],pricing_oracle=wrong,oracle_id='declared')


def test_retained_state_rejects_both_oracle_boundary_directions(monkeypatch):
    helper.install_fakes(monkeypatch);c=indexed.controls()[3]
    old=nh.certify(c['case'],c['market'],arm='retained')
    fakes(monkeypatch)
    with pytest.raises(ValueError,match='oracle identity'):
        compact.certify(c['case'],c['market'],arm='retained',state_index=1,
                       previous=old,expected_previous=old['state_identity'])
    new=compact.certify(c['case'],c['market'],arm='retained')
    with pytest.raises(ValueError,match='oracle identity'):
        nh.certify(c['case'],c['market'],arm='retained',state_index=1,
                   previous=new,expected_previous=new['state_identity'])


def test_worker_owns_compact_identity_and_dispatch(tmp_path,monkeypatch):
    c=cq.controls()[0];seen=[]
    monkeypatch.setattr(cq,'source_hashes',lambda:{'pure':'fixed'})
    monkeypatch.setattr(cq.nq,'environment',lambda:{'runtime':'fake'})
    monkeypatch.setattr(cq,'assess',lambda *a:{'pass':True})
    monkeypatch.setattr(nh,'certify',lambda *a,**k:pytest.fail('unwrapped coordinator reached'))
    def certify(*args,**kwargs):seen.append(kwargs);return {'status':'certified','pricing_oracle':compact.ORACLE_ID,
        'extraction_policy':compact.EXTRACTION_POLICY,'columns':[]}
    monkeypatch.setattr(compact,'certify',certify)
    frozen={'source_hashes':{'pure':'fixed'},'protocol':cq.PROTOCOL,'pricing_oracle':compact.ORACLE_ID,
        'extraction_policy':compact.EXTRACTION_POLICY}
    assert cq.worker(c['id'],tmp_path,nh.Budget(),frozen)==0
    assert seen and json.loads((tmp_path/'result.json').read_text())['result']['pricing_oracle']==compact.ORACLE_ID


def test_compact_controller_uses_own_workers_and_continues_failures(tmp_path,monkeypatch):
    monkeypatch.setattr(cq,'source_hashes',lambda:{'pure':'fixed'})
    monkeypatch.setattr(cq.nq,'environment',lambda:{'runtime':'fake'})
    calls=[]
    def run(cmd,**kwargs):
        assert cmd[cmd.index('-m')+1]=='experiments.native_pathflow_hull_qualification'
        calls.append(cmd[cmd.index('--worker')+1])
        return SimpleNamespace(returncode=2)
    monkeypatch.setattr(cq.subprocess,'run',run)
    assert cq.controller(tmp_path,'pure-fake')==1
    assert calls==[c['id'] for c in cq.controls()]
    frozen=json.loads((tmp_path/'frozen.json').read_text())
    assert frozen['pricing_oracle']==compact.ORACLE_ID and frozen['protocol']==cq.PROTOCOL
    assert len(frozen['controls'])==8
