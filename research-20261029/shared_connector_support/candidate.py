"""Sorted matching thresholds and exact clipped-frontier formulas; no oracle import."""
from fractions import Fraction as F


def _assignments(n):
    def go(i,used,pairs):
        if i == n:
            yield pairs
            return
        yield from go(i+1,used,pairs)
        for j in range(n):
            if not used & (1 << j):
                yield from go(i+1,used | (1 << j),pairs+((i,j),))
    return list(go(0,0,()))


def evaluate(A,B,capacity=F(20),K=F(10),H=F(30),fee=F(7)):
    A,B = tuple(map(F,A)),tuple(map(F,B))
    capacity,K,H,fee = map(F,(capacity,K,H,fee))
    n = len(A)
    if not 1 <= n <= 3 or len(B) != n or capacity <= 0 or min(K,H,fee) < 0:
        raise ValueError('Require n=1..3, capacity>0, K,H,fee>=0')
    if any(not 0 < v <= capacity for v in A+B):
        raise ValueError('Every service energy must lie in (0,capacity]')
    S,L,U = sum(A)+sum(B),max(F(0),sum(A)+sum(B)-H),min(sum(A),K)
    sa,sb = sorted(A),sorted(B)
    thresholds = [sum((max(F(0),sa[i]+sb[m-1-i]-capacity) for i in range(m)),F(0)) for m in range(n+1)]
    assignments = []
    for pairs in _assignments(n):
        matched = dict(pairs)
        lower = tuple(max(F(0),A[i]+B[matched[i]]-capacity) if i in matched else F(0) for i in range(n))
        lo = max(L,sum(lower))
        assignments.append(dict(pairs=pairs,lower=lower,upper=A,sum_interval=(L,U),
                                interval=(lo,U) if lo <= U else None,ops=fee*(2*n-len(pairs))))
    base = dict(matching_thresholds=thresholds,L=L,U=U,assignments=assignments,rawcount=len(assignments))
    if L > U:
        return dict(base,status='INFEASIBLE',D=None,CH=None,gap=None,physical_optima=[],hull_optima=[],positive_gap=False)
    mmax = max(m for m,r in enumerate(thresholds) if r <= U)
    m0 = max(m for m,r in enumerate(thresholds) if r <= L)
    costs = [fee*(2*n-m) for m in range(n+1)]
    E0 = (S-20*n)/2
    clip = lambda e,lo,hi:min(hi,max(lo,e))
    energy = lambda e:4*e+(e*e+(S-e)**2)/(10*n)
    D = min(costs[m]+energy(clip(E0,max(L,thresholds[m]),U)) for m in range(mmax+1))
    if fee == 0:
        e = clip(E0,L,U)
        hull = [(energy(e),e,F(0))]
        frontier = [(L,F(0)),(U,F(0))]
    else:
        frontier = [(L,costs[m0])]+[(thresholds[m],costs[m]) for m in range(m0+1,mmax+1)]
        hull = []
        for (lo,c),(hi,d) in zip(frontier,frontier[1:]):
            slope = (d-c)/(hi-lo)
            e = clip(E0-F(5*n,2)*slope,lo,hi)
            ops = c+slope*(e-lo)
            hull.append((energy(e)+ops,e,ops))
        start,c = frontier[-1]
        e = clip(E0,start,U)
        hull.append((energy(e)+c,e,c))
        if start < U:
            frontier.append((U,c))
    CH = min(v for v,_,_ in hull)
    hull_optima = [dict(early=e,late=S-e,ops=c,value=v) for v,e,c in sorted(set(hull)) if v == CH]
    assert len(hull_optima) == 1
    star = hull_optima[0]['early']
    retained = [L]+[thresholds[m] for m in range(m0+1,mmax+1)]
    positive = fee > 0 and any(lo < star < hi for lo,hi in zip(retained,retained[1:]))
    optima = []
    feasible = [row for row in assignments if row['interval'] is not None]
    for row in feasible:
        e = clip(E0,*row['interval'])
        value = energy(e)+row['ops']
        if value != D:
            continue
        pe,pz = 4+e/(5*n),(S-e)/(5*n)
        responses = []
        for other in feasible:
            lo,hi = other['interval']
            z = lo if pe >= pz else hi
            interval = (lo,hi) if pe == pz else (z,z)
            responses.append(dict(pairs=other['pairs'],early_interval=interval,ops=other['ops'],
                price_cost=other['ops']+pe*z+pz*(S-z),
                allocation_set=dict(lower=other['lower'],upper=other['upper'],sum_interval=interval)))
        best = min(r['price_cost'] for r in responses)
        optima.append(dict(pairs=row['pairs'],early=e,late=S-e,ops=row['ops'],value=value,
            prices=(pe,pz),regret=row['ops']+pe*e+pz*(S-e)-best,
            response_sets=[r for r in responses if r['price_cost'] == best],
            allocation_set=dict(lower=row['lower'],upper=row['upper'],sum_interval=(e,e))))
    return dict(base,status='FEASIBLE',D=D,CH=CH,gap=D-CH,physical_optima=optima,
                hull_optima=hull_optima,positive_gap=positive,mmax=mmax,m0=m0,frontier=frontier)
