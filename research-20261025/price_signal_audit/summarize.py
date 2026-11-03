"""One compact, metered result summary; no replay or optimization."""
import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path
import resource
import statistics
import time

root = Path(__file__).resolve().parent
start = time.process_time()
raw = (root/'results.json').read_bytes()
d = json.loads(raw)
assert d['passed'] and not d['incomplete']
f = lambda x: float(Q(x))
med = lambda x: statistics.median(x) if x else None
out = ['# Fixed-plan price-signal diagnostic — completed 25 October 2026', '',
       '342 admitted plans / 20 development timetables. Original exact objective and historical input hashes all matched. No new routes, charging schedules, model fits, inference or physical replay were run.', '',
       'Primary bank: minimum observed fleet count within each timetable, pooling all six methods and three seeds. It is a hindsight catalog; these are not deployable-selector or full-problem optima.', '',
       '| Target | Groups with a materially better target plan / 20 | Median cost reduction from changing the original-day selection | Maximum reduction |',
       '|---|---:|---:|---:|']
compact = {}
for tariff in d['tariffs']:
    rows = [r for r in d['catalog_results'] if r['scope']=='minimum_observed_fleet' and r['tariff']==tariff]
    gains = [100*f(r['relative_regret']) for r in rows]
    changes = sum(r['changed_over_1e_6'] for r in rows)
    compact[tariff] = dict(groups=len(rows), changed=changes, median_percent=med(gains), max_percent=max(gains))
    out.append(f'| {tariff} | {changes} | {med(gains):.4f}% | {max(gains):.4f}% |')
out += ['', 'Material means more than 1e-6 cost units. All tariffs have the same mean linear coefficient and unchanged curvature. A reduction is relative to the original-day winner evaluated at the target tariff. Fixed stored charging limits the available alternatives; a small effect cannot rule out better unobserved charging or routes.', '',
        '| Objective change, same minimum observed fleet | Positive system-cost loss / 20 | Median loss in cost units | Maximum loss |',
        '|---|---:|---:|---:|']
for tariff in ('day', 'late'):
    rows = [r for r in d['objective_comparisons'] if r['scope']=='minimum_observed_fleet' and r['tariff']==tariff]
    losses = [f(r['welfare_loss']) for r in rows]
    out.append(f"| System-cost optimum to marginal-payment optimum, {tariff} | {sum(r['welfare_loss_over_1e_6'] for r in rows)} | {med(losses):.6f} | {max(losses):.6f} |")
    compact['objective_'+tariff] = dict(positive=sum(r['welfare_loss_over_1e_6'] for r in rows), median_loss=med(losses), max_loss=max(losses))
out += ['', 'System cost is c+aL+bL²/2; all-units marginal-price payment is c+aL+bL². This comparison selects from the same stored bank. It does not solve a strategic fleet model or equilibrium.', '',
        '| Paired equal-fleet comparison, 40 trips | Groups | Paired cells | Median group objective improvement | Positive / negative / zero group signs |',
        '|---|---:|---:|---:|---|']
for r in d['aggregates']:
    if r['size']==40:
        v = r['median_group_relative_gain']
        signs = r['exact_group_sign_counts']
        out.append(f"| Graph vs {r['control']}, {r['tariff']} | {r['groups']} | {r['paired_cells']} | {'unavailable' if v is None else f'{100*f(v):.4f}%'} | {signs['positive']} / {signs['negative']} / {signs['zero']} |")
out += ['', 'Positive means lower integrated system cost for graph. Signs here are exact signs, including numerically tiny differences; they are not tests of significance. Equal-fleet eligibility is conditional on the old endpoints, not a prospective fixed-fleet intervention. At 80 trips the important graph/classical comparisons mostly have unequal fleets, so this analysis cannot remove that confounding.', '',
        'Exact cost differences split into fleet cost, common-mean-price energy quantity, tariff timing exposure and curvature; all additive identities passed. Results preserve every original unavailable endpoint and seed/group denominator.', '',
        'Interpretation: a tariff-dependent bank winner establishes an available alternative, not that the learned scorer recognizes it. The next mechanism test must change the model price inputs and reoptimize charging/routes under the declared objective. Neither this audit nor its stability radii certify the original unrestricted EVSP.']
primary = [r for r in d['catalog_results'] if r['scope']=='minimum_observed_fleet' and r['tariff']=='day']
compact['bank_candidates'] = dict(min=min(r['candidate_count'] for r in primary), median=med([r['candidate_count'] for r in primary]), max=max(r['candidate_count'] for r in primary))
out += ['', f"Same-fleet bank sizes: {compact['bank_candidates']}. Full exact quantities, source hashes and original admitted loads are in results.json."]
with (root/'RESULTS.md').open('x') as stream:
    stream.write('\n'.join(out)+'\n')
receipt = dict(source_result_sha256=hashlib.sha256(raw).hexdigest(), compact=compact,
    summary_process_cpu_s=time.process_time()-start, rusage_maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
with (root/'summary.json').open('x') as stream:
    json.dump(receipt, stream, indent=2)
print(json.dumps(compact, indent=2))
