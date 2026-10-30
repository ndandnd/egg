"""Legacy replay revalidation (measurement closeout, 2026-08-16).

Background: before PR #11, the extractor rounded energy values and replay
used a 1e-6 kWh tolerance, so some loop records were stored with
replay_ok=false. egglab/loops.py at that time appended records and advanced
checkpoints WITHOUT checking replay_ok, so those records were never failed
work units and were never replaced by reruns. Raw JSONL is append-only
evidence and is never edited; instead, each failing record is revalidated
individually and the verdict is stored in an atomic SIDECAR file keyed by
the SHA-256 of the complete original record line. Audits then report both
the raw stored failures (never hidden) and the effectively unresolved
failures after exact-hash sidecar matching.

Revalidation of one record:
1. hash the original JSON line (stable identity);
2. reconstruct the synthetic instance from record metadata and verify the
   instance hash matches the stored one;
3. re-realize the record's exact trip partition at its recorded prices with
   the current full-precision fixed-sequence oracle;
4. replay-validate the re-realization with the current validator;
5. compare objective / load / energy / schedule identity against the legacy
   record under the documented tolerances below;
6. write one sidecar JSON with the full evidence chain and a disposition.

Dispositions:
- certified_equivalent: replay-valid; objective, energy, schedule AND
  per-slot loads all match the legacy record within tolerance. The ONLY
  acceptable disposition.
- certified_alternative_realization: replay-valid; objective/energy/schedule
  match, but the charging allocation differs beyond the load tolerance.
  DIAGNOSTIC ONLY — NOT acceptable: these are loop records, and the per-slot
  load vector determines the next endogenous price state, so economic
  equivalence does not certify trajectory equivalence. Such records remain
  unresolved and fail the audit.
- materially_different: replay-valid but economics do not match the legacy
  record. NOT acceptable; escalate.
- reconstruction_failed: metadata incomplete, instance hash mismatch,
  re-realization infeasible, or current replay failed. NOT acceptable.

Acceptance = {certified_equivalent} only.
A record is never accepted merely because its commit predates PR #11.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

import numpy as np

from . import checkpoint
from .evsp import REPLAY_TOL_KWH, solve_fixed_sequences, validate_solution
from .instance import synthetic_instance
from .records import git_commit, provenance

REVAL_DIR = "revalidation"

# Documented comparison tolerances (see doc/MEASUREMENT_CLOSEOUT.md):
TOL_OBJ = 1e-2        # matches the adaptive-certification scale; absorbs the
                      # 6-decimal price rounding stored in legacy records
TOL_ENERGY_KWH = 1e-3  # total charged energy must match to 1 Wh
TOL_LOAD_KWH = 1e-3    # per-slot load agreement threshold for "equivalent"

DISP_EQUIVALENT = "certified_equivalent"
DISP_ALTERNATIVE = "certified_alternative_realization"  # diagnostic, NOT accepted
DISP_DIFFERENT = "materially_different"
DISP_FAILED = "reconstruction_failed"
# Only exact per-slot load equivalence resolves a legacy loop failure: the
# load vector feeds the next endogenous price state (Codex review, PR #12).
ACCEPTED_DISPOSITIONS = {DISP_EQUIVALENT}


def record_sha256(raw_line: str) -> str:
    """Stable identity of one complete original JSONL record line."""
    return hashlib.sha256(raw_line.strip().encode("utf-8")).hexdigest()


def iter_record_lines(runs_dir: str):
    """Yield (relpath, line_idx, raw_line) over all record files, in a
    deterministic order, skipping revalidation sidecar directories."""
    files = sorted(
        glob.glob(os.path.join(runs_dir, "**", "*.jsonl"), recursive=True)
    )
    for fp in files:
        if f"{os.sep}{REVAL_DIR}{os.sep}" in fp:
            continue
        rel = os.path.relpath(fp, runs_dir)
        with open(fp) as f:
            for i, line in enumerate(f):
                if line.strip():
                    yield rel, i, line

def scan_failures(runs_dir: str) -> list:
    """Deterministic list of records with stored replay_ok == false."""
    out = []
    for rel, i, line in iter_record_lines(runs_dir):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            out.append({"file": rel, "line_idx": i,
                        "sha256": record_sha256(line), "parse_error": True})
            continue
        if rec.get("replay_ok") is False:
            out.append({"file": rel, "line_idx": i, "sha256": record_sha256(line)})
    return out


def sidecar_path(runs_dir: str, sha256: str) -> str:
    return os.path.join(runs_dir, REVAL_DIR, f"{sha256}.json")


def load_sidecars(root: str) -> dict:
    """sha256 -> sidecar dict, for every sidecar under root (recursive)."""
    out = {}
    for fp in sorted(
        glob.glob(os.path.join(root, "**", REVAL_DIR, "*.json"), recursive=True)
    ):
        try:
            with open(fp) as f:
                sc = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        sha = sc.get("original_sha256")
        if sha:
            out[sha] = sc
    return out


_NAME_RE = re.compile(r"syn-s(\d+)-n(\d+)")


def reconstruct_instance(rec: dict):
    """Rebuild the synthetic instance from record metadata; verify hash."""
    extra = rec.get("extra") or {}
    seed = extra.get("seed")
    n_trips = rec.get("n_trips")
    if seed is None:
        m = _NAME_RE.search(rec.get("instance_name") or "")
        if m:
            seed, n_trips = int(m.group(1)), int(m.group(2))
    if seed is None or n_trips is None:
        return None, "missing seed/n_trips metadata"
    kw = {}
    if rec.get("max_vehicles") is not None:
        kw["max_vehicles"] = rec["max_vehicles"]
    inst = synthetic_instance(seed=int(seed), n_trips=int(n_trips), **kw)
    if rec.get("instance_hash") and inst.hash() != rec["instance_hash"]:
        return None, (
            f"instance hash mismatch: reconstructed {inst.hash()} != "
            f"stored {rec['instance_hash']}"
        )
    return inst, None


def revalidate_record(runs_dir: str, entry: dict, solver_kw: dict | None = None) -> dict:
    """Revalidate one failing record; write (atomically) and return its
    sidecar. Idempotent: an existing sidecar for the same hash is returned
    unchanged, so parallel/rerun invocations are safe."""
    solver_kw = solver_kw or {}
    sha = entry["sha256"]
    sc_path = sidecar_path(runs_dir, sha)
    existing = checkpoint.load(sc_path)
    if existing and existing.get("original_sha256") == sha:
        return existing

    raw = None
    with open(os.path.join(runs_dir, entry["file"])) as f:
        for i, line in enumerate(f):
            if i == entry["line_idx"]:
                raw = line
                break
    sidecar = {
        "original_sha256": sha,
        "original_file": entry["file"],
        "original_line_idx": entry["line_idx"],
        "tolerances": {
            "obj_abs": TOL_OBJ,
            "energy_kwh": TOL_ENERGY_KWH,
            "load_kwh": TOL_LOAD_KWH,
            "replay_tol_kwh": REPLAY_TOL_KWH,
        },
        "revalidation_commit": git_commit(),
        "provenance": provenance(),
    }

    def finish(disposition: str, detail: str = "", **fields):
        sidecar["disposition"] = disposition
        sidecar["detail"] = detail
        sidecar.update(fields)
        checkpoint.save(sc_path, sidecar)
        return sidecar

    if raw is None or record_sha256(raw) != sha:
        return finish(DISP_FAILED, "original record line not found or changed")
    try:
        rec = json.loads(raw)
    except json.JSONDecodeError as e:
        return finish(DISP_FAILED, f"original record unparsable: {e}")

    sidecar["source_commit"] = rec.get("git_commit")
    sidecar["original_violations"] = rec.get("replay_violations")
    sidecar["original_regime"] = rec.get("regime")

    if not rec.get("sequences") or rec.get("prices") is None:
        return finish(DISP_FAILED, "record lacks sequences or prices")

    inst, err = reconstruct_instance(rec)
    if inst is None:
        return finish(DISP_FAILED, err)

    prices = np.asarray(rec["prices"], dtype=float)
    re_sol = solve_fixed_sequences(inst, rec["sequences"], ("linear", prices), **solver_kw)
    if re_sol is None:
        return finish(DISP_FAILED, "fixed-sequence re-realization infeasible")
    violations = validate_solution(inst, re_sol)
    sidecar["solver_stats"] = re_sol.stats.to_dict() if re_sol.stats else None
    sidecar["current_replay_violations"] = violations
    if violations:
        return finish(DISP_FAILED, "re-realization failed current replay", )

    legacy_load = np.asarray(rec.get("load") or [], dtype=float)
    re_load = np.asarray(re_sol.load, dtype=float)
    if legacy_load.shape != re_load.shape:
        return finish(DISP_FAILED, "load vector shape mismatch")
    obj_diff = float(re_sol.obj_model - (rec.get("obj_model") or 0.0))
    energy_diff = float(re_load.sum() - (rec.get("energy_charged_kwh") or 0.0))
    load_max_diff = float(np.max(np.abs(re_load - legacy_load))) if len(re_load) else 0.0
    schedule_same = re_sol.schedule_hash() == rec.get("schedule_hash")
    residuals = {
        "obj_diff": obj_diff,
        "energy_diff_kwh": energy_diff,
        "load_max_diff_kwh": load_max_diff,
        "schedule_hash_match": schedule_same,
    }
    if abs(obj_diff) <= TOL_OBJ and abs(energy_diff) <= TOL_ENERGY_KWH and schedule_same:
        disp = DISP_EQUIVALENT if load_max_diff <= TOL_LOAD_KWH else DISP_ALTERNATIVE
        return finish(disp, residuals=residuals)
    return finish(
        DISP_DIFFERENT,
        "economics/schedule do not match the legacy record",
        residuals=residuals,
    )
