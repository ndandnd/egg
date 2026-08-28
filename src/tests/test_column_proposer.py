"""Acceptance battery for the bounded local-move proposer laboratory."""
from __future__ import annotations

import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import egglab.column_proposer as proposer
import experiments.run_column_proposer as runner
from egglab.b2a2 import RC_TOL
from egglab.instance import synthetic_instance


def _source_rows(inst):
    trip_ids = [trip.id for trip in inst.trips]
    source = [[trip_ids[0], trip_ids[2]], [trip_ids[1], trip_ids[3]]]
    return (
        [{"column_key": "source", "lambda": 1.0, "sequences": source}],
        [{"column_key": "source", "sequences": source}],
    )


def test_move_catalog_is_label_invariant_deterministic_and_complete():
    inst = synthetic_instance(seed=1, n_trips=4)
    active, prefix = _source_rows(inst)

    first = proposer.local_move_catalog(inst, active, prefix)
    reversed_labels = [{
        **active[0],
        "sequences": list(reversed(active[0]["sequences"])),
    }]
    second = proposer.local_move_catalog(inst, reversed_labels, prefix)

    assert first == second
    assert first
    assert len({row["candidate_id"] for row in first}) == len(first)
    for row in first:
        covered = sorted(tid for chain in row["sequences"] for tid in chain)
        assert covered == sorted(trip.id for trip in inst.trips)
        assert row["origins"]
        assert {origin["kind"] for origin in row["origins"]} <= {
            "relocate", "swap"}
        assert row["sequences"] != prefix[0]["sequences"]


def test_move_catalog_excludes_every_existing_partition():
    inst = synthetic_instance(seed=1, n_trips=4)
    active, prefix = _source_rows(inst)
    catalog = proposer.local_move_catalog(inst, active, prefix)
    blocked = catalog[0]
    prefix = prefix + [{
        "column_key": "already-present",
        "sequences": blocked["sequences"],
    }]

    after = proposer.local_move_catalog(inst, active, prefix)

    assert blocked["candidate_id"] not in {
        row["candidate_id"] for row in after}


def test_strict_reduced_cost_gate_and_honest_outcomes():
    assert proposer.classify_reduced_cost(
        -1.01 * RC_TOL, novel=True) == "ACCEPTED"
    assert proposer.classify_reduced_cost(
        -RC_TOL, novel=True) == "TOLERANCE-TIE"
    assert proposer.classify_reduced_cost(
        RC_TOL, novel=True) == "TOLERANCE-TIE"
    assert proposer.classify_reduced_cost(
        1.01 * RC_TOL, novel=True) == "NONIMPROVING"
    assert proposer.classify_reduced_cost(
        0.0, novel=False) == "DUPLICATE"
    with pytest.raises(
            proposer.ColumnProposerError,
            match="duplicate candidate"):
        proposer.classify_reduced_cost(-2 * RC_TOL, novel=False)

    assert proposer.disposition(0, 0) == "NO-OPPORTUNITY"
    assert proposer.disposition(4, 0) == "HONEST-NEGATIVE"
    assert proposer.disposition(4, 1) == "LIMITED-SIGNAL"
    assert proposer.disposition(4, 2) == "POSITIVE-SPIKE"


@pytest.mark.parametrize("seed", proposer.SEEDS)
def test_singleton_witness_proves_replacement_population_feasible(seed):
    inst = synthetic_instance(
        seed=seed,
        n_trips=proposer.N_TRIPS,
        max_vehicles=proposer.MAX_VEHICLES,
    )
    witness = proposer.singleton_feasibility_witness(inst)

    assert witness["vehicle_count"] == proposer.N_TRIPS
    assert witness["max_vehicles"] == proposer.MAX_VEHICLES
    assert witness["minimum_terminal_margin_kwh"] >= 0.0
    assert len(witness["trips"]) == proposer.N_TRIPS


@pytest.fixture(scope="module")
def one_cell_report(tmp_path_factory):
    """Real solver-backed evidence, narrowed only inside this test process."""
    original_cells = proposer.CELLS
    proposer.CELLS = ((0, 4, 0.01),)
    try:
        run_root = tmp_path_factory.mktemp("column-proposer-raw")
        # build_report requires a fresh root; tmp_path_factory creates it, so
        # use a not-yet-existing child.
        report = proposer.build_report(
            run_root / "run",
            "a" * 40,
            cells=proposer.CELLS,
        )
        yield report
    finally:
        proposer.CELLS = original_cells


def test_real_prefix_candidates_are_exactly_scored_and_replay(one_cell_report):
    assert proposer.audit_report(one_cell_report) == []
    cell = one_cell_report["cells"][0]
    assert cell["baseline"]["certified"]
    assert cell["snapshots"]
    for snapshot in cell["snapshots"]:
        assert snapshot["prices"] == pytest.approx(
            [-value for value in snapshot["rmp"]["pi"]])
        assert "lb_ch" not in snapshot
        assert "lb_best" not in snapshot
        for proposal in snapshot["proposals"]:
            if proposal["classification"] == "INFEASIBLE-PARTITION":
                assert proposal["evidence"] is None
                continue
            evidence = proposal["evidence"]
            assert evidence["replay_ok"] is True
            if proposal["classification"] == "ACCEPTED":
                assert proposal["novel"] is True
                assert evidence["reduced_cost"] < -RC_TOL
            # A fixed-partition bound is retained as evidence but never
            # promoted to a convex-hull lower-bound field.
            assert "bound" in evidence["solver"]
            assert "lb_ch" not in proposal
            assert "lb_best" not in proposal


def test_independent_audit_rejects_coordinated_summary_or_physics_tamper(
        one_cell_report):
    summary_tamper = copy.deepcopy(one_cell_report)
    summary_tamper["summary"]["captured_opportunities"] += 1
    assert any(
        "aggregate summary" in error
        for error in proposer.audit_report(summary_tamper))

    physics_tamper = copy.deepcopy(one_cell_report)
    evidence = (
        physics_tamper["cells"][0]["snapshots"][0]
        ["global_pricing"]["evidence"]
    )
    evidence["load"][0] += 1.0
    errors = proposer.audit_report(physics_tamper)
    assert any(
        "physical load mismatch" in error or "column key mismatch" in error
        for error in errors)


def test_publish_refuses_existing_raw_or_output_without_solving(tmp_path):
    raw = tmp_path / "raw"
    out = tmp_path / "out"
    raw.mkdir()
    with pytest.raises(
            proposer.ColumnProposerError, match="existing raw run root"):
        proposer.publish(
            raw, out, analysis_commit="a" * 40, verify_git=False)

    raw.rmdir()
    out.mkdir()
    with pytest.raises(
            proposer.ColumnProposerError, match="existing output directory"):
        proposer.publish(
            raw, out, analysis_commit="a" * 40, verify_git=False)


def test_runner_requires_and_forwards_caller_supplied_output_paths(
        tmp_path, monkeypatch):
    calls = []

    def fake_publish(run_root, out_dir, analysis_commit=None):
        calls.append((run_root, out_dir, analysis_commit))
        return out_dir

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner, "publish", fake_publish)
    monkeypatch.setattr(sys, "argv", ["run_column_proposer.py"])
    with pytest.raises(SystemExit) as exc:
        runner.main()
    assert exc.value.code == 2
    assert calls == []
    assert list(tmp_path.iterdir()) == []

    raw = tmp_path / "caller-raw"
    out = tmp_path / "caller-out"
    commit = "a" * 40
    monkeypatch.setattr(sys, "argv", [
        "run_column_proposer.py",
        "--run-root", str(raw),
        "--out", str(out),
        "--analysis-commit", commit,
    ])
    runner.main()

    assert calls == [(raw, out, commit)]
    # The fake publisher makes any accidental runner-side default write
    # visible: the runner itself must create neither path.
    assert not raw.exists()
    assert not out.exists()
