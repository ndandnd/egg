# Frozen-schedule price-signal audit — prospective protocol

25 October 2026. Static source only until the parent reviews and freezes this
protocol and `analyze.py`. One execution, no retry, using only the completed
October17 inspected synthetic development screen. Qualified production/helper/
source-test bytes remain unchanged. No solver, model, inference, training,
new timetable, protected bank, cluster or native-control component is involved.

The scientific-reset decision provides120 CPU seconds/180 wall seconds plus24
seconds startup/final accounting. Preserve the historical guard2546.091499549272
separately; this is new observed analysis cost, not a reset or restored old-cap
compliance. The parent meters the whole process and freezes its exact source and
command. No duplicate tests, full replay audit or model/source-asset hash audit.

The exact child command, from the worktree, is:

```
.venv-local/bin/python research-20261025/price_signal_audit/analyze.py --root /Users/nadan/Documents/ChatGPT/egg/ml-prediction-20261017 --output research-20261025/price_signal_audit/results.json
```

This is the analysis command, not execution clearance. One Python process/thread,
no children. The script sets RLIMIT_CPU120 and alarm180; cooperative checks stop
the body at115 CPU/175 wall to retain5 seconds for publication. The parent owns
the whole-process receipt. An exclusive `results.json` first contains a valid
incomplete/failed placeholder. A complete success or failure report is written
to exclusive `results.json.final.tmp`, flushed/fsynced and atomically replaces
only that process's placeholder. Interruption leaves the incomplete result and
any partial temporary file; neither is a pass. Existing outputs are never reused.

## Inputs and independent identities

Read `screen-analysis-v3-final/summary.json` and
`FINAL_REPLAY_VERIFICATION.json` under `research-20261017`. Require the complete
360-task development cohort,342 independently replayed/exact-bill-matched
admitted endpoints,20 timetables (ten40/ten80), seeds17/41/73 and original arm
valid counts60/60/60/59/44/59. For admitted cells only, read the corresponding
`local-screen-v3/<directory>/{result,replay,supervisor}.json` once each. Validate
every consumed receipt byte digest against the historical replay audit's
`input_sha256`; preserve original invalid/censored endpoints as unavailable.
The summary, historical audit, this source and protocol are themselves hashed
once in-process and bound prospectively by the parent. No raw logs, plan files,
model assets, sealed DEV/TEST/A6/B3/confirmation/GIRO or generated cases are read.

Require task/admission agreement,30 finite nonnegative period loads, saved grid
energy agreement within1e-6kWh and operating cost100 times vehicle count. The
replay `load[t]` is period grid ENERGY in kWh, not kW. Do not multiply again by
period duration. The original market has30 hourly periods, `a=.10` at zero-based
indices10..13 and `.30` elsewhere; `b=float(1/900)` in every period. Reconstruct
the exact historical objective with `Fraction.from_float` of stored finite
numbers and coefficient floats:

`B(L)=ops + sum(a[t]*L[t] + b*L[t]**2/2)`.

It must equal each `result.bill_exact` rational exactly before any inference.
This independently implements `native_hull.supply` without importing project code.
The historical audit supplies physical witness admission; this process does not
claim to repeat physical replay.

## Prespecified tariff and catalog comparisons

Use five distinct mean-preserving linear coefficients: original day; exact flat
mean of the original binary64 coefficients; late (cheap indices22..25); cyclic
day shift+6 (cheap16..19); cyclic day shift-6 (cheap4..7). Shift convention is
`a_shift[t]=a_day[(t-k)%30]`. Shift+12 was removed prospectively because it is
identical to late. Curvature is unchanged. These are paired tariff conditions,
not five independent datasets.

Pool available plans within each timetable across six arms and three seeds.
Primary catalog is all observed plans at that timetable's minimum observed
vehicle count, fixed across every target tariff. Also report an all-fleet
sensitivity catalog. This is observed minimum fleet, not a fleet optimum. Record
candidate and distinct-load counts; a one-option catalog has no demonstrated
selection headroom. Break exact objective ties by `(arm,seed,directory)`.

Select the original-day catalog minimizer, then compute each target's best
observed cost, original-selection regret, relative regret and whether regret
exceeds1e-6 cost units. Include the original/target plan IDs. For every cost
difference report fleet operating cost, common-mean-price energy quantity,
linear tariff timing exposure and quadratic curvature components. Their exact
sum must equal the reported difference. Different route energy requirements can
change electricity cost even at equal fleet count.

For each same-fleet primary catalog, calculate the original-day stability radius
`min_j (B_j-B_best)/||L_j-L_best||_1`, excluding identical load vectors. Null means
no nonidentical catalog competitor, not evidence of full-space stability; exact
ties with distinct loads give zero. This radius applies only to linear-price
L-infinity perturbations with fixed routes/charges, intrinsic cost and curvature
within this finite catalog. It is not a global price-support certificate.

Separately pair graph versus nonlearned and CatBoost within identical timetable/
seed and equal vehicle count. Preserve missing and unequal-fleet denominators.
Report all eligible paired differences, exact signs, within-timetable median
relative differences, and medians/signs across timetable groups by size. Seeds
are repeated searches, not independent timetables. No bootstrap or significance
test, exclusion of unfavorable valid cells, retraining or promotion gate.

## Economic objective check

For day and late, in each same-fleet/all-fleet catalog, compare the minimizer of
the integrated supply/system-cost objective `c+a'L+.5*b*sum(L²)` with the
minimizer of uniform marginal-price payment `c+a'L+b*sum(L²)`, where marginal
price is `p=a+bL` and any base quantity is absorbed in `a`. Report selected IDs,
payment reduction and the integrated-cost loss from choosing the payment
minimizer. Verify the additive welfare-loss identity. These are alternative
finite-catalog accounting objectives, not an equilibrium or strategic fleet
optimization model. Preserve historical `bill_exact` names for provenance while
describing their integrated-cost meaning correctly.

## Output and interpretation

`results.json` records success/failure/incomplete state, all consumed input
hashes, CPU/wall/rusage, budget, catalogs, paired/group summaries and objective
comparisons. `admitted_rows` exports each original case/seed/arm/directory,
vehicles, original numeric ops/load[30] and exact original bill for a separately
reviewed later catalog study. Other exact quantities serialize as rational
strings; original exported loads remain original JSON numeric values.

A pass establishes input identities and these finite-bank calculations only.
Tariff changes preserve historical feasibility because schedules and physical
constraints do not change. There is no charging/route adaptation, optimum over
unobserved plans, causal or learned-price mechanism attribution, new independent
generalization, native qualification or publication claim. Catalog pooling is a
hindsight benchmark. Missing tariff alternatives can produce zero headroom even
when better unobserved plans exist. Preserve all results and failure flags.
