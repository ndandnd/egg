"""Figures for draft1. Run after study.py: python3 figures.py"""
from __future__ import annotations

import json
import os
from fractions import Fraction as Fr

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import twobatch as tb

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
RES = os.path.join(HERE, "..", "results")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # fixed categorical order
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 1.6,
    "legend.frameon": False, "pdf.fonttype": 42,
})


def fig_anchor():
    inst = tb.Instance([5, 15], [14, 15], 20, 15, 49, 7)
    sup = tb.Supply(4, Fr(1, 10), 0, Fr(1, 10))
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.6, 2.8))
    for k, Ly in enumerate(tb.layers(inst)):
        ax.plot([float(Ly.lo), float(Ly.hi)], [float(Ly.cost)] * 2, color=SERIES[0], lw=2.4, solid_capstyle="round")
        ax.text(float(Ly.hi) + 0.3, float(Ly.cost), f"$m={Ly.m}$", va="center", color=INK2, fontsize=7.5)
    V = tb.hull_vertices(inst)
    ax.plot([float(x) for x, _ in V], [float(y) for _, y in V], color=SERIES[1], lw=1.2, ls=(0, (4, 2)), label="hull boundary")
    _, Es, _ = tb.hull_opt(inst, sup)
    ED = tb.physical_opt(inst, sup)[1]
    ax.scatter([float(Es)], [21 - 7 * float(Es) / 9], s=28, color=SERIES[1], zorder=5, edgecolor="white", linewidth=1.2)
    ax.annotate(r"hull optimum $E^\ast=151/18$", (float(Es), 21 - 7 * float(Es) / 9), (2.2, 16.0), fontsize=7.5,
                color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.scatter([float(ED)], [14], s=28, color=SERIES[0], zorder=5, edgecolor="white", linewidth=1.2)
    ax.annotate("physical optimum", (float(ED), 14), (10.0, 17.5), fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.set_xlabel("midday grid energy $E$ (kWh)")
    ax.set_ylabel("vehicle cost $fN_m$")
    ax.set_xlim(-0.5, 18)
    ax.set_ylim(12, 30)
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.62), fontsize=7.5)
    ax.set_title("(a) physical layers and their hull", fontsize=8.5, loc="left", color=INK)

    pistar = float(sup.g(inst, Es))
    runs = [("undamped, $a=1$", 1.0, SERIES[0]), ("constant $a=0.2$", 0.2, SERIES[2]),
            ("diminishing $a_k=1/(k+2)$", lambda k: 1.0 / (k + 2), SERIES[1])]
    for lab, a, col in runs:
        out = tb.iterate(inst, sup, 0.0, a, max_iter=40)
        p = [float(x) for x in out["pis"]]
        while len(p) < 41:  # extend an exactly detected cycle for display
            p.append(p[-2])
        bx.plot(range(41), p[:41], color=col, lw=1.3, label=lab, marker="o", ms=2.2)
    bx.axhline(pistar, color=INK2, lw=0.8, ls=(0, (2, 2)))
    bx.text(40.5, pistar, r" $\pi^\ast=7/9$", ha="left", va="center", fontsize=7.5, color=INK2)
    bx.set_xlabel("iteration $k$")
    bx.set_ylabel(r"posted spread $\pi_k$ (per kWh)")
    bx.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), fontsize=7, ncol=3, handlelength=1.5, columnspacing=0.8)
    bx.set_title("(b) price iteration", fontsize=8.5, loc="left", color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "anchor.pdf"))


def fig_critical():
    d = json.load(open(os.path.join(RES, "study.json")))
    crit = [c for c in d["critical"] if c["f"] == 150]
    ops = sorted({c["operator"] for c in crit})
    nice = {o: o.split("__", 1)[1].replace("_", " ")[:24] for o in ops}
    Bs = [250, 300, 350, 400]
    order = sorted(ops, key=lambda o: min([c["pi_crit"] or 1e9 for c in crit if c["operator"] == o]))
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    cap = 60.0
    for j, B in enumerate(Bs):
        ys, xs, hollow = [], [], []
        for i, o in enumerate(order):
            c = next(c for c in crit if c["operator"] == o and c["B"] == B)
            y = i + (j - 1.5) * 0.17
            if c["pi_crit"] is None:
                hollow.append((cap, y))
            else:
                xs.append(c["pi_crit"])
                ys.append(y)
        ax.scatter(xs, ys, s=16, color=SERIES[j], label=f"$B={B}$ kWh", zorder=3, edgecolor="white", linewidth=0.6)
        if hollow:
            ax.scatter([h[0] for h in hollow], [h[1] for h in hollow], s=14, facecolor="none", edgecolor=SERIES[j], linewidth=0.9, zorder=3)
    ax.set_xscale("log")
    ax.set_xlim(0.4, 80)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([nice[o] for o in order], fontsize=7)
    ax.invert_yaxis()
    ax.axvline(cap, color=GRID, lw=6, zorder=1)
    ax.text(cap, -1.1, "no gap\npossible", ha="center", fontsize=7, color=INK2)
    ax.set_xlabel(r"critical marginal-cost spread $f/\delta_{\max}$ (EUR/kWh), $f=150$ EUR/day")
    ax.legend(loc="lower right", fontsize=7.5, ncol=2)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "critical.pdf"))


def fig_sweep():
    d = json.load(open(os.path.join(RES, "study.json")))
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.4))
    rows = d["sweeps"]["B300_K1.0"]
    s0s = sorted({r["s0"] for r in rows})
    rhos = [0.5, 1.0, 2.0, 4.0]
    for j, rho in enumerate(rhos):
        cyc = [sum(1 for r in rows if r["s0"] == s and r["rho"] == rho and r["undamped"] == "cycle") for s in s0s]
        axs[0].plot(s0s, cyc, color=SERIES[j], lw=1.3, label=rf"$\rho={rho:g}$")
        gp = [sum(1 for r in rows if r["s0"] == s and r["rho"] == rho and r["gap"] > 1e-9) for s in s0s]
        axs[1].plot(s0s, gp, color=SERIES[j], lw=1.3, marker="o", ms=2.5, label=rf"$\rho={rho:g}$")
    axs[0].set_title("(a) undamped iteration cycles", fontsize=8.5, loc="left", color=INK)
    axs[1].set_title(r"(b) positive gap $\Delta>0$", fontsize=8.5, loc="left", color=INK)
    for ax in axs:
        ax.set_xlabel(r"zero-load spread $s_0$ (EUR/kWh)")
        ax.set_ylim(-0.5, 17.5)
    axs[0].set_ylabel(f"operators (of {len(d['operators'])}), $B=300$ kWh")
    axs[0].legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sweep.pdf"))


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    fig_anchor()
    fig_critical()
    fig_sweep()
    print("figures written to", os.path.abspath(FIG))
