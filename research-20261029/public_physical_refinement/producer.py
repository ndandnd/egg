"""Minimal admitted-frontier quadratic refinement; proposals are not authority.

No old search or dual audit occurs. Every admitted base leaf remains represented.
Caller funds independent final verify_refinements and complete outer closure.
"""
from fractions import Fraction as Q
import heapq
import math
import time


def require(condition,message):
    if not condition:raise ValueError(message)


def produce(case,case_dict,base,*,flow,checker,semantic_reconstruct,admit_base,limits,record=None):
    started=time.monotonic();cpu_started=time.process_time()
    required={'new_nodes','native_calls','seconds','cpu_seconds','qp_seconds','feasibility_seconds',
              'checker_seconds','closure_seconds','closure_cpu_seconds'}
    require(set(limits)==required,'Every refinement limit must be frozen')
    require(type(limits['new_nodes']) is int and 0<=limits['new_nodes']<=255
        and type(limits['native_calls']) is int and 1<=limits['native_calls']<=300,'Invalid refinement counts')
    require(all(math.isfinite(limits[k]) and limits[k]>0 for k in required-{'new_nodes','native_calls'}),'Invalid time limits')
    require(limits['qp_seconds']<=10 and limits['feasibility_seconds']<=10,'Native cap exceeds proposal')
    require(admit_base(base) is True and base['status']=='SOURCE_BOUND_BASE_ADMITTED','Base lacks source authority')
    require(case.identity()==base['case_token'],'Native case differs from admitted descriptor identity')
    target=Q(base['target']);deadline=started+limits['seconds']
    proofs={};trees={};states={};events=[];calls=0;new_nodes=0;serial=0;built=None
    packet=dict(status='REFINEMENT_UNRESOLVED',refinements=trees,proofs=proofs,node_states=states,
        native_events=events,target=target,base_artifact_revision=base['artifact_revision'],
        old_nodes_admitted=base['base_nodes'],new_nodes=0,native_calls=0,
        scope='Physical D_two plus admitted physical>=3 floor, never CH',
        opportunity_scope='declared movement modes with fixed leg times and chosen depot-gap alternatives',
        unrestricted_retiming_or_extra_visit_claim=False,
        final_independent_refinement_check_required=True)
    def emit(value):
        event=dict(value);event['producer_elapsed_s']=time.monotonic()-started
        events.append(event)
        if record is not None:record(event)
    def can_call(seconds):
        return (calls<limits['native_calls'] and time.monotonic()+seconds+limits['checker_seconds']+limits['closure_seconds']<=deadline
            and time.process_time()-cpu_started+seconds+limits['checker_seconds']+limits['closure_cpu_seconds']<=limits['cpu_seconds'])
    def can_check():
        return (time.monotonic()+limits['checker_seconds']+limits['closure_seconds']<=deadline
            and time.process_time()-cpu_started+limits['checker_seconds']+limits['closure_cpu_seconds']<=limits['cpu_seconds'])
    def save(check,decisions):
        ref='p'+str(len(proofs));certificate=dict(multipliers={k:v for k,v in check['multipliers'].items() if v})
        if check['status']=='CERTIFIED_BOUND':certificate.update(tangent_loads=check['tangent_loads'],claimed_lower=check['lower_bound'])
        else:certificate['claimed_contradiction']=check['contradiction']
        proofs[ref]=dict(certificate=certificate,decisions=decisions,verified=True)
        return ref
    heap=[]
    for order,leaf in enumerate(base['frontier']):
        name=leaf['leaf_id'];require(name not in trees,'Duplicate admitted base leaf')
        trees[name]=dict(root='r',nodes={'r':dict(kind='base_bound',base_leaf_id=name)})
        states[(name,'r')]=dict(decisions=(),search_state='RETAINED_BASE',lower_bound=leaf['lower_bound'])
        if leaf['status']=='CERTIFIED_BOUND' and Q(leaf['lower_bound'])<target:
            states[(name,'r')]['search_state']='OPEN_UNPROCESSED'
            heapq.heappush(heap,(Q(leaf['lower_bound']),0,order,name,'r'))
    base_by_id={leaf['leaf_id']:leaf for leaf in base['frontier']}
    # JSON object keys are strings; internal pair keys are exported as records.
    try:
        context=checker.prepare(case_dict,semantic_reconstruct,mode='quadratic',fleet_count=2,case_token=base['case_token'])
        require(context['minimum_fleet_proof']['minimum_fleet']>=2,'One-bus obstruction missing')
        if heap:
            require(can_call(limits['qp_seconds']),'No fully funded first new call')
            built=flow.build(case,continuous=True);model,gp=built['model'],built['gp']
            model.Params.Threads=1;model.Params.Method=0;model.Params.InfUnbdInfo=1;model.Params.DualReductions=0
            by_name={v['name']:built['assembly'].native[v['index']] for v in built['ledger']['variables']}
            y={mid:by_name[name] for mid,name in context['movement_variables'].items()}
            model.addConstr(gp.quicksum(y[m['id']] for m in case_dict['movements'] if m['kind']=='pullout')==2,name='__fleet_count__')
            objective=gp.LinExpr([float(c) for c in context['operations'].values()],[by_name[n] for n in context['operations']])
            objective+=gp.quicksum(float(.2)*by_name[n]+float(1/900)*by_name[n]*by_name[n]/2 for n in context['loads'])
            active=[];order=list(context['movement_variables'])
            def native(phase,leaf_id,node_id,seconds):
                nonlocal calls
                require(can_call(seconds),'Next full native call/check/closure not funded')
                model.Params.TimeLimit=seconds;calls+=1;anchor=time.monotonic()
                emit(dict(event='native_begin',call=calls,phase=phase,base_leaf_id=leaf_id,node=node_id,allowance_s=seconds))
                model.optimize()
                answer=dict(event='native_complete',call=calls,phase=phase,base_leaf_id=leaf_id,node=node_id,
                    raw_status=int(model.Status),solution_count=int(model.SolCount),elapsed_s=time.monotonic()-anchor)
                emit(answer);return answer
            def bound(decisions):
                if not can_check():return None,{}
                try:pi={c.ConstrName:float(c.Pi) for c in model.getConstrs() if float(c.Pi)}
                except (AttributeError,gp.GurobiError):return None,{}
                if not model.SolCount:return None,{}
                tangent=[float(by_name[n].X) for n in context['loads']]
                guide={mid:float(v.X) for mid,v in y.items()}
                check=checker.verify_node(context,decisions,dict(multipliers=pi,tangent_loads=tangent),limits={'seconds':limits['checker_seconds']})
                return check,guide
            def infeasible(decisions):
                if not can_check():return None
                try:pi={c.ConstrName:-float(c.FarkasDual) for c in model.getConstrs() if float(c.FarkasDual)}
                except (AttributeError,gp.GurobiError):return None
                return checker.verify_node(context,decisions,dict(multipliers=pi),infeasible=True,limits={'seconds':limits['checker_seconds']})
            while heap:
                if not can_call(limits['qp_seconds']):packet['stop_reason']='Full next-call funding or native-call cap exhausted';break
                lower,_,_,leaf_id,node_id=heapq.heappop(heap)
                state=states[(leaf_id,node_id)];tree=trees[leaf_id];local=tuple(state['decisions'])
                prefix=tuple(tuple(p) for p in base_by_id[leaf_id]['decisions']);decisions=prefix+local
                if lower>=target:state['search_state']='TARGET_PRUNED';continue
                if active:model.remove(active);model.update()
                active=[model.addConstr(y[mid]==value,name=context['branch_names'][mid]) for mid,value in decisions]
                model.setObjective(objective,gp.GRB.MINIMIZE);model.update()
                result=native('QUADRATIC_REFINEMENT',leaf_id,node_id,limits['qp_seconds'])
                check,guide=bound(decisions)
                if check is not None and check['status']=='CERTIFIED_BOUND' and check['lower_bound']>lower:
                    lower=check['lower_bound'];state['lower_bound']=lower
                    tree['nodes'][node_id]=dict(kind='bound',certificate_ref=save(check,decisions))
                if lower>=target:state['search_state']='TARGET_PRUNED';continue
                if result['raw_status'] in (gp.GRB.INFEASIBLE,gp.GRB.INF_OR_UNBD):
                    contradiction=infeasible(decisions)
                    if contradiction is None or contradiction['status']!='CERTIFIED_INFEASIBLE':
                        if can_call(limits['feasibility_seconds']):
                            model.setObjective(0.0,gp.GRB.MINIMIZE);model.update()
                            native('ONE_PRESCRIBED_FEASIBILITY_LP',leaf_id,node_id,limits['feasibility_seconds'])
                            contradiction=infeasible(decisions)
                    if contradiction is not None and contradiction['status']=='CERTIFIED_INFEASIBLE':
                        tree['nodes'][node_id]=dict(kind='infeasible',certificate_ref=save(contradiction,decisions))
                        state['search_state']='EXACT_INFEASIBLE';continue
                    state['search_state']='OPEN_INFEASIBILITY_UNCERTIFIED';packet['stop_reason']='Native infeasibility lacked an exact contradiction';break
                fixed=dict(decisions);remaining=[mid for mid in order if mid not in fixed]
                if not remaining:
                    state['search_state']='OPEN_FIXED_TOPOLOGY_WEAK';packet['stop_reason']='No unfixed movement; exact lower below target';break
                fractional=[(-min(guide[mid],1-guide[mid]),i,mid) for i,mid in enumerate(order)
                    if mid in remaining and mid in guide and math.isfinite(guide[mid]) and 1e-7<guide[mid]<1-1e-7]
                movement=min(fractional)[2] if fractional else remaining[0]
                if new_nodes+2>limits['new_nodes']:
                    state['search_state']='OPEN_NEW_NODE_CAP';packet['stop_reason']='New-node cap before creating both children';break
                inherited=dict(tree['nodes'][node_id]);children={}
                for value in (0,1):
                    serial+=1;child='n'+str(serial);children[str(value)]=child
                    tree['nodes'][child]=dict(inherited)
                    child_decisions=local+((movement,value),)
                    states[(leaf_id,child)]=dict(decisions=child_decisions,lower_bound=lower,search_state='OPEN_UNPROCESSED')
                    heapq.heappush(heap,(lower,-len(prefix+child_decisions),serial+len(base['frontier']),leaf_id,child))
                new_nodes+=2;tree['nodes'][node_id]=dict(kind='branch',movement=movement,children=children)
                state['search_state']='BRANCHED'
    except Exception as exc:
        packet['stop_reason']=type(exc).__name__+': '+str(exc)
        packet['producer_failure']=packet['stop_reason']
    finally:
        if built is not None:
            try:built['model'].dispose()
            except Exception as exc:packet['cleanup_failure']=type(exc).__name__+': '+str(exc)
            built.clear()
    open_nodes=[]
    for (leaf_id,node_id),state in states.items():
        if trees[leaf_id]['nodes'][node_id]['kind']=='branch':continue
        if state['search_state'] not in ('TARGET_PRUNED','EXACT_INFEASIBLE','RETAINED_BASE'):
            open_nodes.append(dict(base_leaf_id=leaf_id,node=node_id))
    packet.update(status=('REFINEMENT_UNRESOLVED' if 'producer_failure' in packet or 'cleanup_failure' in packet else
                          'TARGET_REFINEMENT_PROPOSED' if not open_nodes else 'OPEN_REFINEMENT'),
        open_nodes=open_nodes,new_nodes=new_nodes,native_calls=calls,
        node_states=[dict(base_leaf_id=l,node=n,**s) for (l,n),s in states.items()],
        cpu_s=time.process_time()-cpu_started,elapsed_s=time.monotonic()-started,
        no_old_search_repeated=True,no_old_numeric_audit_repeated=True,exact_optimum_claim=False)
    return packet
