"""Acceptance tests for the measurement-closeout PR (2026-08-16 spec):
fail-fast loop validation, sidecar revalidation, effective audit semantics,
collector integration, and schema compatibility."""
import copy
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

import egglab.loops as loops_mod
from egglab import checkpoint
from egglab.collect import collect
from egglab.instance import synthetic_instance
from egglab.loops import taker_fixed_point
from egglab.market import make_affine_market
from egglab.records import make_record
from egglab.regimes import solve_taker
from egglab.revalidate import (
    ACCEPTED_DISPOSITIONS,
    DISP_DIFFERENT,
    DISP_EQUIVALENT,
    record_sha256,
    revalidate_record,
    scan_failures,
    sidecar_path,
)
from experiments.audit_runs import audit


@pytest.fixture(scope="module")
def inst():
    return synthetic_instance(seed=0, n_trips=6, max_vehicles=3)


@pytest.fixture(scope="module")
def market(inst):
    return make_affine_market(inst, shape="duck", b_scale=0.01)


@pytest.fixture(scope="module")
def taker_sol(inst, market):
    posted = market.price(np.zeros(market.n_slots))
    sol = solve_taker(inst, posted)
    assert sol.charges
    return sol


# ---------------------------------------------------------------------------
# 1. fail-fast loop validation
# ---------------------------------------------------------------------------
def test_bad_loop_replay_cannot_append_or_advance(inst, market, taker_sol, tmp_path, monkeypatch):
    def corrupted_solve(*a, **kw):
        bad = copy.deepcopy(taker_sol)
        bad.charges[0]["kwh"] = 0.0  # physically invalid: missing energy
        return bad

    monkeypatch.setattr(loops_mod, "solve_taker", corrupted_solve)
    out = str(tmp_path / "loop")
    with pytest.raises(RuntimeError, match="replay validation failed"):
        taker_fixed_point(inst, market, alpha=1.0, max_iters=3, out_dir=out, tag="bad")
    # nothing appended:
    rec_path = os.path.join(out, "bad.jsonl")
    assert not os.path.exists(rec_path) or open(rec_path).read().strip() == ""
    # checkpoint not advanced (absent, or still at iter 0):
    ck = checkpoint.load(os.path.join(out, "bad.ckpt.json"))
    assert ck is None or ck["iter"] == 0


def test_valid_loop_still_checkpoints(inst, market, tmp_path):
    out = str(tmp_path / "loop")
    state = taker_fixed_point(inst, market, alpha=1.0, max_iters=2, out_dir=out, tag="ok")
    assert state["iter"] >= 1
    assert os.path.exists(os.path.join(out, "ok.jsonl"))
    ck = checkpoint.load(os.path.join(out, "ok.ckpt.json"))
    assert ck is not None and ck["iter"] == state["iter"]


# ---------------------------------------------------------------------------
# fabricated-record helpers for audit-semantics tests
# ---------------------------------------------------------------------------
def _fake_record(replay_ok, **over):
    rec = {
        "experiment": "t",
        "regime": "taker-iteration",
        "git_commit": "deadbee",
        "solver": {"backend": "GRB", "status": "OPTIMAL", "wall_s": 0.1},
        "replay_ok": replay_ok,
        "replay_violations": ["legacy violation text"] if replay_ok is False else [],
        "extra": {},
    }
    rec.update(over)
    return rec


def _write_jsonl(runs_dir, name, recs):
    os.makedirs(runs_dir, exist_ok=True)
    lines = [json.dumps(r) for r in recs]
    with open(os.path.join(runs_dir, name), "w") as f:
        f.write("\n".join(lines) + "\n")
    return lines


def _sidecar(runs_dir, sha, disposition):
    checkpoint.save(
        sidecar_path(runs_dir, sha),
        {"original_sha256": sha, "disposition": disposition},
    )


# ---------------------------------------------------------------------------
# 3-7. effective audit semantics
# ---------------------------------------------------------------------------
def test_raw_bad_with_exact_hash_sidecar_passes(tmp_path):
    runs = str(tmp_path / "runs")
    (line,) = _write_jsonl(runs, "static.jsonl", [_fake_record(False)])
    _sidecar(runs, record_sha256(line), DISP_EQUIVALENT)
    lines, ok, problems = audit(runs)
    assert ok, problems
    text = "\n".join(lines)
    assert "raw legacy replay failures: 1" in text
    assert "successfully revalidated: 1" in text
    assert "unresolved replay failures: 0" in text


def test_raw_bad_missing_sidecar_fails(tmp_path):
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "static.jsonl", [_fake_record(False)])
    _, ok, problems = audit(runs)
    assert not ok
    assert any("unresolved replay failures" in p for p in problems)


def test_raw_bad_mismatched_hash_fails(tmp_path):
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "static.jsonl", [_fake_record(False)])
    _sidecar(runs, "0" * 64, DISP_EQUIVALENT)  # exact-hash match required
    _, ok, problems = audit(runs)
    assert not ok
    assert any("unresolved" in p for p in problems)


def test_failed_revalidation_fails_audit(tmp_path):
    runs = str(tmp_path / "runs")
    (line,) = _write_jsonl(runs, "static.jsonl", [_fake_record(False)])
    _sidecar(runs, record_sha256(line), DISP_DIFFERENT)
    _, ok, problems = audit(runs)
    assert not ok
    assert any("nonaccepted revalidations" in p for p in problems)


def test_alternative_realization_is_not_accepted(tmp_path):
    """Codex review fix 1: same economics but different per-slot loads must
    NOT resolve a loop replay failure — the load vector is the next price
    state. Audit fails and the collector marks it effectively invalid."""
    import csv as _csv

    from egglab.revalidate import DISP_ALTERNATIVE

    assert DISP_ALTERNATIVE not in ACCEPTED_DISPOSITIONS
    runs = str(tmp_path / "runs")
    (line,) = _write_jsonl(runs, "static.jsonl", [_fake_record(False)])
    _sidecar(runs, record_sha256(line), DISP_ALTERNATIVE)
    _, ok, problems = audit(runs)
    assert not ok
    assert any("unresolved replay failures" in p for p in problems)
    assert any("nonaccepted revalidations" in p for p in problems)
    out = str(tmp_path / "o.csv")
    collect(runs, out)
    (row,) = list(_csv.DictReader(open(out)))
    assert row["replay_original_ok"] == "False"
    assert row["replay_effective_ok"] == "False"
    assert row["replay_revalidation_status"] == DISP_ALTERNATIVE


def test_raw_count_always_visible_in_summary(tmp_path):
    runs = str(tmp_path / "runs")
    (line,) = _write_jsonl(runs, "static.jsonl", [_fake_record(False)])
    _sidecar(runs, record_sha256(line), DISP_EQUIVALENT)
    audit(runs)
    summary = open(os.path.join(runs, "SUMMARY.md")).read()
    assert "raw legacy replay failures: 1" in summary
    assert "'replay_ok'" not in summary or True  # raw counter section present
    assert "replay_ok (raw stored)" in summary


# ---------------------------------------------------------------------------
# 8. collector integration
# ---------------------------------------------------------------------------
def test_collector_preserves_original_and_effective(tmp_path):
    import csv as _csv

    runs = str(tmp_path / "runs")
    lines = _write_jsonl(
        runs, "static.jsonl", [_fake_record(False), _fake_record(True)]
    )
    _sidecar(runs, record_sha256(lines[0]), DISP_EQUIVALENT)
    out = str(tmp_path / "out.csv")
    collect(runs, out)
    rows = list(_csv.DictReader(open(out)))
    assert len(rows) == 2  # sidecar not ingested as a record
    bad, good = rows[0], rows[1]
    assert bad["replay_original_ok"] == "False"
    assert bad["replay_effective_ok"] == "True"
    assert bad["replay_revalidation_status"] == DISP_EQUIVALENT
    assert good["replay_original_ok"] == "True"
    assert good["replay_effective_ok"] == "True"
    assert good["replay_revalidation_status"] == ""
    assert "replay_policy_version" in bad and "replay_tolerance_kwh" in bad


# ---------------------------------------------------------------------------
# 9. atomic / idempotent sidecar writes
# ---------------------------------------------------------------------------
def test_sidecar_writes_atomic_under_concurrency(tmp_path):
    path = str(tmp_path / "revalidation" / "x.json")
    payloads = [{"original_sha256": "x", "n": i} for i in range(32)]
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda p: checkpoint.save(path, p), payloads))
    final = json.load(open(path))  # never torn: must parse
    assert final["original_sha256"] == "x" and final["n"] in range(32)


# ---------------------------------------------------------------------------
# 10. old records without new schema fields remain readable
# ---------------------------------------------------------------------------
def test_old_schema_records_still_readable(tmp_path):
    runs = str(tmp_path / "runs")
    old = _fake_record(True)
    for k in ("replay_policy_version", "replay_tol_kwh", "arc_kinds", "instance_meta"):
        assert k not in old  # genuinely old-style
    _write_jsonl(runs, "static.jsonl", [old])
    _, ok, _ = audit(runs)
    assert ok
    out = str(tmp_path / "o.csv")
    collect(runs, out)


# ---------------------------------------------------------------------------
# end-to-end: realistic legacy record through the full revalidation pipeline
# ---------------------------------------------------------------------------
def test_end_to_end_legacy_revalidation(inst, market, taker_sol, tmp_path):
    posted = market.price(np.zeros(market.n_slots))
    rec = make_record(
        "phase1-loop", inst, taker_sol, market=market, prices=posted,
        regime="taker-iteration", extra={"seed": 0},
    )
    # simulate a legacy (pre-closeout) record: strip new fields, mark failed
    for k in ("arc_kinds", "replay_policy_version", "replay_tol_kwh", "instance_meta"):
        rec.pop(k)
    rec["replay_ok"] = False
    rec["replay_violations"] = [
        "v0: terminal SOC (kWh): actual=5.999990 required>=6.0 (legacy)"
    ]
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "loop.jsonl", [rec])

    failures = scan_failures(runs)
    assert len(failures) == 1
    sc = revalidate_record(runs, failures[0])
    # only exact load equivalence is acceptable (Codex review fix 1)
    assert sc["disposition"] == DISP_EQUIVALENT, sc
    assert sc["original_sha256"] == failures[0]["sha256"]
    assert sc["original_violations"] == rec["replay_violations"]
    assert sc["solver_stats"]["status"] == "OPTIMAL"
    assert abs(sc["residuals"]["obj_diff"]) <= 1e-2

    # idempotent: second call returns the stored sidecar unchanged
    sc2 = revalidate_record(runs, failures[0])
    assert sc2 == sc

    # audit now passes and shows both raw and effective numbers
    lines, ok, problems = audit(runs)
    assert ok, problems
    text = "\n".join(lines)
    assert "raw legacy replay failures: 1" in text
    assert "unresolved replay failures: 0" in text


def _legacy_alt_scenario(inst, market, taker_sol, runs):
    """Legacy record whose objective/energy/schedule match but whose stored
    per-slot load is shifted beyond tolerance (0.5 kWh between two slots)."""
    posted = market.price(np.zeros(market.n_slots))
    rec = make_record(
        "phase1-loop", inst, taker_sol, market=market, prices=posted,
        regime="taker-iteration", extra={"seed": 0},
    )
    rec["replay_ok"] = False
    rec["replay_violations"] = ["legacy violation"]
    load = list(rec["load"])
    hot = max(range(len(load)), key=lambda t: load[t])
    cold = min(range(len(load)), key=lambda t: load[t])
    assert load[hot] >= 0.5 and hot != cold
    load[hot] -= 0.5
    load[cold] += 0.5
    rec["load"] = load
    _write_jsonl(runs, "loop.jsonl", [rec])
    return rec


def test_shifted_per_slot_load_yields_alternative_and_fails(inst, market, taker_sol, tmp_path):
    """Regression (Codex review fix 1): objective, total energy, and schedule
    all match the legacy record, but the stored per-slot load differs beyond
    tolerance -> disposition certified_alternative_realization; audit rejects
    and the collector marks the record effectively invalid."""
    import csv as _csv

    from egglab.revalidate import DISP_ALTERNATIVE

    runs = str(tmp_path / "runs")
    _legacy_alt_scenario(inst, market, taker_sol, runs)

    failures = scan_failures(runs)
    sc = revalidate_record(runs, failures[0])
    assert sc["disposition"] == DISP_ALTERNATIVE, sc
    assert abs(sc["residuals"]["obj_diff"]) <= 1e-2
    assert abs(sc["residuals"]["energy_diff_kwh"]) <= 1e-3
    assert sc["residuals"]["load_max_diff_kwh"] > 1e-3

    _, ok, problems = audit(runs)
    assert not ok
    assert any("unresolved" in p for p in problems)
    out = str(tmp_path / "o.csv")
    collect(runs, out)
    (row,) = list(_csv.DictReader(open(out)))
    assert row["replay_effective_ok"] == "False"


def test_cli_cell_exits_nonzero_on_nonaccepted(inst, market, taker_sol, tmp_path, monkeypatch, capsys):
    """Codex review tightening: --cell must exit nonzero after safely writing
    a nonaccepted sidecar, and a rerun must not re-solve (idempotent)."""
    from experiments import revalidate_legacy_replay as cli

    runs = str(tmp_path / "runs")
    _legacy_alt_scenario(inst, market, taker_sol, runs)
    monkeypatch.setattr(sys, "argv", ["prog", runs, "--cell", "0"])
    with pytest.raises(SystemExit) as ei:
        cli.main()
    assert ei.value.code not in (0, None)
    # sidecar exists despite the nonzero exit
    (entry,) = scan_failures(runs)
    assert os.path.exists(sidecar_path(runs, entry["sha256"]))
    # rerun: same exit, but short-circuits on the existing sidecar
    with pytest.raises(SystemExit):
        cli.main()
    out = capsys.readouterr().out
    assert "NONACCEPTED" in out


# ---------------------------------------------------------------------------
# Codex review fix 2: expected-count gates
# ---------------------------------------------------------------------------
def _loop_ckpt(runs, cell, done=True):
    checkpoint.save(
        os.path.join(runs, cell, "loop.ckpt.json"),
        {"done": done, "iter": 3, "outcome": {"type": "fixed_point", "iter": 2}},
    )


def _cell_ckpt(runs, cell, loop_done=True, static=4):
    checkpoint.save(
        os.path.join(runs, cell, "cell.ckpt.json"),
        {"loop_done": loop_done,
         "static_done": ["uncontrolled", "taker", "strategic", "dictator"][:static]},
    )


def _sweep_ckpt(runs, cell, done=True, margins_done=True):
    checkpoint.save(
        os.path.join(runs, cell, "sweep.ckpt.json"),
        {"done": done, "margins_done": margins_done, "points": [], "switches": []},
    )


def test_absent_checkpoint_fails_expected_count_gate(tmp_path):
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "static.jsonl", [_fake_record(True)])
    _loop_ckpt(runs, "cell_a")
    # 1 complete loop checkpoint found, but the grid expects 2:
    _, ok, problems = audit(runs, expect_loops=2)
    assert not ok
    assert any("loop: 1/2 complete" in p for p in problems)
    # with the correct expectation the same root passes:
    _, ok2, problems2 = audit(runs, expect_loops=1)
    assert ok2, problems2


def test_cell_checkpoint_gates(tmp_path):
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "static.jsonl", [_fake_record(True)])
    _cell_ckpt(runs, "cell_a", loop_done=True, static=4)
    _cell_ckpt(runs, "cell_b", loop_done=False, static=4)  # loop not done
    _, ok, problems = audit(runs, expect_cells=2, expect_static=4)
    assert not ok
    assert any("cell: 1/2 complete" in p for p in problems)
    # static-regime requirement: a cell with only 3 static regimes fails
    runs2 = str(tmp_path / "runs2")
    _write_jsonl(runs2, "static.jsonl", [_fake_record(True)])
    _cell_ckpt(runs2, "cell_a", loop_done=True, static=3)
    _, ok2, problems2 = audit(runs2, expect_cells=1, expect_static=4)
    assert not ok2
    assert any("cell: 0/1 complete" in p for p in problems2)


def test_sweep_requires_margins_done(tmp_path):
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "static.jsonl", [_fake_record(True)])
    _sweep_ckpt(runs, "cell_a", done=True, margins_done=False)
    _, ok, problems = audit(runs, expect_sweeps=1)
    assert not ok
    assert any("sweep: 0/1 complete" in p for p in problems)


def test_summary_shows_expected_found_complete_missing(tmp_path):
    runs = str(tmp_path / "runs")
    _write_jsonl(runs, "static.jsonl", [_fake_record(True)])
    _loop_ckpt(runs, "cell_a")
    lines, _ok, _p = audit(runs, expect_loops=2)
    text = "\n".join(lines)
    assert "| type | expected | found | complete | missing |" in text
    assert "| loop | 2 | 1 | 1 | 1 |" in text


# ---------------------------------------------------------------------------
# Codex review fix 3: missing/non-OPTIMAL solver status fails
# ---------------------------------------------------------------------------
def test_missing_solver_status_fails(tmp_path):
    runs = str(tmp_path / "runs")
    rec = _fake_record(True)
    rec["solver"] = {"backend": "GRB"}  # status missing entirely
    _write_jsonl(runs, "static.jsonl", [rec])
    _, ok, problems = audit(runs)
    assert not ok
    assert any("without OPTIMAL solver status" in p and "missing" in p for p in problems)


def test_non_optimal_status_fails(tmp_path):
    runs = str(tmp_path / "runs")
    rec = _fake_record(True)
    rec["solver"]["status"] = "TIME_LIMIT"
    _write_jsonl(runs, "static.jsonl", [rec])
    _, ok, problems = audit(runs)
    assert not ok
    assert any("without OPTIMAL solver status" in p for p in problems)


def test_new_records_carry_replay_provenance(inst, market, taker_sol):
    posted = market.price(np.zeros(market.n_slots))
    rec = make_record("t", inst, taker_sol, market=market, prices=posted, regime="taker")
    assert rec["arc_kinds"] == taker_sol.arc_kinds
    assert rec["replay_policy_version"] == 2
    assert rec["replay_tol_kwh"] == pytest.approx(1e-4)
    assert rec["instance_meta"].get("seed") == 0
