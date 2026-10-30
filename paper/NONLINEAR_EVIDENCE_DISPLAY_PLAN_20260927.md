# Prospective nonlinear evidence display plan

27 September 2026. **Design only; no pilot output is available.** Add one
figure and one compact table after independent result audit. Keep the current
seven-figure PDF and Figure 7 unchanged until a bundled manuscript revision.

## Figure: bounds for one finite 30-hour service block

Use three panels:

1. **Hourly grid energy:** step curves over periods `t=0,...,29` for the
   physical planner schedule, hull-mixture load mean, and own-price physical
   response. Label the x-axis “hour within the finite 30-hour service block”
   and y-axis `L_t` in the model's declared grid-energy units. Label the hull
   curve “convex mixture mean—not an executable fleet.”
2. **Objective enclosures:** range marks for `[L_D,U_D]` and `[L_CH,U_CH]` on
   a common stored objective-unit axis, with endpoints and no midpoint
   estimates. Identify the planner incumbent when bounded and the hull upper
   endpoint as a replayed mixture witness.
3. **Signed intervals:** plot `Delta=[L_D-U_CH,U_D-L_CH]` and regret
   `[A-U_p,A-L_p]` with zero references; give regret a separate axis as
   needed. On the gap axis mark `+5` resolution and the `-1e-4` consistency
   guard, and print the report classification verbatim. Preserve signs and
   both endpoints.

For panel 1 use `planner/result.json.assessment.replay.load`,
`hull/result.json.result.mixture.load_exact`, and
`own_price/result.json.assessment.replay.load`. Convert stored exact fractions
without rounding and retain source JSON for audit.

**Caption:** “One synthetic depot-15, 37-service, finite 30-hour service
block. Gap and regret are conditional numerical enclosures from stored
binary-float endpoints, not proofs of an exact physical optimum or gap. Five
objective units is the predeclared classification resolution; `1e-4` is only
the negative consistency guard. The hull curve is a convex-mixture mean, not
an executable fleet; the 30-hour deadline does not establish recurring daily
feasibility.” Do not duplicate Figure 7's public witness/SOC story.

## Compact results table

Columns: **quantity/evidence**, **stored interval or value**, **status and
interpretation**. Preserve signed endpoints:

- Physical planner: `planner/result.json.assessment.{lower_exact_stored,
  upper_exact_stored,status,plan_hash,used_buses}`; call a bounded plan a
  named incumbent.
- Full-fleet hull: `hull/result.json.assessment.{lower_exact_stored,
  upper_exact_stored,columns}` plus raw `result.status`; identify the upper
  witness as the replayed convex mixture.
- Gap: `summary.json.report.{gap_interval_exact_stored,gap_classification,
  resolution,negative_guard}`.
- Own-price response: `own_price/result.json.assessment.{lower_exact_stored,
  upper_exact_stored,status}`; identify input price `p_t=.2+L_t/900`.
- Own-price regret: `summary.json.report.{own_price_regret_interval_exact_stored,
  regret_subject}`; retain the named-incumbent qualifier unless planner
  optimality is separately certified under the declared numerical policy.

Publish only independently audited replay/receipt values; the runner summary
marks its claim scope audit-pending. Footnote the stored-coefficient synthetic
objective, numerical-policy scope, and absence of any exact physical optimum,
exact physical gap, or executable hull-mixture fleet. For an unresolved result
show the signed gap interval and “unresolved at five”; for an informative
result retain the interval and literal protocol classification.
