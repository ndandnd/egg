"""Exact node bounds and complete binary-tree coverage, with explicit scope.

No backend or model source is imported. prepare receives the cached independent
exact_dual._reconstruct callback. Only original movement binaries may branch.
Quadratic tree bounds certify physical minima, never the unrestricted CH.
This module supplies no search/controller or launch authority.
"""
from fractions import Fraction as Q
import time


class Rejected(ValueError):
    pass


class CheckLimit(Rejected):
    pass


def _require(condition,message):
    if not condition:
        raise Rejected(message)


class _Budget:
    def __init__(self,limits=None):
        self.limits=dict(nodes=10000,depth=1000,operations=10000000,fraction_bits=32768,seconds=60)
        self.limits.update(limits or {})
        self.started=time.monotonic()
        self.operations=0

    def check(self,value=Q(0)):
        self.operations+=1
        if (self.operations>self.limits['operations'] or time.monotonic()-self.started>self.limits['seconds']
            or value.numerator.bit_length()>self.limits['fraction_bits']
            or value.denominator.bit_length()>self.limits['fraction_bits']):
            raise CheckLimit('Checker resource checkpoint exceeded; no completed coverage certificate')
        return value


def prepare(case_dict,semantic_reconstruct,mode='quadratic',prices=None,fleet_count=None,case_token=None):
    """Build trusted semantic context once; do not admit a serialized context.

    mode quadratic uses the original binary-stored .2,1/900 market. Linear mode
    requires explicit prices. fleet_count may be None (all counts) or exactly2;
    the latter is only a conditional physical/pricing subproblem.
    """
    _require(mode in ('quadratic','linear'),'Unknown objective mode')
    _require(fleet_count is None or (type(fleet_count) is int and fleet_count==2),
             'Only an explicit exact-two-bus restriction is supported')
    variables,rows,intervals,operations,loads,fleet_proof=semantic_reconstruct(case_dict)
    variables={name:(Q(lo),Q(hi)) for name,(lo,hi) in variables.items()}
    _require(all(lo<=hi for lo,hi in variables.values()),'Invalid semantic finite box')
    base={name:(sense,Q(rhs),{v:Q(c) for v,c in coefficients.items() if c})
          for name,(sense,rhs,coefficients) in rows.items()}
    movement_variables={m['id']:'y'+str(j) for j,m in enumerate(case_dict['movements'])}
    _require(len(movement_variables)==len(case_dict['movements']),'Duplicate original movement ID')
    _require(all(v in variables and variables[v]==(Q(0),Q(1)) for v in movement_variables.values()),
             'Original binary movement semantics missing')
    branch_names={mid:'__branch_'+str(j) for j,mid in enumerate(movement_variables)}
    _require(not set(branch_names.values())&set(base) and '__fleet_count__' not in base,
             'Reserved proof-row namespace collision')
    starts={movement_variables[m['id']]:Q(1) for m in case_dict['movements'] if m['kind']=='pullout'}
    if fleet_count is not None:
        base['__fleet_count__']=('=',Q(2),starts)
    if mode=='linear':
        _require(isinstance(prices,(list,tuple)) and len(prices)==len(loads),'Explicit price vector required')
        prices=tuple(map(Q,prices))
    else:
        _require(prices is None,'Quadratic mode has its fixed original market')
    return dict(case=case_dict,case_token=case_token,variables=variables,rows=base,
                operations={v:Q(c) for v,c in operations.items()},loads=tuple(loads),
                movement_variables=movement_variables,branch_names=branch_names,
                minimum_fleet_proof=fleet_proof,mode=mode,prices=prices,fleet_count=fleet_count,
                scope=('D_two' if fleet_count==2 else 'D_physical') if mode=='quadratic'
                       else ('V_two(p)' if fleet_count==2 else 'V(p)'),
                unrestricted_hull_lower_claim=False)


def _decisions(context,decisions):
    result={}
    for mid,value in decisions:
        _require(mid in context['movement_variables'] and mid not in result,'Unknown or repeated branch movement')
        _require(type(value) is int and value in (0,1),'Branch value must be integer0 or1')
        result[mid]=value
    return result


def _node(context,decisions,certificate,infeasible,budget):
    decisions=_decisions(context,decisions)
    _require(isinstance(certificate,dict) and isinstance(certificate.get('multipliers'),dict),
             'An explicit sparse multiplier dictionary is required; no missing-proposal zero fallback')
    branch_rows={context['branch_names'][mid]:('=',Q(value),{context['movement_variables'][mid]:Q(1)})
                 for mid,value in decisions.items()}
    residual={name:Q(0) for name in context['variables']}
    constant=Q(0)
    tangent=None
    if not infeasible:
        residual.update(context['operations'])
        if context['mode']=='quadratic':
            proposed=certificate.get('tangent_loads')
            _require(isinstance(proposed,(list,tuple)) and len(proposed)==len(context['loads']),
                     'Every quadratic node bound needs an explicit tangent vector')
            tangent=tuple(map(Q,proposed))
            a,b=Q(float(.2)),Q(float(1/900))
            constant=-sum((b*z*z/2 for z in tangent),Q(0))
            for name,z in zip(context['loads'],tangent): residual[name]+=a+b*z
        else:
            for name,p in zip(context['loads'],context['prices']): residual[name]+=p
    rhs_sum=Q(0)
    corrected={}
    projected=0
    for name,raw in certificate['multipliers'].items():
        _require(name in context['rows'] or name in branch_rows,'Multiplier names an unknown/unavailable proof row')
        sense,rhs,coefficients=context['rows'][name] if name in context['rows'] else branch_rows[name]
        value=budget.check(Q(raw))
        pi=max(Q(0),value) if sense=='>=' else min(Q(0),value) if sense=='<=' else value
        _require(sense in ('=','>=','<='),'Invalid semantic row sense')
        projected+=int(pi!=value)
        corrected[name]=pi
        rhs_sum=budget.check(rhs_sum+pi*rhs)
        for variable,coefficient in coefficients.items():
            residual[variable]=budget.check(residual[variable]-pi*coefficient)
    compensation=Q(0)
    nonzero=0
    for name,(lo,hi) in context['variables'].items():
        value=residual[name]
        nonzero+=int(value!=0)
        compensation=budget.check(compensation+min(value*lo,value*hi))
    lower=budget.check(constant+rhs_sum+compensation)
    if infeasible:
        _require(lower>0,'Farkas/box contradiction must be strictly positive')
        if 'claimed_contradiction' in certificate:
            _require(Q(certificate['claimed_contradiction'])==lower,'Altered Farkas contradiction')
    elif 'claimed_lower' in certificate:
        _require(Q(certificate['claimed_lower'])==lower,'Claimed node lower differs from exact algebra')
    return dict(status='CERTIFIED_INFEASIBLE' if infeasible else 'CERTIFIED_BOUND',
                lower_bound=None if infeasible else lower,contradiction=lower if infeasible else None,
                scope=context['scope'],tangent_loads=tangent,tangent_constant=constant,
                dual_rhs=rhs_sum,box_compensation=compensation,
                sign_projected_rows=projected,multipliers=corrected,nonzero_residuals=nonzero,
                decisions=tuple(decisions.items()),native_status_used=False,
                unrestricted_CH_claim=False)


def verify_node(context,decisions,certificate,infeasible=False,limits=None):
    """Independently verify one declared node; it is not full-tree coverage."""
    budget=_Budget(limits)
    try:
        result=_node(context,decisions,certificate,bool(infeasible),budget)
    except CheckLimit as exc:
        result=dict(status='UNRESOLVED',reason=str(exc),scope=context.get('scope'))
    except (Rejected,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result=dict(status='REJECTED',reason=str(exc),scope=context.get('scope'))
    result.update(operations=budget.operations,elapsed_s=time.monotonic()-budget.started)
    return result


def _exclusion(context,record,admit_transfer):
    """Check a narrowly typed source-bound three-plus affine service floor.

    admit_transfer checks already cached fixed-path/revision authority, never
    follows metadata paths. It must return True. The mathematical floor is also
    reconstructed here, preventing a qualified nonlinear floor from being
    silently reused for a linear-price objective.
    """
    _require(context['case_token'] is not None and record.get('case_token')==context['case_token'],
             'Exclusion does not bind the same admitted case')
    _require(admit_transfer is not None and admit_transfer(record) is True,
             'Three-plus floor lacks external source-bound transfer admission')
    _require(record.get('minimum_fleet')==3,'Exclusion must cover every fleet count>=3')
    case=context['case']
    # This is the exact admitted descriptor schema: waiting/auxiliary energy
    # must be represented in its movement legs, with no hidden cost fields.
    _require(set(case)==set(('name trips movements resources market_edges_min depot max_vehicles '
        'battery_kwh reserve_kwh terminal_open_min recharge_deadline_min vehicle_cost '
        'deadhead_cost_per_min efficiency graph_scope').split()),'Unadmitted service-floor case schema')
    _require(case['graph_scope']=='declared-movement-modes-only','Unadmitted service-floor graph semantics')
    service=sum((Q(t['energy_kwh']) for t in case['trips']),Q(0))
    fee,eta=Q(case['vehicle_cost']),Q(case['efficiency'])
    _require(fee>=0 and 0<eta<=1 and Q(case['deadhead_cost_per_min'])>=0,
             'Service floor requires nonnegative fees/costs and positive efficiency')
    _require(all(Q(t['energy_kwh'])>=0 for t in case['trips']),
             'Service floor requires nonnegative service consumption')
    _require(all(Q(leg['energy_kwh'])>=0 and Q(leg['arrive_min'])>=Q(leg['depart_min'])
                 for movement in case['movements'] for leg in movement['legs']),
             'Service floor requires nonnegative movement/waiting energy and duration')
    _require(all(Q(c)>=0 for c in context['operations'].values()),
             'Service floor cannot omit negative operating-cost coefficients')
    if context['mode']=='quadratic':
        _require(record.get('proof_kind')=='quadratic_affine_service_floor'
                 and record.get('scope')=='physical_ge_3','Wrong physical exclusion type')
        computed=3*fee+Q(float(.2))*service/eta
    else:
        _require(record.get('proof_kind')=='linear_min_price_service_floor'
                 and record.get('scope')=='response_ge_3','A nonlinear floor cannot exclude linear-price fleets')
        _require(isinstance(record.get('prices'),(list,tuple)) and tuple(map(Q,record['prices']))==context['prices'],
                 'Linear-price exclusion must bind this exact price vector')
        _require(min(context['prices'])>=0,'Service-energy linear floor requires nonnegative prices')
        computed=3*fee+min(context['prices'])*service/eta
    lower=Q(record['lower_bound'])
    _require(lower<=computed,'Transferred floor exceeds its independently justified affine service floor')
    return dict(status='ADMITTED_GE_3_FLOOR',lower_bound=lower,computed_affine_floor=computed,
                scope=record['scope'],case_token=context['case_token'])


def verify_tree(context,tree,exclusion=None,admit_transfer=None,target=None,limits=None):
    """Check a flat full binary proof tree without a search/controller.

    tree={'root':id,'nodes':{id:node}}. Branch node fields: kind='branch',
    movement=originalID, children={'0':id0,'1':id1}. Leaves have kind='bound'
    or 'infeasible' and certificate fields accepted by verify_node; explicit
    kind='open' leaves make coverage incomplete. No omitted, shared, cyclic or
    unreachable nodes are accepted. A supplied target is NOT certified here.
    """
    budget=_Budget(limits)
    result=dict(status='REJECTED',scope=context['scope'],complete=False,
                unrestricted_CH_claim=False,target_is_certified_here=False)
    seen,leaves,open_nodes=set(),[],[]
    try:
        nodes=tree['nodes']
        _require(isinstance(nodes,dict) and tree['root'] in nodes,'Missing proof root/nodes')
        if len(nodes)>budget.limits['nodes']:
            raise CheckLimit('Proof node limit exceeded')
        stack=[(tree['root'],(),0)]
        while stack:
            identifier,decisions,depth=stack.pop()
            budget.check()
            _require(identifier in nodes and identifier not in seen,'Missing, shared or cyclic tree node')
            if depth>budget.limits['depth']:
                raise CheckLimit('Proof depth limit exceeded')
            seen.add(identifier)
            node=nodes[identifier]
            kind=node['kind']
            if kind=='branch':
                mid=node['movement']
                current=_decisions(context,decisions)
                _require(mid in context['movement_variables'] and mid not in current,'Branch must use an unfixed original movement')
                children=node['children']
                _require(isinstance(children,dict) and set(children)=={'0','1'}
                         and children['0']!=children['1'],'Both distinct binary children are required')
                stack.append((children['1'],decisions+((mid,1),),depth+1))
                stack.append((children['0'],decisions+((mid,0),),depth+1))
            elif kind in ('bound','infeasible'):
                checked=_node(context,decisions,node['certificate'],kind=='infeasible',budget)
                leaves.append(dict(id=identifier,certificate=checked))
            elif kind=='open':
                open_nodes.append(dict(id=identifier,decisions=decisions,reason=node.get('reason','Explicit open leaf')))
            else:
                raise Rejected('Unknown proof-node kind')
        _require(seen==set(nodes),'Unreachable nodes are not part of a complete declared tree')
        result.update(checked_nodes=len(seen),leaves=leaves,open_nodes=open_nodes)
        if open_nodes:
            result.update(status='OPEN_TREE',reason='At least one explicit leaf lacks a certificate',complete=False)
        else:
            _require(bool(leaves),'Tree has no certified leaves')
            lower_values=[leaf['certificate']['lower_bound'] for leaf in leaves
                          if leaf['certificate']['status']=='CERTIFIED_BOUND']
            conditional=min(lower_values) if lower_values else None
            result.update(status='COMPLETE',complete=True,all_leaves_infeasible=not lower_values,
                          complete_leaf_minimum='+inf' if conditional is None else conditional)
            global_lower=None
            if context['fleet_count'] is None:
                global_lower='+inf' if conditional is None else conditional
            elif exclusion is not None:
                _require(context['minimum_fleet_proof']['minimum_fleet']>=2,
                         'Exact-two plus three-plus leaves uncovered zero/one-bus fleets')
                admitted=_exclusion(context,exclusion,admit_transfer)
                result['higher_fleet_exclusion']=admitted
                global_lower=admitted['lower_bound'] if conditional is None else min(conditional,admitted['lower_bound'])
            result['global_lower_bound']=global_lower
            result['global_scope']='D_physical' if context['mode']=='quadratic' else 'V(p)'
            if context['fleet_count']==2 and exclusion is None:
                result['global_lower_unavailable_reason']='Conditional two-bus proof needs a separately valid three-plus exclusion and proven one-bus obstruction'
            if target is not None:
                result['supplied_target']=Q(target)
                result['global_lower_exceeds_target']=(global_lower=='+inf' or
                    (global_lower is not None and global_lower>Q(target)))
                result['strict_excess']=(global_lower-Q(target)) if isinstance(global_lower,Q) else None
        budget.check()
    except CheckLimit as exc:
        result.update(status='UNRESOLVED',complete=False,reason=str(exc),checked_nodes=len(seen),
                      leaves=leaves,open_nodes=open_nodes)
        result.pop('global_lower_bound',None)
    except (Rejected,KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError) as exc:
        result.update(status='REJECTED',complete=False,reason=str(exc),checked_nodes=len(seen),
                      leaves=leaves,open_nodes=open_nodes)
        result.pop('global_lower_bound',None)
    if result['status']!='COMPLETE' or not result['complete']:
        for name in ('global_lower_bound','global_lower_exceeds_target','strict_excess',
                     'all_leaves_infeasible','complete_leaf_minimum','higher_fleet_exclusion',
                     'global_scope','global_lower_unavailable_reason'):
            result.pop(name,None)
    result.update(operations=budget.operations,elapsed_s=time.monotonic()-budget.started,
                  limits=dict(budget.limits),native_status_used=False,
                  limitation='Completeness proves this physical/pricing bound only. Hull upper witnesses and external source-transfer authority require separate admission.')
    return result
