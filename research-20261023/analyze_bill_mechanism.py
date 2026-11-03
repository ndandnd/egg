"""Exploratory decomposition of the completed 17-Oct development screen.

Reads compact terminal receipts only. No model, solver, raw traces or new data.
The old campaign remains immutable; these post-hoc results are hypothesis generating.
"""
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research-20261017/local-screen-v3'
OUT = Path(__file__).resolve().parent / 'bill-mechanism'


def main():
    started = time.process_time()
    OUT.mkdir(exist_ok=True)
    hashes, rows, valid = {}, [], {}
    def read(path):
        raw = path.read_bytes()
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    for path in sorted(SOURCE.glob('*/result.json')):
        result = read(path)
        supervisor = read(path.parent / 'supervisor.json')
        task = result['task']
        key = (task['case_key'], task['seed'], task['arm'])
        if not (result.get('accepted_valid') and supervisor.get('endpoint_valid')):
            continue
        replay = read(path.parent / 'replay.json')
        assert replay['replay_ok']
        bill = Fraction(result['bill_exact'])
        ops = Fraction(replay['ops_cost'])
        # The frozen generator has vehicle_cost=100 and zero movement cost.
        assert ops == 100 * result['vehicles']
        valid[key] = dict(bill=bill, ops=ops, energy=bill-ops,
                          vehicles=result['vehicles'], grid_kwh=replay['grid_kwh'])
    assert len(valid) == 342, 'Completed cohort endpoint count changed'
    comparisons = ['nonlearned', 'catboost_v5', 'random', 'full4', 'cold']
    summaries = []
    for comparator in comparisons:
        for size in (40, 80):
            by_group = defaultdict(list)
            for (case, seed, arm), graph in sorted(valid.items()):
                if arm != 'v8' or int(case.rsplit(':', 1)[1]) != size:
                    continue
                other = valid.get((case, seed, comparator))
                if other is None:
                    continue
                bill_delta = other['bill'] - graph['bill']
                ops_delta = other['ops'] - graph['ops']
                energy_delta = other['energy'] - graph['energy']
                assert bill_delta == ops_delta + energy_delta
                row = dict(case=case, seed=seed, comparator=comparator, size=size,
                           graph_vehicles=graph['vehicles'], comparator_vehicles=other['vehicles'],
                           vehicle_reduction=other['vehicles']-graph['vehicles'],
                           bill_delta=float(bill_delta), fleet_cost_delta=float(ops_delta),
                           energy_cost_delta=float(energy_delta),
                           relative_bill_gain=float(bill_delta / other['bill']),
                           graph_grid_kwh=graph['grid_kwh'], comparator_grid_kwh=other['grid_kwh'],
                           exact_deltas={'bill':str(bill_delta), 'fleet':str(ops_delta), 'energy':str(energy_delta)})
                rows.append(row); by_group[case].append(row)
            flat = [r for group in by_group.values() for r in group]
            sums = {k:sum(r[k] for r in flat) for k in ('bill_delta','fleet_cost_delta','energy_cost_delta')}
            summaries.append(dict(comparator=comparator, size=size, groups=len(by_group), pairs=len(flat),
                complete_groups=sum(len(v)==3 for v in by_group.values()),
                median_group_relative_gain=median(median(r['relative_bill_gain'] for r in group) for group in by_group.values()),
                median_graph_vehicles=median(r['graph_vehicles'] for r in flat),
                median_comparator_vehicles=median(r['comparator_vehicles'] for r in flat),
                median_paired_vehicle_reduction=median(r['vehicle_reduction'] for r in flat),
                graph_uses_fewer_vehicles=sum(r['vehicle_reduction']>0 for r in flat),
                same_vehicle_count=sum(r['vehicle_reduction']==0 for r in flat),
                aggregate_delta=sums,
                fleet_share_of_summed_bill_delta=(sums['fleet_cost_delta']/sums['bill_delta'] if sums['bill_delta'] else None)))
    report={'classification':'post-hoc development analysis; no causal attribution or new validation',
        'source_endpoint_count':342, 'rows':rows, 'summaries':summaries,
        'accounting_cpu_s':time.process_time()-started,
        'aggregation_warning':'Summed component shares are descriptive over paired cells. They are not a decomposition of the median group percentage or independent-sample inference.',
        'source_hashes':hashes}
    with (OUT/'decomposition.json').open('x') as handle:
        json.dump(report, handle, indent=2); handle.write('\n')
    lines=['# Where the bill gain comes from — exploratory analysis, 23 October 2026', '',
        'This analysis uses the immutable completed development screen. It introduces no new solver runs, model fits or timetables. The 342 accepted endpoints were independently replayed in the earlier audit; this analysis checks terminal admission flags and decomposes their saved exact bills.', '',
        'The generator charges 100 cost units per vehicle and zero movement operating cost. Thus the exact bill difference separates into fleet-count cost and electricity cost. A reduction in fleet count can dominate the result even without superior electricity-price response.', '',
        '| Comparator | Trips | Paired cells | Median vehicles: graph / comparator | Median paired vehicle reduction | Fleet share of summed bill saving |',
        '|---|---:|---:|---:|---:|---:|']
    for s in summaries:
        share=s['fleet_share_of_summed_bill_delta']
        lines.append(f"| {s['comparator']} | {s['size']} | {s['pairs']} | {s['median_graph_vehicles']:g} / {s['median_comparator_vehicles']:g} | {s['median_paired_vehicle_reduction']:g} | {share:.1%} |")
    lines += ['', 'Shares use sums of matched cost differences, not the published median group percentage. They may exceed 100% or be negative when component changes offset. Conditional comparisons retain missing endpoints; no finite penalty is imputed. Seed repeats are not independent timetables.', '',
        'Interpretation: use these decompositions to design the next experiment, not to retrofit a mechanism claim. Fleet-count gains can result from easier search, a better retained feasible set, or both. Distinguishing those explanations requires matched recovery/time-budget and stronger baseline experiments. A claim about tariff-responsive learning requires tariff shifts and price-blind ablations, which this fixed-tariff screen did not include.', '',
        f"Accounting: {report['accounting_cpu_s']:.4f} CPU seconds for this compact receipt analysis. Full exact deltas and source hashes are in decomposition.json."]
    with (OUT/'RESULTS.md').open('x') as handle:handle.write('\n'.join(lines)+'\n')
    print(json.dumps({'summaries':summaries,'cpu_s':report['accounting_cpu_s']},indent=2))


if __name__ == '__main__':
    main()
