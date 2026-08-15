"""Aggregate JSONL run records into one flat CSV for analysis.

Usage: python -m egglab.collect RUNS_DIR -o out.csv
Selects the scalar fields useful for cross-run analysis; the full JSONL stays
the ground truth.
"""
from __future__ import annotations

import argparse
import csv
import glob
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


def flatten(rec: dict) -> dict:
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
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.runs_dir, "**", "*.jsonl"), recursive=True))
    rows = []
    for fp in files:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(flatten(json.loads(line)))
    if not rows:
        raise SystemExit(f"no records found under {args.runs_dir}")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.out}: {len(rows)} records from {len(files)} files")


if __name__ == "__main__":
    main()
