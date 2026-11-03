"""Replay the historical price map conditional on all recorded T1 fleet loads.

The T1 CSV fixes the assignments, analyzed outcomes, cycle metadata and final
residual. The campaign checkpoints supply complete ordered loads, price states,
final price, responses and detector tolerance. Only the synthetic Phase 1 and
damping-frontier roots of the August 16 closeout are consumed. These are
price-taking trajectories, not the separate convex-hull or V2G studies. No
fleet optimization, independent verification of schedule feasibility, or
test of oracle tie choices at perturbed numerical duals occurs here.
"""
import csv
import json
import sys
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
from egglab.ideal_feeder import solve_ideal_feeder
from egglab.instance import synthetic_instance
from egglab.market import make_affine_market

RESULT = SRC.parent / "result"
T1 = RESULT / "analysis/20260816T190835Z/T1_loop_cells.csv"
STAMP = "20260816T180507Z"
# These grids and limits come from run_phase1.py / submit_overnight_damping.sub.
CAMPAIGNS = {
    "phase1": ("phase1", 120, range(4), [8, 12], [0, .002, .01, .05],
               [1, .5, .25, .1]),
    "damping": ("damping_frontier", 240, range(16), [12], [.01, .05],
                [1, .75, .5, .35, .25, .2, .15, .1, .05]),
}
STATE_TOL = 1e-4  # original detector tolerance in archive currency/kWh
PRICE_ATOL = 1e-12  # separate numerical equality criterion for the replay


def cell_name(seed, n, b, alpha):
    return f"s{seed}_n{n}_duck_b{b:g}_a{alpha:g}"


def first_outcome(states, limit):
    """Historical loops.detect_outcome rule, vectorized over eligible predecessors.

    Importing that module would import the MILP backend. Preserve its priority
    (fixed before recurrent), exclusion of the immediate predecessor and first
    matching prior index, using the historical infinity norm on prices.
    """
    n = len(states) - 1
    for k in range(n):
        if np.max(np.abs(states[k+1] - states[k])) <= STATE_TOL:
            return {"type": "fixed_point", "iter": k}
        if k >= 2:
            prior_distances = np.max(np.abs(states[:k-1] - states[k]), axis=1)
            hits = np.flatnonzero(prior_distances <= STATE_TOL)
            if len(hits):
                first = int(hits[0])
                return {"type": "cycle", "iter": k, "first_seen": first, "length": k-first}
    if n == limit:
        return {"type": "max_iters", "iter": n}
    return None


def replay(row, ck, cfg, limit):
    seed, n_trips, b, alpha = cfg
    if (int(row["seed"]), int(row["n_trips"]), float(row["b"]), float(row["alpha"])) != cfg:
        raise ValueError("T1 parameters disagree with assignment")
    if row["shape"] != "duck" or ck["done"] is not True:
        raise ValueError("invalid shape or unfinished checkpoint")
    if ck["alpha"] != alpha or ck["tol_price"] != STATE_TOL:
        raise ValueError("checkpoint update parameters disagree")
    inst = synthetic_instance(seed=seed, n_trips=n_trips)
    # Reuse the archive's coefficient generator only. The two-bus model
    # independently computes supply cost, transport, and depot DLMP.
    market = make_affine_market(inst, shape=row["shape"], b_scale=b)
    n = ck["iter"]
    if type(n) is not int or not 1 <= n <= limit or n != int(row["iters_run"]):
        raise ValueError("checkpoint/archive iteration count disagrees")
    loads = np.asarray(ck["loads"], dtype=float)
    posted = np.asarray(ck["price_history"], dtype=float)
    final = np.asarray(ck["prices"], dtype=float)
    if (loads.shape != (n, inst.n_slots) or posted.shape != loads.shape
            or final.shape != (inst.n_slots,) or len(ck["responses"]) != n):
        raise ValueError("incomplete load, response or price trajectory")
    if not (np.isfinite(posted).all() and np.isfinite(final).all()):
        raise ValueError("nonfinite posted price or final price")
    # Reconstruct initial price from zero fleet load, then advance only from
    # the reconstructed state. No archived intermediate price seeds the loop.
    def depot_price(energy):
        return solve_ideal_feeder(market.a, market.b, market.U, energy,
                                  inst.slot_min / 60.0).dlmp_per_kwh

    states = np.empty((n+1, inst.n_slots))
    states[0] = depot_price(np.zeros(inst.n_slots))
    for k, price in enumerate(depot_price(loads)):
        states[k+1] = (1.0-alpha) * states[k] + alpha * price

    err = max(float(np.max(np.abs(states[:-1] - posted))),
              float(np.max(np.abs(states[-1] - final))))
    verdict = first_outcome(states, limit)
    expected = {"type": row["outcome"],
                "iter": n if row["outcome"] == "max_iters" else n-1}
    if row["outcome"] == "cycle":
        expected.update(length=int(row["cycle_length"]), first_seen=int(row["cycle_first_seen"]))
    elif row["cycle_length"] or row["cycle_first_seen"]:
        raise ValueError("cycle fields populated for another outcome")
    residual = float(np.max(np.abs(states[-1] - states[-2])))
    errors = []
    if err > PRICE_ATOL:
        errors.append("price trajectory")
    if verdict != expected or ck["outcome"] != expected:
        errors.append("first terminal state/iteration or cycle metadata")
    # T1 writes %.10g. Account for its last decimal, in addition to roundoff
    # in the two independently reconstructed states used by the residual.
    archived_residual = float(row["final_price_residual"])
    if not np.isclose(residual, archived_residual, rtol=5e-10, atol=2*PRICE_ATOL):
        errors.append("final residual at archived precision")
    return err, n, verdict, errors


def qualify():
    expected = {}
    for campaign, (_, _, seeds, sizes, slopes, alphas) in CAMPAIGNS.items():
        for cfg in product(seeds, sizes, slopes, alphas):
            expected[(campaign, cell_name(*cfg))] = cfg
    problems = []
    seen = set()
    max_error = None
    iterations = 0
    read_rows = passed = 0
    outcomes = Counter()
    try:
        with T1.open(newline="") as stream:
            for row in csv.DictReader(stream):
                read_rows += 1
                key = row.get("campaign"), row.get("cell")
                if key not in expected or key in seen:
                    problems.append({"assignment": key, "error": "unexpected or duplicate T1 row"})
                    continue
                seen.add(key)
                campaign, cell = key
                directory, limit, *_ = CAMPAIGNS[campaign]
                path = RESULT / directory / STAMP / "checkpoints" / cell / "loop.ckpt.json"
                try:
                    with path.open() as f:
                        ck = json.load(f)
                    err, n, verdict, errors = replay(row, ck, expected[key], limit)
                    max_error = err if max_error is None else max(err, max_error)
                    iterations += n
                    if errors:
                        problems.append({"assignment": key, "mismatches": errors,
                                         "max_price_error": err, "replayed": verdict})
                    else:
                        passed += 1
                        outcomes[verdict["type"]] += 1
                except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
                    problems.append({"assignment": key, "error": str(exc)})
    except (OSError, csv.Error, UnicodeError) as exc:
        problems.append({"table_error": str(exc)})
    missing = sorted(expected.keys() - seen)
    return {"status": "PASS" if passed == len(expected) and not problems else "FAIL",
            "scope": "conditional T1 replay with archived chronological fleet loads",
            "assigned": len(expected), "t1_rows_read": read_rows, "matched": passed,
            "unmatched": len(expected)-passed, "matched_outcomes": dict(outcomes),
            "iterations_replayed": iterations, "max_price_error_currency_per_kwh": max_error,
            "equality_atol": PRICE_ATOL, "historical_state_tolerance": STATE_TOL,
            "missing_t1_rows": missing, "problems": problems}


if __name__ == "__main__":
    result = qualify()
    print(json.dumps(result, allow_nan=False, separators=(",", ":")))
    sys.exit(0 if result["status"] == "PASS" else 1)
