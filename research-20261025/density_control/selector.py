"""Exact common-density CA1 and frozen-cover-plus-CA1 candidate controls."""
from collections import Counter

from egglab import classical_controls as cc

POLICY = 'common-backbone-exactK-CA1-versus-CoverCA1-v1'
ARMS = ('CA1', 'CoverCA1')


def select(case, a, b, arm, *, cover_function, check=lambda: None):
    if arm not in ARMS:
        raise ValueError('Unknown frozen density-control arm')
    check()
    scored = cc.ca1_score(case, a, b)
    check()
    ordinary = cc.select_connections(case, scored['scores'])
    check()
    original = [m.id for m in case.movements]
    flexible = {m.id for m in case.movements if m.kind in ('direct', 'depot')}
    boundaries = set(original)-flexible
    backbone, quota = set(ordinary['backbone_ids']), ordinary['K']
    ordinary_flexible = set(ordinary['retained_movement_ids']) & flexible
    cover = cover_function(case, check=check) if arm == 'CoverCA1' else None
    check()
    if cover is not None and cover['case_identity'] != case.identity():
        raise ValueError('Fresh cover case identity differs')
    cover_flexible = set() if cover is None else set(cover['retained_movement_ids']) & flexible
    if (ordinary['original_movement_ids'] != original or ordinary['M'] != len(flexible)
            or not backbone <= flexible or not cover_flexible <= flexible
            or len(ordinary_flexible) != quota):
        raise ValueError('Existing selector/movement identity differs')
    protected = backbone | cover_flexible
    status = 'selected' if len(protected) <= quota else 'design_failure_cover_union_exceeds_K'
    fill = [mid for mid in ordinary['flexible_order'] if mid not in protected]
    fill = fill[:quota-len(protected)] if status == 'selected' else []
    selected = protected | set(fill) if status == 'selected' else set()
    retained = boundaries | selected if status == 'selected' else set()
    if status == 'selected' and (len(selected) != quota or not backbone <= selected
            or not cover_flexible <= selected or not boundaries <= retained):
        raise ValueError('ExactK/protected/boundary selection invariant failed')
    if arm == 'CA1' and selected != ordinary_flexible:
        raise ValueError('CA1 differs from unchanged ordinary selector')
    features = {row['movement_id']: row for row in scored['features']}
    ranks = {mid: index+1 for index, mid in enumerate(ordinary['flexible_order'])}
    fill_set = set(fill)
    modes = []
    for movement in case.movements:
        check()
        mid, feature = movement.id, features[movement.id]
        modes.append({'movement': mid, 'kind': movement.kind, 'before': movement.before,
            'after': movement.after, 'boundary': mid in boundaries,
            'backbone': mid in backbone, 'cover': mid in cover_flexible,
            'fill': mid in fill_set, 'selected': mid in retained, 'CA1_rank': ranks.get(mid),
            'stress_flag': feature.get('stress_flag'), 'proxy_cost': feature.get('proxy_cost'),
            'margin_kwh': feature.get('margin_kwh'), 'U_kwh': feature.get('U_kwh')})
    counts = {label: dict(Counter(m.kind for m in case.movements if m.id in ids))
        for label, ids in (('declared', set(original)), ('selected', retained),
                           ('backbone', backbone), ('cover', cover_flexible), ('fill', fill_set))}
    union = ordinary_flexible | selected
    return {'policy': POLICY, 'arm': arm, 'status': status, 'case_identity': case.identity(),
        'M': ordinary['M'], 'K': quota, 'backbone_ids': ordinary['backbone_ids'],
        'boundary_ids': [mid for mid in original if mid in boundaries],
        'cover_flexible_ids': sorted(cover_flexible), 'protected_flexible_ids': sorted(protected),
        'fill_order': fill, 'flexible_order': ordinary['flexible_order'],
        'selected_flexible_ids': [mid for mid in original if mid in selected],
        'retained_movement_ids': [mid for mid in original if mid in retained],
        'ordinary_CA1_flexible_ids': [mid for mid in original if mid in ordinary_flexible],
        'declared_movements': len(original), 'retained_movements': len(retained),
        'protected_count': len(protected), 'backbone_count': len(backbone),
        'cover_flexible_count': len(cover_flexible), 'fill_count': len(fill),
        'ordinary_CA1_overlap': {'intersection': len(ordinary_flexible & selected),
            'only_ordinary': len(ordinary_flexible-selected), 'only_arm': len(selected-ordinary_flexible),
            'union': len(union)},
        'backbone_cover_overlap': len(backbone & cover_flexible), 'mode_counts': counts,
        'scorer_policy': scored['policy'], 'existing_selector_policy': ordinary['policy'],
        'existing_selector_hashes': ordinary['hashes'], 'tariff_sha256': scored['tariff_sha256'],
        'physical_feasibility_certified': False, 'bound_certified': False,
        'cover_ledger': cover, 'mode_ledger': modes}
