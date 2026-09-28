# EGG research journal — 28 September 2026 UTC

## Computational expansion

The user wants a substantial computational paper and suggests learning routes
to avoid repeated solving, beginning with reliable iterative optimization. This
continues the research beyond the delivered v0.5 draft. The referee-style critique
remains accepted: reduce audit prose, improve the public computational evidence,
make price-taking versus strategic behavior clear, add foundational citations,
and move the next manuscript to LaTeX. Historical results and PDFs stay intact.

Work is split by cost and purpose. GPT-6 Sol implements a bounded development
screen; Luna Max inventories public instances and primary learning literature,
prepares the next manuscript scaffold, and will independently review the screen.
Root sets the scientific comparison and resource budget. The existing hourly
research heartbeat is active again and should remain quiet on unchanged state.

The public inventory identifies 20 operator base timetables in the pinned Sistig
archive; only the 37-service Hildenbrand base is currently adapted to our model.
Its two depot variants must remain in one data-split group. The archive has
105-, 131- and 137-service candidates for expansion after input checks. Old
synthetic generator runs have a different terminal-SOC policy and cannot simply
be pooled with fully replenished NativeCase results.

The first screen is eight case–market combinations: two small synthetic cases
and both Hildenbrand depot variants, each at two posted supply-cost intercepts.
It runs a planner, two hull arms (cold and retained), and an own-price response
when a valid planner witness exists. All cases are development. The two-service
market preserves the known counterexample as a useful mechanism check; the
three-service case exercises repeated depot visits. This is a diagnostic screen,
not evidence that the method scales to many timetables.

The prospective protocol distinguishes algorithm work limits from hard complete
stage deadlines. All time, incomplete bounds and failures count. The resource
ceiling is one serial job requesting one CPU and 8 GB, with a two-hour allocation,
one native thread, no retry/requeue and the reserved node excluded. No new job
has been submitted at the time of this entry. The worker source and exact
manifest must be reviewed and published before launch.

The focused literature review distinguishes learned column selection, pricing
proposals and predict-and-repair. Our current hull columns are complete fleet
plans; route-level Dantzig–Wolfe pricing would be a different formulation.
Nearest-neighbor reconstruction and retained plans are required practical
baselines for any learned proposal. Learned feasibility, repair and global
verification must be timed separately; a predictor alone does not prove that
no better complete fleet plan exists.

An additional bounded offline probe is authorized on the old three-column
public restricted pool. It asks whether a numerical quadratic-program proposal
followed by exact simplex/replay checks can avoid growing rational arithmetic.
It uses existing saved columns and no new global pricing or cluster solver;
any improvement is only a restricted-pool result, not a new public hull bound.

The probe completed: a numerical proposal rounded to an exact simplex reduced
the three-column pool residual from approximately 0.00202 to 7.23e-8, with only
a 3.60e-8 objective decrease. Total probe function time was 0.244 s, excluding
imports and output writing; the proposal solver itself took about 0.0025 s.
The negligible objective change alongside a much smaller residual explains why
this is a promising way to unblock further global pricing, rather than a new
substantive cost result. It does not measure full-solver acceleration. Details
and reproduction are in research-20260928/computational-design/POOL_BOTTLENECK_PROBE.md.

## Next handoff

Finish the screen implementation and focused independent review, publish the
source and prospective protocol, freeze and submit once, then retain launch
receipts. Analyze stage bottlenecks and equal-quality reuse comparisons before
a larger sweep. Append one consolidated Google Doc update at a concrete launch
or result milestone. Continue the computational manuscript as new evidence arrives.

## First screen submitted

The reviewed execution source e39bc7e31ea21dae64365c31fa88a85e4b0de349 was
published and submitted once as Unicorn job 569799. At 03:26:12 UTC it was
PENDING (Priority); no allocation or frozen input existed yet. The dedicated
checkout is /home/nc437/egg-computational-screen-20260928. Nine focused harness
tests and independent implementation review passed. The current scientific
core is unchanged; outcomes are pending. The source's CI run is 36373363756.

A standalone numerical restricted-QP proposal helper is also complete with five
focused tests. It is not integrated into this baseline and makes no certificate
claim. Eberbach source-input adaptation planning proceeds independently.

At 03:28:45 UTC the job was RUNNING on snavely-cpu-01 with 1 CPU/8 GB.
Frozen input SHA-256: b36b15a5b9ac8945cff3b4cfd5e8441c705c3c536870f7a34c3d08e7f6f2dca2.
The execution commit's full CI run 36373363756 completed SUCCESS. No stage
outcomes are claimed before collection and analysis.

The Google Doc now contains one “Computational program update — 28 September
2026” append. Saved-to-Drive and exact prior-export prefix preservation were
verified; public receipt is under research-20260928/agent-notes/. Eberbach's
input-only plan confirms 105 services, 14 stops, one depot and 9 routes. Its roughly
10,000 movement choices warrant a model-size estimate before the next solve.
The optional one-trip-per-bus construction is a feasibility attempt, not a
necessary condition for the chained fleet model.
