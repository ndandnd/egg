# Multivisit cold budget-sizing diagnostic

This is a new, eight-cell **development** diagnostic on the existing
three-service multivisit physical case, under both its original and changed
markets. It tests two explicit coordinator limits on cold iterative hull runs.
It does not rerun, alter, or replace the frozen retrieval comparison or its
pending exception. No reserved evaluation data, new case, learned method,
solver claim, or automatic expansion is in scope.

| Factor | Levels |
| --- | --- |
| Pricing-call cap | 4, 16 |
| Projected rational-bit cap | 4096, 8192 |
| Market | Original state 0, changed state 1 |

This gives the full 2×2 factor grid independently in each market. The same
physical case is used in all cells. State 0 uses four intercepts of 0.20;
state 1 uses 0.18, 0.18, 0.22, 0.22; both use curvature 0.20. Each cell is
independent and cold. Use the native LP master and compact path-flow pricing
with GRB, one thread, and `Seed=0`. Disable retained starts/pools, pricing
reserve, cache, and reuse. Fix all other controls: 60 s coordinator wall,
45 s native phase, 64 master calls, pool cap 64, 64 pairwise-polish steps,
20 s polish limit, epsilon `1e-4`, and pool tolerance `1e-6`. The 64 master/pool
headroom prevents the 16-call level from being masked by the old six-master
limit. Reverse factor order between markets. This is a single-seed diagnostic,
not a repeated-trial estimate or a speedup claim.

Give each child a 90 s hard deadline. On expiry, send TERM and wait 10 s, then
send KILL and wait 2 s; a return during termination grace is late and must
remain `on_time=false`. The controller cap is 900 s, outer-shell cap 1000 s,
and Slurm allocation 1200 s, one CPU and 8 GB, excluding
`scaglione-compute-01`. No retry or requeue. Record
all eight outcomes, including failed, timed-out, late, and unstarted cells.
Only report assessed, on-time global bounds; preserve stop reason, actual
pricing/master calls, maximum rational bits, child time, and recorded component
times. Missing times stay unknown.

Compare pricing-call caps at each fixed bit cap, and bit caps at each fixed
call cap, separately by market. The arithmetic choice can change subsequent
prices and columns, so factor contrasts do not hold the price path fixed. If
wall, polish time/steps, master, or pool limits bind first, mark the intended
factor as censored. Certification at 16 calls is a question, not an
assumption; a mixed or censored result does not authorize more cells, another
seed, or an ML comparison without a separate bounded scientific design/review
under the standing authorization; this is not a routine user-approval gate.
