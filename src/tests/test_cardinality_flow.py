"""Small synthetic exact-flow preflight; no public-case algorithm calls."""
from copy import deepcopy
from dataclasses import asdict, replace
from fractions import Fraction as Q
from itertools import product
import json
from types import SimpleNamespace

import pytest

from egglab import cardinality_flow as algorithm
from egglab import cardinality_flow_verify as verifier
from egglab import flat_energy_relaxation as baseline
from experiments import sistig_cardinality_flow as prospective
from experiments.native_recharge_qualification import cyclic_case


def brute(n, gate, edges):
    best = None
    for choices in product(*[[None] + [j for i, j in edges if i == row] for row in range(n)]):
        chosen = [(i, j) for i, j in enumerate(choices) if j is not None]
        if len(chosen) <= gate and len({j for _, j in chosen}) == len(chosen):
            cost = sum((edges[pair] for pair in chosen), Q(0))
            best = cost if best is None else min(best, cost)
    return best


def checked(n, gate, edges, baseline_cost=Q(0)):
    cert = algorithm.solve(n, gate, edges)
    got = verifier.verify(n, gate, edges, baseline_cost, cert)
    assert got["network_cost"] == brute(n, gate, edges)
    assert got["lower"] == baseline_cost + got["network_cost"]
    assert cert["potential"]["t"] == "0"
    return cert, got


def test_empty_sparse_signed_binding_and_nonbinding():
    checked(1, 0, {})
    checked(4, 2, {}, Q(7, 11))
    signed = {(0, 1): Q(-7, 3), (0, 2): Q(-5, 4),
              (1, 2): Q(-3, 2), (1, 3): Q(2, 7), (2, 3): Q(-11, 5)}
    for gate in range(5):
        _, got = checked(4, gate, signed, Q(13, 17))
        if gate in (0, 1, 2, 3):
            assert got["real_count"] <= gate
    assert checked(4, 2, signed)[1]["real_count"] == 2
    assert checked(4, 4, {(0, 1): Q(4)})[1]["real_count"] == 0


def test_exhaustive_three_service_dags_and_deterministic_ties():
    pairs = ((0, 1), (0, 2), (1, 2))
    for values in product((None, Q(-2, 3), Q(0), Q(5, 4)), repeat=3):
        edges = {pair: value for pair, value in zip(pairs, values) if value is not None}
        for gate in range(4):
            first, _ = checked(3, gate, edges)
            assert algorithm.solve(3, gate, edges) == first
    tie = {(0, 2): Q(-1), (1, 2): Q(-1)}
    assert checked(3, 1, tie)[1]["real_count"] == 1


@pytest.mark.parametrize("damage", [
    lambda c: c["arcs"].pop(),
    lambda c: c["arcs"][0].update(capacity=2),
    lambda c: c["arcs"][4].update(cost="-99"),
    lambda c: c["flow"].update({"source:0": 0}),
    lambda c: c["flow"].update({"gate": 0}),
    lambda c: c["potential"].update({"R0": "-100"}),
    lambda c: c["potential"].update({"t": "1"}),
    lambda c: c.update(network_cost="999"),
])
def test_certificate_corruption_rejected(damage):
    edges = {(0, 1): Q(-2), (0, 2): Q(-1), (1, 2): Q(-3)}
    cert, _ = checked(3, 1, edges)
    broken = deepcopy(cert)
    damage(broken)
    with pytest.raises(ValueError):
        verifier.verify(3, 1, edges, Q(0), broken)


def test_forbidden_edge_and_fraction_format_rejected():
    cert, _ = checked(3, 1, {(0, 1): Q(-1)})
    forged = deepcopy(cert)
    forged["flow"]["real:0:2"] = 1
    with pytest.raises(ValueError):
        verifier.verify(3, 1, {(0, 1): Q(-1)}, Q(0), forged)
    forged = deepcopy(cert)
    forged["potential"]["s"] = "0/1"
    with pytest.raises(ValueError, match="Noncanonical"):
        verifier.verify(3, 1, {(0, 1): Q(-1)}, Q(0), forged)


def test_independent_raw_row_reconstruction_parallel_mode_tie():
    case = cyclic_case()
    modes = tuple(replace(m, legs=tuple(replace(leg, energy_kwh=0) for leg in m.legs))
                  if m.kind in ("direct", "depot") else m for m in case.movements)
    case = replace(case, movements=modes)
    variant = {"trips": [{"native": asdict(t)} for t in case.trips],
               "movement_modes": [asdict(m) for m in case.movements],
               "service_count": len(case.trips),
               "charging_model": {"efficiency": case.efficiency},
               "cost_policy": {"vehicle_cost": case.vehicle_cost,
                               "deadhead_cost_per_min": case.deadhead_cost_per_min}}
    rebuilt = verifier.reconstruct_variant(variant, Q.from_float(.2))
    old = baseline.path_cover_problem(case, .2)
    assert rebuilt["baseline"] == old["baseline"]
    assert rebuilt["edges"] == {(i, j): old["matrix"][i][j] for i, j in old["connections"]}
    assert {pair: mode[1] for pair, mode in rebuilt["connections"].items()} == old["connections"]
    cert, got = checked(len(case.trips), 0, rebuilt["edges"], rebuilt["baseline"])
    assert got["path_count"] == len(case.trips)
    assert cert["network_cost"] == "0"


def test_malformed_identity_and_budget_inputs_rejected_without_public_run(tmp_path, monkeypatch):
    prospective.check_pins({"proof": "abc", "input": "def"}, {"proof": "abc", "input": "def"})
    with pytest.raises(ValueError, match="proof hash"):
        prospective.check_pins({"proof": "bad"}, {"proof": "abc"})
    with pytest.raises(ValueError, match="attempt path"):
        prospective.check_attempt(tmp_path)
    monkeypatch.setattr(prospective, "ROOT", tmp_path)
    gate = tmp_path / prospective.REVIEW_GATE
    gate.parent.mkdir(parents=True)
    gate.write_text("**FAIL** public-case algorithm not run")
    with pytest.raises(ValueError, match="review gate"):
        prospective.check_review_gate()
    gate.write_text("**PASS** public-case algorithm not run")
    prospective.check_review_gate()
    with pytest.raises(ValueError, match="Service coverage"):
        verifier.reconstruct_variant({"trips": [{"native": {"id": "A"}}],
                                      "service_count": 2}, Q(1))
    with pytest.raises(ValueError, match="Invalid flow dimensions"):
        algorithm.solve(3, -1, {})
    with pytest.raises(TimeoutError, match="budget"):
        algorithm.solve(3, 1, {(0, 1): Q(-1)}, max_relaxations=1)


@pytest.mark.parametrize("scenario,expected_child,expected_exit,expected_error", [
    ("changed_pin", 0, 1, "Pinned input or proof hash changed"),
    ("deleted_pin", 0, 1, "No such file or directory"),
    ("other_source_drift", 0, 1, "Source hashes changed after child exit"),
    ("child_failure", 7, 7, None),
    ("child_timeout", 124, 124, None),
])
def test_supervisor_seals_failure_evidence(tmp_path, monkeypatch, scenario,
                                           expected_child, expected_exit, expected_error):
    monkeypatch.setattr(prospective, "_check_frozen",
        lambda attempt: ({"source_hashes": {"proof": "original"}}, [], "frozenhash"))
    def fake_child(command, *, cwd, stdout, stderr, timeout, check):
        stdout.write(b"synthetic child output\n")
        prospective.write_new(tmp_path / "partial_result.json", {"started": True})
        if scenario == "child_timeout":
            raise prospective.subprocess.TimeoutExpired(command, timeout)
        return SimpleNamespace(returncode=7 if scenario == "child_failure" else 0)
    monkeypatch.setattr(prospective.subprocess, "run", fake_child)
    def source_state():
        if scenario == "changed_pin":
            raise ValueError("Pinned input or proof hash changed")
        if scenario == "deleted_pin":
            raise FileNotFoundError("No such file or directory: proof")
        if scenario == "other_source_drift":
            return {"proof": "replaced"}
        return {"proof": "original"}
    monkeypatch.setattr(prospective, "source_hashes", source_state)
    with pytest.raises(SystemExit) as exc:
        prospective.supervise(tmp_path)
    assert exc.value.code == expected_exit
    receipt = json.loads((tmp_path / "supervisor_receipt.json").read_text())
    manifest = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert receipt["child_exit_code"] == expected_child
    assert receipt["exit_code"] == expected_exit
    assert receipt["timed_out"] is (scenario == "child_timeout")
    assert receipt["source_hashes_unchanged"] is (expected_error is None)
    if expected_error is None:
        assert receipt["source_hash_exception"] is None
    else:
        assert expected_error in receipt["source_hash_exception"]
    assert {"supervisor_receipt.json", "partial_result.json", "stdout.txt"}.issubset(manifest["files"])
    assert manifest["files"]["supervisor_receipt.json"]["sha256"] == prospective.sha(
        tmp_path / "supervisor_receipt.json")
