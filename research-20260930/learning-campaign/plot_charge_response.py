#!/usr/bin/env python3
"""Plot paired charge-response development outcomes from the summary CSV."""
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
DEFAULT_INPUT = ROOT / "research-20260930/learning-campaign/CHARGE_RESPONSE_CELLS.csv"
DEFAULT_OUTPUT_DIR = ROOT / "research-20260930/learning-campaign/figures"


def exact_float(value: str | None) -> float:
    if not value:
        raise ValueError("missing exact value in development summary row")
    return float(Fraction(value))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as stream:
        dev = [row for row in csv.DictReader(stream) if row["split"] == "dev" and row["arm"] == "cold"]
    dev.sort(key=lambda row: int(row["seed"]))
    if len(dev) != 4:
        raise ValueError(f"expected four development case summaries, found {len(dev)}")

    methods = {
        "ridge": ("Charge-response ridge", "#0072B2", "o"),
        "cheap": ("Cheapest direct = nearest price", "#D55E00", "^"),
        "prior": ("Frozen EdgePrior", "#009E73", "s"),
    }
    offsets = {"ridge": -0.22, "cheap": 0.0, "prior": 0.22}
    x = np.arange(len(dev), dtype=float)
    labels = [f"{row['seed']} · {row['services']} services\n(best S{row['best_two_lp_source'][-1]})" for row in dev]

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 11,
        "axes.labelsize": 9, "svg.fonttype": "none",
    })
    fig, (ax_quality, ax_time) = plt.subplots(
        2, 1, figsize=(10.8, 7.3), gridspec_kw={"height_ratios": [1.12, 0.9]}, sharex=True
    )
    fig.patch.set_facecolor("white")
    for ax in (ax_quality, ax_time):
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
        ax.set_axisbelow(True)

    fields = {
        "ridge": ("ridge_excess_exact", "ridge_acquisition_plus_lp_seconds"),
        "cheap": ("cheapest_direct_excess_exact", "cheapest_direct_acquisition_plus_lp_seconds"),
        "prior": ("frozen_edge_prior_excess_exact", "frozen_edge_prior_acquisition_plus_lp_seconds"),
    }
    for method, (name, color, marker) in methods.items():
        excess = [exact_float(row[fields[method][0]]) for row in dev]
        paid_time = [float(row[fields[method][1]]) for row in dev]
        xx = x + offsets[method]
        ax_quality.vlines(xx, 0, excess, color=color, alpha=0.65, linewidth=1.3, zorder=2)
        ax_quality.scatter(xx, excess, s=58, color=color, marker=marker, edgecolor="white",
                           linewidth=0.8, label=name, zorder=4)
        ax_time.scatter(xx, paid_time, s=58, color=color, marker=marker, edgecolor="white",
                        linewidth=0.8, label=name, zorder=4)
        for xi, yi in zip(xx, excess):
            ax_quality.annotate(f"{yi:.3f}", (xi, yi), xytext=(0, 7 if yi > 0.05 else 6),
                                textcoords="offset points", ha="center", va="bottom", fontsize=7.5,
                                color="#263238")
        for xi, yi in zip(xx, paid_time):
            ax_time.annotate(f"{yi:.1f}", (xi, yi), xytext=(0, 6), textcoords="offset points",
                             ha="center", va="bottom", fontsize=7.5, color="#263238")

    # The post hoc always-source1 diagnostic reproduces the ridge outcomes on
    # these four groups exactly. Draw hollow diamonds over the ridge markers.
    ridge_x = x + offsets["ridge"]
    always_one = [exact_float(row["posthoc_always_source1_excess_exact"]) for row in dev]
    ax_quality.scatter(ridge_x, always_one, s=105, marker="D", facecolors="none",
                       edgecolors="#202124", linewidth=1.15,
                       label="Post hoc always-source1 diagnostic (overlaps ridge)", zorder=5)

    ax_quality.axhline(0, color="#616161", linewidth=0.9)
    ax_quality.set_ylabel("Excess over best of two paid\ncharging LPs (cost units)")
    ax_quality.set_ylim(-0.08, max(0.9, max(exact_float(row["cheapest_direct_excess_exact"]) for row in dev) + 0.18))
    ax_quality.set_title("A. Paired selection quality on four development groups", loc="left", pad=8)

    ax_time.set_xticks(x, labels)
    ax_time.tick_params(axis="x", length=0, pad=8)
    ax_time.set_ylabel("Source acquisition + one selected\ncharging LP (seconds)")
    ax_time.set_ylim(0, max(float(row["cheapest_direct_acquisition_plus_lp_seconds"]) for row in dev) * 1.16)
    ax_time.set_title("B. Paid per-case acquisition and LP time", loc="left", pad=8)

    handles, legend_labels = ax_quality.get_legend_handles_labels()
    fig.legend(handles, legend_labels, frameon=False, fontsize=8, loc="upper center",
               bbox_to_anchor=(0.5, 0.955), ncol=2, columnspacing=1.8)
    fig.suptitle("Charge-response source selection: development costs and timing", y=0.99,
                 fontsize=13, fontweight="semibold")
    fig.text(0.5, 0.018,
             "Open diamonds are a post hoc fixed-source1 diagnostic, not a prospective arm; they coincide with ridge. "
             "Lower panel excludes model generation (11.86 s fit + 5.86 s four-group inference; 27.81 s process total) "
             "because no per-method inference timer was recorded. Synthetic case identifiers; no speedup claim.",
             ha="center", va="bottom", fontsize=7.6, color="#374151", wrap=True)
    fig.tight_layout(rect=(0.04, 0.095, 0.98, 0.88), h_pad=1.6)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_dir / "charge_response_quality_time.png", dpi=220,
                facecolor="white", bbox_inches="tight")
    fig.savefig(args.output_dir / "charge_response_quality_time.svg", facecolor="white",
                bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
