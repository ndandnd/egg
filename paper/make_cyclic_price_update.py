"""Draw the exact undamped price-response cycle; no optimization call."""
from pathlib import Path
from fractions import Fraction as Q

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

def bill(buses, early, prices):
    return Q(7)*buses + prices[0]*early + prices[1]*(30-early)

p_one, p_two = (Q(6),Q(4)), (Q(4),Q(6))
forward = (bill(1,Q(10),p_one), bill(2,Q(0),p_one))
backward = (bill(2,Q(0),p_two), bill(1,Q(10),p_two))
assert forward == (147,134) and backward == (194,167)
# The best two-bus recharging alternative at p_two costs174, still above167.
assert min(bill(2,x,p_two) for x in (Q(0),Q(10))) == 174
assert backward[1] < 174

out = Path(__file__).resolve().parent / "figures"
out.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "pdf.fonttype": 42, "ps.fonttype": 42})
fig, ax = plt.subplots(figsize=(8.6, 3.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis("off")

states = [
    (0.35, "One bus", "Load (10, 20) kWh", "Marginal price (6, 4)", "Next response: two buses"),
    (5.55, "Two buses", "Load (0, 30) kWh", "Marginal price (4, 6)", "Next response: one bus"),
]
for x, title, load, price, response in states:
    rect = FancyBboxPatch((x, 1.15), 4.05, 2.2, boxstyle="round,pad=.12,rounding_size=.15",
                          edgecolor="#156082", facecolor="#EAF4F8", linewidth=1.6)
    ax.add_patch(rect)
    ax.text(x + .18, 3.01, title, fontsize=13, weight="bold", color="#123B51")
    ax.text(x + .18, 2.49, load)
    ax.text(x + .18, 2.07, price)
    ax.text(x + .18, 1.57, response, color="#31596A")

ax.add_patch(FancyArrowPatch((4.58, 2.96), (5.42, 2.96), arrowstyle="-|>",
                             mutation_scale=18, linewidth=1.8, color="#AE6F00"))
ax.text(5.0, 3.72, f"{forward[0]} vs {forward[1]}", ha="center", fontsize=9, color="#855600")
ax.add_patch(FancyArrowPatch((5.42, 1.39), (4.58, 1.39), arrowstyle="-|>",
                             mutation_scale=18, linewidth=1.8, color="#B5493B"))
ax.text(5.0, .80, f"{backward[0]} vs {backward[1]}", ha="center", fontsize=9, color="#91382C")
ax.text(5, .22, "At each step: best response to the posted price, then update price at the new load",
        ha="center", fontsize=9, color="#424A50")
fig.savefig(out / "cyclic_price_update.pdf", bbox_inches="tight", facecolor="white")
fig.savefig(out / "cyclic_price_update.png", dpi=240, bbox_inches="tight", facecolor="white")
plt.close(fig)
