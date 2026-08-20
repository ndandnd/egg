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
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
from experiments.analyze_b3_factor_pilot import (
    CELL_INTERVAL_COLUMNS,
    DECISION_SCHEMA,
    DIRECTION_SIGN,
    MATCHED_CONTRAST_COLUMNS,
    SETTING_SUMMARY_COLUMNS,
    SCHEMA as ANALYSIS_SCHEMA,
)

SELECTION_SCHEMA = "b3-confirmation-selection-v1"
SELECTION_FILENAME = "SELECTION.json"
REPO_ROOT = Path(__file__).resolve().parents[2]

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
    "src/experiments/b3_factor_pilot.py",
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
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3SelectionError(
            f"claimed commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise B3SelectionError(
            f"claimed commit {claimed} resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B3SelectionError(
            f"claimed commit {claimed} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    if [line for line in dirty.splitlines() if not line.startswith("??")]:
        raise B3SelectionError(
            "working tree has tracked modifications; commit the selection "
            "code before freezing")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{relpath}"], cwd=REPO_ROOT)
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise B3SelectionError(
                f"{relpath} differs from the claimed commit {claimed}")
    return resolved


def _csv_rows(path: Path, expected_columns: list[str],
              label: str) -> list[dict]:
    import csv
    try:
        with open(path, newline="") as handle:
            reader = csv.DictReader(handle)
            if list(reader.fieldnames or ()) != expected_columns:
                raise B3SelectionError(f"{label}: column layout differs")
            return list(reader)
    except OSError as exc:
        raise B3SelectionError(f"{label}: unreadable") from exc


def load_analysis_artifact(analysis_dir: str | os.PathLike) -> dict:
    """Load and fully validate the completed analysis artifact: manifest
    schema, output hashes and row counts, table layouts and cardinality,
    and DECISION.json cross-binding."""
    base = Path(analysis_dir)
    manifest_path = base / "MANIFEST.json"
    if not manifest_path.is_file():
        raise B3SelectionError(f"missing analysis manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != ANALYSIS_SCHEMA:
        raise B3SelectionError(
            f"analysis manifest schema {manifest.get('schema')!r} is not "
            f"{ANALYSIS_SCHEMA!r}")
    outputs = manifest.get("outputs") or {}
    required = {"DECISION.json", "SUMMARY.md", "cell_intervals.csv",
                "matched_contrasts.csv", "setting_summary.csv"}
    if set(outputs) != required:
        raise B3SelectionError(
            "analysis manifest outputs are incomplete for a scoreable "
            f"population: {sorted(outputs)}")
    for name, recorded in outputs.items():
        path = base / name
        if not path.is_file():
            raise B3SelectionError(f"missing analysis table: {name}")
        actual = sha256_file(path)
        if actual != recorded:
            raise B3SelectionError(
                f"analysis table {name} hash mismatch (tampered): "
                f"{actual} != {recorded}")
    table_rows = manifest.get("table_rows") or {}
    cells = _csv_rows(base / "cell_intervals.csv", CELL_INTERVAL_COLUMNS,
                      "cell_intervals.csv")
    contrasts = _csv_rows(base / "matched_contrasts.csv",
                          MATCHED_CONTRAST_COLUMNS,
                          "matched_contrasts.csv")
    summary = _csv_rows(base / "setting_summary.csv",
                        SETTING_SUMMARY_COLUMNS, "setting_summary.csv")
    for name, rows, expected in (
            ("cell_intervals.csv", cells, bp.N_CELLS),
            ("matched_contrasts.csv", contrasts, bp.N_MATCHED_CONTRASTS),
            ("setting_summary.csv", summary, 4)):
        if len(rows) != expected or table_rows.get(name) != expected:
            raise B3SelectionError(
                f"{name}: row count {len(rows)} / manifest "
                f"{table_rows.get(name)} != expected {expected}")
    decision = json.loads((base / "DECISION.json").read_text())
    if decision.get("schema") != DECISION_SCHEMA:
        raise B3SelectionError("DECISION.json schema differs")
    for field in ("run_manifest_sha256", "screen_record_sha256",
                  "spec_sha256"):
        if decision.get("inputs", {}).get(field) is None:
            raise B3SelectionError(f"DECISION.json missing input {field}")
    if decision.get("analysis_code_commit") != manifest.get(
            "analysis_code_commit"):
        raise B3SelectionError(
            "DECISION.json / manifest analysis_code_commit mismatch")
    if decision.get("inputs", {}).get("run_manifest_sha256") != (
            manifest.get("run_manifest_sha256")):
        raise B3SelectionError(
            "DECISION.json / manifest run_manifest_sha256 mismatch")
    return {
        "manifest": manifest,
        "manifest_sha256": sha256_file(manifest_path),
        "decision": decision,
        "summary_rows": summary,
    }


def select(analysis_dir: str | os.PathLike, out_dir: str | os.PathLike,
           selection_code_commit: str, *,
           verify_code_commit: bool = True) -> str:
    """Freeze the confirmation selection from a GO decision; refuse
    everything else without partial output."""
    if verify_code_commit:
        verify_selection_code_commit(selection_code_commit)
    artifact = load_analysis_artifact(analysis_dir)
    decision = artifact["decision"]
    state = decision.get("state")
    if state != "GO":
        raise B3SelectionError(
            f"confirmation may be authorized only from GO; decision state "
            f"is {state!r}")
    factor = decision.get("selected_factor")
    if factor not in bp.FROZEN_SELECTED_LEVELS:
        raise B3SelectionError(
            f"selected factor {factor!r} has no frozen level")
    direction = decision.get("direction_sign")
    if direction != DIRECTION_SIGN[factor]:
        raise B3SelectionError(
            "DECISION.json direction sign differs from the preregistered "
            "direction")
    counts = decision.get("counts") or {}
    thresholds = decision.get("thresholds") or {}
    if (thresholds.get("count_gate") != 9
            or thresholds.get("tau_delta") != bp.TAU_DELTA):
        raise B3SelectionError(
            "DECISION.json thresholds differ from the preregistered gates")
    count = counts.get("zero_excluding_count")
    med = decision.get("signed_median_midpoint")
    if not isinstance(count, int) or count < 9:
        raise B3SelectionError(
            f"GO decision with count {count!r} below the 9/12 gate is "
            "inconsistent")
    if not isinstance(med, (int, float)) or med <= bp.TAU_DELTA:
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
        "count_gate": 9,
        "signed_median_midpoint": med,
        "tau_delta": bp.TAU_DELTA,
        "pilot": {
            "run_manifest_sha256":
                decision["inputs"]["run_manifest_sha256"],
            "analysis_manifest_sha256": artifact["manifest_sha256"],
            "analysis_code_commit": decision["analysis_code_commit"],
            "screen_record_sha256":
                decision["inputs"]["screen_record_sha256"],
            "spec_sha256": decision["inputs"]["spec_sha256"],
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
    if destination.exists() or destination.is_symlink():
        raise B3SelectionError(
            f"refusing existing selection destination: {destination}")
    out_path.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return str(destination)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--selection-code-commit", required=True)
    args = ap.parse_args()
    print(select(args.analysis_dir, args.out, args.selection_code_commit))


if __name__ == "__main__":
    main()
