#!/usr/bin/env python3
"""Exact arithmetic supplement; reads pinned evidence, never calls an optimizer."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

PIN = {
    'result/sistig_cardinality_flow/20260927-attempt1/frozen.json': 'bce2293080c3d19d05c37aa8c6bb4a285f1afe59fbde161fa6a6b6505784d103',
    'result/sistig_cardinality_flow/20260927-attempt1/depot_15.json': '01a818211e68be38093b478308d0780d752aeac150b7959d7bd785552d6bdb39',
    'result/sistig_cardinality_flow/20260927-attempt1/review/REVIEW.md': '60604b3467c17ec1c833ef56a2634a7e091d6cb677aaea4ec3c684dfdec15c94',
    'result/sistig_cardinality_flow/20260927-attempt1/review/audit-report.json': 'f4d6acdf46bd3cd6839fc727c9786b63c2b63dbb4fb507197c7336a3f3f6260f',
    'result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json': '35ce1e07876ca62ee366e598fec884556f8f9ea03e46230f19d5999f087e660b',
    'doc/SISTIG_ONE_BUS_OBSTRUCTION_20260927.md': 'a2c4badf085d9d67c205170f8b7460e7efc1b40ac8b87aab4aa846c1815d8bdb',
    'research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md': '7b1d55d1d20fce676ded6aaeb6ae0965cd70fc464581290ad792f2056bce53a2',
    'src/experiments/sistig_nonlinear_pilot.py': '36195617aa3b5b3955bea3f7fe04011a59d0c8d5458f20ad454a80944a7cb2de',
    'doc/SISTIG_NONLINEAR_PILOT_PROTOCOL_20260927.md': '5fe33d06ddf1a52b611013932107bd2a8583cae02b7f3d9ffb0394a53ec0f326',
}
CASE_ID = '1917409b43c0433b4ac2504b0b28c1bb2aa63a033c79ba1a4057418b63874ed7'


def read(repo, name):
    data = (repo / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == PIN[name], name
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2] / 'journal-research-work')
    repo = parser.parse_args().repo.resolve()
    raw = {k: read(repo, k) for k in PIN}
    flow_input = json.loads(raw['result/sistig_cardinality_flow/20260927-attempt1/frozen.json'])
    flow = json.loads(raw['result/sistig_cardinality_flow/20260927-attempt1/depot_15.json'])
    audit = json.loads(raw['result/sistig_cardinality_flow/20260927-attempt1/review/audit-report.json'])
    flat_input = json.loads(raw['result/sistig_pricing/20260927-grb-job557543-attempt1/frozen.json'])
    case = flow_input['cases'][0]
    assert case == flat_input['controls'][0]['case']
    assert flow['case_identity'] == flat_input['controls'][0]['case_identity'] == CASE_ID
    assert flat_input['controls'][0]['source_payload_sha256'] == 'af6da4dea220063d1b2486a4c958bff19ae621328f07bde4a95a5c70690ebeb6'
    assert audit['verdict'].startswith('PASS') and audit['cases'][0]['lower_exact'] == flow['lower_exact']
    assert audit['cases'][0]['paths_in_relaxation'] == flow['used_paths_in_relaxation'] == 2
    assert '**PASS for the one-bus infeasibility proof' in raw['research-20260927/agent-notes/sistig-one-bus-postpilot-review/REVIEW.md'].decode()
    source = raw['src/experiments/sistig_nonlinear_pilot.py'].decode()
    protocol = raw['doc/SISTIG_NONLINEAR_PILOT_PROTOCOL_20260927.md'].decode()
    assert '(.2,) * 30,' in source and '(1 / 900,) * 30' in source
    assert 'F(L)=sum_t(a_t L_t + b_t L_t^2/2)' in protocol
    a, b, T = Q(flow_input['price_input']), Q(1 / 900), Q(30)
    f, eta, rate = Q(case['vehicle_cost']), Q(case['efficiency']), Q(case['deadhead_cost_per_min'])
    assert a == Q(flow['flat_price']) == Q(flow_input['price_exact']) and a > 0 and b > 0
    assert f == 100 and eta == 1 and rate == 0 and len(case['trips']) == 37
    assert case['market_edges_min'] == list(range(0, 1801, 60)) and case['recharge_deadline_min'] == 1800
    assert all(Q(t['energy_kwh']) >= 0 for t in case['trips'])
    assert all(Q(leg['energy_kwh']) >= 0 for m in case['movements'] for leg in m['legs'])
    Eservice = sum((Q(t['energy_kwh']) for t in case['trips']), Q(0))
    modes = {m['id']: m for m in case['movements']}
    selected = flow['selected_movement_ids']
    assert len(selected) == len(set(selected)) == 39 and all(mid in modes for mid in selected)
    Eselected = Eservice + sum((Q(leg['energy_kwh']) for mid in selected for leg in modes[mid]['legs']), Q(0))
    Lflow = Q(flow['lower_exact'])
    Emin = (Lflow - 2*f) / a
    assert Emin == Eselected and Lflow == 2*f + a*Eselected
    p = a + b*Emin/T
    margin = 3*f + p*Eservice - (2*f + p*Emin)
    assert p >= a and margin >= 0
    conjugate = T*(p-a)**2/(2*b)
    pricing_lower = 2*f + p*Emin
    CH_lower = pricing_lower - conjugate
    assert CH_lower == 2*f + a*Emin + b*Emin**2/(2*T)
    result = {k: str(v) for k, v in [('a', a), ('b', b), ('Eservice', Eservice), ('Lflow', Lflow),
              ('Emin', Emin), ('uniform_price', p), ('three_bus_margin', margin),
              ('conjugate', conjugate), ('pricing_lower', pricing_lower), ('CH_lower', CH_lower)]}
    result['CH_lower_decimal'] = format(float(CH_lower), '.12f')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
