"""Exact checks for paper/draft1/theory/EXTENSIONS.md (T1-T5).

Run: python3 test_extensions.py   (prints counts; log in test_extensions_log.txt)
All arithmetic is exact (fractions.Fraction / integers). Random families use
fixed seeds; counts are printed.
"""
from __future__ import annotations

import itertools
import random
from fractions import Fraction as Fr

from extensions import (SInst, Layer, dominating, flow_member, lam_vector,
                        layers_by_size, matchings, phi)


# --------------------------------------------------------------- utilities
def r_of(inst, M):
    return sum((max(Fr(0), inst.a[i] + inst.b[j] - inst.B) for i, j in M), Fr(0))


def mix_ok(reps, weights=(Fr(1, 4), Fr(1, 2), Fr(3, 4))):
    """Mixing property for representatives: for every pair of nonempty
    layers m1 < m2 and weight mu, mu*Gk1 + (1-mu)*Gk2 <= Gk_{floor t}
    (Minkowski combination of truncated base polytopes)."""
    ms = sorted(reps)
    for m1, m2 in itertools.combinations(ms, 2):
        for mu in weights:
            t = mu * m1 + (1 - mu) * m2
            fl = t.numerator // t.denominator
            G = [mu * x + (1 - mu) * y for x, y in zip(reps[m1].Gk, reps[m2].Gk)]
            if fl not in reps or any(g > h for g, h in zip(G, reps[fl].Gk)):
                return False
    return True


def kmax(inst, z):
    """Largest cardinality whose layer contains z (-1 if none)."""
    best = -1
    for M in matchings(inst):
        if Layer(inst, M).member(z):
            best = max(best, len(M))
    return best


# ------------------------------------------------------------------- T1(b)
def test_T1b_cut_vs_flow(n_inst=150):
    """Thm 2 cut formula vs an independent per-bus network-simplex check."""
    rng = random.Random(1)
    agree = inside = 0
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 3), rng.randint(1, 3), rng.randint(4, 10)
        T1, T2 = rng.randint(1, 3), rng.randint(1, 2)
        inst = SInst([rng.randint(1, B) for _ in range(nA)], [rng.randint(1, B) for _ in range(nB)], B,
                     [rng.randint(1, B) for _ in range(T1)], [rng.randint(1, 3 * B) for _ in range(T1)],
                     [rng.randint(1, 2 * B) for _ in range(T2)], [rng.randint(B, 4 * B) for _ in range(T2)],
                     eA=[rng.randint(0, T1) for _ in range(nA)] if rng.random() < .5 else None,
                     sB=[rng.randint(0, T1) for _ in range(nB)] if rng.random() < .5 else None)
        Ls = [Layer(inst, M) for M in matchings(inst)]
        ne = [L for L in Ls if L.nonempty]
        pts = []
        for O in ne:
            for _ in range(3):
                pts.append(O.greedy_min([rng.randint(-5, 5) for _ in range(inst.T)])[1])
        for _ in range(6):
            if len(pts) >= 2:
                p, q = rng.sample(pts, 2)
                mu = Fr(rng.randint(0, 4), 4)
                pts.append([mu * x + (1 - mu) * y for x, y in zip(p, q)])
        for L in Ls:
            for d in pts:
                x = L.member(d)
                assert x == flow_member(inst, L.M, d), (inst, L.M, d)
                agree += 1
                inside += x
    print(f"ok test_T1b_cut_vs_flow: {n_inst} instances, {agree} points agree "
          f"({inside} inside, {agree - inside} outside), 0 disagreements")


# ------------------------------------------------------------------- T1(a)
def lam_closed_form(inst, M, d):
    """Theorem 1 closed form (alpha = 1)."""
    e, l = d[:inst.T1], d[inst.T1:]
    if any(x < 0 for x in d) or any(x > k for x, k in zip(d, inst.kap + inst.kap2)):
        return False
    return r_of(inst, M) <= sum(e) <= sum(inst.a) and sum(e) + sum(l) == inst.S0


def test_T1a_pooled_projection(n_inst=300):
    rng = random.Random(2)
    pts_checked = layers = 0
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 4), rng.randint(1, 4), rng.randint(3, 12)
        T1, T2 = rng.randint(1, 3), rng.randint(1, 3)
        K = [rng.randint(0, 2 * B) for _ in range(T1)]       # zero caps allowed
        H = [rng.randint(0, 3 * B) for _ in range(T2)]
        edges = None if rng.random() < .4 else {(i, j) for i in range(nA) for j in range(nB) if rng.random() < .6}
        inst = SInst([rng.randint(1, B) for _ in range(nA)], [rng.randint(1, B) for _ in range(nB)], B,
                     K, K, H, H, edges=edges)
        LB = layers_by_size(inst)
        allne = [X for Y in LB.values() for X in Y if X.nonempty]
        reps = {}
        for m, Ls in LB.items():
            for L in Ls:
                for O in allne[:6]:
                    d = O.greedy_min([rng.randint(-4, 4) for _ in range(inst.T)])[1]
                    assert L.member(d) == lam_closed_form(inst, L.M, d)
                    pts_checked += 1
            if not any(L.nonempty for L in Ls):
                continue
            layers += 1
            rm = min(r_of(inst, L.M) for L in Ls)
            star = [L for L in Ls if r_of(inst, L.M) == rm]
            assert all(S.contains(L) for S in star for L in Ls), "r_m minimizer must dominate"
            reps[m] = star[0]
        ms = sorted(reps)
        for m1, m2 in zip(ms, ms[1:]):
            assert reps[m1].contains(reps[m2])
        assert mix_ok(reps)
    print(f"ok test_T1a_pooled_projection: {n_inst} instances, {layers} nonempty layers, "
          f"{pts_checked} closed-form membership checks; r_m-minimizer dominates, layers nested, MP holds")


def example1():
    return SInst([5, 7], [7, 5, 6], 10, [2, 2], [10, 10], [10], [100],
                 edges={(0, 0), (0, 1), (1, 1), (1, 2)})


def test_T1b_example1():
    inst = example1()
    M1, M2, M3 = ((0, 0), (1, 1)), ((0, 1), (1, 2)), ((0, 0), (1, 2))
    L1, L2, L3 = (Layer(inst, M) for M in (M1, M2, M3))
    assert sorted([M1, M2, M3]) == sorted(matchings(inst, 2))
    assert [lam_vector(inst, M) for M in (M1, M2, M3)] == [[2, 2], [3, 0], [3, 2]]
    assert [r_of(inst, M) for M in (M1, M2, M3)] == [4, 3, 5]
    p1, p2 = [4, 0, 26], [2, 1, 27]
    for d, a, b in ((p1, True, False), (p2, False, True)):
        assert L1.member(d) == a == flow_member(inst, M1, d)
        assert L2.member(d) == b == flow_member(inst, M2, d)
    assert not dominating(inst, 2)
    assert L1.contains(L3) and L2.contains(L3)
    assert [phi(lam_vector(inst, M1), y) for y in (0, 2, 4)] == [4, 0, 0]
    assert [phi(lam_vector(inst, M2), y) for y in (0, 2, 4)] == [3, 1, 0]
    # linear prices (e1, e2, l): each size-2 matching strictly better at some price
    w1, w2 = [0, 10, 1], [5, 5, 0]
    v1 = [L.greedy_min(w1)[0] for L in (L1, L2, L3)]
    v2 = [L.greedy_min(w2)[0] for L in (L1, L2, L3)]
    assert v1 == [26, 35, 35] and v2 == [20, 15, 25]
    print(f"   Example 1 prices (e1,e2,l)={w1}: energy bills M1,M2,M3 = {[str(v) for v in v1]}; "
          f"prices {w2}: {[str(v) for v in v2]}")
    # one-fee: z = mixture with t = 2 and kmax = 1  =>  D - CH = f
    z = [Fr(1, 2) * x + Fr(1, 2) * y for x, y in zip(p1, p2)]
    assert z == [3, Fr(1, 2), Fr(53, 2)]
    assert kmax(inst, z) == 1 and Layer(inst, ((0, 1),)).member(z)
    # quadratic cost F_c = c|d - z|^2: squared-distance lower bounds from violated cuts
    dist2 = []
    for L in (L1, L2, L3):
        D = L.violated(z)
        assert D is not None
        k = bin(D).count("1")
        viol = sum(z[t] for t in range(3) if D >> t & 1) - L.G[D]
        dist2.append(viol * viol / k)
    assert min(dist2) == Fr(1, 8)
    print(f"   Example 1 mixture z={[str(x) for x in z]}: in no size-2 set, in the size-1 set of (A1,B2); "
          f"squared distances to the size-2 sets >= {[str(x) for x in dist2]}")
    print("ok test_T1b_example1: no dominating size-2 matching; r_2-minimizer fails; D - CH = f "
          "(indicator of z, and c|d-z|^2 for every c >= 8f)")


def test_T1b_example2():
    inst = SInst([4, 1], [1, 6], 6, [1], [10], [5, 1], [9, 11], edges={(0, 0), (0, 1), (1, 1)})
    LB = layers_by_size(inst)
    ne = [L for L in LB[1] if L.nonempty]
    assert sorted(L.M for L in ne) == [((0, 0),), ((1, 1),)]
    assert not dominating(inst, 1)
    La, Lb = Layer(inst, ((1, 1),)), Layer(inst, ((0, 0),))
    ws = list(itertools.product(range(-2, 3), repeat=3))
    wa = next(d for d in (La.greedy_min(w)[1] for w in ws) if not Lb.member(d))
    wb = next(d for d in (Lb.greedy_min(w)[1] for w in ws) if not La.member(d))
    assert flow_member(inst, ((1, 1),), wa) and not flow_member(inst, ((0, 0),), wa)
    assert flow_member(inst, ((0, 0),), wb) and not flow_member(inst, ((1, 1),), wb)
    print(f"ok test_T1b_example2: binding terminal, 4 services, m=1, T1=1: "
          f"{[str(x) for x in wa]} only for (A2,B2); {[str(x) for x in wb]} only for (A1,B1)")


def test_T1b_small_exhaustive():
    """n_A = 2, n_B = 1 (complete): exhaustive grid B <= 3, T1, T2 <= 2."""
    cnt = bad = 0
    for B in (1, 2, 3):
        for T1, T2 in ((1, 1), (1, 2), (2, 1), (2, 2)):
            for a in itertools.product(range(1, B + 1), repeat=2):
                if a[0] > a[1]:
                    continue
                for b in range(1, B + 1):
                    for pi in itertools.product(range(1, B + 1), repeat=T1):
                        for pi2 in itertools.product(range(1, B + 1), repeat=T2):
                            for kap in itertools.product((B, 2 * B, 3 * B), repeat=T1):
                                for kap2 in itertools.product((B, 2 * B, 3 * B), repeat=T2):
                                    inst = SInst(list(a), [b], B, list(pi), list(kap), list(pi2), list(kap2))
                                    Ls = [Layer(inst, M) for M in matchings(inst, 1)]
                                    cnt += 1
                                    if any(L.nonempty for L in Ls) and not dominating(inst, 1, Ls):
                                        bad += 1
    assert bad == 0
    print(f"ok test_T1b_small_exhaustive: n_A=2, n_B=1: {cnt} instances, 0 without a dominating matching")


def test_T1b_nA1(n_inst=2000):
    """n_A = 1: the smallest feasible b dominates (any terminal)."""
    rng = random.Random(4)
    cnt = 0
    for _ in range(n_inst):
        nB, B = rng.randint(2, 4), rng.randint(2, 8)
        T1, T2 = rng.randint(1, 3), rng.randint(1, 3)
        edges = {(0, j) for j in range(nB) if rng.random() < .8}
        inst = SInst([rng.randint(1, B)], [rng.randint(1, B) for _ in range(nB)], B,
                     [rng.randint(1, B) for _ in range(T1)], [rng.randint(1, 3 * B) for _ in range(T1)],
                     [rng.randint(1, B) for _ in range(T2)], [rng.randint(1, 3 * B) for _ in range(T2)],
                     edges=edges)
        Ls = [Layer(inst, M) for M in matchings(inst, 1)]
        ne = [L for L in Ls if L.nonempty]
        if not ne:
            continue
        cnt += 1
        bmin = min(inst.b[L.M[0][1]] for L in ne)
        S = next(L for L in ne if inst.b[L.M[0][1]] == bmin)
        assert all(S.contains(L) for L in Ls)
    print(f"ok test_T1b_nA1: {cnt} instances with n_A = 1: smallest feasible b dominates")


def test_T1b_complete_graph(n_inst=1500):
    rng = random.Random(3)
    adeq = bind = 0
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 3), rng.randint(1, 3), rng.randint(2, 8)
        T1, T2 = rng.randint(1, 3), rng.randint(1, 3)
        a = [rng.randint(1, B) for _ in range(nA)]
        b = [rng.randint(1, B) for _ in range(nB)]
        is_adeq = rng.random() < .4
        inst = SInst(a, b, B, [rng.randint(1, B) for _ in range(T1)], [rng.randint(1, 3 * B) for _ in range(T1)],
                     [B if is_adeq else rng.randint(1, B) for _ in range(T2)],
                     [rng.randint(1, 4 * B) for _ in range(T2)])
        for m, Ls in layers_by_size(inst).items():
            if not any(L.nonempty for L in Ls):
                continue
            ia = sorted(range(nA), key=lambda i: (a[i], i))[:m]
            jb = sorted(range(nB), key=lambda j: (b[j], j))[:m][::-1]
            S = Layer(inst, tuple(sorted(zip(ia, jb))))
            assert all(S.contains(L) for L in Ls), ("Cor 3.2" if is_adeq else "Conjecture 3.2'")
            if is_adeq:
                adeq += 1
            else:
                bind += 1
    print(f"ok test_T1b_complete_graph: sorted matching dominates in {adeq} layers with adequate terminal "
          f"(Cor 3.2) and in {bind} layers with binding terminal limits (Conjecture 3.2' evidence)")


def test_T1b_cor31_and_mixing(n_inst=800):
    rng = random.Random(5)
    cnt = 0
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 4), rng.randint(1, 4), rng.randint(3, 10)
        T1 = rng.randint(1, 3)
        a = [rng.randint(1, B) for _ in range(nA)]
        b = [rng.randint(1, B) for _ in range(nB)]
        edges = {(i, j) for i in range(nA) for j in range(nB) if rng.random() < .6}
        lmax = max([max(0, a[i] + b[j] - B) for i, j in edges] + [0])
        pi = [rng.randint(max(lmax, 1), B + 2) for _ in range(T1)]       # pi_min >= max edge requirement
        inst = SInst(a, b, B, pi, [rng.randint(1, 3 * B) for _ in range(T1)], [B], [rng.randint(B, 6 * B)],
                     edges=edges)
        reps = {}
        for m, Ls in layers_by_size(inst).items():
            if not any(L.nonempty for L in Ls):
                continue
            rm = min(r_of(inst, L.M) for L in Ls)
            S = next(L for L in Ls if r_of(inst, L.M) == rm)
            assert all(S.contains(L) for L in Ls)
            reps[m] = S
        assert mix_ok(reps)
        cnt += 1
    print(f"ok test_T1b_cor31_and_mixing: {cnt} instances (pi_min >= max edge requirement): "
          f"r_m-minimizer dominates, representatives have MP")


def test_T1b_complete_mixing(n_inst=600):
    """Cor 3.3 for complete graphs with adequate terminal: sorted representatives have MP."""
    rng = random.Random(15)
    cnt = 0
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 4), rng.randint(1, 4), rng.randint(2, 9)
        T1 = rng.randint(1, 3)
        a = [rng.randint(1, B) for _ in range(nA)]
        b = [rng.randint(1, B) for _ in range(nB)]
        inst = SInst(a, b, B, [rng.randint(1, B) for _ in range(T1)], [rng.randint(1, 3 * B) for _ in range(T1)],
                     [B], [rng.randint(B, 6 * B)])
        reps = {}
        for m, Ls in layers_by_size(inst).items():
            if any(L.nonempty for L in Ls):
                ia = sorted(range(nA), key=lambda i: (a[i], i))[:m]
                jb = sorted(range(nB), key=lambda j: (b[j], j))[:m][::-1]
                reps[m] = Layer(inst, tuple(sorted(zip(ia, jb))))
        assert mix_ok(reps)
        cnt += 1
    print(f"ok test_T1b_complete_mixing: {cnt} complete-graph instances, sorted representatives have MP")


def test_T1b_pair_split(n_inst=500):
    """A(empty matching) contains every A(M) (any terminal, any windows)."""
    rng = random.Random(6)
    cnt = 0
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 3), rng.randint(1, 3), rng.randint(2, 8)
        T1, T2 = rng.randint(1, 3), rng.randint(1, 3)
        inst = SInst([rng.randint(1, B) for _ in range(nA)], [rng.randint(1, B) for _ in range(nB)], B,
                     [rng.randint(1, B) for _ in range(T1)], [rng.randint(1, 3 * B) for _ in range(T1)],
                     [rng.randint(1, B) for _ in range(T2)], [rng.randint(1, 3 * B) for _ in range(T2)],
                     eA=[rng.randint(0, T1) for _ in range(nA)] if rng.random() < .5 else None)
        E = Layer(inst, ())
        for M in matchings(inst):
            L = Layer(inst, M)
            assert all(x >= y for x, y in zip(E.G, L.G)) and E.contains(L)
            cnt += 1
    print(f"ok test_T1b_pair_split: {cnt} matchings: G_empty >= G_M pointwise, A(empty) contains A(M)")


def test_T1b_gap_search(n_inst=1500):
    """Evidence for Conjecture 3.4 (D - CH <= f in the plug model, common window)."""
    rng = random.Random(7)
    best = Fr(0)
    for _ in range(n_inst):
        nA, nB, B = rng.randint(1, 4), rng.randint(1, 4), rng.randint(3, 10)
        T1 = rng.randint(2, 4)
        edges = {(i, j) for i in range(nA) for j in range(nB) if rng.random() < .6}
        inst = SInst([rng.randint(1, B) for _ in range(nA)], [rng.randint(1, B) for _ in range(nB)], B,
                     [rng.randint(1, B // 2 + 1) for _ in range(T1)], [1000] * T1, [B], [10 ** 4], edges=edges)
        allL = [L for L in (Layer(inst, M) for M in matchings(inst)) if L.nonempty]
        if len(allL) < 2:
            continue
        for _ in range(30):
            L1, L2 = rng.sample(allL, 2)
            z1 = L1.greedy_min([rng.randint(-4, 4) for _ in range(inst.T)])[1]
            z2 = L2.greedy_min([rng.randint(-4, 4) for _ in range(inst.T)])[1]
            mu = Fr(rng.randint(1, 7), 8)
            z = [mu * x + (1 - mu) * y for x, y in zip(z1, z2)]
            t = mu * len(L1.M) + (1 - mu) * len(L2.M)
            km = max(len(L.M) for L in allL if L.member(z))
            best = max(best, t - km)
    assert best <= 1
    print(f"ok test_T1b_gap_search: {n_inst} plug-model instances, two-point mixtures: "
          f"largest (t - kmax) = {best} <= 1 (Conjecture 3.4 evidence)")


# ---------------------------------------------------------------------- T2
def test_T2_two_classes():
    """Example 3: two classes with disjoint early windows; D - CH = 2f(1-eps)."""
    inst = SInst([1, 1], [1, 1], 1, [5, 5], [5, 5], [5], [100], edges={(0, 0), (1, 1)},
                 eA=[0, 1], sB=[1, 2])
    z2, z0 = [1, 1, 2], [0, 0, 4]
    assert Layer(inst, ((0, 0), (1, 1))).member(z2) and Layer(inst, ()).member(z0)
    # every plan containing pair (i,i) has e_i >= 1, so the cap e_1, e_2 <= 1 - eps excludes all pairings
    for M in matchings(inst):
        L = Layer(inst, M)
        for (i, _) in M:
            w = [0, 0, 0]
            w[i] = 1
            assert L.nonempty and L.greedy_min(w)[0] >= 1
    out = []
    for eps in (Fr(1, 4), Fr(1, 10), Fr(1, 100)):
        z = [(1 - eps) * x + eps * y for x, y in zip(z2, z0)]
        assert kmax(inst, z) == 0
        out.append((str(eps), str(2 * (1 - eps))))
    print(f"ok test_T2_two_classes: (eps, (D-CH)/f) = {out}; > 1 for eps < 1/2, tends to the SF bound 2")


# ---------------------------------------------------------------------- T4
def fifo(inst, m):
    A = sorted(range(len(inst.a)), key=lambda i: (inst.eA[i], i))[:m]
    Bs = sorted(range(len(inst.b)), key=lambda j: (-inst.sB[j], j))[:m]
    Bs = sorted(Bs, key=lambda j: (inst.sB[j], j))
    return tuple(sorted(zip(A, Bs)))


def test_T4_homogeneous(n_inst=1200):
    rng = random.Random(8)
    layers = lifo_fail = 0
    for _ in range(n_inst):
        nA, nB, T1, B = rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4), rng.randint(2, 8)
        a, b = rng.randint(1, B), rng.randint(1, B)
        eA = [rng.randint(0, T1) for _ in range(nA)]
        sB = [rng.randint(0, T1) for _ in range(nB)]          # general staggering, Gamma = time-compatible pairs
        K = [rng.randint(0, 2 * B) for _ in range(T1)]
        inst = SInst([a] * nA, [b] * nB, B, K, K, [B], [rng.randint(B, 10 * B)], eA=eA, sB=sB)
        reps = {}
        for m, Ls in layers_by_size(inst).items():
            if not any(L.nonempty for L in Ls):
                continue
            Fm = Layer(inst, fifo(inst, m))
            assert all(inst.allowed(i, j) for i, j in Fm.M)
            assert all(Fm.contains(L) for L in Ls), "Thm 6(i) violated"
            reps[m] = Fm
            layers += 1
            A = sorted(range(nA), key=lambda i: (inst.eA[i], i))[:m]
            Bs = sorted(sorted(range(nB), key=lambda j: (-inst.sB[j], j))[:m], key=lambda j: (inst.sB[j], j))[::-1]
            lifo = tuple(sorted(zip(A, Bs)))
            if not all(inst.allowed(i, j) for i, j in lifo) or not all(Layer(inst, lifo).contains(L) for L in Ls):
                lifo_fail += 1
        assert mix_ok(reps), "Thm 6(ii) violated"
    print(f"ok test_T4_homogeneous: {n_inst} instances, {layers} nonempty layers: FIFO dominates, MP holds; "
          f"earliest-end-with-latest-start fails (incompatible or not dominating) in {lifo_fail}")


def test_T4_example4():
    inst = SInst([1], [1, 2], 2, [5], [5], [5], [100], eA=[0], sB=[0, 1])
    L1, L2, L0 = Layer(inst, ((0, 0),)), Layer(inst, ((0, 1),)), Layer(inst, ())
    S0 = inst.S0
    assert L1.member([0, S0]) and not L2.member([0, S0])
    assert L2.member([1, S0 - 1]) and not L1.member([1, S0 - 1])
    assert not dominating(inst, 1)
    z = [Fr(1, 2), S0 - Fr(1, 2)]
    assert kmax(inst, z) == 0 and L0.member(z)      # t = 1: D - CH = f
    # per-cardinality commitment regret at spread pi = p_e - p_l (fee f = 1): min(|pi|, f)
    f = Fr(1)
    for pi in (Fr(-3), Fr(-1, 2), Fr(1, 3), Fr(2)):
        w = [pi, Fr(0)]
        h = {k: L.greedy_min(w)[0] for k, L in (("B1", L1), ("B2", L2), ("0", L0))}
        V = min(2 * f + min(h["B1"], h["B2"]), 3 * f + h["0"])
        reg = {k: min(2 * f + h[k], 3 * f + h["0"]) - V for k in ("B1", "B2")}
        assert max(reg.values()) == min(abs(pi), f)
    print("ok test_T4_example4: 3 services, 1 early slot, complete compatibility: no dominating matching; "
          "D - CH = f; worst commitment regret = min(|spread|, f)")


def example5(k, delta):
    B = 2 * k + 2
    a = [Fr(B, 2) - (1 - delta) * i for i in range(1, k + 1)]
    b = [Fr(B, 2) + 1 + (1 - delta) * j for j in range(1, k + 1)]
    K = [Fr(10)] * k
    return SInst(a, b, B, K, K, [Fr(10 * B * k)], [Fr(10 * B * k)],
                 eA=list(range(k)), sB=list(range(1, k + 1)))


def test_T4_example5():
    out = []
    for k in (1, 2, 3, 4):
        delta, eps = Fr(1, 20), Fr(1, 10)
        inst = example5(k, delta)
        assert all(inst.a[i] + inst.b[i] - inst.B == 1 for i in range(k))
        diag = tuple((i, i) for i in range(k))
        z_full = [Fr(1)] * k + [inst.S0 - k]
        z_none = [Fr(0)] * k + [inst.S0]
        assert Layer(inst, diag).member(z_full) and Layer(inst, ()).member(z_none)
        z = [(1 - eps) * x + eps * y for x, y in zip(z_full, z_none)]
        assert kmax(inst, z) == 0
        out.append((k, str(k * (1 - eps))))
    print(f"ok test_T4_example5: staggered, heterogeneous, Gamma = time-compatible pairs (complete for k <= 2), "
          f"eps = 1/10, delta = 1/20: (k, (D-CH)/f) = {out}")


def test_T4_complete_compat_search(n_inst=800):
    rng = random.Random(9)
    nodom = layers = 0
    for _ in range(n_inst):
        nA, nB, T1, B = rng.randint(1, 3), rng.randint(1, 3), rng.randint(1, 4), rng.randint(3, 8)
        cut = rng.randint(0, T1)
        K = [rng.randint(1, 2 * B) for _ in range(T1)]
        inst = SInst([rng.randint(1, B) for _ in range(nA)], [rng.randint(1, B) for _ in range(nB)], B,
                     K, K, [B], [10 ** 4],
                     eA=[rng.randint(0, cut) for _ in range(nA)], sB=[rng.randint(cut, T1) for _ in range(nB)])
        for m, Ls in layers_by_size(inst).items():
            if any(L.nonempty for L in Ls):
                layers += 1
                nodom += not dominating(inst, m, Ls)
    print(f"ok test_T4_complete_compat_search: heterogeneous energies, complete time-compatibility: "
          f"{nodom} of {layers} nonempty layers have no dominating matching")


if __name__ == "__main__":
    import time
    t0 = time.time()
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print(f"all tests passed in {time.time() - t0:.0f}s")
