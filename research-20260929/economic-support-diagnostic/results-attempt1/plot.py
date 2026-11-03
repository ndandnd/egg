"""Plot paired native gap and named-incumbent regret from compact rows only."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np


HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "compactrows.json").read_text())["rows"]
labels = [f"{r['services']} {'flat' if r['market'] == 'source0' else 'shifted'}"
          for r in rows]
y = np.arange(len(rows))[::-1]
fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.4), sharey=True,
                         layout="constrained")

for ax, quantity, title, limit in (
        (axes[0], "gap", "Physical minus hull cost", .17),
        (axes[1], "regret", "Named-incumbent own-price regret", .65)):
    for pos, row in zip(y, rows):
        lo = float(row[f"{quantity}_lower_floor6"])
        hi = float(row[f"{quantity}_upper_ceil6"])
        if lo > 0:
            ax.barh(pos, hi, height=.44, color="#b9d1df", zorder=2)
            ax.barh(pos, lo, height=.44, color="#24547a", zorder=3)
            ax.text(hi + .012 * limit, pos, f"{lo:.6f}–{hi:.6f}",
                    va="center", ha="left", fontsize=8.5)
        else:
            ax.plot(0, pos, "o", mfc="white", mec="#bb5536", ms=6, zorder=4)
            ax.text(.02 * limit, pos, f"0–{hi:.0e}",
                    va="center", ha="left", fontsize=8.5, color="#8e3d27")
    ax.set_xlim(0, limit)
    ax.set_ylim(-.55, len(rows) - .45)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Synthetic cost units")
    ax.set_title(title)
    ax.grid(axis="x", color="#e2e2e2", linewidth=.7)
    ax.set_axisbelow(True)
axes[1].tick_params(labelleft=True)
fig.legend(handles=[Patch(facecolor="#24547a", label="Certified lower amount"),
                    Patch(facecolor="#b9d1df", label="Interval to upper bound"),
                    plt.Line2D([], [], marker="o", linestyle="", mfc="white",
                               mec="#bb5536", label="Zero-compatible")],
           loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(.5, 1.07))
for suffix in ("svg", "png"):
    output = HERE / f"joint_economic_evidence.{suffix}"
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    if suffix == "svg":
        output.write_bytes(b"\n".join(line.rstrip(b" \t")
                                      for line in output.read_bytes().splitlines()) + b"\n")
plt.close(fig)
