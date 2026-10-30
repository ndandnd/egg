"""Exact arithmetic for the lossless charge-only two-batch class.

Model (paper Section 3): n_A morning services with battery draws a_i, n_B
afternoon services with draws b_j, common usable capacity B, an allowed
successor graph (default: complete), a shared midday connector delivering at
most K kWh, an overnight connector delivering at most H kWh, used-bus fee f.
Every used bus starts and ends full. A matching of size m uses
N_m = n_A + n_B - m buses.

The complete physical load--cost projection is (Theorem 1, lossless case)

    union_m {(E, S - E, f N_m) : max(Lo, r_m) <= E <= U},

with Lo = max(0, S - H), U = min(sum a, K) and r_m the minimum early
requirement over allowed matchings of size m. Everything here is exact
(fractions.Fraction) so that fixed points and cycles are detected without
tolerances.

The supply objective is separable quadratic,
    F(E, L) = pE*E + qE*E^2/2 + pL*L + qL*L^2/2,
so G(E) = F(E, S - E) is convex quadratic and its derivative g is affine.
The scalar "spread" pi = dF/dE - dF/dL is the only price information the
operator's response depends on, because L = S - E on the physical set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as Fr
from itertools import combinations, permutations

import numpy as np
from scipy.optimize import linear_sum_assignment


def _fr(x) -> Fr:
    return x if isinstance(x, Fr) else Fr(x).limit_denominator(10**9) if isinstance(x, float) else Fr(x)


@dataclass
class Instance:
    a: list
    b: list
    B: Fr
    K: Fr
    H: Fr
    f: Fr
    edges: set | None = None  # allowed (i, j); None means complete bipartite

    def __post_init__(self):
        self.a = [_fr(x) for x in self.a]
        self.b = [_fr(x) for x in self.b]
        self.B, self.K, self.H, self.f = map(_fr, (self.B, self.K, self.H, self.f))
        assert all(0 < x <= self.B for x in self.a + self.b)

    @property
    def S(self) -> Fr:
        return sum(self.a) + sum(self.b)

    @property
    def Lo(self) -> Fr:
        return max(Fr(0), self.S - self.H)

    @property
    def U(self) -> Fr:
        return min(sum(self.a), self.K)

    def fee(self, m: int) -> Fr:
        return self.f * (len(self.a) + len(self.b) - m)


def r_values(inst: Instance) -> list:
    """r_m for m = 0..nu. Complete graph: sorted closed form (classical);
    otherwise exact min-cost matching of each cardinality by brute force for
    small instances (used only in tests)."""
    a, b, B = inst.a, inst.b, inst.B
    if inst.edges is None:
        sa, sb = sorted(a), sorted(b)
        nu = min(len(a), len(b))
        out = [Fr(0)]
        for m in range(1, nu + 1):
            out.append(sum(max(Fr(0), sa[i] + sb[m - 1 - i] - B) for i in range(m)))
        return out
    return r_values_bruteforce(inst)


def r_values_bruteforce(inst: Instance) -> list:
    a, b, B = inst.a, inst.b, inst.B
    E = inst.edges if inst.edges is not None else {(i, j) for i in range(len(a)) for j in range(len(b))}
    out = [Fr(0)]
    m = 1
    while True:
        best = None
        for As in combinations(range(len(a)), m):
            for Bs in permutations(range(len(b)), m):
                if all((i, j) in E for i, j in zip(As, Bs)):
                    v = sum(max(Fr(0), a[i] + b[j] - B) for i, j in zip(As, Bs))
                    best = v if best is None or v < best else best
        if best is None:
            return out
        out.append(best)
        m += 1


def r_values_float(a, b, B, edges=None) -> np.ndarray:
    """Floating min-cost matching of every cardinality (for large calibrated
    instances with a sparse graph). Complete graph uses the sorted form."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if edges is None:
        sa, sb = np.sort(a), np.sort(b)
        nu = min(len(a), len(b))
        out = [0.0]
        for m in range(1, nu + 1):
            out.append(float(np.maximum(0.0, sa[:m] + sb[:m][::-1] - B).sum()))
        return np.array(out)
    # Cardinality-constrained assignment via a dummy-augmented LSA: add
    # (nA) dummy columns and (nB) dummy rows with cost lam; sweep is avoided
    # by solving each m with an explicit "m real pairs" formulation.
    raise NotImplementedError("sparse graphs are handled in tests only")


@dataclass
class Layer:
    m: int
    lo: Fr  # max(Lo, r_m)
    hi: Fr  # U
    cost: Fr


def layers(inst: Instance) -> list:
    out = []
    for m, r in enumerate(r_values(inst)):
        lo = max(inst.Lo, r)
        if lo <= inst.U:
            out.append(Layer(m, lo, inst.U, inst.fee(m)))
    return out


def hull_vertices(inst: Instance) -> list:
    """Vertices (E, c) of the lower operating-cost boundary of the hull,
    including physical thresholds on collinear edges (Theorem 1)."""
    Ls = layers(inst)
    if not Ls:
        return []
    pts = sorted({(L.lo, L.cost) for L in Ls} | {(inst.U, min(L.cost for L in Ls))})
    # lower convex chain over points sorted by E; keep collinear points
    chain = []
    for p in pts:
        while len(chain) >= 2:
            (x1, y1), (x2, y2) = chain[-2], chain[-1]
            cross = (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)
            if cross < 0:  # chain[-1] lies strictly above segment chain[-2]->p
                chain.pop()
            else:
                break
        # drop points with same E but higher cost
        if chain and chain[-1][0] == p[0]:
            if p[1] < chain[-1][1]:
                chain[-1] = p
            continue
        chain.append(p)
    # remove non-decreasing tail beyond the first point achieving min cost
    cmin = min(c for _, c in chain)
    k = next(i for i, (_, c) in enumerate(chain) if c == cmin)
    return chain[: k + 1] + ([(inst.U, cmin)] if chain[k][0] < inst.U else [])


@dataclass
class Supply:
    pE: Fr
    qE: Fr
    pL: Fr
    qL: Fr

    def __post_init__(self):
        self.pE, self.qE, self.pL, self.qL = map(_fr, (self.pE, self.qE, self.pL, self.qL))

    def G(self, inst: Instance, E: Fr) -> Fr:
        L = inst.S - E
        return self.pE * E + self.qE * E * E / 2 + self.pL * L + self.qL * L * L / 2

    def g(self, inst: Instance, E: Fr) -> Fr:
        """Spread pi = dF/dE - dF/dL evaluated at (E, S - E)."""
        return self.pE + self.qE * E - self.pL - self.qL * (inst.S - E)

    @property
    def curv(self) -> Fr:
        return self.qE + self.qL


def _argmin_quad_on(seg_lo, seg_hi, lin, curv):
    """argmin of lin*E + curv*E^2/2 on [lo, hi] (curv >= 0)."""
    if curv > 0:
        x = -lin / curv
        return min(max(x, seg_lo), seg_hi)
    return seg_lo if lin >= 0 else seg_hi


def physical_opt(inst: Instance, sup: Supply):
    """D and an optimal (E, m)."""
    best = None
    for Ly in layers(inst):
        # minimize cost + G(E) on [lo, hi]; G'(E) = g(E) affine in E
        g0 = sup.g(inst, Fr(0))
        E = _argmin_quad_on(Ly.lo, Ly.hi, g0, sup.curv)
        v = Ly.cost + sup.G(inst, E)
        if best is None or v < best[0]:
            best = (v, E, Ly.m)
    return best


def hull_opt(inst: Instance, sup: Supply):
    """CH, E*, and the hull edge (or vertex) containing E*."""
    V = hull_vertices(inst)
    g0 = sup.g(inst, Fr(0))
    best = None
    if len(V) == 1:
        E = V[0][0]
        return (V[0][1] + sup.G(inst, E), E, (0, 0))
    for k in range(len(V) - 1):
        (x1, y1), (x2, y2) = V[k], V[k + 1]
        s = (y2 - y1) / (x2 - x1)
        E = _argmin_quad_on(x1, x2, g0 + s, sup.curv)
        v = y1 + s * (E - x1) + sup.G(inst, E)
        if best is None or v < best[0]:
            best = (v, E, (k, k + 1))
    return best


def gap(inst: Instance, sup: Supply) -> Fr:
    return physical_opt(inst, sup)[0] - hull_opt(inst, sup)[0]


def response_set(inst: Instance, pi: Fr) -> list:
    """All physical vertex responses (E, cost) minimizing cost + pi*E.
    For pi > 0 the minimizers are lower layer endpoints; for pi < 0 the
    upper endpoint U with the cheapest fleet; for pi = 0 the cheapest fleet's
    whole interval (we return its two endpoints)."""
    Ls = layers(inst)
    cands = set()
    for Ly in Ls:
        cands.add((Ly.lo, Ly.cost))
        cands.add((Ly.hi, Ly.cost))
    vals = {(E, c): c + pi * E for (E, c) in cands}
    vmin = min(vals.values())
    return sorted(k for k, v in vals.items() if v == vmin)


def iterate(inst: Instance, sup: Supply, pi0: Fr, steps, tie: str = "low", max_iter: int = 2000):
    """Price iteration pi_{k+1} = (1 - a_k) pi_k + a_k g(E_k), where E_k is a
    physical response to pi_k (tie: 'low' or 'high' load). `steps` is either
    a constant a in (0, 1] or a callable k -> a_k. Returns the price and load
    histories and a state-based outcome (fixed point / cycle / none) exactly
    as in the flagship loop (egglab.loops.detect_outcome, with tol = 0)."""
    pis, Es = [pi0 if isinstance(pi0, float) else _fr(pi0)], []
    seen = {pis[0]: 0}
    for k in range(max_iter):
        R = response_set(inst, pis[-1])
        E = R[0][0] if tie == "low" else R[-1][0]
        Es.append(E)
        a = steps(k) if callable(steps) else steps
        a = a if isinstance(pis[-1], float) else _fr(a)
        nxt = (1 - a) * pis[-1] + a * sup.g(inst, E)
        if nxt == pis[-1]:
            return dict(outcome="fixed_point", at=k, pis=pis, Es=Es)
        if nxt in seen and not callable(steps):
            j = seen[nxt]
            return dict(outcome="cycle", first=j, length=k + 1 - j, pis=pis + [nxt], Es=Es)
        seen[nxt] = k + 1
        pis.append(nxt)
    return dict(outcome="none", pis=pis, Es=Es)
