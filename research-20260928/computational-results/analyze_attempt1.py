#!/usr/bin/env python3
"""Derive compact development-screen evidence from a private sealed report.

Run the reviewed computational_benchmark_report first. This script publishes no
raw event, plan, solver environment or license text; it reads only selected
scalar event wall times from files pinned by the sealed raw manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

CASES = ("synthetic_cyclic", "synthetic_multivisit", "public_depot15", "public_depot16")
STAGES = ("planner", "cold_hull", "retained_hull", "response")
CASE_LABELS = {"synthetic_cyclic": "Cyclic", "synthetic_multivisit": "Multivisit",
               "public_depot15": "Hildenbrand D15", "public_depot16": "Hildenbrand D16"}
STAGE_LABELS = {"planner": "Planner", "cold_hull": "Cold hull",
                "retained_hull": "Retained hull", "response": "Own-price"}


def selected_event_times(path):
    if not path.is_file():
        return {"pricing_solver_calls_timed": 0, "pricing_solver_wall_s": None,
                "master_solver_calls_timed": 0, "master_solver_wall_s": None}
    seen = Counter()
    times = {"pricing": [], "master": []}
    with path.open() as stream:
        for line in stream:
            item = json.loads(line)
            if item.get("event") == "pricing_result":
                kind, stats = "pricing", item.get("result", {}).get("stats", {})
            elif item.get("event") == "master_status":
                kind, stats = "master", item.get("stats", {})
            else:
                continue
            seen[kind] += 1
            value = stats.get("wall_s") if isinstance(stats, dict) else None
            if type(value) in (int, float) and math.isfinite(value) and value >= 0:
                times[kind].append(value)
    return {"pricing_solver_calls_timed": len(times["pricing"]),
            "pricing_solver_wall_s": sum(times["pricing"]) if times["pricing"] else None,
            "pricing_result_events": seen["pricing"],
            "master_solver_calls_timed": len(times["master"]),
            "master_solver_wall_s": sum(times["master"]) if times["master"] else None,
            "master_status_events": seen["master"]}


def native_case(raw):
    from egglab import native_recharge as nr
    fields = dict(raw)
    fields["trips"] = tuple(nr.Trip(**item) for item in raw["trips"])
    fields["movements"] = tuple(nr.Movement(**{**item,
        "legs": tuple(nr.Leg(**leg) for leg in item["legs"])}) for item in raw["movements"])
    fields["resources"] = tuple(nr.Resource(**item) for item in raw["resources"])
    fields["market_edges_min"] = tuple(raw["market_edges_min"])
    return nr.NativeCase(**fields)


def posthoc_two_column(attempt, manifest):
    """Exact stored-float segment minimum; no native solve or new pricing."""
    from egglab import native_hull as nh
    frozen = json.loads((attempt / "frozen.json").read_text())
    results = []
    for case_name in ("public_depot15", "public_depot16"):
        raw_case = frozen["cases"][case_name]
        case = native_case(raw_case["case"])
        for state in (0, 1):
            start = perf_counter()
            market_raw = raw_case["markets"][state]
            market = nh.Market(market_raw["name"], tuple(market_raw["a"]), tuple(market_raw["b"]))
            relative = f"{case_name}/state{state}/cold_hull/raw_result.json"
            path = attempt / relative
            if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[relative]["sha256"]:
                raise ValueError("Posthoc pool source changed: " + relative)
            saved = json.loads(path.read_text())["result"]
            columns = saved["columns"]
            if len(columns) != 2:
                raise ValueError("Expected two saved complete-fleet columns")
            policy = saved["extraction_policy"]
            projections = [nh.replay_column(case, column, policy) for column in columns]
            c0, c1 = (nh.rational(item["ops_cost"]) for item in projections)
            loads = [[nh.rational(value) for value in item["load"]] for item in projections]
            delta = [right - left for left, right in zip(*loads)]
            curvature = sum((nh.rational(b) * d * d for b, d in zip(market.b, delta)), Fraction(0))
            slope = c1 - c0 + sum(((nh.rational(a) + nh.rational(b) * base) * d
                                  for a, b, base, d in zip(market.a, market.b, loads[0], delta)), Fraction(0))
            weight = max(Fraction(0), min(Fraction(1), -slope / curvature)) if curvature else (
                Fraction(1) if slope < 0 else Fraction(0))
            replayed = nh.replay_exact_mixture(case, market, columns, [1 - weight, weight],
                                               extraction_policy=policy)
            old = Fraction(saved["mixture"]["objective_exact"])
            new = Fraction(replayed["objective_exact"])
            results.append({"case": case_name, "state": state,
                "method": "posthoc exact stored-float two-column segment minimum; not charged to baseline",
                "second_column_weight_exact": str(weight),
                "second_column_weight_approx": float(weight),
                "saved_upper_exact": str(old), "posthoc_upper_exact": str(new),
                "posthoc_upper_outward": replayed["upper"],
                "posthoc_improvement_exact": str(old - new),
                "posthoc_elapsed_seconds": perf_counter() - start,
                "posthoc_timing_scope": "raw pool read/hash, column replay, closed form and exact mixture; excludes imports, frozen load/case construction, report and figure writing",
                "physical_columns_replayed": 2,
                "new_global_pricing": False,
                "operational_fleet_schedule": False})
    return results


def derive(report_path, attempt, collection_path=None):
    report = json.loads(Path(report_path).read_text())
    attempt = Path(attempt)
    manifest_path = attempt / "MANIFEST.json"
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != report["manifest_sha256"]:
        raise ValueError("Private report and attempt manifest differ")
    manifest = json.loads(manifest_path.read_text())["files"]
    if len(report["rows"]) != 32:
        raise ValueError("Expected 32 reported stages")
    rows = []
    for original in report["rows"]:
        row = {key: original.get(key) for key in (
            "case", "base_timetable_group", "state", "stage", "eligibility", "outcome",
            "native_status", "on_time", "complete_evidence", "wall_seconds",
            "lower_exact", "upper_exact", "gap_exact", "pricing_requests",
            "master_calls", "polish_steps", "polish_wall_s")}
        if row["stage"].endswith("hull"):
            result_relative = f"{row['case']}/state{row['state']}/{row['stage']}/raw_result.json"
            if result_relative in manifest:
                raw_result = attempt / result_relative
                if hashlib.sha256(raw_result.read_bytes()).hexdigest() != manifest[result_relative]["sha256"]:
                    raise ValueError("Selected hull result changed: " + result_relative)
                native = json.loads(raw_result.read_text())["result"]
                row["stop_reason"] = native.get("reason")
                row["max_rational_bits"] = native.get("counts", {}).get("max_rational_bits")
            relative = f"{row['case']}/state{row['state']}/{row['stage']}/events.jsonl"
            if relative in manifest:
                raw = attempt / relative
                if hashlib.sha256(raw.read_bytes()).hexdigest() != manifest[relative]["sha256"]:
                    raise ValueError("Selected event file changed: " + relative)
                row.update(selected_event_times(raw))
            else:
                row.update(selected_event_times(attempt / "nonexistent"))
        rows.append(row)
    arms = report["hull_arm_totals"]
    collection = json.loads(Path(collection_path).read_text()) if collection_path else None
    slurm = collection["slurm"] if collection else {}
    elapsed = slurm.get("elapsed")
    whole_seconds = sum(int(part) * factor for part, factor in zip(elapsed.split(":"),
        (3600, 60, 1))) if elapsed else None
    return {"scope": "one DEVELOPMENT screen; numerical native bounds, not independent admission",
            "attempt_id": "computational_benchmark/20260928-attempt1",
            "raw_manifest_sha256": report["manifest_sha256"],
            "source_commit": report["source_commit"],
            "supervisor_integrity_ok": report["supervisor_integrity_ok"],
            "supervisor_elapsed_seconds": report["supervisor_elapsed_seconds"],
            "whole_slurm_elapsed_seconds": whole_seconds,
            "slurm_resources": {key: slurm.get(key) for key in (
                "state", "exit_code", "allocated_cpus", "requested_cpus",
                "requested_memory", "allocated_memory", "batch_max_rss")},
            "base_timetable_groups": ["synthetic_cyclic", "synthetic_multivisit", "hildenbrand_37"],
            "outcomes": dict(Counter(row["outcome"] for row in rows)),
            "rows": rows, "hull_arm_totals": arms,
            "posthoc_two_column_public_cold": posthoc_two_column(attempt, manifest),
            "limits": ["All 32 declared stages retained, including ineligible and failures.",
                       "Both public depots share one timetable base group.",
                       "Pricing/master solver times are sums of selected recorded calls, not full components of child wall.",
                       "Missing call timing remains null; no overhead is inferred by subtraction.",
                       "Bounds are native numerical endpoints; certified native status is not an ideal exact proof.",
                       "Two-state totals include state-zero preparation and do not imply equal-quality speedup.",
                       "Posthoc two-column convex-hull upper bounds are not one operational fleet schedule, baseline performance or fresh global lower bounds."]}


def display(number):
    return "—" if number is None else f"{number:.2f}"


def save_figure(fig, out, stem):
    for extension in ("png", "svg", "pdf"):
        path = out / f"{stem}.{extension}"
        fig.savefig(path, dpi=220)
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def figure_runtime(data, out):
    order = [(case, state) for case in CASES for state in (0, 1)]
    matrix = np.full((8, 4), np.nan)
    outcomes = [["" for _ in STAGES] for _ in order]
    for row in data["rows"]:
        i = order.index((row["case"], row["state"]))
        j = STAGES.index(row["stage"])
        if type(row["wall_seconds"]) in (int, float) and row["wall_seconds"] > 0:
            matrix[i, j] = row["wall_seconds"]
        outcomes[i][j] = row["outcome"]
    fig, ax = plt.subplots(figsize=(7.5, 4.25), layout="constrained")
    finite = matrix[np.isfinite(matrix)]
    upper = max(1., float(np.max(finite))) if len(finite) else 1.
    shown = np.ma.masked_invalid(matrix)
    image = ax.imshow(shown, cmap="Blues", norm=LogNorm(vmin=2.5, vmax=max(upper, 2.501)), aspect="auto")
    ax.set_xticks(range(4), [STAGE_LABELS[s] for s in STAGES])
    ax.set_yticks(range(8), [f"{CASE_LABELS[c]} · {'Initial' if s == 0 else 'Shifted'}" for c, s in order])
    ax.tick_params(labelsize=8)
    for i in range(8):
        for j in range(4):
            value = matrix[i, j]
            status = outcomes[i][j]
            label = f"{value:.0f}s" if np.isfinite(value) else "—"
            label += "\n" + status.replace("budget_exhausted", "budget")
            ax.text(j, i, label, ha="center", va="center", fontsize=7,
                    color="white" if np.isfinite(value) and value > upper / 3 else "#17222d")
    ax.axhline(3.5, color="#63717d", linewidth=1)
    ax.set_title("End-to-end stage wall time and recorded outcome", fontsize=10)
    fig.colorbar(image, ax=ax, label="Child wall seconds (log scale)", shrink=.9)
    save_figure(fig, out, "runtime_status")
    plt.close(fig)


def figure_public_bounds(data, out):
    stages = ("planner", "cold_hull", "retained_hull")
    colors = {"planner": "#1b547a", "cold_hull": "#ac5726", "retained_hull": "#5a6f32"}
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.0), layout="constrained")
    for i, case in enumerate(("public_depot15", "public_depot16")):
        for state in (0, 1):
            ax = axes[i, state]
            for j, stage in enumerate(stages):
                row = next(r for r in data["rows"] if r["case"] == case and
                           r["state"] == state and r["stage"] == stage)
                if row["lower_exact"] is None or row["upper_exact"] is None:
                    ax.text(.02, j, "missing / " + row["outcome"], transform=ax.get_yaxis_transform(),
                            va="center", fontsize=7)
                    continue
                lower, upper = float(Fraction(row["lower_exact"])), float(Fraction(row["upper_exact"]))
                ax.plot([lower, upper], [j, j], color=colors[stage], linewidth=2)
                ax.plot([lower, upper], [j, j], "|", color=colors[stage], markersize=9)
                # Endpoints denote an enclosure; no midpoint estimate is implied.
            ax.set_yticks(range(3), [STAGE_LABELS[s] for s in stages], fontsize=8)
            ax.set_ylim(2.5, -.5)
            ax.set_title(f"{CASE_LABELS[case]} · {'Initial' if state == 0 else 'Shifted'}", fontsize=9)
            ax.grid(axis="x", alpha=.2)
            ax.tick_params(axis="x", labelsize=8)
            ax.set_xlabel("Numerical objective enclosure", fontsize=8)
            ax.set_xlim(330, 570)
    save_figure(fig, out, "public_bounds")
    plt.close(fig)


def write(data, attempt, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "analysis.json").write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")
    public_hulls = [r for r in data["rows"] if r["case"].startswith("public_")
                    and r["stage"].endswith("hull") and r["outcome"] != "ineligible"]
    public_pricing = [r["pricing_solver_wall_s"] for r in public_hulls
                      if r.get("pricing_solver_wall_s") is not None]
    lines = ["# First computational DEVELOPMENT screen", "",
             f"All 32 stages accounted: {data['outcomes']}. The two public depots share one base timetable.",
             f"The {len(public_hulls)} launched public hull stages used one master and two pricing requests each; "
             f"recorded native pricing wall was {min(public_pricing):.2f}–{max(public_pricing):.2f} s "
             "of roughly 184 s child wall, while polishing took under 0.006 s per stage. "
             "Native pricing is the measured runtime bottleneck. Separately, omitting a final master "
             "leaves useful mixture improvements unrealized; the master itself is inexpensive. Shifted retained public stages were ineligible "
             "because initial retained bounds were not certified. The multivisit shifted cold hull instead "
             "stopped at the rational projected-bit limit; that is a separate arithmetic issue.",
             "Posthoc two-column replay below can improve a saved feasible upper bound, but its time and "
             "quality are not credited to the frozen run. A prospective change could reserve time for a "
             "final restricted master and test replayed feasible-pool reuse; native pricing warm starts "
             "also merit matched development comparison. No change is claimed effective yet.", "",
             f"Whole Slurm elapsed: {display(data['whole_slurm_elapsed_seconds'])} s; "
             f"supervisor elapsed: {display(data['supervisor_elapsed_seconds'])} s. "
             f"Raw manifest SHA-256: `{data['raw_manifest_sha256']}`; source `{data['source_commit']}`.", "",
             "| Case | Market | Stage | Outcome | Child wall s | Lower | Upper | Pricing | Master | Polish s |",
             "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in data["rows"]:
        label = "Initial" if row["state"] == 0 else "Shifted"
        lower = "—" if row["lower_exact"] is None else f"≈{float(Fraction(row['lower_exact'])):.4f}"
        upper = "—" if row["upper_exact"] is None else f"≈{float(Fraction(row['upper_exact'])):.4f}"
        lines.append(f"| {CASE_LABELS[row['case']]} | {label} | {STAGE_LABELS[row['stage']]} | "
                     f"{row['outcome']} | {display(row['wall_seconds'])} | {lower} | {upper} | "
                     f"{row['pricing_requests'] if row['pricing_requests'] is not None else '—'} | "
                     f"{row['master_calls'] if row['master_calls'] is not None else '—'} | "
                     f"{'—' if row['polish_wall_s'] is None else f'{row['polish_wall_s']:.3f}'} |")
    lines.extend(["", "Two-state hull times include each arm's initial state:", "",
                  "| Case | Arm | Initial s | Shifted s | Total s | Outcomes |",
                  "| --- | --- | ---: | ---: | ---: | --- |"])
    for arm in data["hull_arm_totals"]:
        lines.append(f"| {CASE_LABELS[arm['case']]} | {STAGE_LABELS[arm['arm']]} | "
                     f"{display(arm['state0_wall_seconds'])} | {display(arm['state1_wall_seconds'])} | "
                     f"{display(arm['two_state_wall_seconds'])} | {', '.join(arm['outcomes'])} |")
    lines.extend(["", "Posthoc exact stored-float two-column public cold-pool replay (outside the baseline budget):", "",
                  "| Case | Market | Saved upper | Posthoc upper | Improvement | Second-column weight | Replay s |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
    for item in data["posthoc_two_column_public_cold"]:
        lines.append(f"| {CASE_LABELS[item['case']]} | {'Initial' if item['state'] == 0 else 'Shifted'} | "
                     f"≈{float(Fraction(item['saved_upper_exact'])):.4f} | "
                     f"≈{float(Fraction(item['posthoc_upper_exact'])):.4f} | "
                     f"≈{float(Fraction(item['posthoc_improvement_exact'])):.4f} | "
                     f"≈{item['second_column_weight_approx']:.4f} | "
                     f"{item['posthoc_elapsed_seconds']:.3f} |")
    lines.extend(["", "Posthoc timing covers raw pool read/hash, column replay, closed form and exact mixture; "
                  "it excludes imports, frozen-case construction and report/figure writing. The mixture is "
                  "a convex-hull object, not one operational fleet schedule.",
                  "The figures show descriptive native numerical evidence, not exact ideal-model bounds. "
                  "Missing component timing is unknown, not zero. Outcomes and quality must be matched before "
                  "any retained-versus-cold speed claim.", ""])
    (out / "ANALYSIS.md").write_text("\n".join(lines))
    manifest = json.loads((Path(attempt) / "MANIFEST.json").read_text())["files"]
    private_logs = [{"path": name, **item} for name, item in manifest.items()
                    if Path(name).name.endswith(("stdout.txt", "stderr.txt"))]
    (out / "OMISSIONS.json").write_text(json.dumps({
        "raw_manifest_sha256": data["raw_manifest_sha256"],
        "policy": "Derived analysis omits raw logs; separate scientific_evidence.zip carries only files whitelisted by PUBLIC_EVIDENCE_MANIFEST.json.",
        "scientific_evidence_archive": "scientific_evidence.zip",
        "scientific_evidence_manifest": "PUBLIC_EVIDENCE_MANIFEST.json",
        "omitted_private_logs": private_logs,
        "all_other_raw_files_not_duplicated_in_analysis": True}, indent=2, sort_keys=True) + "\n")
    figure_runtime(data, out)
    figure_public_bounds(data, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--collection", type=Path, help="Verified private collection receipt for Slurm scalars")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    write(derive(args.report, args.attempt, args.collection), args.attempt, args.out)


if __name__ == "__main__":
    main()
