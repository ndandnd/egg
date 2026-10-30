"""Static paired common-32 edge-prediction comparison from strict replay JSON."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
INPUT = HERE / "ROUTE_MODEL64_REPLAY.json"
OUT = HERE / "figures/route_model32_to64_common32"
MODELS = (("logistic", "Logistic", "#407ab5"),
          ("mlp32", "MLP", "#da8a34"),
          ("hist_boosted", "HistGBDT", "#279170"))
PANELS = (("weighted_log_loss", "Weighted log loss ↓"),
          ("input_trip_count_topk_recall_mean_by_fleet", "Input-trip-count top-k recall ↑"))


def plot():
    data = json.loads(INPUT.read_text())
    earlier = data["common32_group_metrics_32fit"]
    later = data["common32_group_metrics_64fit"]
    groups = sorted(earlier)
    if len(groups) != 32 or set(groups) != set(later):
        raise ValueError("Expected the identical 32 TRAIN timetables")
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.7), constrained_layout=True)
    for ax, (metric, title) in zip(axes, PANELS):
        all_values = []
        for model, label, color in MODELS:
            x = np.asarray([earlier[g][model][metric] for g in groups], dtype=float)
            y = np.asarray([later[g][model][metric] for g in groups], dtype=float)
            ax.scatter(x, y, s=20, alpha=.55, color=color, edgecolor="none", label=label)
            ax.scatter([x.mean()], [y.mean()], marker="D", s=90, color=color,
                       edgecolor="white", linewidth=.8, zorder=4)
            all_values.extend(x.tolist()+y.tolist())
        low, high = min(all_values), max(all_values)
        pad = max(.005, (high-low)*.06)
        ax.plot([low-pad, high+pad], [low-pad, high+pad], color="#777777",
                linewidth=1, linestyle="--", zorder=0)
        ax.set(xlim=(low-pad, high+pad), ylim=(low-pad, high+pad),
               xlabel="32-group fit on same timetables", ylabel="64-group fit on same timetables",
               title=title)
        ax.grid(alpha=.18, linewidth=.6)
        ax.set_aspect("equal", adjustable="box")
    axes[0].legend(frameon=False, loc="upper left", fontsize=9)
    fig.suptitle("Observed source-edge prediction · 32 common TRAIN timetables",
                 fontsize=12, fontweight="bold")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        path = OUT.with_suffix("."+extension)
        if path.exists():
            raise ValueError("Versioned figure already exists: "+str(path))
        fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    plot()
