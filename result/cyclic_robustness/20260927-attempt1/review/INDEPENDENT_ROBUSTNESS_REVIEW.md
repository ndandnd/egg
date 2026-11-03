# Independent non-author review: cyclic reserve, loss and connector controls

27 September 2026. **Verdict: PASS within the stated physical model.**

The independent reconstruction agrees with every reported physical interval,
continuous optimum, complete-hull optimum, gap, saved schedule and price/LOC
account in all 16 frozen cases: **nine positive gaps, six zero gaps and one
globally infeasible case**. The joint reserve/loss/headroom example has exact
gap `94249/28880`. The terminal-power positive-gap threshold is exactly
`47/2 kW`, conditional on the nominal reserve, efficiency and early power.

This reviewer authored neither the analytical design nor the result driver.
The protocol and design were read as specifications and scrutinized below.
The independent auditor imports no author experiment code, uses no solver,
does not rerun the experiment, and preserves the raw result and its manifest.
Frozen Git objects were read only to check their hashes, not executed.

## Input identity and reproducibility

- Frozen source/design/protocol commit:
  `bd022ac32ef680446ee17bc4400843a764acb9f6`.
- Raw `../results.json` SHA-256:
  `3d5c20a39b2c7176b6ece22bbeb464a42ea7b3bc58498c0959e227469e25ed29`.
- Immutable raw `../MANIFEST.json` SHA-256:
  `16878cadc5ad8cafdfc7da401fef13e3db04d3711e25c6c83c6eea3d0ecf003a`.
- Final machine-readable audit: `independent-audit-v2.json`.
- Portable auditor: `independent_robustness_audit.py`, standard-library Python
  3.10 or later. Its SHA-256 is embedded in the final audit report.
- `MANIFEST.json` in this **review directory** covers the derived review
  artifacts separately. It does not modify or supersede the raw manifest.

From the repository root, use a previously nonexistent report path:

```sh
python3 result/cyclic_robustness/20260927-attempt1/review/independent_robustness_audit.py \
  --repo . \
  --result result/cyclic_robustness/20260927-attempt1/results.json \
  --report /tmp/egg-robustness-independent-new-audit.json
```

The initial derived report `independent-audit.json` passed the same complete
semantic checks with 20 corruption controls. Version 2 adds two stronger
controls that preserve session energy integrals while corrupting occupancy
or exceeding connector power. No raw output changed between these audits.
The final auditor and final report are the reproduction pair.

## Independent physical derivation

Work initially in **battery-side early recharge**, denoted `y`, rather than
assuming the driver's grid-side interval formulas. There are exactly two
unlabeled partitions of two mandatory services among one or two nonempty bus
duties: `{A,B}` and `{A},{B}`. All used buses start and finish at 20 kWh.
Each service consumes 15 battery kWh. Consequently every physical schedule
must restore 30 battery kWh, regardless of bus count.

After A, its bus has 5 kWh. It can receive at most 15 battery kWh before
overfilling. Early charging delivers at most `eta * P_E`, so
`y <= min(15, eta * P_E)`. A separate B bus starts full, has no prior energy
use and cannot absorb early energy. The remaining total battery recharge is
`30-y`; the one-hour terminal connector can deliver at most `eta*K`.
Therefore `y >= max(0,30-eta*K)` for either partition.

On the one-bus partition, inventory after B is `y-10`, adding the necessary
lower bound `y >= 10+r`. On the two-bus partition, each post-service minimum
is 5, so no additional lower bound is needed when `0 <= r <= 5`. Dividing
these battery-side intervals by `eta` yields the reported complete intervals
for early grid energy `x`:

- Two buses: `[max(0,30/eta-K), min(P_E,15/eta)]`.
- One bus: `[max(0,30/eta-K,(10+r)/eta), min(P_E,15/eta)]`.

An interval with lower endpoint above its upper endpoint is infeasible.
There is no missing service partition. The constraints are sufficient as
well as necessary: SOC changes monotonically during each declared service
or charging interval, and the explicit connector construction below realizes
every point. These statements rely on no idle consumption, no deadheads,
constant efficiency, flexible nonnegative charging power and no taper.

Gross grid energy is `30/eta`, hence `600/19` at efficiency `19/20`.
The supply cost is evaluated on **grid purchases**, not battery delivery.
The two-bus structure cannot receive an initial-inventory subsidy because
both individual buses return to 20 kWh.

## One-connector sufficiency and independent witness replay

For two buses at early grid energy `x`, terminal demands are
`q_A=15/eta-x` and `q_B=15/eta`. Set aggregate terminal power
`q=q_A+q_B=30/eta-x`, which does not exceed `K`. Run A at power `q` for
`q_A/q` hours, then B at the same power for `q_B/q` hours. Both sessions fit
exactly into `[3,4]`, do not overlap, and each bus finishes full. Early A
charging runs at constant power `x` over `[1,2]`. The one-bus case uses power
`30/eta-x` throughout the terminal hour.

For every saved physical optimizer, endpoint witness and positive-weight
hull component, the auditor reconstructs SOC from the service assignments
and charging amounts. It verifies the reserve, battery capacity, individual
replenishment, shared early and terminal power, battery/grid conversion and
all reported margins. It integrates each terminal session's power and splits
the hour at **every** session endpoint. Exactly one session occupies each
resulting open interval, at the reported constant aggregate power. This
establishes continuous nonoverlap rather than sampling a few times.

At the joint example's two-bus supporting endpoint, early grid energy is
`30/19` and terminal demand is exactly 30 grid kWh. A charges at 30 kW over
`[3,66/19]`, duration `9/19`, buying `270/19` grid kWh; B follows over
`[66/19,4]`, duration `10/19`, buying `300/19`. These are two sequential
sessions on connector 0, not simultaneous use of two plugs.

Because the aggregate power is constant in each unit-length charging window,
the window-energy quadratic equals the integral of that quadratic in
aggregate power. Sequential service does not hide a power spike. Positive
switching time, setup energy, taper or minimum session duration would change
this model and are not covered by the result.

## Independent optimization and price verification

Each physical branch is a full continuous interval with constant intrinsic
cost `7 * buses`. The auditor evaluates each quadratic at its two endpoints
and midpoint, reconstructs its coefficients by interpolation, and evaluates
any interior stationary point. This is an exact rational continuous minimum,
not a charging grid search.

To verify the **complete** convex hull independently, it collects both
endpoints of every feasible branch and minimizes the objective on every
pairwise chord, including chords above the lower hull. Since the objective
increases strictly with intrinsic cost, a minimum of this polygon lies on
the lower boundary; each boundary edge is among those chords. Thus this
different algorithm recovers the complete-hull value. The recorded lower
vertices are separately checked against all supporting lines. Recorded
positive weights must reconstruct the independently optimal aggregate load
and intrinsic cost from individually feasible endpoint schedules.

The full posted-price fleet response is a linear minimization over all
feasible branch endpoints. For the globally defined nonnegative-load cost
`F(E,L)=4E+(E^2+L^2)/10`, its conjugate is independently evaluated as

`F*(p_E,p_L) = (5/2) [max(p_E-4,0)^2 + max(p_L,0)^2]`.

For each feasible case, the auditor checks the gradient price at the hull
load, fleet response and exact dual identity `CH = V(p)-F*(p)`. For every
feasible branch optimizer, it checks its own gradient and posted-price
regret, as well as fleet and supply LOC at the common hull price. The exact
identity checked is

`fleet LOC + supply LOC = branch objective - CH`.

This equals the planning gap only for a physical optimizer; a suboptimal
branch adds its physical suboptimality. The auditor also verifies
nonnegativity and the gap/own-price-regret inequality. It does not confuse
fleet regret alone with total market LOC or interpret a fractional fleet
mixture as a dispatchable schedule.

## Joint example and neighborhood claim

For `r=1`, `eta=19/20`, `P_E=12` and `K=30`, let `ell` be the two-bus lower
endpoint, `h` the one-bus lower endpoint and `u` the common upper endpoint.
Independent substitution gives

`ell=30/19`, `h=220/19`, `u=12`, `d=h-ell=10`.

The free minimum of the supply quadratic is `m=110/19`. On the sloping
lower-hull edge, the minimum is at `x*=m+35/(2d)=573/76`. Its one-bus weight
is `453/760`. Exact independently reproduced values are:

| Quantity | Exact value |
|---|---:|
| One-bus physical optimum | `38527/361` |
| Two-bus physical optimum | `38634/361` |
| Physical optimum | `38527/361` |
| Complete-hull optimum | `2987911/28880` |
| Planning gap | `94249/28880` |
| One-bus own-price regret | `307/19` |
| Common-price fleet LOC at the physical optimum | `0` |
| Common-price supply LOC at the physical optimum | `94249/28880` |

The sufficient positive-gap argument is valid. Completing the square gives
curvature `k=1/5`. The lower boundary for `ell <= x <= h` has intrinsic cost
`14-7(x-ell)/d`; for `h <= x <= u` it is 7. The strict conditions
`ell<m<h<u` and `7<2k*d*(h-m)` place the hull optimum between `m` and `h`.
The gap is the smaller of

`k(h-x*)^2` and `7(m-ell)/d + 49/(4k*d^2)`,

both strictly positive. At the joint example, early headroom is
`u-h=8/19` grid kWh, and the upper threshold for fleet cost is `440/19 > 7`.
Together with `0<r<5` and `0<eta<1`, these strict inequalities and continuity
give an open neighborhood in the stated admissible parameter model. If
vehicle acceptance is itself held at 30 kW, terminal-power perturbations
above 30 lie outside that model; the neighborhood is then relative to that
physical restriction, or one can simply hold terminal power fixed at 30.

The argument does **not** mean every constraint has slack. The one-bus
optimizer binds its reserve and the supporting two-bus endpoint binds
terminal power. Nearby feasible schedules change with the parameters. Nor
does it establish robustness of the original unchanged 10 kW early charger:
any positive reserve at efficiency 1, or any charging loss at reserve 0,
removes its one-bus branch. The original example sits on that feasibility
boundary. Enlarging both the individual and shared early limits is an
explicit, scientifically material change.

## Exact terminal-power threshold

With `r=0`, `eta=1`, early power 10 and `K<=30`, fewer than 20 terminal kW
cannot replace the daily 30 battery kWh even at maximal early charging.
At `K=20`, both partitions have only early energy 10, and the cheaper
one-bus schedule gives zero gap.

For `K=20+d`, `0<d<=10`, the lower edge runs from `(10-d,14)` to `(10,7)`.
The physical optimum remains 97. The objective derivative at the upper
endpoint is `2-7/d`; at the lower endpoint it is `2-(2/5)d-7/d`, always
negative because `2d^2-10d+35` is positive (discriminant `-180`). Therefore
the minimizing load leaves 10 exactly when `d>7/2`, or **`K>47/2`**.
The gap is zero on `[20,47/2]`, and above that threshold it is

`[5-35/(2(K-20))]^2/5`.

This independently proves the continuous threshold; it is stronger than
inferring a threshold from five plotted values. It recovers `5/64` at 24 kW
and `169/80` at 30 kW. At 10 kW the model is infeasible, not a zero-gap case.

## Coverage and controls

| Check | Count |
|---|---:|
| Frozen cases | 16 |
| Complete physical branch intervals | 32 |
| Feasible branch optimizers and price/LOC accounts | 26 |
| Feasible endpoint witnesses | 46 |
| Positive-weight hull components | 28 |
| Saved schedule witness replays, including repeated physical schedules | 100 |
| Individual bus and terminal-session replays | 161 |
| SOC event values reconstructed | 805 |
| Rational values checked against decimal display values | 3,301 |
| Deliberately corrupted documents rejected | 22 |

Corruption controls operate **after bypassing the outer result-hash gate**,
so they exercise semantic checks. They cover changed objectives, grid-energy
accounting, reserve and feasibility errors, missing endpoints or hull
vertices, wrong mixtures, failed replenishment, ignored efficiency, plug
overlap, excess connector power, invalid session integrals, second-connector
use and altered regret/LOC/conjugate values. All were rejected. The stronger
occupancy and power controls preserve session energy integrals to ensure
those respective checks are exercised directly.

## Figure and scientific interpretation

The reviewer visually inspected `paper/figures/cyclic_robustness.png`, SHA-256
`6faf342a2c5c3e72dfe799ad4238b4fac146aa00725e56dabe710e8397039e1d`.
All 12 heatmap labels round the corresponding exact gaps correctly. The
terminal panel correctly distinguishes infeasibility at 10 kW from zero
gaps at 20 and 23.5, and displays the 24 and 30 kW gaps faithfully. Axes
state the reserve, efficiency and charger-power parameters. No clipping or
mislabeling was observed. The caption should retain the synthetic cost units,
20 kWh capacity, full replenishment and zero switching-time assumptions.

This is a constructive, exactly verified extension with useful negative
controls. Nine positive cases out of sixteen are not an estimated population
frequency, and larger gaps after increasing reserve do not imply that
reserve generally helps coordination. In two reserve-1/lossless cases the
physical optimizer uses two buses, illustrating why physical optimizer
identity must be retained. These results support existence and parameter
sensitivity in the declared model; they do not establish operational
prevalence, realistic taper robustness or performance of a native solver.
