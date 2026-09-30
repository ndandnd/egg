#!/usr/bin/env python3
"""Recompute tariff-response outcomes from compact frozen campaign receipts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATTEMPT = ROOT / "result/learning_campaign/20260930-tariff-response-attempt1"
DEFAULT_OUTPUT = ROOT / "research-20260930/learning-campaign/TARIFF_RESPONSE_ANALYSIS.json"
METHODS = (
    "always_source0", "always_source1", "train_majority", "cheapest_direct",
    "nearest_price", "frozen_edge_prior", "charge_response_ridge",
)


def read_json(path: Path, errors: list[str] | None = None) -> dict[str, Any] | None:
    if not path.is_file():
        if errors is not None:
            errors.append(f"missing:{path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        if errors is not None:
            errors.append(f"{path.name}:{type(exc).__name__}")
        return None
    if not isinstance(value, dict):
        if errors is not None:
            errors.append(f"{path.name}:not_object")
        return None
    return value


def frac(value: Any) -> Fraction | None:
    if value is None or value == "":
        return None
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def exact(value: Any) -> str | None:
    parsed = frac(value)
    return str(parsed) if parsed is not None else None


def numeric(value: Any) -> float | None:
    parsed = frac(value)
    return float(parsed) if parsed is not None else None


def movement_set(plan: Any) -> set[str] | None:
    if not isinstance(plan, dict) or not isinstance(plan.get("vehicles"), list):
        return None
    ids: set[str] = set()
    for vehicle in plan["vehicles"]:
        movements = vehicle.get("movements") if isinstance(vehicle, dict) else None
        if not isinstance(movements, list):
            return None
        ids.update(str(mid) for mid in movements)
    return ids


def compact_failure(label: dict[str, Any], receipt: dict[str, Any] | None) -> dict[str, str] | None:
    failure = label.get("failure")
    if isinstance(failure, dict):
        return {"type": str(failure.get("type") or ""), "message": str(failure.get("message") or "")}
    if failure:
        return {"type": type(failure).__name__, "message": str(failure)}
    if receipt and receipt.get("error"):
        err = receipt["error"]
        return {"type": type(err).__name__, "message": str(err)}
    return None


def parse_seed_services(case: str) -> tuple[int, int]:
    prefix = "learning_s"
    if not case.startswith(prefix) or "_n" not in case:
        return 0, 0
    seed, services = case[len(prefix):].split("_n", 1)
    try:
        return int(seed), int(services)
    except ValueError:
        return 0, 0


def rounded(value: Fraction | None) -> float | None:
    return round(float(value), 12) if value is not None else None


def build(attempt: Path) -> dict[str, Any]:
    summary = json.loads((attempt / "summary.json").read_text(encoding="utf-8"))
    frozen = json.loads((attempt / "frozen.json").read_text(encoding="utf-8"))
    design = frozen["design"]
    catalog_rows = [json.loads(line) for line in (attempt / "catalog.jsonl").read_text(encoding="utf-8").splitlines() if line]
    catalog = {str(row["row_id"]): row for row in catalog_rows}
    if len(catalog) != len(catalog_rows):
        raise ValueError("duplicate catalog row_id")

    baseline_errors: list[str] = []
    baseline = read_json(attempt / "baseline_choices.json", baseline_errors) or {}
    proposals_errors: list[str] = []
    proposals = read_json(attempt / "learned/proposals.json", proposals_errors) or {}
    inference_errors: list[str] = []
    inference = read_json(attempt / "inference_receipt.json", inference_errors) or {}
    baseline_receipt = read_json(attempt / "baseline_choices_receipt.json", inference_errors) or {}

    case_for_seed = {int(group["seed"]): name for name, group in design["groups"].items()}
    expected_order = list(design.get("cell_order", []))
    if len(expected_order) != int(summary.get("declared_cells", -1)):
        raise ValueError("frozen cell order and declared cell count disagree")

    cells: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    topology_checks: list[dict[str, Any]] = []
    cell_statuses: Counter[str] = Counter()
    native_statuses: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    cell_type_counts: Counter[str] = Counter()
    timeout_count = 0
    returned_count = 0
    feasible_count = 0
    exact_cost_count = 0
    catalog_missing: list[str] = []
    for order, ref in enumerate(expected_order, start=1):
        seed = int(ref["seed"])
        case = case_for_seed[seed]
        stage = str(ref["stage"])
        row_id = f"{case}/{stage}"
        cat = catalog.get(row_id)
        if cat is None:
            catalog_missing.append(row_id)
            cells.append({"order": order, "row_id": row_id, "case": case, "seed": seed,
                          "services": int(design["profile"][str(seed)]), "stage": stage,
                          "cell_status": "missing_catalog", "feasible": False,
                          "artifact_errors": ["catalog_row_missing"]})
            failures.append({"row_id": row_id, "reason": "catalog_row_missing"})
            continue

        label = cat.get("label") if isinstance(cat.get("label"), dict) else {}
        errors: list[str] = []
        receipt = read_json(attempt / case / "state0" / stage / "receipt.json", errors)
        if errors:
            failures.append({"row_id": row_id, "artifact_errors": errors})
        status = str(label.get("status") or "missing_status")
        cell_statuses[status] += 1
        role = str(cat.get("market_role") or "unknown")
        role_counts[role] += 1
        cell_type = "source_acquisition" if role == "source" else (
            "fixed_route_charge_lp" if "_charge_" in stage else "cold_target_hull")
        cell_type_counts[cell_type] += 1
        native_status = str(label.get("native_status") or "none")
        native_statuses[native_status] += 1
        if status == "returned" and receipt and receipt.get("returncode") == 0:
            returned_count += 1
        if label.get("feasible") is True:
            feasible_count += 1
        if label.get("objective_exact") not in (None, ""):
            exact_cost_count += 1
        hard_timeout = bool(receipt and receipt.get("hard_timeout"))
        timeout_count += int(hard_timeout)
        failure = compact_failure(label, receipt)
        if failure:
            failures.append({"row_id": row_id, "failure": failure})

        rec: dict[str, Any] = {
            "order": order, "row_id": row_id, "case": case, "seed": seed,
            "services": int(design["profile"][str(seed)]), "split": cat.get("split"),
            "market_role": role, "stage": stage, "tariff_variant": cat.get("tariff_variant"),
            "cell_status": status, "feasible": label.get("feasible"),
            "native_status": label.get("native_status"), "optimality": label.get("optimality"),
            "objective_exact": exact(label.get("objective_exact")),
            "objective_cost_units": numeric(label.get("objective_exact")),
            "lower_exact": exact(label.get("lower_exact")), "lower_cost_units": numeric(label.get("lower_exact")),
            "upper_exact": exact(label.get("upper_exact")), "upper_cost_units": numeric(label.get("upper_exact")),
            "native_mixture_upper_exact": exact(label.get("native_mixture_upper_exact")),
            "native_mixture_upper_cost_units": numeric(label.get("native_mixture_upper_exact")),
            "label_elapsed_seconds": label.get("elapsed_seconds"),
            "charge_wall_seconds": label.get("charge_wall_seconds"),
            "independent_replay_wall_seconds": label.get("independent_replay_wall_seconds"),
            "child_return_code": receipt.get("returncode") if receipt else None,
            "child_elapsed_seconds": receipt.get("elapsed_seconds") if receipt else None,
            "child_hard_seconds": receipt.get("hard_seconds") if receipt else None,
            "child_hard_timeout": receipt.get("hard_timeout") if receipt else None,
            "child_on_time": receipt.get("on_time") if receipt else None,
            "plan_hash": label.get("plan_hash"), "failure": failure,
            "artifact_errors": errors,
        }

        if "_charge_" in stage:
            source = stage.split("_charge_", 1)[0]
            source_id = f"{case}/{source}"
            source_cat = catalog.get(source_id, {})
            source_label = source_cat.get("label", {}) if isinstance(source_cat, dict) else {}
            source_plan = source_label.get("plan") if isinstance(source_label, dict) else None
            charged_plan = label.get("plan")
            source_moves = movement_set(source_plan)
            charge_moves = movement_set(charged_plan)
            hash_match = label.get("source_plan_hash") == source_label.get("plan_hash")
            move_match = source_moves is not None and source_moves == charge_moves
            topology = {
                "source_row_id": source_id,
                "source_plan_hash_matches": hash_match,
                "source_movement_set_matches": move_match,
                "source_movement_count": len(source_moves) if source_moves is not None else None,
                "charged_movement_count": len(charge_moves) if charge_moves is not None else None,
            }
            rec["source_topology_replay"] = topology
            topology_checks.append({"row_id": row_id, **topology})
        cells.append(rec)

    group_results: list[dict[str, Any]] = []
    comparisons_checked = 0
    group_mean_checks = 0
    switch_checks = 0
    all_pair_feasible = True
    variants_order = [str(v) for v in design["variants"]]
    group_choices_for_method: dict[str, dict[str, list[str]]] = {m: {} for m in METHODS}
    group_excess_exact: dict[str, dict[str, str]] = {}
    all_variants: list[dict[str, Any]] = []
    model_choice_failures: list[dict[str, Any]] = []
    baseline_mismatches: list[dict[str, Any]] = []
    candidate_hash_mismatches: list[dict[str, Any]] = []

    for case, frozen_group in design["groups"].items():
        seed = int(frozen_group["seed"])
        services = int(frozen_group["services"])
        summary_group = summary.get("groups", {}).get(case, {})
        variant_rows: list[dict[str, Any]] = []
        per_group_excess: dict[str, list[Fraction]] = {m: [] for m in METHODS}
        per_group_choices: dict[str, list[str]] = {m: [] for m in METHODS}
        for variant in variants_order:
            stages = {
                "source0": f"source0_charge_{variant}",
                "source1": f"source1_charge_{variant}",
                "cold": f"cold_{variant}",
            }
            source0_id = f"{case}/{stages['source0']}"
            source1_id = f"{case}/{stages['source1']}"
            charge0 = catalog.get(source0_id, {}).get("label", {})
            charge1 = catalog.get(source1_id, {}).get("label", {})
            costs = {"source0": frac(charge0.get("objective_exact")),
                     "source1": frac(charge1.get("objective_exact"))}
            available = {k: v for k, v in costs.items() if v is not None}
            all_pair_feasible = all_pair_feasible and all(
                catalog.get(f"{case}/{stages[src]}", {}).get("label", {}).get("feasible") is True
                for src in ("source0", "source1")
            )
            best = min(available.values()) if available else None
            winners = [src for src in ("source0", "source1") if costs[src] is not None and costs[src] == best]

            proposal = proposals.get(case, {}).get(variant, {}) if isinstance(proposals.get(case), dict) else {}
            base_choice = baseline.get(case, {}).get(variant, {}) if isinstance(baseline.get(case), dict) else {}
            choices = proposal.get("choices", {}) if isinstance(proposal.get("choices"), dict) else {}
            baseline_choices = base_choice.get("choices", {}) if isinstance(base_choice.get("choices"), dict) else {}
            proposal_failure = proposal.get("failure")
            if proposal_failure:
                model_choice_failures.append({"case": case, "variant": variant, "failure": proposal_failure})
            summary_variant = summary_group.get("variants", {}).get(variant, {})
            if summary_variant.get("choice_failure"):
                model_choice_failures.append({"case": case, "variant": variant,
                                              "choice_failure": summary_variant["choice_failure"]})
            for method, source in baseline_choices.items():
                if choices.get(method) != source:
                    baseline_mismatches.append({"case": case, "variant": variant,
                                                "method": method, "baseline": source,
                                                "proposal": choices.get(method)})

            candidates = proposal.get("candidates", [])
            candidate_hashes: dict[str, str] = {}
            for candidate in candidates if isinstance(candidates, list) else []:
                if isinstance(candidate, dict) and candidate.get("source"):
                    candidate_hashes[str(candidate["source"])] = str(candidate.get("plan_hash") or "")
            expected_hashes = {
                source: str(catalog.get(f"{case}/{source}", {}).get("label", {}).get("plan_hash") or "")
                for source in ("source0", "source1")
            }
            candidate_hash_match = all(candidate_hashes.get(k) == v and v for k, v in expected_hashes.items())
            if not candidate_hash_match:
                candidate_hash_mismatches.append({"case": case, "variant": variant,
                                                  "expected": expected_hashes, "actual": candidate_hashes})

            method_results: dict[str, Any] = {}
            summary_methods = summary_variant.get("methods", {})
            for method in METHODS:
                selected = choices.get(method)
                selected_cost = costs.get(selected) if selected in costs else None
                excess = selected_cost - best if selected_cost is not None and best is not None else None
                reported = summary_methods.get(method, {}) if isinstance(summary_methods, dict) else {}
                reported_excess = frac(reported.get("candidate_pool_excess_exact"))
                reported_cost = frac(reported.get("post_lp_objective_exact"))
                matched = (selected == reported.get("source") and excess == reported_excess
                           and selected_cost == reported_cost)
                comparisons_checked += 1
                if not matched:
                    model_choice_failures.append({"case": case, "variant": variant, "method": method,
                                                  "recomputed_source": selected,
                                                  "reported_source": reported.get("source"),
                                                  "recomputed_excess_exact": exact(excess),
                                                  "reported_excess_exact": exact(reported.get("candidate_pool_excess_exact"))})
                if excess is not None:
                    per_group_excess[method].append(excess)
                if selected is not None:
                    per_group_choices[method].append(str(selected))
                method_results[method] = {
                    "source": selected,
                    "objective_exact": exact(selected_cost),
                    "objective_cost_units": numeric(selected_cost),
                    "paired_excess_exact": exact(excess),
                    "paired_excess_cost_units": numeric(excess),
                    "lp_paid_seconds": reported.get("one_lp_paid_seconds"),
                    "source_acquisition_plus_one_lp_seconds": reported.get("source_acquisition_plus_one_lp_seconds"),
                    "summary_exact_match": matched,
                }

            # Recompute the price response directly from each saved prediction.
            ridge_choice = choices.get("charge_response_ridge")
            ridge_candidates = {str(c.get("source")): c for c in candidates
                                if isinstance(c, dict) and c.get("source")}
            prediction_winner = None
            if ridge_candidates and all("predicted_post_lp_cost" in ridge_candidates.get(k, {}) for k in ("source0", "source1")):
                prediction_winner = min(("source0", "source1"),
                                        key=lambda k: (float(ridge_candidates[k]["predicted_post_lp_cost"]), k))
            if ridge_choice != prediction_winner:
                model_choice_failures.append({"case": case, "variant": variant,
                                              "reason": "saved ridge argmin differs from prediction values",
                                              "choice": ridge_choice, "argmin": prediction_winner})

            cold_id = f"{case}/{stages['cold']}"
            cold_label = catalog.get(cold_id, {}).get("label", {})
            cold_cell = next((c for c in cells if c["row_id"] == cold_id), {})
            best_lp = summary_variant.get("paid_two_lp_best", {})
            best_reported = frac(best_lp.get("objective_exact"))
            pair_match = best is not None and best == best_reported
            if not pair_match:
                model_choice_failures.append({"case": case, "variant": variant,
                                              "reason": "best paired charge LP disagrees with catalog labels",
                                              "recomputed": exact(best), "reported": exact(best_reported)})
            variant_result = {
                "variant": variant,
                "source_lp_objective_exact": {k: exact(v) for k, v in costs.items()},
                "best_of_two_paid_lp": {
                    "objective_exact": exact(best), "objective_cost_units": numeric(best),
                    "winning_sources": winners, "summary_exact_match": pair_match,
                    "two_lp_paid_seconds": best_lp.get("two_lp_paid_seconds"),
                },
                "choices": method_results,
                "ridge_prediction_argmin": prediction_winner,
                "saved_ridge_choice": ridge_choice,
                "candidate_source_hashes_match": candidate_hash_match,
                "source_topology_replayed": {
                    src: bool(catalog.get(f"{case}/{stages[src]}", {}).get("label", {}).get("source_plan_hash") ==
                              catalog.get(f"{case}/{src}", {}).get("label", {}).get("plan_hash") and
                              next((c.get("source_topology_replay", {}).get("source_movement_set_matches")
                                    for c in cells if c.get("row_id") == f"{case}/{stages[src]}"), False))
                    for src in ("source0", "source1")
                },
                "cold": {
                    "status": cold_label.get("status"), "feasible": cold_label.get("feasible"),
                    "native_status": cold_label.get("native_status"), "optimality": cold_label.get("optimality"),
                    "physical_feasible_cost_exact": exact(cold_label.get("objective_exact")),
                    "hull_lower_exact": exact(cold_label.get("lower_exact")),
                    "native_mixture_upper_exact": exact(cold_label.get("native_mixture_upper_exact")),
                    "elapsed_seconds": cold_cell.get("child_elapsed_seconds"),
                },
            }
            variant_rows.append(variant_result)
            all_variants.append({"case": case, "seed": seed, "services": services,
                                 "variant": variant, "methods": method_results,
                                 "best_of_two": variant_result["best_of_two_paid_lp"]})

        switches: dict[str, bool] = {}
        group_means: dict[str, dict[str, Any]] = {}
        for method in METHODS:
            sequence = per_group_choices[method]
            switches[method] = len(set(sequence)) > 1
            vals = per_group_excess[method]
            mean_value = sum(vals, Fraction(0, 1)) / len(vals) if vals else None
            group_means[method] = {"mean_excess_exact": exact(mean_value),
                                   "mean_excess_cost_units": numeric(mean_value),
                                   "switches_across_tariffs": switches[method],
                                   "source_sequence": sequence}
            reported_mean = frac(summary_group.get("mean_paired_pool_excess_exact", {}).get(method))
            if mean_value != reported_mean:
                model_choice_failures.append({"case": case, "method": method,
                                              "reason": "recomputed group mean differs from summary",
                                              "recomputed": exact(mean_value), "reported": exact(reported_mean)})
            group_mean_checks += 1
            reported_switch = summary_group.get("choice_switch_across_tariffs", {}).get(method)
            if switches[method] != reported_switch:
                model_choice_failures.append({"case": case, "method": method,
                                              "reason": "recomputed source switch differs from summary",
                                              "recomputed": switches[method], "reported": reported_switch})
            switch_checks += 1
            group_choices_for_method[method][case] = sequence
            if mean_value is not None:
                group_excess_exact.setdefault(method, {})[case] = str(mean_value)

        group_results.append({
            "case": case, "base_group": frozen_group.get("base_group"), "seed": seed,
            "services": services, "source_acquisition_seconds_once": summary_group.get("source_acquisition_seconds_once"),
            "source_labels_feasible": {k: summary_group.get("source_labels", {}).get(k, {}).get("feasible")
                                        for k in ("source0", "source1")},
            "variants": variant_rows, "methods": group_means,
        })

    pooled: dict[str, dict[str, Any]] = {}
    switch_group_counts: dict[str, int] = {}
    for method in METHODS:
        vals = [frac(v["methods"][method]["paired_excess_exact"])
                for v in all_variants]
        values = [v for v in vals if v is not None]
        total = sum(values, Fraction(0, 1)) if values else None
        mean = total / len(values) if values else None
        pooled[method] = {"paired_excess_total_exact": exact(total),
                          "paired_excess_mean_exact": exact(mean),
                          "paired_excess_mean_cost_units": numeric(mean),
                          "zero_excess_variants": sum(v == 0 for v in values),
                          "variant_count": len(values),
                          "source1_selections": sum(
                              item["methods"][method]["source"] == "source1" for item in all_variants)}
        switch_group_counts[method] = sum(g["methods"][method]["switches_across_tariffs"] for g in group_results)

    proposal_variant_count = sum(
        1 for case in design["groups"]
        for variant in variants_order
        if isinstance(proposals.get(case, {}).get(variant), dict)
        and proposals[case][variant].get("choices", {}).get("charge_response_ridge") in ("source0", "source1")
    )
    candidate_count = sum(
        1 for case in design["groups"] for variant in variants_order
        for cand in (proposals.get(case, {}).get(variant, {}).get("candidates", [])
                     if isinstance(proposals.get(case, {}).get(variant), dict) else [])
        if isinstance(cand, dict) and cand.get("source") in ("source0", "source1")
    )
    source_topology_failures = [r for r in topology_checks
                                if not r.get("source_plan_hash_matches") or not r.get("source_movement_set_matches")]
    baseline_mismatches.extend(inference_errors + baseline_errors + proposals_errors)

    result = {
        "schema": "egg-tariff-response-results-v1",
        "attempt": str(attempt),
        "source_commit": frozen.get("source_commit"),
        "input_scope": "Frozen summary, design, catalog labels, choice/proposal files, and compact child receipts only; exact objective comparisons recomputed with Fraction; no event traces or optimizer reruns.",
        "campaign": {
            "declared_cells": summary.get("declared_cells"), "accounted_cells": summary.get("accounted_cells"),
            "catalog_cells": len(catalog_rows), "frozen_order_cells": len(expected_order),
            "groups": len(design.get("groups", {})), "variants_per_group": len(variants_order),
            "target_variant_count": proposal_variant_count, "ridge_candidate_count": candidate_count,
            "test_groups_unobserved": summary.get("test_groups_unobserved"),
            "reserved_unmaterialized": design.get("reserved_unmaterialized"),
            "train_majority": design.get("train_majority"),
            "variant_order": variants_order,
        },
        "pretarget_receipts": {
            "baseline_choices_before_all_targets": baseline_receipt.get("before_all_target_cells"),
            "baseline_choices_elapsed_seconds": baseline_receipt.get("elapsed_seconds"),
            "inference_status": inference.get("status"),
            "inference_returncode": inference.get("returncode"),
            "inference_before_all_target_cells": inference.get("before_all_target_cells"),
            "inference_elapsed_seconds": inference.get("elapsed_seconds"),
            "inference_failure": inference.get("failure"),
            "all_twelve_choices_present": proposal_variant_count == 12,
            "two_source_candidate_hashes_present_per_choice": candidate_count == 24,
        },
        "cell_status": {
            "ordered_cells": len(cells), "returned_and_child_rc_zero": returned_count,
            "feasible_cells": feasible_count, "objective_exact_labels": exact_cost_count,
            "hard_timeouts": timeout_count, "status_counts": dict(cell_statuses),
            "native_status_counts": dict(native_statuses), "role_counts": dict(role_counts),
            "cell_type_counts": dict(cell_type_counts),
            "failures_or_missing_artifacts": failures,
        },
        "verification": {
            "catalog_matches_declared_order": len(expected_order) == len(catalog_rows) and not catalog_missing,
            "catalog_missing_rows": catalog_missing,
            "recomputed_method_variant_comparisons": comparisons_checked,
            "recomputed_group_mean_checks": group_mean_checks,
            "recomputed_switch_checks": switch_checks,
            "method_or_summary_mismatches": model_choice_failures,
            "baseline_choice_mismatches": baseline_mismatches,
            "charge_cells_checked_for_source_topology": len(topology_checks),
            "source_topology_failures": source_topology_failures,
            "charge_cells_preserve_source_movement_sets": len(topology_checks) == 24 and not source_topology_failures,
        },
        "pooled_paired_excess_by_method": pooled,
        "groups": group_results,
        "cells": cells,
        "interpretation": {
            "paired_excess_domain": "Cost difference against the lower exact curved-cost label among the two saved source-specific fixed-route charging LPs for the same target tariff; this is a two-source pool benchmark, not a global fleet optimum.",
            "cold_bounds": "Cold feasible plan objective is a physical upper bound; hull lower is a lower bound. Native mixture upper is not necessarily a physical-plan upper.",
            "units": "Cost units; no monetary calibration assumed.",
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.attempt.resolve())
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(f"wrote {len(result['cells'])} cells and {len(result['groups'])} groups to {output}")


if __name__ == "__main__":
    main()
