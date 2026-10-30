"""Independent exact-target semantics and retained-proof adapter; no I/O/solver.

Original multipliers/tangents are proposals. No old value/admission transfers.
The enclosing future worker owns buffer authority, frozen inputs and resources.
"""
import copy
from fractions import Fraction as Q
import math
import re

OLD_ID='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'
TARGET_ID=OLD_ID+'::exact-consumption-v1'
CANONICAL_REV='76c83d55fe2983138da7b87f9d4d7c5fd36e9573'
A=Q(float(.2));BETA=Q(float(1/900))
POLICY=dict(service_distance_kwh_per_km='6/5',travel_distance_kwh_per_m='24/25000',
    elapsed_seconds_kwh='1/225',distance_semantics='exact encoded JSON decimal',
    supply_semantics='unchanged original binary-stored a=.2,b=1/900',parked_depot_draw='0',version='exact-consumption-v1')


def need(ok,message):
    if not ok:raise ValueError(message)


def rational(value,canonical=False):
    need(type(value) in (int,str) or isinstance(value,Q),'Exact rational, not float/bool, required')
    if isinstance(value,str):
        need(len(value)<=32768,'Rational text ceiling')
        need('e' not in value.lower(),'No exponent in rational proof token')
    result=Q(value)
    need(max(result.numerator.bit_length(),result.denominator.bit_length())<=32768,'Rational bit ceiling')
    if canonical:need(type(value) is str and value==str(result) and result>=0,'Canonical nonnegative target-energy token required')
    return result


def decimal(value):
    need(type(value) in (int,str),'Retained JSON-decimal token required')
    if isinstance(value,str):
        need(len(value)<=256,'Decimal text ceiling')
        match=re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE]([+-]?[0-9]+))?',value)
        need(match is not None and (match.group(1) is None or abs(int(match.group(1)))<=1000),'Bounded JSON decimal required')
    result=Q(value)
    need(max(result.numerator.bit_length(),result.denominator.bit_length())<=4096,'Decimal bit ceiling')
    return result


def original_number(value):
    need(type(value) in (int,float),'Original binary descriptor number required')
    need(not isinstance(value,float) or math.isfinite(value),'Finite original number')
    return Q(value)


def seal(value):
    """Keep the returned seal SEPARATELY; never reseal a mutated validation."""
    if isinstance(value,Q):return ('rational',value.numerator,value.denominator)
    if isinstance(value,dict):
        need(all(type(k) is str for k in value),'String dictionary keys required')
        return ('dict',tuple((k,seal(value[k])) for k in sorted(value)))
    if isinstance(value,(tuple,list)):return (type(value).__name__,tuple(seal(x) for x in value))
    if type(value) is float:
        need(math.isfinite(value),'Nonfinite seal value');return ('float',value.hex())
    need(type(value) in (str,int,bool,type(None)),'Unexpected validation type')
    return (type(value).__name__,value)


def _fleet(case):
    """Own target-energy obstruction derivation, including its full evidence."""
    trips=case['trips'];events={};starts=set()
    for t in trips:
        s,e=original_number(t['start_min']),original_number(t['end_min']);starts.add(s)
        events[s]=events.get(s,0)+1;events[e]=events.get(e,0)-1
    active=0;counts=[]
    for moment in sorted(events):
        active+=events[moment]
        if moment in starts:counts.append(dict(time=moment,count=active))
    overlap=max(row['count'] for row in counts)
    ordered=sorted(trips,key=lambda t:(original_number(t['start_min']),original_number(t['end_min']),t['id']))
    disjoint=all(original_number(x['end_min'])<=original_number(y['start_min']) for x,y in zip(ordered,ordered[1:]))
    links=[]
    if disjoint:
        for x,y in zip(ordered,ordered[1:]):
            options=[m for m in case['movements'] if m['before']==x['id'] and m['after']==y['id']]
            links.append(dict(before=x['id'],after=y['id'],movement_ids=[m['id'] for m in options],kinds=[m['kind'] for m in options]))
    missing=disjoint and any(not row['movement_ids'] for row in links)
    direct=disjoint and all(row['movement_ids'] and set(row['kinds'])=={'direct'} for row in links)
    energy=sum((rational(t['energy_kwh'],True) for t in ordered),Q(0))
    usable=original_number(case['battery_kwh'])-original_number(case['reserve_kwh'])
    obstruction=direct and energy>usable
    return dict(minimum_fleet=max(1,overlap,2 if missing or obstruction else 1),half_open_overlap_bound=overlap,
        overlap_counts=counts,chronologically_disjoint=disjoint,consecutive_connections=links,
        missing_consecutive_connection=missing,all_consecutive_options_direct=direct,service_energy=energy,
        usable_initial_above_reserve=usable,no_recharge_energy_obstruction=obstruction)


def _strip_energy(case):
    result=copy.deepcopy(case)
    for trip in result['trips']:trip['energy_kwh']=None
    for move in result['movements']:
        for leg in move['legs']:leg['energy_kwh']=None
    return result


def validate_semantics(document,original,record,original_reconstruct,target_reconstruct,admit_inputs):
    """Compare every target row to an independent explicit energy substitution.

    admit_inputs authenticates cached source-bound document/original/record
    provenance; a serialized True flag is not sufficient. Each reconstruction
    is called ONCE; later consumers use cached_reconstruct below.
    """
    # Reject a full rich payload BEFORE any callback/recursive traversal. The
    # caller's projection may read only selected_depot_id on foreign variants.
    need(isinstance(document,dict) and set(document)=={'native_cases','source_data'},'Authorized selected projection required')
    need(isinstance(document['native_cases'],list) and len(document['native_cases'])==1,'Exactly one projected variant required')
    projected_variant=document['native_cases'][0]
    need(set(projected_variant)=={'selected_depot_id','case_identity','trips','movement_modes','movement_provenance'}
         and projected_variant['selected_depot_id']==15,'Selected-field authority differs')
    need(set(document['source_data'])=={'deadhead_stop_order_source','deadhead_arcs_directed_row_major'},'Shared-field authority differs')
    need(admit_inputs is not None and admit_inputs(document,original,record) is True,'Missing input admission')
    before=(seal(document),seal(original),seal(record))
    old_identity=record['old_identity']
    need(old_identity==OLD_ID or type(old_identity) is str and old_identity.startswith('SYNTHETIC_LITERAL:'),'Old identity domain')
    identity=old_identity+'::exact-consumption-v1'
    need(record['status']=='EXACT_TARGET_DEFINED' and record['identity']==identity and record['policy']==POLICY,'Exact target identity/policy')
    need(record['old_gap_transferred'] is False and record['old_physical_admission_transferred'] is False,'Old success cannot transfer')
    transfer=record['canonical_transfer']
    need(transfer['revision']==CANONICAL_REV and all(transfer.get(k) is True for k in
        ('source_bound_pass','same_rich_input','same_descriptor','time_predicates_complete')) and transfer['blocked_depot_wait_count']==0,
        'Canonical/time/access transfer authority differs')
    selected=[v for v in document['native_cases'] if v['selected_depot_id']==15]
    need(len(selected)==1 and selected[0]['case_identity']==old_identity,'Unique source variant identity')
    variant=selected[0];case=record['case'];n=len(original['trips']);m=len(original['movements'])
    need(1<=n<=37 and m<=5000 and len(case['trips'])==n and len(case['movements'])==m,'Target denominator')
    need(seal(_strip_energy(case))==seal(_strip_energy(original)),'Nonenergy field/type/order changed')
    need(transfer['mode_count']==m and len(variant['trips'])==n and len(variant['movement_modes'])==m,'Source denominator')
    need([r['native']['id'] for r in variant['trips']]==[r['id'] for r in original['trips']]
         and [r['id'] for r in variant['movement_modes']]==[r['id'] for r in original['movements']],'Source index/ID mapping')
    source_trips={r['native']['id']:r for r in variant['trips']};metadata={r['movement_id']:r for r in variant['movement_provenance']}
    need(len(source_trips)==n and len(metadata)==m,'Unique source mappings')
    locations=document['source_data']['deadhead_stop_order_source'];arcs={}
    need(isinstance(locations,list) and 1<=len(locations)<=256 and len(set(locations))==len(locations),'Source location universe')
    for arc in document['source_data']['deadhead_arcs_directed_row_major']:
        pair=(arc['origin_stop_id'],arc['destination_stop_id']);need(pair not in arcs,'Duplicate primitive arc');arcs[pair]=arc
    need(set(arcs)=={(i,j) for i in locations for j in locations},'Complete primitive arc mapping')
    changes=[]
    for old,new in zip(original['trips'],case['trips']):
        source=source_trips[old['id']];s,e=decimal(source['source_times_sec']['start']),decimal(source['source_times_sec']['end'])
        distance=decimal(source['source_distance_km'])
        need(original_number(old['start_min'])*60==s and original_number(old['end_min'])*60==e and e>s and distance>=0,'Service source/time mapping')
        value=Q(6,5)*distance+(e-s)/225
        need(rational(new['energy_kwh'],True)==value,'Changed target service claim')
        changes.append(dict(kind='service',id=old['id'],old_binary_energy=str(original_number(old['energy_kwh'])),exact_energy=str(value)))
    leg_count=0
    for old,new in zip(original['movements'],case['movements']):
        rows=metadata[old['id']]['legs'];need(len(rows)==len(old['legs']),'Source leg denominator')
        for index,(leg,target,source) in enumerate(zip(old['legs'],new['legs'],rows)):
            duration=(original_number(leg['arrive_min'])-original_number(leg['depart_min']))*60
            need(duration>=0 and decimal(source['duration_sec'])==duration and decimal(source['depart_sec'])==original_number(leg['depart_min'])*60
                 and decimal(source['arrive_sec'])==original_number(leg['arrive_min'])*60,'Source leg times')
            if source['leg_role']=='off_depot_stationary_wait':
                need(leg['origin']==leg['destination'] and leg['origin']!='P15','Wait access/location')
                value=duration/225
            else:
                origin,destination=source['origin_stop_id'],source['destination_stop_id'];arc=arcs[origin,destination]
                need(leg['origin']=='P'+str(origin) and leg['destination']=='P'+str(destination)
                     and decimal(arc['time_sec_source'])==duration,'Primitive paired-arc binding')
                distance=decimal(arc['distance_m_source']);need(distance>=0,'Nonnegative source distance')
                value=Q(24,25000)*distance+duration/225
            need(rational(target['energy_kwh'],True)==value,'Changed target leg claim')
            changes.append(dict(kind='leg',id=old['id'],leg=index,old_binary_energy=str(original_number(leg['energy_kwh'])),exact_energy=str(value)))
            leg_count+=1
    need(seal(record['changes'])==seal(changes) and seal(record['denominators'])==seal(dict(services=n,modes=m,legs=leg_count)),'Change ledger differs')
    old_ledger=original_reconstruct(original);fresh=target_reconstruct(case)
    need(isinstance(old_ledger,tuple) and isinstance(fresh,tuple) and len(old_ledger)==len(fresh)==6,'Semantic six-tuple API')
    variables,rows,intervals,operations,loads,_=old_ledger;expected_rows=copy.deepcopy(rows)
    for j,move in enumerate(case['movements']):
        for k,leg in enumerate(move['legs']):
            name='leg_'+str(j)+'_'+str(k);sense,rhs,coefficients=expected_rows[name];y='y'+str(j)
            need(sense=='=' and rhs==0 and coefficients.get(y,Q(0))==original_number(original['movements'][j]['legs'][k]['energy_kwh']),
                 'Original leg row family differs')
            changed=dict(coefficients);value=rational(leg['energy_kwh'],True)
            if value:changed[y]=value
            else:changed.pop(y,None)
            expected_rows[name]=(sense,rhs,changed)
    for i,trip in enumerate(case['trips']):
        name='service_energy_'+str(i);sense,rhs,coefficients=expected_rows[name]
        need(sense=='=' and rhs==original_number(original['trips'][i]['energy_kwh']),'Original service row family differs')
        expected_rows[name]=(sense,rational(trip['energy_kwh'],True),dict(coefficients))
    fleet=_fleet(case);sense,_,coefficients=expected_rows['derived_minimum_fleet']
    need(sense=='>=','Original fleet row family differs')
    expected_rows['derived_minimum_fleet']=(sense,Q(fleet['minimum_fleet']),dict(coefficients))
    expected=(variables,expected_rows,intervals,operations,loads,fleet)
    need(seal(fresh)==seal(expected),'Target semantic callback changes an unapproved row/bound/objective/fleet proof')
    need((seal(document),seal(original),seal(record))==before,'Source/target mutated during semantic validation')
    return dict(status='VALIDATED_TARGET_SEMANTICS',identity=identity,old_identity=old_identity,case=copy.deepcopy(case),
        ledger=copy.deepcopy(fresh),policy=copy.deepcopy(POLICY),denominators=dict(services=n,modes=m,legs=leg_count),
        row_substitution_scope='Only leg y-energy, service RHS and independently refreshed minimum-fleet RHS',
        old_gap_transferred=False)


def cached_reconstruct(validated,validation_seal):
    need(seal(validated)==validation_seal and validated['status']=='VALIDATED_TARGET_SEMANTICS','Invalid/mutated validation')
    case_seal=seal(validated['case'])
    def callback(case):
        need(seal(validated)==validation_seal and seal(case)==case_seal,'Unvalidated/mutated target descriptor')
        return copy.deepcopy(validated['ledger'])
    return callback


def stripped_certificate(certificate,infeasible=False):
    """Whitelist proof inputs; deliberately discard ALL old scalar/status fields."""
    need(isinstance(certificate,dict) and isinstance(certificate.get('multipliers'),dict),'Explicit multiplier proposal required')
    multipliers={}
    for name,value in certificate['multipliers'].items():
        need(type(name) is str,'Multiplier row name');multipliers[name]=rational(value)
    result=dict(multipliers=multipliers)
    if not infeasible:
        proposed=certificate.get('tangent_loads');need(isinstance(proposed,list) and len(proposed)<=1000,'Explicit tangent proposal')
        result['tangent_loads']=[rational(x) for x in proposed]
    return result


def graft_proposals(original,refinement,expected=(303,152,72)):
    """Preserve fixed topology; old scalar comparison chooses a proposal ONLY."""
    nodes=original['tree']['nodes'];locals_=refinement['refinements'];base,fringe,added=expected
    leaves={key for key,value in nodes.items() if value['kind']!='branch'}
    need(len(nodes)==base and len(leaves)==fringe and set(locals_)==leaves,'Base/frontier identity denominator')
    need(sum(len(t['nodes'])-1 for t in locals_.values())==added,'Fixed new-child denominator')
    result={}
    def local_name(leaf,key):return 'local/'+str(len(leaf))+':'+leaf+'/'+key
    def target(key):
        need(key in nodes,'Missing original child')
        return local_name(key,locals_[key]['root']) if key in leaves else 'old/'+key
    for key,node in nodes.items():
        need(type(key) is str,'Original node identity')
        if node['kind']=='branch':
            need(set(node['children'])=={'0','1'},'Both old children required')
            result['old/'+key]=dict(kind='branch',movement=node['movement'],children={v:target(child) for v,child in node['children'].items()});continue
        need(node['kind'] in ('bound','infeasible'),'Old leaf needs algebraic proposal')
        old=original['proofs'][node['certificate_ref']]['certificate'];tree=locals_[key]
        need(tree['root'] in tree['nodes'],'Missing local root')
        if node['kind']=='infeasible':
            need(len(tree['nodes'])==1 and tree['nodes'][tree['root']]['kind'] in ('base_bound','base_infeasible'),'Old contradiction cannot be replaced by a new branch')
        for local_key,entry in tree['nodes'].items():
            need(type(local_key) is str,'Local node identity');kind=entry['kind'];name=local_name(key,local_key)
            if kind=='branch':
                need(set(entry['children'])=={'0','1'} and all(child in tree['nodes'] for child in entry['children'].values()),'Both new children required')
                result[name]=dict(kind='branch',movement=entry['movement'],children={v:local_name(key,child) for v,child in entry['children'].items()});continue
            if kind in ('base_bound','base_infeasible'):
                need(entry['base_leaf_id']==key and (kind!='base_infeasible' or node['kind']=='infeasible'),'Foreign/unproved inherited proposal')
                kind=node['kind'];selected=old
            else:
                need(kind in ('bound','infeasible'),'No open/native-only leaf')
                selected=refinement['proofs'][entry['certificate_ref']]['certificate']
                if kind=='bound' and node['kind']=='bound' and rational(old['claimed_lower'])>rational(selected['claimed_lower']):selected=old
            result[name]=dict(kind=kind,certificate=stripped_certificate(selected,kind=='infeasible'))
    need(len(result)==base+added,'Combined fixed-node denominator')
    return dict(root=target(original['tree']['root']),nodes=result)


def verify_retained_tree(validated,validation_seal,original,refinement,treechecker,limits,admit_proposals):
    """One complete target check; a failed old contradiction is UNRESOLVED."""
    need(seal(validated)==validation_seal,'Target validation mutated')
    need(admit_proposals is not None and admit_proposals(original,refinement) is True,'Missing fixed artifact admission')
    need(original['case_token']==validated['old_identity'],'Original tree case identity')
    need(limits.get('nodes')==375 and limits.get('depth')==375,'Fixed375-node checking allowance required')
    proof=graft_proposals(original,refinement)
    callback=cached_reconstruct(validated,validation_seal);case=validated['case']
    context=treechecker.prepare(case,callback,mode='quadratic',fleet_count=2,case_token=validated['identity'])
    fleet=validated['ledger'][5]
    if fleet['minimum_fleet']<2:
        return dict(status='UNRESOLVED',reason='Target zero/one-bus exclusion unavailable',target_identity=validated['identity'])
    floor=dict(case_token=validated['identity'],minimum_fleet=3,proof_kind='quadratic_affine_service_floor',scope='physical_ge_3',
        lower_bound=3*original_number(case['vehicle_cost'])+A*sum((rational(t['energy_kwh'],True) for t in case['trips']),Q(0))/original_number(case['efficiency']))
    audit=treechecker.verify_tree(context,proof,exclusion=floor,admit_transfer=lambda x:x is floor,limits=limits)
    need(seal(validated)==validation_seal,'Target mutated during proof checking')
    complete=audit.get('status')=='COMPLETE' and audit.get('complete') is True and isinstance(audit.get('global_lower_bound'),Q)
    return dict(status='COMPLETE_TARGET_BOUND' if complete else 'UNRESOLVED',target_identity=validated['identity'],
        lower=audit['global_lower_bound'] if complete else None,audit=audit,
        reason=None if complete else 'Retained target proof incomplete/invalid; no retry, branch change or old Farkas status rescue',
        physical_only_not_CH=True,old_claimed_scalars_used_as_proof=False)


def _point(point,identity,admit_point):
    need(admit_point is not None and admit_point(point) is True,'New point lacks independent admission binding')
    need(point['status']=='ADMITTED_TARGET_PRIMAL' and point['target_identity']==identity,'Wrong/unadmitted target point')
    replay=point['replay'];need(all(replay.get(k) is True for k in ('strict_pass','physical_strict_pass','objective_is_certified_physical_upper')),'Missing fresh strict target replay')
    loads=tuple(map(rational,point['loads_exact']));ops=rational(point['ops_exact']);objective=rational(point['objective_exact'])
    need(len(loads)==30 and all(x>=0 for x in loads),'Complete charge-only load vector')
    need(tuple(map(rational,point['a_exact']))==(A,)*30 and tuple(map(rational,point['b_exact']))==(BETA,)*30,'Original binary supply changed')
    need(type(point['fleet_count']) is int and point['fleet_count']==2 and ops==200,'Frozen two-route physical operating cost')
    need(tuple(map(rational,replay['loads_exact']))==loads and rational(replay['ops_exact'])==ops
         and rational(replay['objective_exact'])==objective,'Fresh replay/point mismatch')
    need(objective==ops+sum((A*x+BETA*x*x/2 for x in loads),Q(0)),'Changed target objective claim')
    return loads,ops,objective


def check_mixture(left,right,lambda_left,lambda_right,target_identity,admit_point,claimed_upper=None,*,weight_record=None,admit_weights=None):
    need(target_identity==TARGET_ID,'Explicit production target identity required')
    x,cx,ux=_point(left,target_identity,admit_point);y,cy,uy=_point(right,target_identity,admit_point)
    wl,wr=rational(lambda_left),rational(lambda_right);need(wl>=0 and wr>=0 and wl+wr==1,'Frozen mixture weights')
    need(weight_record is not None and admit_weights is not None and admit_weights(weight_record) is True,
         'Frozen historical weight lacks source-bound admission')
    need(wl==rational(weight_record['lambda_left']) and wr==rational(weight_record['lambda_right']),
         'Weights differ from the frozen historical proposal')
    loads=tuple(wl*a+wr*b for a,b in zip(x,y));ops=wl*cx+wr*cy
    upper=ops+sum((A*z+BETA*z*z/2 for z in loads),Q(0))
    if claimed_upper is not None:need(rational(claimed_upper)==upper,'Old/altered mixture value cannot transfer')
    return dict(status='ADMITTED_TARGET_MIXTURE',target_identity=target_identity,loads=loads,ops=ops,upper=upper,
        physical_upper=min(ux,uy),lambda_left=wl,lambda_right=wr,old_value_or_KKT_transferred=False)


def conclude(bound,mixture):
    need(bound['status']=='COMPLETE_TARGET_BOUND' and mixture['status']=='ADMITTED_TARGET_MIXTURE','Incomplete new target certificate')
    need(bound['target_identity']==mixture['target_identity']==TARGET_ID,'Target mismatch')
    lower,upper=bound['lower'],mixture['upper']
    need(isinstance(lower,Q) and lower<=mixture['physical_upper'],'Target lower contradicts admitted physical upper')
    return dict(status='POSITIVE_TARGET_GAP_CERTIFIED' if lower>upper else 'TARGET_GAP_UNRESOLVED',
        target_identity=TARGET_ID,physical_lower=lower,hull_upper=upper,gap_lower=lower-upper,
        physical_upper=mixture['physical_upper'],exact_optima_known=False,old_model_result_unchanged=True)


def literal_qualification():
    """Minimal NEW parser/claim/identity adapter literals, never run on import."""
    controls=[]
    def reject(name,action):
        try:action()
        except (ValueError,KeyError,TypeError,ZeroDivisionError):controls.append(dict(id=name,rejected=True))
        else:raise ValueError('Literal corruption accepted: '+name)
    need(rational('1/3',True)==Q(1,3),'Rational parser anchor')
    for name,value in [('float-energy',.5),('bool-energy',True),('decimal-not-canonical','0.5'),
                       ('negative-energy','-1/3'),('huge-rational-exponent','1e999999999')]:
        reject(name,lambda value=value:rational(value,True))
    old=dict(multipliers={'row':'2'},tangent_loads=['0']*30,claimed_lower='UNTRUSTED_OLD_SCALAR',
             claimed_contradiction='UNTRUSTED_OLD_CONTRADICTION',verified=True)
    clean=stripped_certificate(old)
    need(set(clean)=={'multipliers','tangent_loads'} and clean['multipliers']=={'row':Q(2)},'Old scalar/status stripping')
    controls.append(dict(id='old-scalars-not-proof-inputs',passed=True))
    def point(load):
        values=[Q(load)]+[Q(0)]*29;ops=Q(200);objective=ops+A*load+BETA*load*load/2
        replay=dict(strict_pass=True,physical_strict_pass=True,objective_is_certified_physical_upper=True,
                    loads_exact=values,ops_exact=ops,objective_exact=objective)
        return dict(status='ADMITTED_TARGET_PRIMAL',target_identity=TARGET_ID,loads_exact=values,
            ops_exact=ops,objective_exact=objective,fleet_count=2,a_exact=[A]*30,b_exact=[BETA]*30,replay=replay)
    left,right=point(Q(0)),point(Q(2));weights=dict(lambda_left='1/2',lambda_right='1/2')
    admitted=lambda item:item is left or item is right
    admitted_weight=lambda item:item is weights
    def mix(x=left,y=right,identity=TARGET_ID,wl='1/2',claimed=None):
        return check_mixture(x,y,wl,'1/2',identity,admitted,claimed,weight_record=weights,admit_weights=admitted_weight)
    answer=mix();need(answer['upper']==200+A+BETA/2,'New target mixture anchor')
    reject('wrong-target-identity',lambda:mix(identity=OLD_ID))
    changed=copy.deepcopy(right);changed['objective_exact']=0
    def corrupt_claim():
        return check_mixture(left,changed,'1/2','1/2',TARGET_ID,lambda item:item is left or item is changed,
                             weight_record=weights,admit_weights=admitted_weight)
    reject('changed-new-objective-claim',corrupt_claim)
    reject('old-mixture-value-rejected',lambda:mix(claimed='0'))
    reject('weight-not-source-admitted',lambda:check_mixture(left,right,'1/2','1/2',TARGET_ID,admitted))
    reject('foreign-point-admission',lambda:mix(y=copy.deepcopy(right)))
    return dict(status='PASS',controls=controls,anchors=2,native_calls=0,
        scope='New pure parser/proposal/mixture adapter controls; MOCK admissions, no public input/proof recheck')
