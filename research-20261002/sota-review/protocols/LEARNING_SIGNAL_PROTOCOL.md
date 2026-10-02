# Prospective learning-signal comparison

2 October 2026. **Bounded design, not a final frozen launch protocol.** No execution is authorized by this document. It operationalizes rank 4 and Section 3.2 of [SOTA_REVIEW.md](../SOTA_REVIEW.md), the verified ML1–ML3 sources and training proposal in [ML_PRIMAL_AND_TRAINING.md](../notes/ML_PRIMAL_AND_TRAINING.md), and the timing principles in [MATCHED_ORACLE_PROTOCOL.md](MATCHED_ORACLE_PROTOCOL.md). No new literature search, cluster/data/model access, training, or solves accompany this protocol.

## Question, arms and controlled information

Does learning economical alternative topologies improve replay-valid fleet cost and time-to-quality beyond one incumbent? Use exactly three label arms:

1. **Single incumbent:** one best replay-valid topology in the common acquired pool, with deterministic tie-breaking; its movement indicators are binary labels.
2. **Uniform pool:** each deduplicated accepted topology has equal weight; labels are weighted movement marginals.
3. **Cost-weighted pool:** the identical topologies receive normalized economic weights; labels are their movement marginals.

Best-of-common-pool single labels isolate target multiplicity, not the cost of a cheaper standalone single-incumbent pipeline. Freeze model architecture, feature definitions, preprocessing, loss family, training resource ceilings, inference, movement decoder/search, recovery, charging completion and replay rules. Use the same weighted binary-cross-entropy implementation, with different targets only. Select one common online search policy using TRAIN inner splits before the screen; do not tune a separate decoder for each label arm. Economic negatives, LP features and new architectures are later ablations.

## Grouped TRAIN selection and freeze

Before tariff expansion, partition by timetable/progenitor group: related sizes, perturbations and tariff copies remain together. Identify 32 TRAIN collection timetables and four frozen tariffs per timetable. Assign grouped fit/inner-selection folds within these TRAIN groups; fit preprocessing and model parameters only on each fold's fit groups. Give all arms the same folds and maximum number of fits; temperature selection consumes the weighted arm's fitting budget. Choose configurations using replay-valid economic outcomes, with a predeclared worst-group/tie-breaking rule; AP is diagnostic.

The proposed online screen has 18 permitted cells: 12 synthetic cells from disjoint held-out TRAIN groups and six already explored public stress cells, as envisaged in the existing note. Their identities and group relationships remain unspecified. Freeze choices before screening; public cells cannot tune anything and are exploratory transfer evidence. Sealed DEV/TEST/A6/B3/confirmation/GIRO remain closed, including metadata or labels that could influence selection. Three seeds and multiple tariffs/budgets are repetitions, not independent timetables.

Before launch, version a manifest containing IDs/hashes, splits, tariffs, collector and model hashes, solver/version/hardware, seeds, topology canonicalization, pool cap, training/fitting ceilings, temperature shortlist, scale, failure penalties, reference rules and stop/go thresholds. Their unresolved values require a final freeze. A two-TRAIN-group engineering/timing check draws from the envelope and supplies no positive evidence.

## Common acquisition and label integrity

For every collection timetable/tariff, use three frozen proposal policies: unrestricted exploration, greedy/LP proposals and a previously frozen learned proposal. Each gets **300 cumulative one-thread solver CPU seconds**, across all tangent rounds, topology search, fixed-topology charging completion and solver repair. Preserve valid alternatives across policies, avoiding collection solely inside the learner's retained graph. One collection/relabeling cycle is included; a second collection requires a separate allocation.

Register the fixed collector checkpoint's complete TRAIN provenance, disjoint from **all 32 collection groups and every screen group**; this also protects inner-fold selection. Availability is unverified. Without such a checkpoint, revise and freeze cross-fitted acquisition and its budget before launch.

For each candidate record provenance, topology, bus count, charging plan, physical complete-fleet bill, energy timing, solver termination, incumbent and valid bound with domain, replay/repair status and consumed resources. A feasible label is not a certified optimum. Separate native/tangent objectives from the consistently recomputed physical bill; a restricted-model bound applies only to its stated domain. Never reinterpret it as an unrestricted bound or use a native objective gap as a physical-bill certificate without the necessary mapping.

Only accepted complete replay-valid fleets enter positive pools. Quarantine numerical extraction/replay failures or repair them within the allowance; they are not automatically physically infeasible negatives. Log infeasibility, timeout without incumbent, missing completion and software failure separately. An empty accepted pool supplies no target, rather than all-zero labels; apply the same missing-instance mask to all arms and retain failures in collection statistics. Freeze a missing-label tolerance before launch; exceeding it stops the pilot. A singleton pool remains in all arms and measures an honest absence of diversity.

## Deduplication, weighting and cost scale

Canonicalize integer route topology, including depot/charging-access choices, vehicle relabeling and route ordering; ignore continuous charging jitter. Retain the lowest accepted physical-bill realization of each topology, preserving other realizations' audit records. Freeze any pool cap and deterministic retention rule before inspection; apply it identically. One topology gets one vote regardless of how often a collector finds it. Equalize timetable-group and within-group tariff contribution so large pools do not dominate training.

For pool \(S_i\), use
\[
w_{is}=\frac{\exp[-(J_{is}-J_{i,\min})/(\tau a_i)]}{\sum_{r\in S_i}\exp[-(J_{ir}-J_{i,\min})/(\tau a_i)]},
\qquad a_i=\max\{a_0,|J_{i,\min}|\}>0.
\]
Freeze the currency-unit floor \(a_0\) and inner-TRAIN temperature shortlist; use stable log-sum-exp. Costs share units/accounting. The pool minimum denotes its best feasible bill, not optimality. Report weight entropy, effective topology count and sensitivity to scale: excessively concentrated weights reduce the weighted arm to a single label. Solver pools are biased samples, not probabilities of true optimal fleets.

## Total cost and paired economic evaluation

The arithmetic is:
\[
32\times4\times3\times300/3600=32\text{ CPUh};
\qquad18\times3\times3\times(60+300)/3600=16.2\text{ CPUh}.
\]
Thus **48.2 solver CPUh** leaves **6.8–21.8 CPUh** inside the existing **55–70 CPUh** envelope. The prospective **70 CPUh ceiling** allocates 32 collection solver + 16.2 online solver + 12 all fitting/training + 4 non-solver acquisition/online replay + 2 engineering + 3.8 feature/data preparation = **70**. This supersedes the companion note's narrower overhead shorthand. Failures/retries consume their buckets; extra reference solves are not free. Measure fitting feasibility and freeze fit counts/runtime caps before launch; feasibility is unverified. No GPU allocation is included.

Run paired case/seed comparisons at 60 and 300 seconds, independently, under common end-to-end wall-clock caps. Charge loading, scoring, building, presolve, charging completion, repair and replay; solver allowances are cumulative and cannot override those caps. Record CPU/thread-hours, elapsed time, memory and unused allowance. Count shared collection once in experimental spend, but charge its cost to each algorithm's deployment account. Report collection, fitting, training, online and replay separately; amortized repeated-query claims require an explicit reuse count.

Use common replay-valid best-known references, not assumed optima; recompute all arms consistently if a reference improves. Define normalized loss as the nonnegative bill gap clipped at a fixed penalty M. A run without a replay-valid plan receives M until one appears. Freeze numerical M, normalization and integration before launch. Joint failures are ties without wins; missing references/comparators never justify group deletion or wins. Their exact penalty/aggregation rules are unresolved **launch gates**. Report first valid fleet time, bill/buses, integral, failures and median/90th-percentile losses; unreached quality targets are censored.

Freeze the 18-cell group/tariff mapping and equal weighting: average seeds within each tariff/budget cell, tariff cells and the two budgets equally within each timetable group, then give groups equal weight. Keep synthetic group screening and public transfer summaries separate; seeds are not independent observations.

## Stop/go

Advance weighted pools only if they improve median paired primal integral over single labels by **at least 10%** on synthetic groups, win on **at least 70% of synthetic timetable groups**, and do not increase invalid/no-valid-plan rates. Separately require 90th-percentile public bill deterioration within **2%**, measured against the single-label arm at the same case/seed/budget. All synthetic groups remain in the win denominator. Predeclare zero-integral and missing-comparator rules before launch; failures cannot count as wins. Require the uniform-pool ablation: if uniform explains the benefit and weighting adds none, advance uniform pools and make no weighting claim. Stop for AP-only gains, overhead-erased savings, collapsing diversity, self-confirming collector omissions, missing-label excess or replay deterioration. These are exploratory gates; the small group count cannot establish generalization or confirmation success.
