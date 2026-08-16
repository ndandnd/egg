"""The Phase-0 logging contract (handoff Section 8.1).

One normalized JSONL record per oracle solve / loop iteration / sweep point,
with full provenance: instance hash, price vector, solver statistics
(LP root, MIP bound, gap, sizes, wall time, backend), schedule and load
hashes, economic decomposition, oracle exactness tier, git commit, host and
Slurm identifiers, seeds, and timestamps.
"""
from __future__ import annotations

import datetime
import json
import os
import socket
import subprocess


def git_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


_GIT = None


def provenance() -> dict:
    global _GIT
    if _GIT is None:
        _GIT = git_commit()
    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "git_commit": _GIT,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID"),
        "slurm_restart_count": os.environ.get("SLURM_RESTART_COUNT"),
    }


def make_record(
    experiment: str,
    inst,
    sol,
    market=None,
    prices=None,
    regime: str = "",
    extra: dict | None = None,
    validate: bool = True,
) -> dict:
    from .evsp import REPLAY_POLICY_VERSION, REPLAY_TOL_KWH, validate_solution
    from .regimes import evaluate  # local import to avoid cycles

    replay_violations = validate_solution(inst, sol) if validate else None
    rec = {
        "experiment": experiment,
        "regime": regime,
        **provenance(),
        "instance_name": inst.name,
        "instance_hash": inst.hash(),
        "n_trips": len(inst.trips),
        "max_vehicles": inst.max_vehicles,
        "prices": None if prices is None else [round(float(p), 6) for p in prices],
        "schedule_hash": sol.schedule_hash(),
        "load_hash": sol.load_hash(),
        "load": sol.load,
        "fleet": sol.fleet,
        "dh_min_total": sol.dh_min_total,
        "energy_charged_kwh": sol.energy_charged_kwh,
        "ops_cost": sol.ops_cost,
        "obj_model": sol.obj_model,
        "obj_true": sol.obj_true,
        "energy_cost_model": sol.energy_cost_model,
        "oracle_tier": sol.oracle_tier,
        "replay_ok": None if replay_violations is None else not replay_violations,
        "replay_violations": replay_violations,
        # replay-audit provenance: with sequences+arc_kinds+charges+instance
        # metadata, the independent validator can be rerun later without
        # solving another MILP (measurement-closeout requirement)
        "replay_policy_version": REPLAY_POLICY_VERSION,
        "replay_tol_kwh": REPLAY_TOL_KWH,
        "instance_meta": dict(inst.meta),
        "solver": sol.stats.to_dict() if sol.stats else None,
        "sequences": sol.sequences,
        "arc_kinds": sol.arc_kinds,
        "charges": sol.charges,
    }
    if market is not None:
        rec["market"] = {
            "name": market.name,
            "a": [round(float(x), 6) for x in market.a],
            "b": [round(float(x), 6) for x in market.b],
            "base_load": [round(float(x), 6) for x in market.U],
        }
        rec["economics"] = {
            k: v
            for k, v in evaluate(inst, sol, market).items()
            if k != "clearing_prices"
        }
        rec["clearing_prices"] = evaluate(inst, sol, market)["clearing_prices"]
    if extra:
        rec["extra"] = extra
    return rec


def append_jsonl(path: str, rec: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
