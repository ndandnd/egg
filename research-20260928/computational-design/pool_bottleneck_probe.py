#!/usr/bin/env python3
"""Offline three-column convex-pool probe; never starts a native optimizer.

Reads only the frozen case and saved hull result.json. Complete fleet columns
are replayed through the existing exact-policy helper before the small
restricted quadratic is minimized with SciPy SLSQP. Raw event logs are not read.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import sys
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import scipy
from scipy.optimize import minimize

from egglab import native_hull as nh
from egglab import native_recharge as nr


DEFAULT_ATTEMPT = PROJECT_ROOT / "result/sistig_nonlinear/20260927-attempt2"
DEFAULT_OUTPUT = PROJECT_ROOT / "research-20260928/computational-design/pool_bottleneck_probe.json"
RATIONAL_DENOMINATOR = 1_000_000_000


def native_case(raw: dict) -> nr.NativeCase:
    trips = tuple(nr.Trip(**item) for item in raw["trips"])
    movements = tuple(
        nr.Movement(**{**item, "legs": tuple(nr.Leg(**leg) for leg in item["legs"])})
        for item in raw["movements"]
    )
    resources = tuple(nr.Resource(**item) for item in raw["resources"])
    fields = dict(raw)
    fields.update(
        trips=trips,
        movements=movements,
        resources=resources,
        market_edges_min=tuple(raw["market_edges_min"]),
    )
    return nr.NativeCase(**fields)


def first_order(weights, gradient):
    """Simplex KKT residual: mixture gradient minus the cheapest pool column."""
    w = np.asarray(weights, dtype=float)
    g = np.asarray(gradient, dtype=float)
    residual = float(np.dot(w, g) - np.min(g))
    active = [i for i, value in enumerate(w) if value > 1e-8]
    nu = float(np.dot(w, g))
    active_spread = max((abs(float(g[i]) - nu) for i in active), default=0.0)
    inactive_violation = max((max(0.0, nu - float(g[i]))
                              for i in range(len(w)) if i not in active), default=0.0)
    return {
        "simplex_directional_residual": max(0.0, residual),
        "active_gradient_spread": active_spread,
        "inactive_kkt_violation": inactive_violation,
        "column_gradients": [float(x) for x in g],
    }


def rationalize_simplex(weights):
    values = np.maximum(np.asarray(weights, dtype=float), 0.0)
    if values.sum() <= 0:
        raise ValueError("Cannot rationalize a zero simplex")
    values /= values.sum()
    units = [int(math.floor(float(x) * RATIONAL_DENOMINATOR + 0.5)) for x in values]
    correction_index = int(np.argmax(values))
    units[correction_index] += RATIONAL_DENOMINATOR - sum(units)
    if any(x < 0 for x in units) or sum(units) != RATIONAL_DENOMINATOR:
        raise ValueError("Fixed-denominator rounding did not preserve the simplex")
    return [Fraction(x, RATIONAL_DENOMINATOR) for x in units], units


def objective_gradient(weights, load_matrix, ops, a, b):
    loads = np.asarray(weights) @ load_matrix
    objective = float(np.dot(weights, ops) + np.dot(a, loads) + 0.5 * np.dot(b, loads * loads))
    price = a + b * loads
    gradient = ops + load_matrix @ price
    return objective, gradient, loads, price


def run(attempt: Path) -> dict:
    probe_start = perf_counter()
    frozen_path = attempt / "frozen.json"
    result_path = attempt / "hull/result.json"
    frozen = json.loads(frozen_path.read_text())
    saved = json.loads(result_path.read_text())
    result = saved["result"]
    case = native_case(frozen["case"])
    market_raw = frozen["market"]
    market = nh.Market(market_raw["name"], tuple(market_raw["a"]), tuple(market_raw["b"]))
    if case.identity() != frozen["case_identity"]:
        raise ValueError("Frozen case identity mismatch")
    if market.identity() != frozen["market_identity"]:
        raise ValueError("Frozen market identity mismatch")
    if result["physical_identity"] != case.identity() or result["market_identity"] != market.identity():
        raise ValueError("Saved hull result identity mismatch")

    policy = result["extraction_policy"]
    columns = result["columns"]
    if len(columns) != 3:
        raise ValueError(f"Expected three preserved complete-fleet columns, got {len(columns)}")
    replay_start = perf_counter()
    replayed = [nh.replay_column(case, column, extraction_policy=policy) for column in columns]
    replay_elapsed = perf_counter() - replay_start
    loads = np.asarray([x["load"] for x in replayed], dtype=float)
    ops = np.asarray([x["ops_cost"] for x in replayed], dtype=float)
    a, b = np.asarray(market.a, dtype=float), np.asarray(market.b, dtype=float)

    saved_weights = [Fraction(x) for x in result["mixture"]["simplex"]["weights_exact"]]
    exact_start = perf_counter()
    saved_mix = nh.replay_exact_mixture(case, market, columns, saved_weights,
                                        extraction_policy=policy)
    saved_price = nh.mixture_price(market, saved_mix)
    saved_pool = nh.pool_certificate(market, columns, saved_mix, saved_price)
    saved_exact_elapsed = perf_counter() - exact_start
    if saved_mix["objective_exact"] != result["mixture"]["objective_exact"]:
        raise ValueError("Saved mixture objective did not reproduce exactly")

    starts = [np.asarray([float(x) for x in saved_weights]),
              np.full(len(columns), 1.0 / len(columns))]
    starts.extend(np.eye(len(columns)))
    slsqp_start = perf_counter()
    candidates = []
    for x0 in starts:
        solved = minimize(
            lambda w: objective_gradient(w, loads, ops, a, b)[0],
            x0,
            jac=lambda w: objective_gradient(w, loads, ops, a, b)[1],
            method="SLSQP",
            bounds=[(0.0, 1.0)] * len(columns),
            constraints=[{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0),
                          "jac": lambda w: np.ones_like(w)}],
            options={"ftol": 1e-13, "maxiter": 1000, "disp": False},
        )
        if not solved.success and not np.isfinite(solved.fun):
            continue
        candidates.append(solved)
    slsqp_elapsed = perf_counter() - slsqp_start
    if not candidates:
        raise RuntimeError("No finite SLSQP proposal")
    proposal = min(candidates, key=lambda x: float(x.fun))
    numeric_objective, numeric_gradient, numeric_loads, _ = objective_gradient(
        proposal.x, loads, ops, a, b)
    saved_float = np.asarray([float(x) for x in saved_weights])
    saved_objective, saved_gradient, _, _ = objective_gradient(saved_float, loads, ops, a, b)

    proposed_weights, proposed_units = rationalize_simplex(proposal.x)
    verify_start = perf_counter()
    proposed_mix = nh.replay_exact_mixture(case, market, columns, proposed_weights,
                                           extraction_policy=policy)
    proposed_price = nh.mixture_price(market, proposed_mix)
    proposed_pool = nh.pool_certificate(market, columns, proposed_mix, proposed_price)
    exact_verify_elapsed = perf_counter() - verify_start
    total_probe_elapsed = perf_counter() - probe_start

    return {
        "scope": "offline exploratory restricted-pool diagnostic; not a global hull certificate",
        "attempt": str(attempt.relative_to(PROJECT_ROOT)),
        "source_commit": frozen["source_commit"],
        "frozen_sha256": saved["frozen_sha256"],
        "physical_identity": case.identity(),
        "market_identity": market.identity(),
        "extraction_policy": policy,
        "saved_result_status": result["status"],
        "column_count": len(columns),
        "replayed_complete_fleet_columns": len(replayed),
        "scipy_version": scipy.__version__,
        "total_probe_wall_seconds_excluding_import_and_output_write": total_probe_elapsed,
        "numeric_proposal": {
            "method": "SciPy SLSQP with analytic gradient; 5 deterministic starts",
            "starts": len(starts),
            "finite_runs": len(candidates),
            "successful_runs": sum(bool(x.success) for x in candidates),
            "success": bool(proposal.success),
            "message": str(proposal.message),
            "iterations": int(proposal.nit),
            "weights": [float(x) for x in proposal.x],
            "objective": numeric_objective,
            "saved_mixture_objective": saved_objective,
            "objective_delta_vs_saved": numeric_objective - saved_objective,
            "first_order_residual": first_order(proposal.x, numeric_gradient),
            "saved_mixture_first_order_residual": first_order(saved_float, saved_gradient),
            "slsqp_wall_seconds": slsqp_elapsed,
        },
        "fixed_denominator_replay": {
            "weight_source": "SLSQP proposal rounded to 1e-9 units; largest component absorbs integer-unit mass correction; no exact pairwise weight optimization",
            "denominator": RATIONAL_DENOMINATOR,
            "integer_units": proposed_units,
            "weights_exact": [str(x) for x in proposed_weights],
            "objective_exact": proposed_mix["objective_exact"],
            "objective": proposed_mix["upper"],
            "objective_delta_vs_saved": float(Fraction(proposed_mix["objective_exact"])
                                                - Fraction(saved_mix["objective_exact"])),
            "objective_delta_vs_saved_exact": str(Fraction(proposed_mix["objective_exact"])
                                                    - Fraction(saved_mix["objective_exact"])),
            "pool_certificate": proposed_pool,
            "saved_pool_certificate": saved_pool,
            "exact_replay_and_pool_certificate_wall_seconds": exact_verify_elapsed,
            "saved_exact_replay_and_pool_certificate_wall_seconds": saved_exact_elapsed,
            "column_replay_wall_seconds": replay_elapsed,
        },
        "interpretation_limits": [
            "This minimizes only over the three saved pool columns.",
            "The pool Fenchel lower is restricted to those columns and is not the fresh global-pricing lower.",
            "No MIP, native solver, new experiment, or raw event log was used.",
            "The saved public hull attempt has an independently recorded strict polishing-cap violation; this probe does not cure or reclassify it.",
            "The existing exact replay helper returns a fixed internal simplex-source label; this report identifies the actual SLSQP-plus-1e-9 proposal procedure and does not claim pairwise polishing.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = run(args.attempt.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(args.out.resolve()),
        "columns": output["column_count"],
        "objective": output["numeric_proposal"]["objective"],
        "saved_objective": output["numeric_proposal"]["saved_mixture_objective"],
        "slsqp_wall_seconds": output["numeric_proposal"]["slsqp_wall_seconds"],
        "exact_replay_wall_seconds": output["fixed_denominator_replay"]["exact_replay_and_pool_certificate_wall_seconds"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
