"""Render the six paired scalar rows; no solver or raw trace access."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "compactrows.json").read_text())
rows = data["rows"]
x = np.arange(len(rows))
labels = [f"{r['services']} {'flat' if r['market'] == 'source0' else 'shifted'}"
          for r in rows]

fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6), layout="constrained")
colors = {"lp": "#24547a", "qp": "#bb5536"}
for arm, offset, marker, label in (("lp", -0.13, "o", "Native-LP master"),
                                   ("qp", 0.13, "s", "Numerical-QP proposal")):
    widths = [float(r[f"{arm}_gap_ceil6"]) if r[f"{arm}_gap_ceil6"] else np.nan
              for r in rows]
    seconds = [r[f"{arm}_child_wall_s"] if r[f"{arm}_child_wall_s"] is not None
               else np.nan for r in rows]
    axes[0].scatter(x + offset, widths, color=colors[arm], marker=marker,
                    s=42, label=label, zorder=3)
    axes[1].scatter(x + offset, seconds, color=colors[arm], marker=marker,
                    s=42, label=label, zorder=3)

axes[0].set_yscale("log")
axes[0].axhline(1e-4, color="#555555", linestyle="--", linewidth=1,
                label="Declared $10^{-4}$ width")
axes[0].set_ylabel("Native global width, outward upper bound")
axes[1].set_ylabel("Full child wall time (s)")
for ax in axes:
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.grid(axis="y", color="#dddddd", linewidth=0.7)
    ax.set_xlim(-0.5, len(rows) - 0.5)
axes[0].set_title("Global enclosure quality")
axes[1].set_title("End-to-end child cost")
handles, legend_labels = axes[0].get_legend_handles_labels()
fig.legend(handles, legend_labels, loc="upper center", ncol=3,
           bbox_to_anchor=(0.5, 1.08), frameon=False)
for suffix in ("svg", "png"):
    output = HERE / f"paired_quality_cost.{suffix}"
    fig.savefig(output, dpi=180,
                bbox_inches="tight", facecolor="white")
    if suffix == "svg":
        # Matplotlib indents XML with trailing blanks; keep the checked-in
        # vector artifact LF-terminated without trailing line whitespace.
        output.write_bytes(b"\n".join(line.rstrip(b" \t")
                                      for line in output.read_bytes().splitlines()) + b"\n")
plt.close(fig)
