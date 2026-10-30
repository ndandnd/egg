"""Pure candidate classical ranking and common exact-cardinality selection.

No backend, labels, assets, fixture generation, caching or clock reset. Callers
must charge validation, backbone construction, scoring and selection to the arm.
CA1 proxies/stress flags are ranking conventions, never feasibility or bounds.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import math
from numbers import Real

TAU_KWH = 1e-6
SELECTOR_POLICY = 'common-priceblind-top3-exact30-v1'
SCORER_POLICY = 'ca1-proportional-charging-proxy-v1'
LEDGER_CONVENTION = 'scalar-features-period-capacity-sha256-v1'
_FLEXIBLE = ('direct', 'depot')


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False,
                                    separators=(',',':')).encode()).hexdigest()


def _numbers(values, size, name, *, nonnegative=False):
    values = list(values)
    if (len(values) != size or any(isinstance(v,bool) or not isinstance(v,Real)
            or not math.isfinite(v) or nonnegative and v < 0 for v in values)):
        raise ValueError('Invalid '+name+' dimensions or finite numeric values')
    return [float(v) for v in values]


def _validate(case):
    from egglab.native_recharge import validate_case
    validate_case(case)
    ids = [m.id for m in case.movements]
    if (any(not isinstance(value,str) or not value for value in ids)
            or any(not isinstance(t.id,str) or not t.id for t in case.trips)):
        raise ValueError('Require nonempty string movement and trip IDs')
    return ids


def select_connections(case, scores):
    """Retain all boundaries, common price-blind B, and exactly K flexible edges.

    Return an audit/mask in original movement order; never mutate the full case.
    The retained identity describes that mask, not a feasibility certificate.
    """
    ids = _validate(case)
    scores = _numbers(scores,len(ids),'scores')
    from experiments.codex_offline_rank import heuristic
    backbone_scores = _numbers(heuristic(case),len(ids),'backbone scores')
    flexible = [i for i,m in enumerate(case.movements) if m.kind in _FLEXIBLE]
    backbone_order = sorted(flexible,key=lambda i:(-backbone_scores[i],ids[i]))
    incoming, outgoing, backbone = {}, {}, set()
    for i in backbone_order:
        movement = case.movements[i]
        for counts, trip in ((incoming,movement.after),(outgoing,movement.before)):
            if counts.get(trip,0) < 3:
                backbone.add(i)
                counts[trip] = counts.get(trip,0)+1
    M = len(flexible)
    K = min(M,max((3*M+9)//10,len(backbone)))
    order = sorted(flexible,key=lambda i:(-scores[i],ids[i]))
    fill = [i for i in order if i not in backbone][:K-len(backbone)]
    kept = backbone | set(fill) | {i for i,m in enumerate(case.movements) if m.kind not in _FLEXIBLE}
    mask = [i in kept for i in range(len(ids))]
    retained = [value for i,value in enumerate(ids) if mask[i]]
    backbone_ids = sorted(ids[i] for i in backbone)
    fill_ids = [ids[i] for i in fill]
    if sum(mask[i] for i in flexible) != K:
        raise ValueError('Exact-cardinality selection invariant failed')
    reduced = replace(case,movements=tuple(m for i,m in enumerate(case.movements) if mask[i]))
    restricted_identity = reduced.identity()
    return {'policy':SELECTOR_POLICY,'case_identity':case.identity(),
            'retained_case_identity':restricted_identity,'restricted_identity':restricted_identity,
            'original_movement_ids':ids,
            'retained_movement_ids':retained,'retained_mask':mask,'backbone_ids':backbone_ids,
            'fill_ids':fill_ids,'flexible_order':[ids[i] for i in order],
            'M':M,'backbone_count':len(backbone),'K':K,'exposure_slots':K-len(backbone),
            'zero_exposure':K==len(backbone),
            'hashes':{'original_ids':_hash(ids),'retained_ids':_hash(retained),
                      'backbone_ids':_hash(backbone_ids),'mask':_hash(mask),
                      'scores':_hash(scores),'backbone_scores':_hash(backbone_scores)}}


def restrict_case(case, scores):
    """Apply the common selector once, preserving all other native case fields."""
    ledger = select_connections(case,scores)
    restricted = replace(case,movements=tuple(m for m,keep in zip(
        case.movements,ledger['retained_mask']) if keep))
    if restricted.identity() != ledger['restricted_identity']:
        raise ValueError('Restricted case identity differs from selection ledger')
    return restricted, ledger


def _slices(case):
    """Merge contiguous resource and market partitions without solver compilation."""
    slices, resource, period, lo = [], 0, 0, case.market_edges_min[0]
    while period < len(case.market_edges_min)-1:
        r = case.resources[resource]
        hi = min(r.end_min,case.market_edges_min[period+1])
        rate = min(r.per_bus_kw,r.grid_kw) if r.connectors else 0.
        slices.append((lo,hi,period,rate))
        lo = hi
        if hi == r.end_min:
            resource += 1
        if hi == case.market_edges_min[period+1]:
            period += 1
    return slices


def _capacity_by_period(case, movement, slices=None):
    """Single-vehicle grid kWh in the declared depot_split gap only.

    This helper assumes validated native inputs. It ignores fleet contention.
    Direct and boundary movements have no intermediate capacity in CA1.
    """
    terms = [[] for _ in range(len(case.market_edges_min)-1)]
    if movement.kind == 'depot':
        lo = movement.legs[movement.depot_split-1].arrive_min
        hi = movement.legs[movement.depot_split].depart_min
        for start,end,period,rate in (_slices(case) if slices is None else slices):
            duration = max(0.,min(hi,end)-max(lo,start))
            if duration:
                terms[period].append(duration/60.*rate)
    return [math.fsum(values) for values in terms]


def _proportional_proxy(x, weights, a, b):
    """Proportional-fill total-cost proxy; demand is deliberately not clipped."""
    total = math.fsum(weights)
    if x == 0 or total == 0:
        return 0.
    q = [x*weight/total for weight in weights]
    return math.fsum(math.fsum((aa*value,bb*value*value/2.))
                     for aa,bb,value in zip(a,b,q))


def _finite_features(value):
    if isinstance(value,dict):
        return all(_finite_features(v) for v in value.values())
    if isinstance(value,(list,tuple)):
        return all(_finite_features(v) for v in value)
    return not isinstance(value,float) or math.isfinite(value)


def ca1_score(case, a, b):
    """Score original movement order, returning scalar features and audit hashes.

    Flexible order is ascending (stress, proxy, -margin, -U, ID); scores are
    descending integers M..1. Boundaries score zero and are explicitly unranked.
    Capacity vectors are hashed, not retained in the scalar ledger. Reconstruct
    them from the frozen case and this policy; no outcome/feasibility label is used.
    """
    ids = _validate(case)
    periods = len(case.market_edges_min)-1
    a = _numbers(a,periods,'linear tariff a')
    b = _numbers(b,periods,'curvature tariff b',nonnegative=True)
    C = math.fsum((case.battery_kwh,-case.reserve_kwh))
    eta = case.efficiency
    durations = [end-start for start,end in zip(case.market_edges_min,case.market_edges_min[1:])]
    slices = _slices(case)
    trips = {t.id:t for t in case.trips}
    features, keys = [], {}
    for i,m in enumerate(case.movements):
        row = {'movement_id':m.id,'kind':m.kind,'boundary':m.kind not in _FLEXIBLE}
        if row['boundary']:
            row['ranked'] = False
            features.append(row)
            continue
        Ei, Ej = trips[m.before].energy_kwh, trips[m.after].energy_kwh
        Ee = math.fsum(leg.energy_kwh for leg in m.legs)
        de = math.fsum(leg.arrive_min-leg.depart_min for leg in m.legs)
        S = math.fsum((Ei,Ee,Ej))
        D = max(0.,math.fsum((S,-C)))
        capacity = _capacity_by_period(case,m,slices)
        grid_capacity = math.fsum(capacity)
        U = eta*grid_capacity
        margin = math.fsum((C,U,-S))
        if m.kind == 'depot':
            pre = math.fsum(leg.energy_kwh for leg in m.legs[:m.depot_split])
            post = math.fsum(leg.energy_kwh for leg in m.legs[m.depot_split:])
            residuals = {'predepot':math.fsum((Ei,pre,-C)),
                         'postdepot':math.fsum((post,Ej,-C)),
                         'capacity':math.fsum((D,-U))}
            lo, hi = m.legs[m.depot_split-1].arrive_min, m.legs[m.depot_split].depart_min
            replenishment = _proportional_proxy(D/eta,capacity,a,b)
        else:
            residuals = {'direct':math.fsum((S,-C))}
            lo, hi, replenishment = None, None, 0.
        remaining = max(0.,math.fsum((Ee,-D)))/eta
        movement_proxy = _proportional_proxy(remaining,durations,a,b)
        deadhead_proxy = case.deadhead_cost_per_min*de
        proxy = math.fsum((replenishment,movement_proxy,deadhead_proxy))
        row.update(ranked=True,energy_i_kwh=Ei,energy_j_kwh=Ej,movement_energy_kwh=Ee,
                   leg_minutes=de,usable_battery_kwh=C,window_start_min=lo,window_end_min=hi,
                   total_grid_capacity_kwh=grid_capacity,capacity_by_period_sha256=_hash(capacity),
                   U_kwh=U,D_kwh=D,margin_kwh=margin,stress_residuals_kwh=residuals,
                   borderline_residuals_kwh={key:value for key,value in residuals.items()
                                            if -TAU_KWH <= value <= TAU_KWH},
                   stress_flag=any(value > TAU_KWH for value in residuals.values()),
                   capacity_shortfall_kwh=max(0.,math.fsum((D,-U))),
                   zero_capacity_positive_demand=grid_capacity==0 and D>0,
                   replenishment_proxy=replenishment,movement_proxy=movement_proxy,
                   deadhead_proxy=deadhead_proxy,proxy_cost=proxy)
        if not _finite_features(row):
            raise ValueError('Nonfinite computed CA1 feature')
        features.append(row)
        keys[i] = (row['stress_flag'],proxy,-margin,-U,m.id)
    order = sorted(keys,key=keys.__getitem__)
    scores = [0]*len(ids)
    for rank,i in enumerate(order):
        scores[i] = len(order)-rank
    return {'policy':SCORER_POLICY,'case_identity':case.identity(),'movement_ids':ids,
            'scores':scores,'features':features,'flexible_order':[ids[i] for i in order],
            'tariff_sha256':_hash({'a':a,'b':b}),'ledger_convention':LEDGER_CONVENTION,
            'tau_kwh':TAU_KWH,'feasibility_certified':False,'bound_certified':False}
