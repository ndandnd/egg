"""Independent bounded rational physical polytopes, no threshold formulas.

spec: A,B lists of service energies, capacity, eta_c,eta_d,K,H,fee,
allowed list of (A_index,B_index). n=1 or2, zero reserve, no idle buses.
Only callable functions; no data reads or execution on import.
"""
from fractions import Fraction as Q
from itertools import combinations, product


def need(ok,message):
    if not ok: raise ValueError(message)


def exact(v):
    need(not isinstance(v,(bool,float)), 'exact rational required')
    return Q(v)


def solve(rows,rhs,n):
    matrix=[list(row)+[value] for row,value in zip(rows,rhs)]
    for col in range(n):
        pivot=next((j for j in range(col,n) if matrix[j][col]),None)
        if pivot is None:return None
        matrix[col],matrix[pivot]=matrix[pivot],matrix[col]
        scale=matrix[col][col];matrix[col]=[v/scale for v in matrix[col]]
        for j in range(n):
            if j!=col:
                scale=matrix[j][col]
                matrix[j]=[a-scale*b for a,b in zip(matrix[j],matrix[col])]
    return tuple(matrix[j][-1] for j in range(n))


def dot(a,b):return sum((x*y for x,y in zip(a,b)),Q(0))


def matchings(n,allowed):
    output=[]
    def visit(i,used,chosen):
        if i==n:output.append(tuple(chosen));return
        visit(i+1,used,chosen)
        for j in range(n):
            if j not in used and (i,j) in allowed:
                visit(i+1,used|{j},chosen+[(i,j)])
    visit(0,set(),[])
    return output


def witness(spec,buses,x):
    cap,alpha,delta,K,H=(spec[k] for k in ('capacity','eta_c','eta_d','K','H'))
    early=[];terminal=[];states=[];te=tt=Q(0)
    for index,(bus,exchange) in enumerate(zip(buses,x)):
        a,b=bus['a'],bus['b'];after_a=cap-a;after_early=after_a+exchange;after_b=after_early-b
        need(all(0<=v<=cap for v in (after_a,after_early,after_b)),'SOC')
        buy=exchange/alpha if exchange>=0 else Q(0)
        export=-delta*exchange if exchange<0 else Q(0)
        charge=(cap-after_b)/alpha
        if buy+export:
            need(K>0,'zero early power');duration=(buy+export)/K
            early.append(dict(bus=index,start=te,end=te+duration,buy=buy,export=export));te+=duration
        if charge:
            need(H>0,'zero terminal power');duration=charge/H
            terminal.append(dict(bus=index,start=tt,end=tt+duration,buy=charge));tt+=duration
        states.append(dict(after_A=after_a,after_early=after_early,after_B=after_b,final=cap))
    need(te<=1 and tt<=1,'shared connector')
    return dict(buses=buses,exchange=x,states=states,early=early,terminal=terminal)


def enumerate_physical(raw):
    spec={k:exact(raw[k]) for k in ('capacity','eta_c','eta_d','K','H','fee')}
    A,B=([exact(v) for v in raw[k]] for k in ('A','B'))
    n=len(A);need(n in (1,2) and len(B)==n,'n<=2 equal batches')
    cap,alpha,delta,K,H,fee=(spec[k] for k in ('capacity','eta_c','eta_d','K','H','fee'))
    need(cap>0 and all(0<v<=cap for v in A+B),'service/capacity')
    need(0<alpha<=1 and 0<delta<=1 and K>=0 and H>=0 and fee>0,'domain')
    allowed=set(tuple(e) for e in raw['allowed'])
    need(all(len(e)==2 and all(type(i) is int and 0<=i<n for i in e) for e in allowed),'allowed graph')
    assignments=matchings(n,allowed);branches=[];S=sum(A+B,Q(0))
    attempts=0
    for matching in assignments:
        used_a={i for i,j in matching};used_b={j for i,j in matching}
        buses=[dict(A=i,B=j,a=A[i],b=B[j]) for i,j in matching]
        buses += [dict(A=i,B=None,a=A[i],b=Q(0)) for i in range(n) if i not in used_a]
        buses += [dict(A=None,B=j,a=Q(0),b=B[j]) for j in range(n) if j not in used_b]
        d=len(buses)
        for signs in product((-1,1),repeat=d):
            rows=[]
            def bound(name,index,coefficient,rhs):
                vector=[Q(0)]*d;vector[index]=Q(coefficient);rows.append((name,tuple(vector),Q(rhs)))
            for i,bus in enumerate(buses):
                # Raw post-early and post-B inventory constraints; start after A.
                bound('early_capacity_'+str(i),i,1,bus['a'])
                bound('early_reserve_'+str(i),i,-1,cap-bus['a'])
                bound('after_B_reserve_'+str(i),i,-1,cap-bus['a']-bus['b'])
                bound('after_B_capacity_'+str(i),i,1,bus['a']+bus['b'])
                bound('sign_'+str(i),i,-signs[i],0)
            gross=tuple(1/alpha if s>0 else -delta for s in signs)
            ecoeff=tuple(1/alpha if s>0 else delta for s in signs)
            rows.append(('shared_early',gross,K))
            rows.append(('terminal_total',tuple(-1/alpha for _ in buses),H-S/alpha))
            # Identical left sides intersect to their tightest RHS. Preserve
            # every original row/name for provenance and final feasibility.
            grouped={}
            for name,vector,rhs in rows:
                if vector not in grouped:
                    grouped[vector]=dict(rhs=rhs,provenance=[])
                grouped[vector]['rhs']=min(grouped[vector]['rhs'],rhs)
                grouped[vector]['provenance'].append(dict(name=name,rhs=rhs))
            effective=[(tuple(v),entry['rhs']) for v,entry in grouped.items()]
            vertices={}
            for chosen in combinations(effective,d):
                attempts+=1;need(attempts<=2000000,'source-defined enumeration limit')
                x=solve([r[0] for r in chosen],[r[1] for r in chosen],d)
                if x is None or x in vertices:continue
                if all(dot(row,x)<=rhs for name,row,rhs in rows):
                    E=dot(ecoeff,x);L=(S-sum(x,Q(0)))/alpha
                    vertices[x]=dict(x=x,early=E,late=L,ops=fee*d,witness=witness(spec,buses,x))
            branches.append(dict(matching=matching,N=d,signs=signs,buses=buses,rows=rows,
                                 canonical_rows=[dict(coefficients=v,rhs=e['rhs'],provenance=e['provenance'])
                                                 for v,e in grouped.items()],
                                 vertices=list(vertices.values()),feasible=bool(vertices)))
    return dict(spec=spec,A=A,B=B,assignments=assignments,branches=branches,
                raw_assignment_count=len(assignments),raw_branch_count=len(branches),
                active_systems_considered=attempts,scope='cycle-free complete physical projection; zero reserve/no idles')


def slice_at(result,E,N=None):
    """Exact lower terminal slice by vertex-pair convex combinations per branch."""
    E=exact(E);answers={}
    for index,branch in enumerate(result['branches']):
        if N is not None and branch['N']!=N:continue
        points=branch['vertices'];candidates=[]
        for v in points:
            if v['early']==E:candidates.append((v['late'],v['x']))
        for v,w in combinations(points,2):
            if v['early']==w['early']:continue
            theta=(E-v['early'])/(w['early']-v['early'])
            if 0<=theta<=1:
                x=tuple((1-theta)*a+theta*b for a,b in zip(v['x'],w['x']))
                candidates.append(((1-theta)*v['late']+theta*w['late'],x))
        if candidates:
            L,x=min(candidates);count=branch['N']
            entry=dict(early=E,late=L,ops=result['spec']['fee']*count,branch=index,x=x,
                       witness=witness(result['spec'],branch['buses'],x))
            if count not in answers or L<answers[count]['late']:answers[count]=entry
    return answers


def replay(result,branch_index,value):
    """Independently replay submitted serial witness, including corruptions."""
    branch=result['branches'][branch_index];spec=result['spec'];buses=branch['buses']
    need(value['buses']==buses,'service assignment identity')
    cap,alpha,delta,K,H=(spec[k] for k in ('capacity','eta_c','eta_d','K','H'))
    count=len(buses);buy=[Q(0)]*count;export=[Q(0)]*count;terminal=[Q(0)]*count
    for key,power in (('early',K),('terminal',H)):
        previous=Q(0)
        for event in sorted(value[key],key=lambda e:exact(e['start'])):
            i=event['bus'];need(type(i) is int and 0<=i<count,'bus index')
            start,end=exact(event['start']),exact(event['end'])
            need(0<=previous<=start<end<=1,'connector overlap/window')
            previous=end
            c=exact(event['buy']);d=exact(event['export']) if key=='early' else Q(0)
            need(c>=0 and d>=0 and c+d<=power*(end-start),'power/energy')
            if key=='early':
                need(c==0 or d==0,'cycle-free action');buy[i]+=c;export[i]+=d
            else:terminal[i]+=c
    E=L=Q(0)
    for i,bus in enumerate(buses):
        need(buy[i]==0 or export[i]==0,'cycle-free bus')
        after_A=cap-bus['a'];after_early=after_A+alpha*buy[i]-export[i]/delta
        after_B=after_early-bus['b'];final=after_B+alpha*terminal[i]
        need(all(0<=v<=cap for v in (after_A,after_early,after_B,final)) and final==cap,'inventory/full refill')
        state=dict(after_A=after_A,after_early=after_early,after_B=after_B,final=final)
        need(value['states'][i]==state,'reported state mismatch')
        need(exact(value['exchange'][i])==after_early-after_A,'reported exchange mismatch')
        E+=buy[i]-export[i];L+=terminal[i]
    return dict(status='PASS',early=E,late=L,ops=spec['fee']*count)
