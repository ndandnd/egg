"""Versioned fresh-fit budget extension of frozen v6 graph architectures.

Only epoch/time limits and persistence cadence change. v6 model, features,
weights, Adam settings, inner decisions and numerical model format are reused.
"""
from __future__ import annotations
from collections import defaultdict
import copy
from dataclasses import asdict, dataclass
import math
from pathlib import Path
import time

import numpy as np
import torch
from torch.nn import functional as F

from egglab import physical_route_graph_v6 as core
from experiments import train_physical_route_graph_v6 as old_cli

POLICY = 'physical-source-movement-graph-budget-exact128-v8'
V6_REPLAY_SHA = 'f2034510ef424b70200a075ac9e8d23bbefa51e54f1a21bf0563165fc458e9aa'
V6_COMMIT = 'ca9c3dbbfd22a83c42a8e18465f8524f7f11c98f'
ANCHOR_TOLERANCE = 1e-10


@dataclass(frozen=True)
class Budget:
    max_epochs: int = 900
    candidate_seconds: float = 1600.
    fold_seconds: float = 3400.
    anchor_epoch: int = 300
    save_every: int = 50
    def __post_init__(self):
        if (not 0 < self.anchor_epoch <= self.max_epochs or self.save_every <= 0
                or not 0 < self.candidate_seconds < self.fold_seconds):
            raise ValueError('Invalid explicit graph training budget')


BUDGET = Budget()


class AnchorMismatch(ValueError):
    pass


class AnchorUnavailable(ValueError):
    pass


class AnchorReference:
    """Immutable scalar trajectory + prefix-best v6 state and keyed predictions."""
    def __init__(self, curves, selected_epoch, best_state, predictions,
                 current_anchor_state=None, identity=None):
        self.curves = curves
        self.selected_epoch = selected_epoch
        self.best_state = best_state
        self.predictions = predictions
        self.current_anchor_state = current_anchor_state
        self.identity = identity or {'scope':'tiny synthetic fixture'}
        self.checks = {'shared_epochs_checked':0, 'maximum_shared_loss_difference':0.,
                       'status':'anchor_not_reached', 'mismatches':[], 'identity':self.identity}

    def _require(self, ok, check, detail=None):
        if not ok:
            self.checks['status']='mismatch'
            self.checks['mismatches'].append({'check':check, 'detail':detail})
            raise AnchorMismatch('Frozen v6 anchor mismatch: '+check)

    def shared_epoch(self, row, anchor_epoch):
        if row['epoch'] > anchor_epoch:
            return
        index = row['epoch']-1
        self._require(index < len(self.curves), 'missing_v6_shared_curve', row['epoch'])
        expected = self.curves[index]
        differences = {k:abs(row[k]-expected[k]) for k in
                       ('fit_weighted_log_loss','inner_weighted_log_loss')}
        largest = max(differences.values())
        self.checks['maximum_shared_loss_difference'] = max(self.checks['maximum_shared_loss_difference'], largest)
        self._require(largest <= ANCHOR_TOLERANCE, 'shared_curve', {'epoch':row['epoch'], 'differences':differences})
        self._require(row['selected_so_far']==expected['selected_so_far'], 'shared_inner_selection', row['epoch'])
        self.checks['shared_epochs_checked'] += 1

    def verify_anchor(self, current, prefix_best, best_epoch, parts):
        self._require(best_epoch==self.selected_epoch, 'prefix_best_epoch',
                      {'actual':best_epoch, 'v6':self.selected_epoch})
        def compare_state(actual, expected, label):
            self._require(set(actual)==set(expected), label+'.tensor_keys')
            delta=max(float((actual[k]-expected[k]).abs().max()) for k in actual)
            self.checks[label+'_maximum_tensor_difference']=delta
            self._require(delta <= ANCHOR_TOLERANCE, label+'.weights', delta)
        compare_state(prefix_best.state_dict(), self.best_state, 'prefix_best')
        available = self.current_anchor_state is not None
        self.checks['v6_current_anchor_state_available'] = available
        if available:
            compare_state(current.state_dict(), self.current_anchor_state, 'current_anchor')
        else:
            self.checks['v6_current_anchor_state_unavailable_reason']='v6 saved improvements only; no weight snapshot at anchor epoch'
        errors = {}
        for part,(samples, graph_batches) in parts.items():
            p=core.predict(prefix_best, graph_batches)
            expected=self.predictions[part]
            actual_keys=old_cli.prediction_rows(samples,p)
            keys=lambda rows:[(r['base_group'],r['source'],r['movement_id'],r['observed_selected']) for r in rows]
            self._require(keys(actual_keys)==keys(expected), part+'.movement_keys_labels')
            q=np.asarray([r['probability'] for r in expected]); delta=float(np.max(np.abs(p-q)))
            errors[part]=delta
            self._require(delta <= ANCHOR_TOLERANCE, part+'.prefix_best_probabilities', delta)
            self._require(np.array_equal(p>=.5,q>=.5), part+'.fixed_half')
            cursor=0
            for sample in samples:
                n=len(sample['y']); a=np.argsort(-p[cursor:cursor+n],kind='stable'); b=np.argsort(-q[cursor:cursor+n],kind='stable')
                self._require(np.array_equal(a,b), part+'.ranking', (sample['group'],sample['source']))
                cursor+=n
        self.checks.update({'status':'passed', 'prefix_best_epoch':best_epoch,
                            'prefix_best_probability_differences':errors,
                            'tolerance':ANCHOR_TOLERANCE})


def load_reference(root, task_id, family, samples):
    """Read admitted INNER artifacts only; no v6 outer metrics or outcomes."""
    root=Path(root); replay_path=root/'research-20260930/learning-campaign/ROUTE_GRAPH_V6_REPLAY.json'
    if core.frozen._sha(replay_path) != V6_REPLAY_SHA:
        raise ValueError('Pinned v6 scientific replay changed')
    replay=core.frozen._read(replay_path)
    if replay.get('passed') is not True:
        raise ValueError('No admitted v6 saved-state replay')
    task=root/'result/physical_learning/20260930-route-model128-graph-v6'/f'task{task_id:02d}'
    receipt=core.frozen._read(task/'receipt.json'); identity=core.frozen._read(task/'source_identity.json')
    audited=next(r for r in replay['task_checks'] if r['task_id']==task_id)
    if (receipt.get('status')!='completed' or core.frozen._sha(task/'receipt.json')!=audited['receipt_sha256']
            or core.frozen._sha(task/'source_identity.json')!=receipt['source_identity_sha256']
            or identity['source_commit']!=V6_COMMIT or identity['runtime_versions']!=old_cli.EXPECTED_RUNTIME):
        raise ValueError('Frozen v6 task/source receipt mismatch')
    for name,digest in identity['source_hashes'].items():
        if core.frozen._sha(root/name)!=digest:
            raise ValueError('Frozen v6 source changed: '+name)
    progress=task/'inner_progress'
    def read_pinned(name):
        if core.frozen._sha(progress/name)!=receipt['inner_progress_hashes'][name]:
            raise ValueError('Frozen v6 inner artifact changed: '+name)
        return core.frozen._read(progress/name)
    metadata=read_pinned(f'{family}_selected_inner.json')
    if metadata['completed_epochs']!=300 or len(metadata['train_curves'])!=300:
        raise ValueError('Baseline v6 did not complete declared300-epoch anchor')
    checkpoint=task/metadata['saved_model']['path']
    if core.frozen._sha(checkpoint)!=metadata['saved_model']['sha256']:
        raise ValueError('Frozen v6 selected model changed')
    best=core.restore_model(checkpoint)
    current_name=f'{family}_epoch0300.npz'; current=None
    if current_name in receipt['inner_progress_hashes']:
        if core.frozen._sha(progress/current_name)!=receipt['inner_progress_hashes'][current_name]:
            raise ValueError('Frozen v6 epoch300 model changed')
        current=copy.deepcopy(core.restore_model(progress/current_name).state_dict())
    predictions={part:read_pinned(f'{family}_{part}_predictions.json') for part in ('fit','inner')}
    transform=read_pinned('fit_only_preprocessing_and_groups.json')
    for part in ('fit','inner'):
        if tuple(sorted({s['group'] for s in samples[part]}))!=tuple(sorted(transform[part+'_groups'])):
            raise ValueError('Frozen v6 anchor group partition changed')
    mean,scale=core.frozen._preprocess(np.concatenate([s['x'] for s in samples['fit']]))
    if (tuple(transform['features'])!=tuple(core.FEATURES) or not np.array_equal(mean,np.asarray(transform['mean_fit_only']))
            or not np.array_equal(scale,np.asarray(transform['scale_fit_only']))):
        raise ValueError('Frozen v6 fit-only transform changed')
    return AnchorReference(metadata['train_curves'],metadata['selected_epoch'],
        copy.deepcopy(best.state_dict()),predictions,current,
        {'task_id':task_id,'family':family,'v6_source_commit':V6_COMMIT,'v6_replay_sha256':V6_REPLAY_SHA,
         'receipt_sha256':audited['receipt_sha256'],'selected_model_sha256':metadata['saved_model']['sha256']})


def fit_candidate(family, parts, seed, recorder, reference, budget=BUDGET, task_deadline=None):
    """Explicit fresh-fit loop; same v6 model and Adam/full-gradient mathematics."""
    core.configure_cpu(); torch.manual_seed(seed)
    model=core.GraphScorer(family)
    optimizer=torch.optim.Adam(model.parameters(),lr=core.LEARNING_RATE,betas=(.9,.999),
                               eps=1e-8,weight_decay=core.WEIGHT_DECAY)
    started=time.monotonic(); deadline=min(started+budget.candidate_seconds,
        task_deadline if task_deadline is not None else math.inf)
    best, best_state, best_epoch, stale, curve=math.inf,None,0,0,[]
    timers={k:0. for k in ('gradient_and_update_seconds','fit_evaluation_seconds',
                           'inner_evaluation_seconds','epoch_persistence_seconds','anchor_verification_seconds','stop_persistence_seconds')}
    stop='epoch_cap'
    try:
        for epoch in range(1,budget.max_epochs+1):
            if time.monotonic()>=deadline:
                stop='candidate_time_cap'; break
            step_started=time.monotonic(); model.train(); optimizer.zero_grad(set_to_none=True)
            interrupted=False
            for batch in parts['fit'][1]:
                if time.monotonic()>=deadline:
                    interrupted=True; break
                loss=(F.binary_cross_entropy_with_logits(model(batch),batch['y'],reduction='none')*batch['w']).sum()
                if not torch.isfinite(loss): raise ValueError('Nonfinite graph fit loss')
                loss.backward()
            if interrupted:
                timers['gradient_and_update_seconds']+=time.monotonic()-step_started
                stop='candidate_time_cap_incomplete_gradient_discarded'; break
            optimizer.step(); timers['gradient_and_update_seconds']+=time.monotonic()-step_started
            losses={}
            for part in ('fit','inner'):
                eval_started=time.monotonic(); losses[part]=core._loss(model,parts[part][1])
                timers[part+'_evaluation_seconds']+=time.monotonic()-eval_started
            if not np.isfinite(list(losses.values())).all(): raise ValueError('Nonfinite graph checkpoint loss')
            improved=losses['inner']<best
            if improved: best,best_epoch,stale=losses['inner'],epoch,0; best_state=copy.deepcopy(model.state_dict())
            else: stale+=1
            row={'epoch':epoch,'fit_weighted_log_loss':losses['fit'],'inner_weighted_log_loss':losses['inner'],
                 'selected_so_far':improved,'selected_epoch_so_far':best_epoch,'elapsed_seconds':time.monotonic()-started}
            curve.append(row)
            persist_started=time.monotonic()
            prefix=None
            if epoch%budget.save_every==0 or epoch==budget.anchor_epoch:
                prefix=copy.deepcopy(model); prefix.load_state_dict(best_state)
            recorder.epoch(family,epoch,prefix if epoch%budget.save_every==0 else None,row)
            timers['epoch_persistence_seconds']+=time.monotonic()-persist_started
            # Preserve both declared anchor states before even the scalar comparison.
            if epoch==budget.anchor_epoch:
                persist_started=time.monotonic(); recorder.anchor_states(family,epoch,model,prefix)
                timers['epoch_persistence_seconds']+=time.monotonic()-persist_started
            anchor_started=time.monotonic()
            reference.shared_epoch(row,budget.anchor_epoch)
            timers['anchor_verification_seconds']+=time.monotonic()-anchor_started
            if epoch==budget.anchor_epoch:
                anchor_started=time.monotonic(); reference.verify_anchor(model,prefix,best_epoch,parts)
                timers['anchor_verification_seconds']+=time.monotonic()-anchor_started
                persist_started=time.monotonic(); recorder.anchor_check(family,reference.checks)
                timers['epoch_persistence_seconds']+=time.monotonic()-persist_started
            if stale>=core.PATIENCE:
                stop='inner_patience'; break
        if best_state is None: raise TimeoutError('No complete graph epoch within candidate time budget')
        selected=copy.deepcopy(model); selected.load_state_dict(best_state)
        persist_started=time.monotonic()
        recorder.stop_state(family,selected,{'status':'stopped','selected_epoch':best_epoch,
            'completed_epochs':len(curve),'stop_reason':stop,'anchor':reference.checks})
        timers['stop_persistence_seconds']+=time.monotonic()-persist_started
        if reference.checks['status']!='passed':
            raise AnchorUnavailable('Stopped without a complete verified300-epoch anchor; no outer interpretation')
        return selected.eval(),{'family':family,'seed':seed,'parameter_count':model.parameter_count,
            'selected_epoch':best_epoch,'completed_epochs':len(curve),'stop_reason':stop,
            'inner_weighted_log_loss':best,'train_curves':curve,'anchor':reference.checks,
            'budget':asdict(budget),'fresh_fit_no_optimizer_resume':True,
            'fit_and_inner_seconds':time.monotonic()-started,'training_timers':timers}
    except BaseException:
        # Handled exceptions can preserve a scored best state. A process hard kill cannot.
        recorder.anchor_failure(family,reference.checks)
        if best_state is not None:
            preserved=copy.deepcopy(model); preserved.load_state_dict(best_state)
            recorder.failure_best(family,preserved,{'selected_epoch':best_epoch,'completed_epochs':len(curve),
                'stop_reason':stop,'fit_and_inner_seconds':time.monotonic()-started,'training_timers':timers})
        raise


def run_fold(dataset,task_id,recorder,root):
    if (tuple(dataset['groups'])!=tuple(f'physical_v2_s{i}' for i in range(10000,10128))
            or dataset['manifest_sha256']!=core.POOL_SHA or task_id not in range(12)):
        raise ValueError('Only frozen exact128 TRAIN/12 tasks are declared')
    started=time.monotonic(); deadline=started+BUDGET.fold_seconds
    fold,seed_index=divmod(task_id,3); seed=core.SEEDS[seed_index]
    fit_groups,inner_groups,outer_groups=core.previous.grouped_split(dataset['groups'],fold)
    samples={part:[s for s in dataset['samples'] if s['group'] in groups]
             for part,groups in (('fit',fit_groups),('inner',inner_groups))}
    fit_x,_,_=core.previous._stack(samples['fit']); mean,scale=core.frozen._preprocess(fit_x)
    recorder.preprocessing({'features':core.FEATURES,'mean_fit_only':mean.tolist(),'scale_fit_only':scale.tolist(),
        'fit_groups':fit_groups,'inner_groups':inner_groups,'outer_groups':outer_groups})
    parts={p:(s,core.batches(s,mean,scale,labelled=True)) for p,s in samples.items()}
    models,rows={},{}
    for family in core.FAMILIES:
        recorder.start_candidate(family,{'budget':asdict(BUDGET),'width':core.WIDTH,'layers':core.LAYERS,
            'patience':core.PATIENCE,'learning_rate':core.LEARNING_RATE,'weight_decay':core.WEIGHT_DECAY})
        reference=load_reference(root,task_id,family,samples)
        fitted,row=fit_candidate(family,parts,seed,recorder,reference,task_deadline=deadline)
        probabilities={}
        for part in ('fit','inner'):
            before=time.monotonic(); probabilities[part]=core.predict(fitted,parts[part][1])
            row[part+'_selected_prediction_seconds']=time.monotonic()-before
            _,y,w=core.previous._stack(samples[part]); row[part+'_metrics']=core.frozen._metrics(y,probabilities[part],w,samples[part])
        row['saved_model']=recorder.candidate(family,fitted,row,samples['fit'],probabilities['fit'],samples['inner'],probabilities['inner'])
        models[family],rows[family]=fitted,row
    promoted=core.select_family(rows)
    promotion={'family':promoted,'tie_order':core.FAMILIES,
        'inner_weighted_log_losses':{f:rows[f]['inner_weighted_log_loss'] for f in core.FAMILIES}}
    recorder.promotion(promotion)
    # No outer graph/features/labels before both anchor passes, selected states and promotion persist.
    outer=[s for s in dataset['samples'] if s['group'] in outer_groups]
    outer_batches=core.batches(outer,mean,scale,labelled=False); predictions={}; inference={}
    for family in core.FAMILIES:
        before=time.monotonic(); predictions[family]=core.predict(models[family],outer_batches); inference[family]=time.monotonic()-before
    predictions['inner_promoted']=predictions[promoted]
    per_source=defaultdict(dict); prediction_rows=[]; cursor=0
    for s in outer:
        n=len(s['y']); per_source[s['group']][s['source']]={f:core.frozen._metrics(s['y'],p[cursor:cursor+n],np.ones(n)/n,[s]) for f,p in predictions.items()}
        for j,mid in enumerate(s['movement_ids']):
            prediction_rows.append({'base_group':s['group'],'source':s['source'],'movement_id':mid,
                'observed_selected':bool(s['y'][j]),'input_trip_count_k':min(n,s['trip_count']),
                'probabilities':{f:float(p[cursor+j]) for f,p in predictions.items()}})
        cursor+=n
    per_group={g:{f:core.previous._macro_metrics([r[f] for r in per_source[g].values()]) for f in predictions} for g in outer_groups}
    _,y,w=core.previous._stack(outer); common=[g for g in outer_groups if int(g.rsplit('s',1)[-1])<10032]
    return {'policy':POLICY,'task_id':task_id,'fold':fold,'seed':seed,'features':core.FEATURES,
        'budget':asdict(BUDGET),'fit_groups':fit_groups,'inner_groups':inner_groups,'outer_groups':outer_groups,
        'dtype':'float64','device':'cpu','width':core.WIDTH,'layers':core.LAYERS,
        'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),
        'weights':{p:core.previous._weight_manifest(s) for p,s in {**samples,'outer':outer}.items()},
        'eligibility':{p:core.previous._partition_eligibility(dataset['group_eligibility'],g)
            for p,g in (('fit',fit_groups),('inner',inner_groups),('outer',outer_groups))},
        'pool_manifest_sha256':dataset['manifest_sha256'],'pool_table_hashes':dataset['table_hashes'],
        'v6_replay_sha256':V6_REPLAY_SHA,'candidates':rows,'inner_architecture_promotion':promotion,
        'outer_metrics':{f:core.previous._macro_metrics([per_group[g][f] for g in outer_groups]) for f in predictions},
        'common32_outer_metrics':{f:core.previous._macro_metrics([per_group[g][f] for g in common]) for f in predictions},
        'outer_pooled_diagnostics':{f:core.frozen._metrics(y,p,w,outer) for f,p in predictions.items()},
        'per_group_source_outer_metrics':dict(per_source),'per_group_outer_metrics':per_group,
        'outer_prediction_rows':prediction_rows,'outer_inference_seconds_by_family':inference,
        'progress_persistence_seconds':recorder.persistence_seconds,'no_outer_selection':True,
        'both300_anchors_verified':True,'fresh_fit_no_optimizer_resume':True,'wall_seconds':time.monotonic()-started,
        'label_scope':'observed feasible incumbent edge imitation only; no route optimality or fleet benefit claim'}
