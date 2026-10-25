# Paired FIT targets — completed 25 October 2026

The pinned TRAIN pool contains **48 differing and31 identical movement targets
among79 paired FIT timetables**. Every differing pair also differs in flexible
direct/depot membership. Vehicle counts match within all79 pairs. This provides
observed conditional target variation in the audited substrate, rather than a
universal constant-label explanation. It does **not** establish that the
differences are economically useful tariff responses or justify another fit.

The once-only audit ran after source/protocol commit `277dc933` was pushed and
closed exit0 with complete support/checks passed. All80 fixed declared FIT groups
were retained. All79 expected pairs and159 expected source records passed
internal case/market/whole-plan identity and membership checks, with no findings
or exceptions. `physical_v2_s10037` remains source1-only: its missing comparison
is undefined, not zero disagreement. There was no replacement or retry.

## What changed in the supervision

| Paired-target description | All movements | Flexible direct/depot modes |
|---|---:|---:|
| Intended complete pairs | 79 | 79 |
| Internally admitted pairs | 79 | 79 |
| Identical positive sets | 31 | 31 |
| Different positive sets | 48 | 48 |
| Median Hamming disagreement / candidate universe | 1/173 | 1/160 |
| Median Jaccard disagreement / positive union | 2/17 | 2/13 |
| Defined Hamming/Jaccard fractions | 79/79 | 79/79 |

For flexible candidates, median changed membership is **0.625% of the whole
candidate universe**, while median change relative to the positive union is
**2/13 (about15.38%)**. These are different denominators; neither is accuracy,
bill savings or causal price information. They show why a large negative class
can dilute changes in the selected alternatives. The exact rational equal-group
means, medians and ranges are preserved in attempt01/receipt.json. Movement
rows, two tariffs and repeated teacher outputs are not independent timetables.

The source-bound market IDs agree with source0 flat a=.20 and source1 a=.10 in
periods18–21/.30 elsewhere, both with b=1/900 and the common stored30-period grid.
The physical-case identity agrees across each paired source. These checks bind
the stored records to that explicit source contract; they are not new numerical
market observations or verification of every historical executed source version.

Equal vehicle counts exclude changing fleet quantity as an explanation of the
within-pair target differences in these79 pairs. They do not fix route energy,
charging times, deadhead, teacher quality or search randomness. Different labels
could still arise from different imperfect incumbents rather than a changed
economic preference. The labels remain membership in one observed source plan,
not optimal decisions, probabilities, regret or uniquely good connections.

## Admission and access actually exercised

The two reconciled FIT lists came from the completed selected metadata receipt.
The declared pool is pinned by CatBoost preprocessing; historical GNN pool
lineage remains unverified. Do not describe this as full GNN training provenance.
No model was loaded, refit, selected or scored.

The audit read all original bytes of the two mixed TRAIN tables once and checked
their prebound digests:128 case lines and255 source lines. Standard JSON decoding
transiently decoded rows for top-level routing;48 non-FIT case rows and96
non-FIT source rows were immediately discarded without further semantic
inspection or retention. This was explicitly authorized routing access, **not
FIT-only byte access or identifier-only parsing**. No inner/outer performance,
non-FIT label analysis, outcome table or sealed bank was opened.

All80 FIT case identities,159 source-market identities and159 whole source-plan
digests matched. Entire FIT plans were traversed for canonical hashing only;
semantic access was restricted to identity and movement membership. Costs,
charges, loads, source_replay and solver diagnostics were not analyzed or
published. The source tables' physical feasibility/optimality claims were not
independently replayed here. Identity/membership consistency is a narrower claim.

## Next scientific decision

Before more training, test the **economic coherence of these teacher choices**.
A separately frozen small diagnostic can independently replay both old plans
under their common physical case, then value the same two fixed whole-schedule
witnesses at both source tariffs. Ask whether each own-source teacher choice is
cheapest in that two-witness catalog, whether there is a strict preference
reversal, a tie, or an observed competing plan that dominates its label.

This is a diagnostic of restricted-catalog objective consistency, not a novel
theorem, a full optimum or price-learning value. Repricing fixed charging
schedules still mixes route and charging differences; it is not fixed-route QP
reoptimization. A changed membership target is not enough to assume a useful
conditional learning target. No automatic relabeling, teacher solve, QP, refit
or larger evaluation is authorized. NEXT_CATALOG_COHERENCE_DECISION.md supplies
a design direction; exact fields, replay/cost APIs, tolerances, sources, command,
namespace and practical resource budget must be reviewed/frozen before access.

The eight-group warm result remains unchanged: GNN0.0386688%E0 and CatBoost
0.1997028%E0 beyond CoverCA1, both below the prospective1%E0 useful-margin
threshold. This FIT analysis does not rescue that gate or establish a
publication-ready ML contribution.

## Resources

External meter:0.51CPU/0.81elapsed seconds. Retain0.53CPU as the phase charge to
allow for two centisecond-rounded CPU components. Observed prepublication peak
RSS35,373,056bytes; one standard-library process, no project/scientific-library
imports. Original-file hashes and canonical-object hashes are distinct: six
file/input identities, plus80case/159market/159plan hashes. No duplicate file
audit, generator, physical replay, solver, inference or training was run.
FINAL_RESOURCE_RECEIPT.json preserves actual display, rounding charge and old
unknown/guard accounting separately; no exact whole-session claim or reset.
