# Ordered solver-baseline comparison

**Prospective development protocol — 28 September 2026.** Run after independent
runner review and required CI, under the existing two-hour single-job ceiling.
Freeze the committed source, environment, inputs, controls and declared order
before optimization. Use a new exclusive attempt; preserve completed attempts.

## Question and design

Test whether the numerical restricted master and saved physical pricing bounds
improve the completed pilot's retained-plan baseline. This is an ordered addition
of methods, not a full factorial interaction study or an ML evaluation. The 32
cells are the existing cyclic two-service, multivisit three-service, Hildenbrand
depot15 and depot16 cases, each at the same two market states, under four arms:

| Arm | Master | State 1 initialization | Pricing-bound cache |
| --- | --- | --- | --- |
| `reserve_cold_hull` | Native LP + rational pairwise polish | Empty pool | Disabled |
| `reserve_feasible_hull` | Native LP + rational pairwise polish | Its own admitted state-0 physical pool | Disabled |
| `qp_feasible_hull` | Numerical QP proposal + exact replay | Its own admitted state-0 physical pool | Disabled |
| `qp_cache_feasible_hull` | Numerical QP proposal + exact replay | Its own admitted state-0 physical pool | Its own checked state-0 pricing evidence |

Every arm starts state 0 from an empty pool and pays its own preparation.
Execute serially in frozen case order, then arm order as above, then state 0 and
state 1 consecutively. All cases remain development data. Both public depot
variants belong to one Hildenbrand timetable group; they are not independent
train/test bases. No planner, own-price response, new data intake, learning or
additional physical qualification is included.

Compare reserve-cold with reserve-feasible for plan retention, reserve-feasible
with QP-feasible for the numerical master, and QP-feasible with QP-cache-feasible
for cached bounds. Report state-0 and state-1 outcomes, bounds, calls and paid
wall time, plus complete two-state totals. This deterministic screening run
supports descriptive comparisons. Claim time to common quality only when an
on-time recorded certificate/trace supports that same declared quality; do not
infer general speedup, statistical replication or scalability.

## Fixed solver and stopping rules

All arms use the compact physical pricing formulation, Gurobi, one native
thread and the ten-second reserve inside the existing native wall target. Keep
four pricing calls, six master calls, pool cap 16, epsilon `1e-4`, restricted-pool
tolerance `1e-6`, rational-bit cap 4096, and native-polish limits of 64 steps and
20 aggregate soft seconds. Per-state native wall target is 60 seconds for the
two synthetic cases and 180 seconds for the two public cases. Leave native
phase limits unchanged. The independent child deadline is native target +30s.
Record actual elapsed and reserve/solver overshoot.

QP arms select `master_policy='numerical_qp_proposal'`, denominator 1,000,000,000
and maximum 500 numerical iterations per proposal. Each QP proposal consumes
one master call. These arms bypass the native LP and pairwise polish for that
call; the old polish limits are inactive for the bypassed work. Record numerical
status, proposal/setup/rounding/replay work, rational-bit maximum and exact
restricted-pool gap. A finite non-success numerical proposal may be replayed;
its status remains visible. Malformed/import/proposer failures stay
`proposal_failed` with prior valid evidence retained. Physical validation errors
remain failures; time/bit limits remain budget-exhausted. No hidden fallback or
retry is allowed. In-process SciPy is not forcibly preemptible; the whole-child
deadline and actual overshoot remain part of the record.

Exact simplex and physical replay admit a feasible convex mixture, not an
executable individual fleet schedule. Restricted-pool success does not certify
the full hull problem. All certification still requires fresh target physical
pricing and the global numerical enclosure criterion. Preserve solver tolerance
qualifications; exact arithmetic on stored floats is not an ideal-model proof.

## Source admission and cache integrity

Retained state 1 can use only its own arm's complete, on-time state-0 result,
with literal status `certified`, `bounded`, `stalled_bounded` or
`budget_exhausted`, finite bounds and complete independently replayed evidence.
A failed, `proposal_failed`, late, timed-out, missing or invalid state 0 makes
its retained target ineligible. Never substitute cold solving or another arm's
pool. The cold arm has no predecessor dependency.

Check receipt completion/on-time status, exact expected source state identity,
physical/market/oracle/extraction/control identities, unique column keys and all
physical columns. Recompute source mixture and Fenchel certificate under its
source market. Pin bytes and hashes of source raw result, assessed result,
receipt and pricing events in an admission record, and recheck those files in
the worker before consuming them. Preserve validation errors and spent time.

Only the final arm enables `bound_cache_policy='physical_pricing'` in both
states. Its state-0 cache entries must match their original emitted
`pricing_result` events by call, unchanged posted price, native status/bounds,
physical/oracle/extraction identity and replayed projection/witness provenance.
Validate every entry; no silent filtering. Pin the complete original events
file. Digests bind recorded inputs; they do not independently prove a native
solver's bound. Re-evaluate every admitted physical lower with the target
market's Fenchel conjugate, and preserve source and target lineage. Never copy
the old-market transformed hull lower as a target bound. Fresh target pricing
remains required before certification; cached evidence alone cannot certify.

## Resource envelope and complete accounting

| Cases | Cells | Native target each | Sum of native targets |
| --- | ---: | ---: | ---: |
| Two synthetic cases | 16 | 60s | 960s |
| Two public depot variants | 16 | 180s | 2,880s |
| Total | 32 | — | 3,840s |

The sum of individual hard child deadlines is 4,800s. Keep the controller cap
at 5,400s and use a 6,000s outer wrapper cap, with termination grace before the
two-hour Slurm limit. Request one CPU and 8GB, configure native and numerical
libraries to one thread, run one serial job, no requeue or retry, exclude
`scaglione-compute-01`, and leave other projects/held jobs untouched. Record
actual Slurm allocation and total job elapsed even if allocation exceeds the
request. Pin SciPy, NumPy, Python and native backend/runtime information without
publishing sensitive environment details. Missing required runtime dependencies
fail before optimization; do not silently switch backend.

Child wall includes its startup, own-source validation and solver work. Measure
parent admission/check work separately and add it once to the corresponding
arm's paid two-state accounting; disclose common freeze/controller/setup and
whole-job elapsed separately. Avoid double-counting source timing metadata
inside the already-paid state-0 child. A complete two-state total requires both
state timings; an ineligible/unstarted state has no complete two-state total.
Preserve its spent preparation and admission costs separately. Missing component
times remain unknown, never zero-filled or obtained by subtraction.

Seal a row for all 32 declared cells, including `proposal_failed`, bounded,
ineligible, late, timed-out, interrupted and unstarted outcomes. Preserve raw
results, pricing events, source pins, admission/failure/launch/child/supervisor
receipts and all work already spent. Reconcile partial termination and seal
only after process-group quiescence. Summarize outcomes and final bound quality
together with time; the frozen comparison cannot be redefined after results.
