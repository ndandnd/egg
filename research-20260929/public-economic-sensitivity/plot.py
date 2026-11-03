"""Plot all eight public development cells from reviewed compact rows only."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from summarize import CELLS, directed


def render(data, out):
    rows = data["rows"]
    if [(r["case"], r["market"]) for r in rows] != list(CELLS):
        raise ValueError("Figure requires all eight cells in declared order")
    if data.get("global_integrity_ok") is not True:
        raise ValueError("Do not render an unreviewable unsealed attempt")
    out.mkdir(parents=True, exist_ok=True)
    labels = [f"Depot {r['depot'][-2:]}   f={r['bus_fee']}, κ×{r['curvature_multiplier']}"
              for r in rows]
    positions = list(range(len(rows)))[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.7), sharey=True)
    for ax, field, title in ((axes[0], "gap", "Physical minus hull cost"),
                             (axes[1], "regret", "Returned-schedule own-price regret")):
        intervals = [r["native_combined"]["gap_exact"]
                     if field == "gap" and r["native_combined"] else
                     r["regret_exact"] if field == "regret" else None for r in rows]
        xmax = max([float(Fraction(v[1])) for v in intervals if v] + [1.0])
        limit = xmax * 1.40
        for pos, row, values in zip(positions, rows, intervals):
            color = "#24547a" if row["depot"].endswith("15") else "#a9552c"
            if values is None:
                ax.text(.02 * limit, pos, "insufficient evidence", va="center",
                        fontsize=9, color="#666666")
                continue
            lo, hi = map(lambda x: float(Fraction(x)), values)
            ax.plot([lo, hi], [pos, pos], color=color, linewidth=4,
                    solid_capstyle="butt", alpha=.75)
            ax.plot([lo, hi], [pos, pos], "|", color=color, markersize=12)
            if lo == 0:
                ax.plot(0, pos, "o", markerfacecolor="white", markeredgecolor=color,
                        markersize=5, zorder=4)
            digits = 6 if hi < .001 else 2
            label = f"[{directed(values[0], digits)}, {directed(values[1], digits, upper=True)}]"
            ax.text(hi + .018 * limit, pos, label, va="center", fontsize=8.5,
                    color=color)
        for y in (1.5, 3.5, 5.5):
            ax.axhline(y, color="#e5e5e5", linewidth=.7)
        ax.set_xlim(-.015 * limit, limit)
        ax.set_ylim(-.55, 7.55)
        ax.set_yticks(positions, labels)
        ax.set_xlabel("Declared cost units")
        ax.set_title(title, fontsize=12, pad=12)
        ax.grid(axis="x", color="#dddddd", linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].tick_params(labelleft=False)
    fig.legend(handles=[Line2D([0], [0], color="#24547a", lw=4, label="Depot 15"),
                        Line2D([0], [0], color="#a9552c", lw=4, label="Depot 16")],
               loc="upper center", ncol=2, frameon=False)
    fig.text(.5, .012, "Native solver/replay tolerances apply. Regret concerns the returned schedule; "
             "planner uncertainty is reported in the table.\n"
             "Both depots and all parameter settings belong to one public timetable group.",
             ha="center", fontsize=9, color="#444444")
    fig.subplots_adjust(left=.20, right=.98, bottom=.16, top=.86, wspace=.15)
    for suffix in ("png", "svg"):
        dest = out / f"public_economic_intervals.{suffix}"
        fig.savefig(dest, dpi=190, facecolor="white", bbox_inches="tight")
        if suffix == "svg":
            dest.write_bytes(b"\n".join(line.rstrip() for line in dest.read_bytes().splitlines()) + b"\n")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compact", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    render(json.loads(args.compact.read_text()), args.out)
