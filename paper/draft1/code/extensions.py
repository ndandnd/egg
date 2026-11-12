"""Exact slot-level layers for the two-batch class (theory extensions T1-T4).

Model.  Early (midday) slots t = 0..T1-1 and terminal slots s = 0..T2-1.
Charge-only, unit efficiency (a common efficiency alpha only rescales grid
energy; see theory/EXTENSIONS.md).  In early slot t a bus may receive at most
pi[t] and the depot at most kap[t]; in terminal slot s at most pi2[s] and
kap2[s].  The pooled-connector model of the paper is pi = kap (any bus can
take the whole connector), the plug model is pi[t] = p*h_t and
kap[t] = min(C*p*h_t, site cap) (preemptive plug sharing, McNaughton).

Staggered availability (T4): A run i ends at slot boundary eA[i] and B run j
starts at boundary sB[j].  A paired bus (i, j) may charge in early slots
eA[i] <= t < sB[j]; an A-only bus in slots t >= eA[i].  Pair (i, j) is
time-compatible iff eA[i] <= sB[j].  Defaults give the common window.

A bus is a tuple (s, lam, hi, W): total daily draw s, minimum early gain lam,
maximum early gain hi, early availability W (bitmask over early slots).
For a fixed matching the set of attainable slot-load vectors d = (e, l) is
the base polytope of G_M = sum_v g_v intersected with the box [0, kap],
where g_v(D) = min(s, min(hi, pi(D n W)) + min(s - lam, pi2(D n T2))) is the
rank function of the bus's laminar polymatroid (proof in EXTENSIONS.md).
Everything is exact (fractions.Fraction).  `flow_member` is an independent
max-flow check of the same set used to validate the cut formula.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr
from functools import reduce
from math import lcm

import networkx as nx


def F(x) -> Fr:
    return x if isinstance(x, Fr) else Fr(x)


@dataclass
class SInst:
    a: list
    b: list
    B: Fr
    pi: list            # early per-bus per-slot cap
    kap: list           # early aggregate per-slot cap
    pi2: list           # terminal per-bus per-slot cap
    kap2: list          # terminal aggregate per-slot cap
    edges: set | None = None   # allowed (i, j); None = complete (subject to time)
    eA: list | None = None     # A end boundaries (default 0)
    sB: list | None = None     # B start boundaries (default T1)
    f: Fr = Fr(1)

    def __post_init__(self):
        self.a = [F(x) for x in self.a]
        self.b = [F(x) for x in self.b]
        self.B = F(self.B)
        self.pi = [F(x) for x in self.pi]
        self.kap = [F(x) for x in self.kap]
        self.pi2 = [F(x) for x in self.pi2]
        self.kap2 = [F(x) for x in self.kap2]
        self.f = F(self.f)
        assert all(0 < x <= self.B for x in self.a + self.b)
        assert len(self.pi) == len(self.kap) and len(self.pi2) == len(self.kap2)
        if self.eA is None:
            self.eA = [0] * len(self.a)
        if self.sB is None:
            self.sB = [self.T1] * len(self.b)

    @property
    def T1(self):
        return len(self.pi)

    @property
    def T2(self):
        return len(self.pi2)

    @property
    def T(self):
        return self.T1 + self.T2

    @property
    def S0(self):
        return sum(self.a) + sum(self.b)

    def allowed(self, i, j):
        if self.eA[i] > self.sB[j]:
            return False
        return self.edges is None or (i, j) in self.edges

    def win(self, lo, hi):
        """bitmask of early slots lo <= t < hi"""
        m = 0
        for t in range(lo, min(hi, self.T1)):
            m |= 1 << t
        return m

    def fee(self, M):
        return self.f * (len(self.a) + len(self.b) - len(M))


# ---------------------------------------------------------------- matchings
def matchings(inst: SInst, size=None):
    """All matchings (tuples of (i, j)) of the allowed graph, optionally of one size."""
    out = []
    nA, nB = len(inst.a), len(inst.b)

    def rec(i, used, cur):
        if i == nA:
            if size is None or len(cur) == size:
                out.append(tuple(cur))
            return
        rec(i + 1, used, cur)
        for j in range(nB):
            if not (used >> j) & 1 and inst.allowed(i, j):
                cur.append((i, j))
                rec(i + 1, used | (1 << j), cur)
                cur.pop()

    rec(0, 0, [])
    return out


def buses(inst: SInst, M):
    """(s, lam, hi, W) for every bus of the fleet induced by matching M."""
    out = []
    pa = {i: j for i, j in M}
    pb = {j for _, j in M}
    for i, a in enumerate(inst.a):
        if i in pa:
            j = pa[i]
            s = a + inst.b[j]
            out.append((s, max(Fr(0), s - inst.B), a, inst.win(inst.eA[i], inst.sB[j])))
        else:
            out.append((a, Fr(0), a, inst.win(inst.eA[i], inst.T1)))
    for j, b in enumerate(inst.b):
        if j not in pb:
            out.append((b, Fr(0), Fr(0), 0))
    return out


def lam_vector(inst, M):
    return sorted((max(Fr(0), inst.a[i] + inst.b[j] - inst.B) for i, j in M), reverse=True)


# ------------------------------------------------------------ cut functions
class Layer:
    """Exact description of A(M) as a box-truncated polymatroid base polytope."""

    def __init__(self, inst: SInst, M):
        self.inst, self.M = inst, tuple(M)
        T1, T = inst.T1, inst.T
        self.bus = buses(inst, M)
        caps = inst.pi + inst.pi2
        kaps = inst.kap + inst.kap2
        n = 1 << T
        capsum = [Fr(0)] * n
        for D in range(1, n):
            t = (D & -D).bit_length() - 1
            capsum[D] = capsum[D & (D - 1)] + caps[t]
        emask = (1 << T1) - 1
        G = [Fr(0)] * n
        for (s, lam, hi, W) in self.bus:
            for D in range(n):
                pe = capsum[(D & emask) & W]
                pt = capsum[D & ~emask]
                G[D] += min(s, min(hi, pe) + min(s - lam, pt))
        self.G = G
        full = n - 1
        self.feasible_buses = all(
            min(s, min(hi, capsum[W]) + min(s - lam, capsum[full & ~emask])) == s
            for (s, lam, hi, W) in self.bus)
        # truncation by the aggregate box: Gk(D) = min_{Y<=D} G(Y) + kap(D\Y)
        Gk = [Fr(0)] * n
        for D in range(1, n):
            v = G[D]
            DD = D
            while DD:
                t = (DD & -DD).bit_length() - 1
                DD &= DD - 1
                w = Gk[D & ~(1 << t)] + kaps[t]
                if w < v:
                    v = w
            Gk[D] = v
        self.Gk = Gk
        self.kaps = kaps
        self.S0 = inst.S0
        self.nonempty = self.feasible_buses and Gk[full] == G[full] == inst.S0

    def member(self, d) -> bool:
        if not self.nonempty:
            return False
        d = [F(x) for x in d]
        if any(x < 0 for x in d) or any(x > k for x, k in zip(d, self.kaps)):
            return False
        if sum(d) != self.S0:
            return False
        n = len(self.G)
        ds = [Fr(0)] * n
        for D in range(1, n):
            t = (D & -D).bit_length() - 1
            ds[D] = ds[D & (D - 1)] + d[t]
            if ds[D] > self.G[D]:
                return False
        return True

    def violated(self, d):
        """A cut D with d(D) > G(D), or None."""
        n = len(self.G)
        ds = [Fr(0)] * n
        for D in range(1, n):
            t = (D & -D).bit_length() - 1
            ds[D] = ds[D & (D - 1)] + F(d[t])
            if ds[D] > self.G[D]:
                return D
        return None

    def contains(self, other: "Layer") -> bool:
        if not other.nonempty:
            return True
        if not self.nonempty:
            return False
        return all(x >= y for x, y in zip(self.Gk, other.Gk))

    def greedy_min(self, w):
        """(value, point) of min w.d over A(M) (Edmonds greedy)."""
        assert self.nonempty
        order = sorted(range(self.inst.T), key=lambda t: F(w[t]))
        d = [Fr(0)] * self.inst.T
        D = 0
        prev = Fr(0)
        for t in order:
            D |= 1 << t
            d[t] = self.Gk[D] - prev
            prev = self.Gk[D]
        return sum(F(w[t]) * d[t] for t in range(self.inst.T)), d


# ------------------------------------------------- independent flow witness
def flow_member(inst: SInst, M, d) -> bool:
    """Independent check: is the slot vector d attainable for matching M?
    Exact integer network-simplex feasibility on a per-bus network with
    lower bounds (no use of the cut formula)."""
    d = [F(x) for x in d]
    kaps = inst.kap + inst.kap2
    if any(x < 0 for x in d) or any(x > k for x, k in zip(d, kaps)):
        return False
    bus = buses(inst, M)
    vals = d + inst.pi + inst.pi2 + [x for bb in bus for x in bb[:3]]
    L = reduce(lcm, (x.denominator for x in vals), 1)

    def sc(x):
        return int(F(x) * L)

    G = nx.DiGraph()
    dem = {}

    def add(u, v, lo, cap):
        lo, cap = sc(lo), sc(cap)
        if cap < lo:
            raise ValueError
        G.add_edge(u, v, capacity=cap - lo, weight=0)
        dem[u] = dem.get(u, 0) + lo
        dem[v] = dem.get(v, 0) - lo

    for v, (s, lam, hi, W) in enumerate(bus):
        dem[("v", v)] = dem.get(("v", v), 0) - sc(s)
        add(("v", v), ("E", v), lam, hi)
        add(("v", v), ("T", v), 0, s)
        for t in range(inst.T1):
            if (W >> t) & 1:
                add(("E", v), ("e", t), 0, inst.pi[t])
        for t in range(inst.T2):
            add(("T", v), ("l", t), 0, inst.pi2[t])
    for t in range(inst.T1):
        dem[("e", t)] = dem.get(("e", t), 0) + sc(d[t])
    for t in range(inst.T2):
        dem[("l", t)] = dem.get(("l", t), 0) + sc(d[inst.T1 + t])
    for u, x in dem.items():
        G.add_node(u)
        G.nodes[u]["demand"] = x
    if sum(dem.values()) != 0:
        return False
    try:
        nx.network_simplex(G)
        return True
    except nx.NetworkXUnfeasible:
        return False


# ---------------------------------------------------------------- utilities
def layers_by_size(inst: SInst):
    out = {}
    for M in matchings(inst):
        out.setdefault(len(M), []).append(Layer(inst, M))
    return out


def dominating(inst: SInst, m, lays=None):
    """Matchings of size m whose set contains every size-m set (may be empty list)."""
    lays = lays if lays is not None else layers_by_size(inst).get(m, [])
    ne = [L for L in lays if L.nonempty]
    return [L for L in ne if all(L.contains(O) for O in ne)]


def phi(lams, y):
    return sum(max(Fr(0), x - y) for x in lams)
