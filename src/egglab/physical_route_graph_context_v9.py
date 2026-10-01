"""New matched38-input graph ablation; frozen v6/v8 code is unchanged.

The two feature arms share tensor shapes, initial tensors and the scaled17
prefix. Only fit/inner inputs enter preprocessing, training and selection.
This is fresh training, with no historical17-dimensional trajectory anchor.
"""
from __future__ import annotations

from collections import defaultdict
import copy
from dataclasses import asdict, dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from egglab import physical_context_features_v9 as context
from egglab import physical_learning_cases as physical
from egglab import physical_route_graph_v6 as core
from egglab import native_recharge as nr

POLICY = "physical-source-movement-graph-context-exact128-v9"
FEATURES = context.FEATURES
FEATURE_ARMS = ("padded17", "physical38")
FAMILIES = core.FAMILIES
ARMS = tuple(f"{feature}__{family}" for feature in FEATURE_ARMS for family in FAMILIES)
WIDTH, LAYERS, PARAMETER_CEILING = 32, 2, 20700
EXPECTED_PARAMETERS = {"mean_message":20545, "graph_attention":20673}
INTERCEPT_INDEX = 16
FEATURE_SHA = "a83c629902a6e704010b02c0c3b22e0ebbdb99351126af20fa78055ee208c33f"
INVENTORY_SHA = "1e096c5e34edab7a142fe0afa9f43f1b5e3b24f07658894967b06f8bc3447963"


@dataclass(frozen=True)
class Budget:
    max_epochs: int = 900
    candidate_seconds: float = 1600.
    fold_seconds: float = 6900.
    save_every: int = 50

    def __post_init__(self):
        if (type(self.max_epochs) is not int or self.max_epochs < 1
                or type(self.save_every) is not int or self.save_every < 1
                or not 0 < self.candidate_seconds < self.fold_seconds
                or not np.isfinite([self.candidate_seconds,self.fold_seconds]).all()):
            raise ValueError("Invalid declared v9 training budget")


BUDGET = Budget()


class FoldCensored(TimeoutError):
    """Preserved partial task; no matched feature or promoted OUTER admission."""
    pass


def task_arm_order(task_id):
    if type(task_id) is not int or task_id not in range(12): raise ValueError("Undeclared v9 task")
    ranked = sorted(range(12),key=lambda task:hashlib.sha256(f"{POLICY}:{task}".encode()).hexdigest())
    rotation = ranked.index(task_id) % 4
    return ARMS[rotation:]+ARMS[:rotation]


def arm_parts(arm):
    if arm not in ARMS: raise ValueError("Unknown matched feature/architecture arm")
    return tuple(arm.split("__",1))


class GraphScorer(core.GraphScorer):
    """Reuse v6 forward equations explicitly, with new38-dimensional layers."""
    def __init__(self,family,feature_arm):
        nn.Module.__init__(self)
        if family not in FAMILIES or feature_arm not in FEATURE_ARMS: raise ValueError("Unknown v9 arm")
        self.family, self.feature_arm = family, feature_arm
        self.node = nn.Linear(2*len(FEATURES)+2,WIDTH)
        self.edge = nn.Linear(len(FEATURES),WIDTH)
        self.message = nn.ModuleList(nn.Linear(3*WIDTH,WIDTH) for _ in range(LAYERS))
        self.update = nn.ModuleList(nn.Linear(3*WIDTH,WIDTH) for _ in range(LAYERS))
        if family == "graph_attention":
            self.attention_in = nn.ParameterList(nn.Parameter(torch.zeros(WIDTH)) for _ in range(LAYERS))
            self.attention_out = nn.ParameterList(nn.Parameter(torch.zeros(WIDTH)) for _ in range(LAYERS))
        self.decoder = nn.Linear(3*WIDTH+len(FEATURES),WIDTH)
        self.output = nn.Linear(WIDTH,1)
        self.to(device="cpu",dtype=core.DTYPE)
        self.parameter_count = sum(parameter.numel() for parameter in self.parameters())
        if self.parameter_count != EXPECTED_PARAMETERS[family] or self.parameter_count > PARAMETER_CEILING:
            raise ValueError("Matched38 graph parameter budget differs")


def tensor_sha(model):
    digest = hashlib.sha256()
    for name,tensor in sorted(model.state_dict().items()):
        array = tensor.detach().cpu().numpy()
        digest.update(name.encode()); digest.update(str(array.shape).encode())
        digest.update(array.dtype.str.encode()); digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def paired_initial_models(seed):
    models, checks = {}, {}
    for family in FAMILIES:
        torch.manual_seed(seed)
        prototype = GraphScorer(family,"padded17")
        for feature_arm in FEATURE_ARMS:
            model = copy.deepcopy(prototype); model.feature_arm = feature_arm
            models[f"{feature_arm}__{family}"] = model
        left, right = (models[f"{feature}__{family}"] for feature in FEATURE_ARMS)
        if not all(torch.equal(value,right.state_dict()[key]) for key,value in left.state_dict().items()):
            raise ValueError("Paired initial graph tensors differ")
        checks[family] = {"paired_initial_tensors_identical":True,"maximum_tensor_difference":0.,
            "initial_tensor_sha256":tensor_sha(left),"parameter_count":left.parameter_count,
            "inactive_padded_input_weights":2688,"historical17_anchor":False}
    return models, checks


def save_model(model,path):
    values = {name:tensor.detach().cpu().numpy() for name,tensor in model.state_dict().items()}
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream,**values,architecture=np.asarray(model.family),
            feature_arm=np.asarray(model.feature_arm),features=np.asarray(FEATURES),policy=np.asarray(POLICY))


def restore_model(path):
    with np.load(path,allow_pickle=False) as data:
        if str(data["policy"]) != POLICY or tuple(data["features"].tolist()) != FEATURES:
            raise ValueError("Unknown v9 model feature/policy identity")
        model = GraphScorer(str(data["architecture"]),str(data["feature_arm"]))
        expected = model.state_dict()
        if set(data.files) != set(expected)|{"architecture","feature_arm","features","policy"}:
            raise ValueError("v9 checkpoint tensor set differs")
        state = {}
        for name,tensor in expected.items():
            value = data[name]
            if value.shape != tuple(tensor.shape) or value.dtype != np.dtype("float64") or not np.isfinite(value).all():
                raise ValueError("Malformed v9 numeric checkpoint tensor")
            state[name] = torch.as_tensor(value,dtype=core.DTYPE)
        model.load_state_dict(state,strict=True)
    return model.eval()


def preprocess(fit_samples):
    x = np.concatenate([sample["x"] for sample in fit_samples])
    if x.ndim != 2 or x.shape[1] != len(FEATURES) or not np.isfinite(x).all():
        raise ValueError("Invalid fit-only physical38 inputs")
    mean,scale = x.mean(axis=0),x.std(axis=0)
    exact_constant = np.ptp(x,axis=0) == 0.
    mean[exact_constant] = x[0,exact_constant]
    scale[scale<1e-8] = 1.
    # Historical intercept is column16, not the final38-input column.
    prefix_mean,prefix_scale = core.frozen._preprocess(x[:,:17])
    mean[:17],scale[:17] = prefix_mean,prefix_scale
    if mean[INTERCEPT_INDEX] != 0. or scale[INTERCEPT_INDEX] != 1.:
        raise ValueError("Historical intercept transform changed")
    return {"mean":mean,"scale":scale,"exact_constant_fit_columns":exact_constant}


def scaled_features(x,transform,feature_arm):
    if feature_arm not in FEATURE_ARMS: raise ValueError("Unknown feature arm")
    x = np.asarray(x,dtype=float)
    if x.ndim != 2 or x.shape[1] != len(FEATURES) or not np.isfinite(x).all():
        raise ValueError("Malformed raw physical38 matrix")
    mean,scale = np.asarray(transform["mean"]),np.asarray(transform["scale"])
    if mean.shape != (38,) or scale.shape != (38,) or not np.isfinite(mean).all() or not np.isfinite(scale).all() or np.any(scale<=0):
        raise ValueError("Malformed fit-only transform")
    result = (x-mean)/scale
    if feature_arm == "padded17": result[:,17:] = 0.
    if not np.isfinite(result).all(): raise ValueError("Nonfinite scaled v9 features")
    return result


def batches(samples,transform,feature_arm,*,labelled):
    """Identical v6 disconnected batching/weights; explicitly38 input columns."""
    if not samples: raise ValueError("Empty grouped graph partition")
    counts = defaultdict(int)
    for sample in samples: counts[sample["group"]] += 1
    output = []
    for begin in range(0,len(samples),core.GRAPH_BATCH):
        xs,srcs,dsts,roles,ys,weights,offset = [],[],[],[],[],[],0
        for sample in samples[begin:begin+core.GRAPH_BATCH]:
            x = scaled_features(sample["x"],transform,feature_arm); graph = sample["graph"]
            src,dst,nodes = np.asarray(graph["src"]),np.asarray(graph["dst"]),graph["nodes"]
            if (not len(x) or nodes != sample["trip_count"]+2 or src.shape != (len(x),) or dst.shape != (len(x),)
                    or src.dtype.kind not in "iu" or dst.dtype.kind not in "iu"
                    or np.any(src<0) or np.any(dst<0) or np.any(src>=nodes) or np.any(dst>=nodes)):
                raise ValueError("Malformed disconnected movement graph")
            xs.append(x); srcs.append(src+offset); dsts.append(dst+offset)
            role = np.zeros((nodes,2)); role[0,0],role[-1,1] = 1.,1.; roles.append(role)
            if labelled:
                y = np.asarray(sample["y"],dtype=float)
                if y.shape != (len(x),) or not np.isin(y,(0.,1.)).all(): raise ValueError("Invalid incumbent imitation labels")
                ys.append(y); weights.append(np.full(len(x),1/(len(counts)*counts[sample["group"]]*len(x))))
            offset += nodes
        batch = {"x":torch.as_tensor(np.concatenate(xs),dtype=core.DTYPE),
            "src":torch.as_tensor(np.concatenate(srcs),dtype=torch.long),
            "dst":torch.as_tensor(np.concatenate(dsts),dtype=torch.long),
            "roles":torch.as_tensor(np.concatenate(roles),dtype=core.DTYPE),"nodes":offset}
        if labelled:
            batch.update(y=torch.as_tensor(np.concatenate(ys),dtype=core.DTYPE),
                         w=torch.as_tensor(np.concatenate(weights),dtype=core.DTYPE))
        output.append(batch)
    return output


def paired_batch_checks(left,right):
    if len(left) != len(right): raise ValueError("Paired graph batches differ")
    for padded,actual in zip(left,right):
        if not torch.equal(padded["x"][:,:17],actual["x"][:,:17]) or torch.count_nonzero(padded["x"][:,17:]):
            raise ValueError("Paired scaled prefix/padding differs")
        for key in ("src","dst","roles","y","w"):
            if key in padded and not torch.equal(padded[key],actual[key]): raise ValueError("Paired graph/labels/weights differ")
        if padded["nodes"] != actual["nodes"]: raise ValueError("Paired graph offsets differ")
    return {"prefix17_scaled_identical":True,"padded21_exact_zero":True,"graph_labels_weights_identical":True,
            "batch_count":len(left),"maximum_prefix_difference":0.}


def input_inventory(root):
    root = Path(root)
    path = root/"research-20260930/learning-campaign/PHYSICAL_CONTEXT_FEATURE_V9_FIT_INVENTORY.json"
    if core.frozen._sha(path) != INVENTORY_SHA or core.frozen._sha(root/"src/egglab/physical_context_features_v9.py") != FEATURE_SHA:
        raise ValueError("Reviewed v9 feature/inventory identity changed")
    inventory = core.frozen._read(path)
    if inventory.get("passed") is not True: raise ValueError("No admitted fit-only input inventory")
    for name,digest in inventory["source_hashes"].items():
        if core.frozen._sha(root/name) != digest: raise ValueError("Inventory-bound source changed: "+name)
    spec = importlib.util.spec_from_file_location("v9_input_registry",root/"research-20260930/learning-campaign/inventory_physical_context_v9.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class InputPool:
    """Header-only admission. Full source labels/features are loaded per partition."""
    def __init__(self,path,*,expected_manifest_sha256,root):
        if expected_manifest_sha256 != core.POOL_SHA: raise ValueError("Only exact128 pinned TRAIN pool")
        inventory = input_inventory(root)
        self.inputs = inventory.load_input_registry(path,128,expected_manifest_sha256)
        self.groups = tuple(sorted(self.inputs["cases"]))
        self.manifest_sha256 = expected_manifest_sha256
        self.table_hashes = self.inputs["table_sha256"]
        self.group_eligibility = core.frozen._read(Path(path)/"pool_manifest.json")["group_eligibility"]
        self.lines = {}
        with (Path(path)/"source_inputs.jsonl").open() as stream:
            for line in stream:
                if not line.strip(): continue
                header = inventory.registry_projection(line,inventory.SOURCE_REGISTRY_FIELDS)
                self.lines[header["base_group"],header["source"]] = line
        self.root = Path(root)

    def load_samples(self,groups):
        allowed = set(groups)
        if not allowed or not allowed<=set(self.groups): raise ValueError("Unknown grouped partition")
        cases, samples = {}, []
        for pair,header in self.inputs["sources"].items():
            group,source = pair
            if group not in allowed: continue
            if group not in cases:
                case = physical.make_case(self.inputs["cases"][group]["base_id"])
                if case.identity() != self.inputs["cases"][group]["case_identity"]: raise ValueError("Case identity differs")
                cases[group] = case
            case = cases[group]; market = physical.market(case,source)
            if market.identity() != header["market_identity"]: raise ValueError("Source market identity differs")
            row = json.loads(self.lines[pair]); plan = row["source_plan"]
            if nr.digest(plan) != row.get("source_plan_hash"): raise ValueError("Source label plan hash differs")
            selected = {mid for vehicle in plan["vehicles"] for mid in vehicle["movements"]}
            if selected != set(row["selected_movements"]): raise ValueError("Source label topology differs")
            x = context.edge_features(case,market)
            if not np.array_equal(x[:,:17],core.edge.edge_features(case,market.a)): raise ValueError("Raw original17 prefix differs")
            samples.append({"group":group,"source":source,"x":x,"y":core.edge.selected_vector(case,plan),
                "movement_ids":[movement.id for movement in case.movements],"trip_count":len(case.trips),
                "graph":core.topology(case),"case_identity":case.identity(),"market_identity":market.identity()})
        if {sample["group"] for sample in samples} != allowed: raise ValueError("Grouped source support missing")
        return samples


def fit_candidate(arm,parts,initial,recorder,*,budget=BUDGET,task_deadline=None):
    core.configure_cpu(); feature_arm,family = arm_parts(arm)
    if initial.family != family or initial.feature_arm != feature_arm: raise ValueError("Initial arm identity differs")
    model = copy.deepcopy(initial)
    optimizer = torch.optim.Adam(model.parameters(),lr=core.LEARNING_RATE,betas=(.9,.999),eps=1e-8,weight_decay=core.WEIGHT_DECAY)
    started = time.monotonic(); arm_deadline = started+budget.candidate_seconds
    fold_deadline = task_deadline if task_deadline is not None else math.inf
    deadline = min(arm_deadline,fold_deadline)
    limiting = "fold_global" if fold_deadline<=arm_deadline else "arm"
    deadline_evidence = {"limiting_deadline_kind":limiting,
        "effective_time_budget_seconds":max(0.,deadline-started),
        "arm_deadline_monotonic":arm_deadline,"fold_deadline_monotonic":fold_deadline if np.isfinite(fold_deadline) else None}
    best,best_state,best_epoch,stale,curve = math.inf,None,0,0,[]
    stop = "epoch_cap"
    timers = {name:0. for name in ("gradient_and_update_seconds","fit_evaluation_seconds","inner_evaluation_seconds",
                                    "epoch_persistence_seconds","stop_persistence_seconds")}
    try:
        for epoch in range(1,budget.max_epochs+1):
            if time.monotonic()>=deadline: stop="fold_time_cap" if limiting=="fold_global" else "arm_time_cap"; break
            before = time.monotonic(); model.train(); optimizer.zero_grad(set_to_none=True); interrupted=False
            for batch in parts["fit"]:
                if time.monotonic()>=deadline: interrupted=True; break
                loss = (F.binary_cross_entropy_with_logits(model(batch),batch["y"],reduction="none")*batch["w"]).sum()
                if not torch.isfinite(loss): raise ValueError("Nonfinite v9 fit loss")
                loss.backward()
            if interrupted:
                timers["gradient_and_update_seconds"] += time.monotonic()-before
                stop=("fold_time_cap" if limiting=="fold_global" else "arm_time_cap")+"_incomplete_gradient_discarded"; break
            optimizer.step(); timers["gradient_and_update_seconds"] += time.monotonic()-before
            losses = {}
            for part in ("fit","inner"):
                before=time.monotonic(); losses[part]=core._loss(model,parts[part]); timers[part+"_evaluation_seconds"]+=time.monotonic()-before
            if not np.isfinite(list(losses.values())).all(): raise ValueError("Nonfinite v9 checkpoint loss")
            improved = losses["inner"]<best
            if improved: best,best_epoch,stale=losses["inner"],epoch,0; best_state=copy.deepcopy(model.state_dict())
            else: stale+=1
            row={"epoch":epoch,"fit_weighted_log_loss":losses["fit"],"inner_weighted_log_loss":losses["inner"],
                 "selected_so_far":improved,"selected_epoch_so_far":best_epoch,"elapsed_seconds":time.monotonic()-started}
            curve.append(row); before=time.monotonic()
            snapshot=None
            if epoch%budget.save_every==0: snapshot=copy.deepcopy(model); snapshot.load_state_dict(best_state)
            recorder.epoch(arm,epoch,snapshot,row); timers["epoch_persistence_seconds"]+=time.monotonic()-before
            if stale>=core.PATIENCE: stop="inner_patience"; break
        if best_state is None:
            if stop.startswith("fold_time_cap"): raise FoldCensored("No completed/scored epoch before global fold cap")
            raise TimeoutError("No completed/scored epoch within v9 arm budget")
        selected=copy.deepcopy(model); selected.load_state_dict(best_state)
        fold_censored = stop.startswith("fold_time_cap")
        cap_source = "fold_global" if fold_censored else "arm" if stop.startswith("arm_time_cap") else None
        qualification = {"fold_censored":fold_censored,"matched_allowance_qualified":not fold_censored,
                         "time_cap_source":cap_source,**deadline_evidence}
        before=time.monotonic(); recorder.stop_state(arm,selected,{"selected_epoch":best_epoch,"completed_epochs":len(curve),"stop_reason":stop,**qualification})
        timers["stop_persistence_seconds"]+=time.monotonic()-before
        return selected.eval(),{"arm":arm,"feature_arm":feature_arm,"family":family,"parameter_count":model.parameter_count,
            "selected_epoch":best_epoch,"completed_epochs":len(curve),"stop_reason":stop,"inner_weighted_log_loss":best,
            "train_curves":curve,"budget":asdict(budget),"fit_and_inner_seconds":time.monotonic()-started,
            "training_timers":timers,"initial_tensor_sha256":tensor_sha(initial),"fresh_fit_no_optimizer_resume":True,**qualification}
    except BaseException as exc:
        if best_state is not None:
            preserved=copy.deepcopy(model); preserved.load_state_dict(best_state)
            recorder.failure_best(arm,preserved,{"selected_epoch":best_epoch,"completed_epochs":len(curve),"stop_reason":stop,
                "fit_and_inner_seconds":time.monotonic()-started,"training_timers":timers,"type":type(exc).__name__,"message":str(exc),
                "fold_censored":stop.startswith("fold_time_cap"),**deadline_evidence})
        recorder.arm_failure(arm,{"type":type(exc).__name__,"message":str(exc),"completed_epochs":len(curve),
            "selected_epoch":best_epoch,"stop_reason":stop,"fit_and_inner_seconds":time.monotonic()-started,"training_timers":timers,
            "fold_censored":stop.startswith("fold_time_cap"),"matched_allowance_qualified":False,**deadline_evidence})
        raise


def select_policy(rows):
    if (set(rows) != set(ARMS) or not all(np.isfinite(rows[arm]["inner_weighted_log_loss"]) for arm in ARMS)
            or any(row.get("fold_censored",False) or not row.get("matched_allowance_qualified",True) for row in rows.values())):
        raise ValueError("All four finite selected INNER arms are required")
    return min(ARMS,key=lambda arm:(rows[arm]["inner_weighted_log_loss"],ARMS.index(arm)))


def matched_qualification(rows):
    arms={arm:{"selected_model_and_predictions_saved":arm in rows,
        "fold_censored":rows.get(arm,{}).get("fold_censored",False),
        "matched_allowance_qualified":arm in rows and rows[arm].get("matched_allowance_qualified",True)} for arm in ARMS}
    pairs={family:all(arms[f"{feature}__{family}"]["matched_allowance_qualified"] for feature in FEATURE_ARMS) for family in FAMILIES}
    return {"arms":arms,"within_architecture_pair_eligible":pairs,
            "all_four_qualified":all(arm["matched_allowance_qualified"] for arm in arms.values()),
            "fold_censored":any(arm["fold_censored"] for arm in arms.values()),
            "primary_comparison":"paired feature arms within architecture/fold/seed; timetable groups are independent units"}


def run_fold(dataset,task_id,recorder,*,budget=BUDGET,task_deadline=None):
    if tuple(dataset.groups) != tuple(f"physical_v2_s{i}" for i in range(10000,10128)) or dataset.manifest_sha256 != core.POOL_SHA:
        raise ValueError("Only pinned exact128 grouped TRAIN dataset")
    order=task_arm_order(task_id); fold,seed_index=divmod(task_id,3); seed=core.SEEDS[seed_index]
    started=time.monotonic(); deadline=min(started+budget.fold_seconds,task_deadline if task_deadline is not None else math.inf)
    fit_groups,inner_groups,outer_groups=core.previous.grouped_split(dataset.groups,fold)
    before=time.monotonic(); samples={"fit":dataset.load_samples(fit_groups),"inner":dataset.load_samples(inner_groups)}
    extraction_seconds=time.monotonic()-before
    before=time.monotonic(); transform=preprocess(samples["fit"])
    prepared={feature:{part:batches(part_samples,transform,feature,labelled=True) for part,part_samples in samples.items()} for feature in FEATURE_ARMS}
    proof={part:paired_batch_checks(prepared["padded17"][part],prepared["physical38"][part]) for part in ("fit","inner")}
    preparation_seconds=time.monotonic()-before
    recorder.preprocessing({"features":FEATURES,"mean_fit_only":transform["mean"].tolist(),"scale_fit_only":transform["scale"].tolist(),
        "exact_constant_fit_columns":transform["exact_constant_fit_columns"].tolist(),"intercept_column":INTERCEPT_INDEX,
        "intercept_mean":0.,"intercept_scale":1.,"fit_groups":fit_groups,"inner_groups":inner_groups,"outer_groups":outer_groups,
        "paired_batch_checks":proof,"feature_arm_padding":"21exact zeros after the common scaled17prefix"})
    initial,initial_checks=paired_initial_models(seed)
    recorder.initialization(initial,initial_checks,order,seed)
    models,rows={},{}
    for arm in order:
        feature,family=arm_parts(arm)
        recorder.start_candidate(arm,{"budget":asdict(budget),"width":WIDTH,"layers":LAYERS,"parameter_ceiling":PARAMETER_CEILING,
            "patience":core.PATIENCE,"learning_rate":core.LEARNING_RATE,"weight_decay":core.WEIGHT_DECAY,"seed":seed,
            "initial_tensor_sha256":tensor_sha(initial[arm]),"arm_order":order,"historical17_anchor":False})
        fitted,row=fit_candidate(arm,prepared[feature],initial[arm],recorder,budget=budget,task_deadline=deadline)
        probabilities={}
        for part in ("fit","inner"):
            before=time.monotonic(); probabilities[part]=core.predict(fitted,prepared[feature][part]); row[part+"_selected_prediction_seconds"]=time.monotonic()-before
            _,y,w=core.previous._stack(samples[part]); before=time.monotonic()
            row[part+"_metrics"]=core.frozen._metrics(y,probabilities[part],w,samples[part]); row[part+"_metric_seconds"]=time.monotonic()-before
        row["saved_model"]=recorder.candidate(arm,fitted,row,samples["fit"],probabilities["fit"],samples["inner"],probabilities["inner"])
        models[arm],rows[arm]=fitted,row
        if row.get("fold_censored",False):
            recorder.qualification(matched_qualification(rows))
            raise FoldCensored("Fold-censored selected arm retained; no four-arm promotion or OUTER admission")
    qualification=matched_qualification(rows)
    recorder.qualification(qualification)
    if not qualification["all_four_qualified"]: raise FoldCensored("Incomplete matched arm qualification")
    if time.monotonic()>=deadline:
        recorder.fold_censor({"stage":"before_promotion","all_arms_scored_and_saved":True})
        raise FoldCensored("v9 fold cap before promotion; saved INNER evidence retained")
    promoted=select_policy(rows)
    promotion={"arm":promoted,"tie_order":ARMS,"inner_weighted_log_losses":{arm:rows[arm]["inner_weighted_log_loss"] for arm in ARMS},
               "per_feature_inner_architecture":{feature:min((arm for arm in ARMS if arm_parts(arm)[0]==feature),
                    key=lambda arm:(rows[arm]["inner_weighted_log_loss"],ARMS.index(arm))) for feature in FEATURE_ARMS}}
    recorder.promotion(promotion)
    # Four selected models/predictions and INNER promotion are immutable before
    # a single OUTER case, market, graph, feature or label is materialized.
    if time.monotonic()>=deadline:
        recorder.fold_censor({"stage":"before_outer_materialization","all_arms_scored_and_saved":True})
        raise FoldCensored("v9 fold cap before OUTER evaluation; saved INNER evidence retained")
    before=time.monotonic(); outer=dataset.load_samples(outer_groups); outer_extraction_seconds=time.monotonic()-before
    before=time.monotonic(); outer_batches={feature:batches(outer,transform,feature,labelled=False) for feature in FEATURE_ARMS}
    outer_proof=paired_batch_checks(outer_batches["padded17"],outer_batches["physical38"])
    outer_preparation_seconds=time.monotonic()-before
    predictions,inference={},{}
    for arm in ARMS:
        if time.monotonic()>=deadline:
            recorder.fold_censor({"stage":"outer_inference","all_arms_scored_and_saved":True,"next_arm":arm})
            raise FoldCensored("v9 fold cap during OUTER inference; selected models retained")
        before=time.monotonic(); predictions[arm]=core.predict(models[arm],outer_batches[arm_parts(arm)[0]]); inference[arm]=time.monotonic()-before
    predictions["inner_promoted"]=predictions[promoted]
    for feature,arm in promotion["per_feature_inner_architecture"].items():
        predictions[feature+"__inner_architecture"]=predictions[arm]
    per_source=defaultdict(dict); prediction_rows=[]; cursor=0; before=time.monotonic()
    for sample in outer:
        n=len(sample["y"])
        per_source[sample["group"]][sample["source"]]={arm:core.frozen._metrics(sample["y"],p[cursor:cursor+n],np.ones(n)/n,[sample]) for arm,p in predictions.items()}
        for index,mid in enumerate(sample["movement_ids"]):
            prediction_rows.append({"base_group":sample["group"],"source":sample["source"],"movement_id":mid,
                "observed_selected":bool(sample["y"][index]),"input_trip_count_k":min(n,sample["trip_count"]),
                "probabilities":{arm:float(p[cursor+index]) for arm,p in predictions.items()}})
        cursor+=n
    per_group={group:{arm:core.previous._macro_metrics([row[arm] for row in per_source[group].values()]) for arm in predictions} for group in outer_groups}
    _,y,w=core.previous._stack(outer); common=[group for group in outer_groups if int(group.rsplit("s",1)[-1])<10032]
    aggregate={arm:core.previous._macro_metrics([per_group[group][arm] for group in outer_groups]) for arm in predictions}
    common_metrics={arm:core.previous._macro_metrics([per_group[group][arm] for group in common]) for arm in predictions}
    pooled={arm:core.frozen._metrics(y,p,w,outer) for arm,p in predictions.items()}
    metric_seconds=time.monotonic()-before
    return {"policy":POLICY,"task_id":task_id,"fold":fold,"seed":seed,"arm_order":order,"features":FEATURES,
        "fit_groups":fit_groups,"inner_groups":inner_groups,"outer_groups":outer_groups,"budget":asdict(budget),
        "width":WIDTH,"layers":LAYERS,"parameter_ceiling":PARAMETER_CEILING,"dtype":"float64","device":"cpu",
        "torch_threads":torch.get_num_threads(),"torch_interop_threads":torch.get_num_interop_threads(),
        "pool_manifest_sha256":dataset.manifest_sha256,"pool_table_hashes":dataset.table_hashes,
        "input_inventory_sha256":INVENTORY_SHA,"feature_source_sha256":FEATURE_SHA,"paired_initial_checks":initial_checks,
        "paired_fit_inner_checks":proof,"paired_outer_checks":outer_proof,"candidates":rows,"inner_policy_promotion":promotion,
        "outer_metrics":aggregate,"common32_outer_metrics":common_metrics,"outer_pooled_diagnostics":pooled,
        "per_group_source_outer_metrics":dict(per_source),"per_group_outer_metrics":per_group,"outer_prediction_rows":prediction_rows,
        "weights":{part:core.previous._weight_manifest(part_samples) for part,part_samples in {**samples,"outer":outer}.items()},
        "eligibility":{part:core.previous._partition_eligibility(dataset.group_eligibility,groups) for part,groups in
            (("fit",fit_groups),("inner",inner_groups),("outer",outer_groups))},
        "fit_inner_feature_extraction_seconds":extraction_seconds,"fit_inner_preparation_seconds":preparation_seconds,
        "outer_feature_extraction_seconds":outer_extraction_seconds,"outer_preparation_seconds":outer_preparation_seconds,
        "outer_inference_seconds_by_arm":inference,"outer_metric_seconds":metric_seconds,
        "progress_persistence_seconds":recorder.persistence_seconds,"wall_seconds":time.monotonic()-started,
        "all_four_selected_before_outer":True,"matched_pair_qualification":qualification,
        "no_outer_selection":True,"historical17_anchor":False,
        "label_scope":"observed feasible-incumbent movement imitation only; not route feasibility or optimality"}
