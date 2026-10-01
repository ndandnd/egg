#!/usr/bin/env python3
"""Compact, read-only physical/bound reconciliation for the sealed pilot."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
EGG = REPO.parent
DEFAULT_ATTEMPT = EGG / "research-20260928/cluster/pricing-start-pilot-attempt1/sealed/20260928-attempt1"
DEFAULT_SOURCE = EGG / "research-20260928/cluster/solver-baseline-comparison-attempt1/sealed/20260928-attempt1"
sys.path.insert(0, str(REPO / "src"))

from egglab import native_recharge as nr  # noqa: E402
from experiments import computational_benchmark as base  # noqa: E402
from experiments import pricing_start_pilot as runner  # noqa: E402


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def close(a, b, *, atol=1e-7, rtol=1e-10):
    return (isinstance(a, (int, float)) and isinstance(b, (int, float))
            and math.isfinite(a) and math.isfinite(b)
            and math.isclose(a, b, abs_tol=atol, rel_tol=rtol))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def bill(column, prices):
    return Fraction(column["ops_cost"]) + sum(
        (Fraction(p) * Fraction(load) for p, load in zip(prices, column["load"])), Fraction(0))


def choose(columns, prices):
    return min(columns, key=lambda col: (bill(col, prices), col["key"]))


def check_source_pool(source_root, frozen, case_name, case, market):
    row = frozen["cases"][case_name]
    source = row["source"]
    require(source.get("eligible") is True, f"{case_name}: source was not eligible")
    folder = Path(source_root) / case_name / "state0/qp_cache_feasible_hull"
    hashes = source["source_files"]
    for filename in ("raw_result.json", "receipt.json"):
        require(sha(folder / filename) == hashes[filename]["sha256"],
                f"{case_name}: source {filename} hash differs from freeze")
    raw = load(folder / "raw_result.json")
    receipt = load(folder / "receipt.json")
    require((raw.get("case"), raw.get("state"), raw.get("stage")) ==
            (case_name, 0, "qp_cache_feasible_hull"), f"{case_name}: source identity differs")
    pool = raw["result"]
    require(pool.get("status") == source["source_status"], f"{case_name}: source status differs")
    require(receipt.get("returncode") == 0 and receipt.get("on_time") is True
            and close(receipt.get("elapsed_seconds"), source["source_child_elapsed_seconds"]),
            f"{case_name}: source paid-time receipt differs")
    columns = pool.get("columns")
    require(isinstance(columns, list) and columns, f"{case_name}: source pool has no columns")

    linear = [float(Fraction(a)) for a in market.a]
    linear_column = choose(columns, linear)
    queries = row["queries"]
    require(queries["linear_tariff"]["prices"] == linear,
            f"{case_name}: linear query prices differ from state-1 tariff")
    exact_linear = [str(Fraction(a)) for a in market.a]
    require(queries["linear_tariff"]["prices_exact"] == exact_linear,
            f"{case_name}: exact linear prices differ")
    marginal_exact = [Fraction(a) + Fraction(b) * Fraction(load)
                      for a, b, load in zip(market.a, market.b, linear_column["load"])]
    marginal = [float(p) for p in marginal_exact]
    require(queries["marginal_price"]["prices"] == marginal
            and queries["marginal_price"]["prices_exact"] == [str(p) for p in marginal_exact],
            f"{case_name}: marginal-price gradient differs")
    require(queries["marginal_price"].get("gradient_anchor_key") == linear_column["key"],
            f"{case_name}: gradient anchor differs from linear-tariff source minimum")
    require(queries["marginal_price"].get("duplicates_linear_prices") == (marginal == linear),
            f"{case_name}: duplicate-query flag differs")

    baseline = {}
    for query, prices in (("linear_tariff", linear), ("marginal_price", marginal)):
        selected = queries[query]
        expected_col = choose(columns, prices)
        require(selected["source_column_key"] == expected_col["key"],
                f"{case_name}/{query}: selected source column is not the deterministic pool minimum")
        require(selected["source_plan_hash"] == nr.digest(expected_col["plan"])
                and selected["source_plan"] == expected_col["plan"],
                f"{case_name}/{query}: frozen source plan is not the selected raw source column")
        replay = nr.replay_native(case, selected["source_plan"], prices)
        objective = float(bill(expected_col, prices))
        require(close(replay["pricing_objective"], objective)
                and close(selected["source_pricing_objective"], objective),
                f"{case_name}/{query}: common source upper does not replay")
        require(replay["load"] == selected["source_load"],
                f"{case_name}/{query}: source load differs from physical replay")
        baseline[query] = {"plan_hash": selected["source_plan_hash"], "objective": objective,
                           "selected_column": selected["source_column_key"]}
    return baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    attempt, source_root = args.attempt.resolve(), args.source_root.resolve()
    frozen, summary = load(attempt / "frozen.json"), load(attempt / "summary.json")
    supervisor = load(attempt / "supervisor_receipt.json")

    # Check only the code used by this replay and the configured source inventory;
    # transport/seal-manifest verification belongs to the parent review.
    for rel in ("src/experiments/pricing_start_pilot.py", "src/egglab/native_recharge.py"):
        require(frozen["source_hashes"].get(rel) == sha(REPO / rel), f"Execution pin differs: {rel}")
    inventory = REPO / "research-20260928/pricing-start/SOURCE_INVENTORY.json"
    require(sha(inventory) == frozen["source_inventory_sha256"], "Source inventory pin differs")
    source_frozen = source_root / "frozen.json"
    require(sha(source_frozen) == frozen["source_root_frozen_sha256"], "Source-attempt freeze pin differs")
    require(summary.get("protocol") == runner.PROTOCOL and summary.get("all_declared_calls_accounted") is True,
            "Summary protocol/accounting marker differs")
    require(len(summary.get("rows", [])) == 16, "Expected exactly 16 declared rows")
    require(supervisor.get("returncode") == 0 and supervisor.get("hard_timeout") is False
            and supervisor.get("process_group_quiescent") is True
            and supervisor.get("stable_seal") is True
            and supervisor.get("source_and_inputs_unchanged") is True,
            "Supervisor completion/quiescence/input receipt is not clean")

    expected_order = [(case, query, arm) for case in frozen["case_order"]
                      for query in frozen["query_order"]
                      for arm in frozen["arm_orders"][case][query]]
    observed_order = [(r.get("case"), r.get("query"), r.get("arm")) for r in summary["rows"]]
    require(observed_order == expected_order, "Summary row order differs from frozen arm schedule")

    cases = base.cases()
    baselines = {}
    for name in frozen["case_order"]:
        baselines[name] = check_source_pool(source_root, frozen, name, cases[name], base.market(name, 1))

    checked_rows, pairs = [], []
    online_sum = 0.0
    per_pair = {}
    for row in summary["rows"]:
        name, query, arm = row["case"], row["query"], row["arm"]
        folder = attempt / name / query / arm
        receipt = load(folder / "receipt.json")
        selected = frozen["cases"][name]["queries"][query]
        require(row["status"] == "returned" and receipt.get("returncode") == 0
                and receipt.get("hard_timeout") is False and receipt.get("on_time") is True,
                f"{name}/{query}/{arm}: call was not a clean return")
        require(row.get("receipt") == receipt, f"{name}/{query}/{arm}: summary receipt differs")
        expected_hard = base.budget(name, "cold_hull").wall_seconds + 30
        require(receipt.get("hard_seconds") == expected_hard
                and receipt.get("elapsed_seconds", math.inf) <= expected_hard,
                f"{name}/{query}/{arm}: paid receipt exceeds declared child cap")
        online_sum += receipt["elapsed_seconds"]
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
        starts = [event for event in events if event.get("event") == "native_start"]
        statuses = [event for event in events if event.get("event") == "native_status"]
        setups = [event for event in events if event.get("event") == "mip_start_setup"]
        require(len(starts) == len(statuses) == 1, f"{name}/{query}/{arm}: native event counts differ")
        expected_probe = frozen["native_probe"]
        require(starts[0].get("model_seed") == expected_probe["model_seed"]
                and starts[0].get("backend_runtime") == expected_probe["backend_identity"]
                and starts[0].get("backend") == "GRB", f"{name}/{query}/{arm}: seed/backend differs")
        if arm == "start":
            require(len(setups) == 1 and setups[0].get("status") == "submitted",
                    f"{name}/{query}/start: start setup was not submitted exactly once")
            require(row.get("native_acceptance") == "unknown" and row.get("start_submitted") is True,
                    f"{name}/{query}/start: acceptance was inferred or submission lost")
        else:
            require(not setups, f"{name}/{query}/cold: unexpected start event")
        require(row.get("start_setup_events") == setups
                and row.get("native_start_events") == 1 and row.get("native_status_events") == 1
                and not row.get("evidence_issues"), f"{name}/{query}/{arm}: summary event accounting differs")

        result = load(folder / "raw_result.json")
        result_doc = load(folder / "result.json")
        case = cases[name]
        prices = selected["prices"]
        require(result.get("case_identity") == case.identity() and result.get("prices") == prices,
                f"{name}/{query}/{arm}: native result identity/price differs")
        source_upper = baselines[name][query]["objective"]
        require(close(row.get("known_source_upper"), source_upper),
                f"{name}/{query}/{arm}: common source upper differs")
        plan = result.get("plan")
        replay = nr.replay_native(case, plan, prices) if plan is not None else None
        if replay is not None:
            admitted = nr.admit_bound(result["stats"], replay["pricing_objective"])
            require(result.get("lower") is not None and result.get("upper") is not None
                    and close(result["lower"], admitted[0]) and close(result["upper"], admitted[1]),
                    f"{name}/{query}/{arm}: admitted interval does not replay")
            interval = [result["lower"], result["upper"]]
            feasible_upper = min(source_upper, replay["pricing_objective"])
        else:
            require(result.get("lower") is None and result.get("upper") is None,
                    f"{name}/{query}/{arm}: raw no-plan bound leaked into interval")
            interval = None
            feasible_upper = source_upper
        assessment = result_doc["assessment"]
        require(row.get("native_admitted_interval") == interval
                and assessment.get("native_admitted_interval") == interval,
                f"{name}/{query}/{arm}: summary interval differs from raw replay")
        require(close(row.get("best_feasible_upper"), feasible_upper)
                and close(assessment.get("best_feasible_upper"), feasible_upper),
                f"{name}/{query}/{arm}: best feasible upper differs")
        require(close(row.get("native_replayed_objective"),
                     replay["pricing_objective"] if replay else None),
                f"{name}/{query}/{arm}: replayed native objective differs")

        stats = result["stats"]
        core_elapsed = result_doc["core_call_elapsed_seconds"]
        expected_phase = base.budget(name, "cold_hull").phase_seconds
        require(stats.get("seconds_cap") == expected_phase and stats.get("threads") == 1
                and stats.get("backend") == "GRB" and close(stats.get("wall_s"), statuses[0]["stats"]["wall_s"]),
                f"{name}/{query}/{arm}: native status/cap/thread telemetry differs")
        require(core_elapsed <= base.budget(name, "cold_hull").wall_seconds + 0.5,
                f"{name}/{query}/{arm}: core-call elapsed exceeds declared wall cap")
        if setups:
            setup_s = setups[0]["setup_elapsed_s"]
            require(setup_s <= core_elapsed + 1e-6,
                    f"{name}/{query}/{arm}: setup accounting exceeds core-call elapsed")
        source_inclusive = result_doc["actual_environment"]
        for key, value in frozen["environment"].items():
            require(source_inclusive.get(key) == value, f"{name}/{query}/{arm}: runtime {key} differs")

        checked = {"case": name, "query": query, "arm": arm, "native_status": result["status"],
                   "native_objective": replay["pricing_objective"] if replay else None,
                   "admitted_interval": interval, "common_source_upper": source_upper,
                   "best_feasible_upper": feasible_upper, "child_seconds": receipt["elapsed_seconds"],
                   "native_seconds": stats["wall_s"],
                   "setup_seconds": setups[0]["setup_elapsed_s"] if setups else None,
                   "native_acceptance": row.get("native_acceptance")}
        checked_rows.append(checked)
        per_pair.setdefault((name, query), {})[arm] = checked

    source_once = sum(frozen["cases"][name]["source"]["source_child_elapsed_seconds"]
                      for name in frozen["case_order"])
    require(close(summary["conditional_online_child_seconds"], online_sum, atol=1e-8),
            "Online child time sum differs from all 16 receipts")
    require(close(summary["historical_source_once_seconds"], source_once, atol=1e-8),
            "Historical source child time is not counted once")
    prep = frozen["freeze_preparation_elapsed_seconds"]
    require(close(summary["freeze_preparation_once_seconds"], prep, atol=1e-8),
            "Freeze preparation time differs")
    require(close(summary["source_inclusive_seconds"], source_once + prep + online_sum, atol=1e-8),
            "Source-inclusive total does not reconcile")

    for key, arms in per_pair.items():
        cold, start = arms["cold"], arms["start"]
        pairs.append({"case": key[0], "query": key[1],
                      "start_minus_cold_native_objective": start["native_objective"] - cold["native_objective"],
                      "start_minus_cold_lower": start["admitted_interval"][0] - cold["admitted_interval"][0],
                      "start_minus_cold_upper": start["admitted_interval"][1] - cold["admitted_interval"][1],
                      "start_minus_cold_child_seconds": start["child_seconds"] - cold["child_seconds"]})

    public_rows = [r for r in checked_rows if r["case"].startswith("public_")]
    public_at_cap = sum(math.isclose(r["native_seconds"], 160.0, rel_tol=0, abs_tol=0.1)
                        for r in public_rows)
    output = {"checks": "passed", "native_optimization_performed": False,
              "declared_rows": len(checked_rows), "status_counts": {"returned": len(checked_rows)},
              "public_calls_at_160s_native_phase_cap": public_at_cap,
              "conditional_online_child_seconds": online_sum,
              "historical_source_once_seconds": source_once,
              "freeze_preparation_once_seconds": prep,
              "source_inclusive_seconds": source_once + prep + online_sum,
              "rows": checked_rows, "paired_deltas_start_minus_cold": pairs}
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
