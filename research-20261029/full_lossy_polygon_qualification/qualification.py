"""Exact cross-implementation comparison and bounded prospective controls."""
from copy import deepcopy
from fractions import Fraction as Q


def need(ok, message):
    if not ok:
        raise ValueError(message)


def cross(a, b, p):
    return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])


def contains(vertices, point):
    """Membership in a convex hull in its recorded boundary order."""
    if not vertices:
        return False
    if len(vertices) == 1:
        return tuple(vertices[0]) == tuple(point)
    if len(vertices) == 2:
        a, b = vertices
        return cross(a,b,point) == 0 and all(min(a[k],b[k]) <= point[k] <= max(a[k],b[k]) for k in (0,1))
    turns = [cross(vertices[i], vertices[(i+1)%len(vertices)], point) for i in range(len(vertices))]
    if all(t == 0 for t in turns):
        return all(min(v[k] for v in vertices) <= point[k] <= max(v[k] for v in vertices) for k in (0,1))
    return all(t >= 0 for t in turns) or all(t <= 0 for t in turns)


def expected_matchings(spec):
    n = len(spec['a'])
    edges = set(tuple(e) for e in spec['edges'])
    rows = [()]
    for i in range(n):
        expanded = []
        for row in rows:
            expanded.append(row)
            used = {j for _,j in row}
            expanded.extend(row+((i,j),) for j in range(n) if (i,j) in edges and j not in used)
        rows = expanded
    return set(rows)


def compare(spec, reference, physical, analytic):
    # Physical construction already performed exactly one strict replay for
    # every vertex. Do not repeat successful replay or imported calculations.
    need(physical['id'] == analytic['id'] == spec['id'], 'Case identity')
    need(physical['status'] == 'ENUMERATED' and analytic['status'] == 'DERIVED', 'Known completed implementation statuses')
    n = len(spec['a'])
    records = physical['records']
    by_pair = {}
    for record in records:
        pairs = tuple(tuple(e) for e in record['pairs'])
        need(pairs not in by_pair, 'Duplicate reference matching')
        need(record['cardinality'] == len(pairs), 'Reference cardinality identity')
        by_pair[pairs] = record
    need(set(by_pair) == expected_matchings(spec), 'Complete matching denominator')
    need(physical['matching_count'] == len(records), 'Reported matching count')
    need(physical['feasible_count'] == sum(bool(r['vertices']) for r in records), 'Reported feasible matching count')
    rows = analytic['cardinalities']
    need([row['m'] for row in rows] == list(range(n+1)), 'Complete cardinality denominator')
    need(analytic['nu'] == max(map(len,by_pair)), 'Maximum matching cardinality')
    alpha, delta, fee = (Q(spec[k]) for k in ('alpha','delta','fee'))
    total_vertices = 0
    summaries = []
    for row in rows:
        m = row['m']
        group = [r for r in records if r['cardinality'] == m]
        need(row['matching_exists'] == bool(group), 'Matching existence')
        need(row['N'] == 2*n-m and row['c'] == fee*(2*n-m), 'Candidate fleet/cost')
        if not group:
            need(row['status'] == 'NO_MATCHING' and not row['vertices'] and row['r_m'] is None, 'No matching state')
            summaries.append(dict(m=m,status='NO_MATCHING',matchings=0,vertices=0))
            continue
        # Directly enumerate raw mandatory positive battery increments only
        # for independent DP provenance. Reference polygon generation itself
        # never used this aggregate statistic.
        requirements = [(sum((max(Q(0),b['lower']) for b in r['buses']),Q(0)),
                         tuple(tuple(e) for e in r['pairs'])) for r in group]
        best = min(requirements)
        pair = tuple(tuple(e) for e in row['minimizing_matching'])
        need((row['r_m'],pair) == best, 'Minimum matching requirement/provenance')
        selected = by_pair[pair]
        need(row['S_m'] == selected['total_consumption'], 'Common transition total')
        vertices = [tuple(v) for v in row['vertices']]
        need(len(set(vertices)) == len(vertices) and len(vertices) <= 5, 'Complete candidate vertex schema')
        selected_vertices = [(v['C'],v['X']) for v in selected['vertices']]
        need(bool(vertices) == bool(selected_vertices), 'Fixed matching feasibility')
        need(row['status'] == ('FEASIBLE' if vertices else 'INFEASIBLE_RESOURCES'), 'Resource status')
        expected_kind='EMPTY' if not vertices else 'POINT' if selected['dimension']==0 else 'SEGMENT' if selected['dimension']==1 else 'POLYGON'
        need(row['polygon_kind'] == expected_kind, 'Polygon degeneracy metadata')
        need(row['efficient_early_upper'] == min(sum(map(Q,spec['a']),Q(0))/alpha,Q(spec['K'])), 'One-direction efficient upper metadata, not full-polygon maximum E')
        if selected_vertices:
            need(row['efficient_early_threshold'] == min(v['E'] for v in selected['vertices']), 'Efficient lower threshold from full raw polygon')
        need(len(vertices) == len(row['load_cost_images']), 'Affine image denominator')
        for point, image in zip(vertices,row['load_cost_images']):
            C,X = point
            need(contains(selected_vertices,point), 'Whole candidate polygon lacks ONE fixed matching')
            need(all(h['C']*C+h['X']*X <= h['rhs'] for h in row['halfspaces']), 'Candidate own halfspace')
            need(tuple(image) == (C-X,(row['S_m']-alpha*C+X/delta)/alpha,row['c']), 'Candidate affine load/cost image')
        image_hull=[tuple(v[:2]) for v in row['image_hull']]
        images=[tuple(v[:2]) for v in row['load_cost_images']]
        need(len(set(image_hull))==len(image_hull) and all(len(v)==3 and v[2]==row['c'] for v in row['image_hull']), 'Projected hull vertex/cost metadata')
        need(bool(image_hull)==bool(images), 'Projected hull empty state')
        need(all(contains(image_hull,p) for p in images) and all(contains(images,p) for p in image_hull), 'Complete affine-image hull both containments, including lossless collapse')
        for record in group:
            need(record['fleet'] == 2*n-m and record['total_consumption'] == row['S_m'], 'Raw common totals')
            expected_dimension=-1 if not record['vertices'] else 0 if len(record['vertices'])==1 else 1 if len(record['vertices'])==2 else 2
            need(record['dimension']==expected_dimension,'Raw polygon dimension metadata')
            need(record['strict_replayed_vertices'] == len(record['vertices']), 'Per-matching once-replay denominator')
            for vertex in record['vertices']:
                total_vertices += 1
                need(contains(vertices,(vertex['C'],vertex['X'])), 'Raw polygon not contained in candidate')
                need(vertex['ops'] == row['c'], 'Reference operations cost')
        summaries.append(dict(m=m,status=row['status'],matchings=len(group),
                              vertices=len(vertices),single_matching=list(pair)))
    need(physical['strict_replayed_vertices'] == total_vertices, 'Fresh complete replay denominator')
    return dict(status='PASS',matching_count=len(records),cardinality_count=len(rows),
                strict_replayed_vertices=total_vertices,cardinalities=summaries,
                scope='Exact convex polygon containments and one physical matching for each whole candidate polygon; eight literals, no empirical claim')


def controls(reference, candidate):
    spec=dict(id='Q0-charge-loss',B='1',a=['3/4'],b=['3/4'],alpha='1/2',delta='1',
              K='2',H='3',fee='2',d='0',edges=[[0,0]])
    physical=reference.enumerate_physical(spec)
    analytic=candidate.derive(spec)
    good=compare(spec,reference,physical,analytic)
    records=physical['records']
    values={r['cardinality']:min(v['ops']-3*v['E']+v['L'] for v in r['vertices']) for r in records}
    need(values == {0:Q(1,2),1:Q(-3,2)}, 'Hand-derived both-cardinality minima')
    selected=next(r for r in records if r['cardinality']==1)
    anchor=next(v for v in selected['vertices'] if (v['C'],v['X'])==(Q(11,6),Q(1,6)))
    need((anchor['E'],anchor['L'],anchor['ops'])==(Q(5,3),Q(3,2),Q(2)), 'Hand physical anchor')
    rejected=[]
    def rejects(name, action):
        try:
            outcome=action()
            bad=isinstance(outcome,dict) and outcome.get('strict_pass') is False
        except (ValueError,KeyError,IndexError,TypeError,StopIteration):
            bad=True
        need(bad,'Corruption unexpectedly accepted: '+name)
        rejected.append(name)
    def altered_candidate(change):
        a=deepcopy(analytic);change(a);return compare(spec,reference,physical,a)
    def altered_reference(change):
        p=deepcopy(physical);change(p);return compare(spec,reference,p,analytic)
    def altered_witness(change):
        v=deepcopy(anchor);change(v);return reference.replay(spec,selected,v)
    rejects('missing_cardinality',lambda:altered_candidate(lambda a:a['cardinalities'].pop()))
    rejects('missing_matching',lambda:altered_reference(lambda p:p['records'].pop()))
    rejects('wrong_threshold',lambda:altered_candidate(lambda a:a['cardinalities'][1].update(r_m=Q(0))))
    rejects('wrong_efficient_lower_threshold',lambda:altered_candidate(lambda a:a['cardinalities'][1].update(efficient_early_threshold=Q(-1))))
    rejects('wrong_cost',lambda:altered_candidate(lambda a:a['cardinalities'][1].update(c=Q(3))))
    rejects('lost_polygon_vertex',lambda:altered_candidate(lambda a:a['cardinalities'][1]['vertices'].pop()))
    rejects('missing_replay',lambda:altered_reference(lambda p:p.update(strict_replayed_vertices=0)))
    rejects('wrong_reported_load',lambda:altered_witness(lambda v:v.update(E=v['E']+1)))
    rejects('wrong_inventory_energy',lambda:altered_witness(lambda v:v['witness']['terminal'][0].update(energy=Q(1))))
    rejects('early_connector_overlap',lambda:altered_witness(lambda v:v['witness']['early'][1].update(start=Q(1))))
    rejects('missing_terminal_refill',lambda:altered_witness(lambda v:v['witness'].update(terminal=[])))
    rejects('wrong_action_power',lambda:altered_witness(lambda v:v['witness']['early'][0].update(power=Q(3))))
    return dict(status='PASS',spec=spec,reference=physical,candidate=analytic,comparison=good,
                exact_negative_price_values=values,controls=rejected,
                summary=dict(status='PASS',rejected_controls=len(rejected),anchor='Full price value -3/2; D=CH, no support gap'))
