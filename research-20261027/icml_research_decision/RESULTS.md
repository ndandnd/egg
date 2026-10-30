# Literal qualification complete; ICML research gap remains empirical

The new stdlib check ran once and exited0 against source `4a20f8da41c81f75b3a68527371140850606c5e1`, control `7378c728`. All213 assertions passed. These are repeated checks on one small abstract set-partition construction with four declared epsilon values and one negative-reduced-cost variant, not213 experiments or independent observations. No solver, transport data, physical replay, generation, inference or training ran.

| Triple-column surcharge epsilon | LP value | Integer value with no/one new triple | Integer value with both | Joint benefit |
|---|---:|---:|---:|---:|
| 0 | 3 | 10 | 3 | 7 |
| 1/2 | 3 | 10 | 4 | 6 |
| 7/2 | 3 | 10 | 10 (tie preserved) | 0 |
| 4 | 3 | 10 | 10 (fallback retained) | 0 |

The negative-reduced-cost singleton has rc=-1/2 and improves an LP witness from3 to5/2, while integer value stays10. For new-column limits0,1,2, direct classical completion and explicit best augmentation agree in value and all minimizers in every declared scenario. Exact fractional primal/dual witnesses certify the displayed LP values; no floating tolerance or optimizer status is used.

This resolves two formulation questions: singleton reduced cost is not joint integer utility, and a conventional joint master is a necessary comparator for a learned set selector. It does **not** resolve whether the EGG workload has costly residual recovery, whether the example is physically realizable, whether ML helps, or whether the tentative target is novel. Prior art already addresses integer-useful columns and coordinated repair.

The newly identified source seam is material for the next empirical study: partition-aware diving exists but was disabled in the closed pilot; the existing IPColGen adaptation explicitly rejects partition mode. Preserving exactly-once service requires a qualified compatible baseline, not removing that guard. That is a new source-supported observation, not a diagnosis or rerun of prior failed cells.

Transport-study status remains PENDING. NEXT_EXPERIMENT specifies questions, baselines, measurements and a proposed promotion rule, but has no executable cohort/source/import/native/resource manifest. No fit has been selected or run. The ICML plan is review-ready; the scientific contribution is not submission-ready.
