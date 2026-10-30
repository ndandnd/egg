# Cost-aware repair launch review

**Disposition: ready for the bounded development launch.** I reviewed the new
cost-aware decoder, four-cell runner, wrapper, and protocol delta against the
frozen stage-2 repair setup. I found no launch blocker.

For any two binary route covers, the learned-score difference is bounded by
`alpha * sum(abs(logits)) <= 0.25`, where
`alpha = 1 / (4 * max(1, sum(abs(logits))))`. Since pullout count is integral,
one additional pullout cannot improve the learned objective at an exact
optimum. `cost_only` minimizes pullouts and passes no prior to repair; its
inference flags distinguish attempted and completed inference. A minimum-bus
claim is emitted only for native status 0 and is scoped to structural route
covers, excluding charging feasibility. Time-limited incumbents retain native
status/gap and are not described as proved minima.

The frozen cases are only development seeds 2016/2017; the stage-2 model remains
frozen, with no refit or reserved-test inputs. The four cells use the declared
crossed order, one cover solve per cell, fixed movement order, HiGHS seed 0 and
one thread. Repair, fallback, independent replay, and target-hull stages remain
separate and bounded. The protocol correctly limits conclusions to this
unreplicated ablation and makes no speedup or learning-benefit claim.

Root reports 18 focused tests passed, the new wrapper passed `bash -n`,
`git diff --check` passed, and the 21 source/9 input hashes plus four-cell
design loaded successfully. Root retains cluster submission authority.
