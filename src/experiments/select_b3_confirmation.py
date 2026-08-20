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
    BASELINE_SETTING,
    CELL_INTERVAL_COLUMNS,
    COUNT_GATE,
    DECISION_SCHEMA,
    DIRECTION_SIGN,
    FACTOR_ORDER,
    MATCHED_CONTRAST_COLUMNS,
    SETTING_SUMMARY_COLUMNS,
    SCHEMA as ANALYSIS_SCHEMA,
    TAU_DELTA,
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


def _read_bytes_once(path: Path, label: str) -> bytes:
    """Read each input file's bytes exactly once; hashing and parsing use
    THESE bytes (no hash-close-reopen-parse window)."""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise B3SelectionError(f"{label}: unreadable") from exc


def _csv_rows_from_bytes(raw: bytes, expected_columns: list[str],
                         label: str) -> list[dict]:
    import csv
    import io
    reader = csv.DictReader(io.StringIO(raw.decode()))
    if list(reader.fieldnames or ()) != expected_columns:
        raise B3SelectionError(f"{label}: column layout differs")
    return list(reader)


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
            ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B3SelectionError(
            f"{label}: commit {commit} does not resolve") from exc
    if resolved != commit:
        raise B3SelectionError(f"{label}: commit resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B3SelectionError(
            f"{label}: commit {commit} is not an ancestor of the current "
            "branch")


def recompute_decision(cells: list[dict],
                       contrasts: list[dict]) -> dict:
    """Independently recompute the FULL preregistered decision from the
    primitive tables: 60 cell intervals -> 48 matched contrasts ->
    direction signs -> zero-excluding counts -> signed medians ->
    count/median/factor-order ranking -> state.  The recorded
    matched_contrasts rows are cross-checked field by field."""
    import statistics
    interval = {}
    for row in cells:
        key = (row["setting"], int(row["seed"]), int(row["n_trips"]),
               row["b"])
        if key in interval:
            raise B3SelectionError(
                f"cell_intervals.csv: duplicate cell {key}")
        interval[key] = {"lo_raw": float(row["u_lo_raw"]),
                         "lo": float(row["u_lo_tightened"]),
                         "hi": float(row["u_hi"])}
    expected_keys = {
        (cell["setting"], cell["seed"], cell["n_trips"], f"{cell['b']:g}")
        for cell in bp.build_cells()}
    if set(interval) != expected_keys:
        raise B3SelectionError(
            "cell_intervals.csv does not cover the frozen 60-cell grid "
            "exactly")
    recorded = {}
    for row in contrasts:
        key = (row["setting"], int(row["seed"]), int(row["n_trips"]),
               row["b"])
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
            zero_excluding = (lo > 0) if sign > 0 else (hi < 0)
            row = recorded.get(key)
            if row is None:
                raise B3SelectionError(
                    f"matched_contrasts.csv: missing contrast {key}")
            for field, value in (
                    ("delta_lo", lo), ("delta_hi", hi),
                    ("delta_midpoint", midpoint)):
                if float(row[field]) != value:
                    raise B3SelectionError(
                        f"matched_contrasts.csv {key}: recorded {field} "
                        f"{row[field]} != recomputed {value!r}")
            if int(row["direction_sign"]) != sign:
                raise B3SelectionError(
                    f"matched_contrasts.csv {key}: direction_sign differs "
                    "from the preregistered sign")
            if (row["direction_consistent_zero_excluding"] == "True") \
                    != zero_excluding:
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
    f_star = ranked[0]
    med_star = per_setting[f_star]["signed_median_midpoint"]
    count_star = per_setting[f_star]["count"]
    if abs(med_star) <= TAU_DELTA:
        state = "UNDER-RESOLVED"
    elif med_star > TAU_DELTA and count_star >= COUNT_GATE:
        state = "GO"
    else:
        state = "NO-GO"
    return {"state": state, "selected_factor": f_star,
            "count": count_star, "signed_median_midpoint": med_star,
            "per_setting": per_setting, "ranked": ranked}


def load_analysis_artifact(analysis_dir: str | os.PathLike) -> dict:
    """Load and fully validate the completed analysis artifact with
    transactional single reads, frozen-constant provenance, and a FULL
    independent recomputation of the decision from primitives."""
    base = Path(analysis_dir)
    manifest_path = base / "MANIFEST.json"
    if not manifest_path.is_file():
        raise B3SelectionError(f"missing analysis manifest: {manifest_path}")
    manifest_bytes = _read_bytes_once(manifest_path, "MANIFEST.json")
    manifest = json.loads(manifest_bytes)
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
    expected_spec_sha = sha256_file(REPO_ROOT / bp.SPEC_RELPATH)
    if (manifest.get("spec") or {}).get("sha256") != expected_spec_sha:
        raise B3SelectionError(
            "analysis spec SHA differs from the committed specification")
    _require_commit_in_history(
        manifest.get("analysis_code_commit"), "analysis_code_commit")

    outputs = manifest.get("outputs") or {}
    required = {"DECISION.json", "SUMMARY.md", "cell_intervals.csv",
                "matched_contrasts.csv", "setting_summary.csv"}
    if set(outputs) != required:
        raise B3SelectionError(
            "analysis manifest outputs are incomplete for a scoreable "
            f"population: {sorted(outputs)}")
    raw_by_name = {}
    for name, recorded in outputs.items():
        path = base / name
        if not path.is_file():
            raise B3SelectionError(f"missing analysis table: {name}")
        raw = _read_bytes_once(path, name)
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
    decision = json.loads(raw_by_name["DECISION.json"])
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
                ("signed_median_midpoint", "signed_median_midpoint"))),
            ("MANIFEST.json[decision]", manifest_decision, (
                ("state", "state"),
                ("selected_factor", "selected_contrast"),
                ("count", "count"),
                ("signed_median_midpoint", "signed_median_midpoint")))):
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
    # setting_summary must agree with the recomputation too
    for row in summary:
        factor = row["setting"]
        stats = recomputed["per_setting"].get(factor)
        if stats is None:
            raise B3SelectionError(
                f"setting_summary.csv: unexpected factor {factor!r}")
        if int(row["zero_excluding_count"]) != stats["count"]:
            raise B3SelectionError(
                f"setting_summary.csv {factor}: zero_excluding_count "
                "disagrees with the recomputed decision")
        if float(row["signed_median_midpoint"]) != (
                stats["signed_median_midpoint"]):
            raise B3SelectionError(
                f"setting_summary.csv {factor}: signed_median_midpoint "
                "disagrees with the recomputed decision")
        if (row["selected"] == "True") != (
                factor == recomputed["selected_factor"]):
            raise B3SelectionError(
                f"setting_summary.csv {factor}: selected flag disagrees "
                "with the recomputed ranking")
    return {
        "manifest": manifest,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "decision": decision,
        "summary_rows": summary,
        "recomputed": recomputed,
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


def select(analysis_dir: str | os.PathLike, out_dir: str | os.PathLike,
           selection_code_commit: str, *,
           verify_code_commit: bool = True) -> str:
    """Freeze the confirmation selection from a GO decision; refuse
    everything else without partial output."""
    # publication isolation is settled BEFORE any input read
    analysis_real = Path(analysis_dir).resolve()
    out_real = Path(out_dir).resolve()
    _refuse_a6_path(analysis_real, "analysis dir")
    _refuse_a6_path(out_real, "output dir")
    _refuse_symlinked_parents(Path(analysis_dir), "analysis dir")
    _refuse_symlinked_parents(Path(out_dir), "output dir")
    if out_real == analysis_real or out_real in analysis_real.parents \
            or analysis_real in out_real.parents:
        raise B3SelectionError(
            "output dir and analysis dir must be disjoint on resolved "
            f"real paths: {out_real} vs {analysis_real}")
    if verify_code_commit:
        verify_selection_code_commit(selection_code_commit)
    artifact = load_analysis_artifact(analysis_dir)
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
    # atomic publication: the full payload is written and fsynced to a
    # temp file first, then linked into place with no-replace semantics.
    # An O_EXCL-create-then-write would expose a partially written
    # SELECTION.json under the final name; this never does.
    temp = out_path / f".{SELECTION_FILENAME}.tmp-{os.getpid()}"
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp, destination)
        except FileExistsError as exc:
            raise B3SelectionError(
                f"refusing existing selection destination: "
                f"{destination}") from exc
    finally:
        temp.unlink(missing_ok=True)
    dir_fd = os.open(out_path, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
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
