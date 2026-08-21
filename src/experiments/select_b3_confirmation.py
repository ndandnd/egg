"""B3 confirmation-selection freeze (outcome-blind boundary).

Consumes ONLY a completed, audited B3 factor-pilot analysis artifact
(the `result/b3_factor_pilot/<stamp>/` directory emitted by
`analyze_b3_factor_pilot.analyze`) and writes a deterministic
SELECTION.json that freezes the confirmation stage's identity BEFORE any
confirmation implementation or launch exists.

Authorization requires DECISION.state == "GO".  Every other state
(NO-GO, UNDER-RESOLVED, INVALID/HALT, DESIGN-NOT-FROZEN), any
missing/tampered table, mismatched hash, non-ancestor commit, dirty
tracked tree, or an existing destination refuses WITHOUT partial output.

The later confirmation population is frozen here but NOT implemented or
launched: seeds {32,33,34,35,36,37}; S0 versus the selected factor only;
n {8,12}; b {0.01,0.05}; 24 matched contrasts = 48 method-cells; gate
>= 18/24 direction-consistent zero-excluding AND signed median > 0.04.
No seeds 16-31, no A6, and no confirmation driver exists in this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
import experiments.b3_pilot_anchor as anchor
import experiments.b3_pilot_evidence as evidence
import experiments.analyze_b3_factor_pilot as az
from experiments.analyze_b3_factor_pilot import (
    BASELINE_SETTING,
    BOUNDARY_ADJACENT_TOL,
    CELL_INTERVAL_COLUMNS,
    COUNT_GATE,
    DECISION_SCHEMA,
    DIRECTION_SIGN,
    FACTOR_ORDER,
    MATCHED_CONTRAST_COLUMNS,
    SETTING_SUMMARY_COLUMNS,
    SCHEMA as ANALYSIS_SCHEMA,
    TAU_DELTA,
    WIDTH_BOUND,
)
from experiments.package_a6_holdout import (
    PackagingError,
    canonical_tree_sha256,
    publish_flat_directory_no_replace,
    snapshot_source,
)

SELECTION_SCHEMA = "b3-confirmation-selection-v1"
SELECTION_FILENAME = "SELECTION.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_BINDING_FIELDS = (
    "raw_tree_sha256", "file_count", "directory_count", "total_bytes",
    "manifest_sha256", "job_id", "job_sha256", "pre_analysis_anchor",
)

# frozen confirmation population (spec Section 8) — NOT implemented here
CONFIRMATION_POPULATION = {
    "seeds": [32, 33, 34, 35, 36, 37],
    "settings": ["S0_baseline", "<selected factor>"],
    "n_trips": [8, 12],
    "b_scales": [0.01, 0.05],
    "matched_contrasts": 24,
    "method_cells": 48,
    "gate": {
        "min_zero_excluding": 18,
        "of": 24,
        "signed_median_exceeds": bp.TAU_DELTA,
    },
    "excluded_seed_bands": {"holdout_16_31": "never used",
                            "development": [0, 11, 15]},
}

PROVENANCE_FILES = (
    "src/experiments/select_b3_confirmation.py",
    "src/experiments/analyze_b3_factor_pilot.py",
    "src/experiments/audit_b3_factor_pilot.py",
    "src/experiments/b3_factor_pilot.py",
    "src/experiments/b3_pilot_anchor.py",
    "src/experiments/b3_factor_screen.py",
    "src/experiments/b3_pilot_evidence.py",
    "src/experiments/package_a6_holdout.py",
    "src/experiments/provenance_git.py",
)


class B3SelectionError(RuntimeError):
    """The confirmation selection cannot be frozen safely."""


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_selection_code_commit(claimed: str) -> str:
    """Full 40-hex SHA that resolves, is an ancestor of HEAD, with a clean
    tracked tree and byte-identical provenance files."""
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise B3SelectionError(
            "selection-code-commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        evidence.assert_no_history_rewrites(REPO_ROOT)
    except evidence.EvidenceError as exc:
        raise B3SelectionError(str(exc)) from exc
    try:
        resolved = subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "rev-parse", "--verify",
                                   f"{claimed}^{{commit}}"),
            cwd=REPO_ROOT, env=evidence.git_env(),
            stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3SelectionError(
            f"claimed commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise B3SelectionError(
            f"claimed commit {claimed} resolves to {resolved}")
    if subprocess.run(
            evidence.git_argv(REPO_ROOT, "merge-base", "--is-ancestor",
                              claimed, "HEAD"),
            cwd=REPO_ROOT, env=evidence.git_env()).returncode != 0:
        raise B3SelectionError(
            f"claimed commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        evidence.git_argv(REPO_ROOT, "status", "--porcelain"),
        cwd=REPO_ROOT, env=evidence.git_env()).decode()
    if [line for line in dirty.splitlines() if not line.startswith("??")]:
        raise B3SelectionError(
            "working tree has tracked modifications; commit the selection "
            "code before freezing")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "show",
                              f"{claimed}:{relpath}"),
            cwd=REPO_ROOT, env=evidence.git_env())
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise B3SelectionError(
                f"{relpath} differs from the claimed commit {claimed}")
    return resolved


def _read_bytes_once(
    path: Path,
    label: str,
    signatures: dict[Path, tuple] | None = None,
) -> bytes:
    """Read each input file's bytes exactly once; hashing and parsing use
    THESE bytes (no hash-close-reopen-parse window)."""
    try:
        raw, signature = evidence.read_regular_bytes_with_signature(path, label)
    except evidence.EvidenceError as exc:
        raise B3SelectionError(str(exc)) from exc
    if signatures is not None:
        signatures[path] = signature
    return raw


def _revalidate_signatures(signatures: dict[Path, tuple]) -> None:
    for path, expected in signatures.items():
        try:
            info = path.lstat()
        except OSError as exc:
            raise B3SelectionError(
                f"analysis artifact changed after immutable read: {path.name}"
            ) from exc
        actual = (
            info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink)
        if actual != expected or path.is_symlink():
            raise B3SelectionError(
                f"analysis artifact changed after immutable read: {path.name}")


def _json_object_from_bytes(raw: bytes, label: str) -> dict:
    try:
        value = evidence.strict_json_loads(raw, label)
    except evidence.EvidenceError as exc:
        raise B3SelectionError(str(exc)) from exc
    if not isinstance(value, dict):
        raise B3SelectionError(f"{label}: JSON root is not an object")
    return value


def _csv_rows_from_bytes(raw: bytes, expected_columns: list[str],
                         label: str) -> list[dict]:
    import csv
    import io
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise B3SelectionError(f"{label}: malformed UTF-8 CSV") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if list(reader.fieldnames or ()) != expected_columns:
        raise B3SelectionError(f"{label}: column layout differs")
    rows = list(reader)
    if any(set(row) != set(expected_columns)
           or any(value is None for value in row.values())
           for row in rows):
        raise B3SelectionError(f"{label}: malformed row layout")
    return rows


def _require_commit_in_history(commit: str, label: str) -> None:
    """The commit must be a real object in THIS repository's history (an
    ancestor of the current branch); all-zero or unresolvable commits
    refuse."""
    if (not isinstance(commit, str) or len(commit) != 40
            or not all(c in "0123456789abcdef" for c in commit)
            or commit == "0" * 40):
        raise B3SelectionError(
            f"{label}: commit {commit!r} is not a real 40-hex commit")
    try:
        resolved = subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "rev-parse", "--verify",
                                   f"{commit}^{{commit}}"),
            cwd=REPO_ROOT, env=evidence.git_env(),
            stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3SelectionError(
            f"{label}: commit {commit} does not resolve") from exc
    if resolved != commit:
        raise B3SelectionError(f"{label}: commit resolves to {resolved}")
    if subprocess.run(
            evidence.git_argv(REPO_ROOT, "merge-base", "--is-ancestor",
                              commit, "HEAD"),
            cwd=REPO_ROOT, env=evidence.git_env()).returncode != 0:
        raise B3SelectionError(
            f"{label}: commit {commit} is not an ancestor of the current "
            "branch")


def _git_file_at_commit(commit: str, relpath: str, label: str) -> bytes:
    try:
        return subprocess.check_output(
            evidence.git_argv(REPO_ROOT, "show", f"{commit}:{relpath}"),
            cwd=REPO_ROOT, env=evidence.git_env(),
            stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        raise B3SelectionError(
            f"{label}: commit {commit} does not contain {relpath}") from exc


def _verify_analysis_commit_identity(
    commit: str,
    *,
    spec_sha256: str,
    screen_sha256: str,
) -> None:
    """Prove the claimed analyzer commit contains all executed B3 helpers."""
    required_code = (
        "src/experiments/analyze_b3_factor_pilot.py",
        "src/experiments/audit_b3_factor_pilot.py",
        "src/experiments/b3_factor_pilot.py",
        "src/experiments/b3_pilot_anchor.py",
        "src/experiments/b3_factor_screen.py",
        "src/experiments/b3_pilot_evidence.py",
        "src/experiments/package_a6_holdout.py",
    )
    for relpath in required_code:
        _git_file_at_commit(commit, relpath, "analysis_code_commit")
    committed_spec = _git_file_at_commit(
        commit, bp.SPEC_RELPATH, "analysis_code_commit")
    if hashlib.sha256(committed_spec).hexdigest() != spec_sha256:
        raise B3SelectionError(
            "analysis commit's specification bytes do not match the "
            "artifact's frozen spec identity")
    screen_relpath = f"{bp.FROZEN_SCREEN_RELDIR}/SCREEN_RECORD.json"
    committed_screen = _git_file_at_commit(
        commit, screen_relpath, "analysis_code_commit")
    if hashlib.sha256(committed_screen).hexdigest() != screen_sha256:
        raise B3SelectionError(
            "analysis commit's screen bytes do not match the frozen screen "
            "identity")


def _number(row: dict, field: str, label: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise B3SelectionError(
            f"{label}: {field} is not a finite number") from exc
    if not math.isfinite(value):
        raise B3SelectionError(f"{label}: {field} is not a finite number")
    return value


def _integer(row: dict, field: str, label: str) -> int:
    value = row.get(field)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise B3SelectionError(f"{label}: {field} is not an integer") from exc
    if str(parsed) != value:
        raise B3SelectionError(f"{label}: {field} is not canonical")
    return parsed


def _boolean(row: dict, field: str, label: str) -> bool:
    value = row.get(field)
    if value not in ("True", "False"):
        raise B3SelectionError(f"{label}: {field} is not a canonical boolean")
    return value == "True"


def _load_raw_identity(
    runs_dir: str | os.PathLike,
    expected_raw_anchor: dict | None,
) -> dict:
    runs = Path(runs_dir)
    try:
        snapshot = snapshot_source(runs)
    except PackagingError as exc:
        raise B3SelectionError(f"raw runs tree is unreadable: {exc}") from exc
    tree_sha = canonical_tree_sha256(snapshot)
    identity = anchor.snapshot_identity(snapshot, tree_sha)
    expected = (anchor.FROZEN_RAW_ANCHOR if expected_raw_anchor is None
                else expected_raw_anchor)
    if not isinstance(expected, dict) \
            or set(expected) != set(anchor.FROZEN_RAW_ANCHOR):
        raise B3SelectionError(
            "expected pre-analysis raw anchor is malformed")
    for field in anchor.FROZEN_RAW_ANCHOR:
        if identity.get(field) != expected.get(field):
            raise B3SelectionError(
                f"live raw-tree anchor mismatch for {field}: "
                f"{identity.get(field)!r} != {expected.get(field)!r}")
    file_hashes = {
        row["path"]: row["sha256"] for row in snapshot["files"]}
    for name in (bp.JOB_FILENAME, bp.RUN_MANIFEST_FILENAME):
        if name not in file_hashes:
            raise B3SelectionError(f"raw runs tree is missing {name}")
    try:
        job_bytes = evidence.read_regular_bytes_once(
            runs / bp.JOB_FILENAME, bp.JOB_FILENAME)
        manifest_bytes = evidence.read_regular_bytes_once(
            runs / bp.RUN_MANIFEST_FILENAME, bp.RUN_MANIFEST_FILENAME)
    except evidence.EvidenceError as exc:
        raise B3SelectionError(str(exc)) from exc
    job_sha = hashlib.sha256(job_bytes).hexdigest()
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    if job_sha != file_hashes[bp.JOB_FILENAME]:
        raise B3SelectionError(
            "raw runs tree changed while reading JOB.json")
    if manifest_sha != file_hashes[bp.RUN_MANIFEST_FILENAME]:
        raise B3SelectionError(
            "raw runs tree changed while reading MANIFEST.json")
    # Provenance is RE-VERIFIED here, not inherited from the analysis
    # manifest.  ``run_commit_verified`` is a single editable boolean: flipping
    # it in a seam-derived artifact laundered unverified provenance into
    # authorization, packaging and import.  The selector therefore resolves the
    # producer commit itself, from the run manifest bytes it just
    # digest-checked, and treats the recorded flag as diagnostic only.
    try:
        run_manifest_doc = evidence.strict_json_loads(
            manifest_bytes, bp.RUN_MANIFEST_FILENAME)
    except evidence.EvidenceError as exc:
        raise B3SelectionError(str(exc)) from exc
    if not isinstance(run_manifest_doc, dict):
        raise B3SelectionError("run MANIFEST.json root is not an object")
    try:
        az.verify_run_commit(run_manifest_doc.get("run_commit"))
    except evidence.EvidenceError as exc:
        raise B3SelectionError(
            f"raw run provenance is not verifiable: {exc}") from exc
    job = _json_object_from_bytes(job_bytes, bp.JOB_FILENAME)
    manifest = _json_object_from_bytes(
        manifest_bytes, bp.RUN_MANIFEST_FILENAME)
    job_id = job.get("job_id")
    if (job.get("schema") != "b3-factor-pilot-job-v1"
            or not isinstance(job_id, str) or not job_id.isdigit()
            or job_id.startswith("0") or len(job_id) > 18):
        raise B3SelectionError("raw JOB.json has a noncanonical Slurm job id")
    if (manifest.get("schema") != bp.RUN_MANIFEST_SCHEMA
            or job.get("run_manifest_sha256") != manifest_sha
            or job.get("run_commit") != manifest.get("run_commit")):
        raise B3SelectionError(
            "raw JOB.json does not bind the exact MANIFEST.json bytes")
    return {
        "raw_tree_sha256": identity["tree_sha256"],
        "file_count": identity["file_count"],
        "directory_count": identity["directory_count"],
        "total_bytes": identity["total_bytes"],
        "manifest_sha256": manifest_sha,
        "job_id": job_id,
        "job_sha256": job_sha,
        "pre_analysis_anchor": dict(expected),
        "_snapshot": snapshot,
        "_runs": runs,
    }


def recompute_decision(cells: list[dict],
                       contrasts: list[dict]) -> dict:
    """Independently recompute the FULL preregistered decision from the
    primitive tables: 60 cell intervals -> 48 matched contrasts ->
    direction signs -> zero-excluding counts -> signed medians ->
    count/median/factor-order ranking -> state.  The recorded
    matched_contrasts rows are cross-checked field by field."""
    import statistics
    interval = {}
    screen = bp.load_frozen_screen()
    market_hash_by_cell = {}
    expected_keys = {
        (cell["setting"], cell["seed"], cell["n_trips"], f"{cell['b']:g}")
        for cell in bp.build_cells()}
    for row in cells:
        label = "cell_intervals.csv row"
        setting = row.get("setting")
        seed = _integer(row, "seed", label)
        n_trips = _integer(row, "n_trips", label)
        b = row.get("b")
        key = (setting, seed, n_trips, b)
        if key not in expected_keys:
            raise B3SelectionError(
                f"cell_intervals.csv: cell {key} is outside the frozen grid")
        if key in interval:
            raise B3SelectionError(
                f"cell_intervals.csv: duplicate cell {key}")
        expected_instance = screen["instance_hashes"].get(
            (setting, seed, n_trips))
        if row.get("instance_hash") != expected_instance:
            raise B3SelectionError(
                f"cell_intervals.csv {key}: instance hash differs from the "
                "frozen screen")
        market_hash = row.get("market_hash")
        if (not isinstance(market_hash, str) or len(market_hash) != 64
                or any(c not in "0123456789abcdef" for c in market_hash)):
            raise B3SelectionError(
                f"cell_intervals.csv {key}: market hash is invalid")
        market_key = (seed, n_trips, b)
        prior_market = market_hash_by_cell.setdefault(
            market_key, market_hash)
        if prior_market != market_hash:
            raise B3SelectionError(
                f"cell_intervals.csv {key}: matched settings disagree on "
                "market hash")

        z_d_lb = _number(row, "z_d_lb", str(key))
        z_d_ub = _number(row, "z_d_ub", str(key))
        lb_ch = _number(row, "lb_ch", str(key))
        ub_ch = _number(row, "ub_ch", str(key))
        lo_raw = _number(row, "u_lo_raw", str(key))
        lo = _number(row, "u_lo_tightened", str(key))
        hi = _number(row, "u_hi", str(key))
        width = _number(row, "width", str(key))
        expected_values = {
            "u_lo_raw": z_d_lb - ub_ch,
            "u_lo_tightened": max(0.0, z_d_lb - ub_ch),
            "u_hi": z_d_ub - lb_ch,
            "width": (z_d_ub - lb_ch) - (z_d_lb - ub_ch),
            "u_lo_raw_per_trip": (z_d_lb - ub_ch) / n_trips,
            "u_hi_per_trip": (z_d_ub - lb_ch) / n_trips,
            "dictator_gap": z_d_ub - z_d_lb,
            "ch_gap": ub_ch - lb_ch,
        }
        for field, expected in expected_values.items():
            if _number(row, field, str(key)) != expected:
                raise B3SelectionError(
                    f"cell_intervals.csv {key}: {field} does not recompute")
        if (hi < 0 or lo > hi or hi < lo_raw
                or width > WIDTH_BOUND + evidence.NUM_TOL):
            raise B3SelectionError(
                f"cell_intervals.csv {key}: impossible certified interval")
        if row.get("lo_endpoint_source") != "z_D_lb":
            raise B3SelectionError(
                f"cell_intervals.csv {key}: non-evidence lower endpoint")
        if lb_ch > 0:
            if (_number(row, "cost_fraction_lo", str(key))
                    != lo / ub_ch
                    or _number(row, "cost_fraction_hi", str(key))
                    != hi / lb_ch):
                raise B3SelectionError(
                    f"cell_intervals.csv {key}: cost fraction does not "
                    "recompute")
        elif (row.get("cost_fraction_lo") != ""
              or row.get("cost_fraction_hi") != ""):
            raise B3SelectionError(
                f"cell_intervals.csv {key}: non-positive denominator has a "
                "cost fraction")
        calls = _integer(row, "oracle_calls", str(key))
        if not 1 <= calls <= bp.BUDGET:
            raise B3SelectionError(
                f"cell_intervals.csv {key}: oracle call count out of budget")
        if row.get("solver_backend") != "GRB":
            raise B3SelectionError(
                f"cell_intervals.csv {key}: solver backend is not GRB")
        solver_gap = _number(row, "solver_mip_gap", str(key))
        interval[key] = {
            "lo_raw": lo_raw, "lo": lo, "hi": hi, "width": width,
            "solver_mip_gap": solver_gap,
        }
    if set(interval) != expected_keys:
        raise B3SelectionError(
            "cell_intervals.csv does not cover the frozen 60-cell grid "
            "exactly")
    if len(market_hash_by_cell) != 12:
        raise B3SelectionError(
            "cell_intervals.csv does not carry all 12 matched markets")
    for seed in bp.SEEDS:
        for n_trips in bp.N_TRIPS:
            hashes = {
                market_hash_by_cell[(seed, n_trips, f"{b:g}")]
                for b in bp.B_SCALES}
            if len(hashes) != len(bp.B_SCALES):
                raise B3SelectionError(
                    "cell_intervals.csv market hashes do not distinguish b")
    recorded = {}
    for row in contrasts:
        key = (
            row.get("setting"),
            _integer(row, "seed", "matched_contrasts.csv row"),
            _integer(row, "n_trips", "matched_contrasts.csv row"),
            row.get("b"),
        )
        if key in recorded:
            raise B3SelectionError(
                f"matched_contrasts.csv: duplicate contrast {key}")
        recorded[key] = row
    per_setting = {}
    for factor in FACTOR_ORDER:
        sign = DIRECTION_SIGN[factor]
        signed_mids = []
        count = 0
        for cell in bp.build_cells():
            if cell["setting"] != factor:
                continue
            key = (factor, cell["seed"], cell["n_trips"],
                   f"{cell['b']:g}")
            base_key = (BASELINE_SETTING, cell["seed"], cell["n_trips"],
                        f"{cell['b']:g}")
            u_f = interval[key]
            u_0 = interval[base_key]
            lo = u_f["lo_raw"] - u_0["hi"]
            hi = u_f["hi"] - u_0["lo_raw"]
            midpoint = 0.5 * (lo + hi)
            width = u_f["width"] + u_0["width"]
            zero_excluding = (lo > 0) if sign > 0 else (hi < 0)
            row = recorded.get(key)
            if row is None:
                raise B3SelectionError(
                    f"matched_contrasts.csv: missing contrast {key}")
            for field, value in (
                    ("delta_lo", lo), ("delta_hi", hi),
                    ("delta_midpoint", midpoint),
                    ("delta_width", width)):
                if _number(row, field, str(key)) != value:
                    raise B3SelectionError(
                        f"matched_contrasts.csv {key}: recorded {field} "
                        f"{row[field]} != recomputed {value!r}")
            if _integer(row, "direction_sign", str(key)) != sign:
                raise B3SelectionError(
                    f"matched_contrasts.csv {key}: direction_sign differs "
                    "from the preregistered sign")
            if _boolean(
                    row, "direction_consistent_zero_excluding", str(key)
                    ) != zero_excluding:
                raise B3SelectionError(
                    f"matched_contrasts.csv {key}: zero-excluding flag "
                    "does not recompute")
            if zero_excluding:
                count += 1
            signed_mids.append(sign * midpoint)
        per_setting[factor] = {
            "count": count,
            "signed_median_midpoint": statistics.median(signed_mids),
        }
    ranked = sorted(
        FACTOR_ORDER,
        key=lambda f: (per_setting[f]["count"],
                       per_setting[f]["signed_median_midpoint"],
                       -FACTOR_ORDER.index(f)),
        reverse=True)
    for rank, factor in enumerate(ranked, start=1):
        per_setting[factor].update({
            "direction_sign": DIRECTION_SIGN[factor],
            "n_cells": 12,
            "factor_order_index": FACTOR_ORDER.index(factor),
            "rank": rank,
            "selected": rank == 1,
        })
    f_star = ranked[0]
    med_star = per_setting[f_star]["signed_median_midpoint"]
    count_star = per_setting[f_star]["count"]
    if abs(med_star) <= TAU_DELTA:
        state = "UNDER-RESOLVED"
    elif med_star > TAU_DELTA and count_star >= COUNT_GATE:
        state = "GO"
    else:
        state = "NO-GO"
    boundary_margin = abs(med_star) - TAU_DELTA
    return {"state": state, "selected_factor": f_star,
            "count": count_star, "signed_median_midpoint": med_star,
            "signed_median_midpoint_repr": repr(med_star),
            "boundary_margin": boundary_margin,
            "boundary_adjacent":
                abs(boundary_margin) < BOUNDARY_ADJACENT_TOL,
            "boundary_adjacent_tolerance": BOUNDARY_ADJACENT_TOL,
            "per_setting": per_setting, "ranked": ranked}


def load_analysis_artifact(
    analysis_dir: str | os.PathLike,
    runs_dir: str | os.PathLike,
    *,
    expected_raw_anchor: dict | None = None,
) -> dict:
    """Load and fully validate the completed analysis artifact with
    transactional single reads, frozen-constant provenance, and a FULL
    independent recomputation of the decision from primitives."""
    base = Path(analysis_dir)
    if base.is_symlink() or not base.is_dir():
        raise B3SelectionError(f"missing or unsafe analysis directory: {base}")
    signatures: dict[Path, tuple] = {}
    manifest_path = base / "MANIFEST.json"
    manifest_bytes = _read_bytes_once(
        manifest_path, "MANIFEST.json", signatures)
    manifest = _json_object_from_bytes(manifest_bytes, "MANIFEST.json")
    if manifest.get("schema") != ANALYSIS_SCHEMA:
        raise B3SelectionError(
            f"analysis manifest schema {manifest.get('schema')!r} is not "
            f"{ANALYSIS_SCHEMA!r}")
    # provenance must be REAL: verified flag, frozen screen/spec hashes,
    # and an analyzer commit that resolves inside this repository history
    if manifest.get("analysis_code_verified") is not True:
        raise B3SelectionError(
            "analysis was produced without code verification "
            "(analysis_code_verified != true); not selectable")
    frozen_screen = manifest.get("frozen_screen") or {}
    if frozen_screen.get("record_sha256") != (
            bp.FROZEN_SCREEN_RECORD_SHA256):
        raise B3SelectionError(
            "analysis screen record SHA differs from the frozen screen "
            "constant; non-scoreable analysis is not selectable")
    if manifest.get("frozen_screen_verified") is not True:
        raise B3SelectionError(
            "analysis did not verify the frozen canonical screen")
    expected_spec_sha = sha256_file(REPO_ROOT / bp.SPEC_RELPATH)
    if ((manifest.get("spec") or {}).get("path") != bp.SPEC_RELPATH
            or (manifest.get("spec") or {}).get("sha256")
            != expected_spec_sha):
        raise B3SelectionError(
            "analysis spec SHA differs from the committed specification")
    if manifest.get("tolerances") != {
            "epsilon": bp.EPSILON,
            "tol_d": bp.TOL_D,
            "budget": bp.BUDGET,
            "tau_delta": TAU_DELTA,
    }:
        raise B3SelectionError(
            "analysis manifest tolerances differ from the frozen design")
    if manifest.get("counts") != bp.counts():
        raise B3SelectionError(
            "analysis manifest counts differ from the frozen design")
    solver = manifest.get("solver")
    if (not isinstance(solver, dict)
            or solver.get("backend") != "GRB"
            or solver.get("method") != bp.METHOD
            or not isinstance(solver.get("mip_gap"), (int, float))
            or isinstance(solver.get("mip_gap"), bool)
            or not math.isfinite(solver["mip_gap"])):
        raise B3SelectionError(
            "analysis manifest solver identity is missing or invalid")
    analysis_commit = manifest.get("analysis_code_commit")
    _require_commit_in_history(analysis_commit, "analysis_code_commit")
    _verify_analysis_commit_identity(
        analysis_commit,
        spec_sha256=expected_spec_sha,
        screen_sha256=bp.FROZEN_SCREEN_RECORD_SHA256,
    )

    outputs = manifest.get("outputs") or {}
    required = {"DECISION.json", "SUMMARY.md", "cell_intervals.csv",
                "matched_contrasts.csv", "setting_summary.csv"}
    if set(outputs) != required:
        raise B3SelectionError(
            "analysis manifest outputs are incomplete for a scoreable "
            f"population: {sorted(outputs)}")
    observed_names = {
        entry.name for entry in os.scandir(base)
    }
    expected_names = required | {"MANIFEST.json"}
    missing_names = sorted(expected_names - observed_names)
    if missing_names:
        raise B3SelectionError(
            f"missing analysis table: {missing_names[0]}")
    if observed_names != expected_names:
        raise B3SelectionError(
            "analysis directory population differs from the complete "
            f"artifact contract: {sorted(observed_names)}")
    raw_by_name = {}
    for name, recorded in outputs.items():
        path = base / name
        if not path.is_file():
            raise B3SelectionError(f"missing analysis table: {name}")
        raw = _read_bytes_once(path, name, signatures)
        actual = hashlib.sha256(raw).hexdigest()
        if actual != recorded:
            raise B3SelectionError(
                f"analysis table {name} hash mismatch (tampered): "
                f"{actual} != {recorded}")
        raw_by_name[name] = raw
    table_rows = manifest.get("table_rows") or {}
    cells = _csv_rows_from_bytes(
        raw_by_name["cell_intervals.csv"], CELL_INTERVAL_COLUMNS,
        "cell_intervals.csv")
    contrasts = _csv_rows_from_bytes(
        raw_by_name["matched_contrasts.csv"], MATCHED_CONTRAST_COLUMNS,
        "matched_contrasts.csv")
    summary = _csv_rows_from_bytes(
        raw_by_name["setting_summary.csv"], SETTING_SUMMARY_COLUMNS,
        "setting_summary.csv")
    for name, rows, expected in (
            ("cell_intervals.csv", cells, bp.N_CELLS),
            ("matched_contrasts.csv", contrasts, bp.N_MATCHED_CONTRASTS),
            ("setting_summary.csv", summary, 4)):
        if len(rows) != expected or table_rows.get(name) != expected:
            raise B3SelectionError(
                f"{name}: row count {len(rows)} / manifest "
                f"{table_rows.get(name)} != expected {expected}")
    for row in cells:
        if _number(
                row, "solver_mip_gap", "cell_intervals.csv"
                ) != solver["mip_gap"]:
            raise B3SelectionError(
                "cell_intervals.csv solver identity differs from the "
                "analysis manifest")
    decision = _json_object_from_bytes(
        raw_by_name["DECISION.json"], "DECISION.json")
    if decision.get("schema") != DECISION_SCHEMA:
        raise B3SelectionError("DECISION.json schema differs")
    for field in ("run_manifest_sha256", "screen_record_sha256",
                  "spec_sha256"):
        if decision.get("inputs", {}).get(field) is None:
            raise B3SelectionError(f"DECISION.json missing input {field}")
    if decision.get("inputs", {}).get("screen_record_sha256") != (
            bp.FROZEN_SCREEN_RECORD_SHA256):
        raise B3SelectionError(
            "DECISION.json screen record SHA differs from the frozen "
            "constant")
    if decision.get("analysis_code_commit") != manifest.get(
            "analysis_code_commit"):
        raise B3SelectionError(
            "DECISION.json / manifest analysis_code_commit mismatch")
    if decision.get("inputs", {}).get("run_manifest_sha256") != (
            manifest.get("run_manifest_sha256")):
        raise B3SelectionError(
            "DECISION.json / manifest run_manifest_sha256 mismatch")
    if decision.get("inputs", {}).get("spec_sha256") != expected_spec_sha:
        raise B3SelectionError(
            "DECISION.json spec identity differs from the frozen "
            "specification")
    if decision.get("frozen_screen_verified") is not True:
        raise B3SelectionError(
            "DECISION.json does not verify the frozen screen")
    if decision.get("inputs", {}).get("solver") != solver:
        raise B3SelectionError(
            "DECISION.json / manifest solver identity mismatch")
    if decision.get("thresholds") != {
            "count_gate": COUNT_GATE,
            "tau_delta": TAU_DELTA,
            "width_bound": WIDTH_BOUND,
    }:
        raise B3SelectionError(
            "DECISION.json thresholds differ from the preregistered gates")
    if decision.get("counts", {}).get("expected_cells") != bp.N_CELLS \
            or decision.get("counts", {}).get(
                "expected_contrasts") != bp.N_MATCHED_CONTRASTS \
            or decision.get("counts", {}).get(
                "n_matched_cells") != 12:
        raise B3SelectionError(
            "DECISION.json frozen population counts differ")

    raw_binding = manifest.get("raw_binding")
    expected_binding_fields = set(RAW_BINDING_FIELDS)
    if not isinstance(raw_binding, dict):
        raise B3SelectionError("analysis raw_binding is missing")
    if set(raw_binding) != expected_binding_fields:
        raise B3SelectionError(
            "analysis raw_binding fields are incomplete or unexpected")
    # A recorded flag is only a control if something refuses on it: an
    # analysis whose run_commit was resolved through the synthetic test seam
    # rather than through git must never authorize confirmation.  Checked here,
    # alongside the other raw-provenance bindings, so that an incomplete or
    # non-frozen artifact is still refused for the more informative reason.
    if manifest.get("run_commit_verified") is not True:
        raise B3SelectionError(
            "analysis run_commit was not production-verified "
            "(run_commit_verified != true); not selectable")
    live_raw = _load_raw_identity(runs_dir, expected_raw_anchor)
    for field in RAW_BINDING_FIELDS:
        actual = live_raw[field]
        claimed = raw_binding.get(field)
        if claimed != actual:
            raise B3SelectionError(
                f"analysis raw_binding mismatch for {field}: "
                f"{claimed!r} != {actual!r}")
    if raw_binding["manifest_sha256"] != manifest.get("run_manifest_sha256"):
        raise B3SelectionError(
            "analysis raw_binding mismatch for manifest_sha256: "
            "binding differs from analysis run_manifest_sha256")
    if decision.get("inputs", {}).get("raw_binding") != raw_binding:
        raise B3SelectionError(
            "DECISION.json / manifest exact raw-job binding mismatch")

    # BLOCKER repair: never trust the recorded decision — recompute the
    # full preregistered decision from primitives and require EXACT
    # agreement with BOTH DECISION.json and MANIFEST.json["decision"].
    recomputed = recompute_decision(cells, contrasts)
    manifest_decision = manifest.get("decision") or {}
    for source, doc, fields in (
            ("DECISION.json", decision, (
                ("state", "state"),
                ("selected_factor", "selected_factor"),
                ("count", ("counts", "zero_excluding_count")),
                ("signed_median_midpoint", "signed_median_midpoint"),
                ("signed_median_midpoint_repr",
                 "signed_median_midpoint_repr"),
                ("boundary_margin", "boundary_margin"),
                ("boundary_adjacent", "boundary_adjacent"),
                ("boundary_adjacent_tolerance",
                 "boundary_adjacent_tolerance"))),
            ("MANIFEST.json[decision]", manifest_decision, (
                ("state", "state"),
                ("selected_factor", "selected_contrast"),
                ("count", "count"),
                ("signed_median_midpoint", "signed_median_midpoint"),
                ("signed_median_midpoint_repr",
                 "signed_median_midpoint_repr"),
                ("boundary_margin", "boundary_margin"),
                ("boundary_adjacent", "boundary_adjacent"),
                ("boundary_adjacent_tolerance",
                 "boundary_adjacent_tolerance")))):
        for recomputed_field, recorded_field in fields:
            if isinstance(recorded_field, tuple):
                value = (doc.get(recorded_field[0]) or {}).get(
                    recorded_field[1])
                name = ".".join(recorded_field)
            else:
                value = doc.get(recorded_field)
                name = recorded_field
            if value != recomputed[recomputed_field]:
                raise B3SelectionError(
                    f"{source}.{name} = {value!r} disagrees with the "
                    f"recomputed decision "
                    f"{recomputed[recomputed_field]!r}")
    if (manifest_decision.get("count_gate") != COUNT_GATE
            or manifest_decision.get("tau_delta") != TAU_DELTA
            or manifest_decision.get("n_cells") != 12):
        raise B3SelectionError(
            "MANIFEST.json decision thresholds/counts differ from the "
            "preregistered decision")
    if manifest.get("decision_document") != decision:
        raise B3SelectionError(
            "MANIFEST.json exact decision copy differs from DECISION.json")
    selected = recomputed["selected_factor"]
    if decision.get("direction_sign") != DIRECTION_SIGN[selected]:
        raise B3SelectionError(
            "DECISION.json direction sign differs from the recomputed factor")
    # setting_summary must agree field-for-field with the recomputation too.
    summary_factors = [row.get("setting") for row in summary]
    if len(set(summary_factors)) != len(FACTOR_ORDER) \
            or set(summary_factors) != set(FACTOR_ORDER):
        raise B3SelectionError(
            "setting_summary.csv does not cover each frozen factor once")
    for row in summary:
        factor = row["setting"]
        stats = recomputed["per_setting"].get(factor)
        if stats is None:
            raise B3SelectionError(
                f"setting_summary.csv: unexpected factor {factor!r}")
        for field, expected in (
                ("direction_sign", stats["direction_sign"]),
                ("zero_excluding_count", stats["count"]),
                ("n_cells", stats["n_cells"]),
                ("factor_order_index", stats["factor_order_index"]),
                ("rank", stats["rank"])):
            if _integer(row, field, f"setting_summary.csv {factor}") != expected:
                raise B3SelectionError(
                    f"setting_summary.csv {factor}: {field} disagrees with "
                    "the recomputation")
        if _number(
                row, "signed_median_midpoint",
                f"setting_summary.csv {factor}"
                ) != stats["signed_median_midpoint"]:
            raise B3SelectionError(
                f"setting_summary.csv {factor}: signed_median_midpoint "
                "disagrees with the recomputation")
        if _boolean(
                row, "selected", f"setting_summary.csv {factor}"
                ) != stats["selected"]:
            raise B3SelectionError(
                f"setting_summary.csv {factor}: selected flag disagrees "
                "with the recomputed ranking")
    _revalidate_signatures(signatures)
    return {
        "manifest": manifest,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "decision": decision,
        "summary_rows": summary,
        "recomputed": recomputed,
        "raw_binding": raw_binding,
        "raw_snapshot": live_raw["_snapshot"],
        "runs_dir": live_raw["_runs"],
        "signatures": signatures,
    }


def _refuse_a6_path(path: Path, label: str) -> None:
    """The A6 holdout boundary is absolute: no selector path may point at
    an A6 tree.  Checked on the RESOLVED real path before any read."""
    for part in path.parts:
        if "a6" in part.lower():
            raise B3SelectionError(
                f"{label} {path} crosses the A6 holdout boundary; refusing")


def _refuse_symlinked_parents(path: Path, label: str) -> None:
    """Every existing component of the ABSOLUTE (unresolved) path must be a
    real directory, so a symlinked parent cannot alias the publication."""
    probe = path.absolute()
    for candidate in (probe, *probe.parents):
        if candidate.is_symlink():
            raise B3SelectionError(
                f"{label} has a symlinked component: {candidate}")


def select(runs_dir: str | os.PathLike,
           analysis_dir: str | os.PathLike,
           out_dir: str | os.PathLike,
           selection_code_commit: str, *,
           verify_code_commit: bool = True,
           expected_raw_anchor: dict | None = None) -> str:
    """Freeze the confirmation selection from a GO decision; refuse
    everything else without partial output."""
    # publication isolation is settled BEFORE any input read
    runs_real = Path(runs_dir).resolve()
    analysis_real = Path(analysis_dir).resolve()
    out_real = Path(out_dir).resolve()
    _refuse_a6_path(runs_real, "runs dir")
    _refuse_a6_path(analysis_real, "analysis dir")
    _refuse_a6_path(out_real, "output dir")
    _refuse_symlinked_parents(Path(runs_dir), "runs dir")
    _refuse_symlinked_parents(Path(analysis_dir), "analysis dir")
    _refuse_symlinked_parents(Path(out_dir), "output dir")
    for left, right, left_label, right_label in (
            (runs_real, analysis_real, "runs dir", "analysis dir"),
            (runs_real, out_real, "runs dir", "output dir"),
            (analysis_real, out_real, "analysis dir", "output dir")):
        if left == right or left in right.parents or right in left.parents:
            raise B3SelectionError(
                f"{left_label} and {right_label} must be disjoint on "
                f"resolved real paths: {left} vs {right}")
    if verify_code_commit:
        verify_selection_code_commit(selection_code_commit)
    artifact = load_analysis_artifact(
        analysis_dir, runs_dir,
        expected_raw_anchor=expected_raw_anchor)
    decision = artifact["decision"]
    # the artifact loader has already proven DECISION.json equals the
    # recomputed decision; authorization gates on the RECOMPUTED values
    recomputed = artifact["recomputed"]
    state = recomputed["state"]
    if state != "GO":
        raise B3SelectionError(
            f"confirmation may be authorized only from GO; recomputed "
            f"decision state is {state!r}")
    factor = recomputed["selected_factor"]
    if factor not in bp.FROZEN_SELECTED_LEVELS:
        raise B3SelectionError(
            f"selected factor {factor!r} has no frozen level")
    direction = decision.get("direction_sign")
    if direction != DIRECTION_SIGN[factor]:
        raise B3SelectionError(
            "DECISION.json direction sign differs from the preregistered "
            "direction")
    thresholds = decision.get("thresholds") or {}
    if (thresholds.get("count_gate") != COUNT_GATE
            or thresholds.get("tau_delta") != bp.TAU_DELTA):
        raise B3SelectionError(
            "DECISION.json thresholds differ from the preregistered gates")
    count = recomputed["count"]
    med = recomputed["signed_median_midpoint"]
    boundary_margin = recomputed["boundary_margin"]
    boundary_adjacent = recomputed["boundary_adjacent"]
    if count < COUNT_GATE:
        raise B3SelectionError(
            f"GO decision with count {count!r} below the 9/12 gate is "
            "inconsistent")
    if med <= bp.TAU_DELTA:
        raise B3SelectionError(
            f"GO decision with signed median {med!r} <= tau_Delta is "
            "inconsistent")
    summary_selected = [row for row in artifact["summary_rows"]
                        if row["selected"] == "True"]
    if (len(summary_selected) != 1
            or summary_selected[0]["setting"] != factor):
        raise B3SelectionError(
            "setting_summary selected row differs from DECISION.json")

    if factor.startswith(("S1", "S2")):
        baseline_level = bp.BASELINE_BATTERY_KWH
    else:
        baseline_level = bp.BASELINE_POWER_KW
    population = json.loads(json.dumps(CONFIRMATION_POPULATION))
    population["settings"] = ["S0_baseline", factor]

    document = {
        "schema": SELECTION_SCHEMA,
        "campaign": "b3-factor-pilot",
        "state": "GO",
        "selected_factor": factor,
        "direction_sign": direction,
        "frozen_factor_level": bp.FROZEN_SELECTED_LEVELS[factor],
        "baseline_level": baseline_level,
        "zero_excluding_count": count,
        "count_gate": COUNT_GATE,
        "signed_median_midpoint": med,
        "signed_median_midpoint_repr":
            recomputed["signed_median_midpoint_repr"],
        "tau_delta": bp.TAU_DELTA,
        "boundary_margin": boundary_margin,
        "boundary_adjacent": boundary_adjacent,
        "boundary_adjacent_tolerance": BOUNDARY_ADJACENT_TOL,
        "boundary_review_required": boundary_adjacent,
        "authorization_state": (
            "HUMAN_REVIEW_REQUIRED" if boundary_adjacent
            else "AUTHORIZED_BY_FROZEN_RULE"),
        "boundary_policy": (
            "A boundary-adjacent decision requires human review before "
            "this selection authorizes any confirmation action."),
        "pilot": {
            "run_manifest_sha256":
                decision["inputs"]["run_manifest_sha256"],
            "analysis_manifest_sha256": artifact["manifest_sha256"],
            "analysis_code_commit": decision["analysis_code_commit"],
            "screen_record_sha256":
                decision["inputs"]["screen_record_sha256"],
            "spec_sha256": decision["inputs"]["spec_sha256"],
            "raw_binding": artifact["raw_binding"],
        },
        "certificate_integrity": {
            "attestation": "replayed-not-re-solved",
            "limitation": (
                "The analyzer proves internal consistency of recorded "
                "RMP/oracle and dictator evidence; it does not prove that "
                "the records came from real solver executions. Decision "
                "integrity therefore rests on provenance of the bound raw "
                "runs tree."),
            "pre_analysis_raw_anchor":
                artifact["raw_binding"]["pre_analysis_anchor"],
        },
        "selection_code_commit": selection_code_commit,
        "confirmation_population": population,
        "boundary": (
            "frozen only; no confirmation driver, launcher, or run exists; "
            "seeds 16-31 and A6 are never touched"),
    }
    payload = (json.dumps(document, indent=2, sort_keys=True)
               + "\n").encode()

    out_path = Path(out_dir)
    destination = out_path / SELECTION_FILENAME
    if out_path.exists() or out_path.is_symlink():
        raise B3SelectionError(
            f"refusing existing selection destination: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _refuse_symlinked_parents(out_path.parent, "output parent")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{out_path.name}.staging-", dir=out_path.parent))
    try:
        staged_selection = staging / SELECTION_FILENAME
        descriptor = os.open(
            staged_selection, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            def revalidate_inputs():
                _revalidate_signatures(artifact["signatures"])
                try:
                    current_raw = snapshot_source(artifact["runs_dir"])
                except PackagingError as exc:
                    raise B3SelectionError(
                        f"raw runs tree changed before selection commit: "
                        f"{exc}") from exc
                if current_raw != artifact["raw_snapshot"]:
                    raise B3SelectionError(
                        "raw runs tree changed before selection commit")

            publish_flat_directory_no_replace(
                staging, out_path, expected_names={SELECTION_FILENAME},
                revalidate=revalidate_inputs)
        except PackagingError as exc:
            if isinstance(exc.__cause__, B3SelectionError):
                raise exc.__cause__
            raise B3SelectionError(str(exc)) from exc
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return str(destination)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--selection-code-commit", required=True)
    args = ap.parse_args()
    print(select(
        args.runs, args.analysis_dir, args.out,
        args.selection_code_commit))


if __name__ == "__main__":
    main()
