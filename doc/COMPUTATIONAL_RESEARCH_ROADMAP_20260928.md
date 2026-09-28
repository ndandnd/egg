# Computational research direction — 28 September 2026 UTC

The user chooses a computational paper with many examples, reliable iterative
optimization first, and a possible learned route-proposal method afterward.
This supersedes the completed-draft stop and the suggested theory-only direction.
It does not authorize relabelling old results, opening protected evaluation data,
publishing private GIRO data, or spending reset credits.

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

The public archive contains 20 distinct selected-operator base networks. Only
Hildenbrand has been adapted and checked for the current physical model. Metadata
identifies Eberbach (105 services), Dreieich (131), Bad Nauheim (137) and
Pfaffenhofen (323) as plausible next intake candidates; these counts do not imply
that their energy, depots or operating assumptions have been validated. After
the diagnostic screen, adapt a small number of these independent networks and
build synthetic families with increasing service counts and variation in temporal
overlap, battery size and charger scarcity. Freeze grouped evaluation assignments
before inspecting comparative outcomes. The two tiny synthetic diagnostics are
regression anchors, not evidence of scalability.

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
independently reviewed with 26 focused tests passing; full CI is pending.
It has no measured online performance result yet.
Different physical cases cannot automatically share these certificates. The
core preserves measured source work and leaves unmeasured child/preparation
costs explicit for the later experiment runner.

Then integrate the existing numerical restricted-QP proposal under physical
mixture replay and global-bound checks to address projected rational-bit stops.
Pricing remains expensive, and a useful master proposal does not prove a global
optimum. Use focused tests and a new prospective comparison before counting any
online benefit. Broader independent public timetables and retained/retrieved
proposal comparisons follow these baseline corrections; reserve grouped test
networks before training. Do not repeat broad qualification campaigns or
reinterpret completed runs.

## Manuscript direction

Retain the exact mechanism and replication results, but support the computational
story with substantive multi-instance comparisons. Move reuse development and
qualification histories out of the main narrative. Use one reproducibility
paragraph plus supplementary detail. Plan a LaTeX source and a roughly 150-word
abstract. Consolidate compatible bounds and explicitly state the later numerical
flat-price optimum; keep exact and tolerance-qualified claims distinct. Add the
foundational pricing/aggregation/EV-coordination literature identified in review.
Explain competitive price support and strategic price impact as distinct questions.
Do not promote the old unresolved nonlinear run as the main computational figure.

## Execution and cost controls

GPT-6 Sol handles implementation/analysis; Luna Max handles supporting literature,
inventory, independent checks and documentation. Astra coordinates. Keep handoffs
short; avoid broad JSONL output, redundant audits, repeated full-suite tests,
qualification chains or repeated empty queue polls. One bounded work package per
follow-up. Back up meaningful results and append consolidated Google Doc updates.
Flag major scope/compute/data-release choices; routine authorized work continues.
