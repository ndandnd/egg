"""Calibrated study (Section 6): when can assignment-induced support failure
occur for real peak-run energies?

Inputs: ../data/peak_runs.json (calibrate.py). Outputs: ../results/*.json and
../figures/*.pdf. Every number in Section 6 is produced here.

Economics (illustrative, varied in sensitivity grids):
  f        used-bus cost per day, EUR
  s0       zero-load marginal-cost spread, midday minus overnight, EUR/kWh
  rho      price impact: marginal cost in a window rises by rho * pbar when
           the fleet's whole daily energy S is drawn in that window,
           i.e. kappa = rho * pbar / S EUR/kWh^2 in each window.
With L = S - E, the spread at early load E is g(E) = s0 + kappa*(2E - S).
"""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction as Fr

import numpy as np

import twobatch as tb

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "peak_runs.json")
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
PBAR = 0.15  # EUR/kWh reference energy price used only to scale rho


def r_sorted(a, b, B):
    sa, sb = np.sort(a), np.sort(b)
    nu = min(len(a), len(b))
    r = np.zeros(nu + 1)
    for m in range(1, nu + 1):
        r[m] = np.maximum(0.0, sa[:m] + sb[:m][::-1] - B).sum()
    return r


class FloatClass:
    """Float twin of twobatch for large calibrated instances."""

    def __init__(self, a, b, B, K, H, f):
        self.a, self.b = np.asarray(a, float), np.asarray(b, float)
        self.B, self.K, self.H, self.f = B, K, H, f
        self.S = self.a.sum() + self.b.sum()
        self.Lo = max(0.0, self.S - H)
        self.U = min(self.a.sum(), K)
        r = r_sorted(self.a, self.b, B)
        N = len(self.a) + len(self.b)
        self.layers = [(m, max(self.Lo, r[m]), f * (N - m)) for m in range(len(r)) if max(self.Lo, r[m]) <= self.U + 1e-9]
        if not self.layers:
            self.V, self.edges = [], []
            return
        pts = sorted({(lo, c) for _, lo, c in self.layers} | {(self.U, min(c for *_, c in self.layers))})
        ch = []
        for p in pts:
            while len(ch) >= 2:
                (x1, y1), (x2, y2) = ch[-2], ch[-1]
                if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) <= 1e-12 * (1 + abs(y1)):
                    ch.pop()  # strict vertices only (faces)
                else:
                    break
            if ch and abs(ch[-1][0] - p[0]) < 1e-12:
                if p[1] < ch[-1][1]:
                    ch[-1] = p
                continue
            ch.append(p)
        cmin = min(c for _, c in ch)
        k = next(i for i, (_, c) in enumerate(ch) if c <= cmin + 1e-9)
        self.V = ch[: k + 1] + ([(self.U, cmin)] if ch[k][0] < self.U - 1e-12 else [])
        self.edges = [(self.V[i][0], self.V[i + 1][0], (self.V[i][1] - self.V[i + 1][1]) / (self.V[i + 1][0] - self.V[i][0]))
                      for i in range(len(self.V) - 1) if self.V[i + 1][1] < self.V[i][1] - 1e-9]

    def ell_max(self):
        return max((x2 - x1 for x1, x2, _ in self.edges), default=0.0)

    # G(E) = s0*E + kappa*(E^2 + (S-E)^2)/2 up to a constant; g = G'
    @staticmethod
    def _G(E, S, s0, kap):
        return s0 * E + kap * (E * E + (S - E) ** 2) / 2.0

    def solve(self, s0, kap):
        S = self.S
        g0, curv = s0 - kap * S, 2 * kap

        def argmin(lo, hi, lin):
            if curv > 0:
                return min(max(-lin / curv, lo), hi)
            return lo if lin >= 0 else hi

        D, ED, cD = np.inf, None, None
        for _, lo, c in self.layers:
            E = argmin(lo, self.U, g0)
            v = c + self._G(E, S, s0, kap)
            if v < D:
                D, ED, cD = v, E, c
        CH, Es = np.inf, None
        if len(self.V) == 1:
            CH, Es = self.V[0][1] + self._G(self.V[0][0], S, s0, kap), self.V[0][0]
        for i in range(len(self.V) - 1):
            (x1, y1), (x2, y2) = self.V[i], self.V[i + 1]
            sl = (y2 - y1) / (x2 - x1)
            E = argmin(x1, x2, g0 + sl)
            v = y1 + sl * (E - x1) + self._G(E, S, s0, kap)
            if v < CH:
                CH, Es = v, E
        # own-marginal-price regret of the planner optimum (Prop. 2)
        pi = g0 + curv * ED
        resp = min(c + pi * E for _, lo, c in self.layers for E in (lo, self.U))
        regret = cD + pi * ED - resp
        return dict(D=D, CH=CH, gap=max(0.0, D - CH), ED=ED, Es=Es, regret=max(0.0, regret), pi_D=pi)


def iterate_float(X, s0, kap, a=1.0, iters=400, tol=1e-10):
    """Flagship-style state-based price iteration on the scalar spread."""
    g = lambda E: s0 + kap * (2 * E - X.S)
    pts = [(E, c) for _, lo, c in X.layers for E in (lo, X.U)]
    pi = g(X.Lo)
    hist = [pi]
    for k in range(iters):
        E = min(pts, key=lambda p: (p[1] + pi * p[0], p[0]))[0]
        nxt = (1 - a) * pi + a * g(E)
        if abs(nxt - pi) <= tol * (1 + abs(pi)):
            return "fixed_point"
        if any(abs(nxt - h) <= tol * (1 + abs(h)) for h in hist[:-1]):
            return "cycle"
        hist.append(nxt)
        pi = nxt
    return "none"


def check_against_exact():
    rng = np.random.default_rng(0)
    for _ in range(200):
        n = rng.integers(1, 6)
        a = rng.integers(1, 30, n)
        b = rng.integers(1, 30, rng.integers(1, 6))
        B = int(max(a.max(), b.max()) + rng.integers(0, 10))
        K = int(rng.integers(0, a.sum() + 3))
        H = int(rng.integers(max(0, a.sum() + b.sum() - K), a.sum() + b.sum() + 5))
        f = int(rng.integers(1, 10))
        s0, kap = float(rng.integers(-8, 8)) / 4, float(rng.integers(1, 20)) / 40
        I = tb.Instance(list(map(int, a)), list(map(int, b)), B, K, H, f)
        if not tb.layers(I):
            continue
        X = FloatClass(a, b, B, K, H, f)
        sup = tb.Supply(Fr(s0) - Fr(kap) * I.S, Fr(kap), 0, Fr(kap))  # same g and curvature
        ex = tb.gap(I, sup)
        fl = X.solve(s0, kap)["gap"]
        assert abs(float(ex) - fl) < 1e-7 * (1 + abs(float(ex))), (float(ex), fl)


def load_ops(min_runs=5):
    d = json.load(open(DATA))
    return [o for o in d["operators"] if "error" not in o and min(len(o["a_kwh"]), len(o["b_kwh"])) >= min_runs], d["meta"]


def critical_spreads(ops, Bs=(400, 450, 500), fs=(100, 150, 200)):
    out = []
    for o in ops:
        for B in Bs:
            a = [x for x in o["a_kwh"] if x <= B]
            b = [x for x in o["b_kwh"] if x <= B]
            X = FloatClass(a, b, B, K=sum(a), H=sum(a) + sum(b), f=1.0)
            r = r_sorted(np.array(a), np.array(b), B)
            for f in fs:
                lm = X.ell_max()
                out.append(dict(operator=o["operator"], B=B, f=f, nA=len(a), nB=len(b),
                                dropped=len(o["a_kwh"]) + len(o["b_kwh"]) - len(a) - len(b),
                                n_pairs_free=int((r == 0).sum() - 1), nu=len(r) - 1,
                                ell_max_kwh=lm, pi_crit=(f / lm if lm > 0 else None),
                                S_kwh=X.S, P_kwh=sum(a)))
    return out


def sweep(ops, B=400, f=150.0, K_frac=1.0, s0_grid=None, rho_grid=None, with_iter=True):
    s0_grid = s0_grid if s0_grid is not None else np.round(np.linspace(-0.2, 1.6, 37), 3)
    rho_grid = rho_grid if rho_grid is not None else [0.0, 0.5, 1.0, 2.0, 4.0]
    rows = []
    for o in ops:
        a = [x for x in o["a_kwh"] if x <= B]
        b = [x for x in o["b_kwh"] if x <= B]
        X = FloatClass(a, b, B, K=K_frac * sum(a), H=sum(a) + sum(b), f=f)
        for rho in rho_grid:
            kap = rho * PBAR / X.S
            for s0 in s0_grid:
                r = X.solve(float(s0), kap)
                it = iterate_float(X, float(s0), kap) if with_iter else None
                rows.append(dict(undamped=it, operator=o["operator"], B=B, f=f, K_frac=K_frac, rho=rho, s0=float(s0),
                                 gap=r["gap"], D=r["D"], regret=r["regret"],
                                 rel_gap=r["gap"] / abs(r["D"]) if r["D"] else 0.0,
                                 rel_regret=r["regret"] / abs(r["D"]) if r["D"] else 0.0))
    return rows


def main():
    os.makedirs(RES, exist_ok=True)
    check_against_exact()
    ops, meta = load_ops()
    crit = critical_spreads(ops, Bs=(250, 300, 350, 400), fs=(50, 100, 150, 200))
    sweeps = {f"B{B}_K{kf}": sweep(ops, B=B, K_frac=kf) for B in (300, 400) for kf in (1.0, 0.5)}
    json.dump(dict(meta=meta, pbar=PBAR, operators=[o["operator"] for o in ops], critical=crit,
                   sweeps=sweeps), open(os.path.join(RES, "study.json"), "w"), indent=0)
    summary = dict(n_operators=len(ops))
    for B in (250, 300, 350, 400):
        base = [c for c in crit if c["B"] == B and c["f"] == 150]
        pc = sorted(c["pi_crit"] for c in base if c["pi_crit"])
        summary[f"B{B}"] = dict(n_gap_possible=len(pc), pi_crit_min=pc[0] if pc else None,
                                pi_crit_median=float(np.median(pc)) if pc else None)
    for name, S in sweeps.items():
        g = [r for r in S if r["gap"] > 1e-9]
        summary[name] = dict(cells=len(S), gap_cells=len(g),
                             gap_cells_s0_le_0p3=sum(1 for r in g if r["s0"] <= 0.3),
                             max_rel_gap=max((r["rel_gap"] for r in g), default=0.0),
                             median_regret_over_gap=float(np.median([r["regret"] / r["gap"] for r in g])) if g else None,
                             undamped_cycle_cells=sum(1 for r in S if r["undamped"] == "cycle"),
                             undamped_cycle_cells_zero_gap=sum(1 for r in S if r["undamped"] == "cycle" and r["gap"] <= 1e-9),
                             undamped_none=sum(1 for r in S if r["undamped"] == "none"))
    json.dump(summary, open(os.path.join(RES, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
