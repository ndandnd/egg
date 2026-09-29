"""Plot exact algebra from REVIEW.md; performs no optimization."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
fig, (dispatch, costs) = plt.subplots(1, 2, figsize=(9.6, 3.5), layout="constrained")
t = np.arange(3)
dispatch.bar(t, [5, 10, 15], color="#176e83", label="Generator A", width=.65)
dispatch.bar(t, [0, 5, 10], bottom=[5, 10, 15], color="#d5a664", label="Generator B", width=.65)
dispatch.plot(t, [5, 10, 15], "o--", color="#143f4a", lw=1, ms=4)
for j, (label, top) in enumerate(zip(["5 fleet", "15 background", "25 fleet"], [5, 15, 25])):
    dispatch.text(j, top + .8, label, ha="center", fontsize=9)
dispatch.set(xticks=t, xticklabels=["Early\n[1, 2]", "Service B\n[2, 3]", "Terminal\n[3, 4]"],
             ylim=(0, 31), ylabel="Hourly generation (kWh)", title="Dispatch at the hull mean")
dispatch.legend(frameon=False, loc="upper left", fontsize=9)
dispatch.grid(axis="y", alpha=.15)
x = np.linspace(0, 10, 401)
g = np.where(x <= 5, 110 - 2*x, 95 + x)
costs.plot(x, g + 14, color="#a95731", lw=1.8, label="Physical two-bus branch")
costs.plot(x, g + 14 - .7*x, color="#176e83", lw=1.8, label="Complete-fleet hull")
costs.axhline(112, color="#707b83", ls=":", lw=1)
costs.scatter([10], [112], color="#202a32", s=40, zorder=4, label="Physical one-bus optimum")
costs.scatter([5], [110.5], color="#176e83", marker="*", s=100, zorder=4)
costs.annotate("CH = 110.5", (5, 110.5), xytext=(5.45, 109.3), fontsize=9)
costs.text(.35, 112.35, "D = 112", fontsize=9, color="#4a555b")
costs.set(xlabel="Early fleet energy x (kWh)", ylabel="Incremental system cost",
          xlim=(-.2, 10.5), ylim=(108.5, 126), title="Exact gap: 1.5 cost units")
costs.legend(frameon=False, fontsize=8.5, loc="upper right")
costs.grid(alpha=.15)
for ext in ("png", "pdf", "svg"):
    fig.savefig(ROOT / "paper/latex/figures" / f"ramped_generation_example.{ext}", dpi=200)
plt.close(fig)
