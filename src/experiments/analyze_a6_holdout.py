#!/usr/bin/env python3
"""Deterministic closeout for the frozen A6 holdout.

The production population is exactly 64 matched instances (seeds 16--31,
``n_trips`` in {8, 12}, ``b`` in {0.01, 0.05}) and exactly two methods:
fresh A2 and the pilot-selected ``a6_a4``.  Invalid evidence is never
assigned a score: audit, replay, identity, provenance, or outcome-coherence
failures abort before the output directory is created.

Normative decision rule: doc/A6_SPARSE_STABILIZATION_SPEC.md Section 6.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from egglab import checkpoint
from egglab.a6 import (A6_K_MAX, A6_PRIORITY, A6_SCHEMA_VERSION,
                       A6_THETA_CERT_MULT, DEFAULT_CANDIDATE)
from egglab.b2a2 import (MAX_DUPLICATE_RETRIES, MAX_PRICING_ESCALATIONS,
                         PWL_TOL, RC_TOL, SCHEMA_VERSION, market_hash)
from egglab.b2a345 import stab_identity_params
from egglab.evsp import Solution, validate_solution
from egglab.market import make_affine_market
from experiments.analyze_b2_pilot import (
    AnalysisError,
    _price_path_metrics,
    default_instance_builder,
    scan_extras,
    sha256_file,
    tree_hashes,
    validate_cell,
    verify_analysis_code_commit,
    wall_partition,
    write_csv,
)
from experiments.audit_runs import audit


METHODS = ("a2", "a6_a4")
A6_METHOD = "a6_a4"
HOLDOUT_INSTANCES = tuple(
    (s, n, b)
    for s in range(16, 32)
    for n in (8, 12)
    for b in (0.01, 0.05)
)
PILOT_INSTANCES = tuple(
    (s, n, b)
    for s in (0, 11, 15)
    for n in (8, 12)
    for b in (0.01, 0.05)
)
EXPECTED_EXPERIMENT = "a6-holdout"
EPSILON = 1e-2
BUDGET = 240
BUDGET_EXHAUSTED_SCORE = BUDGET + 1
TOL_D = 1e-2
MIN_A6_CERTIFIED = 61
RATIO_BAR = 0.85
WIN_BAR = 38
REQUIRED_BACKEND = "GRB"
TV_XCHECK_TOL = 1e-3
EXPECTED_SELECTION_SHA256 = (
    "026ddc38e90f9dd2e9342a50cfb5550bc52731c5f1ee67d87d53008bd6b4b507"
)
EXPECTED_SELECTION_COMMIT = (
    "8f59a905bd5e12ac5784e57aebc66a03b47a00cb"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SELECTION = (
    REPO_ROOT / "result" / "a6_pilot" / "20260819T005514Z"
    / "SELECTION.json"
)
TRIGGERS = tuple(A6_PRIORITY) + (DEFAULT_CANDIDATE,)


def _git(args: list[str], *, text: bool = True):
    return subprocess.check_output(
        ["git", *args], cwd=REPO_ROOT, text=text,
        stderr=subprocess.STDOUT,
    )


def _is_sha256(value) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def assert_frozen_grid(instances) -> None:
    """The production CLI may analyze only the preregistered population."""
    got = tuple(instances)
    if len(got) != 64 or len(set(got)) != 64:
        raise AnalysisError(
            f"holdout grid must contain 64 unique instances; got {len(got)} "
            f"rows and {len(set(got))} unique rows")
    if set(got) != set(HOLDOUT_INSTANCES):
        missing = sorted(set(HOLDOUT_INSTANCES) - set(got))
        extra = sorted(set(got) - set(HOLDOUT_INSTANCES))
        raise AnalysisError(
            f"holdout grid tampering: missing={missing}, extra={extra}")


def _selection_tables(sel: dict) -> None:
    """Recompute the burned-pilot selection instead of trusting labels."""
    if sel.get("schema") != "a6-arm-selection-v1":
        raise AnalysisError("selection artifact has wrong schema")
    if sel.get("analysis_code_verified") is not True:
        raise AnalysisError("selection analysis_code_verified is not true")
    analysis_commit = sel.get("analysis_code_commit")
    if not (isinstance(analysis_commit, str)
            and len(analysis_commit) == 40
            and all(c in "0123456789abcdef" for c in analysis_commit)):
        raise AnalysisError("selection analysis_code_commit is not a full SHA")
    if sel.get("n_instances") != 12 or sel.get("win_threshold") != 9:
        raise AnalysisError("selection denominator/threshold was tampered")
    if sel.get("scoring") != {
            "certified": "calls-to-certificate",
            "budget_exhausted": BUDGET_EXHAUSTED_SCORE}:
        raise AnalysisError("selection scoring contract was tampered")

    expected_cells = {
        (m, s, n, b) for m in ("a6_a3", "a6_a4")
        for s, n, b in PILOT_INSTANCES
    }
    cell_map = {}
    for row in sel.get("per_cell") or []:
        try:
            key = (row["method"], int(row["seed"]),
                   int(row["n_trips"]), float(row["b"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisError(f"malformed selection per_cell row: {row}") from exc
        if key in cell_map:
            raise AnalysisError(f"duplicate selection per_cell row {key}")
        calls = row.get("oracle_calls")
        if (row.get("outcome") != "certified"
                or row.get("certified") is not True
                or not isinstance(calls, int)
                or not 2 <= calls <= BUDGET
                or row.get("score") != calls):
            raise AnalysisError(f"invalid pilot score evidence for {key}")
        cell_map[key] = calls
    if set(cell_map) != expected_cells:
        raise AnalysisError("selection per_cell grid is not the exact pilot")

    expected_matched = set(PILOT_INSTANCES)
    seen, wins = set(), 0
    for row in sel.get("matched") or []:
        try:
            key = (int(row["seed"]), int(row["n_trips"]), float(row["b"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisError(f"malformed selection matched row: {row}") from exc
        if key in seen:
            raise AnalysisError(f"duplicate selection matched row {key}")
        seen.add(key)
        s4 = cell_map[("a6_a4", *key)]
        s3 = cell_map[("a6_a3", *key)]
        a3_win = s3 < s4
        if (row.get("score_a6_a4") != s4
                or row.get("score_a6_a3") != s3
                or row.get("a6_a3_wins") is not a3_win):
            raise AnalysisError(f"selection matched scores disagree at {key}")
        wins += int(a3_win)
    if seen != expected_matched:
        raise AnalysisError("selection matched grid is not the exact pilot")
    expected_arm = "a6_a3" if wins >= 9 else "a6_a4"
    if sel.get("a6_a3_wins") != wins or sel.get("selected_arm") != expected_arm:
        raise AnalysisError("selection decision does not recompute")
    if expected_arm != A6_METHOD:
        raise AnalysisError(
            f"holdout analyzer is frozen to {A6_METHOD}, selection says "
            f"{expected_arm}")
    files = ((sel.get("inputs") or {}).get("files") or {})
    if not files or any(not _is_sha256(v) for v in files.values()):
        raise AnalysisError("selection pilot input hashes are missing/malformed")


def validate_selection(path: str | os.PathLike,
                       *, verify_git: bool = True) -> dict:
    path = Path(path).resolve()
    if verify_git and path != DEFAULT_SELECTION.resolve():
        raise AnalysisError(
            f"selection path {path} is not the frozen canonical path "
            f"{DEFAULT_SELECTION.resolve()}")
    if not path.is_file():
        raise AnalysisError(f"missing committed selection artifact: {path}")
    try:
        sel = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"cannot parse selection artifact: {path}") from exc
    _selection_tables(sel)
    digest = sha256_file(str(path))
    if digest != EXPECTED_SELECTION_SHA256:
        raise AnalysisError(
            f"selection SHA-256 {digest} != frozen artifact "
            f"{EXPECTED_SELECTION_SHA256}")

    selection_commit = None
    if verify_git:
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError as exc:
            raise AnalysisError("selection artifact is outside the repository") from exc
        try:
            _git(["ls-files", "--error-unmatch", "--", rel])
            committed = _git(["show", f"HEAD:{rel}"], text=False)
            dirty = _git(["status", "--porcelain", "--untracked-files=no",
                          "--", rel]).strip()
            selection_commit = _git(
                ["log", "-1", "--format=%H", "--", rel]).strip()
        except subprocess.CalledProcessError as exc:
            raise AnalysisError("selection artifact is not committed at HEAD") from exc
        if committed != path.read_bytes() or dirty:
            raise AnalysisError("working selection differs from committed artifact")
        if not selection_commit:
            raise AnalysisError("cannot resolve selection artifact commit")
        if selection_commit != EXPECTED_SELECTION_COMMIT:
            raise AnalysisError(
                f"selection commit {selection_commit} != frozen commit "
                f"{EXPECTED_SELECTION_COMMIT}")
        try:
            _git(["cat-file", "-e", f"{sel['analysis_code_commit']}^{{commit}}"])
            subprocess.check_call(
                ["git", "merge-base", "--is-ancestor",
                 sel["analysis_code_commit"], selection_commit],
                cwd=REPO_ROOT, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            subprocess.check_call(
                ["git", "merge-base", "--is-ancestor",
                 EXPECTED_SELECTION_COMMIT, "HEAD"], cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as exc:
            raise AnalysisError(
                "selection analysis commit is not an ancestor of its "
                "artifact commit") from exc

    return {
        "path": str(path),
        "sha256": digest,
        "selection_commit": selection_commit,
        "pilot_analysis_code_commit": sel["analysis_code_commit"],
        "selected_arm": sel["selected_arm"],
        "a6_a3_wins": sel["a6_a3_wins"],
        "n_instances": sel["n_instances"],
    }


def validate_preflight(path: str | os.PathLike, instances=HOLDOUT_INSTANCES) -> dict:
    """Independently validate the driver's deterministic preflight.

    This establishes that the exact frozen grid was reconstructed, every
    physical instance has a replayed constructive witness, and every market
    hash agrees with the canonical generators.  Cell checkpoint validation
    later repeats the instance/market hash checks method by method.
    """
    path = Path(path)
    if not path.is_file():
        raise AnalysisError(f"missing required holdout preflight: {path}")
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"cannot parse holdout preflight: {path}") from exc
    if doc.get("schema") != "a6-holdout-feasibility-v1":
        raise AnalysisError("holdout preflight has wrong schema")
    if doc.get("campaign") != EXPECTED_EXPERIMENT:
        raise AnalysisError("holdout preflight has wrong campaign")
    code_commit = doc.get("code_commit")
    if (not isinstance(code_commit, str) or len(code_commit) != 40
            or any(c not in "0123456789abcdef" for c in code_commit)):
        raise AnalysisError("holdout preflight has invalid code_commit")

    expected_seeds = sorted({int(s) for s, _n, _b in instances})
    expected_n = sorted({int(n) for _s, n, _b in instances})
    expected_b = sorted({float(b) for _s, _n, b in instances})
    physical_keys = {(int(s), int(n)) for s, n, _b in instances}
    market_keys = {(int(s), int(n), float(b)) for s, n, b in instances}
    expected_grid = {
        "methods": list(METHODS), "seeds": expected_seeds,
        "n_trips": expected_n, "b_scales": expected_b,
        "physical_instances": len(physical_keys),
        "market_instances": len(market_keys),
        "method_cells": 2 * len(market_keys),
    }
    if doc.get("grid") != expected_grid:
        raise AnalysisError(
            f"holdout preflight grid mismatch: {doc.get('grid')}")

    selection = doc.get("selection") or {}
    expected_selection = {
        "path": "result/a6_pilot/20260819T005514Z/SELECTION.json",
        "sha256": EXPECTED_SELECTION_SHA256,
        "artifact_commit": EXPECTED_SELECTION_COMMIT,
        "analysis_code_commit":
            "c663fcf5b7a142db595738c8b20bb83549f1ab99",
        "analysis_code_verified": True,
        "selected_arm": A6_METHOD,
        "schema": "a6-arm-selection-v1",
        "a6_a3_wins": 2,
        "n_instances": 12,
        "win_threshold": 9,
    }
    if selection != expected_selection:
        raise AnalysisError("holdout preflight selection gate was tampered")

    physical = doc.get("physical_instances") or []
    seen_physical = set()
    for row in physical:
        try:
            key = (int(row["seed"]), int(row["n_trips"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisError(f"malformed physical witness row: {row}") from exc
        if key in seen_physical:
            raise AnalysisError(f"duplicate physical preflight row {key}")
        seen_physical.add(key)
        inst = default_instance_builder(*key)
        if (row.get("instance_hash") != inst.hash()
                or row.get("max_vehicles") != inst.max_vehicles
                or row.get("replay_ok") is not True):
            raise AnalysisError(f"physical witness identity/replay failed at {key}")
        required = row.get("required_vehicles")
        pairs = row.get("pairs")
        if (not isinstance(required, int) or isinstance(required, bool)
                or not 1 <= required <= inst.max_vehicles
                or not isinstance(pairs, list)
                or len(pairs) != len(inst.trips) - required):
            raise AnalysisError(f"malformed constructive witness at {key}")
        trip_map = {t.id: t for t in inst.trips}
        used_ids = set()
        pair_specs = []
        for pair in pairs:
            if not isinstance(pair, dict):
                raise AnalysisError(f"malformed witness pair at {key}")
            ordered = pair.get("trip_ids")
            kind = pair.get("arc_kind")
            soc = pair.get("soc_trace_kwh")
            if (not isinstance(ordered, list) or len(ordered) != 2
                    or not all(isinstance(x, str) and x in trip_map
                               for x in ordered)
                    or ordered[0] == ordered[1]
                    or kind not in ("dir", "dep")
                    or not isinstance(soc, list) or not soc):
                raise AnalysisError(f"malformed witness chain at {key}")
            if used_ids & set(ordered):
                raise AnalysisError(f"constructive pairs are not disjoint at {key}")
            used_ids.update(ordered)
            first, second = (trip_map[x] for x in ordered)
            D = inst.depot
            trace = []
            value = inst.soc0_kwh - inst.dhk(D, first.start_loc)
            trace.append(("after_pull_out", value, inst.soc_min_kwh))
            value -= first.energy_kwh
            trace.append(("after_trip_1", value, inst.soc_min_kwh))
            if kind == "dir":
                ready = first.end_min + inst.dhm(
                    first.end_loc, second.start_loc)
                if ready > second.start_min:
                    raise AnalysisError(f"direct witness pair is late at {key}")
                value -= inst.dhk(first.end_loc, second.start_loc)
                trace.append(("before_trip_2_after_direct_deadhead", value,
                              inst.soc_min_kwh))
            else:
                arrive = first.end_min + inst.dhm(first.end_loc, D)
                depart = second.start_min - inst.dhm(D, second.start_loc)
                if arrive > depart:
                    raise AnalysisError(f"depot witness pair is late at {key}")
                value -= inst.dhk(first.end_loc, D)
                trace.append(("at_depot_after_trip_1", value,
                              inst.soc_min_kwh))
                trace.append(("after_zero_charge", value, inst.soc_min_kwh))
                if value > inst.battery_kwh:
                    raise AnalysisError(f"depot witness overfills battery at {key}")
                value -= inst.dhk(D, second.start_loc)
                trace.append(("before_trip_2_after_pull_out", value,
                              inst.soc_min_kwh))
            value -= second.energy_kwh
            trace.append(("after_trip_2", value, inst.soc_min_kwh))
            value -= inst.dhk(second.end_loc, D)
            trace.append(("after_pull_in", value, inst.soc_end_kwh))
            if len(soc) != len(trace):
                raise AnalysisError(f"SOC trace length mismatch at {key}")
            for observed, expected in zip(soc, trace):
                if (not isinstance(observed, dict)
                        or observed.get("stage") != expected[0]
                        or not isinstance(observed.get("soc_kwh"), (int, float))
                        or not math.isfinite(observed["soc_kwh"])
                        or abs(observed["soc_kwh"] - expected[1]) > 1e-12
                        or observed.get("required_min_kwh") != expected[2]
                        or observed["soc_kwh"] < expected[2]):
                    raise AnalysisError(f"SOC trace replay failed at {key}")
            pair_specs.append((ordered, kind))
        if required != len(inst.trips) - len(pair_specs):
            raise AnalysisError(f"required-vehicle witness mismatch at {key}")
        sequences = [list(ids) for ids, _kind in pair_specs]
        arc_kinds = [[kind] for _ids, kind in pair_specs]
        for trip in inst.trips:
            if trip.id not in used_ids:
                sequences.append([trip.id])
                arc_kinds.append([])
        if len(sequences) != required:
            raise AnalysisError(f"constructive witness fleet mismatch at {key}")
        sol = Solution(sequences=sequences, arc_kinds=arc_kinds,
                       charges=[], load=[0.0] * inst.n_slots,
                       fleet=required)
        violations = validate_solution(inst, sol, tol_kwh=0.0)
        if violations:
            raise AnalysisError(
                f"constructive witness physical replay failed at {key}: "
                f"{violations}")
    if seen_physical != physical_keys:
        raise AnalysisError("physical preflight population mismatch")

    markets = doc.get("markets") or []
    seen_markets = set()
    for row in markets:
        try:
            key = (int(row["seed"]), int(row["n_trips"]), float(row["b"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisError(f"malformed market preflight row: {row}") from exc
        if key in seen_markets:
            raise AnalysisError(f"duplicate market preflight row {key}")
        seen_markets.add(key)
        inst = default_instance_builder(key[0], key[1])
        market = make_affine_market(inst, shape="duck", b_scale=key[2])
        if (row.get("instance_hash") != inst.hash()
                or row.get("market_hash") != market_hash(market)):
            raise AnalysisError(f"preflight market hash mismatch at {key}")
    if seen_markets != market_keys:
        raise AnalysisError("market preflight population mismatch")
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(str(path)),
        "schema": doc["schema"],
        "code_commit": code_commit,
        "physical_instances": len(physical),
        "market_instances": len(markets),
        "method_cells": expected_grid["method_cells"],
        "selection": selection,
    }


def cell_dir(root: str, method: str, seed: int, n: int, b: float) -> str:
    return os.path.join(root, f"{method}_s{seed}_n{n}_b{b:g}")


def _load_jsonl(path: str) -> list:
    if not os.path.isfile(path):
        raise AnalysisError(f"missing materialized evidence log: {path}")
    rows = []
    try:
        with open(path) as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    raise AnalysisError(f"blank JSONL record at {path}:{i}")
                rows.append(json.loads(line))
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"invalid JSONL evidence in {path}") from exc
    return rows


def _validate_materialization(d: str, method: str, ck: dict) -> None:
    for suffix, field in (("oracle.jsonl", "oracle_events"),
                          ("iterations.jsonl", "iteration_events")):
        path = os.path.join(d, f"{method}.{suffix}")
        if _load_jsonl(path) != (ck.get(field) or []):
            raise AnalysisError(
                f"materialized {suffix} differs from committed checkpoint "
                f"evidence in {d}")
    dck = checkpoint.load(os.path.join(d, "dictator.ckpt.json"))
    drows = _load_jsonl(os.path.join(d, "dictator.jsonl"))
    if len(drows) != 1 or drows[0] != dck.get("record"):
        raise AnalysisError(
            f"dictator.jsonl differs from committed dictator evidence in {d}")


def _validate_identity(ck: dict, method: str, label: str) -> None:
    ident = ck.get("identity") or {}
    expected_schema = SCHEMA_VERSION if method == "a2" else A6_SCHEMA_VERSION
    if ident.get("schema_version") != expected_schema:
        raise AnalysisError(
            f"{label}: schema {ident.get('schema_version')!r} != "
            f"{expected_schema!r}")
    for field, expected in (("epsilon", EPSILON), ("budget", BUDGET),
                            ("pwl_tol", PWL_TOL), ("rc_tol", RC_TOL),
                            ("tol_d", TOL_D)):
        if ident.get(field) != expected:
            raise AnalysisError(
                f"{label}: identity {field}={ident.get(field)!r} != {expected}")
    solver_ident = ident.get("solver") or {}
    expected_solver = {
        "backend": REQUIRED_BACKEND,
        "max_mip_gap": 1e-6,
        "time_limit_s": None,
    }
    if solver_ident != expected_solver:
        raise AnalysisError(
            f"{label}: solver identity {solver_ident!r} != "
            f"{expected_solver!r}; comparable evidence required")
    if method == "a2":
        if "method" in ident:
            raise AnalysisError(f"{label}: A2 identity method mismatch")
    else:
        expected_scheduler = {
            "theta_cert_mult": A6_THETA_CERT_MULT,
            "theta_cert": A6_THETA_CERT_MULT * EPSILON,
            "k_max": A6_K_MAX,
            "priority": list(A6_PRIORITY) + [DEFAULT_CANDIDATE],
        }
        expected_recovery = {
            "max_pricing_escalations": MAX_PRICING_ESCALATIONS,
            "max_duplicate_retries": MAX_DUPLICATE_RETRIES,
            "gap_divisor": 100.0,
            "gap_floor": 1e-12,
        }
        if ident.get("method") != A6_METHOD:
            raise AnalysisError(f"{label}: A6 method identity mismatch")
        if ident.get("scheduler") != expected_scheduler:
            raise AnalysisError(f"{label}: scheduler identity was tampered")
        if ident.get("recovery") != expected_recovery:
            raise AnalysisError(f"{label}: recovery identity was tampered")
        if ident.get("stab") != stab_identity_params("a4"):
            raise AnalysisError(f"{label}: A4 mechanism identity was tampered")


def _validate_cell_provenance(
    d: str,
    *,
    cell_index: int,
    method: str,
    seed: int,
    n_trips: int,
    b: float,
    instance_hash: str,
    market_hash_value: str,
    preflight: dict,
) -> None:
    path = os.path.join(d, "CELL_PROVENANCE.json")
    if not os.path.isfile(path):
        raise AnalysisError(f"missing cell provenance: {path}")
    try:
        got = json.load(open(path))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"invalid cell provenance: {path}") from exc
    expected = {
        "schema": "a6-holdout-cell-provenance-v1",
        "campaign": EXPECTED_EXPERIMENT,
        "code_commit": preflight["code_commit"],
        "cell_index": cell_index,
        "cell": {"method": method, "seed": seed,
                 "n_trips": n_trips, "b": b},
        "instance_hash": instance_hash,
        "market_hash": market_hash_value,
        "selection": preflight["selection"],
        "preflight_path": "PREFLIGHT.json",
        "preflight_sha256": preflight["sha256"],
    }
    if got != expected:
        raise AnalysisError(
            f"cell provenance mismatch for {method} seed={seed} "
            f"n={n_trips} b={b}")


def validate_holdout_root(
    root: str,
    instances=HOLDOUT_INSTANCES,
    instance_builder=default_instance_builder,
    preflight: dict | None = None,
) -> dict:
    """Audit and resolve exactly one checkpoint for every frozen cell."""
    if not os.path.isdir(root):
        raise AnalysisError(f"missing holdout runs root: {root}")
    n = len(instances)
    _lines, ok, problems = audit(
        root, out_path=os.devnull, expect_cg=2 * n,
        expect_cg_method={m: n for m in METHODS})
    if not ok:
        raise AnalysisError(
            "holdout audit FAILED — campaign HALT-AND-DEBUG, nothing "
            f"scored: {problems}")

    if preflight is None:
        raise AnalysisError("validated preflight metadata is required")
    paths, seen = {}, set()
    ordered_cells = [
        (method, seed, n_trips, b)
        for method in METHODS for seed, n_trips, b in instances
    ]
    for cell_index, (method, seed, n_trips, b) in enumerate(ordered_cells):
        d = cell_dir(root, method, seed, n_trips, b)
        ck_path = validate_cell(
            d, method, seed, n_trips, b, instance_builder)
        if ck_path in seen:
            raise AnalysisError(f"duplicate/overlapping cell {ck_path}")
        seen.add(ck_path)
        ck = checkpoint.load(ck_path)
        label = f"{method} seed={seed} n={n_trips} b={b}"
        _validate_identity(ck, method, label)
        _validate_cell_provenance(
            d, cell_index=cell_index, method=method, seed=seed,
            n_trips=n_trips, b=b,
            instance_hash=ck["identity"]["instance_hash"],
            market_hash_value=ck["identity"]["market_hash"],
            preflight=preflight)
        _validate_materialization(d, method, ck)
        experiments = {e.get("experiment")
                       for e in ck.get("oracle_events") or []}
        if experiments != {EXPECTED_EXPERIMENT}:
            raise AnalysisError(
                f"{label}: experiment lineage {experiments} != "
                f"{{{EXPECTED_EXPERIMENT!r}}}")
        paths[(method, seed, n_trips, b)] = d
    scan_extras((root,), seen)
    if len(paths) != 2 * n:
        raise AnalysisError(
            f"{len(paths)} method-cells found; expected {2 * n}")
    return paths


def score_outcome(ck: dict, label: str) -> int:
    """Section 6 score.  Every malformed terminal state fails unscored."""
    oc = ck.get("outcome") or {}
    calls = ck.get("oracle_calls")
    if (not isinstance(calls, int) or isinstance(calls, bool)
            or calls < 2 or calls > BUDGET
            or oc.get("oracle_calls") != calls):
        raise AnalysisError(f"{label}: invalid oracle-call accounting")
    gap, eps = oc.get("gap"), (ck.get("identity") or {}).get("epsilon")
    if not isinstance(gap, (int, float)) or not math.isfinite(gap):
        raise AnalysisError(f"{label}: invalid final gap {gap!r}")
    kind = oc.get("type")
    if oc.get("certified") is True:
        if kind not in ("certified", "budget_exhausted") or gap > eps + 1e-12:
            raise AnalysisError(f"{label}: invalid certified terminal state")
        if kind == "budget_exhausted" and calls != BUDGET:
            raise AnalysisError(
                f"{label}: early budget-exhausted certified terminal state")
        return calls
    if kind == "budget_exhausted":
        if (oc.get("certified") is not False or calls != BUDGET
                or gap <= eps + 1e-12):
            raise AnalysisError(
                f"{label}: invalid budget-exhausted terminal state")
        return BUDGET_EXHAUSTED_SCORE
    raise AnalysisError(
        f"{label}: unscorable terminal state {oc.get('type')!r}")


def _finite_nonnegative(value, label: str) -> float:
    if (not isinstance(value, (int, float)) or not math.isfinite(value)
            or value < 0):
        raise AnalysisError(f"{label}: invalid value {value!r}")
    return float(value)


def extract_cell(d: str, method: str, seed: int, n: int, b: float) -> dict:
    ck = checkpoint.load(os.path.join(d, f"{method}.cg.ckpt.json"))
    dck = checkpoint.load(os.path.join(d, "dictator.ckpt.json"))
    label = f"{method} seed={seed} n={n} b={b}"
    score = score_outcome(ck, label)
    oc = ck["outcome"]
    events = ck["oracle_events"]

    wall_clean, wall_candidate, wall_total = wall_partition(
        ck, method, label)
    if wall_total <= 0:
        raise AnalysisError(f"{label}: nonpositive total solver wall time")
    regimes = Counter(e.get("regime") for e in events)
    clean_calls = regimes["cg-seed"] + regimes["cg-pricing"]
    candidate_calls = regimes["cg-stab-pricing"]
    if sum(regimes.values()) != clean_calls + candidate_calls:
        raise AnalysisError(f"{label}: unknown oracle regime in {dict(regimes)}")
    if clean_calls + candidate_calls != ck["oracle_calls"]:
        raise AnalysisError(f"{label}: oracle-call partition mismatch")
    if method == "a2" and candidate_calls:
        raise AnalysisError(f"{label}: A2 contains candidate calls")
    if (oc.get("oracle_calls_clean", clean_calls) != clean_calls
            or oc.get("oracle_calls_stab", candidate_calls) != candidate_calls):
        raise AnalysisError(f"{label}: outcome call partition mismatch")

    backends = {(e.get("solver") or {}).get("backend") for e in events}
    if backends != {REQUIRED_BACKEND}:
        raise AnalysisError(f"{label}: solver backends {backends}")
    mips = {e.get("mip_version") for e in events}
    commits = {e.get("git_commit") for e in events}
    if None in mips or "unknown" in mips or len(mips) != 1:
        raise AnalysisError(f"{label}: inconsistent mip versions {mips}")
    if None in commits or "unknown" in commits or len(commits) != 1:
        raise AnalysisError(f"{label}: inconsistent source commits {commits}")
    source_commit = next(iter(commits))

    drec = dck.get("record") or {}
    expected_cell = [method, seed, n, b]
    dextra = drec.get("extra") or {}
    if (drec.get("experiment") != EXPECTED_EXPERIMENT
            or drec.get("git_commit") != source_commit
            or drec.get("replay_ok") is not True
            or (drec.get("solver") or {}).get("backend") != REQUIRED_BACKEND
            or (drec.get("solver") or {}).get("status") != "OPTIMAL"
            or drec.get("mip_version") != next(iter(mips))
            or dextra.get("cell") != expected_cell
            or dextra.get("tag") != os.path.basename(d)):
        raise AnalysisError(f"{label}: dictator provenance mismatch")
    if (dck.get("identity") or {}).get("solver") != ck["identity"]["solver"]:
        raise AnalysisError(f"{label}: dictator/CG solver identity mismatch")

    iterations = [e for e in ck.get("iteration_events") or []
                  if not e.get("terminal")]
    candidate_iters = [e for e in iterations
                       if e.get("call_kind") == "candidate"
                       or e.get("phase") == "stabilized"]
    serious = sum(e.get("serious_step") is True for e in candidate_iters)
    null = sum(e.get("serious_step") is False for e in candidate_iters)
    if serious + null != candidate_calls:
        raise AnalysisError(f"{label}: serious/null accounting mismatch")
    stab = ck.get("stab") or {}
    if method == A6_METHOD and (
            stab.get("serious_steps") != serious
            or stab.get("null_steps") != null):
        raise AnalysisError(f"{label}: checkpoint serious/null mismatch")

    trigger_counts = Counter()
    if method == A6_METHOD:
        trigger_counts.update(e.get("trigger_selected") for e in iterations)
        if None in trigger_counts or set(trigger_counts) - set(TRIGGERS):
            raise AnalysisError(f"{label}: invalid trigger accounting")
        if dict(trigger_counts) != oc.get("trigger_selected_counts"):
            raise AnalysisError(f"{label}: outcome trigger counts mismatch")
        if sum(trigger_counts.values()) != ck["oracle_calls"] - 1:
            raise AnalysisError(f"{label}: trigger count excludes more than seed")

    uplift = oc.get("uplift_interval")
    if (not isinstance(uplift, list) or len(uplift) != 2
            or any(not isinstance(v, (int, float)) or not math.isfinite(v)
                   for v in uplift)
            or uplift[0] > uplift[1] + 1e-9):
        raise AnalysisError(f"{label}: invalid uplift interval {uplift!r}")
    expected_uplift = [
        (dck["z_d_ub"] - dck["tol_d"]) - oc["ub_ch"],
        dck["z_d_ub"] - ck["lb_best"],
    ]
    if any(abs(got - expected) > 1e-9
           for got, expected in zip(uplift, expected_uplift)):
        raise AnalysisError(f"{label}: uplift interval does not recompute")
    zd_margin = dck["z_d_ub"] + dck["tol_d"] - ck["lb_best"]
    if zd_margin < -1e-6:
        raise AnalysisError(
            f"{label}: LB_CH contradicts dictator interval; HALT-AND-DEBUG")
    dictator_wall = _finite_nonnegative(
        (dck.get("adaptive") or {}).get("adaptive_total_wall_s"),
        f"{label} dictator wall")

    tv, linf, points = _price_path_metrics(
        events, ("cg-seed", "cg-pricing", "cg-stab-pricing"))
    if oc.get("broadcast_tv") is None:
        raise AnalysisError(f"{label}: missing broadcast path summary")
    else:
        stored_tv = oc.get("broadcast_tv")
        stored_linf = oc.get("broadcast_linf_max")
        stored_points = oc.get("broadcast_points")
        if (not isinstance(stored_tv, (int, float))
                or not math.isfinite(stored_tv) or stored_tv < 0
                or not isinstance(stored_linf, (int, float))
                or not math.isfinite(stored_linf) or stored_linf < 0
                or not isinstance(stored_points, int)
                or stored_points != points
                or abs(stored_tv - tv) > TV_XCHECK_TOL * max(1.0, tv)
                or abs(stored_linf - linf) > TV_XCHECK_TOL * max(1.0, linf)):
            raise AnalysisError(f"{label}: broadcast path summary mismatch")
        tv, linf, points = float(stored_tv), float(stored_linf), stored_points

    row = {
        "method": method, "seed": seed, "n_trips": n, "b": b,
        "outcome": oc["type"], "certified": bool(oc["certified"]),
        "score": score, "oracle_calls": ck["oracle_calls"],
        "oracle_calls_clean": clean_calls,
        "oracle_calls_candidate": candidate_calls,
        "final_gap": float(oc["gap"]), "lb_best": ck["lb_best"],
        "ub_ch": oc["ub_ch"], "n_columns": len(ck["columns"]),
        "serious_steps": serious, "null_steps": null,
        "wall_clean_s": wall_clean, "wall_candidate_s": wall_candidate,
        "total_solver_wall_s": wall_total,
        "dictator_wall_s": dictator_wall,
        "uplift_lo": uplift[0], "uplift_hi": uplift[1],
        "uplift_width": uplift[1] - uplift[0],
        "zd_minus_lb": zd_margin,
        "broadcast_tv": tv, "broadcast_linf_max": linf,
        "broadcast_points": points,
        "epsilon": ck["identity"]["epsilon"],
        "budget": ck["identity"]["budget"],
        "tol_d": ck["identity"]["tol_d"],
        "backend": next(iter(backends)),
        "mip_version": next(iter(mips)),
        "source_commit": source_commit,
        "solver_identity": json.dumps(
            ck["identity"]["solver"], sort_keys=True, separators=(",", ":")),
    }
    for trigger in TRIGGERS:
        row[f"trigger_{trigger}"] = int(trigger_counts[trigger])
    return row


def check_population_contract(cells: pd.DataFrame, n_instances: int) -> None:
    if len(cells) != 2 * n_instances:
        raise AnalysisError(
            f"population has {len(cells)} method-cells; expected "
            f"{2 * n_instances}")
    for method in METHODS:
        if int((cells.method == method).sum()) != n_instances:
            raise AnalysisError(f"population denominator error for {method}")
    for col, expected in (("epsilon", {EPSILON}), ("budget", {BUDGET}),
                          ("tol_d", {TOL_D}),
                          ("backend", {REQUIRED_BACKEND})):
        got = set(cells[col].tolist())
        if got != expected:
            raise AnalysisError(f"scientific contract {col}: {got} != {expected}")
    if len(set(cells["solver_identity"])) != 1:
        raise AnalysisError("A2/A6 solver identities are not identical")
    if len(set(cells["mip_version"])) != 1:
        raise AnalysisError("population mixes python-mip versions")
    if len(set(cells["source_commit"])) != 1:
        raise AnalysisError("population mixes experiment code commits")


def verify_run_provenance(cells: pd.DataFrame, selection_commit: str,
                          analysis_commit: str) -> str:
    source = str(cells["source_commit"].iloc[0])
    try:
        resolved = _git(["rev-parse", f"{source}^{{commit}}"] ).strip()
        for older, newer, label in (
            (selection_commit, resolved, "selection before holdout"),
            (resolved, analysis_commit, "holdout before analysis"),
        ):
            rc = subprocess.call(
                ["git", "merge-base", "--is-ancestor", older, newer],
                cwd=REPO_ROOT, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            if rc:
                raise AnalysisError(f"provenance ancestry failed: {label}")
    except subprocess.CalledProcessError as exc:
        raise AnalysisError(
            f"cannot resolve holdout source commit {source!r}") from exc
    return resolved


def matched_comparison(cells: pd.DataFrame) -> pd.DataFrame:
    base = cells[cells.method == "a2"].set_index(["seed", "n_trips", "b"])
    rows = []
    for _, a6 in cells[cells.method == A6_METHOD].iterrows():
        key = (a6.seed, a6.n_trips, a6.b)
        if key not in base.index:
            raise AnalysisError(f"missing A2 match for {key}")
        a2 = base.loc[key]
        diff = int(a6.score - a2.score)
        clean_diff = int(a6.oracle_calls_clean - a2.oracle_calls_clean)
        rows.append({
            "seed": int(key[0]), "n_trips": int(key[1]), "b": key[2],
            "a2_score": int(a2.score), "a6_score": int(a6.score),
            "score_diff": diff, "score_ratio": a6.score / a2.score,
            "score_result": "win" if diff < 0 else "tie" if diff == 0 else "loss",
            "a2_oracle_calls": int(a2.oracle_calls),
            "a6_oracle_calls": int(a6.oracle_calls),
            "a2_clean_calls": int(a2.oracle_calls_clean),
            "a6_clean_calls": int(a6.oracle_calls_clean),
            "a6_candidate_calls": int(a6.oracle_calls_candidate),
            "clean_calls_diff": clean_diff,
            "clean_result": ("win" if clean_diff < 0 else
                             "tie" if clean_diff == 0 else "loss"),
            "a2_certified": bool(a2.certified),
            "a6_certified": bool(a6.certified),
            "a2_final_gap": a2.final_gap, "a6_final_gap": a6.final_gap,
            "a2_solver_wall_s": a2.total_solver_wall_s,
            "a6_solver_wall_s": a6.total_solver_wall_s,
            "wall_diff_s": a6.total_solver_wall_s - a2.total_solver_wall_s,
            "wall_ratio": a6.total_solver_wall_s / a2.total_solver_wall_s,
            "a2_uplift_lo": a2.uplift_lo, "a2_uplift_hi": a2.uplift_hi,
            "a6_uplift_lo": a6.uplift_lo, "a6_uplift_hi": a6.uplift_hi,
        })
    out = pd.DataFrame(rows)
    if len(out) != len(base):
        raise AnalysisError("matched join has the wrong denominator")
    return out


def _quartiles(values) -> tuple[float, float]:
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0], vals[0]
    qs = statistics.quantiles(vals, n=4, method="inclusive")
    return qs[0], qs[2]


def method_summary(cells: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    scopes = [("overall", cells)] + [
        (f"b={b:g}", cells[cells.b == b]) for b in sorted(cells.b.unique())]
    for scope, sub in scopes:
        for method in METHODS:
            s = sub[sub.method == method]
            scores, walls = s.score.tolist(), s.total_solver_wall_s.tolist()
            sq1, sq3 = _quartiles(scores)
            wq1, wq3 = _quartiles(walls)
            mm = matched if scope == "overall" else matched[
                matched.b == float(scope.split("=")[1])]
            row = {
                "scope": scope, "method": method, "cells": len(s),
                "certified": int(s.certified.sum()),
                "cert_rate": float(s.certified.mean()),
                "score_median": statistics.median(scores),
                "score_q1": sq1, "score_q3": sq3, "score_max": max(scores),
                "raw_calls_median": statistics.median(s.oracle_calls.tolist()),
                "clean_calls_median": statistics.median(
                    s.oracle_calls_clean.tolist()),
                "candidate_calls_median": statistics.median(
                    s.oracle_calls_candidate.tolist()),
                "wall_clean_median_s": statistics.median(s.wall_clean_s.tolist()),
                "wall_candidate_median_s": statistics.median(
                    s.wall_candidate_s.tolist()),
                "wall_median_s": statistics.median(walls),
                "wall_q1_s": wq1, "wall_q3_s": wq3,
                "gap_median": statistics.median(s.final_gap.tolist()),
                "gap_max": max(s.final_gap.tolist()),
                "serious_steps_median": statistics.median(
                    s.serious_steps.tolist()),
                "null_steps_median": statistics.median(s.null_steps.tolist()),
                "uplift_lo_median": statistics.median(s.uplift_lo.tolist()),
                "uplift_hi_median": statistics.median(s.uplift_hi.tolist()),
                "uplift_width_median": statistics.median(
                    s.uplift_width.tolist()),
            }
            if method == A6_METHOD:
                row.update(
                    score_wins=int((mm.score_result == "win").sum()),
                    score_ties=int((mm.score_result == "tie").sum()),
                    score_losses=int((mm.score_result == "loss").sum()),
                    clean_wins=int((mm.clean_result == "win").sum()),
                    clean_ties=int((mm.clean_result == "tie").sum()),
                    clean_losses=int((mm.clean_result == "loss").sum()),
                )
            else:
                row.update(score_wins=0, score_ties=0, score_losses=0,
                           clean_wins=0, clean_ties=0, clean_losses=0)
            rows.append(row)
    return pd.DataFrame(rows)


def exact_sign_test_p(wins: int, losses: int) -> float:
    """Exact two-sided sign test on non-ties (supporting, never gating)."""
    n = wins + losses
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(wins, losses) + 1)) / 2**n
    return min(1.0, 2.0 * tail)


def classify_decision(*, a6_certified: int, a2_certified: int,
                      ratio: float, wins: int, n_instances: int = 64) -> dict:
    """The exhaustive prespecified partition, including exact boundaries."""
    if (not isinstance(ratio, (int, float)) or not math.isfinite(ratio)
            or ratio < 0 or not 0 <= wins <= n_instances
            or not 0 <= a6_certified <= n_instances
            or not 0 <= a2_certified <= n_instances):
        raise AnalysisError("invalid decision inputs")
    acc1 = a6_certified >= MIN_A6_CERTIFIED
    acc3 = a6_certified / n_instances >= a2_certified / n_instances
    if not (acc1 and acc3):
        verdict = "FINAL NEGATIVE — certification shortfall"
        cell = "certification-shortfall"
    elif ratio <= RATIO_BAR and wins >= WIN_BAR:
        verdict = "ADOPT"
        cell = "adopt"
    elif ratio >= 1.0 or wins <= 32:
        verdict = "FINAL NEGATIVE — clear kill"
        cell = "clear-kill"
    elif RATIO_BAR < ratio < 1.0 and 33 <= wins <= 37:
        verdict = "FINAL NEGATIVE — gray"
        cell = "gray"
    else:
        verdict = "FINAL NEGATIVE — discordant"
        cell = "discordant"
    return {"acc_a6_1": acc1, "acc_a6_3": acc3,
            "decision_cell": cell, "verdict": verdict}


def decision_table(cells: pd.DataFrame, matched: pd.DataFrame) -> pd.DataFrame:
    a2 = cells[cells.method == "a2"]
    a6 = cells[cells.method == A6_METHOD]
    med_a2 = statistics.median(a2.score.tolist())
    med_a6 = statistics.median(a6.score.tolist())
    ratio = med_a6 / med_a2
    wins = int((matched.score_result == "win").sum())
    ties = int((matched.score_result == "tie").sum())
    losses = int((matched.score_result == "loss").sum())
    dec = classify_decision(
        a6_certified=int(a6.certified.sum()),
        a2_certified=int(a2.certified.sum()), ratio=ratio, wins=wins,
        n_instances=len(matched))
    p = exact_sign_test_p(wins, losses)
    return pd.DataFrame([{
        **dec, "n_instances": len(matched),
        "a2_certified": int(a2.certified.sum()),
        "a6_certified": int(a6.certified.sum()),
        "a2_cert_rate": float(a2.certified.mean()),
        "a6_cert_rate": float(a6.certified.mean()),
        "a2_score_median": med_a2, "a6_score_median": med_a6,
        "median_score_ratio_a6_over_a2": ratio,
        "score_wins": wins, "score_ties": ties, "score_losses": losses,
        "ratio_bar": RATIO_BAR, "win_bar": WIN_BAR,
        "min_a6_certified": MIN_A6_CERTIFIED,
        "sign_test_non_ties": wins + losses,
        "sign_test_p_two_sided": p,
        "sign_test_supports_a6_alpha_005": bool(p <= 0.05 and wins > losses),
        "sign_test_is_gating": False,
    }])


def trigger_summary(cells: pd.DataFrame) -> pd.DataFrame:
    a6 = cells[cells.method == A6_METHOD]
    rows = []
    for trigger in TRIGGERS:
        col = f"trigger_{trigger}"
        rows.append({
            "trigger_selected": trigger,
            "selected_total": int(a6[col].sum()),
            "cells_with_trigger": int((a6[col] > 0).sum()),
            "per_cell_median": statistics.median(a6[col].tolist()),
            "per_cell_max": int(a6[col].max()),
        })
    return pd.DataFrame(rows)


COLORS = {"a2": "#264653", A6_METHOD: "#e9c46a"}


def make_figures(cells: pd.DataFrame, matched: pd.DataFrame,
                 triggers: pd.DataFrame, out_dir: str) -> list[str]:
    made = []

    fig, ax = plt.subplots(figsize=(6.4, 4.5))
    for method in METHODS:
        vals = sorted(cells[cells.method == method].score.tolist())
        y = [(i + 1) / len(vals) for i in range(len(vals))]
        ax.step(vals, y, where="post", label=method.upper(),
                color=COLORS[method], linewidth=2)
    ax.set_xlabel("prespecified score (budget exhaustion = 241)")
    ax.set_ylabel("empirical CDF")
    ax.set_title("A6 holdout: score distributions")
    ax.legend()
    fig.tight_layout()
    fn = "F1_score_ecdf.png"
    fig.savefig(os.path.join(out_dir, fn), dpi=150, metadata={})
    plt.close(fig)
    made.append(fn)

    ordered = matched.sort_values(["b", "n_trips", "seed"], kind="mergesort")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["#2a9d8f" if x < 0 else "#888888" if x == 0 else "#e76f51"
              for x in ordered.score_diff]
    ax.scatter(range(len(ordered)), ordered.score_diff, c=colors, s=28)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("matched holdout instance (fixed order)")
    ax.set_ylabel("A6 score - A2 score")
    ax.set_title("Matched score differences (negative favors A6)")
    fig.tight_layout()
    fn = "F2_matched_score_differences.png"
    fig.savefig(os.path.join(out_dir, fn), dpi=150, metadata={})
    plt.close(fig)
    made.append(fn)

    fig, ax = plt.subplots(figsize=(5.8, 4.5))
    data = [cells[cells.method == m].total_solver_wall_s.tolist()
            for m in METHODS]
    bp = ax.boxplot(data, tick_labels=[m.upper() for m in METHODS],
                    patch_artist=True, medianprops={"color": "black"})
    for patch, method in zip(bp["boxes"], METHODS):
        patch.set_facecolor(COLORS[method])
        patch.set_alpha(0.75)
    ax.set_yscale("log")
    ax.set_ylabel("solver-reported wall time (s, log scale)")
    ax.set_title("Corrected solver-wall partition: totals")
    fig.tight_layout()
    fn = "F3_solver_wall.png"
    fig.savefig(os.path.join(out_dir, fn), dpi=150, metadata={})
    plt.close(fig)
    made.append(fn)

    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.bar(triggers.trigger_selected, triggers.selected_total,
           color="#457b9d")
    ax.set_ylabel("selected calls across 64 A6 cells")
    ax.set_title("A6 scheduler trigger selections")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fn = "F4_trigger_counts.png"
    fig.savefig(os.path.join(out_dir, fn), dpi=150, metadata={})
    plt.close(fig)
    made.append(fn)
    return made


def write_summary(path: str, cells: pd.DataFrame, summary: pd.DataFrame,
                  decision: pd.DataFrame, stamp: str, code_commit: str) -> None:
    d = decision.iloc[0]
    ov = summary[summary.scope == "overall"].set_index("method")
    consequence = (
        "ADOPT continues the stabilization line under the frozen research "
        "plan."
        if d.verdict == "ADOPT" else
        "This FINAL NEGATIVE ends further stabilization variants unless new "
        "theory motivates a new, separately prespecified program."
    )
    lines = [
        f"# A6 frozen-holdout closeout ({stamp})", "",
        f"Analysis code commit: `{code_commit}`. Exact population: 64 "
        "matched instances, fresh A2 versus pilot-selected A6-A4; all 128 "
        "method-cells passed identity, replay, solver, audit, and lineage "
        "validation before scoring.", "", "## Primary endpoint", "",
        f"- A2 median score: {d.a2_score_median:g}; A6 median score: "
        f"{d.a6_score_median:g}; ratio A6/A2: "
        f"{d.median_score_ratio_a6_over_a2:.6g} (ADOPT bar <= {RATIO_BAR}).",
        f"- Matched score W/T/L for A6: {int(d.score_wins)}/"
        f"{int(d.score_ties)}/{int(d.score_losses)} (ADOPT win bar >= "
        f"{WIN_BAR}).",
        f"- Certification: A6 {int(d.a6_certified)}/64; A2 "
        f"{int(d.a2_certified)}/64. Gates acc-A6-1={bool(d.acc_a6_1)}; "
        f"acc-A6-3={bool(d.acc_a6_3)}.", "",
        f"## Computed verdict: **{d.verdict}**", "",
        f"Exhaustive decision cell: `{d.decision_cell}`. The exact two-sided "
        f"sign test gives p={d.sign_test_p_two_sided:.6g} on "
        f"{int(d.sign_test_non_ties)} non-ties; it is supporting only and "
        f"does not enter the verdict. {consequence}", "",
        "## Overall method summary", "",
        "| method | cert | median score | median raw | median clean | median "
        "candidate | median wall s | median final gap | uplift interval "
        "medians |", "|---|---|---|---|---|---|---|---|---|",
    ]
    for method in METHODS:
        r = ov.loc[method]
        lines.append(
            f"| {method.upper()} | {int(r.certified)}/{int(r.cells)} | "
            f"{r.score_median:g} | {r.raw_calls_median:g} | "
            f"{r.clean_calls_median:g} | {r.candidate_calls_median:g} | "
            f"{r.wall_median_s:.3f} | {r.gap_median:.6g} | "
            f"[{r.uplift_lo_median:.6g}, {r.uplift_hi_median:.6g}] |")
    lines += [
        "", "All raw calls, score assignments, clean/candidate partitions, "
        "serious/null steps, trigger selections, corrected wall partitions, "
        "final gaps, and uplift intervals are in the CSV tables. "
        "MANIFEST.json hashes every input and generated artifact.",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _fsync_tree(path: str) -> None:
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()
        for filename in sorted(filenames):
            with open(os.path.join(dirpath, filename), "rb") as f:
                os.fsync(f.fileno())
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def analyze(
    root: str,
    out_base: str,
    stamp: str,
    analysis_code_commit: str,
    *,
    selection_path: str | os.PathLike = DEFAULT_SELECTION,
    preflight_path: str | os.PathLike | None = None,
    instances=HOLDOUT_INSTANCES,
    instance_builder=default_instance_builder,
    verify_code_commit: bool = True,
    verify_selection_git: bool = True,
    verify_experiment_commit: bool = True,
    require_frozen_grid: bool = True,
    preflight_validator=validate_preflight,
) -> str:
    if require_frozen_grid:
        assert_frozen_grid(instances)
    code_verified = False
    if verify_code_commit:
        analysis_code_commit = verify_analysis_code_commit(
            analysis_code_commit)
        code_verified = True
    selection = validate_selection(
        selection_path, verify_git=verify_selection_git)
    canonical_preflight = Path(root, "PREFLIGHT.json").resolve()
    preflight_path = str(Path(preflight_path or canonical_preflight).resolve())
    if Path(preflight_path) != canonical_preflight:
        raise AnalysisError(
            f"preflight must be the campaign-root artifact "
            f"{canonical_preflight}")
    preflight = preflight_validator(preflight_path, instances=instances)
    paths = validate_holdout_root(
        root, instances, instance_builder, preflight=preflight)

    rows = [extract_cell(paths[(method, s, n, b)], method, s, n, b)
            for s, n, b in instances for method in METHODS]
    cells = pd.DataFrame(rows)
    check_population_contract(cells, len(instances))
    experiment_commit = str(cells.source_commit.iloc[0])
    if not preflight["code_commit"].startswith(experiment_commit):
        raise AnalysisError(
            "PREFLIGHT code_commit does not match checkpoint provenance")
    if verify_experiment_commit:
        if selection["selection_commit"] is None:
            raise AnalysisError("cannot verify run ancestry without selection commit")
        experiment_commit = verify_run_provenance(
            cells, selection["selection_commit"], analysis_code_commit)
        if experiment_commit != preflight["code_commit"]:
            raise AnalysisError(
                "resolved experiment commit does not equal PREFLIGHT code_commit")

    matched = matched_comparison(cells)
    summary = method_summary(cells, matched)
    decision = decision_table(cells, matched)
    triggers = trigger_summary(cells)

    out_dir = os.path.join(out_base, stamp)
    if os.path.exists(out_dir):
        raise AnalysisError(f"refusing existing output path: {out_dir}")
    os.makedirs(out_base, exist_ok=True)
    staging = tempfile.mkdtemp(prefix=f".{stamp}.staging-", dir=out_base)
    try:
        write_csv(cells, os.path.join(staging, "cells.csv"),
                  ["method", "b", "n_trips", "seed"])
        write_csv(matched, os.path.join(staging, "matched_comparison.csv"),
                  ["b", "n_trips", "seed"])
        write_csv(summary, os.path.join(staging, "method_summary.csv"),
                  ["scope", "method"])
        write_csv(decision, os.path.join(staging, "decision_status.csv"),
                  ["decision_cell"])
        write_csv(triggers, os.path.join(staging, "trigger_summary.csv"),
                  ["trigger_selected"])
        figures = make_figures(cells, matched, triggers, staging)
        write_summary(os.path.join(staging, "SUMMARY.md"), cells, summary,
                      decision, stamp, analysis_code_commit)

        outputs = sorted([
            "cells.csv", "matched_comparison.csv", "method_summary.csv",
            "decision_status.csv", "trigger_summary.csv", "SUMMARY.md",
            *figures,
        ])
        manifest = {
            "schema": "a6-holdout-closeout-v1",
            "stamp": stamp,
            "analysis_code_commit": analysis_code_commit,
            "analysis_code_verified": code_verified,
            "selection": selection,
            "preflight": preflight,
            "population": {
                "instances": [list(t) for t in instances],
                "methods": list(METHODS),
                "method_cells": len(cells),
            },
            "scoring": {
                "certified": "calls-to-certificate",
                "budget_exhausted": BUDGET_EXHAUSTED_SCORE,
            },
            "decision_rule": {
                "a6_min_certified": MIN_A6_CERTIFIED,
                "a6_rate_ge_a2": True,
                "adopt_ratio_max": RATIO_BAR,
                "adopt_wins_min": WIN_BAR,
                "sign_test_gating": False,
            },
            "solver": {
                "backends": sorted(cells.backend.unique().tolist()),
                "mip_versions": sorted(cells.mip_version.unique().tolist()),
                "solver_identities": sorted(
                    cells.solver_identity.unique().tolist()),
            },
            "experiment_commit": experiment_commit,
            "inputs": {
                "holdout": {"path": root, "files": tree_hashes(root)},
                "selection": {"path": str(Path(selection_path).resolve()),
                              "sha256": selection["sha256"]},
                "preflight": {"path": str(Path(preflight_path).resolve()),
                              "sha256": sha256_file(preflight_path)},
            },
            "outputs": {fn: sha256_file(os.path.join(staging, fn))
                        for fn in outputs},
        }
        with open(os.path.join(staging, "MANIFEST.json"), "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write("\n")
        _fsync_tree(staging)
        os.replace(staging, out_dir)
        staging = ""
        parent_fd = os.open(out_base, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if staging and os.path.isdir(staging):
            shutil.rmtree(staging)
    return out_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="runs/a6_holdout")
    ap.add_argument("--selection", default=str(DEFAULT_SELECTION))
    ap.add_argument("--preflight", default=None,
                    help="default: <root>/PREFLIGHT.json")
    ap.add_argument("--out", default=os.path.join("..", "result", "a6_holdout"))
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--analysis-code-commit", required=True)
    args = ap.parse_args()
    stamp = args.stamp or datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = analyze(
        args.root, args.out, stamp, args.analysis_code_commit,
        selection_path=args.selection, preflight_path=args.preflight)
    decision = pd.read_csv(os.path.join(out, "decision_status.csv")).iloc[0]
    print(f"[done] wrote {out} — {decision['verdict']}")


if __name__ == "__main__":
    main()
