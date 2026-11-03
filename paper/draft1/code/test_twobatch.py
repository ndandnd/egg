"""Exact randomized checks of the price-formation results (Section 5).

Run: python3 -m pytest -q test_twobatch.py   (or python3 test_twobatch.py)
"""
from __future__ import annotations

import random
from fractions import Fraction as Fr

from twobatch import (Instance, Supply, gap, hull_opt, hull_vertices, iterate,
                      layers, physical_opt, r_values, r_values_bruteforce,
                      response_set)


def rand_instance(rng: random.Random, n=None):
    n = n or rng.randint(1, 5)
    B = Fr(rng.randint(10, 30))
    a = [Fr(rng.randint(1, int(B))) for _ in range(n)]
    b = [Fr(rng.randint(1, int(B))) for _ in range(n)]
    S = sum(a) + sum(b)
    K = Fr(rng.randint(0, int(sum(a)) + 3))
    H = Fr(rng.randint(max(0, int(S - K) - 2), int(S) + 5))
    f = Fr(rng.randint(1, 8), rng.randint(1, 4))
    return Instance(a, b, B, K, H, f)


def rand_supply(rng: random.Random):
    return Supply(Fr(rng.randint(-10, 10), 4), Fr(rng.randint(1, 40), 20),
                  Fr(rng.randint(-10, 10), 4), Fr(rng.randint(0, 40), 20))


def targeted_supply(rng: random.Random, inst):
    """Supply whose hull optimum tends to fall inside a decreasing hull
    edge (gaps are otherwise rare: they need g(E*) = f / edge length)."""
    V = hull_vertices(inst)
    edges = [k for k in range(len(V) - 1) if V[k + 1][1] < V[k][1]]
    if not edges:
        return rand_supply(rng)
    k = rng.choice(edges)
    (x1, y1), (x2, y2) = V[k], V[k + 1]
    slope = (y1 - y2) / (x2 - x1)
    t = Fr(rng.randint(1, 9), 10)
    mid = x1 + t * (x2 - x1)
    qE, qL = Fr(rng.randint(1, 40), 20), Fr(rng.randint(0, 40), 20)
    pL = Fr(rng.randint(-10, 10), 4)
    # g(mid) = pE + qE*mid - pL - qL*(S - mid) = slope
    pE = slope - qE * mid + pL + qL * (inst.S - mid)
    return Supply(pE, qE, pL, qL)


def draw(rng):
    inst = rand_instance(rng)
    return inst, (targeted_supply(rng, inst) if rng.random() < 0.6 else rand_supply(rng))


def feasible(inst):
    return bool(layers(inst))


def strict_vertices(V):
    """Drop physical thresholds lying in the relative interior of a hull
    edge: the faces of the lower boundary are between consecutive strict
    vertices."""
    out = []
    for p in V:
        while len(out) >= 2:
            (x1, y1), (x2, y2) = out[-2], out[-1]
            if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) == 0:
                out.pop()
            else:
                break
        out.append(p)
    return out


def edge_of(inst, E):
    V = strict_vertices(hull_vertices(inst))
    for k in range(len(V) - 1):
        if V[k][0] < E < V[k + 1][0]:
            return V, k
    return V, None


def test_sorted_matching_formula():
    rng = random.Random(1)
    for _ in range(300):
        inst = rand_instance(rng, rng.randint(1, 4))
        assert r_values(inst) == r_values_bruteforce(inst)


def test_anchor_values():
    inst = Instance([5, 15], [14, 15], 20, 15, 49, 7)
    sup = Supply(4, Fr(1, 10), 0, Fr(1, 10))
    assert physical_opt(inst, sup)[0] == Fr(2681, 20)
    assert hull_opt(inst, sup)[0] == Fr(434201, 3240)
    out = iterate(inst, sup, 0, 1)
    assert out["outcome"] == "cycle" and out["length"] == 2


def test_fixed_point_iff_no_gap_and_undamped_period():
    """Undamped iteration is eventually periodic with period <= 2; a fixed
    point is reached only if Delta = 0; when Delta > 0 the 2-cycle brackets
    the hull edge containing E*."""
    rng = random.Random(2)
    n_gap = n_cyc_nogap = 0
    for _ in range(700):
        inst, sup = draw(rng)
        if not feasible(inst):
            continue
        D = gap(inst, sup)
        pi0 = Fr(rng.randint(-40, 40), 4)
        for tie in ("low", "high"):
            out = iterate(inst, sup, pi0, 1, tie=tie, max_iter=200)
            assert out["outcome"] in ("fixed_point", "cycle")
            if out["outcome"] == "cycle":
                assert out["length"] == 2
            if D > 0:
                n_gap += 1
                assert out["outcome"] == "cycle"
                _, Es, _ = hull_opt(inst, sup)[0], hull_opt(inst, sup)[1], None
                V, k = edge_of(inst, Es)
                assert k is not None
                tail = out["Es"][-2:]
                assert min(tail) <= V[k][0] and max(tail) >= V[k + 1][0]
            elif out["outcome"] == "cycle":
                n_cyc_nogap += 1
    assert n_gap > 100
    print(f"gap cases {n_gap}; undamped cycles despite zero gap {n_cyc_nogap}")


def test_fixed_point_is_support():
    """A fixed point price equals g at its own response: support."""
    rng = random.Random(3)
    for _ in range(800):
        inst, sup = draw(rng)
        if not feasible(inst):
            continue
        out = iterate(inst, sup, Fr(0), Fr(1, 3), max_iter=3000)
        if out["outcome"] == "fixed_point":
            assert gap(inst, sup) == 0


def trap_threshold(inst, sup, V, k, Es):
    """a_bar of Theorem (price iteration), with sigma_{k-1}, sigma_{k+1} the
    spreads at which the response leaves {v_k, v_{k+1}}."""
    pistar = sup.g(inst, Es)
    sl = [(V[i][1] - V[i + 1][1]) / (V[i + 1][0] - V[i][0]) for i in range(len(V) - 1)]
    sig_lo = sl[k + 1] if k + 1 < len(sl) else None   # None = -infinity
    sig_hi = sl[k - 1] if k >= 1 else None            # None = +infinity
    dlo, dhi = pistar - sup.g(inst, V[k][0]), sup.g(inst, V[k + 1][0]) - pistar
    cands = []
    if sig_lo is not None:
        cands.append((pistar - sig_lo) / dlo)
    if sig_hi is not None:
        cands.append((sig_hi - pistar) / dhi)
    abar = min(cands + [Fr(1)])
    return pistar, sig_lo, sig_hi, dlo, dhi, abar


def test_small_constant_step_traps_adjacent_vertices():
    rng = random.Random(4)
    checked = 0
    for _ in range(4000):
        inst, sup = draw(rng)
        if not feasible(inst) or gap(inst, sup) == 0:
            continue
        CH, Es, _ = hull_opt(inst, sup)
        V, k = edge_of(inst, Es)
        vk, vk1 = V[k][0], V[k + 1][0]
        pistar, sig_lo, sig_hi, dlo, dhi, abar = trap_threshold(inst, sup, V, k, Es)
        a = abar / 2
        if a < Fr(1, 2000):
            continue  # keep the float iteration short; threshold is exact anyway
        pi0 = (pistar + sig_hi) / 2 if sig_hi is not None else pistar + 1
        n = int(40 / a) + 2000
        out = iterate(inst, sup, float(pi0), float(a), max_iter=n)
        if out["outcome"] == "cycle":  # exact float recurrence: use the cycle
            tailE, tailp = out["Es"][out["first"]:], out["pis"][out["first"]:]
        else:
            tailE, tailp = out["Es"][-1500:], out["pis"][-1500:]
        assert set(tailE) <= {vk, vk1} and {vk, vk1} <= set(tailE)
        tol = 1e-9 * (1 + abs(float(pistar)))
        assert all(float(pistar - a * dlo) - tol <= p <= float(pistar + a * dhi) + tol for p in tailp)
        # time-averaged load is within O(a) of E* (affine g)
        avg = sum(float(x) for x in tailE) / len(tailE)
        assert abs(avg - float(Es)) <= float(vk1 - vk) * (0.02 + 4 * float(a) * float(max(dlo, dhi) / min(dlo, dhi)))
        checked += 1
        if checked >= 60:
            break
    assert checked >= 30, checked


def test_diminishing_steps_converge_to_hull_price():
    rng = random.Random(5)
    checked = 0
    for _ in range(3000):
        inst, sup = draw(rng)
        if not feasible(inst) or gap(inst, sup) == 0:
            continue
        CH, Es, _ = hull_opt(inst, sup)
        pistar = sup.g(inst, Es)
        out = iterate(inst, sup, float(pistar - 5), lambda k: 1.0 / (k + 2), max_iter=4000)
        assert abs(out["pis"][-1] - float(pistar)) < 0.02 * (1 + abs(float(pistar)))
        checked += 1
        if checked >= 25:
            break
    assert checked >= 15


def test_fee_dominance_and_gap_bound():
    """Delta = 0 if f >= max increment * max spread on [Lo, U]; and for
    quadratic supply Delta <= kappa * l^2 / 8 for the edge length l."""
    rng = random.Random(6)
    for _ in range(3000):
        inst, sup = draw(rng)
        if not feasible(inst):
            continue
        V = hull_vertices(inst)
        incs = [V[k + 1][0] - V[k][0] for k in range(len(V) - 1) if V[k + 1][1] < V[k][1]]
        gmax = max(sup.g(inst, inst.Lo), sup.g(inst, inst.U))
        D = gap(inst, sup)
        if not incs or inst.f >= max(incs) * gmax:
            assert D == 0
        CH, Es, _ = hull_opt(inst, sup)
        _, k = edge_of(inst, Es)
        if k is not None:
            ell = V[k + 1][0] - V[k][0]
            assert D <= sup.curv * ell * ell / 8




def test_interior_face_explains_nonconvergence():
    """Unified statement: for a small constant step the prices converge iff
    E* is not in the relative interior of a hull face; Delta > 0 iff, in
    addition, E* is not physical. Checked on random instances."""
    rng = random.Random(7)
    seen = {"vertex": 0, "face_gap": 0, "face_nogap": 0}
    for _ in range(4000):
        inst, sup = draw(rng)
        if not feasible(inst):
            continue
        CH, Es, _ = hull_opt(inst, sup)
        V, k = edge_of(inst, Es)
        D = gap(inst, sup)
        if k is None:
            # E* at a strict vertex (or single point): constant small step converges
            kind = "vertex"
        else:
            kind = "face_gap" if D > 0 else "face_nogap"
            if D == 0:
                # physical: either flat face or a collinear threshold
                assert V[k][1] == V[k + 1][1] or any(E == Es for E, _ in hull_vertices(inst))
        if seen[kind] >= 25:
            continue
        pistar = sup.g(inst, Es)
        if kind == "vertex":
            # Theorem (c): with a*M below the distance from pi* to the boundary
            # of E*'s normal cone, prices converge and E_k = E* eventually.
            Vs = strict_vertices(hull_vertices(inst))
            j = next((i for i, (x, _) in enumerate(Vs) if x == Es), None)
            if j is None:
                continue
            sl = [(Vs[i][1] - Vs[i + 1][1]) / (Vs[i + 1][0] - Vs[i][0]) for i in range(len(Vs) - 1)]
            hi = sl[j - 1] if j >= 1 else None          # left face slope magnitude
            lo = sl[j] if j < len(sl) else None         # right face slope magnitude
            dist = min([x for x in ((hi - pistar) if hi is not None else None,
                                     (pistar - lo) if lo is not None else None) if x is not None] + [Fr(10**6)])
            M = max(abs(sup.g(inst, inst.Lo) - pistar), abs(sup.g(inst, inst.U) - pistar))
            if dist <= 0 or M == 0:
                continue
            a = min(Fr(1, 2), dist / (2 * M))
            if a < Fr(1, 2000):
                continue
            out = iterate(inst, sup, float(pistar + M), float(a), max_iter=int(60 / a) + 2000)
            assert out["Es"][-1] == Es
            assert abs(out["pis"][-1] - float(pistar)) < 1e-6 * (1 + abs(float(pistar)))
            seen[kind] += 1
            continue
        if any(E == Es for E, _ in hull_vertices(inst)):
            continue  # E* is a collinear physical threshold: knife-edge
        _, sig_lo, sig_hi, dlo, dhi, abar = trap_threshold(inst, sup, V, k, Es)
        a = abar / 2
        if a < Fr(1, 2000):
            continue
        pi0 = (pistar + sig_hi) / 2 if sig_hi is not None else pistar + 1
        out = iterate(inst, sup, float(pi0), float(a), max_iter=int(40 / a) + 2000)
        assert out["outcome"] != "fixed_point"
        tail = out["Es"][out["first"]:] if out["outcome"] == "cycle" else out["Es"][-1500:]
        assert {V[k][0], V[k + 1][0]} <= set(tail)
        seen[kind] += 1
    print(seen)
    assert min(seen.values()) >= 10


def test_unequal_batches_sorted_formula():
    """The sorted closed form and the fleet count N_m = n_A + n_B - m hold
    for unequal batch sizes (the calibrated instances have n_A != n_B)."""
    rng = random.Random(8)
    for _ in range(300):
        B = Fr(rng.randint(10, 30))
        a = [Fr(rng.randint(1, int(B))) for _ in range(rng.randint(1, 4))]
        b = [Fr(rng.randint(1, int(B))) for _ in range(rng.randint(1, 4))]
        inst = Instance(a, b, B, sum(a), sum(a) + sum(b), 1)
        assert r_values(inst) == r_values_bruteforce(inst)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
