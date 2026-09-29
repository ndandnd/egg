# Frozen local dispatch pilot protocol

Recorded before the first dispatch solve on 2026-09-29. This is a synthetic
two-hour generation replacement for the supply function in the paper's exact
two-service fleet construction (`paper/latex/exact_results.tex`). Hours here
denote its early and terminal one-hour charging windows; both services still
consume 15 kWh, every used bus starts/ends at 20 kWh, the one-bus load is
`(10,20)` and the two-bus loads are `(x,30-x)`, `0 <= x <= 10`. Their operating
costs are 7 and 14. Charging remains continuous and lossless with the same
shared early/terminal power limits and other exclusions in that construction.

Generation has two continuous, convex linear-cost units and no commitment:

| unit | early marginal cost | terminal marginal cost | early cap | terminal cap | initial MW | up ramp | down ramp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 7 | 1 | 10 | 15 | 0 | 10 | 30 |
| B | 6 | 5 | 10 | 30 | 0 | 30 | 30 |

One-hour power and energy numbers coincide. The initial output applies at the
start of the early window; ramp rows link initial-to-early and early-to-terminal
outputs. There is no imposed end output after the terminal window. There is no
background demand (`b=(0,0)`), so `G(L)=H(L)-H(b)=H(L)`. Generator minimum
outputs are zero; any unmet demand is infeasible rather than silently shed.

Before solving, the intended exact calculation is to minimize supply over all
generator dispatches for each fleet load, then minimize over the *entire*
two-bus charging interval and the complete-fleet convex hull. The planned
controls are removing only ramp rows and checking nonzero-baseline subtraction
through the reusable evaluator. Report primal/dual equality, generator balance
price(s), ramp binding, cut validity and any price multiplicity. A grid scan or
cluster launch is outside this protocol. One small LP per explicitly identified
load/mixture plus a compact hull LP is sufficient; rational algebra supplies
the global branch proof independently of the LP results.

## Chronology correction before the final three-period solve

The first two-period local solve verified the algebra above but skipped hour
`[2,3]`, when service B is operating. It is exploratory and **cannot support an
hourly ramp claim for the paper's timetable**. The linked experiment is amended
to three actual consecutive grid hours `[1,2]`, `[2,3]`, `[3,4]`, with fleet load
`L=(x,0,30-x)` and background `b=(0,15,0)`. Its generator data are:

| unit | marginal costs | capacities | initial output | initial up / down | each later up / down |
| --- | --- | --- | ---: | --- | --- |
| A | `(7,5,1)` | `(10,15,15)` | 0 | `10 / 30` | `5 / 30` |
| B | `(6,5,5)` | `(10,15,30)` | 0 | `30 / 30` | `30 / 30` |

The middle 15-kWh background is served at unit cost 5 by either unit. It is
explicitly included in dispatch and baseline subtraction. A must ramp through
that hour: `A_middle <= A_early+5` and `A_terminal <= A_middle+5`. There is no
fleet charging in the middle hour. All physical fleet parameters above remain
unchanged. The no-ramp control changes only the up limits to 30 (the other
data, including middle demand, remain identical). The planned checks also
include all three balance prices and two binding hourly ramp rows. This
amendment precedes the first three-period solve.
