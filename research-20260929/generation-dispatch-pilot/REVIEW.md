# Hourly generation dispatch on the exact two-service fleet

29 September 2026. Local synthetic pilot. The [protocol](PROTOCOL.md) records
an initial **invalid-for-hourly-ramps two-period exploratory model**, followed
by the chronology correction made before the final solve. Only the corrected
three-period numbers below are evidence for the paper's timetable. No cluster
job, manuscript edit, or commitment model is involved.

## Physical setup and dispatch baseline

This retains every fleet branch of `paper/latex/exact_results.tex`: one bus has
early/terminal load `(10,20)` and costs 7; two buses cost 14 and have load
`(x,30-x)` for every real `0<=x<=10`. The early and terminal charging windows
are `[1,2]` and `[3,4]`, separated by B's `[2,3]` service. The hourly fleet
load is therefore `L=(x,0,30-x)`, with background demand `b=(0,15,0)`.
Generation is continuous, with no startup cost or shedding:

| generator | hourly costs | hourly caps | initial output | initial up/down | later up/down |
| --- | --- | --- | ---: | --- | --- |
| A | `(7,5,1)` | `(10,15,15)` | 0 | `10/30` | `5/30` |
| B | `(6,5,5)` | `(10,15,30)` | 0 | `30/30` | `30/30` |

There is no required terminal output after `[3,4]`. The baseline is feasible
and has `H(b)=75`: all 15 middle-hour units cost 5, regardless of generator
split. The fleet supply cost is `G(L)=H(b+L)-75`. In particular, the middle
background is dispatched and the two A ramp rows each cover exactly one hour.

## Exact cost over the entire continuous charging branch

Let `a,m,z` be A's early, middle, and terminal outputs. The B outputs are
`x-a, 15-m, 30-x-z`. Subtracting the 75 baseline gives

`G(x,0,30-x) = 150 + x + a - 4z`.

The two hourly A ramps and terminal cap imply
`z <= min(15,m+5) <= min(15,a+10)`. For any `0<=a<=x<=10`, setting
`m=a+5` and `z=min(15,a+10)` attains that bound; the resulting B outputs,
both units' capacities, initial ramps, and all down ramps are feasible.
The marginal cost of A in the middle equals B's, so raising `m` has no direct
cost. For `a<=5`, the objective becomes `110+x-3a`; for `a>=5`, it is
`90+x+a`. Minimizing over **all** `a in [0,x]` proves

```
G(x,0,30-x) = 110 - 2x    for 0 <= x <= 5,
                 95 + x     for 5 <= x <= 10.
```

Thus the one-bus physical cost is `7+G(10)=112`. The best two-bus cost is
`14+G(5)=114`. The exact physical optimum is `D=112`. At `x=5` a dispatch
is A=`(5,10,15)`, B=`(0,5,10)`; A's early-to-middle and middle-to-terminal
up ramps each bind at 5, as does its terminal capacity.

For a complete-fleet mixture with one-bus weight `lambda`, write the two-bus
component's early charge as `y in [0,10]`. Its mean early charge is
`x=10lambda+(1-lambda)y`, so the exact projected hull is
`0<=x<=10`, `0<=lambda<=x/10`, intrinsic cost `14-7lambda`.
At fixed x the largest lambda is cheapest. The resulting hull objective is
`G(x)+14-7x/10`: it decreases to `x=5` from the left and increases to its
right. Its exact value is `CH=221/2=110.5`; the physical gap is
`D-CH=3/2`. A feasible supporting mixture is half the one-bus plan at
`L=(10,0,20)` and half the two-bus plan with zero early charging at
`L=(0,0,30)`. Its mean `L=(5,0,25)` is a pricing object, not a physical fleet.

## Exact price certificate and multiplicity

At the mean load, a generator dual has balance prices
`p=(57/10,5,5)`. Nonzero inequality rents are `13/10` on each of A's two
hourly up ramps and `27/10` on A's terminal cap. These rents satisfy all
generator dual inequalities; the dual intercept is
`5(13/10)+5(13/10)+15(27/10)=107/2`. Subtracting the background dispatch
cost cancels its `p*b=75`, so the globally valid incremental supply cut is

`G(L) >= p*L - 107/2`.

At this price the one-bus plan and the zero-early two-bus plan both have
private cost 164; every other two-bus charge has private cost `164+7x/10`.
Hence `V(p)=164` over the **entire physical fleet set** and the cut proves
`CH >= 164-107/2=221/2`. The feasible mixture above attains equality.
At the physical one-bus optimum, supply LOC at this common price is `3/2`
and fleet LOC is zero.

The complete optimal generator balance-price projection at the mean has
`p_middle=p_terminal=5` and `p_early in [3,6]`, so the admissible early-minus-
terminal price spread is exactly `[-2,1]`. This follows from positive B
output in middle/terminal, positive A output in all three hours, the two
binding ramp rents, the terminal-cap rent, and B's unused early option.
The selected `57/10-5=7/10` spread makes the two supporting fleet plans tie.
At the physical optimum `L=(10,0,20)`, positive B output in all hours pins
the price uniquely at `(6,5,5)`; its spread is 1. The one-bus private cost
is 167, versus 164 for the zero-early two-bus response. Thus the **minimum
own-price regret across all admissible generator dual prices is 3**.

For comparison, the feasible but physically suboptimal two-bus plan at `x=5`
has an optimal generator price set `(s,5,5)`, `3<=s<=6`. Its private cost is
`139+5s`. The complete-fleet response value is `107+10s` for `s<=57/10`
and 164 for `s>=57/10`; these expressions minimize over both the one-bus
point and the full continuous two-bus branch. Its regret is therefore
`32-5s` on the first range and `5s-25` on the second, attaining an exact
minimum of `7/2` at `s=57/10`. That equals this plan's physical cost above
the hull, `114-110.5=3.5`, and shows why one arbitrarily selected dispatch
dual is insufficient to assess a plan with multiple admissible prices.

## Control and solver checks

Changing only A's two inter-hour up limits from 5 to 30 removes their effect
on the fleet branch. A is then cheapest to dispatch terminally at its cap,
and B serves the early hour. Exact algebra gives `G_control(x)=90+x` on
`[0,10]`. The physical optimum is the zero-early two-bus plan at 104, and
the hull optimum is the same plan: `D_control=CH_control=104`, gap zero.
These are outcomes under different supply feasible sets, not an additive
decomposition of ramp and fleet effects.

The [solver output](RESULT.json) is an independent numerical check at
`x=0,5,10` for both models and of a compact LP with the whole two-bus interval.
All six dispatches have primal residual, dual violation, objective gap, and
complementarity zero to printed precision. The three-hour ramp case has
`H(b)=75`, `H(b+(5,0,25))=175`, hull mean `x=5`, and hull value 110.5.
Numerical price-range endpoints differ from the exact integers by at most
about `2e-9` under the requested `1e-8` optimal-face tolerance. The
[Fraction certificate](exact_certificate.py) separately verifies the stated
rational schedules, cut, values, and regret; the algebra above establishes
global optimality over continuous x and all allowed mixtures.
The [execution log](RUN_LOG.md) records the superseded two-period solve,
preserved command wall-time receipts, and the fact that its original JSON was
overwritten before output preservation was added. Subsequent runner outputs
use exclusive filenames and capture per-LP timing prospectively.

Run locally with one native thread:

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src python3 research-20260929/generation-dispatch-pilot/run_pilot.py
python3 research-20260929/generation-dispatch-pilot/exact_certificate.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src python3 -m pytest -q src/tests/test_convex_dispatch.py
```

The reusable [dispatch evaluator](../../src/egglab/convex_dispatch.py) takes
hourly costs, caps, initial outputs and per-hour ramps; it reports feasible
primal output, balance prices, inequality rents and primal-dual checks. It
returns infeasible for demand beyond capacity and computes baseline-subtracted
cost only when both dispatches are feasible. It does not optimize a fleet,
model a network, use quadratic/PWL blocks, or handle unit commitment. At
infeasible fleet loads, a full integrated implementation would need explicit
feasibility cuts or declared emergency supply. This pilot changes supply
economics only; the original smooth-quadratic manuscript theorem requires
separate nonsmooth/attainment hypotheses before reuse with this LP value
function.
