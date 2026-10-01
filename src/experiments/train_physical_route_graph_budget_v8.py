"""Immutable v8 fresh graph-budget task; v6 source/verified anchors stay frozen."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import traceback

from egglab import physical_route_graph_budget_v8 as model
from egglab import physical_route_graph_v6 as core
from experiments import train_physical_route_graph_v6 as original
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool

OUTPUT_ROOT=base.ROOT/'result/physical_learning/20261001-route-model128-graph-budget-v8'
SOURCE_FILES=tuple(dict.fromkeys((*original.SOURCE_FILES,
    'src/egglab/physical_route_graph_budget_v8.py','src/experiments/train_physical_route_graph_budget_v8.py',
    'src/tests/test_physical_route_graph_budget_v8.py','src/cluster/physical_route_graph_budget_v8.sbatch',
    'research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_BUDGET_V8_PROTOCOL.md',
    'research-20260930/learning-campaign/ROUTE_GRAPH_V6_REPLAY.json',
    'research-20260930/learning-campaign/LAUNCH_722841.json')))


class Progress(original.Progress):
    """Scalar JSONL every epoch; best weights each50epochs and stop/failure."""
    def start_candidate(self,family,config):
        super().start_candidate(family,{'campaign_policy':model.POLICY,**config})
        with (self.path/f'{family}_epochs.jsonl').open('x'):
            pass

    def snapshot(self,family,suffix,fitted,row=None):
        path=self.path/f'{family}_{suffix}.npz'; self._model(fitted,path)
        evidence={'path':str(path.relative_to(self.path.parent)),'sha256':base.sha(path),
                  'format':'v6 numeric NPZ architecture policy; campaign metadata v8'}
        if row is not None: self._save(self.path/f'{family}_{suffix}.json',{**row,'saved_model':evidence})
        return evidence

    def epoch(self,family,epoch,fitted,row):
        checkpoint=self.snapshot(family,f'periodic_epoch{epoch:04d}_best',fitted) if fitted is not None else None
        path=self.path/f'{family}_epochs.jsonl'
        if not path.exists(): raise ValueError('Epoch stream requires a saved candidate start')
        started=time.monotonic()
        try:
            with path.open('a') as stream:
                stream.write(json.dumps({**row,'persisted_best_checkpoint':checkpoint},sort_keys=True,allow_nan=False)+'\n')
                stream.flush(); os.fsync(stream.fileno())
        finally:
            self.persistence_seconds+=time.monotonic()-started

    def anchor_states(self,family,epoch,current,prefix_best):
        self.snapshot(family,f'anchor{epoch:04d}_current',current)
        self.snapshot(family,f'anchor{epoch:04d}_prefix_best',prefix_best)

    def anchor_check(self,family,row):
        self._save(self.path/f'{family}_anchor_check.json',row)

    def anchor_failure(self,family,row):
        self._save(self.path/f'{family}_handled_failure_anchor_ledger.json',row)

    def stop_state(self,family,fitted,row):
        self.snapshot(family,'stop_best',fitted,row)

    def failure_best(self,family,fitted,row):
        self.snapshot(family,'handled_failure_best',fitted,row)


def run(task_id,pool_manifest_sha256,output_root=None):
    if task_id not in range(12) or pool_manifest_sha256!=core.POOL_SHA:
        raise ValueError('Only pinned exact128 TRAIN/12 tasks are declared')
    destination=Path(output_root or OUTPUT_ROOT).resolve()/f'task{task_id:02d}'
    if destination.exists(): raise ValueError('Immutable v8 task output; no retry or resume')
    started=time.monotonic(); destination.mkdir(parents=True,exist_ok=False); progress=None; identity=None
    try:
        base.save_new(destination/'launch.json',{'policy':model.POLICY,'task_id':task_id,'pool_manifest_sha256':pool_manifest_sha256,
            'v6_replay_sha256':model.V6_REPLAY_SHA,'budget':asdict(model.BUDGET),'started_unix':time.time(),
            'fresh_fit_no_optimizer_resume':True,'launch_before_source_hash_and_data_load':True})
        progress=Progress(destination)
        identity={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=base.ROOT,text=True).strip(),
            'source_hashes':{name:base.sha(base.ROOT/name) for name in SOURCE_FILES},
            'runtime_versions':original.versions(),'platform':platform.platform(),'torch_build':core.torch.__config__.show(),
            'pool_manifest_sha256':pool_manifest_sha256,'v6_source_commit':model.V6_COMMIT,'v6_replay_sha256':model.V6_REPLAY_SHA}
        base.save_new(destination/'source_identity.json',identity)
        if original.versions()!=original.EXPECTED_RUNTIME: raise ValueError('Pinned Linux CPU graph runtime differs')
        if base.sha(base.ROOT/'research-20260930/learning-campaign/ROUTE_GRAPH_V6_REPLAY.json')!=model.V6_REPLAY_SHA:
            raise ValueError('Pinned v6 replay changed')
        core.configure_cpu()
        dataset=core.load_pool(pool.OUTPUTS[128],expected_manifest_sha256=pool_manifest_sha256)
        result=model.run_fold(dataset,task_id,progress,base.ROOT)
        result.update({'wall_seconds':time.monotonic()-started,'source_identity':identity})
        base.save_new(destination/'result.json',result)
        base.save_new(destination/'receipt.json',{'policy':model.POLICY,'task_id':task_id,'status':'completed',
            'pool_manifest_sha256':pool_manifest_sha256,'v6_replay_sha256':model.V6_REPLAY_SHA,
            'both300_anchors_verified':True,'result_sha256':base.sha(destination/'result.json'),
            'source_identity_sha256':base.sha(destination/'source_identity.json'),
            'inner_progress_hashes':progress.hashes(),'wall_seconds':result['wall_seconds']})
        return {'task_id':task_id,'output':str(destination),'wall_seconds':result['wall_seconds']}
    except BaseException as exc:
        base.save_new(destination/'failure.json',{'type':type(exc).__name__,'message':str(exc),
            'traceback':traceback.format_exc(),'wall_seconds':time.monotonic()-started})
        base.save_new(destination/'receipt.json',{'policy':model.POLICY,'task_id':task_id,'status':'failed',
            'source_identity':identity,'failure_sha256':base.sha(destination/'failure.json'),
            'inner_progress_hashes':progress.hashes() if progress else {},'wall_seconds':time.monotonic()-started})
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id',type=int,required=True); parser.add_argument('--pool-manifest-sha256',required=True)
    parser.add_argument('--output-root',type=Path); args=parser.parse_args(argv)
    print(json.dumps(run(args.task_id,args.pool_manifest_sha256,args.output_root),sort_keys=True))


if __name__=='__main__': main()
