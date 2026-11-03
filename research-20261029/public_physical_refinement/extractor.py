"""Source-bound base-partition transfer; no old dual algebra or physical replay.

Caller must byte-admit each fixed source/input at PINS before calling adopt.
Full JSON decoding may be transient; only old structure/audited leaf summaries
and compact closure are consumed. No old multiplier vectors are traversed.
"""
from fractions import Fraction as Q

CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
OLD_SOURCE='6a171357b65254b52cade63ed95dcce798485f36'
OLD_CONTROL='6bdcf254'
ARTIFACT='ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9'
PREFIX='research-20261029/public_support_tree/attempt01/'
PINS={name:(ARTIFACT,PREFIX+filename) for name,filename in (
    ('tree','PUBLIC_TREE.json.gz'),('audit','INDEPENDENT_TREE_CHECK.json.gz'),
    ('results','results.json'),('owner','owner_receipt.json'))}
PINS['upper_authority']=('3cbb8c9d965e9222ef8a98191bf775b4925382a1',
    'research-20261029/public_rational_recovery/TRANSFER_AUTHORITY.json')
UPPER=Q('15487225773558335836678536516523969405935273717647515/35076039295941670036888435985190792471742381031424')


def require(condition,message):
    if not condition:raise ValueError(message)


def adopt(tree_packet,audit,results,owner,upper_authority,pins):
    """Adopt already checked leaves, not a fresh numerical tree verification."""
    require(pins==PINS,'Fixed base-partition input pins changed')
    require(results.get('status')=='CLOSED' and results.get('assigned')==3
        and results.get('resource_pass') is True and results.get('scientific_outcome')=='POSITIVE_GAP_CERTIFIED',
        'Original complete package closure missing')
    names=('Q0','PUBLIC_TREE','INDEPENDENT_TREE_CHECK')
    require(tuple(r['id'] for r in results['rows'])==names and all(r['status']=='DELIVERED' for r in results['rows']),
        'Original assigned-state coverage missing')
    require(results['rows'][0]['summary'].get('status')=='PASS'
        and results['rows'][0]['summary'].get('backend_calls')==0,'Original qualification gate missing')
    require(owner.get('source_revision')==OLD_SOURCE and owner.get('result_status')=='CLOSED'
        and owner.get('child_exit')==0 and owner.get('reaped') is True
        and owner.get('resource_pass') is True and owner.get('failure') is None,'Original worker closure missing')
    require(audit.get('status')=='COMPLETE' and audit.get('complete') is True
        and audit.get('checked_nodes')==303 and audit.get('scope')=='D_two'
        and audit.get('global_scope')=='D_physical','Old audit scope/coverage missing')
    require(tree_packet.get('case_token')==CASE_TOKEN,'Wrong original tree case')
    floor=audit['higher_fleet_exclusion']
    require(floor.get('status')=='ADMITTED_GE_3_FLOOR' and floor.get('scope')=='physical_ge_3'
        and floor.get('case_token')==CASE_TOKEN,'Old higher-fleet scope missing')
    require(upper_authority.get('status')=='QUALIFIED_TRANSFER'
        and upper_authority.get('case_identity')==CASE_TOKEN
        and upper_authority.get('packet_artifact_revision')=='0cb3c54de6e8e5c391afb37bcbb68ad3a51925ee'
        and upper_authority.get('producer_source_revision')=='425bf35452eb3f5444f20058ad6fd6b540ffed88'
        and upper_authority.get('primal_admitted') is True and upper_authority.get('worker_reaped') is True
        and upper_authority.get('resource_pass') is True and upper_authority.get('producer_exit')==0
        and Q(upper_authority['upper_exact'])==UPPER,'Qualified physical incumbent differs')
    require(Q(floor['lower_bound'])>UPPER,'Admitted higher-fleet floor does not cover the new target')
    nodes=tree_packet['tree']['nodes'];root=tree_packet['tree']['root']
    require(len(nodes)==303 and root in nodes,'Original branch structure missing')
    checked={leaf['id']:leaf for leaf in audit['leaves']}
    require(len(checked)==len(audit['leaves']),'Duplicate old audited leaf')
    seen=set();frontier=[];structure={};stack=[(root,())]
    while stack:
        identifier,decisions=stack.pop()
        require(identifier in nodes and identifier not in seen,'Invalid/shared old node identity')
        seen.add(identifier);node=nodes[identifier];kind=node['kind']
        if kind=='branch':
            mid=node['movement'];children=node['children']
            require(mid not in dict(decisions) and set(children)=={'0','1'} and children['0']!=children['1'],
                'Invalid inherited base branch')
            structure[identifier]=dict(kind='branch',movement=mid,children=dict(children))
            stack.append((children['1'],decisions+((mid,1),)))
            stack.append((children['0'],decisions+((mid,0),)))
        else:
            require(kind in ('bound','infeasible') and identifier in checked,'Unadmitted original frontier leaf')
            old=checked[identifier]
            expected='CERTIFIED_BOUND' if kind=='bound' else 'CERTIFIED_INFEASIBLE'
            require(old['status']==expected,'Old leaf kind/audit mismatch')
            lower=Q(old['lower_bound']) if kind=='bound' else None
            contradiction=Q(old['contradiction']) if kind=='infeasible' else None
            if kind=='infeasible':require(contradiction>0,'Old contradiction not positive')
            frontier.append(dict(leaf_id=identifier,decisions=decisions,status=expected,
                lower_bound=lower,contradiction=contradiction,old_proof_ref=node['certificate_ref']))
            structure[identifier]=dict(kind='admitted_base_leaf',leaf_id=identifier)
    require(seen==set(nodes) and {f['leaf_id'] for f in frontier}==set(checked),'Old frontier not exhaustive')
    epsilon=Q(1,10000)
    return dict(status='SOURCE_BOUND_BASE_ADMITTED',case_token=CASE_TOKEN,old_source=OLD_SOURCE,
        old_control=OLD_CONTROL,artifact_revision=ARTIFACT,input_pins=dict(PINS),
        base_tree=dict(root=root,nodes=structure),frontier=frontier,base_nodes=303,
        floor_ge3=Q(floor['lower_bound']),minimum_fleet=2,fleet_count=2,
        old_global_physical_lower=Q(audit['global_lower_bound']),physical_upper=UPPER,
        epsilon=epsilon,target=UPPER-epsilon,scope='D_two refinements plus admitted physical_ge_3 floor',
        old_numeric_audit_repeated=False,old_search_repeated=False,old_physical_replay_repeated=False)
