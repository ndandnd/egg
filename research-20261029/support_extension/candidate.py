"""Closed-form extension predictions, independent of raw SOC enumeration."""
from fractions import Fraction as F


def evaluate(B=None, fee=None, detour=False):
    if (B is None) != (fee is None):
        raise ValueError('Supply both B and fee')
    if B is not None:
        B, fee = F(B), F(fee)
        if not 20 <= B <= 30 or fee < 7:
            raise ValueError('Require 20 <= B <= 30 and fee >= 7')
        if fee != 7 and B != 25:
            raise ValueError('Formula domain: equal fee or B25')
    # Energy/cost dominance removes movement additions only in the analytic
    # prediction. The independent enumerator retains every raw branch.
    lines = [(F(10), F(10), F(7)), (F(0), F(10), F(14))]
    if B is not None:
        lines.append((30-B, F(10), fee))
    g = lambda x: 90-2*x+x*x/5
    points = {(max(lo, min(hi, F(5))), c) for lo, hi, c in lines}
    D = min(g(x)+c for x, c in points)
    if B is None:
        hx, hc, CH = F(27,4), F(371,40), F(7591,80)
    elif fee == 7:
        a = 30-B
        if a*a-5*a-F(35,2) <= 0:
            hx, hc, CH = max(a,F(5)), F(7), D
        else:
            hx = 5+F(35,2)/a
            hc = 14-7*hx/a
            CH = g(hx)+hc
    elif fee <= F(21,2):
        hx = 5+(fee-7)/2
        hc = fee-(fee-7)*(fee-7)/10
        CH = 85+fee-(fee-7)*(fee-7)/20
    else:
        hx, hc, CH = F(27,4), F(371,40), F(7591,80)

    def responses(pe, pz):
        all_values = []
        for lo, hi, c in lines:
            x = lo if pe >= pz else hi
            interval = (lo,hi) if pe == pz else (x,x)
            all_values.append((c+pe*x+pz*(30-x),interval,c))
        best = min(v for v, _, _ in all_values)
        sets = [dict(early_interval=i,total_energy=F(30),ops=c)
                for v,i,c in all_values if v == best]
        return best, sets

    optima = []
    for x,c in sorted(points):
        if g(x)+c == D:
            pe,pz = 4+x/5,(30-x)/5
            best,sets = responses(pe,pz)
            optima.append(dict(early=x,late=30-x,ops=c,prices=(pe,pz),
                               regret=c+pe*x+pz*(30-x)-best,response_sets=sets))
    best,_ = responses(F(6),F(4))
    return dict(D=D,CH=CH,hull_points=[(hx,30-hx,hc)],
                physical_optima=optima,old_plan_regret=147-best)
