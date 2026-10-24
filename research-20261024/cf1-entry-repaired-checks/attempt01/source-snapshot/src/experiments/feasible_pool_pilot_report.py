"""Read-only, manifest-checked descriptive report for the feasible-pool pilot."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

from experiments import feasible_pool_pilot as pilot

METHOD = {"legacy_cold_hull": "Legacy cold", "reserve_cold_hull": "Reserve cold",
          "reserve_feasible_hull": "Reserve + feasible pool"}
ROW_FIELDS = ("case", "base_timetable_group", "state", "arm", "method", "outcome",
              "native_status", "complete_evidence", "on_time", "wall_s", "lower_exact",
              "upper_exact", "gap_exact", "pricing_requests", "pricing_results",
              "pricing_solver_wall_recorded_s", "pricing_solver_wall_complete", "master_calls",
              "master_statuses", "master_solver_wall_recorded_s", "master_solver_wall_complete",
              "polish_steps", "polish_wall_s", "polish_finish_recorded_s", "imported_columns",
              "imported_in_first_master", "new_columns_added", "added_columns_reached_later_master",
              "added_columns_unprocessed", "fresh_global_bounds", "reserve_stop_events",
              "stop_reason", "last_restricted_pool_gap_exact", "events_sha256")


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(attempt):
    attempt = Path(attempt)
    manifest_path = attempt / "MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("No stable manifest")
    manifest = read(manifest_path)
    if manifest.get("protocol") != pilot.PROTOCOL or not isinstance(manifest.get("files"), dict):
        raise ValueError("Wrong manifest protocol or file list")
    files = manifest["files"]
    actual = {p.relative_to(attempt).as_posix() for p in attempt.rglob("*") if p.is_file()}
    if actual != set(files) | {"MANIFEST.json"}:
        raise ValueError("Manifest does not cover exactly the sealed files")
    for name, item in files.items():
        relative = PurePosixPath(name)
        path = attempt / name
        if (relative.is_absolute() or ".." in relative.parts or not isinstance(item, dict)
                or path.is_symlink() or path.stat().st_size != item.get("bytes")
                or sha(path) != item.get("sha256")):
            raise ValueError("Unsafe, missing, or mismatched sealed file: " + name)
    supervisor = read(attempt / "supervisor_receipt.json")
    if supervisor.get("stable_seal") is not True or supervisor.get("process_group_quiescent") is not True:
        raise ValueError("Unstable process-group seal")
    frozen = read(attempt / "frozen.json")
    if (frozen.get("protocol") != pilot.PROTOCOL or set(frozen.get("cases", {})) != set(pilot.CASES)
            or frozen.get("stage_order") != list(pilot.ARMS) or frozen.get("states") != list(pilot.STATES)):
        raise ValueError("Frozen design differs from 24-cell declaration")
    summary_name = "summary.json" if (attempt / "summary.json").is_file() else "postmortem_summary.json"
    summary = read(attempt / summary_name)
    expected = {(case, state, arm) for case in pilot.CASES for state in pilot.STATES for arm in pilot.ARMS}
    keys = [(r.get("case"), r.get("state"), r.get("stage")) for r in summary.get("rows", [])]
    if len(keys) != 24 or len(set(keys)) != 24 or set(keys) != expected:
        raise ValueError("Summary does not account exactly once for all 24 cells")
    return manifest, frozen, supervisor, summary_name


def valid_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def sum_recorded(values):
    return sum(v for v in values if valid_number(v)) if any(valid_number(v) for v in values) else None


def extract_trace(events):
    """Small scalar trace; never copy plans, prices, raw variables or JSONL."""
    pricing, added, master_starts = [], [], []
    native_statuses, master_statuses, polish = [], [], []
    imported = None
    last_pool_gap, reserve_stops, global_bounds = None, 0, 0
    for pos, event in enumerate(events):
        kind = event.get("event")
        if kind == "state_start":
            imported = list(event.get("imported_column_keys", []))
        elif kind == "pricing_request":
            pricing.append({"call": event.get("call"), "seed": event.get("seed"),
                            "allowance_s": event.get("pricing_wall_allowance_seconds"),
                            "remaining_total_s": event.get("remaining_total_seconds"),
                            "reserve_s": event.get("reserve_seconds"), "native_status": None,
                            "native_incumbent": None, "native_lower_bound": None,
                            "native_solver_wall_s": None, "global_lower_exact": None,
                            "candidate_key": None})
        elif kind == "pricing_result":
            call = event.get("call")
            target = next((p for p in pricing if p["call"] == call), None)
            if target is not None:
                result = event.get("result", {})
                stats = result.get("stats", {})
                target.update(native_status=stats.get("status"),
                              native_incumbent=stats.get("incumbent"),
                              native_lower_bound=stats.get("lower_bound"),
                              native_solver_wall_s=stats.get("wall_s"),
                              pricing_status=result.get("status"))
        elif kind == "global_bound":
            global_bounds += 1
            target = next((p for p in pricing if p["call"] == event.get("call")), None)
            if target is not None:
                target.update(global_lower_exact=event.get("certificate", {}).get("lower_exact"),
                              candidate_key=event.get("column", {}).get("key"))
        elif kind == "column_added":
            added.append((pos, event.get("key")))
        elif kind == "master_start":
            master_starts.append((pos, event.get("call"), set(event.get("column_keys", []))))
        elif kind == "master_status":
            stats = event.get("stats", {})
            master_statuses.append({"call": event.get("call"), "native_status": stats.get("status"),
                                    "native_solver_wall_s": stats.get("wall_s")})
        elif kind == "pool_polish_finish":
            polish.append(event.get("elapsed_s"))
        elif kind == "pricing_reserve_stop":
            reserve_stops += 1
        elif kind == "master_replay":
            last_pool_gap = event.get("pool", {}).get("pool_gap_exact")
    reached = sum(any(later > pos and key in keys for later, _, keys in master_starts)
                  for pos, key in added)
    first_master = master_starts[0][2] if master_starts else set()
    return {"pricing_trace": pricing, "master_trace": master_statuses,
            "pricing_results": sum(p.get("pricing_status") is not None for p in pricing),
            "pricing_solver_wall_recorded_s": sum_recorded([p["native_solver_wall_s"] for p in pricing]),
            "pricing_solver_wall_complete": all(valid_number(p["native_solver_wall_s"]) for p in pricing),
            "master_statuses": len(master_statuses),
            "master_solver_wall_recorded_s": sum_recorded([m["native_solver_wall_s"] for m in master_statuses]),
            "master_solver_wall_complete": all(valid_number(m["native_solver_wall_s"]) for m in master_statuses),
            "polish_finish_recorded_s": sum_recorded(polish),
            "imported_columns": len(imported) if imported is not None else None,
            "imported_in_first_master": len(set(imported) & first_master) if imported is not None and master_starts else None,
            "new_columns_added": len(added), "added_columns_reached_later_master": reached,
            "added_columns_unprocessed": len(added) - reached,
            "fresh_global_bounds": global_bounds, "reserve_stop_events": reserve_stops,
            "last_restricted_pool_gap_exact": last_pool_gap}


def cell(attempt, frozen, manifest, case, state, arm):
    folder = attempt / case / f"state{state}" / arm
    row = dict.fromkeys(ROW_FIELDS)
    row.update(case=case, base_timetable_group=frozen["cases"][case]["base_timetable_group"],
               state=state, arm=arm, method=METHOD[arm], complete_evidence=False)
    receipt_file, result_file, raw_file = (folder / name for name in ("receipt.json", "result.json", "raw_result.json"))
    if receipt_file.is_file():
        try:
            receipt = read(receipt_file)
            row["on_time"], row["wall_s"] = receipt.get("on_time"), receipt.get("elapsed_seconds")
            row["outcome"] = ("timed_out" if receipt.get("hard_timeout") else
                              "failed" if receipt.get("returncode") != 0 else
                              "late" if receipt.get("on_time") is not True else "returned")
        except (OSError, ValueError, TypeError, AttributeError):
            row["outcome"] = "receipt_unreadable"
    elif (folder / "ineligible.json").is_file():
        row["outcome"] = "ineligible"
    elif (folder / "launch.json").is_file():
        row["outcome"] = "interrupted_unreceipted"
    else:
        row["outcome"] = "unstarted"
    if result_file.is_file():
        try:
            assessment = read(result_file)["assessment"]
            row["complete_evidence"] = assessment.get("complete_evidence") is True
            row["native_status"] = assessment.get("status")
            if row["outcome"] == "returned":
                row["outcome"] = row["native_status"] or "returned_unassessed"
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            if row["outcome"] == "returned":
                row["outcome"] = "partial_result"
    elif row["outcome"] == "returned":
        row["outcome"] = "returned_unassessed"
    if raw_file.is_file():
        try:
            raw = read(raw_file)["result"]
            row["stop_reason"] = raw.get("reason")
            cert, mix, counts = raw.get("lower_certificate", {}), raw.get("mixture", {}), raw.get("counts", {})
            lo, hi = cert.get("lower_exact"), mix.get("objective_exact")
            if lo is not None and hi is not None:
                lower, upper = Fraction(lo), Fraction(hi)
                row.update(lower_exact=str(lower), upper_exact=str(upper), gap_exact=str(upper-lower))
            row.update(pricing_requests=counts.get("pricing_requests"), master_calls=counts.get("master_calls"),
                       polish_steps=counts.get("polish_steps"), polish_wall_s=counts.get("polish_wall_s"))
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ZeroDivisionError):
            row["raw_read_error"] = True
    event_file = folder / "events.jsonl"
    if event_file.is_file():
        relative = event_file.relative_to(attempt).as_posix()
        row["events_sha256"] = manifest["files"][relative]["sha256"]
        try:
            events = [json.loads(line) for line in event_file.read_text().splitlines()]
            trace = extract_trace(events)
            row.update({key: val for key, val in trace.items() if key not in ("pricing_trace", "master_trace")})
            row["pricing_solver_wall_complete"] &= row["pricing_results"] == row["pricing_requests"]
            row["master_solver_wall_complete"] &= row["master_statuses"] == row["master_calls"]
            return row, {"case": case, "state": state, "arm": arm,
                         "events_sha256": row["events_sha256"], "pricing": trace["pricing_trace"],
                         "master": trace["master_trace"]}
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            row["events_read_error"] = True
    return row, {"case": case, "state": state, "arm": arm, "events_sha256": row["events_sha256"],
                 "pricing": [], "master": []}


def build(attempt):
    attempt = Path(attempt)
    manifest, frozen, supervisor, summary_name = verify(attempt)
    pairs = [cell(attempt, frozen, manifest, case, state, arm)
             for case in pilot.CASES for state in pilot.STATES for arm in pilot.ARMS]
    rows, traces = [p[0] for p in pairs], [p[1] for p in pairs]
    index = {(r["case"], r["state"], r["arm"]): r for r in rows}
    totals = []
    for case in pilot.CASES:
        for arm in pilot.ARMS:
            zero, one = (index[(case, state, arm)] for state in pilot.STATES)
            times = (zero["wall_s"], one["wall_s"])
            totals.append({"case": case, "base_timetable_group": zero["base_timetable_group"],
                           "arm": arm, "method": METHOD[arm], "state0_s": times[0], "state1_s": times[1],
                           "paid_two_state_s": sum(times) if all(valid_number(t) for t in times) else None,
                           "state0_outcome": zero["outcome"], "state1_outcome": one["outcome"]})
    comparisons = []
    for case in pilot.CASES:
        for state, left_arm, right_arm, label in (
                *((s, "legacy_cold_hull", "reserve_cold_hull", "reserve effect") for s in pilot.STATES),
                (1, "reserve_cold_hull", "reserve_feasible_hull", "reuse effect")):
            left, right = index[(case, state, left_arm)], index[(case, state, right_arm)]
            delta = lambda key: (float(Fraction(right[key])-Fraction(left[key]))
                                 if left[key] is not None and right[key] is not None else None)
            comparisons.append({"case": case, "state": state, "comparison": label,
                                "left": METHOD[left_arm], "right": METHOD[right_arm],
                                "left_outcome": left["outcome"], "right_outcome": right["outcome"],
                                "right_minus_left_wall_s": delta("wall_s"),
                                "right_minus_left_lower": delta("lower_exact"),
                                "right_minus_left_upper": delta("upper_exact")})
    wrapper = attempt.with_name(attempt.name + ".slurm_wrapper_receipt.json")
    if not wrapper.is_file():
        wrapper = attempt.parents[2] / (attempt.name + ".slurm_wrapper_receipt.json")
    wrapper_data = read(wrapper) if wrapper.is_file() else None
    return {"scope": "single deterministic development pilot; descriptive only",
            "manifest_sha256": sha(attempt / "MANIFEST.json"), "frozen_sha256": sha(attempt / "frozen.json"),
            "source_commit": frozen.get("source_commit"), "accounting_source": summary_name,
            "supervisor_returncode": supervisor.get("returncode"),
            "source_hashes_unchanged": supervisor.get("source_hashes_unchanged"),
            "supervisor_elapsed_s": supervisor.get("elapsed_seconds"),
            "wrapper": wrapper_data, "rows": rows, "pricing_traces": traces,
            "paid_totals": totals, "paired_comparisons": comparisons,
            "limitations": ["Native global lower bounds and feasible mixture uppers form an enclosure; a restricted-pool gap is not the global gap.",
                            "Mixtures of complete fleet plans are convex hull evidence, not one executable schedule.",
                            "Solver wall times cover only recorded native calls; missing component time is not inferred.",
                            "Both public depots are one base timetable group; this pilot does not support general scalability or equal-quality speedup claims."]}


def short(value, decimals=2):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float, Fraction)) or (isinstance(value, str) and "/" in value):
        try:
            return f"{float(Fraction(value)):.{decimals}f}"
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    return str(value)


def outward(value, lower):
    if value is None:
        return "—"
    cents = Fraction(value) * 100
    rounded = cents.numerator // cents.denominator if lower else -((-cents.numerator) // cents.denominator)
    return f"{rounded / 100:.2f}"


def write_csv(path, rows, fields):
    with Path(path).open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def normalize_svg(path):
    path = Path(path)
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def plot(report, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.fonttype": "none"})
    colors = ("#2b5c7d", "#c16d33", "#4b8768")
    cases = list(pilot.CASES)
    labels = ["Cyclic", "Multivisit", "Depot 15", "Depot 16"]
    totals = {(r["case"], r["arm"]): r for r in report["paid_totals"]}
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.7), constrained_layout=True)
    for ax, chosen, titles in ((axes[0], cases[:2], labels[:2]), (axes[1], cases[2:], labels[2:])):
        available = [totals[(case, arm)]["paid_two_state_s"] for case in chosen for arm in pilot.ARMS
                     if valid_number(totals[(case, arm)]["paid_two_state_s"])]
        maximum = max(available, default=1)
        for i, arm in enumerate(pilot.ARMS):
            xs = [k + (i-1)*.24 for k in range(2)]
            t0 = [totals[(case, arm)]["state0_s"] for case in chosen]
            t1 = [totals[(case, arm)]["state1_s"] for case in chosen]
            named = False
            for x, a, b in zip(xs, t0, t1):
                if valid_number(a) and valid_number(b):
                    ax.bar(x, a, width=.21, color=colors[i], alpha=.5)
                    ax.bar(x, b, width=.21, bottom=a, color=colors[i],
                           label=METHOD[arm] if not named else None)
                    named = True
                    ax.text(x, a+b+maximum*.013, f"{a+b:.2f}", ha="center", va="bottom", fontsize=7)
                else:
                    ax.text(x, maximum*.04, "n/a", ha="center", va="bottom", rotation=90,
                            fontsize=7, color=colors[i])
        ax.set_xticks(range(2), titles)
        ax.set_ylim(0, maximum*1.17)
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Paid two-state child wall time (s)")
    axes[0].set_title("Synthetic cases")
    axes[1].set_title("Public depot variants")
    handles, legend_labels = axes[1].get_legend_handles_labels()
    if not handles:
        handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, ncol=3, loc="lower center", bbox_to_anchor=(.5, -.07),
               frameon=False, fontsize=8)
    fig.suptitle("Both state runs counted; lighter segment is state 0", fontsize=11)
    for ext in ("svg", "png", "pdf"):
        path = out / f"paid_two_state_time.{ext}"
        fig.savefig(path, dpi=220, bbox_inches="tight",
                    metadata={"Creator": "feasible_pool_pilot_report"})
        if ext == "svg":
            normalize_svg(path)
    plt.close(fig)

    lookup = {(r["case"], r["state"], r["arm"]): r for r in report["rows"]}
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.65), sharey=True, constrained_layout=True)
    for ax, case, title in zip(axes, cases[2:], labels[2:]):
        for i, arm in enumerate(pilot.ARMS):
            row = lookup[(case, 1, arm)]
            if row["lower_exact"] is None or row["upper_exact"] is None:
                continue
            lower, upper = float(Fraction(row["lower_exact"])), float(Fraction(row["upper_exact"]))
            ax.vlines(i, lower, upper, color=colors[i], lw=6)
            ax.plot(i, lower, marker="_", markersize=12, color="#172b3b")
            ax.plot(i, upper, marker="_", markersize=12, color="#172b3b")
            ax.text(i, upper+4, outward(row["upper_exact"], False), ha="center", va="bottom", fontsize=7)
            ax.text(i, lower-4, outward(row["lower_exact"], True), ha="center", va="top", fontsize=7)
        ax.set_xticks(range(3), ["Legacy\ncold", "Reserve\ncold", "Reserve +\npool"])
        ax.set_xlim(-.5, 2.5)
        ax.set_title(f"{title}: state 1")
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Objective: global lower to feasible upper")
    axes[0].set_ylim(275, 590)
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    for ext in ("svg", "png", "pdf"):
        path = out / f"public_state1_bounds.{ext}"
        fig.savefig(path, dpi=220, metadata={"Creator": "feasible_pool_pilot_report"})
        if ext == "svg":
            normalize_svg(path)
    plt.close(fig)


def write(report, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    write_csv(out / "cells.csv", report["rows"], ROW_FIELDS)
    write_csv(out / "paid_totals.csv", report["paid_totals"], tuple(report["paid_totals"][0]))
    write_csv(out / "paired_comparisons.csv", report["paired_comparisons"], tuple(report["paired_comparisons"][0]))
    lines = ["# Feasible-pool pilot: descriptive results", "",
             f"Development-only sealed attempt; manifest SHA-256 `{report['manifest_sha256']}`; source commit `{report['source_commit']}`.",
             f"All 24 cells are accounted for. Supervisor return code {report['supervisor_returncode']}; source hashes unchanged: {report['source_hashes_unchanged']}.",
             "", "The reserve enabled a second master in all four public reserve-cold cells, while the legacy public cells ended before a second master. The reserve stop was recorded in all four reserve-cold public cells.",
             "State-1 feasible-pool reuse closed the global enclosure on the multivisit case. On both public depot variants it improved the feasible upper but weakened the fresh global lower; neither public state-1 reuse cell certified.",
             "The public variants share one base timetable group. One deterministic development run gives paired descriptions, not a general speedup or scalability estimate.", "",
             "## All declared cells", "",
             "| Case | State | Method | Outcome | Wall s | Global lower | Feasible upper | Pricing | Master | Polish s | Stop reason |",
             "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for r in report["rows"]:
        lines.append("| " + " | ".join((r["case"], str(r["state"]), r["method"], str(r["outcome"]),
                     short(r["wall_s"]), outward(r["lower_exact"], True), outward(r["upper_exact"], False),
                     short(r["pricing_requests"], 0), short(r["master_calls"], 0),
                     short(r["polish_wall_s"]), r["stop_reason"] or "—")) + " |")
    lines.extend(["", "## Paid two-state time", "",
                  "Both state receipts are required; state 0 is never free.", "",
                  "| Case | Method | State 0 s | State 1 s | Total s | Outcomes |",
                  "| --- | --- | ---: | ---: | ---: | --- |"])
    for t in report["paid_totals"]:
        lines.append("| " + " | ".join((t["case"], t["method"], short(t["state0_s"]),
                     short(t["state1_s"]), short(t["paid_two_state_s"]),
                     t["state0_outcome"] + ", " + t["state1_outcome"])) + " |")
    lines.extend(["", "## Reading the bounds and timings", "",
                  "The lower endpoint comes from fresh target-market native pricing; the upper endpoint is a feasible convex mixture of complete fleet plans. The last restricted-pool gap in `cells.csv` concerns only that finite column pool. A mixture is not one executable fleet schedule.",
                  "Displayed lower endpoints round down and upper endpoints round up to two decimals. Unrounded values in `cells.csv` and `report.json` determine gaps and certification.",
                  "`report.json` retains compact pricing-call native status, incumbent, lower bound, native solver wall time, global-bound lower, candidate key and the sealed events SHA for each cell. It also records master native wall times, added columns reaching later masters, reserve-stop events, and stop reasons. Missing component times stay missing; native solver sums are not end-to-end stage time. Import replay cost has no independent timer in this run.",
                  "In public state 1, legacy cold obtained a second priced fleet column but did not reach a second master before the wall stop. Reserve cold reached two masters, with both priced columns processed, then hit the explicit reserve guard. Feasible reuse imported two state-0 columns into its first master, priced one fresh target-market column, processed it in a second master, and then hit the projected rational bit-size limit. Recorded public pricing native wall time dominates (about 160–172 s per state-1 cell); master native solves are below 0.01 s, while feasible-reuse polishing totals about 5.75–6.06 s. These recorded components do not measure import replay separately.",
                  "The last completed restricted-pool gap can be zero while the global enclosure remains open: the finite pool excludes unpriced fleet plans. The feasible-pool public upper endpoints improved by 56.43 and 41.24 relative to reserve cold, but its fresh global lower endpoints weakened by 23.59 and 48.43. Thus those cells do not establish tighter global gaps.",
                  "The public feasible-pool state-1 stops were projected rational bit-size limits; reserve engagement there was not observed. The reserve-cold public stops were explicit reserve guards. No equal-quality time target was specified, so the time differences are descriptive and no speedup is claimed.", "",
                  "A [separate posthoc oracle-bound diagnostic](../posthoc_oracle_bound/README.md) recomputes target-market lower bounds from same-physical-case state-0 pricing evidence. It is a lead for a prospectively controlled cache baseline; it is not part of these timed arms or a new optimizer solve.", "",
                  "## Reproduction", "",
                  "Run from the repository root with a new output directory and the complete sealed private attempt, including every `events.jsonl` and `MANIFEST.json`. The curated public evidence subset omits files required by the manifest check.", "",
                  "```sh", "PYTHONPATH=src python -m experiments.feasible_pool_pilot_report <complete-private-attempt> <new-output-dir>", "```", "",
                  "![Paid two-state wall time](paid_two_state_time.svg)", "",
                  "![Public state-1 global enclosures](public_state1_bounds.svg)", ""])
    (out / "README.md").write_text("\n".join(lines))
    plot(report, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.out.resolve().is_relative_to(args.attempt.resolve()):
        parser.error("Output must be outside the sealed attempt")
    write(build(args.attempt), args.out)


if __name__ == "__main__":
    main()
