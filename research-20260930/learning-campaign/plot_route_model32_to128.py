"""Plot predeclared 32/64/128 fits on the exact same 32 TRAIN timetables."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
INPUT = HERE / "ROUTE_MODEL128_REPLAY.json"
OUT = HERE / "figures/route_model32_to128_common32"
MODELS = (("logistic", "Logistic", "#397ab8"),
          ("mlp32", "MLP32", "#dd8a32"),
          ("hist_boosted", "HistGBDT", "#258e70"))
PANELS = (("weighted_log_loss", "Weighted log loss ↓"),
          ("input_trip_count_topk_recall_mean_by_fleet", "Input-trip-count top-k recall ↑"))
SIZES = (32, 64, 128)


def plot():
    artifact = json.loads(INPUT.read_text())
    by_size = {size: artifact[f"common32_group_metrics_{size}fit"] for size in SIZES}
    groups = sorted(by_size[32])
    if len(groups) != 32 or any(set(by_size[size]) != set(groups) for size in SIZES):
        raise ValueError("The fixed common-32 cohort changed")
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.3), constrained_layout=True)
    for ax, (metric, title) in zip(axes, PANELS):
        for name, label, color in MODELS:
            values = np.array([[by_size[size][group][name][metric] for group in groups]
                               for size in SIZES], dtype=float)
            means = values.mean(axis=1)
            lo, hi = np.quantile(values, (.25, .75), axis=1)
            ax.fill_between(SIZES, lo, hi, color=color, alpha=.11, linewidth=0)
            ax.plot(SIZES, means, marker="o", color=color, linewidth=2.1,
                    markersize=5, label=label)
        ax.set(xlabel="TRAIN bank size (fit groups per fold: 20 / 40 / 80)",
               ylabel="Outer metric on the same original 32 timetables", title=title,
               xticks=SIZES, xlim=(29, 131))
        ax.grid(alpha=.22, linewidth=.7)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Saved-model learning curve · observed source-edge prediction",
                 fontsize=12, fontweight="bold")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        path = OUT.with_suffix("."+extension)
        if path.exists():
            raise ValueError("Versioned figure already exists: " + str(path))
        fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    plot()
