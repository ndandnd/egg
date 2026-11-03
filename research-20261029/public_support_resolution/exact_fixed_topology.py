"""One-face rational fixed-topology QP recovery; never a global fleet proof.

Callbacks supply the cached semantic reconstruction and independent physical
replay. No backend, model module, data, or external process is imported here.
The fixed face is a proposal only; every original constraint and every variable's
box residual is checked exactly before a certificate is returned.
"""
from fractions import Fraction as Q
import time


class RecoveryFailure(ValueError):
    pass


class _Work:
    def __init__(self,limits):
        self.limit=dict(dimension=250,operations=2000000,fraction_bits=16384,seconds=30)
        self.limit.update(limits or {})
        self.started=time.monotonic()
        self.operations=0

    def check(self,value=Q(0)):
        self.operations+=1
        if (self.operations>self.limit['operations'] or time.monotonic()-self.started>self.limit['seconds']
            or value.numerator.bit_length()>self.limit['fraction_bits']
            or value.denominator.bit_length()>self.limit['fraction_bits']):
            raise RecoveryFailure('Exact work/time/fraction-size limit reached; no alternate face attempted')
        return value

    def dimension(self,n):
        if n>self.limit['dimension']:
            raise RecoveryFailure('Exact system dimension limit reached; no dense full-graph solve attempted')


def _require(condition,message):
    if not condition:
        raise RecoveryFailure(message)


def _basis(equations,n,work):
    """Sparse exact echelon basis of affine equations, retaining inconsistency."""
    work.dimension(n)
    basis={}
    for coefficients,rhs in equations:
        row={i:Q(v) for i,v in coefficients.items() if v}
        rhs=Q(rhs)
        for pivot,(old,old_rhs) in sorted(basis.items()):
            if pivot in row:
                factor=row[pivot]
                rhs=work.check(rhs-factor*old_rhs)
                for i,value in old.items():
                    new=work.check(row.get(i,Q(0))-factor*value)
                    if new: row[i]=new
                    else: row.pop(i,None)
        if not row:
            _require(rhs==0,'Proposed face has inconsistent exact equations')
            continue
        pivot=min(row)
        factor=row[pivot]
        row={i:work.check(v/factor) for i,v in row.items()}
        basis[pivot]=(row,work.check(rhs/factor))
    return basis


def _solve(equations,n,seeds,work):
    basis=_basis(equations,n,work)
    values=[Q(v) for v in seeds]
    _require(len(values)==n,'Incorrect affine free-coordinate seed dimension')
    for pivot,(row,rhs) in sorted(basis.items(),reverse=True):
        values[pivot]=work.check(rhs-sum((v*values[i] for i,v in row.items() if i!=pivot),Q(0)))
    return values,dict(rank=len(basis),free_coordinates=[i for i in range(n) if i not in basis])


def build_problem(case_dict,selected_movement_ids,semantic_reconstruct):
    """Charge-only exact QP from original paths and the checked semantic partition.

    semantic_reconstruct is exact_dual._reconstruct, supplied from cached source;
    it validates the original descriptor and returns its independently assembled
    semantic intervals. Its full-graph variables/rows are not used in linear
    algebra. Returned problem is intended for a separately frozen native QP
    adapter and this recovery helper, never an untrusted caller-supplied matrix.
    """
    _,_,intervals,_,_,_=semantic_reconstruct(case_dict)
    case=case_dict
    moves={m['id']:m for m in case['movements']}
    trips={t['id']:t for t in case['trips']}
    selected=list(selected_movement_ids)
    _require(len(selected)==len(set(selected)) and all(mid in moves for mid in selected),'Invalid selected IDs')
    incoming,outgoing,starts={},{},[]
    for mid in selected:
        m=moves[mid]
        if m['before'] is None: starts.append(mid)
        else:
            _require(m['before'] not in outgoing,'Repeated outgoing service')
            outgoing[m['before']]=mid
        if m['after'] is not None:
            _require(m['after'] not in incoming,'Repeated incoming service')
            incoming[m['after']]=mid
    _require(set(incoming)==set(trips)==set(outgoing),'Incomplete path cover')
    _require(1<=len(starts)<=case['max_vehicles'],'Invalid fleet count')
    routes,seen,covered=[],set(),set()
    for start in sorted(starts):
        route=[]
        mid=start
        while True:
            _require(mid not in seen,'Selected cycle/repetition')
            seen.add(mid)
            route.append(mid)
            after=moves[mid]['after']
            if after is None: break
            _require(after not in covered,'Service repetition')
            covered.add(after)
            mid=outgoing[after]
        routes.append(route)
    _require(seen==set(selected) and covered==set(trips),'Disconnected selected component')
    variables=[]
    by_movement={mid:[] for mid in selected}
    for m in case['movements']:
        if m['id'] not in seen: continue
        for interval in intervals:
            if m['id'] in interval['visits'] and interval['capacity']>0:
                i=len(variables)
                variables.append(dict(index=i,name='charge_'+str(i),movement=m['id'],
                    interval=interval['index'],period=interval['period'],lower=Q(0),upper=Q(interval['capacity'])))
                by_movement[m['id']].append(i)
    rows=[]
    def row(name,coefficients,sense,rhs):
        rows.append(dict(name=name,coefficients={i:Q(v) for i,v in coefficients.items() if v},sense=sense,rhs=Q(rhs)))
    for interval in intervals:
        row('shared_'+str(interval['index']),{v['index']:1 for v in variables if v['interval']==interval['index']},
            '<=',interval['capacity'])
    B,reserve,eta=(Q(case[k]) for k in ('battery_kwh','reserve_kwh','efficiency'))
    for bus,route in enumerate(routes):
        spent,charged=Q(0),[]
        event=0
        def inventory(description):
            nonlocal event
            terms={i:eta for i in charged}
            row('soc_lower_'+str(bus)+'_'+str(event)+'_'+description,terms,'>=',reserve-B+spent)
            row('soc_upper_'+str(bus)+'_'+str(event)+'_'+description,terms,'<=',spent)
            event+=1
        for mid in route:
            m=moves[mid]
            for leg_index,leg in enumerate(m['legs']):
                if m['kind']=='depot' and leg_index==m['depot_split']:
                    charged+=by_movement[mid]
                    inventory('after_depot_charge')
                spent+=Q(leg['energy_kwh'])
                inventory('after_leg')
            if m['kind']=='pullin':
                charged+=by_movement[mid]
                inventory('after_terminal_charge')
            if m['after'] is not None:
                spent+=Q(trips[m['after']]['energy_kwh'])
                inventory('after_service')
        row('full_refill_'+str(bus),{i:eta for i in charged},'=',spent)
    ops=Q(case['vehicle_cost'])*len(routes)+Q(case['deadhead_cost_per_min'])*sum(
        (Q(l['arrive_min'])-Q(l['depart_min']) for mid in selected for l in moves[mid]['legs']),Q(0))
    periods=len(case['market_edges_min'])-1
    return dict(case=case,selected_movement_ids=selected,routes=routes,variables=variables,rows=rows,
                intervals=intervals,ops=ops,a=[Q(float(.2))]*periods,b=[Q(float(1/900))]*periods,
                scope='exact convex charging QP on this fixed complete topology only')


def recover(problem,proposal,physical_verify,limits=None):
    """One fixed face, exact affine/KKT recovery, and full box-dual equality.

    proposal={'values':[one native q value per problem variable],
              'dual_by_row':{row name:native Pi}}. One absolute 1e-7 policy
    selects near-zero q and near-tight rows. It is never varied after failure.
    Every q, including proposed zero coordinates, participates in final residual
    checks. Failure is incomplete recovery, not fixed-topology infeasibility.
    """
    work=_Work(limits)
    result=dict(status='RECOVERY_FAILED',scope=problem['scope'],face_attempts=1,
                topology_infeasibility_claim=False,global_fleet_optimum_claim=False,
                global_price_support_claim=False,tolerance_is_only_face_selection=True)
    stage='PROPOSAL'
    try:
        variables,rows=problem['variables'],problem['rows']
        n=len(variables)
        raw=list(map(Q,proposal['values']))
        _require(len(raw)==n,'Proposal charge dimension mismatch')
        pi_seed=proposal['dual_by_row']
        _require(isinstance(pi_seed,dict) and all(row['name'] in pi_seed for row in rows),
                 'Explicit native row-multiplier proposals required; no zero fallback')
        tolerance=Q(1,10**7)
        zero={i for i,x in enumerate(raw) if abs(x)<=tolerance}
        free=[i for i in range(n) if i not in zero]
        work.dimension(len(free))
        local={i:j for j,i in enumerate(free)}
        def dot(row,x):
            value=Q(0)
            for i,c in row['coefficients'].items():
                value=work.check(value+c*x[i])
            return value
        active=[row for row in rows if row['sense']=='=' or abs(dot(row,raw)-row['rhs'])<=tolerance]
        proposed_active_names=[row['name'] for row in active]
        stage='FACE_BASIS'
        equations=[({local[i]:c for i,c in row['coefficients'].items() if i in local},row['rhs']) for row in active]
        basis=_basis(equations,len(free),work)
        basis_rows=list(basis.values())
        rank=len(basis_rows)
        size=len(free)+rank
        work.dimension(size)
        stage='PRIMAL_KKT'
        # H_ij=b_t when allocations share market period t, otherwise zero.
        # No full-graph dense matrix is built; dimensions apply after zero-face
        # substitution and exact removal of dependent face equalities.
        system=[]
        for j,i in enumerate(free):
            period=variables[i]['period']
            coefficients={k:problem['b'][period] for k,other in enumerate(free)
                          if variables[other]['period']==period and problem['b'][period]}
            for k,(constraint,rhs) in enumerate(basis_rows):
                if j in constraint: coefficients[len(free)+k]=-constraint[j]
            system.append((coefficients,-problem['a'][period]))
        for constraint,rhs in basis_rows:
            system.append((dict(constraint),rhs))
        solution,primal_rank=_solve(system,size,[raw[i] for i in free]+[Q(0)]*rank,work)
        x=[Q(0)]*n
        for i,j in local.items(): x[i]=solution[j]
        stage='FULL_PRIMAL_CHECK'
        for variable,value in zip(variables,x):
            _require(variable['lower']<=value<=variable['upper'],'Recovered point violates an original finite bound')
        for row in rows:
            difference=dot(row,x)-row['rhs']
            _require((row['sense']=='=' and difference==0) or (row['sense']=='<=' and difference<=0)
                     or (row['sense']=='>=' and difference>=0),'Recovered point violates an original prefix/resource row')
        loads=[Q(0)]*len(problem['a'])
        for variable,value in zip(variables,x): loads[variable['period']]+=value
        gradient=[problem['a'][v['period']]+problem['b'][v['period']]*loads[v['period']] for v in variables]
        # Retain ALL active original rows here. A primal row basis is not a
        # sign-valid dual basis; redundant inequalities can be essential.
        active=[row for row in rows if row['coefficients'] and
                (row['sense']=='=' or dot(row,x)==row['rhs'])]
        interior=[i for i,v in enumerate(variables) if v['lower']<x[i]<v['upper']]
        work.dimension(len(active))
        dual_equations=[({j:row['coefficients'].get(i,Q(0)) for j,row in enumerate(active)
                          if row['coefficients'].get(i,Q(0))},gradient[i]) for i in interior]
        stage='DUAL_RECOVERY'
        dual,dual_rank=_solve(dual_equations,len(active),[Q(pi_seed[row['name']]) for row in active],work)
        multipliers={row['name']:Q(0) for row in rows}
        for row,value in zip(active,dual): multipliers[row['name']]=value
        stage='ALL_COORDINATE_BOX_CERTIFICATE'
        residual=list(gradient)
        rhs_sum=Q(0)
        for row in rows:
            value=multipliers[row['name']]
            _require(row['sense']=='=' or (row['sense']=='>=' and value>=0)
                     or (row['sense']=='<=' and value<=0),'Recovered multiplier has wrong sign')
            _require(value*(dot(row,x)-row['rhs'])==0,'Exact row complementarity failed')
            rhs_sum=work.check(rhs_sum+value*row['rhs'])
            for i,c in row['coefficients'].items(): residual[i]=work.check(residual[i]-c*value)
        compensation=Q(0)
        for variable,value,r in zip(variables,x,residual):
            minimum=min(r*variable['lower'],r*variable['upper'])
            _require(r*value==minimum,'A proposed zero/bound/free q fails exact box-residual complementarity')
            compensation=work.check(compensation+minimum)
        constant=problem['ops']-sum((b*load*load/2 for b,load in zip(problem['b'],loads)),Q(0))
        lower=constant+rhs_sum+compensation
        upper=problem['ops']+sum((a*load+b*load*load/2 for a,b,load in zip(problem['a'],problem['b'],loads)),Q(0))
        _require(lower==upper,'Exact tangent dual lower and primal objective do not coincide')
        candidate=dict(selected_movement_ids=list(problem['selected_movement_ids']),charge_by_interval=[
            dict(movement=v['movement'],interval=v['interval'],energy=value) for v,value in zip(variables,x)])
        result['candidate']=candidate
        stage='INDEPENDENT_ORIGINAL_PHYSICAL_REPLAY'
        work.check()
        audit=physical_verify(problem['case'],candidate)
        result['replay']=audit
        work.check()
        _require(audit.get('strict_pass') is True and Q(audit['objective_exact'])==upper,
                 'Original physical replay failed or disagrees with exact QP objective')
        result.update(status='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM',candidate=candidate,replay=audit,
            objective_exact=upper,lower_exact=lower,loads_exact=loads,
            own_prices=[a+b*load for a,b,load in zip(problem['a'],problem['b'],loads)],
            multipliers=multipliers,residuals=residual,tangent_constant=constant,
            dual_rhs=rhs_sum,box_compensation=compensation,
            face=dict(zero_coordinates=sorted(zero),free_coordinates=free,
                      proposed_active_rows=proposed_active_names,
                      final_tight_dual_rows=[row['name'] for row in active],
                      primal_system=primal_rank,dual_system=dual_rank),
            limitation='Global support still requires a full-opportunity-set own-price response equality certificate')
    except (RecoveryFailure,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result.update(stage=stage,reason=str(exc))
    result.update(exact_operations=work.operations,elapsed_s=time.monotonic()-work.started,
                  operation_counter_semantics='Calls to the monitored work checkpoint, not every rational primitive or temporary',
                  limits=dict(work.limit),face_tolerance='1/10000000')
    return result
