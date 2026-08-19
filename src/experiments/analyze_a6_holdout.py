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
import hashlib
import json
import math
import os
import re
import shutil
import stat
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
import numpy as np
import pandas as pd

from egglab import checkpoint
from egglab.a6 import (A6_K_MAX, A6_PRIORITY, A6_SCHEMA_VERSION,
                       A6_THETA_CERT_MULT, DEFAULT_CANDIDATE)
from egglab.b2a2 import (MAX_DUPLICATE_RETRIES, MAX_PRICING_ESCALATIONS,
                         PWL_TOL, RC_TOL, SCHEMA_VERSION, TOL_MONO, column_key,
                         market_hash)
from egglab.b2a345 import (a4_alpha_update, a4_direction_signal,
                           initial_stab_state, serious_step,
                           stab_identity_params, theta_cert)
from egglab.evsp import (LOAD_RECONSTRUCTION_POLICY_VERSION,
                         REPLAY_POLICY_VERSION, REPLAY_TOL_KWH, Solution,
                         validate_solution)
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
EXPECTED_GRID_LIST_SHA256 = (
    "4ca11f7fe113c849c7a65921ddc78badce0a7fdb7b01b35db6a7fb8d72716bcd"
)
TRANSFER_RECEIPT_SCHEMA = "a6-holdout-transfer-receipt-v1"
TRANSFER_RECEIPT_FILENAME = "a6_holdout.TRANSFER_RECEIPT.json"
CLOSEOUT_CLAIM_SCHEMA = "a6-holdout-closeout-claim-v1"
IMPORT_LOCK_FILENAME = ".a6_holdout.import-lock"
ANALYSIS_CLAIM_SCHEMA = "a6-holdout-analysis-claim-v1"
ANALYSIS_CLAIM_FILENAME = "a6_holdout.ANALYSIS_CLAIM.json"
CLOSEOUT_SCHEMA = "a6-holdout-closeout-v2"
MASTER_FW_TOL = 1e-6
EVIDENCE_LIMITATIONS = (
    "Launch-era clean-master lambdas, aggregate load, and link duals were "
    "not serialized. Certificate safety is independently bounded by "
    "resolving the exact convex restricted master from retained columns; "
    "the historical producer primal/dual path is not reconstructed.",
    "Launch-era A6-A4 candidate records did not serialize the "
    "contemporaneous clean pi_out vector. Candidate mechanism diagnostics "
    "replay only conditional on the recorded candidate price.",
    "Launch-era solver records did not serialize SLURM_ARRAY_JOB_ID. Cell "
    "task indices and within-cell job consistency are checked, but the "
    "record bytes cannot prove the parent-array join retroactively.",
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


def _parse_launch_record(path: Path, expected_keys: set[str], label: str) -> dict:
    """Parse one launcher key-value record without accepting ambiguity."""
    if path.is_symlink() or not path.is_file():
        raise AnalysisError(f"missing or non-regular {label}: {path}")
    try:
        text = path.read_text()
    except OSError as exc:
        raise AnalysisError(f"cannot read {label}: {path}") from exc
    if not text or not text.endswith("\n"):
        raise AnalysisError(f"{label} must be nonempty and newline-terminated")
    values = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line or "=" not in line:
            raise AnalysisError(
                f"{label} has malformed line {line_no}: {line!r}")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not value:
            raise AnalysisError(
                f"{label} has malformed key/value on line {line_no}")
        if key in values:
            raise AnalysisError(f"{label} has duplicate key {key!r}")
        values[key] = value
    if set(values) != expected_keys:
        raise AnalysisError(
            f"{label} keys differ: got {sorted(values)}, "
            f"expected {sorted(expected_keys)}")
    return values


def _parse_launch_utc(value: str, label: str) -> datetime.datetime:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise AnalysisError(f"{label} is not a launcher UTC timestamp: {value!r}")
    try:
        return datetime.datetime.strptime(
            value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc)
    except ValueError as exc:
        raise AnalysisError(f"{label} is not a valid UTC timestamp") from exc


def _launch_grid_text(instances) -> str:
    seeds = sorted({int(s) for s, _n, _b in instances})
    n_trips = sorted({int(n) for _s, n, _b in instances})
    b_scales = sorted({float(b) for _s, _n, b in instances})
    if seeds == list(range(seeds[0], seeds[-1] + 1)):
        seed_text = f"{seeds[0]}-{seeds[-1]}"
    else:
        seed_text = "{" + ",".join(str(v) for v in seeds) + "}"
    n_text = ",".join(str(v) for v in n_trips)
    b_text = ",".join(f"{v:g}" for v in b_scales)
    return (
        f"seeds {seed_text} x n{{{n_text}}} x b{{{b_text}}}; "
        f"{len(instances)} matched instances")


def canonical_grid_list_bytes(selection: dict, instances) -> bytes:
    """Independently reproduce the launcher's exact ``--list`` bytes.

    This intentionally owns a small canonical representation rather than
    invoking the experiment driver during closeout.  The selection and cell
    key orders mirror the frozen launch protocol and are therefore part of
    the provenance contract.
    """
    selection_keys = (
        "path", "sha256", "artifact_commit", "analysis_code_commit",
        "analysis_code_verified", "schema", "selected_arm", "a6_a3_wins",
        "n_instances", "win_threshold",
    )
    if not isinstance(selection, dict) or set(selection) != set(selection_keys):
        raise AnalysisError("cannot reconstruct grid list from selection")
    ordered_selection = {key: selection[key] for key in selection_keys}
    lines = [f"selection: {ordered_selection}"]
    index = 0
    for method in METHODS:
        for seed, n_trips, b in instances:
            cell = {
                "method": method,
                "seed": int(seed),
                "n_trips": int(n_trips),
                "b": float(b),
                "epsilon": EPSILON,
                "budget": BUDGET,
            }
            lines.append(f"{index} {cell}")
            index += 1
    lines.append(f"total: {index} cells")
    return ("\n".join(lines) + "\n").encode("utf-8")


def canonical_grid_list_sha256(selection: dict, instances) -> str:
    return hashlib.sha256(
        canonical_grid_list_bytes(selection, instances)).hexdigest()


def _canonical_json_bytes(document: dict) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _input_tree_snapshot(root: str | os.PathLike) -> dict:
    """Hash a regular-file-only raw tree without following links."""
    raw_root = Path(root)
    if raw_root.is_symlink():
        raise AnalysisError(f"holdout root must not be a symlink: {raw_root}")
    root_path = raw_root.resolve()
    if not root_path.is_dir():
        raise AnalysisError(f"missing holdout runs root: {root_path}")
    directories = []
    files = []
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        dirnames.sort()
        filenames.sort()
        parent = Path(dirpath)
        for dirname in dirnames:
            child = parent / dirname
            info = child.lstat()
            if not stat.S_ISDIR(info.st_mode):
                raise AnalysisError(
                    f"holdout tree has non-directory entry: {child}")
            directories.append(child.relative_to(root_path).as_posix())
        for filename in filenames:
            path = parent / filename
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise AnalysisError(
                    f"holdout tree has unsafe file entry: {path}")
            digest = hashlib.sha256()
            try:
                with path.open("rb") as handle:
                    opened = os.fstat(handle.fileno())
                    if (opened.st_dev, opened.st_ino, opened.st_size,
                            opened.st_mtime_ns, opened.st_ctime_ns) != (
                            before.st_dev, before.st_ino, before.st_size,
                            before.st_mtime_ns, before.st_ctime_ns):
                        raise AnalysisError(
                            f"holdout file changed before hashing: {path}")
                    for chunk in iter(lambda: handle.read(1 << 20), b""):
                        digest.update(chunk)
                    after_read = os.fstat(handle.fileno())
                after_close = path.lstat()
            except OSError as exc:
                raise AnalysisError(
                    f"cannot hash holdout input file: {path}") from exc
            signature = lambda value: (
                value.st_dev, value.st_ino, value.st_size,
                value.st_mtime_ns, value.st_ctime_ns)
            if (signature(after_read) != signature(before)
                    or signature(after_close) != signature(before)):
                raise AnalysisError(
                    f"holdout file changed while hashing: {path}")
            files.append({
                "path": path.relative_to(root_path).as_posix(),
                "sha256": digest.hexdigest(),
                "size": before.st_size,
            })
    directories.sort()
    files.sort(key=lambda row: row["path"])
    inventory = {"directories": directories, "files": files}
    return {
        **inventory,
        "file_count": len(files),
        "directory_count": len(directories),
        "total_bytes": sum(row["size"] for row in files),
        "canonical_tree_sha256": hashlib.sha256(json.dumps(
            inventory, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def _full_hex(value, length: int) -> bool:
    return (isinstance(value, str) and len(value) == length
            and all(char in "0123456789abcdef" for char in value))


def validate_transfer_receipt(
    root: str | os.PathLike,
    *,
    preflight: dict,
    selection: dict,
    launch: dict,
    analysis_code_commit: str,
    repository: str | os.PathLike = REPO_ROOT,
    verify_git: bool = True,
) -> dict:
    """Bind imported bytes to their guarded bundle and exact analysis code."""
    root_path = Path(root).resolve()
    repository_path = Path(repository).resolve()
    runs_parent = root_path.parent
    import_lock = runs_parent / IMPORT_LOCK_FILENAME
    if import_lock.exists() or import_lock.is_symlink():
        raise AnalysisError(
            f"active or interrupted import lock blocks analysis: {import_lock}")
    receipt_path = runs_parent / TRANSFER_RECEIPT_FILENAME
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise AnalysisError(
            f"missing regular transfer receipt: {receipt_path}")
    info = receipt_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise AnalysisError(f"unsafe transfer receipt: {receipt_path}")
    try:
        raw = receipt_path.read_bytes()
        document = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError("cannot parse transfer receipt") from exc
    if raw != _canonical_json_bytes(document):
        raise AnalysisError("transfer receipt is not canonical JSON")
    if set(document) != {
            "schema", "campaign", "imported_utc", "destination", "bundle",
            "archive", "source", "provenance", "closeout_claim"}:
        raise AnalysisError("transfer receipt top-level keys differ")
    if (document.get("schema") != TRANSFER_RECEIPT_SCHEMA
            or document.get("campaign") != EXPECTED_EXPERIMENT):
        raise AnalysisError("transfer receipt schema/campaign is invalid")
    try:
        datetime.datetime.strptime(
            document.get("imported_utc", ""), "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as exc:
        raise AnalysisError("transfer receipt imported_utc is invalid") from exc

    expected_destination = {
        "repository": str(repository_path),
        "target": str(root_path),
        "repository_relative_target": "src/runs/a6_holdout",
    }
    if document.get("destination") != expected_destination:
        raise AnalysisError("transfer receipt destination is invalid")
    bundle = document.get("bundle") or {}
    if (set(bundle) != {
            "path", "manifest_sha256", "audit_summary_sha256"}
            or not isinstance(bundle.get("path"), str)
            or not Path(bundle["path"]).is_absolute()
            or not _full_hex(bundle.get("manifest_sha256"), 64)
            or not _full_hex(bundle.get("audit_summary_sha256"), 64)):
        raise AnalysisError("transfer receipt bundle identity is invalid")
    archive = document.get("archive") or {}
    if (set(archive) != {"name", "sha256", "size"}
            or not isinstance(archive.get("name"), str)
            or Path(archive["name"]).name != archive["name"]
            or not archive["name"].endswith(".tar.gz")
            or not _full_hex(archive.get("sha256"), 64)
            or not isinstance(archive.get("size"), int)
            or isinstance(archive.get("size"), bool)
            or archive["size"] <= 0):
        raise AnalysisError("transfer receipt archive identity is invalid")

    snapshot = _input_tree_snapshot(root_path)
    expected_source = {
        key: snapshot[key]
        for key in (
            "canonical_tree_sha256", "file_count", "directory_count",
            "total_bytes")
    }
    if document.get("source") != expected_source:
        raise AnalysisError(
            "transfer receipt does not match installed holdout tree")
    expected_provenance = {
        "experiment_code_commit": preflight.get("code_commit"),
        "packaging_code_commit": analysis_code_commit,
        "selection_sha256": selection.get("sha256"),
        "selection_artifact_commit": EXPECTED_SELECTION_COMMIT,
        "preflight_sha256": preflight.get("sha256"),
        "launch_job_id": launch.get("job_id"),
    }
    if document.get("provenance") != expected_provenance:
        raise AnalysisError(
            "transfer receipt provenance differs from validated campaign")

    closeout = document.get("closeout_claim") or {}
    if (set(closeout) != {"sha256", "document"}
            or not _full_hex(closeout.get("sha256"), 64)
            or not isinstance(closeout.get("document"), dict)):
        raise AnalysisError("transfer receipt closeout claim is invalid")
    closeout_document = closeout["document"]
    closeout_bytes = _canonical_json_bytes(closeout_document)
    if hashlib.sha256(closeout_bytes).hexdigest() != closeout["sha256"]:
        raise AnalysisError("transfer receipt closeout claim hash differs")
    if set(closeout_document) != {
            "schema", "campaign", "status", "claimed_utc",
            "packaging_code_commit", "experiment_code_commit",
            "selection_sha256", "preflight_sha256", "launch_job_id",
            "grid_list_sha256", "source"}:
        raise AnalysisError("transfer receipt closeout claim keys differ")
    expected_closeout = {
        "schema": CLOSEOUT_CLAIM_SCHEMA,
        "campaign": EXPECTED_EXPERIMENT,
        "status": "claimed-before-outcome-validation",
        "packaging_code_commit": analysis_code_commit,
        "experiment_code_commit": preflight.get("code_commit"),
        "selection_sha256": selection.get("sha256"),
        "preflight_sha256": preflight.get("sha256"),
        "launch_job_id": launch.get("job_id"),
        "grid_list_sha256": launch.get("grid_list_sha256"),
        "source": expected_source,
    }
    for field, expected in expected_closeout.items():
        if closeout_document.get(field) != expected:
            raise AnalysisError(
                f"transfer receipt closeout claim {field} differs")
    try:
        claimed_at = datetime.datetime.strptime(
            closeout_document.get("claimed_utc", ""),
            "%Y-%m-%dT%H:%M:%SZ")
        imported_at = datetime.datetime.strptime(
            document.get("imported_utc", ""), "%Y-%m-%dT%H:%M:%SZ")
        submitted_at = datetime.datetime.strptime(
            launch.get("manifest_submitted_utc", ""),
            "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as exc:
        raise AnalysisError(
            "transfer receipt closeout claim chronology is invalid") from exc
    if not submitted_at <= claimed_at <= imported_at:
        raise AnalysisError(
            "transfer receipt closeout claim chronology is invalid")

    if verify_git:
        experiment_commit = expected_provenance["experiment_code_commit"]
        packaging_commit = expected_provenance["packaging_code_commit"]
        try:
            head = subprocess.check_output(
                ["git", "rev-parse", "--verify", "HEAD^{commit}"],
                cwd=repository_path, text=True,
                stderr=subprocess.STDOUT).strip()
            for commit in (
                    EXPECTED_SELECTION_COMMIT, experiment_commit,
                    packaging_commit):
                subprocess.check_call(
                    ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                    cwd=repository_path, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
            subprocess.check_call(
                ["git", "merge-base", "--is-ancestor",
                 EXPECTED_SELECTION_COMMIT, experiment_commit],
                cwd=repository_path, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            subprocess.check_call(
                ["git", "merge-base", "--is-ancestor",
                 experiment_commit, packaging_commit],
                cwd=repository_path, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, OSError, TypeError) as exc:
            raise AnalysisError(
                "transfer receipt Git ancestry is invalid") from exc
        if head != packaging_commit:
            raise AnalysisError(
                "analysis HEAD must exactly equal receipt packaging commit")
    return {
        "path": str(receipt_path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "document": document,
        "tree_snapshot": snapshot,
    }


def claim_single_analysis(
    root: str | os.PathLike,
    *,
    out_dir: str | os.PathLike,
    stamp: str,
    analysis_code_commit: str,
    transfer: dict,
) -> dict:
    """Persist the one-look claim before any checkpoint is interpreted."""
    root_path = Path(root).resolve()
    claim_path = root_path.parent / ANALYSIS_CLAIM_FILENAME
    document = {
        "schema": ANALYSIS_CLAIM_SCHEMA,
        "campaign": EXPECTED_EXPERIMENT,
        "claimed_utc": datetime.datetime.now(
            datetime.timezone.utc).replace(microsecond=0).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
        "analysis_code_commit": analysis_code_commit,
        "transfer_receipt_sha256": transfer["sha256"],
        "canonical_tree_sha256":
            transfer["tree_snapshot"]["canonical_tree_sha256"],
        "stamp": stamp,
        "output": str(Path(out_dir).resolve()),
    }
    payload = _canonical_json_bytes(document)
    try:
        descriptor = os.open(
            claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise AnalysisError(
            f"A6 holdout analysis was already claimed: {claim_path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        parent = os.open(root_path.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except BaseException:
        # A complete claim is intentionally never auto-removed.  A partial
        # write also remains a fail-closed recovery marker for manual review.
        raise
    return {
        "path": str(claim_path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "document": document,
    }


def _assert_sidecar_unchanged(record: dict, label: str) -> None:
    path = Path(record["path"])
    if path.is_symlink() or not path.is_file():
        raise AnalysisError(f"{label} disappeared or became unsafe")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise AnalysisError(f"{label} became unsafe")
    raw = path.read_bytes()
    expected = _canonical_json_bytes(record["document"])
    if (raw != expected
            or hashlib.sha256(raw).hexdigest() != record["sha256"]):
        raise AnalysisError(f"{label} changed during analysis")


def _assert_analysis_inputs_unchanged(
    root_path: Path,
    transfer: dict,
    analysis_claim: dict,
) -> dict:
    """Revalidate the exact imported evidence and both one-look sidecars."""
    snapshot = _input_tree_snapshot(root_path)
    if snapshot != transfer["tree_snapshot"]:
        raise AnalysisError(
            "raw holdout tree changed during analysis; claim remains for "
            "incident review")
    _assert_sidecar_unchanged(transfer, "transfer receipt")
    _assert_sidecar_unchanged(analysis_claim, "analysis claim")
    return snapshot


def validate_launch_provenance(
    root: str | os.PathLike,
    preflight: dict,
    selection: dict,
    instances=HOLDOUT_INSTANCES,
) -> dict:
    """Bind scoring to the one-shot launcher claim, intent, and submission.

    The scientific checkpoints are validated separately.  This gate proves
    that the transferred campaign root also carries one unambiguous launch
    history whose commit, hashes, grid, and job identity agree with the
    independently validated preflight and canonical arm selection.
    """
    root_path = Path(root).resolve()
    manifests = sorted(root_path.glob("MANIFEST-*.txt"))
    if len(manifests) != 1:
        raise AnalysisError(
            f"launch provenance requires exactly one MANIFEST-*.txt; "
            f"found {len(manifests)}")
    manifest_path = manifests[0]
    match = re.fullmatch(
        r"MANIFEST-(\d{8}T\d{6}Z)\.txt", manifest_path.name)
    if manifest_path.is_symlink() or match is None:
        raise AnalysisError("launch manifest path/name is invalid")

    lock = root_path / "SUBMISSION_LOCK"
    if lock.is_symlink() or not lock.is_dir():
        raise AnalysisError(f"missing regular submission lock directory: {lock}")
    expected_lock_files = {"CLAIM.txt", "INTENT.txt", "SUBMITTED.txt"}
    observed_lock_files = {p.name for p in lock.iterdir()}
    if observed_lock_files != expected_lock_files:
        raise AnalysisError(
            "submission lock must contain exactly CLAIM.txt, INTENT.txt, "
            f"and SUBMITTED.txt; found {sorted(observed_lock_files)}")

    claim = _parse_launch_record(
        lock / "CLAIM.txt",
        {"status", "git_commit", "selection_sha256", "claimed_utc"},
        "launch CLAIM")
    intent = _parse_launch_record(
        lock / "INTENT.txt",
        {"status", "git_commit", "grid_list_sha256", "selection_sha256",
         "preflight_sha256", "prepared_utc"},
        "launch INTENT")
    submitted = _parse_launch_record(
        lock / "SUBMITTED.txt",
        {"status", "job_id", "submitted_utc"},
        "launch SUBMITTED")
    manifest = _parse_launch_record(
        manifest_path,
        {"campaign", "cells", "grid", "grid_list_sha256", "array",
         "epsilon", "audit", "selection_path", "selection_sha256",
         "selection_gate_commit", "preflight_path", "preflight_sha256",
         "submission_sentinel", "feasibility", "job_id", "git_commit",
         "submitted_utc"},
        "launch manifest")

    if claim["status"] != "claimed-before-preflight":
        raise AnalysisError("launch CLAIM status is not claimed-before-preflight")
    if intent["status"] != "prepared":
        raise AnalysisError("launch INTENT status is not prepared")
    if submitted["status"] != "submitted":
        raise AnalysisError("launch SUBMITTED status is not submitted")

    code_commit = preflight.get("code_commit")
    selection_sha = selection.get("sha256")
    preflight_sha = preflight.get("sha256")
    if (not isinstance(code_commit, str) or len(code_commit) != 40
            or any(c not in "0123456789abcdef" for c in code_commit)):
        raise AnalysisError("validated preflight lacks a full code commit")
    for label, value in {
            "canonical selection": selection_sha,
            "validated preflight": preflight_sha,
            "grid list": intent["grid_list_sha256"],
    }.items():
        if not _is_sha256(value):
            raise AnalysisError(f"{label} SHA-256 is missing or malformed")

    actual_preflight = root_path / "PREFLIGHT.json"
    if (Path(preflight.get("path", "")).resolve() != actual_preflight
            or sha256_file(str(actual_preflight)) != preflight_sha):
        raise AnalysisError("launch preflight path/hash does not match root")
    if (selection_sha != EXPECTED_SELECTION_SHA256
            or (preflight.get("selection") or {}).get("sha256") != selection_sha):
        raise AnalysisError("launch selection does not match canonical preflight")
    if {claim["git_commit"], intent["git_commit"],
            manifest["git_commit"]} != {code_commit}:
        raise AnalysisError("launch commit chain disagrees with preflight")
    if {claim["selection_sha256"], intent["selection_sha256"],
            manifest["selection_sha256"]} != {selection_sha}:
        raise AnalysisError("launch selection SHA chain is inconsistent")
    if {intent["preflight_sha256"], manifest["preflight_sha256"]} != {
            preflight_sha}:
        raise AnalysisError("launch preflight SHA chain is inconsistent")
    recomputed_grid_sha = canonical_grid_list_sha256(
        preflight.get("selection") or {}, instances)
    if tuple(instances) == HOLDOUT_INSTANCES:
        if recomputed_grid_sha != EXPECTED_GRID_LIST_SHA256:
            raise AnalysisError(
                "independent frozen grid serialization changed: "
                f"{recomputed_grid_sha}")
    if (intent["grid_list_sha256"] != manifest["grid_list_sha256"]
            or not _is_sha256(manifest["grid_list_sha256"])
            or intent["grid_list_sha256"] != recomputed_grid_sha):
        raise AnalysisError("launch grid-list SHA chain is inconsistent")
    if not re.fullmatch(r"[1-9]\d*", submitted["job_id"]):
        raise AnalysisError("submitted Slurm job id is not numeric")
    if submitted["job_id"] != manifest["job_id"]:
        raise AnalysisError("launch job id differs between lock and manifest")

    n_instances = len(instances)
    method_cells = 2 * n_instances
    physical_instances = len({(s, n) for s, n, _b in instances})
    expected_manifest = {
        "campaign": (
            "a6-holdout (spec doc/A6_SPARSE_STABILIZATION_SPEC.md "
            "Section 6)"),
        "cells": (
            f"{method_cells} (verified: {n_instances} a2 + "
            f"{n_instances} a6_a4; a6_a3 forbidden)"),
        "grid": _launch_grid_text(instances),
        "array": f"0-{method_cells - 1}%12",
        "epsilon": (
            "1e-2; budget=240 exact oracle calls; budget exhaustion is "
            "valid and scores 241"),
        "audit": (
            f"--expect-cg {method_cells} --expect-cg-method a2={n_instances} "
            f"--expect-cg-method a6_a4={n_instances} "
            "(NO certification-count gate)"),
        "selection_path": (
            "result/a6_pilot/20260819T005514Z/SELECTION.json"),
        "selection_gate_commit": EXPECTED_SELECTION_COMMIT
            + " (verified ancestor)",
        "preflight_path": "runs/a6_holdout/PREFLIGHT.json",
        "submission_sentinel": (
            "runs/a6_holdout/SUBMISSION_LOCK "
            "(persistent; deletion requires audit/review)"),
        "feasibility": (
            f"{physical_instances}/{physical_instances} physical instances "
            "have exact zero-charge covers; "
            f"{n_instances} market hashes recorded before sbatch"),
    }
    bad = {
        key: (manifest.get(key), expected)
        for key, expected in expected_manifest.items()
        if manifest.get(key) != expected
    }
    if bad:
        raise AnalysisError(f"launch manifest contract mismatch: {bad}")
    if "certified" in manifest["audit"].lower():
        raise AnalysisError("launch audit incorrectly includes certification gate")

    claimed_at = _parse_launch_utc(claim["claimed_utc"], "claimed_utc")
    prepared_at = _parse_launch_utc(intent["prepared_utc"], "prepared_utc")
    submitted_at = _parse_launch_utc(
        submitted["submitted_utc"], "submitted_utc")
    manifest_submitted_at = _parse_launch_utc(
        manifest["submitted_utc"], "manifest submitted_utc")
    manifest_at = datetime.datetime.strptime(
        match.group(1), "%Y%m%dT%H%M%SZ").replace(
            tzinfo=datetime.timezone.utc)
    if not (claimed_at <= prepared_at <= submitted_at
            <= manifest_at <= manifest_submitted_at):
        raise AnalysisError("launch timestamps violate claim/submit chronology")

    return {
        "schema": "a6-holdout-launch-provenance-v1",
        "job_id": submitted["job_id"],
        "code_commit": code_commit,
        "selection_sha256": selection_sha,
        "preflight_sha256": preflight_sha,
        "grid_list_sha256": recomputed_grid_sha,
        "grid_list_recomputed": True,
        "claimed_utc": claim["claimed_utc"],
        "prepared_utc": intent["prepared_utc"],
        "submitted_utc": submitted["submitted_utc"],
        "manifest_submitted_utc": manifest["submitted_utc"],
        "manifest": {
            "path": str(manifest_path),
            "sha256": sha256_file(str(manifest_path)),
        },
        "lock": {
            name: {
                "path": str(lock / name),
                "sha256": sha256_file(str(lock / name)),
            }
            for name in sorted(expected_lock_files)
        },
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
    expected_load_policy = {
        "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
        "tolerance_kwh": REPLAY_TOL_KWH,
    }
    if ident.get("load_reconstruction") != expected_load_policy:
        raise AnalysisError(
            f"{label}: load reconstruction identity "
            f"{ident.get('load_reconstruction')!r} != "
            f"{expected_load_policy!r}")
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


def _evidence_close(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= 1e-10 * max(
        1.0, abs(actual), abs(expected))


def _finite_vector(value, n_slots: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != n_slots:
        raise AnalysisError(
            f"{label}: expected {n_slots} numeric slots, got "
            f"{None if not isinstance(value, list) else len(value)}")
    out = []
    for t, item in enumerate(value):
        if (not isinstance(item, (int, float)) or isinstance(item, bool)
                or not math.isfinite(item)):
            raise AnalysisError(f"{label}: nonfinite/non-numeric slot {t}")
        out.append(float(item) + 0.0)
    return out


def _validate_physical_load_evidence(
    obj: dict,
    *,
    n_slots: int,
    stats_field: str,
    label: str,
) -> tuple[list[float], list[float]]:
    """Recompute canonical load and the raw-residual audit from bytes."""
    if not isinstance(obj, dict):
        raise AnalysisError(f"{label}: evidence record is not an object")
    load = _finite_vector(obj.get("load"), n_slots, f"{label} load")
    if any(value < 0.0 for value in load):
        raise AnalysisError(f"{label}: canonical load contains a negative slot")
    charges = obj.get("charges")
    if not isinstance(charges, list):
        raise AnalysisError(f"{label}: charges are missing or malformed")
    physical = [0.0] * n_slots
    for i, charge in enumerate(charges):
        if not isinstance(charge, dict):
            raise AnalysisError(f"{label}: charge event {i} is malformed")
        slot, amount = charge.get("slot"), charge.get("kwh")
        if (not isinstance(slot, int) or isinstance(slot, bool)
                or not 0 <= slot < n_slots
                or not isinstance(amount, (int, float))
                or isinstance(amount, bool) or not math.isfinite(amount)
                or amount < 0.0):
            raise AnalysisError(f"{label}: charge event {i} is nonphysical")
        physical[slot] += float(amount)
    if any(not _evidence_close(a, b) for a, b in zip(load, physical)):
        raise AnalysisError(
            f"{label}: canonical load does not equal summed charge events")
    energy = obj.get("energy_charged_kwh")
    if energy is not None and (
            not isinstance(energy, (int, float)) or isinstance(energy, bool)
            or not math.isfinite(energy)
            or not _evidence_close(float(energy), sum(load))):
        raise AnalysisError(f"{label}: energy/load accounting mismatch")

    stats = obj.get(stats_field) or {}
    lr = ((stats.get("extra") or {}).get("load_reconstruction")
          if isinstance(stats, dict) else None)
    expected_policy = {
        "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
        "tolerance_kwh": REPLAY_TOL_KWH,
    }
    if (not isinstance(lr, dict)
            or any(lr.get(k) != v for k, v in expected_policy.items())):
        raise AnalysisError(f"{label}: missing load reconstruction evidence")
    raw = _finite_vector(
        lr.get("raw_load_kwh"), n_slots, f"{label} raw load")
    residual = _finite_vector(
        lr.get("residual_kwh"), n_slots, f"{label} load residual")
    expected_residual = [raw[t] - load[t] for t in range(n_slots)]
    if any(not _evidence_close(a, b)
           for a, b in zip(residual, expected_residual)):
        raise AnalysisError(f"{label}: recorded load residual was tampered")
    max_abs = max((abs(x) for x in expected_residual), default=0.0)
    max_slot = (max(range(n_slots), key=lambda t: abs(expected_residual[t]))
                if n_slots else None)
    expected_scalars = {
        "max_abs_residual_kwh": max_abs,
        "max_abs_residual_slot": max_slot,
        "raw_min_kwh": min(raw, default=0.0),
        "physical_min_kwh": min(load, default=0.0),
    }
    for field, expected in expected_scalars.items():
        actual = lr.get(field)
        if field == "max_abs_residual_slot":
            ok = actual == expected
        else:
            ok = (isinstance(actual, (int, float))
                  and not isinstance(actual, bool)
                  and math.isfinite(actual)
                  and _evidence_close(float(actual), float(expected)))
        if not ok:
            raise AnalysisError(
                f"{label}: load reconstruction scalar {field} was tampered")
    if max_abs > REPLAY_TOL_KWH:
        raise AnalysisError(
            f"{label}: raw/canonical residual {max_abs} exceeds "
            f"{REPLAY_TOL_KWH}")
    return load, raw


def _validate_schedule_evidence(
    obj: dict,
    *,
    inst,
    load: list[float],
    label: str,
    record: bool,
    column: bool,
) -> None:
    """Replay one serialized schedule and recompute its structural economics.

    ``validate_solution`` assumes well-shaped input and intentionally does not
    use a charge event's ``vehicle`` field when grouping events by an arc.  The
    closeout therefore prevalidates the complete shape and association first,
    then invokes that independent physical replay.  This prevents a stored
    ``replay_ok=true`` (or mutually adjusted economic fields) from becoming a
    substitute for evidence.
    """
    sequences = obj.get("sequences")
    arc_kinds = obj.get("arc_kinds")
    if not isinstance(sequences, list) or not sequences:
        raise AnalysisError(f"{label}: sequences must be a nonempty list")
    if not isinstance(arc_kinds, list) or len(arc_kinds) != len(sequences):
        raise AnalysisError(f"{label}: arc_kinds outer shape mismatch")

    trip_ids = {trip.id for trip in inst.trips}
    covered = []
    for vehicle, (sequence, kinds) in enumerate(zip(sequences, arc_kinds)):
        if not isinstance(sequence, list) or not sequence:
            raise AnalysisError(
                f"{label}: vehicle {vehicle} sequence must be nonempty")
        if (not isinstance(kinds, list)
                or len(kinds) != len(sequence) - 1
                or any(kind not in ("dir", "dep") for kind in kinds)):
            raise AnalysisError(
                f"{label}: vehicle {vehicle} arc shape/kind mismatch")
        for trip_id in sequence:
            if not isinstance(trip_id, str) or trip_id not in trip_ids:
                raise AnalysisError(
                    f"{label}: vehicle {vehicle} has unknown trip {trip_id!r}")
        covered.extend(sequence)
    if Counter(covered) != Counter(trip_ids):
        raise AnalysisError(f"{label}: trips are not covered exactly once")

    fleet = obj.get("fleet")
    if (not isinstance(fleet, int) or isinstance(fleet, bool)
            or fleet != len(sequences)
            or not 1 <= fleet <= inst.max_vehicles):
        raise AnalysisError(
            f"{label}: fleet {fleet!r} disagrees with {len(sequences)} "
            f"sequences or max_vehicles={inst.max_vehicles}")
    if record and obj.get("max_vehicles") != inst.max_vehicles:
        raise AnalysisError(
            f"{label}: max_vehicles {obj.get('max_vehicles')!r} != "
            f"instance value {inst.max_vehicles}")

    charges = obj.get("charges")
    if not isinstance(charges, list):
        raise AnalysisError(f"{label}: charges are missing or malformed")
    charge_keys = set()
    for i, charge in enumerate(charges):
        if not isinstance(charge, dict):
            raise AnalysisError(f"{label}: charge event {i} is malformed")
        vehicle = charge.get("vehicle")
        after = charge.get("after_trip")
        before = charge.get("before_trip")
        slot = charge.get("slot")
        if (not isinstance(vehicle, int) or isinstance(vehicle, bool)
                or not 0 <= vehicle < len(sequences)):
            raise AnalysisError(
                f"{label}: charge event {i} has invalid vehicle {vehicle!r}")
        if (not isinstance(after, str) or after not in trip_ids
                or not isinstance(before, str) or before not in trip_ids):
            raise AnalysisError(
                f"{label}: charge event {i} has invalid trip association")
        key = (vehicle, after, before, slot)
        if key in charge_keys:
            raise AnalysisError(
                f"{label}: duplicate charge event for vehicle/arc/slot {key}")
        charge_keys.add(key)
        sequence = sequences[vehicle]
        matches = [
            k for k in range(len(sequence) - 1)
            if sequence[k] == after and sequence[k + 1] == before
        ]
        if len(matches) != 1 or arc_kinds[vehicle][matches[0]] != "dep":
            raise AnalysisError(
                f"{label}: charge event {i} is not tied to its stated "
                "vehicle's consecutive depot arc")

    sol = Solution(
        sequences=[list(sequence) for sequence in sequences],
        arc_kinds=[list(kinds) for kinds in arc_kinds],
        charges=[dict(charge) for charge in charges],
        load=list(load),
        fleet=fleet,
    )
    violations = validate_solution(inst, sol, tol_kwh=REPLAY_TOL_KWH)
    if violations:
        raise AnalysisError(
            f"{label}: independent physical replay failed: {violations}")
    if obj.get("instance_hash") != inst.hash():
        raise AnalysisError(f"{label}: record instance hash mismatch")
    if obj.get("replay_ok") is not True:
        raise AnalysisError(f"{label}: replay_ok is not true")
    if obj.get("replay_violations") != []:
        raise AnalysisError(f"{label}: replay_violations is not empty")
    if record and (
            obj.get("replay_policy_version") != REPLAY_POLICY_VERSION
            or obj.get("replay_tol_kwh") != REPLAY_TOL_KWH):
        raise AnalysisError(f"{label}: replay policy metadata mismatch")

    if obj.get("schedule_hash") != sol.schedule_hash():
        raise AnalysisError(f"{label}: schedule hash does not recompute")
    if obj.get("load_hash") != sol.load_hash():
        raise AnalysisError(f"{label}: load hash does not recompute")

    trip_map = {trip.id: trip for trip in inst.trips}
    depot = inst.depot
    deadhead = 0.0
    for sequence, kinds in zip(sequences, arc_kinds):
        first = trip_map[sequence[0]]
        last = trip_map[sequence[-1]]
        deadhead += inst.dhm(depot, first.start_loc)
        for k, kind in enumerate(kinds):
            left = trip_map[sequence[k]]
            right = trip_map[sequence[k + 1]]
            if kind == "dir":
                deadhead += inst.dhm(left.end_loc, right.start_loc)
            else:
                deadhead += inst.dhm(left.end_loc, depot)
                deadhead += inst.dhm(depot, right.start_loc)
        deadhead += inst.dhm(last.end_loc, depot)
    if record:
        actual_deadhead = obj.get("dh_min_total")
        if (not isinstance(actual_deadhead, (int, float))
                or isinstance(actual_deadhead, bool)
                or not math.isfinite(actual_deadhead)
                or not _evidence_close(float(actual_deadhead), deadhead)):
            raise AnalysisError(f"{label}: deadhead minutes do not recompute")
    expected_ops = float(
        inst.vehicle_fixed_cost * fleet + inst.dh_cost_per_min * deadhead)
    actual_ops = obj.get("ops_cost")
    if (not isinstance(actual_ops, (int, float))
            or isinstance(actual_ops, bool) or not math.isfinite(actual_ops)
            or not _evidence_close(float(actual_ops), expected_ops)):
        raise AnalysisError(f"{label}: operating cost does not recompute")
    if column and obj.get("column_key") != column_key(obj):
        raise AnalysisError(f"{label}: column_key does not recompute")


def _finite_evidence_number(value, label: str) -> float:
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(value)):
        raise AnalysisError(f"{label}: missing/nonfinite numeric evidence")
    return float(value)


def _require_evidence_close(actual, expected: float, label: str) -> float:
    value = _finite_evidence_number(actual, label)
    if not _evidence_close(value, float(expected)):
        raise AnalysisError(
            f"{label}: {value!r} does not recompute as {expected!r}")
    return value


def _evidence_abs_tolerance(actual: float, expected: float,
                            absolute: float) -> float:
    """Combine an explicit solver-scale tolerance with serialization noise."""
    return float(absolute) + 1e-10 * max(
        1.0, abs(float(actual)), abs(float(expected)))


def _require_evidence_close_with_abs_tol(
    actual,
    expected: float,
    *,
    absolute: float,
    label: str,
) -> float:
    value = _finite_evidence_number(actual, label)
    if abs(value - float(expected)) > _evidence_abs_tolerance(
            value, float(expected), absolute):
        raise AnalysisError(
            f"{label}: {value!r} differs from {expected!r} beyond "
            f"absolute tolerance {absolute!r}")
    return value


def _require_decision_gap(actual, expected: float, label: str) -> float:
    """Compare a scheduler gap, admitting only the initial positive infinity."""
    if (not isinstance(actual, (int, float)) or isinstance(actual, bool)):
        raise AnalysisError(f"{label}: missing/non-numeric scheduler gap")
    value = float(actual)
    if math.isinf(expected):
        if value != expected:
            raise AnalysisError(
                f"{label}: {value!r} does not replay as {expected!r}")
        return value
    if not math.isfinite(value) or not _evidence_close(value, expected):
        raise AnalysisError(
            f"{label}: {value!r} does not replay as {expected!r}")
    return value


def _clean_master_evidence(
    event: dict,
    *,
    tag: str,
    oracle_call: int,
    label: str,
) -> tuple[float, float]:
    """Validate one clean RMP transcript and return (model objective, UB).

    The launch-era transcript stores every tangent-refinement solve and the
    exact-evaluation UB, but not the RMP lambdas/load.  We can therefore bind
    the model objective to the final LP solve and verify the frozen PWL-slack
    envelope; the exact-evaluation UB itself remains direct iteration
    evidence (rather than something reconstructible from the serialization).
    """
    solves = event.get("master_solves")
    if not isinstance(solves, list) or not solves:
        raise AnalysisError(f"{label}: clean master transcript is missing")
    seen_ids = set()
    for j, solve in enumerate(solves):
        expected_id = f"{tag}-it{oracle_call}-rmp-r{j}"
        if (not isinstance(solve, dict)
                or solve.get("solve_id") != expected_id
                or solve.get("status") != "OPTIMAL"
                or solve.get("backend") != REQUIRED_BACKEND
                or solve.get("n_int") != 0
                or solve.get("stabilized") not in (None, False)):
            raise AnalysisError(
                f"{label}: malformed clean master solve {j}")
        if expected_id in seen_ids:
            raise AnalysisError(f"{label}: duplicate clean master solve id")
        seen_ids.add(expected_id)
        obj = _finite_evidence_number(
            solve.get("obj"), f"{label} master solve {j} objective")
        bound = _finite_evidence_number(
            solve.get("bound"), f"{label} master solve {j} bound")
        if not _evidence_close(obj, bound):
            raise AnalysisError(
                f"{label}: clean LP objective/bound disagree at solve {j}")
    refinements = event.get("n_tangent_refinements")
    if (not isinstance(refinements, int) or isinstance(refinements, bool)
            or refinements != len(solves) - 1):
        raise AnalysisError(
            f"{label}: tangent-refinement count does not match master solves")
    z_model = _require_evidence_close(
        event.get("z_rmp_model"), float(solves[-1]["obj"]),
        f"{label} z_rmp_model")
    ub = _finite_evidence_number(event.get("ub_ch"), f"{label} ub_ch")
    slack = ub - z_model
    slack_tol = 1e-10 * max(1.0, abs(ub), abs(z_model))
    if slack < -slack_tol or slack > PWL_TOL + slack_tol:
        raise AnalysisError(
            f"{label}: exact/model master slack {slack} is outside "
            f"[0, {PWL_TOL}]")
    return z_model, ub


def _replay_cg_certificate_evidence(ck: dict, label: str) -> dict:
    """Derive the complete CG certificate trajectory from event evidence.

    Checkpoint ``ub_history``, ``lb_history``, ``lb_best`` and ``outcome`` are
    treated only as redundant claims.  Bounds are rebuilt chronologically
    from clean-master iteration records and the linked pricing oracle's
    certified solver bound.  Candidate calls carry the previously derived LB
    and can never create a certificate.
    """
    if not isinstance(ck, dict) or ck.get("done") is not True:
        raise AnalysisError(f"{label}: checkpoint is not a completed state")
    identity = ck.get("identity") or {}
    epsilon = _finite_evidence_number(
        identity.get("epsilon"), f"{label} epsilon")
    budget = identity.get("budget")
    if (epsilon < 0 or not isinstance(budget, int)
            or isinstance(budget, bool) or budget <= 0):
        raise AnalysisError(f"{label}: invalid certificate identity")
    method = identity.get("method", "a2")
    if method not in METHODS:
        raise AnalysisError(f"{label}: unsupported certificate method {method!r}")

    calls = ck.get("oracle_calls")
    events = ck.get("oracle_events")
    iterations = ck.get("iteration_events")
    if (not isinstance(calls, int) or isinstance(calls, bool)
            or not 2 <= calls <= budget
            or not isinstance(events, list) or len(events) != calls
            or not isinstance(iterations, list)):
        raise AnalysisError(f"{label}: malformed CG event cardinality")

    seed = events[0]
    seed_extra = seed.get("extra") if isinstance(seed, dict) else None
    if (not isinstance(seed_extra, dict)
            or seed.get("regime") != "cg-seed"
            or not isinstance(seed_extra.get("tag"), str)
            or not seed_extra["tag"]
            or seed_extra.get("call_id") != f"{seed_extra['tag']}-oc0"):
        raise AnalysisError(f"{label}: malformed seed oracle evidence")
    tag = seed_extra["tag"]
    if tag != method:
        raise AnalysisError(
            f"{label}: oracle tag {tag!r} does not match method {method!r}")

    terminal = []
    priced = []
    for pos, event in enumerate(iterations):
        if not isinstance(event, dict) or event.get("terminal") not in (
                None, False, True):
            raise AnalysisError(f"{label}: malformed iteration event {pos}")
        (terminal if event.get("terminal") is True else priced).append(event)
    if len(terminal) > 1 or len(priced) != calls - 1:
        raise AnalysisError(
            f"{label}: iteration/oracle cardinality does not replay")
    if terminal and (iterations[-1] is not terminal[0] or calls != budget):
        raise AnalysisError(
            f"{label}: terminal master is not the final budget event")

    ub_history = []
    lb_history = []
    lb_best = -float("inf")
    first_certificate_call = None
    previous_ub = float("inf")
    for oracle_call, event in enumerate(priced, start=1):
        elabel = f"{label} iteration {oracle_call}"
        prior_lb_best = lb_best
        if event.get("oracle_calls") != oracle_call:
            raise AnalysisError(f"{elabel}: oracle-call index mismatch")
        oracle = events[oracle_call]
        extra = oracle.get("extra") if isinstance(oracle, dict) else None
        call_id = f"{tag}-oc{oracle_call}"
        if (not isinstance(extra, dict) or extra.get("tag") != tag
                or extra.get("call_id") != call_id
                or event.get("pricing_solve_id") != call_id):
            raise AnalysisError(f"{elabel}: pricing oracle link is broken")

        if method == "a2":
            clean = True
            if (event.get("phase") != "clean"
                    or event.get("call_kind") not in (None, "clean")):
                raise AnalysisError(f"{elabel}: A2 has a non-clean iteration")
        else:
            kind = event.get("call_kind")
            phase = event.get("phase")
            if kind not in ("clean", "candidate") or phase != (
                    "clean" if kind == "clean" else "stabilized"):
                raise AnalysisError(f"{elabel}: A6 call kind/phase disagree")
            clean = kind == "clean"
            for field in ("call_kind", "trigger_selected", "triggers_fired"):
                if extra.get(field) != event.get(field):
                    raise AnalysisError(
                        f"{elabel}: oracle/iteration {field} disagree")
        expected_regime = "cg-pricing" if clean else "cg-stab-pricing"
        if oracle.get("regime") != expected_regime:
            raise AnalysisError(f"{elabel}: oracle regime does not match call")

        for field in ("column_key", "column_novel"):
            if extra.get(field) != event.get(field):
                raise AnalysisError(
                    f"{elabel}: oracle/iteration {field} disagree")

        if clean:
            z_model, ub = _clean_master_evidence(
                event, tag=tag, oracle_call=oracle_call, label=elabel)
        else:
            if not math.isfinite(lb_best):
                raise AnalysisError(
                    f"{elabel}: candidate precedes any certified clean bound")
            if event.get("master_solves") != []:
                raise AnalysisError(
                    f"{elabel}: a6_a4 candidate has unexpected master solves")
            ub = _finite_evidence_number(
                event.get("ub_ch"), f"{elabel} ub_ch")

        if method == A6_METHOD:
            _require_decision_gap(
                event.get("gap_at_decision"), ub - prior_lb_best,
                f"{elabel} gap_at_decision")

        if clean:
            sigma = _finite_evidence_number(
                event.get("duals_sigma"), f"{elabel} duals_sigma")
            solver = oracle.get("solver") or {}
            pricing_bound = _finite_evidence_number(
                solver.get("bound"), f"{elabel} pricing certified bound")
            pricing_model_incumbent = _finite_evidence_number(
                solver.get("obj"), f"{elabel} pricing model incumbent")
            pricing_incumbent = _finite_evidence_number(
                oracle.get("obj_true"), f"{elabel} pricing incumbent")
            if (pricing_bound > pricing_model_incumbent
                    and not _evidence_close(
                        pricing_bound, pricing_model_incumbent)):
                raise AnalysisError(
                    f"{elabel}: pricing bound exceeds model incumbent")
            if (pricing_bound > pricing_incumbent
                    and not _evidence_close(pricing_bound, pricing_incumbent)):
                raise AnalysisError(
                    f"{elabel}: pricing bound exceeds physical incumbent")
            min_rc_lb = pricing_bound - sigma
            min_rc_ub = pricing_incumbent - sigma
            for owner, record in (("iteration", event), ("oracle", extra)):
                _require_evidence_close(
                    record.get("min_reduced_cost_lb"), min_rc_lb,
                    f"{elabel} {owner} min_reduced_cost_lb")
                _require_evidence_close(
                    record.get("min_reduced_cost_ub"), min_rc_ub,
                    f"{elabel} {owner} min_reduced_cost_ub")
            pricing_gap = pricing_incumbent - pricing_bound
            if pricing_gap < 0.0 and not _evidence_close(pricing_gap, 0.0):
                raise AnalysisError(f"{elabel}: pricing gap is negative")
            _require_evidence_close(
                event.get("pricing_gap_abs"), pricing_gap,
                f"{elabel} pricing_gap_abs")
            if "pricing_gap_rel" in event:
                _require_evidence_close(
                    event.get("pricing_gap_rel"),
                    pricing_gap / max(1e-12, abs(pricing_incumbent)),
                    f"{elabel} pricing_gap_rel")
            lb_ch = z_model + min(0.0, min_rc_lb)
            _require_evidence_close(
                event.get("lb_ch"), lb_ch, f"{elabel} lb_ch")
            lb_best = max(lb_best, lb_ch)
            _require_evidence_close(
                event.get("lb_best"), lb_best, f"{elabel} lb_best")
        if ub > previous_ub + TOL_MONO:
            raise AnalysisError(f"{elabel}: UB history is not monotone")
        gap = ub - lb_best
        _require_evidence_close(
            event.get("certificate_gap"), gap,
            f"{elabel} certificate_gap")
        ub_history.append(ub)
        lb_history.append(lb_best)
        previous_ub = ub
        if clean and gap <= epsilon:
            first_certificate_call = oracle_call + 1
            if oracle_call != calls - 1 or terminal:
                raise AnalysisError(
                    f"{elabel}: trace continues after first certificate")

    if terminal:
        event = terminal[0]
        elabel = f"{label} terminal iteration"
        if (event.get("phase") != "terminal"
                or event.get("oracle_calls") != calls
                or event.get("pricing_solve_id") is not None
                or event.get("iteration_id") != f"{tag}-it{calls}-terminal"):
            raise AnalysisError(f"{elabel}: malformed terminal master event")
        _z_model, ub = _clean_master_evidence(
            event, tag=tag, oracle_call=calls, label=elabel)
        if ub > previous_ub + TOL_MONO:
            raise AnalysisError(f"{elabel}: UB history is not monotone")
        _require_evidence_close(
            event.get("lb_best"), lb_best, f"{elabel} lb_best")
        gap = ub - lb_best
        _require_evidence_close(
            event.get("certificate_gap"), gap,
            f"{elabel} certificate_gap")
        ub_history.append(ub)
        lb_history.append(lb_best)
        if gap <= epsilon:
            first_certificate_call = calls
        expected_type = "budget_exhausted"
    else:
        ub = ub_history[-1]
        gap = ub - lb_best
        if first_certificate_call is None:
            raise AnalysisError(
                f"{label}: completed trace has no certificate or terminal event")
        expected_type = "certified"

    stored_ubs = ck.get("ub_history")
    stored_lbs = ck.get("lb_history")
    if (not isinstance(stored_ubs, list) or not isinstance(stored_lbs, list)
            or len(stored_ubs) != len(ub_history)
            or len(stored_lbs) != len(lb_history)
            or any(not isinstance(a, (int, float)) or isinstance(a, bool)
                   or not math.isfinite(a) or not _evidence_close(float(a), b)
                   for a, b in zip(stored_ubs, ub_history))
            or any(not isinstance(a, (int, float)) or isinstance(a, bool)
                   or not math.isfinite(a) or not _evidence_close(float(a), b)
                   for a, b in zip(stored_lbs, lb_history))):
        raise AnalysisError(
            f"{label}: checkpoint UB/LB histories do not replay")
    _require_evidence_close(
        ck.get("lb_best"), lb_best, f"{label} checkpoint lb_best")

    outcome = ck.get("outcome") or {}
    expected_certified = bool(gap <= epsilon)
    if (outcome.get("type") != expected_type
            or outcome.get("certified") is not expected_certified
            or outcome.get("oracle_calls") != calls):
        raise AnalysisError(
            f"{label}: terminal outcome does not follow replayed trace")
    for field, expected in (
            ("ub_ch", ub), ("lb_best", lb_best), ("gap", gap)):
        _require_evidence_close(
            outcome.get(field), expected, f"{label} outcome {field}")
    if expected_certified and first_certificate_call is None:
        raise AnalysisError(f"{label}: certified outcome has no first call")
    score = (first_certificate_call if expected_certified
             else BUDGET_EXHAUSTED_SCORE)
    return {
        "ub_history": ub_history,
        "lb_history": lb_history,
        "ub_ch": ub,
        "lb_best": lb_best,
        "gap": gap,
        "certified": expected_certified,
        "outcome_type": expected_type,
        "first_certificate_call": first_certificate_call,
        "score": score,
    }


def _validate_retained_column_lineage(
    ck: dict,
    label: str,
    certificate: dict,
) -> None:
    """Rebuild the retained-column stream from chronological oracle bytes."""
    columns = ck.get("columns")
    keys = ck.get("keys")
    events = ck.get("oracle_events")
    iterations = [
        event for event in (ck.get("iteration_events") or [])
        if event.get("terminal") is not True
    ]
    if (not isinstance(columns, list) or not columns
            or not isinstance(keys, list) or not isinstance(events, list)):
        raise AnalysisError(f"{label}: malformed retained-column evidence")
    recomputed_keys = [column_key(column) for column in columns]
    if keys != recomputed_keys or len(set(keys)) != len(keys):
        raise AnalysisError(
            f"{label}: retained key list does not exactly match columns")

    iteration_by_call = {
        event.get("oracle_calls"): event for event in iterations
    }
    if len(iteration_by_call) != len(iterations):
        raise AnalysisError(f"{label}: duplicate iteration oracle-call index")
    expected_columns = []
    seen_keys = set()
    expected_column_fields = {
        "sequences", "arc_kinds", "charges", "load", "ops_cost", "fleet",
        "schedule_hash", "load_hash", "instance_hash", "replay_ok",
        "replay_violations", "oracle_stats", "column_key",
    }
    for call, event in enumerate(events):
        extra = event.get("extra") or {}
        projected = {
            "sequences": event.get("sequences"),
            "arc_kinds": event.get("arc_kinds"),
            "charges": event.get("charges"),
            "load": event.get("load"),
            "ops_cost": event.get("ops_cost"),
            "fleet": event.get("fleet"),
            "schedule_hash": event.get("schedule_hash"),
            "load_hash": event.get("load_hash"),
            "instance_hash": event.get("instance_hash"),
            "replay_ok": event.get("replay_ok"),
            "replay_violations": event.get("replay_violations"),
            "oracle_stats": event.get("solver"),
        }
        projected["column_key"] = column_key(projected)
        if call == 0:
            expected_columns.append(projected)
            seen_keys.add(projected["column_key"])
            continue
        novel = projected["column_key"] not in seen_keys
        iteration = iteration_by_call.get(call)
        if (not isinstance(iteration, dict)
                or extra.get("column_key") != projected["column_key"]
                or iteration.get("column_key") != projected["column_key"]
                or extra.get("column_novel") is not novel
                or iteration.get("column_novel") is not novel):
            raise AnalysisError(
                f"{label}: retained-column novelty/linkage fails at call {call}")
        # Both A2 and A6 return immediately when a clean call first closes
        # the certificate, before their later "retain every novel column"
        # branch.  All other novel calls, including the last candidate before
        # a terminal budget master, are retained.
        certifying_return = (
            certificate["outcome_type"] == "certified"
            and certificate["first_certificate_call"] == call + 1
        )
        if novel and not certifying_return:
            expected_columns.append(projected)
            seen_keys.add(projected["column_key"])

    if len(columns) != len(expected_columns):
        raise AnalysisError(
            f"{label}: retained columns do not match novel oracle stream")
    for j, (stored, expected) in enumerate(zip(columns, expected_columns)):
        if (not isinstance(stored, dict)
                or set(stored) != expected_column_fields
                or stored != expected):
            raise AnalysisError(
                f"{label}: retained column {j} does not equal its oracle "
                "projection")


def _validate_clean_bound_safety(
    ck: dict,
    market,
    label: str,
    certificate: dict,
) -> None:
    """Validate every derivable clean-master and global-bound invariant.

    Historical checkpoints omit the clean RMP primal load/lambdas and link
    duals.  We therefore solve the exact convex restricted master again from
    the retained columns, obtaining an independent feasible upper bound and a
    Frank--Wolfe lower bound.  This proves certificate safety without claiming
    to reproduce the producer's missing primal/dual path.  The retained-column
    dual-tightness and price-independent ``theta_cert`` checks separately bind
    every clean lower bound to serialized oracle evidence.
    """
    events = ck["oracle_events"]
    columns = ck["columns"]
    iterations = ck["iteration_events"]
    retained_count = 1
    master_bounds = {}

    def validate_master(event: dict, event_label: str) -> dict:
        if retained_count not in master_bounds:
            master_bounds[retained_count] = _independent_master_bounds(
                columns[:retained_count], market,
                label=f"{event_label} exact restricted master")
        bounds = master_bounds[retained_count]
        ub = _finite_evidence_number(
            event.get("ub_ch"), f"{event_label} ub_ch")
        lower = bounds["lower_bound"]
        upper = bounds["upper_bound"]
        if ub < lower - _evidence_abs_tolerance(ub, lower, TOL_MONO):
            raise AnalysisError(
                f"{event_label}: ub_ch is below the independently bounded "
                "restricted-master optimum")
        if ub > upper + PWL_TOL + _evidence_abs_tolerance(
                ub, upper, TOL_MONO):
            raise AnalysisError(
                f"{event_label}: ub_ch exceeds the independently bounded "
                "restricted-master optimum plus PWL tolerance")
        z_model = event.get("z_rmp_model")
        if z_model is not None:
            z_model = _finite_evidence_number(
                z_model, f"{event_label} z_rmp_model")
            if z_model > upper + _evidence_abs_tolerance(
                    z_model, upper, TOL_MONO):
                raise AnalysisError(
                    f"{event_label}: z_rmp_model exceeds an independent "
                    "restricted-master feasible objective")
            if z_model < lower - PWL_TOL - _evidence_abs_tolerance(
                    z_model, lower, TOL_MONO):
                raise AnalysisError(
                    f"{event_label}: z_rmp_model is below the independent "
                    "restricted-master lower bound beyond PWL tolerance")
        return bounds

    for event in iterations:
        if event.get("terminal") is True:
            if event.get("n_columns") != retained_count:
                raise AnalysisError(
                    f"{label}: terminal n_columns does not replay")
            bounds = validate_master(event, f"{label} terminal")
            terminal_gap = _finite_evidence_number(
                event.get("certificate_gap"),
                f"{label} terminal certificate_gap")
            if terminal_gap <= EPSILON:
                lb_best = _finite_evidence_number(
                    event.get("lb_best"), f"{label} terminal lb_best")
                safe_gap = bounds["upper_bound"] - lb_best
                if safe_gap > EPSILON + _evidence_abs_tolerance(
                        safe_gap, EPSILON, MASTER_FW_TOL):
                    raise AnalysisError(
                        f"{label} terminal: certificate is not supported by "
                        "an independent restricted-master feasible bound")
            continue

        call = event.get("oracle_calls")
        elabel = f"{label} iteration {call}"
        if (not isinstance(call, int) or isinstance(call, bool)
                or not 1 <= call < len(events)):
            raise AnalysisError(f"{elabel}: invalid oracle-call index")
        if event.get("n_columns") != retained_count:
            raise AnalysisError(f"{elabel}: n_columns does not replay")

        bounds = validate_master(event, elabel)

        oracle = events[call]
        if event.get("phase") == "clean":
            pricing = (((oracle.get("solver") or {}).get("extra") or {})
                       .get("pricing_objective_reconstruction") or {})
            prices = _finite_vector(
                pricing.get("prices"), market.n_slots,
                f"{elabel} full prices")
            sigma = _finite_evidence_number(
                event.get("duals_sigma"), f"{elabel} duals_sigma")
            retained_costs = [
                float(column["ops_cost"] + sum(
                    prices[t] * column["load"][t]
                    for t in range(market.n_slots)))
                for column in columns[:retained_count]
            ]
            _require_evidence_close_with_abs_tol(
                sigma, min(retained_costs),
                absolute=RC_TOL,
                label=f"{elabel} retained-column dual tightness")

            pricing_bound = _finite_evidence_number(
                (oracle.get("solver") or {}).get("bound"),
                f"{elabel} pricing certified bound")
            safe_bound = theta_cert(market, prices, pricing_bound)
            if not math.isfinite(safe_bound):
                raise AnalysisError(
                    f"{elabel}: independent Lagrangian bound is nonfinite")
            claimed_bound = _finite_evidence_number(
                event.get("lb_ch"), f"{elabel} lb_ch")
            if claimed_bound - safe_bound > _evidence_abs_tolerance(
                    claimed_bound, safe_bound, RC_TOL):
                raise AnalysisError(
                    f"{elabel}: lb_ch exceeds independent Lagrangian bound")

            certificate_gap = _finite_evidence_number(
                event.get("certificate_gap"),
                f"{elabel} certificate_gap")
            if certificate_gap <= EPSILON:
                lb_best = _finite_evidence_number(
                    event.get("lb_best"), f"{elabel} lb_best")
                safe_gap = bounds["upper_bound"] - lb_best
                if safe_gap > EPSILON + _evidence_abs_tolerance(
                        safe_gap, EPSILON, MASTER_FW_TOL):
                    raise AnalysisError(
                        f"{elabel}: certificate is not supported by an "
                        "independent restricted-master feasible bound")

        certifying_return = (
            certificate["outcome_type"] == "certified"
            and certificate["first_certificate_call"] == call + 1
        )
        if event.get("column_novel") is True and not certifying_return:
            retained_count += 1

    if retained_count != len(columns):
        raise AnalysisError(
            f"{label}: chronological retained-column count differs")


def _independent_master_bounds(
    columns: list[dict],
    market,
    *,
    label: str,
) -> dict:
    """Bracket the exact convex restricted-master optimum from raw columns.

    The objective over the simplex is a convex quadratic.  A primal active-set
    solve produces a feasible convex combination.  At that point the standard
    Frank--Wolfe gap is a rigorous global optimality gap, so ``f - gap`` and
    ``f`` are independently derived lower/upper bounds even if the active-set
    iteration terminates short of an exact KKT solution.
    """
    if not isinstance(columns, list) or not columns:
        raise AnalysisError(f"{label}: no retained columns")
    try:
        loads = np.asarray([column["load"] for column in columns], dtype=float)
        ops = np.asarray([column["ops_cost"] for column in columns], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisError(f"{label}: malformed retained columns") from exc
    if (loads.ndim != 2 or loads.shape != (len(columns), market.n_slots)
            or ops.shape != (len(columns),)
            or not np.isfinite(loads).all() or not np.isfinite(ops).all()):
        raise AnalysisError(f"{label}: nonfinite/wrong-shape master data")

    linear_market = np.asarray(
        market.a + market.b * market.U, dtype=float)
    slopes = np.asarray(market.b, dtype=float)
    if (linear_market.shape != (market.n_slots,)
            or slopes.shape != (market.n_slots,)
            or not np.isfinite(linear_market).all()
            or not np.isfinite(slopes).all()
            or np.any(slopes < 0.0)):
        raise AnalysisError(f"{label}: invalid affine-market coefficients")
    linear = ops + loads @ linear_market
    hessian = (loads * slopes) @ loads.T

    vertex_objectives = linear + 0.5 * np.diag(hessian)
    start = int(np.argmin(vertex_objectives))
    weights = np.zeros(len(columns), dtype=float)
    weights[start] = 1.0
    gradient = hessian[:, start] + linear
    max_iterations = max(10_000, 1_000 * len(columns))

    for _iteration in range(max_iterations):
        active = np.flatnonzero(weights > 1e-14)
        if len(active) == 0:
            raise AnalysisError(
                f"{label}: independent master lost simplex feasibility")
        upper = float(
            0.5 * weights @ hessian @ weights + linear @ weights)
        gap = float(weights @ gradient - np.min(gradient))
        gap_noise = 1e-10 * max(
            1.0, abs(upper), float(np.max(np.abs(gradient))))
        if gap < 0.0 and abs(gap) <= gap_noise:
            gap = 0.0
        if not math.isfinite(upper) or not math.isfinite(gap) or gap < 0.0:
            raise AnalysisError(
                f"{label}: independent master bounds are nonfinite")
        if gap <= MASTER_FW_TOL + gap_noise:
            load = weights @ loads
            direct_upper = float(
                weights @ ops + market.system_cost_delta(load))
            _require_evidence_close_with_abs_tol(
                upper, direct_upper,
                absolute=MASTER_FW_TOL,
                label=f"{label} independent objective")
            return {
                "lower_bound": upper - gap,
                "upper_bound": upper,
                "fw_gap": gap,
                "active_columns": len(active),
            }

        entering = int(np.argmin(gradient))
        leaving = int(active[np.argmax(gradient[active])])
        pairwise_improvement = float(
            gradient[leaving] - gradient[entering])
        if (entering == leaving or pairwise_improvement <= 0.0
                or weights[leaving] <= 0.0):
            raise AnalysisError(
                f"{label}: independent master stalled above its gap target")
        direction_curvature = float(
            hessian[entering, entering]
            + hessian[leaving, leaving]
            - 2.0 * hessian[entering, leaving])
        max_step = float(weights[leaving])
        if direction_curvature <= 1e-20:
            step = max_step
        else:
            step = min(
                max_step, pairwise_improvement / direction_curvature)
        if not math.isfinite(step) or step <= 0.0:
            raise AnalysisError(
                f"{label}: independent master produced an invalid step")
        weights[entering] += step
        weights[leaving] -= step
        if abs(weights[leaving]) <= 1e-14:
            weights[leaving] = 0.0
        if (np.min(weights) < -1e-12
                or abs(float(np.sum(weights)) - 1.0) > 1e-10):
            raise AnalysisError(
                f"{label}: independent master left the simplex")
        gradient += step * (
            hessian[:, entering] - hessian[:, leaving])

    raise AnalysisError(
        f"{label}: independent master did not close its Frank--Wolfe gap")


def _replay_a6_a4_mechanism(ck: dict, market, label: str) -> None:
    """Replay all A4 diagnostics derivable from launch-era evidence.

    The candidate's contemporaneous clean-RMP out dual was not serialized, so
    its price cannot be independently anchored to that solve.  Conditional on
    the recorded candidate price, however, theta, serious/null classification,
    direction signal, alpha transition, center, and final counters are all
    deterministic and must replay.
    """
    if (ck.get("identity") or {}).get("method") != A6_METHOD:
        return
    state = initial_stab_state("a4", market)
    events = ck["oracle_events"]
    iterations = [
        event for event in ck["iteration_events"]
        if event.get("terminal") is not True
    ]
    for event in iterations:
        call = event["oracle_calls"]
        elabel = f"{label} iteration {call}"
        oracle = events[call]
        pricing = (((oracle.get("solver") or {}).get("extra") or {})
                   .get("pricing_objective_reconstruction") or {})
        prices = _finite_vector(
            pricing.get("prices"), market.n_slots,
            f"{elabel} full prices")
        pricing_bound = _finite_evidence_number(
            (oracle.get("solver") or {}).get("bound"),
            f"{elabel} pricing certified bound")
        theta = theta_cert(market, prices, pricing_bound)
        if not math.isfinite(theta):
            raise AnalysisError(f"{elabel}: theta_cert is nonfinite")

        if event.get("call_kind") == "clean":
            best = state.get("theta_best")
            if best is None or theta > best:
                state["theta_best"] = theta
            continue

        _require_evidence_close(
            event.get("theta_cert"), theta, f"{elabel} theta_cert")
        expected_serious = serious_step(state.get("theta_best"), theta)
        if event.get("serious_step") is not expected_serious:
            raise AnalysisError(
                f"{elabel}: serious/null classification does not replay")

        before = event.get("params_before")
        if not isinstance(before, dict) or set(before) != {"alpha"}:
            raise AnalysisError(f"{elabel}: invalid A4 params_before")
        alpha = _require_evidence_close(
            before.get("alpha"), state["alpha"],
            f"{elabel} alpha before")
        if not 0.0 <= alpha < 1.0:
            raise AnalysisError(f"{elabel}: A4 alpha cannot imply out price")

        pi_candidate = [-value for value in prices]
        pi_out = [
            (pi_candidate[t] - alpha * state["center"][t])
            / (1.0 - alpha)
            for t in range(market.n_slots)
        ]
        prices_out = [-value for value in pi_out]
        signal = a4_direction_signal(
            market, prices, prices_out, oracle["load"])
        _require_evidence_close(
            event.get("a4_signal"), signal, f"{elabel} a4_signal")
        alpha_after = a4_alpha_update(alpha, signal)
        after = event.get("params_after")
        if not isinstance(after, dict) or set(after) != {"alpha"}:
            raise AnalysisError(f"{elabel}: invalid A4 params_after")
        _require_evidence_close(
            after.get("alpha"), alpha_after, f"{elabel} alpha after")

        state["alpha"] = alpha_after
        if expected_serious:
            state["center"] = pi_candidate
            state["serious_steps"] += 1
        else:
            state["null_steps"] += 1
        best = state.get("theta_best")
        if best is None or theta > best:
            state["theta_best"] = theta
        _require_evidence_close(
            event.get("theta_best"), state["theta_best"],
            f"{elabel} theta_best")

    stored = ck.get("stab")
    if not isinstance(stored, dict) or set(stored) != set(state):
        raise AnalysisError(f"{label}: final A4 stabilization state differs")
    for field in ("alpha", "theta_best"):
        _require_evidence_close(
            stored.get(field), state[field], f"{label} final A4 {field}")
    for field in ("serious_steps", "null_steps"):
        if stored.get(field) != state[field]:
            raise AnalysisError(f"{label}: final A4 {field} differs")
    center = _finite_vector(
        stored.get("center"), market.n_slots, f"{label} final A4 center")
    if any(not _evidence_close(actual, expected)
           for actual, expected in zip(center, state["center"])):
        raise AnalysisError(f"{label}: final A4 center differs")


def _validate_cell_numeric_evidence(
    ck: dict,
    dck: dict,
    inst,
    market,
    label: str,
) -> None:
    n_slots = market.n_slots
    columns = ck.get("columns")
    if not isinstance(columns, list) or not columns:
        raise AnalysisError(f"{label}: retained columns are missing/empty")
    for j, col in enumerate(columns):
        clabel = f"{label} column {j}"
        load, _raw = _validate_physical_load_evidence(
            col, n_slots=n_slots, stats_field="oracle_stats",
            label=clabel)
        _validate_schedule_evidence(
            col, inst=inst, load=load, label=clabel,
            record=False, column=True)
    for i, rec in enumerate(ck.get("oracle_events") or []):
        rlabel = f"{label} oracle event {i}"
        load, raw = _validate_physical_load_evidence(
            rec, n_slots=n_slots, stats_field="solver", label=rlabel)
        _validate_schedule_evidence(
            rec, inst=inst, load=load, label=rlabel,
            record=True, column=False)
        stats_extra = ((rec.get("solver") or {}).get("extra") or {})
        pricing = stats_extra.get("pricing_objective_reconstruction")
        if (not isinstance(pricing, dict)
                or pricing.get("policy_version")
                != LOAD_RECONSTRUCTION_POLICY_VERSION):
            raise AnalysisError(f"{rlabel}: missing pricing objective evidence")
        prices = _finite_vector(
            pricing.get("prices"), n_slots, f"{rlabel} full prices")
        if rec.get("prices") != [round(x, 6) for x in prices]:
            raise AnalysisError(f"{rlabel}: rounded/full price mismatch")
        if i == 0:
            posted = [float(value) for value in market.price(
                [0.0] * n_slots)]
            if (rec.get("regime") != "cg-seed"
                    or any(not _evidence_close(actual, expected)
                           for actual, expected in zip(prices, posted))):
                raise AnalysisError(
                    f"{rlabel}: seed prices do not match frozen posted vector")
        ops_cost = rec.get("ops_cost")
        if (not isinstance(ops_cost, (int, float))
                or isinstance(ops_cost, bool) or not math.isfinite(ops_cost)):
            raise AnalysisError(f"{rlabel}: invalid operating cost")
        expected_obj = float(ops_cost + sum(
            prices[t] * load[t] for t in range(n_slots)))
        for field, actual in (
                ("record obj_true", rec.get("obj_true")),
                ("pricing physical_obj", pricing.get("physical_obj"))):
            if (not isinstance(actual, (int, float))
                    or isinstance(actual, bool) or not math.isfinite(actual)
                    or not _evidence_close(float(actual), expected_obj)):
                raise AnalysisError(f"{rlabel}: {field} mismatch")
        model_obj = pricing.get("model_obj")
        record_model_obj = rec.get("obj_model")
        solver_obj = (rec.get("solver") or {}).get("obj")
        solver_bound = (rec.get("solver") or {}).get("bound")
        expected_model_obj = float(ops_cost + sum(
            prices[t] * raw[t] for t in range(n_slots)))
        for field, actual, expected in (
                ("pricing model_obj", model_obj, expected_model_obj),
                ("record obj_model", record_model_obj, expected_model_obj),
                ("solver obj", solver_obj, expected_model_obj),
                ("pricing/record model_obj", model_obj, record_model_obj)):
            if (not isinstance(actual, (int, float))
                    or isinstance(actual, bool) or not math.isfinite(actual)
                    or not isinstance(expected, (int, float))
                    or isinstance(expected, bool) or not math.isfinite(expected)
                    or not _evidence_close(float(actual), float(expected))):
                raise AnalysisError(f"{rlabel}: {field} mismatch")
        if (not isinstance(solver_bound, (int, float))
                or isinstance(solver_bound, bool)
                or not math.isfinite(solver_bound)):
            raise AnalysisError(f"{rlabel}: solver bound is nonfinite")
        if (float(solver_bound) > expected_model_obj
                and not _evidence_close(
                    float(solver_bound), expected_model_obj)):
            raise AnalysisError(
                f"{rlabel}: solver bound exceeds model incumbent")
        if (float(solver_bound) > expected_obj
                and not _evidence_close(float(solver_bound), expected_obj)):
            raise AnalysisError(
                f"{rlabel}: solver bound exceeds physical incumbent")
        adjustment = pricing.get("abs_adjustment")
        expected_adjustment = abs(float(model_obj) - expected_obj)
        if (not isinstance(adjustment, (int, float))
                or isinstance(adjustment, bool)
                or not math.isfinite(adjustment)
                or not _evidence_close(
                    float(adjustment), expected_adjustment)):
            raise AnalysisError(
                f"{rlabel}: pricing abs_adjustment mismatch")

    certificate = _replay_cg_certificate_evidence(ck, label)
    _validate_retained_column_lineage(ck, label, certificate)
    _validate_clean_bound_safety(ck, market, label, certificate)
    _replay_a6_a4_mechanism(ck, market, label)

    drec = dck.get("record") or {}
    load, raw = _validate_physical_load_evidence(
        drec, n_slots=n_slots, stats_field="solver",
        label=f"{label} dictator record")
    _validate_schedule_evidence(
        drec, inst=inst, load=load, label=f"{label} dictator record",
        record=True, column=False)
    extra = ((drec.get("solver") or {}).get("extra") or {})
    objective = extra.get("dictator_objective_reconstruction")
    if (not isinstance(objective, dict)
            or objective.get("policy_version")
            != LOAD_RECONSTRUCTION_POLICY_VERSION):
        raise AnalysisError(
            f"{label}: missing dictator objective reconstruction evidence")
    ops_cost = drec.get("ops_cost")
    if (not isinstance(ops_cost, (int, float))
            or isinstance(ops_cost, bool) or not math.isfinite(ops_cost)):
        raise AnalysisError(f"{label}: dictator operating cost is invalid")
    expected_obj = float(
        ops_cost + market.system_cost_delta(load))
    for field, actual in (
            ("record obj_true", drec.get("obj_true")),
            ("dictator physical_obj", objective.get("physical_obj"))):
        if (not isinstance(actual, (int, float))
                or isinstance(actual, bool) or not math.isfinite(actual)
                or not _evidence_close(float(actual), expected_obj)):
            raise AnalysisError(f"{label}: dictator {field} mismatch")
    raw_true_obj = objective.get("raw_true_obj")
    expected_raw_true_obj = float(
        ops_cost + market.system_cost_delta(raw))
    if (not isinstance(raw_true_obj, (int, float))
            or isinstance(raw_true_obj, bool)
            or not math.isfinite(raw_true_obj)
            or not _evidence_close(
                float(raw_true_obj), expected_raw_true_obj)):
        raise AnalysisError(f"{label}: dictator raw_true_obj mismatch")
    adjustment = objective.get("abs_adjustment")
    expected_adjustment = abs(float(raw_true_obj) - expected_obj)
    if (not isinstance(adjustment, (int, float))
            or isinstance(adjustment, bool) or not math.isfinite(adjustment)
            or not _evidence_close(float(adjustment), expected_adjustment)):
        raise AnalysisError(f"{label}: dictator abs_adjustment mismatch")

    adaptive = dck.get("adaptive") or {}
    adaptive_ub = extra.get("adaptive_ub")
    adaptive_lb = extra.get("adaptive_lb")
    adaptive_gap = extra.get("adaptive_gap_abs")
    adaptive_tol = extra.get("adaptive_tol_abs")
    for field, value in (
            ("adaptive_ub", adaptive_ub),
            ("adaptive_lb", adaptive_lb),
            ("adaptive_gap_abs", adaptive_gap),
            ("adaptive_tol_abs", adaptive_tol)):
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(value)):
            raise AnalysisError(
                f"{label}: dictator {field} is missing/nonfinite")
        stored = adaptive.get(field)
        if (not isinstance(stored, (int, float)) or isinstance(stored, bool)
                or not math.isfinite(stored)
                or not _evidence_close(float(stored), float(value))):
            raise AnalysisError(
                f"{label}: dictator checkpoint/record {field} mismatch")
    if not _evidence_close(float(adaptive_ub), expected_obj):
        raise AnalysisError(f"{label}: dictator adaptive_ub mismatch")
    expected_gap = float(adaptive_ub) - float(adaptive_lb)
    if not _evidence_close(float(adaptive_gap), expected_gap):
        raise AnalysisError(f"{label}: dictator adaptive gap arithmetic mismatch")
    if (not _evidence_close(float(adaptive_tol), float(dck.get("tol_d")))
            or not _evidence_close(float(adaptive_tol), TOL_D)):
        raise AnalysisError(f"{label}: dictator adaptive tolerance mismatch")
    expected_converged = bool(expected_gap <= float(adaptive_tol))
    if (extra.get("adaptive_converged") is not expected_converged
            or adaptive.get("adaptive_converged") is not expected_converged):
        raise AnalysisError(
            f"{label}: dictator adaptive convergence flag mismatch")
    solve_rows = extra.get("adaptive_solve_stats")
    rounds = extra.get("adaptive_rounds")
    if (not isinstance(solve_rows, list) or not solve_rows
            or not isinstance(rounds, int) or isinstance(rounds, bool)
            or rounds != len(solve_rows)):
        raise AnalysisError(
            f"{label}: dictator adaptive subsolve history is malformed")
    certified_bounds = []
    for i, row in enumerate(solve_rows, start=1):
        if (not isinstance(row, dict) or row.get("round") != i
                or row.get("status") != "OPTIMAL"):
            raise AnalysisError(
                f"{label}: dictator adaptive subsolve {i} is malformed")
        bound = row.get("bound")
        incumbent = row.get("incumbent")
        if (not isinstance(bound, (int, float)) or isinstance(bound, bool)
                or not math.isfinite(bound)
                or not isinstance(incumbent, (int, float))
                or isinstance(incumbent, bool)
                or not math.isfinite(incumbent)):
            raise AnalysisError(
                f"{label}: dictator adaptive subsolve {i} has nonfinite "
                "bound/incumbent")
        bound = float(bound)
        incumbent = float(incumbent)
        row_gap = row.get("gap")
        expected_row_gap = incumbent - bound
        if (not isinstance(row_gap, (int, float))
                or isinstance(row_gap, bool) or not math.isfinite(row_gap)
                or not _evidence_close(float(row_gap), expected_row_gap)):
            raise AnalysisError(
                f"{label}: dictator adaptive subsolve {i} gap does not "
                "recompute")
        if bound > incumbent and not _evidence_close(bound, incumbent):
            raise AnalysisError(
                f"{label}: dictator adaptive subsolve {i} bound exceeds "
                "incumbent")
        certified_bounds.append(bound)
    if not _evidence_close(max(certified_bounds), float(adaptive_lb)):
        raise AnalysisError(
            f"{label}: dictator adaptive_lb does not recompute from bounds")
    if (float(adaptive_lb) > expected_obj
            and not _evidence_close(float(adaptive_lb), expected_obj)):
        raise AnalysisError(
            f"{label}: dictator certified lower bound exceeds independently "
            "recomputed physical upper bound")
    adaptive_model_obj = extra.get("adaptive_model_obj")
    if (not isinstance(adaptive_model_obj, (int, float))
            or isinstance(adaptive_model_obj, bool)
            or not math.isfinite(adaptive_model_obj)
            or not _evidence_close(
                float(adaptive_model_obj),
                float(solve_rows[-1]["incumbent"]))):
        raise AnalysisError(
            f"{label}: dictator adaptive model objective does not recompute")
    stored_model_obj = adaptive.get("adaptive_model_obj")
    if (adaptive.get("adaptive_solve_stats") != solve_rows
            or adaptive.get("adaptive_rounds") != rounds
            or not isinstance(stored_model_obj, (int, float))
            or isinstance(stored_model_obj, bool)
            or not math.isfinite(stored_model_obj)
            or not _evidence_close(
                float(stored_model_obj), float(adaptive_model_obj))):
        raise AnalysisError(
            f"{label}: dictator checkpoint/record adaptive history mismatch")
    z_d_ub = dck.get("z_d_ub")
    if (not isinstance(z_d_ub, (int, float)) or isinstance(z_d_ub, bool)
            or not math.isfinite(z_d_ub)
            or not _evidence_close(float(z_d_ub), float(adaptive_ub))):
        raise AnalysisError(f"{label}: dictator z_d_ub/adaptive_ub mismatch")


def _validate_cell_slurm_lineage(
    ck: dict,
    dck: dict,
    *,
    cell_index: int,
    label: str,
    launch_job_id: str | None = None,
) -> str:
    """Require every execution record to come from the frozen array task.

    The launch-era recorder did not preserve ``SLURM_ARRAY_JOB_ID``, so this
    can bind the exact task index and consistent task job ID but cannot infer
    the parent array ID.  That residual limitation is recorded in the
    engineering incident ledger rather than silently overstated here.
    """
    records = [
        *(ck.get("oracle_events") or []),
        *(ck.get("iteration_events") or []),
        (dck.get("record") or {}),
    ]
    if not records:
        raise AnalysisError(f"{label}: no records for Slurm lineage")
    expected_task = str(cell_index)
    job_ids = set()
    array_job_ids = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise AnalysisError(f"{label}: malformed Slurm record {i}")
        task_id = record.get("slurm_array_task_id")
        job_id = record.get("slurm_job_id")
        if task_id != expected_task:
            raise AnalysisError(
                f"{label}: Slurm task {task_id!r} != frozen cell index "
                f"{expected_task}")
        if (not isinstance(job_id, str)
                or re.fullmatch(r"[1-9]\d*(?:_\d+)?", job_id) is None):
            raise AnalysisError(
                f"{label}: missing/malformed Slurm job lineage")
        restart = record.get("slurm_restart_count")
        if (restart is not None
                and (not isinstance(restart, str) or not restart.isdigit())):
            raise AnalysisError(
                f"{label}: malformed Slurm restart count {restart!r}")
        job_ids.add(job_id)
        array_job_ids.add(record.get("slurm_array_job_id"))
    if len(job_ids) != 1:
        raise AnalysisError(
            f"{label}: records mix Slurm task job IDs {sorted(job_ids)}")
    if array_job_ids != {None}:
        if (None in array_job_ids or len(array_job_ids) != 1
                or launch_job_id is None
                or array_job_ids != {launch_job_id}):
            raise AnalysisError(
                f"{label}: parent Slurm array IDs {array_job_ids!r} do not "
                f"bind launch job {launch_job_id!r}")
    return next(iter(job_ids))


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
    launch: dict | None = None,
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
        dck = checkpoint.load(os.path.join(d, "dictator.ckpt.json"))
        d_ident = (dck or {}).get("identity") or {}
        expected_load_policy = {
            "policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH,
        }
        if d_ident.get("schema_version") != SCHEMA_VERSION:
            raise AnalysisError(
                f"{label}: dictator schema "
                f"{d_ident.get('schema_version')!r} != {SCHEMA_VERSION!r}")
        if d_ident.get("load_reconstruction") != expected_load_policy:
            raise AnalysisError(
                f"{label}: dictator load reconstruction identity "
                f"{d_ident.get('load_reconstruction')!r} != "
                f"{expected_load_policy!r}")
        inst = instance_builder(seed, n_trips)
        market = make_affine_market(inst, shape="duck", b_scale=b)
        _validate_cell_numeric_evidence(ck, dck, inst, market, label)
        _validate_cell_slurm_lineage(
            ck, dck, cell_index=cell_index, label=label,
            launch_job_id=None if launch is None else launch.get("job_id"))
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
    """Derive Section 6 score from the transcript after population safety.

    Production callers first run ``validate_holdout_root``, whose independent
    schedule, oracle, master-bound, and lineage checks are load bearing.  This
    small helper alone replays only the serialized certificate arithmetic.
    """
    replay = _replay_cg_certificate_evidence(ck, label)
    return int(replay["score"])


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
        "MANIFEST.json hashes every input and generated artifact.", "",
        "## Evidence limits", "",
        *[f"- {limitation}" for limitation in EVIDENCE_LIMITATIONS],
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


def _assert_analysis_publication_owned(
    target: Path,
    *,
    target_signature: tuple[int, int],
    expected_names: set[str],
    signatures: dict[str, tuple[int, int]],
    marker: Path,
    marker_signature: tuple[int, int],
) -> None:
    """Prove the reserved directory still contains only our exact inodes."""
    try:
        target_info = target.lstat()
    except OSError as exc:
        raise AnalysisError(
            "analysis publication reservation disappeared") from exc
    if (not stat.S_ISDIR(target_info.st_mode)
            or (target_info.st_dev, target_info.st_ino) != target_signature):
        raise AnalysisError(
            "analysis publication reservation ownership changed")
    try:
        observed = {entry.name for entry in target.iterdir()}
    except OSError as exc:
        raise AnalysisError(
            "cannot revalidate analysis publication reservation") from exc
    expected = {*expected_names, marker.name}
    if observed != expected:
        raise AnalysisError(
            "analysis publication reservation population changed")
    for name in sorted(expected_names):
        path = target / name
        try:
            info = path.lstat()
        except OSError as exc:
            raise AnalysisError(
                f"analysis publication artifact disappeared: {path}") from exc
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or (info.st_dev, info.st_ino) != signatures[name]):
            raise AnalysisError(
                f"analysis publication artifact ownership changed: {path}")
    try:
        marker_info = marker.lstat()
    except OSError as exc:
        raise AnalysisError(
            "analysis publication sentinel disappeared") from exc
    if (not stat.S_ISREG(marker_info.st_mode)
            or marker_info.st_nlink != 1
            or (marker_info.st_dev, marker_info.st_ino) != marker_signature):
        raise AnalysisError(
            "analysis publication sentinel ownership changed")


def _publish_analysis_directory_no_replace(
    staging: str | os.PathLike,
    destination: str | os.PathLike,
    *,
    expected_names: set[str],
) -> None:
    """Publish flat analysis artifacts under an exclusive reservation."""
    source = Path(staging)
    target = Path(destination)
    entries = {entry.name: entry for entry in source.iterdir()}
    if (set(entries) != expected_names
            or "MANIFEST.json" not in expected_names):
        raise AnalysisError("analysis publication staging is incomplete")
    signatures = {}
    for name, path in entries.items():
        if path.is_symlink() or not path.is_file():
            raise AnalysisError(f"unsafe analysis publication source: {path}")
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise AnalysisError(f"unsafe analysis publication source: {path}")
        signatures[name] = (info.st_dev, info.st_ino)
    try:
        target.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise AnalysisError(
            f"refusing existing analysis publication path: {target}") from exc
    target_info = target.lstat()
    target_signature = (target_info.st_dev, target_info.st_ino)

    marker = target / ".publication-incomplete"
    marker_signature = None
    linked = []
    try:
        descriptor = os.open(
            marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(b"incomplete\n")
            handle.flush()
            os.fsync(handle.fileno())
        marker_info = marker.lstat()
        marker_signature = (marker_info.st_dev, marker_info.st_ino)
        for name in [
                *sorted(set(entries) - {"MANIFEST.json"}),
                "MANIFEST.json"]:
            try:
                os.link(entries[name], target / name, follow_symlinks=False)
            except FileExistsError as exc:
                raise AnalysisError(
                    f"analysis publication target appeared: {target / name}"
                ) from exc
            linked.append(name)
        directory_fd = os.open(target, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        for name in sorted(entries):
            entries[name].unlink()
        source.rmdir()
        # The exclusive mkdir protects the reservation itself, but a path can
        # still appear or be replaced inside it while links are installed.
        # Revalidate the exact population and every inode immediately before
        # removing the only visible incomplete-state marker.
        _assert_analysis_publication_owned(
            target,
            target_signature=target_signature,
            expected_names=expected_names,
            signatures=signatures,
            marker=marker,
            marker_signature=marker_signature,
        )
        marker.unlink()
        os.chmod(target, 0o755)
        directory_fd = os.open(target, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        parent_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except BaseException as exc:
        cleanup_errors = []
        try:
            current_target = target.lstat()
        except FileNotFoundError:
            current_target = None
        except OSError as cleanup_exc:
            current_target = None
            cleanup_errors.append(str(cleanup_exc))
        target_owned = (
            current_target is not None
            and stat.S_ISDIR(current_target.st_mode)
            and (current_target.st_dev, current_target.st_ino)
            == target_signature
        )
        if not target_owned:
            cleanup_errors.append(
                "analysis publication reservation is no longer owned")
        else:
            for name in reversed(linked):
                path = target / name
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    continue
                if (info.st_dev, info.st_ino) == signatures[name]:
                    try:
                        path.unlink()
                    except OSError as cleanup_exc:
                        cleanup_errors.append(str(cleanup_exc))

        marker_owned = False
        if target_owned and marker_signature is not None:
            try:
                marker_info = marker.lstat()
            except FileNotFoundError:
                marker_info = None
            marker_owned = (
                marker_info is not None
                and stat.S_ISREG(marker_info.st_mode)
                and (marker_info.st_dev, marker_info.st_ino)
                == marker_signature
            )
        if target_owned:
            try:
                remaining = {entry.name for entry in target.iterdir()}
            except OSError as cleanup_exc:
                remaining = None
                cleanup_errors.append(str(cleanup_exc))
            # Remove our marker only when that makes the owned reservation
            # empty.  If competitor-owned paths remain, retain the marker and
            # reservation as an explicit fail-closed incident boundary.
            if remaining == ({marker.name} if marker_owned else set()):
                if marker_owned:
                    try:
                        marker.unlink()
                    except OSError as cleanup_exc:
                        cleanup_errors.append(str(cleanup_exc))
                try:
                    target.rmdir()
                except OSError as cleanup_exc:
                    cleanup_errors.append(str(cleanup_exc))
            elif remaining is not None:
                cleanup_errors.append(
                    "competitor-owned analysis publication paths remain")
        if cleanup_errors:
            raise AnalysisError(
                "analysis publication failed and reservation cleanup was "
                "incomplete: " + "; ".join(cleanup_errors)) from exc
        raise


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
    launch_validator=validate_launch_provenance,
    transfer_validator=validate_transfer_receipt,
    analysis_claimer=claim_single_analysis,
) -> str:
    root_path = Path(root).resolve()
    out_base_path = Path(out_base).resolve()
    if (not isinstance(stamp, str) or not stamp
            or stamp in (".", "..")
            or re.fullmatch(r"[A-Za-z0-9_.-]+", stamp) is None):
        raise AnalysisError(f"unsafe analysis stamp: {stamp!r}")
    if require_frozen_grid and re.fullmatch(
            r"\d{8}T\d{6}Z", stamp) is None:
        raise AnalysisError(
            "production analysis stamp must be YYYYMMDDTHHMMSSZ")
    out_dir_path = out_base_path / stamp
    if _path_is_within(out_dir_path, root_path):
        raise AnalysisError(
            "analysis output directory must be outside the raw holdout root")
    if out_dir_path.exists() or out_dir_path.is_symlink():
        raise AnalysisError(f"refusing existing output path: {out_dir_path}")
    if require_frozen_grid:
        if not (verify_code_commit and verify_selection_git
                and verify_experiment_commit):
            raise AnalysisError(
                "production analysis cannot disable Git/provenance gates")
        if out_base_path.exists():
            if (not out_base_path.is_dir()
                    or any(out_base_path.iterdir())):
                raise AnalysisError(
                    "production A6 closeout output already contains artifacts")
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
    launch = launch_validator(
        root, preflight, selection, instances=instances)
    transfer = None
    analysis_claim = None
    if require_frozen_grid:
        transfer = transfer_validator(
            root_path,
            preflight=preflight,
            selection=selection,
            launch=launch,
            analysis_code_commit=analysis_code_commit,
            repository=REPO_ROOT,
            verify_git=True,
        )
        analysis_claim = analysis_claimer(
            root_path,
            out_dir=out_dir_path,
            stamp=stamp,
            analysis_code_commit=analysis_code_commit,
            transfer=transfer,
        )
    paths = validate_holdout_root(
        root, instances, instance_builder, preflight=preflight,
        launch=launch)

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

    out_dir = str(out_dir_path)
    out_base = str(out_base_path)
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
        final_tree_snapshot = None
        if transfer is not None:
            final_tree_snapshot = _assert_analysis_inputs_unchanged(
                root_path, transfer, analysis_claim)
        holdout_files = (
            {row["path"]: row["sha256"]
             for row in final_tree_snapshot["files"]}
            if final_tree_snapshot is not None else tree_hashes(root))
        transfer_manifest = None if transfer is None else {
            "path": transfer["path"],
            "sha256": transfer["sha256"],
            "document": transfer["document"],
        }
        manifest = {
            "schema": CLOSEOUT_SCHEMA,
            "stamp": stamp,
            "analysis_code_commit": analysis_code_commit,
            "analysis_code_verified": code_verified,
            "selection": selection,
            "preflight": preflight,
            "launch": launch,
            "transfer": transfer_manifest,
            "analysis_claim": analysis_claim,
            "population": {
                "instances": [list(t) for t in instances],
                "methods": list(METHODS),
                "method_cells": len(cells),
            },
            "scoring": {
                "certified": "calls-to-certificate",
                "budget_exhausted": BUDGET_EXHAUSTED_SCORE,
            },
            "scientific_validation": {
                "independent_master_fw_tolerance": MASTER_FW_TOL,
                "evidence_limitations": list(EVIDENCE_LIMITATIONS),
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
                "holdout": {
                    "path": str(root_path),
                    "files": holdout_files,
                    "canonical_tree_sha256": (
                        None if final_tree_snapshot is None else
                        final_tree_snapshot["canonical_tree_sha256"]),
                },
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
        _publish_analysis_directory_no_replace(
            staging,
            out_dir,
            expected_names={*outputs, "MANIFEST.json"},
        )
        staging = ""
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
