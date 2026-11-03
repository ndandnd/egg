# Charging-cap repair results

Job 691594 completed in 109 seconds (exit 0; one allocated CPU; maximum RSS
230,152 KiB). All four cells returned without a hard timeout. The new
per-visit charging-cap filter produced one new physically replayed candidate:
the 2017 learned arm. Its eight-bus fleet has exact target cost 980.998586
cost units. This is a feasible physical candidate, not an optimality claim.

| Case | Policy | Cover buses; status / gap | Fixed-route charge | Admitted candidate |
|---|---|---|---|---|
| 2016, 20 services | cost-only | 4; optimal / 0 | infeasible | 4-bus archived source fallback, 553.474774 cost units |
| 2016, 20 services | cost-learned | 5; stopped / 0.201 | infeasible | 4-bus archived source fallback, 553.474774 cost units |
| 2017, 28 services | cost-learned | 8; stopped / 0.500 | feasible; replay passed | New 8-bus repaired fleet, 980.998586 cost units |
| 2017, 28 services | cost-only | 4; optimal / 0 | infeasible | 5-bus archived source fallback, 724.660042 cost units |

The three failures were at the fixed-route charging stage. Their fallback
costs are archived source plans, not costs from the proposed covers. The
2017 learned fleet is the only new repair; the saved independent replay
confirms it uses eight buses. For context, the archived stage-2
target-verified 2017 incumbent remains 689.474312 cost units, distinct from
the 724.660042 source fallback.

The 2017 learned cover ended with a 0.5003 MIP gap, so its eight-bus cover is
an incumbent, not a certified minimum even for the relaxed model. Its native
target-hull assessment ended `budget_exhausted`: the saved replay-checked
global lower bound is 588.165909 cost units and the mixture upper is
688.761949. The mixture upper is not a physical feasible-plan bound. The
global lower bound also lower-bounds the physical optimum. The replayed
980.998586-cost fleet is a physical feasible upper candidate; the hull
assessment did not establish physical optimality. The three source
fallback cells correctly skipped fresh hull checks, with empty assessments
and zero hull time; they add no new bounds.

| Case / policy | Inference (s) | Cover (s) | Charge stage (s) | Repair total (s) | Pool (s) | Hull (s) | Child (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2016 cost-only | 0.000 | 2.213 | 0.243 | 2.456 | 0.000 | 0.000 | 5.689 |
| 2016 cost-learned | 0.037 | 5.233 | 0.242 | 5.513 | 0.000 | 0.000 | 8.852 |
| 2017 cost-learned | 0.075 | 5.276 | 0.834 | 6.186 | 0.305 | 61.260 | 70.961 |
| 2017 cost-only | 0.000 | 1.253 | 0.587 | 1.842 | 0.000 | 0.000 | 5.506 |

The learned arm supplied the sole new feasible repair, but it used a
time-limited cover with an open optimality gap, while cost-only failed on the
2017 case and returned a source fallback. The 2017 learned fleet is more
expensive and uses more buses than the archived source fallback; its cost
also exceeds the archived target-verified incumbent. These four unreplicated
cells do not support a learning-advantage or speedup claim.

The follow-up numerical LP diagnosis found all four fixed covers feasible when
each vehicle has its own interval capacity; enforcing the shared interval
capacity made the same three failed covers infeasible while the repaired 2017
cover remained feasible. This corroborates the saved native GRB statuses as a
shared-charging bottleneck in these selected covers, but the LP comparison is
numerical evidence, not an exact infeasibility certificate. Independent
replay reconfirmed all four plan identities and exact costs. See the [diagnosis
summary](CHARGING_CAP_FAILURE_DIAGNOSIS.md), [diagnosis data](CHARGING_CAP_FAILURE_DIAGNOSIS.json),
and [independent replay receipt](INDEPENDENT_REPLAY_CHARGING_CAP.json).

Across the two compared same-case, same-market hull runs, the combined
target-hull interval is [588.165909, 686.653533] cost units (the charging-cap
global lower and the lower of the two mixture uppers). The physical-optimum
enclosure is [588.165909, 689.474312], using the same global lower and the
archived target-verified feasible control. Both gaps remain open. This
two-run comparison does not establish an ML benefit or speedup and makes no
claim to the strongest bound across uninspected older runs; exact values and
receipt hashes are recorded in
[BOUNDS_CHARGING_CAP_COMPARISON.json](BOUNDS_CHARGING_CAP_COMPARISON.json).
