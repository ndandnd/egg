"""Pure ordered-comparison admission and accounting checks; no native solver."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

import pytest

from egglab import native_hull as nh
from experiments import solver_baseline_comparison as run
from experiments import native_hull_qualification as qualification
from test_native_hull import install_fakes
from test_native_hull_numerical_master import fake_proposal


def test_design_is_ordered_32_cells_with_exact_declared_controls():
    design = run.design()
    assert len(design) == 4
    assert run.ARMS == ("reserve_cold_hull", "reserve_feasible_hull",
                        "qp_feasible_hull", "qp_cache_feasible_hull")
    assert len(run.CASES) * len(run.ARMS) * len(run.STATES) == 32
    for name, row in design.items():
        assert row["hard_child_seconds"] == row["budget"]["wall_seconds"] + 30
        assert row["arms"]["reserve_cold_hull"]["hull_arm"] == "cold"
        assert all(row["arms"][arm]["hull_arm"] == "retained" for arm in run.ARMS[1:])
        assert all(row["arms"][arm]["controls"]["pricing_reserve_seconds"] == 10.0
                   for arm in run.ARMS)
        assert all(row["arms"][arm]["controls"]["qp_denominator"] == 1_000_000_000
                   for arm in run.ARMS[2:])
        assert "bound_cache_policy" not in row["arms"]["qp_feasible_hull"]["controls"]
        assert row["arms"]["qp_cache_feasible_hull"]["controls"]["bound_cache_policy"] == "physical_pricing"
    assert design["public_depot15"]["base_timetable_group"] == "hildenbrand_37"
    assert design["public_depot16"]["base_timetable_group"] == "hildenbrand_37"
    assert "src/egglab/restricted_qp_proposal.py" in run.SOURCES
    assert "doc/SOLVER_BASELINE_COMPARISON_PROTOCOL_20260928.md" in run.SOURCES


def source_fixture(monkeypatch, root, *, arm="qp_cache_feasible_hull", status=None):
    install_fakes(monkeypatch)
    fake_proposal(monkeypatch)
    name = "synthetic_cyclic"
    case, market = qualification.controls()[0]["case"], qualification.controls()[0]["market"]
    monkeypatch.setattr(run.base, "cases", lambda: {name: case})
    monkeypatch.setattr(run.base, "market", lambda _name, _state: market)
    cfg = run.base.budget(name, "cold_hull")
    original = nh.nr.solve_pricing
    def pricing(case, prices, budget, record=None):
        raw = original(case, prices, budget, record)
        raw["plan"] = {**raw["plan"], "formulation": run.compact.ORACLE_ID,
                       "extraction_policy": run.compact.EXTRACTION_POLICY}
        raw["formulation"] = run.compact.ORACLE_ID
        raw["extraction_policy"] = run.compact.EXTRACTION_POLICY
        return raw
    events = []
    prior = nh.certify(case, market, cfg, arm="retained", state_index=0,
                       pricing_oracle=pricing, oracle_id=run.compact.ORACLE_ID,
                       extraction_policy=run.compact.EXTRACTION_POLICY,
                       record=events.append, **run.controls(arm))
    if status is not None:
        prior["status"] = status
    folder = run.cell_dir(root, name, 0, arm)
    run.base.save_new(folder / "raw_result.json", {"result": prior, "case": name,
                      "state": 0, "stage": arm})
    assessment = run.base.assess(case, market, arm, prior)
    run.base.save_new(folder / "result.json", {"assessment": assessment, "case": name,
                      "state": 0, "stage": arm})
    run.base.save_new(folder / "receipt.json", {"returncode": 0, "hard_timeout": False,
                      "on_time": True, "elapsed_seconds": 4.0,
                      "hard_seconds": cfg.wall_seconds + 30})
    (folder / "events.jsonl").write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in events))
    return name, folder, prior


def test_own_source_and_all_cache_events_are_admitted_then_pinned(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        name, folder, prior = source_fixture(monkeypatch, tmp)
        admitted = run.admission(tmp, name, "qp_cache_feasible_hull")
        assert admitted["eligible"] is True
        assert admitted["source_state_identity"] == prior["state_identity"]
        assert set(admitted["source_files"]) == set(run.SOURCE_FILES)
        assert run.predecessor(tmp, name, "qp_cache_feasible_hull",
                               admitted["source_files"])[0] == prior
        (folder / "result.json").write_text((folder / "result.json").read_text() + " ")
        assert run.admission(tmp, name, "qp_cache_feasible_hull")["eligible"] is True
        with pytest.raises(ValueError, match="differ from parent admission"):
            run.predecessor(tmp, name, "qp_cache_feasible_hull", admitted["source_files"])


@pytest.mark.parametrize("corrupt", ["price", "lower", "witness", "missing_event",
                                   "event_shape", "proposal_failed", "late"])
def test_bad_own_source_is_ineligible(monkeypatch, corrupt):
    with tempfile.TemporaryDirectory() as tmp:
        name, folder, _ = source_fixture(monkeypatch, tmp)
        if corrupt in ("price", "lower", "witness", "missing_event", "event_shape"):
            events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
            if corrupt == "price":
                next(e for e in events if e["event"] == "pricing_request")["prices"][0] += 1
            elif corrupt == "lower":
                next(e for e in events if e["event"] == "pricing_result")["result"]["stats"]["lower_bound"] += 1
            elif corrupt == "witness":
                next(e for e in events if e["event"] == "pricing_result")["result"]["plan"]["ops_cost"] += 1
            elif corrupt == "event_shape":
                events[0] = None
            else:
                events = [e for e in events if e["event"] != "global_bound"]
            (folder / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
        elif corrupt == "proposal_failed":
            wrapped = json.loads((folder / "raw_result.json").read_text())
            wrapped["result"]["status"] = "proposal_failed"
            (folder / "raw_result.json").write_text(json.dumps(wrapped))
        else:
            receipt = json.loads((folder / "receipt.json").read_text())
            receipt.update(on_time=False, hard_timeout=True)
            (folder / "receipt.json").write_text(json.dumps(receipt))
        assert run.admission(tmp, name, "qp_cache_feasible_hull")["eligible"] is False


def test_partial_accounting_preserves_timeout_and_unknown_pair_costs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = run.cell_dir(root, "synthetic_cyclic", 0, run.ARMS[0])
        run.base.save_new(folder / "result.json", {"assessment": {"status": "certified",
                          "bounds": ["1", "2"], "complete_evidence": True,
                          "counts": {}, "columns": 1, "polish_soft_excess_seconds": 0}})
        run.base.save_new(folder / "receipt.json", {"returncode": -15,
                          "hard_timeout": True, "on_time": False,
                          "elapsed_seconds": 91, "hard_seconds": 90})
        run.base.save_new(run.cell_dir(root, "synthetic_cyclic", 1, run.ARMS[0]) /
                          "launch.json", {"command": ["unimportant"]})
        bad_admission = run.cell_dir(root, "synthetic_cyclic", 1, "reserve_feasible_hull") / "admission.json"
        bad_admission.parent.mkdir(parents=True)
        bad_admission.write_text('{"eligible":')
        rows = run.reconcile_partial(root)
        assert len(rows) == 32
        assert (rows[0]["status"], rows[0]["native_status"]) == ("timed_out", "certified")
        assert rows[1]["status"] == "interrupted_unreceipted"
        pair = run.paid_pairs(rows)[0]
        assert pair["state0_child_elapsed_seconds"] == 91
        assert pair["state1_child_elapsed_seconds"] is None
        assert pair["complete_two_state_paid_seconds"] is None
        assert rows[3]["status"] == "admission_unreadable"


def test_pair_cost_adds_parent_admission_once():
    rows = [{"case": "synthetic_cyclic", "stage": "reserve_feasible_hull", "state": 0,
             "receipt": {"elapsed_seconds": 12}},
            {"case": "synthetic_cyclic", "stage": "reserve_feasible_hull", "state": 1,
             "receipt": {"elapsed_seconds": 15},
             "admission": {"parent_check_elapsed_seconds": 2}}]
    pair = next(p for p in run.paid_pairs(rows) if p["case"] == "synthetic_cyclic"
                and p["arm"] == "reserve_feasible_hull")
    assert pair["complete_two_state_paid_seconds"] == 29
    assert run.paid_pairs(rows)[0]["complete_two_state_paid_seconds"] is None


def test_source_drift_reconciles_all_cells_and_seals(monkeypatch, tmp_path):
    target = tmp_path / "attempt"
    target.mkdir()
    run.base.save_new(target / "frozen.json", {"source_hashes": {"pin": "before"}})
    monkeypatch.setattr(run, "ATTEMPT", target)
    monkeypatch.setattr(run, "frozen", lambda _: (_ for _ in ()).throw(ValueError("source drift")))
    monkeypatch.setattr(run, "source_hashes", lambda: {"pin": "after"})
    assert run.supervise(target) == 1
    assert len(json.loads((target / "postmortem_summary.json").read_text())["rows"]) == 32
    assert (target / "MANIFEST.json").is_file()
