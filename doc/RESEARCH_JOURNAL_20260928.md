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
