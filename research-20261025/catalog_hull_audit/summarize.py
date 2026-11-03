"""Summarize all finite-catalog cells, retaining optimizer failures."""
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import statistics
import time

p = Path(__file__).resolve().parent
start = time.process_time()
raw = (p/'results.json').read_bytes()
d = json.loads(raw)
assert d['analysis_completed'] and d['completed_cells'] == 120
assert d['qualified_cells'] == 120
f = lambda x: float(Q(x))
out = ['# Finite-catalog convexification diagnostic — completed 25 October 2026', '',
    '120 predetermined cells: 20 observed minimum-fleet banks × day/late tariffs × curvature multipliers 0/1/5. Eighty one-start continuous SLSQP optimizations; 40 zero-curvature exact vertex controls. No route/charging reoptimization, learning or unrestricted fleet solve.', '',
    f"Overall process pass flag: **{d['passed']}**; all 120 cells completed, and all 120 independently rationalized primal/dual bounds satisfy the frozen numerical catalog tolerance. Optimizer status is preserved separately. No attempt was repeated.", '',
    '| Tariff | Curvature multiplier | Cells | Strictly positive gap lower bound (>1e-6) | Median pure-minus-catalog-hull gap (% of best pure cost), interval | Maximum gap upper bound (%) |',
    '|---|---:|---:|---:|---|---:|']
summary = []
for tariff in ('day', 'late'):
    for mult in (0, 1, 5):
        rows = [r for r in d['cells'] if r['tariff']==tariff and r['curvature_multiplier']==mult]
        lows = [max(0, 100*f(r['relative_gap_interval'][0])) for r in rows]
        highs = [100*f(r['relative_gap_interval'][1]) for r in rows]
        positive = sum(Q(r['pure_minus_hull_gap_interval'][0]) > Q(1, 1000000) for r in rows)
        item = dict(tariff=tariff, curvature_multiplier=mult, cells=len(rows), positive_gap_groups=positive,
            median_gap_percent_interval=[statistics.median(lows), statistics.median(highs)],
            max_gap_upper_percent=max(highs))
        summary.append(item)
        out.append(f"| {tariff} | {mult} | {len(rows)} | {positive} | [{item['median_gap_percent_interval'][0]:.6f}, {item['median_gap_percent_interval'][1]:.6f}] | {max(highs):.6f} |")
failures = [dict(case=r['case'], tariff=r['tariff'], curvature_multiplier=r['curvature_multiplier'],
    optimizer=r.get('optimizer'), numerical_catalog_qualification=r['numerical_catalog_qualification'],
    catalog_optimization_gap=r.get('catalog_optimization_gap'), failure=r.get('failure'))
    for r in d['cells'] if not r['passed']]
out += ['', 'All zero-curvature controls have exactly zero gap. Positive-curvature multipliers are sensitivity conditions on the same physical bank, not new datasets or calibrated market forecasts.', '',
    f"Optimizer/non-pass cells: {len(failures)}. Their exact feasible-mixture, lower-bound, decomposition and tolerance checks remain separately recorded; they have not been relabelled as optimizer successes."]
for r in failures:
    out.append(f"- {r['case']} / {r['tariff']} / multiplier {r['curvature_multiplier']}: {r['optimizer'].get('message')}; exact catalog optimization gap {f(r['catalog_optimization_gap']):.10g}.")
dimensions = [r['load_difference_descriptor']['squared_energy_dimensions95'] for r in d['banks']]
out += ['', f"The observed 30-period load-difference banks require a median {statistics.median(dimensions):g} singular directions to explain 95% of squared variation (range {min(dimensions)}–{max(dimensions)}). This is a bank-dependent descriptor, not the dimension of the full feasible set.", '',
    'Every cell checks with exact rational arithmetic: nonnegative mixture weights summing to one; primal/dual order; the pure-cost minus dual-bound = linear opportunity loss + curvature-weighted load distance identity; and the Jensen weighted-variance identity. The optimizer only proposes weights; these checks qualify the finite-bank bounds independently.', '',
    'The relaxation mixes whole physical schedules. Its fractional load is not an executable fractional fleet. Missing schedules and missing reoptimized charging can change both the best pure solution and the convex relaxation; the measured gap is neither a lower nor an upper bound on the original full-problem integrality gap. Minimum-fleet restriction and original-day candidate generation further limit inference.', '',
    'Scientific implication: use these measured magnitudes to decide whether full-space price-support work is worthwhile. Do not promote an elementary convexity identity, an SVD descriptor or a catalog calculation into a novel theorem, strategic equilibrium, ML improvement or global certificate.']
with (p/'RESULTS.md').open('x') as stream:
    stream.write('\n'.join(out)+'\n')
receipt = dict(source_result_sha256=hashlib.sha256(raw).hexdigest(), summary=summary, preserved_failures=failures,
    median_dimensions95=statistics.median(dimensions), dimensions95_range=[min(dimensions),max(dimensions)],
    cpu_s=time.process_time()-start)
with (p/'summary.json').open('x') as stream:
    json.dump(receipt, stream, indent=2)
print(json.dumps(dict(summary=summary, optimizer_failure_cells=len(failures), median_dimensions95=statistics.median(dimensions)), indent=2))
