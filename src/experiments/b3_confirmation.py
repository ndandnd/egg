"""B3 fresh-seed confirmation stage: GO-gated, outcome-blind bindings.

Single source of truth shared by the confirmation driver, launcher,
audit, and tests.  It mirrors the pilot machinery in
``experiments.b3_factor_pilot`` (run manifest over exact bytes, cell
identity sidecar, held-submit job binding, fresh-run-dir refusal) but
for the FROZEN confirmation population of ``doc/B3_FACTOR_PILOT_SPEC_DRAFT.md``
Section 8:

    seeds {32,33,34,35,36,37}; S0_baseline versus the SELECTED factor
    (an input, never hardcoded); n {8,12}; b {0.01,0.05};
    24 matched contrasts = 48 method-cells; method A2; epsilon 0.01,
    tol_d 0.01, budget 240; Gurobi only on the cluster.

The confirmation is authorized ONLY by a committed GO selection artifact
(``SELECTION.json``) that structurally validates: recomputing hashes,
state == GO, the named factor, an analyzer commit that is an ancestor of
HEAD, the frozen screen SHA and pilot spec hash, the frozen pilot
raw-tree anchor, the boundary disclosure (a knife-edge decision refuses),
and that it is not INVALID/HALT-derived.  There is NO flag, environment
variable, or test hook that bypasses the gate: a test must build a
complete, internally-consistent fake GO artifact instead.

This module reads NOTHING under ``runs/b3_factor_pilot`` and never infers
which factor wins; the winning factor is supplied by the artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
from egglab.instance import synthetic_instance
from experiments.b3_factor_screen import GENERATOR_HELD_FIXED_ARGUMENTS

SCHEMA = "b3-confirmation-v1"
RUN_MANIFEST_SCHEMA = "b3-confirmation-run-v1"
CELL_IDENTITY_SCHEMA = "b3-confirmation-cell-v1"
SELECTION_SCHEMA = "b3-confirmation-selection-v1"
RUN_MANIFEST_FILENAME = "MANIFEST.json"
JOB_FILENAME = "JOB.json"
CELL_IDENTITY_FILENAME = "identity.json"
JOB_SCHEMA = "b3-confirmation-job-v1"
REPO_ROOT = bp.REPO_ROOT
SPEC_RELPATH = bp.SPEC_RELPATH
MIP_GAP_DEFAULT = bp.MIP_GAP_DEFAULT

# --- frozen confirmation population (spec Section 8) -----------------------
CONFIRMATION_SEEDS = (32, 33, 34, 35, 36, 37)
N_TRIPS = bp.N_TRIPS
B_SCALES = bp.B_SCALES
BASELINE_SETTING = bp.BASELINE_SETTING
METHOD = "a2"
EPSILON = bp.EPSILON
BUDGET = bp.BUDGET
TOL_D = bp.TOL_D
TAU_DELTA = bp.TAU_DELTA                 # 0.04 SEK
CONFIRMATION_GATE_MIN = 18              # >= 18/24 direction-consistent
CONFIRMATION_GATE_OF = 24
PILOT_COUNT_GATE = 9                    # the pilot's own 9/12 gate (echoed)
N_PHYSICAL_INSTANCES = 24              # settings(2) x seeds(6) x n(2)
N_CELLS = 48                           # x b(2)
N_MATCHED_CONTRASTS = 24              # (seed,n,b) x factor-vs-baseline

# reserved / forbidden seed bands (nothing outside 32-37 may be generated)
DEVELOPMENT_SEEDS = (0, 11, 15)
HOLDOUT_BAND = tuple(range(16, 32))

# frozen direction signs (spec Section 2 table) — used ONLY to validate the
# sign the artifact carries; the authoritative value is read from the artifact
DIRECTION_SIGN = {
    "S1_batt_low": +1,
    "S2_batt_high": -1,
    "S3_pow_low": +1,
    "S4_pow_high": -1,
}

# frozen provenance anchors the selection artifact must match
FROZEN_SCREEN_RECORD_SHA256 = bp.FROZEN_SCREEN_RECORD_SHA256
FROZEN_SPEC_SHA256 = (
    "150f4b32220b13866d2872e4bb8a29bfcc5137cca18ebb55c8ddf3d163d4275f")
# the pilot's frozen pre-analysis raw-tree anchor (Task-2 amendment 1); these
# are validated against, NEVER recomputed from runs/b3_factor_pilot
FROZEN_PILOT_RAW_TREE = {
    "tree_sha256":
        "efc5ca31dcddb21166f6a5da2cf60b4961706c99edf9dbda882f87a18a88ace4",
    "file_count": 363,
    "directory_count": 60,
    "total_bytes": 17385781,
}

PILOT_RUNS_RELDIR = "runs/b3_factor_pilot"


class B3ConfirmationError(RuntimeError):
    """The confirmation stage cannot proceed without weakening its contract."""


# --------------------------------------------------------------------------
# boundary refusals
# --------------------------------------------------------------------------
def assert_confirmation_seed(seed: int) -> None:
    if seed in DEVELOPMENT_SEEDS:
        raise B3ConfirmationError(
            f"seed {seed} is a development seed (0,11,15); the confirmation "
            "stage must never generate it")
    if seed in HOLDOUT_BAND:
        raise B3ConfirmationError(
            f"seed {seed} is in the reserved A6 holdout band 16-31; refusing")
    if seed not in CONFIRMATION_SEEDS:
        raise B3ConfirmationError(
            f"seed {seed} is not a frozen confirmation seed "
            f"{CONFIRMATION_SEEDS}")


def assert_no_a6(*tokens: object) -> None:
    for token in tokens:
        text = str(token)
        low = text.lower()
        if low == "a6" or low.startswith("a6_") or low.startswith("a6-"):
            raise B3ConfirmationError(f"refusing A6 method/label: {text!r}")
        parts = Path(text).parts if (os.sep in text or "/" in text) else ()
        for part in parts:
            p = part.lower()
            if p.startswith("a6") or "a6_" in p:
                raise B3ConfirmationError(
                    f"refusing A6 path (scientific boundary): {text}")


def refuse_pilot_runs_path(*paths: str | os.PathLike) -> None:
    """Outcome blindness: no confirmation path may resolve into the pilot
    outcome tree ``runs/b3_factor_pilot`` (which must never be read)."""
    pilot = (REPO_ROOT / PILOT_RUNS_RELDIR).resolve()
    for path in paths:
        if path is None:
            continue
        resolved = Path(path).resolve()
        if resolved == pilot or pilot in resolved.parents \
                or resolved in pilot.parents:
            raise B3ConfirmationError(
                f"refusing a path that overlaps the pilot outcome tree "
                f"{PILOT_RUNS_RELDIR}: {resolved}")


def assert_method_a2(method: str) -> None:
    assert_no_a6(method)
    if method != METHOD:
        raise B3ConfirmationError(
            f"method {method!r} is not A2; the confirmation stage is A2-only")


def assert_grb_backend() -> None:
    try:
        bp.assert_grb_backend()
    except bp.B3PilotError as exc:
        raise B3ConfirmationError(str(exc)) from exc


def assert_clean_tracked_tree() -> None:
    try:
        bp.assert_clean_tracked_tree()
    except bp.B3PilotError as exc:
        raise B3ConfirmationError(str(exc)) from exc


def assert_fresh_run_dir(out_dir) -> None:
    try:
        bp.assert_fresh_run_dir(out_dir)
    except bp.B3PilotError as exc:
        raise B3ConfirmationError(str(exc)) from exc


def git_head_commit() -> str:
    return bp.git_head_commit()


# --------------------------------------------------------------------------
# instance construction (confirmation seeds only)
# --------------------------------------------------------------------------
def setting_params(setting: str) -> tuple[float, float]:
    return bp.setting_params(setting)


def selected_factor_level(factor: str) -> float:
    if factor not in bp.FROZEN_SELECTED_LEVELS:
        raise B3ConfirmationError(f"factor {factor!r} has no frozen level")
    return bp.FROZEN_SELECTED_LEVELS[factor]


def build_confirmation_instance(seed: int, n_trips: int, battery_kwh: float,
                                charge_power_kw: float):
    """Fresh-seed instance built with the SAME frozen held-fixed generator
    arguments as the pilot/screen, but from the confirmation seed band."""
    assert_confirmation_seed(seed)
    g = GENERATOR_HELD_FIXED_ARGUMENTS
    return synthetic_instance(
        seed=seed, n_trips=n_trips, battery_kwh=battery_kwh,
        charge_power_kw=charge_power_kw,
        soc_min_frac=g["soc_min_frac"], soc_end_frac=g["soc_end_frac"],
        trip_energy_range=tuple(g["trip_energy_range"]),
        day_start_min=g["day_start_min"], day_end_min=g["day_end_min"],
        max_vehicles=g["max_vehicles"], name=g["name"])


# --------------------------------------------------------------------------
# GO gate: load + fully validate the committed selection artifact
# --------------------------------------------------------------------------
def _is_hex64(value) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def _require(doc: dict, key: str, label: str):
    if not isinstance(doc, dict) or key not in doc:
        raise B3ConfirmationError(
            f"selection artifact missing required field: {label}")
    return doc[key]


def _commit_is_ancestor(commit: str, label: str) -> None:
    if (not isinstance(commit, str) or len(commit) != 40
            or not all(c in "0123456789abcdef" for c in commit)
            or commit == "0" * 40):
        raise B3ConfirmationError(
            f"{label}: commit {commit!r} is not a real 40-hex commit")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3ConfirmationError(
            f"{label}: commit {commit} does not resolve") from exc
    if resolved != commit:
        raise B3ConfirmationError(f"{label}: commit resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B3ConfirmationError(
            f"{label}: commit {commit} is not an ancestor of HEAD")


def load_selection_artifact(path: str | os.PathLike, *,
                            verify_commit: bool = True) -> dict:
    """Structurally validate a committed GO selection artifact and return
    {document, sha256, selected_factor, direction_sign}.  Every failure is a
    hard refusal that names the field; there is no bypass."""
    p = Path(path)
    refuse_pilot_runs_path(p)
    if not p.is_file() or p.is_symlink():
        raise B3ConfirmationError(f"selection artifact missing: {p}")
    raw = p.read_bytes()
    doc = json.loads(raw)
    artifact_sha = hashlib.sha256(raw).hexdigest()

    if _require(doc, "schema", "schema") != SELECTION_SCHEMA:
        raise B3ConfirmationError(
            f"selection schema {doc.get('schema')!r} != {SELECTION_SCHEMA!r}")
    state = _require(doc, "state", "state")
    if state != "GO":
        raise B3ConfirmationError(
            f"selection state is {state!r}, not GO; confirmation is not "
            "authorized (INVALID/HALT, NO-GO, UNDER-RESOLVED refuse)")

    factor = _require(doc, "selected_factor", "selected_factor")
    if factor not in bp.FROZEN_SELECTED_LEVELS:
        raise B3ConfirmationError(
            f"selected_factor {factor!r} is not a real factor with a frozen "
            "level")
    # direction sign is READ from the artifact, then validated against the
    # frozen spec table (a mismatch is tampering)
    direction = _require(doc, "direction_sign", "direction_sign")
    if direction != DIRECTION_SIGN[factor]:
        raise B3ConfirmationError(
            f"direction_sign {direction!r} disagrees with the frozen sign "
            f"{DIRECTION_SIGN[factor]} for {factor}")
    level = _require(doc, "frozen_factor_level", "frozen_factor_level")
    if level != bp.FROZEN_SELECTED_LEVELS[factor]:
        raise B3ConfirmationError(
            "frozen_factor_level disagrees with the frozen screen level")

    # the pilot decision the artifact freezes must itself be a valid GO
    tau = _require(doc, "tau_delta", "tau_delta")
    if tau != TAU_DELTA:
        raise B3ConfirmationError(f"tau_delta {tau!r} != frozen {TAU_DELTA}")
    count_gate = _require(doc, "count_gate", "count_gate")
    if count_gate != PILOT_COUNT_GATE:
        raise B3ConfirmationError(
            f"count_gate {count_gate!r} != frozen pilot gate {PILOT_COUNT_GATE}")
    count = _require(doc, "zero_excluding_count", "zero_excluding_count")
    if not isinstance(count, int) or isinstance(count, bool) \
            or count < PILOT_COUNT_GATE:
        raise B3ConfirmationError(
            f"zero_excluding_count {count!r} is below the pilot GO gate "
            f"{PILOT_COUNT_GATE}")
    med = _require(doc, "signed_median_midpoint", "signed_median_midpoint")
    if not isinstance(med, (int, float)) or isinstance(med, bool) \
            or not (med > TAU_DELTA):
        raise B3ConfirmationError(
            f"signed_median_midpoint {med!r} does not exceed tau_delta "
            f"{TAU_DELTA}; not a GO")

    # pilot provenance sub-block, bound to frozen constants
    pilot = _require(doc, "pilot", "pilot")
    for field in ("run_manifest_sha256", "analysis_manifest_sha256",
                  "analysis_code_commit", "screen_record_sha256",
                  "spec_sha256"):
        _require(pilot, field, f"pilot.{field}")
    for field in ("run_manifest_sha256", "analysis_manifest_sha256"):
        if not _is_hex64(pilot[field]):
            raise B3ConfirmationError(
                f"pilot.{field} is not a 64-hex digest")
    if pilot["screen_record_sha256"] != FROZEN_SCREEN_RECORD_SHA256:
        raise B3ConfirmationError(
            "pilot.screen_record_sha256 differs from the frozen screen anchor")
    if pilot["spec_sha256"] != FROZEN_SPEC_SHA256:
        raise B3ConfirmationError(
            "pilot.spec_sha256 differs from the frozen pilot spec hash")
    _commit_is_ancestor(pilot["analysis_code_commit"],
                        "pilot.analysis_code_commit")
    if verify_commit:
        _commit_is_ancestor(
            _require(doc, "selection_code_commit", "selection_code_commit"),
            "selection_code_commit")
    else:
        _require(doc, "selection_code_commit", "selection_code_commit")

    # Task-2 amendment 1: frozen pilot raw-tree binding (validated against the
    # anchor, never recomputed from runs/b3_factor_pilot)
    raw_binding = _require(doc, "raw_binding", "raw_binding")
    for field, expected in (
            ("tree_sha256", FROZEN_PILOT_RAW_TREE["tree_sha256"]),
            ("file_count", FROZEN_PILOT_RAW_TREE["file_count"]),
            ("directory_count", FROZEN_PILOT_RAW_TREE["directory_count"]),
            ("total_bytes", FROZEN_PILOT_RAW_TREE["total_bytes"])):
        value = _require(raw_binding, field, f"raw_binding.{field}")
        if value != expected:
            raise B3ConfirmationError(
                f"raw_binding.{field} {value!r} != frozen pilot anchor "
                f"{expected!r}")

    # Task-2 amendment 2: boundary disclosure; a knife-edge decision needs a
    # human, never an automated launch (no override flag exists)
    boundary_margin = _require(doc, "boundary_margin", "boundary_margin")
    if not isinstance(boundary_margin, (int, float)) \
            or isinstance(boundary_margin, bool):
        raise B3ConfirmationError("boundary_margin is not numeric")
    signed_full = _require(doc, "signed_median_full_precision",
                           "signed_median_full_precision")
    if not isinstance(signed_full, (int, float)) \
            or isinstance(signed_full, bool):
        raise B3ConfirmationError(
            "signed_median_full_precision is not numeric")
    boundary_adjacent = _require(doc, "boundary_adjacent", "boundary_adjacent")
    if not isinstance(boundary_adjacent, bool):
        raise B3ConfirmationError("boundary_adjacent is not a boolean")
    if boundary_adjacent:
        raise B3ConfirmationError(
            "selection is boundary_adjacent (knife-edge decision); a human "
            "must authorize confirmation — refusing to launch automatically")

    # confirmation population must equal the frozen Section-8 grid
    population = _require(doc, "confirmation_population",
                         "confirmation_population")
    _validate_population_block(population, factor)

    return {"document": doc, "sha256": artifact_sha,
            "selected_factor": factor, "direction_sign": direction}


def _validate_population_block(population: dict, factor: str) -> None:
    if _require(population, "seeds", "confirmation_population.seeds") != list(
            CONFIRMATION_SEEDS):
        raise B3ConfirmationError(
            "confirmation_population.seeds != frozen confirmation seeds")
    if _require(population, "settings",
                "confirmation_population.settings") != [BASELINE_SETTING,
                                                        factor]:
        raise B3ConfirmationError(
            "confirmation_population.settings != [S0_baseline, selected]")
    if _require(population, "n_trips",
                "confirmation_population.n_trips") != list(N_TRIPS):
        raise B3ConfirmationError("confirmation_population.n_trips drift")
    if _require(population, "b_scales",
                "confirmation_population.b_scales") != list(B_SCALES):
        raise B3ConfirmationError("confirmation_population.b_scales drift")
    if _require(population, "matched_contrasts",
                "confirmation_population.matched_contrasts") != \
            N_MATCHED_CONTRASTS:
        raise B3ConfirmationError("confirmation_population.matched_contrasts")
    if _require(population, "method_cells",
                "confirmation_population.method_cells") != N_CELLS:
        raise B3ConfirmationError("confirmation_population.method_cells")
    gate = _require(population, "gate", "confirmation_population.gate")
    if _require(gate, "min_zero_excluding",
                "gate.min_zero_excluding") != CONFIRMATION_GATE_MIN:
        raise B3ConfirmationError("confirmation gate min != 18")
    if _require(gate, "of", "gate.of") != CONFIRMATION_GATE_OF:
        raise B3ConfirmationError("confirmation gate denominator != 24")
    if _require(gate, "signed_median_exceeds",
                "gate.signed_median_exceeds") != TAU_DELTA:
        raise B3ConfirmationError("confirmation gate tau != 0.04")


# --------------------------------------------------------------------------
# exact 48-cell enumeration (deterministic order)
# --------------------------------------------------------------------------
def cell_tag(setting: str, seed: int, n_trips: int, b: float) -> str:
    return f"{setting}_s{seed}_n{n_trips}_b{b:g}"


def build_cells(selected_factor: str) -> list[dict]:
    if selected_factor not in bp.FROZEN_SELECTED_LEVELS:
        raise B3ConfirmationError(
            f"selected factor {selected_factor!r} has no frozen level")
    settings = [BASELINE_SETTING, selected_factor]
    cells = []
    for setting in settings:
        battery, power = setting_params(setting)
        for seed in CONFIRMATION_SEEDS:
            for n in N_TRIPS:
                for b in B_SCALES:
                    cells.append({
                        "setting": setting, "seed": seed, "n_trips": n,
                        "b": b, "battery_kwh": battery,
                        "charge_power_kw": power,
                        "tag": cell_tag(setting, seed, n, b),
                    })
    if len(cells) != N_CELLS:
        raise B3ConfirmationError(
            f"enumerated {len(cells)} cells, expected {N_CELLS}")
    return cells


def make_cell_instance(cell: dict):
    assert_confirmation_seed(cell["seed"])
    battery, power = setting_params(cell["setting"])
    if (battery, power) != (cell["battery_kwh"], cell["charge_power_kw"]):
        raise B3ConfirmationError(
            f"factor drift for {cell['setting']}: cell levels "
            f"({cell['battery_kwh']}, {cell['charge_power_kw']}) != frozen "
            f"({battery}, {power})")
    return build_confirmation_instance(cell["seed"], cell["n_trips"],
                                       battery, power)


# --------------------------------------------------------------------------
# run manifest (canonical, deterministic, SHA-bound) — mirrors the pilot
# --------------------------------------------------------------------------
def _recompute_hashes(selected_factor: str) -> tuple[dict, list]:
    from egglab.market import make_affine_market
    from egglab.b2a2 import market_hash

    instance_hashes: dict[str, str] = {}
    market_rows: list[dict] = []
    for cell in build_cells(selected_factor):
        inst = make_cell_instance(cell)
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


def _assert_hash_invariants(instance_hashes: dict, market_rows: list) -> None:
    from collections import Counter
    if len(instance_hashes) != N_PHYSICAL_INSTANCES:
        raise B3ConfirmationError(
            f"expected {N_PHYSICAL_INSTANCES} distinct instances, got "
            f"{len(instance_hashes)}")
    inst_counts = Counter(r["instance_hash"] for r in market_rows)
    for ihash, n in inst_counts.items():
        if n != 2:
            raise B3ConfirmationError(
                f"instance {ihash} occurs {n} times, expected exactly twice")
    by_phys: dict[tuple, dict] = {}
    for r in market_rows:
        by_phys.setdefault((r["setting"], r["seed"], r["n_trips"]), {})[
            r["b"]] = r["market_hash"]
    for key, bmap in by_phys.items():
        if len(set(bmap.values())) != len(bmap):
            raise B3ConfirmationError(
                f"{key}: market hashes do not differ across b")
    by_market_cell: dict[tuple, set] = {}
    for r in market_rows:
        by_market_cell.setdefault(
            (r["seed"], r["n_trips"], r["b"]), set()).add(r["market_hash"])
    for key, mset in by_market_cell.items():
        if len(mset) != 1:
            raise B3ConfirmationError(
                f"market cell {key}: settings disagree on market hash")


def build_run_manifest(selected_factor: str, selection: dict, *,
                       git_commit: str, backend_name: str,
                       mip_gap: float = MIP_GAP_DEFAULT) -> dict:
    if len(git_commit) != 40 or not all(
            c in "0123456789abcdef" for c in git_commit):
        raise B3ConfirmationError(
            "run manifest requires the full 40-char commit SHA")
    if backend_name != "GRB":
        raise B3ConfirmationError(
            f"run manifest backend {backend_name!r} is not GRB (Gurobi-only)")
    instance_hashes, market_rows = _recompute_hashes(selected_factor)
    _assert_hash_invariants(instance_hashes, market_rows)
    return {
        "schema": RUN_MANIFEST_SCHEMA,
        "campaign": "b3-confirmation",
        "run_commit": git_commit,
        "selected_factor": selected_factor,
        "direction_sign": DIRECTION_SIGN[selected_factor],
        "frozen_factor_level": bp.FROZEN_SELECTED_LEVELS[selected_factor],
        "selection_artifact_sha256": selection["sha256"],
        "spec": {"path": SPEC_RELPATH,
                 "sha256": bp.sha256_file(REPO_ROOT / SPEC_RELPATH)},
        "screen_record_sha256": FROZEN_SCREEN_RECORD_SHA256,
        "pilot_raw_tree_sha256": FROZEN_PILOT_RAW_TREE["tree_sha256"],
        "generator": {
            "path": bp.GENERATOR_RELPATH if hasattr(bp, "GENERATOR_RELPATH")
            else "src/egglab/instance.py",
            "held_fixed_arguments": dict(GENERATOR_HELD_FIXED_ARGUMENTS),
            "baseline": {"battery_kwh": bp.BASELINE_BATTERY_KWH,
                         "charge_power_kw": bp.BASELINE_POWER_KW},
        },
        "grid": {
            "settings": [BASELINE_SETTING, selected_factor],
            "seeds": list(CONFIRMATION_SEEDS),
            "n_trips": list(N_TRIPS),
            "b_scales": list(B_SCALES),
        },
        "tolerances": {"epsilon": EPSILON, "budget": BUDGET, "tol_d": TOL_D,
                       "tau_delta": TAU_DELTA},
        "confirmation_gate": {"min_zero_excluding": CONFIRMATION_GATE_MIN,
                              "of": CONFIRMATION_GATE_OF,
                              "signed_median_exceeds": TAU_DELTA},
        "solver": {"backend": backend_name, "method": METHOD,
                   "mip_gap": mip_gap},
        "counts": counts(),
        "instance_hashes": instance_hashes,
        "market_hashes": market_rows,
    }


def canonical_manifest_bytes(manifest: dict) -> bytes:
    return bp.canonical_manifest_bytes(manifest)


def run_manifest_sha256(manifest: dict) -> str:
    return bp.run_manifest_sha256(manifest)


def market_hash_by_cell(manifest: dict) -> dict:
    return {(r["setting"], r["seed"], r["n_trips"], r["b"]): r["market_hash"]
            for r in manifest.get("market_hashes", [])}


def write_run_manifest(out_dir, manifest: dict) -> str:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / RUN_MANIFEST_FILENAME
    payload = canonical_manifest_bytes(manifest)
    if path.exists():
        if path.read_bytes() != payload:
            raise B3ConfirmationError(
                f"refusing to overwrite a different run manifest at {path}")
        return str(path)
    bp._atomic_write_bytes(path, payload)
    return str(path)


def load_run_manifest(out_dir) -> dict:
    path = Path(out_dir) / RUN_MANIFEST_FILENAME
    if not path.is_file():
        raise B3ConfirmationError(f"run manifest missing: {path}")
    manifest = json.loads(path.read_bytes())
    if manifest.get("schema") != RUN_MANIFEST_SCHEMA:
        raise B3ConfirmationError("run manifest schema mismatch")
    return {"manifest": manifest, "sha256": run_manifest_sha256(manifest)}


def bind_job_id(out_dir, job_id: str) -> str:
    loaded = load_run_manifest(out_dir)
    manifest = loaded["manifest"]
    path = Path(out_dir) / JOB_FILENAME
    if path.exists():
        raise B3ConfirmationError(f"job binding already exists: {path}")
    import datetime
    doc = {
        "schema": JOB_SCHEMA,
        "job_id": str(job_id),
        "run_manifest_sha256": loaded["sha256"],
        "run_commit": manifest["run_commit"],
        "selection_artifact_sha256": manifest["selection_artifact_sha256"],
        "submitted_utc": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    bp._atomic_write_bytes(
        path, (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode())
    return str(path)


# --------------------------------------------------------------------------
# cell identity sidecar
# --------------------------------------------------------------------------
def cell_identity(cell: dict, manifest: dict, *, market_hash: str,
                  instance_hash: str, run_manifest_sha256: str,
                  run_commit: str, selection_artifact_sha256: str,
                  mip_gap: float, backend_name: str) -> dict:
    return {
        "schema": CELL_IDENTITY_SCHEMA,
        "campaign": "b3-confirmation",
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
        "selected_factor": manifest["selected_factor"],
        "direction_sign": manifest["direction_sign"],
        "screen_record_sha256": FROZEN_SCREEN_RECORD_SHA256,
        "instance_hash": instance_hash,
        "market_hash": market_hash,
        "run_manifest_sha256": run_manifest_sha256,
        "run_commit": run_commit,
        "selection_artifact_sha256": selection_artifact_sha256,
        "solver": {"backend": backend_name, "mip_gap": mip_gap},
    }


def canonical_cell_identity_bytes(identity: dict) -> bytes:
    return (json.dumps(identity, indent=2, sort_keys=True) + "\n").encode()


def verify_or_write_cell_identity(cell_dir, identity: dict) -> None:
    path = Path(cell_dir) / CELL_IDENTITY_FILENAME
    payload = canonical_cell_identity_bytes(identity)
    if path.exists():
        if path.read_bytes() != payload:
            try:
                prior = json.loads(path.read_bytes())
            except ValueError:
                prior = {}
            diffs = sorted(
                k for k in set(identity) | set(prior)
                if prior.get(k) != identity.get(k))
            raise B3ConfirmationError(
                f"cell identity mismatch on resume (fields: {diffs}); refusing "
                "to resume under a different run/selection/code identity")
        return
    bp._atomic_write_bytes(path, payload)


def counts() -> dict:
    return {
        "settings": 2,
        "physical_instances": N_PHYSICAL_INSTANCES,
        "cells": N_CELLS,
        "dictators": N_CELLS,
        "matched_contrasts": N_MATCHED_CONTRASTS,
        "confirmation_seeds": len(CONFIRMATION_SEEDS),
    }
