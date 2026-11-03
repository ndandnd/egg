# Shared-interval repair results

Job 695461 completed in 171 seconds (exit 0; one allocated CPU; maximum RSS
205,836 KiB). Both 2016 arms produced a new, independently replayed feasible
four-bus fleet with shared interval limits enforced. Both 2017 covers stopped
without an integral incumbent and fell back to the same archived source
fleet; those cells have no new hull assessment.

| Case | Policy | Cover result | Physical candidate | Target cost (rounded cost units) |
|---|---|---|---|---:|
| 2016, 20 services | cost-only | 4-bus incumbent; status 0, gap 0 | New replayed 4-bus repair | 522.792412 |
| 2016, 20 services | cost-learned | 4-bus incumbent; status 1, gap 0.000529 | New replayed 4-bus repair | 516.926077 |
| 2017, 28 services | cost-learned | Stopped without integral incumbent | 5-bus archived source fallback | 724.660042 |
| 2017, 28 services | cost-only | Stopped without integral incumbent | 5-bus archived source fallback | 724.660042 |

For the 2016 case, both new repair costs are below the archived four-bus
source-only baseline cost 553.474774 ([archived source replay](CHARGING_CAP_REPAIR_CELLS.csv)),
while the prior target-verified feasible control remains cheaper at
515.515556. That control is historical target-check evidence, not a direct
prediction from this pilot. The learned repair is 5.866335 cost units below
the cost-only repair in this one case, but its cover ended with an open MIP
gap; this single comparison does not establish a learning advantage. In
2017, both arms returned the same source fallback. Its cost 724.660042 is
above the archived target-verified feasible control at 689.474312.

The two 2016 native target-hull assessments both ended `budget_exhausted`
with their saved global-certificate and mixture checks replayed:

| Policy | Global lower bound | Mixture upper |
|---|---:|---:|
| cost-only | 514.844508 | 515.508483 |
| cost-learned | 515.356816 | 515.471130 |

All values are in cost units. The global lower bounds also lower-bound the
physical optimum. The mixture uppers are hull-mixture results, not costs of
physical fleet plans. Combining the stronger current 2016 lower bound with
the prior target-verified feasible control gives a physical-optimum
enclosure of [515.356816, 515.515556]; the gap remains open. The native hull
status did not prove physical optimality. The 2017 fallback cells skipped a
new hull, recording an empty assessment and zero hull time.

| Case / policy | Inference (s) | Cover (s) | Charge (s) | Repair total (s) | Independent replay (s) | Fallback select/replay (s) | Pool (s) | Hull (s) | Child (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016 cost-only | 0.000 | 3.659 | 0.352 | 4.012 | 0.053 | — | 0.147 | 60.631 | 67.874 |
| 2016 cost-learned | 0.037 | 5.378 | 0.348 | 5.764 | 0.051 | — | 0.147 | 54.788 | 63.811 |
| 2017 cost-learned | 0.077 | 5.770 | — | 5.855 | 0.101 | 0.486 | 0.000 | 0.000 | 9.312 |
| 2017 cost-only | 0.000 | 5.513 | — | 5.539 | 0.099 | 0.483 | 0.000 | 0.000 | 8.902 |

The 2017 repair phase ends at the cover failure. The CSV includes the exact fractions and
per-cell status fields: [SHARED_INTERVAL_REPAIR_CELLS.csv](SHARED_INTERVAL_REPAIR_CELLS.csv).
The learned 2016 repair phase took longer than cost-only (5.764 versus 4.012
seconds), and the two fresh hull checks took 54.788 and 60.631 seconds. This
pilot supports a meaningful feasible 2016 repair, not a speedup claim or a
general learned-policy benefit.

A separate read-only review replayed the ten physical columns from these two
new hull runs and five archived control columns. The new columns did not improve
on the archived physical incumbent at 515.515556. At that incumbent's own-load
marginal electricity prices, however, a different replayed four-bus plan lowers
the price-taking objective by at least 0.724020 cost units while increasing true
target cost to 516.505682. The incumbent is within 0.158740 of the physical optimum
using the fresh lower certificate. This documents an incentive mismatch at a
verified near-optimal incumbent; it does not establish support failure of the
unknown exact optimum. See [the physical pool and price-response review](SHARED_INTERVAL_PHYSICAL_POOL_REVIEW.md)
for exact arithmetic, scope and reproducibility.

The [development schedule figure](figures/shared_interval_2016_learned.png)
shows the new learned repair at 516.93, distinct from the archived 515.52
incumbent used in that incentive test. Its [plot script](plot_shared_interval_example.py)
uses the saved physical schedule and charging segments; no optimization is run.
