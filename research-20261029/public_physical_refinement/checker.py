"""Narrow admitted-partition refinement; old numerical proofs are not rerun.

The caller authenticates extractor output with admit_base. Only new node
algebra is delegated to the immutable exact checker. This is physical D only.
"""
from fractions import Fraction as Q
import time


def need(ok,message):
    if not ok:raise ValueError(message)


def seal_base(value):
    """Immutable snapshot made once after authenticated extraction, not a hash."""
    if isinstance(value,dict):
        need(all(isinstance(k,str) for k in value),'base keys')
        return ('dict',tuple((k,seal_base(value[k])) for k in sorted(value)))
    if isinstance(value,(list,tuple)):
        return ('sequence',tuple(seal_base(v) for v in value))
    if isinstance(value,Q):return ('rational',value.numerator,value.denominator)
    if value is None or type(value) in (str,int,bool):return (type(value).__name__,value)
    raise ValueError('nonexact/unexpected base field type')


def decisions(context,sequence):
    output=[];seen=set()
    for mid,value in sequence:
        need(mid in context['movement_variables'] and mid not in seen,'unknown/repeated movement')
        need(type(value) is int and value in (0,1),'binary decision')
        seen.add(mid);output.append((mid,value))
    return tuple(output)


def _limits(limits):
    result=dict(nodes=255,depth=255,seconds=180,node_seconds=30)
    if limits:result.update(limits)
    need(all(result[k]>0 for k in result),'positive limits')
    return result


def verify_local(context,root_decisions,tree,checker,base_leaf,limits=None,proofs=None):
    """Check one new subtree under a source-admitted original frontier prefix.

    base_bound leaves name base_leaf_id, preserving that bound on descendants.
    New bound/infeasible leaves carry certificate or a new certificate_ref.
    Rejected/unresolved local work never strengthens the admitted old bound.
    """
    cap=_limits(limits);started=time.monotonic();seen=set();leaves=[]
    try:
        prefix=decisions(context,root_decisions)
        need(prefix==decisions(context,base_leaf['decisions']),'altered inherited prefix')
        need(base_leaf['status']=='CERTIFIED_BOUND','cannot reopen admitted infeasible leaf')
        old=Q(base_leaf['lower_bound']);nodes=tree['nodes']
        need(isinstance(nodes,dict) and tree['root'] in nodes and len(nodes)-1<=cap['nodes'],'local node limit/root')
        stack=[(tree['root'],prefix,0)]
        while stack:
            need(time.monotonic()-started<cap['seconds'],'local time limit')
            identifier,path,depth=stack.pop()
            need(identifier in nodes and identifier not in seen and depth<=cap['depth'],'local coverage/depth')
            seen.add(identifier);node=nodes[identifier];kind=node['kind']
            if kind=='branch':
                mid=node['movement'];children=node['children']
                need(mid in context['movement_variables'] and mid not in dict(path),'branch repeats inherited/fixed movement')
                need(set(children)=={'0','1'} and children['0']!=children['1'],'both distinct children required')
                stack.append((children['1'],path+((mid,1),),depth+1))
                stack.append((children['0'],path+((mid,0),),depth+1))
            elif kind=='base_bound':
                need(node['base_leaf_id']==base_leaf['leaf_id'],'foreign admitted base bound')
                leaves.append(dict(id=identifier,status='ADOPTED_BASE_BOUND',lower_bound=old))
            elif kind in ('bound','infeasible'):
                if 'certificate' in node:
                    certificate=node['certificate']
                else:
                    need(proofs is not None,'missing new proof store')
                    certificate=proofs[node['certificate_ref']]['certificate']
                remaining=cap['seconds']-(time.monotonic()-started)
                need(remaining>0,'local check funding')
                audit=checker.verify_node(context,path,certificate,infeasible=kind=='infeasible',
                    limits=dict(seconds=min(cap['node_seconds'],remaining)))
                need(audit['status']==('CERTIFIED_BOUND' if kind=='bound' else 'CERTIFIED_INFEASIBLE'),
                     'new exact node certificate not accepted: '+str(audit.get('reason')))
                leaves.append(dict(id=identifier,status=audit['status'],
                    lower_bound=max(old,Q(audit['lower_bound'])) if kind=='bound' else None,
                    audit=audit))
            else:
                raise ValueError('explicit open/unknown local leaf lacks retained base bound')
        need(seen==set(nodes) and leaves,'unreachable node/empty local coverage')
        finite=[l['lower_bound'] for l in leaves if l['lower_bound'] is not None]
        return dict(status='COMPLETE',complete=True,local_lower=min(finite) if finite else None,
                    all_infeasible=not finite,checked_new_nodes=max(0,len(seen)-1),leaves=leaves,
                    scope='D_two under admitted inherited prefix')
    except (ValueError,KeyError,TypeError,IndexError,OverflowError) as exc:
        return dict(status='REJECTED',complete=False,reason=str(exc),checked_new_nodes=max(0,len(seen)-1),
                    leaves=leaves,retained_base_lower=base_leaf.get('lower_bound'))


def verify_refinements(context,base,packet,checker,admit_base,limits=None,base_seal=None):
    """Require every old frontier identity; certify new algebra only.

    packet={'refinements':{oldleafid:localtree,...},'proofs':{newref:...}}.
    Old infeasible leaves use a singleton base_infeasible tree naming their ID.
    admit_base must bind this exact object to prospectively authenticated input.
    """
    started=time.monotonic();cap=_limits(limits);reports=[]
    try:
        need(callable(admit_base) and admit_base(base) is True,'base authority denied')
        need(base_seal is not None and seal_base(base)==base_seal,'base changed after authenticated extraction')
        need(base['status']=='SOURCE_BOUND_BASE_ADMITTED' and base['case_token']==context['case_token'],
             'base status/case')
        need(base['minimum_fleet']>=2 and base['fleet_count']==2 and context['fleet_count']==2
             and context['mode']=='quadratic','physical exact-two scope required')
        need(context['minimum_fleet_proof']['minimum_fleet']>=2,'fresh semantic minimum-fleet obstruction missing')
        need(Q(base['epsilon'])==Q(1,10000) and Q(base['target'])==Q(base['physical_upper'])-Q(base['epsilon']),
             'physical target/epsilon')
        frontier={f['leaf_id']:f for f in base['frontier']}
        need(len(frontier)==len(base['frontier']) and frontier,'base frontier denominator')
        # Reconstruct only the adopted branch partition and inherited prefixes;
        # no original multiplier/certificate vector is inspected or recalculated.
        structure=base['base_tree'];nodes=structure['nodes'];seen=set();found=set()
        stack=[(structure['root'],())]
        while stack:
            identifier,path=stack.pop()
            need(identifier in nodes and identifier not in seen,'base shared/missing node')
            seen.add(identifier);node=nodes[identifier]
            if node['kind']=='branch':
                mid=node['movement'];children=node['children']
                decisions(context,path+((mid,0),))
                need(set(children)=={'0','1'} and children['0']!=children['1'],'base binary coverage')
                stack.append((children['1'],path+((mid,1),)))
                stack.append((children['0'],path+((mid,0),)))
            else:
                need(node['kind']=='admitted_base_leaf' and node['leaf_id']==identifier and identifier in frontier,
                     'base leaf identity')
                need(decisions(context,frontier[identifier]['decisions'])==path,'base inherited path changed')
                found.add(identifier)
        need(seen==set(nodes) and len(seen)==base['base_nodes'] and found==set(frontier),'base partition denominator')
        refinements=packet['refinements'];need(set(refinements)==set(frontier),'missing/foreign refinement entry')
        finite=[];new_count=0;failed=[]
        for identifier,leaf in frontier.items():
            tree=refinements[identifier]
            if leaf['status']=='CERTIFIED_INFEASIBLE':
                need(Q(leaf['contradiction'])>0,'admitted contradiction')
                need(len(tree['nodes'])==1 and tree['root'] in tree['nodes'],'infeasible retention tree')
                node=tree['nodes'][tree['root']]
                need(node in (dict(kind='base_infeasible',base_leaf_id=identifier),
                              dict(kind='base_bound',base_leaf_id=identifier)),
                     'altered old infeasible leaf')
                reports.append(dict(leaf_id=identifier,status='ADOPTED_BASE_INFEASIBLE'));continue
            need(leaf['status']=='CERTIFIED_BOUND','base status')
            remaining=cap['seconds']-(time.monotonic()-started)
            need(remaining>0,'refinement audit time limit')
            audit=verify_local(context,leaf['decisions'],tree,checker,leaf,
                dict(cap,seconds=remaining),packet.get('proofs'))
            new_count+=audit['checked_new_nodes'];need(new_count<=cap['nodes'],'total new node limit')
            reports.append(dict(leaf_id=identifier,result=audit))
            if audit['status']!='COMPLETE':
                finite.append(Q(leaf['lower_bound']));failed.append(identifier)
            elif not audit['all_infeasible']:finite.append(audit['local_lower'])
        need(finite,'all-infeasible partition contradicts admitted physical upper')
        two=min(finite);global_lower=min(two,Q(base['floor_ge3']))
        need(global_lower>=Q(base['old_global_physical_lower']),'weakened adopted global bound')
        need(global_lower<=Q(base['physical_upper']),'lower contradicts admitted physical upper')
        need(seal_base(base)==base_seal,'base mutated during refinement verification')
        return dict(status='VALID_REFINEMENT' if not failed else 'VALID_BASE_WITH_REJECTED_REFINEMENTS',
            complete_base_coverage=True,global_lower_bound=global_lower,two_bus_lower=two,
            physical_upper=Q(base['physical_upper']),epsilon_met=Q(base['physical_upper'])-global_lower<=Q(base['epsilon']),
            rejected_refinements=failed,reports=reports,new_nodes_checked=new_count,
            scope='D_physical, not CH',old_numeric_audit_repeated=False)
    except (ValueError,KeyError,TypeError,IndexError,OverflowError) as exc:
        return dict(status='REJECTED',reason=str(exc),complete_base_coverage=False,reports=reports,
                    scope='No new global bound certified')
