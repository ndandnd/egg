"""Analytical matching-threshold candidate, independent of raw SOC polytopes."""
from fractions import Fraction as Q
from itertools import combinations

def exact(v):
    if isinstance(v,(bool,float)):raise ValueError('Exact rational required')
    return Q(v)

def curve(S,P,cap,alpha,delta,K,H,fee,N,R):
    kappa=1/(alpha*delta)-1
    lo=max((1/alpha-delta)*R+delta*(S-N*cap),2*R/alpha-K,
           S/alpha-H,(S/alpha+kappa*R/alpha-H)/(1+kappa))
    hi=min(P/alpha,K)
    planes=[(S/alpha,Q(-1)),(S/alpha+kappa*R/alpha,-1-kappa)]
    pieces=[]
    if lo<=hi:
        knots=sorted({lo,hi}|({R/alpha} if lo<R/alpha<hi else set()))
        if lo==hi:knots=[lo,hi]
        for left,right in zip(knots,knots[1:]):
            index=1 if (left+right)/2<R/alpha else 0
            intercept,slope=planes[index]
            pieces.append(dict(left=left,right=right,intercept=intercept,slope=slope))
    return dict(N=N,R=R,ops=fee*N,lower=lo,upper=hi,feasible=lo<=hi,planes=planes,segments=pieces)

def derive(raw):
    A,B=([exact(x) for x in raw[k]] for k in ('A','B'));n=len(A)
    cap,alpha,delta,K,H,fee=(exact(raw[k]) for k in ('capacity','eta_c','eta_d','K','H','fee'))
    if not(n in (1,2) and len(B)==n and cap>0 and all(0<x<=cap for x in A+B)
           and 0<alpha<=1 and 0<delta<=1 and K>=0 and H>=0 and fee>0):raise ValueError('Domain')
    edges=sorted(set(tuple(e) for e in raw['allowed']))
    if not all(len(e)==2 and all(type(i) is int and 0<=i<n for i in e) for e in edges):raise ValueError('Graph')
    S,P=sum(A+B,Q(0)),sum(A,Q(0));args=(S,P,cap,alpha,delta,K,H,fee)
    assignments=[]
    for m in range(n+1):
        for selected in combinations(edges,m):
            if len({i for i,j in selected})!=m or len({j for i,j in selected})!=m:continue
            R=sum((max(Q(0),A[i]+B[j]-cap) for i,j in selected),Q(0))
            assignments.append(dict(matching=tuple(selected),m=m,**curve(*args,2*n-m,R)))
    # Subset DP computes cardinality minima separately from the assignment list.
    dp={(0,0):Q(0)}
    for i in range(n):
        following=dict(dp)
        for (mask,m),cost in dp.items():
            for j in range(n):
                if (i,j) in edges and not(mask>>j&1):
                    key=(mask|1<<j,m+1);value=cost+max(Q(0),A[i]+B[j]-cap)
                    if key not in following or value<following[key]:following[key]=value
        dp=following
    minima={}
    for (mask,m),cost in dp.items():minima[m]=min(minima.get(m,cost),cost)
    cardinalities=[dict(m=m,**curve(*args,2*n-m,minima[m])) for m in sorted(minima)]
    return dict(assignments=assignments,cardinalities=cardinalities,
                scope='cycle-free efficient curves; no full-projection or support claim')
