# Computational research direction — 28 September 2026 UTC

The user chooses a computational paper with many examples, reliable iterative
optimization first, and a possible learned route-proposal method afterward.
This supersedes the completed-draft stop and the suggested theory-only direction.
It does not authorize relabelling old results, opening protected evaluation data,
publishing private GIRO data, or spending reset credits.

## Active direction — solver data and learned proposals, 30 September 2026

The user now explicitly requests cluster work and model training in parallel with
solver improvement, even if the research takes a long time. This overrides the
older postponement of learning and idle-monitor pause instructions below. The
hourly heartbeat is active; future runs must inspect the newest continuation
checkpoint and campaign receipts, then advance a justified bounded work package.

The first campaign builds independent synthetic timetables, records bounded
native solves, trains a CPU route-topology predictor and compares feasible
projected starts against cold solving and simple reuse. Incumbent labels remain
provisional unless certified. Source-pool generation time, prediction, projection,
replay and global verification are reported separately. Two independent test
seeds remain reserved; development outcomes do not become confirmatory evidence.
Initial concurrent budget is one job/one CPU/8GB/two hours, with a tighter first
batch recorded in `research-20260930/learning-campaign/PROTOCOL.md` before launch.
Scale only after examining complete receipts and recording the next budget.

## Coauthor discussion draft 0.10 — 29 September 2026

The review response clarifies the computational role of column generation and
the institutional role of dual price adjustment. Archived same-toy evidence
uses three pricing calls; the separate 20,000-call analytic run stops just
outside a 1e-6 best-bound error. A direct proof now establishes convergence
of the quadratic recurrence's step-weighted hull average, despite continuing
physical bus-count switches. A best-price corollary, a two-institution table,
the observed HiGHS endpoint and clearer generator economics complete the change.
The reserved-pair link to Alizadeh remains an analogy, not a proved network limit.
The 23-page draft and targeted reviews are ready for coauthor discussion; public
support/scalability remain unresolved. No new solver or cluster experiment was
run. The next computational work remains the formulation study below; idle
monitoring remains paused.

## Prior supply-side direction — implemented in draft 0.9, 29 September 2026

The user selected hourly convex generation with ramp limits and balance prices,
dual decomposition, a subgradient support theorem, and Shapley–Folkman framing.
The first bounded package is complete: nonsmooth Proposition 1, qualified dual
best-value convergence, a 20,000-call analytic illustration with full trace, and
an exact two-generator/three-hour example. The latter gives physical 112,
hull 110.5, gap 1.5; relaxing only the up-ramps gives equality at 104. It also
tests support over a nonunique dispatch-price face. Two new figures accompany
the 21-page author-review PDF. See `research-20260929/generation-dispatch-pilot/`
and `research-20260929/nonsmooth-coordination/` for proofs, receipts and reviews.

This adds a dispatch value function, not generator commitment or a network.
The middle service hour and its background load remain explicit. Positive gap
rules out balanced joint convergence of exact responses, not universal schedule
nonconvergence. The O(1) operator incentive is a construction-specific result;
Hreinsson et al. supply aggregation context rather than its rate proof.

The timetable-scale fleet formulation still gates the computational program.
Improve and compare its exact-oracle formulation before running many dual
iterations, adding nodal prices, or training proposals. A proof-driven check
of the candidate cardinality/energy row and a same-model direct quadratic
planner comparison are prospective options; neither is currently an implemented
cluster launch. No new cluster work or budget was used here. Conditional
monitoring stays paused, while meaningful local research can continue on request.

## Prior review response — v0.8 and economic evaluation, 29 September 2026

The reviewed v0.8 manuscript merges both markets with the strongest public
bounds, shows the exact undamped toy price cycle, states a posted-tariff
institution, and treats incumbent regret as a diagnostic. Three relevant
references are restored with primary-source checks. A universal charging-visit
availability argument improves exact public floors by4.86–12.03 cost units;
positive connector caps do not bind in these four bounds. The proof/source/review
are in `research-20260929/charging-availability-bound/`. None proves a positive
public gap. No native cut, solver status or historical result is changed.

Job 597526 completed all six physical D and six own-price responses in 176 s.
The three flat-intercept cases have positive native D−CH gaps (about 0.005,
0.114 and 0.007), while the three changed-intercept cases remain zero-compatible
within about 0.000002. The largest positive gap is below 0.03% of physical cost;
these are related cases in one development family, with native solver/replay
tolerances. Results and independent review are in
`research-20260929/economic-support-diagnostic/results-attempt1/`.
The v0.8 PDF predates this package. Next, the prospective public economic
sensitivity is specified in
`research-20260929/economic-support-diagnostic/NEXT_PUBLIC_SENSITIVITY.md`:
both depots, four bus-fee/curvature scenarios including the original control,
one CPU/8 GB/100 min ceiling. The reviewed implementation was submitted once
as job 600028 on 29 September at 02:11:37 UTC and completed in 54 min 9 s.
All 24 declared stages returned on time. All eight native cost-gap intervals
include zero: the public question remains unresolved. All planners remain
bounded and all cold hulls exhausted their wall budget; three own-price
responses certified and five remain bounded. The 204–563-unit regret concerns
the returned uncertain planner schedules, not optimal public dispatches.
Source, protocol
and launch review: `research-20260929/public-economic-sensitivity/`; receipt:
`research-20260929/cluster/public-economic-600028.json`. The fixed range predates outcomes;
keep zero/unresolved gaps. The32–44 fee values are dual-certificate thresholds,
not proven physical fleet crossovers. Only then compare retained/nearest-neighbor
proposals at common quality; independent test groups remain reserved and ML waits.

The complete eight-case table, figure and diagnosis are in
`research-20260929/public-economic-sensitivity/results-attempt1/`.
Recorded native MIP time accounts for 1411.77 of 1469.95 planner-child seconds.
The hull made only 24 total pricing calls; its QP proposal and exact replay
counters sum to 9.48 s, with no rational-size or master-call stop. Raising those
master caps would not address the measured bottleneck. Saved individual hull
fleet columns provide three material physical-upper improvements without
optimization; these are separate from the hull mixture and from the original
planner whose regret was measured. No exact ideal upper is newly certified.

The next scientific target is a proof-driven check of whether the existing
cardinality/energy inequality supplies a nonredundant native root-relaxation
improvement. Its relationship to aggregate energy-balance rows must be checked
before spending on another solve. This is a recommendation, not an implemented
launch or authorization to enlarge resources. No new cluster job is submitted;
do not keep polling completed 600028. A wider sweep and ML training wait for a
useful certificate strategy. The user's conditional monitor was paused after
this result package and its local follow-up, with no active experiment or
concrete next launch under implementation.

## Review-driven correction — v0.7, 28 September 2026

The author's external review identifies a missing analytical baseline and
cap-dependent development comparisons. The revised v0.7 manuscript reports D,
CH, their gap and own-price regret of a named planner incumbent together.
Analytical cardinality/energy floors must accompany computational bounds.
The historical reuse and start pilots remain in a separate supplement;
their failures, caps and resource use are not erased or relabelled.

The computational-paper objective remains active. The analytical baseline now
has an opt-in reporting implementation, restricted to the two reviewed public
physical cases and supported price-only changes. It checks proof lineage and
keeps ideal bounds separate from native results; conditional combinations use
native upper witnesses only. It does not enter the coordinator, pricing cache,
native status or MIP cuts. Code, focused checks and a replay preserving all 32
historical rows are in `research-20260928/analytic-baseline-integration/`.
The completed eight-cell sizing diagnostic (job 591255) now shows that the
three-service cold baseline certifies with five calls in the original market
and six in the changed market when the bit limit is 8192. Four-call arms stop;
4096 bits also stops the changed market even with sixteen calls. This diagnoses
the earlier cap-dependent tiny-case advantage, without a reuse speedup claim.
Results are in `research-20260928/budget-sizing-diagnostic/results-attempt1/`.
The larger cold-baseline viability screen is now complete (job593482, source
e3ac75f): all three cheap-window target cases certify, while the three flat-price
cases stop at projected8192bits with useful narrow bounds. These 8/16/24-service
cases are nested variants of one development family. At24services, pricing is
the largest measured runtime component; arithmetic prevents flat-price
certification. Results: `research-20260929/cold-baseline-viability/results-attempt1/`.
The matched numerical-QP diagnostic is now complete (job595105, source60a66e7):
all six cells meet the same numerical accuracy target, resolving the three
flat-price arithmetic stops under unchanged caps. Times are mixed; this is no
general speedup claim. Paired evidence and figure are in
`research-20260929/qp-baseline-diagnostic/results-attempt1/`.
The matched physical-planner/own-price-response package is now complete, as
recorded above. It reuses completed CH bounds, preserves all outcomes and names
the incumbent whose regret is measured. A public fee/curvature study follows;
successful CH solves alone do not prove a cost gap or lack of support.
Then design a wider common-quality cold/retained/nearest-neighbor comparison,
with independent test groups still reserved. Preserve all outcomes; no naive
bit expansion or ML training. A pricing cut
needs its own valid energy/cardinality inequality, not the hull-objective bound pasted into a
linear-price subproblem. Record whether a native start was accepted before
interpreting its effect; seed repetition and common-quality targets follow a
viable configuration. The existing no-incumbent bug is already repaired and
independently tested; new experiments must retain the failed historical records.

The frozen retrieval design still uses four pricing calls and 4096 arithmetic
bits. Review those limits against measured stops before deciding how to proceed;
its old preflight failure and the pending one-replacement exception remain as
recorded. This manuscript correction does not launch or authorize that
replacement, and the old protocol cannot silently change. Eberbach has already
been adapted and replayed as described below; neither it nor future independent
timetables have comparative results yet. No training or protected test access.

Old-terminal-inventory iteration outcomes cannot be imported as current-model
results. Cycling of an update rule does not prove that no supporting physical
plan exists. A new same-model convergence study is a distinct possible work
package, not a prerequisite implied by this editorial correction.

## Research questions and order

1. Establish complete physical-planning, full-fleet hull and own-price-response
   calculations across a varied set of declared timetables and market conditions.
   Diagnose where routing, continuous charging, restricted-master optimization
   and fresh global pricing consume time. Preserve incomplete results.
2. Compare cold solving with retained physical columns, then nearest-neighbor
   retrieval with a feasible charging/route repair. Compare equal solution quality
   and all online work, including checking and repair. Existing small reuse cases
   are preliminary evidence, not a sufficient learning benchmark.
3. If there is useful remaining work, learn a route/connection proposal from
   training timetables. Test direct prediction, prediction plus repair, and
   prediction followed by global verification separately. The existing hull
   columns are complete fleet plans; a route predictor must assemble and repair
   a complete fleet before entering that master. Direct prediction may deliver
   a useful feasible schedule without a global certificate; a learned
   proposal alone does not establish optimality or a price-support gap.
4. Report feasibility, objective/bound gaps, regret, calls, complete wall time,
   failures, offline training/data-generation cost and amortization. Do not call
   time-limited incumbents optimal labels. A null learning result is retained.

Keep the computational question connected to the paper: how much repeated
planning is needed to measure and respond to prices, and can a reusable or learned
proposal reduce that work without concealing the price-support failure? A fast
feasible route prediction and a globally verified hull calculation are different
deliverables. Score learned routes by complete-fleet feasibility, objective and
time, not agreement with one arbitrary optimizer route label; different routes
may be equally good. Store incumbent quality and lower bounds with any training
label so time-limited solves do not become supposed ground truth.

## Data and evaluation

Use public timetable data and explicitly synthetic generators. Group every depot,
tariff, curvature and timing variant of the same base timetable together when
splitting train/development/test; depot15 and depot16 are both Hildenbrand, not
independent train/test networks. Reserve independent base networks for evaluation
before training. A second evaluation should vary the economic/physical regime.
All initial screening cases are DEVELOPMENT. They cannot later become untouched
ML test data. No existing protected A6/B3/confirmation data or private GIRO enters.

The public archive contains 20 selected-operator base groups. Hildenbrand and
Eberbach (105 services) have now been adapted to the current physical model.
Eberbach's conservative one-service-per-bus witness passes physical replay with
full replenishment; its 105 buses are not an optimized fleet result. Its compact
model has an estimated 291,637 variables and 312,316 rows, without allocating a
native solver model. The first solve must measure construction within its cap.
Metadata counts for other operators do not imply physical-model validation or
semantic independence. The prospective group reservation and synthetic scaling
design are in `research-20260928/benchmark-intake/`; all existing screens remain
development. The two tiny synthetic diagnostics are regression anchors, not
evidence of scalability.

The first bounded screen used two declared synthetic base timetables and the
two already modeled public depot variants, with two market states per case.
Compare cold/retained hull solves and compute common physical/own-price results.
The new driver uses the existing physical model. A failed or uncertified
predecessor makes a retained comparison ineligible rather than silently replacing
it with cold success. Exact cases, caps and source are frozen before execution.
Initial resource ceiling: one serial CPU job, one native thread, request 1 CPU/8 GB,
maximum 2 hours, no requeue/retry, exclude scaglione-compute-01. Record allocation
if Slurm grants additional CPUs. Other-project jobs remain untouched.

Polishing work limits are algorithm stopping rules in this NEW development
screen, under a separately enforced complete-cell deadline. Returned valid bounds
remain useful when iteration stops. Record actual time and any overshoot; do not
claim a time-to-target success after a hard deadline. The old 5 s protocol failure
remains immutable. If numerical restricted-master work dominates, improve that
bottleneck before attributing benefit to route learning or launching a large sweep.

The diagnostic presentation will pair a complete 32-stage outcome table with
runtime and bound-quality panels. Show each cold/retained arm's initial-state
cost, second-state cost and two-state total; a transition-only timing is not a
total speedup. Show unsuccessful and ineligible stages explicitly. Component
times are available only where recorded, and missing times stay missing rather
than becoming zero or an inferred routing cost. Whole-job Slurm elapsed includes
setup that stage sums omit. Compare time to a common quality target when the
traces support it; otherwise report time and final bounds together without a
speedup claim. Keep the two Hildenbrand depots grouped. Fraction-valued exports
of native numerical bounds do not convert them into ideal-model exact proofs.

## Current computational evidence and next step

The completed first screen (job 569799) identified public pricing as the main
runtime cost: new plans arrived too late for another master. A separate matched
24-cell pilot (job 572392, source 77dee96) now confirms that a ten-second reserve
inside the pricing budget lets all four public cold runs process a second plan.
Their upper bounds improved by roughly 18–69 cost units. All 24 cells returned
on time: 7 certified native enclosures and 17 budget stops. Both public depots
remain one development timetable group. Public optimality gaps remain open.

Feasible-pool reuse certified the shifted three-service diagnostic, where cold
runs reached an arithmetic limit. In the public cases it improved upper costs
but weakened fresh lower bounds: the final interval narrowed in one case and
widened in the other. Paid two-market time was slightly higher than reserved-time
cold solving. This is not yet an equal-quality speedup or learning result.
Full tables, figures and evidence are at
`research-20260928/feasible-pool-pilot/results-attempt1/`.

A separate posthoc calculation exposes a missing baseline: a physical pricing
bound at a fixed price is still valid for the same physical feasible set after
changing only the supply cost. Recomputing the target Fenchel conjugate tightens
this run's shifted public intervals to widths about 64 and 70, with no additional
optimization. It changes no frozen status or timing. An explicit opt-in checked
oracle-bound cache has now been implemented, with source lineage, target-market
conjugate re-evaluation and a fresh-target-pricing certification gate. It is
independently reviewed with 26 focused tests passing, and implementation
8a54521 passed full CI 36396410119. The completed ordered comparison below
now measures its online work and resulting bounds; no equal-quality speedup
has been established.
Different physical cases cannot automatically share these certificates. The
core preserves measured source work and leaves unmeasured child/preparation
costs explicit for the later experiment runner.

The numerical restricted-QP proposal is integrated under exact simplex and
physical-mixture replay, with a fresh-pricing certification gate. The completed
ordered 32-cell comparison (job 575215, source f4b342d) now gives 11 numerical
certifications, 18 budget-exhausted outcomes and three child failures. All
attempts and paid time are retained. Both public depots still share one base
network; these are development results rather than replicated scalability or
learning evidence. Results and figures:
`research-20260928/solver-baseline-comparison/results-attempt1/`.

The clearest positive finding is a within-run bound decomposition. In the two
public cache-enabled target runs, inherited evidence improves the lower bound
by 98.82 and 69.83 over each run's own fresh-pricing lower. The final numerical
intervals are [405.83, 471.52] and [420.45, 491.46]; paid two-market time is about
352 seconds each. The intervals remain open, with Gurobi tolerance qualifications.
Exact replay of stored numerical values does not turn the native lower into an
ideal-model proof. No public optimality, equal-quality speedup or learned benefit
is established. Convex mixtures remain distinct from executable whole fleets.

The numerical master stayed within the configured arithmetic limit in the
completed public cache runs. Its public targets without cache both failed;
a cold public target also failed. All three native calls returned no new
incumbent (`NO_SOLUTION_FOUND`), and the compact wrapper incorrectly checked
an absent plan's extraction policy. An earlier valid pricing result exists in
each failed trace. This identifies no-plan handling rather than an invalid
completed physical witness; it does not reclassify those failed attempts.
Physical pricing remains the principal measured runtime cost.

The no-plan return path is now repaired in the compact wrapper and shared
coordinator, with 156 focused tests passing. A distinct unresolved-call event
preserves the full raw return without creating a column, admitted lower or cache
record. Earlier verified lower and feasible mixture remain bounded but
uncertified; without both, the state remains unresolved. Invalid present
witnesses and claimed success without a witness remain rejected. The event
reader accepts the new record while the cache-bound admission contract stays
strict. Independent review and publication checks are recorded in
`research-20260928/no-plan-repair/`. Historical outcomes remain unchanged.

An opt-in physical-pricing start now maps an already checked complete fleet
to every compact movement binary, leaving continuous charging to the native
solver. The core passed 40 focused pure tests and a small CBC functional check;
this supplies no Gurobi or public-case performance evidence. Hint submission,
acceptance and a returned certified result remain different observations.
Start validation and setup are measured inside the pricing wall deadline.
Retained master columns alone still do not supply a native solver start.

The fixed-price starting-point pilot is now complete: job 577225, execution
source 6759daa, 16 calls and 22m14s on one CPU. All eight synthetic calls were
numerically certified; all eight public calls returned bounded results at their
160-second native phase allowance. Common feasible baselines and counterbalanced
order were frozen before execution; the public depots remain one development
timetable group and one observed solver seed.

The quality effects are mixed. Depot 15's linear query has the same incumbent
and a weaker lower bound with a start. Its marginal-price query improves the
incumbent by 1.10 but weakens the lower bound. Depot 16's linear query ties; its
marginal query improves the lower bound by 11.78 with the same incumbent. The
original source fleet costs are 0.32–2.74% above the best newly returned public
incumbents, which is not a bound on their distance from the unknown optimum.
Returning a feasible proposal and certifying its quality remain separate tasks.
The pilot establishes no general acceleration, full iterative speedup or learned
benefit, and does not justify immediate integration of starts into the full method.
Tables, figures and recorded paid work:
`research-20260928/pricing-start-pilot/results-attempt1/`.

The benchmark intake package adds Eberbach and reserves future base groups before
training or comparative outcomes. Five synthetic cases are now generated and
physically replayed: 8/16/24 services for development seed1006, plus16 services
for each of seeds1012 and1009. Their mandatory service-energy lower bounds show
real charging pressure outside any four-hour/90kW window in all16/24-service
cases; the8-service witness fits. Every prespecified case is retained.

The separately frozen retrieval comparison was designed for these five cases
plus Eberbach. It failed before optimization and its one-replacement exception
remains pending. Its design has two source markets building the same checked whole-fleet pool
for retained columns, nearest-source-price retrieval and exact cheapest-current-
bill selection; cold iterative solving is the common baseline. Target bounds
require fresh global pricing, with no inherited bound cache or native MIP start.
Direct proposal feasibility/quality, checking, full verification and paid source
work are distinct measurements. A shared target planner and own-price response
keep the price-support question central. Cross-timetable transfer is outside this
price-only comparison. Full protocol, caps and case order are in
`doc/RETRIEVAL_COMPARISON_PROTOCOL_20260928.md`; current launch status is in
`doc/AUTONOMOUS_RESEARCH_CONTINUATION.md`.

Do not conduct another start or retrieval sweep to seek a favorable result.
The readable draft has been consolidated and the bounded stopping-limit/master
diagnostics are complete. The immediate research priority is the joint
D/CH/regret evidence on the now-solvable development cells.
Learned proposals remain optional; reserved independent test groups stay closed
until a later declared evaluation.

## Manuscript direction

The current author-review manuscript is the17-page LaTeX draft0.8:
`output/pdf/egg-journal-v0.8-reviewed-draft.pdf`, built from
`paper/latex/main.tex`. It reports joint cost/gap/incumbent-regret evidence and
analytical public bounds. Historical reuse/start comparisons are in a separate
seven-page development supplement. Prior drafts remain preserved.

This first-draft milestone does not close the computational research questions.
The attempted six-case comparison stopped before optimization; it contributes
no algorithm evidence, and one replacement remains a pending user decision.
Nearest-neighbor retrieval and learned proposals remain untested. The next
bounded task is joint D/CH/regret evaluation on the six completed QP development
cells, separate from the failed retrieval attempt and its pending exception. Keep one computational paper as
the working target and a short theory paper as an editorial fallback. Resolve
informative public bounds whether the eventual gap is positive, small or zero;
do not select experiments until a positive result appears.

Retain the exact mechanism and replication results, but support the computational
story with substantive multi-instance comparisons. Move reuse development and
qualification histories out of the main narrative, as implemented in v0.7.
Keep exact and tolerance-qualified claims distinct. Preserve the foundational
pricing/aggregation/EV-coordination antecedents and the distinction between
competitive price support and strategic price impact. The next effort should
produce stronger computational evidence, not another manuscript-polishing cycle.

## Execution and cost controls

GPT-6 Sol handles implementation/analysis; Luna Max handles supporting literature,
inventory, independent checks and documentation. Astra coordinates. Keep handoffs
short; avoid broad JSONL output, redundant audits, repeated full-suite tests,
qualification chains or repeated empty queue polls. One bounded work package per
follow-up. Back up meaningful results and append consolidated Google Doc updates.
Flag major scope/compute/data-release choices; routine authorized work continues.
