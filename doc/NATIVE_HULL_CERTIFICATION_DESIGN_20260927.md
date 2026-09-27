# Native complete-fleet hull certification: design and prospective protocol

27 September 2026. **Design/proof only. No hull implementation, optimizer run,
cluster job, or new numerical result was produced for this document.** The
native V2 CBC qualification passed its 15 fixed controls; its independent
result audit is a prerequisite to using it here. The failed V1 attempt remains
separate. This document proposes the next source freeze; it does not assert
that the proposed hull algorithm has been qualified.

## Smallest useful extension

Build a separate native hull module on the qualified `NativeCase`, complete-fleet
linear oracle and physical replay. Use an ordinary fully corrective restricted
master with quadratic tangent cuts, followed by a fresh complete-fleet pricing
call at the **true supply gradient** of the replayed master mixture. Certify
with a global Fenchel lower bound and the true objective of that mixture.
No learned, shifted, stabilized or incumbent-only pricing certificate is needed.

`src/egglab/certified.py` is absent from this checkout. Relevant existing code is
`b2a2.solve_rmp` (one convexity block, tangent LP, true-mixture upper bound),
`b2a345.conj_true/theta_cert` (nonnegative-domain Fenchel bound), and the reuse
qualification's fresh-state/retained-column discipline. Reuse their mathematical
structure and evidence conventions. Do not call their legacy `Instance`/EVSP
column adapters: their movement ownership, terminal semantics, replay schemas,
load bounds, backend wrapper and certification policies differ from native V2.
In particular, the old nonnegative epigraph-variable bound is invalid for
arbitrary negative supply intercepts; the native epigraph must be free below.

The new code should import the qualified native oracle and replay rather than
copy their feasible-set builder. A hull column is **one complete feasible fleet**
including its shared connector schedule. Averaging columns is a planning
relaxation. It does not authorize dispatching fractional buses, averaging
incompatible plug schedules inside a physical fleet, or convexifying individual
buses before enforcing shared resources.

## Common physical set and exact mathematical target

Fix one declared native case, including all service obligations, directed
movement alternatives and energies, battery/reserve/efficiency, resource periods,
market-period edges, fleet cap and intrinsic costs. Let `X` be precisely the
complete-fleet feasible set represented by the native builder. For `x in X`,
write `e(x) >= 0` for its vector of **grid** kWh and `c(x)` for intrinsic cost.
Set `Y = {(e(x), c(x)): x in X}`. No extra source movement can be inferred here.

The fixed finite graph, finite fleet cap and bounded charging intervals imply
that the native algebraic set is a finite union of bounded polytopes. Its
projection `Y` and `conv(Y)` are compact. Assume nonempty `X` for the value
comparisons below. Supply cost is

`F(L) = sum_t [a_t L_t + b_t L_t^2/2]`, with finite `a_t`, finite `b_t >= 0`.

The physical and convexified objectives are

`D = min_(e,c in Y) [c + F(e)]`,

`CH = min_(L,cbar in conv(Y)) [cbar + F(L)]`.

Thus `CH <= D`. The native physical tangent planner and hull pricing oracle must
use the identical `NativeCase` identity; their objectives are the only modeling
difference. Supply vectors receive a separate market identity. A physical
planner upper bound does not lower-bound `D`, and a restricted-master value does
not by itself lower-bound `CH`.

Every stored column contains the native schema/physical identity, complete
physical plan and source receipt, its freshly replayed `(e,c)` projection, and an
immutable witness hash. A separate master key hashes the full-precision
canonical load **and cost**, with normalized signed zero. Equal load with unequal
cost is distinct. Exact duplicate projections may be deduplicated with all
witness provenance retained. Near duplicates are diagnosed but not silently
merged. No negative or positive load is rounded away to manufacture novelty.

## Global Fenchel lower bound: proof and domain

Use the extended supply function `F_+(L) = F(L)` for `L >= 0`, and `+infinity`
otherwise. Its conjugate is

`F_+*(p) = sum_t sup_(z>=0) [p_t z - a_t z - b_t z^2/2]`.

For `b_t > 0`, its term is `max(p_t-a_t,0)^2/(2 b_t)`. For `b_t = 0`, its
term is zero if `p_t <= a_t` and `+infinity` otherwise. **An unbounded conjugate
is not replaced by zero or a large finite constant.** The initial price `p=a`
and subsequent true-gradient prices are in the finite domain, including
zero-curvature and unavailable charging periods. Arbitrary retained prices are
not imported. The implementation still checks the domain at every actual price.

Let `psi(p) = min_(x in X) [c(x)+p dot e(x)]`. A newly admitted native global
pricing lower bound `q_lower <= psi(p)` gives

`LB(p) = q_lower - F_+*(p) <= CH`.

Proof: for any convex mixture with weights `lambda_j`, Fenchel's inequality gives
`F(sum lambda_j e_j) >= p dot sum lambda_j e_j - F_+*(p)`; each physical column
satisfies `c_j+p dot e_j >= psi(p)`. Multiplying by nonnegative weights summing
to one and adding proves the bound. Native pricing incumbents are used to add
physical columns and bound pricing from above; **they cannot replace q_lower**.

This is also the correct complete-hull dual. At an optimal hull point
`(L*,c*)`, set `p*=grad F(L*)`. First-order optimality of `c+F(L)` on `conv(Y)`
implies `c*+p* dot L* = min_Y(c+p* dot e)`. Fenchel equality holds at `L*`, so
`psi(p*)-F_+*(p*)=CH`. This argument uses the smooth quadratic on its ambient
space and compact nonempty hull; it does not silently assume an interior
charging load or strict positive curvature. It establishes the exact target,
not finite-iteration convergence of a numerical implementation.

All bounds in the software remain conditional on the qualified native solver,
feasibility and replay tolerances. Use the oracle's already outward-guarded
pricing lower bound once; save its raw counterpart separately. Evaluate the
conjugate at the **actual serialized price supplied to the oracle**, not an
ideal unrounded gradient. Exact `Fraction` arithmetic on finite input floats
can compute the conjugate and bound subtraction, followed by outward decimal
conversion. This prevents an additional floating conjugate error being hidden
inside an unmeasured tolerance; it does not turn the native MILP bound into a
rationally verified bound.

## True mixture upper bound and master refinement

For a finite pool of replayed complete-fleet columns, solve the ordinary LP

`min sum_j lambda_j c_j + sum_t z_t`,

`sum_j lambda_j = 1; lambda >= 0; L = sum_j lambda_j e_j; L >= 0`,

`z_t >= (a_t+b_t q) L_t - b_t q^2/2` for each saved tangent point `q`.

Each `z_t` is free below. Begin with the tangent at zero; add tangents at the
newly replayed load vector. Save the exact solved tangent set before appending.
No price stabilization, quadratic penalty, trust region or old dual enters this
master. A single shared LP builder serves all synthetic cells and both arms.

The raw LP lambda vector, aggregate load, epigraph values, objective, bound,
status and dimensions must be written before any conversion. Admit only a
finite `OPTIMAL` LP in this first qualification. Negative simplex mass and
normalization need a separate, prospectively fixed **dimensionless** policy:
sum of magnitudes of negative raw weights at most `1e-10`, and
`abs(sum(max(lambda,0))-1) <= 1e-10`. Larger residuals fail. Record all changes;
never delete a positive weight. Convert each retained nonnegative float to its
exact rational value and divide by their exact positive sum. The resulting
rational weights are nonnegative and sum to one exactly. Save numerator/
denominator strings and the raw weights. Independent audit reconstructs them.

Replay every referenced physical witness without dividing energy by a tiny
weight. Form the convex combination of their canonical projections using those
rational weights, then evaluate

`UB_mix = sum_j lambda_j c_j + F(sum_j lambda_j e_j)`.

This is a true restricted-mixture objective, hence an upper bound on `CH`.
Evaluate it with exact arithmetic on the stored projection/market floats and
round outward upward for the reported enclosure. The physical columns remain
numerical witnesses subject to native replay tolerance. Retain the best valid
mixture from any completed iteration; a later worse candidate does not erase it.
Do not report an LP tangent objective or a weighted average of `F(e_j)` as this
upper bound. In general `F(sum lambda e)` differs from `sum lambda F(e)`.

For a candidate mixture, form `p = grad F(L)` and save the actual float vector
used. A cheap, solver-free restricted-pool Fenchel gap is

`g_pool = UB_mix - [min_j(c_j+p dot e_j) - F_+*(p)] >= 0`.

It upper-bounds suboptimality within the current finite pool. It includes any
Fenchel residual caused by rounding the gradient. Refine the LP until
`g_pool <= 1e-6`, rather than treating a small tangent epigraph slack alone as
a sufficiently stationary mixture. The ordinary LP bound, recomputed PWL
objective, simplex correction, true-objective slack and `g_pool` are all saved
as distinct diagnostics. The global certificate never depends on LP dual signs.

Then make one **fresh** complete-fleet pricing call at `p`. A native `certified`
or `bounded` result may supply its already admitted lower bound and replayed
incumbent. A wide pricing gap can prevent hull certification, but it does not
invalidate a valid global lower bound. Store `LB_best = max valid LB(p)` and
`UB_best = min valid UB_mix`; certify only when their current-market absolute
width is at most `1e-4`. Reversed enclosures outside the declared guards fail.
An `INFEASIBLE` pricing result after any valid physical column is a consistency
failure. Missing, nonfinite, unresolved or failed physical evidence is retained
as a failed/incomplete cell, not interpreted as exhaustion.

If uncertified and pricing yields a novel physical projection, append it and
fully correct the entire pool again. An exact duplicate with an open gap is
`stalled_bounded`, preserving the valid enclosure and raw pricing gap. It is not
a no-improvement proof; do not retry with relaxed/tightened solver settings.
Successful termination is the Fenchel enclosure, never the duplicate flag or
an incumbent reduced-cost sign. Stop normally at any predeclared resource limit.

## Retained-column semantics

A cold state begins with no columns and one counted pricing call at `p=a` to
obtain a replayed seed; this call can also contribute a valid Fenchel lower
bound. The retained arm's first state follows the same initialization. Later
retained states import only the immediately preceding certified retained-state
pool, after checking the unchanged physical identity, compatible native replay/
extraction policy, witness hashes and full physical replay of every column.
Original oracle statuses are provenance; physical validity supplies the column.
No original oracle lower bound becomes a bound for the new market.

Every new market rebuilds the ordinary master and resets lower/upper records,
prices, simplex weights and tangent inequalities. At most the **columns** cross
the transition. Supply tangent slopes/intercepts are recalculated from the new
market. A changed physical case, graph, intrinsic-cost parameter, efficiency,
resource, market-period partition or unsupported witness policy rejects import.
If a predecessor failed, dependent retained states are explicitly
`blocked_by_predecessor`; independent cold controls still run. There is no silent
fallback to a successful cold pool or restart. Reusing old gaps or successful
statuses is forbidden. The first study makes no learned-price or amortization
claim; imported replay and master overhead are included in time accounting.

## Frozen synthetic qualification to implement first

Use the qualified native cyclic, joint and fixed-reserve cases exactly. Do not
reintroduce terminal service markers. Native terminal opening stays at zero;
resources open in their declared early/late windows. In particular, an A-only
bus can recharge early after its final service. Supply uses early/late grid
energy with `b=1/5` and zero load in the two unavailable periods.

The proposed first grid has **eight cells**, fixed before implementation solves:
nominal case at early intercepts `[4, 21/5, 4]` under both cold and retained arms
(six cells), plus joint cold and fixed-reserve cold (one each). The final nominal
state is a return-to-base control. All cold cells are independent; each retained
state depends only on its own predecessor. No cell is selected after observing
its gap, fleet structure or runtime.

| Physical case / market | Exact CH | Exact D | Hull early/late load | One-bus mixture weight |
|---|---:|---:|---|---:|
| Nominal, early intercept 4 | 7591/80 | 97 | (27/4,93/4) | 27/40 |
| Nominal, early intercept 21/5 | 1539/16 | 99 | (25/4,95/4) | 5/8 |
| Joint reserve 1, efficiency 19/20, early 12 kW, intercept 4 | 2987911/28880 | 38527/361 | (573/76,1827/76) | 453/760 |
| Fixed battery 20/reserve 1/early 10 kW, intercept 4 | 99 | 99 | (5,25) | 0 |

Nominal hull support uses the complete one-bus point `(10,20,c=7)` and two-bus
point `(0,30,c=14)`. Its exact supporting early/late prices are `(107/20,93/20)`
at the base market and `(109/20,19/4)` at the tilted market. The full two-bus
family must remain available; selecting only these supports as the pricing
feasible set would invalidate the test.

Joint support uses one bus at `(220/19,20,c=7)` and two buses at
`(30/19,30,c=14)`, with weights `453/760` and `307/760`. Supporting prices are
`(2093/380,1827/380)` and the exact pricing value there is `60263/361`.
These targets follow from the complete projected-set proof in
`CYCLIC_ROBUSTNESS_DESIGN_20260927.md`. Fixed reserve removes the one-bus branch;
its surviving continuous two-bus projection is already convex, testing zero
gap. The tilted nominal target follows by minimizing
`104+(a-67/10)x+x*x/5` over `0<=x<=10` with `a=21/5`.

The rational table gives independent expected values, not supplied oracle
solutions or seeded supporting columns. First run uses only the generic `p=a`
seed and generated columns. Numerical CH enclosures must have width `<=1e-4`
and agree with the rational target within `2e-4`; support weights/loads are
checked against the complete supporting face, allowing equivalent decompositions.
The existing physical certificates can contextualize base/joint/fixed D values;
the tilted D=99 is an analytical reference until separately qualified. Do not
claim a new numerical D certificate from this hull-only run. If numerical
physical and hull enclosures are later paired, report the planning-gap enclosure
`[D_lower-CH_upper, D_upper-CH_lower]`, rather than subtracting two incumbents.

## Interfaces, bounds and complete evidence

Proposed small interfaces:

- `native_column(case, plan, source_receipt)` replays and produces an immutable
  complete-fleet column and full-precision projection key.
- `replay_mixture(case, market, columns, raw_lambda)` performs the fixed simplex
  normalization and returns a true mixture witness/upper bound and corrections.
- `solve_native_rmp(...)` performs bounded ordinary LP/tangent refinement and
  returns its immutable evidence, mixture, true-gradient price and `g_pool`.
- `native_hull_state(case, market, budget, imported_columns, record)` coordinates
  fresh pricing, current-market bounds, column addition, and terminal status.
- A dedicated qualification controller owns exclusive attempt directories,
  fixed input manifests, child-process caps and all eight receipts.

Proposed initial budget: explicit CBC, one thread; at most 10 seconds per native
pricing or LP call; 16 pricing calls including any seed; 64 master LP calls;
48 stored columns; 60 seconds total per cell, with every phase capped by the
remaining cell time. Each fresh worker has a 75-second external cap. An outer
650-second controller cap covers eight workers plus overhead. No LP-first
hidden solve, concurrent workers, adaptive cap increase, fallback solver or
within-attempt retry. A later GRB replication requires a separate published
source freeze and resource-policy check after local audit.

Before the first optimizer call save all eight cases, markets, targets, dependency
edges, budgets, source/version/native-library identities and committed source
label. Flush every call start/status, raw model primal/mapping data, exact solved
master tangent snapshot, native pricing events, physical replay, simplex
corrections, mixture, conjugate/domain calculation and objective reconstruction.
Record columns before/after import and addition, exact and near projection
novelty, every master/pricing solve, successful and unsuccessful calls, numerical
correction totals and all wall times. Count seed calls separately but include
them in totals. Failed or truncated outputs retain their valid trace prefix and
an incomplete-accounting flag. Continue all independent cells, recording blocked
dependencies explicitly. Cross-state results are descriptive; the eight-cell
qualification is not a performance study or statistical generalization claim.

## Implementation size and review gates

A bounded implementation is roughly 250–350 lines for the native column/master/
certificate layer, 150–220 for the attempt-preserving controller, and 200–300 for
pure/corruption/status regressions. These are planning estimates, not a request
for a general optimization framework. Prefer a small isolated module and driver;
leave production CG, native V2 physical modeling and protected artifacts unchanged.

Before scientific execution, independent preflight must review the proof,
conjugate domain, objective signs, full-fleet granularity, exact mixture handling,
source separation and hard limits. Pure tests must cover negative/zero-curvature
supply, an infinite conjugate, a high incumbent with a lower global bound,
mixture-vs-average supply cost, simplex corruption/tiny positive weights,
changed-physical-state import, stale-market bounds, mutated tangent snapshots,
duplicate open-gap termination, malformed/truncated traces and all-call accounting.
Analytical supports may be used in pure replay/certificate tests but not as
hidden seeds in the scientific cold cells.

Freeze code, protocol and fixtures before the first hull attempt. Independently
audit every accepted column and nonzero mixture component, all native bounds,
Fenchel calculations and the rational targets after the run. A failure produces
a preserved attempt and prospective correction, not a reclassified success.
Only after local qualification and audit may a single bounded cross-backend
replication be proposed. A private operational microcase remains a later gate
with a separately validated declared movement graph and no public raw data.

## Prospective V2 amendment: bounded exact pairwise pool refinement

V1 (`f549100`, preserved attempt1) produced two accepted cells, four repeated-LP
master-cap failures and two blocked retained successors. The original tangent
refinement proposal above is superseded for V2 by one ordinary native LP per
pool, then the bounded exact polishing procedure in
`NATIVE_HULL_QUALIFICATION_PROTOCOL_20260927.md`. The scientific controls,
complete physical set, pricing admission and final Fenchel proof are unchanged.
No V1 failure is relabeled. The author diagnosis and raw-trace arithmetic are
under `research-20260927/agent-notes/native-hull-attempt1-author/`.

For stored pool projection `(e_j,c_j)` and an exact feasible simplex w, write
`Q(w)=sum_j w_j c_j + F(sum_j w_j e_j)`. Define scores
`s_j=c_j+grad F(L) dot e_j`. Choose a minimum-score toward column i and a
maximum-score away column j among **strictly positive** weights, using fixed
smallest-index tie breaking. If `d=s_j-s_i>0`, move gamma along
`unit_i-unit_j`, with `0<gamma<=w_j`. Its exact one-dimensional objective is

`Q(w+gamma(unit_i-unit_j)) = Q(w)-gamma*d + H*gamma^2/2`,

where `H=sum_t b_t(e_it-e_jt)^2>=0`. For H>0 the feasible line minimum is at
`gamma=min(w_j,d/H)`; for H=0 and d>0 it is at gamma=w_j. The new simplex is
nonnegative and sums to one. The exact objective decreases, so its repeated
identical simplex cannot occur in exact arithmetic. All rational weights,
including ones below float representability, remain authoritative strings;
aggregate values are computed from them without a float round trip. Every
accepted step independently replays the physical columns and checks the exact
quadratic equation before recording the feasible upper bound.

If d<=0, all positive-weight scores equal the minimum score, which is the
simplex first-order optimality condition for this convex quadratic. Nonetheless
V2 does not substitute that condition for its implemented stopping test:
`g_pool` is recomputed using the actual serialized float price and its exact
stored-number conjugate. An open serialized-price gap still causes a bounded
stall. Step/time/bit-size limits likewise terminate without assuming an exact
restricted optimum. This is a generic feasible improvement method with a
checked certificate, not a promise that 256 steps solve any finite pool.

The new fixed limits are 256 accepted transfers, 8,192 bits per checked rational
numerator/denominator and five cumulative seconds in polishing per state,
within the unchanged state deadline. These limits may fail; no adaptive
increase is authorized inside a scientific attempt. One native LP per pool and
duplicate-tangent detection avoid consuming the same native call repeatedly at
a floating tolerance plateau. Successful polishing is still followed by fresh
complete-fleet pricing and the unchanged global Fenchel enclosure test.

The state now records the minimum true objective across every replayed raw
master and polished mixture immediately, including when a later inner cap
prevents return. Each such point is a feasible convex mixture, so this only
tightens a valid upper bound. It does not improve the native pricing lower
bound, rescue missing accounting, or convert a failed cell to a success.

Prospective regressions cover the preserved numerical-plateau shape, the exact
step equation, zero curvature, multiple positive components, no float underflow
of exact weights, cumulative step/time/bit caps, streamed bounds on failure,
immutable raw tangents and complete polishing start/finish accounting. Source
freeze and a new independent preflight precede any V2 optimizer execution.
