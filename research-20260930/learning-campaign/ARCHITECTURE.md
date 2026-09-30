# Fleet proposal and catalog interface

`catalog.jsonl` is an append-only sequence of one row per completed solver
cell. `row_id` is `<case-name>/<stage>`. A row identifies `base_group`,
`split`, `case_identity`, `market_identity`, `market_name`, `market_role`, and
`arm`. It includes the serialized `NativeCase` and market coefficients. Its
`label` records native status, receipt, elapsed wall time, failure, bound,
and the best replayed feasible **whole-fleet** column, if one exists. A fleet
label has `plan`, `plan_hash`, `load`, `ops_cost`, and `objective_exact`.
`optimality` is `unknown` even when a hull mixture receives a certified lower
bound: the selected single fleet is only a feasible incumbent. The hull
mixture upper bound is separately named `native_mixture_upper_exact`.

The learner may consume source and training cold rows. It must partition on
`base_group`, so tariff variants never cross train/development/test. Its
prospective input is a new physical case and tariff; it should emit a route
topology or timing template plus a deterministic reconstruction trace, then
produce a complete case-specific fleet plan. Admission requires native
`replay_native` under the target case identity and an exact recomputation of
the target nonlinear objective. Rejected proposals retain their failure and
spent wall time. A learned proposal has no global lower certificate and must
never be called optimal just because replay succeeds.

The first campaign collects comparable cold, retained, and nearest-price
target results and provisional training labels. It trains once before the
development cold solve. The trainer uses the frozen design to construct a
market-only development prediction request. It predicts route edges and
projects onto the nearest replayed complete development source fleet. The
learned fleet enters the same native target hull through a replayed feasible
pool adapter. Learned, nearest-price, and cheapest-bill each select from the
same one-best-fleet-per-source catalog pool; retained uses all source columns.
The pool coverage limits the learned claim. The first job's `scientific_admission`
remains pending. A later test phase requires a separately frozen trainer,
budget, prediction path, and independent test-group materialization.
