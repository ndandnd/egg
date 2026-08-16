"""Aggregate JSONL run records into one flat CSV for analysis.

Usage: python -m egglab.collect RUNS_DIR -o out.csv
Selects the scalar fields useful for cross-run analysis; the full JSONL stays
the ground truth.
"""
from __future__ import annotations

import argparse
import csv
import json
import os

SCALARS = [
    "experiment",
    "regime",
    "timestamp",
    "host",
    "git_commit",
    "slurm_job_id",
    "slurm_array_task_id",
    "instance_name",
    "instance_hash",
    "n_trips",
    "max_vehicles",
    "schedule_hash",
    "load_hash",
    "fleet",
    "dh_min_total",
    "energy_charged_kwh",
    "ops_cost",
    "obj_model",
    "obj_true",
    "energy_cost_model",
    "oracle_tier",
    "replay_ok",
]
SOLVER = ["backend", "status", "obj", "bound", "mip_gap", "lp_obj",
          "lp_mip_gap_abs", "wall_s", "lp_wall_s", "n_vars", "n_int", "n_constrs"]
ADAPTIVE = ["adaptive_rounds", "adaptive_lb", "adaptive_ub", "adaptive_gap_abs",
            "adaptive_converged"]
ECON = ["bill", "system_cost_delta", "total_private", "total_system", "energy_kwh"]
EXTRA = ["tag", "cell", "seed", "shape", "b_scale", "alpha", "tol_price",
         "iter", "price_residual", "load_residual", "schedule_recurred",
         "response_recurred", "sweep_slot", "delta", "idx"]


def flatten(rec: dict, sidecar: dict | None = None) -> dict:
    """Flatten one record. Replay semantics (measurement closeout):
    - replay_original_ok: the stored flag, never altered;
    - replay_revalidation_status: sidecar disposition (exact-hash match);
    - replay_effective_ok: original True, or original False covered by a
      successful revalidation. CANONICAL ANALYSIS USES THE EFFECTIVE FIELD;
      the original is always preserved alongside."""
    from .revalidate import ACCEPTED_DISPOSITIONS

    row = {k: rec.get(k) for k in SCALARS}
    for k in SOLVER:
        row[f"solver_{k}"] = (rec.get("solver") or {}).get(k)
    solver_extra = ((rec.get("solver") or {}).get("extra")) or {}
    for k in ADAPTIVE:
        row[k] = solver_extra.get(k)
    for k in ECON:
        row[f"econ_{k}"] = (rec.get("economics") or {}).get(k)
    ext = rec.get("extra") or {}
    for k in EXTRA:
        row[f"x_{k}"] = ext.get(k)
    oc = ext.get("outcome")
    row["x_outcome_type"] = oc.get("type") if isinstance(oc, dict) else None
    row["x_cycle_length"] = oc.get("length") if isinstance(oc, dict) else None
    row["n_replay_violations"] = len(rec.get("replay_violations") or [])

    original_ok = rec.get("replay_ok")
    status = sidecar.get("disposition") if sidecar else None
    if original_ok is False:
        effective = status in ACCEPTED_DISPOSITIONS
    else:
        effective = original_ok  # True, or None for pre-replay-era records
    row["replay_original_ok"] = original_ok
    row["replay_effective_ok"] = effective
    row["replay_revalidation_status"] = status
    row["replay_policy_version"] = rec.get("replay_policy_version")
    row["replay_tolerance_kwh"] = rec.get("replay_tol_kwh")
    return row


def collect(runs_dir: str, out: str) -> int:
    """Aggregate all records under runs_dir into one CSV. Sidecar files under
    revalidation/ directories are consulted for effective replay status but
    are never ingested as oracle records."""
    from .revalidate import iter_record_lines, load_sidecars, record_sha256

    sidecars = load_sidecars(runs_dir)
    rows = []
    files = set()
    for rel, _i, raw in iter_record_lines(runs_dir):
        files.add(rel)
        rec = json.loads(raw)
        sc = None
        if rec.get("replay_ok") is False:
            sc = sidecars.get(record_sha256(raw))
        rows.append(flatten(rec, sidecar=sc))
    if not rows:
        raise SystemExit(f"no records found under {runs_dir}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} records from {len(files)} files")
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    collect(args.runs_dir, args.out)


if __name__ == "__main__":
    main()
