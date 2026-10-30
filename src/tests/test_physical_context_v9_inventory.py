"""Tiny registry/statistics/gating fixtures: no actual pool or model outcomes."""
import ast
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from egglab import native_hull as nh
from egglab import native_recharge as nr

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("v9_inventory", ROOT/"research-20260930/learning-campaign/inventory_physical_context_v9.py")
inventory = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(inventory)


def tiny_case(base_id):
    return nr.NativeCase(f"fixture-{base_id}", (nr.Trip("t",20,30,"P","Q",1.),),
        (nr.Movement("out","pullout",None,"t",(nr.Leg("D","P",0,20,2.),)),
         nr.Movement("in","pullin","t",None,(nr.Leg("Q","D",30,40,2.),))),
        (nr.Resource(0,120,90.,90.,1),),(0,60,120),"D",1,100.,20.,60,120,1.,efficiency=.9)


def tiny_market(case,source):
    return nh.Market(case.name+source,(.1,.2),(.01,.01))


def registry_fixture(prefix=32):
    cases, sources = {}, {}
    for base_id in range(10000,10000+prefix):
        group=f"physical_v2_s{base_id}"; case=tiny_case(base_id)
        cases[group]={"base_group":group,"base_id":base_id,"case_identity":case.identity()}
        for source in ("source0","source1"):
            sources[group,source]={"market_identity":tiny_market(case,source).identity()}
    return {"cases":cases,"sources":sources}


def test_whitelist_does_not_decode_excluded_values(monkeypatch):
    poison={"source_plan":{"loads":[1234],"quote":"escaped \\\" } ], : key"},
            "selected_movements":["forbidden"],"source_replay":{"feasible":True},
            "case":{"battery_kwh":999},"base_id":10000,"base_group":"physical_v2_s10000",
            "source":"source0","case_identity":"case-hash","market_identity":"market-hash"}
    decoded=[]; original=json.JSONDecoder.decode
    def decode(decoder,text,*args,**kwargs):
        decoded.append(text)
        return original(decoder,text,*args,**kwargs)
    monkeypatch.setattr(json.JSONDecoder,"decode",decode)
    projection=inventory.registry_projection(json.dumps(poison),inventory.SOURCE_REGISTRY_FIELDS)
    assert set(projection)==inventory.SOURCE_REGISTRY_FIELDS
    assert projection["base_id"]==10000
    assert not any(text.startswith(("{","[")) for text in decoded)
    assert not any("1234" in text or "999" in text or "forbidden" in text for text in decoded)
    # Replacing outcome values cannot alter the registry projection.
    poison["source_plan"]={"malicious_other_outcome":"unused"}
    assert inventory.registry_projection(json.dumps(poison),inventory.SOURCE_REGISTRY_FIELDS)==projection


@pytest.mark.parametrize("row", ['{"base_id":1,"base_id":2}', '{"base_id":[]}',
    '{"base_id":1,}', '{"base_id":1}trailing', '{"plan":[{"bad":2]}'])
def test_invalid_or_nonscalar_registry_is_rejected(row):
    with pytest.raises(ValueError): inventory.registry_projection(row,{"base_id"})


@pytest.mark.parametrize("prefix",(32,64,128))
def test_partition_matches_frozen_source_functions_without_model_import(prefix):
    path=ROOT/"src/egglab"/("physical_route_model_v2.py" if prefix==32 else "physical_route_model_v3.py")
    function=next(node for node in ast.parse(path.read_text()).body
                  if isinstance(node,ast.FunctionDef) and node.name=="grouped_split")
    scope={"FOLDS":4}; module=ast.Module(body=[function],type_ignores=[])
    exec(compile(module,str(path),"exec"),scope)
    groups=tuple(f"physical_v2_s{i}" for i in range(10000,10000+prefix))
    for fold in range(4):
        fit,inner,outer=inventory.partitions(prefix,fold)
        assert (fit,inner,outer)==scope["grouped_split"](groups,fold)
        assert not set(fit)&set(inner) and not set(fit)&set(outer) and not set(inner)&set(outer)
        assert set(fit)|set(inner)|set(outer)==set(groups)


def test_only_fit_case_market_and_features_are_constructed_and_identified():
    inputs=registry_fixture(); fit,inner,outer=inventory.partitions(32,0)
    fit_ids={inputs["cases"][group]["base_id"] for group in fit}
    calls=[]
    def case_factory(base_id):
        assert base_id in fit_ids; calls.append(("case",base_id)); return tiny_case(base_id)
    def market_factory(case,source):
        base_id=int(case.name.split("-")[-1]); assert base_id in fit_ids
        calls.append(("market",base_id)); return tiny_market(case,source)
    def featurizer(case,market):
        assert int(case.name.split("-")[-1]) in fit_ids
        calls.append(("features",case.name)); return inventory.features.edge_features(case,market)
    row=inventory.inventory_fold(inputs,32,0,case_factory=case_factory,
                                 market_factory=market_factory,featurizer=featurizer)
    assert row["fit_group_count"]==20 and row["fit_source_count"]==40 and row["movement_rows"]==80
    assert row["positive_window_rows"]==40 and row["weight_sum"]==pytest.approx(1.)
    assert len(row["columns"])==len(inventory.UNITS)==38
    assert len([call for call in calls if call[0]=="case"])==20
    assert len([call for call in calls if call[0]=="features"])==40
    power=next(column for column in row["columns"] if column["name"]=="window_grid_kw_mean")
    assert power["all_fit_movement_rows"]["range"]==90.
    assert power["conditional_positive_window_rows"]["constant_exact"]
    assert power["conditional_positive_window_rows"]["minimum"]==90.
    assert row["excluded_outer_groups_identifiers_only"]==outer
    assert row["excluded_inner_groups_identifiers_only"]==inner


def test_regenerated_fit_identity_mismatch_stops_before_feature_extraction():
    inputs=registry_fixture(); fit,_,_=inventory.partitions(32,0)
    inputs["cases"][fit[0]]["case_identity"]="wrong"
    with pytest.raises(ValueError,match="case identity"):
        inventory.inventory_fold(inputs,32,0,case_factory=tiny_case,market_factory=tiny_market,
                                 featurizer=lambda *_:pytest.fail("Features must wait for identity"))
    inputs=registry_fixture(); inputs["sources"][fit[0],"source0"]["market_identity"]="wrong"
    with pytest.raises(ValueError,match="market identity"):
        inventory.inventory_fold(inputs,32,0,case_factory=tiny_case,market_factory=tiny_market,
                                 featurizer=lambda *_:pytest.fail("Features must wait for identity"))


def test_population_and_group_weighted_variance_missingness_and_roundoff():
    stats=inventory.column_stats([0.,2.,4.,np.nan,np.inf],[.1,.2,.7,.1,.1],True)
    assert stats["mean"]==2. and stats["variance_population"]==pytest.approx(8/3)
    assert stats["equal_group_source_edge_mean"]==pytest.approx(3.2)
    assert stats["equal_group_source_edge_variance"]==pytest.approx(1.76)
    assert stats["missing_nan"]==1 and stats["nonfinite_infinity"]==1 and stats["ratio_gt_one_rows"]==2
    exact=inventory.column_stats([.9]*23,np.ones(23))
    assert exact["constant_exact"] and exact["variance_population"]==0.
    close=inventory.column_stats([.9,np.nextafter(.9,1.)],[1.,1.])
    assert close["near_constant_roundoff"] and not close["constant_exact"]
    empty=inventory.column_stats([],[])
    assert empty["rows"]==0 and empty["minimum"] is None and empty["constant_exact"] is None


def test_exclusive_output_never_overwrites_inventory(tmp_path):
    path=tmp_path/"inventory.json"; inventory.save_new(path,{"passed":True})
    with pytest.raises(FileExistsError): inventory.save_new(path,{"passed":False})
    assert json.loads(path.read_text())=={"passed":True}


def test_pinned_pool_projection_uses_registry_only_and_detects_changed_table(tmp_path):
    cases=[]; sources=[]
    for base_id in range(10000,10032):
        group=f"physical_v2_s{base_id}"; case=tiny_case(base_id)
        cases.append({"base_id":base_id,"base_group":group,"split":"train",
            "generator":inventory.registry.GENERATOR,"case_identity":case.identity(),
            "case":{"opaque_fixture_payload":"not consumed"}})
        for source in ("source0","source1"):
            sources.append({"base_id":base_id,"base_group":group,"source":source,
                "case_identity":case.identity(),"market_identity":tiny_market(case,source).identity(),
                "source_plan":{"vehicles":[{"selected":"forbidden"}]},"source_replay":{"load":"forbidden"}})
    for name,rows in (("cases.jsonl",cases),("source_inputs.jsonl",sources)):
        (tmp_path/name).write_text("\n".join(json.dumps(row) for row in rows)+"\n")
    manifest={"policy":"physical-route-source-pool32-admitted-train-v1","train_only":True,
              "base_ids":list(range(10000,10032)),"output_hashes":{
                  name:inventory.sha(tmp_path/name) for name in ("cases.jsonl","source_inputs.jsonl")}}
    (tmp_path/"pool_manifest.json").write_text(json.dumps(manifest))
    pinned=inventory.sha(tmp_path/"pool_manifest.json")
    projected=inventory.load_input_registry(tmp_path,32,pinned)
    assert len(projected["cases"])==32 and len(projected["sources"])==64
    assert all(set(row)==inventory.SOURCE_REGISTRY_FIELDS for row in projected["sources"].values())
    assert all("case" not in row for row in projected["cases"].values())
    with pytest.raises(ValueError,match="manifest"):
        inventory.load_input_registry(tmp_path,32,"0"*64)
    with (tmp_path/"source_inputs.jsonl").open("a") as stream: stream.write("\n")
    with pytest.raises(ValueError,match="table"):
        inventory.load_input_registry(tmp_path,32,pinned)
