#!/usr/bin/env python3
"""B3 factor-pilot replication comparator.

Compares two already-written 60-cell run trees for certificate agreement.
It does not launch jobs, does not import a solver, and never writes into
either input directory.  The original tree remains canonical regardless
of the verdict; a disagreement is an engineering incident, never a
choice of which run to score.

Normative freeze: ``doc/B3_REPLICATION_COMPARATOR_SPEC.md``.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.b3_factor_pilot as bp
from experiments.analyze_b3_factor_pilot import cell_interval
from experiments import b3_pilot_evidence as evidence

SCHEMA = "b3-replication-comparator-v1"

# --- frozen comparison contract (spec; committed before any replica exists)
N_CELLS = bp.N_CELLS                          # 60
REQUIRED_AGREEING_CELLS = 60                  # explicit 60/60; not a majority
ORIGINAL_IS_CANONICAL = True
REPLICA_MAY_SUBSTITUTE_ORIGINAL = False

# Machinery noise floor (SEK).  CG epsilon and dictator tol_d are both 1e-2.
# A comparator tighter than this is not meaningful for certificate replay.
ABS_TOL_SEK = bp.EPSILON                      # 1e-2
# Operand scale for serialization / float noise on large objectives.
REL_SCALE = 1e-10
# Physical replay tolerance is energy, not SEK.  Documented so it cannot
# be silently reused as a tighter objective threshold.
PHYSICAL_REPLAY_TOL_KWH = 1e-4
CG_EPSILON = bp.EPSILON                       # 1e-2
DICTATOR_TOL_D = bp.TOL_D                     # 1e-2

# Numeric certificate fields compared under operand-scaled SEK tolerance.
COMPARED_NUMERIC_FIELDS = (
    "lb_best",
    "ub_ch",
    "U_lo_raw",
    "U_hi",
    "z_D_lb",
    "z_D_ub",
)
COMPARED_BOOLEAN_FIELDS = ("certified",)
# Scientific identity / solve-path (exact).  Provenance is excluded.
SOLVE_PATH_FIELDS = (
    "setting",
    "seed",
    "n_trips",
    "b",
    "method",
    "epsilon",
    "tol_d",
    "budget",
    "instance_hash",
    "market_hash",
)
EXCLUDED_PROVENANCE_FIELDS = (
    "run_commit",
    "run_manifest_sha256",
    "run_manifest.json",
)

REQUIRED_CELL_FILES = (
    bp.CELL_IDENTITY_FILENAME,
    "a2.cg.ckpt.json",
    "dictator.ckpt.json",
)

STATUS_AGREE = "AGREE"
STATUS_INCOMPLETE = "INCOMPLETE_POPULATION"
STATUS_INCIDENT = "ENGINEERING_INCIDENT"


class ComparatorError(RuntimeError):
    """The comparator cannot emit an agreement verdict."""


def operand_scaled_allowance(left: float, right: float) -> float:
    """SEK allowance: CG-epsilon floor plus operand-scaled float noise."""
    return float(ABS_TOL_SEK) + float(REL_SCALE) * max(
        1.0, abs(float(left)), abs(float(right)))


def numbers_agree(left, right) -> bool:
    return abs(float(left) - float(right)) <= operand_scaled_allowance(
        left, right)


def is_finite_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _resolved(path: str | os.PathLike) -> Path:
    return Path(path).resolve()


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _cell_dirs(root: Path) -> dict[str, Path]:
    """Map directory names to paths; refuse following a symlink root."""
    if root.is_symlink():
        raise ComparatorError(f"refusing symlinked run root: {root}")
    if not root.is_dir():
        raise ComparatorError(f"run directory does not exist: {root}")
    found = {}
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink():
            raise ComparatorError(f"refusing symlinked entry: {entry}")
        if entry.is_dir():
            found[entry.name] = entry
    return found


def _load_json(path: Path):
    return evidence.strict_json_loads(evidence.read_regular_bytes_once(path))


def _required_files_present(cell_dir: Path) -> list[str]:
    missing = []
    for name in REQUIRED_CELL_FILES:
        path = cell_dir / name
        if path.is_symlink() or not path.is_file():
            missing.append(name)
    return missing


def expected_cell_tags() -> tuple[str, ...]:
    return tuple(cell["tag"] for cell in bp.build_cells())


def extract_certificate(cell_dir: Path, tag: str) -> dict:
    """Replay one cell's recorded evidence into the compared certificate.

    Bounds are taken from committed histories the same way the analyzer
    does: ``ub_ch`` is the last ``ub_history`` entry, ``lb_best`` is the
    max of ``lb_history``.  Uplift endpoints use ``cell_interval``.
    """
    ident = _load_json(cell_dir / bp.CELL_IDENTITY_FILENAME)
    cg = _load_json(cell_dir / "a2.cg.ckpt.json")
    dictator = _load_json(cell_dir / "dictator.ckpt.json")
    cg_ident = cg.get("identity") or {}
    outcome = cg.get("outcome") or {}
    ub_hist = cg.get("ub_history") or []
    lb_hist = cg.get("lb_history") or []
    problems = []
    for label, hist in (("ub_history", ub_hist), ("lb_history", lb_hist)):
        if not hist:
            problems.append(f"{tag}: empty {label}")
        elif not all(is_finite_number(x) for x in hist):
            problems.append(f"{tag}: non-finite {label}")
    if problems:
        return {"tag": tag, "problems": problems, "fields": None}

    ub_ch = ub_hist[-1]
    lb_best = max(lb_hist)
    z_d_ub = dictator.get("z_d_ub")
    z_d_lb = dictator.get("z_d_lb")
    numeric = {
        "lb_best": lb_best,
        "ub_ch": ub_ch,
        "z_D_lb": z_d_lb,
        "z_D_ub": z_d_ub,
    }
    for name, value in numeric.items():
        if not is_finite_number(value):
            problems.append(f"{tag}: non-finite {name}={value!r}")
    if problems:
        return {"tag": tag, "problems": problems, "fields": None}

    n_trips = ident.get("n_trips")
    if not isinstance(n_trips, int) or isinstance(n_trips, bool) or n_trips <= 0:
        problems.append(f"{tag}: n_trips {n_trips!r} is not a positive int")
        return {"tag": tag, "problems": problems, "fields": None}

    interval = cell_interval(ub_ch, lb_best, z_d_ub, z_d_lb, n_trips)
    u_lo = interval["U_lo_raw"]
    u_hi = interval["U_hi"]
    if not is_finite_number(u_lo) or not is_finite_number(u_hi):
        problems.append(f"{tag}: non-finite uplift endpoints")
        return {"tag": tag, "problems": problems, "fields": None}
    if u_hi < u_lo - operand_scaled_allowance(u_lo, u_hi):
        problems.append(
            f"{tag}: reversed interval U_hi={u_hi} < U_lo_raw={u_lo}")

    certified = bool(outcome.get("certified")) and outcome.get("type") == "certified"
    method = ident.get("method", cg_ident.get("method"))
    fields = {
        "tag": tag,
        "lb_best": float(lb_best),
        "ub_ch": float(ub_ch),
        "U_lo_raw": float(u_lo),
        "U_hi": float(u_hi),
        "z_D_lb": float(z_d_lb),
        "z_D_ub": float(z_d_ub),
        "certified": certified,
        "setting": ident.get("setting"),
        "seed": ident.get("seed"),
        "n_trips": n_trips,
        "b": ident.get("b"),
        "method": method,
        "epsilon": ident.get("epsilon", cg_ident.get("epsilon")),
        "tol_d": ident.get("tol_d", cg_ident.get("tol_d")),
        "budget": ident.get("budget", cg_ident.get("budget")),
        "instance_hash": ident.get("instance_hash", cg_ident.get("instance_hash")),
        "market_hash": ident.get("market_hash", cg_ident.get("market_hash")),
    }
    return {"tag": tag, "problems": problems, "fields": fields}


def _population_inventory(root: Path) -> dict:
    expected = set(expected_cell_tags())
    present = _cell_dirs(root)
    present_tags = set(present)
    missing = sorted(expected - present_tags)
    extra = sorted(present_tags - expected)
    incomplete_files = []
    for tag in sorted(present_tags & expected):
        absent = _required_files_present(present[tag])
        if absent:
            incomplete_files.append({"tag": tag, "missing_files": absent})
    return {
        "root": str(root),
        "present_count": len(present_tags & expected),
        "missing": missing,
        "extra": extra,
        "incomplete_files": incomplete_files,
        "dirs": present,
        "complete": (
            not missing and not extra and not incomplete_files
            and len(present_tags & expected) == N_CELLS),
    }


def _base_verdict() -> dict:
    return {
        "schema": SCHEMA,
        "status": STATUS_INCIDENT,
        "original_is_canonical": ORIGINAL_IS_CANONICAL,
        "replica_may_substitute_original": REPLICA_MAY_SUBSTITUTE_ORIGINAL,
        "required_agreeing_cells": REQUIRED_AGREEING_CELLS,
        "n_cells_expected": N_CELLS,
        "agreeing_cells": 0,
        "incident": True,
        "incomplete_population": False,
        "disagreements": [],
        "missing_original": [],
        "missing_replica": [],
        "extra_original": [],
        "extra_replica": [],
        "incomplete_files_original": [],
        "incomplete_files_replica": [],
        "compared_numeric_fields": list(COMPARED_NUMERIC_FIELDS),
        "compared_boolean_fields": list(COMPARED_BOOLEAN_FIELDS),
        "solve_path_fields": list(SOLVE_PATH_FIELDS),
        "excluded_provenance_fields": list(EXCLUDED_PROVENANCE_FIELDS),
        "tolerances": {
            "numeric_fields": "operand-scaled SEK",
            "abs_tol_sek": ABS_TOL_SEK,
            "rel_scale": REL_SCALE,
            "formula": (
                "allowance = abs_tol_sek + rel_scale * max(1, |left|, |right|)"),
            "justification": (
                "CG epsilon and dictator tol_d are both 1e-2 SEK; this is "
                "the certificate machinery noise floor.  Physical replay "
                f"tolerance {PHYSICAL_REPLAY_TOL_KWH} kWh is an energy "
                "residual and is not a SEK threshold.  A comparator tighter "
                "than 1e-2 SEK is not meaningful."),
            "physical_replay_tol_kwh": PHYSICAL_REPLAY_TOL_KWH,
            "cg_epsilon": CG_EPSILON,
            "dictator_tol_d": DICTATOR_TOL_D,
            "certified": "exact boolean",
            "solve_path": "exact",
        },
        "single_disagreement_policy": (
            "A single disagreeing cell is an engineering incident to "
            "investigate.  It is never a choice of which run to score."),
        "canonical_policy": (
            "The original run remains canonical regardless of outcome and "
            "may never be substituted by the replica."),
        "provenance_policy": (
            "run_commit and run manifests are expected to differ between "
            "independent runs and are excluded from the comparison.  "
            "Solve-path equivalence is asserted separately."),
    }


def _reversed_pair(orig: dict, repl: dict) -> bool:
    """True when replica endpoints are the original pair swapped."""
    o_lo, o_hi = orig["U_lo_raw"], orig["U_hi"]
    r_lo, r_hi = repl["U_lo_raw"], repl["U_hi"]
    if numbers_agree(o_lo, o_hi):
        return False
    return numbers_agree(o_lo, r_hi) and numbers_agree(o_hi, r_lo)


def compare_replications(
    original_dir: str | os.PathLike,
    replica_dir: str | os.PathLike,
) -> dict:
    """Return a deterministic verdict dict.  Never writes."""
    original = _resolved(original_dir)
    replica = _resolved(replica_dir)
    verdict = _base_verdict()
    try:
        orig_inv = _population_inventory(original)
        repl_inv = _population_inventory(replica)
    except (ComparatorError, evidence.EvidenceError) as exc:
        verdict["status"] = STATUS_INCIDENT
        verdict["disagreements"] = [{
            "kind": "read_error",
            "detail": str(exc),
        }]
        return verdict

    verdict["missing_original"] = orig_inv["missing"]
    verdict["missing_replica"] = repl_inv["missing"]
    verdict["extra_original"] = orig_inv["extra"]
    verdict["extra_replica"] = repl_inv["extra"]
    verdict["incomplete_files_original"] = orig_inv["incomplete_files"]
    verdict["incomplete_files_replica"] = repl_inv["incomplete_files"]
    verdict["original_cell_count"] = orig_inv["present_count"]
    verdict["replica_cell_count"] = repl_inv["present_count"]

    if not orig_inv["complete"] or not repl_inv["complete"]:
        verdict["status"] = STATUS_INCOMPLETE
        verdict["incomplete_population"] = True
        verdict["incident"] = True
        verdict["agreeing_cells"] = 0
        verdict["disagreements"] = [{
            "kind": "incomplete_population",
            "detail": (
                "Refusing to compare an incomplete population.  Agreement "
                f"is {REQUIRED_AGREEING_CELLS}/{N_CELLS} cells matched by "
                "cell identity; a missing or extra cell is not a majority "
                "vote and is not scored."),
        }]
        return verdict

    disagreements = []
    agreeing = 0
    for tag in expected_cell_tags():
        try:
            orig_cell = extract_certificate(orig_inv["dirs"][tag], tag)
            repl_cell = extract_certificate(repl_inv["dirs"][tag], tag)
        except evidence.DuplicateJsonKeyError as exc:
            disagreements.append({
                "tag": tag,
                "kind": "duplicate_json_key",
                "detail": str(exc),
            })
            continue
        except evidence.EvidenceError as exc:
            disagreements.append({
                "tag": tag,
                "kind": "parse_error",
                "detail": str(exc),
            })
            continue

        cell_problems = list(orig_cell["problems"])
        for problem in repl_cell["problems"]:
            cell_problems.append(
                problem.replace(f"{tag}:", f"{tag} replica:", 1))

        if orig_cell["fields"] is None or repl_cell["fields"] is None:
            kind = "non_finite_field"
            joined = " ".join(cell_problems)
            if "reversed interval" in joined:
                kind = "reversed_interval"
            disagreements.append({
                "tag": tag,
                "kind": kind,
                "detail": cell_problems,
            })
            continue
        if cell_problems:
            disagreements.append({
                "tag": tag,
                "kind": "reversed_interval",
                "detail": cell_problems,
                "original": {k: orig_cell["fields"][k]
                             for k in ("U_lo_raw", "U_hi")},
                "replica": {k: repl_cell["fields"][k]
                            for k in ("U_lo_raw", "U_hi")},
            })
            continue

        orig_f = orig_cell["fields"]
        repl_f = repl_cell["fields"]
        field_hits = []
        for name in SOLVE_PATH_FIELDS:
            if orig_f.get(name) != repl_f.get(name):
                field_hits.append({
                    "field": name,
                    "kind": "solve_path",
                    "original": orig_f.get(name),
                    "replica": repl_f.get(name),
                })
        for name in COMPARED_NUMERIC_FIELDS:
            left, right = orig_f[name], repl_f[name]
            if not numbers_agree(left, right):
                field_hits.append({
                    "field": name,
                    "kind": "numeric",
                    "original": left,
                    "replica": right,
                    "allowance": operand_scaled_allowance(left, right),
                    "abs_delta": abs(left - right),
                })
        for name in COMPARED_BOOLEAN_FIELDS:
            if orig_f[name] != repl_f[name]:
                field_hits.append({
                    "field": name,
                    "kind": "boolean",
                    "original": orig_f[name],
                    "replica": repl_f[name],
                })
        if _reversed_pair(orig_f, repl_f):
            disagreements.append({
                "tag": tag,
                "kind": "reversed_interval",
                "detail": (
                    "replica uplift endpoints are the original pair swapped"),
                "original": {"U_lo_raw": orig_f["U_lo_raw"],
                             "U_hi": orig_f["U_hi"]},
                "replica": {"U_lo_raw": repl_f["U_lo_raw"],
                            "U_hi": repl_f["U_hi"]},
                "fields": field_hits,
            })
            continue
        if field_hits:
            disagreements.append({
                "tag": tag,
                "kind": "field_disagreement",
                "fields": field_hits,
            })
            continue
        agreeing += 1

    verdict["agreeing_cells"] = agreeing
    verdict["disagreements"] = disagreements
    if (agreeing == REQUIRED_AGREEING_CELLS and not disagreements):
        verdict["status"] = STATUS_AGREE
        verdict["incident"] = False
        verdict["incomplete_population"] = False
    else:
        verdict["status"] = STATUS_INCIDENT
        verdict["incident"] = True
        verdict["incomplete_population"] = False
    return verdict


def verdict_bytes(verdict: dict) -> bytes:
    """Canonical machine-readable encoding (byte-identical across reruns)."""
    return (json.dumps(verdict, indent=2, sort_keys=True, ensure_ascii=True)
            + "\n").encode("utf-8")


def write_verdict(verdict: dict, dest: str | os.PathLike,
                  original_dir: str | os.PathLike,
                  replica_dir: str | os.PathLike) -> Path:
    """Write the verdict next to the inputs, never into them."""
    path = Path(dest)
    orig = _resolved(original_dir)
    repl = _resolved(replica_dir)
    target = path.resolve() if path.exists() else path.parent.resolve() / path.name
    if _is_under(target, orig) or _is_under(target, repl):
        raise ComparatorError(
            f"refusing to write verdict into an input directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = verdict_bytes(verdict)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare a B3 factor-pilot original run to a replica.")
    parser.add_argument("--original", required=True,
                        help="Canonical original run directory (never replaced).")
    parser.add_argument("--replica", required=True,
                        help="Independent replication run directory.")
    parser.add_argument(
        "--verdict", required=True,
        help="Destination JSON path; must not lie inside either input tree.")
    args = parser.parse_args(argv)
    verdict = compare_replications(args.original, args.replica)
    write_verdict(verdict, args.verdict, args.original, args.replica)
    sys.stdout.write(verdict_bytes(verdict).decode("utf-8"))
    if verdict["status"] == STATUS_AGREE:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
