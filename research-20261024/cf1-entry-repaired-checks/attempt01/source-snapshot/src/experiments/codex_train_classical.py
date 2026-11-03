"""Bounded grouped classical baselines; frozen protocol in research-20261017/classical-training."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import time
import traceback
import warnings

import numpy as np
from egglab import learned_proposals as edge
from egglab import physical_route_model_v2 as frozen
from egglab import physical_route_model_v3 as previous
from egglab import physical_route_model_families_v5 as families

SEED = 17
MENU = {'logistic': ({'C': .1}, {'C': 1.}), 'catboost': ({'depth': 4}, {'depth': 6})}
QUALIFICATION = 'Exploratory historical TRAIN-bank grouped CV; single feasible-incumbent labels, not optimum; no independent benchmark.'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def assert_manifest(pool):
    manifest = json.loads((pool/'pool_manifest.json').read_text())
    if manifest.get('train_only') is not True or manifest.get('base_ids') != list(range(10000,10128)):
        raise ValueError('Refuse pool outside exact whitelisted TRAIN IDs')
    return manifest

def fit_logistic(config, fit, inner):
    from sklearn.linear_model import LogisticRegression
    started=time.monotonic()
    x,y,w=fit; ix,iy,iw=inner
    model=LogisticRegression(C=config['C'],solver='lbfgs',max_iter=2000,tol=1e-7,random_state=SEED,n_jobs=1)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always'); model.fit(x,y,sample_weight=families._weighted_for_library(w))
    row={'config':config,'warnings':[str(item.message) for item in caught], 'iterations':model.n_iter_.tolist(),
         'fit_metrics':frozen._metrics(y,model.predict_proba(x)[:,1],w),
         'inner_metrics':frozen._metrics(iy,model.predict_proba(ix)[:,1],iw),
         'fit_and_inner_seconds':time.monotonic()-started,'fitted_parameters':model.get_params()}
    return model,row

def score_case(case, prices, model_dir, arm):
    """Return aligned raw logits using frozen selected fit-only model; no solver."""
    started=time.monotonic(); folder=Path(model_dir)/arm
    metadata=json.loads((folder/'metadata.json').read_text()); pre=json.loads((folder/'preprocessing.json').read_text())
    if tuple(pre['features']) != tuple(edge.FEATURES): raise ValueError('feature ordering changed')
    load_started=time.monotonic()
    x=(edge.edge_features(case,prices)-np.asarray(pre['mean_fit_only']))/np.asarray(pre['scale_fit_only'])
    if arm=='catboost':
        from catboost import CatBoostClassifier
        model=CatBoostClassifier(); model.load_model(str(folder/'model.cbm'))
        loaded=time.monotonic(); logits=np.asarray(model.predict(x,prediction_type='RawFormulaVal',thread_count=1),dtype=float)
    elif arm=='logistic':
        import joblib
        model=joblib.load(folder/'model.joblib'); loaded=time.monotonic(); logits=np.asarray(model.decision_function(x),dtype=float)
    else: raise ValueError('Unknown classical arm')
    if logits.shape != (len(case.movements),) or not np.isfinite(logits).all(): raise ValueError('Invalid aligned finite logits')
    return {'movement_ids':[m.id for m in case.movements], 'case_identity':case.identity(), 'logits':logits.tolist(),
            'score_seconds':time.monotonic()-started,'cold_load_seconds':loaded-load_started,'inference_seconds':time.monotonic()-loaded,'model_metadata':metadata}

def train(args):
    from threadpoolctl import threadpool_limits
    import joblib
    out=args.output; out.mkdir(parents=True,exist_ok=False)
    wall=time.monotonic(); cpu=time.process_time()
    receipt={'policy':'codex-classical-frozen-task00-seed17','qualification':QUALIFICATION,'seed':SEED,'menu':MENU,
             'failures':[], 'candidates':{},'selection':{},'versions':{p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-learn','catboost','joblib')},
             'limits':{'wall_seconds':1200,'cpu_seconds':1800,'threads':1},'thread_env':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')}}
    def timed_out(signum,frame): raise TimeoutError('Frozen initial wall/CPU budget exhausted')
    signal.signal(signal.SIGALRM,timed_out); signal.alarm(1200)
    resource.setrlimit(resource.RLIMIT_CPU,(1800,1801))
    signal.signal(signal.SIGXCPU,timed_out)
    try:
        manifest=assert_manifest(args.pool)
        receipt['hashes']={str(p):sha(p) for p in (args.pool/'pool_manifest.json', args.split,Path(__file__),Path('src/egglab/learned_proposals.py'),Path('src/egglab/physical_route_model_v2.py'),Path('src/egglab/physical_route_model_v3.py'),Path('src/egglab/physical_route_model_families_v5.py'),Path('research-20261017/classical-training/PROTOCOL.md'))}
        dataset=previous.load_pool(args.pool,expected_manifest_sha256=sha(args.pool/'pool_manifest.json'),prefix=128)
        receipt['pool_table_hashes']=dataset['table_hashes']; receipt['eligibility']=dataset['group_eligibility']
        pre=json.loads(args.split.read_text())
        expected=previous.grouped_split(dataset['groups'],0)
        for key,groups in zip(('fit_groups','inner_groups','outer_groups'),expected):
            if pre[key]!=list(groups): raise ValueError('v8 split mismatch '+key)
        if tuple(pre['features'])!=tuple(edge.FEATURES): raise ValueError('v8 features mismatch')
        fit=[s for s in dataset['samples'] if s['group'] in pre['fit_groups']]
        inner=[s for s in dataset['samples'] if s['group'] in pre['inner_groups']]
        fx,fy,fw=previous._stack(fit); ix,iy,iw=previous._stack(inner)
        mean,scale=frozen._preprocess(fx)
        if not np.allclose(mean,pre['mean_fit_only'],rtol=0,atol=1e-12) or not np.allclose(scale,pre['scale_fit_only'],rtol=0,atol=1e-12): raise ValueError('fit preprocessing differs from v8')
        pre['pool_manifest_sha256']=sha(args.pool/'pool_manifest.json'); write(out/'preprocessing.json',pre)
        receipt['split']=pre; receipt['sample_counts']={'fit':len(fit),'inner':len(inner)}
        selected={}
        with threadpool_limits(limits=1):
            for arm,configs in MENU.items():
                rows=[]; models=[]; receipt['candidates'][arm]=rows
                for index,config in enumerate(configs):
                    receipt['active_candidate']={'arm':arm,'index':index,'config':config}; write(out/'receipt.json',receipt)
                    folder=out/f'{arm}-candidate{index}'; folder.mkdir()
                    if arm=='logistic': model,row=fit_logistic(config,((fx-mean)/scale,fy,fw),((ix-mean)/scale,iy,iw))
                    else: model,row=families.fit_candidate('catboost',config,(fx-mean)/scale,fy,fw,(ix-mean)/scale,iy,iw,SEED)
                    row['candidate_index']=index
                    if arm=='logistic': joblib.dump(model,folder/'model.joblib')
                    else: model.save_model(str(folder/'model.cbm'))
                    row['model_sha256']=sha(folder/('model.joblib' if arm=='logistic' else 'model.cbm'))
                    write(folder/'metrics.json',row); rows.append(row); models.append(model); write(out/'receipt.json',receipt)
                winner=families.select_candidate(rows); selected[arm]=models[winner]
                receipt['selection'][arm]={'candidate_index':winner,'config':configs[winner],'inner_weighted_log_loss':rows[winner]['inner_metrics']['weighted_log_loss']}
                folder=out/arm; folder.mkdir(); filename='model.joblib' if arm=='logistic' else 'model.cbm'
                shutil.copyfile(out/f'{arm}-candidate{winner}'/filename,folder/filename); write(folder/'preprocessing.json',pre)
                write(folder/'metadata.json',{'arm':arm,'seed':SEED,'selection':receipt['selection'][arm], 'qualification':QUALIFICATION,'model_sha256':sha(folder/filename),'training_source_hashes':receipt['hashes'],'pool_table_hashes':receipt['pool_table_hashes'],'features':pre['features']})
                write(out/'receipt.json',receipt)
            receipt['selection_frozen_before_outer']=True; write(out/'receipt.json',receipt)
            outer=[s for s in dataset['samples'] if s['group'] in pre['outer_groups']]
            ox,oy,ow=previous._stack(outer); oz=(ox-mean)/scale
            receipt['outer_exploratory']={}; predictions={}
            for arm,model in selected.items():
                prob=model.predict_proba(oz,thread_count=1)[:,1] if arm=='catboost' else model.predict_proba(oz)[:,1]
                receipt['outer_exploratory'][arm]=frozen._metrics(oy,prob,ow,outer)
                per_group={};cursor=0
                for sample in outer:
                    n=len(sample['y']); pp=prob[cursor:cursor+n]; cursor+=n
                    per_group.setdefault(sample['group'],[]).append(frozen._metrics(sample['y'],pp,np.ones(n)/n,[sample]))
                    predictions.setdefault(arm,[]).append({'group':sample['group'],'source':sample['source'],'movement_ids':sample['movement_ids'],'probabilities':pp.tolist()})
                receipt['outer_exploratory'][arm]['per_group']={g:previous._macro_metrics(rs) for g,rs in per_group.items()}
                receipt['outer_exploratory'][arm]['macro_by_group']=previous._macro_metrics([previous._macro_metrics(rs) for rs in per_group.values()])
            write(out/'outer_exploratory_predictions.json',predictions)
    except BaseException:
        receipt['failures'].append(traceback.format_exc())
    finally:
        signal.alarm(0); receipt['wall_seconds']=time.monotonic()-wall;receipt['cpu_seconds']=time.process_time()-cpu
        write(out/'receipt.json',receipt)
    if receipt['failures']: raise SystemExit(1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pool',type=Path,required=True);ap.add_argument('--split',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    train(ap.parse_args())
if __name__=='__main__':main()
