#!/usr/bin/env python3
"""Summarize saved cost-aware repair receipts without invoking solvers."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = ROOT / "result/learning_repair/20260930-cost-aware-attempt1"
OUTPUT = ROOT / "research-20260930/learning-campaign/COST_AWARE_REPAIR_CELLS.csv"
CELLS = (
    (1, "learning_s2016_n20", 20, "cost_only"),
    (2, "learning_s2016_n20", 20, "cost_learned"),
    (3, "learning_s2017_n28", 28, "cost_learned"),
    (4, "learning_s2017_n28", 28, "cost_only"),
)

FIELDS = (
    "cell_order", "case", "services", "mode",
    "child_outcome", "child_return_code", "child_elapsed_seconds", "child_hard_timeout",
    "result_outcome", "result_elapsed_seconds",
    "repair_status", "repair_failure_stage", "cover_solver_status", "cover_mip_gap",
    "cover_minimum_bus_count_reported", "minimum_bus_count_scope",
    "relaxation_minimum_bus_count_reported", "proposed_structural_buses",
    "proposed_pullout_count", "energy_relaxation", "charging_caps",
    "candidate_kind", "saved_independent_replay_ok", "replayed_candidate_buses",
    "direct_repaired_cost_exact", "fallback_cost_exact",
    "inference_attempted", "inference_performed", "inference_seconds", "cover_seconds",
    "charge_replay_seconds", "repair_total_seconds", "independent_replay_seconds",
    "fallback_selection_replay_seconds", "pool_preparation_seconds", "hull_seconds",
    "worker_exception_type", "worker_exception_message",
    "hull_status", "hull_lower_bound", "hull_mixture_upper_bound",
    "hull_skipped_reason",
    "hull_global_certificate_replayed", "hull_mixture_replayed",
    "hull_pricing_requests", "hull_seed_requests", "hull_master_calls", "hull_columns",
    "artifact_errors",
)


def _read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
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


def _get(obj: Any, *keys: str) -> Any:
    value = obj
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _first(obj: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return None


def _bool(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return ""


def _bus_count(vehicles: Any) -> int | None:
    if isinstance(vehicles, list):
        return len(vehicles)
    if type(vehicles) is int and vehicles >= 0:
        return vehicles
    return None


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def summarize_cell(attempt: Path, order: int, case: str, services: int,
                   mode: str) -> dict[str, Any]:
    folder = attempt / case / "state0" / mode
    errors: list[str] = []
    receipt = _read_json(folder / "receipt.json", errors)
    repair_file = _read_json(folder / "repair.json", errors)
    independent = _read_json(folder / "independent_replay.json", errors)
    fallback = _read_json(folder / "fallback.json", errors)
    failure_receipt = _read_json(folder / "failure.json", errors)
    exception = _read_json(folder / "exception.json", errors)
    pool = _read_json(folder / "pool_preparation.json", errors)
    hull_skip = _read_json(folder / "hull_skipped.json", errors)
    result = _read_json(folder / "result.json", errors)

    proposed = repair_file.get("result", {}) if repair_file else {}
    if not isinstance(proposed, dict):
        proposed = {}
        errors.append("repair.json:missing_result_object")
    cover = proposed.get("cover") if isinstance(proposed.get("cover"), dict) else {}
    timing = proposed.get("timing_seconds") if isinstance(proposed.get("timing_seconds"), dict) else {}
    repair_status = _first(proposed, "repair_status")
    failure = proposed.get("failure") if isinstance(proposed.get("failure"), dict) else {}
    fallback_failure = _get(failure_receipt or {}, "failure")
    if not isinstance(fallback_failure, dict):
        fallback_failure = {}
    failure_stage = _first(failure, "stage")
    if failure_stage is None:
        failure_stage = _first(fallback_failure, "stage")
    independent_replay = independent.get("replay") if independent else None
    if not isinstance(independent_replay, dict):
        independent_replay = {}
    saved_replay_ok = independent_replay.get("replay_ok") is True

    candidate_kind = _first(result or {}, "candidate_kind")
    if candidate_kind is None and independent:
        candidate_kind = independent.get("candidate_kind")
    if candidate_kind is None and fallback:
        candidate_kind = fallback.get("candidate_kind")
    if candidate_kind is None and repair_status == "replayed":
        candidate_kind = "repaired"

    replayed_candidate_buses = None
    if saved_replay_ok:
        trajectories = independent_replay.get("soc_trajectories")
        if isinstance(trajectories, list):
            replayed_candidate_buses = len(trajectories)

    direct_repaired_cost = None
    if (saved_replay_ok and repair_status == "replayed"
            and candidate_kind == "repaired"):
        direct_repaired_cost = _first(independent or {}, "objective_exact")
        if direct_repaired_cost is None:
            direct_repaired_cost = _first(proposed, "true_cost_exact")

    fallback_cost = None
    if saved_replay_ok and candidate_kind == "source_fallback":
        fallback_provenance = fallback.get("provenance", {}) if fallback else {}
        if not isinstance(fallback_provenance, dict):
            fallback_provenance = {}
        fallback_cost = _first(independent or {}, "objective_exact")
        if fallback_cost is None:
            fallback_cost = _first(fallback_provenance, "objective_exact")

    result_assessment = result.get("hull_assessment", {}) if result else {}
    if not isinstance(result_assessment, dict):
        result_assessment = {}
    bounds = result_assessment.get("bounds")
    lower = bounds[0] if isinstance(bounds, list) and len(bounds) == 2 else None
    upper = bounds[1] if isinstance(bounds, list) and len(bounds) == 2 else None
    counts = result_assessment.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    energy_relaxation = _first(proposed, "energy_relaxation", "soc_relaxation")
    if energy_relaxation is None:
        energy_relaxation = _first(cover, "energy_relaxation", "soc_relaxation")
    if energy_relaxation is None:
        energy_relaxation = _first(result or {}, "energy_relaxation", "soc_relaxation")
    charging_caps = _first(proposed, "charging_caps")
    if charging_caps is None:
        charging_caps = _first(cover, "charging_caps")
    if charging_caps is None:
        charging_caps = _first(result or {}, "charging_caps")
    hull_skipped_reason = _first(result or {}, "hull_skipped_reason", "hull_skip_reason")
    if hull_skipped_reason is None:
        hull_skipped_reason = _first(result_assessment,
                                     "hull_skipped_reason", "skipped_reason", "skip_reason")
    if hull_skipped_reason is None:
        hull_skipped_reason = _first(hull_skip or {}, "hull_skipped_reason", "reason")

    repair_total_seconds = _first(repair_file or {}, "repair_wall_seconds")
    if repair_total_seconds is None:
        repair_total_seconds = _get(result, "repair_wall_seconds")
    pool_preparation_seconds = _first(pool or {}, "pool_preparation_wall_seconds")
    if pool_preparation_seconds is None:
        pool_preparation_seconds = _get(result, "pool_preparation_wall_seconds")

    if not folder.exists():
        child_outcome = "unstarted"
    elif receipt is None:
        child_outcome = "interrupted_unreceipted" if (folder / "launch.json").exists() else "unstarted"
    elif receipt.get("hard_timeout") is True:
        child_outcome = "hard_timeout"
    elif receipt.get("returncode") != 0:
        child_outcome = "failed"
    else:
        child_outcome = "returned"

    row = {
        "cell_order": order,
        "case": case,
        "services": services,
        "mode": mode,
        "child_outcome": child_outcome,
        "child_return_code": _get(receipt, "returncode"),
        "child_elapsed_seconds": _get(receipt, "elapsed_seconds"),
        "child_hard_timeout": _bool(_get(receipt, "hard_timeout")),
        "result_outcome": _get(result, "outcome"),
        "result_elapsed_seconds": _get(result, "elapsed_seconds"),
        "repair_status": repair_status,
        "repair_failure_stage": failure_stage,
        "cover_solver_status": _get(cover, "status"),
        "cover_mip_gap": _get(cover, "mip_gap"),
        "cover_minimum_bus_count_reported": _bool(_get(cover, "native_minimum_bus_count_reported")),
        "minimum_bus_count_scope": _get(cover, "minimum_bus_count_scope"),
        "relaxation_minimum_bus_count_reported": _bool(
            _get(cover, "relaxation_minimum_bus_count_reported")),
        "proposed_structural_buses": _bus_count(_get(cover, "vehicles")),
        "proposed_pullout_count": _get(cover, "pullout_count"),
        "energy_relaxation": _csv_value(energy_relaxation),
        "charging_caps": _csv_value(charging_caps),
        "candidate_kind": candidate_kind,
        "saved_independent_replay_ok": _bool(saved_replay_ok if independent else None),
        "replayed_candidate_buses": replayed_candidate_buses,
        "direct_repaired_cost_exact": direct_repaired_cost,
        "fallback_cost_exact": fallback_cost,
        "inference_attempted": _bool(_get(proposed, "inference_attempted")),
        "inference_performed": _bool(_get(proposed, "inference_performed")),
        "inference_seconds": _get(timing, "topology"),
        "cover_seconds": _get(timing, "cover"),
        "charge_replay_seconds": _get(timing, "charging_and_replay"),
        "repair_total_seconds": repair_total_seconds,
        "independent_replay_seconds": _first(independent or {}, "replay_wall_seconds"),
        "fallback_selection_replay_seconds": _first(
            fallback or {}, "selection_and_replay_wall_seconds"),
        "pool_preparation_seconds": pool_preparation_seconds,
        "hull_seconds": _get(result, "hull_wall_seconds"),
        "worker_exception_type": _get(exception, "type"),
        "worker_exception_message": _get(exception, "message"),
        "hull_status": _get(result_assessment, "status"),
        "hull_lower_bound": lower,
        "hull_mixture_upper_bound": upper,
        "hull_skipped_reason": hull_skipped_reason,
        "hull_global_certificate_replayed": _bool(
            _get(result_assessment, "global_certificate_replayed")),
        "hull_mixture_replayed": _bool(_get(result_assessment, "mixture_replayed")),
        "hull_pricing_requests": _first(counts, "pricing_requests", "pricing_calls"),
        "hull_seed_requests": _get(counts, "seed_requests"),
        "hull_master_calls": _get(counts, "master_calls"),
        "hull_columns": _get(result_assessment, "columns"),
        "artifact_errors": ";".join(errors),
    }
    return row


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=ATTEMPT,
                        help="attempt directory (default: cost-aware attempt 1)")
    parser.add_argument("--output", type=Path, default=OUTPUT,
                        help="CSV destination (default: COST_AWARE_REPAIR_CELLS.csv)")
    args = parser.parse_args(argv)
    attempt = args.attempt.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [summarize_cell(attempt, *cell) for cell in CELLS]
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(output)
    print(f"wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
