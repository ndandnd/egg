#!/usr/bin/env python3
"""Emit ML warm-start training data from the certified CG pipeline.

ENGINEERING-TIER DATA — NEVER SCIENTIFIC EVIDENCE. This driver logs the
internals of the certified column-generation negotiation
(``egglab.b2a2.certified_cg`` plus ``regimes.solve_dictator`` where cheap)
into a per-solve JSONL schema for a future machine-learning experiment
(warm-starting the price-feedback reoptimization with predicted duals).
The ML model's outputs are NEVER a certificate: the exact certified oracle
remains the sole certifier. See ``doc/ML_WARMSTART_DATA_SPEC.md``.

Hard constraints:
- generates EXCLUSIVELY from seeds >= 10000 (every committed range 0-47 is
  reserved for a scientific population); a seed below 10000 is refused by
  name;
- reads no ``runs/b3_factor_pilot`` outcome and no A6 path; writes only
  under the supplied ``--out`` (never a default under ``result/``);
- tests run on CBC (do not set ``EGGLAB_REQUIRE_GRB``); nothing is launched.

Two label-quality rules (both drawn from the published methods):
1. duals are CANONICALIZED (an optimal-face representative), never the raw
   last simplex iterate, and the method is recorded per record;
2. per accepted column the separation to the next-best pool alternative
   (a margin) is recorded, so downstream training can filter degeneracy.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess

import numpy as np

import experiments.b3_factor_pilot as bp
from egglab import checkpoint
from egglab.b2a2 import certified_cg, market_hash, solve_rmp
from egglab.evsp import canonicalize_solution_load
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market
from egglab.regimes import solve_dictator
from egglab.solver import backend

SCHEMA = "cg-warmstart-training-v1"
EXPERIMENT = "cg-warmstart-training"
REPO_ROOT = bp.REPO_ROOT
RECORD_FILENAME = "record.jsonl"

SEED_FLOOR = 10000                     # hard seed-namespace floor
EPSILON = 1e-2
TOL_D = 1e-2
BUDGET = 240
MIP_GAP_DEFAULT = 1e-6
DUAL_CANON_SAMPLES = 4                 # optimal-face averaging samples
DUAL_CANON_METHOD = "optimal_face_average_over_column_rotations"

# stratified grid; battery/charge reuse the frozen B3 screen levels
N_TRIPS = (8, 10, 12, 16)
B_SCALES = (0.0, 0.01, 0.05)
BATTERY_LEVELS = (
    bp.FROZEN_SELECTED_LEVELS["S1_batt_low"],      # 45.0
    bp.BASELINE_BATTERY_KWH,                        # 60.0
    bp.FROZEN_SELECTED_LEVELS["S2_batt_high"],     # 90.0
)
CHARGE_LEVELS = (
    bp.FROZEN_SELECTED_LEVELS["S3_pow_low"],       # 75.0
    bp.BASELINE_POWER_KW,                           # 150.0
    bp.FROZEN_SELECTED_LEVELS["S4_pow_high"],      # 300.0
)
PER_CELL_CPU_H_ESTIMATE = 0.09         # advisory (pilot: 5.1 CPU-h / 60 cells)

# held-fixed generator arguments (same family as the B3 screen/pilot)
from experiments.b3_factor_screen import GENERATOR_HELD_FIXED_ARGUMENTS


class CGTrainingError(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finite(x) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).decode().strip()
    except subprocess.CalledProcessError:
        return None


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def assert_ml_seed(seed: int) -> None:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise CGTrainingError(f"seed {seed!r} is not an integer")
    if seed < SEED_FLOOR:
        raise CGTrainingError(
            f"seed {seed} is below the ML seed floor {SEED_FLOOR}; seeds "
            "0-47 are reserved for scientific populations and must never be "
            "used for engineering-tier training data")


def refuse_a6_paths(*paths) -> None:
    for path in paths:
        if path is None:
            continue
        resolved = Path(path).resolve()
        for part in resolved.parts:
            low = part.lower()
            if low.startswith("a6") or "a6_" in low:
                raise CGTrainingError(
                    f"refusing A6 path (scientific boundary): {resolved}")


def refuse_protected_output(out_dir) -> None:
    """The output root must not be under result/ or the pilot outcome tree."""
    out = Path(out_dir).resolve()
    for rel in ("result", "runs/b3_factor_pilot"):
        protected = (REPO_ROOT / rel).resolve()
        if out == protected or protected in out.parents \
                or out in protected.parents:
            raise CGTrainingError(
                f"refusing output under protected tree {rel}: {out}")


def assert_within_output(out_dir, path) -> None:
    out = Path(out_dir).resolve()
    target = Path(path).resolve()
    if out != target and out not in target.parents:
        raise CGTrainingError(
            f"refusing to write outside the supplied output directory: "
            f"{target} not under {out}")


# --------------------------------------------------------------------------
# grid
# --------------------------------------------------------------------------
def build_cells(seed_base: int, count: int) -> list[dict]:
    if count < 1:
        raise CGTrainingError("count must be >= 1")
    seeds = [seed_base + i for i in range(count)]
    for s in seeds:
        assert_ml_seed(s)
    cells = []
    for seed, n, b, batt, chg in itertools.product(
            seeds, N_TRIPS, B_SCALES, BATTERY_LEVELS, CHARGE_LEVELS):
        cells.append({
            "seed": seed, "n_trips": n, "b": b,
            "battery_kwh": batt, "charge_power_kw": chg,
            "tag": f"s{seed}_n{n}_b{b:g}_bat{batt:g}_chg{chg:g}",
        })
    return cells


def cells_per_seed() -> int:
    return len(N_TRIPS) * len(B_SCALES) * len(BATTERY_LEVELS) * len(CHARGE_LEVELS)


def build_instance(cell: dict):
    assert_ml_seed(cell["seed"])
    g = GENERATOR_HELD_FIXED_ARGUMENTS
    return synthetic_instance(
        seed=cell["seed"], n_trips=cell["n_trips"],
        battery_kwh=cell["battery_kwh"],
        charge_power_kw=cell["charge_power_kw"],
        soc_min_frac=g["soc_min_frac"], soc_end_frac=g["soc_end_frac"],
        trip_energy_range=tuple(g["trip_energy_range"]),
        day_start_min=g["day_start_min"], day_end_min=g["day_end_min"],
        max_vehicles=g["max_vehicles"], name=g["name"])


# --------------------------------------------------------------------------
# dual canonicalization (optimal-face representative, not the last iterate)
# --------------------------------------------------------------------------
def canonical_rmp_duals(inst, market, columns: list) -> dict:
    """Average the RMP duals over several optimal-face samples (deterministic
    column rotations), so the emitted label is a stable representative rather
    than an arbitrary simplex vertex.  Records the method and sample count."""
    n = len(columns)
    pis = []
    sigmas = []
    z_models = []
    ubs = []
    for k in range(DUAL_CANON_SAMPLES):
        rot = columns[k % n:] + columns[:k % n] if n else columns
        rmp = solve_rmp(inst, market, rot, tangent_points=[],
                        solve_id_prefix=f"canon-{k}")
        pis.append(np.asarray(rmp["pi"], dtype=float))
        sigmas.append(float(rmp["sigma"]))
        z_models.append(float(rmp["z_model"]))
        ubs.append(float(rmp["ub"]))
    pi_mean = np.mean(np.stack(pis, axis=0), axis=0)
    return {
        "method": DUAL_CANON_METHOD,
        "n_samples": DUAL_CANON_SAMPLES,
        "pi": [float(x) for x in pi_mean],
        "sigma": float(np.mean(sigmas)),
        "z_model": float(np.mean(z_models)),
        "ub": float(np.mean(ubs)),
        "pi_sample_spread": float(
            np.max(np.stack(pis, axis=0), axis=0).max()
            - np.min(np.stack(pis, axis=0), axis=0).min()) if n else 0.0,
    }


def _reduced_cost(col: dict, pi, sigma: float) -> float:
    """Reduced cost under price p = -pi: ops_cost + p.load - sigma."""
    load = np.asarray(col["load"], dtype=float)
    return float(col["ops_cost"]) - float(np.dot(np.asarray(pi), load)) - sigma


# --------------------------------------------------------------------------
# record construction (deterministic function of the committed checkpoint)
# --------------------------------------------------------------------------
def _iteration_rows(state: dict) -> list[dict]:
    rows = []
    events = state.get("oracle_events") or []
    for idx, it in enumerate(state.get("iteration_events") or []):
        it = it or {}
        pricing_dual_bound = None
        pricing_incumbent = None
        psid = it.get("pricing_solve_id")
        if psid is not None:
            match = next((e for e in events
                          if ((e.get("extra") or {}).get("call_id")) == psid),
                         None)
            if match is not None:
                solver = match.get("solver") or {}
                pricing_dual_bound = solver.get("bound")
                pricing_incumbent = solver.get("obj")
        rows.append({
            "index": idx,
            "terminal": bool(it.get("terminal")),
            "master_objective": it.get("z_rmp_model"),
            "convexity_dual": it.get("duals_sigma"),
            "incumbent_ub": it.get("ub_ch"),
            "certified_lb": it.get("lb_best"),
            "iteration_lb_ch": it.get("lb_ch"),
            "min_reduced_cost_lb": it.get("min_reduced_cost_lb"),
            "min_reduced_cost_ub": it.get("min_reduced_cost_ub"),
            "pricing_solve_id": psid,
            "pricing_dual_bound": pricing_dual_bound,
            "pricing_incumbent": pricing_incumbent,
        })
    return rows


def _column_rows(state: dict, duals: dict) -> tuple[list[dict], float | None]:
    columns = state.get("columns") or []
    pi = duals["pi"]
    sigma = duals["sigma"]
    reduced = [_reduced_cost(c, pi, sigma) for c in columns]
    order = sorted(reduced)
    pool_margin = (order[1] - order[0]) if len(order) >= 2 else None
    events = state.get("oracle_events") or []
    rows = []
    for j, col in enumerate(columns):
        replay_ok = None
        if j < len(events):
            replay_ok = events[j].get("replay_ok")
        # margin: how far THIS column's reduced cost sits above the pool min
        margin_to_min = reduced[j] - order[0] if reduced else None
        rows.append({
            "column_key": col.get("column_key"),
            "load": [float(x) for x in col.get("load", [])],
            "ops_cost": float(col.get("ops_cost")) if _finite(
                col.get("ops_cost")) else None,
            "reduced_cost_final": reduced[j],
            "margin_to_pool_min": margin_to_min,
            "replay_ok": replay_ok,
        })
    return rows, pool_margin


def build_record(cell: dict, inst, market, state: dict, dictator: dict | None,
                 mip_gap: float, time_limit_s, incomplete: bool,
                 reason: str | None) -> dict:
    state = state or {}
    posted = market.price(np.zeros(market.n_slots))
    posted_list = [float(x) for x in np.asarray(posted)]
    prices_bytes = json.dumps(posted_list).encode()
    # duals + per-column margins require at least one committed column; a
    # time-limited/incomplete cell may have none, in which case they are null
    if state.get("columns"):
        duals = canonical_rmp_duals(inst, market, state["columns"])
        columns, pool_margin = _column_rows(state, duals)
    else:
        duals = None
        columns, pool_margin = [], None
    oc = state.get("outcome") or {}
    return {
        "schema": SCHEMA,
        "evidence_tier": "engineering-only (never a certificate)",
        "code_commit": _git_commit(),
        "identity": {
            "instance_hash": inst.hash(),
            "market_hash": market_hash(market),
            "seed": cell["seed"], "n_trips": cell["n_trips"], "b": cell["b"],
            "battery_kwh": cell["battery_kwh"],
            "charge_power_kw": cell["charge_power_kw"],
            "epsilon": EPSILON, "tol_d": TOL_D, "budget": BUDGET,
            "solver": {"backend": backend(), "mip_gap": mip_gap},
        },
        "posted_prices": posted_list,
        "posted_prices_sha256": _sha256_bytes(prices_bytes),
        "iterations": _iteration_rows(state),
        "rmp_duals_canonical": duals,
        "dual_canonicalization": ({"method": duals["method"],
                                   "n_samples": duals["n_samples"]}
                                  if duals else
                                  {"method": DUAL_CANON_METHOD,
                                   "n_samples": 0}),
        "columns": columns,
        "column_pool_min_margin": pool_margin,
        "certificate": {
            "ub_ch": oc.get("ub_ch"), "lb_best": oc.get("lb_best"),
            "gap": oc.get("gap"), "certified": oc.get("certified"),
            "outcome_type": oc.get("type"),
            "oracle_calls_total": state.get("oracle_calls"),
            "oracle_calls_clean": state.get("calls_clean"),
        },
        "dictator": dictator,
        "time_limit_s": time_limit_s,
        "incomplete": incomplete,
        "incomplete_reason": reason,
    }


def canonical_record_bytes(record: dict) -> bytes:
    return (json.dumps(record, sort_keys=True) + "\n").encode()


# --------------------------------------------------------------------------
# per-cell emission (resumable)
# --------------------------------------------------------------------------
def _dictator_certificate(inst, market, kw) -> dict | None:
    try:
        sol = solve_dictator(inst, market, tol_abs=TOL_D, **kw)
    except Exception:
        return None
    canonicalize_solution_load(inst, sol)
    physical = float(sol.ops_cost + market.system_cost_delta(
        np.asarray(sol.load)))
    lb = float(sol.stats.extra.get("adaptive_lb")) if sol.stats.extra.get(
        "adaptive_lb") is not None else None
    gap = (physical - lb) if lb is not None else None
    return {
        "z_d_ub": physical, "z_d_lb": lb, "gap": gap,
        "converged": bool(gap is not None and gap <= TOL_D),
        "status": sol.stats.status,
    }


def emit_cell(cell: dict, args) -> str:
    out = Path(args.out)
    refuse_a6_paths(out, cell["tag"])
    cdir = out / cell["tag"]
    cdir.mkdir(parents=True, exist_ok=True)
    assert_within_output(out, cdir)
    record_path = cdir / RECORD_FILENAME

    inst = build_instance(cell)
    market = make_affine_market(inst, shape="duck", b_scale=cell["b"])
    kw = dict(max_mip_gap=args.mip_gap, time_limit_s=args.time_limit_s)

    # a per-cell wall/time cap must MARK the cell incomplete, never silently
    # truncate: if the solve completes non-certified OR raises (e.g. a pricing
    # MIP cannot reach OPTIMAL inside the time limit), we still emit a record
    # from whatever was atomically committed, flagged incomplete.
    state = None
    incomplete = False
    reason = None
    try:
        state = certified_cg(
            inst, market, epsilon=EPSILON, budget=BUDGET, out_dir=str(cdir),
            tag="a2", experiment=EXPERIMENT, solver_kw=dict(kw), method="a2")
        oc = state.get("outcome") or {}
        incomplete = not (oc.get("type") == "certified" and oc.get("certified"))
        if incomplete:
            reason = f"not certified within budget/time (type={oc.get('type')})"
    except Exception as exc:  # noqa: BLE001 — cap/solver failure is data, not a crash
        state = checkpoint.load(str(cdir / "a2.cg.ckpt.json"))
        incomplete = True
        reason = f"solve did not complete within the time/wall cap: {exc}"

    dictator = None
    if args.with_dictator and not incomplete:
        dictator = _dictator_certificate(inst, market, dict(kw))

    record = build_record(cell, inst, market, state, dictator, args.mip_gap,
                          args.time_limit_s, incomplete, reason)
    payload = canonical_record_bytes(record)
    # atomic write; on resume the record is a deterministic function of the
    # committed checkpoint, so it re-materializes byte-identically
    assert_within_output(out, record_path)
    fd, tmp = tempfile.mkstemp(prefix=f".{RECORD_FILENAME}.", dir=str(cdir))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, record_path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    final_oc = (state or {}).get("outcome") or {}
    print(f"[emit] {cell['tag']}: {final_oc.get('type')} "
          f"certified={final_oc.get('certified')} "
          f"columns={len((state or {}).get('columns') or [])} "
          f"incomplete={incomplete}")
    return str(record_path)


def _dry_run(cells: list[dict], args) -> None:
    per_seed = cells_per_seed()
    total = len(cells)
    est_cpu_h = total * args.per_cell_cpu_h_estimate
    print(f"[dry-run] output: {Path(args.out).resolve()}")
    print(f"[dry-run] grid: n_trips={list(N_TRIPS)} b={list(B_SCALES)} "
          f"battery={list(BATTERY_LEVELS)} charge={list(CHARGE_LEVELS)}")
    print(f"[dry-run] seeds: {args.seed_base}..{args.seed_base + args.count - 1} "
          f"(count {args.count}); {per_seed} cells/seed")
    print(f"[dry-run] total instances: {total}")
    print(f"[dry-run] estimated CPU-hours: ~{est_cpu_h:.1f} "
          f"(at {args.per_cell_cpu_h_estimate} CPU-h/cell; "
          f"per-cell wall cap {args.time_limit_s}s)")
    for k, c in enumerate(cells):
        print(k, {kk: c[kk] for kk in ("seed", "n_trips", "b",
                                       "battery_kwh", "charge_power_kw")})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/cg_training_data")
    ap.add_argument("--seed-base", dest="seed_base", type=int, default=10000)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--mip-gap", dest="mip_gap", type=float,
                    default=MIP_GAP_DEFAULT)
    ap.add_argument("--time-limit-s", dest="time_limit_s", type=float,
                    default=600.0)
    ap.add_argument("--with-dictator", dest="with_dictator",
                    action="store_true",
                    help="also emit the dictator certificate per cell")
    ap.add_argument("--per-cell-cpu-h-estimate", dest="per_cell_cpu_h_estimate",
                    type=float, default=PER_CELL_CPU_H_ESTIMATE)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    refuse_a6_paths(args.out)
    refuse_protected_output(args.out)
    assert_ml_seed(args.seed_base)
    cells = build_cells(args.seed_base, args.count)

    if args.list:
        for k, c in enumerate(cells):
            print(k, c)
        print(f"total: {len(cells)} cells")
        return
    if args.dry_run:
        _dry_run(cells, args)
        return
    if args.cell is not None:
        if not (0 <= args.cell < len(cells)):
            ap.error(f"--cell must be in [0, {len(cells)})")
        emit_cell(cells[args.cell], args)
    elif args.all:
        for c in cells:
            emit_cell(c, args)
    else:
        ap.error("choose --list, --dry-run, --cell K, or --all")


if __name__ == "__main__":
    main()
