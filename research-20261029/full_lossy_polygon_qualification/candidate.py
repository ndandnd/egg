"""Analytical matching/polygon candidate; no I/O, native API or reference import."""
from fractions import Fraction as Q
from itertools import combinations
import re

def need(ok,message):
    if not ok:raise ValueError(message)

def rational(value):
    need(type(value) is str and len(value)<=1024,'Exact rational text required')
    need(re.fullmatch(r'-?[0-9]+(?:/[1-9][0-9]*|\.[0-9]+)?',value) is not None,'Bounded integer/fraction/decimal syntax; no exponent')
    x=Q(value)
    need(max(x.numerator.bit_length(),x.denominator.bit_length())<=4096,'Input fraction-size bound')
    return x

def parse(spec):
    need(type(spec) is dict and set(spec)==set(('id','B','a','b','alpha','delta','K','H','fee','d','edges')),'Exact literal schema')
    need(type(spec['id']) is str and 0<len(spec['id'])<=128,'Literal identity')
    need(type(spec['a']) is list and type(spec['b']) is list and 1<=len(spec['a'])==len(spec['b'])<=2,'One or two services per batch')
    s={k:rational(spec[k]) for k in ('B','alpha','delta','K','H','fee','d')}
    s.update(id=spec['id'],a=tuple(map(rational,spec['a'])),b=tuple(map(rational,spec['b'])))
    n=len(s['a']);need(s['B']>0 and 0<s['alpha']<=1 and 0<s['delta']<=1,'Capacity/efficiency domain')
    need(all(s[k]>=0 for k in ('K','H','fee','d')) and all(0<x<=s['B'] for x in s['a']+s['b']),'Physical nonnegative/positive domain')
    need(type(spec['edges']) is list and len(spec['edges'])<=n*n,'Edge-list bound')
    edges=[]
    for edge in spec['edges']:
        need(type(edge) is list and len(edge)==2 and all(type(x) is int and 0<=x<n for x in edge),'Zero-based typed edge indices')
        pair=tuple(edge);need(pair not in edges,'Duplicate declared edge');edges.append(pair)
        need(s['b'][edge[1]]+s['d']<=s['B'],'Theorem graph requires b_j+d<=B on EVERY declared edge; no silent filtering')
    s['edges']=tuple(sorted(edges));return s

def matching_minima(s):
    """Row-by-row subset DP; skip a row or match it to an unused allowed column."""
    n=len(s['a']);weights={(i,j):max(Q(0),s['a'][i]+s['b'][j]+s['d']-s['B']) for i,j in s['edges']}
    states={0:(Q(0),())}
    for i in range(n):
        following=dict(states)
        for mask,(cost,matching) in states.items():
            for j in range(n):
                if (i,j) not in weights or mask&(1<<j):continue
                newmask=mask|(1<<j);proposal=(cost+weights[i,j],matching+((i,j),))
                if newmask not in following or proposal<following[newmask]:following[newmask]=proposal
        states=following
    minima={}
    for mask,proposal in states.items():
        m=mask.bit_count()
        if m not in minima or proposal<minima[m]:minima[m]=proposal
    return minima,weights

def hull(points):
    """Canonical exact 2D hull: CCW from lexicographic minimum; no collinear interior."""
    p=sorted(set(points))
    if len(p)<=1:return p
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower=[];upper=[]
    for v in p:
        while len(lower)>=2 and cross(lower[-2],lower[-1],v)<=0:lower.pop()
        lower.append(v)
    for v in reversed(p):
        while len(upper)>=2 and cross(upper[-2],upper[-1],v)<=0:upper.pop()
        upper.append(v)
    return lower[:-1]+upper[:-1]

def polygon(halfspaces):
    """Intersect A*C+B*X<=rhs exactly. Fixed axes/gross bounds ensure boundedness."""
    points=set()
    for left,right in combinations(halfspaces,2):
        a,b,h=left['C'],left['X'],left['rhs'];c,d,k=right['C'],right['X'],right['rhs']
        determinant=a*d-b*c
        if determinant==0:continue
        C=(h*d-b*k)/determinant;X=(a*k-h*c)/determinant
        if all(r['C']*C+r['X']*X<=r['rhs'] for r in halfspaces):points.add((C,X))
    vertices=hull(points)
    kind='EMPTY' if not vertices else 'POINT' if len(vertices)==1 else 'SEGMENT' if len(vertices)==2 else 'POLYGON'
    return kind,vertices

def derive(spec):
    """Return exact Fraction-valued records for ALL cardinalities0,...,n.

    Inputs outside the theorem contract raise ValueError (not physical
    infeasibility). Missing size-m matchings and empty resource polygons are
    separately recorded. Caller owns source admission/resources/JSON encoding.
    """
    s=parse(spec);n=len(s['a']);minima,weights=matching_minima(s)
    alpha,delta,B=s['alpha'],s['delta'],s['B'];S=sum(s['a']+s['b'],Q(0));P=sum(s['a'],Q(0))
    result=dict(id=s['id'],status='DERIVED',n=n,nu=max(minima),S=S,P=P,alpha=alpha,delta=delta,d=s['d'],
        edge_requirements=[dict(edge=[i,j],requirement=weights[i,j]) for i,j in s['edges']],cardinalities=[],
        scope='Complete finite-action common-loss polygons; prospective candidate implementation, no empirical/numerical qualification claim')
    for m in range(n+1):
        N=2*n-m;Sm=S+m*s['d'];c=s['fee']*N
        row=dict(m=m,N=N,S_m=Sm,c=c,matching_exists=m in minima)
        if m not in minima:
            row.update(status='NO_MATCHING',r_m=None,minimizing_matching=None,polygon_kind='EMPTY',vertices=[],load_cost_images=[],image_hull=[],halfspaces=None)
            result['cardinalities'].append(row);continue
        R,matching=minima[m];T=Sm-N*B;Qmin=max(T,Sm-alpha*s['H']);U=min(P/alpha,s['K'])
        halfspaces=[dict(name='minimum_purchases',C=Q(-1),X=Q(0),rhs=-R/alpha),
            dict(name='nonnegative_exports',C=Q(0),X=Q(-1),rhs=Q(0)),
            dict(name='gross_budget',C=Q(1),X=Q(1),rhs=s['K']),
            dict(name='minimum_battery_exchange',C=-alpha,X=1/delta,rhs=-Qmin),
            dict(name='maximum_battery_exchange',C=alpha,X=-1/delta,rhs=P)]
        kind,vertices=polygon(halfspaces)
        images=[(C-X,(Sm-alpha*C+X/delta)/alpha,c) for C,X in vertices]
        image_vertices=hull([(E,L) for E,L,_ in images])
        kappa=1/(alpha*delta)-1
        threshold=max((1/alpha-delta)*R+delta*T,2*R/alpha-s['K'],Sm/alpha-s['H'],(Sm/alpha+kappa*R/alpha-s['H'])/(1+kappa))
        row.update(status='FEASIBLE' if vertices else 'INFEASIBLE_RESOURCES',r_m=R,minimizing_matching=[list(e) for e in matching],
            T=T,Q_min=Qmin,Q_max=P,minimum_purchases=R/alpha,efficient_early_threshold=threshold,efficient_early_upper=U,
            polygon_kind=kind,halfspaces=halfspaces,vertices=[list(v) for v in vertices],
            load_cost_images=[list(v) for v in images],image_hull=[[E,L,c] for E,L in image_vertices],
            provenance='Minimum requirement by independent subset DP; cost/edge-list lexicographic tie break; exact rational line intersections')
        result['cardinalities'].append(row)
    return result
