"""Transparent finite-run dual replay of the exact EGG quadratic example."""
from __future__ import annotations

import csv
import json
import math
import time
from fractions import Fraction as Q
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CH = float(Q(7591, 80))


def fleet_response(p):
    early = 0.0 if p[0] >= p[1] else 10.0
    one = 7 + 10 * p[0] + 20 * p[1]
    two = 14 + early * p[0] + (30 - early) * p[1]
    return (1, (10.0, 20.0), one) if one <= two else (2, (early, 30 - early), two)


def run(iterations=20000):
    p = [6.0, 4.0]
    rows = []
    best = -math.inf
    one_count = switches = 0
    previous = None
    total_weight = weighted_one = 0.0
    total_load = [0.0, 0.0]
    weighted_load = [0.0, 0.0]
    started = time.perf_counter()
    for k in range(1, iterations + 1):
        if time.perf_counter() - started > 30:
            raise TimeoutError("Declared 30-second analytic replay budget exceeded")
        buses, load, value = fleet_response(p)
        supply = [5 * max(p[0] - 4, 0), 5 * max(p[1], 0)]
        conjugate = 2.5 * (max(p[0] - 4, 0) ** 2 + max(p[1], 0) ** 2)
        supply_cost = 4 * supply[0] + (supply[0] ** 2 + supply[1] ** 2) / 10
        assert abs(conjugate - (sum(a * b for a, b in zip(p, supply)) - supply_cost)) < 1e-9
        dual = value - conjugate
        assert dual <= CH + 1e-10
        best = max(best, dual)
        alpha = 0.5 / math.sqrt(k)
        one_count += buses == 1
        weighted_one += alpha * (buses == 1)
        total_weight += alpha
        switches += previous is not None and previous != buses
        previous = buses
        for t in range(2):
            total_load[t] += load[t]
            weighted_load[t] += alpha * load[t]
        rows.append(dict(k=k, price_early=p[0], price_terminal=p[1],
                         dual_current=dual, dual_best=best, buses=buses,
                         fleet_early=load[0], supply_early=supply[0],
                         supply_terminal=supply[1],
                         mismatch_l2=math.dist(load, supply),
                         one_bus_share=one_count / k,
                         one_bus_step_weighted_share=weighted_one / total_weight,
                         mean_early=total_load[0] / k,
                         step_weighted_mean_early=weighted_load[0] / total_weight,
                         switches=switches))
        p = [max(0.0, p[t] + alpha * (load[t] - supply[t])) for t in range(2)]
    seconds = time.perf_counter() - started
    return rows, seconds


def main():
    rows, seconds = run()
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    with (out / "quadratic_trace.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    claim_price = (Q(11, 2), Q(9, 2))
    claim_v = min(Q(7) + 10 * claim_price[0] + 20 * claim_price[1],
                  Q(14) + 30 * claim_price[1])
    claim_dual = claim_v - Q(5, 2) * ((claim_price[0] - 4) ** 2 + claim_price[1] ** 2)
    assert claim_dual == Q(371, 4)
    receipt = dict(protocol="SUBGRADIENT_PROTOCOL.md", iterations=len(rows),
                   analytic_oracle_calls=len(rows), loop_seconds=seconds,
                   initialization=[6, 4], step="0.5/sqrt(k)",
                   checkpoint_convention="Before update, current and best dual separate",
                   exact_reference=dict(CH="7591/80", prices=["107/20", "93/20"],
                                        one_bus_hull_weight="27/40"),
                   pasted_price_current_dual=str(claim_dual),
                   checkpoints=[rows[k - 1] for k in (1, 100, 1000, 20000)],
                   last_60_switches=sum(rows[i]["buses"] != rows[i - 1]["buses"]
                                        for i in range(len(rows) - 59, len(rows))),
                   scope="Cheap analytic development replay; no fleet MIP or convergence proof")
    (out / "quadratic_summary.json").write_text(json.dumps(receipt, indent=2) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 3, figsize=(10, 2.8), layout="constrained")
    k = [r["k"] for r in rows]
    axes[0].plot(k, [r["price_early"] for r in rows], lw=.65, color="#16677b", label="Early")
    axes[0].plot(k, [r["price_terminal"] for r in rows], lw=.65, color="#b35528", label="Terminal")
    axes[0].axhline(5.35, ls="--", color="#16677b", lw=.7)
    axes[0].axhline(4.65, ls="--", color="#b35528", lw=.7)
    axes[0].set(xscale="log", xlabel="Analytic oracle call", ylabel="Posted price",
                title="Prices approach hull targets")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].plot(k, [max(CH - r["dual_current"], 1e-12) for r in rows], lw=.5,
                 alpha=.7, color="#8b99a2", label="Current")
    axes[1].plot(k, [max(CH - r["dual_best"], 1e-12) for r in rows], lw=1.1,
                 color="#16677b", label="Best so far")
    axes[1].set(xscale="log", yscale="log", xlabel="Analytic oracle call",
                ylabel="Exact CH minus dual bound", title="Different dual diagnostics")
    axes[1].legend(frameon=False, fontsize=8)
    axes[2].step(k[-60:], [r["buses"] for r in rows[-60:]], where="mid", lw=.8, color="#16677b")
    axes[2].set(yticks=[1, 2], ylim=(.85, 2.15), xlabel="Analytic oracle call",
                ylabel="Buses in response", title="Switching persists in this run")
    axes[2].ticklabel_format(axis="x", style="plain", useOffset=False)
    for ax in axes:
        ax.grid(alpha=.15)
    for ext in ("pdf", "png", "svg"):
        fig.savefig(ROOT / "paper" / "latex" / "figures" / f"quadratic_dual_replay.{ext}", dpi=200)
    plt.close(fig)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
