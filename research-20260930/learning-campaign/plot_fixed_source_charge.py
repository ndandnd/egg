#!/usr/bin/env python3
"""Plot fixed-source charging cost response and separately paid time."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "research-20260930/learning-campaign/FIXED_SOURCE_CHARGE_CELLS.csv"
DEFAULT_DIR = ROOT / "research-20260930/learning-campaign/figures"


def exact_float(value: str | None) -> float:
    if not value:
        raise ValueError("missing exact value")
    return float(Fraction(value))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.input.open(encoding="utf-8", newline="")))
    seeds = sorted({int(r["seed"]) for r in rows}, key=int)
    cells = {(int(r["seed"]), r["source"]): r for r in rows}
    if len(rows) != 8 or len(seeds) != 4 or len(cells) != 8:
        raise ValueError(f"expected eight source charging cells over four cases, got {len(rows)} rows")

    source_colors = {"source0": "#0072B2", "source1": "#D55E00"}
    case_labels = {
        2016: "Seed 2016 · 20 services", 2017: "Seed 2017 · 28 services",
        2018: "Seed 2018 · 20 services", 2019: "Seed 2019 · 28 services",
    }
    xbase = {seed: i * 3.0 for i, seed in enumerate(seeds)}
    source_x = {(seed, "source0"): xbase[seed] - 0.45 for seed in seeds}
    source_x.update({(seed, "source1"): xbase[seed] + 0.45 for seed in seeds})

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10.5,
        "axes.labelsize": 9, "svg.fonttype": "none",
    })
    fig = plt.figure(figsize=(13.0, 8.0), facecolor="white")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.65, 0.9], hspace=0.48, wspace=0.25)
    ax_cost = fig.add_subplot(grid[0, :])
    ax_acq = fig.add_subplot(grid[1, 0])
    ax_lp = fig.add_subplot(grid[1, 1])
    for ax in (ax_cost, ax_acq, ax_lp):
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        ax.set_axisbelow(True)

    direct_label = "Original source charging"
    recharged_label = "Target-price charging, exact nonlinear rescore"
    historical_label = "Best historical native target incumbent"
    for seed in seeds:
        center = xbase[seed]
        native_cost = exact_float(cells[(seed, "source0")]["historical_best_native_cost_exact"])
        ax_cost.hlines(native_cost, center - 0.85, center + 0.85, color="#333333",
                       linestyle=(0, (4, 2)), linewidth=1.0, zorder=1)
        ax_cost.scatter([center], [native_cost], marker="D", s=43, color="#333333", zorder=5,
                        label=historical_label if seed == seeds[0] else None)
        ax_cost.annotate(f"native {native_cost:.2f}", (center, native_cost),
                         xytext=(0, -24), textcoords="offset points", ha="center", va="top",
                         fontsize=7.6, color="#333333",
                         bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.8})
        for source in ("source0", "source1"):
            row = cells[(seed, source)]
            xpos = source_x[(seed, source)]
            direct = exact_float(row["direct_cost_exact"])
            after = exact_float(row["recharged_cost_exact"])
            color = source_colors[source]
            ax_cost.plot([xpos, xpos], [direct, after], color=color, linewidth=1.4, alpha=0.85, zorder=2)
            ax_cost.scatter([xpos], [direct], marker="o", s=42, color=color,
                            edgecolor="white", linewidth=0.7,
                            label=f"{source.replace('source', 'Source ')} · original" if seed == seeds[0] else None,
                            zorder=4)
            ax_cost.scatter([xpos], [after], marker="s", s=43, color=color,
                            edgecolor="white", linewidth=0.7,
                            label=f"{source.replace('source', 'Source ')} · recharged" if seed == seeds[0] else None,
                            zorder=4)
            dx = -6 if source == "source0" else 6
            align = "right" if source == "source0" else "left"
            ax_cost.annotate(f"{direct:.2f}", (xpos, direct), xytext=(dx, 6),
                             textcoords="offset points", ha=align, va="bottom", fontsize=7.8, color=color)
            ax_cost.annotate(f"{after:.2f}", (xpos, after), xytext=(dx, 8),
                             textcoords="offset points", ha=align, va="bottom", fontsize=7.8, color=color)

    tick_positions = [source_x[(seed, src)] for seed in seeds for src in ("source0", "source1")]
    ax_cost.set_xticks(tick_positions, ["Source 0", "Source 1"] * len(seeds))
    ax_cost.tick_params(axis="x", length=0, pad=7)
    for seed in seeds:
        ax_cost.text(xbase[seed], -0.14, case_labels.get(seed, str(seed)), ha="center", va="top",
                     transform=ax_cost.get_xaxis_transform(), fontsize=8.5, fontweight="medium")
    ax_cost.set_ylim(475, 775)
    ax_cost.set_xlim(xbase[seeds[0]] - 1.15, xbase[seeds[-1]] + 1.15)
    ax_cost.set_ylabel("Exact nonlinear target bill (cost units)")
    ax_cost.set_title("A. Recharging fixed source routes changes the curved target bill", loc="left", pad=9)
    handles, labels = ax_cost.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, loc="upper center",
               bbox_to_anchor=(0.5, 0.99), ncol=5, columnspacing=1.3)

    acq_values, lp_values = [], []
    for seed in seeds:
        first = cells[(seed, "source0")]
        acq_values.append(float(first["historical_source_acquisition_seconds_once"]))
        lp_values.append(sum(float(cells[(seed, src)]["lp_elapsed_seconds"]) for src in ("source0", "source1")))
    positions = np.arange(len(seeds))
    acquisition_bars = ax_acq.bar(positions, acq_values, width=0.58, color="#7B8794", zorder=3)
    ax_acq.set_xticks(positions, [case_labels[s].replace(" · ", "\n") for s in seeds])
    ax_acq.set_ylim(0, 150)
    ax_acq.set_ylabel("Seconds")
    ax_acq.set_title("B. Historical source acquisition\n(both source fleets, fully paid)", loc="left", pad=8)
    for bar, val in zip(acquisition_bars, acq_values):
        ax_acq.annotate(f"{val:.1f}", (bar.get_x() + bar.get_width() / 2, val),
                        xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    lp_bars = ax_lp.bar(positions, lp_values, width=0.58, color="#009E73", zorder=3)
    ax_lp.set_xticks(positions, [case_labels[s].replace(" · ", "\n") for s in seeds])
    ax_lp.set_ylim(0, 15)
    ax_lp.set_ylabel("Seconds")
    ax_lp.set_title("C. Both target-charging cell times\n(source 0 + source 1)", loc="left", pad=8)
    for bar, val in zip(lp_bars, lp_values):
        ax_lp.annotate(f"{val:.2f}", (bar.get_x() + bar.get_width() / 2, val),
                       xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Fixed-route charging response across four development cases", y=1.025,
                 fontsize=13, fontweight="semibold")
    fig.text(0.5, 0.005,
             "Case labels are synthetic seed IDs, not calendar years. LPs optimize linear tariff a; "
             "points show independently replayed nonlinear bills. Physical fleet optimality remains unknown.",
             ha="center", va="bottom", fontsize=8, color="#374151")
    fig.subplots_adjust(top=0.89, bottom=0.12, left=0.075, right=0.985)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_dir / "fixed_source_charge_cost_time.png", dpi=220, facecolor="white", bbox_inches="tight")
    fig.savefig(args.output_dir / "fixed_source_charge_cost_time.svg", facecolor="white", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
