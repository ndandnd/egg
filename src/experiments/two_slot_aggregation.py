"""Exact exploratory duty-menu laboratory; no protected data or solver imports.

Each participant must choose one of two fixed energy blocks. This is a finite
menu model, not an EVSP instance generator or an operational-data experiment.
Fractions certify every reported comparison. Run with --output in a NEW path.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
import json
from pathlib import Path
import platform
import subprocess
import time


@dataclass(frozen=True)
class Case:
    name: str
    energy: tuple[Q, ...]
    early_cost: tuple[Q, ...]
    late_cost: tuple[Q, ...]
    a: tuple[Q, Q] = (Q(0), Q(0))
    b: Q = Q(1)
    early_cap: Q | None = None


def schedules(case):
    if (not case.energy or len(case.energy) != len(case.early_cost)
            or len(case.energy) != len(case.late_cost)
            or case.b <= 0 or any(e <= 0 for e in case.energy)):
        raise ValueError('invalid finite-menu case')
    rows = []
    for choices in product((0, 1), repeat=len(case.energy)):
        x = sum((e * z for e, z in zip(case.energy, choices)), Q(0))
        if case.early_cap is not None and x > case.early_cap:
            continue
        c = sum((ce if z else cl for ce, cl, z in zip(
            case.early_cost, case.late_cost, choices)), Q(0))
        rows.append((x, c, choices))
    if not rows:
        raise ValueError('empty physical set')
    return rows


def lower_hull(rows):
    """Lower boundary of the exact (early energy, intrinsic cost) convex hull."""
    cheapest = {}
    for x, c, _ in rows:
        cheapest[x] = min(c, cheapest.get(x, c))
    hull = []
    for point in sorted(cheapest.items()):
        while len(hull) >= 2:
            x0, c0 = hull[-2]
            x1, c1 = hull[-1]
            x2, c2 = point
            cross = (x1-x0)*(c2-c0) - (c1-c0)*(x2-x0)
            if cross > 0:
                break
            hull.pop()
        hull.append(point)
    return hull


def supply(case, x):
    y = sum(case.energy) - x
    return case.a[0]*x + case.a[1]*y + case.b*(x*x+y*y)/2


def price(case, x):
    return (case.a[0]+case.b*x, case.a[1]+case.b*(sum(case.energy)-x))


def convex_optimum(case, hull):
    candidates = [(c+supply(case, x), x, c) for x, c in hull]
    for (x0, c0), (x1, c1) in zip(hull, hull[1:]):
        slope = (c1-c0)/(x1-x0)
        stationary = (case.b*sum(case.energy)-case.a[0]+case.a[1]-slope)/(2*case.b)
        x = max(x0, min(x1, stationary))
        c = c0+slope*(x-x0)
        candidates.append((c+supply(case, x), x, c))
    return min(candidates)


def independent_value(case, p):
    return sum((min(ce+p[0]*e, cl+p[1]*e) for e, ce, cl in zip(
        case.energy, case.early_cost, case.late_cost)), Q(0))


def individual_regrets(case, choices, p):
    regrets = []
    for e, ce, cl, z in zip(case.energy, case.early_cost, case.late_cost, choices):
        early, late = ce+p[0]*e, cl+p[1]*e
        regrets.append((early if z else late)-min(early, late))
    return regrets


def evaluate(case):
    rows = schedules(case)
    hull = lower_hull(rows)
    energy = sum(case.energy)
    zd, xd, cd, choices = min((c+supply(case, x), x, c, z) for x, c, z in rows)
    zch, xch, cch = convex_optimum(case, hull)
    gap = zd-zch
    if gap < 0:
        raise AssertionError('relaxation exceeds physical optimum')

    def joint_value(p):
        return min(c+p[0]*x+p[1]*(energy-x) for x, c in hull)

    total_regrets, max_individual = [], []
    support_exists = False
    for x, c, z in rows:
        p = price(case, x)
        regret = c+p[0]*x+p[1]*(energy-x)-joint_value(p)
        if regret < c+supply(case, x)-zch:
            raise AssertionError('own-price regret bound failed')
        support_exists |= regret == 0
        total_regrets.append(regret)
        regs = individual_regrets(case, z, p)
        max_individual.append(max(regs))
        if case.early_cap is None:
            if independent_value(case, p) != joint_value(p) or sum(regs) != regret:
                raise AssertionError('price-taking participant regrouping failed')
    if support_exists != (gap == 0):
        raise AssertionError('gap/support equivalence failed for joint feasible set')

    pch = price(case, xch)
    v = joint_value(pch)
    # F is on the nonnegative orthant; its conjugate is separable.
    fstar = sum((max(p-a, Q(0))**2/(2*case.b) for p, a in zip(pch, case.a)), Q(0))
    dual = v-fstar
    fleet_loc = cd+pch[0]*xd+pch[1]*(energy-xd)-v
    supplier_loc = supply(case, xd)-pch[0]*xd-pch[1]*(energy-xd)+fstar
    if dual != zch or fleet_loc < 0 or supplier_loc < 0 or fleet_loc+supplier_loc != gap:
        raise AssertionError('exact supporting-price settlement identity failed')

    return dict(name=case.name, participants=len(case.energy), energy=list(case.energy),
                early_cost=list(case.early_cost), late_cost=list(case.late_cost),
                a=list(case.a), b=case.b, early_cap=case.early_cap,
                physical_schedules=len(rows), lower_hull_vertices=len(hull),
                zd=zd, zch=zch, gap=gap, relative_gap=gap/zch if zch else None,
                optimal_early_energy=xd, convex_early_energy=xch,
                joint_price_support=support_exists,
                minimum_joint_own_price_regret=min(total_regrets),
                minimum_max_individual_unrestricted_regret=min(max_individual),
                fleet_loc_at_ch_price=fleet_loc, supplier_loc_at_ch_price=supplier_loc,
                planner_choices=list(choices))


def experiment_cases():
    cases = []
    for n in range(1, 13):
        for regime, e, b in [('fixed_unit_and_slope', Q(1), Q(1)),
                             ('replicated_market', Q(1), Q(1, n)),
                             ('fixed_total_energy', Q(1, n), Q(1))]:
            cases.append(Case(f'{regime}_n{n:02}', (e,)*n, (Q(0),)*n, (Q(0),)*n, b=b))
    for n, weights, costs, offset in product((4, 6, 8), ('uniform', 'alternating', 'three_sizes'),
                                              ('zero', 'alternating'), (Q(0), Q(1, 2), Q(2))):
        e = tuple(Q(1 if weights == 'uniform' else 1+i%(2 if weights == 'alternating' else 3)) for i in range(n))
        d = tuple(Q(0) if costs == 'zero' else Q((-1)**i, 4) for i in range(n))
        cases.append(Case(f'heterogeneous_n{n}_{weights}_{costs}_a{offset}', e,
                          tuple(max(x, Q(0)) for x in d), tuple(max(-x, Q(0)) for x in d),
                          a=(Q(0), offset)))
    return cases


def shared_capacity_witness():
    case = Case('unpriced_shared_early_capacity', (Q(1),)*2, (Q(0),)*2,
                (Q(0),)*2, a=(Q(0), Q(2)), early_cap=Q(1))
    result = evaluate(case)
    p = price(case, result['optimal_early_energy'])
    choices = tuple(result['planner_choices'])
    tau = Q(2)
    residual_regrets = []
    for i, z in enumerate(choices):
        alternatives = []
        for alternative in (0, 1):
            profile = list(choices)
            profile[i] = alternative
            if sum(profile) <= case.early_cap:
                alternatives.append(p[0] if alternative else p[1])
        residual_regrets.append((p[0] if z else p[1])-min(alternatives))
    result.update(energy_price=list(p), capacity_price=tau,
                  unrestricted_individual_regrets=individual_regrets(case, choices, p),
                  capacity_priced_individual_regrets=individual_regrets(case, choices, (p[0]+tau, p[1])),
                  residual_capacity_deviation_regrets=residual_regrets,
                  capacity_rent=tau*result['optimal_early_energy'])
    if result['gap'] != 0 or max(result['unrestricted_individual_regrets']) != 2:
        raise AssertionError('unpriced capacity witness failed')
    if any(result['capacity_priced_individual_regrets']) or any(residual_regrets):
        raise AssertionError('capacity support failed')
    return result


def jsonable(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    start = time.perf_counter()
    rows = [evaluate(c) for c in experiment_cases()]
    witness = shared_capacity_witness()
    result = dict(schema='egg-two-slot-exploratory-v1', arithmetic='fractions.Fraction',
                  scope='finite two-choice energy menus; not full EVSP or protected evidence',
                  case_count=len(rows), rows=rows, shared_capacity_witness=witness,
                  elapsed_seconds=time.perf_counter()-start, python=platform.python_version(),
                  code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[2], text=True).strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        json.dump(jsonable(result), handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('rows', 'shared_capacity_witness')}, indent=2))


if __name__ == '__main__':
    main()
