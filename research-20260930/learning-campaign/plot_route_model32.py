"""Plot already replayed per-timetable edge metrics; never fit or score models."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "ROUTE_MODEL32_REPLAY.json"
OUT = HERE / "figures"
STEM = "route_model32_grouped_comparison"
METHODS = (
    ("constant", "Constant", "#8c8c8c"),
    ("kind_frequency", "Kind freq.", "#3a7ca5"),
    ("logistic", "Logistic", "#4e9b75"),
    ("mlp32", "MLP", "#9370b3"),
    ("hist_boosted", "Boosted", "#d47638"),
)
PANELS = (
    ("weighted_log_loss", "Held-out edge log loss", "Lower is better"),
    ("input_trip_count_topk_recall_mean_by_fleet", "Trip-count top-k recall", "Higher is better"),
)


def main():
    evidence = json.loads(EVIDENCE.read_text())
    if (evidence.get("schema") != "physical-route32-replay-v1"
            or evidence.get("strict_saved_model_replay") is not True
            or evidence.get("independent_outer_groups") != 32):
        raise ValueError("Expected strict saved-model replay for 32 independent groups")
    groups = evidence["per_group_seed_and_source_averages"]
    if len(groups) != 32:
        raise ValueError("Missing held-out timetable groups")
    ordered = sorted(groups)
    fig, axes = plt.subplots(1, 2, figsize=(12.3, 5.6))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.25, top=0.78, wspace=0.24)
    fig.suptitle("Physical source-route edge prediction only", y=0.97,
                 fontsize=15, fontweight="bold")
    offsets = np.linspace(-0.16, 0.16, len(ordered))
    for ax, (metric, title, direction) in zip(axes, PANELS):
        values = np.asarray([[groups[g][method][metric] for method, _, _ in METHODS]
                             for g in ordered], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Nonfinite group metric")
        for row in values:
            ax.plot(range(len(METHODS)), row, color="#7f8992", alpha=0.12,
                    linewidth=0.55, zorder=1)
        for j, (_, label, color) in enumerate(METHODS):
            ax.scatter(j + offsets, values[:, j], s=20, color=color, alpha=0.68,
                       edgecolors="none", zorder=2)
            mean = values[:, j].mean()
            ax.scatter(j, mean, marker="D", s=76, facecolor="white",
                       edgecolor="#1a2630", linewidth=1.55, zorder=4)
        ax.set_xticks(range(len(METHODS)), [label for _, label, _ in METHODS])
        ax.set_xlim(-0.45, len(METHODS)-0.55)
        ax.set_title(f"{title}\n{direction}", fontsize=12)
        ax.set_ylabel(title)
        ax.grid(axis="y", color="#dfe5e8", linewidth=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelrotation=12)
    fig.text(0.5, 0.055,
        "n = 32 independent timetables • 3 seeds and 2 source fleets averaged within timetable • diamond = mean",
        ha="center", va="bottom", fontsize=9, color="#33434d")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{STEM}.png", dpi=220, facecolor="white", bbox_inches="tight")
    fig.savefig(OUT / f"{STEM}.pdf", facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(OUT / f"{STEM}.png")


if __name__ == "__main__":
    main()
