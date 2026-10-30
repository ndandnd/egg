#!/usr/bin/env python3
"""Frozen A6 holdout driver: exactly 128 method-cells.

Population (doc/A6_SPARSE_STABILIZATION_SPEC.md Section 6):

    methods {a2, a6_a4} x seeds 16..31 x n_trips {8, 12}
    x b {0.01, 0.05} = 128 cells (64 matched pairs).

The driver fails closed unless the canonical, committed pilot selection
artifact is byte-identical to the frozen SHA-256 and selects ``a6_a4``.
The selection-gate commit must be an ancestor of the implementation HEAD;
HEAD is recorded as experiment-code provenance, not confused with the older
analysis-code commit stored inside the selection artifact.

Section 6 also forbids running either method if any generated physical
instance is infeasible.  ``--preflight`` therefore proves feasibility for
the *whole* 32-instance physical population before submission.  It builds a
deterministic zero-charge perfect pairing of all trips into exactly n/2
two-trip duties, checks time and SOC at every stage, and independently replays
the resulting cover with zero tolerance.  The atomic PREFLIGHT.json also
records all 64 market hashes.  Every method cell reconstructs and exact-
compares that complete manifest before creating its output directory.

Budget exhaustion is a valid completed scientific outcome.  Post-run audit
must gate 128 complete/sane cells and 64 per method, not demand 64/64
certification from either method.

Usage (from src/):
  python experiments/run_a6_holdout.py --preflight --out runs/a6_holdout
  python experiments/run_a6_holdout.py --list
  python experiments/run_a6_holdout.py --cell K --out runs/a6_holdout
  python experiments/run_a6_holdout.py --all --out runs/a6_holdout
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from egglab import checkpoint
from egglab.a6 import certified_cg_a6
from egglab.b2a2 import certified_cg, market_hash
from egglab.evsp import Solution, validate_solution
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.solver import backend
from experiments.run_b2a2_pilot import _dictator_stage


METHODS = ("a2", "a6_a4")
SELECTED_A6_METHOD = "a6_a4"
SEEDS = tuple(range(16, 32))
N_TRIPS = (8, 12)
B_SCALES = (0.01, 0.05)
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2
MIP_GAP = 1e-6
EXPECTED_CELLS = 128
EXPECTED_INSTANCES = 64
EXPECTED_PHYSICAL_INSTANCES = 32

SELECTION_RELATIVE_PATH = (
    "result/a6_pilot/20260819T005514Z/SELECTION.json"
)
EXPECTED_SELECTION_SHA256 = (
    "026ddc38e90f9dd2e9342a50cfb5550bc52731c5f1ee67d87d53008bd6b4b507"
)
SELECTION_GATE_COMMIT = "8f59a905bd5e12ac5784e57aebc66a03b47a00cb"
PREFLIGHT_FILENAME = "PREFLIGHT.json"
PREFLIGHT_SCHEMA = "a6-holdout-feasibility-v1"
CELL_PROVENANCE_FILENAME = "CELL_PROVENANCE.json"

SRC_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = SRC_DIR.parent


class HoldoutGuardError(RuntimeError):
    """A frozen-protocol or provenance gate failed."""


def physical_instances():
    """The 32 physical instances; b changes the market, not feasibility."""
    return list(itertools.product(SEEDS, N_TRIPS))


def market_instances():
    return list(itertools.product(SEEDS, N_TRIPS, B_SCALES))


def build_cells():
    return [
        (method, seed, n_trips, b)
        for method in METHODS
        for seed, n_trips, b in market_instances()
    ]


def validate_grid(cells) -> None:
    """Fail closed if any part of the frozen 128-cell grid drifts."""
    expected = [
        (m, s, n, b)
        for m in ("a2", "a6_a4")
        for s in range(16, 32)
        for n in (8, 12)
        for b in (0.01, 0.05)
    ]
    if cells != expected:
        raise HoldoutGuardError(
            "holdout grid differs from the frozen ordered 128-cell grid"
        )
    if len(cells) != EXPECTED_CELLS or len(set(cells)) != EXPECTED_CELLS:
        raise HoldoutGuardError("holdout grid count/uniqueness failure")
    counts = {m: sum(c[0] == m for c in cells) for m in METHODS}
    if counts != {"a2": 64, "a6_a4": 64}:
        raise HoldoutGuardError(f"holdout method counts invalid: {counts}")
    if any(c[0] == "a6_a3" for c in cells):
        raise HoldoutGuardError("a6_a3 is forbidden from the holdout")


def _git(repo_dir: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=str(repo_dir), stderr=subprocess.STDOUT
        ).decode().strip()
    except subprocess.CalledProcessError as exc:
        detail = exc.output.decode(errors="replace").strip()
        raise HoldoutGuardError(
            f"git {' '.join(args)} failed: {detail}"
        ) from exc


def current_code_commit(repo_dir: Path = REPO_DIR) -> str:
    return _git(repo_dir, "rev-parse", "HEAD")


def _tracked_dirty(repo_dir: Path = REPO_DIR) -> list[str]:
    text = _git(
        repo_dir, "status", "--porcelain", "--untracked-files=no"
    )
    return text.splitlines() if text else []


def _require_selection_gate_ancestor(
    repo_dir: Path = REPO_DIR,
    code_commit: str | None = None,
) -> None:
    code_commit = code_commit or current_code_commit(repo_dir)
    try:
        subprocess.check_call(
            [
                "git", "merge-base", "--is-ancestor",
                SELECTION_GATE_COMMIT, code_commit,
            ],
            cwd=str(repo_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise HoldoutGuardError(
            f"selection-gate commit {SELECTION_GATE_COMMIT} is not an "
            f"ancestor of experiment-code HEAD {code_commit}"
        ) from exc


def _validate_selection_payload(payload: dict, digest: str) -> None:
    """Validate the one-shot rule as well as its selected-arm headline."""
    if digest != EXPECTED_SELECTION_SHA256:
        raise HoldoutGuardError(
            f"selection SHA-256 is {digest}; expected frozen "
            f"{EXPECTED_SELECTION_SHA256}"
        )
    expected = {
        "schema": "a6-arm-selection-v1",
        "selected_arm": "a6_a4",
        "analysis_code_verified": True,
        "n_instances": 12,
        "win_threshold": 9,
        "a6_a3_wins": 2,
    }
    bad = {
        key: (payload.get(key), value)
        for key, value in expected.items()
        if payload.get(key) != value
    }
    if bad:
        raise HoldoutGuardError(
            f"selection artifact fields violate frozen decision: {bad}"
        )
    matched = payload.get("matched")
    if not isinstance(matched, list) or len(matched) != 12:
        raise HoldoutGuardError("selection matched table must contain 12 rows")
    wins = sum(bool(row.get("a6_a3_wins")) for row in matched)
    selected = "a6_a3" if wins >= payload["win_threshold"] else "a6_a4"
    if wins != payload["a6_a3_wins"] or selected != payload["selected_arm"]:
        raise HoldoutGuardError(
            "selection artifact does not reproduce its own frozen rule"
        )
    scoring = payload.get("scoring") or {}
    if scoring.get("budget_exhausted") != 241:
        raise HoldoutGuardError(
            "selection artifact does not preserve budget-exhausted score 241"
        )


def load_committed_selection(repo_dir: Path = REPO_DIR) -> dict:
    """Load the canonical selection only if worktree == HEAD == frozen hash."""
    path = repo_dir / SELECTION_RELATIVE_PATH
    try:
        worktree_bytes = path.read_bytes()
    except OSError as exc:
        raise HoldoutGuardError(
            f"canonical selection artifact missing: {path}"
        ) from exc
    try:
        head_bytes = subprocess.check_output(
            ["git", "show", f"HEAD:{SELECTION_RELATIVE_PATH}"],
            cwd=str(repo_dir), stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        raise HoldoutGuardError(
            "canonical selection artifact is not committed at HEAD"
        ) from exc
    if worktree_bytes != head_bytes:
        raise HoldoutGuardError(
            "working selection artifact differs from the version committed "
            "at HEAD"
        )
    digest = hashlib.sha256(head_bytes).hexdigest()
    try:
        payload = json.loads(head_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HoldoutGuardError("selection artifact is not valid JSON") from exc
    _validate_selection_payload(payload, digest)
    artifact_commit = _git(
        repo_dir, "log", "-1", "--format=%H", "--",
        SELECTION_RELATIVE_PATH,
    )
    if artifact_commit != SELECTION_GATE_COMMIT:
        raise HoldoutGuardError(
            f"selection artifact was last committed at {artifact_commit}; "
            f"expected gate commit {SELECTION_GATE_COMMIT}"
        )
    return {
        "path": SELECTION_RELATIVE_PATH,
        "sha256": digest,
        "artifact_commit": artifact_commit,
        "analysis_code_commit": payload["analysis_code_commit"],
        "analysis_code_verified": payload["analysis_code_verified"],
        "schema": payload["schema"],
        "selected_arm": payload["selected_arm"],
        "a6_a3_wins": payload["a6_a3_wins"],
        "n_instances": payload["n_instances"],
        "win_threshold": payload["win_threshold"],
    }


def require_execution_context(repo_dir: Path = REPO_DIR) -> str:
    """Pin an execution to one clean implementation commit after the gate."""
    code_commit = current_code_commit(repo_dir)
    _require_selection_gate_ancestor(repo_dir, code_commit)
    dirty = _tracked_dirty(repo_dir)
    if dirty:
        raise HoldoutGuardError(
            "tracked tree is dirty; holdout preflight/execution requires one "
            f"committed implementation ({len(dirty)} changed tracked files)"
        )
    expected = os.environ.get("EGGLAB_HOLDOUT_CODE_COMMIT")
    if expected and expected != code_commit:
        raise HoldoutGuardError(
            f"job expected experiment-code commit {expected}, but checkout "
            f"is {code_commit}"
        )
    return code_commit


def _trace_option(inst, first_idx: int, second_idx: int, kind: str):
    """Return an exact zero-charge SOC/time witness, or None if infeasible."""
    first = inst.trips[first_idx]
    second = inst.trips[second_idx]
    depot = inst.depot
    floor = inst.soc_min_kwh
    trace = []
    soc = float(inst.soc0_kwh)

    def spend(stage: str, energy: float, required: float = floor) -> bool:
        nonlocal soc
        soc -= float(energy)
        trace.append({"stage": stage, "soc_kwh": soc,
                      "required_min_kwh": float(required)})
        return soc >= required

    if not spend("after_pull_out", inst.dhk(depot, first.start_loc)):
        return None
    if not spend("after_trip_1", first.energy_kwh):
        return None

    if kind == "dir":
        ready = first.end_min + inst.dhm(first.end_loc, second.start_loc)
        if ready > second.start_min:
            return None
        if not spend(
            "before_trip_2_after_direct_deadhead",
            inst.dhk(first.end_loc, second.start_loc),
        ):
            return None
    elif kind == "dep":
        arrive = first.end_min + inst.dhm(first.end_loc, depot)
        depart = second.start_min - inst.dhm(depot, second.start_loc)
        if arrive > depart:
            return None
        if not spend(
            "at_depot_after_trip_1", inst.dhk(first.end_loc, depot)
        ):
            return None
        trace.append({
            "stage": "after_zero_charge",
            "soc_kwh": soc,
            "required_min_kwh": float(floor),
        })
        if soc > inst.battery_kwh:
            return None
        if not spend(
            "before_trip_2_after_pull_out",
            inst.dhk(depot, second.start_loc),
        ):
            return None
    else:
        raise ValueError(f"unknown arc kind {kind!r}")

    if not spend("after_trip_2", second.energy_kwh):
        return None
    if not spend(
        "after_pull_in", inst.dhk(second.end_loc, depot),
        required=inst.soc_end_kwh,
    ):
        return None
    return {
        "trip_ids": [first.id, second.id],
        "arc_kind": kind,
        "soc_trace_kwh": trace,
    }


def constructive_zero_charge_cover(inst) -> list[dict]:
    """Deterministic perfect pairing with exact time/SOC feasibility."""
    n = len(inst.trips)
    if n % 2:
        raise HoldoutGuardError(
            f"{inst.name}: odd trip count {n}; two-trip perfect cover impossible"
        )
    if n // 2 > inst.max_vehicles:
        raise HoldoutGuardError(
            f"{inst.name}: cover needs {n // 2} vehicles but maximum is "
            f"{inst.max_vehicles}"
        )

    def search(remaining: tuple[int, ...]):
        if not remaining:
            return []
        i = remaining[0]
        for j in remaining[1:]:
            for first, second in ((i, j), (j, i)):
                for kind in ("dir", "dep"):
                    witness = _trace_option(inst, first, second, kind)
                    if witness is None:
                        continue
                    rest = tuple(k for k in remaining if k not in (i, j))
                    suffix = search(rest)
                    if suffix is not None:
                        return [witness, *suffix]
        return None

    pairs = search(tuple(range(n)))
    if pairs is None:
        raise HoldoutGuardError(
            f"{inst.name}: no exact zero-charge two-trip perfect cover"
        )
    sol = Solution(
        sequences=[p["trip_ids"] for p in pairs],
        arc_kinds=[[p["arc_kind"]] for p in pairs],
        charges=[],
        load=[0.0] * inst.n_slots,
        fleet=len(pairs),
    )
    replay_errors = validate_solution(inst, sol, tol_kwh=0.0)
    if replay_errors:
        raise HoldoutGuardError(
            f"{inst.name}: constructive cover failed exact replay: "
            f"{replay_errors}"
        )
    return pairs


def build_feasibility_manifest(selection: dict, code_commit: str) -> dict:
    """Build the deterministic whole-population proof and hash inventory."""
    validate_grid(build_cells())
    physical = []
    physical_hashes = {}
    for seed, n_trips in physical_instances():
        inst = synthetic_instance(seed=seed, n_trips=n_trips)
        pairs = constructive_zero_charge_cover(inst)
        physical_hashes[(seed, n_trips)] = inst.hash()
        physical.append({
            "seed": seed,
            "n_trips": n_trips,
            "instance_hash": inst.hash(),
            "max_vehicles": inst.max_vehicles,
            "required_vehicles": len(pairs),
            "pairs": pairs,
            "replay_ok": True,
        })

    markets = []
    for seed, n_trips, b in market_instances():
        inst = synthetic_instance(seed=seed, n_trips=n_trips)
        market = make_affine_market(inst, shape="duck", b_scale=b)
        if inst.hash() != physical_hashes[(seed, n_trips)]:
            raise HoldoutGuardError(
                f"generator drift while building seed={seed}, n={n_trips}"
            )
        markets.append({
            "seed": seed,
            "n_trips": n_trips,
            "b": b,
            "instance_hash": inst.hash(),
            "market_hash": market_hash(market),
        })

    if len(physical) != EXPECTED_PHYSICAL_INSTANCES:
        raise HoldoutGuardError("physical feasibility manifest is not 32 rows")
    if len(markets) != EXPECTED_INSTANCES:
        raise HoldoutGuardError("market hash manifest is not 64 rows")
    return {
        "schema": PREFLIGHT_SCHEMA,
        "campaign": "a6-holdout",
        "code_commit": code_commit,
        "grid": {
            "methods": list(METHODS),
            "seeds": list(SEEDS),
            "n_trips": list(N_TRIPS),
            "b_scales": list(B_SCALES),
            "physical_instances": EXPECTED_PHYSICAL_INSTANCES,
            "market_instances": EXPECTED_INSTANCES,
            "method_cells": EXPECTED_CELLS,
        },
        "selection": selection,
        "physical_instances": physical,
        "markets": markets,
    }


def write_preflight(out_root: str, selection: dict, code_commit: str) -> dict:
    expected = build_feasibility_manifest(selection, code_commit)
    path = os.path.join(out_root, PREFLIGHT_FILENAME)
    existing = checkpoint.load(path)
    if existing is not None and existing != expected:
        raise HoldoutGuardError(
            f"stale or tampered {path}; it differs from the exact "
            "whole-population feasibility proof for this commit"
        )
    checkpoint.save(path, expected)
    return expected


def load_valid_preflight(
    out_root: str, selection: dict, code_commit: str
) -> tuple[dict, str]:
    path = os.path.join(out_root, PREFLIGHT_FILENAME)
    observed = checkpoint.load(path)
    if observed is None:
        raise HoldoutGuardError(
            f"missing {path}; run --preflight successfully before either "
            "holdout method"
        )
    expected = build_feasibility_manifest(selection, code_commit)
    if observed != expected:
        raise HoldoutGuardError(
            f"{path} is stale, incomplete, or tampered; refusing method run"
        )
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return observed, digest


def _cell_tag(cell) -> str:
    method, seed, n_trips, b = cell
    return f"{method}_s{seed}_n{n_trips}_b{b:g}"


def _commit_cell_provenance(
    out: str,
    cell,
    code_commit: str,
    selection: dict,
    preflight_sha256: str,
    inst,
    market,
) -> None:
    os.makedirs(out, exist_ok=True)
    cells = build_cells()
    payload = {
        "schema": "a6-holdout-cell-provenance-v1",
        "campaign": "a6-holdout",
        "code_commit": code_commit,
        "cell_index": cells.index(cell),
        "cell": {
            "method": cell[0], "seed": cell[1],
            "n_trips": cell[2], "b": cell[3],
        },
        "instance_hash": inst.hash(),
        "market_hash": market_hash(market),
        "selection": selection,
        "preflight_path": PREFLIGHT_FILENAME,
        "preflight_sha256": preflight_sha256,
    }
    path = os.path.join(out, CELL_PROVENANCE_FILENAME)
    existing = checkpoint.load(path)
    if existing is None:
        preexisting = sorted(os.listdir(out))
        if preexisting:
            raise HoldoutGuardError(
                f"unprovenanced preexisting files in holdout cell {out}: "
                f"{preexisting}; refusing to adopt stale evidence"
            )
        checkpoint.save(path, payload)
        return
    if existing != payload:
        raise HoldoutGuardError(
            f"cell provenance mismatch at {path}; refusing stale resume"
        )
    # Identical provenance is already committed.  Downstream transactional
    # checkpoints validate their own instance/market/solver identities.


def run_cell(cell, args, gate: dict | None = None):
    """Run one resume-safe method-cell after the complete population gate."""
    if cell not in build_cells():
        raise HoldoutGuardError(f"cell outside frozen grid: {cell!r}")
    method, seed, n_trips, b = cell
    if method not in METHODS or method == "a6_a3":
        raise HoldoutGuardError(f"forbidden holdout method {method!r}")

    if gate is None:
        selection = load_committed_selection()
        code_commit = require_execution_context()
        if backend() != "GRB":
            raise HoldoutGuardError(
                f"holdout requires GRB; active backend is {backend()!r}"
            )
        _, preflight_sha256 = load_valid_preflight(
            args.out, selection, code_commit
        )
    else:
        selection = gate["selection"]
        code_commit = gate["code_commit"]
        preflight_sha256 = gate["preflight_sha256"]

    tag_dir = _cell_tag(cell)
    out = os.path.join(args.out, tag_dir)
    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    market = make_affine_market(inst, shape="duck", b_scale=b)
    os.makedirs(out, exist_ok=True)
    _commit_cell_provenance(
        out, cell, code_commit, selection, preflight_sha256, inst, market
    )
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=None)
    d_state = _dictator_stage(
        inst, market, out, tag_dir, list(cell), kw,
        experiment="a6-holdout",
    )

    common = dict(
        epsilon=EPSILON,
        budget=BUDGET,
        out_dir=out,
        experiment="a6-holdout",
        solver_kw=kw,
        z_d_ub=d_state["z_d_ub"],
        tol_d=d_state["tol_d"],
    )
    if method == "a2":
        state = certified_cg(inst, market, tag="a2", method="a2", **common)
    else:
        state = certified_cg_a6(
            inst, market, tag="a6_a4", method="a6_a4", **common
        )
    oc = state["outcome"]
    print(
        f"[done] {tag_dir}: {oc['type']} gap={oc['gap']:.6f} "
        f"calls={state['oracle_calls']} "
        f"(clean={oc['oracle_calls_clean']}, "
        f"candidate={oc['oracle_calls_stab']}) "
        f"uplift={oc.get('uplift_interval')}"
    )
    return state


def _runtime_gate(args) -> dict:
    selection = load_committed_selection()
    code_commit = require_execution_context()
    active = backend()
    if active != "GRB":
        raise HoldoutGuardError(
            f"holdout requires GRB; active backend is {active!r}"
        )
    _, preflight_sha256 = load_valid_preflight(
        args.out, selection, code_commit
    )
    return {
        "selection": selection,
        "code_commit": code_commit,
        "preflight_sha256": preflight_sha256,
    }


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/a6_holdout")
    ap.add_argument("--mip-gap", dest="mip_gap", type=float, default=MIP_GAP)
    actions = ap.add_mutually_exclusive_group(required=True)
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--list", action="store_true")
    actions.add_argument("--cell", type=int, default=None)
    actions.add_argument("--all", action="store_true")
    return ap


def main(argv=None) -> int:
    ap = _parser()
    args = ap.parse_args(argv)
    if args.mip_gap != MIP_GAP:
        ap.error(
            f"--mip-gap is frozen at {MIP_GAP:g} for the holdout; "
            "overrides are refused"
        )
    args.out = os.path.abspath(args.out)
    cells = build_cells()
    try:
        validate_grid(cells)
        selection = load_committed_selection()
        if args.list:
            print("selection:", selection)
            for k, c in enumerate(cells):
                print(k, {
                    "method": c[0], "seed": c[1], "n_trips": c[2],
                    "b": c[3], "epsilon": EPSILON, "budget": BUDGET,
                })
            print(f"total: {len(cells)} cells")
            return 0

        code_commit = require_execution_context()
        if args.preflight:
            active = backend()
            if active != "GRB":
                raise HoldoutGuardError(
                    f"holdout preflight/submission requires GRB; active "
                    f"backend is {active!r}"
                )
            manifest = write_preflight(args.out, selection, code_commit)
            print(
                f"[preflight] PASS: {len(manifest['physical_instances'])} "
                "physical instances have exact zero-charge covers; "
                f"{len(manifest['markets'])} market hashes recorded; "
                f"wrote {os.path.join(args.out, PREFLIGHT_FILENAME)}"
            )
            return 0

        if args.cell is not None and not (0 <= args.cell < len(cells)):
            ap.error(f"--cell must be in 0..{len(cells) - 1}")
        gate = _runtime_gate(args)
        if args.cell is not None:
            run_cell(cells[args.cell], args, gate=gate)
        else:
            for cell in cells:
                run_cell(cell, args, gate=gate)
        return 0
    except HoldoutGuardError as exc:
        print(f"[REFUSED] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
