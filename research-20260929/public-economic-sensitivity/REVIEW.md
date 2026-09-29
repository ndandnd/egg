# Prospective public sensitivity review

## Initial design review

The declared eight-cell sweep is a bounded, interpretable follow-up: two depot cases crossed with `(f, curvature multiplier)` values `(100,1)`, `(40,1)`, `(20,1)`, and `(40,2)`, with intercept `a=0.20` and base curvature `1/900`. Keeping both depot variants in the same timetable group and retaining all declared outcomes avoids treating related cases as independent evidence. The design correctly calls for fresh physical planner, whole-fleet hull, and eligible own-price response work in every cell; old hull bounds or witness costs cannot be reused after changing bus fees.

Before submission, the runner must make the scenario identity include the depot case and exact economic parameters, and must rebuild the cost model for `D`, `CH`, and response objectives consistently. In particular, each bound and replayed upper witness must use that cell's `f`; scenario-specific cache keys and hashes must prevent a valid-looking old cost, load identity, state identity, or hull interval from crossing scenarios. Freeze and report the exact coefficient rule (`b = multiplier × 1/900`) alongside `a=0.20` so scenario labels cannot obscure which market was solved.

The own-price response must use the gradient of the on-time, replayed planner incumbent from that same depot/scenario cell, preserve its plan identity and saved price vector, and solve over the matching physical feasible set with the same scenario cost. Report the incumbent's regret separately from planner suboptimality, with bounds that account for the `D` interval; do not interpret an incumbent's price response as regret at an unknown optimal fleet. The convexified hull must represent the same whole-fleet choices and scenario objective as `D`, with the expected convexification as the only intended difference.

Only complete, on-time, ordered native intervals should contribute to gap or regret arithmetic. Late, failed, missing, or inconsistent cells must remain explicit with their outcomes and measured time/call fields; a missing stage must not be filled by an old bound or by the analytical availability/cardinality grid. Keep that analytical lower bound visibly separate from native bounds and do not filter cells based on the sign or usefulness of their result.

The worst-case child caps total `8 × (210+210+90) = 4,080` seconds. If all 24 children receive 10-second TERM and 2-second KILL grace, the maximum becomes 4,368 seconds, leaving 1,032 seconds under the 5,400-second controller. The 5,700-second outer cap leaves 300 seconds before the 6,000-second Slurm limit for setup and cleanup; the implementation should preserve these nested limits and one-thread/no-retry policy.

This is a design review, not a launch approval. The source, scheduler wrapper, and focused tests still need review for the cost/identity, interval-admission, lineage, failure-accounting, and resource guarantees above.
