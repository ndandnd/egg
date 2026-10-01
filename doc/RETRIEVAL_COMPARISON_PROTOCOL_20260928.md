# Prospective development comparison: solving and whole-fleet retrieval

This bounded comparison completes the next computational evidence package before
consolidation of the expanded first draft. It tests reuse and simple retrieval;
it trains no learned method. All outcomes, including unsuccessful sources,
unused proposals, ties, open intervals and deadline failures, remain reportable.
Do not enlarge the campaign to seek a favorable result.

## Cases and fixed markets

Use five new synthetic cases under the complete-replenishment NativeCase model:
seed 1006 at 8/16/24 services, seed 1012 at 16, and seed 1009 at 16. The names are
`native_scale_dev_s1006_n08`, `native_scale_dev_s1006_n16`,
`native_scale_dev_s1006_n24`, `native_scale_dev_s1012_n16`, and
`native_scale_dev_s1009_n16`, in that order. All variants of one seed remain one
base group. The sixth case is the admitted 105-service Eberbach/depot36 input,
SHA-256 `5ffb2f3a322b40c9c6c56972607fd0c4b21130cd35cd08e0a465f34fba67dc19`.
Do not regenerate or inspect reserved train/test seeds or public groups.
Hildenbrand's previously reported comparisons are historical context, not rerun
in this package. Synthetic realized charging pressure must be recorded; an
energy upper bound alone does not establish congestion or a minimum energy need.

All six cases have 30 hourly electricity periods over 00:00–30:00. Let
F(L)=sum_t(a_t L_t + b_t L_t^2/2), using the existing stored-number conventions.
Each case has two source markets and one target market, fixed before outcomes:

| Market | Linear coefficient a | Curvature b |
|---|---|---|
| Source 0 | 0.20 in every hour | 1/900 in every hour |
| Source 1 | 0.10 for 18:00–22:00; 0.30 otherwise | 1/900 in every hour |
| Target | 0.10 for 22:00–26:00; 0.30 otherwise | 1/900 in every hour |

These coefficients are synthetic comparison choices, not measured tariffs.
The nearest-price query is the target linear coefficient vector a. It is an
explicit exogenous descriptor, not a prediction of endogenous target prices.
Physical data, charging resources and vehicle costs are identical across a
case's markets. Cross-timetable route transfer is outside this comparison.

## Sources, proposals and verification

For each case, first run two fresh iterative hull calculations in source 0 and
source 1. Use numerical-QP restricted-master proposals, checked physical/simplex
replay, a 10-second pricing reserve and fresh native pricing. Preserve the full
source results and event records. A returned valid feasible column may be useful
even if its source optimality gap remains open; no such incumbent is an optimal
training label. A failed or late source cannot silently become a successful one.

Collect eligible, physically replayed whole-fleet columns. Match every column's
actual generating price to its source pricing_request/global_bound call,
physical identity, projection key and witness hash. Preserve source file hashes
and full original provenance. Distinct price labels may map to the same fleet
projection; record these ties rather than removing an unfavorable case. The
three proposal methods below share precisely this admitted candidate pool.

| Target arm | Initial complete-fleet columns |
|---|---|
| Cold | None |
| Retained | Every distinct admitted source fleet projection |
| Nearest price | One fleet whose actual generating source price is nearest to target a |
| Cheapest bill | One fleet minimizing operating cost + a·L over the same admitted pool |

Use Euclidean price distance; deterministic ties follow source order, pricing
call and column key. The cheapest bill calculation compares the stored numerical
values exactly, with the same deterministic tie policy. It is a finite-pool
minimum, not a global optimum. Report direct proposal bill and nonlinear
operating-cost-plus-F(L) separately: a cheapest linear bill need not imply the
best nonlinear objective or the fastest subsequent certificate.

All target arms use the same numerical-QP master, pricing reserve, fresh global
pricing, budgets and tolerances. No inherited lower-bound cache or native MIP
start is enabled. Record initialization/checking work, full iterative outcomes,
fresh bounds and complete child wall time. A price-only change preserves an
admitted plan's physical feasibility: repair is explicitly identity/no repair,
not a hidden optimization. Full hull verification is a separate stage from
returning a directly feasible proposal. Convex mixtures are not executable
individual fleet schedules.

The existing retained-state interface accepts a single predecessor. A derived
feasible-pool import envelope may bridge the multi-source pool only if it is
explicitly labeled as such, replayed, and pinned to original source hashes,
source-price labels and selected keys. It is not a source solver result or a
certificate. Use feasible_pool admission and a bounded feasible status; never
invent a certified status. Exclude all prior lower bounds, gaps and solver
statistics. Keep original per-column provenance when setting adapter-facing
pool identifiers. Fresh target pricing is still required for global support.

Run one shared target physical-planner calculation per case and a response to
its own marginal price a+b·L when an on-time checked planner witness exists.
Report executable-plan cost, planner bounds, hull bounds, and own-price regret
intervals with their distinct solver qualifications. Missing prerequisites make
response/dependent comparisons explicitly unavailable. Do not impute zero time
or zero regret, and do not relabel a solver-tolerance bound as an exact proof.

## Prospective resource and accounting limits

There are at most 48 children: six cases times two sources, four target arms,
one planner and one own-price response. No retry, requeue, substitute case or
seed sweep is allowed. Each child has a scientific routine allowance plus a
30-second complete-process margin. Setup, source admission, model construction,
checking and extraction are all measured; the parent enforces the complete
child limit even when a native routine stalls. Report overruns and hard stops.

| Stage, per case | Synthetic routine allowance | Eberbach routine allowance |
|---|---:|---:|
| Each source hull (two) | 60s | 240s |
| Each target hull (four) | 90s | 300s |
| Target physical planner | 60s | 240s |
| Own-price response | 60s | 240s |

Routine allowances total 5160s; all 48 child margins bring the sum of nominal
child limits to 6600s. Any forced-termination grace is additional spent time,
recorded explicitly. The controller cap of 6900s still limits the whole sequence
and may leave later cells unstarted; outer supervisor 7100s, Slurm 7200s. Request
one CPU and 8 GB; use one native/numerical thread and exclude
`scaglione-compute-01`. Run serially. Do not modify other-project or held jobs.
The prospective freeze records final code/input identities, environment,
backend and solver seed, exact child order and full controls before execution.
A completed source that is ineligible for reuse still consumes source work.
Cold may proceed independently when a source fails; dependent arms must record
why they were skipped. Preserve partial traces and terminal receipts at all caps.

Separate the two source-generation costs, each direct lookup/replay cost, and
each target's full online verification cost. Report both online costs and paid
source-plus-target totals; shared source work is paid once, not free and not
summed again as if each arm had created the same pool. State amortization
assumptions explicitly. Counterbalance the four target arms across the fixed
case order and freeze that order before outcomes. Report time-to-quality only
when observed traces support a common target; otherwise compare elapsed work
and final bounds together without a speedup claim.

This protocol is a development comparison, not independent test evidence or a
learning validation. After the single bounded attempt and its result review,
consolidate the LaTeX manuscript under `DRAFT_COMPLETION_PLAN_20260928.md`, even
if no acceleration is found. ML training remains optional for that first draft.
