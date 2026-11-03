"""Distinct exact certificate method: admitted primal, then dual phase I.

No backend/model imports or native reruns. Primal recovery reuses one frozen
face and cached affine-algebra callbacks. Dual signs are solved as an exact
nonnegative feasibility problem, not guessed from free native multipliers.
The old failed attempt remains unchanged; this file requires a new paid freeze.
"""
from fractions import Fraction as Q
import time


class MethodFailure(ValueError):
    pass


def _require(condition,message):
    if not condition:
        raise MethodFailure(message)


class _Budget:
    def __init__(self,limits=None):
        self.limits=dict(rows=250,columns=1000,pivots=2000,operations=5000000,
                         fraction_bits=16384,seconds=30)
        self.limits.update(limits or {})
        self.started=time.monotonic()
        self.operations=0
        self.pivots=0

    def tick(self,value=Q(0)):
        self.operations+=1
        if (self.operations>self.limits['operations'] or self.pivots>self.limits['pivots']
            or time.monotonic()-self.started>self.limits['seconds']
            or value.numerator.bit_length()>self.limits['fraction_bits']
            or value.denominator.bit_length()>self.limits['fraction_bits']):
            raise MethodFailure('Exact phase-I resource checkpoint exceeded')
        return value


def _equations(equations,n):
    _require(isinstance(n,int) and not isinstance(n,bool) and n>=0,'Invalid nonnegative-variable count')
    output=[]
    for coefficients,rhs in equations:
        row={}
        for i,c in coefficients.items():
            _require(isinstance(i,int) and not isinstance(i,bool) and 0<=i<n,'Invalid equation column')
            value=Q(c)
            if value: row[i]=value
        output.append((row,Q(rhs)))
    return output


def verify_phase_one(equations,n,result):
    """Independent algebraic checks of a primal or Farkas certificate.

    For infeasibility: y*A<=0 and y*b>0 contradict A*z=b,z>=0.
    No simplex history, native status or phase-I optimality claim is trusted.
    """
    try:
        equations=_equations(equations,n)
        if result.get('status')=='FEASIBLE':
            z=list(map(Q,result['solution']))
            _require(len(z)==n and all(v>=0 for v in z),'Invalid nonnegative primal certificate')
            _require(all(sum((c*z[i] for i,c in row.items()),Q(0))==rhs for row,rhs in equations),
                     'Primal equality certificate failed')
            _require(Q(result['phase_one_objective'])==0,'Nonzero claimed feasible phase-I objective')
            return dict(status='VERIFIED_FEASIBLE')
        if result.get('status')=='INFEASIBLE':
            y=list(map(Q,result['farkas']))
            _require(len(y)==len(equations),'Farkas dimension mismatch')
            columns=[Q(0)]*n
            value=Q(0)
            for multiplier,(row,rhs) in zip(y,equations):
                value+=multiplier*rhs
                for i,c in row.items(): columns[i]+=multiplier*c
            _require(all(v<=0 for v in columns) and value>0,'Farkas signs or positive separation failed')
            _require(Q(result['phase_one_objective'])==value,'Farkas/objective mismatch')
            return dict(status='VERIFIED_INFEASIBLE',separation=value)
        raise MethodFailure('No completed phase-I certificate')
    except (MethodFailure,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        return dict(status='REJECTED',reason=str(exc))


def phase_one(equations,n,limits=None):
    """Deterministic rational phase I for A*z=b,z>=0; Bland's pivot rules.

    Artificial identity basis handles dependent/zero rows. At phase-I value
    zero no artificial cleanup or phase II is needed: the original-variable
    basic vector is already a feasible certificate. A positive optimum exports
    a checked Farkas certificate. Limits mean unresolved, never infeasible.
    """
    budget=_Budget(limits)
    result=dict(status='UNRESOLVED',algorithm='rational artificial-basis phase I; Bland entering/leaving')
    try:
        original=_equations(equations,n)
        m=len(original)
        _require(m<=budget.limits['rows'] and n+m<=budget.limits['columns'],
                 'Phase-I row/column limit exceeded')
        table,rhs,transforms,basis=[],[],[],[]
        for i,(row,b) in enumerate(original):
            sign=Q(1) if b>=0 else Q(-1)
            normalized={j:budget.tick(sign*c) for j,c in row.items()}
            normalized[n+i]=Q(1)
            table.append(normalized)
            rhs.append(budget.tick(sign*b))
            transforms.append({i:sign})
            basis.append(n+i)
        while True:
            budget.tick()
            value=sum((rhs[i] for i,basic in enumerate(basis) if basic>=n),Q(0))
            reduced={n+i:Q(1) for i in range(m)}
            for i,basic in enumerate(basis):
                if basic<n: continue
                for j,c in table[i].items():
                    new=budget.tick(reduced.get(j,Q(0))-c)
                    if new: reduced[j]=new
                    else: reduced.pop(j,None)
            basic_set=set(basis)
            entering=min((j for j,c in reduced.items() if j not in basic_set and c<0),default=None)
            if entering is None:
                if value==0:
                    solution=[Q(0)]*n
                    for i,basic in enumerate(basis):
                        if basic<n: solution[basic]=rhs[i]
                    result.update(status='FEASIBLE',solution=solution,phase_one_objective=Q(0))
                else:
                    _require(value>0,'Negative artificial objective contradicts nonnegativity')
                    farkas=[Q(0)]*m
                    for i,basic in enumerate(basis):
                        if basic>=n:
                            for j,c in transforms[i].items(): farkas[j]=budget.tick(farkas[j]+c)
                    result.update(status='INFEASIBLE',farkas=farkas,phase_one_objective=value)
                audit=verify_phase_one(original,n,result)
                _require(audit['status']==('VERIFIED_FEASIBLE' if result['status']=='FEASIBLE' else 'VERIFIED_INFEASIBLE'),
                         'Generated phase-I certificate failed independent algebraic audit')
                result['certificate_check']=audit
                budget.tick()
                break
            ratios=[(rhs[i]/row[entering],basis[i],i) for i,row in enumerate(table) if row.get(entering,Q(0))>0]
            _require(bool(ratios),'Unexpected unbounded phase-I objective; no infeasibility inference')
            _require(budget.pivots<budget.limits['pivots'],'Exact phase-I pivot limit reached before another pivot')
            _,_,leaving=min(ratios)
            pivot=table[leaving][entering]
            new_row={j:budget.tick(c/pivot) for j,c in table[leaving].items()}
            new_rhs=budget.tick(rhs[leaving]/pivot)
            new_transform={j:budget.tick(c/pivot) for j,c in transforms[leaving].items()}
            for i in range(m):
                if i==leaving: continue
                factor=table[i].get(entering,Q(0))
                if not factor: continue
                rhs[i]=budget.tick(rhs[i]-factor*new_rhs)
                for j,c in new_row.items():
                    value2=budget.tick(table[i].get(j,Q(0))-factor*c)
                    if value2: table[i][j]=value2
                    else: table[i].pop(j,None)
                for j,c in new_transform.items():
                    value2=budget.tick(transforms[i].get(j,Q(0))-factor*c)
                    if value2: transforms[i][j]=value2
                    else: transforms[i].pop(j,None)
                _require(rhs[i]>=0,'Simplex feasibility invariant failed')
            table[leaving],rhs[leaving],transforms[leaving]=new_row,new_rhs,new_transform
            basis[leaving]=entering
            budget.pivots+=1
    except (MethodFailure,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result.update(status='UNRESOLVED',reason=str(exc))
    result.update(pivots=budget.pivots,operations=budget.operations,
                  elapsed_s=time.monotonic()-budget.started,limits=dict(budget.limits))
    return result


def _dot(row,x):
    return sum((Q(c)*x[i] for i,c in row['coefficients'].items()),Q(0))


def _primal(problem,values):
    x=list(map(Q,values))
    _require(len(x)==len(problem['variables']),'Primal vector dimension mismatch')
    for v,value in zip(problem['variables'],x):
        _require(Q(v['lower'])<=value<=Q(v['upper']),'Exact primal bound violation')
    for row in problem['rows']:
        d=_dot(row,x)-Q(row['rhs'])
        _require((row['sense']=='=' and d==0) or (row['sense']=='<=' and d<=0)
                 or (row['sense']=='>=' and d>=0),'Exact primal prefix/resource violation')
    loads=[Q(0)]*len(problem['a'])
    for v,value in zip(problem['variables'],x): loads[v['period']]+=value
    objective=Q(problem['ops'])+sum((Q(a)*e+Q(b)*e*e/2 for a,b,e in zip(problem['a'],problem['b'],loads)),Q(0))
    gradient=[Q(problem['a'][v['period']])+Q(problem['b'][v['period']])*loads[v['period']]
              for v in problem['variables']]
    return x,loads,objective,gradient


def recover_primal(problem,proposal,affine,physical_verify,limits=None):
    """Admit a new exact primal before seeking any optimality certificate.

    affine is the frozen exact_fixed_topology module (_Work/_basis/_solve).
    Same one-face 1e-7 policy, no alternate face, native call or Pi seed.
    """
    work=affine._Work(limits)
    result=dict(status='PRIMAL_UNRESOLVED',face_attempts=1,topology_infeasibility_claim=False,
                fixed_topology_optimum_claim=False,global_support_claim=False)
    stage='PROPOSED_FACE'
    try:
        variables,rows=problem['variables'],problem['rows']
        raw=list(map(Q,proposal['values']))
        _require(len(raw)==len(variables),'Saved charge proposal dimension mismatch')
        free=[i for i,x in enumerate(raw) if abs(x)>Q(1,10**7)]
        local={i:j for j,i in enumerate(free)}
        active=[r for r in rows if r['sense']=='=' or abs(_dot(r,raw)-Q(r['rhs']))<=Q(1,10**7)]
        stage='RATIONAL_AFFINE_PRIMAL'
        basis=affine._basis([({local[i]:Q(c) for i,c in r['coefficients'].items() if i in local},Q(r['rhs']))
                             for r in active],len(free),work)
        basis_rows=list(basis.values())
        size=len(free)+len(basis_rows)
        work.dimension(size)
        system=[]
        for j,i in enumerate(free):
            period=variables[i]['period']
            row={k:Q(problem['b'][period]) for k,other in enumerate(free)
                 if variables[other]['period']==period and problem['b'][period]}
            for k,(coefficients,rhs) in enumerate(basis_rows):
                if j in coefficients: row[len(free)+k]=-coefficients[j]
            system.append((row,-Q(problem['a'][period])))
        system += [(dict(row),rhs) for row,rhs in basis_rows]
        solved,rank=affine._solve(system,size,[raw[i] for i in free]+[Q(0)]*len(basis_rows),work)
        values=[Q(0)]*len(variables)
        for i,j in local.items(): values[i]=solved[j]
        stage='EXACT_FULL_PRIMAL'
        values,loads,objective,_=_primal(problem,values)
        candidate=dict(selected_movement_ids=list(problem['selected_movement_ids']),charge_by_interval=[
            dict(movement=v['movement'],interval=v['interval'],energy=x) for v,x in zip(variables,values)])
        result.update(values=values,candidate=candidate,loads_exact=loads,objective_exact=objective,
                      face=dict(zero_coordinates=[i for i in range(len(values)) if i not in local],
                                proposed_active_rows=[r['name'] for r in active],system=rank))
        stage='INDEPENDENT_PHYSICAL_ADMISSION'
        work.check()
        audit=physical_verify(problem['case'],candidate)
        result['replay']=audit
        work.check()
        _require(audit.get('strict_pass') is True and Q(audit['objective_exact'])==objective,
                 'New exact primal did not pass original physical admission')
        result.update(status='ADMITTED_PRIMAL',own_prices=[Q(a)+Q(b)*e for a,b,e in zip(problem['a'],problem['b'],loads)],
                      physical_upper_certified=True,optimality_certificate_still_required=True)
    except (MethodFailure,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result.update(stage=stage,reason=str(exc))
    result.update(operations=work.operations,elapsed_s=time.monotonic()-work.started,limits=dict(work.limit))
    return result


def check_certificate(problem,values,certificate):
    """Full exact fixed-topology box-dual audit, independent of phase-I pivots."""
    try:
        x,loads,objective,gradient=_primal(problem,values)
        multipliers=certificate['multipliers']
        _require(set(multipliers)=={r['name'] for r in problem['rows']},'Multiplier row-set mismatch')
        residual=list(gradient)
        rhs_sum=Q(0)
        for row in problem['rows']:
            pi=Q(multipliers[row['name']])
            _require(row['sense']=='=' or (row['sense']=='>=' and pi>=0) or
                     (row['sense']=='<=' and pi<=0),'Wrong multiplier sign')
            _require(pi*(_dot(row,x)-Q(row['rhs']))==0,'Row complementarity failure')
            rhs_sum+=pi*Q(row['rhs'])
            for i,c in row['coefficients'].items(): residual[i]-=pi*Q(c)
        box=Q(0)
        for v,value,r in zip(problem['variables'],x,residual):
            term=min(r*Q(v['lower']),r*Q(v['upper']))
            _require(r*value==term,'Box residual fails on a zero, upper-bound or interior coordinate')
            box+=term
        constant=Q(problem['ops'])-sum((Q(b)*e*e/2 for b,e in zip(problem['b'],loads)),Q(0))
        lower=constant+rhs_sum+box
        _require(lower==objective,'Exact dual/primal inequality does not close')
        if 'lower_exact' in certificate: _require(Q(certificate['lower_exact'])==lower,'Altered claimed lower bound')
        if 'objective_exact' in certificate: _require(Q(certificate['objective_exact'])==objective,'Altered claimed objective')
        if 'residuals' in certificate: _require(list(map(Q,certificate['residuals']))==residual,'Altered residual vector')
        return dict(status='VERIFIED_FIXED_TOPOLOGY_OPTIMUM',lower_exact=lower,objective_exact=objective,
                    residuals=residual,tangent_constant=constant,dual_rhs=rhs_sum,box_compensation=box)
    except (MethodFailure,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        return dict(status='REJECTED',reason=str(exc))


def certify_dual(problem,values,limits=None):
    """Solve all signed KKT/box conditions by one exact phase-I LP.

    Same primal remains admitted even if this method returns infeasible or hits
    a limit. Infeasibility concerns the normal cone at this point, never routing
    feasibility. Duplicate stationarity rows are coalesced; all original q
    residuals and all original row multipliers are audited afterwards.
    """
    result=dict(status='DUAL_UNRESOLVED',global_fleet_optimum_claim=False,global_support_claim=False)
    try:
        x,loads,objective,gradient=_primal(problem,values)
        columns=[]
        for row in problem['rows']:
            if not row['coefficients'] or _dot(row,x)!=Q(row['rhs']): continue
            signs=(Q(1),Q(-1)) if row['sense']=='=' else (Q(1),) if row['sense']=='>=' else (Q(-1),)
            for sign in signs: columns.append(dict(row=row['name'],sign=sign,coefficients=row['coefficients']))
        conditions={}
        for i,v in enumerate(problem['variables']):
            lo,hi=Q(v['lower']),Q(v['upper'])
            if lo==hi: continue
            coefficients=tuple((j,col['sign']*Q(col['coefficients'][i])) for j,col in enumerate(columns)
                               if col['coefficients'].get(i,Q(0)))
            sense='<=' if x[i]==lo else '>=' if x[i]==hi else '='
            key=(coefficients,sense,gradient[i])
            conditions.setdefault(key,[]).append(i)
        equations=[]
        metadata=[]
        count=len(columns)
        for (coefficients,sense,rhs),coordinates in conditions.items():
            row=dict(coefficients)
            slack=None
            if sense!='=':
                slack=count
                row[count]=Q(1) if sense=='<=' else Q(-1)
                count+=1
            equations.append((row,rhs))
            metadata.append(dict(coordinates=coordinates,sense=sense,slack=slack))
        solved=phase_one(equations,count,limits)
        result.update(phase_one=solved,cone_columns=[dict(row=c['row'],sign=c['sign']) for c in columns],
                      stationarity_groups=metadata,normal_cone_equations=equations,normal_cone_variables=count,
                      objective_exact=objective)
        if solved['status']=='INFEASIBLE':
            result.update(status='DUAL_INFEASIBLE_FOR_THIS_PRIMAL',
                          reason='Exact checked normal-cone infeasibility; physical primal remains separately admitted')
        elif solved['status']=='FEASIBLE':
            z=list(map(Q,solved['solution']))
            multipliers={row['name']:Q(0) for row in problem['rows']}
            for column,value in zip(columns,z): multipliers[column['row']]+=column['sign']*value
            certificate=dict(multipliers=multipliers,objective_exact=objective)
            audit=check_certificate(problem,x,certificate)
            _require(audit['status']=='VERIFIED_FIXED_TOPOLOGY_OPTIMUM','Phase-I multiplier failed full original certificate audit')
            result.update(status='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM',multipliers=multipliers,
                          lower_exact=audit['lower_exact'],residuals=audit['residuals'],certificate_check=audit)
        else:
            result['reason']=solved.get('reason','No completed exact phase-I result')
    except (MethodFailure,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result.update(status='DUAL_UNRESOLVED',reason=str(exc))
    return result
