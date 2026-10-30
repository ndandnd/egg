# Shared-budget repair results

Job 696067 completed in 214 seconds (exit 0; one allocated CPU; 8 GB requested;
maximum RSS 301,796 KiB). Both 2017 arms returned a five-bus route-cover
incumbent under the extended 30-second cover cap, and both resulting repaired
fleets passed independent physical replay. The cover solver stopped with an
open gap in both arms, so neither bus count is certified minimum.

| Arm | Cover status / gap | Buses | New direct repaired target cost | Archived source0 target cost | Archived target-verified cheapest/learned | Archived retained incumbent |
|---|---:|---:|---:|---:|---:|---:|
| Learned | time limit / 0.200503 | 5 | 689.100163 | 724.660042 | 689.474312 | 685.788696 |
| Cost only | time limit / 0.200000 | 5 | 691.228570 | 724.660042 | 689.474312 | 685.788696 |

Costs are in target cost units and the new direct costs are rounded from the
saved exact fractions. Both new repaired plans cost less than the archived
source0 fleet's target revaluation. The learned repair is 2.128407 below the
cost-only repair and 0.374149 below the historical cheapest-bill/learned
incumbent, but remains 3.311467 above the better archived retained fleet.
The cost-only repair is above both archived target-verified fleets. A fresh
cost-only hull column at 685.695043 is about 0.094 below the archived retained
incumbent; it is a separate feasible fleet, not the repaired candidate. This
single crossed comparison does not establish a general learning benefit.

Both new target-hull assessments ended `budget_exhausted`; their saved global
lower certificates and mixture checks replayed. Learned returned a lower
bound of 596.091736 and mixture upper of 685.087240. Cost only returned a
lower bound of 597.829694 and mixture upper of 685.542524. The global lower
bounds also lower-bound the physical optimum. Mixture uppers are hull results,
not necessarily physical fleet costs. Each independently replayed repaired
candidate is a physical feasible upper candidate; the cost-only hull column
at 685.695043 is a separate, cheaper feasible candidate. None of these gaps
closed. The cost-only lower bound is also stronger than the archived retained
target-hull lower bound of 585.913858, giving a same-market physical-optimum
enclosure of [597.829694, 685.695043] from the new lower and feasible hull
column.

A [review of 21 saved physical plans](SHARED_BUDGET_PHYSICAL_POOL_REVIEW.md)
independently replays that upper-bound fleet. At its own-load marginal prices,
another replayed plan lowers the price-taking objective by at least 5.092135
cost units while increasing true system cost. This is a witness at the saved
incumbent only: the wide physical bound prevents a conclusion about support of
the unknown exact optimum. The [candidate replay receipt](INDEPENDENT_REPLAY_SHARED_BUDGET.json)
also verifies both direct repairs, their hashes and shared charging constraints.

| Arm | Inference (s) | Cover (s) | Charging + native replay (s) | Repair total (s) | Independent replay (s) | Pool preparation (s) | Hull (s) | Result / child wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Learned | 0.075 | 32.732 | 0.792 | 33.600 | 0.105 | 0.296 | 61.193 | 97.892 / 98.388 |
| Cost only | 0.000 | 30.734 | 0.774 | 31.509 | 0.104 | 0.302 | 61.182 | 95.861 / 96.640 |

The cover stage consumed about the full 30-second cap in both arms, while
fixed-route charging with native replay and the independent replay each took
under one second. Hull checks
then took about 61 seconds per arm, so the full stage was dominated by
verification. This two-cell development run supports that the larger cover
budget found replayable routes where the earlier five-second cap did not; it
does not support a speedup claim or a general learned-policy benefit.

The cell ledger retains exact target-cost fractions, statuses, saved replay
flags, bounds, and per-phase timings in
[SHARED_BUDGET_REPAIR_CELLS.csv](SHARED_BUDGET_REPAIR_CELLS.csv). The
summarizer reads cell order from the frozen attempt design and can be rerun
with `--attempt` and `--output`.
