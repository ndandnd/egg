#!/usr/bin/env python3
"""Independent exact audit; never imports or executes the experiment code.

Convexification checks every segment joining cheapest-cost load points. The
producer instead constructs a lower hull and checks its adjacent segments.
All input/output reads are of the explicitly supplied public synthetic JSON.
"""
import argparse
import copy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

SOURCE_COMMIT = "7e139b32f8ae762482e33b688f75092e1a2afdf2"


def q(value):
    if not isinstance(value, str):
        raise AssertionError("scientific quantities must be rational strings")
    return F(value)


def check(row):
    es = tuple(map(q, row["energy"]))
    ce = tuple(map(q, row["early_cost"]))
    cl = tuple(map(q, row["late_cost"]))
    a0, a1 = map(q, row["a"])
    b = q(row["b"])
    cap = None if row["early_cap"] is None else q(row["early_cap"])
    n, total = len(es), sum(es)
    assert n == row["participants"] and len(ce) == len(cl) == n
    assert n > 0 and b > 0 and min(es) > 0

    def supply(x):
        return a0*x + a1*(total-x) + b*(x*x+(total-x)**2)/2

    def prices(x):
        return a0+b*x, a1+b*(total-x)

    # Bit masks, rather than the producer's Cartesian-product iterator.
    profiles = []
    cheapest = {}
    for mask in range(1 << n):
        z = tuple((mask >> (n-1-i)) & 1 for i in range(n))
        x = sum(e for e, v in zip(es, z) if v)
        if cap is not None and x > cap:
            continue
        c = sum((ce[i] if z[i] else cl[i]) for i in range(n))
        profiles.append((c+supply(x), x, c, z))
        cheapest[x] = min(cheapest.get(x, c), c)
    assert profiles
    zd, xd, cd, chosen = min(profiles)

    # The lower boundary in two dimensions consists of segments. Checking
    # every pair includes those boundary segments without constructing a hull.
    points = sorted(cheapest.items())
    candidates = [(c+supply(x), x, c) for x, c in points]
    for i, (x0, c0) in enumerate(points):
        for x1, c1 in points[i+1:]:
            slope = (c1-c0)/(x1-x0)
            stationary = (b*total+a1-a0-slope)/(2*b)
            x = min(x1, max(x0, stationary))
            c = c0+(x-x0)*slope
            candidates.append((c+supply(x), x, c))
    zch, xch, cch = min(candidates)
    gap = zd-zch
    assert gap >= 0

    # Count exposed lower vertices using all supporting-line inequalities,
    # independently of the producer's cross-product stack.
    vertices = 0
    for i, (x, c) in enumerate(points):
        left = [(cc-c)/(xx-x) for xx, cc in points[:i]]
        right = [(cc-c)/(xx-x) for xx, cc in points[i+1:]]
        if not left or not right or max(left) < min(right):
            vertices += 1

    best_at_load = {}
    for x in cheapest:
        p0, p1 = prices(x)
        best_at_load[x] = min(c+p0*y+p1*(total-y) for y, c in points)
    regrets, maximum_individual, supported = [], [], []
    for h, x, c, z in profiles:
        p0, p1 = prices(x)
        private = c+p0*x+p1*(total-x)
        r = private-best_at_load[x]
        own = [(ce[i]+p0*es[i] if z[i] else cl[i]+p1*es[i]) -
               min(ce[i]+p0*es[i], cl[i]+p1*es[i]) for i in range(n)]
        assert r >= h-zch >= gap
        if cap is None:
            assert sum(own) == r
            # Pair adjacent participants into economic owners. Each owner can
            # choose every joint menu combination; no shared restriction added.
            grouped_best = F(0)
            for lo in range(0, n, 2):
                hi = min(lo+2, n)
                grouped_best += min(
                    sum((ce[i]+p0*es[i] if (m >> (i-lo)) & 1
                         else cl[i]+p1*es[i]) for i in range(lo, hi))
                    for m in range(1 << (hi-lo)))
            assert grouped_best == best_at_load[x]
        regrets.append(r)
        maximum_individual.append(max(own))
        if r == 0:
            supported.append((h, z))
    assert bool(supported) == (gap == 0)
    assert all(h == zd for h, _ in supported)
    if gap == 0:
        assert all(c+sum(p*l for p, l in zip(prices(x), (x, total-x)))
                   == best_at_load[x] for h, x, c, z in profiles if h == zd)

    p0, p1 = prices(xch)
    v = min(c+p0*x+p1*(total-x) for x, c in points)
    fstar = (max(F(0), p0-a0)**2 + max(F(0), p1-a1)**2)/(2*b)
    fleet = cd+p0*xd+p1*(total-xd)-v
    supplier = supply(xd)-p0*xd-p1*(total-xd)+fstar
    assert v-fstar == zch
    assert fleet >= 0 and supplier >= 0 and fleet+supplier == gap

    rational_expected = dict(zd=zd, zch=zch, gap=gap,
        optimal_early_energy=xd, convex_early_energy=xch,
        minimum_joint_own_price_regret=min(regrets),
        minimum_max_individual_unrestricted_regret=min(maximum_individual),
        fleet_loc_at_ch_price=fleet, supplier_loc_at_ch_price=supplier)
    for key, value in rational_expected.items():
        assert q(row[key]) == value, (row["name"], key, row[key], str(value))
    assert row["relative_gap"] == (str(gap/zch) if zch else None)
    assert row["planner_choices"] == list(chosen)
    assert row["physical_schedules"] == len(profiles)
    assert row["lower_hull_vertices"] == vertices
    assert row["joint_price_support"] is bool(supported)

    if not row["name"].startswith("heterogeneous") and cap is None:
        assert len(set(es)) == 1 and set(ce+cl) == {F(0)} and a0 == a1 == 0
        e = es[0]
        odd = n % 2
        assert zch == b*n*n*e*e/4
        assert gap == odd*b*e*e/4
        assert min(regrets) == odd*b*e*e*(n+1)/2
        assert min(maximum_individual) == odd*b*e*e
        assert fleet == 0 and supplier == gap

    if cap is not None:
        assert es == (F(1), F(1)) and ce == cl == (F(0), F(0))
        assert (a0, a1, b, cap) == (F(0), F(2), F(1), F(1))
        assert (zd, zch, xd) == (F(3), F(3), F(1))
        assert list(map(q, row["energy_price"])) == [F(1), F(3)]
        tau = q(row["capacity_price"])
        assert tau == 2 and q(row["capacity_rent"]) == tau*xd == 2
        unrestricted, residual, priced = [], [], []
        for i in range(n):
            current = F(1) if chosen[i] else F(3)
            unrestricted.append(current-1)
            feasible_costs = []
            for alternative in [0, 1]:
                altered = list(chosen)
                altered[i] = alternative
                if sum(altered) <= cap:
                    feasible_costs.append(F(1) if alternative else F(3))
            residual.append(current-min(feasible_costs))
            priced.append((F(1)+tau if chosen[i] else F(3))-min(F(1)+tau, F(3)))
        for key, expected in [("unrestricted_individual_regrets", unrestricted),
                              ("residual_capacity_deviation_regrets", residual),
                              ("capacity_priced_individual_regrets", priced)]:
            assert list(map(q, row[key])) == expected
        assert sum(unrestricted) == 2 and sum(priced) == sum(residual) == 0
    return {"profiles": len(profiles), "positive_gap": gap > 0,
            "positive_fleet_loc": fleet > 0, "positive_supplier_loc": supplier > 0,
            "pair_segments": len(points)*(len(points)-1)//2}


def check_grid(rows):
    expected = {}
    for n in range(1, 13):
        for regime in ("fixed_unit_and_slope", "replicated_market", "fixed_total_energy"):
            e = F(1, n) if regime == "fixed_total_energy" else F(1)
            b = F(1, n) if regime == "replicated_market" else F(1)
            expected[f"{regime}_n{n:02d}"] = ([e]*n, [F(0)]*n, [F(0)]*n, [F(0), F(0)], b)
    for n in (4, 6, 8):
        for pattern, cycle in [("uniform", [1]), ("alternating", [1, 2]), ("three_sizes", [1, 2, 3])]:
            es = [F(cycle[i % len(cycle)]) for i in range(n)]
            for costs in ("zero", "alternating"):
                ce = [F(0) if costs == "zero" or i % 2 else F(1, 4) for i in range(n)]
                cl = [F(0) if costs == "zero" or not i % 2 else F(1, 4) for i in range(n)]
                for offset in (F(0), F(1, 2), F(2)):
                    expected[f"heterogeneous_n{n}_{pattern}_{costs}_a{offset}"] = (es, ce, cl, [F(0), offset], F(1))
    assert len(rows) == len(expected) == 90
    assert len({r["name"] for r in rows}) == 90
    for row in rows:
        actual = tuple(list(map(q, row[key])) for key in ("energy", "early_cost", "late_cost", "a")) + (q(row["b"]),)
        assert actual == expected[row["name"]]
        assert row["early_cap"] is None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    raw = args.results.read_bytes()
    document = json.loads(raw)
    assert document["schema"] == "egg-two-slot-exploratory-v1"
    assert document["arithmetic"] == "fractions.Fraction"
    assert document["code_commit"] == SOURCE_COMMIT
    assert document["case_count"] == len(document["rows"]) == 90
    check_grid(document["rows"])
    totals = {k: 0 for k in ("profiles", "positive_gap", "positive_fleet_loc", "positive_supplier_loc", "pair_segments")}
    for row in document["rows"] + [document["shared_capacity_witness"]]:
        for key, value in check(row).items():
            totals[key] += value
    # These negative controls establish that the independent auditor rejects
    # wrong artifacts, not merely the producer's own assertion success.
    rejected = []
    for key in ("zch", "gap", "minimum_joint_own_price_regret", "minimum_max_individual_unrestricted_regret", "fleet_loc_at_ch_price", "supplier_loc_at_ch_price"):
        wrong = copy.deepcopy(document["rows"][0])
        wrong[key] = str(q(wrong[key])+1)
        try:
            check(wrong)
        except AssertionError:
            rejected.append(key)
        else:
            raise AssertionError("negative control accepted: "+key)
    print(json.dumps(dict(status="PASS", source_commit=SOURCE_COMMIT,
        artifact_sha256=hashlib.sha256(raw).hexdigest(), cases=90, shared_capacity_witnesses=1,
        method="all point-pair segments, no hull/import; exhaustive physical profiles",
        negative_controls_rejected=rejected, **totals), indent=2))


if __name__ == "__main__":
    main()
