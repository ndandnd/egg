"""Bounded literal set-partition check; run only after independent review/freeze.

Intended invocation: python -I -S -B literal_check.py
  --source-revision <claimed-frozen-40-hex-revision> --output <fresh-directory>
No project, solver, network, subprocess, or instance-data access occurs.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import resource
import signal
import sys
import time
from fractions import Fraction


START_CPU = time.process_time()
START_WALL = time.monotonic()
CHECKS = []
ALL_ROWS = (1 << 6) - 1
FLEET_CAP = 3


class VerificationFailure(Exception):
    pass


class BudgetFailure(Exception):
    pass


def budget_signal(signum, frame):
    raise BudgetFailure("Internal resource limit signal: " + str(signum))


def require(condition, name, detail=None):
    entry = {"name": name, "passed": bool(condition)}
    if detail is not None:
        entry["detail"] = detail
    CHECKS.append(entry)
    if not condition:
        raise VerificationFailure(name)


def column(name, rows, cost, new=False):
    mask = 0
    for row in rows:
        mask |= 1 << (row - 1)
    return {"name": name, "rows": tuple(rows), "mask": mask,
            "cost": Fraction(cost), "new": new}


def base_pool():
    return [
        column("A12", (1, 2), 1),
        column("A13", (1, 3), 1),
        column("A23", (2, 3), 1),
        column("B45", (4, 5), 1),
        column("B46", (4, 6), 1),
        column("B56", (5, 6), 1),
        column("fallback", (1, 2, 3, 4, 5, 6), 10),
    ]


def enumerate_integer(columns, new_limit=None):
    """Exhaust all at most 512 literal binary assignments; retain every optimum."""
    best = None
    minimizers = []
    examined = 0
    for bits in range(1 << len(columns)):
        examined += 1
        selected = [c for i, c in enumerate(columns) if bits & (1 << i)]
        if len(selected) > FLEET_CAP:
            continue
        if new_limit is not None and sum(c["new"] for c in selected) > new_limit:
            continue
        coverage = 0
        compatible = True
        for c in selected:
            if coverage & c["mask"]:
                compatible = False
                break
            coverage |= c["mask"]
        if not compatible or coverage != ALL_ROWS:
            continue
        cost = sum((c["cost"] for c in selected), Fraction(0))
        names = tuple(sorted(c["name"] for c in selected))
        if best is None or cost < best:
            best = cost
            minimizers = [names]
        elif cost == best:
            minimizers.append(names)
    if best is None:
        raise VerificationFailure("Protected integer model unexpectedly infeasible")
    return {"cost": best, "minimizers": tuple(sorted(minimizers)),
            "binary_assignments_examined": examined}


def serial_integer(result):
    return {"cost": str(result["cost"]),
            "minimizers": [list(s) for s in result["minimizers"]],
            "binary_assignments_examined": result["binary_assignments_examined"]}


def serial_columns(columns):
    return [{"name": c["name"], "rows": list(c["rows"]),
             "cost": str(c["cost"]), "new": c["new"]} for c in columns]


def verify_primal(columns, weights, label):
    coverage = [Fraction(0) for unused in range(6)]
    fleet = Fraction(0)
    cost = Fraction(0)
    for c in columns:
        weight = weights.get(c["name"], Fraction(0))
        require(weight >= 0, label + ":nonnegative:" + c["name"])
        fleet += weight
        cost += c["cost"] * weight
        for row in c["rows"]:
            coverage[row - 1] += weight
    require(coverage == [Fraction(1)] * 6, label + ":exact_coverage")
    require(fleet <= FLEET_CAP, label + ":fleet_cap")
    return {"weights": {name: str(value) for name, value in sorted(weights.items())},
            "coverage": [str(value) for value in coverage],
            "fleet": str(fleet), "cost": str(cost)}


def verify_dual(columns, label):
    # Min primal with fleet <= K has a nonpositive fleet dual multiplier.
    row_duals = [Fraction(1, 2)] * 6
    fleet_dual = Fraction(0)
    reduced = {}
    require(fleet_dual <= 0, label + ":fleet_dual_sign")
    for c in columns:
        rc = c["cost"] - sum((row_duals[r - 1] for r in c["rows"]), Fraction(0)) - fleet_dual
        reduced[c["name"]] = rc
        require(rc >= 0, label + ":dual_feasible:" + c["name"])
    objective = sum(row_duals, Fraction(0)) + FLEET_CAP * fleet_dual
    return {"row_duals": [str(value) for value in row_duals],
            "fleet_dual": str(fleet_dual), "objective": str(objective),
            "reduced_costs": {name: str(value) for name, value in sorted(reduced.items())}}


def verify_scenario(epsilon):
    label = "epsilon=" + str(epsilon)
    base = base_pool()
    candidates = [column("a", (1, 2, 3), Fraction(3, 2) + epsilon, True),
                  column("b", (4, 5, 6), Fraction(3, 2) + epsilon, True)]
    universe = base + candidates
    require(len(universe) == 9, label + ":nine_columns")
    for c in universe:
        require(bool(c["rows"]) and len(set(c["rows"])) == len(c["rows"])
                and all(1 <= r <= 6 for r in c["rows"]),
                label + ":valid_abstract_set:" + c["name"])
    weights = {c["name"]: Fraction(1, 2) for c in base if c["name"] != "fallback"}
    primal = verify_primal(universe, weights, label + ":LP")
    dual = verify_dual(universe, label + ":LP")
    require(primal["cost"] == dual["objective"] == "3", label + ":primal_dual_equality")
    require(dual["reduced_costs"]["a"] == str(epsilon)
            and dual["reduced_costs"]["b"] == str(epsilon), label + ":candidate_reduced_costs")

    pool_results = {}
    records = []
    for count in range(3):
        for subset in itertools.combinations(candidates, count):
            names = tuple(c["name"] for c in subset)
            result = enumerate_integer(base + list(subset))
            pool_results[names] = result
            expected_cost = Fraction(10) if count < 2 else min(Fraction(10), 3 + 2 * epsilon)
            require(result["cost"] == expected_cost, label + ":integer_cost:" + repr(names))
            expected_minimizers = []
            if count < 2 or Fraction(10) <= 3 + 2 * epsilon:
                expected_minimizers.append(("fallback",))
            if count == 2 and 3 + 2 * epsilon <= Fraction(10):
                expected_minimizers.append(("a", "b"))
            require(result["minimizers"] == tuple(sorted(expected_minimizers)),
                    label + ":all_integer_minimizers:" + repr(names))
            record = {"added_columns": list(names), "integer": serial_integer(result),
                      "utility": str(Fraction(10) - result["cost"])}
            records.append(record)

    completion_records = []
    for k in range(3):
        allowed = [(names, result) for names, result in pool_results.items() if len(names) <= k]
        augmentation_best = min(result["cost"] for names, result in allowed)
        best_augmentations = [names for names, result in allowed if result["cost"] == augmentation_best]
        augmentation_solutions = set()
        for names, result in allowed:
            if result["cost"] == augmentation_best:
                augmentation_solutions.update(result["minimizers"])
        direct = enumerate_integer(universe, new_limit=k)
        require(augmentation_best == direct["cost"], label + ":completion_identity_cost:k=" + str(k))
        require(augmentation_solutions == set(direct["minimizers"]),
                label + ":completion_identity_all_minimizers:k=" + str(k))
        completion_records.append({"k": k, "best_augmentation_cost": str(augmentation_best),
                                   "all_best_augmentations": [list(s) for s in best_augmentations],
                                   "direct_completion": serial_integer(direct)})
    return {"epsilon": str(epsilon), "columns": serial_columns(universe),
            "LP_primal": primal, "LP_dual": dual,
            "augmentations": records, "completion_identity": completion_records}


def verify_negative_singleton():
    base = base_pool()
    a = column("a", (1, 2, 3), 1, True)
    base_dual = verify_dual(base, "negative_singleton:original_pool")
    rc = a["cost"] - Fraction(1, 2) * len(a["rows"])
    require(rc == Fraction(-1, 2), "negative_singleton:negative_reduced_cost")
    before = enumerate_integer(base)
    after = enumerate_integer(base + [a])
    require(before["cost"] == after["cost"] == 10, "negative_singleton:zero_integer_utility")
    require(after["minimizers"] == (("fallback",),), "negative_singleton:all_minimizers")
    weights = {"a": Fraction(1), "B45": Fraction(1, 2),
               "B46": Fraction(1, 2), "B56": Fraction(1, 2)}
    improved_primal = verify_primal(base + [a], weights, "negative_singleton:improved_LP_witness")
    require(improved_primal["cost"] == "5/2", "negative_singleton:strict_LP_improvement")
    return {"candidate": serial_columns([a])[0], "original_pool_dual": base_dual,
            "reduced_cost_against_original_dual": str(rc),
            "before": serial_integer(before), "after": serial_integer(after),
            "integer_utility": "0", "improved_LP_primal_witness": improved_primal,
            "note": "Original dual is not claimed feasible after adding the negative-RC column."}


def prepublication_metrics():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {"process_cpu_seconds": time.process_time() - START_CPU,
            "wall_seconds": time.monotonic() - START_WALL,
            "cpu_wall_scope": "This process after stdlib imports through this prepublication sample; excludes startup/imports, final JSON serialization, and publication.",
            "max_rss_raw": usage.ru_maxrss,
            "max_rss_unit": "bytes" if sys.platform == "darwin" else "KiB (platform getrusage convention)",
            "rss_scope": "Lifetime high-water RSS of this process, including interpreter startup and imports; excludes parent/supervisor.",
            "internal_limits": {"cpu_soft_seconds": 3, "cpu_hard_seconds": 4,
                                "realtime_alarm_seconds": 5},
            "external_budget": "Prospective 5 CPU seconds / 10 wall seconds must be enforced and measured by the parent; not certified by this self-report."}


def main():
    output_dir = None
    publication_attempted = False
    payload = {"status": "failure", "checks": CHECKS,
               "scope": "Literal abstract six-row illustration only; no physical EVSP, empirical failure, novelty, convergence, or global-pricing claim."}
    try:
        signal.signal(signal.SIGXCPU, budget_signal)
        signal.signal(signal.SIGALRM, budget_signal)
        resource.setrlimit(resource.RLIMIT_CPU, (3, 4))
        signal.setitimer(signal.ITIMER_REAL, 5)
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--source-revision", required=True)
        parser.add_argument("--output", required=True)
        args = parser.parse_args()
        output_dir_candidate = Path(args.output)
        # Fail without touching an existing directory or its contents.
        output_dir_candidate.mkdir(exist_ok=False)
        output_dir = output_dir_candidate
        payload["claimed_frozen_source_revision"] = args.source_revision
        require(len(args.source_revision) == 40
                and all(c in "0123456789abcdefABCDEF" for c in args.source_revision),
                "claimed_revision_is_40_hex")
        flags = {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                 "dont_write_bytecode": sys.flags.dont_write_bytecode}
        payload["interpreter_flags"] = flags
        require(all(value == 1 for value in flags.values()), "required_python_I_S_B_flags")
        # Exactly one own-source read, with the hash derived from that same buffer.
        source_buffer = Path(__file__).read_bytes()
        payload["own_source"] = {"path": str(Path(__file__)), "bytes": len(source_buffer),
                                 "sha256": hashlib.sha256(source_buffer).hexdigest(),
                                 "read_count": 1,
                                 "revision_scope": "Caller-supplied claim only; no repository was read or revision verified."}
        payload["scenarios"] = [verify_scenario(epsilon) for epsilon in
                                (Fraction(0), Fraction(1, 2), Fraction(7, 2), Fraction(4))]
        payload["negative_singleton"] = verify_negative_singleton()
        require(all(entry["passed"] for entry in CHECKS), "all_checks_pass")
        payload["status"] = "success"
        payload["self_prepublication_metrics"] = prepublication_metrics()
        publication_attempted = True
        with (output_dir / "results.json").open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        signal.setitimer(signal.ITIMER_REAL, 0)
        return 0
    except Exception as exc:
        payload["status"] = "failure"
        payload["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if output_dir is not None and not publication_attempted:
            try:
                payload["self_prepublication_metrics"] = prepublication_metrics()
                publication_attempted = True
                with (output_dir / "results.json").open("x", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
                    handle.write("\n")
            except Exception:
                pass
        # No retry, alternate execution path, or second publication attempt.
        return 1


if __name__ == "__main__":
    sys.exit(main())
