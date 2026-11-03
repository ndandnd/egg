# Prospective Sistig market-sensitivity design

27 September 2026. **Candidate planning note, not a frozen protocol:** no
sensitivity optimizer, price oracle, or cluster job was run for this design.
The flat-price pilot and its follow-up matching audit informed the decision to
defer a broad sensitivity campaign pending adequate baseline bounds, an
independent scope review, and a separate manager decision. They did not
determine the proposed curvature values or add or remove scenario cells. Those
remain candidate values until a separate source freeze. The grid is a finite
scenario census, not a sample of bus operators or an estimate of field
prevalence. The proposed 11-hour upper envelope is planning information only;
it is not execution authorization or an admitted resource allocation.

## Question and comparison

For the two separately restricted Hildenbrand depot cases, how often is the
physical-versus-complete-fleet-hull planning gap positive, numerically zero, or
unresolved across a small, declared range of synthetic supply curvature and
full-recharge deadlines? Do the two depots differ under identical assumptions?
For every case, compare the physical planner and the convexified planner on
exactly the same complete, physically feasible fleet set, then measure both
physical-optimum own-price regret and fleet lost-opportunity cost at a common
hull-mixture price.

Use the same source-qualified 37 mandatory services, exact directed movement
matrix, fixed movement modes, modeled service/movement energy, zero deadhead
intrinsic cost, and synthetic f100 used-bus cost in both planners. Each
scenario gets one canonical physical identity. The physical value is

\[
D=\min_{x\in X}\{c(x)+F(L(x))\},
\]

and the hull value is

\[
CH=\min_{(\bar c,\bar L)\in\operatorname{conv}\{(c(x),L(x)):x\in X\}}
  \{\bar c+F(\bar L)\}.
\]

The hull columns must be replay-valid whole fleets from that same feasible
set X. Using different connection modes, movement timing, terminal conditions,
or replay rules in the two calculations invalidates the comparison.

## Candidate scenario grid for a prospective freeze

Keep the declared linear coefficient at \(a=0.2\) synthetic objective units
per grid kWh in every hourly period. Let \(L_t\) be grid energy in kWh in
hourly period \(t\), not average kW. Apply the supply function to all 30
one-hour periods in the baseline horizon and the first 26 one-hour periods in
the 26:00 sensitivity; charging past that deadline is unavailable.

\[
F(L)=\sum_t (0.2L_t+\tfrac12 bL_t^2).
\]

The coefficient \(b\) has units of synthetic objective units per kWh squared.
The three proposed values are:

| Candidate label | \(b\) | Role |
|---|---:|---|
| linear control | \(0\) | Exact zero-gap control: a linear objective has the same minimum over the physical set and its convex hull |
| curvature low | \(1/7200\) (about 0.000138889) | At 360 kWh in one hour, the quadratic term is one-eighth of the linear term |
| curvature high | \(1/900\) (about 0.001111111) | At 360 kWh in one hour, the quadratic and linear terms are equal |

These scales use 360 kWh solely as the one-hour energy equivalent of the
declared 360 kW EGG cap. They are synthetic numerical contrasts, not fitted
tariffs, market costs, or estimates. The proposed grid uses the same two
positive coefficients for both depot cases and both horizons. Neither the
values nor any result from this candidate design is frozen.

The primary grid is the complete cross of two source-depot restrictions,
three b settings, and two full-recharge deadlines:

| Physical case | Deadline | Curvature cases |
|---|---:|---|
| Depot 15, all 37 services | 30:00 | linear control, curvature low, curvature high |
| Depot 16, all 37 services | 30:00 | linear control, curvature low, curvature high |
| Depot 15, all 37 services | 26:00 | linear control, curvature low, curvature high |
| Depot 16, all 37 services | 26:00 | linear control, curvature low, curvature high |

That is 12 candidate scenario cells. At \(b=0\), the zero gap is analytic at either
deadline; the common physical-planner/pricing objective is exactly
\(c(x)+0.2\sum_t L_t\). For the 30:00 cases, the already-prespecified flat-price
pilot result may supply its physical objective bound and incumbent only if a
separate baseline-bounds scope review finds it adequate for the nonlinear
comparison and the audited pilot case identity, feasible set, objective, and
replay match exactly. No universal \(10^{-4}\) threshold is assumed necessary;
the review must set and justify the required resolution before any sensitivity
result is inspected. If the baseline evidence is inadequate, do not add a
replacement solve under this draft; keep the b=0 physical metrics unresolved
and defer the campaign. At 26:00, the first fresh uniform-price response can
also supply the physical linear-objective plan; do not add a separate duplicate
planner call. Do not spend a hull run to rediscover the linear identity. The eight
positive-curvature primary cells are the denominator
for the nonlinear-gap scenario tally. Keep 26:00 as a named full-recharge
deadline sensitivity under the existing 00:00 terminal-open policy. The
source-qualified one-trip-per-bus witnesses complete terminal charging by
25:00:31.4 and 25:01:07.4, respectively, so they remain feasibility references
at 26:00. This demonstrates only that the declared 37-bus references fit; it
does not establish an optimum or a practical overnight availability window.

Separate from that primary tally, add four one-factor synthetic hardware
stress cells at 30:00 and curvature high: both depots with 300 kWh usable
inventory and 360 kW charging, and both depots with 400 kWh usable inventory
and 180 kW charging. Keep the other EB-3-based assumptions fixed. These are
EGG perturbations, not values from the paper. They form a separately reported
four-cell stratum and are not folded into the primary eight-cell tally.

The reference physical baseline remains the paper's EB-3 concept with 400 kWh
usable inventory. The 360 kW per-bus/shared cap, one connector, unit efficiency,
zero additional reserve, 00:00 terminal opening, and 30:00 baseline deadline
are declared EGG model choices; they do not reproduce the paper's charging
layout or assert deployed infrastructure. The 300 kWh and 180 kW cases are
explicit synthetic hardware changes. Retain the EB-3 traction and auxiliary
rates for all cells; do not add a separate energy-rate factorial to this small
study.

The post-pilot matching audit independently reconstructed exact stored-input
relaxation lower bounds 301.3153438838777 (depot 15) and 305.6338078838777
(depot 16). Each matching uses one relaxed path; neither value establishes a
physically feasible fleet or the flat-price physical optimum. Together with
the bounded flat pilot, this evidence motivated postponing the broader study.
The proposed coefficients and scenario cells were not selected from those
numerical outcomes.

## Matched bounds and classifications

For each scenario, retain physical-planner bounds
\(D\in[L_D,U_D]\) and complete-fleet-hull bounds
\(CH\in[L_{CH},U_{CH}]\). A feasible physical plan supplies an upper bound on
D; a valid physical solver bound supplies its lower bound. A replayed convex
mixture supplies an upper bound on CH; only the admitted global pricing /
Fenchel argument supplies its lower bound. A restricted pool is not a global
lower bound. Preserve solver-conditioned bounds and replay receipts separately.

The gap enclosure is

\[
\Delta\in[L_D-U_{CH},\,U_D-L_{CH}].
\]

Classify without subtracting incumbents:

- **Certifiably positive:** the gap lower endpoint exceeds the predeclared
  objective resolution \(10^{-4}\).
- **Numerically zero at resolution:** the gap upper endpoint is at most
  \(10^{-4}\) and no less than the frozen negative numerical guard.
- **Unresolved:** the interval crosses the resolution band or either valid
  enclosure is missing.
- **Infeasible:** a physical feasibility check is contradicted, preserved as a
  model/source consistency failure rather than counted as a gap result.

An upper endpoint below the negative guard, a reversed interval, or
inconsistent physical/hull identities is a separate consistency-failure
status, not a gap result. The theorem \(\Delta\geq0\) can support the
zero-at-resolution classification when a valid raw enclosure straddles zero;
retain and report that raw enclosure without clipping it. Do not silently
repair any interval. Explain solver-conditioned or replay-tolerance
contributions. If a result is
unresolved, keep it in the candidate denominator and report it as such. Report the
primary eight positive-curvature cells and the four hardware cells separately
as counts of positive, numerically zero, unresolved, and infeasible cases.
The four b=0 cases are reported as analytic exact-zero controls, not as
evidence about nonlinear scenarios. These are counts over the candidate scenarios;
do not attach statistical prevalence or operator-population language.

## Physical and price-response quantities

For every admitted physical planner incumbent, report used buses, modeled
service energy, selected movement energy, total grid kWh, the hourly load
vector, intrinsic cost, and its physical and objective bounds. For every hull
certificate, report the mixture's weights and whole-fleet column identities,
expected used-bus count, expected total grid energy, average hourly load, and
the mixture objective. An expected bus count or average load is a convexified
quantity, not a dispatchable fleet.

For each recovered physical planner optimum \(s\), compute its own gradient
price \(p_{s,t}=0.2+bL_{s,t}\) and own-price regret against the same complete
physical response set:

\[
r(s;p_s)=c(s)+p_s\cdot L(s)-
 \min_{x\in X}\{c(x)+p_s\cdot L(x)\}.
\]

Keep the oracle's lower bound and replayed feasible response upper bound, so
regret is an interval. If more than one distinct tied physical optimum is
found, retain each result; do not report one convenient tie as representative.
For an unresolved planner, identify the regret as belonging to its named
incumbent, not to a proven physical optimum. Whole-fleet regret is primary;
regret per used bus may be shown separately and cannot replace it.

For the hull solution, set \(p_{h,t}=0.2+b\bar L_{h,t}\) at the best replayed
hull-mixture load and report the physical planner incumbent's common-price
fleet LOC:

\[
\mathrm{LOC}_{\mathrm{fleet}}(s;p_h)=c(s)+p_h\cdot L(s)-
 \min_{x\in X}\{c(x)+p_h\cdot L(x)\}.
\]

Use a fresh admitted response bound at this price. Call it a certified
common-hull price only when hull optimality and its supporting-price residual
are admitted; otherwise label it the price of the best current hull mixture.
Keep \(p_s\) and \(p_h\) distinct. Do not infer payment balance, strategic
behavior, voluntary participation, or convergence. Check the price-support
inequality \(r(s;p_s)\geq D-CH\) against the respective enclosures as an
independent consistency check, not as a replacement for either computation.

## Candidate reuse baselines

Reserve three hull-method arms only for the baseline 30:00, high-curvature
case, separately by depot. These are candidates, not frozen or currently
executable settings.

1. **Cold coordinator start:** use the current compact hull coordinator's
   default cold path: one fresh full-fleet pricing solve at the linear vector
   \(p=a=(0.2,\ldots,0.2)\) supplies the initial column, then run the hull
   procedure. Retain the source-qualified one-trip-per-bus witness as an
   external feasible reference, not as though the current coordinator already
   accepted it as its sole seed.
2. **Retained columns:** seed from the audited flat-price physical-plan column
   for that depot plus the common source-qualified witness. Replay every
   column under the unchanged high-curvature physical identity. Discard any
   previous mixture weights, tangents, bounds, duals and objective value; the
   high-curvature hull certificate is solved afresh. Deduplicate only exact
   projection duplicates.
3. **Retained columns plus shifted-price proposal:** use the same replayed
   pool and propose
   \(p_{\mathrm{shift},t}=0.2+b_{\mathrm{high}}L_{\mathrm{flat},t}\),
   where \(L_{\mathrm{flat}}\) is the audited b=0 physical-plan load. This is
   one paid oracle call inside the hull routine's six-call ceiling; it is not a
   lower bound or certificate. The hull arm must still obtain its own fresh
   final pricing bound and valid mixture.

There is an implementation gate here. The present
`native_pathflow_hull.certify` entry point imports columns only from a prior
certified hull state and requires a matching state identity; it does not accept
the flat-price pilot plan or the source witness as a direct initial pool. Its
default cold seed is the price-oracle call at \(a\), not a supplied witness. It
also has no explicit shifted-price proposal parameter. Before a freeze, a
small separately reviewed coordinator adapter must support replay-validated
initial columns and the one-call proposal without fabricating a prior hull
certificate. Add pure schema, identity, replay and call-accounting tests. If
that gate is not passed, mark the four reuse comparison arms blocked; do not
replace them with an outcome-selected seed or price. They remain inside the
candidate compute envelope below.

The physical set is unchanged across the three b cases, so the flat plan may
be replayed for column reuse. The 26:00 and hardware-perturbation cases have
new physical identities; do not transfer stale columns or bounds across the
changed deadline, battery or charging rate. The common one-trip-per-bus
witness may be replayed as a feasible reference wherever it passes the revised
case. Never import publisher-generated vehicle blocks or charging plans. This
candidate grid contains no separate physical MIP-start comparison; an audited
flat plan is not a substitute for a cold physical result. Count the shifted
proposal call within its hull arm, and compare reuse time/work only alongside
the final bound quality and termination status. The source witness is a
feasibility reference, not evidence that reuse finds a better schedule.

## Prospective admission gates and compute envelope

This 11-hour ceiling describes a candidate ceiling only. It is not admitted,
requested, or authorized for execution. The pilot and its matching diagnostic
prompted the deferral; the next practical step is a bounded qualification or
pilot chosen after a separate scope and cost review, not this full campaign.
No cluster use is proposed by this note.

Before any stage is considered, an independent review must establish that the
baseline flat-price evidence is adequate to interpret the planned nonlinear
comparison. It must assess both 30:00 depot cases, the audited physical
incumbents and numerical lower bounds, the exact matching-relaxation bounds
with their different ideal-model scope, and all replay/source identities. The
review must set and justify a useful resolution for the intended question;
the native `1e-4` certification width is not automatically a scientifically
necessary flat-baseline gate for these 37 services. A wide or mismatched flat
interval blocks admission until a bounded follow-up is separately chosen and
approved. Do not silently tighten the threshold after seeing sensitivity
results.

Other candidate prerequisites are:

1. The source-pinned case adapter, complete movement/energy replay, and revised
   26:00 feasibility references pass independent preflight for both depots.
2. The compact physical planner's PWL loop and the compact-pricing hull
   coordinator pass matched-objective, replay, bound-admission and time-budget
   qualification on enumerable controls. Fresh own-price and common-mixture
   responses receive their own tests and audit rules.
3. The flat pilot, its exact matching follow-up, and the scope review have
   frozen manifests and independent audits. The matching bounds remain labeled
   ideal stored-input relaxations, not native physical lower bounds. The
   separately reviewed one-bus obstruction, together with the independently
   replayed two-bus witnesses, supports minimum cardinality two only under these
   exact declared graphs; neither result establishes cost optimality.
4. The reuse-pool/proposal adapter described above passes pure identity,
   replay and call-accounting tests; otherwise its four arms are blocked.
5. A manager separately decides whether the question, 11-hour upper envelope,
   and cost justify any future launch. Only then freeze a protocol, code
   commit, environment, case hashes and report schema before inspecting
   sensitivity results.

If those gates later pass, consider three sequential stages. Stage 1 is the
six baseline 30:00 cases; Stage 2 is the six 26:00 cases; Stage 3 is the four
hardware perturbations plus four retained-column/shifted-price hull comparators
at high curvature, two per depot. The high-curvature cold hull runs are already
in Stage 1. Failed gates block not-started cells without substitution. Within
an admitted stage, preserve every prescribed result, including independent
failures and unresolved intervals.

The candidate coordinator accounting is based on current implementation
semantics. `native_pathflow.solve_planner` is one PWL **routine**, not one MIP
solve: it rebuilds the model and can perform up to 48 tangent-refinement MIP
phases. Each phase has a 180-second solver cap, but all phases, extraction and
replay share a 240-second routine deadline; do not budget 48×180 seconds.
`solve_pricing` is one native optimization phase per call. Reserve two separate
fresh `solve_pricing` calls per scenario, one at the physical plan's own price
and one at the best current hull-mixture price, even when the two prices happen
to coincide. At \(b=0\), the first fresh 26:00 response can also supply the
linear physical plan; the second remains a separately logged cross-check.
Each response call has a 180-second solver cap, a 240-second full-routine cap,
and a 255-second child hard stop.

Each `native_pathflow_hull.certify` routine has a 24-minute total deadline, at
most six global pricing calls, eight master LP solves, 48 columns, up to 256
exact pool-polish steps and a cumulative five-second polish budget. Every
pricing/MIP or master/LP phase is capped at 180 seconds but shares the single
24-minute hull deadline. The shifted proposal consumes one of the six pricing
calls; it is not extra. The outer hull child hard stop is 24 minutes 15 seconds.
The lower 24-minute cap, instead of the earlier 30-minute draft, keeps the
two requested fresh response calls within the original stage ceilings.

| Stage | PWL physical routines | Hull routines | Fresh response calls | Routine-cap sum | With 15-second child margins |
|---|---:|---:|---:|---:|---:|
| 1: 30:00 primary | 4 | 4 | 12 | 160 min | 165 min |
| 2: 26:00 primary | 4 | 4 | 12 | 160 min | 165 min |
| 3: hardware and reuse | 4 | 8 | 16 | 272 min | 279 min |
| **Total** | **12** | **16** | **40** | **592 min** | **609 min** |

Stage 1's two b=0 physical baseline results come from the independently
admitted 30:00 flat pilot; if they do not pass that gate, Stage 1 is deferred,
not supplemented with unbudgeted replacement solves. In Stage 2, the first of
the two fresh flat-price calls for each b=0 26:00 case also supplies that
linear physical plan. The 12 PWL routines cover the eight positive-curvature
primary cells and four hardware cells. The 16 hull routines cover the eight
positive-curvature primary cells, four hardware cells and four Stage 3 reuse
arms. Each reuse arm receives its own two fresh response calls (own-price and
that arm's common-mixture price); this conservative accounting does not assume
the physical response can be shared across arms. The total cap is at most 576
PWL MIP phases, 40 fresh response MIP phases, 96 hull-pricing MIP phases and
128 hull-master LP solves. Those are worst-case caps; the PWL phase count is
separately limited by each 240-second routine deadline. The staged envelopes stay at three hours, three hours and
five hours, with the remainder for fixed startup, serialization and review;
do not borrow time across stages or increase caps to rescue a weak result.

Any later admitted run is sequential on one CPU, one Gurobi thread, and at most
8 GB RAM. No retries, solver retuning, hidden pool growth, extra price samples,
or post-result grid expansion. Preserve raw values, every start, bounds,
replay/normalization ledgers, exceptions, timeouts and receipts for failures as
well as successes. A capped routine remains bounded or unresolved under its
actual enclosure; a stage allocation does not extend its scientific deadline.

## Reporting boundary

If this candidate is later admitted, publish the then-frozen case table, every
status and bound interval, the nonlinear-gap tally with its denominator, all
four exact linear controls, and the
separate hardware tally. Include fleet size, energy, own-price regret, and
common-mixture-price fleet LOC with units and case identity. Show the strong
reuse arms beside the cold baseline with total solve time and work counts.
Keep the 37-bus constructions labeled as feasible references, never optima.

All coefficients, costs, and hardware changes are synthetic. The input is a
curated timetable with modeled movement distances, not vehicle telemetry. No
result supports an operational bus recommendation, a calibrated tariff,
general charger-market claim, statistical frequency of positive gap in the
population, or representation of the publisher's two-depot charging model.
