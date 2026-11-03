"""Pure selected-depot metadata projection; caller authenticates input buffers."""
from fractions import Fraction as Q

RICH_REVISION='2f386362aa241a8a4f197a88a50fa150b6d47d9c'
RICH_PATH='data/public/sistig_26088190_v1/hildenbrand_native_cases.json'
DESCRIPTOR_REVISION='253c1e29295e766b3889fc8f5c28d9808e00b3d6'
DESCRIPTOR_PATH='research-20261029/public_support_resolution/attempt01/case_descriptor.json'
OD_REVISION='6f87f052c1a6e30ffb89a984743514e0b2744aa1'
CASE_TOKEN='1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'


def need(ok,message):
    if not ok:raise ValueError(message)


def project(document,descriptor,od_transfer,expected_services=37,expected_case_identity=CASE_TOKEN):
    """No triangles, plans or nonselected variant contents are inspected.

    Runner binds od_transfer to the complete closed receipt and SAME rich bytes;
    these booleans are not self-authenticating public evidence.
    """
    need(od_transfer['revision']==OD_REVISION and od_transfer['source_bound_pass'] is True
         and od_transfer['same_rich_input'] is True,'source-bound prior OD transfer')
    chosen=[]
    for variant in document['native_cases']:
        if variant['selected_depot_id']==15:chosen.append(variant)
    need(len(chosen)==1,'unique selected depot15')
    variant=chosen[0]
    need(variant['case_identity']==expected_case_identity,'selected case identity')
    need(expected_case_identity==CASE_TOKEN or (isinstance(expected_case_identity,str)
         and expected_case_identity.startswith('SYNTHETIC_LITERAL:')),'explicit literal identity override')
    need(type(expected_services) is int and 1<=expected_services<=37,'service limit')
    need(len(variant['trips'])==len(descriptor['trips'])==expected_services,'complete service denominator')
    source=document['source_data'];locations=list(source['deadhead_stop_order_source'])
    need(0<len(locations)<=256 and len(set(locations))==len(locations),'location denominator')
    need(len(source['deadhead_arcs_directed_row_major'])==len(locations)**2,'OD denominator')
    policy=document['modeling_assumptions']
    return dict(variant=variant,descriptor=descriptor,locations=locations,
        arcs=source['deadhead_arcs_directed_row_major'],
        stops=[dict(id=s['id'],b_depot=s['b_depot']) for s in source['stops']],
        source_field_semantics=document['source_field_semantics'],
        modeling_assumptions={k:policy[k] for k in ('time_horizon','terminal_open_sec','departure_policies',
            'depot_idle_auxiliary','direct_wait_policy')},od_transfer=dict(od_transfer),
        expected_services=expected_services,
        expected_case_identity=expected_case_identity,
        scope='Selected depot15 canonical/provenance metadata only; no physical or energy/path dominance claim')
