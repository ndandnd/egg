# Interpretation review — closed resource-recourse diagnostic

Scope: only the frozen `PROTOCOL.md`, `readout-stdout.txt` and selected fields
of `READOUT.json`. No original table, owned plan, raw owner receipt, replay,
solver, new numerical calculation or new metric was accessed or performed.

## What completed, and what remains missing

Administrative closure passed: complete ledger/accounting, no owner failures,
findings, configuration failure, stop signal or dispatch stop. This does not
mean complete scientific endpoints. All eight acquisitions were attempted; five
new priors were admitted. Of 32 planned active cells, 26 were attempted, 22 have
qualified QP points, 21 have full-method success and 22 have operational costs.
The six unattempted fixed cells have no acquired current-resource reference;
they are genuine missing endpoints, not free costs or successful fallbacks.

All 16 planned resource-by-tariff blocks remain visible, but only ten have both
operational arms. Only two of eight planned resource interactions are defined,
both for 10001. The complete-eight-interaction mean is correctly null. Neither
the ten available blocks nor the two available interactions substitute for the
planned denominator. Four exposed groups are development cases; two tariffs and
two resource levels do not create independent population units.

The distinction between 22 QP qualifications and 21 full-method successes is
substantive. At 10009/90/source1, adaptive routing found no admissible first
incumbent (`NO_SOLUTION_FOUND` in the routing packet), then a qualified QP on
the common acquired route retained a valid operational endpoint. Its zero
fixed-minus-adaptive cost contrast is not successful adaptive route discovery.
Conversely, a recorded later routing cutoff can coexist with a valid earlier
admitted route and full-method success; a failure-inventory entry alone is not
an endpoint classification.

## Feasibility recourse is the clearest observation

The 45-kW fixed-reference acquisitions for 10006, 10009 and 10005 returned native
`INFEASIBLE`. Their scope is the constructed current-physics matrix with exact
reference fleet N and all reference movement choices fixed. These are numerical
statuses for those restricted models, not unrestricted physical infeasibility
certificates. Rejection of the original timed schedule is a separate weaker
fact. Indeed, 10001's old 45-kW schedule is invalid while fresh fixed-topology
acquisition succeeds: old-schedule failure does not imply topology failure.

For 10006/45, cold adaptive routing finds independently admitted five-bus plans
under both tariffs despite the missing fixed-reference prior. This establishes
an operationally valid routing-recourse witness at the same fleet count under
the restricted grid. It does not establish its minimum cost, necessity of every
changed movement, or a positive finite fixed-versus-adaptive cost gain: the fixed
operand is missing. The adaptive plans use approximately 570.989 kWh, whereas
the original/reference topology's reported ideal demand is approximately
555.522 kWh. Better feasibility therefore does not require lower total energy;
route-dependent access and timing are plausible explanations, still unseparated.

For 10009/45 and 10005/45, both cold tariff searches returned `INF_OR_UNBD`, no
incumbent, no QP and no operational endpoint. They returned without native
overrun; calling these mere timeouts would misdescribe the readout. Equally,
`INF_OR_UNBD` does not resolve infeasible versus unbounded solver status and
does not prove global fixed-N infeasibility. Those four cells remain unresolved
under this method and frozen budget. No rescue run is justified by relabeling
them as proven infeasible or by treating missing values as zero routing value.

## Defined cost comparisons are modest and heterogeneous

Only 10001 supports the complete 90-to-45 interaction. Under flat source0,
adaptive gain is about 0.195301 cost units at 90 kW and 0.163498 at 45 kW;
the reported interaction is **−0.0318028**, not the predicted larger routing
cost advantage under tighter capacity. Under source1, the interaction is about
3.91e−13. These tiny represented differences are numerical-scale agreement,
not exact equality or an optimization-gap certificate. The flat-price gains
relative to the preoutcome fixed E_ref are about 0.001574 and 0.001318; E_ref is
an electricity-cost denominator, not total bill, energy or a population effect.

The 10001 adaptive flat-price solutions consume more grid energy than fixed
(approximately 505.733 versus 500.333 kWh); increased linear electricity is
offset by a lower quadratic component. Fleet is equal and reported deadhead
cost is zero. Thus this is not evidence of energy saving, a changed fleet
mechanism, or a pure cheap-window-access explanation. Zero deadhead cost also
does not mean identical physical travel or movement energy.

The other defined blocks reinforce the need to retain all controls and failures.
At 90 kW, 10009 has a small positive flat-price gain and a fallback-based zero
source1 contrast; 10005 has zero retained contrasts for both tariffs. For
10006/90, source0 is zero and source1 favors fixed by about 0.038065. A broader
adaptive feasible set does not make this bounded two-tangent implementation
dominate a separately optimized fixed-route control. None of these 90-kW-only
comparisons supplies a missing resource interaction.

## The structural diagnostic narrows the hypothesis

All original paths return by terminal opening, but the no-midday-SOC-sufficiency
condition is false for 10006, 10009 and 10005. It is true only for 10001. The
simple common-terminal charging construction therefore cannot be used to explain
away route-dependent charging opportunities for three of four groups. A failed
sufficient condition is not a necessary-condition violation or an infeasibility
proof. At 45 kW, aggregate terminal capacity is below original ideal demand for
those three groups, but earlier charging opportunities exist and must be treated
explicitly before any capacity argument becomes a necessary cut.

No group satisfies the conditional all-energy-fits-cheap-window diagnostic:
10001 is explicitly false at both capacities; the other three are null because
the preceding SOC assumption fails. Null is not false. The original-path
diagnostic does not establish the load set of a newly adapted topology, equality
or nesting of load sets, or the binding physical constraint in a solver result.
Finite QP point qualifications remain distinct from ideal route ordering, which
the readout leaves unresolved.

## Concessions and the next useful science

This experiment provides a concrete conventional routing feasibility witness
under reduced grid power, but not an across-case cost-value result. Its only
complete group's resource interaction does not support an increasing routing
cost advantage. The missing endpoints prevent the planned aggregate claim;
they do not establish absence of routing value. No ML value, trained-information
causality, population conclusion, global optimality or unrestricted infeasibility
claim follows. The separate learned-family stopping decision is unchanged.

The next bounded step should be a **source-defined charging-opportunity cut
diagnostic**, before another solve: derive from the unchanged physical equations
what cumulative per-bus energy/SOC demand must be served before each available
charging interval, and what the shared grid/connector/window constraints can
supply. Distinguish necessary capacity cuts from optional sufficient terminal
constructions. Its falsifiable question is whether timing/access cuts can explain
why the reference topology fails while the admitted 10006 topology works despite
higher total energy. If aggregate energy alone already explains a proposed
contrast, concede that rather than credit route flexibility.

This review authorizes no new plan access or numerical evaluation. A later
manifest would need to bound any reference-versus-admitted-path diagnostic and
name its development-case selection and limits prospectively. If the source
equations cannot give a discriminating necessary condition, report that limit;
do not automatically retry searches, scan capacities, expand to all 79 pairs,
refit models, or claim a favorable ML regime. The potential contribution is a
tested classical account of when routing changes feasible charging access and
when competent charging alone removes apparent route value.

One additional competence limit is source-defined: adaptive routing chooses its
best route by replay cost before its single final QP, while the common prior
comes from zero-price feasibility acquisition. The fixed arm separately
target-QP-optimizes that prior. Adaptive fallback is therefore not an already
target-charged fixed-QP incumbent; searching a larger route set does not guarantee
dominance of the fixed-QP endpoint under this composition. This is a possible
explanation of the negative 10006 baseline contrast, not an established cause
without further audit. Any future cost-value study would need a strong,
target-charged common incumbent with its construction and use fully paid inside
the prospective budget. This does not authorize a rerun, automatic rescue, or
revision of any past cost point or gate.
