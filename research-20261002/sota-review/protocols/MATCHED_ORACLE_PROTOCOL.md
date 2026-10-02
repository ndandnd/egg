# Prospective matched oracle-allocation pilot

Status: protocol only, 2 October 2026. No execution authorized by this document. This operationalizes rank 3 of [SOTA_REVIEW.md](../SOTA_REVIEW.md), Sections 3.5, 4 and 6; certificate qualifications follow [CERTIFICATE_REVIEW.md](../notes/CERTIFICATE_REVIEW.md). The question is whether allocating effort between feasible candidate generation and global pricing certification improves a complete-fleet hull enclosure within a common decision-time budget.

## Freeze before launch

Select exactly ten permitted TRAIN/development-generation or already explored public stress cases, with three fixed solver seeds per case. Record case IDs, timetable groups, tariff variants and input hashes in a signed/versioned manifest before launch; their identities are presently unspecified. Sealed DEV/TEST/A6/B3/GIRO remain closed. Public cases are exploratory development evidence. Seeds and tariffs are nested repetitions, not independent timetables.

Freeze solver/version, one-thread settings, hardware, physical acceptance rules, scorer/model hashes, seed-generation policies, initial columns/prices, objective/energy units, numerical enclosure margins, allocation rules, stabilization parameters, stopping targets and run order. Allocation hyperparameters are presently unspecified: complete the manifest before any outcome inspection, without selecting them on this pilot. No new training is part of this budget. State historical training/label-cost amortization separately. A tiny implementation check requires separately resumed compute, followed by a final protocol freeze.

## Arms and information

For each of the 30 case/seed cells, acquire one common pool using three frozen seed-generation arms, each with at most 300 solver seconds. Their exact policies must be identified before launch. Preserve all replay-valid complete coupled fleet plans, deduplicate with a frozen rule, and charge scoring, construction, fixed-route charging completion and replay. Rejected candidates remain logged.

Run four seeded policies, each with a maximum 600 solver-second hull-stage allowance:

1. Full unrestricted pricing throughout.
2. Fixed learned/full pricing allocation, with a predeclared split/order.
3. Adaptive learned/full allocation, with predeclared observations, triggers and minimum certification effort.
4. The same adaptive rule plus additional stabilization, with its center/update/strength and any projection specified in advance.

Every seeded policy receives exactly the same acquired pool and seed information. Learned restricted pricing supplies candidates only; the full oracle supplies global bounds. The fifth arm is an unseeded full-pricing control with up to 1,500 solver seconds and the same ordinary initialization conventions where applicable. It receives no acquired seed pool. This is a comparison of complete algorithms as well as a conditional comparison of four oracle policies.

## Time and compute accounting

Freeze a single numerical end-to-end **wall-clock cap T** before launch. T is currently unspecified; solver allowances do not define it. Start its clock before instance-specific seed acquisition or, for the unseeded control, before its initialization. Include loading/scoring, model construction, master work, presolve, oracle solves, repair, replay and final verification. Stop at T even if a solver allowance remains; reserve verification time using a frozen rule. All five arms face T. The unseeded control may devote the whole cap to its own pipeline, subject to its solver allowance. Report early termination and unused allowance.

Each 300/600/1,500-second solver allowance is cumulative one-thread CPU across **all solver invocations in that stage**, including charging completion, restricted masters, pricing, and optimization used for conjugate computation or verification; it is not a per-call wall-clock TimeLimit. Track remaining allowance before each invocation. Measure process CPU for accounting and retain native solver runtime separately, since reported runtime may be elapsed time. Non-solver construction, scoring and replay consume the common wall-clock cap and recorded overhead.

With these cumulative stage allowances, the shared experiment spends at most 20 solver CPUh on four seeded hull stages (30 × 4 × 600 / 3,600), 7.5 on acquisition (30 × 3 × 300 / 3,600), and 12.5 on the unseeded control (30 × 1,500 / 3,600): **40 solver CPUh**, with a **45–55 CPUh envelope including overhead**. Historical diagnostics, implementation/timing checks and failed attempts draw from this same envelope; there are no uncapped extra solves. Record actual measured costs and halt or seek a separate allocation before exceeding the envelope.

Shared acquisition is performed once experimentally. Charge its actual measured elapsed/CPU cost to **each seeded algorithm's cold-start account**, but count it once in the actual experimental-spend ledger. Obtain cold-start curves by offsetting each hull-stage curve by that same acquisition time; reconstruct serial clocks rather than adding concurrent wall times. Never multiply shared acquisition in the spend ledger or omit it from algorithm costs. No seed/column/bound produced by another policy may flow into a run. Report 600-second conditional hull comparisons explicitly as conditional on supplied seeds; they cannot establish end-to-end savings. A repeated-query reuse scenario requires a declared reuse count, identical available artifacts and separate amortized accounting, without a free-reuse advantage.

## Certificates and logged fields

Keep the same unrestricted response domain X, intrinsic cost c and energy coordinates throughout. For each finite query p, accept only a validated global enclosure ell(p) ≤ V(p) = inf over X of c(x)+pᵀe(x). Restricted-model lower bounds are inadmissible. Compute L = max of ell(p) minus a verified **upper** enclosure of F*(p), including arithmetic/numerical allowances; a conjugate-maximization incumbent has the wrong direction. Stabilized master objectives do not themselves certify the original hull.

Build U from an explicitly feasible mixture of replay-valid complete fleets: nonnegative normalized weights, feasible combined load in dom F, and outward-enclosed mixture cost plus F of the mixed load. Master optimality is unnecessary; approximate weights require feasibility verification. Retain best valid L and U across rounds. Require finite L ≤ U; certified width W = U − L is nonnegative. Contradiction, invalid domain or replay failure triggers a certificate-integrity failure, never successful stopping. Distinguish rigorous enclosures from native tolerance-qualified ones.

Log case/group/input hashes; policy/solver seed; acquisition arm and artifact provenance; all stage elapsed/CPU times and memory; price/query/domain; restricted/full status; raw bounds and enclosure margins; conjugate method/value; mixture weights and validation; L/U/W trajectories; accepted physical bills/bus counts; rejection/repair causes; timeout/stop reason; and charged versus shared costs. Preserve the last valid enclosure if later work fails.

## Outcomes and stop/go

Freeze absolute/relative width tolerances, normalization scale and target rule before launch. Report final W at T and time to the frozen valid certificate target, using the same numerical standard for all arms. Unreached targets are right-censored at their actual cap/termination; integrity failures are reported separately, not discarded or assigned successful times. Compare paired case summaries averaged over three seeds, then timetable-group summaries and uncertainty where independent group counts permit. Do not pool seeds as independent samples. Predeclare how the strongest matched baseline is selected and handle censored comparisons without successful-only medians.

Advance if a candidate achieves ≥25% lower median final width or ≥20% lower median time to the frozen tolerance over the strongest matched-budget baseline, with all reported bounds valid and meaningful group benefit. Stop if price-policy iteration savings disappear after end-to-end overhead, validity fails, or censoring prevents the claimed target comparison. These are exploratory screens, not generalization guarantees. Cheap aggregate-load/cache reuse is **optional later, separately budgeted and validity-reviewed**, not a sixth arm in this pilot.
