"""Prospective pilot mock and archived replay tests; no native optimizer."""
import copy
from fractions import Fraction as Q
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments import sistig_nonlinear_pilot as pilot


def archived_hull_joint():
    """Read the sealed V3 schema as a pure replay fixture; never solve it."""
    cell = next(c for c in pilot.hull_gate.controls() if c["id"] == "joint_cold")
    path = pilot.ROOT / "result/native_pathflow_hull/20260927-attempt2/joint_cold/result.json"
    return cell["case"], cell["market"], json.loads(path.read_text())["result"]


def test_archived_hull_schema_and_later_valid_column_budget_limit():
    case, market, original = archived_hull_joint()
    assert pilot.assess("hull", case, market, original)["status"] == "certified"
    result = copy.deepcopy(original)
    # A valid third priced column remains in the final pool after the best
    # feasible mixture was saved over the first two columns.
    saved = pilot.nh.replay_exact_mixture(case, market, result["columns"][:2],
                                          [Q(1), Q(0)],
                                          extraction_policy=pilot.compact.EXTRACTION_POLICY)
    result.update(status="budget_exhausted", mixture=saved, upper=saved["upper"],
                  gap_exact=str(Q(saved["objective_exact"])
                                - Q(result["lower_certificate"]["lower_exact"])))
    assessed = pilot.assess("hull", case, market, result)
    assert assessed["bounded_budget_limited"] is True
    assert assessed["columns"] == 3 and len(saved["column_keys"]) == 2
    reordered_final = copy.deepcopy(result)
    reordered_final["columns"].reverse()
    assert pilot.assess("hull", case, market, reordered_final)["bounded_budget_limited"] is True
    for damaged in (dict(result, lower_certificate=None), dict(result, mixture=None),
                    dict(result, upper=float("inf"))):
        with pytest.raises((ValueError, TypeError)):
            pilot.assess("hull", case, market, damaged)
    reordered = copy.deepcopy(result)
    reordered["mixture"]["column_keys"].reverse()
    with pytest.raises(ValueError, match="does not replay"):
        pilot.assess("hull", case, market, reordered)
    duplicate = copy.deepcopy(result)
    duplicate["columns"].append(copy.deepcopy(duplicate["columns"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        pilot.assess("hull", case, market, duplicate)


def package(assessment):
    return {"assessment": assessment}


def test_declared_cell_budgets_and_unqualified_hold(tmp_path, monkeypatch):
    assert pilot.STAGES == ("planner", "hull", "own_price")
    assert list(pilot.ROUTINE_CAPS.values()) == [240, 1440, 240]
    assert list(pilot.CHILD_CAPS.values()) == [255, 1455, 255]
    assert pilot.TOTAL_CAP == 2040 and pilot.BACKEND == "GRB"
    assert pilot.budget("planner").max_rounds == 48
    assert pilot.budget("hull").pricing_calls == 6
    assert pilot.budget("hull").master_calls == 8
    assert pilot.budget("own_price").max_rounds == 1
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot, "ATTEMPT", tmp_path / "attempt")
    monkeypatch.setattr(pilot.pf, "solve_planner", lambda *a, **k: pytest.fail("optimizer called"))
    with pytest.raises(pilot.QualificationHold, match="NOT-YET-QUALIFIED"):
        pilot.freeze(tmp_path / "attempt")
    assert not (tmp_path / "attempt").exists()


def test_same_source_grb_twenty_plus_eight_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    review = tmp_path / pilot.REVIEW
    review.parent.mkdir(parents=True)
    review.write_text("**PASS** prospective implementation preflight")
    modules = ("src/egglab/native_recharge.py", "src/egglab/native_pathflow.py",
               "src/egglab/native_hull.py", "src/egglab/native_pathflow_hull.py")
    hashes = {name: f"hash-{i}" for i, name in enumerate(modules)}
    admission = {"status": "PASS", "backend": "GRB"}
    physical_budget = pilot.nr.Budget(backend="GRB", threads=1, phase_seconds=10,
                                      wall_seconds=45, max_rounds=48, epsilon=1e-4)
    hull_budget = pilot.nh.Budget(backend="GRB")
    physical_controls = [{**c, "case": pilot.asdict(c["case"]),
                          "case_identity": c["case"].identity()}
                         for c in pilot.physical_gate.controls()]
    hull_controls = [pilot.hull_gate.manifest(c, hull_budget)
                     for c in pilot.hull_gate.controls()]
    for name, count, protocol, controls, gate_budget in (
            ("physical", 20, pilot.physical_gate.PROTOCOL,
             physical_controls, physical_budget),
            ("hull", 8, pilot.hull_gate.PROTOCOL, hull_controls, hull_budget)):
        frozen = {"protocol": protocol, "budget": pilot.asdict(gate_budget),
                  "source_hashes": hashes,
                  "controls": controls,
                  "formulation": pilot.pf.FORMULATION,
                  "pricing_oracle": pilot.compact.ORACLE_ID,
                  "extraction_policy": pilot.pf.EXTRACTION_POLICY}
        documents = {"frozen": frozen,
                     "summary": {"protocol": protocol, "all_pass": True,
                                 "source_hashes_unchanged": True,
                                 "cells": [{"pass": True}] * count},
                     "audit": {"audit_status": "PASS independently reconstructed"}}
        admission[name] = {}
        for kind, content in documents.items():
            relative = Path("result") / name / f"{kind}.json"
            target = tmp_path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            pilot.write_new(target, content)
            admission[name][kind] = {"path": str(relative), "sha256": pilot.sha(target)}
    path = tmp_path / pilot.ADMISSION
    path.parent.mkdir(parents=True, exist_ok=True)
    pilot.write_new(path, admission)
    assert pilot.check_admission(hashes) == admission
    physical_frozen = tmp_path / "result/physical/frozen.json"
    original = json.loads(physical_frozen.read_text())
    changed = copy.deepcopy(original)
    changed["controls"][0]["target"] = 123456789
    physical_frozen.write_text(json.dumps(changed))
    admission["physical"]["frozen"]["sha256"] = pilot.sha(physical_frozen)
    path.write_text(json.dumps(admission))
    with pytest.raises(pilot.QualificationHold, match="incomplete"):
        pilot.check_admission(hashes)
    changed = copy.deepcopy(original)
    changed["budget"]["phase_seconds"] = 11
    physical_frozen.write_text(json.dumps(changed))
    admission["physical"]["frozen"]["sha256"] = pilot.sha(physical_frozen)
    path.write_text(json.dumps(admission))
    with pytest.raises(pilot.QualificationHold, match="incomplete"):
        pilot.check_admission(hashes)
    physical_frozen.write_text(json.dumps(original))
    admission["physical"]["frozen"]["sha256"] = pilot.sha(physical_frozen)
    path.write_text(json.dumps(admission))
    assert pilot.check_admission(hashes) == admission
    admission["hull"]["frozen"]["sha256"] = "bad"
    pilot.write_new(tmp_path / "bad.json", admission)
    path.write_text((tmp_path / "bad.json").read_text())
    with pytest.raises(pilot.QualificationHold, match="hash"):
        pilot.check_admission(hashes)


def _report_packages(planner_lo, planner_hi, hull_lo, hull_hi, response_lo, response_hi,
                     planner_status="bounded"):
    load = [10] * 30
    p = {"lower_exact_stored": str(planner_lo), "upper_exact_stored": str(planner_hi),
         "replay": {"ops_cost": 100, "load": load}, "status": planner_status,
         "plan_hash": "named-incumbent", "used_buses": 2}
    h = {"lower_exact_stored": str(hull_lo), "upper_exact_stored": str(hull_hi)}
    r = {"lower_exact_stored": str(response_lo), "upper_exact_stored": str(response_hi)}
    return package(p), package(h), package(r)


def test_signed_gap_and_own_price_regret_keep_raw_endpoints():
    prices = [0.2] * 30
    p, h, r = _report_packages(147, 150, 140, 141, 155, 158)
    result = pilot.report(p, h, r, prices)
    assert result["gap_interval_exact_stored"] == ["6", "10"]
    assert result["gap_classification"] == "resolvably_positive_above_five"
    assert Q(result["own_price_regret_interval_exact_stored"][0]) > 0
    assert result["regret_subject"] == "named_planner_incumbent"
    p, h, r = _report_packages(140.99999, 144, 140, 141, 155, 158, "certified")
    result = pilot.report(p, h, r, prices)
    assert Q(result["gap_interval_exact_stored"][0]) < 0
    assert result["gap_classification"] == "gap_at_most_five_under_declared_numerical_policy"
    assert result["regret_subject"] == "planner_optimum_under_declared_numerical_policy"
    p, h, r = _report_packages(140, 144, 140, 141, 155, 158)
    assert pilot.report(p, h, r, prices)["gap_classification"] == "unresolved_at_five"
    p, h, r = _report_packages(130, 134, 140, 141, 155, 158)
    with pytest.raises(ValueError, match="inconsistent"):
        pilot.report(p, h, r, prices)


@pytest.mark.parametrize("failure", [None, "hull_failure", "planner_timeout"])
def test_mock_controller_orders_once_and_seals_stage_receipts(tmp_path, monkeypatch, failure):
    spec = {"budgets": {stage: {"backend": "GRB"} for stage in pilot.STAGES},
            "source_hashes": {"pure": "fixed"}}
    monkeypatch.setattr(pilot, "_frozen", lambda attempt: (spec, object(), object(), "frozen"))
    monkeypatch.setattr(pilot, "source_hashes", lambda: {"pure": "fixed"})
    monkeypatch.setattr(pilot, "own_prices", lambda m, p: [0.2] * 30)
    monkeypatch.setattr(pilot, "assess", lambda stage, case, market, result, prices=None: {"stage": stage})
    monkeypatch.setattr(pilot, "report", lambda *a: {"verified": True})
    monkeypatch.setattr(pilot, "_events", lambda folder, stage: ({"native_starts": 1}, []))
    pilot.write_new(tmp_path / "supervisor_launch.json", {"mock": True})
    calls = []
    def fake_run(command, **kwargs):
        stage = command[command.index("--stage") + 1]
        calls.append(stage)
        if failure == "planner_timeout":
            raise pilot.subprocess.TimeoutExpired(command, kwargs["timeout"])
        if failure == "hull_failure" and stage == "hull":
            return SimpleNamespace(returncode=2)
        folder = tmp_path / stage
        pilot.write_new(folder / "result.json", {"stage": stage, "frozen_sha256": "frozen",
                        "elapsed_seconds": 1, "result": {"status": "bounded"},
                        "assessment": {"stage": stage}})
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(pilot.subprocess, "run", fake_run)
    assert pilot.controller(tmp_path) == (0 if failure is None else 1)
    assert calls == (["planner", "hull", "own_price"] if failure is None else
                     ["planner", "hull"] if failure == "hull_failure" else ["planner"])
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["complete"] is (failure is None)
    for stage in calls:
        receipt = json.loads((tmp_path / stage / "receipt.json").read_text())
        assert receipt["stage"] == stage
    if failure == "planner_timeout":
        assert summary["stages"][0]["hard_timeout"]
        assert summary["unstarted_stages"] == ["hull", "own_price"]


def test_mock_worker_uses_frozen_planner_budget_only(tmp_path, monkeypatch):
    stage = "planner"
    folder = tmp_path / stage
    folder.mkdir()
    pilot.write_new(tmp_path / "STARTED.json", {"mock": True})
    pilot.write_new(folder / "launch.json", {"mock": True})
    pilot.write_new(folder / "input.json", {"stage": stage, "frozen_sha256": "frozen",
                    "budget": vars(pilot.budget(stage))})
    market = SimpleNamespace(a=(.2,) * 30, b=(1/900,) * 30)
    case = object()
    spec = {"budgets": {stage: vars(pilot.budget(stage))}}
    monkeypatch.setattr(pilot, "_frozen", lambda attempt: (spec, case, market, "frozen"))
    calls = []
    def fake_planner(got_case, a, b, got_budget, record):
        calls.append((got_case, a, b, got_budget))
        record({"event": "native_start", "round": 0})
        return {"status": "bounded"}
    monkeypatch.setattr(pilot.pf, "solve_planner", fake_planner)
    monkeypatch.setattr(pilot, "assess", lambda *a: {"status": "bounded"})
    assert pilot.worker(tmp_path, stage) == 0
    assert len(calls) == 1 and calls[0][0] is case
    assert calls[0][3].backend == "GRB" and calls[0][3].wall_seconds == 240
    assert json.loads((folder / "result.json").read_text())["assessment"]["status"] == "bounded"
    assert json.loads((folder / "raw_result.json").read_text())["result"]["status"] == "bounded"


def test_worker_preserves_returned_raw_result_when_assessment_fails(tmp_path, monkeypatch):
    folder = tmp_path / "hull"
    folder.mkdir()
    pilot.write_new(tmp_path / "STARTED.json", {"mock": True})
    pilot.write_new(folder / "launch.json", {"mock": True})
    pilot.write_new(folder / "input.json", {"stage": "hull", "frozen_sha256": "frozen",
                    "budget": vars(pilot.budget("hull"))})
    monkeypatch.setattr(pilot, "_frozen", lambda attempt: (
        {"budgets": {"hull": vars(pilot.budget("hull"))}}, object(), object(), "frozen"))
    monkeypatch.setattr(pilot.compact, "certify", lambda *a, **k: {
        "status": "budget_exhausted", "lower_certificate": None})
    monkeypatch.setattr(pilot, "assess", lambda *a: (_ for _ in ()).throw(
        ValueError("incomplete global certificate")))
    assert pilot.worker(tmp_path, "hull") == 2
    assert json.loads((folder / "raw_result.json").read_text())["result"]["status"] == "budget_exhausted"
    assert not (folder / "result.json").exists()
    assert "incomplete global certificate" in json.loads((folder / "exception.json").read_text())["message"]


def test_supervisor_prechild_hold_still_seals_receipt(tmp_path, monkeypatch):
    pilot.write_new(tmp_path / "frozen.json", {"source_hashes": {"pure": "old"}})
    monkeypatch.setattr(pilot, "_frozen", lambda attempt: (_ for _ in ()).throw(
        pilot.QualificationHold("NOT-YET-QUALIFIED: gate changed")))
    assert pilot.supervise(tmp_path) == 1
    receipt = json.loads((tmp_path / "supervisor_receipt.json").read_text())
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert receipt["returncode"] == 1 and receipt["child_returncode"] is None
    assert "NOT-YET-QUALIFIED" in receipt["exception"]
    assert "supervisor_receipt.json" in manifest["files"]


def test_partial_event_log_keeps_valid_prefix_and_failure_issue(tmp_path):
    (tmp_path / "events.jsonl").write_bytes(
        b'{"event":"native_start","round":0}\n{"event":')
    counts, issues = pilot._events(tmp_path, "own_price")
    assert counts["native_starts"] == 1 and counts["native_returns"] == 0
    assert issues[0]["valid_prefix_events"] == 1
    assert any("Incomplete physical" in issue["message"] for issue in issues)


@pytest.mark.parametrize("source_drift,timeout,expected", [(True, False, 1),
                                                              (False, True, 124)])
def test_mock_supervisor_manifest_on_drift_or_timeout(tmp_path, monkeypatch,
                                                      source_drift, timeout, expected):
    pilot.write_new(tmp_path / "frozen.json", {"source_hashes": {"pure": "fixed"}})
    monkeypatch.setattr(pilot, "_frozen", lambda attempt: ({}, None, None, "frozen"))
    def hashes():
        if source_drift:
            raise FileNotFoundError("pinned source deleted")
        return {"pure": "fixed"}
    monkeypatch.setattr(pilot, "source_hashes", hashes)
    waits = []
    class FakeProcess:
        pid = 12345
        def wait(self, timeout=None):
            waits.append(timeout)
            if timeout == pilot.TOTAL_CAP and source_drift is False:
                raise pilot.subprocess.TimeoutExpired("fake", timeout)
            return 0
    monkeypatch.setattr(pilot.subprocess, "Popen", lambda *a, **k: FakeProcess())
    monkeypatch.setattr(pilot.os, "killpg", lambda *a, **k: None)
    assert pilot.supervise(tmp_path) == expected
    receipt = json.loads((tmp_path / "supervisor_receipt.json").read_text())
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert receipt["returncode"] == expected
    assert receipt["outer_timeout"] is timeout
    assert "supervisor_receipt.json" in manifest["files"]
    assert manifest["files"]["supervisor_receipt.json"]["sha256"] == pilot.sha(
        tmp_path / "supervisor_receipt.json")
