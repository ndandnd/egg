"""Curate the sealed eight-cell public DEV attempt from summaries and receipts only.

No event logs, solver calls, or numerical result assumptions are used. Incomplete
stages remain in the output and never contribute a derived native interval.
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEPOTS = ("public_depot15", "public_depot16")
SCENARIOS = ((100, 1), (40, 1), (20, 1), (40, 2))
CELLS = tuple((f"{depot}_f{fee}_k{mult}", "market0")
              for fee, mult in SCENARIOS for depot in DEPOTS)
STAGES = ("planner", "cold_hull", "response")
HARD = {"planner": 210, "cold_hull": 210, "response": 90}
CSV_FIELDS = ("case", "depot", "bus_fee", "curvature_multiplier", "market",
              "planner_outcome", "hull_outcome", "response_outcome",
              "D_lower_floor4", "D_upper_ceil4", "CH_lower_floor4",
              "CH_upper_ceil4", "gap_lower_floor6", "gap_upper_ceil6",
              "regret_lower_floor6", "regret_upper_ceil6",
              "planner_width_upper_ceil6", "ideal_floor_floor4",
              "conditional_ideal_gap_upper_ceil4", "planner_child_s",
              "hull_child_s", "response_child_s", "planner_stop",
              "hull_stop", "response_stop", "planner_calls", "hull_pricing_calls",
              "hull_qp_proposal_calls", "response_calls", "used_buses",
              "native_admitted", "ideal_upper_conditional")


def read(path):
    return json.loads(Path(path).read_text())


def sha_text(value):
    return hashlib.sha256(value.encode()).hexdigest()


def directed(value, digits, *, upper=False):
    number = Fraction(value)
    scale = 10 ** digits
    units = (-((-number.numerator * scale) // number.denominator)
             if upper else (number.numerator * scale) // number.denominator)
    sign = "-" if units < 0 else ""
    absolute = abs(units)
    return f"{sign}{absolute // scale}.{absolute % scale:0{digits}d}"


def interval(values):
    if not isinstance(values, list) or len(values) != 2:
        return None
    if any(isinstance(value, bool) for value in values):
        return None
    try:
        lo, hi = map(Fraction, values)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return (lo, hi) if lo <= hi else None


def native_combination(d_values, ch_values):
    """Combine only compatible same-case physical and hull native enclosures."""
    d, ch = interval(d_values), interval(ch_values)
    if d is None or ch is None or d[1] < ch[0]:
        return None
    d_lo, d_hi = max(d[0], ch[0]), d[1]
    ch_lo, ch_hi = ch[0], min(ch[1], d_hi)
    if d_lo > d_hi or ch_lo > ch_hi:
        return None
    return {"D_exact": [str(d_lo), str(d_hi)],
            "CH_exact": [str(ch_lo), str(ch_hi)],
            "gap_exact": [str(max(Fraction(0), d_lo - ch_hi)), str(d_hi - ch_lo)]}


def _case(name):
    for fee, mult in SCENARIOS:
        for depot in DEPOTS:
            if name == f"{depot}_f{fee}_k{mult}":
                return depot, fee, mult
    raise ValueError("Unexpected public sensitivity case")


def _stage_key(row):
    return row.get("case"), row.get("market"), row.get("stage")


def _optional_read(path):
    try:
        return read(path) if path.is_file() else None
    except (OSError, ValueError):
        return None


def _manifest_ok(sealed, protocol):
    """Check every sealed file's declared size and SHA, without parsing logs."""
    if (sealed / "MANIFEST.json").is_symlink():
        return False
    manifest = _optional_read(sealed / "MANIFEST.json")
    if not isinstance(manifest, dict) or manifest.get("protocol") != protocol:
        return False
    declared = manifest.get("files")
    if not isinstance(declared, dict):
        return False
    try:
        found = {str(path.relative_to(sealed)): path for path in sealed.rglob("*")
                 if path.is_file() and path != sealed / "MANIFEST.json"}
        if set(found) != set(declared):
            return False
        for name, path in found.items():
            entry = declared[name]
            if (path.is_symlink() or not isinstance(entry, dict)
                    or type(entry.get("bytes")) is not int
                    or entry["bytes"] != path.stat().st_size
                    or not isinstance(entry.get("sha256"), str)):
                return False
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != entry["sha256"]:
                return False
    except (OSError, KeyError, TypeError, ValueError):
        return False
    return True


def _global_integrity(sealed, frozen, summary):
    supervisor = _optional_read(sealed / "supervisor_receipt.json")
    wrapper = _optional_read(sealed.with_name(
        sealed.name + ".slurm_wrapper_receipt.json"))
    manifest_ok = _manifest_ok(sealed, frozen.get("protocol"))
    ok = bool(manifest_ok and supervisor and wrapper
              and summary.get("protocol") == frozen.get("protocol")
              and summary.get("all_declared_stages_accounted") is True
              and summary.get("declared_cells") == 8
              and summary.get("accounted_cells") == 8
              and summary.get("declared_stages") == 24
              and summary.get("accounted_stages") == 24
              and len(summary.get("rows") or []) == 24
              and supervisor.get("protocol") == frozen.get("protocol")
              and supervisor.get("returncode") == 0
              and supervisor.get("stable_seal") is True
              and supervisor.get("process_group_quiescent") is True
              and supervisor.get("source_hashes_unchanged") is True
              and all(wrapper.get(k) == 0 for k in
                      ("returncode", "freeze_returncode", "preflight_returncode",
                       "supervise_returncode")))
    return ok, supervisor, wrapper, manifest_ok


def _stage(sealed, declared, row, name, kind, stage, integrity_ok):
    """Retain raw scalar accounting; admit bounds only with complete receipts."""
    source = row or {}
    dest = sealed / name / "state0" / stage
    receipt = _optional_read(dest / "receipt.json")
    result = _optional_read(dest / "result.json")
    exception = _optional_read(dest / "exception.json")
    receipt_elapsed = receipt.get("elapsed_seconds") if receipt else None
    summary_elapsed = source.get("child_wall_s")
    paid_elapsed = (receipt_elapsed if type(receipt_elapsed) in (int, float)
                    else summary_elapsed)
    compact = {"case": name, "market": kind, "stage": stage,
               "outcome": source.get("outcome", "unstarted"),
               "native_status": source.get("native_status"),
               "stop_reason": source.get("stop_reason"),
               "on_time": source.get("on_time"),
               "child_wall_s": paid_elapsed,
               "summary_child_wall_s": summary_elapsed,
               "receipt_elapsed_seconds": receipt_elapsed,
               "child_returncode": receipt.get("returncode") if receipt else None,
               "hard_timeout": receipt.get("hard_timeout") if receipt else None,
               "receipt_error": receipt.get("error") if receipt else None,
               "exception_type": exception.get("type") if exception else None,
               "exception_message": exception.get("message") if exception else None,
               "native_calls": source.get("native_calls"),
               "native_solver_wall_recorded_s": source.get("native_solver_wall_recorded_s"),
               "native_solver_wall_complete": source.get("native_solver_wall_complete"),
               "pricing_requests": source.get("pricing_requests"),
               "master_calls": source.get("master_calls"),
               "max_rational_bits": source.get("max_rational_bits"),
               "polish_wall_s": source.get("polish_wall_s"),
               "qp_proposal_calls": source.get("qp_proposal_calls"),
               "qp_non_success": source.get("qp_non_success"),
               "qp_proposal_wall_s": source.get("qp_proposal_wall_s"),
               "qp_replay_wall_s": source.get("qp_replay_wall_s"),
               "used_buses": source.get("used_buses"),
               "plan_hash": source.get("plan_hash"),
               "planner_plan_hash": source.get("planner_plan_hash"),
               "raw_lower_exact": source.get("lower_exact"),
               "raw_upper_exact": source.get("upper_exact"),
               "raw_regret_lower_exact": source.get("regret_lower_exact"),
               "raw_regret_upper_exact": source.get("regret_upper_exact"),
               "admitted": False, "admitted_interval_exact": None,
               "admission_reason": None}
    if not integrity_ok:
        compact["admission_reason"] = "incomplete_or_unsealed_attempt"
        return compact
    if not (source.get("complete_evidence") is True
            and source.get("on_time") is True
            and source.get("outcome") in ("certified", "bounded", "budget_exhausted",
                                          "stalled_bounded")
            and receipt and result):
        compact["admission_reason"] = "missing_or_incomplete_stage"
        return compact
    assessment = result.get("assessment") or {}
    if (receipt.get("returncode") != 0 or receipt.get("hard_timeout") is not False
            or receipt.get("on_time") is not True
            or receipt_elapsed != summary_elapsed
            or receipt.get("hard_seconds") != HARD[stage]
            or (result.get("case"), result.get("market"), result.get("stage")) !=
               (name, kind, stage)
            or assessment.get("status") != source.get("outcome")
            or source.get("native_status") != source.get("outcome")):
        compact["admission_reason"] = "receipt_or_assessment_mismatch"
        return compact
    if stage == "cold_hull":
        assessed_interval = interval(assessment.get("bounds"))
        exact_interval = interval([source.get("lower_exact"), source.get("upper_exact")])
        if (assessment.get("complete_evidence") is not True
                or assessment.get("status") not in
                ("certified", "budget_exhausted", "stalled_bounded")
                or assessed_interval is None or exact_interval is None
                or assessed_interval[0] > exact_interval[0]
                or assessed_interval[1] < exact_interval[1]):
            compact["admission_reason"] = "incomplete_hull_assessment"
            return compact
    elif (assessment.get("plan_replayed") is not True
          or assessment.get("plan_hash") != source.get("plan_hash")
          or assessment.get("bounds") !=
          [source.get("lower_exact"), source.get("upper_exact")]
          or assessment.get("status") not in ("certified", "bounded")):
        compact["admission_reason"] = "incomplete_physical_assessment"
        return compact
    value = [source.get("lower_exact"), source.get("upper_exact")]
    if interval(value) is None:
        compact["admission_reason"] = "invalid_interval"
        return compact
    if stage == "response":
        if (source.get("planner_plan_hash") is None
                or assessment.get("planner_plan_hash") != source.get("planner_plan_hash")
                or assessment.get("own_price_regret_interval_exact") !=
                [source.get("regret_lower_exact"), source.get("regret_upper_exact")]
                or interval(assessment.get("own_price_regret_interval_exact")) is None):
            compact["admission_reason"] = "response_lineage_or_regret_mismatch"
            return compact
    else:
        if source.get("plan_hash") is None and stage == "planner":
            compact["admission_reason"] = "missing_planner_plan_hash"
            return compact
    compact["admitted"] = True
    compact["admitted_interval_exact"] = value
    return compact


def curate(sealed):
    sealed = Path(sealed)
    frozen = read(sealed / "frozen.json")
    summary = (_optional_read(sealed / "summary.json") or
               _optional_read(sealed / "postmortem_summary.json") or {"rows": []})
    declared = frozen.get("design", {})
    expected_order = [{"case": name, "market": kind, "state_index": 0}
                      for name, kind in CELLS]
    if (declared.get("order") != expected_order
            or set(declared.get("cases", {})) != {name for name, _ in CELLS}
            or declared.get("hard_child_seconds") != HARD
            or declared.get("controller_cap_seconds") != 5400
            or declared.get("master_policy") != "numerical_qp_proposal"
            or declared.get("qp_denominator") != 10**9
            or declared.get("qp_maxiter") != 500
            or declared.get("bound_cache_policy") != "none"
            or declared.get("arm") != "cold"):
        raise ValueError("Frozen eight-cell design or controls differ")
    budgets = declared.get("budgets", {})
    expected_budget_fields = {
        "planner": {"backend": "GRB", "threads": 1, "wall_seconds": 180,
                    "phase_seconds": 160, "max_rounds": 16, "epsilon": 1e-4},
        "cold_hull": {"backend": "GRB", "threads": 1, "wall_seconds": 180,
                      "phase_seconds": 160, "pricing_calls": 16,
                      "master_calls": 64, "pool_cap": 64,
                      "rational_bits": 8192, "epsilon": 1e-4,
                      "pool_tolerance": 1e-6, "polish_steps": 64,
                      "polish_seconds": 20},
        "response": {"backend": "GRB", "threads": 1, "wall_seconds": 60,
                     "phase_seconds": 45, "max_rounds": 1, "epsilon": 1e-4}}
    if (set(budgets) != set(STAGES)
            or any(budgets[stage].get(key) != value
                   for stage, expected_fields in expected_budget_fields.items()
                   for key, value in expected_fields.items())
            or declared.get("pricing_reserve_seconds") != 10.0):
        raise ValueError("Frozen planner/hull/response budgets differ")
    for name, kind in CELLS:
        case = declared["cases"][name]
        _, fee, mult = _case(name)
        if (case.get("scenario") != {"bus_fee": fee, "curvature_multiplier": mult}
                or case.get("market_identities", {}).get(kind) is None
                or case.get("case_identity") is None
                or case.get("market", {}).get("a") != [0.2] * 30
                or case.get("market", {}).get("b") != [mult / 900] * 30):
            raise ValueError("Frozen case, fee or market identity differs")
    rows = summary.get("rows") or []
    by_stage = {_stage_key(row): row for row in rows}
    expected = {(name, kind, stage) for name, kind in CELLS for stage in STAGES}
    if (len(rows) != len(by_stage) or not set(by_stage) <= expected
            or any(row.get("state_index") != 0 for row in rows)):
        raise ValueError("Duplicate or undeclared stage summary row")
    integrity_ok, supervisor, wrapper, manifest_ok = _global_integrity(
        sealed, frozen, summary)
    stage_rows, compact_rows = [], []
    for name, kind in CELLS:
        depot, fee, mult = _case(name)
        pair = {}
        for stage in STAGES:
            item = _stage(sealed, declared, by_stage.get((name, kind, stage)),
                          name, kind, stage, integrity_ok)
            pair[stage] = item
            stage_rows.append(item)
        p, h, r = (pair[key] for key in STAGES)
        floor = declared.get("analytical_floors", {}).get(name)
        case_decl = declared["cases"][name]
        if (not isinstance(floor, dict)
                or floor.get("modified_case_identity") != case_decl["case_identity"]
                or floor.get("market_identity") != case_decl["market_identities"][kind]
                or floor.get("base_case_identity") != case_decl.get("base_case_identity")
                or floor.get("scope") != "ideal stored-input model; reporting only"
                or floor.get("source_sha256") != frozen.get("source_hashes", {}).get(
                    "research-20260929/charging-availability-bound/bounds.json")):
            raise ValueError("Frozen ideal floor has wrong case/market/scope")
        ideal = Fraction(floor["lower_exact"])
        d = p["admitted_interval_exact"] if p["admitted"] else None
        ch = h["admitted_interval_exact"] if h["admitted"] else None
        native = native_combination(d, ch)
        regret = ([r["raw_regret_lower_exact"], r["raw_regret_upper_exact"]]
                  if r["admitted"] and p["admitted"] and
                  r["planner_plan_hash"] == p["plan_hash"] else None)
        if (regret is not None and (interval(regret) is None
                                    or interval(regret)[0] < 0)):
            regret = None
        d_width = str(interval(d)[1] - interval(d)[0]) if d else None
        # No reviewed receipt establishes ideal feasibility of a native upper
        # witness for these scenarios; do not combine model namespaces.
        conditional = None
        conditional_issue = "ideal_witness_feasibility_unverified" if d else None
        row = {"case": name, "depot": depot, "bus_fee": fee,
               "curvature_multiplier": mult, "market": kind,
               "case_identity": case_decl["case_identity"],
               "market_identity": case_decl["market_identities"][kind],
               "planner_outcome": p["outcome"], "hull_outcome": h["outcome"],
               "response_outcome": r["outcome"], "D_raw_exact": d,
               "CH_raw_exact": ch, "native_combined": native,
               "native_admitted": native is not None,
               "native_inconsistency": bool(d and ch and native is None),
               "regret_exact": regret, "planner_width_exact": d_width,
               "ideal_floor_exact": str(ideal),
               "conditional_ideal_gap_upper_exact": conditional,
               "conditional_ideal_issue": conditional_issue,
               "ideal_upper_conditional": False,
               "planner_child_s": p["child_wall_s"],
               "hull_child_s": h["child_wall_s"],
               "response_child_s": r["child_wall_s"],
               "planner_stop": p["stop_reason"], "hull_stop": h["stop_reason"],
               "response_stop": r["stop_reason"],
               "planner_calls": p["native_calls"],
               "hull_pricing_calls": h["pricing_requests"],
               "hull_qp_proposal_calls": h["qp_proposal_calls"],
               "response_calls": r["native_calls"],
               "used_buses": p["used_buses"]}
        for prefix, values, digits in (("D", d, 4), ("CH", ch, 4),
                                       ("gap", native["gap_exact"] if native else None, 6),
                                       ("regret", regret, 6)):
            row[f"{prefix}_lower_floor{digits}"] = (
                directed(values[0], digits) if values else None)
            row[f"{prefix}_upper_ceil{digits}"] = (
                directed(values[1], digits, upper=True) if values else None)
            row[f"{prefix}_exact_sha256"] = ([sha_text(x) for x in values]
                                              if values else None)
        row["planner_width_upper_ceil6"] = (directed(d_width, 6, upper=True)
                                               if d_width else None)
        row["ideal_floor_floor4"] = directed(ideal, 4)
        row["conditional_ideal_gap_upper_ceil4"] = (
            directed(conditional, 4, upper=True) if conditional else None)
        compact_rows.append(row)
    return {"scope": "eight declared public-timetable DEV sensitivity cells; native tolerance-qualified",
            "protocol": frozen.get("protocol"), "source_commit": frozen.get("source_commit"),
            "frozen_source_hashes": frozen.get("source_hashes"),
            "frozen_controls": {key: declared.get(key) for key in
                                ("order", "budgets", "hard_child_seconds",
                                 "controller_cap_seconds", "arm", "master_policy",
                                 "qp_denominator", "qp_maxiter",
                                 "pricing_reserve_seconds", "bound_cache_policy")},
            "job_id": wrapper.get("job_id") if wrapper else None,
            "global_integrity_ok": integrity_ok,
            "manifest_ok": manifest_ok,
            "supervisor_elapsed_s": supervisor.get("elapsed_seconds") if supervisor else None,
            "wrapper_elapsed_s": wrapper.get("elapsed_whole_seconds") if wrapper else None,
            "wrapper_setup_s": wrapper.get("setup_seconds") if wrapper else None,
            "declared_cells": 8, "accounted_cells": len(compact_rows),
            "declared_stages": 24, "summary_stage_rows_present": len(rows),
            "accounted_stage_slots": len(stage_rows),
            "native_tolerance_qualified": integrity_ok,
            "ideal_exact_lower_separate": True,
            "conditional_ideal_upper_scope":
            "unset: no reviewed exact ideal-feasible-witness receipt for these native uppers; "
            "native lower bounds are never transferred to the ideal interval",
            "stage_rows": stage_rows, "rows": compact_rows}


def markdown(data):
    lines = ["| Depot | Fee | Curvature | D native | CH native | D−CH native | Planner width ≤ | Incumbent regret | Ideal floor | Planner / hull / response s | Outcomes |",
             "| --- | ---: | ---: | --- | --- | --- | ---: | --- | ---: | --- | --- |"]
    def shown(values, digits):
        return (f"[{directed(values[0], digits)}, "
                f"{directed(values[1], digits, upper=True)}]" if values else "—")
    for row in data["rows"]:
        native = row["native_combined"]
        times = " / ".join("—" if row[key] is None else f"{row[key]:.2f}"
                           for key in ("planner_child_s", "hull_child_s", "response_child_s"))
        outcomes = " / ".join(str(row[key]) for key in
                              ("planner_outcome", "hull_outcome", "response_outcome"))
        lines.append(f"| {row['depot'].removeprefix('public_')} | {row['bus_fee']} | "
                     f"{row['curvature_multiplier']} | {shown(row['D_raw_exact'], 4)} | "
                     f"{shown(row['CH_raw_exact'], 4)} | "
                     f"{shown(native['gap_exact'] if native else None, 6)} | "
                     f"{row['planner_width_upper_ceil6'] or '—'} | "
                     f"{shown(row['regret_exact'], 6)} | "
                     f"{row['ideal_floor_floor4']} | {times} | {outcomes} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sealed", type=Path)
    parser.add_argument("out", type=Path, nargs="?", default=HERE / "results-attempt1")
    args = parser.parse_args()
    data = curate(args.sealed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "compactrows.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    with (args.out / "compactrows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in CSV_FIELDS} for row in data["rows"])
    (args.out / "TABLE.md").write_text(markdown(data))


if __name__ == "__main__":
    main()
