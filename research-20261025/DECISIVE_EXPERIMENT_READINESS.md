# Decisive experiment readiness — 25 October 2026

The shortest useful route is a frozen-schedule tariff audit of the completed
October17 evidence. It needs no unfinished responsive owner, new optimizer run,
trained model or protected data. Further supervision engineering is not a
prerequisite for asking whether the saved plan alternatives contain a meaningful
price-response signal.

## What is already established

`research-20261017/screen-analysis-v3-final/summary.json` describes360 completed
decisions:20 inspected synthetic development timetables, three paired solver
seeds and six arms. Its342 admitted endpoints have saved `result.json`,
`replay.json`, `plan.json` and supervisor receipts under `local-screen-v3`.
`FINAL_REPLAY_VERIFICATION.{json,md}` independently replayed these342 witnesses
with zero recorded replay/bill/mapping mismatches; the18 nonvalid endpoints stay
nonvalid. This is development evidence, not a generalization or optimum claim.

The proposed simple fleet/electricity decomposition has already been done:
`research-20261023/analyze_bill_mechanism.py`, `bill-mechanism/decomposition.json`
and `BILL_MECHANISM_INDEPENDENT_CHECK.md`. At80 trips,91.916% of summed matched
graph-versus-nonlearned savings was vehicle-count cost. At40 trips every primary
pair had equal fleet count, but residual electricity differences can still arise
from route energy/charging opportunities. Repeating this arithmetic is not the
missing decisive experiment. The large ranking result cannot presently be sold
as learned tariff response or an advantage over strong classical methods.

## Runnable existing-evidence analysis: fixed witnessed-plan price signal

New standalone script: `research-20261025/price_signal_audit/analyze.py`.
Exact inputs, command, tariff transformations, estimands, failure handling and
120CPU/180wall limit are frozen in its adjacent `PROTOCOL.md`; the scientific
reset decision provides24 seconds startup/final accounting in addition.
The sole intended output is `price_signal_audit/results.json`.

It reads the summary, previous replay audit and only342 admitted compact
result/replay/supervisor triples, validates receipt hashes once and matches
each original rational bill exactly. No original plan reconstruction or audit of
unrelated model/source assets is needed. Original replay loads are30 hourly grid
energy values in kWh. The formula is `ops+sum(a*load+b*load²/2)`; using kW, an
extra duration factor, decimal1/900 instead of the original binary64 coefficient,
or changing curvature would answer a different question.

The fixed minimum-observed-fleet bank within each timetable prevents fleet
penalties from mechanically dominating primary tariff selection. Prespecified
day/flat/late/+6/-6 shifts preserve the original mean. Target regret, winner
switches, energy-quantity/timing/curvature decomposition and a catalog-only price
stability radius identify whether the observed alternatives expose useful price
headroom. Same-seed/equal-fleet graph versus nonlearned/CatBoost comparisons retain
their conditional denominators. All-fleet sensitivity reveals the fleet tradeoff.
Day/late integrated system-cost versus marginal-price-payment minima explicitly
test the economic objective distinction. Neither calculation identifies a learned
mechanism or strategic equilibrium. A zero result with one catalog option is a
coverage failure, not evidence that prices are irrelevant.

This is the immediately runnable analysis after parent source review. It has
not been imported, tested, hashed or executed during this static assessment.

## Small prospective new solve: hold routes fixed, move the charging incentive

After the catalog result, the smallest genuine new optimizer evidence is one
inspected40-trip route, two target charging schedules, no route acquisition.
Use `scale:50955:40`, seed17 graph plan at
`research-20261017/local-screen-v3/52ca62654b1c267736af/plan.json`, with the original
lock mapping and accepted replay/result receipts. The case is already part of
the completed development screen; no new timetable or protected bank is opened.
Freeze this selection before the price-audit outcomes; do not swap to a favorable
case. This is a mechanism diagnostic, not a population comparison.

The existing implementation path is
`egglab.route_fixed_repair._solve_fixed_charge(case,market,selected,budget)` in
`src/egglab/route_fixed_repair.py:303`. Construct the original full case through
`claude_cases.make('scale:50955:40')`, collect the archived plan's movement IDs,
and use `physical_learning_cases.market(case,'day')` and `'late'`.
`native_recharge.Budget(backend='GRB',threads=1,phase_seconds=10,wall_seconds=15,max_rounds=1,epsilon=1e-4)`
is a prospective cap per target, not a measured runtime promise. The helper
already fixes every movement binary, optimizes linear `a`, extracts and physically
replays the unchanged routes. Independently call `native_recharge.replay_native`
and recompute both integrated cost and marginal-price payment afterwards.
Its current objective uses only `a`; it does not optimize the curved objective.

Use a new research-only `fixed_route_tariff_pilot.py` driver, not the historical
hardcoded exclusive `fixed_source_charge_campaign` namespace or a responsive
native task. That thin driver still needs static implementation/review and a
separate prospective command/receipt; it is not being presented as an existing
ready CLI. Reuse the already functioning helper/replay functions instead of
building a new recovery controller. An existing metered single-process outer
cap can supervise it; no60-second benchmark or native-entry qualification is
claimed. Budget60CPU/90wall inclusive of two15-second charge windows, imports,
independent replay, output and closure; one native thread, no retry. If setup
or the first target exhausts the envelope, retain failure and do not dispatch
the second target. No assumption that a library time limit covers model build,
serialization or all native calls.

Readouts: changed charge-period load at fixed routes; target integrated cost
relative to the original frozen schedule; linear target objective; grid energy
and exact physical replay; solver status and all missing/censored failures.
Matching a fixed-route LP optimum under linear prices proves neither full-route
optimality nor learned ranking value. Differences can establish that physical
charging flexibility exists under this selected topology; no difference can
reflect restricted charging windows or the linear-objective limitation.

## What remains decisive after these cheap diagnostics

A later prospective learned-value comparison must challenge the weak-baseline,
fleet-construction and search-allocation explanations: price-blind/charging-aware
classical controls, a common feasible backbone and comparable retained counts,
matched total time, grouped independent timetable/regime shifts, and failures
retained without invented penalty bills. Per-trip recall against learned-produced
incumbents alone is circular evidence; a fixed schedule repricing result alone
is also insufficient. No additional architecture sweep is justified until these
mechanisms and conventional controls earn a clear scientific question.

All current sealed DEV/TEST/A6/B3/confirmation/GIRO restrictions remain. This
assessment changes no qualified source, historical result or incomplete flag.
