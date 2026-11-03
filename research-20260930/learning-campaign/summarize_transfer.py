#!/usr/bin/env python3
"""Summarize frozen transfer receipts without reading solver event/raw dumps."""
from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ATTEMPT = ROOT / "result/learning_campaign/20260930-transfer-attempt1"
DEFAULT_OUTPUT = ROOT / "research-20260930/learning-campaign/TRANSFER_CELLS.csv"

FIELDS = (
    "cell_order", "case", "seed", "services", "stage", "cell_type",
    "child_return_code", "child_elapsed_seconds", "child_hard_seconds", "child_hard_timeout",
    "catalog_status", "feasible", "optimality", "candidate_kind", "repair_status",
    "failure_stage", "native_status", "cover_status", "cover_gap", "cover_buses",
    "candidate_buses", "direct_proposal_costs_exact", "direct_proposal_cost_min_exact",
    "direct_proposal_cost_min", "direct_candidate_cost_exact", "fallback_cost_exact",
    "final_incumbent_cost_exact", "final_incumbent_cost", "improvement_vs_direct_exact",
    "hull_status", "hull_lower_exact", "hull_lower", "hull_mixture_upper_exact",
    "hull_mixture_upper", "hull_global_replayed", "hull_mixture_replayed",
    "hull_pricing_requests", "hull_master_calls", "hull_columns",
    "source0_acquisition_seconds", "source1_acquisition_seconds",
    "source_acquisition_paid_seconds_repeated", "model_inference_shared_seconds_once",
    "proposal_online_seconds", "source_validation_scoring_seconds",
    "target_topology_prediction_seconds", "selection_lookup_seconds",
    "direct_rescoring_seconds", "result_worker_elapsed_seconds", "repair_topology_seconds",
    "cover_seconds", "charge_replay_seconds", "repair_total_seconds",
    "independent_replay_seconds", "pool_preparation_seconds", "hull_seconds",
    "artifact_errors",
)


def read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
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


def exact_value(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(Fraction(str(value)))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def exact_difference(left: Any, right: Any) -> str | None:
    if left in (None, "") or right in (None, ""):
        return None
    try:
        return str(Fraction(str(right)) - Fraction(str(left)))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def bool_text(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def bus_count(plan: Any) -> int | None:
    vehicles = plan.get("vehicles") if isinstance(plan, dict) else None
    return len(vehicles) if isinstance(vehicles, list) else None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    attempt = args.attempt.resolve()
    output = args.output.resolve()
    frozen = json.loads((attempt / "frozen.json").read_text(encoding="utf-8"))
    design = frozen["design"]
    cell_order = design["cell_order"]
    profile = design.get("profile", {})

    catalog_path = attempt / "catalog.jsonl"
    catalog_rows = [json.loads(line) for line in catalog_path.read_text(encoding="utf-8").splitlines()]
    catalog = {row["row_id"]: row for row in catalog_rows}
    inference = read_json(attempt / "inference_receipt.json", []) or {}
    inference_seconds = inference.get("elapsed_seconds")
    proposals_path = attempt / "learned/proposals.jsonl"
    proposals = [json.loads(line) for line in proposals_path.read_text(encoding="utf-8").splitlines()]
    proposal_by_case = {row.get("target_row_id", "").split("/", 1)[0]: row for row in proposals}

    source_times: dict[str, dict[str, float | None]] = {}
    for item in cell_order:
        seed, stage = item["seed"], item["stage"]
        if stage not in ("source0", "source1"):
            continue
        case = item.get("case") or f"learning_s{seed}_n{profile.get(str(seed), {}).get('services', 'unknown')}"
        receipt = read_json(attempt / case / "state0" / stage / "receipt.json", []) or {}
        source_times.setdefault(case, {})[stage] = receipt.get("elapsed_seconds")

    rows: list[dict[str, Any]] = []
    for order, item in enumerate(cell_order, start=1):
        seed, stage = int(item["seed"]), str(item["stage"])
        services = int(item.get("services", profile.get(str(seed), {}).get("services", 0)))
        case = item.get("case") or f"learning_s{seed}_n{services}"
        cell_dir = attempt / case / "state0" / stage
        errors: list[str] = []
        receipt = read_json(cell_dir / "receipt.json", errors)
        result = read_json(cell_dir / "result.json", errors)
        result = result or {}
        label_row = catalog.get(f"{case}/{stage}", {})
        label = label_row.get("label", {}) if isinstance(label_row, dict) else {}
        selection = read_json(cell_dir / "selection.json", errors) or {}
        direct = read_json(cell_dir / "direct_proposals.json", errors) or {}
        repair_doc = read_json(cell_dir / "repair.json", errors) or {}
        repair_result = repair_doc.get("result", {})
        if not isinstance(repair_result, dict):
            repair_result = {}
            if stage.startswith("shared_cost_"):
                errors.append("repair.json:missing_result_object")
        independent = read_json(cell_dir / "independent_replay.json", errors) or {}
        pool = read_json(cell_dir / "pool_preparation.json", errors) or {}
        fallback = read_json(cell_dir / "fallback.json", errors) or {}

        direct_items = direct.get("proposals", [])
        if not isinstance(direct_items, list):
            direct_items = []
            errors.append("direct_proposals.json:proposals_not_list")
        direct_costs = [row.get("nonlinear_cost_exact") for row in direct_items
                        if isinstance(row, dict) and row.get("nonlinear_cost_exact")]
        direct_min = min((Fraction(value) for value in direct_costs), default=None)
        direct_min_text = str(direct_min) if direct_min is not None else None

        candidate_kind = label.get("candidate_kind")
        if stage.startswith("shared_cost_"):
            candidate_kind = result.get("candidate_kind") or candidate_kind
        repair_status = result.get("repair_status") or repair_result.get("repair_status")
        failure = repair_result.get("failure") if isinstance(repair_result.get("failure"), dict) else {}
        failure_stage = failure.get("stage")
        if not failure_stage and isinstance(fallback.get("failure"), dict):
            failure_stage = fallback["failure"].get("stage")

        final_exact = label.get("objective_exact")
        if stage.startswith("shared_cost_"):
            final_exact = result.get("candidate_objective_exact") or final_exact
        direct_candidate_exact = None
        fallback_exact = None
        if stage.startswith("shared_cost_"):
            if candidate_kind == "repaired" and repair_status == "replayed":
                direct_candidate_exact = result.get("candidate_objective_exact") or repair_result.get("true_cost_exact")
            elif candidate_kind == "source_fallback":
                fallback_exact = independent.get("objective_exact")

        assessment = result.get("assessment", {})
        if not isinstance(assessment, dict):
            assessment = {}
        hull_assessment = label.get("hull_assessment", {})
        if not isinstance(hull_assessment, dict):
            hull_assessment = {}
        if stage.startswith("shared_cost_"):
            hull_assessment = result.get("hull_assessment", {})
            if not isinstance(hull_assessment, dict):
                hull_assessment = {}
        bounds = assessment.get("bounds") if assessment else hull_assessment.get("bounds")
        lower_exact = bounds[0] if isinstance(bounds, list) and len(bounds) == 2 else label.get("lower_exact")
        upper_exact = (bounds[1] if isinstance(bounds, list) and len(bounds) == 2
                       else label.get("native_mixture_upper_exact"))
        counts = assessment.get("counts", {}) if assessment else hull_assessment.get("counts", {})
        if not isinstance(counts, dict):
            counts = {}
        hull_status = assessment.get("status") or hull_assessment.get("status")
        hull_global_replayed = assessment.get("global_certificate_replayed")
        hull_mixture_replayed = assessment.get("mixture_replayed")
        if stage.startswith("shared_cost_"):
            hull_global_replayed = hull_assessment.get("global_certificate_replayed")
            hull_mixture_replayed = hull_assessment.get("mixture_replayed")

        cover = repair_result.get("cover", {}) if isinstance(repair_result.get("cover"), dict) else {}
        timing = repair_result.get("timing_seconds", {}) if isinstance(repair_result.get("timing_seconds"), dict) else {}
        inference_detail = selection.get("learned_proposal", {}) or {}
        online_timing = inference_detail.get("online_timing_seconds", {}) if isinstance(inference_detail, dict) else {}
        per_case_proposal = proposal_by_case.get(case, {})
        per_case_online = per_case_proposal.get("online_timing_seconds", {})
        replay_info = independent.get("replay", {}) if isinstance(independent.get("replay"), dict) else {}
        plan = label.get("plan")
        if stage.startswith("shared_cost_"):
            plan = repair_result.get("plan")
        candidate_buses = len(replay_info.get("soc_trajectories", [])) if replay_info else bus_count(plan)
        if not candidate_buses:
            candidate_buses = bus_count(plan)

        result_elapsed = result.get("elapsed_seconds")
        if stage.startswith("shared_cost_"):
            result_elapsed = result.get("elapsed_seconds")
        source_case = source_times.get(case, {})
        # Source acquisition is represented once in source rows; the repeated
        # selection field is kept separately to make its duplication explicit.
        is_first_learned = stage == "learned" and seed == 2018
        row = {
            "cell_order": order, "case": case, "seed": seed, "services": services,
            "stage": stage,
            "cell_type": "source" if stage in ("source0", "source1") else
                         "repair" if stage.startswith("shared_cost_") else "target",
            "child_return_code": (receipt or {}).get("returncode"),
            "child_elapsed_seconds": (receipt or {}).get("elapsed_seconds"),
            "child_hard_seconds": (receipt or {}).get("hard_seconds"),
            "child_hard_timeout": bool_text((receipt or {}).get("hard_timeout")),
            "catalog_status": label.get("status"),
            "feasible": bool_text(label.get("feasible")),
            "optimality": label.get("optimality", "unknown"),
            "candidate_kind": candidate_kind,
            "repair_status": repair_status,
            "failure_stage": failure_stage,
            "native_status": label.get("native_status"),
            "cover_status": cover.get("status"),
            "cover_gap": cover.get("mip_gap"),
            "cover_buses": len(cover.get("vehicles", [])) if isinstance(cover.get("vehicles"), list) else None,
            "candidate_buses": candidate_buses,
            "direct_proposal_costs_exact": compact_json(direct_costs) if direct_costs else None,
            "direct_proposal_cost_min_exact": direct_min_text,
            "direct_proposal_cost_min": float(direct_min) if direct_min is not None else None,
            "direct_candidate_cost_exact": direct_candidate_exact,
            "fallback_cost_exact": fallback_exact,
            "final_incumbent_cost_exact": final_exact,
            "final_incumbent_cost": exact_value(final_exact),
            # Positive means the direct selected/repair cost is above the
            # post-hull incumbent. Keep the exact signed delta auditable.
            "improvement_vs_direct_exact": exact_difference(final_exact, direct_min_text or direct_candidate_exact),
            "hull_status": hull_status,
            "hull_lower_exact": lower_exact,
            "hull_lower": exact_value(lower_exact),
            "hull_mixture_upper_exact": upper_exact,
            "hull_mixture_upper": exact_value(upper_exact),
            "hull_global_replayed": bool_text(hull_global_replayed),
            "hull_mixture_replayed": bool_text(hull_mixture_replayed),
            "hull_pricing_requests": counts.get("pricing_requests"),
            "hull_master_calls": counts.get("master_calls"),
            "hull_columns": assessment.get("columns") or hull_assessment.get("columns"),
            "source0_acquisition_seconds": source_case.get("source0") if stage == "source0" else None,
            "source1_acquisition_seconds": source_case.get("source1") if stage == "source1" else None,
            "source_acquisition_paid_seconds_repeated": selection.get("source_paid_seconds"),
            "model_inference_shared_seconds_once": inference_seconds if is_first_learned else None,
            "proposal_online_seconds": per_case_online.get("total") or online_timing.get("total"),
            "source_validation_scoring_seconds": per_case_online.get("source_validation_and_scoring") or online_timing.get("source_validation_and_scoring"),
            "target_topology_prediction_seconds": per_case_online.get("topology_prediction") or online_timing.get("topology_prediction"),
            "selection_lookup_seconds": selection.get("lookup_elapsed_seconds"),
            "direct_rescoring_seconds": selection.get("direct_replay_rescoring_wall_seconds"),
            "result_worker_elapsed_seconds": result_elapsed,
            "repair_topology_seconds": timing.get("topology"),
            "cover_seconds": timing.get("cover"),
            "charge_replay_seconds": timing.get("charging_and_replay"),
            "repair_total_seconds": result.get("repair_wall_seconds") or repair_doc.get("repair_wall_seconds"),
            "independent_replay_seconds": independent.get("replay_wall_seconds"),
            "pool_preparation_seconds": pool.get("pool_preparation_wall_seconds"),
            "hull_seconds": result.get("hull_wall_seconds"),
            "artifact_errors": ";".join(errors),
        }
        rows.append(row)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(output)
    print(f"wrote {len(rows)} cells to {output}")


if __name__ == "__main__":
    main()
