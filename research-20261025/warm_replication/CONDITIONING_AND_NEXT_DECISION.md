# Conditioning result and the next decision

Static parent handoff from `RESULTS_VIEW.json`, its rounded
`export-view-stdout.txt`, and the existing matched-blind/restriction interpretation
notes only. No new statistics, data audit, source change, model access, inference,
replay, solver call or numerical run was performed. All frozen outcomes and gates
remain unchanged.

## The replication did not clear its learned continuation rule

All16 priors were admitted and all384 active assignments were attempted. There
are382 accepted method endpoints,371 strict method successes,384 defined
operational costs and two operational fallbacks. Late/timed-out, configuration
failure and invalid-admission counts are zero. The48 fixed-route QP controls
qualified with new physical candidates, native optimality and timely admission;
fallback availability alone did not qualify them.

Both learned families have seven positive base-group medians against CoverCA1,
but their mean gains fail the frozen `mean d > 0.01` requirement:

| Family | Mean d versus CoverCA1 | Mean d versus qualified fixed-route QP | Continuation |
| --- | ---: | ---: | --- |
| GNN | 0.000386688 | 0.087352508 | Do not continue |
| CatBoost | 0.001997028 | 0.088962848 | Do not continue |

These are the export's rounded values of
`d=(control cost−learned cost)/prior late electricity E0`, not relative savings
against the control's total bill. Both exceed the magnitude threshold against
fixed-route QP and have eight positive group medians there. That does not rescue
the failed conjunction against competent CoverCA1. The result supports route
adaptation in this setting more clearly than a useful learned increment over
the conventional route-selection control. It neither proves equivalence nor
global irrelevance of learned or tariff information. There are eight development
groups, not48 independent timetable observations.

## What GNN_day contributes

For the same frozen weights and late-target optimizer, the reported mean
`(GNN_day cost−GNN cost)/E0` is0.001206672. The mean signed cost difference is
0.913905916 generator cost units; the displayed median rounds to zero. At the
declared `|d|<=1e-6` near-zero convention, the cell counts are23 GNN wins,
15 GNN_day wins and10 near-zero; group-median descriptors are4/2/2. These are
descriptive results with no automatic promotion threshold.

Pool metadata exist for47/48 pairs: all47 recorded pools changed, and none had
zero rank-fill room. This rules out an identical-pool explanation for those
observed pairs, but gives neither a pool-change magnitude nor its causal share
of cost differences. The missing record remains missing; do not claim all48
pools changed or promote from an available-only47-pair subset. Operational cost
comparisons remain defined for all48 pairs.

This is an inference-conditioning intervention on one fixed model/pipeline.
It is not a matched trained-blind comparison: the same historically trained
weights remain, and both optimizers know target prices. A controlled change of
proposal inputs can change restriction and finite-budget search behavior without
establishing the marginal value of current-case tariff inputs in a **matched
trained proposal pair**. As the
restriction note explains, a pruned incumbent's advantage can reflect lower
search error offsetting restriction regret; those components are not separately
identified by these receipts. Random or classical compression can help too.

## Smallest justified next step: TRAIN readiness, not a refit

Recommend only a separately frozen, metadata-first TRAIN audit under the existing
small readiness direction. Parent must specify the whitelist, budget and output
before access; this note grants none. Request a compact answer to four questions:

1. Can canonical generator/base IDs, size/resource/tariff variants and source
   plans be linked to the declared80 fit/16 inner/32 outer groups without alias
   leakage? Record missing crosswalks rather than inferring them from names.
2. Which actual tariff vectors and objectives produced the TRAIN supervision?
   Does the proposed within-timetable paired design have price variation at
   unchanged physics/fleet, or is support absent/unknown? That pairing is our
   strong design choice, not a universal requirement for every possible design.
3. What do the labels mean: observed feasible-incumbent edge membership, from
   which teacher/candidate bank, effort, seeds and tie policy? Is binary edge-label
   variation present across prices, or only charging/cost variation? Changing
   incumbent labels may reflect teacher search or noise and is not itself
   information value. Identical edge labels do not supply a conditional binary
   target; a cost-sensitive target needs a separate justified label design.
4. Is a matched current-case tariff-blind proposal feasible without leaks through
   price-derived features, graph construction, normalization, IDs or cached
   scores? Both students would retain shared price-influenced supervision and
   the same price-aware downstream optimizer. Plan equal fit preprocessing,
   inner-selection opportunities and compute before considering training.

Start with manifest/schema/provenance fields, not a broad row or outcome search.
If those fields cannot answer the label-support question, record **unknown** and
propose a specifically bounded TRAIN-only inspection for a later decision; do
not automatically generate labels, solve cases or launch the earlier label pilot.
Single universal-tariff supervision provides no observed support for sensitivity;
other designs or targets need their own assumptions and admission review.

Only usable support and a leakage-safe matched design could justify a later
refit decision. The existing outer groups and this eight-group study stay
development evidence; no sealed DEV/TEST/A6/B3/confirmation/GIRO source is opened
or rebranded. Do not lower the1%E0 gate, add families, extend search, or force an
ML contribution after this result. A competent conventional policy may be the
appropriate operational conclusion for the tested regime. Parent decides the
next package after the readiness facts are known.
