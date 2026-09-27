# Recommendation: minimal nonlinear Sistig public pilot

27 September 2026. **Advisory design only; no execution authorization or new
calculation.** Choose the experiment before seeing nonlinear results. The
question is whether positive supply curvature produces a resolvable difference
between the physical fleet planner and the convex hull of the **same complete
feasible fleet set**, and what own-price regret can be established for the
resulting physical plan. This is a much smaller question than the candidate
12-cell sensitivity census and reuse study in
`SISTIG_MARKET_SENSITIVITY_DESIGN_20260927.md`.

## One-cell recommendation

Use the full 37-service, depot-15 restriction, existing 400-kWh usable
inventory, 360-kW one-connector charging policy and 30:00 full-recharge
deadline. Select depot 15 in advance as the lower numbered source depot,
not for an observed nonlinear outcome. Use the candidate synthetic supply
function on all 30 hourly grid-energy periods,

\[
F(L)=\sum_t\left(0.2L_t+\tfrac{1}{1800}L_t^2\right),
\]

which is the design note's high-curvature value \(b=1/900\) in
\(0.2L_t+\tfrac12 bL_t^2\). Keep every movement, energy, vehicle-cost and
replay rule identical between planners. Use the current cold hull start;
retained-column and shifted-price comparisons require an adapter and answer
a different method question. The \(b=0\) zero gap is analytic, so no fresh
linear planner or hull solve is needed as a control. The archived flat plan
may be a replayed feasible reference, never a substitute for a new bound.

Run exactly three bounded routines, sequentially: one physical PWL planner,
one complete-fleet hull certificate with global pricing, and one fresh full
physical response at the named physical incumbent's own gradient price
\(p_{s,t}=0.2+L_{s,t}/900\). The physical result needs a solver-valid
\([L_D,U_D]\), a whole-fleet replay of the upper witness, case/source identity,
used buses, selected modes, SOC and charging ledgers, hourly grid load, and
intrinsic and total objective values. The hull needs a valid global
pricing/Fenchel lower bound \(L_{CH}\), a replayed convex mixture of whole
feasible fleets giving \(U_{CH}\), column identities and weights, average
load, supporting-price residual, and call-accounting ledger. A restricted
column pool alone cannot supply \(L_{CH}\).

Preserve the raw gap enclosure
\([L_D-U_{CH},\ U_D-L_{CH}]\). Predeclare a five-synthetic-objective-unit
resolution for this **pilot question**, subject to independent preflight
review before launch; it is not a calibrated tariff or universal tolerance.
A lower endpoint above five is a resolvably positive gap. An upper endpoint
at most five, together with the theorem \(D\ge CH\) and a raw lower
endpoint no farther below zero than a predeclared numerical guard, supports
zero at this declared resolution. Set that guard from qualification error
and replay tolerance before launch. Otherwise
report unresolved. A reversed interval, failed replay, or mismatched fleet
identity is a consistency failure, not a gap classification.

At \(p_s\), retain the response's solver-valid value interval
\([L_p,U_p]\) and replayed feasible upper witness. With
\(A=c(s)+p_s\cdot L(s)\), report the raw own-price-regret interval
\([A-U_p,\ A-L_p]\) and its response gap. Call this the regret of a physical
**optimum** only if planner optimality is independently certified under the
declared numerical policy; a five-unit planner gap supports a near-optimal
incumbent label, not an exact optimum label. Otherwise report the regret of
the named incumbent. Preserve
every distinct tied optimum discovered, without choosing a favorable tie.
Do not spend a fourth response call on common-mixture-price fleet LOC in
this minimal question; reserve that for a separately authorized extension.

The three routine caps are 240 seconds for PWL planning, 24 minutes for
the hull, and 240 seconds for own-price response: **32 minutes of routine
time**. Child hard stops are 255 seconds, 24 minutes 15 seconds, and 255
seconds, totaling **32 minutes 45 seconds**. Add at most 75 seconds for
fixed startup, serialization and supervisor bookkeeping; the complete
one-cell attempt cap is **34 minutes**. Use one CPU, one solver thread,
at most 8 GB RAM, no retry, retuning, extra columns or added price samples
outside the frozen hull limits. Preserve partial results, errors, hard stops,
receipts and manifests; an unresolved run does not receive more time.

## Optional paired version

If the scientific question is specifically whether the two depot restrictions
differ under identical assumptions, precommit to **both** depot 15 and depot
16 high-curvature 30:00 cells. Each gets the same three fresh routines and
34-minute complete cap, sequentially; the total cap is **68 minutes**. Do
not decide whether to add depot 16 after seeing depot 15's result. Report
two named enclosures and regret intervals, not a prevalence estimate or a
claim about the publisher's two-depot fleet. This option is the smallest
paired comparison; it still cannot support a curvature or deadline trend.

## Admission and stop rules

Before freezing either option, require independent qualification of the
PWL planner, complete-fleet hull/pricing coordinator and own-price response
on enumerable controls, including matched objectives, replay, bound signs,
supporting-price logic, child time limits and failure accounting. Recheck
the public payload, graph, price/curvature units, case identity and feasible
fleet set. Independently audit the archived flat pilot and the exact
matching/one-bus proof scopes. The flat pilot's numerical pricing intervals
are broad (depot 15: about 237.14–408.53; depot 16: about
232.15–433.75); the exact matching bounds around 301.32 and 305.63 are
for an ideal stored-input relaxation, not native physical endpoints. Their
main role here is provenance and context. A universal \(10^{-4}\) flat-price
accuracy gate would not answer the proposed high-curvature comparison. The
preflight review should instead confirm that five units is a meaningful and
attainable **reported resolution** for the matched nonlinear bounds, or set
a different justified resolution before any public nonlinear output.

Freeze the chosen option, hashes, budget, report fields, admission rules and
independent audit plan in a separate protocol. Do not start if qualification,
source/replay identity or fresh global hull-bound logic fails. During an
admitted attempt, stop at any failed identity or physical replay, invalid
bound direction, missing global hull pricing bound, budget exhaustion or
hard timeout; retain the evidence and label the result blocked, failed or
unresolved as appropriate. A bounded run is still useful if it produces
honest enclosures but cannot classify the gap. Afterward, an independent
reviewer must reconstruct the bound and replay evidence before any scientific
claim is admitted.

Any result concerns only these synthetic single-depot adaptations. A positive
or zero-at-resolution outcome does not establish physical optimality when the
planner remains bounded, a complete sensitivity pattern, calibrated energy
prices, operational savings, or a recommendation for the source operator.

## Research-lead scope decision

Proceed toward the one-cell, 34-minute option after its separate implementation
and independent preflight gates. This is a preparation decision, not a source
freeze or launch. Depot 15, the full 37-service graph, the stated synthetic
curvature and the three matched routines remain the prospective scope. Do not
expand to the optional paired version based on the first outcome.

Use the literal conclusion “gap at most five units under the declared numerical
policy” if the certified upper endpoint establishes it; do not call this an
exact zero gap. Preserve all intervals and report any independently supported
positive lower endpoint, including one below the five-unit resolution. The
five-unit threshold controls pilot classification, not which evidence is
shown. No broad sensitivity or reuse campaign is admitted by this decision.

The new cardinality-flow attempt reports stronger ideal lower bounds near
404.92 and 414.39 and is undergoing independent audit. Once admitted, report
those separately from the original matching bounds and native endpoints;
they do not replace matched nonlinear global bounds.
