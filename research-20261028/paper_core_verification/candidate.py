"""Closed-form two-parameter characterization, independently checked by reference.py.

No reference imports, solver, discretization, data access or work at import.
Domain and assumptions are in PROTOCOL.md and PROOF.md.
"""
from fractions import Fraction as F


def supply(x):
    return F(90) - 2*x + x*x/5


def evaluate(K, fee):
    K, fee = F(K), F(fee)
    if not 0 <= K <= 30 or fee < 0:
        raise ValueError('Require 0 <= K <= 30 and fee >= 0')
    if K < 20:
        return dict(D=None, CH=None, physical_optima=[], positive_gap=False,
                    hull_early=None)
    lo, d = 30-K, K-20
    t = max(F(5), lo)
    h = F(10) if d == 0 else min(F(10), max(lo, 5+5*fee/(2*d)))
    cost_one, cost_two = fee+90, 2*fee+supply(t)
    D = min(cost_one, cost_two)
    CH = fee+90 if d == 0 else 2*fee-fee*(h-lo)/d+supply(h)
    opts = []
    for partition, count, x, value in [('AB', 1, F(10), cost_one),
                                      ('A|B', 2, t, cost_two)]:
        if value != D:
            continue
        pe, pl = 4+x/5, (30-x)/5
        q = pe-pl
        one = fee + 10*pe + 20*pl
        bx = lo if q > 0 else F(10) if q < 0 else lo
        two = 2*fee + bx*pe + (30-bx)*pl
        V = min(one, two)
        sets = []
        if one == V:
            sets.append(dict(partition='AB', early_interval=(F(10), F(10))))
        if two == V:
            sets.append(dict(partition='A|B', early_interval=(lo, F(10)) if q == 0 else (bx, bx)))
        opts.append(dict(partition=partition, early=x, late=30-x,
                         ops=count*fee, objective=value, prices=(pe, pl),
                         own_price_regret=count*fee+pe*x+pl*(30-x)-V,
                         response_minimizer_sets=sets))
    positive = (d > 0 and fee > 0 and
                max(F(0), F(2, 5)*d*(lo-5)) < fee < 2*d)
    return dict(D=D, CH=CH, physical_optima=opts, positive_gap=positive,
                hull_early=h)
