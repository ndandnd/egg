"""Scientific CPU fixtures only, synthetic inputs, no real pool or campaign fit."""
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from egglab import native_hull as nh
from egglab import native_recharge as nr
from egglab import physical_route_graph_context_v9 as model
from experiments import train_physical_route_graph_context_v9 as cli


@pytest.fixture(autouse=True)
def cpu_only(): model.core.configure_cpu()


def sample(group="fixture",source="source0",seed=5):
    rng=np.random.default_rng(seed); x=rng.normal(size=(8,38))
    x[:,16]=1.; x[:,20]=.9; x[:,37]=0.
    return {"group":group,"source":source,"x":x,"y":(x[:,21]>0).astype(float),
        "movement_ids":list(range(8)),"trip_count":2,
        "graph":{"src":np.array([0,0,1,1,1,2,2,2]),"dst":np.array([1,2,2,2,3,1,1,3]),"nodes":4}}


def prepared(feature="physical38"):
    samples={"fit":[sample("a"),sample("b",seed=6)],"inner":[sample("c",seed=7)]}
    transform=model.preprocess(samples["fit"])
    return samples,{part:model.batches(rows,transform,feature,labelled=True) for part,rows in samples.items()}


def recorder(tmp_path): return cli.Progress(tmp_path)


def test_paired_initialization_shapes_counts_rng_and_ceiling(monkeypatch):
    initials,checks=model.paired_initial_models(17)
    torch.rand(71); repeated,_=model.paired_initial_models(17)
    for family in model.FAMILIES:
        left,right=(initials[f"{feature}__{family}"] for feature in model.FEATURE_ARMS)
        assert left.node.in_features==78 and left.edge.in_features==38 and left.decoder.in_features==134
        assert left.parameter_count==model.EXPECTED_PARAMETERS[family] <= model.PARAMETER_CEILING
        assert checks[family]["inactive_padded_input_weights"]==2688
        assert model.tensor_sha(left)==model.tensor_sha(right)==model.tensor_sha(repeated[f"padded17__{family}"])
        assert all(torch.equal(value,right.state_dict()[key]) for key,value in left.state_dict().items())
    monkeypatch.setattr(model,"PARAMETER_CEILING",20544)
    with pytest.raises(ValueError,match="parameter budget"): model.GraphScorer("mean_message","padded17")


def test_hashed_order_balances_positions_and_has_no_seed_rng_side_effect():
    orders=[model.task_arm_order(task) for task in range(12)]
    for position in range(4): assert Counter(order[position] for order in orders)==Counter({arm:3 for arm in model.ARMS})
    before=torch.get_rng_state(); [model.task_arm_order(task) for task in range(12)]
    assert torch.equal(before,torch.get_rng_state())
    with pytest.raises(ValueError): model.task_arm_order(True)


def test_fit_only_preprocessing_exact_prefix_intercept_constants_and_padding():
    fit=[sample("a"),sample("b",seed=6)]; inner=sample("inner",seed=7)
    transform=model.preprocess(fit); before=copy.deepcopy(transform)
    inner["x"][:]=1e12  # excluded input cannot alter a previously fit-only transform
    repeated=model.preprocess(fit)
    assert all(np.array_equal(before[key],repeated[key]) for key in before)
    expected_mean,expected_scale=model.core.frozen._preprocess(np.concatenate([row["x"][:,:17] for row in fit]))
    assert np.array_equal(transform["mean"][:17],expected_mean)
    assert np.array_equal(transform["scale"][:17],expected_scale)
    assert transform["mean"][16]==0. and transform["scale"][16]==1.
    actual=model.scaled_features(fit[0]["x"],transform,"physical38")
    padded=model.scaled_features(fit[0]["x"],transform,"padded17")
    assert np.array_equal(padded[:,:17],actual[:,:17]) and np.count_nonzero(padded[:,17:])==0
    assert np.all(actual[:,16]==1.) and np.all(actual[:,20]==0.) and np.all(actual[:,37]==0.)
    assert np.array_equal(actual[:,:17],(fit[0]["x"][:,:17]-expected_mean)/expected_scale)


def test_paired_batches_are_disconnected_with_equal_group_source_edge_weights():
    samples=[sample("a","source0"),sample("a","source1",6),sample("b","source0",7)]
    transform=model.preprocess(samples)
    padded=model.batches(samples,transform,"padded17",labelled=True)
    actual=model.batches(samples,transform,"physical38",labelled=True)
    proof=model.paired_batch_checks(padded,actual)
    assert proof["prefix17_scaled_identical"] and proof["padded21_exact_zero"]
    assert float(actual[0]["w"].sum())==pytest.approx(1.)
    assert actual[0]["w"][:16].numpy()==pytest.approx(np.full(16,1/32))
    assert actual[0]["w"][16:].numpy()==pytest.approx(np.full(8,1/16))
    scorer=model.paired_initial_models(17)[0]["physical38__graph_attention"]
    together=model.core.predict(scorer,actual)
    separately=np.concatenate([model.core.predict(scorer,model.batches([row],transform,"physical38",labelled=False)) for row in samples])
    assert together==pytest.approx(separately,abs=1e-14,rel=0.)


@pytest.mark.parametrize("family",model.FAMILIES)
def test_full_gradient_adam_step_sparse_curves_and_selected_replay(tmp_path,family):
    _,parts=prepared(); arm=f"physical38__{family}"; initial=model.paired_initial_models(17)[0][arm]
    expected=copy.deepcopy(initial)
    optimizer=torch.optim.Adam(expected.parameters(),lr=model.core.LEARNING_RATE,betas=(.9,.999),eps=1e-8,weight_decay=model.core.WEIGHT_DECAY)
    optimizer.zero_grad(set_to_none=True)
    for batch in parts["fit"]:
        (F.binary_cross_entropy_with_logits(expected(batch),batch["y"],reduction="none")*batch["w"]).sum().backward()
    optimizer.step()
    progress=recorder(tmp_path); progress.start_candidate(arm,{})
    trained,row=model.fit_candidate(arm,parts,initial,progress,budget=model.Budget(max_epochs=1,save_every=2))
    assert row["selected_epoch"]==row["completed_epochs"]==1 and row["stop_reason"]=="epoch_cap"
    assert all(torch.equal(value,expected.state_dict()[key]) for key,value in trained.state_dict().items())
    assert model.tensor_sha(initial)==row["initial_tensor_sha256"]
    assert not list(progress.path.glob("*periodic*.npz"))
    restored=model.restore_model(progress.path/f"{arm}_stop_best.npz")
    assert restored.feature_arm=="physical38" and restored.family==family
    assert np.array_equal(model.core.predict(trained,parts["inner"]),model.core.predict(restored,parts["inner"]))
    assert sum(row["training_timers"].values()) <= row["fit_and_inner_seconds"]+1e-8
    with pytest.raises(FileExistsError): progress.start_candidate(arm,{})


def test_scalar_stream_periodic_best_and_inner_patience_are_preserved(tmp_path,monkeypatch):
    _,parts=prepared(); arm="physical38__mean_message"; initial=model.paired_initial_models(17)[0][arm]
    monkeypatch.setattr(model.core,"_loss",lambda *_:.2)
    progress=recorder(tmp_path); progress.start_candidate(arm,{})
    _,row=model.fit_candidate(arm,parts,initial,progress,budget=model.Budget(max_epochs=40,save_every=10))
    assert row["selected_epoch"]==1 and row["completed_epochs"]==31 and row["stop_reason"]=="inner_patience"
    curves=[json.loads(line) for line in (progress.path/f"{arm}_epochs.jsonl").read_text().splitlines()]
    assert len(curves)==31 and [event["epoch"] for event in curves if event["persisted_best_checkpoint"]]==[10,20,30]
    assert all(event["selected_epoch_so_far"]==1 for event in curves)
    assert len(list(progress.path.glob("*periodic*.npz")))==3


def test_incomplete_gradient_is_discarded_and_no_scored_epoch_is_typed_failure(tmp_path,monkeypatch):
    monkeypatch.setattr(model.core,"GRAPH_BATCH",1); _,parts=prepared()
    arm="physical38__mean_message"; initial=model.paired_initial_models(17)[0][arm]
    clock={"now":0.,"fit_forwards":0}
    monkeypatch.setattr(model,"time",SimpleNamespace(monotonic=lambda:clock["now"]))
    original=model.GraphScorer.forward
    def forward(scorer,batch):
        value=original(scorer,batch)
        if scorer.training and torch.is_grad_enabled():
            clock["fit_forwards"]+=1
            if clock["fit_forwards"]==3: clock["now"]=2.
        return value
    monkeypatch.setattr(model.GraphScorer,"forward",forward)
    progress=recorder(tmp_path); progress.start_candidate(arm,{})
    _,row=model.fit_candidate(arm,parts,initial,progress,budget=model.Budget(max_epochs=4,candidate_seconds=1.,fold_seconds=2.))
    assert row["completed_epochs"]==1 and row["stop_reason"]=="arm_time_cap_incomplete_gradient_discarded"
    assert row["time_cap_source"]=="arm" and not row["fold_censored"] and row["matched_allowance_qualified"]
    selected=model.restore_model(progress.path/f"{arm}_stop_best.npz")
    # Reproduce the completed first epoch independently; partial epoch2 must
    # never become a weight update or the selected snapshot.
    expected=copy.deepcopy(initial); optimizer=torch.optim.Adam(expected.parameters(),lr=.003,betas=(.9,.999),eps=1e-8,weight_decay=.0001)
    optimizer.zero_grad(set_to_none=True)
    for batch in parts["fit"]:
        (F.binary_cross_entropy_with_logits(expected(batch),batch["y"],reduction="none")*batch["w"]).sum().backward()
    optimizer.step()
    assert model.tensor_sha(selected)==model.tensor_sha(expected)
    empty=tmp_path/"empty"; empty.mkdir(); second=recorder(empty); second.start_candidate(arm,{})
    with pytest.raises(TimeoutError,match="No completed"):
        model.fit_candidate(arm,parts,initial,second,task_deadline=0.)
    assert json.loads((second.path/f"{arm}_failure.json").read_text())["completed_epochs"]==0
    assert not list(second.path.glob("*stop_best.npz"))


def test_handled_scoring_failure_retains_best_curve_and_weight(tmp_path,monkeypatch):
    _,parts=prepared(); arm="physical38__mean_message"; initial=model.paired_initial_models(17)[0][arm]
    calls={"n":0}; original=model.core._loss
    def loss(*args):
        calls["n"]+=1
        if calls["n"]==4: raise ValueError("fixture failed INNER evaluation")
        return original(*args)
    monkeypatch.setattr(model.core,"_loss",loss)
    progress=recorder(tmp_path); progress.start_candidate(arm,{})
    with pytest.raises(ValueError,match="fixture failed"):
        model.fit_candidate(arm,parts,initial,progress,budget=model.Budget(max_epochs=3))
    failure=json.loads((progress.path/f"{arm}_failure.json").read_text())
    assert failure["completed_epochs"]==1 and failure["selected_epoch"]==1
    assert (progress.path/f"{arm}_handled_failure_best.npz").exists()
    assert len((progress.path/f"{arm}_epochs.jsonl").read_text().splitlines())==1
    assert not (progress.path/f"{arm}_selected.npz").exists()


def test_inner_promotion_requires_four_arms_and_uses_declared_ties():
    rows={arm:{"inner_weighted_log_loss":.2} for arm in model.ARMS}
    assert model.select_policy(rows)==model.ARMS[0]
    rows[model.ARMS[3]]["inner_weighted_log_loss"] = .1
    assert model.select_policy(rows)==model.ARMS[3]
    rows.pop(model.ARMS[1])
    with pytest.raises(ValueError,match="All four"): model.select_policy(rows)


def test_outer_materialization_waits_for_all_four_saved_selections_and_promotion(tmp_path,monkeypatch):
    groups=tuple(f"physical_v2_s{i}" for i in range(10000,10128))
    fit,inner,outer=model.core.previous.grouped_split(groups,0)
    state={"selected":0,"promoted":False,"outer_loads":0}
    class Pool:
        manifest_sha256=model.core.POOL_SHA; table_hashes={}
        group_eligibility=[{"base_group":group,"observed_source_count":1,
            "eligible_for_observed_source_supervision":True,"eligible_for_full_pair_supervision":False} for group in groups]
        def load_samples(self,requested):
            if tuple(requested)==outer:
                assert state["selected"]==4 and state["promoted"]; state["outer_loads"]+=1
            else: assert tuple(requested) in (fit,inner)
            return [sample(group) for group in requested]
    pool=Pool(); pool.groups=groups
    class Progress(cli.Progress):
        def candidate(self,*args):
            evidence=super().candidate(*args); state["selected"]+=1; return evidence
        def promotion(self,row):
            assert state["selected"]==4; super().promotion(row); state["promoted"]=True
    def fake_fit(arm,parts,initial,progress,**kwargs):
        return initial,{"arm":arm,"inner_weighted_log_loss":.1+model.ARMS.index(arm)/100,
                        "selected_epoch":1,"completed_epochs":1,"stop_reason":"fixture"}
    monkeypatch.setattr(model,"fit_candidate",fake_fit)
    result=model.run_fold(pool,0,Progress(tmp_path))
    assert result["all_four_selected_before_outer"] and result["no_outer_selection"] and state["outer_loads"]==1
    assert result["inner_policy_promotion"]["arm"]==model.ARMS[0]
    assert set(result["outer_metrics"])==set(model.ARMS)|{"inner_promoted","padded17__inner_architecture","physical38__inner_architecture"}
    assert result["matched_pair_qualification"]["all_four_qualified"]
    for arm in model.ARMS:
        selected=model.restore_model(tmp_path/"inner_progress"/f"{arm}_selected.npz")
        assert (selected.feature_arm,selected.family)==model.arm_parts(arm)


def test_input_pool_only_decodes_requested_source_labels_and_checks_prefix(tmp_path,monkeypatch):
    inventory_path=Path(__file__).resolve().parents[2]/"research-20260930/learning-campaign/inventory_physical_context_v9.py"
    spec=importlib.util.spec_from_file_location("fixture_input_registry",inventory_path)
    inventory=importlib.util.module_from_spec(spec); spec.loader.exec_module(inventory)
    case=nr.NativeCase("synthetic-input",(nr.Trip("t",20,30,"P","Q",1.),),
        (nr.Movement("out","pullout",None,"t",(nr.Leg("D","P",0,20,2.),)),
         nr.Movement("in","pullin","t",None,(nr.Leg("Q","D",30,40,2.),))),
        (nr.Resource(0,120,90.,90.,1),),(0,60,120),"D",1,100.,20.,60,120,1.,efficiency=.9)
    market=nh.Market("synthetic-input-source0",(.1,.2),(.01,.01))
    plan={"vehicles":[{"trips":["t"],"movements":["out","in"]}]}
    allowed="physical_v2_s10000"; excluded="physical_v2_s10001"
    headers={}; lines=[]
    for group in (allowed,excluded):
        header={"base_group":group,"base_id":int(group.rsplit("s",1)[-1]),"source":"source0",
                "case_identity":case.identity(),"market_identity":market.identity()}
        headers[group,"source0"]=header
        row={**header,"source_plan":plan if group==allowed else {"poison_outer_outcome":True},
             "source_plan_hash":nr.digest(plan),"selected_movements":["out","in"]}
        lines.append(json.dumps(row))
    (tmp_path/"source_inputs.jsonl").write_text("\n".join(lines)+"\n")
    (tmp_path/"pool_manifest.json").write_text(json.dumps({"group_eligibility":[]}))
    projected={"cases":{group:{"base_id":int(group.rsplit("s",1)[-1]),"case_identity":case.identity()} for group in (allowed,excluded)},
               "sources":headers,"table_sha256":{}}
    fake_inventory=SimpleNamespace(load_input_registry=lambda *_:projected,registry_projection=inventory.registry_projection,
                                   SOURCE_REGISTRY_FIELDS=inventory.SOURCE_REGISTRY_FIELDS)
    monkeypatch.setattr(model,"input_inventory",lambda _:fake_inventory)
    original=json.loads
    def loads(text,*args,**kwargs):
        assert "poison_outer_outcome" not in text
        return original(text,*args,**kwargs)
    monkeypatch.setattr(json,"loads",loads)
    monkeypatch.setattr(model.physical,"make_case",lambda base_id:case if base_id==10000 else pytest.fail("Excluded case materialized"))
    monkeypatch.setattr(model.physical,"market",lambda *_:market)
    pool=model.InputPool(tmp_path,expected_manifest_sha256=model.core.POOL_SHA,root=tmp_path)
    samples=pool.load_samples([allowed])
    assert len(samples)==1 and samples[0]["x"].shape==(2,38)
    assert np.array_equal(samples[0]["x"][:,:17],model.core.edge.edge_features(case,market.a))
    assert np.array_equal(samples[0]["y"],np.ones(2))


def test_mismatched_runtime_stops_before_bank_and_saves_failed_task(tmp_path,monkeypatch):
    monkeypatch.setattr(cli.original,"versions",lambda:{"torch":"wrong"})
    monkeypatch.setattr(cli.base,"sha",lambda _:"fixture-sha")
    monkeypatch.setattr(model,"InputPool",lambda *_ ,**__:pytest.fail("Bank must remain sealed"))
    with pytest.raises(ValueError,match="runtime"):
        cli.run(0,model.core.POOL_SHA,tmp_path)
    receipt=json.loads((tmp_path/"task00/receipt.json").read_text())
    assert receipt["status"]=="failed" and receipt["no_partial_task_promotion_or_admission"]
    assert (tmp_path/"task00/source_identity.json").exists()
    with pytest.raises(ValueError,match="Immutable"): cli.run(0,model.core.POOL_SHA,tmp_path)


def test_fold_cap_is_distinct_from_arm_cap_and_invalidates_matched_pair(tmp_path,monkeypatch):
    monkeypatch.setattr(model.core,"GRAPH_BATCH",1); _,parts=prepared()
    arm="physical38__mean_message"; initial=model.paired_initial_models(17)[0][arm]
    clock={"now":0.,"n":0}; original=model.GraphScorer.forward
    monkeypatch.setattr(model,"time",SimpleNamespace(monotonic=lambda:clock["now"]))
    def forward(scorer,batch):
        result=original(scorer,batch)
        if scorer.training and torch.is_grad_enabled():
            clock["n"]+=1
            if clock["n"]==3: clock["now"]=1.
        return result
    monkeypatch.setattr(model.GraphScorer,"forward",forward)
    progress=recorder(tmp_path); progress.start_candidate(arm,{})
    selected,row=model.fit_candidate(arm,parts,initial,progress,
        budget=model.Budget(max_epochs=4,candidate_seconds=2.,fold_seconds=3.),task_deadline=.5)
    assert row["completed_epochs"]==1 and row["fold_censored"] and not row["matched_allowance_qualified"]
    assert row["time_cap_source"]==row["limiting_deadline_kind"]=="fold_global"
    assert row["stop_reason"]=="fold_time_cap_incomplete_gradient_discarded"
    assert row["effective_time_budget_seconds"]==.5
    assert model.tensor_sha(selected)==model.tensor_sha(model.restore_model(progress.path/f"{arm}_stop_best.npz"))
    rows={candidate:{"inner_weighted_log_loss":.2,"matched_allowance_qualified":True} for candidate in model.ARMS}
    rows[arm]=row
    qualification=model.matched_qualification(rows)
    assert not qualification["all_four_qualified"] and qualification["fold_censored"]
    assert not qualification["within_architecture_pair_eligible"]["mean_message"]
    with pytest.raises(ValueError,match="All four"): model.select_policy(rows)


def test_fold_censored_saved_arm_blocks_promotion_and_outer_materialization(tmp_path,monkeypatch):
    groups=tuple(f"physical_v2_s{i}" for i in range(10000,10128))
    fit,inner,outer=model.core.previous.grouped_split(groups,0)
    class Pool:
        manifest_sha256=model.core.POOL_SHA
        def load_samples(self,requested):
            assert tuple(requested) in (fit,inner), "OUTER must stay sealed"
            return [sample(group) for group in requested]
    pool=Pool(); pool.groups=groups
    def fake_fit(arm,parts,initial,progress,**kwargs):
        return initial,{"inner_weighted_log_loss":.2,"fold_censored":True,"matched_allowance_qualified":False,
                        "selected_epoch":1,"completed_epochs":1,"stop_reason":"fold_time_cap"}
    monkeypatch.setattr(model,"fit_candidate",fake_fit)
    progress=recorder(tmp_path)
    with pytest.raises(model.FoldCensored,match="no four-arm promotion"):
        model.run_fold(pool,0,progress)
    saved=list(progress.path.glob("*selected.npz")); assert len(saved)==1
    assert not (progress.path/"inner_policy_promotion.json").exists()
    ledger=json.loads((progress.path/"matched_pair_qualification.json").read_text())
    assert ledger["fold_censored"] and not ledger["all_four_qualified"]
