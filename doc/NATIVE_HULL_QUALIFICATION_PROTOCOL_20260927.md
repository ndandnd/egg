# Native complete-fleet hull qualification protocol

27 September 2026. Protocol `native-hull-qualification-20260927-v1`;
result/column schema `egg-native-hull-v1`. **No native hull optimizer has run at
protocol preparation.** Source, fixtures, this protocol and dependency hashes
must be frozen by the principal researcher before the first scientific attempt.
The qualified native physical/pricing module remains a separate dependency;
this implementation does not change its feasible-set builder or replay.

## Question, target and limits

Can complete-fleet pricing plus a fully corrective ordinary master certify the
known continuous native hulls, and can replayed columns be retained across a
fixed tariff path without carrying stale bounds? This is a bounded software
qualification, not a runtime benchmark, evidence of learned-price benefit, or
an operational dispatch study. No private inputs, cluster actions or production
checkpoints are part of the first local gate.

The proof and complete-feasible-set assumptions are in
`NATIVE_HULL_CERTIFICATION_DESIGN_20260927.md`. For the fixed native set `X`,
with grid-energy projection `e(x)` and intrinsic cost `c(x)`, the target is

`CH = min_(L,cbar in conv{(e(x),c(x)):x in X}) [cbar + F(L)]`,

where `F(L)=sum_t(a_t L_t+b_t L_t^2/2)`, `b_t>=0`, and `L>=0`.
Every column is an independently replayed **entire fleet**, with native terminal
recharge, directed movement modes, SOC, service coverage and shared connector
constraints already imposed. Its convex mixture is a planning relaxation, not
an executable fractional fleet or a promise to dispatch average charging power.

A new pricing call supplies a qualified native global lower bound `q_lower` on
`min_X[c(x)+p dot e(x)]`. The clean certificate is

`LB(p)=q_lower-F_+*(p) <= CH <= cbar+F(L)=UB_mix`,

where `F_+` extends `F` by infinity outside the nonnegative orthant. For `b>0`,
the conjugate contribution is `max(p-a,0)^2/(2b)`; for `b=0`, it is zero when
`p<=a`, infinity otherwise. Infinite-conjugate prices fail, never become a finite
surrogate. The actual serialized price supplied to native pricing is used in
all calculations. Fresh prices are the true supply gradient at the replayed
master mixture; seed prices are `a`. These choices respect the finite conjugate
domain, including unavailable and zero-curvature periods.

The native **global lower bound**, not its incumbent, enters `LB`. Both admitted
native `OPTIMAL` and `FEASIBLE` statuses retain their raw names and require the
existing physical/objective/bound checks. An admitted wide pricing gap remains
usable as a weak global bound but may prevent hull certification. Missing,
nonfinite, infeasible or unresolved pricing fails this all-feasible control set.
A pricing infeasibility after a valid column is a consistency failure.

## Columns, exact stored-number arithmetic and numerical limits

Each column saves physical identity, native extraction-policy version, complete
plan, immutable witness hash, source receipt and freshly replayed load/cost.
Master identity hashes the full-precision load and intrinsic cost. Equal load
with different cost is distinct; signed zero is normalized. Exact duplicates
are detected by this key. No positive charge or nearly equal projection is
silently deleted or rounded into another column.

The raw LP lambda vector is saved in immutable column order. Its negative mass
must total at most `1e-10`, and the nonnegative mass must differ from one by at
most `1e-10`; violations fail. Negative residuals are clipped, every positive
weight is retained, and weights are divided by their exact rational sum. Raw
values, rational weights, mass residuals and L1 changes are recorded. Every
referenced column, including zero-weight entries, undergoes full physical replay;
no charge is divided by a tiny mixture weight.

The resulting rational simplex is exact **for the stored finite projection
numbers**. Aggregate energy, intrinsic cost, quadratic supply cost, conjugate
and final bound subtraction use `Fraction` arithmetic on those numbers. Save
exact strings and outward-rounded display bounds. This avoids understating
arithmetic rounding; it does not assert an exact physical fleet witness or an
exact global MILP bound. Physical replay and native solver evidence remain
conditional on their qualified tolerances and roundoff policy. Float mixture
loads displayed in JSON are conveniences; the rational load strings and weights
are the certificate's arithmetic representation.

The true upper bound uses `F(sum lambda e)`, not `sum lambda F(e)` and not the
LP epigraph objective. The native oracle's already outward-guarded lower bound
is used once. The reported global enclosure retains the maximum fresh lower
bound and minimum true mixture objective within the current state. Negative
stored-number widths fail; successful termination requires width `<=1e-4`.

## Ordinary master and stopping logic

The restricted master is a pure LP: nonnegative weights summing to one, load
links to their convex combination, and free-below epigraph variables for valid
quadratic tangent lines. Load upper bounds are the maximum of the current pool's
loads in each period. Tangent coefficients computed in floating representation
are weakened by an explicitly saved rounding pad so they remain lower lines on
that finite pool box. Zero is the initial tangent point; later points come only
from the current state's mixture. The solved points/rows are copied before any
new tangent is appended.

Each actual master call must return an `OPTIMAL` LP, with zero integer variables,
finite primal/bound data, checked simplex/linking/epigraph residuals and a native
objective matching reconstruction. This master policy is deliberately distinct
from pricing's admitted `FEASIBLE` policy. Master duals are unnecessary for the
certificate. Native master bounds and PWL objectives are logged as diagnostics;
neither is substituted for the global Fenchel lower bound.

At a candidate mixture, form the actual float gradient price and compute

`g_pool = UB_mix - [min_(stored j)(c_j+p dot e_j) - F_+*(p)]`.

This restricted-pool certificate, including the Fenchel residual of the rounded
price, must be `<=1e-6` before requesting another global price. A small tangent
slack alone is insufficient. If not, add the candidate's load as a tangent point
and re-solve within the cumulative master/time budget.

After clean pricing, certify using the global enclosure. Otherwise add a novel
replayed projection and re-optimize the full pool. A duplicate with an open gap
ends as `stalled_bounded`, preserving the bound interval; it is not exhaustion
or evidence that the pricing incumbent is globally optimal. There is no solver
retuning or repeated same-price retry. A final novel pricing column can be
retained even when the prior mixture already closes the certificate. Reaching
a call, pool or wall limit ends as `budget_exhausted`; independent cells continue.

## Eight fixed controls and independent analytical targets

Use the native synthetic inputs exactly as constructed by the qualified fixture
helper. All have native terminal opening at zero and fixed resource windows.
An A-only bus can therefore charge in the early window after its final service.
No service marker, altered charging cap or restricted pricing support is added.
The qualification contains six nominal cells on the intercept path
`[4,21/5,4]`, each under cold and retained arms, plus joint cold and fixed-reserve
cold. The first occurrence and return to base are distinct fresh states.

| Cells | Case / early intercept | Exact CH | Exact aggregate early/late grid kWh |
|---|---|---:|---|
| nominal cold/retained state 0 | Battery 20, reserve 0, efficiency 1, early 10 kW; `a=4` | `7591/80` | `(27/4,93/4)` |
| nominal cold/retained state 1 | Same physical case; `a=21/5` | `1539/16` | `(25/4,95/4)` |
| nominal cold/retained state 2 | Return to `a=4` | `7591/80` | `(27/4,93/4)` |
| joint cold | Battery 20, reserve 1, efficiency 19/20, early 12 kW; `a=4` | `2987911/28880` | `(573/76,1827/76)` |
| fixed-reserve cold | Battery 20, reserve 1, efficiency 1, early 10 kW; `a=4` | `99` | `(5,25)` |

Supply curvature is `1/5` in early and late periods, with early linear coefficient
as above and late coefficient zero. The two unavailable periods have zero
coefficients and zero physical charging. Input coefficients are encoded as
finite floats; rational targets describe the analytical decimal-valued model.
Compare the numerical enclosure with these targets using `2e-4` tolerance, while
still requiring the stricter `1e-4` certificate width. Aggregate load errors are
reported; no unsupported equality of alternative supporting decompositions is
required for acceptance. Independent audit checks the complete supporting face.

The analytical support plans and supporting prices are **not seeded into the
scientific runs**. Cold states begin with one counted price at `p=a`. Retained
state 0 does the same; states 1 and 2 import only their immediately preceding
certified retained-arm pool. They validate the expected state identity, arm,
index, unchanged complete physical identity, compatible replay policy and every
witness. Old prices, lambdas, tangents and bounds are discarded. Changed physics,
costs or period partition reject import. A failed/missing predecessor yields
`blocked_by_predecessor` with zero solver calls; it never substitutes a cold pool.
Import also requires the predecessor controller receipt to identify the expected
cell, pass, exit with return code zero, report no timeout and no evidence issues,
and mark the result certified. The successor independently recounts the saved
trace: native phase accounting must be complete and nonzero, with every count
and returned phase time agreeing with that receipt. A completed result followed
by a timeout/nonzero exit, a truncated trace, or a missing/malformed receipt is
therefore a failed dependency even if its result file says certified.
All independent cold, joint and fixed-reserve controls are still attempted.

Known physical optima contextualize the relaxation: nominal base 97, nominal
tilt 99, joint `38527/361`, fixed-reserve 99. The tilted physical value is an
analytical reference, not a new native planner certificate from this hull run.
No physical-minus-hull gap is reported as certified by subtracting incumbents.

## Resources, immutable evidence and execution gate

Initial backend is explicitly CBC, one thread. Per state: at most 16 pricing
requests including the seed, 64 master LP requests, 48 stored columns, 10 seconds
per actual native phase, and 60 seconds total with each phase capped by remaining
time. Each fresh sequential worker has a 75-second external cap. The supervisor
creates a new process group and enforces a 650-second outer timeout, then TERM
and at most 10 seconds before KILL for any remaining group members. No existing
attempt is resumed or overwritten. A later GRB replication is a separate gate.

The supervisor writes its launch before creating the controller. The controller
writes all eight inputs, targets, identities, dependencies, budgets, source
hashes and environment before any worker solve. Source hashes include the new
module/runner/tests/protocol, proof design, native physical module, and imported
fixture/runtime helper. Workers verify the dependency hashes again. A declared
commit label does not itself prove a source freeze; the principal researcher
must verify and commit the full state before launching.

Flush every pricing request, nested native call start/status/raw-variable record,
master start/status/raw-primal mapping, immutable column order/tangent rows,
mixture and simplex correction, restricted-pool gap, global Fenchel calculation,
column addition and terminal state. Save stdout, stderr, exceptions, per-cell
receipts and a supervisor receipt. Every phase count includes unsuccessful calls;
seed, pricing and master counts remain separately available. Timing includes
column replay/import/master refinement, not only the final successful oracle.

Malformed/truncated worker files remain unchanged. Read only the valid trace
prefix, record parse issues and incomplete accounting, fail that cell and
continue independent cells. Accounting matches unique phase/call identifiers,
not just equal aggregate counts. An outer kill may leave incomplete cells; the
frozen eight-cell manifest and preserved traces identify them. No missing result
is called success, and no timeout/cap/backend switch is retried inside an attempt.

After pure tests and independent preflight, freeze before running:

```sh
PYTHONPATH=src ../.research-venv-repaired-1176/bin/python -m experiments.native_hull_qualification --output result/native_hull/20260927-attempt1 --freeze-label COMMIT_ID --backend CBC
```

Replace `COMMIT_ID` with the actual full committed execution state. Qualify all
cells against their predeclared target and retain every failure. Independently
audit each accepted full-fleet column, simplex mixture, pricing native bound,
Fenchel subtraction and target enclosure before claiming success. Any correction
requires a new freeze and distinct attempt; protected historical results and
other projects remain outside scope.
