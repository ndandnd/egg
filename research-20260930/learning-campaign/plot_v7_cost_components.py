"""Plot the reviewed saved-load decomposition; no model fitting or solves."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "V7_COST_COMPONENT_DIAGNOSIS.json").read_text())
assert data["all_exact_component_identities_passed"]
arms = ("tabular_v3", "families_v5", "graph_v6")
rows = [data["common15_summary"][arm]["mean_delta"] for arm in arms]
components = (
    ("linear_quantity_reference_high_tariff", "Energy quantity at high-tariff reference", "#466C98"),
    ("linear_cheap_period_discount", "Change in cheap-period discount", "#CB7750"),
    ("quadratic", "Quadratic supply cost", "#65A393"),
)
values = np.array([[row[key]["value"] for row in rows] for key, _, _ in components])
totals = np.array([row["bill"]["value"] for row in rows])
assert all(row["operations"]["value"] == 0 for row in rows)
assert np.allclose(values.sum(axis=0), totals, rtol=0, atol=1e-12)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(8.5, 5.4))
x = np.arange(3)
positive = np.zeros(3)
negative = np.zeros(3)
for (key, label, color), ys in zip(components, values):
    bottom = np.where(ys >= 0, positive, negative)
    ax.bar(x, ys, bottom=bottom, width=0.54, color=color, label=label)
    positive += np.maximum(ys, 0)
    negative += np.minimum(ys, 0)
ax.scatter(x, totals, marker="D", s=42, c="#202020", edgecolors="white", linewidth=0.7,
           zorder=4, label="Net bill difference")
for xi, total, top in zip(x, totals, positive):
    ax.text(xi, top + 0.13, f"Net +{total:.2f}", ha="center", weight="bold")
ax.axhline(0, color="#505050", linewidth=0.8)
ax.set_xticks(x, ["Tabular", "Tree-family policy", "Graph policy"])
ax.set_ylabel("Mean cost difference from reused plans\n(positive = more expensive)")
ax.set_ylim(-1.45, 5.6)
ax.set_title("Same fleet size, different charging bills", loc="left", weight="bold", pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.16)
ax.set_axisbelow(True)
fig.legend(*ax.get_legend_handles_labels(), loc="lower left", bbox_to_anchor=(0.12, 0.12),
           frameon=False, fontsize=9, ncol=2)
fig.text(0.12, 0.085, "15 common complete TRAIN cases; all vehicle-count and operations-cost differences are zero.", fontsize=9)
fig.text(0.12, 0.055, "Case 10069 is missing for two learned methods; tabular's all-16 mean remains +7.57.", fontsize=9)
fig.text(0.12, 0.025, "Saved-load accounting identities, not causal effects or a final test-set evaluation.", fontsize=9, color="#555555")
fig.subplots_adjust(left=0.12, right=0.98, bottom=0.31, top=0.90)
out = HERE / "figures"
out.mkdir(exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(out / f"v7_cost_component_diagnosis.{ext}", dpi=180)
plt.close(fig)
