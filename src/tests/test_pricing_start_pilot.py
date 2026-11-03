"""Pure checks for the prospective pricing-start driver; no optimizer calls."""
from fractions import Fraction
import json

import pytest

from experiments import pricing_start_pilot as pilot


def test_declared_order_and_caps():
    assert len(pilot.CASES) * len(pilot.QUERIES) * len(pilot.ARMS) == 16
    assert [pilot.arm_order(i, 0)[0] for i in range(4)] == ["cold", "start", "cold", "start"]
    assert [pilot.arm_order(i, 1)[0] for i in range(4)] == ["start", "cold", "start", "cold"]
    assert sum(pilot.budget(name).wall_seconds * 4 for name in pilot.CASES) == 1920
    assert sum((pilot.budget(name).wall_seconds + 30) * 4 for name in pilot.CASES) == 2400
    assert pilot.CONTROLLER_CAP == 2700


def test_query_selection_uses_stored_number_rationals_and_key_tie_break(monkeypatch):
    class Market:
        a = (0.1, 0.2)
        b = (0.25, 0.5)
    monkeypatch.setattr(pilot.base, "market", lambda *_: Market())
    columns = [
        {"key": "z", "ops_cost": 1.0, "load": [2.0, 0.0], "plan": {"vehicles": [{"movements": ["a"]}]}, "physical_identity": "case"},
        {"key": "a", "ops_cost": 1.0, "load": [0.0, 1.0], "plan": {"vehicles": [{"movements": ["b", "c"]}]}, "physical_identity": "case"},
    ]
    queries = pilot._queries("example", columns)
    assert queries["linear_tariff"]["source_column_key"] == "a"  # equal cost, canonical key
    marginal = queries["marginal_price"]
    expected = Fraction(0.2) + Fraction(0.5) * Fraction(1.0)
    assert marginal["prices_exact"][1] == str(expected)
    assert marginal["gradient_anchor_key"] == "a"
    assert marginal["source_column_key"] == "z"
    assert marginal["source_pricing_objective_exact"] == str(pilot._bill(columns[0], marginal["prices"]))


@pytest.mark.parametrize("status", ["submitted", "rejected", "timed_out"])
def test_start_aware_reader_retains_setup_and_time(tmp_path, status):
    folder = tmp_path / "cell"
    folder.mkdir()
    event = {"event": "mip_start_setup", "status": status, "setup_elapsed_s": 0.25,
             "timings": {"validation_s": 0.1}}
    (folder / "events.jsonl").write_text(json.dumps(event) + "\n")
    events, issues = pilot.read_worker_evidence(folder)
    assert events == [event]
    assert issues == []


def test_reader_preserves_valid_prefix_on_partial_event(tmp_path):
    folder = tmp_path / "cell"
    folder.mkdir()
    (folder / "events.jsonl").write_text(json.dumps({"event": "mip_start_setup",
        "status": "rejected", "setup_elapsed_s": 0.3, "timings": {}}) + "\n{" )
    events, issues = pilot.read_worker_evidence(folder)
    assert len(events) == 1 and events[0]["status"] == "rejected"
    assert issues[0]["valid_prefix_events"] == 1


def test_no_plan_has_common_source_upper_but_no_native_interval(monkeypatch):
    class Case:
        def identity(self):
            return "case"
    result = {"case_identity": "case", "prices": [1.0], "formulation": pilot.pf.FORMULATION,
              "native_matrix": pilot.pf.NATIVE_MATRIX,
              "extraction_policy": pilot.pf.EXTRACTION_POLICY,
              "status": "unresolved", "stats": {"status": "NO_SOLUTION", "lower_bound": 7.0},
              "plan": None}
    assessed = pilot._assessment(Case(), [1.0], result, 10.0)
    assert assessed["native_admitted_interval"] is None
    assert assessed["best_feasible_upper"] == 10.0
    assert assessed["raw_native_stats"]["lower_bound"] == 7.0


def test_result_row_keeps_failed_start_setup_without_cold_reclassification(tmp_path):
    folder = pilot.cell_dir(tmp_path, "synthetic_cyclic", "linear_tariff", "start")
    folder.mkdir(parents=True)
    (folder / "events.jsonl").write_text(json.dumps({"event": "mip_start_setup",
        "status": "rejected", "stage": "start_attach", "setup_elapsed_s": 0.7,
        "timings": {"validation_s": 0.2}, "error_type": "ValueError"}) + "\n")
    row = pilot.result_row(tmp_path, "synthetic_cyclic", "linear_tariff", "start",
        {"hard_timeout": False, "returncode": 2, "elapsed_seconds": 1.0},
        {"selected_movement_count": 3, "source_pricing_objective": 10.0})
    assert row["status"] == "failed"
    assert row["start_requested"] is True and row["start_submitted"] is False
    assert row["start_setup_events"][0]["setup_elapsed_s"] == 0.7
    assert row["native_acceptance"] == "unknown"


def test_source_path_mismatch_is_ineligible_before_read(tmp_path):
    class Case:
        pass
    admitted = pilot._source_case(tmp_path, {"case": "synthetic_cyclic",
        "source_relative_path": "synthetic_cyclic/state1/qp_cache_feasible_hull"},
        "synthetic_cyclic", Case())
    assert admitted["eligible"] is False
    assert "path/case" in admitted["reason"]


def test_native_probe_reads_effective_seed_without_optimize(monkeypatch):
    import mip
    class Model:
        seed = 17
    monkeypatch.setattr(mip, "Model", lambda **_kwargs: Model())
    monkeypatch.setattr(pilot.nr, "_backend_identity", lambda model, requested:
                        {"requested": requested, "native_library_sha256": "abc"})
    assert pilot.native_probe() == {"backend_identity": {"requested": "GRB",
        "native_library_sha256": "abc"}, "model_seed": 17}
