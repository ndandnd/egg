"""Independent exact stored-number reconstruction of the two energy rows.

Standard library only. The reviewer participated in the analytical band
discussion but did not author the scientific implementation or run its solver.
"""
from fractions import Fraction as Q
import math


def require(ok, label):
    if not ok:
        raise AssertionError(label)


def profile(case):
    service = sum(map(lambda t: Q(t['energy_kwh']), case['trips']), Q())
    sf = sum(t['energy_kwh'] for t in case['trips'])
    modes = []
    defects, residual_lows, residual_highs = [], [], []
    for j, m in enumerate(case['movements']):
        ef = sum(l['energy_kwh'] for l in m['legs'])
        exact = sum((Q(l['energy_kwh']) for l in m['legs']), Q())
        bf = case['battery_kwh'] + ef
        if m['kind'] == 'pullout':
            cf = -(case['battery_kwh']-ef)
            ideal = Q(ef)-Q(case['battery_kwh'])
        elif m['kind'] == 'pullin':
            cf = -ef-case['battery_kwh']
            ideal = -Q(ef)-Q(case['battery_kwh'])
        else:
            cf, ideal = ef, Q(ef)
        # The normalized selected rows bound phi by M-fl(C+M) and
        # -M-fl(C-M); adding the intended constant yields these bounds.
        lo = Q(bf)-Q(cf+bf)+ideal
        hi = -Q(bf)-Q(cf-bf)+ideal
        signed = (-hi, -lo) if m['kind'] == 'pullin' else (lo, hi)
        defects.append(exact-Q(ef))
        residual_lows.append(signed[0]); residual_highs.append(signed[1])
        modes.append(dict(index=j, id=m['id'], kind=m['kind'], energy_float=ef,
            semantic_energy_exact=str(exact), energy_aggregation_defect_exact=str(exact-Q(ef)),
            big_m_float=bf, residual_constant_float=cf,
            normalized_plus_constant_float=cf+bf, normalized_minus_constant_float=cf-bf,
            residual_constant_defect_exact=str(Q(cf)-ideal),
            selected_intended_residual_lower_exact=str(lo),
            selected_intended_residual_upper_exact=str(hi),
            signed_contribution_lower_exact=str(signed[0]), signed_contribution_upper_exact=str(signed[1])))
    cap=2*len(case['trips'])
    # At most N+k <= 2N selected arcs. Ignoring path correlations makes
    # independent extremal subset sums conservative, never too narrow.
    low_sum=lambda xs:sum(sorted(x for x in xs if x<0)[:cap], Q())
    high_sum=lambda xs:sum(sorted((x for x in xs if x>0),reverse=True)[:cap], Q())
    pl,pu=service+low_sum(defects),service+high_sum(defects)
    sl,su=service-high_sum(residual_highs),service-low_sum(residual_lows)
    lo,hi=min(pl,sl),max(pu,su)
    def directed(x, direction):
        f=float(x)
        if direction*(Q(f)-x)<0:
            f=math.nextafter(f, direction*math.inf)
        return f
    return dict(policy='stored-row-and-physical-conservation-band-v1',charge_coefficient=case['efficiency'],
        service_energy_exact=str(service),service_energy_float=sf,service_aggregation_defect_exact=str(service-Q(sf)),
        selected_mode_cap=cap,modes=modes,physical_lower_exact=str(pl),physical_upper_exact=str(pu),
        stored_matrix_lower_exact=str(sl),stored_matrix_upper_exact=str(su),union_lower_exact=str(lo),union_upper_exact=str(hi),
        lower_rhs=directed(lo,-1),upper_rhs=directed(hi,1),additional_constraints=2,
        interpretation='Union of intended per-leg conservation and exact binary-stored integer matrix bands; native tolerances unchanged')


def check(case, saved, first_row, energies, selection):
    expected=profile(case)
    expected['constraint_indices']=[first_row,first_row+1]
    require(saved==expected, 'complete independent aggregate-energy profile and row positions')
    lhs=Q(case['efficiency'])*sum(energies.values(),Q())-sum(Q(m['energy_float'])*y for m,y in zip(expected['modes'],selection))
    rows=[max(Q(),Q(expected['lower_rhs'])-lhs),max(Q(),lhs-Q(expected['upper_rhs']))]
    return dict(lhs=lhs,lower_rhs=Q(expected['lower_rhs']),upper_rhs=Q(expected['upper_rhs']),
        row_residuals=rows,exact_union_width=Q(expected['union_upper_exact'])-Q(expected['union_lower_exact']))
