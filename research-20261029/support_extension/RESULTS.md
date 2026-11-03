# Support extension: closed exact qualification

The original support failure survives the specified nonnegative-energy,
nonnegative-cost movement additions with unchanged equipment. It need not
survive a richer equipment set. A fully replenished battery25 bus at fee7
restores support, whereas the same added bus at fee8 leaves a positive gap.

The written proof supplies the continuous-domain claims. Independently
written raw physical enumeration matched the analytic implementation in all
14 prospectively fixed cases: 10 positive-gap, 4 zero-gap, no failed, late,
missing or unattempted cases. All 17 negative controls rejected and the
nominal arithmetic smoke check passed. This is exact-model implementation
qualification, not statistical replication or fleet-population evidence.

## Findings

1. An old unsupported plan cannot become supported merely by enlarging the
   feasible set. Its own marginal price is unchanged and its deviation set
   grows, so its regret cannot decrease. A newly admitted plan can nevertheless
   become a supported optimum of the enlarged problem.
2. A sufficient survival condition is min(D_X,D_Y)>CH_X. A sharper dual
   certificate preserves the old hull if all added plans have linear bill
   at least V_X(p*) at an attained old hull-dual price p*. Under that certificate,
   erasure requires both fleet equality and supply Fenchel equality. A strict
   added-plan bill margin epsilon gives gap>=min(old gap,epsilon)>0.
3. Keeping original services, batteries, windows, resources and full refill,
   extra movements with nonnegative energy/cost are dominated by old physical
   plans. Thus D=97, CH=7591/80, gap169/80 remain unchanged for the entire
   stated expansion class. The numerical movement illustration additionally
   delays the B bus's terminal access by0.1h and retains infeasible branches.
4. Adding buses with battery B and fee7, while retaining all old buses, restores
   support exactly for B >= (55-sqrt(95))/2, approximately22.6266, within
   20<=B<=30. This changes equipment, not just routes of the original model.
5. For battery25 and fee h>=7, support is restored only at h=7. At h=8,
   D=93<old CH94.8875 but new CH92.95, gap0.05 and own-price regret1.
   Therefore D_Y<=old CH is necessary but not sufficient for erasure.

|Declared expansion|D|CH|Gap|Own-price regret of physical optima|
|---|---:|---:|---:|---|
|Original model|97|94.8875|2.1125|13|
|Movement alternative, same equipment|97|94.8875|2.1125|13|
|Battery22.6, fee7|93.152|510099/5476|169/684500|0.104|
|Battery22.7, fee7|93.058|93.058|0|0|
|Battery25, fee7|92|92|0|0|
|Battery25, fee8|93|92.95|0.05|1|
|Battery25, fee12|97|94.8875|2.1125|5 and13, both tied optima retained|

All14 exact rows are in cycle01/TABLE.md; its Fraction displays are verbatim
inline output. cycle01/results.json retains every raw branch, labeled type
assignment, vertex, charging witness and continuous price-response set.
Comparison merges only identical projected economic outcomes/response unions,
not physical records. No old bank, journal, solver or private input was used.

## The erasure witness

New battery25, fee7, one bus: SOC25 before A,10 after A,15 after5kWh early
charge,0 after B,25 after25kWh terminal charge. Shared power and full refill
hold. Load(5,25), operating cost7, supply cost85, total92. At marginal price
(5,5) this fleet minimizes the posted bill over the complete expanded set.
The old one-bus load(10,20) still has regret13 at its own price(6,4).

## Execution and limits

Source349018d917d3fedc098e77b34b9fb586ffbfd74c, control ed13b362.
One owner dispatch, managed session73360 exited0. Worker85478 exited0 and
was reaped. No unresolved child. Source admission and publication were inline;
no repeated check/export/finalizer. Meter1.01 displayedCPU/2.55wall, retained
1.03CPU administrative allowance, below NEW60CPU/90wall. See final receipt.

The general support/convex-hull mechanism is prior art. The new content is
the exact physical stability class, changed-equipment region and counterexample
to a proposed sufficiency shortcut. No V2G, calibrated welfare, public-fleet
prevalence, unrestricted larger-EVSP theorem or new ML result is established.
