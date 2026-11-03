"""Analytic threshold theorem; no reference import or physical vertex routine.

Cardinality thresholds use subset dynamic programming. Literal assignments
are separately retained for ties and complete fixed-price response sets.
"""
from fractions import Fraction as F


def _assignments(n):
    def visit(i,used,pairs):
        if i == n:
            yield pairs
        else:
            yield from visit(i+1,used,pairs)
            for j in range(n):
                if not used & (1 << j):
                    yield from visit(i+1,used | (1 << j),pairs+((i,j),))
    return list(visit(0,0,()))


def evaluate(A,B,fee=F(7)):
    A,B,fee = tuple(map(F,A)),tuple(map(F,B)),F(fee)
    n = len(A)
    if not 1 <= n <= 3 or len(B) != n or fee <= 0:
        raise ValueError('Require equal nonempty batches n<=3 and fee>0')
    if any(not 0 < v <= 20 for v in A+B) or any(a+b > 30 for a in A for b in B):
        raise ValueError('Require energies in (0,20] and every cross sum<=30')
    S,U = sum(A)+sum(B),sum(min(a,F(10)) for a in A)
    edge = [[max(F(0),a+b-20) for b in B] for a in A]
    dp = {0:F(0)}
    for i in range(n):
        following = dict(dp)
        for mask,value in dp.items():
            for j in range(n):
                if not mask & (1 << j):
                    new = mask | (1 << j)
                    proposal = value+edge[i][j]
                    if new not in following or proposal < following[new]:
                        following[new] = proposal
        dp = following
    thresholds = [min(v for mask,v in dp.items() if mask.bit_count() == m) for m in range(n+1)]
    assert thresholds[0] == 0
    assert all(thresholds[m+1]-thresholds[m] >= thresholds[m]-thresholds[m-1]
               for m in range(1,n))
    m0 = max(m for m,r in enumerate(thresholds) if r == 0)
    E0 = (S-20*n)/2
    energy = lambda E: 4*E+(E*E+(S-E)**2)/(10*n)
    clip = lambda x,lo,hi: min(hi,max(lo,x))
    costs = [fee*(2*n-m) for m in range(n+1)]
    D = min(costs[m]+energy(clip(E0,r,U)) for m,r in enumerate(thresholds))
    hull = []
    for j in range(m0+1,n+1):
        left,right = thresholds[j-1],thresholds[j]
        d = right-left
        h = clip(E0+F(5*n,2)*fee/d,left,right)
        ops = costs[j-1]-fee*(h-left)/d
        hull.append((energy(h)+ops,h,ops))
    h = clip(E0,thresholds[n],U)
    hull.append((costs[n]+energy(h),h,costs[n]))
    CH = min(value for value,_,_ in hull)
    hull_optima = [dict(early=E,late=S-E,ops=c,value=value)
                   for value,E,c in sorted(set(hull)) if value == CH]
    assert len(hull_optima) == 1
    E_star = hull_optima[0]['early']
    criterion_positive = any(thresholds[j-1] < E_star < thresholds[j] for j in range(m0+1,n+1))
    assignments = []
    for pairs in _assignments(n):
        paired = dict(pairs)
        lower = tuple(edge[i][paired[i]] if i in paired else F(0) for i in range(n))
        upper = tuple(min(a,F(10)) for a in A)
        assignments.append(dict(pairs=pairs,lower=lower,upper=upper,
                                interval=(sum(lower),U),ops=fee*(2*n-len(pairs))))
    optima = []
    for assignment in assignments:
        lo,hi = assignment['interval']
        E = clip(E0,lo,hi)
        value = energy(E)+assignment['ops']
        if value != D:
            continue
        pe,pz = 4+E/(5*n),(S-E)/(5*n)
        responses = []
        for response in assignments:
            lo2,hi2 = response['interval']
            x = lo2 if pe >= pz else hi2
            interval = (lo2,hi2) if pe == pz else (x,x)
            responses.append(dict(pairs=response['pairs'],early_interval=interval,
                total_energy=S,ops=response['ops'],price_cost=response['ops']+pe*x+pz*(S-x)))
        best = min(row['price_cost'] for row in responses)
        optima.append(dict(pairs=assignment['pairs'],early=E,late=S-E,ops=assignment['ops'],
            value=value,prices=(pe,pz),regret=assignment['ops']+pe*E+pz*(S-E)-best,
            response_sets=[row for row in responses if row['price_cost'] == best],
            allocation_set=dict(lower=assignment['lower'],upper=assignment['upper'],sum=E)))
    return dict(D=D,CH=CH,gap=D-CH,positive_gap=criterion_positive,
                matching_thresholds=thresholds,physical_optima=optima,
                hull_optima=hull_optima,assignments=assignments,rawcount=len(assignments))
