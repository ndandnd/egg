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

The first bounded screen will use two declared synthetic base timetables and the
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
