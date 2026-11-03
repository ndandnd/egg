"""Immutable v9 matched feature/architecture task; wrapper owns native qualification."""
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

from egglab import physical_route_graph_context_v9 as model
from experiments import computational_benchmark as base
from experiments import pool_physical_route_training_v3 as pool
from experiments import train_physical_route_graph_v6 as original

OUTPUT_ROOT = base.ROOT/"result/physical_learning/20261001-route-model128-graph-context-v9"
SOURCE_FILES = tuple(dict.fromkeys((*original.SOURCE_FILES,
    "src/egglab/native_hull.py", "src/egglab/physical_context_features_v9.py",
    "src/egglab/physical_route_graph_context_v9.py", "src/experiments/train_physical_route_graph_context_v9.py",
    "src/tests/test_physical_route_graph_context_v9.py", "src/cluster/physical_route_graph_context_v9.sbatch",
    "src/tests/test_physical_route_graph_context_v9_wrapper.py",
    "research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_CONTEXT_V9_PROTOCOL.md",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_PROTOCOL.md",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_REVIEW.md",
    "research-20260930/learning-campaign/inventory_physical_context_v9.py",
    "src/tests/test_physical_context_v9_inventory.py",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY_REPORT.md",
    "research-20260930/learning-campaign/ROUTE_MODEL_GRAPH_CONTEXT_V9_INPUTS.json",
    "research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY_REVIEW.md")))


class Progress(original.Progress):
    """Append-only scalar curves, sparse best weights, immutable selected artifacts."""
    def _model(self,fitted,path):
        started=time.monotonic()
        try: model.save_model(fitted,path)
        finally: self.persistence_seconds+=time.monotonic()-started

    def snapshot(self,arm,suffix,fitted,row=None):
        path=self.path/f"{arm}_{suffix}.npz"; self._model(fitted,path)
        evidence={"path":str(path.relative_to(self.path.parent)),"sha256":base.sha(path),
                  "format":"v9 numeric float64 NPZ; allow_pickle=False; no optimizer state"}
        if row is not None: self._save(self.path/f"{arm}_{suffix}.json",{**row,"saved_model":evidence})
        return evidence

    def initialization(self,models,checks,order,seed):
        weights={arm:self.snapshot(arm,"initial",models[arm]) for arm in model.ARMS}
        self._save(self.path/"paired_initialization_and_arm_order.json",{
            "checks":checks,"models":weights,"arm_order":order,"seed":seed,
            "order_policy":"SHA256(policy:task) ranking then rank modulo4 cyclic canonical arms",
            "historical17_anchor":False,"new_matched38_baseline":True})

    def start_candidate(self,arm,config):
        feature,family=model.arm_parts(arm)
        self._save(self.path/f"{arm}_start.json",{"arm":arm,"feature_arm":feature,"family":family,
            "config":config,"started_unix":time.time()})
        with (self.path/f"{arm}_epochs.jsonl").open("x"): pass

    def epoch(self,arm,epoch,fitted,row):
        if not (self.path/f"{arm}_epochs.jsonl").is_file():
            raise ValueError("Scalar stream requires immutable candidate start")
        checkpoint=self.snapshot(arm,f"periodic_epoch{epoch:04d}_best",fitted) if fitted is not None else None
        started=time.monotonic()
        try:
            with (self.path/f"{arm}_epochs.jsonl").open("a") as stream:
                stream.write(json.dumps({**row,"persisted_best_checkpoint":checkpoint},sort_keys=True,allow_nan=False)+"\n")
                stream.flush(); os.fsync(stream.fileno())
        finally: self.persistence_seconds+=time.monotonic()-started

    def stop_state(self,arm,fitted,row): self.snapshot(arm,"stop_best",fitted,row)
    def failure_best(self,arm,fitted,row): self.snapshot(arm,"handled_failure_best",fitted,row)
    def arm_failure(self,arm,row): self._save(self.path/f"{arm}_failure.json",row)

    def promotion(self,row): self._save(self.path/"inner_policy_promotion.json",row)
    def qualification(self,row): self._save(self.path/"matched_pair_qualification.json",row)
    def fold_censor(self,row): self._save(self.path/"fold_censoring.json",{**row,"fold_censored":True,"outer_admission":False})


def run(task_id,pool_manifest_sha256,output_root=None):
    if type(task_id) is not int or task_id not in range(12) or pool_manifest_sha256 != model.core.POOL_SHA:
        raise ValueError("Only frozen v9 exact128TRAIN/12tasks")
    destination=Path(output_root or OUTPUT_ROOT).resolve()/f"task{task_id:02d}"
    if destination.exists(): raise ValueError("Immutable v9 task output; no retry or optimizer resume")
    started=time.monotonic(); destination.mkdir(parents=True,exist_ok=False)
    identity,progress=None,None
    try:
        base.save_new(destination/"launch.json",{"policy":model.POLICY,"task_id":task_id,
            "pool_manifest_sha256":pool_manifest_sha256,"input_inventory_sha256":model.INVENTORY_SHA,
            "feature_source_sha256":model.FEATURE_SHA,"budget":asdict(model.BUDGET),
            "arm_order":model.task_arm_order(task_id),"started_unix":time.time(),
            "launch_before_source_hash_and_bank_read":True,"historical17_anchor":False})
        progress=Progress(destination)
        identity={"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=base.ROOT,text=True).strip(),
            "source_hashes":{name:base.sha(base.ROOT/name) for name in SOURCE_FILES},
            "runtime_versions":original.versions(),"platform":platform.platform(),"torch_build":model.core.torch.__config__.show(),
            "pool_manifest_sha256":pool_manifest_sha256,"input_inventory_sha256":model.INVENTORY_SHA,
            "feature_source_sha256":model.FEATURE_SHA,"arm_order":model.task_arm_order(task_id)}
        base.save_new(destination/"source_identity.json",identity)
        if original.versions() != original.EXPECTED_RUNTIME: raise ValueError("Pinned Linux CPU v9 runtime differs")
        if identity["source_hashes"]["src/egglab/physical_context_features_v9.py"] != model.FEATURE_SHA:
            raise ValueError("Frozen v9 feature source differs")
        if identity["source_hashes"]["research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json"] != model.INVENTORY_SHA:
            raise ValueError("Admitted fit-only inventory differs")
        model.core.configure_cpu()
        before=time.monotonic()
        dataset=model.InputPool(pool.OUTPUTS[128],expected_manifest_sha256=pool_manifest_sha256,root=base.ROOT)
        admission_seconds=time.monotonic()-before
        result=model.run_fold(dataset,task_id,progress,task_deadline=started+model.BUDGET.fold_seconds)
        result.update(wall_seconds=time.monotonic()-started,source_identity=identity,header_admission_seconds=admission_seconds)
        before=time.monotonic(); base.save_new(destination/"result.json",result)
        result_persistence_seconds=time.monotonic()-before
        base.save_new(destination/"receipt.json",{"policy":model.POLICY,"task_id":task_id,"status":"completed",
            "pool_manifest_sha256":pool_manifest_sha256,"input_inventory_sha256":model.INVENTORY_SHA,
            "source_identity_sha256":base.sha(destination/"source_identity.json"),"result_sha256":base.sha(destination/"result.json"),
            "inner_progress_hashes":progress.hashes(),"all_four_selected_before_outer":True,
            "candidate_stop_reasons":{arm:row["stop_reason"] for arm,row in result["candidates"].items()},
            "candidate_time_cap_sources":{arm:row.get("time_cap_source") for arm,row in result["candidates"].items()},
            "matched_pair_qualification":result["matched_pair_qualification"],
            "result_persistence_seconds":result_persistence_seconds,"wall_seconds":time.monotonic()-started,
            "requires_independent_saved_model_replay":True,"historical17_anchor":False})
        return {"task_id":task_id,"output":str(destination),"wall_seconds":time.monotonic()-started}
    except BaseException as exc:
        base.save_new(destination/"failure.json",{"type":type(exc).__name__,"message":str(exc),
            "traceback":traceback.format_exc(),"wall_seconds":time.monotonic()-started})
        base.save_new(destination/"receipt.json",{"policy":model.POLICY,"task_id":task_id,"status":"failed",
            "source_identity":identity,"failure_sha256":base.sha(destination/"failure.json"),
            "inner_progress_hashes":progress.hashes() if progress else {},"wall_seconds":time.monotonic()-started,
            "no_partial_task_promotion_or_admission":True,"fold_censored":isinstance(exc,model.FoldCensored)})
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id",type=int,required=True)
    parser.add_argument("--pool-manifest-sha256",required=True)
    parser.add_argument("--output-root",type=Path)
    args=parser.parse_args(argv)
    print(json.dumps(run(args.task_id,args.pool_manifest_sha256,args.output_root),sort_keys=True))


if __name__ == "__main__": main()
