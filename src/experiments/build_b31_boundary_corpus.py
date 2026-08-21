"""B31 switch-boundary corpus builder (solver-free, deterministic).

Reconstructs every adjacent interval of the committed Phase-2
fine-boundary sweeps into a leakage-safe learning corpus, re-verifying
the producer's hashes, classifications, and margin logic WITHOUT
importing any solver, EVSP, or boundary module.

Specification: doc/B31_BOUNDARY_CORPUS_SPEC.md.  Stdlib only; a
regression enforces the import closure.  The production CLI is pinned to
the canonical input; alternate inputs exist only as test-injection
parameters.  ``--validate-only`` runs every gate read-only and writes
nothing.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

SCHEMA = "b31-boundary-corpus-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_RELDIR = "result/boundary_fine/20260816T180507Z"
CANONICAL_INPUT = REPO_ROOT / CANONICAL_RELDIR
PINNED_CHECKPOINTS_SHA256 = (
    "b9807ab8f8b50094e5bd4ebceb507b87eabd1c546372fb54d35906e8420ba4a1")
BASE_COMMIT = "740ab0c1578b454268102c0bb15b1104d9ac8d9d"

# frozen sweep design (validated, never inferred)
SEEDS = tuple(range(8))
N_TRIPS = (8, 12)
SLOTS = (8, 12, 16, 20)
N_POINTS = 301
DELTA_START = -1.5
DELTA_STEP = 0.01
DELTA_TOL = 1e-9

# producer constants replicated from egglab.boundary (NOT imported)
LOAD_TOL_KWH = 1.0
MARGIN_TOL = 1e-3
MARGIN_NOISE_FLOOR = -1e-9  # committed minimum is ~-4.5e-13
L1_MATCH_TOL = 1e-9
SWITCH_KINDS = ("degenerate_tie", "charging_only", "duty_change",
                "fleet_change")

# exact totals on the canonical input (fail-closed gates)
EXPECTED_TOTALS = {
    "sweeps": 64,
    "points": 19264,
    "intervals": 19200,
    "stable": 16460,
    "degenerate_tie": 2559,
    "charging_only": 35,
    "duty_change": 146,
    "fleet_change": 0,
    "margin_ties": 89,
    "economic_charging_only": 35,
    "economic_duty_change": 57,
    "economic_fleet_change": 0,
    "degenerate_schedule_preserving": 1,
}

# whole-seed split (leakage-safe)
SPLIT_BY_SEED = {
    "train": (0, 1, 2, 3, 4),
    "validation": (5,),
    "test": (6, 7),
}

# features derive ONLY from the left endpoint and exogenous design
FEATURE_COLUMNS = (
    "seed", "n_trips", "slot", "idx_left", "delta_left", "delta_right",
    "left_obj", "left_fleet", "left_load_slot", "left_energy_total",
    "left_schedule_hash", "left_load_hash",
)
OUTCOME_COLUMNS = (
    "stable", "kind", "schedule_changed", "fleet_change", "load_l1",
    "load_jump_slot", "tie_margin", "economic",
    "margin_b_at_a", "margin_a_at_b",
)
EVIDENCE_LIMITS = (
    "\"Stable\" means stability at HASH RESOLUTION: equal schedule hash "
    "and equal two-decimal load hash; it is not a proof that the two "
    "optima are identical below two-decimal load resolution.",
    "Charging-only changes never received the margin test: the producer "
    "ran cross-realization margins only for duty and fleet changes, so "
    "economic charging-only counts carry no margin certification.",
    "Exactly one degenerate row does not change the route partition "
    "(schedule_changed == false): a two-decimal load-hash flip with an "
    "unchanged duty partition.",
    "Tiny negative margins down to solver noise are allowed (committed "
    "minimum ~-4.5e-13); validation admits margins >= -1e-9 and rejects "
    "anything more negative.",
)

PROVENANCE_FILES = (
    "src/experiments/build_b31_boundary_corpus.py",
    "src/tests/test_b31_boundary_corpus.py",
    "doc/B31_BOUNDARY_CORPUS_SPEC.md",
)


class B31Error(RuntimeError):
    """The corpus cannot be built without weakening its contract."""


def sha256_file(path: str | os.PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoints_digest(root: str | os.PathLike) -> tuple[str, int]:
    """Producer-compatible combined digest (analyze_closeout recipe):
    sorted relpaths; per file, relpath bytes then lowercase hex SHA-256
    of the file bytes."""
    h = hashlib.sha256()
    files = sorted(glob.glob(
        os.path.join(str(root), "checkpoints", "*", "*.ckpt.json")))
    for fp in files:
        rel = os.path.relpath(fp, str(root))
        h.update(rel.encode())
        h.update(sha256_file(fp).encode())
    return h.hexdigest(), len(files)


# --------------------------------------------------------------------------
# replicated producer semantics (verified against the committed evidence)
# --------------------------------------------------------------------------
def _norm2(x: float) -> float:
    """Producer's ``_norm(x, 2)``: round to two decimals, normalize -0.0."""
    v = round(float(x), 2)
    return v + 0.0 if v != 0 else 0.0


def schedule_hash(sequences) -> str:
    canon = sorted(tuple(seq) for seq in sequences)
    return hashlib.sha256(json.dumps(canon).encode()).hexdigest()[:12]


def load_hash(load) -> str:
    canon = [_norm2(x) for x in load]
    return hashlib.sha256(json.dumps(canon).encode()).hexdigest()[:12]


def classify_pair(a: dict, b: dict) -> dict | None:
    """Replica of egglab.boundary.classify_pair (sequential L1 sum)."""
    if (a["schedule_hash"] == b["schedule_hash"]
            and a["load_hash"] == b["load_hash"]):
        return None
    if len(a["load"]) != len(b["load"]):
        raise B31Error("adjacent points have different load lengths")
    load_l1 = 0.0
    for xa, xb in zip(a["load"], b["load"]):
        load_l1 += abs(float(xa) - float(xb))
    if b["fleet"] != a["fleet"]:
        kind = "fleet_change"
    elif load_l1 <= LOAD_TOL_KWH:
        kind = "degenerate_tie"
    elif a["schedule_hash"] != b["schedule_hash"]:
        kind = "duty_change"
    else:
        kind = "charging_only"
    return {
        "between_deltas": [a["delta"], b["delta"]],
        "kind": kind,
        "load_l1": load_l1,
        "load_jump_slot": (float(b.get("load_slot", 0.0))
                           - float(a.get("load_slot", 0.0))),
        "fleet_change": b["fleet"] - a["fleet"],
        "schedule_changed": a["schedule_hash"] != b["schedule_hash"],
    }


def assert_no_feature_leakage(features=FEATURE_COLUMNS) -> None:
    """Right-endpoint solution values are outcomes-only."""
    for name in features:
        if name.startswith("right_") or name in OUTCOME_COLUMNS:
            raise B31Error(
                f"feature column {name!r} leaks right-endpoint or outcome "
                "information")


def _fin(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(
        value, bool) and math.isfinite(value)


def verify_build_provenance(claimed: str) -> bool:
    """Full-SHA attribution: the claimed commit resolves, is an ancestor
    of (or equal to) HEAD, the frozen base is an ancestor of HEAD (not
    necessarily equal), the tracked tree is clean, and the builder,
    specification, and battery are byte-identical to the claimed
    commit."""
    if (not claimed or len(claimed) != 40
            or not all(c in "0123456789abcdef" for c in claimed)):
        raise B31Error(
            "analysis-code-commit must be the full 40-character lowercase "
            "hexadecimal SHA")
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{claimed}^{{commit}}"],
            cwd=REPO_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError as exc:
        raise B31Error(f"claimed commit {claimed} does not resolve") from exc
    if resolved != claimed:
        raise B31Error(f"claimed commit {claimed} resolves to {resolved}")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", claimed, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B31Error(
            f"claimed commit {claimed} is not an ancestor of HEAD")
    if subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
            cwd=REPO_ROOT).returncode != 0:
        raise B31Error(
            f"frozen base {BASE_COMMIT} is not an ancestor of HEAD")
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT).decode()
    tracked_dirty = [
        line for line in dirty.splitlines() if not line.startswith("??")]
    if tracked_dirty:
        raise B31Error(
            "working tree has tracked modifications; commit the builder "
            "before generating artifacts")
    for relpath in PROVENANCE_FILES:
        committed = subprocess.check_output(
            ["git", "show", f"{claimed}:{relpath}"], cwd=REPO_ROOT)
        if committed != (REPO_ROOT / relpath).read_bytes():
            raise B31Error(
                f"{relpath} differs from the claimed correction commit "
                f"{claimed}; artifacts would be misattributed")
    return True


# --------------------------------------------------------------------------
# canonical input loading and fail-closed validation
# --------------------------------------------------------------------------
def _sweep_identity(dirname: str) -> tuple[int, int, int]:
    try:
        seed_part, n_part, slot_part = dirname.split("_")
        if (not seed_part.startswith("s") or not n_part.startswith("n")
                or not slot_part.startswith("slot")):
            raise ValueError(dirname)
        return (int(seed_part[1:]), int(n_part[1:]), int(slot_part[4:]))
    except ValueError as exc:
        raise B31Error(f"malformed sweep directory name: {dirname}") from exc


def seed_split(seed: int) -> str:
    for split, seeds in SPLIT_BY_SEED.items():
        if seed in seeds:
            return split
    raise B31Error(f"seed {seed} is not assigned to any split")


def _validate_point(point: dict, idx: int, label: str) -> None:
    if point.get("idx") != idx:
        raise B31Error(f"{label}: point index {point.get('idx')} != {idx}")
    expected_delta = DELTA_START + DELTA_STEP * idx
    delta = point.get("delta")
    if not _fin(delta) or abs(delta - expected_delta) > DELTA_TOL:
        raise B31Error(
            f"{label}: delta {delta!r} off-grid (expected "
            f"{expected_delta})")
    for field in ("obj", "load_slot", "energy_total"):
        if not _fin(point.get(field)):
            raise B31Error(f"{label}: point field {field} is not finite")
    if not isinstance(point.get("fleet"), int) or isinstance(
            point.get("fleet"), bool):
        raise B31Error(f"{label}: point fleet is not an integer")
    load = point.get("load")
    if not isinstance(load, list) or not load or not all(
            _fin(x) for x in load):
        raise B31Error(f"{label}: point load vector is invalid")
    sequences = point.get("sequences")
    if not isinstance(sequences, list) or not all(
            isinstance(seq, list) for seq in sequences):
        raise B31Error(f"{label}: point sequences are invalid")
    if schedule_hash(sequences) != point.get("schedule_hash"):
        raise B31Error(
            f"{label}: schedule_hash does not recompute from sequences")
    if load_hash(load) != point.get("load_hash"):
        raise B31Error(
            f"{label}: load_hash does not recompute from the load vector")


def _reconcile_switch(stored: dict, recomputed: dict, label: str) -> None:
    if stored.get("kind") != recomputed["kind"]:
        raise B31Error(
            f"{label}: stored kind {stored.get('kind')!r} != recomputed "
            f"{recomputed['kind']!r}")
    if stored.get("between_deltas") != recomputed["between_deltas"]:
        raise B31Error(f"{label}: between_deltas disagree")
    if stored.get("schedule_changed") != recomputed["schedule_changed"]:
        raise B31Error(f"{label}: schedule_changed disagrees")
    if stored.get("fleet_change") != recomputed["fleet_change"]:
        raise B31Error(f"{label}: fleet_change disagrees")
    for field in ("load_l1", "load_jump_slot"):
        if not _fin(stored.get(field)) or abs(
                stored[field] - recomputed[field]) > L1_MATCH_TOL:
            raise B31Error(
                f"{label}: stored {field}={stored.get(field)!r} deviates "
                f"from recomputed {recomputed[field]!r}")
    if stored["kind"] in ("duty_change", "fleet_change"):
        margins = []
        for field in ("margin_b_at_a", "margin_a_at_b"):
            if field not in stored:
                raise B31Error(
                    f"{label}: {stored['kind']} switch lacks {field}")
            value = stored[field]
            if value is not None:
                if not _fin(value):
                    raise B31Error(f"{label}: {field} is not finite")
                if value < MARGIN_NOISE_FLOOR:
                    raise B31Error(
                        f"{label}: {field}={value} below the solver-noise "
                        f"floor {MARGIN_NOISE_FLOOR}")
                margins.append(value)
        if type(stored.get("tie_margin")) is not bool:
            raise B31Error(f"{label}: tie_margin is not exactly a bool")
        expected_tie = bool(margins and min(margins) <= MARGIN_TOL)
        if stored["tie_margin"] != expected_tie:
            raise B31Error(
                f"{label}: tie_margin={stored['tie_margin']} but the "
                f"stored margins replay {expected_tie}")
    else:
        for field in ("margin_b_at_a", "margin_a_at_b", "tie_margin"):
            if field in stored:
                raise B31Error(
                    f"{label}: {stored['kind']} switch must not carry "
                    f"{field} (charging-only changes never received the "
                    "margin test)")


def load_canonical_sweeps(input_dir: str | os.PathLike,
                          expected_totals: dict | None = None) -> dict:
    """Load, digest-pin, and fail-closed-validate all sweeps; reconstruct
    every adjacent interval."""
    input_dir = Path(input_dir)
    expected_totals = dict(
        EXPECTED_TOTALS if expected_totals is None else expected_totals)
    digest, n_files = checkpoints_digest(input_dir)
    if digest != PINNED_CHECKPOINTS_SHA256:
        raise B31Error(
            "canonical checkpoints digest mismatch: pinned "
            f"{PINNED_CHECKPOINTS_SHA256} but the tree digests to "
            f"{digest}")
    expected_ids = {(s, n, slot) for s in SEEDS for n in N_TRIPS
                    for slot in SLOTS}
    if n_files != len(expected_ids):
        raise B31Error(
            f"expected {len(expected_ids)} sweep checkpoints, found "
            f"{n_files}")

    sweeps = []
    intervals = []
    totals = {
        "sweeps": 0, "points": 0, "intervals": 0, "stable": 0,
        "degenerate_tie": 0, "charging_only": 0, "duty_change": 0,
        "fleet_change": 0, "margin_ties": 0,
        "economic_charging_only": 0, "economic_duty_change": 0,
        "economic_fleet_change": 0, "degenerate_schedule_preserving": 0,
    }
    seen_ids = set()
    for path in sorted(
            (input_dir / "checkpoints").iterdir(), key=lambda p: p.name):
        dirname = path.name
        seed, n_trips, slot = _sweep_identity(dirname)
        key = (seed, n_trips, slot)
        if key not in expected_ids or key in seen_ids:
            raise B31Error(f"sweep {dirname} outside or duplicating the "
                           "frozen grid")
        seen_ids.add(key)
        ck = json.loads((path / "sweep.ckpt.json").read_text())
        label = f"sweep {dirname}"
        if ck.get("done") is not True or ck.get("margins_done") is not True:
            raise B31Error(f"{label}: checkpoint is not complete")
        points = ck.get("points")
        if not isinstance(points, list) or len(points) != N_POINTS:
            raise B31Error(
                f"{label}: expected {N_POINTS} points, found "
                f"{len(points) if isinstance(points, list) else points!r}")
        for idx, point in enumerate(points):
            _validate_point(point, idx, f"{label} point {idx}")
        stored_switches = list(ck.get("switches") or ())
        split = seed_split(seed)
        counts = {kind: 0 for kind in SWITCH_KINDS}
        n_stable = 0
        n_ties = 0
        n_economic = 0
        switch_cursor = 0
        for a, b in zip(points, points[1:]):
            pair_label = f"{label} interval idx={a['idx']}"
            recomputed = classify_pair(a, b)
            outcome = {
                "stable": recomputed is None,
                "kind": "stable" if recomputed is None
                        else recomputed["kind"],
                "schedule_changed": (False if recomputed is None
                                     else recomputed["schedule_changed"]),
                "fleet_change": (0 if recomputed is None
                                 else recomputed["fleet_change"]),
                "load_l1": (0.0 if recomputed is None
                            else recomputed["load_l1"]),
                "load_jump_slot": (0.0 if recomputed is None
                                   else recomputed["load_jump_slot"]),
                "tie_margin": "", "economic": False,
                "margin_b_at_a": "", "margin_a_at_b": "",
            }
            if recomputed is None:
                n_stable += 1
            else:
                if switch_cursor >= len(stored_switches):
                    raise B31Error(
                        f"{pair_label}: recomputed switch has no stored "
                        "counterpart")
                stored = stored_switches[switch_cursor]
                switch_cursor += 1
                _reconcile_switch(stored, recomputed, pair_label)
                counts[recomputed["kind"]] += 1
                tie = bool(stored.get("tie_margin", False))
                economic = (recomputed["kind"] in (
                    "charging_only", "duty_change", "fleet_change")
                    and not tie)
                if recomputed["kind"] in ("duty_change", "fleet_change"):
                    outcome["tie_margin"] = tie
                    outcome["margin_b_at_a"] = stored["margin_b_at_a"]
                    outcome["margin_a_at_b"] = stored["margin_a_at_b"]
                    if tie:
                        n_ties += 1
                outcome["economic"] = economic
                if economic:
                    n_economic += 1
                    totals[f"economic_{recomputed['kind']}"] += 1
                if (recomputed["kind"] == "degenerate_tie"
                        and not recomputed["schedule_changed"]):
                    totals["degenerate_schedule_preserving"] += 1
            intervals.append({
                "sweep_id": dirname, "seed": seed, "n_trips": n_trips,
                "slot": slot, "split": split,
                "idx_left": a["idx"], "delta_left": a["delta"],
                "delta_right": b["delta"],
                "left_obj": a["obj"], "left_fleet": a["fleet"],
                "left_load_slot": a["load_slot"],
                "left_energy_total": a["energy_total"],
                "left_schedule_hash": a["schedule_hash"],
                "left_load_hash": a["load_hash"],
                **outcome,
            })
        if switch_cursor != len(stored_switches):
            raise B31Error(
                f"{label}: {len(stored_switches) - switch_cursor} stored "
                "switches have no recomputed counterpart")
        stored_counts = ck.get("counts_by_kind") or {}
        if stored_counts != counts:
            raise B31Error(
                f"{label}: stored counts_by_kind {stored_counts} != "
                f"recomputed {counts}")
        if ck.get("n_switches") != sum(counts.values()):
            raise B31Error(f"{label}: n_switches does not replay")
        if ck.get("n_economic_switches") != n_economic:
            raise B31Error(f"{label}: n_economic_switches does not replay")
        totals["sweeps"] += 1
        totals["points"] += len(points)
        totals["intervals"] += len(points) - 1
        totals["stable"] += n_stable
        totals["margin_ties"] += n_ties
        for kind in SWITCH_KINDS:
            totals[kind] += counts[kind]
        sweeps.append({
            "sweep_id": dirname, "seed": seed, "n_trips": n_trips,
            "slot": slot, "split": split,
            "n_points": len(points), "n_intervals": len(points) - 1,
            "n_stable": n_stable,
            "n_degenerate_tie": counts["degenerate_tie"],
            "n_charging_only": counts["charging_only"],
            "n_duty_change": counts["duty_change"],
            "n_fleet_change": counts["fleet_change"],
            "n_margin_ties": n_ties,
            "n_economic": n_economic,
        })
    if seen_ids != expected_ids:
        raise B31Error("sweep set does not cover the frozen grid exactly")
    for key, expected in expected_totals.items():
        if totals[key] != expected:
            raise B31Error(
                f"exact-total gate failed: {key} = {totals[key]}, "
                f"expected {expected}")
    # input mutation detection: the tree must digest identically AFTER
    # the full parse and reconstruction
    post_digest, _ = checkpoints_digest(input_dir)
    if post_digest != digest:
        raise B31Error("canonical input mutated during the build")
    return {"sweeps": sweeps, "intervals": intervals, "totals": totals,
            "digest": digest}


# --------------------------------------------------------------------------
# deterministic publication
# --------------------------------------------------------------------------
def _format(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_format(row[column]) for column in columns])


SWEEP_COLUMNS = [
    "sweep_id", "seed", "n_trips", "slot", "split",
    "n_points", "n_intervals", "n_stable",
    "n_degenerate_tie", "n_charging_only", "n_duty_change",
    "n_fleet_change", "n_margin_ties", "n_economic",
]
INTERVAL_COLUMNS = (
    ["sweep_id", "split"]
    + [c for c in FEATURE_COLUMNS]
    + [c for c in OUTCOME_COLUMNS]
)


def build(input_dir: str | os.PathLike, out_base: str | os.PathLike,
          stamp: str, analysis_code_commit: str, *,
          verify_code_commit: bool = True,
          expected_totals: dict | None = None,
          validate_only: bool = False) -> str | dict:
    assert_no_feature_leakage()
    if verify_code_commit and not validate_only:
        verify_build_provenance(analysis_code_commit)
    data = load_canonical_sweeps(input_dir, expected_totals)
    if validate_only:
        return data["totals"]

    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    out_dir = out_base / stamp
    if out_dir.exists():
        raise B31Error(f"refusing existing output directory: {out_dir}")
    staging = Path(tempfile.mkdtemp(
        prefix=f".{stamp}.b31-staging-", dir=out_base))
    try:
        write_csv(staging / "sweeps.csv", data["sweeps"], SWEEP_COLUMNS)
        write_csv(staging / "intervals.csv", data["intervals"],
                  INTERVAL_COLUMNS)
        feature_schema = {
            "schema": SCHEMA,
            "features": list(FEATURE_COLUMNS),
            "outcomes": list(OUTCOME_COLUMNS),
            "leakage_rule": (
                "Features derive ONLY from the LEFT interval endpoint and "
                "exogenous design variables; right-endpoint solution "
                "values are outcomes-only and any right_* feature is "
                "refused."),
            "split_rule": (
                "Whole-seed split: every sweep and interval of a seed "
                "belongs to exactly one split."),
            "evidence_limits": list(EVIDENCE_LIMITS),
        }
        with open(staging / "feature_schema.json", "w") as handle:
            json.dump(feature_schema, handle, indent=2, sort_keys=True)
            handle.write("\n")
        split_manifest = {"schema": SCHEMA, "by_seed": {
            split: list(seeds) for split, seeds in SPLIT_BY_SEED.items()}}
        for split in SPLIT_BY_SEED:
            sweep_ids = sorted(
                s["sweep_id"] for s in data["sweeps"]
                if s["split"] == split)
            split_manifest[split] = {
                "sweeps": sweep_ids,
                "n_sweeps": len(sweep_ids),
                "n_intervals": sum(
                    s["n_intervals"] for s in data["sweeps"]
                    if s["split"] == split),
            }
        with open(staging / "SPLIT_MANIFEST.json", "w") as handle:
            json.dump(split_manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
        outputs = sorted([
            "sweeps.csv", "intervals.csv", "feature_schema.json",
            "SPLIT_MANIFEST.json"])
        manifest = {
            "schema": SCHEMA,
            "stamp": stamp,
            "analysis_code_commit": analysis_code_commit,
            "analysis_code_verified": verify_code_commit,
            "base_commit": BASE_COMMIT,
            "inputs": {
                "checkpoints": {
                    "path": f"{CANONICAL_RELDIR}/checkpoints",
                    "combined_sha256": data["digest"],
                    "n_files": data["totals"]["sweeps"],
                },
            },
            "totals": data["totals"],
            "tolerances": {
                "load_tol_kwh": LOAD_TOL_KWH,
                "margin_tol": MARGIN_TOL,
                "margin_noise_floor": MARGIN_NOISE_FLOOR,
                "l1_match_tol": L1_MATCH_TOL,
                "delta_tol": DELTA_TOL,
            },
            "evidence_limits": list(EVIDENCE_LIMITS),
            "csv_headers": {
                "sweeps.csv": SWEEP_COLUMNS,
                "intervals.csv": INTERVAL_COLUMNS,
            },
            "outputs": {name: sha256_file(staging / name)
                        for name in outputs},
        }
        with open(staging / "MANIFEST.json", "w") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.rename(staging, out_dir)
    except BaseException:
        # the staging tree contains only files this run just wrote
        for entry in staging.glob("*"):
            entry.unlink()
        staging.rmdir()
        raise
    return str(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", default=str(REPO_ROOT / "result" / "b31_corpus"))
    parser.add_argument("--stamp")
    parser.add_argument("--analysis-code-commit")
    parser.add_argument(
        "--validate-only", action="store_true",
        help="read-only: run every gate on the canonical input, write "
             "nothing")
    args = parser.parse_args()
    if args.validate_only:
        totals = build(CANONICAL_INPUT, args.out, "validate-only", "",
                       validate_only=True)
        print(json.dumps(totals, indent=2, sort_keys=True))
        return
    if not args.stamp or not args.analysis_code_commit:
        parser.error("--stamp and --analysis-code-commit are required "
                     "unless --validate-only")
    # the production CLI is PINNED to the canonical input
    out_dir = build(CANONICAL_INPUT, args.out, args.stamp,
                    args.analysis_code_commit)
    print(out_dir)


if __name__ == "__main__":
    main()
