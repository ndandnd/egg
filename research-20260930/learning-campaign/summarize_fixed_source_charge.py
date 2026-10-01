#!/usr/bin/env python3
"""Summarize fixed-source charging receipts without reading event dumps."""
from __future__ import annotations

import argparse
import csv
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATTEMPT = ROOT / "result/learning_repair/20260930-fixed-source-charge-attempt1"
DEFAULT_OUTPUT = ROOT / "research-20260930/learning-campaign/FIXED_SOURCE_CHARGE_CELLS.csv"

FIELDS = (
    "cell_order", "case", "seed", "services", "source", "case_identity", "market_identity",
    "source_plan_hash", "direct_plan_hash", "recharged_plan_hash", "source_plan_hash_pinned",
    "child_return_code", "child_elapsed_seconds", "child_hard_seconds", "child_hard_timeout",
    "direct_rescore_status", "lp_status", "lp_native_status", "lp_optimality_scope", "target_optimality",
    "direct_cost_exact", "direct_cost", "recharged_cost_exact", "recharged_cost",
    "recharged_minus_direct_exact", "recharged_minus_direct", "linear_lp_incumbent", "linear_lp_lower_bound",
    "lp_elapsed_seconds", "charge_phase_seconds", "independent_replay_seconds",
    "historical_source_paid_seconds", "historical_source_acquisition_seconds_once",
    "model_preparation_artifact", "model_preparation_seconds_once",
    "learned_choice_inference_seconds_once", "selection_wall_seconds", "frozen_learned_source_choice",
    "cheapest_direct_source_choice", "best_recharged_source", "best_of_four_kind", "best_of_four_source",
    "best_of_four_cost_exact", "best_of_four_cost", "is_frozen_learned_choice", "is_cheapest_direct_choice",
    "is_best_recharged_source", "historical_best_native_arm", "historical_best_native_cost_exact",
    "historical_best_native_cost", "historical_best_native_status", "historical_best_native_lower_exact",
    "historical_best_native_elapsed_seconds", "artifact_errors",
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


def fraction(value: Any) -> Fraction | None:
    if value in (None, ""):
        return None
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def exact_float(value: Any) -> float | None:
    parsed = fraction(value)
    return float(parsed) if parsed is not None else None


def exact_difference(left: Any, right: Any) -> str | None:
    """Return right - left as an exact fraction string."""
    a, b = fraction(left), fraction(right)
    return str(b - a) if a is not None and b is not None else None


def bool_text(value: bool | None) -> str:
    return "true" if value is True else "false" if value is False else ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    attempt = args.attempt.resolve()
    output = args.output.resolve()

    frozen = json.loads((attempt / "frozen.json").read_text(encoding="utf-8"))
    summary = json.loads((attempt / "summary.json").read_text(encoding="utf-8"))
    design = frozen["design"]
    groups = design.get("groups", {})
    rows: list[dict[str, Any]] = []

    for order, item in enumerate(design["cell_order"], start=1):
        seed = int(item["seed"])
        source = str(item["source"])
        case = next((key for key, meta in groups.items() if int(meta.get("seed", -1)) == seed), f"learning_s{seed}_nunknown")
        service_match = re.search(r"_n(\d+)$", case)
        services = int(service_match.group(1)) if service_match else None
        case_summary = summary.get("selections", {}).get(case, {})
        cell_dir = attempt / case / "state0" / f"{source}_charge"
        errors: list[str] = []
        result = read_json(cell_dir / "result.json", errors) or {}
        direct = read_json(cell_dir / "direct_rescore.json", errors) or {}
        fixed = read_json(cell_dir / "fixed_charge.json", errors) or {}
        receipt = read_json(cell_dir / "receipt.json", errors) or {}
        candidate = next((row for row in case_summary.get("candidates", []) if row.get("source") == source), {})
        single = case_summary.get("single_lp_methods", {})
        learned_choice = single.get("frozen_learned_source", {}).get("source")
        cheapest_choice = single.get("pre_target_cheapest_direct", {}).get("source")
        historical = case_summary.get("historical_target_controls", {})
        historical_arm, historical_row = min(
            historical.items(), key=lambda pair: fraction(pair[1].get("objective_exact")) or Fraction(10**100),
            default=(None, {}),
        )
        direct_exact = direct.get("objective_exact") or result.get("direct_objective_exact") or candidate.get("direct_objective_exact")
        recharged_exact = fixed.get("objective_exact") or result.get("post_lp_objective_exact") or candidate.get("post_lp_objective_exact")
        direct_hash = direct.get("source_plan_hash")
        recharged_hash = fixed.get("plan_hash")
        if direct.get("objective_exact") and result.get("direct_objective_exact") and direct["objective_exact"] != result["direct_objective_exact"]:
            errors.append("direct_cost_mismatch")
        if fixed.get("objective_exact") and result.get("post_lp_objective_exact") and fixed["objective_exact"] != result["post_lp_objective_exact"]:
            errors.append("recharged_cost_mismatch")
        if fixed.get("plan_hash") and result.get("post_lp_plan_hash") and fixed["plan_hash"] != result["post_lp_plan_hash"]:
            errors.append("recharged_plan_hash_mismatch")
        expected_source_hash = groups.get(case, {}).get("source_plan_hashes", {}).get(source)
        if expected_source_hash and direct_hash and expected_source_hash != direct_hash:
            errors.append("source_plan_hash_mismatch")
        if direct.get("case_identity") and direct["case_identity"] != groups.get(case, {}).get("case_identity"):
            errors.append("case_identity_mismatch")
        if direct.get("market_identity") and direct["market_identity"] != groups.get(case, {}).get("market_identity"):
            errors.append("market_identity_mismatch")
        if result.get("status") != "replayed":
            errors.append("not_replayed")

        best_recharged_source = case_summary.get("best_recharged_source")
        best_four = case_summary.get("best_of_four", {})
        lp_native = fixed.get("native_stats", {})
        change_exact = exact_difference(direct_exact, recharged_exact)
        is_frozen = source == learned_choice if learned_choice else None
        is_cheap = source == cheapest_choice if cheapest_choice else None
        is_best_recharged = source == best_recharged_source if best_recharged_source else None
        rows.append({
            "cell_order": order, "case": case, "seed": seed, "services": services, "source": source,
            "case_identity": direct.get("case_identity") or groups.get(case, {}).get("case_identity"),
            "market_identity": direct.get("market_identity") or groups.get(case, {}).get("market_identity"),
            "source_plan_hash": direct_hash or expected_source_hash, "direct_plan_hash": direct_hash,
            "recharged_plan_hash": recharged_hash,
            "source_plan_hash_pinned": bool_text(bool(expected_source_hash and expected_source_hash == direct_hash and fixed.get("source_plan_hash") == expected_source_hash)),
            "child_return_code": receipt.get("returncode"), "child_elapsed_seconds": receipt.get("elapsed_seconds"),
            "child_hard_seconds": receipt.get("hard_seconds"), "child_hard_timeout": bool_text(receipt.get("hard_timeout")),
            "direct_rescore_status": candidate.get("direct_rescore_status"), "lp_status": result.get("status") or fixed.get("status"),
            "lp_native_status": result.get("native_status") or fixed.get("native_stats", {}).get("status"),
            "lp_optimality_scope": "linear market.a fixed-route charging LP",
            "target_optimality": result.get("target_optimality", "unknown"),
            "direct_cost_exact": direct_exact, "direct_cost": exact_float(direct_exact),
            "recharged_cost_exact": recharged_exact, "recharged_cost": exact_float(recharged_exact),
            "recharged_minus_direct_exact": change_exact, "recharged_minus_direct": exact_float(change_exact),
            "linear_lp_incumbent": lp_native.get("incumbent"), "linear_lp_lower_bound": lp_native.get("lower_bound"),
            "lp_elapsed_seconds": receipt.get("elapsed_seconds"),
            "charge_phase_seconds": result.get("charge_wall_seconds") or fixed.get("charge_wall_seconds"),
            "independent_replay_seconds": result.get("independent_replay_wall_seconds") or fixed.get("independent_replay_wall_seconds"),
            "historical_source_paid_seconds": candidate.get("source_paid_seconds"),
            "historical_source_acquisition_seconds_once": case_summary.get("historical_source_acquisition_seconds") if source == "source0" else None,
            "model_preparation_artifact": ("stage2" if seed == 2016 else "transfer") if source == "source0" and seed in (2016, 2018) else None,
            "model_preparation_seconds_once": case_summary.get("archived_model_preparation_elapsed_seconds") if source == "source0" and seed in (2016, 2018) else None,
            "learned_choice_inference_seconds_once": single.get("frozen_learned_source", {}).get("inference_seconds") if source == "source0" else None,
            "selection_wall_seconds": case_summary.get("selection_wall_seconds") if source == "source0" else None,
            "frozen_learned_source_choice": learned_choice,
            "cheapest_direct_source_choice": cheapest_choice,
            "best_recharged_source": best_recharged_source,
            "best_of_four_kind": best_four.get("kind"), "best_of_four_source": best_four.get("source"),
            "best_of_four_cost_exact": best_four.get("objective_exact"), "best_of_four_cost": exact_float(best_four.get("objective_exact")),
            "is_frozen_learned_choice": bool_text(is_frozen),
            "is_cheapest_direct_choice": bool_text(is_cheap), "is_best_recharged_source": bool_text(is_best_recharged),
            "historical_best_native_arm": historical_arm,
            "historical_best_native_cost_exact": historical_row.get("objective_exact"),
            "historical_best_native_cost": exact_float(historical_row.get("objective_exact")),
            "historical_best_native_status": historical_row.get("native_status"),
            "historical_best_native_lower_exact": historical_row.get("lower_exact"),
            "historical_best_native_elapsed_seconds": historical_row.get("elapsed_seconds"),
            "artifact_errors": ";".join(errors),
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(output)
    print(f"wrote {len(rows)} cells to {output}; rows with receipt issues: {sum(bool(r['artifact_errors']) for r in rows)}")


if __name__ == "__main__":
    main()
