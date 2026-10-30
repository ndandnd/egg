"""Read-only compact report for one sealed computational DEVELOPMENT screen."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path, PurePosixPath

from experiments import computational_benchmark as screen

FIELDS = ("case", "base_timetable_group", "state", "stage", "eligibility",
          "outcome", "native_status", "on_time", "complete_evidence",
          "wall_seconds", "lower_exact", "upper_exact", "gap_exact",
          "pricing_requests", "pricing_solver_wall_recorded_s",
          "pricing_solver_wall_complete", "master_calls",
          "master_solver_wall_recorded_s", "master_solver_wall_complete",
          "polish_steps", "polish_wall_s")


def read_json(path):
    return json.loads(path.read_text())


def verify_manifest(attempt):
    attempt = Path(attempt)
    manifest_path = attempt / "MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("Attempt has no stable manifest")
    manifest = read_json(manifest_path)
    if manifest.get("protocol") != screen.PROTOCOL or not isinstance(manifest.get("files"), dict):
        raise ValueError("Manifest protocol or file listing invalid")
    expected = manifest["files"]
    actual = {p.relative_to(attempt).as_posix() for p in attempt.rglob("*") if p.is_file()}
    if actual != set(expected) | {"MANIFEST.json"}:
        raise ValueError("Manifest does not exactly cover attempt files")
    for name, item in expected.items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or name == "MANIFEST.json"
                or not isinstance(item, dict)):
            raise ValueError("Unsafe or invalid manifest entry")
        path = attempt / name
        if path.is_symlink() or path.stat().st_size != item.get("bytes"):
            raise ValueError("Manifest byte or link mismatch: " + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256"):
            raise ValueError("Manifest hash mismatch: " + name)
    receipt = read_json(attempt / "supervisor_receipt.json")
    if receipt.get("stable_seal") is not True or receipt.get("process_group_quiescent") is not True:
        raise ValueError("Supervisor did not confirm a stable seal")
    return manifest, receipt


def declared_rows(attempt):
    frozen = read_json(attempt / "frozen.json")
    if (frozen.get("protocol") != screen.PROTOCOL or
            set(frozen.get("cases", {})) != set(screen.CASES) or
            frozen.get("stage_order") != list(screen.STAGES) or
            frozen.get("states") != [0, 1]):
        raise ValueError("Frozen declaration differs from the 32-stage protocol")
    source = attempt / "summary.json"
    if not source.is_file():
        source = attempt / "postmortem_summary.json"
    if not source.is_file():
        raise ValueError("Sealed attempt has no complete accounting summary")
    summary = read_json(source)
    expected = {(case, state, stage) for case in screen.CASES
                for state in (0, 1) for stage in screen.STAGES}
    keys = [(row.get("case"), row.get("state"), row.get("stage"))
            for row in summary.get("rows", [])]
    if len(keys) != 32 or len(set(keys)) != 32 or set(keys) != expected:
        raise ValueError("Summary does not account once for all 32 declared stages")
    return frozen, summary


def bounds(assessment):
    pair = assessment.get("bounds") if assessment else None
    if not isinstance(pair, list) or len(pair) != 2:
        return None, None, None
    try:
        lower, upper = (Fraction(value) for value in pair)
    except (TypeError, ValueError, ZeroDivisionError):
        return None, None, None
    return str(lower), str(upper), str(upper - lower)


def outward_decimal(value, digits=4, *, upper=False):
    """Exact directed decimal display of a saved rational endpoint."""
    amount = Fraction(value)
    scale = 10 ** digits
    units = -((-amount.numerator * scale) // amount.denominator) if upper else (
        amount.numerator * scale) // amount.denominator
    sign = "-" if units < 0 else ""
    magnitude = abs(units)
    return f"{sign}{magnitude // scale}.{magnitude % scale:0{digits}d}"


def stage_row(attempt, frozen, case, state, stage):
    folder = attempt / case / f"state{state}" / stage
    row = dict.fromkeys(FIELDS)
    row.update(case=case, base_timetable_group=frozen["cases"][case]["base_timetable_group"],
               state=state, stage=stage, complete_evidence=False)
    receipt_path = folder / "receipt.json"
    if receipt_path.is_file():
        row["eligibility"] = "attempted"
        try:
            receipt = read_json(receipt_path)
        except (OSError, ValueError, TypeError):
            row["outcome"] = "receipt_unreadable"
            return row
        if not isinstance(receipt, dict):
            row["outcome"] = "receipt_unreadable"
            return row
        row["wall_seconds"] = receipt.get("elapsed_seconds")
        row["on_time"] = receipt.get("on_time")
        row["outcome"] = ("timed_out" if receipt.get("hard_timeout") else
                          "failed" if receipt.get("returncode") != 0 else
                          "late" if receipt.get("on_time") is not True else "returned")
        result_path = folder / "result.json"
        if result_path.is_file():
            try:
                assessment = read_json(result_path)["assessment"]
                if not isinstance(assessment, dict):
                    raise ValueError("Assessment is not an object")
                row["native_status"] = assessment.get("status")
                row["complete_evidence"] = assessment.get("complete_evidence") is True
                row["lower_exact"], row["upper_exact"], row["gap_exact"] = bounds(assessment)
                if row["outcome"] == "returned":
                    row["outcome"] = row["native_status"] or "returned_unassessed"
                counts = assessment.get("counts", {})
                if stage.endswith("hull") and isinstance(counts, dict):
                    row["pricing_requests"] = counts.get("pricing_requests")
                    row["master_calls"] = counts.get("master_calls")
                    row["polish_steps"] = counts.get("polish_steps")
                    row["polish_wall_s"] = counts.get("polish_wall_s")
                    row["pricing_solver_wall_recorded_s"] = counts.get("pricing_wall_s")
                    row["master_solver_wall_recorded_s"] = counts.get("master_wall_s")
            except (OSError, ValueError, KeyError, TypeError):
                if row["outcome"] == "returned":
                    row["outcome"] = "partial_result"
        elif row["outcome"] == "returned":
            row["outcome"] = "returned_unassessed"
    elif (folder / "ineligible.json").is_file():
        row.update(eligibility="ineligible", outcome="ineligible")
    elif (folder / "launch.json").is_file():
        row.update(eligibility="attempted_unreceipted", outcome="interrupted_unreceipted")
    else:
        row.update(eligibility="not_reached", outcome="unstarted")
    return row


def build_report(attempt, *, analytic_energy_floor=False, repo=None):
    attempt = Path(attempt)
    manifest, supervisor = verify_manifest(attempt)
    frozen, summary = declared_rows(attempt)
    rows = [stage_row(attempt, frozen, case, state, stage)
            for case in screen.CASES for state in (0, 1) for stage in screen.STAGES]
    arms = []
    for case in screen.CASES:
        for stage in ("cold_hull", "retained_hull"):
            pair = [next(row for row in rows if row["case"] == case
                         and row["state"] == state and row["stage"] == stage)
                    for state in (0, 1)]
            times = [row["wall_seconds"] for row in pair]
            arms.append({"case": case, "arm": stage, "state0_wall_seconds": times[0],
                         "state1_wall_seconds": times[1],
                         "two_state_wall_seconds": sum(times) if all(
                             type(value) in (int, float) for value in times) else None,
                         "outcomes": [row["outcome"] for row in pair]})
    report = {"scope": "development screen descriptive report; no scientific admission",
            "attempt": str(attempt), "manifest_sha256": hashlib.sha256(
                (attempt / "MANIFEST.json").read_bytes()).hexdigest(),
            "source_commit": frozen.get("source_commit"),
            "source_hashes_unchanged": supervisor.get("source_hashes_unchanged"),
            "supervisor_returncode": supervisor.get("returncode"),
            "supervisor_integrity_ok": supervisor.get("source_hashes_unchanged") is True
                and supervisor.get("returncode") == 0,
            "supervisor_elapsed_seconds": supervisor.get("elapsed_seconds"),
            "slurm_elapsed_seconds": None,
            "accounting_source": "summary" if (attempt / "summary.json").is_file() else "postmortem_summary",
            "declared_stage_count": len(summary["rows"]), "rows": rows, "hull_arm_totals": arms,
            "limits": ["Bounds are reported native binary endpoints, not ideal exact proofs.",
                       "Elapsed stage time is end-to-end child wall time; solver wall fields include only recorded calls.",
                       "Supervisor integrity does not establish scientific validity or success of individual stages.",
                       "Source drift or nonzero supervisor exit precludes a valid-run interpretation.",
                       "No equal-quality speedup, regret, global certificate or whole-job timing is inferred."]}
    if analytic_energy_floor:
        return with_analytic_energy_floor(report, frozen, repo=repo)
    return report


def with_analytic_energy_floor(report, frozen, *, repo=None):
    """Add a separate ideal-model appendix; never change native stage rows."""
    from egglab.analytic_energy_floor import UnsupportedBaseline, evaluate

    rows = report["rows"]
    appendix = {"scope": "reviewed ideal stored-input CH baseline for reporting only",
                "native_certification": False,
                "native_bounds_status_timing_unchanged": True,
                "cases": {}}
    for case_name, declaration in frozen["cases"].items():
        if case_name not in ("public_depot15", "public_depot16"):
            appendix["cases"][case_name] = {"status": "unavailable",
                                            "reason": "no reviewed public energy-floor certificate"}
            continue
        states = {}
        for state, market in enumerate(declaration["markets"]):
            try:
                baseline = evaluate(declaration["case"], declaration["case_identity"],
                                    market, repo=repo)
            except UnsupportedBaseline as exc:
                states[str(state)] = {"status": "unavailable", "reason": str(exc),
                                      "native_certification": False}
                continue
            entry = {"status": "ideal_baseline_available", "ideal_ch_lower": baseline,
                     "native_certification": False, "conditional_mixed_enclosures": {}}
            planner = next((row for row in rows if row["case"] == case_name
                            and row["state"] == state and row["stage"] == "planner"), None)
            def admitted(row):
                return (row is not None and row.get("complete_evidence") is True
                        and row.get("eligibility") == "attempted"
                        and row.get("on_time") is True
                        and row.get("outcome") in ("certified", "bounded", "budget_exhausted")
                        and row.get("lower_exact") is not None
                        and row.get("upper_exact") is not None)
            for stage in ("cold_hull", "retained_hull"):
                hull = next((row for row in rows if row["case"] == case_name
                             and row["state"] == state and row["stage"] == stage), None)
                if report.get("supervisor_integrity_ok") is not True:
                    entry["conditional_mixed_enclosures"][stage] = {
                        "status": "unavailable", "reason": "supervisor source/process integrity not established",
                        "native_certification": False}
                    continue
                if not admitted(planner) or not admitted(hull):
                    entry["conditional_mixed_enclosures"][stage] = {
                        "status": "unavailable", "reason": "complete planner/hull native evidence missing",
                        "native_certification": False}
                    continue
                try:
                    if any(type(value) is bool for value in
                           (planner["lower_exact"], planner["upper_exact"],
                            hull["lower_exact"], hull["upper_exact"])):
                        raise ValueError("boolean native endpoint")
                    d_lower, d_upper = Fraction(planner["lower_exact"]), Fraction(planner["upper_exact"])
                    ch_lower, ch_upper = Fraction(hull["lower_exact"]), Fraction(hull["upper_exact"])
                    floor = Fraction(baseline["ch_lower_exact"])
                except (TypeError, ValueError, ZeroDivisionError):
                    entry["conditional_mixed_enclosures"][stage] = {
                        "status": "unavailable", "reason": "malformed native bound endpoint",
                        "native_certification": False}
                    continue
                combined_ch_upper = min(ch_upper, d_upper)
                if (floor > combined_ch_upper or floor > d_upper
                        or d_lower > d_upper or ch_lower > combined_ch_upper):
                    entry["conditional_mixed_enclosures"][stage] = {
                        "status": "inconsistent_unavailable",
                        "reason": "native upper below ideal floor or inverted native interval",
                        "native_certification": False}
                    continue
                entry["conditional_mixed_enclosures"][stage] = {
                    "status": "conditional_mixed_enclosure", "native_certification": False,
                    "physical_interval_exact": [str(floor), str(d_upper)],
                    "hull_interval_exact": [str(floor), str(combined_ch_upper)],
                    "gap_interval_exact": ["0", str(d_upper - floor)],
                    "native_lower_bounds_not_transferred_to_ideal_model": True,
                    "qualification": "exact ideal lower plus same-case native upper witnesses, conditional on those witnesses being feasible for the ideal model; no status or time change",
                }
            states[str(state)] = entry
        appendix["cases"][case_name] = states
    return {**report, "analytic_energy_floor_baseline": appendix}


def write_report(report, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    with (out / "stages.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(report["rows"])
    lines = ["# Computational development screen", "",
             f"Manifest SHA-256: `{report['manifest_sha256']}`. "
             f"Supervisor return code: {report['supervisor_returncode']}; "
             f"source hashes unchanged: {report['source_hashes_unchanged']}.", "",
             "| Case | State | Stage | Eligibility | Outcome | Wall s | Lower | Upper | Gap | Pricing calls | Master calls | Polish s |",
             "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    def show(key, value):
        if value is None:
            return "—"
        if key in ("lower_exact", "upper_exact", "gap_exact"):
            return f"≈{float(Fraction(value)):.6g}"
        if key in ("wall_seconds", "polish_wall_s"):
            return f"{value:.3f}"
        return str(value)
    columns = ("case", "state", "stage", "eligibility", "outcome", "wall_seconds", "lower_exact",
               "upper_exact", "gap_exact", "pricing_requests", "master_calls", "polish_wall_s")
    for row in report["rows"]:
        lines.append("| " + " | ".join(show(key, row[key]) for key in columns) + " |")
    lines.extend(["", "Two-state hull stage wall times (includes each arm's state-zero preparation):", "",
                  "| Case | Arm | State 0 s | State 1 s | Total s | Outcomes |",
                  "| --- | --- | ---: | ---: | ---: | --- |"])
    for arm in report["hull_arm_totals"]:
        lines.append("| " + " | ".join((arm["case"], arm["arm"],
            show("wall_seconds", arm["state0_wall_seconds"]),
            show("wall_seconds", arm["state1_wall_seconds"]),
            show("wall_seconds", arm["two_state_wall_seconds"]),
            ", ".join(arm["outcomes"]))) + " |")
    lines.extend(["", "Totals require both stage receipts; they are not equal-quality speedup claims.",
                  "Pricing and master solver wall times remain missing unless assessed counts record them.",
                  "Supervisor integrity describes source and process status, not success of individual stages or scientific validity.",
                  "No source-drifted or failed attempt is interpreted as a valid run.", ""])
    if "analytic_energy_floor_baseline" in report:
        lines.extend(["## Optional ideal stored-input energy-floor baseline", "",
                      "This appendix is mathematical postprocessing for the two reviewed public physical cases. "
                      "It is not a native-MIP lower bound, cache entry, solver certificate, stage outcome, or timed method.", "",
                      "| Case | State | Exact ideal CH lower | Cold-hull conditional mixed gap |",
                      "| --- | ---: | ---: | ---: |"])
        for case, states in report["analytic_energy_floor_baseline"]["cases"].items():
            if not case.startswith("public_"):
                continue
            if states.get("status") == "unavailable":
                lines.append(f"| {case} | — | unavailable: {states['reason']} | — |")
                continue
            for state, item in states.items():
                if item["status"] != "ideal_baseline_available":
                    lines.append(f"| {case} | {state} | unavailable: {item['reason']} | — |")
                    continue
                exact = item["ideal_ch_lower"]["ch_lower_exact"]
                mixed = item["conditional_mixed_enclosures"]["cold_hull"]
                gap = ("[" + outward_decimal(mixed["gap_interval_exact"][0]) + ", "
                       + outward_decimal(mixed["gap_interval_exact"][1], upper=True) + "]") if mixed["status"] == "conditional_mixed_enclosure" else mixed["status"]
                lines.append(f"| {case} | {state} | {outward_decimal(exact)} | {gap} |")
        lines.extend(["", "Conditional mixed intervals combine an exact ideal lower with existing "
                      "native upper witnesses, conditional on those witnesses being feasible for the ideal model. "
                      "All displayed endpoints round outward. "
                      "Missing or inconsistent native evidence stays unavailable. "
                      "All native stage rows, statuses, bounds and timings above are unchanged.", ""])
    (out / "comparison.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", type=Path)
    parser.add_argument("out", type=Path, help="New sibling output directory, outside the sealed attempt")
    parser.add_argument("--analytic-energy-floor", action="store_true",
                        help="Append reviewed ideal public CH floors as separate reporting evidence")
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(args.attempt.resolve()):
        parser.error("Report output must be outside the sealed attempt")
    write_report(build_report(args.attempt, analytic_energy_floor=args.analytic_energy_floor), args.out)


if __name__ == "__main__":
    main()
