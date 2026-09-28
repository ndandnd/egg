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

## First screen findings and immediate next step

Job 569799 completed in 35:57 on one CPU. All 32 declared stages are accounted:
10 native-certified, 10 bounded, 9 budget-exhausted and 3 ineligible. The public
hulls spent about 173 of 184 seconds in native pricing solves and only about
0.005 seconds polishing. Two columns were returned, but the remaining wall
budget did not allow a master solve using the second. The shifted multivisit
example instead reached the rational-bit limit. These are different limitations;
the historical QP lead does not establish a speedup for the public screen.

The next experiment should preserve time for processing newly found columns and
compare a separate reuse mode that accepts replayed feasible pools from bounded
predecessors. The strict certified-predecessor arm remains a baseline. Rebuild
the target-market mixture and obtain fresh pricing/global bounds; prior-market
weights, duals and certificates do not transfer. Include predecessor preparation
and checking time, preserve incomplete outcomes, and keep the same physical and
market cases for the first comparison. Define and freeze this pilot before
execution under the existing resource ceiling. Public enclosures are still broad;
this screen establishes neither a positive planner-hull gap nor a public reuse or
learning advantage. See `research-20260928/computational-results/attempt1/`.

The follow-up is now specified as a 24-cell hull-only pilot, with legacy cold,
reserved-time cold and reserved-time feasible-pool reuse arms. Each pays for
its own initial solve. The opt-in implementation and focused source review are
complete. Published execution source 77dee96 passed full CI 36385045833 and was
submitted once as job 572392 at 06:14 UTC, pending at the initial observation.
Collect its frozen inputs and sealed results before interpreting the pilot.
The design and stopping rules are in
`doc/FEASIBLE_POOL_PILOT_PROTOCOL_20260928.md`. This direct two-market reuse mode
does not yet support ancestral pools over longer market sequences.

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
