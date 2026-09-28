"""Publish compact, non-private analysis of the sealed pricing-start pilot.

Run from repository root with the repaired research Python and PYTHONPATH=src.
Matplotlib is supplied by the matching system Python site-packages on this host.
No native solve or experiment module is imported.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[4]
SEALED = (ROOT.parent / "research-20260928/cluster/pricing-start-pilot-attempt1"
          / "sealed/20260928-attempt1")
OUT = Path(__file__).resolve().parent
CASE_LABEL = {
    "synthetic_cyclic": "Cyclic",
    "synthetic_multivisit": "Multivisit",
    "public_depot15": "Depot 15",
    "public_depot16": "Depot 16",
}
QUERY_LABEL = {"linear_tariff": "linear", "marginal_price": "marginal"}
BLUE = "#1764a0"
ORANGE = "#d47513"
GRAY = "#68717a"
TOL = 1e-5  # Beyond the admission margin (1e-6) and printed roundoff.


def number(value):
    return "" if value is None else f"{value:.3f}"


def classify(delta, desirable):
    if delta is None:
        return "unavailable"
    if abs(delta) <= TOL:
        return "tie within 1e-5"
    return "start better" if delta * desirable > 0 else "start worse"


def write_csv(name, rows, fields):
    with (OUT / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load():
    frozen = json.loads((SEALED / "frozen.json").read_text())
    summary = json.loads((SEALED / "summary.json").read_text())
    assert frozen["protocol"] == summary["protocol"] == "egg-pricing-start-development-20260928-v1"
    assert summary["all_declared_calls_accounted"] is True
    assert len(summary["rows"]) == 16
    expected = {(c, q, a) for c in frozen["case_order"]
                for q in frozen["query_order"] for a in ("cold", "start")}
    actual = {(r["case"], r["query"], r["arm"]) for r in summary["rows"]}
    assert actual == expected
    return frozen, summary


def build_rows(frozen, summary):
    output = []
    lookup = {(r["case"], r["query"], r["arm"]): r for r in summary["rows"]}
    for case in frozen["case_order"]:
        spec = frozen["cases"][case]
        for query in frozen["query_order"]:
            selected = spec["queries"][query]
            for arm in frozen["arm_orders"][case][query]:
                r = lookup[case, query, arm]
                setup_events = r.get("start_setup_events", [])
                assert len(setup_events) <= 1
                setup = setup_events[0] if setup_events else {}
                timings = setup.get("timings", {})
                receipt = r.get("receipt", {})
                interval = r.get("native_admitted_interval")
                raw = r.get("raw_native_stats") or {}
                output.append({
                    "case": case,
                    "base_timetable_group": spec["base_timetable_group"],
                    "query": query,
                    "execution_order": frozen["arm_orders"][case][query].index(arm) + 1,
                    "arm": arm,
                    "call_status": r["status"],
                    "hard_timeout": receipt.get("hard_timeout"),
                    "returncode": receipt.get("returncode"),
                    "native_status": r.get("native_status"),
                    "raw_solver_status": raw.get("status"),
                    "returned_plan": r.get("returned_plan"),
                    "start_requested": r["start_requested"],
                    "start_setup_status": setup.get("status"),
                    "start_submitted": r["start_submitted"],
                    "native_acceptance": r["native_acceptance"],
                    "selected_movement_count": r["selected_movement_count"],
                    "raw_native_incumbent": raw.get("incumbent"),
                    "raw_native_lower": raw.get("lower_bound"),
                    "native_replayed_upper": r.get("native_replayed_objective"),
                    "native_admitted_lower": interval[0] if interval else None,
                    "native_admitted_upper": interval[1] if interval else None,
                    "known_source_upper": r["known_source_upper"],
                    "best_feasible_upper": r.get("best_feasible_upper", r["known_source_upper"]),
                    "native_optimization_s": r.get("native_optimization_seconds"),
                    "start_setup_s": setup.get("setup_elapsed_s"),
                    "model_build_s": timings.get("model_build_s"),
                    "start_validation_s": timings.get("validation_s"),
                    "start_attachment_s": timings.get("start_attach_s"),
                    "core_call_s": r.get("core_call_elapsed_seconds"),
                    "child_work_s": r.get("child_work_elapsed_seconds"),
                    "complete_child_s": receipt.get("elapsed_seconds"),
                    "hard_child_cap_s": receipt.get("hard_seconds"),
                    "evidence_issue_count": len(r.get("evidence_issues", [])),
                    "model_seed": r.get("native_seed"),
                })
    return output


def pair_rows(frozen, rows):
    lookup = {(r["case"], r["query"], r["arm"]): r for r in rows}
    pairs = []
    for case in frozen["case_order"]:
        for query in frozen["query_order"]:
            cold = lookup[case, query, "cold"]
            start = lookup[case, query, "start"]
            assert cold["known_source_upper"] == start["known_source_upper"]
            upper_delta = ((start["native_replayed_upper"] - cold["native_replayed_upper"])
                           if start["native_replayed_upper"] is not None
                           and cold["native_replayed_upper"] is not None else None)
            lower_delta = ((start["native_admitted_lower"] - cold["native_admitted_lower"])
                           if start["native_admitted_lower"] is not None
                           and cold["native_admitted_lower"] is not None else None)
            pairs.append({
                "case": case,
                "base_timetable_group": cold["base_timetable_group"],
                "query": query,
                "common_source_upper": cold["known_source_upper"],
                "cold_native_replayed_upper": cold["native_replayed_upper"],
                "start_native_replayed_upper": start["native_replayed_upper"],
                "start_minus_cold_upper": upper_delta,
                "upper_comparison": classify(upper_delta, -1),
                "cold_admitted_lower": cold["native_admitted_lower"],
                "start_admitted_lower": start["native_admitted_lower"],
                "start_minus_cold_lower": lower_delta,
                "lower_comparison": classify(lower_delta, 1),
                "cold_best_feasible_upper": cold["best_feasible_upper"],
                "start_best_feasible_upper": start["best_feasible_upper"],
                "best_returned_native_upper": min(v for v in (
                    cold["native_replayed_upper"], start["native_replayed_upper"]) if v is not None),
                "cold_complete_child_s": cold["complete_child_s"],
                "start_complete_child_s": start["complete_child_s"],
            })
            pairs[-1]["source_excess_over_best_returned_pct"] = (
                100 * (pairs[-1]["common_source_upper"] - pairs[-1]["best_returned_native_upper"])
                / pairs[-1]["best_returned_native_upper"])
    return pairs


def accounting(frozen, summary, rows):
    source = [{
        "case": case,
        "base_timetable_group": frozen["cases"][case]["base_timetable_group"],
        "historical_source_child_once_s": frozen["cases"][case]["source"]["source_child_elapsed_seconds"],
        "case_preparation_within_freeze_s": frozen["cases"][case]["source"]["preparation_elapsed_seconds"],
    } for case in frozen["case_order"]]
    online = sum(r["complete_child_s"] for r in rows if r["complete_child_s"] is not None)
    historical = sum(r["historical_source_child_once_s"] for r in source)
    freeze_receipt = json.loads((ROOT / "research-20260928/pricing-start-pilot/FREEZE_RECEIPT.json").read_text())
    whole_freeze = freeze_receipt["complete_freeze_command_seconds"]
    termination = json.loads((ROOT / "research-20260928/pricing-start-pilot/TERMINATION_577225.json").read_text())
    wrapper = termination["receipts"]["20260928-attempt1.slurm_wrapper_receipt.json"]["content"]
    slurm_elapsed = termination["accounting"].splitlines()[0].split("|")[3]
    hours, minutes, seconds = map(int, slurm_elapsed.split(":"))
    assert math.isclose(online, summary["conditional_online_child_seconds"], abs_tol=1e-6)
    assert math.isclose(historical, summary["historical_source_once_seconds"], abs_tol=1e-6)
    return source, {
        "declared_calls": len(rows),
        "returned_calls": sum(r["call_status"] == "returned" for r in rows),
        "failed_or_unresolved_calls": sum(r["call_status"] != "returned" for r in rows),
        "conditional_online_complete_children_s": online,
        "historical_source_generation_once_s": historical,
        "freeze_internal_preparation_once_s": frozen["freeze_preparation_elapsed_seconds"],
        "whole_freeze_command_once_s": whole_freeze,
        "runner_source_inclusive_subtotal_s": summary["source_inclusive_seconds"],
        "source_plus_whole_freeze_plus_child_s": historical + whole_freeze + online,
        "supervisor_elapsed_s": json.loads((SEALED / "supervisor_receipt.json").read_text())["elapsed_seconds"],
        "slurm_wrapper_elapsed_s": wrapper["elapsed_whole_seconds"],
        "slurm_wrapper_setup_s": wrapper["setup_seconds"],
        "slurm_allocation_elapsed_s": hours * 3600 + minutes * 60 + seconds,
        "note": "Native optimization and setup are inside core call; core and child work are inside complete child. Internal freeze preparation includes case admission and lies inside the whole freeze command. Supervisor, wrapper and Slurm allocation intervals overlap the online work and are not added to paid work subtotals.",
    }


def figure_bounds(pairs):
    public = [p for p in pairs if p["case"].startswith("public_")]
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.8), constrained_layout=True)
    for ax, p in zip(axes.flat, public):
        baseline = p["common_source_upper"]
        ax.axvline(baseline, color=GRAY, ls="--", lw=1.5, label="common source upper")
        for y, arm, color in ((1, "cold", BLUE), (0, "start", ORANGE)):
            lower = p[f"{arm}_admitted_lower"]
            upper = p[f"{arm}_native_replayed_upper"]
            if lower is None or upper is None:
                ax.plot(baseline, y, marker="x", color=color, ms=10, mew=2)
                continue
            ax.plot([lower, upper], [y, y], color=color, lw=3, solid_capstyle="round")
            ax.plot(lower, y, marker="<", color=color, ms=8)
            ax.plot(upper, y, marker="o", color=color, ms=7)
        ax.set_yticks([0, 1], ["start", "cold"])
        ax.set_title(f"{CASE_LABEL[p['case']]} · {QUERY_LABEL[p['query']]}")
        ax.set_xlabel("Fixed-price objective (cost units)")
        ax.grid(axis="x", alpha=0.2)
        ax.set_ylim(-0.5, 1.5)
        ax.set_xlim(min(p["cold_admitted_lower"], p["start_admitted_lower"]) - 6,
                    baseline + 6)
    fig.legend(handles=[
        Line2D([0], [0], color=GRAY, ls="--", label="common known source upper"),
        Line2D([0], [0], marker="<", color="black", lw=0, label="admitted native lower"),
        Line2D([0], [0], marker="o", color="black", lw=0, label="replayed native upper"),
    ], loc="upper center", bbox_to_anchor=(0.5, 1.065), ncol=3, frameon=False)
    fig.savefig(OUT / "public_bound_quality.png", dpi=180, bbox_inches="tight")
    fig.savefig(OUT / "public_bound_quality.pdf", bbox_inches="tight")
    plt.close(fig)


def figure_times(rows, source):
    fig = plt.figure(figsize=(12, 8), constrained_layout=True)
    grid = fig.add_gridspec(3, 1, height_ratios=[1, 1, 0.95])
    for ax, public, lo, hi in ((fig.add_subplot(grid[0]), False, 0, 1.7),
                               (fig.add_subplot(grid[1]), True, 0, 180)):
        cases = [c for c in CASE_LABEL if c.startswith("public_") == public]
        pairs = [(c, q) for c in cases for q in QUERY_LABEL]
        for y, (case, query) in enumerate(pairs[::-1]):
            for arm, shift, color, marker in (("cold", 0.12, BLUE, "o"),
                                               ("start", -0.12, ORANGE, "D")):
                r = next(x for x in rows if (x["case"], x["query"], x["arm"]) == (case, query, arm))
                is_fail = r["call_status"] != "returned"
                ax.plot(r["complete_child_s"], y + shift,
                        marker="x" if is_fail else marker,
                        ms=8 if is_fail else 6, mew=2 if is_fail else 1,
                        color="crimson" if is_fail else color)
        ax.set_yticks(range(len(pairs)), [f"{CASE_LABEL[c]} · {QUERY_LABEL[q]}" for c, q in pairs[::-1]])
        ax.set_xlim(lo, hi)
        ax.grid(axis="x", alpha=0.2)
        ax.set_xlabel("Complete child elapsed (s)")
        ax.set_title("Public pairs" if public else "Synthetic pairs")
    ax = fig.add_subplot(grid[2])
    bars = [r["historical_source_child_once_s"] for r in source]
    ax.barh(range(4), bars, color="#818a93", height=0.55)
    ax.set_yticks(range(4), [CASE_LABEL[r["case"]] for r in source])
    ax.invert_yaxis()
    ax.set_xlim(0, max(bars) * 1.18)
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    ax.set_xlabel("Historical source generation, paid once per case (s)")
    for y, val in enumerate(bars):
        ax.text(val + 2, y, f"{val:.1f}", va="center", fontsize=9)
    legend_handles = [
        Line2D([0], [0], color=BLUE, marker="o", lw=0, label="cold"),
        Line2D([0], [0], color=ORANGE, marker="D", lw=0, label="start"),
    ]
    if any(r["call_status"] != "returned" for r in rows):
        legend_handles.append(Line2D([0], [0], color="crimson", marker="x", lw=0,
                                     label="failed / unresolved"))
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 1.035),
               ncol=len(legend_handles), frameon=False)
    fig.savefig(OUT / "paid_times.png", dpi=180, bbox_inches="tight")
    fig.savefig(OUT / "paid_times.pdf", bbox_inches="tight")
    plt.close(fig)


def markdown(frozen, rows, pairs, source, totals):
    lines = [
        "# Fixed-price pricing-start pilot: attempt 1",
        "",
        "All 16 declared calls returned. Each of eight starts was submitted to the native API; solver acceptance was not observable. The four synthetic pairs returned the same certified numerical intervals in both arms. All eight public calls consumed the 160 s native cap. Among four public query pairs, the start improved one replayed incumbent (depot 15 marginal) and one admitted lower bound (depot 16 marginal), worsened two lower bounds, and tied the remaining lower bound within 1e-5. This is a mixed quality result at equal caps, not evidence of faster solving.",
        "",
        "The cases are development diagnostics. Depot 15 and depot 16 are variants of one Hildenbrand base timetable; they are not independent public replications. Linear and marginal prices were distinct in all four cases. No time to first incumbent was recorded.",
        "",
        "## Public native quality at the cap",
        "",
        "Every row below has a physically replayed native upper. The source upper is the same known feasible baseline available to both arms. The native lower is the separately admitted lower bound; the solver's raw lower is retained in `calls.csv`. Lower objective/upper is better; higher lower bound is better.",
        "",
        "| Case · query | Common source upper | Cold native upper | Start native upper | Cold admitted lower | Start admitted lower | Source excess¹ | Start effect |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for p in pairs:
        if not p["case"].startswith("public_"):
            continue
        effect = f"upper {p['upper_comparison']}; lower {p['lower_comparison']}"
        lines.append(f"| {CASE_LABEL[p['case']]} · {QUERY_LABEL[p['query']]} | "
                     f"{p['common_source_upper']:.3f} | {p['cold_native_replayed_upper']:.3f} | "
                     f"{p['start_native_replayed_upper']:.3f} | {p['cold_admitted_lower']:.3f} | "
                     f"{p['start_admitted_lower']:.3f} | {p['source_excess_over_best_returned_pct']:.2f}% | {effect} |")
    lines += [
        "",
        "¹ `(common source upper − best newly returned native incumbent) / best newly returned native incumbent`. This 0.32–2.74% excess is relative to the best returned fleet in each query, **not** relative to the unknown true optimum; it shows the feasible-solution gain purchased by native solving at this cap.",
        "",
        "Native admitted interval uppers include the solver-tolerance margin of 1e-6; the native upper columns above are the physically replayed feasible costs. The best feasible upper for each arm is `min(common source upper, native replayed upper)` in `calls.csv`. All public native uppers improved that baseline; a cold call would still have its source plan even if its native result had no incumbent.",
        "",
        "![Public bound quality](public_bound_quality.png)",
        "",
        "## All declared calls",
        "",
        "Setup is the start-event interval and includes model build. All timing columns are seconds; blank denotes no measurement. The child column is the complete paid child receipt.",
        "",
        "| Case · query | Arm | Call / native status | Replayed upper | Admitted lower | Start setup | Core call | Native optimize | Complete child |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {CASE_LABEL[r['case']]} · {QUERY_LABEL[r['query']]} | {r['arm']} | "
                     f"{r['call_status']} / {r['native_status'] or '—'} | "
                     f"{number(r['native_replayed_upper'])} | {number(r['native_admitted_lower'])} | "
                     f"{number(r['start_setup_s'])} | {number(r['core_call_s'])} | "
                     f"{number(r['native_optimization_s'])} | {number(r['complete_child_s'])} |")
    lines += [
        "",
        "## Complete call and paid source time",
        "",
        "| Case | Source generation once (s) | Admission within freeze (s) |",
        "|---|---:|---:|",
    ]
    for s in source:
        lines.append(f"| {CASE_LABEL[s['case']]} | {s['historical_source_child_once_s']:.3f} | "
                     f"{s['case_preparation_within_freeze_s']:.3f} |")
    lines += [
        "",
        f"The 16 complete child receipts sum to **{totals['conditional_online_complete_children_s']:.3f} s**. Historical generation of the four source pools cost **{totals['historical_source_generation_once_s']:.3f} s** in earlier paid work, shared across both prices and arms. The whole freeze command cost **{totals['whole_freeze_command_once_s']:.3f} s**; its internal preparation measurement was **{totals['freeze_internal_preparation_once_s']:.3f} s**, including the per-case admission times above. The runner's source-inclusive subtotal using that internal preparation is **{totals['runner_source_inclusive_subtotal_s']:.3f} s**. Source generation once plus the whole freeze command plus complete children is **{totals['source_plus_whole_freeze_plus_child_s']:.3f} s**. The current job's supervisor elapsed was **{totals['supervisor_elapsed_s']:.3f} s**; its wrapper elapsed was **{totals['slurm_wrapper_elapsed_s']:,} s**, including **{totals['slurm_wrapper_setup_s']} s** setup, and Slurm accounting elapsed was **{totals['slurm_allocation_elapsed_s']:,} s**. These enclosing and overlapping intervals are not added to the child sum. They also do not represent a replicated per-arm end-to-end speedup comparison.",
        "",
        "![Paid times](paid_times.png)",
        "",
        "For each call, `calls.csv` reports complete child, inner child work, core call, native optimization, and (for starts) setup, model build, validation and attachment times. Native optimization and setup occur within the core call, which occurs within the child; those fields must not be summed. Missing timing is blank, not zero. Start setup totals include model build, so only its measured validation and attachment fields isolate hint-related work. All 16 returns were on time; no failed marker appears in the figure.",
        "",
        "## Interpretation and limits",
        "",
        "The start arm supplied checked movement selections; continuous charging remained a native decision. Submission records only an API action, not native acceptance. A returned plan also cannot establish that the hint was used. Four synthetic pairs tied within the stated tolerance; multivisit marginal improved the source upper in both arms. Public depot 15 marginal had a 1.105 lower native upper with the start but a 3.593 lower (worse) admitted lower bound. Depot 16 marginal had an 11.785 higher (better) admitted lower bound with the same incumbent. Depot 15 linear's lower worsened by 5.679; depot 16 linear tied. Public calls still reached the cap, and the setup/child differences are far too small and unreplicated to support a speedup estimate.",
        "",
        "The pilot tests fixed-price oracle calls, not an iterative hull method or a learned proposal. The mixed public result does not justify immediate full-method integration. Broader independent timetable groups and retrieval evaluation would be the next development evidence before any machine-learning claim. Native bounds and numeric plans retain solver-tolerance qualifications.",
        "",
        "## Provenance",
        "",
        f"Read-only inputs: sealed `20260928-attempt1` (protocol `{frozen['protocol']}`), its `frozen.json`, `summary.json`, supervisor receipt and the previously recorded termination receipt. Frozen execution commit `{frozen['source_commit']}`; historical pool execution commit `{frozen['source_execution_commit']}`. GRB, one thread, effective seed `{frozen['native_probe']['model_seed']}`; Python-MIP `{frozen['environment']['mip']}`, Gurobi `{frozen['environment']['gurobi_runtime']}`. The parent collection checked the 119-file seal. The runner created physically replayed objectives and admitted intervals; an independent reconciliation review is separate from this analysis. This directory contains only derived metrics and figures, no raw logs or plans.",
        "",
    ]
    (OUT / "ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    frozen, summary = load()
    rows = build_rows(frozen, summary)
    pairs = pair_rows(frozen, rows)
    source, totals = accounting(frozen, summary, rows)
    write_csv("calls.csv", rows, list(rows[0]))
    write_csv("pairs.csv", pairs, list(pairs[0]))
    write_csv("source_costs.csv", source, list(source[0]))
    (OUT / "accounting.json").write_text(json.dumps(totals, indent=2) + "\n")
    figure_bounds(pairs)
    figure_times(rows, source)
    markdown(frozen, rows, pairs, source, totals)
    print(f"Wrote {len(rows)} call rows, {len(pairs)} pairs, four source costs, two figures")


if __name__ == "__main__":
    main()
