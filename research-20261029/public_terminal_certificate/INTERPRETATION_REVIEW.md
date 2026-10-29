# Exact terminal witness: independent compact closeout review

29 October 2026. Read cycle01 `results.json` (public outcome), `owner_receipt.json`, `changes.json` and the parent-folder `owner-time.txt`. No new replay, numerical run, hash, native solve or raw prior input/candidate inspection. Existing lower-bound and one-bus-obstruction results are used as established premises, not rerun. Reviewer actual CPU is UNKNOWN.

## Outcome and permissible new claim

The new exact construction passed independent strict replay and provides a two-bus physical upper witness of **442.1230490171687** in the declared ideal stored-input model. Its authoritative cost is the exact fraction in the public result row, rather than that rounded display. The report records no failure and resource_pass=true. This is a new explicitly adjusted witness, not retroactive admission of the original failed native allocation.

The change ledger records exactly two existing terminal cells: subtract3669/562949953421312 from one bus's pull-in allocation and add1221/562949953421312 to the other. No new cell was created. Both per-bus exact fullness residuals are zero after construction. Routes and every other allocation are preserved; stale reported loads/SOC/operations were dropped. The constructor's `independently_replayed=false`/`physical_upper_certified=false` fields describe its pre-replay stage, not the later completed independent admission. The final public PASS/upper depends on the separate strict replay, not on these constructor flags alone.

## Improved public interval

Combining the new physical witness with the prior valid CH lower bound gives the safe outward display

    429.22 ≤ CH ≤ D ≤ 442.13,
    0 ≤ D−CH ≤ 12.91.

The lower endpoint429.22 remains the previously established outward lower bound. The new exact physical cost is below the outward upper442.13. These displayed endpoints justify12.91 conservatively. The interval still contains zero: **optimal-fleet price support remains unresolved**. It neither proves a positive gap nor equality of physical/hull values. No exact optimality claim follows from the number of digits in the new upper.

## Physical optimum has exactly two buses

The new report's elementary lower bound for every physical fleet using at least3 buses is **477.8235038838777**, with its exact fraction saved. It strictly exceeds the new admitted upper. The bound uses full replenishment, nonnegative movement energy/costs, nonnegative quadratic supply cost, fee100 and the minimum linear energy coefficient. It excludes all3+ bus physical plans from physical optimum.

Combining that exclusion with the established one-bus impossibility and the new feasible two-bus witness shows: **every physical planner optimizer uses exactly two buses in this declared case**. This narrows cardinality, not routing/charging optimality.

The exclusion does **not** apply to arbitrary components of a complete-fleet hull mixture. A higher-cost3+ bus component can still help a mixture attain a different mean energy profile and convexified cost. Do not restrict hull pricing or the complete-fleet response oracle to two buses solely from this physical objective bound. At other posted prices, physical price-response cardinality can also differ.

## Closure and accounting

Worker33007 exited0 and was reaped; owner receipt has no failure and preserves literal/public PASS states. The external meter reads real0.84,user0.60,sys0.16, confirming **0.76 displayedCPU /0.84wall**. Retained allowance **0.78** is the parent's frozen accounting convention, not another measured execution.

Parent-supplied accumulated closure: **22020.27 displayedCPU /22901.21 elapsed-sum /22021.20 retainedCPU**. Worker/owner usage overlaps the external meter and must not be added again. The original native attempt stays closed and immutable; this new successful construction does not erase its failed strict candidates or refund any spend. Current reviewer/static CPU remains UNKNOWN.

## Recommended concise report

“An exact terminal-only adjustment of two charging cells yields a strictly replayed two-bus witness with cost below442.13. Together with the existing lower certificate, this narrows the public physical–hull gap to[0,12.91]. An elementary energy bound excludes3+ buses from physical optimality; prior one-bus infeasibility therefore fixes the optimal physical fleet size at two. The gap sign and optimal-fleet marginal-price support remain unresolved.”
