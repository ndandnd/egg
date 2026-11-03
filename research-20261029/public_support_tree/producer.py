"""Bounded best-bound quadratic physical search: proposals, not proof authority.

One continuous energy-flow model is reused; every node bound/Farkas vector is
checked by the separately authored exact checker. No old root packet is read.
No backend is imported except lazily by the supplied flow.build callback.
This is a producer only: an independent final coverage check is mandatory.
"""
from fractions import Fraction as Q
import heapq
import math
import time


def _require(condition,message):
    if not condition:
        raise ValueError(message)


def materialize_tree(packet):
    """Expand single-stored proof references in memory for checker.verify_tree.

    Serialize packet's reference tree/proof store, not this expanded view.
    The checker independently verifies every branch domain and leaf algebra.
    """
    output={}
    for identifier,node in packet['tree']['nodes'].items():
        if node['kind'] in ('bound','infeasible'):
            proof=packet['proofs'][node['certificate_ref']]
            _require(proof['verified'] is True,'Unverified proof reference')
            output[identifier]=dict(kind=node['kind'],certificate=proof['certificate'])
        elif node['kind']=='branch':
            output[identifier]=dict(kind='branch',movement=node['movement'],children=dict(node['children']))
        else:
            output[identifier]=dict(kind='open',reason=node.get('reason','Missing bound'))
    return dict(root=packet['tree']['root'],nodes=output)


def produce(case,case_dict,*,flow,checker,semantic_reconstruct,case_token,
            target_authority,admit_target,exclusion,admit_exclusion,limits,record=None):
    """New conditional-two-bus QP tree; all callbacks are cached frozen source.

    limits has nodes,native_calls,seconds,cpu_seconds,qp_seconds,infeasibility_lp_seconds,
    checker_seconds,closure_seconds,closure_cpu_seconds. Target admission returns {status:'ADMITTED_HULL_UPPER',
    case_token,upper_bound}. Admission callbacks inspect source-bound cached
    records, never follow artifact-supplied paths. No owner/dispatch is included.
    """
    started=time.monotonic()
    cpu_started=time.process_time()
    required={'nodes','native_calls','seconds','cpu_seconds','qp_seconds','infeasibility_lp_seconds',
              'checker_seconds','closure_seconds','closure_cpu_seconds'}
    _require(set(limits)==required,'Freeze every producer limit explicitly')
    _require(type(limits['nodes']) is int and limits['nodes']>=1 and
             type(limits['native_calls']) is int and limits['native_calls']>=1,'Invalid integer limits')
    _require(all(math.isfinite(limits[k]) and limits[k]>0 for k in required-{'nodes','native_calls'}),
             'Invalid time limits')
    deadline=started+limits['seconds']
    proofs,nodes,states,events={}, {}, {}, []
    calls=0
    built=None
    active_constraints=[]
    packet=dict(status='PRODUCER_UNRESOLVED',tree=dict(root='n0',nodes=nodes),proofs=proofs,
                node_states=states,native_events=events,limits=dict(limits),
                scope='D_two plus separately qualified physical>=3 floor; NOT CH',
                final_independent_coverage_check_required=True,exact_global_certificate_claim=False,
                exact_integer_optimum_claim=False)
    def emit(value):
        event=dict(producer_elapsed_s=time.monotonic()-started,**value)
        events.append(event)
        if record is not None: record(event)
    def can_call(seconds):
        return (calls<limits['native_calls'] and time.monotonic()+seconds+limits['checker_seconds']+limits['closure_seconds']<=deadline
                and time.process_time()-cpu_started+seconds+limits['checker_seconds']+limits['closure_cpu_seconds']<=limits['cpu_seconds'])
    def can_check():
        return (time.monotonic()+limits['checker_seconds']+limits['closure_seconds']<=deadline
                and time.process_time()-cpu_started+limits['checker_seconds']+limits['closure_cpu_seconds']<=limits['cpu_seconds'])
    def add_proof(certificate,checked,decisions,source):
        identifier='p'+str(len(proofs))
        canonical=dict(multipliers={name:value for name,value in checked['multipliers'].items() if value})
        if checked['status']=='CERTIFIED_BOUND':
            canonical.update(tangent_loads=checked['tangent_loads'],claimed_lower=checked['lower_bound'])
        else:
            canonical['claimed_contradiction']=checked['contradiction']
        proofs[identifier]=dict(verified=True,certificate=canonical,source=source,decisions=decisions,
            status=checked['status'],lower_bound=checked['lower_bound'],
            sign_projected_rows=checked['sign_projected_rows'])
        return identifier
    try:
        admitted=admit_target(target_authority)
        _require(isinstance(admitted,dict) and admitted.get('status')=='ADMITTED_HULL_UPPER'
                 and admitted.get('case_token')==case_token,'Target lacks source-bound feasible-mixture admission')
        target=Q(admitted['upper_bound'])
        context=checker.prepare(case_dict,semantic_reconstruct,mode='quadratic',fleet_count=2,case_token=case_token)
        # A prescribed mathematical seed, not a replacement for missing native
        # Pi: fleet fee at exactly two buses and an explicit zero supply tangent.
        elementary=dict(tangent_loads=[Q(0)]*len(context['loads']),
                        multipliers={'__fleet_count__':Q(case_dict['vehicle_cost'])})
        initial_tree=dict(root='n0',nodes={'n0':dict(kind='bound',certificate=elementary)})
        _require(can_check(),'No full initial certificate-check funding')
        initial=checker.verify_tree(context,initial_tree,exclusion=exclusion,
            admit_transfer=admit_exclusion,target=target,limits={'seconds':limits['checker_seconds']})
        _require(initial['status']=='COMPLETE' and initial.get('global_lower_bound') is not None,
                 'Conditional scope/external higher-fleet admission failed')
        _require(initial['higher_fleet_exclusion']['lower_bound']>target,
                 'Current three-plus floor cannot separate this target; no two-bus-only search launched')
        checked=initial['leaves'][0]['certificate']
        p0=add_proof(elementary,checked,(),'source-defined fleet-fee/zero-tangent seed')
        nodes['n0']=dict(kind='bound',certificate_ref=p0)
        states['n0']=dict(decisions=(),lower_bound=checked['lower_bound'],search_state='OPEN_UNPROCESSED')
        heap=[(checked['lower_bound'],0,0,'n0')]
        serial=0
        packet.update(target=target,target_admission=admitted,
                      higher_fleet_exclusion=initial['higher_fleet_exclusion'],case_token=case_token)
        if checked['lower_bound']>target:
            states['n0']['search_state']='TARGET_PRUNED'
            heap=[]
        if heap:
            _require(can_call(limits['qp_seconds']),'Insufficient funding for one full new conditional root QP')
            built=flow.build(case,continuous=True)
            model,gp=built['model'],built['gp']
            model.Params.Threads=1
            model.Params.Method=0
            model.Params.InfUnbdInfo=1
            model.Params.DualReductions=0
            by_name={v['name']:built['assembly'].native[v['index']] for v in built['ledger']['variables']}
            y={m['id']:by_name['y'+str(j)] for j,m in enumerate(case_dict['movements'])}
            starts=[y[m['id']] for m in case_dict['movements'] if m['kind']=='pullout']
            model.addConstr(gp.quicksum(starts)==2,name='__fleet_count__')
            model.update()
            a,b=float(.2),float(1/900)
            objective=gp.LinExpr([float(c) for c in context['operations'].values()],
                                [by_name[name] for name in context['operations']])
            objective+=gp.quicksum(a*by_name[name]+b*by_name[name]*by_name[name]/2 for name in context['loads'])
            order=list(context['movement_variables'])
            def snapshot(phase,node_id,seconds):
                nonlocal calls
                _require(can_call(seconds),'No fully funded next native call')
                model.Params.TimeLimit=seconds
                calls+=1
                anchor=time.monotonic()
                emit(dict(event='native_call_begin',call=calls,phase=phase,node=node_id,allowance_s=seconds))
                try:
                    model.optimize()
                except Exception as exc:
                    emit(dict(event='native_call_failure',call=calls,phase=phase,node=node_id,
                              elapsed_s=time.monotonic()-anchor,reason=type(exc).__name__+': '+str(exc)))
                    raise
                event=dict(event='native_call',call=calls,phase=phase,node=node_id,
                    raw_status=int(model.Status),solution_count=int(model.SolCount),
                    allowance_s=seconds,elapsed_s=time.monotonic()-anchor,method=0,
                    model_policy='reused model/solver state, no supplied primal start')
                emit(event)
                return event
            def extract_bound(decisions,fallback):
                try:
                    multipliers={}
                    for c in model.getConstrs():
                        value=float(c.Pi)
                        if value:multipliers[c.ConstrName]=value
                except (AttributeError,gp.GurobiError):
                    return None,None,{},'Pi unavailable'
                tangent=list(fallback)
                guide={}
                if model.SolCount:
                    tangent=[float(by_name[name].X) for name in context['loads']]
                    guide={mid:float(variable.X) for mid,variable in y.items() if math.isfinite(float(variable.X))}
                proposal=dict(multipliers=multipliers,tangent_loads=tangent)
                if not can_check(): return proposal,None,guide,'No full bound-check funding'
                check=checker.verify_node(context,decisions,proposal,limits={'seconds':limits['checker_seconds']})
                return proposal,check,guide,None
            def extract_farkas(decisions):
                try:
                    # Solver orientation is a proposal only. Exact sign/box
                    # checking decides whether this is a contradiction.
                    multipliers={}
                    for c in model.getConstrs():
                        value=-float(c.FarkasDual)
                        if value:multipliers[c.ConstrName]=value
                    proposal=dict(multipliers=multipliers)
                except (AttributeError,gp.GurobiError):
                    return None,None,'FarkasDual unavailable'
                if not can_check(): return proposal,None,'No full Farkas-check funding'
                check=checker.verify_node(context,decisions,proposal,infeasible=True,limits={'seconds':limits['checker_seconds']})
                return proposal,check,None
            def choose(guide,decisions):
                fixed={mid for mid,value in decisions}
                remaining=[mid for mid in order if mid not in fixed]
                if not remaining: return None
                fractional=[]
                for index,mid in enumerate(order):
                    value=guide.get(mid)
                    if mid not in fixed and value is not None and math.isfinite(value) and 1e-7<value<1-1e-7:
                        fractional.append((-min(value,1-value),index,mid))
                return min(fractional)[2] if fractional else remaining[0]
            while heap:
                if time.monotonic()+limits['closure_seconds']>=deadline:
                    packet['stop_reason']='Producer deadline/closure reserve reached'
                    break
                if time.process_time()-cpu_started+limits['closure_cpu_seconds']>=limits['cpu_seconds']:
                    packet['stop_reason']='Producer CPU/closure reserve reached'
                    break
                _,_,_,identifier=heapq.heappop(heap)
                state=states[identifier]
                decisions=tuple(state['decisions'])
                if state['lower_bound']>target:
                    state['search_state']='TARGET_PRUNED'
                    continue
                if not can_call(limits['qp_seconds']):
                    state['search_state']='OPEN_UNPROCESSED'
                    packet['stop_reason']='Native-call count or complete next-QP funding exhausted'
                    break
                if active_constraints:
                    model.remove(active_constraints)
                    model.update()
                active_constraints=[]
                for mid,value in decisions:
                    active_constraints.append(model.addConstr(y[mid]==value,name=context['branch_names'][mid]))
                model.setObjective(objective,gp.GRB.MINIMIZE)
                model.update()
                call=snapshot('QUADRATIC_NODE',identifier,limits['qp_seconds'])
                inherited=proofs[nodes[identifier]['certificate_ref']]['certificate']
                proposal,check,guide,error=extract_bound(decisions,inherited['tangent_loads'])
                state['last_native_status']=call['raw_status']
                state['bound_proposal_status']=check['status'] if check is not None else 'UNAVAILABLE'
                if error: state['bound_proposal_reason']=error
                elif check is not None and check['status']!='CERTIFIED_BOUND':
                    state['bound_proposal_reason']=check.get('reason','Exact node proposal not accepted')
                if check is not None and check['status']=='CERTIFIED_BOUND':
                    ref=add_proof(proposal,check,decisions,'new conditional node QP multipliers/tangent')
                    if check['lower_bound']>state['lower_bound']:
                        state['lower_bound']=check['lower_bound']
                        nodes[identifier]['certificate_ref']=ref
                if state['lower_bound']>target:
                    state['search_state']='TARGET_PRUNED'
                    continue
                if call['raw_status'] in (gp.GRB.INFEASIBLE,gp.GRB.INF_OR_UNBD):
                    proposal,contradiction,error=extract_farkas(decisions)
                    if contradiction is None or contradiction['status']!='CERTIFIED_INFEASIBLE':
                        # At most one explicitly funded feasibility-LP conversion
                        # at this node. No objective solve, phase or cap retry.
                        if can_call(limits['infeasibility_lp_seconds']):
                            model.setObjective(0.0,gp.GRB.MINIMIZE)
                            model.update()
                            snapshot('ONE_ZERO_OBJECTIVE_FEASIBILITY_LP',identifier,limits['infeasibility_lp_seconds'])
                            proposal,contradiction,error=extract_farkas(decisions)
                        else:
                            error='Prescribed feasibility LP not fully funded'
                    if contradiction is not None and contradiction['status']=='CERTIFIED_INFEASIBLE':
                        ref=add_proof(proposal,contradiction,decisions,'exact checked Farkas from prescribed node/LP proposal')
                        nodes[identifier]=dict(kind='infeasible',certificate_ref=ref)
                        state['search_state']='EXACT_INFEASIBLE'
                        state['lower_bound']='+inf'
                        continue
                    state['search_state']='OPEN_NATIVE_INFEASIBILITY_UNCERTIFIED'
                    state['infeasibility_reason']=error or contradiction.get('reason','No exact positive contradiction')
                    packet['stop_reason']='Native infeasibility did not produce an exact proof; inherited bound retained'
                    break
                movement=choose(guide,decisions)
                if movement is None:
                    state['search_state']='OPEN_FIXED_TOPOLOGY_BOUND_TOO_WEAK'
                    packet['stop_reason']='No unfixed movement remains and exact lower does not exceed target'
                    break
                if len(nodes)+2>limits['nodes']:
                    state['search_state']='OPEN_NODE_LIMIT'
                    packet['stop_reason']='Node limit reached before creating both children'
                    break
                parent_ref=nodes[identifier]['certificate_ref']
                children={}
                for value in (0,1):
                    serial+=1
                    child='n'+str(serial)
                    children[str(value)]=child
                    child_decisions=decisions+((movement,value),)
                    nodes[child]=dict(kind='bound',certificate_ref=parent_ref)
                    states[child]=dict(decisions=child_decisions,lower_bound=state['lower_bound'],
                                      search_state='OPEN_UNPROCESSED')
                    # Best exact bound; deeper first on ties, then creation order.
                    heapq.heappush(heap,(state['lower_bound'],-len(child_decisions),serial,child))
                nodes[identifier]=dict(kind='branch',movement=movement,children=children)
                state.update(search_state='BRANCHED',branched_movement=movement,
                             branch_guide_value=guide.get(movement))
        fringe=[identifier for identifier,node in nodes.items() if node['kind']!='branch']
        open_fringe=[identifier for identifier in fringe if states[identifier]['search_state'] not in ('TARGET_PRUNED','EXACT_INFEASIBLE')]
        packet.update(status='TARGET_COVERAGE_PROPOSED' if not open_fringe else 'OPEN_SEARCH',
                      search_complete=not open_fringe,open_fringe=open_fringe,
                      complete_bound_fringe_preserved=True,
                      distinction='Every frontier leaf has a valid bound or contradiction; open search leaves may have bounds below target. This is not an integer optimum certificate.')
    except Exception as exc:
        packet.update(status='PRODUCER_UNRESOLVED',stop_reason=type(exc).__name__+': '+str(exc))
    finally:
        if built is not None:
            try:
                built['model'].dispose()
            except Exception as exc:
                packet.update(status='PRODUCER_UNRESOLVED',cleanup_failure=type(exc).__name__+': '+str(exc))
            built.clear()
    if nodes:
        fringe=[identifier for identifier,node in nodes.items() if node['kind']!='branch']
        packet['open_fringe']=[identifier for identifier in fringe
            if states[identifier]['search_state'] not in ('TARGET_PRUNED','EXACT_INFEASIBLE')]
        packet.setdefault('search_complete',False)
        packet['complete_bound_fringe_preserved']=all(nodes[i]['kind'] in ('bound','infeasible') for i in fringe)
    packet.update(native_calls=calls,elapsed_s=time.monotonic()-started,
                  cpu_s=time.process_time()-cpu_started,
                  storage_policy='Exact proof vectors stored once by ID; expand references only in memory for final independent checker',
                  no_old_root_packet_consumed=True,no_automatic_native_retry=True)
    return packet
