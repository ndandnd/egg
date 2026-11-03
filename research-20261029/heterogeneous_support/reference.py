"""Independent exact physical enumeration for at most three two-batch services.

No cardinality matching reduction or discrete-convex support criterion is used.
All partial crossmatchings, physical vertices and continuous early sums remain.
"""
from fractions import Fraction as F
from itertools import combinations


def _solve(rows,rhs,n):
    a = [[F(v) for v in row]+[F(b)] for row,b in zip(rows,rhs)]
    for c in range(n):
        pivot = next((i for i in range(c,n) if a[i][c]),None)
        if pivot is None:
            return None
        a[c],a[pivot] = a[pivot],a[c]
        d = a[c][c]
        a[c] = [v/d for v in a[c]]
        for i in range(n):
            if i != c and a[i][c]:
                d = a[i][c]
                a[i] = [v-d*w for v,w in zip(a[i],a[c])]
    return tuple(row[-1] for row in a)


def _vertices(n,constraints):
    # Retain every original row in the report; consolidate only redundant
    # parallel rows in this generic enumeration to keep the small reference lean.
    reduced = {}
    for constraint in constraints:
        row,rhs = constraint['row'],constraint['rhs']
        if not any(row):
            if rhs < 0:
                return []
            continue
        reduced[row] = min(rhs,reduced.get(row,rhs))
    inequalities = sorted(reduced.items())
    result = set()
    for active in combinations(inequalities,n):
        point = _solve([row for row,_ in active],[rhs for _,rhs in active],n)
        if point is not None and all(sum(c*x for c,x in zip(row,point)) <= rhs for row,rhs in inequalities):
            result.add(point)
    return sorted(result)


def _matchings(n):
    def extend(i,available,pairs):
        if i == n:
            yield tuple(pairs)
            return
        yield from extend(i+1,available,pairs)
        for j in sorted(available):
            yield from extend(i+1,available-{j},pairs+[(i,j)])
    return list(extend(0,set(range(n)),[]))


def _model(A,B,fee,pairs):
    n = len(A)
    paired = dict(pairs)
    used_b = {j for _,j in pairs}
    buses = [dict(bus=i,A=i,B=paired.get(i)) for i in range(n)]
    buses += [dict(bus=n+j,A=None,B=j) for j in range(n) if j not in used_b]
    constraints,equalities = [],[]
    zero = (F(0),)*n
    def le(row,rhs,description):
        constraints.append(dict(row=tuple(map(F,row)),rhs=F(rhs),description=description))
    terminal_constant = F(0)
    terminal_row = [F(0)]*n
    for bus in buses:
        i,j = bus['A'],bus['B']
        row = [F(0)]*n
        if i is not None:
            row[i] = 1
            le([-v for v in row],0,'nonnegative early charge bus '+str(bus['bus']))
            le(row,10,'individual early power bus '+str(bus['bus']))
            le(zero,20-A[i],'SOC after A nonnegative bus '+str(bus['bus']))
            le(row,A[i],'SOC after early charge at most 20 bus '+str(bus['bus']))
            demand = A[i]+(B[j] if j is not None else 0)
            le([-v for v in row],20-demand,'SOC after all services nonnegative bus '+str(bus['bus']))
        else:
            demand = B[j]
            le(zero,20-demand,'SOC after B nonnegative bus '+str(bus['bus']))
            equalities.append(dict(description='B-only early charge is zero because it starts full',bus=bus['bus']))
        # Full terminal refill eliminates z=demand-x from the raw equations.
        equalities.append(dict(description='full terminal SOC 20',bus=bus['bus'],
                               terminal_constant=F(demand),terminal_early_row=tuple(-F(v) for v in row)))
        le(row,demand,'nonnegative terminal demand bus '+str(bus['bus']))
        le([-v for v in row],20-demand,'terminal battery headroom bus '+str(bus['bus']))
        le([-v for v in row],30-demand,'individual terminal-hour power bus '+str(bus['bus']))
        terminal_constant += demand
        terminal_row = [a-v for a,v in zip(terminal_row,row)]
        bus['demand'] = F(demand)
    le([1]*n,10*n,'aggregate early grid power')
    le(terminal_row,30*n-terminal_constant,'aggregate terminal grid power')
    vertices = _vertices(n,constraints)
    return dict(pairs=pairs,buses=buses,ops=fee*len(buses),constraints=constraints,
                equalities=equalities,vertices=vertices,
                interval=(min(map(sum,vertices)),max(map(sum,vertices))) if vertices else None)


def _allocation(model,E):
    vertices = model['vertices']
    low = min(vertices,key=lambda x:(sum(x),x))
    high = max(vertices,key=lambda x:(sum(x),x))
    lo,hi = sum(low),sum(high)
    if not lo <= E <= hi:
        raise ValueError('Requested early energy outside physical interval')
    weight = (E-lo)/(hi-lo) if hi != lo else F(0)
    return tuple((1-weight)*x+weight*y for x,y in zip(low,high))


def _witness(A,B,model,E,allocation=None):
    n = len(A)
    x = _allocation(model,E) if allocation is None else tuple(map(F,allocation))
    if len(x) != n or sum(x) != E:
        raise ValueError('Witness allocation does not match requested early sum')
    services,charges = [],[]
    paired = dict(model['pairs'])
    used_b = set(paired.values())
    unpaired_a = [i for i in range(n) if i not in paired]
    unpaired_b = [j for j in range(n) if j not in used_b]
    for i,a in enumerate(A):
        services.append((i,'A',i,F(0),F(1),a))
        if x[i]:
            charges.append((i,'early',i,F(1),F(1)+x[i]/10,F(10)))
    for j,b in enumerate(B):
        bus = next((i for i,jj in model['pairs'] if jj == j),n+j)
        services.append((bus,'B',j,F(2),F(3),b))
    groups = [[(i,A[i]+B[j]-x[i])] for i,j in model['pairs']]
    groups += [[(i,A[i]-x[i]),(n+j,B[j])] for i,j in zip(unpaired_a,unpaired_b)]
    for connector,group in enumerate(groups):
        cursor = F(3)
        for bus,energy in group:
            if energy:
                end = cursor+energy/30
                charges.append((bus,'terminal',connector,cursor,end,F(30)))
                cursor = end
    witness = dict(early_allocation=x,services=services,charges=charges)
    replay(A,B,model['pairs'],E,witness)
    return witness


def replay(A,B,pairs,E,witness):
    """Independent exact coverage, per-bus SOC and all connector/grid checks."""
    A,B = tuple(map(F,A)),tuple(map(F,B))
    n = len(A)
    assert len(B) == n and len({i for i,j in pairs}) == len(pairs) == len({j for i,j in pairs})
    assert all(0 <= i < n and 0 <= j < n for i,j in pairs)
    paired = dict(pairs)
    expected = [(i,'A',i,F(0),F(1),a) for i,a in enumerate(A)]
    for j,b in enumerate(B):
        bus = next((i for i,jj in pairs if jj == j),n+j)
        expected.append((bus,'B',j,F(2),F(3),b))
    assert sorted(witness['services']) == sorted(expected)
    buses = {row[0] for row in expected}
    charges = witness['charges']
    for bus,window,connector,start,end,power in charges:
        assert bus in buses and isinstance(connector,int) and 0 <= connector < n
        assert start < end and power >= 0
        assert (window == 'early' and 1 <= start < end <= 2 and power <= 10) or (
            window == 'terminal' and 3 <= start < end <= 4 and power <= 30)
    cuts = sorted({F(0),F(1),F(2),F(3),F(4)} |
                  {t for _,_,_,s,e,_ in charges for t in (s,e)})
    soc = {bus:F(20) for bus in buses}
    early_by_bus = {bus:F(0) for bus in buses}
    total_early,total_late = F(0),F(0)
    for left,right in zip(cuts,cuts[1:]):
        assert 0 <= left < right <= 4
        active = [row for row in charges if row[3] <= left and right <= row[4]]
        window = 'early' if 1 <= left < 2 else 'terminal' if 3 <= left < 4 else None
        limit = F(10) if window == 'early' else F(30) if window == 'terminal' else F(0)
        assert sum(row[5] for row in active) <= n*limit
        for connector in range(n):
            assert len([row for row in active if row[2] == connector]) <= 1
        for bus in buses:
            own = [row for row in active if row[0] == bus]
            assert len(own) <= 1
            power = sum((row[5] for row in own),F(0))
            assert power <= limit
            serving = [row for row in expected if row[0] == bus and row[3] <= left and right <= row[4]]
            assert len(serving) <= 1 and not (serving and own)
            drain = serving[0][5] if serving else F(0)
            gain = power*(right-left)
            if window == 'early':
                early_by_bus[bus] += gain
                total_early += gain
            elif window == 'terminal':
                total_late += gain
            soc[bus] += gain-drain*(right-left)
            assert 0 <= soc[bus] <= 20
    assert all(value == 20 for value in soc.values())
    assert total_early == E and total_early+total_late == sum(A)+sum(B)
    assert tuple(early_by_bus[i] for i in range(n)) == tuple(witness['early_allocation'])
    assert all(early_by_bus[bus] == 0 for bus in buses if bus >= n)
    return True


def _hull(points):
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    points = sorted(set(points))
    lower,upper = [],[]
    for chain,sequence in ((lower,points),(upper,reversed(points))):
        for point in sequence:
            while len(chain) >= 2 and cross(chain[-2],chain[-1],point) <= 0:
                chain.pop()
            chain.append(point)
    return lower,lower[:-1]+upper[:-1] if len(points)>1 else points


def evaluate(A,B,fee=F(7)):
    """All projected physical optima, with full individual-allocation sets.

    Each optimum record represents an assignment and its unique optimal early
    sum, not a finite enumeration of every charging schedule. Its allocation_set
    retains the raw inequalities and the exact sum equality for the continuum.
    """
    A,B,fee = tuple(map(F,A)),tuple(map(F,B)),F(fee)
    n = len(A)
    if not 1 <= n <= 3 or len(B) != n or fee <= 0:
        raise ValueError('Require equal nonempty batches n<=3 and fee>0')
    if any(not 0 < v <= 20 for v in A+B) or any(a+b > 30 for a in A for b in B):
        raise ValueError('Require energies in (0,20] and every cross sum<=30')
    S = sum(A)+sum(B)
    def energy(E):
        return 4*E+(E*E+(S-E)**2)/(10*n)
    models = [_model(A,B,fee,pairs) for pairs in _matchings(n)]
    candidates,points = [],[]
    for index,model in enumerate(models):
        model['assignment_id'] = index
        model['endpoints'] = []
        for vertex in model['vertices']:
            E = sum(vertex)
            points.append((E,model['ops']))
            # Every raw vertex, not merely a projected endpoint, is replayed.
            witness = _witness(A,B,model,E,allocation=vertex)
            model['endpoints'].append(dict(early=E,late=S-E,ops=model['ops'],
                                           raw_early=vertex,witness=witness))
        if model['interval'] is not None:
            lo,hi = model['interval']
            stationary = (S-20*n)/2
            E = min(hi,max(lo,stationary))
            candidates.append((energy(E)+model['ops'],index,E))
    D = min(value for value,_,_ in candidates)
    optima = []
    for value,index,E in candidates:
        if value != D:
            continue
        model = models[index]
        pe,pz = 4+E/(5*n),(S-E)/(5*n)
        response_rows = []
        for response in models:
            lo,hi = response['interval']
            x = lo if pe >= pz else hi
            interval = (lo,hi) if pe == pz else (x,x)
            response_rows.append(dict(assignment_id=response['assignment_id'],pairs=response['pairs'],
                early_interval=interval,total_energy=S,ops=response['ops'],
                price_cost=pe*x+pz*(S-x)+response['ops']))
        best = min(row['price_cost'] for row in response_rows)
        optima.append(dict(assignment_id=index,pairs=model['pairs'],early=E,late=S-E,
            ops=model['ops'],value=value,prices=(pe,pz),regret=pe*E+pz*(S-E)+model['ops']-best,
            response_sets=[row for row in response_rows if row['price_cost'] == best],
            allocation_set=dict(inequalities=model['constraints'],sum_equality=([F(1)]*n,E)),
            witness=_witness(A,B,model,E)))
    lower,hull = _hull(points)
    hull_candidates = set(lower)
    for a,b in zip(lower,lower[1:]):
        if a[0] == b[0]:
            continue
        slope = (b[1]-a[1])/(b[0]-a[0])
        stationary = (S-20*n)/2-F(5*n,2)*slope
        E = min(b[0],max(a[0],stationary))
        hull_candidates.add((E,a[1]+slope*(E-a[0])))
    CH = min(energy(E)+ops for E,ops in hull_candidates)
    hull_optima = [dict(early=E,late=S-E,ops=ops,value=CH)
                   for E,ops in sorted(hull_candidates) if energy(E)+ops == CH]
    return dict(D=D,CH=CH,physical_optima=optima,hull_optima=hull_optima,
                hull_vertices=hull,lower_hull=lower,rawcount=len(models),assignments=models,
                provenance=dict(arithmetic='stdlib Fraction',n=n,A=A,B=B,fee=fee,
                    enumeration='all partial bipartite crossmatchings; raw SOC active vertices',
                    objective='quadratic minimized continuously on every assignment interval and every lower hull edge',
                    initial_terminal_inventory=F(20),early_connectors=n,terminal_connectors=n,
                    early_per_bus_and_connector_power=F(10),early_grid_power=F(10*n),
                    terminal_per_bus_and_connector_power=F(30),terminal_grid_power=F(30*n)))
