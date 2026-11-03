"""Read-only scalar report from one complete sealed solver-baseline comparison."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

from experiments import solver_baseline_comparison as run

METHOD = {"reserve_cold_hull": "Reserve cold", "reserve_feasible_hull": "Reserve + pool",
          "qp_feasible_hull": "QP + pool", "qp_cache_feasible_hull": "QP + pool + bound cache"}
COLORS = {"reserve_cold_hull": "#27577a", "reserve_feasible_hull": "#b56c34",
          "qp_feasible_hull": "#6b5a9d", "qp_cache_feasible_hull": "#36836c"}
FIELDS = ("case", "base_timetable_group", "state", "arm", "method", "outcome", "native_status",
          "complete_evidence", "on_time", "child_wall_s", "parent_admission_s", "source_check_s",
          "lower_exact", "upper_exact", "gap_exact", "lower_origin", "fresh_pricing_successes",
          "fresh_lower_exact", "selected_minus_fresh_lower", "cached_bound_candidates",
          "pricing_requests", "pricing_results", "global_bounds", "pricing_native_wall_recorded_s",
          "pricing_native_wall_complete", "master_calls", "native_master_results",
          "native_master_wall_recorded_s", "qp_proposal_calls", "qp_non_success",
          "qp_proposal_wall_s", "qp_replay_wall_s", "qp_result_count", "qp_replay_count",
          "last_pool_gap_exact", "pool_qualified_last", "polish_steps", "polish_wall_s",
          "max_rational_bits", "imported_columns", "imported_in_first_master",
          "new_columns_added", "added_columns_reached_master", "reserve_stops", "stop_reason",
          "last_native_status", "last_native_incumbent", "last_native_call",
          "exception_type", "exception_message", "exception_elapsed_s", "events_sha256")


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def number_sum(values):
    found = [v for v in values if finite(v)]
    return sum(found) if found else None


def verify(attempt):
    attempt = Path(attempt)
    manifest_path = attempt / "MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("Missing stable manifest")
    manifest = read(manifest_path)
    if manifest.get("protocol") != run.PROTOCOL or not isinstance(manifest.get("files"), dict):
        raise ValueError("Wrong sealed manifest")
    files = manifest["files"]
    actual = {p.relative_to(attempt).as_posix() for p in attempt.rglob("*") if p.is_file()}
    if actual != set(files) | {"MANIFEST.json"}:
        raise ValueError("Sealed file list differs")
    for name, item in files.items():
        path = attempt / name
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or path.is_symlink()
                or not isinstance(item, dict) or path.stat().st_size != item.get("bytes")
                or sha(path) != item.get("sha256")):
            raise ValueError("Sealed file differs: " + name)
    frozen = read(attempt / "frozen.json")
    supervisor = read(attempt / "supervisor_receipt.json")
    summary = read(attempt / "summary.json")
    expected = {(case, state, arm) for case in run.CASES for arm in run.ARMS for state in run.STATES}
    keys = [(r.get("case"), r.get("state"), r.get("stage")) for r in summary.get("rows", [])]
    if (frozen.get("protocol") != run.PROTOCOL or frozen.get("stage_order") != list(run.ARMS)
            or frozen.get("within_arm_order") != list(run.STATES)
            or set(frozen.get("cases", {})) != set(run.CASES)
            or len(keys) != 32 or len(set(keys)) != 32 or set(keys) != expected
            or summary.get("all_declared_cells_accounted") is not True
            or supervisor.get("stable_seal") is not True
            or supervisor.get("process_group_quiescent") is not True
            or supervisor.get("source_hashes_unchanged") is not True):
        raise ValueError("Frozen design, accounting, or quiescence differs")
    return manifest, frozen, supervisor, summary


def trace(events):
    """Retain compact numerical/status scalars, never plans or raw variables."""
    pricing, master, qp = [], [], []
    starts, added = [], []
    imported = None
    last_pool, last_qualified = None, None
    reserve_stops = 0
    last_native_status, last_native_incumbent, last_native_call = None, None, None
    for pos, event in enumerate(events):
        kind = event.get("event")
        if kind == "state_start":
            imported = list(event.get("imported_column_keys", []))
        elif kind == "pricing_request":
            pricing.append({"call": event.get("call"), "seed": event.get("seed"),
                            "allowance_s": event.get("pricing_wall_allowance_seconds"),
                            "remaining_total_s": event.get("remaining_total_seconds"),
                            "reserve_s": event.get("reserve_seconds"), "status": None,
                            "incumbent": None, "physical_lower_bound": None,
                            "native_wall_s": None, "global_lower_exact": None,
                            "candidate_key": None})
        elif kind == "pricing_result":
            item = next((x for x in pricing if x["call"] == event.get("call")), None)
            if item is not None:
                raw = event.get("result", {})
                stats = raw.get("stats", {})
                item.update(status=raw.get("status"), incumbent=stats.get("incumbent"),
                            physical_lower_bound=stats.get("lower_bound"),
                            native_status=stats.get("status"), native_wall_s=stats.get("wall_s"))
        elif kind == "pricing_native" and event.get("detail", {}).get("event") == "native_status":
            last_native_call = event.get("call")
            last_native_status = event["detail"].get("stats", {}).get("status")
            last_native_incumbent = event["detail"].get("stats", {}).get("incumbent")
        elif kind == "global_bound":
            item = next((x for x in pricing if x["call"] == event.get("call")), None)
            if item is not None:
                item.update(global_lower_exact=event.get("certificate", {}).get("lower_exact"),
                            candidate_key=event.get("column", {}).get("key"))
        elif kind == "master_start":
            starts.append((pos, set(event.get("column_keys", []))))
        elif kind == "master_status":
            stats = event.get("stats", {})
            master.append({"call": event.get("call"), "status": stats.get("status"),
                           "native_wall_s": stats.get("wall_s")})
        elif kind == "qp_proposal_result":
            prop = event.get("proposal", {})
            qp.append({"call": event.get("call"), "success": prop.get("success"),
                       "solver_status": prop.get("solver_status"),
                       "numeric_s": prop.get("numeric_seconds"),
                       "rounding_s": prop.get("rounding_seconds"),
                       "proposal_wall_s": event.get("proposal_wall_s"),
                       "replay_wall_s": None, "pool_gap_exact": None,
                       "pool_qualified": None})
        elif kind == "qp_candidate_replay":
            item = next((x for x in qp if x["call"] == event.get("call")), None)
            if item is not None:
                item.update(replay_wall_s=event.get("replay_wall_s"),
                            pool_gap_exact=event.get("pool", {}).get("pool_gap_exact"),
                            pool_qualified=event.get("pool_qualified"))
            last_pool = event.get("pool", {}).get("pool_gap_exact")
            last_qualified = event.get("pool_qualified")
        elif kind == "master_replay":
            last_pool = event.get("pool", {}).get("pool_gap_exact")
            last_qualified = event.get("pool", {}).get("qualified")
        elif kind == "column_added":
            added.append((pos, event.get("key")))
        elif kind == "pricing_reserve_stop":
            reserve_stops += 1
    reached = sum(any(later > pos and key in keys for later, keys in starts)
                  for pos, key in added)
    first_master = starts[0][1] if starts else set()
    return {"pricing": pricing, "native_master": master, "qp": qp,
            "imported_columns": len(imported) if imported is not None else None,
            "imported_in_first_master": len(set(imported) & first_master)
            if imported is not None and starts else None,
            "new_columns_added": len(added), "added_columns_reached_master": reached,
            "reserve_stops": reserve_stops, "last_pool_gap_exact": last_pool,
            "pool_qualified_last": last_qualified,
            "last_native_status": last_native_status,
            "last_native_incumbent": last_native_incumbent,
            "last_native_call": last_native_call}


def cell(attempt, manifest, frozen, summary_row, case, state, arm):
    folder = attempt / case / f"state{state}" / arm
    row = dict.fromkeys(FIELDS)
    row.update(case=case, base_timetable_group=frozen["cases"][case]["base_timetable_group"],
               state=state, arm=arm, method=METHOD[arm],
               outcome=summary_row["status"], native_status=summary_row.get("native_status"),
               complete_evidence=summary_row.get("complete_evidence"),
               on_time=summary_row.get("receipt", {}).get("on_time"),
               child_wall_s=summary_row.get("receipt", {}).get("elapsed_seconds"),
               parent_admission_s=summary_row.get("admission", {}).get("parent_check_elapsed_seconds"))
    check = folder / "child_source_check.json"
    if check.is_file():
        row["source_check_s"] = read(check).get("elapsed_seconds")
    exception_file = folder / "exception.json"
    if exception_file.is_file():
        error = read(exception_file)
        row["exception_type"] = error.get("type")
        row["exception_message"] = error.get("message")
        row["exception_elapsed_s"] = error.get("elapsed_seconds")
    raw_path = folder / "raw_result.json"
    if raw_path.is_file():
        raw = read(raw_path)["result"]
        cert, mix, counts = raw.get("lower_certificate", {}), raw.get("mixture", {}), raw.get("counts", {})
        lo, hi = cert.get("lower_exact"), mix.get("objective_exact")
        if lo is not None and hi is not None:
            row.update(lower_exact=str(Fraction(lo)), upper_exact=str(Fraction(hi)),
                       gap_exact=str(Fraction(hi)-Fraction(lo)))
        fresh = raw.get("fresh_lower_certificate") or {}
        fresh_exact = fresh.get("lower_exact")
        row["fresh_lower_exact"] = fresh_exact
        row["selected_minus_fresh_lower"] = (
            str(Fraction(lo)-Fraction(fresh_exact)) if lo is not None and fresh_exact is not None else None)
        row["cached_bound_candidates"] = (len(raw["cached_lower_candidates"])
                                         if "cached_lower_candidates" in raw else None)
        row.update(stop_reason=raw.get("reason"),
                   lower_origin=(raw.get("lower_certificate_origin") or {}).get("kind"),
                   fresh_pricing_successes=raw.get("fresh_pricing_successes"),
                   pricing_requests=counts.get("pricing_requests"),
                   master_calls=counts.get("master_calls"),
                   qp_proposal_calls=counts.get("qp_proposal_calls"),
                   qp_non_success=counts.get("qp_non_success"),
                   qp_proposal_wall_s=counts.get("qp_proposal_wall_s"),
                   qp_replay_wall_s=counts.get("qp_replay_wall_s"),
                   polish_steps=counts.get("polish_steps"),
                   polish_wall_s=counts.get("polish_wall_s"),
                   max_rational_bits=counts.get("max_rational_bits"))
    event_path = folder / "events.jsonl"
    compact = {"case": case, "state": state, "arm": arm, "events_sha256": None,
               "pricing": [], "native_master": [], "qp": []}
    if event_path.is_file():
        row["events_sha256"] = manifest["files"][event_path.relative_to(attempt).as_posix()]["sha256"]
        compact["events_sha256"] = row["events_sha256"]
        saved = trace([json.loads(line) for line in event_path.read_text().splitlines()])
        compact.update({key: saved[key] for key in ("pricing", "native_master", "qp")})
        row.update(imported_columns=saved["imported_columns"],
                   imported_in_first_master=saved["imported_in_first_master"],
                   new_columns_added=saved["new_columns_added"],
                   added_columns_reached_master=saved["added_columns_reached_master"],
                   reserve_stops=saved["reserve_stops"],
                   last_pool_gap_exact=saved["last_pool_gap_exact"],
                   pool_qualified_last=saved["pool_qualified_last"],
                   last_native_status=saved["last_native_status"],
                   last_native_incumbent=saved["last_native_incumbent"],
                   last_native_call=saved["last_native_call"],
                   pricing_results=sum(x["status"] is not None for x in saved["pricing"]),
                   global_bounds=sum(x["global_lower_exact"] is not None for x in saved["pricing"]),
                   pricing_native_wall_recorded_s=number_sum(x["native_wall_s"] for x in saved["pricing"]),
                   pricing_native_wall_complete=all(finite(x["native_wall_s"]) for x in saved["pricing"])
                   and len(saved["pricing"]) == (row["pricing_requests"] or 0),
                   native_master_results=len(saved["native_master"]),
                   native_master_wall_recorded_s=number_sum(x["native_wall_s"] for x in saved["native_master"]),
                   qp_result_count=len(saved["qp"]),
                   qp_replay_count=sum(x["replay_wall_s"] is not None for x in saved["qp"]))
    return row, compact


def build(attempt):
    attempt = Path(attempt)
    manifest, frozen, supervisor, summary = verify(attempt)
    by_key = {(r["case"], r["state"], r["stage"]): r for r in summary["rows"]}
    extracted = [cell(attempt, manifest, frozen, by_key[(case, state, arm)], case, state, arm)
                 for case in run.CASES for arm in run.ARMS for state in run.STATES]
    rows, traces = [x[0] for x in extracted], [x[1] for x in extracted]
    lookup = {(r["case"], r["state"], r["arm"]): r for r in rows}
    pairs = []
    for case in run.CASES:
        for arm in run.ARMS:
            zero, one = (lookup[(case, state, arm)] for state in run.STATES)
            admission = one["parent_admission_s"]
            known = (finite(zero["child_wall_s"]) and finite(one["child_wall_s"])
                     and (arm == run.ARMS[0] or finite(admission)))
            pairs.append({"case": case, "base_timetable_group": zero["base_timetable_group"],
                          "arm": arm, "method": METHOD[arm],
                          "state0_child_s": zero["child_wall_s"], "state1_child_s": one["child_wall_s"],
                          "parent_admission_s": admission,
                          "paid_two_state_s": (zero["child_wall_s"] + one["child_wall_s"]
                                               + (admission if arm != run.ARMS[0] else 0)) if known else None,
                          "state0_outcome": zero["outcome"], "state1_outcome": one["outcome"]})
    declared_pairs = {(p["case"], p["arm"]): p for p in summary.get("paid_pairs", [])}
    for pair in pairs:
        original = declared_pairs.get((pair["case"], pair["arm"]))
        if original is None or original.get("complete_two_state_paid_seconds") != pair["paid_two_state_s"]:
            raise ValueError("Derived paid time differs from sealed summary")
    comparisons = []
    for case in run.CASES:
        for left_arm, right_arm, label in ((run.ARMS[0], run.ARMS[1], "plan retention"),
                                           (run.ARMS[1], run.ARMS[2], "numerical master"),
                                           (run.ARMS[2], run.ARMS[3], "physical-bound cache")):
            left_pair = next(p for p in pairs if p["case"] == case and p["arm"] == left_arm)
            right_pair = next(p for p in pairs if p["case"] == case and p["arm"] == right_arm)
            for state in run.STATES:
                left, right = lookup[(case, state, left_arm)], lookup[(case, state, right_arm)]
                def delta(key):
                    return (float(Fraction(right[key])-Fraction(left[key]))
                            if left[key] is not None and right[key] is not None else None)
                comparisons.append({"case": case, "state": state, "comparison": label,
                                    "left": METHOD[left_arm], "right": METHOD[right_arm],
                                    "left_outcome": left["outcome"], "right_outcome": right["outcome"],
                                    "right_minus_left_child_s": delta("child_wall_s"),
                                    "right_minus_left_lower": delta("lower_exact"),
                                    "right_minus_left_upper": delta("upper_exact"),
                                    "right_minus_left_paid_pair_s":
                                    right_pair["paid_two_state_s"]-left_pair["paid_two_state_s"]
                                    if (state == 1 and finite(left_pair["paid_two_state_s"])
                                        and finite(right_pair["paid_two_state_s"])) else None})
    wrapper_path = attempt.with_name(attempt.name + ".slurm_wrapper_receipt.json")
    wrapper = read(wrapper_path) if wrapper_path.is_file() else None
    return {"scope": "single ordered development comparison; descriptive paired differences",
            "manifest_sha256": sha(attempt / "MANIFEST.json"),
            "frozen_sha256": sha(attempt / "frozen.json"),
            "summary_sha256": sha(attempt / "summary.json"),
            "source_commit": frozen.get("source_commit"),
            "source_hashes": frozen.get("source_hashes"),
            "supervisor_returncode": supervisor.get("returncode"),
            "supervisor_elapsed_s": supervisor.get("elapsed_seconds"),
            "controller_elapsed_s": summary.get("controller_elapsed_seconds"),
            "wrapper_receipt_sha256": sha(wrapper_path) if wrapper_path.is_file() else None,
            "wrapper_elapsed_whole_s": wrapper.get("elapsed_whole_seconds") if wrapper else None,
            "wrapper_returncode": wrapper.get("returncode") if wrapper else None,
            "rows": rows, "traces": traces, "paid_pairs": pairs,
            "comparisons": comparisons,
            "limitations": ["Global lower comes from physical pricing, possibly checked inherited evidence; feasible upper is an exact replayed convex mixture.",
                            "Exact replay checks stored floating-point evidence; native Gurobi lower bounds remain solver-tolerance-qualified, not ideal-model proofs.",
                            "An exact restricted-pool residual is not the global hull gap.",
                            "Mixtures are not single executable fleet schedules.",
                            "Component times are recorded scopes only; absent values remain unknown.",
                            "Both public depots share one base timetable; no replicated scalability or speedup inference."]}


def write_csv(path, rows, fields):
    with Path(path).open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def outward(value, lower):
    if value is None:
        return "—"
    cents = Fraction(value) * 100
    whole = cents.numerator // cents.denominator if lower else -((-cents.numerator) // cents.denominator)
    return f"{whole/100:.2f}"


def short(value):
    return "—" if value is None else f"{value:.2f}" if finite(value) else str(value)


def figures(report, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    cases = list(run.CASES)
    names = {"synthetic_cyclic": "Cyclic", "synthetic_multivisit": "Multivisit",
             "public_depot15": "Depot 15", "public_depot16": "Depot 16"}
    pairs = {(p["case"], p["arm"]): p for p in report["paid_pairs"]}
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0), constrained_layout=True)
    for ax, group, title in ((axes[0], cases[:2], "Synthetic cases"),
                             (axes[1], cases[2:], "Public depot variants")):
        available = [pairs[(case, arm)]["paid_two_state_s"] for case in group for arm in run.ARMS
                     if finite(pairs[(case, arm)]["paid_two_state_s"])]
        ceiling = max(available, default=1)
        for i, arm in enumerate(run.ARMS):
            for j, case in enumerate(group):
                item = pairs[(case, arm)]
                x = j + (i-1.5)*.2
                a, b = item["state0_child_s"], item["state1_child_s"]
                if finite(item["paid_two_state_s"]):
                    ax.bar(x, a, width=.18, color=COLORS[arm], alpha=.45)
                    ax.bar(x, b, width=.18, bottom=a, color=COLORS[arm],
                           label=METHOD[arm] if j == 0 else None)
                    if finite(item["parent_admission_s"]):
                        ax.bar(x, item["parent_admission_s"], width=.18, bottom=a+b,
                               color=COLORS[arm], hatch="///", alpha=.9)
                    ax.text(x, item["paid_two_state_s"]+ceiling*.012,
                            f"{item['paid_two_state_s']:.2f}", ha="center", va="bottom", fontsize=6.5)
                    if item["state1_outcome"] == "failed":
                        ax.plot(x, item["paid_two_state_s"], marker="x", markersize=9,
                                markeredgewidth=2, color="#a32525", zorder=5)
                else:
                    ax.text(x, ceiling*.04, "n/a", ha="center", va="bottom",
                            rotation=90, fontsize=7, color=COLORS[arm])
        ax.set_xticks(range(2), [names[case] for case in group])
        ax.set_ylim(0, ceiling*1.17)
        ax.set_title(title)
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Paid two-state wall time (s)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc="lower center", bbox_to_anchor=(.5, -.08), frameon=False)
    fig.suptitle("Initial market light; changed market solid; source checking hatched. Red ×: failed target, time retained.",
                 fontsize=10)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"paid_two_state_time.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)

    lookup = {(r["case"], r["state"], r["arm"]): r for r in report["rows"]}
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0), sharey=True, constrained_layout=True)
    for ax, case in zip(axes, cases[2:]):
        for i, arm in enumerate(run.ARMS):
            row = lookup[(case, 1, arm)]
            if row["lower_exact"] is None or row["upper_exact"] is None:
                ax.text(i, .04, "Failed" if row["outcome"] == "failed" else "No interval",
                        transform=ax.get_xaxis_transform(), ha="center", fontsize=7,
                        color="#a32525" if row["outcome"] == "failed" else "#333333")
                continue
            lo, hi = float(Fraction(row["lower_exact"])), float(Fraction(row["upper_exact"]))
            ax.vlines(i, lo, hi, color=COLORS[arm], lw=6)
            ax.plot(i, lo, marker="_", markersize=12, color="#1a2d3b")
            ax.plot(i, hi, marker="_", markersize=12, color="#1a2d3b")
            ax.text(i, hi+4, outward(row["upper_exact"], False), ha="center", va="bottom", fontsize=7)
            ax.text(i, lo-4, outward(row["lower_exact"], True), ha="center", va="top", fontsize=7)
        ax.set_xticks(range(4), ["Reserve\ncold", "Reserve +\npool", "QP +\npool",
                                  "QP + pool\n+ cache"])
        ax.set_xlim(-.5, 3.5)
        ax.set_title(f"{names[case]}: changed market")
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Objective: global lower to feasible upper")
    all_bounds = [float(Fraction(r[key])) for r in report["rows"] if r["case"] in cases[2:]
                  and r["state"] == 1 for key in ("lower_exact", "upper_exact") if r[key] is not None]
    if all_bounds:
        margin = max(15, (max(all_bounds)-min(all_bounds))*.1)
        axes[0].set_ylim(min(all_bounds)-margin, max(all_bounds)+margin)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"public_state1_bounds.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write(report, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    write_csv(out / "cells.csv", report["rows"], FIELDS)
    write_csv(out / "paid_pairs.csv", report["paid_pairs"], tuple(report["paid_pairs"][0]))
    write_csv(out / "comparisons.csv", report["comparisons"], tuple(report["comparisons"][0]))


def selection(attempt, out):
    """List every public output and every omitted sealed input by pinned hash."""
    attempt, out = Path(attempt), Path(out)
    manifest, _, _, _ = verify(attempt)
    public = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "PUBLIC_SELECTION.json":
            if path.is_symlink():
                raise ValueError("Public output may not be a symlink")
            public[path.relative_to(out).as_posix()] = {"sha256": sha(path),
                                                         "bytes": path.stat().st_size}
    public["PUBLIC_SELECTION.json"] = {"sha256": None,
                                       "reason": "self-listing; digest is intentionally not recursive"}
    omitted = {name: {"sha256": item["sha256"], "bytes": item["bytes"],
                      "reason": "private sealed input; scalar projection only"}
               for name, item in sorted(manifest["files"].items())}
    omitted["MANIFEST.json"] = {"sha256": sha(attempt / "MANIFEST.json"),
                                "bytes": (attempt / "MANIFEST.json").stat().st_size,
                                "reason": "private seal; hash pinned in report.json"}
    wrapper_path = attempt.with_name(attempt.name + ".slurm_wrapper_receipt.json")
    if wrapper_path.is_file():
        omitted[wrapper_path.name] = {"sha256": sha(wrapper_path),
                                     "bytes": wrapper_path.stat().st_size,
                                     "reason": "private operational receipt; scalar projection only"}
    with (out / "PUBLIC_SELECTION.json").open("x") as stream:
        stream.write(json.dumps({
            "scope": "complete inclusion and omission list for this derived publication directory",
            "sealed_manifest_sha256": sha(attempt / "MANIFEST.json"),
            "public_files": public, "omitted_private_inputs": omitted
        }, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", type=Path, help="sealed attempt, or public report.json with --figures-only")
    parser.add_argument("out", type=Path)
    parser.add_argument("--figures-only", action="store_true",
                        help="Render from the passed public report.json; no sealed-source read")
    parser.add_argument("--selection-only", action="store_true",
                        help="List public outputs and hashed private sealed inputs")
    args = parser.parse_args(argv)
    if not args.figures_only and args.out.resolve().is_relative_to(args.attempt.resolve()):
        parser.error("Output must be outside sealed attempt")
    if args.selection_only:
        selection(args.attempt, args.out)
    elif args.figures_only:
        figures(read(args.attempt), args.out)
    else:
        write(build(args.attempt), args.out)


if __name__ == "__main__":
    main()
