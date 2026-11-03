"""Pure training/proposal checks; no native optimizer call."""
from dataclasses import asdict
from pathlib import Path
import json

import pytest

from egglab import learned_proposals as lp, native_recharge as nr, native_pathflow as pf
from experiments.native_recharge_qualification import cyclic_case
from experiments.train_fleet_proposals import append_dev_design_target, main, read_catalog, run


def _plan(case):
    plan = {"schema":nr.SCHEMA, "case_identity":case.identity(),
        "formulation":pf.FORMULATION, "native_matrix":pf.NATIVE_MATRIX,
        "extraction_policy":pf.EXTRACTION_POLICY,
        "vehicles":[{"vehicle":0,"trips":["A","B"],
                     "movements":["out_A","depot_AB","in_B"]}],
        "charges":[{"vehicle":0,"movement":"depot_AB","connector":0,
                    "start_min":60.0,"end_min":120.0,"grid_kwh":10.0},
                   {"vehicle":0,"movement":"in_B","connector":0,
                    "start_min":180.0,"end_min":220.0,"grid_kwh":20.0}],
        "load":[0.0,10.0,0.0,20.0], "ops_cost":7.0}
    assert nr.replay_native(case, plan)["replay_ok"]
    return plan


def _row(group, split, role, arm, prices):
    case = cyclic_case(group)
    plan = _plan(case) if arm == "source" else None
    return {"row_id":f"{group}-{role}-{arm}", "base_group":group,
        "split":split, "case":asdict(case), "case_identity":case.identity(),
        "market_role":role, "market_prices":prices,
        "market_quadratic":[0.0]*4, "arm":arm,
        "label":{"feasible":bool(plan), "plan":plan,
            "plan_hash":nr.digest(plan) if plan else None,
            "status":"bounded" if plan else "unresolved",
            "optimality":"provisional"}}


def test_training_replays_sources_and_dev_proposal_is_complete():
    rows = [_row("train1", "train", "source0", "source", [1,2,3,4]),
        _row("train2", "train", "source0", "source", [4,3,2,1]),
        _row("dev1", "dev", "source0", "source", [1,2,3,4]),
        _row("dev1", "dev", "target", "cold", [2,2,2,2])]
    model, proposals, report = run(rows)
    assert model["training_groups"] == ("train1", "train2")
    assert report["dev_proposal_count"] == 1
    assert len(report["leave_one_group_out"]) == 0  # no target markets in train
    proposal = proposals[0]
    assert proposal["source_row_id"] == "dev1-source0-source"
    assert proposal["replay_ok"] and proposal["plan"]["vehicles"]
    assert proposal["online_timing_seconds"]["total"] >= 0
    assert set(proposal["controls"]) == {"first_source", "nearest_price", "cheapest_bill"}


def test_group_split_guard_and_reserved_test_rejection(tmp_path: Path):
    rows = [_row("same", "train", "source0", "source", [1]*4),
        _row("same", "dev", "target", "cold", [2]*4)]
    path = tmp_path / "catalog.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows)+"\n")
    with pytest.raises(ValueError, match="crosses splits"):
        read_catalog(path)
    with pytest.raises(ValueError, match="Reserved test"):
        run([_row("train", "train", "source0", "source", [1]*4),
             _row("test", "test", "target", "cold", [2]*4)])
    alias = _row("same", "dev", "target", "cold", [2]*4)
    alias["base_group"] = "alias"
    path.write_text("\n".join(json.dumps(row) for row in (rows[0], alias))+"\n")
    with pytest.raises(ValueError, match="case identity aliases"):
        read_catalog(path)


def test_source_plan_must_replay_and_match_identity():
    row = _row("train", "train", "source0", "source", [1]*4)
    row["label"]["plan"]["load"][1] = 9.0
    with pytest.raises(ValueError, match="Stored physical load"):
        lp.fit([row])


def test_frozen_dev_market_precedes_target_label(tmp_path: Path):
    train = _row("train", "train", "source0", "source", [1]*4)
    source = _row("dev", "dev", "source0", "source", [2]*4)
    cold = _row("dev", "dev", "target", "cold", [3]*4)
    # This label is deliberately poisoned. Inference must use only frozen
    # market/case data, and must not inspect development target incumbents.
    cold["label"] = {"feasible":True, "plan":{"poison":"dev label"}}
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"design":{"groups":{"dev":{
        "split":"dev", "base_group":"dev", "case":source["case"],
        "case_identity":source["case_identity"],
        "markets":{"target":{"a":[3]*4,"b":[0]*4}}}}}}))
    rows = append_dev_design_target([train, source, cold], frozen)
    assert all(row.get("arm") != "cold" for row in rows)
    _, proposals, report = run(rows)
    assert report["dev_proposal_count"] == 1
    assert proposals[0]["proposed_topology"]
    assert proposals[0]["source_pool_acquisition_seconds"] == 0

    catalog = tmp_path / "catalog.jsonl"
    catalog.write_text("\n".join(json.dumps(row) for row in (train, source, cold))+"\n")
    output = tmp_path / "learned"
    main(["--catalog", str(catalog), "--frozen", str(frozen),
          "--output-dir", str(output)])
    receipt = json.loads((output / "training_receipt.json").read_text())
    assert receipt["status"] == "complete"
    assert len(receipt["inputs"]["catalog_sha256"]) == 64
    assert set(receipt["output_files"]) == {"model.json", "proposals.jsonl", "report.json"}
    with pytest.raises(ValueError, match="already exists"):
        main(["--catalog", str(catalog), "--frozen", str(frozen),
              "--output-dir", str(output)])
