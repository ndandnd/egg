"""Pure exact metadata/algebra admission; caller authenticates cached buffers."""
from fractions import Fraction as Q

AUTHORITY_REVISION='c5f056b90ca895786c44f96903cdaafff97fce52'
AUTHORITY_PATH='research-20261029/public_price_witness/TRANSFER_AUTHORITY.json'
PACKET_REVISION='f5ec2aa5770188d173af7297620a5fcea99fef9a'
NAMESPACE='research-20261029/public_price_witness/attempt01'
PACKET_PATH=NAMESPACE+'/MIXTURE.json.gz'
CASE_REVISION='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
CASE_PATH='research-20261029/public_support_resolution/attempt01/case_descriptor.json'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
PINS=dict(authority=(AUTHORITY_REVISION,AUTHORITY_PATH),
          packet=(PACKET_REVISION,PACKET_PATH),case=(CASE_REVISION,CASE_PATH))


def require(ok, message):
    if not ok: raise ValueError(message)


def exact(value):
    require(not isinstance(value,(float,bool)), 'exact rational required')
    return Q(value)


def derive(loads,cbar,H,a,b,epsilon=Q(1,10000)):
    loads,a,b=([exact(v) for v in seq] for seq in (loads,a,b))
    cbar,H,epsilon=map(exact,(cbar,H,epsilon))
    require(len(loads)>0 and len(loads)==len(a)==len(b),'dimensions')
    require(all(v>=0 for v in loads+b) and cbar>=0,'load/curvature/ops sign')
    require(epsilon==Q(1,10000),'fixed epsilon')
    F=sum((at*u+bt*u*u/2 for at,bt,u in zip(a,b,loads)),Q(0))
    require(cbar+F==H,'mixture objective identity')
    p=[at+bt*u for at,bt,u in zip(a,b,loads)]
    k=-sum((bt*u*u/2 for bt,u in zip(b,loads)),Q(0))
    require(F-sum((pt*u for pt,u in zip(p,loads)),Q(0))==k,'tangent constant')
    return dict(mean_loads=loads,cbar=cbar,H=H,a=a,b=b,p=p,k=k,
                epsilon=epsilon,target=H-k-epsilon,
                fleet_count=None,all_bus_counts_retained=True,
                objective_mode='linear',minimum_fleet=2)


def validate_derived(record):
    expected=derive(record['mean_loads'],record['cbar'],record['H'],
                    record['a'],record['b'],record['epsilon'])
    for key,value in expected.items():
        require(record[key]==value,'derived field mismatch: '+key)
    return dict(status='PASS',target=expected['target'])


def admit(authority,packet,coefficients,pins):
    """Decoded inputs only; pins must describe byte-authenticated fixed paths.

    coefficients={'a':exact original stored-float rationals,'b':...} must
    originate in the authenticated semantic source, never packet metadata.
    No component replay or mixture weight optimization is performed.
    """
    require(pins==PINS,'immutable input pins')
    expected=dict(status='ADMITTED_HULL_UPPER',case_token=CASE_TOKEN,
        producer_source_revision='cddd5072be949c36a8f674dd12298503a73407a7',
        producer_control_commit_prefix='61b14412',producer_namespace=NAMESPACE,
        packet_artifact_revision=PACKET_REVISION,case_input_revision=CASE_REVISION,
        case_path=CASE_PATH,mixture_path=PACKET_PATH,
        results_path=NAMESPACE+'/results.json',owner_receipt_path=NAMESPACE+'/owner_receipt.json',
        required_mixture_check_status='PASS',new_component_physical_status='ADMITTED_PRIMAL',
        new_component_strict_physical_replays=1)
    for key,value in expected.items(): require(authority[key]==value,'authority '+key)
    for key in ('all_five_states_delivered_timely','worker_reaped','resource_pass'):
        require(authority[key] is True,'authority '+key)
    for key in ('owner_exit','worker_exit'):
        require(type(authority[key]) is int and authority[key]==0,'authority '+key)
    mixture=packet['mixture'];audit=packet['independent_check']
    require(audit['status']=='PASS','producer mixture check')
    H=exact(authority['upper_bound'])
    require(exact(packet['hull_upper_exact'])==exact(mixture['objective'])==
            exact(audit['objective_exact'])==H,'upper identity')
    right,left=map(exact,(mixture['lambda_right'],mixture['lambda_left']))
    require(0<=right<=1 and left==1-right,'mixture weights')
    result=derive(mixture['loads'],mixture['ops'],H,coefficients['a'],coefficients['b'])
    result.update(weights=dict(left=left,right=right),source_identity=expected,
                  input_pins=dict(PINS),status='ADMITTED_FIXED_PRICE_TRANSFORM',
                  scope='same admitted mixture; no replay or reoptimization')
    validate_derived(result)
    return result


def close_bound(record,linear_lower):
    validate_derived(record)
    linear_lower=exact(linear_lower)
    lower=record['k']+linear_lower
    require(lower<=record['H'],'lower exceeds admitted feasible upper')
    return dict(linear_lower=linear_lower,hull_lower=lower,hull_upper=record['H'],
                width=record['H']-lower,epsilon_met=record['H']-lower<=record['epsilon'])
