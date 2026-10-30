"""Render manuscript figures from already reviewed public scalar tables only."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figures"
SOURCES = {
    "cells": ROOT / "research-20260928/solver-baseline-comparison/results-attempt1/analysis/cells.csv",
    "paid": ROOT / "research-20260928/solver-baseline-comparison/results-attempt1/analysis/paid_pairs.csv",
    "starts": ROOT / "research-20260928/pricing-start-pilot/results-attempt1/analysis/pairs.csv",
}
ARMS = ("reserve_cold_hull", "reserve_feasible_hull", "qp_feasible_hull", "qp_cache_feasible_hull")
LABELS = ("Cold + reserve", "Retained fleets", "Retained + QP master", "Retained + QP\n+ prior bounds")
BLUE, RED, GREY = "#176F8C", "#B45142", "#87929C"


def rows(key):
    with SOURCES[key].open(newline="") as stream:
        return list(csv.DictReader(stream))


def number(value):
    return float(Fraction(value))


def outward(value, upper=False):
    q = Fraction(value) * 100
    n = -((-q.numerator) // q.denominator) if upper else q.numerator // q.denominator
    return f"{n / 100:.2f}"


def style(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#E6E9EC", linewidth=.7, zorder=0)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(OUT / (name + ".pdf"), bbox_inches="tight")
    fig.savefig(OUT / (name + ".png"), dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "pdf.fonttype": 42, "savefig.facecolor": "white"})
    cells = {(r["case"], r["arm"]): r for r in rows("cells") if r["state"] == "1"}
    paid = {(r["case"], r["arm"]): r for r in rows("paid")}
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 6.2), gridspec_kw={"width_ratios": [1.9, 1]},
                             layout="constrained")
    plotted = []
    for panel, case in enumerate(("public_depot15", "public_depot16")):
        left, right = axes[panel]
        ys = np.arange(len(ARMS))[::-1]
        for y, arm in zip(ys, ARMS):
            row, timing = cells[case, arm], paid[case, arm]
            failed = row["outcome"] == "failed"
            assert row["outcome"] == timing["state1_outcome"]
            seconds = float(timing["paid_two_state_s"])
            if failed:
                assert row["lower_exact"] == row["upper_exact"] == ""
                left.text(422, y, "No returned interval", ha="center", va="center", color=RED, fontsize=9)
            else:
                lo, hi = number(row["lower_exact"]), number(row["upper_exact"])
                assert lo <= hi
                left.plot([lo, hi], [y, y], color=BLUE, linewidth=3, solid_capstyle="round")
                left.plot(lo, y, "|", color=BLUE, markersize=10, markeredgewidth=1.7)
                left.plot(hi, y, "|", color=BLUE, markersize=10, markeredgewidth=1.7)
                left.text((lo + hi) / 2, y + .20,
                          f"[{outward(row['lower_exact'])}, {outward(row['upper_exact'], True)}]",
                          ha="center", va="bottom", fontsize=8.5)
            right.barh(y, seconds, color=GREY if failed else BLUE, height=.34,
                       hatch="///" if failed else None, edgecolor="white", linewidth=.4)
            right.text(seconds + 4, y, f"{seconds:.2f}", ha="left", va="center", fontsize=9)
            plotted.append({"case": case, "method": arm, "status": row["outcome"],
                            "paid_two_state_s": seconds,
                            "lower": None if failed else lo, "upper": None if failed else hi})
        left.set_yticks(ys, LABELS)
        right.set_yticks(ys, [""] * len(ys))
        left.set_xlim(300, 550)
        right.set_xlim(0, 420)
        right.set_xticks([0, 200, 400])
        for ax in (left, right):
            ax.set_ylim(-.6, 3.65)
            style(ax)
        left.set_title(f"Depot {case[-2:]}: target hull enclosure", loc="left", pad=10)
        right.set_title("Paid two-market time", loc="left", pad=10)
        if panel == 1:
            left.set_xlabel("Objective units")
            right.set_xlabel("Seconds")
    save(fig, "public_hull_comparison")

    public = [r for r in rows("starts") if r["case"].startswith("public_")]
    assert len(public) == 4
    query_order = {(case, query): i for i, (case, query) in enumerate(
        [(c, q) for c in ("public_depot15", "public_depot16") for q in ("linear_tariff", "marginal_price")])}
    public.sort(key=lambda r: query_order[r["case"], r["query"]])
    gains = [[-float(r["start_minus_cold_upper"]) for r in public],
             [float(r["start_minus_cold_lower"]) for r in public]]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.5), sharey=True, layout="constrained")
    ys = np.arange(4)[::-1]
    for ax, values, title in zip(axes, gains, ("Feasible-cost improvement", "Lower-bound improvement")):
        for y, value in zip(ys, values):
            tie = abs(value) <= 1e-5
            shown = 0.0 if tie else value
            color = GREY if tie else BLUE if value > 0 else RED
            if tie:
                ax.plot(0, y, "o", color=color, markersize=5)
                ax.text(.5, y, "tie", va="center", fontsize=9, color="#5C6670")
            else:
                ax.barh(y, shown, height=.36, color=color)
                ax.text(shown + (.45 if shown > 0 else -.45), y, f"{shown:+.2f}",
                        va="center", ha="left" if shown > 0 else "right", fontsize=9)
        ax.axvline(0, color="#3B444B", linewidth=.8)
        ax.set_xlim(-8, 16)
        ax.set_xticks([-5, 0, 5, 10, 15])
        ax.set_ylim(-.5, 3.6)
        ax.set_title(title, loc="left", pad=10)
        ax.set_xlabel("Improvement in objective units (positive is better)", fontsize=9)
        style(ax)
    axes[0].set_yticks(ys, [f"Depot {r['case'][-2:]} / " +
        ("linear" if r["query"] == "linear_tariff" else "marginal") for r in public])
    save(fig, "pricing_start_effects")
    (OUT / "FIGURE_SOURCES.json").write_text(json.dumps({
        "source_files": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in SOURCES.values()},
        "inputs": "Previously reviewed public scalar CSV tables only; no solver or raw-event reconstruction.",
        "public_hull_rows": plotted,
        "pricing_start_effects": [{"case": r["case"], "query": r["query"],
            "upper_improvement": gains[0][i], "lower_improvement": gains[1][i]} for i, r in enumerate(public)],
        "qualifications": ["Both public depots share one Hildenbrand base timetable.",
            "Native tolerance-qualified bounds, not ideal-model exact proofs.",
            "Failed targets have no displayed interval; spent time remains.",
            "Paid pair totals include both children and measured parent admission once.",
            "Pricing starts compare quality at the same 160-second native cap, not speed.",
            "Changes of at most 1e-5 are displayed as ties."]}, indent=2, sort_keys=True) + "\n")
    print("Rendered two vector figures from 8 iterative rows and 4 fixed-price pairs.")


if __name__ == "__main__":
    main()
