from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path("/Users/nadan/Documents/ChatGPT/egg/journal-research-work")
EVIDENCE = Path("/Users/nadan/Documents/ChatGPT/egg/research-20260928/cluster/solver-baseline-comparison-attempt1/sealed/20260928-attempt1")
OUT = Path("/Users/nadan/Documents/ChatGPT/egg/journal-research-work/research-20260928/agent-notes/solver-baseline-comparison-results/replay.json")
sys.path.insert(0, str(REPO / "src"))

from egglab import native_hull as nh  # noqa: E402
from egglab import native_pathflow_hull as compact  # noqa: E402
from experiments import computational_benchmark as base  # noqa: E402
from experiments import solver_baseline_comparison as comparison  # noqa: E402


def read_json(path: Path):
    return json.loads(path.read_text()) if path.is_file() else None


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def events(path: Path):
    if not path.is_file():
        return []
    result = []
    for line in path.read_text().splitlines():
        if line.strip():
            result.append(json.loads(line))
    return result


def main():
    summary = read_json(EVIDENCE / "summary.json")
    if not isinstance(summary, dict) or not isinstance(summary.get("rows"), list):
        raise RuntimeError("Sealed summary is missing or malformed")
    source_rows = summary["rows"]
    row_map = {(row["case"], row["stage"], row["state"]): row for row in source_rows}
    expected_cell_keys = {(case, arm, state) for case in comparison.CASES
                          for arm in comparison.ARMS for state in comparison.STATES}
    if len(source_rows) != 32 or set(row_map) != expected_cell_keys:
        raise RuntimeError("Declared-cell summary does not contain exactly 32 unique cells")

    built = base.cases()
    cells = []
    errors = []
    assessment_replayed = 0
    admissions_replayed = 0
    admission_mismatches = 0
    cache_targets_replayed = 0
    starts_checked = 0

    for case_name in comparison.CASES:
        case = built[case_name]
        cfg = base.budget(case_name, "cold_hull")
        for state in comparison.STATES:
            market = base.market(case_name, state)
            for arm in comparison.ARMS:
                key = (case_name, arm, state)
                row = row_map[key]
                folder = comparison.cell_dir(EVIDENCE, case_name, state, arm)
                receipt = read_json(folder / "receipt.json")
                raw_wrapper = read_json(folder / "raw_result.json")
                saved_result = read_json(folder / "result.json")
                exception = read_json(folder / "exception.json")
                entry = {
                    "case": case_name,
                    "arm": arm,
                    "state": state,
                    "row_status": row.get("status"),
                    "receipt_returncode": (receipt or {}).get("returncode"),
                    "receipt_hard_timeout": (receipt or {}).get("hard_timeout"),
                    "receipt_on_time": (receipt or {}).get("on_time"),
                    "receipt_elapsed_seconds": (receipt or {}).get("elapsed_seconds"),
                    "exception_type": (exception or {}).get("type"),
                    "exception_message": (exception or {}).get("message"),
                    "raw_status": None,
                    "raw_bounds": None,
                    "replayed_bounds": None,
                    "complete_evidence": None,
                    "assessment_matches_saved": None,
                    "summary_matches_replay": None,
                    "pricing_calls": None,
                    "master_calls": None,
                }

                if receipt is not None:
                    if row.get("receipt") != receipt:
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": "summary receipt differs from sealed receipt"})
                    expected_receipt_status = (
                        "timed_out" if receipt.get("hard_timeout") else
                        "failed" if receipt.get("returncode") != 0 else
                        "late" if not receipt.get("on_time") else None)
                    if expected_receipt_status and row.get("status") != expected_receipt_status:
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": "failed/late/timeout classification differs from receipt"})
                    if (receipt.get("returncode") != 0 and receipt.get("hard_timeout") is False
                            and receipt.get("on_time") is False):
                        entry["failure_class"] = "nonzero child exit; not a hard timeout"
                elif row.get("status") != "ineligible":
                    errors.append({"cell": [case_name, arm, state],
                                   "issue": "missing receipt without ineligible status"})

                if raw_wrapper is not None:
                    wrapper_id = (raw_wrapper.get("case"), raw_wrapper.get("state"),
                                  raw_wrapper.get("stage"))
                    if wrapper_id != (case_name, state, arm):
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": "raw wrapper identity differs"})
                    result = raw_wrapper["result"]
                    entry["raw_status"] = result.get("status")
                    entry["raw_bounds"] = [result.get("lower"), result.get("upper")]
                    counts = result.get("counts", {})
                    entry["pricing_calls"] = counts.get("pricing_requests")
                    entry["master_calls"] = counts.get("master_calls")
                    try:
                        replay = base.assess(case, market, arm, result)
                        assessment_replayed += 1
                        entry["replayed_bounds"] = replay.get("bounds")
                        entry["complete_evidence"] = replay.get("complete_evidence")
                        if saved_result is not None:
                            saved_assessment = saved_result.get("assessment")
                            entry["assessment_matches_saved"] = replay == saved_assessment
                            if replay != saved_assessment:
                                errors.append({"cell": [case_name, arm, state],
                                               "issue": "saved assessment differs from independent base.assess replay"})
                        else:
                            entry["assessment_matches_saved"] = False
                            errors.append({"cell": [case_name, arm, state],
                                           "issue": "raw result exists without saved assessment"})
                        expected_native = replay.get("status")
                        expected_bounds = replay.get("bounds")
                        expected_complete = replay.get("complete_evidence")
                        entry["summary_matches_replay"] = (
                            row.get("native_status") == expected_native
                            and row.get("bounds") == expected_bounds
                            and row.get("complete_evidence") == expected_complete)
                        if not entry["summary_matches_replay"]:
                            errors.append({"cell": [case_name, arm, state],
                                           "issue": "summary outcome/bounds/evidence differs from replay"})
                    except Exception as exc:
                        entry["assessment_replay_error"] = f"{type(exc).__name__}: {exc}"
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": entry["assessment_replay_error"]})
                elif row.get("native_status") is not None or row.get("bounds") is not None:
                    errors.append({"cell": [case_name, arm, state],
                                   "issue": "summary reports native outcome without raw result"})

                if exception is not None and receipt is not None:
                    if receipt.get("returncode") == 0:
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": "exception file accompanies zero child exit"})
                cells.append(entry)

                # Every state-0 comparison arm must start from an empty pool.
                ev = events(folder / "events.jsonl")
                starts = [item for item in ev if item.get("event") == "state_start"]
                if starts:
                    starts_checked += 1
                    if len(starts) != 1:
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": "state_start event count is not one"})
                    if state == 0 and starts[0].get("imported_column_keys") != []:
                        errors.append({"cell": [case_name, arm, state],
                                       "issue": "state 0 did not start with an empty pool"})

    # One saved-evidence predecessor replay for each retained state-1 cell.
    predecessor_records = []
    prior_by_cell = {}
    identity_by_cell = {}
    for case_name in comparison.CASES:
        for arm in comparison.ARMS[1:]:
            row = row_map[(case_name, arm, 1)]
            folder = comparison.cell_dir(EVIDENCE, case_name, 1, arm)
            admission = read_json(folder / "admission.json")
            record = {"case": case_name, "arm": arm,
                      "summary_status": row.get("status"),
                      "admission_present": admission is not None,
                      "admission_eligible": (admission or {}).get("eligible"),
                      "predecessor_replayed": False,
                      "admission_matches_replay": None,
                      "child_source_check_matches": None}
            if admission is None:
                errors.append({"cell": [case_name, arm, 1],
                               "issue": "retained state 1 lacks parent admission receipt"})
                predecessor_records.append(record)
                continue
            if row.get("admission") != admission:
                errors.append({"cell": [case_name, arm, 1],
                               "issue": "summary admission differs from sealed admission"})
            try:
                prior, identity = comparison.predecessor(
                    EVIDENCE, case_name, arm,
                    admission.get("source_files") if admission.get("eligible") is True else None)
                replay_eligible = True
                prior_by_cell[(case_name, arm)] = prior
                identity_by_cell[(case_name, arm)] = identity
                record["source_identity"] = identity
                record["source_status"] = prior.get("status")
                record["source_column_count"] = len(prior.get("columns", []))
            except Exception as exc:
                replay_eligible = False
                record["predecessor_error"] = f"{type(exc).__name__}: {exc}"
            admissions_replayed += 1
            record["predecessor_replayed"] = True
            record["admission_matches_replay"] = replay_eligible == admission.get("eligible")
            if not record["admission_matches_replay"]:
                admission_mismatches += 1
                errors.append({"cell": [case_name, arm, 1],
                               "issue": "saved admission eligibility differs from predecessor replay"})
            if replay_eligible:
                if identity != admission.get("source_state_identity"):
                    record["admission_matches_replay"] = False
                    admission_mismatches += 1
                    errors.append({"cell": [case_name, arm, 1],
                                   "issue": "saved admission source identity differs from replay"})
                # The worker must show it rechecked the pinned source files before use.
                child_check = read_json(folder / "child_source_check.json")
                if child_check is not None:
                    record["child_source_check_matches"] = (
                        child_check.get("source_state_identity") == identity
                        and child_check.get("source_files") == admission.get("source_files"))
                    if not record["child_source_check_matches"]:
                        errors.append({"cell": [case_name, arm, 1],
                                       "issue": "worker source-check receipt differs from admission pins"})
                elif (row.get("receipt", {}).get("returncode") == 0
                      or (folder / "events.jsonl").is_file()):
                    record["child_source_check_matches"] = False
                    errors.append({"cell": [case_name, arm, 1],
                                   "issue": "eligible launched child lacks source-check receipt"})

                # Replay the retained physical pool lineage in a target cell when raw exists.
                raw_wrapper = read_json(comparison.cell_dir(EVIDENCE, case_name, 1, arm)
                                         / "raw_result.json")
                if raw_wrapper is not None:
                    raw = raw_wrapper["result"]
                    try:
                        imported = nh.import_pool(
                            built[case_name], prior, identity, base.budget(case_name, "cold_hull"),
                            previous_index=0, extraction_policy=compact.EXTRACTION_POLICY,
                            reuse_policy="feasible_pool", oracle_id=compact.ORACLE_ID,
                            pricing_reserve_seconds=10.0)
                        start_events = [item for item in events(folder / "events.jsonl")
                                        if item.get("event") == "state_start"]
                        expected_imported_keys = [column["key"] for column in imported]
                        if (len(start_events) != 1
                                or start_events[0].get("imported_column_keys") != expected_imported_keys):
                            errors.append({"cell": [case_name, arm, 1],
                                           "issue": "target imported pool differs from own admitted source"})
                        elif len(raw.get("columns", [])) < len(imported):
                            errors.append({"cell": [case_name, arm, 1],
                                           "issue": "target raw pool lost admitted physical columns"})
                    except Exception as exc:
                        errors.append({"cell": [case_name, arm, 1],
                                       "issue": f"target retained pool replay failed: {type(exc).__name__}: {exc}"})

                # Rebuild each target-market Fenchel conjugate from source physical lowers.
                if arm == "qp_cache_feasible_hull" and raw_wrapper is not None:
                    target_market = base.market(case_name, 1)
                    raw = raw_wrapper["result"]
                    records = prior.get("physical_pricing_evidence", [])
                    candidates = raw.get("cached_lower_candidates")
                    rebuilt = []
                    for item in records:
                        data = item["record"]
                        rebuilt.append({
                            "certificate": nh.fenchel_bound(target_market, data["prices"],
                                                            data["pricing_lower"]),
                            "source_state_identity": identity,
                            "source_market_identity": prior["market_identity"],
                            "source_pricing_call": data["pricing_call"],
                            "source_record_digest": item["digest"],
                            "source_column_key": data["column_key"],
                        })
                    if (raw.get("cache_source_state_identity") != identity
                            or candidates != rebuilt):
                        errors.append({"cell": [case_name, arm, 1],
                                       "issue": "target cache candidates differ from source physical lowers re-evaluated at target market"})
                    cache_events = [item for item in events(folder / "events.jsonl")
                                    if item.get("event") == "physical_pricing_cache_checked"]
                    starts = [item for item in events(folder / "events.jsonl")
                              if item.get("event") == "state_start"]
                    if (len(cache_events) != 1 or len(starts) != 1
                            or cache_events[0].get("source_state_identity") != identity
                            or cache_events[0].get("candidate_count") != len(records)
                            or starts[0].get("cached_bound_candidates") != len(records)
                            or starts[0].get("target_conjugates_rebuilt_from_cached_physical_lowers") is not True
                            or starts[0].get("fresh_target_pricing_required") is not True):
                        errors.append({"cell": [case_name, arm, 1],
                                       "issue": "target cache-check event does not preserve full lineage/fresh-pricing requirements"})
                    if raw.get("status") == "certified" and raw.get("fresh_pricing_successes", 0) < 1:
                        errors.append({"cell": [case_name, arm, 1],
                                       "issue": "cached-bound target certified without fresh target pricing"})
                    cache_targets_replayed += 1
            predecessor_records.append(record)

    # Confirm the sealed paid-pair arithmetic: two child receipt times and one
    # parent admission time for retained arms; incomplete components stay null.
    saved_pairs = summary.get("paid_pairs")
    api_pairs = comparison.paid_pairs(source_rows)
    manual_pairs = []
    for case_name in comparison.CASES:
        for arm in comparison.ARMS:
            first = (row_map[(case_name, arm, 0)].get("receipt") or {}).get("elapsed_seconds")
            second_row = row_map[(case_name, arm, 1)]
            second = (second_row.get("receipt") or {}).get("elapsed_seconds")
            admission = ((second_row.get("admission") or {}).get("parent_check_elapsed_seconds")
                         if arm != comparison.ARMS[0] else None)
            known = (finite_number(first) and finite_number(second)
                     and (arm == comparison.ARMS[0] or finite_number(admission)))
            total = first + second + (admission if arm != comparison.ARMS[0] else 0) if known else None
            manual_pairs.append({
                "case": case_name,
                "arm": arm,
                "state0_child_elapsed_seconds": first,
                "state1_child_elapsed_seconds": second,
                "parent_admission_elapsed_seconds": admission,
                "complete_two_state_paid_seconds": total,
            })
    if saved_pairs != api_pairs or saved_pairs != manual_pairs:
        errors.append({"issue": "sealed paid-pair totals differ from independent receipt/admission arithmetic"})

    status_counts = {}
    native_counts = {}
    for cell in cells:
        status_counts[cell["row_status"]] = status_counts.get(cell["row_status"], 0) + 1
        native = cell["raw_status"] or "(no raw native result)"
        native_counts[native] = native_counts.get(native, 0) + 1
    summary_report = {
        "evidence_root": str(EVIDENCE),
        "expected_cell_count": len(expected_cell_keys),
        "sealed_row_count": len(source_rows),
        "all_declared_cells_unique": True,
        "row_status_counts": status_counts,
        "raw_native_status_counts": native_counts,
        "assessment_replay_count": assessment_replayed,
        "predecessor_replay_count": admissions_replayed,
        "admission_eligibility_mismatches": admission_mismatches,
        "cache_target_replay_count": cache_targets_replayed,
        "state_start_events_checked": starts_checked,
        "paid_pair_count": len(manual_pairs),
        "paid_pair_arithmetic_matches_saved": not any(
            item.get("issue", "").startswith("sealed paid-pair") for item in errors),
        "errors": errors,
        "cells": cells,
        "predecessors": predecessor_records,
        "paid_pairs": manual_pairs,
    }
    OUT.write_text(json.dumps(summary_report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: value for key, value in summary_report.items()
                      if key not in ("cells", "predecessors", "paid_pairs")},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
