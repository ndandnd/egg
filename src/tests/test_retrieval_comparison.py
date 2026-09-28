"""Pure replay and provenance tests; no solver/model allocation."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from egglab import native_hull as nh
from egglab import native_pathflow_hull as compact
from egglab import native_recharge as nr
from experiments import native_scaling_cases as scaling
from experiments import retrieval_comparison as run


def fixture_candidate():
    name = run.SYNTHETIC_CASES[0]
    case = scaling.cases()[name]
    plan = deepcopy(scaling.witnesses()[name])
    plan["formulation"] = compact.ORACLE_ID
    plan["extraction_policy"] = compact.EXTRACTION_POLICY
    m = run.market(name, "source0")
    cfg = run.budget(name, "source0")
    identity = compact.state_identity(case, m, "retained", 0, cfg, **run.HULL_CONTROLS)
    prices = list(m.a)
    column = nh.native_column(case, plan,
                              {"state_identity": identity, "pricing_call": 0,
                               "pricing_oracle": compact.ORACLE_ID},
                              compact.EXTRACTION_POLICY)
    objective = column["ops_cost"] + sum(p*x for p, x in zip(prices, column["load"]))
    stats = {"status": "FEASIBLE", "incumbent": objective,
             "lower_bound": objective-1.0, "wall_s": 0.01,
             "backend": "GRB", "threads": 1}
    lower, upper = nr.admit_bound(stats, objective)
    result = {"case_identity": case.identity(), "prices": prices,
              "formulation": compact.ORACLE_ID,
              "extraction_policy": compact.EXTRACTION_POLICY,
              "status": "bounded", "plan": plan, "stats": stats,
              "lower": lower, "upper": upper}
    request = {"event": "pricing_request", "call": 0, "prices": prices}
    priced = {"event": "pricing_result", "call": 0, "result": result}
    bound = {"event": "global_bound", "call": 0, "column": column,
             "certificate": nh.fenchel_bound(m, prices, lower)}
    return name, case, m, identity, request, priced, bound


def test_source_admits_complete_early_call_when_last_call_unresolved(tmp_path):
    name, case, m, identity, request, priced, bound = fixture_candidate()
    folder = tmp_path / name / "source0"
    folder.mkdir(parents=True)
    later_request = {"event": "pricing_request", "call": 1, "prices": list(m.a)}
    later_result = {"event": "pricing_result", "call": 1,
                    "result": {"case_identity": case.identity(), "prices": list(m.a),
                               "status": "unresolved"}}
    with (folder / "events.jsonl").open("w") as stream:
        for event in (request, priced, bound, later_request, later_result):
            stream.write(json.dumps(event) + "\n")
    (folder / "receipt.json").write_text(json.dumps({
        "returncode": 2, "hard_timeout": False, "on_time": False,
        "elapsed_seconds": 7.0,
        "hard_seconds": run.budget(name, "source0").wall_seconds + run.CHILD_MARGIN}))
    admitted = run.admit_source(tmp_path, name, "source0")
    assert admitted["complete_source_return"] is False
    assert admitted["unused_result_calls"] == [1]
    assert admitted["candidates"][0]["source_state_identity"] == identity
    assert len(admitted["candidates"]) == 1


def test_source_rejects_tampered_call_price_and_column(tmp_path):
    name, case, m, identity, request, priced, bound = fixture_candidate()
    changed = deepcopy(request)
    changed["prices"][0] += 0.01
    with pytest.raises(ValueError, match="lineage"):
        run._candidate(case, m, identity, "source0", changed, priced, bound)
    changed_bound = deepcopy(bound)
    changed_bound["column"]["witness_hash"] = "changed"
    with pytest.raises(ValueError):
        run._candidate(case, m, identity, "source0", request, priced, changed_bound)


def test_import_envelope_rejects_changed_selected_payload():
    name, case, m, identity, request, priced, bound = fixture_candidate()
    candidate = run._candidate(case, m, identity, "source0", request, priced, bound)
    pool = {"candidates": [candidate], "sources": {
        "source0": {"files": {"events.jsonl": {"sha256": "a", "bytes": 1}},
                    "source_state_identity": identity},
        "source1": {"files": {}, "source_state_identity": None}}}
    target = run.market(name, "target")
    cfg = run.budget(name, "retained")
    envelope, expected = run.import_envelope(case, target, cfg, pool, [candidate])
    assert envelope["status"] == "bounded"
    assert envelope["kind"] == "derived_feasible_pool_import"
    assert "lower" not in envelope and "gap" not in envelope and "counts" not in envelope
    assert envelope["columns"][0]["source"]["original_source"] == candidate["column"]["source"]
    assert expected == envelope["state_identity"]
    changed = deepcopy(candidate)
    changed["prices"][0] += 0.01
    with pytest.raises(ValueError, match="differs from admitted"):
        run.import_envelope(case, target, cfg, pool, [changed])
    changed = deepcopy(candidate)
    changed["column"]["load"][0] += 1
    with pytest.raises(ValueError, match="differs from admitted"):
        run.import_envelope(case, target, cfg, pool, [changed])


def test_retrieval_selections_share_pool_and_price_bill_exact():
    name, case, m, identity, request, priced, bound = fixture_candidate()
    first = run._candidate(case, m, identity, "source0", request, priced, bound)
    second = deepcopy(first)
    second["source"] = "source1"
    second["call"] = 1
    second["prices"] = list(run.market(name, "target").a)
    second["key"] = "different-projection"
    second["column"]["key"] = "different-projection"
    pool = {"eligible": True, "candidates": [first, second]}
    target = run.market(name, "target")
    assert run.select(pool, target, "nearest_price")[0] is second
    # Same bill forces source-order tie even though the nearest price differs.
    assert run.select(pool, target, "cheapest_bill")[0] is first
    assert run.exact_bill(first["column"], target.a) == run.exact_bill(second["column"], target.a)
    assert run.arm_order(0) != run.arm_order(1)


def test_primary_metrics_exclude_late_results_and_charge_pool_preparation():
    rows = []
    for stage in ("planner", "response", *run.ARMS):
        rows.append({"stage": stage, "status": "bounded",
                     "receipt": {"on_time": True, "returncode": 0},
                     "assessment": {"bounds": ["10", "12"],
                                    "executable_cost_exact": "12",
                                    "own_price_regret_interval_exact": ["1", "2"]}})
    rows[0]["receipt"]["on_time"] = False
    rows[1]["receipt"]["returncode"] = 2
    rows[2]["receipt"]["on_time"] = False
    metrics = run.comparison_metrics(rows)
    assert metrics["physical_planner_D_interval"] is None
    assert metrics["own_price_regret_interval_exact"] is None
    assert metrics["hull_by_arm"]["cold"]["CH_interval"] is None
    assert metrics["hull_by_arm"]["retained"]["CH_interval"] == ["10", "12"]
    pool = {"sources": {"source0": {"paid_source_seconds": 5.0},
                        "source1": {"paid_source_seconds": 7.0}}}
    assert run.paid_pool_costs(pool, 3.0) == {
        "source_generation_child_seconds": 12.0,
        "pool_preparation_seconds": 3.0,
        "paid_source_pool_seconds": 15.0}


def test_hard_stop_row_preserves_direct_proposal_artifact(tmp_path):
    name = run.SYNTHETIC_CASES[0]
    folder = tmp_path / name / "nearest_price"
    folder.mkdir(parents=True)
    (folder / "proposal.json").write_text(json.dumps({"selected_keys": ["fleet-a"],
                                                      "direct_proposal_wall_seconds": 0.2}))
    receipt = {"returncode": -9, "hard_timeout": True, "on_time": False,
               "elapsed_seconds": 120.0, "hard_seconds": 120}
    row = run.result_row(tmp_path, name, "nearest_price", receipt)
    assert row["status"] == "hard_timeout"
    assert row["direct_proposal"]["selected_keys"] == ["fleet-a"]


def test_supervisor_enforces_controller_cap_before_outer_cap(tmp_path, monkeypatch):
    (tmp_path / "frozen.json").write_text(json.dumps({"source_hashes": {}}))
    monkeypatch.setattr(run, "_attempt", lambda path: tmp_path)
    monkeypatch.setattr(run, "frozen", lambda path: {})
    monkeypatch.setattr(run, "source_hashes", lambda: {})
    monkeypatch.setattr(run.subprocess, "Popen", lambda *args, **kwargs: object())
    seen = []
    monkeypatch.setattr(run.base, "wait_process_group",
                        lambda process, hard: (seen.append(hard) or (0, False, True)))
    monkeypatch.setattr(run, "seal_manifest", lambda path: None)
    assert run.supervise(tmp_path) == 0
    assert seen == [run.CONTROLLER_CAP]
    launch = json.loads((tmp_path / "supervisor_launch.json").read_text())
    assert launch["controller_hard_seconds"] == run.CONTROLLER_CAP
    assert launch["supervisor_outer_seconds"] == run.SUPERVISOR_CAP


def test_hull_assessment_binds_reported_interval_to_replayed_evidence():
    name, case, m, identity, request, priced, bound = fixture_candidate()
    column = bound["column"]
    mixture = nh.replay_mixture(case, m, [column], [1.0], compact.EXTRACTION_POLICY)
    result = {"schema": nh.SCHEMA, "physical_identity": case.identity(),
              "market_identity": m.identity(), "pricing_oracle": compact.ORACLE_ID,
              "extraction_policy": compact.EXTRACTION_POLICY,
              "reuse_policy": "feasible_pool", "master_policy": "numerical_qp_proposal",
              "pricing_reserve_seconds": 10.0, "status": "bounded",
              "columns": [column], "counts": {},
              "lower_certificate": bound["certificate"],
              "lower": bound["certificate"]["lower"],
              "mixture": mixture, "upper": mixture["upper"]}
    assert run.assess_hull(case, m, result)["bounds"] is not None
    changed = deepcopy(result)
    changed["lower"] -= 0.01
    with pytest.raises(ValueError, match="reported lower"):
        run.assess_hull(case, m, changed)
    changed = deepcopy(result)
    changed["upper"] += 0.01
    with pytest.raises(ValueError, match="reported upper"):
        run.assess_hull(case, m, changed)
