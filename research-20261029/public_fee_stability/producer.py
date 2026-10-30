"""Thin exact fee interval producer and closed-metadata adapter; no I/O."""
from fractions import Fraction as Q

TREE='ef0e08203dba5ac2ddcaff6bd8639cc9a70677b9'
PRICE='f5ec2aa5770188d173af7297620a5fcea99fef9a'
CASE='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
TSOURCE='6a171357b65254b52cade63ed95dcce798485f36'
PSOURCE='cddd5072be949c36a8f674dd12298503a73407a7'

def need(ok,reason):
    if not ok:raise ValueError(reason)

def closed(result,owner,worker,source,assigned,status):
    need(owner['source_revision']==source and owner['child_exit']==0 and owner['reaped'] is True
         and owner.get('failure') in (None,'') and owner['resource_pass'] is True,'Closed owner admission')
    need(result['status']==status and worker['status']==status and result['resource_pass'] is True and worker['resource_pass'] is True,
         'Closed resource/result admission')
    need([r['id'] for r in result['rows']]==assigned and all(r['status']=='DELIVERED' for r in result['rows']),
         'Closed assigned denominator')

def project(data):
    """Access only admitted outcome/operations/weight/floor metadata, never routes/loads."""
    tr,pr=data['tree_results'],data['price_results']
    closed(tr,data['tree_owner'],data['tree_worker'],TSOURCE,
           ['Q0','PUBLIC_TREE','INDEPENDENT_TREE_CHECK'],'CLOSED')
    closed(pr,data['price_owner'],data['price_worker'],PSOURCE,
           ['Q0','FIXED_PRICE_LP','EXACT_PRIMAL','FIXED_PRICE_DUAL','MIXTURE'],'COMPLETED')
    trows={r['id']:r['summary'] for r in tr['rows']}
    prows={r['id']:r['summary'] for r in pr['rows']}
    need(trows['Q0']['status']=='PASS' and prows['Q0']['qualification_status']=='PASS','Closed Q0')
    need(prows['EXACT_PRIMAL']['primal_status']=='ADMITTED_PRIMAL'
         and prows['FIXED_PRICE_DUAL']['dual_status']=='CERTIFIED_FIXED_TOPOLOGY_OPTIMUM','Component admission')
    authority=data['authority']
    expected=dict(status='ADMITTED_HULL_UPPER',producer_source_revision=PSOURCE,
        producer_control_commit_prefix='61b14412',packet_artifact_revision=PRICE,
        producer_namespace='research-20261029/public_price_witness/attempt01',
        case_input_revision=CASE,case_token=TOKEN,required_mixture_check_status='PASS',
        new_component_physical_status='ADMITTED_PRIMAL',new_component_strict_physical_replays=1,
        owner_exit=0,worker_exit=0,worker_reaped=True)
    need(all(authority.get(k)==v for k,v in expected.items()),'Price authority identity')
    need(authority['all_five_states_delivered_timely'] is True and authority['resource_pass'] is True,'Price authority closeout')
    audit=data['audit']
    need(audit['status']=='COMPLETE' and audit['complete'] is True
         and audit['scope']=='D_two' and audit['global_scope']=='D_physical'
         and audit['positive_gap_certified'] is True,'Global physical coverage')
    summary=trows['INDEPENDENT_TREE_CHECK']
    need(summary['status']=='COMPLETE' and summary['complete'] is True and summary['positive_gap_certified'] is True,'Compact tree coverage')
    lower=Q(summary['global_lower_bound']);upper=Q(authority['upper_bound'])
    need(lower==Q(audit['global_lower_bound']) and lower>upper,'Transferred strict lower')
    need(all(Q(v)==upper for v in (audit['supplied_target'],summary['supplied_target'],prows['MIXTURE']['hull_upper_exact'])),
         'Cross-package target identity')
    floor=audit['higher_fleet_exclusion']
    need(floor['status']=='ADMITTED_GE_3_FLOOR' and floor['scope']=='physical_ge_3'
         and floor['case_token']==TOKEN,'Typed algebraic physical floor')
    # computed_affine_floor was independently reconstructed as3*f0+a*service/eta.
    # Do NOT shift an arbitrary stored higher-fleet optimum for negative tau.
    three=Q(floor['computed_affine_floor'])
    need(three>=300 and Q(floor['lower_bound'])<=three,'Affine floor identity/domain')
    mix=data['mixture'];m=mix['mixture']
    need(mix['independent_check']['status']=='PASS' and Q(mix['hull_upper_exact'])==upper
         and Q(m['objective'])==upper,'Qualified mixture identity')
    w=Q(m['lambda_right']);need(Q(m['lambda_left'])==1-w and 0<=w<=1,'Mixture weights')
    ops0,ops1=Q(data['incumbent']['ops']),Q(data['response']['ops'])
    n0,n1=ops0/100,ops1/100
    need(all(n.denominator==1 and n>=2 for n in (n0,n1)),'Fee-only component counts')
    mixed=Q(m['ops']);need(mixed==(1-w)*ops0+w*ops1,'Transferred operating mixture')
    a=dict(tree_source=TSOURCE,tree_control='6bdcf254',tree_artifact=TREE,
           mixture_source=PSOURCE,mixture_control='61b14412',mixture_artifact=PRICE,
           descriptor_revision=CASE,case_token=TOKEN,supply_token='original-binary-a-b-30interval',
           physics_token='original-charge-only-depot15-case',original_fee=100,tree_L2=lower,
           tree_target_U=upper,mixture_U=upper,minimum_fleet=2,L3=three,
           three_plus_algebraic_floor=True)
    for key in ('descriptor_revision','case_token','supply_token','physics_token'):
        a['tree_'+key]=a[key];a['mixture_'+key]=a[key]
    for key in ('tree_complete','resource_pass','all_states_delivered','source_bound_closeout',
                'components_admitted','full_replenishment','nonnegative_nonfee_costs',
                'nonnegative_movement_energy','nonnegative_quadratic','fee_only_ops','unchanged_feasibility'):
        a[key]=True
    return dict(f0=100,L2=lower,U=upper,tau0=0,
        mixture=dict(w=w,N0=n0,N1=n1,ops0=ops0,ops1=ops1,mixed_ops=mixed),
        floor=dict(kind='three_plus',L3=three),authority=a)

def propose(fields):
    """Independent direct affine-halfline intersection, checked by checker.check."""
    f=Q(fields['f0']);m=fields['mixture'];w=Q(m['w'])
    n=(1-w)*Q(m['N0'])+w*Q(m['N1']);u=Q(fields['U'])
    inequalities=[(Q(fields['L2'])-u,2-n),(Q(fields['floor']['L3'])-u,3-n)]
    lower=[(-f,True)];upper=[];empty=False
    for a,b in inequalities:
        if b>0:lower.append((-a/b,False))
        elif b<0:upper.append((-a/b,False))
        elif a<=0:empty=True
    lo=max(x for x,_ in lower);lc=all(c for x,c in lower if x==lo)
    hi=min((x for x,_ in upper),default=None)
    hc=all(c for x,c in upper if x==hi) if hi is not None else False
    empty=empty or (hi is not None and (lo>hi or (lo==hi and not(lc and hc))))
    return dict(empty=empty,lower=lo,lower_closed=lc,upper=hi,upper_closed=hc)
