"""Read-only graph722841 saved-state replay; no fitting or reserved-data access.

Independent functional CPU forward and metric formulas verify selected models.
Epoch states are hash/tensor audited; only selected states are predicted.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import torch
from torch.nn import functional as F
from egglab import physical_route_graph_v6 as declared
from egglab import physical_route_model_v3 as prior
from experiments import train_physical_route_graph_v6 as cli

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'research-20260930/learning-campaign'
ATTEMPT = ROOT / 'result/physical_learning/20260930-route-model128-graph-v6'
TOLERANCE = 1e-10  # Frozen before first numerical replay; never silently expanded.
PRIMARY = ('weighted_log_loss','weighted_brier','average_precision',
           'input_trip_count_topk_recall_mean_by_fleet')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


class Audit:
    def __init__(self):
        self.checks = 0; self.failures = []; self.maximum_deltas = defaultdict(float)
    def check(self, ok, label, detail=None):
        self.checks += 1
        if not bool(ok):
            self.failures.append({'check':label,'detail':detail})
    def close(self, actual, expected, label, category='metrics'):
        if isinstance(expected, dict):
            self.check(isinstance(actual, dict) and set(actual)==set(expected), label+'.keys')
            if isinstance(actual, dict):
                for key in set(actual)&set(expected):
                    self.close(actual[key], expected[key], label+'.'+str(key), category)
        elif isinstance(expected,(list,tuple)):
            self.check(isinstance(actual,(list,tuple)) and len(actual)==len(expected), label+'.length')
            if isinstance(actual,(list,tuple)):
                for i,(a,b) in enumerate(zip(actual,expected)):
                    self.close(a,b,label+f'[{i}]',category)
        elif isinstance(expected,(float,np.floating)):
            if isinstance(actual,(float,int,np.number)) and np.isfinite([actual,expected]).all():
                delta = abs(float(actual)-float(expected)); self.maximum_deltas[category] = max(self.maximum_deltas[category],delta)
                self.check(delta <= TOLERANCE,label,{'absolute_difference':delta,'tolerance':TOLERANCE})
            else:
                self.check(False,label,{'actual':str(actual),'expected':str(expected)})
        else:
            self.check(actual==expected,label)


def aggregate(values,indexes,nodes,attention=None):
    if attention is None:
        sums = values.new_zeros((nodes,values.shape[1])).index_add(0,indexes,values)
        counts = values.new_zeros(nodes).index_add(0,indexes,values.new_ones(len(values)))
        return sums/counts.clamp_min(1)[:,None]
    scores = values @ attention / math.sqrt(values.shape[1])
    maxima = scores.new_full((nodes,),-torch.inf)
    maxima.scatter_reduce_(0,indexes,scores,reduce='amax',include_self=True)
    exp = torch.exp(scores-maxima[indexes])
    totals = exp.new_zeros(nodes).index_add(0,indexes,exp)
    return values.new_zeros((nodes,values.shape[1])).index_add(0,indexes,values*(exp/totals[indexes])[:,None])


def numeric_state(path,audit,label):
    with np.load(path,allow_pickle=False) as archive:
        family = str(archive['architecture'])
        audit.check(str(archive['policy'])==declared.POLICY,label+'.policy')
        reference = declared.GraphScorer(family).state_dict()
        audit.check(set(archive.files)==set(reference)|{'policy','architecture'},label+'.tensor_keys')
        state = {}
        for name,value in reference.items():
            array = archive[name]
            audit.check(array.shape==tuple(value.shape) and array.dtype==np.float64
                        and np.isfinite(array).all(),label+'.tensor.'+name)
            state[name]=torch.as_tensor(array.copy(),dtype=torch.float64)
        audit.check(sum(t.numel() for t in state.values())==
                    {'mean_message':17857,'graph_attention':17985}[family],label+'.parameters')
    return family,state


def functional_forward(state,batch,family):
    x,src,dst,roles,nodes = (batch[k] for k in ('x','src','dst','roles','nodes'))
    def linear(value,name):
        return F.linear(value,state[name+'.weight'],state[name+'.bias'])
    h = torch.relu(linear(torch.cat((aggregate(x,dst,nodes),aggregate(x,src,nodes),roles),1),'node'))
    e = torch.relu(linear(x,'edge'))
    for layer in range(2):
        message = torch.tanh(linear(torch.cat((h[src],h[dst],e),1),f'message.{layer}'))
        ai = state[f'attention_in.{layer}'] if family=='graph_attention' else None
        ao = state[f'attention_out.{layer}'] if family=='graph_attention' else None
        h = torch.relu(linear(torch.cat((h,aggregate(message,dst,nodes,ai),
                                            aggregate(message,src,nodes,ao)),1),f'update.{layer}'))
    return linear(torch.relu(linear(torch.cat((h[src],h[dst],e,x),1),'decoder')),'output').ravel()


def independent_batches(samples,mean,scale):
    output=[]
    for start in range(0,len(samples),8):
        xs,ss,ds,rs=[],[],[],[]; nodes=0
        for sample in samples[start:start+8]:
            x=(sample['x']-mean)/scale; graph=sample['graph']; n=sample['trip_count']+2
            roles=np.zeros((n,2)); roles[0,0]=roles[-1,1]=1
            xs.append(x); ss.append(graph['src']+nodes); ds.append(graph['dst']+nodes); rs.append(roles); nodes+=n
        output.append({'x':torch.tensor(np.concatenate(xs),dtype=torch.float64),
            'src':torch.tensor(np.concatenate(ss),dtype=torch.long),
            'dst':torch.tensor(np.concatenate(ds),dtype=torch.long),
            'roles':torch.tensor(np.concatenate(rs),dtype=torch.float64),'nodes':nodes})
    return output


def replay(state,graph_batches,family):
    with torch.no_grad():
        logits=np.concatenate([functional_forward(state,b,family).numpy() for b in graph_batches])
        probabilities=np.concatenate([torch.sigmoid(functional_forward(state,b,family)).numpy() for b in graph_batches])
    return logits,probabilities


def weights(samples):
    counts=Counter(s['group'] for s in samples)
    return np.concatenate([np.full(len(s['y']),1/(len(counts)*counts[s['group']]*len(s['y']))) for s in samples])


def metrics(y,p,w,samples=None):
    p=np.clip(np.asarray(p),1e-9,1-1e-9); total=w.sum(); positive=y>.5; negative=~positive; predicted=p>=.5
    order=np.argsort(-p,kind='stable'); sorted_p=p[order]; yy=y[order]; ww=w[order]
    ends=np.r_[np.flatnonzero(np.diff(sorted_p)),len(p)-1]
    tp=np.cumsum(ww*yy)[ends]; denom=np.cumsum(ww)[ends]
    recall=tp/np.sum(w*y); precision=tp/denom
    ap=float(np.sum(np.diff(np.r_[0.,recall])*precision))
    row={'weighted_log_loss':float(np.sum(w*(-y*np.log(p)-(1-y)*np.log1p(-p)))/total),
        'weighted_brier':float(np.sum(w*(p-y)**2)/total),
        'weighted_accuracy_at_fixed_half':float(np.sum(w*(predicted==positive))/total),
        'weighted_positive_recall_at_fixed_half':float(w[predicted&positive].sum()/w[positive].sum()) if positive.any() else None,
        'weighted_negative_recall_at_fixed_half':float(w[(~predicted)&negative].sum()/w[negative].sum()) if negative.any() else None,
        'positive_count':int(positive.sum()),'negative_count':int(negative.sum()),
        'positive_weight':float(w[positive].sum()),'negative_weight':float(w[negative].sum()),
        'average_precision':ap,'positive_rate':float(np.sum(w*y)/total)}
    if samples is not None:
        cursor=0; diagnostic=[]
        for s in samples:
            n=len(s['y']); k=min(s['trip_count'],n); selected=np.argsort(-p[cursor:cursor+n],kind='stable')[:k]
            denom=float(s['y'].sum()); topk=float(s['y'][selected].sum()/denom) if denom else None
            diagnostic.append({'base_group':s['group'],'source':s['source'],'trip_count_input_k':k,
                               'observed_positive_edges':int(denom),'topk_recall':topk}); cursor+=n
        row['input_trip_count_topk_recall_mean_by_fleet']=float(np.mean([r['topk_recall'] for r in diagnostic if r['topk_recall'] is not None]))
        row['topk_by_fleet']=diagnostic
    return row


def macro(rows):
    row={'eligible_units':len(rows)}
    for key in prior.PERFORMANCE_METRICS:
        values=[r[key] for r in rows if r[key] is not None]
        row[key]=float(np.mean(values)) if values else None; row[key+'_eligible_units']=len(values)
    row['positive_count']=sum(r['positive_count'] for r in rows)
    row['negative_count']=sum(r['negative_count'] for r in rows)
    return row


def probability_check(audit,samples,p,saved,label):
    keys=[(s['group'],s['source'],mid,bool(s['y'][i])) for s in samples for i,mid in enumerate(s['movement_ids'])]
    got=[(r['base_group'],r['source'],r['movement_id'],r['observed_selected']) for r in saved]
    audit.check(keys==got,label+'.movement_keys_labels')
    q=np.array([r['probability'] for r in saved]); delta=float(np.max(np.abs(p-q)))
    audit.maximum_deltas['probabilities']=max(audit.maximum_deltas['probabilities'],delta)
    audit.check(delta<=TOLERANCE,label+'.probabilities',{'maximum_absolute_difference':delta})
    audit.check(np.isfinite(p).all() and np.all((p>=0)&(p<=1)),label+'.probability_bounds')
    audit.check(np.array_equal(p>=.5,q>=.5),label+'.fixed_half_decisions')
    cursor=0; ranking_mismatch=0; topk_mismatch=0
    for s in samples:
        n=len(s['y']); a=np.argsort(-p[cursor:cursor+n],kind='stable'); b=np.argsort(-q[cursor:cursor+n],kind='stable')
        ranking_mismatch+=int(not np.array_equal(a,b)); k=min(s['trip_count'],n)
        topk_mismatch+=int(not np.array_equal(a[:k],b[:k])); cursor+=n
    audit.check(ranking_mismatch==0,label+'.full_rankings',ranking_mismatch)
    audit.check(topk_mismatch==0,label+'.topk_rankings',topk_mismatch)
    return {'maximum_probability_difference':delta,'source_rank_mismatches':ranking_mismatch,
            'source_topk_mismatches':topk_mismatch,'movement_rows':len(p)}


def verify_task(task_id,data,launch,audit):
    directory=ATTEMPT/f'task{task_id:02d}'; result=read(directory/'result.json'); receipt=read(directory/'receipt.json')
    identity=read(directory/'source_identity.json'); marker=read(directory/'launch.json')
    label=f'task{task_id:02d}'; before=len(audit.failures)
    audit.check(receipt['status']=='completed' and receipt['task_id']==task_id,label+'.receipt')
    audit.check(sha(directory/'result.json')==receipt['result_sha256'],label+'.result_hash')
    audit.check(sha(directory/'source_identity.json')==receipt['source_identity_sha256'],label+'.identity_hash')
    audit.check(identity==result['source_identity'],label+'.embedded_identity')
    audit.check(identity['source_commit']==launch['source_commit'],label+'.commit')
    audit.check(identity['runtime_versions']==cli.EXPECTED_RUNTIME,label+'.training_runtime')
    audit.check(set(identity['source_hashes'])==set(cli.SOURCE_FILES),label+'.source_file_set')
    for name,digest in identity['source_hashes'].items():
        blob=subprocess.check_output(['git','show',f"{launch['source_commit']}:{name}"],cwd=ROOT)
        audit.check(hashlib.sha256(blob).hexdigest()==digest,label+'.frozen_source.'+name)
        audit.check(sha(ROOT/name)==digest,label+'.live_replay_source.'+name)
    progress=directory/'inner_progress'
    audit.check({p.name for p in progress.iterdir()}==set(receipt['inner_progress_hashes']),label+'.exact_progress_files')
    for name,digest in receipt['inner_progress_hashes'].items():
        audit.check(sha(progress/name)==digest,label+'.progress_hash.'+name)
    wrappers=list(ATTEMPT.glob(f'task{task_id:02d}.slurm_wrapper_receipt.*.json'))
    audit.check(len(wrappers)==1,label+'.wrapper_count'); wrapper=read(wrappers[0])
    audit.check(wrapper['array_job_id']=='722841' and wrapper['returncode']==0 and not wrapper['timeout_exit']
                and wrapper['hostname'].split('.')[0]=='unicorn-cpu-75',label+'.wrapper_identity_status')
    probe=ROOT/wrapper['runtime_probe_path']; audit.check(sha(probe)==wrapper['runtime_probe_sha256'],label+'.probe_hash')
    snapshots=[json.loads(line) for line in probe.read_text().splitlines()]; probe_result=snapshots[-1]
    audit.check(probe_result['status']=='passed' and [s['stage'] for s in probe_result['stages']]==
                ['numpy','scipy','sklearn_joblib','torch','graph_autograd_roundtrip'] and
                all(s['returncode']==0 and s['status']=='passed' for s in probe_result['stages']),label+'.native_probe')
    probe_end=max(s['started_unix']+s['elapsed_seconds'] for s in probe_result['stages'])
    audit.check(probe_end<=marker['started_unix'],label+'.probe_before_bank_launch')
    ordered=tuple(data['groups']); fold,seed_index=divmod(task_id,3)
    outer=tuple(g for i,g in enumerate(ordered) if i%4==fold); training=tuple(g for g in ordered if g not in outer)
    inner=training[2::6]; fit=tuple(g for g in training if g not in inner)
    audit.check((len(fit),len(inner),len(outer))==(80,16,32),label+'.partition_sizes')
    for part,groups in [('fit',fit),('inner',inner),('outer',outer)]:
        audit.check(tuple(result[part+'_groups'])==groups,label+'.'+part+'_groups')
    audit.check(result['seed']==(17,29,43)[seed_index] and result['fold']==fold,label+'.seed_fold')
    audit.check(result['pool_manifest_sha256']==declared.POOL_SHA and identity['pool_manifest_sha256']==declared.POOL_SHA
                and result['pool_table_hashes']==data['table_hashes'],label+'.input_identity')
    audit.check(tuple(result['features'])==tuple(declared.FEATURES) and result['device']=='cpu' and
                result['dtype']=='float64' and result['torch_threads']==result['torch_interop_threads']==1
                and result['width']==32 and result['layers']==2 and result['no_outer_selection'],label+'.fixed_architecture')
    samples={part:[s for s in data['samples'] if s['group'] in groups]
             for part,groups in [('fit',fit),('inner',inner),('outer',outer)]}
    x=np.concatenate([s['x'] for s in samples['fit']]); mean=x.mean(0); scale=x.std(0)
    mean[-1]=0.; scale[-1]=1.; scale[scale<1e-8]=1.
    transform=read(progress/'fit_only_preprocessing_and_groups.json')
    audit.close(transform['mean_fit_only'],mean.tolist(),label+'.fit_only_mean','transform')
    audit.close(transform['scale_fit_only'],scale.tolist(),label+'.fit_only_scale','transform')
    for part in samples:
        audit.close(result['weights'][part],prior._weight_manifest(samples[part]),label+'.'+part+'_weights')
        audit.close(result['eligibility'][part],prior._partition_eligibility(data['group_eligibility'],result[part+'_groups']),label+'.'+part+'_eligibility')
    predictions={}; candidate_checks={}
    graph_batches={part:independent_batches(rows,mean,scale) for part,rows in samples.items()}
    for family in declared.FAMILIES:
        row=result['candidates'][family]; curve=row['train_curves']; losses=[r['inner_weighted_log_loss'] for r in curve]
        audit.check(row['selected_epoch']==int(np.argmin(losses))+1 and row['completed_epochs']==len(curve)<=300,
                    label+'.'+family+'.selected_epoch')
        audit.close(row['inner_weighted_log_loss'],min(losses),label+'.'+family+'.selected_inner_bce')
        best=math.inf
        for i,event in enumerate(curve,1):
            event_path=progress/f'{family}_epoch{i:04d}.json'; saved=read(event_path); checkpoint=saved.pop('checkpoint')
            audit.close(saved,event,label+'.'+family+f'.epoch{i}')
            improved=event['inner_weighted_log_loss']<best
            audit.check(event['epoch']==i and event['selected_so_far']==improved and
                        np.isfinite([event['fit_weighted_log_loss'],event['inner_weighted_log_loss'],event['elapsed_seconds']]).all(),
                        label+'.'+family+f'.epoch{i}.curve')
            audit.check((checkpoint is not None)==improved,label+'.'+family+f'.epoch{i}.checkpoint_rule')
            if checkpoint:
                audit.check(sha(directory/checkpoint['path'])==checkpoint['sha256'],label+'.'+family+f'.epoch{i}.checkpoint_hash')
            if i>1:
                audit.check(event['elapsed_seconds']>=curve[i-2]['elapsed_seconds'],label+'.'+family+f'.epoch{i}.time_order')
            best=min(best,event['inner_weighted_log_loss'])
        if row['stop_reason']=='inner_patience':
            audit.check(len(curve)-row['selected_epoch']==30,label+'.'+family+'.patience')
        elif row['stop_reason']=='epoch_cap':
            audit.check(len(curve)==300,label+'.'+family+'.epoch_cap')
        else:
            audit.check(row['stop_reason'] in ('candidate_time_cap','candidate_time_cap_incomplete_gradient_discarded')
                        and row['fit_and_inner_seconds']>=750,label+'.'+family+'.candidate_budget')
        family_loaded,state=numeric_state(directory/row['saved_model']['path'],audit,label+'.'+family+'.selected')
        best_loaded,best_state=numeric_state(progress/f'{family}_epoch{row["selected_epoch"]:04d}.npz',audit,label+'.'+family+'.best')
        audit.check(family_loaded==best_loaded==family,label+'.'+family+'.architecture')
        audit.check(all(torch.equal(state[k],best_state[k]) for k in state),label+'.'+family+'.selected_equals_best_state')
        audit.check(sha(directory/row['saved_model']['path'])==row['saved_model']['sha256'],label+'.'+family+'.selected_model_hash')
        saved_candidate=read(progress/f'{family}_selected_inner.json'); audit.close(saved_candidate,row,label+'.'+family+'.candidate_receipt')
        checks={}
        for part in ('fit','inner','outer'):
            logits,p=replay(state,graph_batches[part],family)
            if part=='outer':
                saved=[{**r,'probability':r['probabilities'][family]} for r in result['outer_prediction_rows']]
                predictions[family]=p
            else:
                saved=read(progress/f'{family}_{part}_predictions.json')
            checks[part]=probability_check(audit,samples[part],p,saved,label+'.'+family+'.'+part)
            y=np.concatenate([s['y'] for s in samples[part]]); w=weights(samples[part])
            if part!='outer':
                audit.close(metrics(y,p,w,samples[part]),row[part+'_metrics'],label+'.'+family+'.'+part+'_metrics')
                if part=='inner':
                    stable=float(np.sum(w*(np.logaddexp(0.,logits)-y*logits)))
                    audit.close(stable,row['inner_weighted_log_loss'],label+'.'+family+'.stable_inner_bce','stable_bce')
        timers=row['training_timers']; audit.check(all(v>=0 and math.isfinite(v) for v in timers.values()),label+'.'+family+'.timers')
        audit.check(sum(timers.values())<=row['fit_and_inner_seconds']+TOLERANCE,label+'.'+family+'.timer_sum')
        candidate_checks[family]={**checks,'selected_epoch':row['selected_epoch'],'completed_epochs':row['completed_epochs'],
            'stop_reason':row['stop_reason'],'selected_inner_bce':row['inner_weighted_log_loss'],
            'initial_inner_bce':curve[0]['inner_weighted_log_loss'],'last_inner_bce':curve[-1]['inner_weighted_log_loss'],
            'last_fit_bce':curve[-1]['fit_weighted_log_loss'],'training_timers':timers,
            'fit_and_inner_seconds':row['fit_and_inner_seconds'],'fit_selected_prediction_seconds':row['fit_selected_prediction_seconds'],
            'inner_selected_prediction_seconds':row['inner_selected_prediction_seconds']}
    winner=min(declared.FAMILIES,key=lambda f:(result['candidates'][f]['inner_weighted_log_loss'],declared.FAMILIES.index(f)))
    audit.check(result['inner_architecture_promotion']['family']==winner,label+'.inner_promotion')
    audit.check(read(progress/'inner_architecture_promotion.json')==result['inner_architecture_promotion'],label+'.saved_promotion')
    predictions['inner_promoted']=predictions[winner]
    audit.check(all(r['probabilities']['inner_promoted']==r['probabilities'][winner] for r in result['outer_prediction_rows']),label+'.promoted_saved_probabilities')
    per_source=defaultdict(dict); cursor=0
    for s in samples['outer']:
        n=len(s['y']); per_source[s['group']][s['source']]={f:metrics(s['y'],p[cursor:cursor+n],np.ones(n)/n,[s]) for f,p in predictions.items()}; cursor+=n
    per_group={g:{f:macro([source[f] for source in per_source[g].values()]) for f in predictions} for g in outer}
    audit.close(dict(per_source),result['per_group_source_outer_metrics'],label+'.per_source_outer_metrics')
    audit.close(per_group,result['per_group_outer_metrics'],label+'.per_group_outer_metrics')
    for family,p in predictions.items():
        y=np.concatenate([s['y'] for s in samples['outer']]); w=weights(samples['outer'])
        audit.close(metrics(y,p,w,samples['outer']),result['outer_pooled_diagnostics'][family],label+'.'+family+'.outer_pooled_metrics')
        audit.close(macro([per_group[g][family] for g in outer]),result['outer_metrics'][family],label+'.'+family+'.outer_macro')
        common=[g for g in outer if int(g.rsplit('s',1)[-1])<10032]
        audit.close(macro([per_group[g][family] for g in common]),result['common32_outer_metrics'][family],label+'.'+family+'.common32_macro')
    audit.check(0<=result['wall_seconds']<=wrapper['elapsed_seconds']+1,label+'.wall_bounds')
    audit.check(result['progress_persistence_seconds']>=sum(c['training_timers']['epoch_persistence_seconds'] for c in result['candidates'].values()),label+'.persistence_bounds')
    return {'task_id':task_id,'passed':len(audit.failures)==before,'fold':fold,'seed':result['seed'],
        'fit_inner_outer_groups':[len(fit),len(inner),len(outer)],'fit_inner_outer_fleets':[len(samples[p]) for p in ('fit','inner','outer')],
        'result_sha256':receipt['result_sha256'],'receipt_sha256':sha(directory/'receipt.json'),
        'probe_sha256':wrapper['runtime_probe_sha256'],'source_identity_sha256':receipt['source_identity_sha256'],
        'progress_file_count':len(receipt['inner_progress_hashes']),'candidates':candidate_checks,'promoted_family':winner,
        'training_wall_seconds':result['wall_seconds'],'wrapper_elapsed_seconds':wrapper['elapsed_seconds'],
        'outer_inference_seconds_by_family':result['outer_inference_seconds_by_family'],
        'progress_persistence_seconds':result['progress_persistence_seconds'],'group_metrics':per_group}


def group_summary(tasks,audit):
    by_group=defaultdict(list)
    for task in tasks:
        for group,row in task['group_metrics'].items(): by_group[group].append(row)
    audit.check(set(by_group)=={f'physical_v2_s{i}' for i in range(10000,10128)},'aggregate.full128_groups')
    audit.check(all(len(rows)==3 for rows in by_group.values()),'aggregate.three_seeds_per_group')
    per_group={g:{f:{k:float(np.mean([r[f][k] for r in rows])) for k in prior.PERFORMANCE_METRICS}
                  for f in (*declared.FAMILIES,'inner_promoted')} for g,rows in sorted(by_group.items())}
    def means(groups):
        return {f:{k:{'n':len(groups),'mean':float(np.mean([per_group[g][f][k] for g in groups]))}
                     for k in prior.PERFORMANCE_METRICS} for f in (*declared.FAMILIES,'inner_promoted')}
    common=[g for g in per_group if int(g.rsplit('s',1)[-1])<10032]
    return per_group,{'full128':means(list(per_group)),'common32':means(common)}


def baseline_comparisons(per_group,audit):
    names={'v3':'ROUTE_MODEL128_REPLAY.json','v4':'ROUTE_MODEL128_BUDGET_V4_REPLAY.json','v5':'ROUTE_FAMILIES_V5_REPLAY.json'}
    baselines={v:read(DOC/name) for v,name in names.items()}; hashes={v:sha(DOC/name) for v,name in names.items()}
    for v in ('v3','v4'): audit.check(hashes[v]==baselines['v5']['baseline_replay_hashes'][v],'baselines.'+v+'.pinned_replay_hash')
    audit.check(hashes['v3']==baselines['v4']['frozen_v3_replay_sha256'],'baselines.v4_v3_pin')
    summaries={}
    for version,baseline in baselines.items():
        audit.check(baseline['pool_manifest_sha256']==declared.POOL_SHA,'baselines.'+version+'.pool_identity')
        rows=baseline['per_group_seed_and_source_averages']
        audit.check(set(rows)==set(per_group),'baselines.'+version+'.same128_groups')
        summaries[version]={}
        for population,groups in [('full128',list(per_group)),('common32',[g for g in per_group if int(g.rsplit('s',1)[-1])<10032])]:
            base={f:{k:float(np.mean([rows[g][f][k] for g in groups])) for k in PRIMARY} for f in rows[groups[0]]}
            delta={}
            for arm in (*declared.FAMILIES,'inner_promoted'):
                delta[arm]={}
                for comparator in base:
                    delta[arm][comparator]={}
                    for metric in PRIMARY:
                        differences=np.array([per_group[g][arm][metric]-rows[g][comparator][metric] for g in groups])
                        improves=differences<0 if metric in ('weighted_log_loss','weighted_brier') else differences>0
                        delta[arm][comparator][metric]={'n':len(groups),'mean_graph_minus_baseline':float(differences.mean()),
                            'groups_improved':int(improves.sum()),'groups_worsened':int(((differences>0) if metric in ('weighted_log_loss','weighted_brier') else (differences<0)).sum())}
            summaries[version][population]={'baseline_equal_group_means':base,'paired_graph_minus_baseline':delta}
    return hashes,summaries


def run(output):
    if Path(output).exists(): raise ValueError('Replay output is immutable; choose a new explicit path for a further audit')
    started=time.monotonic(); audit=Audit(); declared.configure_cpu()
    launch=read(DOC/'LAUNCH_722841.json'); accounting=read(DOC/'ACCOUNTING_722841.json')
    audit.check(launch['source_commit']=='ca9c3dbbfd22a83c42a8e18465f8524f7f11c98f','launch.frozen_commit')
    audit.check(len(accounting['records'])==12 and all(r['state']=='COMPLETED' and r['exit_code']=='0:0'
                and r['nodes']=='unicorn-cpu-75' for r in accounting['records']),'accounting.completed12')
    audit.check(sum(r['elapsed_seconds'] for r in accounting['records'])==10335==accounting['elapsed_seconds_sum'],'accounting.elapsed')
    audit.check(sum(r['elapsed_seconds']*r['allocated_cpus'] for r in accounting['records'])==10335==accounting['allocated_cpu_seconds_sum'],'accounting.allocated_cpu')
    data=declared.load_pool(ROOT/'result/physical_learning/20260930-route-pool128-v3',expected_manifest_sha256=declared.POOL_SHA)
    audit.check(len(data['groups'])==128 and len(data['samples'])==255,'data.observed_counts')
    audit.check([s['source'] for s in data['samples'] if s['group']=='physical_v2_s10037']==['source1'],'data.registered_censor')
    tasks=[]
    for task_id in range(12):
        try:
            task=verify_task(task_id,data,launch,audit); tasks.append(task)
            print(json.dumps({'task':task_id,'passed':task['passed'],'new_failure_count':len(audit.failures)}),flush=True)
        except Exception as exc:
            audit.check(False,f'task{task_id:02d}.exception',{'type':type(exc).__name__,'message':str(exc)})
    per_group,aggregate_result=group_summary(tasks,audit) if len(tasks)==12 else ({},{})
    baseline_hashes,comparisons=baseline_comparisons(per_group,audit) if per_group else ({},{})
    for t in tasks: t.pop('group_metrics',None)
    output_data={'schema':'graph-v6-independent-saved-state-replay-v1','passed':not audit.failures,
        'checks':audit.checks,'failures':audit.failures,'frozen_absolute_tolerance':TOLERANCE,
        'maximum_observed_absolute_differences':dict(audit.maximum_deltas),
        'runtime':{'python':sys.version,'platform':platform.platform(),'torch':str(torch.__version__),
                   'numpy':np.__version__,'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads()},
        'platform_qualification':'macOS arm64 torch2.4.1 functional float64 CPU replay against Linux x86_64 torch2.4.1+cpu; quantified differences retained; not bitwise-platform qualification',
        'no_fit_or_outer_selection':True,'independent_timetables':128,'observed_source_fleets':255,
        'registered_censor':'10037/source0 missing; source1 retained','seeds_per_group':3,
        'pool_manifest_sha256':declared.POOL_SHA,'launch_sha256':sha(DOC/'LAUNCH_722841.json'),
        'accounting_sha256':sha(DOC/'ACCOUNTING_722841.json'),'elapsed_task_seconds_sum':10335,'allocated_cpu_seconds_sum':10335,
        'script_sha256':sha(__file__),'task_checks':tasks,'baseline_replay_hashes':baseline_hashes,
        'per_group_seed_and_source_averages':per_group,'equal_group_aggregate':aggregate_result,'baseline_comparisons':comparisons,
        'inner_promotion_counts':dict(Counter(t['promoted_family'] for t in tasks)),
        'stop_reason_counts':{f:dict(Counter(t['candidates'][f]['stop_reason'] for t in tasks)) for f in declared.FAMILIES},
        'task_wall_seconds_sum':sum(t['training_wall_seconds'] for t in tasks),
        'candidate_fit_inner_seconds_sum':sum(t['candidates'][f]['fit_and_inner_seconds'] for t in tasks for f in declared.FAMILIES),
        'outer_inference_seconds_sum':{f:sum(t['outer_inference_seconds_by_family'][f] for t in tasks) for f in declared.FAMILIES},
        'replay_wall_seconds':time.monotonic()-started,
        'scope':'Observed feasible incumbent edge imitation only; no route optimality, lower fleet cost, decoder feasibility or online speedup established.'}
    with Path(output).open('x') as stream: json.dump(output_data,stream,sort_keys=True,indent=2,allow_nan=False); stream.write('\n')
    return output_data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,default=DOC/'ROUTE_GRAPH_V6_REPLAY.json')
    args=parser.parse_args(); result=run(args.output)
    print(json.dumps({'passed':result['passed'],'checks':result['checks'],'failures':result['failures'][:10],
                      'maximum_differences':result['maximum_observed_absolute_differences'],'wall_seconds':result['replay_wall_seconds']}))
    sys.exit(0 if result['passed'] else 1)
