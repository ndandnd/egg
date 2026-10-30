# Prospective public economic sensitivity (not submitted)

This follows the matched six-cell physical-planner/response package. It is a new
development study, not a retry of the failed frozen retrieval comparison.
The current f=100 scenario remains a control; no scenario is selected or dropped
based on obtaining a positive gap. Both depot variants remain one Hildenbrand
timetable group, and no reserved independent test timetable is opened.

Candidate first public block: both depot variants, the original flat-intercept
nonlinear market, and four fixed scenarios (f, curvature multiplier):
(100,1), (40,1), (20,1), (40,2). Intercept remains0.20; base curvature is1/900.
Eight case/scenario cells permit a lower bus fee and a curvature interaction
without an unrestricted parameter search. The next block would address the
changed intercept pattern only if the first block produces informative bounds.
No actual two-/three-bus crossover is assumed: the approximate32–44 numbers
from the old bound are only certificate thresholds.

For every declared cell report physical D bounds, whole-fleet CH bounds, the
nonnegative gap interval, incumbent identity/fleet size, own-price regret with
planner-suboptimality bounds, full time, calls and all failures. Record the
availability/cardinality analytical lower separately from native bounds.
Changed vehicle cost creates a new cost-and-load identity even though physical
feasibility is unchanged; update all hashes and do not import a stale witness
cost, state identity, or native bound.

Prospective ceiling, to be frozen with an implemented runner before submission:
one serial job, one CPU,8GB, one native thread, seed0, no retry/requeue, exclude
scaglione-compute-01. Per cell: planner180/160s wall/native with16rounds,
QP hull180/160s with16pricingcalls/64mastercalls/8192bits, response60/45s.
Hard child caps210/210/90s; controller5400s, outer5700s, Slurm100min. This is
within the standing two-hour ceiling. Stops/incomplete cells are retained.
Never reuse a bound across modified economic scenarios without recomputing its
valid objective and proof. No native cuts are silently introduced in this block.

The analytical grid in `../charging-availability-bound/bounds.json` is generated
without optimization, covers both markets at f20/40/100 and curvature1/2, and
informs interpretation. It neither predicts nor establishes positive gaps.
If the present six-cell diagnostic reveals a correctness issue, repair it before
this public block; if it merely returns null gaps, retain them and proceed with
the declared question. Resource changes beyond this ceiling must be flagged.
