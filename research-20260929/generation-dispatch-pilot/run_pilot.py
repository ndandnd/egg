"""One bounded local LP verification of PROTOCOL.md; no parameter sweep."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np

from egglab.convex_dispatch import (
    Generator,
    bounded_linprog,
    capture_lp_timings,
    dispatch_matrices,
    incremental_cost,
    optimal_price_ranges,
    solve_dispatch,
)


def units(up_ramp: float) -> tuple[Generator, Generator]:
    return (
        Generator("A", (7, 5, 1), (10, 15, 15), (10, up_ramp, up_ramp), 30, 0),
        Generator("B", (6, 5, 5), (10, 15, 30), 30, 30, 0),
    )


def hull_lp(generators: tuple[Generator, ...]) -> dict:
    """Mix the complete one-bus point and the full two-bus interval."""
    costs, eq, ub, rhs, _ = dispatch_matrices(generators, 3)
    # Variables: generator outputs, mean early load x, one-bus weight lambda.
    n = len(costs)
    objective = np.concatenate((costs, [0, -7]))
    balance = np.zeros((3, n + 2))
    balance[:, :n] = eq
    balance[0, n] = -1
    balance[2, n] = 1
    inequalities = np.vstack((np.pad(ub, ((0, 0), (0, 2))), np.array([*([0] * n), -1, 10])))
    limits = np.concatenate((rhs, [0]))
    solved = bounded_linprog(
        objective,
        A_eq=balance,
        b_eq=(0, 15, 30),
        A_ub=inequalities,
        b_ub=limits,
        bounds=[(0, None)] * n + [(0, 10), (0, 1)],
    )
    if solved.status != 0:
        raise RuntimeError(solved.message)
    return {
        "incremental_value": 14 + solved.fun - 75,
        "gross_value": 14 + solved.fun,
        "mean_early_load": solved.x[n],
        "one_bus_weight": solved.x[n + 1],
        "generation": solved.x[:n].tolist(),
    }


def case(generators: tuple[Generator, ...]) -> dict:
    samples = {}
    for x in (0, 5, 10):
        solved = solve_dispatch(generators, (x, 15, 30 - x))
        samples[str(x)] = {
            "gross_supply": solved.objective,
            "incremental_supply": solved.objective - 75 if solved.objective is not None else None,
            "generation": solved.output,
            "price": solved.balance_price,
            "dual": solved.dual_objective,
            "primal_residual": solved.max_primal_residual,
            "dual_violation": solved.max_dual_violation,
            "complementarity": solved.max_complementarity,
            "binding": [
                name
                for name, slack in zip(solved.constraint_names, solved.constraint_slack or ())
                if abs(slack) < 1e-7
            ],
        }
    return {
        "samples": samples,
        "hull": hull_lp(generators),
        "price_ranges_at_5": optimal_price_ranges(generators, (5, 15, 25)),
        "price_ranges_at_10": optimal_price_ranges(generators, (10, 15, 20)),
        "baseline_cost": solve_dispatch(generators, (0, 15, 0)).objective,
        "incremental_5": incremental_cost(generators, (0, 15, 0), (5, 0, 25)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new JSON output path; must not exist")
    args = parser.parse_args()
    path = args.output or Path(__file__).with_name(
        f"RESULT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.json"
    )
    start = perf_counter()
    with capture_lp_timings() as lp_timings:
        result = {"ramp": case(units(5)), "control_relaxed_ramp": case(units(30))}
    result["timing"] = {
        "run_elapsed_seconds": perf_counter() - start,
        "lp_elapsed_seconds": lp_timings,
        "note": "local process wall times, not a benchmark",
    }
    with path.open("x") as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
