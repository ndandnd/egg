"""B3 internal-uplift factor pilot: frozen binding, enumeration, guards.

This module is the single source of truth that the launcher-ready B3
factor pilot (driver, cluster launcher, exact-count audit, and
preregistered analyzer) all import.  It implements, exactly, Sections 2,
3, 5, 6, and 7 of ``doc/B3_FACTOR_PILOT_SPEC_DRAFT.md`` for the
*development* grid:

- exactly 60 A2 + matched-dictator cells = 5 frozen settings x seeds
  {0, 11, 15} x n {8, 12} x b {0.01, 0.05};
- every run identity is bound to the committed, FROZEN factor-screen
  artifact (its SHA-256, disposition, selected levels), the exact
  ``Instance.hash()`` of all 30 unique physical setting-instances, and
  the frozen selected levels;
- the scientific-boundary refusals: no A6 method or A6 code path, no seed
  >= 16 (the reserved 16-31 holdout band and the frozen 32-37
  confirmation band), no factor drift from the frozen levels, no wrong
  counts, no non-Gurobi solver fallback, and no dirty tracked tree.

It launches nothing and reads no A6 outcome.  The heavy solver imports
(dictator + certified CG) live in the driver, not here, so that the
audit and analyzer can bind provenance without importing an optimizer.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Reuse the frozen screen's constants and pure instance builder verbatim so
# that the pilot cannot silently diverge from the screen it is bound to.
from experiments.b3_factor_screen import (
    BASELINE_BATTERY_KWH,
    BASELINE_POWER_KW,
    FROZEN_BURNED_SEEDS,
    GENERATOR_HELD_FIXED_ARGUMENTS,
    GENERATOR_RELPATH,
    N_TRIPS,
    SETTING_ORDER,
    SPEC_RELPATH,
    build_instance,
    sha256_file,
)

SCHEMA = "b3-factor-pilot-v1"
RUN_MANIFEST_SCHEMA = "b3-factor-pilot-run-v1"
CELL_IDENTITY_SCHEMA = "b3-factor-pilot-cell-v1"
RUN_MANIFEST_FILENAME = "MANIFEST.json"
JOB_FILENAME = "JOB.json"
CELL_IDENTITY_FILENAME = "identity.json"
MIP_GAP_DEFAULT = 1e-6
REPO_ROOT = Path(__file__).resolve().parents[2]

# --- frozen design (spec Sections 2-3, 5) ---------------------------------
SEEDS = FROZEN_BURNED_SEEDS            # (0, 11, 15) — development only
B_SCALES = (0.01, 0.05)
BASELINE_SETTING = "S0_baseline"
EPSILON = 1e-2
BUDGET = 240
TOL_D = 1e-2
METHOD = "a2"                          # A2 only; no A6 method or code path
TAU_DELTA = 0.04                       # 2 * (tol_d + epsilon) SEK (spec 6)

RESERVED_HOLDOUT_BAND = tuple(range(16, 32))     # never generated (spec 3)
CONFIRMATION_SEEDS = (32, 33, 34, 35, 36, 37)    # frozen; NOT development

# --- the committed, FROZEN factor-screen artifact this pilot binds to -----
# (result/b3_factor_screen/20260820T105318Z, merged in PR #34).  The record
# SHA-256 is the MANIFEST's recorded output hash; the selected levels are the
# screen's FROZEN disposition.  Both are asserted at load time.
FROZEN_SCREEN_RELDIR = "result/b3_factor_screen/20260820T105318Z"
FROZEN_SCREEN_RECORD_SHA256 = (
    "27c04d82bc88b62eed84394569b3ab8a35238a3a57c9cf4ba6463fb85f7bf603")
FROZEN_SELECTED_LEVELS = {
    "S1_batt_low": 45.0,
    "S2_batt_high": 90.0,
    "S3_pow_low": 75.0,
    "S4_pow_high": 300.0,
}
SCREEN_SCHEMA = "b3-factor-screen-v1"

# expected exact counts (spec Section 3)
N_SETTINGS = 5
N_PHYSICAL_INSTANCES = 30   # settings x seeds x n
N_CELLS = 60                # x b
N_BASELINE_CELLS = 12       # S0 x seeds x n x b
N_MATCHED_CONTRASTS = 48    # (seed,n,b) x {S1,S2,S3,S4}


class B3PilotError(RuntimeError):
    """The pilot cannot proceed without weakening its frozen contract."""


# --------------------------------------------------------------------------
# frozen level -> generator parameters
# --------------------------------------------------------------------------
def setting_params(setting: str) -> tuple[float, float]:
    """(battery_kwh, charge_power_kw) for a setting at the FROZEN levels."""
    if setting not in SETTING_ORDER:
        raise B3PilotError(f"unknown setting {setting!r}")
    battery, power = BASELINE_BATTERY_KWH, BASELINE_POWER_KW
    if setting in ("S1_batt_low", "S2_batt_high"):
        battery = FROZEN_SELECTED_LEVELS[setting]
    elif setting in ("S3_pow_low", "S4_pow_high"):
        power = FROZEN_SELECTED_LEVELS[setting]
    return battery, power


# --------------------------------------------------------------------------
# scientific-boundary refusals (spec Sections 3, 11)
# --------------------------------------------------------------------------
def assert_development_seed(seed: int) -> None:
    """Only the burned development seeds may ever be generated."""
    if seed in CONFIRMATION_SEEDS:
        raise B3PilotError(
            f"seed {seed} is a frozen confirmation seed (32-37); the "
            "development pilot must never generate it")
    if seed in RESERVED_HOLDOUT_BAND or seed >= 16:
        raise B3PilotError(
            f"seed {seed} is in a reserved band (16-31 holdout, 32-37 "
            "confirmation); the development pilot must never generate it")
    if seed not in FROZEN_BURNED_SEEDS:
        raise B3PilotError(
            f"seed {seed} is not a burned development seed {FROZEN_BURNED_SEEDS}")


def assert_no_a6(*tokens: object) -> None:
    """Refuse any A6 method label or A6 code path (scientific boundary)."""
    for token in tokens:
        text = str(token)
        low = text.lower()
        if low == "a6" or low.startswith("a6_") or low.startswith("a6-"):
            raise B3PilotError(f"refusing A6 method/label: {text!r}")
        for part in Path(text).parts if os.sep in text or "/" in text else ():
            p = part.lower()
            if p.startswith("a6") or "a6_" in p:
                raise B3PilotError(f"refusing A6 path (scientific boundary): {text}")


def assert_method_a2(method: str) -> None:
    assert_no_a6(method)
    if method != METHOD:
        raise B3PilotError(
            f"method {method!r} is not A2; the B3 factor pilot is A2-only")


def assert_grb_backend() -> None:
    """Gurobi-only: refuse a non-GRB solver fallback before any solve."""
    from egglab.solver import backend
    b = backend()
    if b != "GRB":
        raise B3PilotError(
            f"solver backend is {b!r}, not Gurobi (GRB); the B3 factor pilot "
            "refuses a non-GRB fallback. Set EGGLAB_REQUIRE_GRB=1 and run "
            "under cluster/unicorn_env.sh on Unicorn.")


def assert_clean_tracked_tree() -> None:
    """Refuse execution against a dirty tracked tree (spec Section 7)."""
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    tracked = [ln for ln in dirty.splitlines() if not ln.startswith("??")]
    if tracked:
        raise B3PilotError(
            "working tree has tracked modifications; commit before running "
            f"the pilot ({len(tracked)} changed tracked path(s))")


def refuse_existing_dir(path: str | os.PathLike) -> None:
    if Path(path).exists():
        raise B3PilotError(f"refusing existing output directory: {path}")


# --------------------------------------------------------------------------
# frozen screen artifact loading and binding (spec Section 7)
# --------------------------------------------------------------------------
def load_frozen_screen(screen_dir: str | os.PathLike | None = None) -> dict:
    """Load and fully validate the committed FROZEN factor-screen artifact,
    returning the record, manifest, canonical SHA, and the
    (setting, seed, n) -> Instance.hash() map that binds every run.

    Every check here is a *binding* check: a mutated screen record, a
    non-FROZEN disposition, drifted selected levels, or a schema change
    fails closed and no cell can be enumerated.
    """
    base = Path(screen_dir) if screen_dir is not None \
        else REPO_ROOT / FROZEN_SCREEN_RELDIR
    record_path = base / "SCREEN_RECORD.json"
    manifest_path = base / "MANIFEST.json"
    if not record_path.is_file() or not manifest_path.is_file():
        raise B3PilotError(
            f"frozen screen artifact incomplete under {base}")

    record_bytes = record_path.read_bytes()
    record_sha = hashlib.sha256(record_bytes).hexdigest()
    manifest = json.loads(manifest_path.read_bytes())
    record = json.loads(record_bytes)

    if screen_dir is None and record_sha != FROZEN_SCREEN_RECORD_SHA256:
        raise B3PilotError(
            f"screen record SHA-256 {record_sha} != frozen "
            f"{FROZEN_SCREEN_RECORD_SHA256}; refusing drifted screen")
    manifest_sha = ((manifest.get("outputs") or {}).get("SCREEN_RECORD.json"))
    if manifest_sha != record_sha:
        raise B3PilotError(
            f"MANIFEST output hash {manifest_sha} != actual record SHA "
            f"{record_sha}; screen artifact was mutated")
    if record.get("schema") != SCREEN_SCHEMA \
            or manifest.get("schema") != SCREEN_SCHEMA:
        raise B3PilotError("screen artifact schema mismatch")
    disposition = record.get("disposition") or {}
    if disposition.get("state") != "FROZEN":
        raise B3PilotError(
            f"screen disposition is {disposition.get('state')!r}, not FROZEN; "
            "the pilot may only bind to a frozen screen")
    if record.get("selected_levels") != FROZEN_SELECTED_LEVELS \
            or disposition.get("levels") != FROZEN_SELECTED_LEVELS:
        raise B3PilotError(
            f"screen selected levels {record.get('selected_levels')} != frozen "
            f"{FROZEN_SELECTED_LEVELS}; factor drift refused")

    setting_instances = record.get("setting_instances") or []
    if len(setting_instances) != N_PHYSICAL_INSTANCES:
        raise B3PilotError(
            f"screen lists {len(setting_instances)} setting-instances, "
            f"expected {N_PHYSICAL_INSTANCES}")
    hash_map: dict[tuple[str, int, int], str] = {}
    for si in setting_instances:
        key = (si["setting"], si["seed"], si["n_trips"])
        if key in hash_map:
            raise B3PilotError(f"duplicate setting-instance {key} in screen")
        hash_map[key] = si["instance_hash"]

    return {
        "dir": str(base),
        "record": record,
        "manifest": manifest,
        "record_sha256": record_sha,
        "spec_sha256": (record.get("spec") or {}).get("sha256"),
        "generator_sha256": (record.get("design", {}).get("generator", {})
                             .get("sha256")),
        "instance_hashes": hash_map,
    }


# --------------------------------------------------------------------------
# exact 60-cell enumeration (spec Section 3), deterministic order
# --------------------------------------------------------------------------
def build_cells() -> list[dict]:
    """The 60 A2 method-cells in a fixed, stable order.

    Cell index is the Slurm array index; order is settings (frozen
    Section-2 order) x seeds asc x n asc x b asc.
    """
    cells = []
    for setting in SETTING_ORDER:
        battery, power = setting_params(setting)
        for seed in SEEDS:
            for n in N_TRIPS:
                for b in B_SCALES:
                    cells.append({
                        "setting": setting, "seed": seed, "n_trips": n,
                        "b": b, "battery_kwh": battery,
                        "charge_power_kw": power,
                        "tag": cell_tag(setting, seed, n, b),
                    })
    if len(cells) != N_CELLS:
        raise B3PilotError(
            f"enumerated {len(cells)} cells, expected exactly {N_CELLS}")
    return cells


def cell_tag(setting: str, seed: int, n_trips: int, b: float) -> str:
    return f"{setting}_s{seed}_n{n_trips}_b{b:g}"


def make_cell_instance(cell: dict):
    """Build one cell's physical Instance at the FROZEN levels, refusing any
    non-development seed first."""
    assert_development_seed(cell["seed"])
    battery, power = setting_params(cell["setting"])
    if (battery, power) != (cell["battery_kwh"], cell["charge_power_kw"]):
        raise B3PilotError(
            f"factor drift for {cell['setting']}: cell carries "
            f"({cell['battery_kwh']}, {cell['charge_power_kw']}) but frozen "
            f"levels give ({battery}, {power})")
    return build_instance(cell["seed"], cell["n_trips"], battery, power)


def bind_cell_to_screen(cell: dict, screen: dict):
    """Build the cell instance and assert its Instance.hash() matches the
    frozen screen artifact for (setting, seed, n).  This single check binds
    the run identity to the artifact, the selected levels, AND the hashes;
    any factor drift changes the hash and fails closed."""
    inst = make_cell_instance(cell)
    key = (cell["setting"], cell["seed"], cell["n_trips"])
    expected = screen["instance_hashes"].get(key)
    if expected is None:
        raise B3PilotError(f"screen has no instance hash for {key}")
    if inst.hash() != expected:
        raise B3PilotError(
            f"instance-hash drift for {key}: built {inst.hash()} != frozen "
            f"screen {expected}; factor levels or generator changed")
    return inst


def assert_no_factor_drift(screen: dict) -> None:
    """Rebuild all 30 physical instances at the frozen levels and assert each
    hash matches the frozen screen (the full factor-drift gate)."""
    seen = 0
    for setting in SETTING_ORDER:
        for seed in SEEDS:
            for n in N_TRIPS:
                bind_cell_to_screen(
                    {"setting": setting, "seed": seed, "n_trips": n,
                     "b": B_SCALES[0], **dict(zip(
                         ("battery_kwh", "charge_power_kw"),
                         setting_params(setting)))},
                    screen)
                seen += 1
    if seen != N_PHYSICAL_INSTANCES:
        raise B3PilotError(
            f"checked {seen} physical instances, expected "
            f"{N_PHYSICAL_INSTANCES}")


def cell_identity(cell: dict, screen: dict, *, market_hash: str,
                  run_manifest_sha256: str, run_commit: str,
                  mip_gap: float, backend_name: str) -> dict:
    """The frozen provenance every cell's sidecar carries, binding the cell to
    the frozen screen AND to the specific run (manifest SHA + code commit +
    solver identity + market hash)."""
    key = (cell["setting"], cell["seed"], cell["n_trips"])
    return {
        "schema": CELL_IDENTITY_SCHEMA,
        "setting": cell["setting"],
        "seed": cell["seed"],
        "n_trips": cell["n_trips"],
        "b": cell["b"],
        "battery_kwh": cell["battery_kwh"],
        "charge_power_kw": cell["charge_power_kw"],
        "method": METHOD,
        "epsilon": EPSILON,
        "budget": BUDGET,
        "tol_d": TOL_D,
        "screen_record_sha256": screen["record_sha256"],
        "screen_selected_levels": dict(FROZEN_SELECTED_LEVELS),
        "instance_hash": screen["instance_hashes"][key],
        "market_hash": market_hash,
        "run_manifest_sha256": run_manifest_sha256,
        "run_commit": run_commit,
        "solver": {"backend": backend_name, "mip_gap": mip_gap},
    }


def canonical_cell_identity_bytes(identity: dict) -> bytes:
    return (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode()


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def verify_or_write_cell_identity(cell_dir: str | os.PathLike,
                                  identity: dict) -> None:
    """Write the cell-identity sidecar on first run; on resume, refuse if ANY
    bound field (code commit, manifest SHA, screen SHA, setting, factor level,
    instance hash, market hash, or solver identity) differs."""
    path = Path(cell_dir) / CELL_IDENTITY_FILENAME
    payload = canonical_cell_identity_bytes(identity)
    if path.exists():
        existing = path.read_bytes()
        if existing != payload:
            try:
                prior = json.loads(existing)
            except ValueError:
                prior = {}
            diffs = sorted(
                k for k in set(identity) | set(prior)
                if prior.get(k) != identity.get(k))
            raise B3PilotError(
                f"cell identity mismatch on resume (fields: {diffs}); refusing "
                "to resume a cell under a different run/code/screen identity — "
                "delete the cell directory to restart")
        return
    _atomic_write_bytes(path, payload)


def counts() -> dict:
    return {
        "settings": N_SETTINGS,
        "physical_instances": N_PHYSICAL_INSTANCES,
        "cells": N_CELLS,
        "baseline_cells": N_BASELINE_CELLS,
        "dictators": N_CELLS,
        "matched_contrasts": N_MATCHED_CONTRASTS,
    }


# --------------------------------------------------------------------------
# git provenance
# --------------------------------------------------------------------------
def git_head_commit() -> str:
    """The full 40-char lowercase HEAD commit, pinned to the repo root."""
    out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    if len(out) != 40 or not all(c in "0123456789abcdef" for c in out):
        raise B3PilotError(f"HEAD did not resolve to a 40-char SHA: {out!r}")
    return out


# --------------------------------------------------------------------------
# Section-7 run manifest (canonical, deterministic, SHA-bound)
# --------------------------------------------------------------------------
def _recompute_hashes(screen: dict) -> tuple[dict, list]:
    """Rebuild every physical instance and market, binding each instance hash
    to the frozen screen; return (instance_hashes, market_rows)."""
    from egglab.market import make_affine_market
    from egglab.b2a2 import market_hash

    instance_hashes: dict[str, str] = {}
    market_rows: list[dict] = []
    for cell in build_cells():
        inst = bind_cell_to_screen(cell, screen)   # rebuild + hash-check
        market = make_affine_market(inst, shape="duck", b_scale=cell["b"])
        ihash = inst.hash()
        mhash = market_hash(market)
        ikey = f"{cell['setting']}|{cell['seed']}|{cell['n_trips']}"
        instance_hashes.setdefault(ikey, ihash)
        market_rows.append({
            "setting": cell["setting"], "seed": cell["seed"],
            "n_trips": cell["n_trips"], "b": cell["b"],
            "instance_hash": ihash, "market_hash": mhash,
        })
    return instance_hashes, market_rows


def _assert_hash_invariants(instance_hashes: dict, market_rows: list,
                            screen: dict) -> None:
    """Spec Section 7: each instance occurs exactly twice; the two b-markets of
    a physical instance differ; matched cells (same seed,n,b) share a market;
    baseline S0 identities match the frozen screen."""
    from collections import Counter
    inst_counts = Counter(r["instance_hash"] for r in market_rows)
    if len(instance_hashes) != N_PHYSICAL_INSTANCES:
        raise B3PilotError(
            f"expected {N_PHYSICAL_INSTANCES} distinct instances, got "
            f"{len(instance_hashes)}")
    for ihash, n in inst_counts.items():
        if n != 2:
            raise B3PilotError(
                f"instance {ihash} occurs {n} times, expected exactly twice")
    # b-markets differ per physical instance
    by_phys: dict[tuple, dict] = {}
    for r in market_rows:
        by_phys.setdefault((r["setting"], r["seed"], r["n_trips"]), {})[
            r["b"]] = r["market_hash"]
    for key, bmap in by_phys.items():
        if len(set(bmap.values())) != len(bmap):
            raise B3PilotError(
                f"{key}: market hashes do not differ across b ({bmap})")
    # matched cells (same seed,n,b) share the market across settings
    by_market_cell: dict[tuple, set] = {}
    for r in market_rows:
        by_market_cell.setdefault(
            (r["seed"], r["n_trips"], r["b"]), set()).add(r["market_hash"])
    for key, mset in by_market_cell.items():
        if len(mset) != 1:
            raise B3PilotError(
                f"market cell {key}: settings disagree on market hash ({mset})")
    # baseline S0 identities match the frozen screen
    for seed in SEEDS:
        for n in N_TRIPS:
            ikey = f"{BASELINE_SETTING}|{seed}|{n}"
            if instance_hashes.get(ikey) != screen["instance_hashes"][
                    (BASELINE_SETTING, seed, n)]:
                raise B3PilotError(
                    f"baseline instance {ikey} differs from the frozen screen")


def build_run_manifest(screen: dict, *, git_commit: str, backend_name: str,
                       mip_gap: float = MIP_GAP_DEFAULT) -> dict:
    """The canonical Section-7 run manifest (pure function of the frozen
    screen, code commit, and solver identity).  Raises on any hash invariant
    failure so a malformed design can never be submitted."""
    if len(git_commit) != 40 or not all(
            c in "0123456789abcdef" for c in git_commit):
        raise B3PilotError("run manifest requires the full 40-char commit SHA")
    if backend_name != "GRB":
        raise B3PilotError(
            f"run manifest backend {backend_name!r} is not GRB (Gurobi-only)")
    instance_hashes, market_rows = _recompute_hashes(screen)
    _assert_hash_invariants(instance_hashes, market_rows, screen)
    return {
        "schema": RUN_MANIFEST_SCHEMA,
        "run_commit": git_commit,
        "spec": {"path": SPEC_RELPATH,
                 "sha256": sha256_file(REPO_ROOT / SPEC_RELPATH)},
        "screen": {
            "dir": FROZEN_SCREEN_RELDIR,
            "record_sha256": screen["record_sha256"],
            "selected_levels": dict(FROZEN_SELECTED_LEVELS),
        },
        "generator": {
            "path": GENERATOR_RELPATH,
            "sha256": screen.get("generator_sha256"),
            "held_fixed_arguments": dict(GENERATOR_HELD_FIXED_ARGUMENTS),
            "baseline": {"battery_kwh": BASELINE_BATTERY_KWH,
                         "charge_power_kw": BASELINE_POWER_KW},
        },
        "grid": {
            "settings": list(SETTING_ORDER),
            "seeds": list(SEEDS),
            "n_trips": list(N_TRIPS),
            "b_scales": list(B_SCALES),
        },
        "tolerances": {
            "epsilon": EPSILON, "budget": BUDGET, "tol_d": TOL_D,
            "tau_delta": TAU_DELTA,
        },
        "solver": {
            "backend": backend_name, "method": METHOD, "mip_gap": mip_gap,
        },
        "load_reconstruction": _load_reconstruction_policy(),
        "counts": counts(),
        "instance_hashes": instance_hashes,
        "market_hashes": market_rows,
    }


def _load_reconstruction_policy() -> dict:
    from egglab.evsp import (LOAD_RECONSTRUCTION_POLICY_VERSION,
                             REPLAY_TOL_KWH)
    return {"policy_version": LOAD_RECONSTRUCTION_POLICY_VERSION,
            "tolerance_kwh": REPLAY_TOL_KWH}


def canonical_manifest_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()


def run_manifest_sha256(manifest: dict) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def market_hash_by_cell(manifest: dict) -> dict:
    return {(r["setting"], r["seed"], r["n_trips"], r["b"]): r["market_hash"]
            for r in manifest.get("market_hashes", [])}


def write_run_manifest(out_dir: str | os.PathLike, manifest: dict) -> str:
    """Atomically write the canonical run manifest before submission.  If a
    manifest already exists it must be byte-identical (idempotent re-emit);
    otherwise refuse (a different manifest means a different design)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / RUN_MANIFEST_FILENAME
    payload = canonical_manifest_bytes(manifest)
    if path.exists():
        if path.read_bytes() != payload:
            raise B3PilotError(
                f"refusing to overwrite a different run manifest at {path}")
        return str(path)
    _atomic_write_bytes(path, payload)
    return str(path)


def load_run_manifest(out_dir: str | os.PathLike) -> dict:
    """Load and SHA-validate the run manifest; return {manifest, sha256}."""
    path = Path(out_dir) / RUN_MANIFEST_FILENAME
    if not path.is_file():
        raise B3PilotError(f"run manifest missing: {path}")
    manifest = json.loads(path.read_bytes())
    sha = run_manifest_sha256(manifest)
    if manifest.get("schema") != RUN_MANIFEST_SCHEMA:
        raise B3PilotError("run manifest schema mismatch")
    return {"manifest": manifest, "sha256": sha}


def bind_job_id(out_dir: str | os.PathLike, job_id: str) -> str:
    """Atomically record the submitted Slurm job id, referencing the manifest
    SHA and run commit, immediately after sbatch — closing the post-sbatch
    provenance gap.  Refuses to overwrite an existing binding."""
    loaded = load_run_manifest(out_dir)
    manifest = loaded["manifest"]
    path = Path(out_dir) / JOB_FILENAME
    if path.exists():
        raise B3PilotError(f"job binding already exists: {path}")
    import datetime
    doc = {
        "schema": "b3-factor-pilot-job-v1",
        "job_id": str(job_id),
        "run_manifest_sha256": loaded["sha256"],
        "run_commit": manifest["run_commit"],
        "submitted_utc": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _atomic_write_bytes(
        path, (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode())
    return str(path)
