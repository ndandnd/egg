#!/usr/bin/env python3
"""Plot direct route-repair outcomes from the compact frozen-transfer CSV."""
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
DEFAULT_INPUT = ROOT / "research-20260930/learning-campaign/TRANSFER_CELLS.csv"
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
    repair = {(r["seed"], r["stage"]): r for r in rows if r["cell_type"] == "repair"}
    targets = [r for r in rows if r["cell_type"] == "target"]
    seeds = sorted({r["seed"] for r in targets}, key=int)
    cases = {seed: min(exact_float(r["final_incumbent_cost_exact"])
                       for r in targets if r["seed"] == seed) for seed in seeds}
    if len(seeds) != 2 or len(repair) != 4:
        raise ValueError(f"expected two cases and four repaired cells; got {len(seeds)} cases, {len(repair)} repairs")

    colors = {"shared_cost_only": "#0072B2", "shared_cost_learned": "#D55E00", "incumbent": "#555555"}
    labels = {"shared_cost_only": "Cost-only repair", "shared_cost_learned": "Learned repair", "incumbent": "Best target-arm incumbent after hull"}
    seed_labels = {"2018": "2018 · 20 services", "2019": "2019 · 28 services"}
    x = np.arange(len(seeds), dtype=float)
    width = 0.22
    cost_offsets = {"shared_cost_only": -0.24, "shared_cost_learned": 0.0, "incumbent": 0.24}
    time_offsets = {"shared_cost_only": -0.19, "shared_cost_learned": 0.19}

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "svg.fonttype": "none",
    })
    fig, (ax_cost, ax_time) = plt.subplots(2, 1, figsize=(11.3, 8.0), gridspec_kw={"height_ratios": [1.05, 0.9]})
    fig.patch.set_facecolor("white")
    for ax in (ax_cost, ax_time):
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        ax.set_axisbelow(True)

    for i, seed in enumerate(seeds):
        for stage in ("shared_cost_only", "shared_cost_learned"):
            row = repair[(seed, stage)]
            value = exact_float(row["direct_candidate_cost_exact"])
            ax_cost.scatter([x[i] + cost_offsets[stage]], [value], s=66, marker="o",
                            color=colors[stage], edgecolor="white", linewidth=0.8,
                            label=labels[stage] if i == 0 else None, zorder=4)
            buses = row["candidate_buses"]
            ax_cost.annotate(f"{value:.2f}\n{buses} buses",
                             (x[i] + cost_offsets[stage], value),
                             xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=8)

            time_s = float(row["repair_total_seconds"])
            tbar = ax_time.bar(x[i] + time_offsets[stage], time_s, width=0.32,
                               color=colors[stage], edgecolor="white", linewidth=0.7,
                               label=labels[stage] if i == 0 else None, zorder=3)
            ax_time.annotate(f"{time_s:.2f} s\n{buses} buses",
                             (tbar[0].get_x() + tbar[0].get_width() / 2, time_s),
                             xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=8)

        best = cases[seed]
        ax_cost.scatter([x[i] + cost_offsets["incumbent"]], [best], s=70, marker="D",
                        color=colors["incumbent"], edgecolor="white", linewidth=0.8,
                        label=labels["incumbent"] if i == 0 else None, zorder=5)
        ax_cost.annotate(f"{best:.2f}\nincumbent",
                         (x[i] + cost_offsets["incumbent"], best),
                         xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    xticklabels = [seed_labels.get(seed, seed) for seed in seeds]
    for ax in (ax_cost, ax_time):
        ax.set_xticks(x, xticklabels)
        ax.tick_params(axis="x", length=0, pad=8)

    ax_cost.set_ylim(490, 815)
    ax_cost.set_ylabel("Objective (cost units; displayed range 490–815)")
    ax_cost.set_title("A. Direct repair candidates and best target-arm incumbent after hull", loc="left", pad=8)

    ax_time.set_ylim(0, 40)
    ax_time.set_ylabel("Repair wall time (seconds)")
    ax_time.set_title("B. Direct route-repair time", loc="left", pad=8)

    handles, legend_labels = ax_cost.get_legend_handles_labels()
    fig.legend(handles, legend_labels, frameon=False, fontsize=8, loc="upper center",
               bbox_to_anchor=(0.5, 0.945), ncol=3, columnspacing=2.0)
    fig.suptitle("Frozen-model transfer: repair quality and time", y=0.985, fontsize=13, fontweight="semibold")
    fig.text(0.5, 0.025,
             "2018 covers were optimal; both 2019 covers timed out at 30 s (gaps 0.200 / 0.334). "
             "Hull incumbent is not a physical-optimality certificate; two development cases only.",
             ha="center", va="bottom", fontsize=8, color="#374151")
    fig.tight_layout(rect=(0.04, 0.075, 0.98, 0.90), h_pad=2.0)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_dir / "transfer_campaign_cost_time.png", dpi=220, facecolor="white", bbox_inches="tight")
    fig.savefig(args.output_dir / "transfer_campaign_cost_time.svg", facecolor="white", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
