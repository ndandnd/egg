#!/usr/bin/env python3
"""Summarize frozen charge-response campaign receipts without solver traces."""
from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATTEMPT = ROOT / "result/learning_campaign/20260930-charge-response-attempt1"
DEFAULT_OUTPUT = ROOT / "research-20260930/learning-campaign/CHARGE_RESPONSE_CELLS.csv"

FIELDS = (
    "cell_order", "row_id", "case", "seed", "services", "split", "market_role", "arm",
    "cell_status", "feasible", "native_status", "optimality", "objective_exact", "objective_cost",
    "lower_exact", "lower_cost", "upper_exact", "upper_cost", "native_mixture_upper_exact",
    "native_mixture_upper_cost", "label_elapsed_seconds", "charge_wall_seconds",
    "child_return_code", "child_elapsed_seconds", "child_hard_seconds", "child_hard_timeout",
    "child_on_time", "failure_type", "failure_message", "artifact_errors",
    "source_acquisition_seconds_once", "baseline_choices_elapsed_seconds_once",
    "training_fit_seconds_once", "four_group_inference_seconds_once",
    "inference_process_elapsed_seconds_once", "inference_status_once", "inference_return_code_once",
    "complete_six_training_pairs_once", "training_rows_replayed_once", "training_rows_expected_once",
    "before_all_dev_target_cells_once",
    "best_two_lp_source", "best_two_lp_objective_exact", "best_two_lp_objective_cost",
    "ridge_choice", "ridge_objective_exact", "ridge_objective_cost", "ridge_excess_exact", "ridge_excess_cost",
    "ridge_lp_seconds", "ridge_acquisition_plus_lp_seconds",
    "cheapest_direct_choice", "cheapest_direct_objective_exact", "cheapest_direct_objective_cost",
    "cheapest_direct_excess_exact", "cheapest_direct_excess_cost", "cheapest_direct_lp_seconds",
    "cheapest_direct_acquisition_plus_lp_seconds",
    "nearest_price_choice", "nearest_price_objective_exact", "nearest_price_objective_cost",
    "nearest_price_excess_exact", "nearest_price_excess_cost", "nearest_price_lp_seconds",
    "nearest_price_acquisition_plus_lp_seconds",
    "frozen_edge_prior_choice", "frozen_edge_prior_objective_exact", "frozen_edge_prior_objective_cost",
    "frozen_edge_prior_excess_exact", "frozen_edge_prior_excess_cost", "frozen_edge_prior_lp_seconds",
    "frozen_edge_prior_acquisition_plus_lp_seconds",
    "posthoc_always_source1_objective_exact", "posthoc_always_source1_objective_cost",
    "posthoc_always_source1_excess_exact", "posthoc_always_source1_excess_cost",
    "posthoc_always_source1_matches_ridge",
)


def read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append(f"missing:{path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}:{type(exc).__name__}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path.name}:not_object")
        return None
    return value


def exact_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(Fraction(str(value)))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def exact_text(value: Any) -> str:
    return "" if value is None else str(value)


def bool_text(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def get_failure(value: Any) -> tuple[str, str]:
    if isinstance(value, dict):
        return (str(value.get("type") or value.get("stage") or ""),
                str(value.get("message") or value.get("error") or ""))
    if value:
        return (type(value).__name__, str(value))
    return "", ""


def seed_services(case: str) -> tuple[int, int]:
    try:
        seed_text, services_text = case.removeprefix("learning_s").split("_n", 1)
        return int(seed_text), int(services_text)
    except (ValueError, AttributeError):
        return 0, 0


def method_fields(row: dict[str, Any], prefix: str, method: dict[str, Any] | None) -> None:
    method = method or {}
    row[f"{prefix}_choice"] = method.get("source", "")
    row[f"{prefix}_objective_exact"] = method.get("post_lp_objective_exact", "")
    row[f"{prefix}_objective_cost"] = exact_float(method.get("post_lp_objective_exact"))
    row[f"{prefix}_excess_exact"] = method.get("excess_over_best_two_lp_exact", "")
    row[f"{prefix}_excess_cost"] = exact_float(method.get("excess_over_best_two_lp_exact"))
    row[f"{prefix}_lp_seconds"] = method.get("lp_paid_seconds", "")
    row[f"{prefix}_acquisition_plus_lp_seconds"] = method.get("source_acquisition_plus_lp_paid_seconds", "")


def build_rows(attempt: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary = json.loads((attempt / "summary.json").read_text(encoding="utf-8"))
    catalog_rows = [json.loads(line) for line in (attempt / "catalog.jsonl").read_text(encoding="utf-8").splitlines() if line]
    catalog = {str(item.get("row_id")): item for item in catalog_rows}
    if len(catalog_rows) != len(catalog):
        raise ValueError("catalog contains duplicate row_id values")

    train_coverage_errors: list[str] = []
    coverage = read_json(attempt / "training_coverage.json", train_coverage_errors) or {}
    inference = read_json(attempt / "inference_receipt.json", train_coverage_errors) or {}
    baseline = read_json(attempt / "baseline_choices_receipt.json", train_coverage_errors) or {}
    timing = summary.get("training_inference_timing", {})

    ordered_ids = [str(item.get("row_id")) for item in catalog_rows]
    expected = int(summary.get("declared_cells", len(ordered_ids)))
    if int(summary.get("accounted_cells", -1)) != expected or len(ordered_ids) != expected:
        raise ValueError(f"incomplete campaign catalog/summary: declared={expected}, catalog={len(ordered_ids)}, accounted={summary.get('accounted_cells')}")

    rows: list[dict[str, Any]] = []
    dev_groups = sorted((name for name, value in summary.get("cases", {}).items() if value.get("split") == "dev"), key=lambda s: int(s.split("s", 2)[1].split("_", 1)[0]))
    first_dev = dev_groups[0] if dev_groups else ""
    for order, row_id in enumerate(ordered_ids, start=1):
        item = catalog[row_id]
        # base_group is a family identifier in some catalogs; row_id carries
        # the exact frozen case identifier (including its service count).
        case = row_id.split("/", 1)[0]
        # Source catalog rows encode their market as market_name and use the
        # generic arm label "source"; the row id contains the precise arm.
        arm = row_id.split("/", 1)[-1]
        seed, services = seed_services(case)
        label = item.get("label", {}) if isinstance(item.get("label"), dict) else {}
        errors: list[str] = []
        receipt = read_json(attempt / case / "state0" / arm / "receipt.json", errors)
        fail_type, fail_msg = get_failure(label.get("failure"))
        if not fail_type and receipt:
            fail_type, fail_msg = get_failure(receipt.get("error"))

        row: dict[str, Any] = {
            "cell_order": order, "row_id": row_id, "case": case, "seed": seed, "services": services,
            "split": item.get("split", ""), "market_role": item.get("market_role", ""), "arm": arm,
            "cell_status": label.get("status", ""), "feasible": bool_text(label.get("feasible")),
            "native_status": label.get("native_status", ""), "optimality": label.get("optimality", ""),
            "objective_exact": label.get("objective_exact", ""), "objective_cost": exact_float(label.get("objective_exact")),
            "lower_exact": label.get("lower_exact", ""), "lower_cost": exact_float(label.get("lower_exact")),
            "upper_exact": label.get("upper_exact", ""), "upper_cost": exact_float(label.get("upper_exact")),
            "native_mixture_upper_exact": label.get("native_mixture_upper_exact", ""),
            "native_mixture_upper_cost": exact_float(label.get("native_mixture_upper_exact")),
            "label_elapsed_seconds": label.get("elapsed_seconds", ""),
            "charge_wall_seconds": label.get("charge_wall_seconds", ""),
            "child_return_code": receipt.get("returncode", "") if receipt else "",
            "child_elapsed_seconds": receipt.get("elapsed_seconds", "") if receipt else "",
            "child_hard_seconds": receipt.get("hard_seconds", "") if receipt else "",
            "child_hard_timeout": bool_text(receipt.get("hard_timeout")) if receipt else "",
            "child_on_time": bool_text(receipt.get("on_time")) if receipt else "",
            "failure_type": fail_type, "failure_message": fail_msg,
            "artifact_errors": ";".join(errors),
        }

        case_summary = summary.get("cases", {}).get(case, {})
        # Charge source acquisition once per case: on its source0 row only.
        if item.get("market_role") == "source" and arm == "source0":
            row["source_acquisition_seconds_once"] = case_summary.get("source_acquisition_seconds", "")
        else:
            row["source_acquisition_seconds_once"] = ""

        # Put the one-time training/inference receipts in the first dev case's
        # cold row to keep the cell ledger at exactly 44 rows.
        if case == first_dev and arm == "cold":
            row.update({
                "baseline_choices_elapsed_seconds_once": baseline.get("elapsed_seconds", ""),
                "training_fit_seconds_once": timing.get("training_fit_seconds", ""),
                "four_group_inference_seconds_once": timing.get("four_group_inference_seconds", ""),
                "inference_process_elapsed_seconds_once": inference.get("elapsed_seconds", ""),
                "inference_status_once": inference.get("status", ""),
                "inference_return_code_once": inference.get("returncode", ""),
                "complete_six_training_pairs_once": bool_text(coverage.get("complete_six_pairs")),
                "training_rows_replayed_once": len(coverage.get("replayed_rows", [])) if isinstance(coverage.get("replayed_rows"), list) else "",
                "training_rows_expected_once": (len(coverage.get("expected_rows", []))
                                                  if isinstance(coverage.get("expected_rows"), list)
                                                  else coverage.get("expected_rows", "")),
                "before_all_dev_target_cells_once": bool_text(inference.get("before_all_dev_target_cells")),
            })

        # Case-level development comparisons are stored on its cold row only;
        # cell-level native results remain one row per catalog cell.
        if item.get("split") == "dev" and arm == "cold":
            best = case_summary.get("paid_two_lp_best", {})
            row["best_two_lp_source"] = best.get("source", "")
            row["best_two_lp_objective_exact"] = best.get("objective_exact", "")
            row["best_two_lp_objective_cost"] = exact_float(best.get("objective_exact"))
            methods = case_summary.get("single_lp_methods", {})
            method_fields(row, "ridge", methods.get("charge_response_ridge"))
            method_fields(row, "cheapest_direct", methods.get("cheapest_direct"))
            method_fields(row, "nearest_price", methods.get("nearest_price"))
            method_fields(row, "frozen_edge_prior", methods.get("frozen_edge_prior"))
            # This is an explicitly post hoc diagnostic, not a prospective arm.
            source1 = case_summary.get("charged_labels", {}).get("source1", {})
            source1_exact = source1.get("objective_exact")
            best_exact = best.get("objective_exact")
            row["posthoc_always_source1_objective_exact"] = source1_exact or ""
            row["posthoc_always_source1_objective_cost"] = exact_float(source1_exact)
            if source1_exact and best_exact:
                delta = Fraction(str(source1_exact)) - Fraction(str(best_exact))
                row["posthoc_always_source1_excess_exact"] = str(delta)
                row["posthoc_always_source1_excess_cost"] = float(delta)
            ridge = methods.get("charge_response_ridge", {})
            row["posthoc_always_source1_matches_ridge"] = bool_text(
                ridge.get("source") == "source1" and ridge.get("post_lp_objective_exact") == source1_exact
            )
        rows.append(row)

    meta = {
        "summary": summary, "coverage": coverage, "inference": inference,
        "baseline": baseline, "catalog_count": len(catalog_rows),
    }
    return rows, meta


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    rows, _ = build_rows(args.attempt.resolve())
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
