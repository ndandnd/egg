"""Pair sealed QP scalar summary with the curated six-cell native-LP baseline.

Read only frozen declarations, top-level receipts, summaries, and baseline
compact rows. Do not open event logs, route data, or an optimizer.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASELINE = HERE.parents[1] / "cold-baseline-viability/results-attempt1"
CASES = tuple(f"native_scale_dev_s1006_n{n:02d}" for n in (8, 16, 24))
KINDS = ("source0", "target")
KEYS = tuple((case, market) for case in CASES for market in KINDS)
COMPLETE_STATUSES = {"certified", "budget_exhausted", "stalled_bounded"}
EPSILON = Fraction(1, 10_000)
FIELDS = (
    "case", "services", "market", "case_identity", "market_identity",
    "lp_outcome", "lp_stop_reason", "lp_complete_evidence", "lp_on_time",
    "lp_certified", "lp_within_epsilon", "lp_lower_floor4", "lp_upper_ceil4",
    "lp_gap_ceil6", "lp_lower_exact_sha256", "lp_upper_exact_sha256",
    "lp_gap_exact_sha256", "lp_pricing_requests", "lp_master_calls",
    "lp_max_rational_bits", "lp_child_wall_s",
    "lp_pricing_solver_wall_recorded_s", "lp_pricing_solver_wall_complete",
    "lp_native_master_wall_s", "lp_native_master_wall_complete",
    "lp_polish_wall_s", "lp_model_construction_s",
    "qp_outcome", "qp_stop_reason", "qp_complete_evidence", "qp_on_time",
    "qp_certified", "qp_within_epsilon", "qp_lower_floor4", "qp_upper_ceil4",
    "qp_gap_ceil6", "qp_lower_exact_sha256", "qp_upper_exact_sha256",
    "qp_gap_exact_sha256", "qp_pricing_requests", "qp_master_calls",
    "qp_max_rational_bits", "qp_child_wall_s",
    "qp_pricing_solver_wall_recorded_s", "qp_pricing_solver_wall_complete",
    "qp_proposal_calls", "qp_non_success", "qp_proposal_wall_s",
    "qp_replay_wall_s", "qp_polish_wall_s", "qp_model_construction_s",
    "qp_native_lp_master_time_applicable", "qp_curation_issue",
)


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def directed(value, digits, *, upper=False):
    number = Fraction(value)
    scale = 10 ** digits
    units = (-((-number.numerator * scale) // number.denominator)
             if upper else (number.numerator * scale) // number.denominator)
    sign = "-" if units < 0 else ""
    absolute = abs(units)
    return f"{sign}{absolute // scale}.{absolute % scale:0{digits}d}"


def _six_unique(rows, label):
    keys = [(row.get("case"), row.get("market")) for row in rows]
    if len(rows) != 6 or len(set(keys)) != 6 or set(keys) != set(KEYS):
        raise ValueError(f"{label} must contain six unique declared cells")
    return {(row["case"], row["market"]): row for row in rows}


def _matched_design(lp, qp):
    left, right = lp["design"], qp["design"]
    for field in ("budget", "order", "hard_child_seconds", "pricing_reserve_seconds",
                  "arm", "bound_cache_policy", "development_only", "independent_test_data"):
        if left.get(field) != right.get(field):
            raise ValueError(f"Matched design differs: {field}")
    if lp.get("declared_cells") != 6 or qp.get("declared_cells") != 6:
        raise ValueError("Six-cell declaration differs")
    if (right.get("master_policy"), right.get("qp_denominator"),
            right.get("qp_maxiter")) != ("numerical_qp_proposal", 10**9, 500):
        raise ValueError("QP master controls differ")
    if left.get("master_policy") not in (None, "native_lp"):
        raise ValueError("Baseline master policy differs")
    if set(left["cases"]) != set(CASES) or set(right["cases"]) != set(CASES):
        raise ValueError("Physical case selection differs")
    for case in CASES:
        a, b = left["cases"][case], right["cases"][case]
        for field in ("base_group", "case_identity", "market_identities", "markets"):
            if a.get(field) != b.get(field):
                raise ValueError(f"Case/market mismatch: {case}/{field}")
        if set(a["market_identities"]) != set(KINDS):
            raise ValueError(f"Market selection differs: {case}")


def _qp_integrity(sealed, summary, frozen):
    reasons = []
    if summary.get("protocol") != frozen.get("protocol"):
        reasons.append("protocol_mismatch")
    if (summary.get("declared_cells"), summary.get("accounted_cells"),
            summary.get("all_declared_cells_accounted")) != (6, 6, True):
        reasons.append("incomplete_top_level_accounting")
    try:
        supervisor = read(sealed / "supervisor_receipt.json")
        if (supervisor.get("protocol") != frozen.get("protocol")
                or supervisor.get("returncode") != 0
                or supervisor.get("stable_seal") is not True
                or supervisor.get("process_group_quiescent") is not True
                or supervisor.get("source_hashes_unchanged") is not True):
            reasons.append("supervisor_integrity_failed")
    except (OSError, ValueError, TypeError):
        supervisor = {}
        reasons.append("supervisor_receipt_missing_or_unreadable")
    try:
        wrapper = read(sealed.with_name(sealed.name + ".slurm_wrapper_receipt.json"))
        if any(wrapper.get(field) != 0 for field in
               ("returncode", "freeze_returncode", "preflight_returncode",
                "supervise_returncode")):
            reasons.append("wrapper_phase_failed")
    except (OSError, ValueError, TypeError):
        wrapper = {}
        reasons.append("wrapper_receipt_missing_or_unreadable")
    return reasons, supervisor, wrapper


def _lp_fields(row):
    admitted = (row.get("complete_evidence") is True and row.get("on_time") is True
                and row.get("outcome") in COMPLETE_STATUSES
                and row.get("gap_ceil6") is not None)
    # The source baseline curator already checked its exact sealed endpoints.
    return {
        "lp_outcome": row.get("outcome"), "lp_stop_reason": row.get("stop_reason"),
        "lp_complete_evidence": row.get("complete_evidence"),
        "lp_on_time": row.get("on_time"),
        "lp_certified": admitted and row["outcome"] == "certified",
        "lp_within_epsilon": admitted and Fraction(row["gap_ceil6"]) <= EPSILON,
        "lp_lower_floor4": row.get("lower_floor4") if admitted else None,
        "lp_upper_ceil4": row.get("upper_ceil4") if admitted else None,
        "lp_gap_ceil6": row.get("gap_ceil6") if admitted else None,
        "lp_lower_exact_sha256": row.get("lower_exact_sha256") if admitted else None,
        "lp_upper_exact_sha256": row.get("upper_exact_sha256") if admitted else None,
        "lp_gap_exact_sha256": row.get("gap_exact_sha256") if admitted else None,
        "lp_pricing_requests": row.get("pricing_requests"),
        "lp_master_calls": row.get("master_calls"),
        "lp_max_rational_bits": row.get("max_rational_bits"),
        "lp_child_wall_s": row.get("child_wall_s"),
        "lp_pricing_solver_wall_recorded_s": row.get("pricing_solver_wall_recorded_s"),
        "lp_pricing_solver_wall_complete": row.get("pricing_solver_wall_complete"),
        "lp_native_master_wall_s": row.get("master_solver_wall_recorded_s"),
        "lp_native_master_wall_complete": row.get("master_solver_wall_complete"),
        "lp_polish_wall_s": row.get("polish_wall_s"),
        "lp_model_construction_s": row.get("model_construction_s"),
    }


def _qp_fields(row, *, integrity_ok):
    eligible = (integrity_ok and row.get("complete_evidence") is True
                and row.get("on_time") is True
                and row.get("outcome") in COMPLETE_STATUSES
                and row.get("master_policy") == "numerical_qp_proposal")
    issue = None
    lower = upper = gap = None
    if eligible:
        try:
            lower, upper, gap = (Fraction(row[field]) for field in
                                 ("lower_exact", "upper_exact", "gap_exact"))
            if not (lower <= upper and upper - lower == gap):
                raise ValueError("interval arithmetic")
        except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
            lower = upper = gap = None
            issue = "invalid_native_enclosure"
    elif row.get("complete_evidence") is True:
        issue = "complete_row_not_admitted"
    admitted = gap is not None
    return {
        "qp_outcome": row.get("outcome"), "qp_stop_reason": row.get("stop_reason"),
        "qp_complete_evidence": row.get("complete_evidence"),
        "qp_on_time": row.get("on_time"),
        "qp_certified": admitted and row["outcome"] == "certified",
        "qp_within_epsilon": admitted and gap <= EPSILON,
        "qp_lower_floor4": directed(lower, 4) if admitted else None,
        "qp_upper_ceil4": directed(upper, 4, upper=True) if admitted else None,
        "qp_gap_ceil6": directed(gap, 6, upper=True) if admitted else None,
        "qp_lower_exact_sha256": digest(row["lower_exact"]) if admitted else None,
        "qp_upper_exact_sha256": digest(row["upper_exact"]) if admitted else None,
        "qp_gap_exact_sha256": digest(row["gap_exact"]) if admitted else None,
        "qp_pricing_requests": row.get("pricing_requests"),
        "qp_master_calls": row.get("master_calls"),
        "qp_max_rational_bits": row.get("max_rational_bits"),
        "qp_child_wall_s": row.get("child_wall_s"),
        "qp_pricing_solver_wall_recorded_s": row.get("pricing_solver_wall_recorded_s"),
        "qp_pricing_solver_wall_complete": row.get("pricing_solver_wall_complete"),
        "qp_proposal_calls": row.get("qp_proposal_calls"),
        "qp_non_success": row.get("qp_non_success"),
        "qp_proposal_wall_s": row.get("qp_proposal_wall_s"),
        "qp_replay_wall_s": row.get("qp_replay_wall_s"),
        "qp_polish_wall_s": row.get("polish_wall_s"),
        "qp_model_construction_s": row.get("model_construction_s"),
        "qp_native_lp_master_time_applicable": False,
        "qp_curation_issue": issue,
    }


def collect(sealed):
    sealed = Path(sealed)
    baseline = read(BASELINE / "compactrows.json")
    lp_frozen = read(BASELINE / "frozen_identity.json")
    qp_frozen = read(sealed / "frozen.json")
    _matched_design(lp_frozen, qp_frozen)
    if (baseline.get("source_commit") != lp_frozen.get("source_commit")
            or baseline.get("protocol") != lp_frozen.get("protocol")):
        raise ValueError("Curated baseline differs from its frozen declaration")
    left = _six_unique(baseline["rows"], "Curated LP baseline")
    try:
        summary = read(sealed / "summary.json")
    except (OSError, ValueError, TypeError):
        summary = read(sealed / "postmortem_summary.json")
    right = _six_unique(summary["rows"], "QP summary/postmortem")
    reasons, supervisor, wrapper = _qp_integrity(sealed, summary, qp_frozen)
    rows = []
    for case, market in KEYS:
        declaration = qp_frozen["design"]["cases"][case]
        source = right[(case, market)]
        if (source.get("state_index") != KINDS.index(market)
                or source.get("case") != case or source.get("market") != market):
            raise ValueError(f"QP row identity/state mismatch: {case}/{market}")
        row = {"case": case, "services": int(case[-2:]), "market": market,
               "case_identity": declaration["case_identity"],
               "market_identity": declaration["market_identities"][market]}
        row.update(_lp_fields(left[(case, market)]))
        row.update(_qp_fields(source, integrity_ok=not reasons))
        rows.append(row)
    return {
        "scope": "paired six-cell cold development diagnosis; one nested seed-1006 family",
        "baseline_protocol": lp_frozen["protocol"],
        "baseline_source_commit": lp_frozen["source_commit"],
        "baseline_job_id": baseline.get("job_id"),
        "qp_protocol": qp_frozen["protocol"],
        "qp_source_commit": qp_frozen["source_commit"],
        "qp_job_id": wrapper.get("job_id"),
        "matched_frozen_case_market_budget_order": True,
        "qp_integrity_ok": not reasons, "qp_integrity_reasons": reasons,
        "qp_supervisor_elapsed_s": supervisor.get("elapsed_seconds"),
        "qp_wrapper_elapsed_s": wrapper.get("elapsed_whole_seconds"),
        "qp_setup_s": wrapper.get("setup_seconds"),
        "native_tolerance_qualified": True,
        "exact_ideal_proof": False,
        "exact_fraction_policy": "SHA-256 hashes refer to sealed QP summary endpoint text",
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sealed", type=Path, help="collected QP attempt directory")
    parser.add_argument("out", type=Path, nargs="?", default=HERE)
    args = parser.parse_args()
    data = collect(args.sealed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "compactrows.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with (args.out / "compactrows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in FIELDS} for row in data["rows"])


if __name__ == "__main__":
    main()
