# Necessary early-capacity cuts explain the fixed-reference failures

The frozen diagnostic completed ONCE after source/protocol478da6df was pushed.
It analyzed only the permitted derived READOUT fields, with no original cases,
plans, TRAIN rows, replay, optimizer or model. All eight reference diagnostics
were available. Exactly the three45kW references whose fixed models returned
INFEASIBLE violate the necessary ideal capacity cuts. All twelve available
adaptive diagnostics show no violation; four planned adaptive records remain
missing. No native status or past admission was changed.

## What the cut says

All consumption/returns precede terminal opening1080. A bus with total draw D
and usable initial battery B−reserve needs at least ell=max(0,D−(B−reserve))/eta
grid kWh before opening. Only its selected depot visits can supply that energy.
Per-bus capacities use each bus's UNION of visits; shared capacity uses the
MERGED UNION across buses, not their sum. The shared early requirement also
includes max(0,total grid demand−post-opening capacity). These are necessary
conditions under the stated ideal physical assumptions, not sufficient schedules
or tolerance-qualified code/unrestricted certificates.

|45kW reference|Shared early requirement, kWh|Accessible early upper capacity, kWh|Shortfall, kWh|Controlling shared lower bound|
|---|---:|---:|---:|---|
|10001|0|0|0|No early charge required|
|10006|130.4333|72|58.4333|Sum of per-bus reserve deficits|
|10009|478.5889|255.75|222.8389|Sum of per-bus reserve deficits|
|10005|351.4444|89.25|262.1944|Total energy minus terminal capacity|

Values are rounded here; exact represented Fraction values remain primary in
attempt01/receipt.json. The10001 row has no violation, rather than a positive
feasibility certificate. All90kW reference cuts also show no violation. The three
45kW failures additionally have per-bus violations: one bus in10006, all four
in10009, and two in10005. Window counts alone would miss these energy obligations.

## Why the higher-energy10006 alternative works

The reference topology exposes only96 merged minutes of early depot opportunity.
At45kW that can supply at most72kWh, below its130.4333kWh required early grid
energy. The adaptive45kW endpoints at both tariffs expose194 merged minutes:
145.5kWh upper capacity versus130.9889kWh early requirement, leaving14.5111kWh
shared margin and no individual cut violation. Their total grid energy is higher
than the reference, but the early charging-access budget is larger as well.

This is a conditional ideal-model obstruction for the original fixed topology,
consistent with the earlier native INFEASIBLE statuses, plus independent prior
replay evidence for an alternative topology. Passing the necessary cuts does not
construct or prove the adaptive schedule; the already recorded physical replay
supplies that separate evidence. The cuts omit earlier prefixes, headroom and
subset allocation constraints. No exact ideal/tolerance-qualified equivalence,
new theorem or learning advantage is claimed.

## Concessions and next question

The result strengthens the charging-opportunity explanation for the reference
failures. It does not repair the preceding cost experiment: only2/8 interactions
remain defined and its complete mean stays NULL. Nor do reference-route cuts
settle the full-graph INF_OR_UNBD cases10009/10005. They exclude only the fixed
reference topology under the stated ideal assumptions, not every possible route
collection or the original variable-fleet EVSP.

Before more routing/training work, the next useful diagnosis is an all-declared-
mode outer capacity/energy cut at the same fixed N, with known feasible groups
as controls. That requires separately admitted owned case fields and a new
prospective source/protocol/command; current input authority does not extend to
cases/specs/plans. No solver retry, cap scan, extra cohort, refit or automatic
publication claim follows. If no outer cut excludes the unresolved cases, retain
that uncertainty rather than calling them globally infeasible.

The scientific unit is four exposed groups, not24 independent records. Resource/
tariff copies and unchanged/fallback routes remain labeled. Twelve adaptive cuts
are available with zero violations; the other four are unknown, not passes. All
original statuses, failures, cost components and negative learning gates persist.

## Resource closeout

External total.04CPU/.07wall seconds, within the NEW20CPU/45wall package and
body15/35 plus publication5/10 allowance. Retained rounding charge.06CPU. No
children or native libraries. Observed source/report metadata are prepublication;
external total includes startup/write/exit. Closed displayed process sums now
19811.15CPU/20406.13elapsed-sum; retained tracking19811.37CPU. These are not exact
session CPU or continuous elapsed. The legacy conditional guard2546.091499549272
and unknown actual old review CPU remain separate, without reset or refund.
