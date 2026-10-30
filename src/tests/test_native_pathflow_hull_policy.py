"""Pure V3 hull extraction-policy integration; no optimizer imports or calls."""
import copy
from dataclasses import asdict
import importlib.abc
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egglab import native_hull as hull, native_pathflow_hull as compact
from experiments import native_hull_qualification as indexed
from experiments import native_pathflow_hull_qualification as prospective
import test_native_hull as helper


@pytest.fixture(autouse=True)
def forbid_optimizer_imports():
    class Guard(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in ('mip', 'gurobipy'):
                raise AssertionError('Native optimizer import forbidden')
    guard = Guard()
    sys.meta_path.insert(0, guard)
    yield
    sys.meta_path.remove(guard)


def install_v3_fakes(monkeypatch):
    helper.install_fakes(monkeypatch)
    indexed_fake = hull.nr.solve_pricing
    def compact_fake(case, prices, budget, record=None):
        result = indexed_fake(case, prices, budget, record)
        result['formulation'] = compact.ORACLE_ID
        result['extraction_policy'] = compact.EXTRACTION_POLICY
        result['plan']['formulation'] = compact.ORACLE_ID
        result['plan']['extraction_policy'] = compact.EXTRACTION_POLICY
        return result
    monkeypatch.setattr(compact.pathflow, 'solve_pricing', compact_fake)
    monkeypatch.setattr(hull.nr, 'solve_pricing', lambda *a, **k: pytest.fail('indexed oracle called'))
    return compact_fake


def test_v3_state_identity_and_eight_control_freeze_are_explicit():
    cell = indexed.controls()[0]
    budget = hull.Budget()
    old = hull.state_identity(cell['case'], cell['market'], cell['arm'],
                              cell['state_index'], budget)
    old_payload = {'schema': hull.SCHEMA, 'case': cell['case'].identity(),
                   'market': cell['market'].identity(), 'arm': cell['arm'],
                   'state_index': cell['state_index'], 'budget': asdict(budget),
                   'extraction_policy': hull.nr.EXTRACTION_POLICY}
    assert old == hull.nr.digest(old_payload)
    v2 = hull.state_identity(cell['case'], cell['market'], cell['arm'],
                             cell['state_index'], budget, oracle_id=compact.ORACLE_ID)
    assert compact.state_identity(cell['case'], cell['market'], cell['arm'],
                                  cell['state_index'], budget) != v2
    assert prospective.controls() == indexed.controls()
    assert prospective.WORKER_SECONDS == 75 and prospective.OUTER_SECONDS == 650
    assert 'src/egglab/native_hull.py' in prospective.SOURCES
    assert 'src/tests/test_native_pathflow_hull_policy.py' in prospective.SOURCES
    assert 'doc/NATIVE_PATHFLOW_HULL_V3_IMPLEMENTATION_REVIEW_20260927.md' in prospective.SOURCES
    frozen = prospective.manifest(cell, budget)
    assert frozen['extraction_policy'] == compact.EXTRACTION_POLICY
    assert frozen['state_identity'] == compact.state_identity(
        cell['case'], cell['market'], cell['arm'], cell['state_index'], budget)


def test_eight_v3_fake_controls_store_and_replay_policy(monkeypatch):
    install_v3_fakes(monkeypatch)
    previous = {}
    for cell in prospective.controls():
        predecessor = previous.get(cell['predecessor'])
        result = compact.certify(cell['case'], cell['market'], arm=cell['arm'],
            state_index=cell['state_index'], previous=predecessor,
            expected_previous=predecessor['state_identity'] if predecessor else None)
        assert prospective.assess(cell, result)['pass']
        assert result['extraction_policy'] == compact.EXTRACTION_POLICY
        assert result['state_identity'] == prospective.manifest(cell, hull.Budget())['state_identity']
        assert all(column['extraction_policy'] == compact.EXTRACTION_POLICY
                   and column['plan']['extraction_policy'] == compact.EXTRACTION_POLICY
                   for column in result['columns'])
        for column in result['columns']:
            hull.replay_column(cell['case'], column, compact.EXTRACTION_POLICY)
        previous[cell['id']] = result


@pytest.mark.parametrize('field', ['result_missing', 'result_wrong', 'plan_missing', 'plan_wrong'])
def test_later_compact_price_policy_mismatch_fails_closed(monkeypatch, field):
    install_v3_fakes(monkeypatch)
    original = compact.pathflow.solve_pricing
    calls = []
    def corrupted(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(1)
        if len(calls) == 2:
            target = result if field.startswith('result') else result['plan']
            if field.endswith('missing'):
                target.pop('extraction_policy')
            else:
                target['extraction_policy'] = hull.nr.EXTRACTION_POLICY
        return result
    monkeypatch.setattr(compact.pathflow, 'solve_pricing', corrupted)
    cell = prospective.controls()[0]
    with pytest.raises(ValueError, match='extraction policy'):
        compact.certify(cell['case'], cell['market'])
    assert len(calls) == 2


def test_column_plan_and_retained_v2_to_v3_rejection(monkeypatch):
    install_v3_fakes(monkeypatch)
    cell = prospective.controls()[3]
    v3 = compact.certify(cell['case'], cell['market'], arm='retained')
    column = copy.deepcopy(v3['columns'][0])
    with pytest.raises(ValueError, match='provenance identity'):
        hull.replay_column(cell['case'], column)
    column['plan']['extraction_policy'] = hull.nr.EXTRACTION_POLICY
    column['witness_hash'] = hull.nr.digest(column['plan'])
    with pytest.raises(ValueError, match='plan extraction policy'):
        hull.replay_column(cell['case'], column, compact.EXTRACTION_POLICY)
    v2 = copy.deepcopy(v3)
    v2['extraction_policy'] = hull.nr.EXTRACTION_POLICY
    with pytest.raises(ValueError, match='predecessor'):
        hull.import_pool(cell['case'], v2, v2['state_identity'], hull.Budget(),
                         extraction_policy=compact.EXTRACTION_POLICY)
    with pytest.raises(ValueError, match='predecessor'):
        hull.import_pool(cell['case'], v3, v3['state_identity'], hull.Budget())


def test_indexed_default_rejects_explicit_v3_nested_plan_but_accepts_legacy_absence():
    case = prospective.controls()[0]['case']
    plan = helper.physical(case, 2, 0)
    legacy = hull.native_column(case, plan, {'source': 'legacy-pure'})
    hull.replay_column(case, legacy)
    tagged = copy.deepcopy(plan)
    tagged['extraction_policy'] = compact.EXTRACTION_POLICY
    with pytest.raises(ValueError, match='extraction policy'):
        hull.native_column(case, tagged, {'source': 'forged-pure'})
    forged = copy.deepcopy(legacy)
    forged['plan']['extraction_policy'] = compact.EXTRACTION_POLICY
    forged['witness_hash'] = hull.nr.digest(forged['plan'])
    with pytest.raises(ValueError, match='plan extraction policy'):
        hull.replay_column(case, forged)


@pytest.mark.parametrize('bad', ['', ' ', 4, True])
def test_invalid_explicit_policy_identity_rejected(bad):
    cell = prospective.controls()[0]
    with pytest.raises(ValueError, match='extraction policy'):
        hull.state_identity(cell['case'], cell['market'], cell['arm'],
                            cell['state_index'], hull.Budget(),
                            oracle_id=compact.ORACLE_ID, extraction_policy=bad)


@pytest.mark.parametrize('reported,column_policy,expected_exit', [
    (None, None, 2),
    (hull.nr.EXTRACTION_POLICY, None, 2),
    (compact.EXTRACTION_POLICY, hull.nr.EXTRACTION_POLICY, 2),
    (compact.EXTRACTION_POLICY, compact.EXTRACTION_POLICY, 0),
])
def test_worker_admits_only_v3_policy_result_and_column(tmp_path, monkeypatch,
                                                         reported, column_policy,
                                                         expected_exit):
    cell = prospective.controls()[0]
    monkeypatch.setattr(prospective, 'source_hashes', lambda: {'pure': 'fixed'})
    monkeypatch.setattr(prospective, 'assess', lambda *a: {'pass': True})
    monkeypatch.setattr(prospective.nq, 'environment', lambda: {'runtime': 'fake'})
    monkeypatch.setattr(compact, 'certify', lambda *a, **k: {
        'status': 'certified', 'extraction_policy': reported,
        'columns': [{'extraction_policy': column_policy}]})
    frozen = {'source_hashes': {'pure': 'fixed'}, 'protocol': prospective.PROTOCOL,
              'pricing_oracle': compact.ORACLE_ID,
              'extraction_policy': compact.EXTRACTION_POLICY}
    assert prospective.worker(cell['id'], tmp_path, hull.Budget(), frozen) == expected_exit
    if expected_exit:
        assert 'extraction policy' in json.loads((tmp_path / 'exception.json').read_text())['message']
    else:
        assert json.loads((tmp_path / 'result.json').read_text())['assessment']['pass']
