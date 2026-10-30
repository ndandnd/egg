"""Tiny v8 controls, no TRAIN fits or native optimizer; no v6 source edits."""
from __future__ import annotations
import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from egglab import physical_route_graph_v6 as core
from egglab import physical_route_graph_budget_v8 as budget
from egglab import physical_route_model_v3 as previous
from experiments import train_physical_route_graph_v6 as old_cli
from experiments import train_physical_route_graph_budget_v8 as cli


def sample(group='fixture',seed=5):
    rng=np.random.default_rng(seed); x=rng.normal(size=(6,17)); x[:,1:16]=0.; x[:,-1]=1.
    return {'group':group,'source':'source0','x':x,'y':(x[:,0]>0).astype(float),
        'movement_ids':[10,11,12,13,14,15],'trip_count':2,
        'graph':{'src':np.array([0,0,1,1,1,2]),'dst':np.array([1,2,2,2,3,3]),'nodes':4}}


def parts():
    samples={'fit':[sample('a'),sample('b',6)],'inner':[sample('c',7)]}
    return {p:(s,core.batches(s,np.zeros(17),np.ones(17),labelled=True)) for p,s in samples.items()}


def reference(monkeypatch,folder,family,data,epochs):
    # Explicit tiny-fixture v6 cap override only; production v8 never patches v6 globals.
    monkeypatch.setattr(core,'MAX_EPOCHS',epochs)
    folder.mkdir()
    old=old_cli.Progress(folder)
    fitted,row=core.fit_candidate(family,data['fit'][1],data['inner'][1],17,old)
    predictions={p:old_cli.prediction_rows(s,core.predict(fitted,batches)) for p,(s,batches) in data.items()}
    current_path=old.path/f'{family}_epoch{epochs:04d}.npz'
    current=copy.deepcopy(core.restore_model(current_path).state_dict()) if current_path.exists() else None
    return budget.AnchorReference(row['train_curves'],row['selected_epoch'],
        copy.deepcopy(fitted.state_dict()),predictions,current)


@pytest.mark.parametrize('family',core.FAMILIES)
def test_fresh_fit_reproduces_v6_anchor_then_extends_with_sparse_models(tmp_path,monkeypatch,family):
    data=parts(); original_max=core.MAX_EPOCHS
    baseline=reference(monkeypatch,tmp_path/'old',family,data,4)
    destination=tmp_path/'new'; destination.mkdir(); progress=cli.Progress(destination)
    limits=budget.Budget(max_epochs=6,anchor_epoch=4,save_every=2)
    progress.start_candidate(family,{'budget_fixture':True})
    trained,row=budget.fit_candidate(family,data,17,progress,baseline,limits)
    assert row['fresh_fit_no_optimizer_resume'] and row['anchor']['status']=='passed'
    assert row['anchor']['shared_epochs_checked']==4
    assert row['anchor']['maximum_shared_loss_difference']==pytest.approx(0.,abs=1e-12)
    assert row['anchor']['prefix_best_maximum_tensor_difference']==0.
    assert row['completed_epochs']==6 and row['stop_reason']=='epoch_cap'
    curves=[json.loads(line) for line in (progress.path/f'{family}_epochs.jsonl').read_text().splitlines()]
    assert len(curves)==6 and [r['epoch'] for r in curves]==list(range(1,7))
    assert [r['epoch'] for r in curves if r['persisted_best_checkpoint']] == [2,4,6]
    assert len(list(progress.path.glob(f'{family}_periodic*.npz')))==3
    assert (progress.path/f'{family}_anchor0004_current.npz').exists()
    assert (progress.path/f'{family}_anchor0004_prefix_best.npz').exists()
    assert budget.BUDGET.max_epochs==900 and original_max==300
    loaded=core.restore_model(progress.path/f'{family}_stop_best.npz')
    assert core.predict(trained,data['inner'][1])==pytest.approx(core.predict(loaded,data['inner'][1]),abs=1e-12)
    assert sum(row['training_timers'].values()) <= row['fit_and_inner_seconds']+1e-8
    with pytest.raises(FileExistsError): progress.start_candidate(family,{})


def test_anchor_mismatch_preserves_failed_checks_and_best_weight(tmp_path,monkeypatch):
    data=parts(); baseline=reference(monkeypatch,tmp_path/'old','mean_message',data,4)
    baseline.curves[0]['inner_weighted_log_loss'] += .01
    folder=tmp_path/'new'; folder.mkdir(); progress=cli.Progress(folder)
    progress.start_candidate('mean_message',{})
    with pytest.raises(budget.AnchorMismatch,match='shared_curve'):
        budget.fit_candidate('mean_message',data,17,progress,baseline,
            budget.Budget(max_epochs=6,anchor_epoch=4,save_every=2))
    ledger=json.loads((progress.path/'mean_message_handled_failure_anchor_ledger.json').read_text())
    assert ledger['status']=='mismatch' and ledger['mismatches'][0]['check']=='shared_curve'
    assert len((progress.path/'mean_message_epochs.jsonl').read_text().splitlines())==1
    assert (progress.path/'mean_message_handled_failure_best.npz').exists()
    assert not (progress.path/'mean_message_selected.npz').exists()


def test_valid_inner_patience_is_never_forced_to_epoch_cap(tmp_path,monkeypatch):
    data=parts(); monkeypatch.setattr(core,'_loss',lambda *_:.2)
    baseline=reference(monkeypatch,tmp_path/'old','mean_message',data,2)
    folder=tmp_path/'new'; folder.mkdir(); progress=cli.Progress(folder); progress.start_candidate('mean_message',{})
    _,row=budget.fit_candidate('mean_message',data,17,progress,baseline,
        budget.Budget(max_epochs=40,anchor_epoch=2,save_every=10))
    assert row['completed_epochs']==31 and row['selected_epoch']==1
    assert row['stop_reason']=='inner_patience' and row['anchor']['status']=='passed'
    assert row['anchor']['v6_current_anchor_state_available'] is False


def test_time_cap_discards_partial_gradient_and_explicitly_holds_missing_anchor(tmp_path,monkeypatch):
    monkeypatch.setattr(core,'GRAPH_BATCH',1); data=parts()
    baseline=reference(monkeypatch,tmp_path/'old','mean_message',data,4)
    clock={'now':0.,'forwards':0}
    monkeypatch.setattr(budget,'time',SimpleNamespace(monotonic=lambda:clock['now']))
    original=core.GraphScorer.forward
    def forward(model,batch):
        value=original(model,batch)
        if model.training and torch.is_grad_enabled():
            clock['forwards']+=1
            if clock['forwards']==3: clock['now']=2.
        return value
    monkeypatch.setattr(core.GraphScorer,'forward',forward)
    folder=tmp_path/'new'; folder.mkdir(); progress=cli.Progress(folder); progress.start_candidate('mean_message',{})
    with pytest.raises(budget.AnchorUnavailable,match='anchor'):
        budget.fit_candidate('mean_message',data,17,progress,baseline,
            budget.Budget(max_epochs=6,candidate_seconds=1.,fold_seconds=2.,anchor_epoch=4,save_every=2))
    stopped=json.loads((progress.path/'mean_message_stop_best.json').read_text())
    assert stopped['completed_epochs']==1 and stopped['stop_reason']=='candidate_time_cap_incomplete_gradient_discarded'
    assert stopped['anchor']['status']=='anchor_not_reached' and clock['forwards']==3
    assert len((progress.path/'mean_message_epochs.jsonl').read_text().splitlines())==1
    assert (progress.path/'mean_message_handled_failure_best.npz').exists()


def test_outer_data_waits_for_both_selected_anchors_and_persisted_inner_promotion(tmp_path,monkeypatch):
    groups=tuple(f'physical_v2_s{i}' for i in range(10000,10128)); _,_,outer=previous.grouped_split(groups,0)
    state={'complete':0,'promoted':False,'outer_reads':0}
    class Guarded(dict):
        def __getitem__(self,key):
            if key in ('x','y','graph','trip_count','movement_ids'):
                assert state['complete']==2 and state['promoted']; state['outer_reads']+=1
            return super().__getitem__(key)
    samples=[Guarded(sample(g)) if g in outer else sample(g) for g in groups]
    class Recorder(cli.Progress):
        def promotion(self,row):
            super().promotion(row); state['promoted']=True
    def fake_fit(family,*_,**__):
        state['complete']+=1
        return core.GraphScorer(family),{'family':family,'inner_weighted_log_loss':.1 if family=='mean_message' else .2,
                                       'anchor':{'status':'passed'}}
    monkeypatch.setattr(budget,'fit_candidate',fake_fit); monkeypatch.setattr(budget,'load_reference',lambda *_:None)
    data={'groups':groups,'samples':samples,'manifest_sha256':core.POOL_SHA,'table_hashes':{},
        'group_eligibility':[{'base_group':g,'observed_source_count':1,'eligible_for_observed_source_supervision':True,
                              'eligible_for_full_pair_supervision':False} for g in groups]}
    result=budget.run_fold(data,0,Recorder(tmp_path),tmp_path)
    assert result['both300_anchors_verified'] and result['no_outer_selection'] and state['outer_reads']>0
    assert result['inner_architecture_promotion']['family']=='mean_message'


def test_mismatched_runtime_is_typed_failed_task_without_retry(tmp_path,monkeypatch):
    monkeypatch.setattr(cli.original,'versions',lambda:{'torch':'wrong'})
    with pytest.raises(ValueError,match='runtime'):
        cli.run(0,core.POOL_SHA,tmp_path)
    receipt=json.loads((tmp_path/'task00/receipt.json').read_text())
    assert receipt['status']=='failed' and (tmp_path/'task00/launch.json').exists()
    with pytest.raises(ValueError,match='Immutable'):
        cli.run(0,core.POOL_SHA,tmp_path)


def test_scalar_mismatch_at_anchor_preserves_both_declared_states_first(tmp_path,monkeypatch):
    data=parts(); baseline=reference(monkeypatch,tmp_path/'old','mean_message',data,4)
    baseline.curves[3]['inner_weighted_log_loss'] += .01
    folder=tmp_path/'new'; folder.mkdir(); progress=cli.Progress(folder); progress.start_candidate('mean_message',{})
    with pytest.raises(budget.AnchorMismatch,match='shared_curve'):
        budget.fit_candidate('mean_message',data,17,progress,baseline,
            budget.Budget(max_epochs=6,anchor_epoch=4,save_every=2))
    for suffix in ('current','prefix_best'):
        path=progress.path/f'mean_message_anchor0004_{suffix}.npz'
        assert path.exists() and core.restore_model(path).family=='mean_message'
    ledger=json.loads((progress.path/'mean_message_handled_failure_anchor_ledger.json').read_text())
    assert ledger['status']=='mismatch' and ledger['mismatches'][0]['detail']['epoch']==4
    assert len((progress.path/'mean_message_epochs.jsonl').read_text().splitlines())==4


def test_wrapper_guard_failure_has_early_immutable_receipt(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    environment=os.environ.copy()
    environment.update({'SLURM_ARRAY_TASK_ID':'0','SLURM_SUBMIT_DIR':str(tmp_path),
        'SLURM_JOB_ID':'fixture-guard','SLURM_ARRAY_JOB_ID':'fixture-array',
        'EGG_RECEIPT_PYTHON':sys.executable})
    environment.pop('EGG_RUN_COMMIT',None)
    wrapper=Path(__file__).resolve().parents[1]/'cluster/physical_route_graph_budget_v8.sbatch'
    child=subprocess.run(['bash',str(wrapper)],env=environment,text=True,capture_output=True)
    assert child.returncode != 0
    path=tmp_path/'result/physical_learning/20261001-route-model128-graph-budget-v8/task00.slurm_wrapper_receipt.fixture-guard.json'
    row=json.loads(path.read_text())
    assert row['wrapper_phase']=='guards' and row['returncode']==child.returncode
    assert row['runtime_probe_sha256'] is None and row['elapsed_seconds'] >= 0
